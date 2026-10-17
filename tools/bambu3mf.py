#!/usr/bin/env python3
"""
Write Bambu Studio project files (.3mf) for the models in this repository.

A project holds the parts laid out on one Bambu Lab A1 plate, the printer,
filament and process presets, per-object overrides (for example 100 %
infill on small parts) and pauses at given heights (for example to drop in
magnets).  It opens in Bambu Studio ready to slice.

Presets: the project selects Bambu's own system presets and lists only the
settings it changes ("different_settings_to_system").  Bambu Studio fills
every other value from the presets installed on the user's computer, so the
file does not go stale when Bambu updates its profiles.  The full values are
written as well, because Bambu Studio expects a complete configuration.

bambu_profiles/*.json are Bambu's A1 presets with their inheritance resolved,
taken from the Bambu Studio repository (resources/profiles/BBL).

Usage (see the model folders for real examples; snack-basket/make_3mf.py puts
one object on two AMS filaments with Part(..., extra=[(name, mesh, 2)])):

    from bambu3mf import Part, write_project
    write_project("thing.3mf", [Part("thing", mesh, x=128, y=128)],
                  process="0.20mm Standard @BBL A1", process_changes={"wall_loops": "3"})
"""
import io, json, os, zipfile, datetime
from dataclasses import dataclass, field
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PRINTER = "Bambu Lab A1 0.4 nozzle"
FILAMENT = "Bambu PLA Basic @BBL A1"
APP_VERSION = "02.00.00.95"      # a 2.x version, so current Bambu Studio opens it without a "newer version" prompt
BED = 256.0

META = {"type", "name", "from", "instantiation", "setting_id", "include", "inherits", "description",
        "compatible_printers", "compatible_printers_condition", "compatible_prints",
        "compatible_prints_condition", "renamed_from", "filament_id", "version"}

def _profile(name):
    fn = name.replace(" @BBL A1", "").replace(" ", "_") + ".json"
    d = json.load(open(os.path.join(HERE, "bambu_profiles", fn)))
    return {k: v for k, v in d.items() if not k.startswith("_")}

@dataclass
class Part:
    name: str
    mesh: object                 # trimesh.Trimesh, in print orientation
    x: float                     # plate position of the part's footprint centre (mm)
    y: float
    rot_z: float = 0.0           # turn on the plate (degrees)
    settings: dict = field(default_factory=dict)   # per-object overrides, e.g. {"sparse_infill_density": "100%"}
    extra: list = field(default_factory=list)      # more volumes in the same object, on other filaments (AMS):
                                                   # [(name, mesh, filament number)], in the mesh's coordinates

def _volumes(p):
    return [(p.name, p.mesh, 1)] + list(p.extra)

def _transform(p):
    a = np.radians(p.rot_z); c, s = np.cos(a), np.sin(a)
    v = np.concatenate([m.vertices for _, m, _ in _volumes(p)]) @ np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
    lo, hi = v.min(0), v.max(0)
    t = np.array([p.x - (lo[0] + hi[0]) / 2, p.y - (lo[1] + hi[1]) / 2, -lo[2]])
    # 3MF row-vector convention: m00 m01 m02 m10 m11 m12 m20 m21 m22 tx ty tz
    m = [c, s, 0, -s, c, 0, 0, 0, 1]
    return " ".join(f"{x:.6g}" for x in m) + f" {t[0]:.4f} {t[1]:.4f} {t[2]:.4f}", lo + t, hi + t

def _mesh_xml(m):
    out = io.StringIO()
    out.write("   <mesh>\n    <vertices>\n")
    for x, y, z in m.vertices:
        out.write(f'     <vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>\n')
    out.write("    </vertices>\n    <triangles>\n")
    for a, b, c in m.faces:
        out.write(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>\n')
    out.write("    </triangles>\n   </mesh>\n")
    return out.getvalue()

NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
      'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
      'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')

def project_settings(process, process_changes, filament_colour):
    """filament_colour: one colour, or a list with one per filament (AMS slot)"""
    colours = [filament_colour] if isinstance(filament_colour, str) else list(filament_colour)
    n = len(colours)
    printer, proc, filament = _profile(PRINTER), _profile(process), _profile(FILAMENT)
    cfg = {}
    for part in (printer, proc):
        for k, v in part.items():
            if k not in META: cfg[k] = v
    for k, v in filament.items():         # filament settings are per-filament lists: one entry per slot
        if k not in META: cfg[k] = v * n if isinstance(v, list) and len(v) == 1 else v
    cfg.update(process_changes)
    changed = sorted(k for k, v in process_changes.items() if proc.get(k) != v)
    cfg.update({
        "version": APP_VERSION, "name": "project_settings", "from": "project",
        "print_settings_id": process,
        "printer_settings_id": PRINTER,
        "filament_settings_id": [FILAMENT] * n,
        "filament_ids": [filament["filament_id"]] * n,
        "filament_colour": colours,
        "filament_map": ["1"] * n,
        "filament_self_index": [str(i + 1) for i in range(n)],
        "print_compatible_printers": proc.get("compatible_printers", [PRINTER]),
        "curr_bed_type": "Textured PEI Plate",
        # one entry per preset: print, each filament, printer.  The filament
        # and printer entries name a key whose value is unchanged, so those
        # presets are refreshed from the installed system presets and load
        # unmodified.
        "different_settings_to_system": [";".join(changed)] + ["filament_type"] * n + ["printable_height"],
    })
    if n > 1:                             # purge generously between colours (dark into light needs the most)
        cfg["flush_volumes_matrix"] = ["0" if i == j else "280" for i in range(n) for j in range(n)]
        cfg["flush_volumes_vector"] = ["140"] * (2 * n)
    return cfg

def write_project(out, parts, process, process_changes, pauses=(), title="", description="",
                  thumbnail_png=None, filament_colour="#E8D3B0"):
    """parts: list of Part.  pauses: heights (mm) to pause before printing
    the first layer at or above."""
    today = datetime.date.today().isoformat()
    resources, items, settings_objs, instances, subs = [], [], [], [], {}
    next_id = 1
    for k, p in enumerate(parts):
        vols = _volumes(p)
        vol_ids = list(range(next_id, next_id + len(vols)))   # Bambu numbers each volume, then its object
        obj_id = next_id + len(vols)
        next_id = obj_id + 1
        path = f"3D/Objects/object_{k + 1}.model"
        tr, lo, hi = _transform(p)
        assert lo[0] >= 0 and lo[1] >= 0 and hi[0] <= BED and hi[1] <= BED, f"{p.name} is off the plate: {lo}, {hi}"
        resources.append(f'''  <object id="{obj_id}" p:UUID="{obj_id:08x}-61cb-4c03-9d28-80fed5dfa1dc" type="model">
   <components>
{chr(10).join(f'    <component p:path="/{path}" objectid="{v}" p:UUID="{v:04x}0000-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>' for v in vol_ids)}
   </components>
  </object>''')
        items.append(f'  <item objectid="{obj_id}" p:UUID="{obj_id:08x}-b1ec-4553-aec9-835e5b724bb4" transform="{tr}" printable="1"/>')
        subs[path] = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" {NS}>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
{"".join(f"""  <object id="{v}" p:UUID="{v:04x}0000-81cb-4c03-9d28-80fed5dfa1dc" type="model">
{_mesh_xml(m)}  </object>
""" for v, (_, m, _) in zip(vol_ids, vols))} </resources>
 <build/>
</model>
'''
        extra = "".join(f'    <metadata key="{key}" value="{val}"/>\n' for key, val in p.settings.items())
        part_xml = ""
        for i, (v, (vname, m, fil)) in enumerate(zip(vol_ids, vols)):
            ext = f'      <metadata key="extruder" value="{fil}"/>\n' if len(vols) > 1 else ""
            part_xml += f'''    <part id="{v}" subtype="normal_part">
      <metadata key="name" value="{vname}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
{ext}      <metadata key="source_file" value="{vname}.stl"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="{i}"/>
      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
'''
        settings_objs.append(f'''  <object id="{obj_id}">
    <metadata key="name" value="{p.name}"/>
    <metadata key="extruder" value="1"/>
{extra}    <metadata face_count="{sum(len(m.faces) for _, m, _ in vols)}"/>
{part_xml}  </object>''')
        instances.append(f'''    <model_instance>
      <metadata key="object_id" value="{k}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="{101 + k}"/>
    </model_instance>''')

    model = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" {NS}>
 <metadata name="Application">BambuStudio-{APP_VERSION}</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">{title}</metadata>
 <metadata name="Description">{description}</metadata>
 <metadata name="CreationDate">{today}</metadata>
 <metadata name="ModificationDate">{today}</metadata>
 <resources>
{chr(10).join(resources)}
 </resources>
 <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">
{chr(10).join(items)}
 </build>
</model>
'''
    model_settings = f'''<?xml version="1.0" encoding="UTF-8"?>
<config>
{chr(10).join(settings_objs)}
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>
    <metadata key="thumbnail_no_light_file" value="Metadata/plate_1.png"/>
{chr(10).join(instances)}
  </plate>
</config>
'''
    model_rels = '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n' + \
        "".join(f' <Relationship Target="/{path}" Id="rel-{i + 1}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                for i, path in enumerate(subs)) + "</Relationships>"
    content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="gcode" ContentType="text/x.gcode"/>
</Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
 <Relationship Target="/Metadata/plate_1.png" Id="rel-2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>
 <Relationship Target="/Metadata/plate_1.png" Id="rel-4" Type="http://schemas.bambulab.com/package/2021/cover-thumbnail-middle"/>
 <Relationship Target="/Metadata/plate_1_small.png" Id="rel-5" Type="http://schemas.bambulab.com/package/2021/cover-thumbnail-small"/>
</Relationships>'''
    printer = _profile(PRINTER)
    custom = None
    if pauses:
        layers = "".join(f'<layer top_z="{z:g}" type="1" extruder="1" color="" extra="" gcode="{printer["machine_pause_gcode"]}"/>\n'
                         for z in pauses)
        custom = ('<?xml version="1.0" encoding="utf-8"?>\n<custom_gcodes_per_layer>\n<plate>\n<plate_info id="1"/>\n'
                  + layers + '<mode value="SingleExtruder"/>\n</plate>\n</custom_gcodes_per_layer>\n')

    def png(size):
        from PIL import Image
        im = Image.open(thumbnail_png).convert("RGB")
        s = min(im.size)
        im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
        b = io.BytesIO(); im.resize((size, size), Image.LANCZOS).save(b, "PNG"); return b.getvalue()

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("3D/_rels/3dmodel.model.rels", model_rels)
        for path, xml in subs.items(): z.writestr(path, xml)
        z.writestr("Metadata/model_settings.config", model_settings)
        z.writestr("Metadata/project_settings.config",
                   json.dumps(project_settings(process, process_changes, filament_colour), indent=4))
        if custom: z.writestr("Metadata/custom_gcode_per_layer.xml", custom)
        if thumbnail_png:
            z.writestr("Metadata/plate_1.png", png(512))
            z.writestr("Metadata/plate_1_small.png", png(128))
    return out
