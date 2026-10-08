#!/usr/bin/env python3
"""
Build Bambu Studio projects for the wheel, the wedge and the tile, each on its
own A1 plate with the print settings chosen.

    python3 make_3mf.py                 wheel.3mf, wedge.3mf and tile.3mf for the sample, in stl/
    python3 make_3mf.py private         the same for your own build, in private/

Same approach as the other models' make_3mf.py: the projects select Bambu's
own system presets

    printer   Bambu Lab A1 0.4 nozzle
    filament  Bambu PLA Basic @BBL A1   (the tile uses two: slot 1 yellow, slot 2 dark)
    process   0.16mm High Quality @BBL A1

and list only the keys they change, so Bambu Studio fills everything else from
the presets installed on your computer.  bambu_profiles/*.json are those
presets with their inheritance resolved.
"""
import io, json, os, sys, zipfile, datetime
import trimesh
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))

PRINTER = "Bambu Lab A1 0.4 nozzle"
FILAMENT = "Bambu PLA Basic @BBL A1"
PROCESS = "0.16mm High Quality @BBL A1"
COMMON = {
    "brim_type": "no_brim",            # flat, wide footprints
    "enable_support": "0",             # every hole has a 45-degree roof
}
SOLID_PARTS = dict(COMMON, **{
    "seam_position": "back",           # the plate is turned so the seam runs down the back of the rind
    "sparse_infill_pattern": "lightning",  # only holds up the top: these are mostly air inside
    "sparse_infill_density": "10%",
})
PROJECTS = {
    # name: (parts [(stl, extruder)], colours, process changes, thumbnail, description)
    "wheel": ([("wheel", 1)], ["#F7C64A"], SOLID_PARTS, "wheel_closed.png",
              "The wheel. Print in cheese yellow."),
    "wedge": ([("wedge", 1)], ["#F7C64A"], SOLID_PARTS, "wheel_closed.png",
              "The wedge. Print in cheese yellow."),
    "tile": ([("tile_plate", 1), ("tile_qr", 2)], ["#F7C64A", "#2B1D14"], COMMON, "wheel_open.png",
             "The QR tile: yellow plate, dark code. One filament change at the top of the plate."),
}
APP_VERSION = "02.00.00.95"
BED = 256.0

def load(name):
    d = json.load(open(os.path.join(HERE, "bambu_profiles", name)))
    for k in [k for k in d if k.startswith("_")]: d.pop(k)
    return d

META = {"type", "name", "from", "instantiation", "setting_id", "include", "inherits", "description",
        "compatible_printers", "compatible_printers_condition", "compatible_prints",
        "compatible_prints_condition", "renamed_from", "filament_id", "version"}

def project_settings(colours, changes):
    printer, process, filament = load("printer.json"), load("process.json"), load("filament.json")
    nf = len(colours)
    cfg = {}
    for part in (printer, process):
        for k, v in part.items():
            if k not in META: cfg[k] = v
    for k, v in filament.items():         # filament settings are per-filament lists: one entry per slot
        if k not in META: cfg[k] = v * nf if isinstance(v, list) and len(v) == 1 else v
    cfg.update(changes)
    cfg.update({
        "version": APP_VERSION, "name": "project_settings", "from": "project",
        "print_settings_id": PROCESS,
        "printer_settings_id": PRINTER,
        "filament_settings_id": [FILAMENT] * nf,
        "filament_ids": [filament["filament_id"]] * nf,
        "filament_colour": colours,
        "filament_map": ["1"] * nf,
        "filament_self_index": [str(i + 1) for i in range(nf)],
        "print_compatible_printers": process.get("compatible_printers", [PRINTER]),
        "curr_bed_type": "Textured PEI Plate",
        # one entry per preset: print, each filament, printer
        "different_settings_to_system": [";".join(sorted(k for k, v in changes.items() if process.get(k) != v))]
                                        + ["filament_type"] * nf + ["printable_height"],
    })
    if nf == 2:
        cfg["flush_volumes_matrix"] = ["0", "280", "280", "0"]      # dark into yellow needs a generous purge
        cfg["flush_volumes_vector"] = ["140", "140", "140", "140"]
    return cfg

def mesh_xml(m):
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

def part_settings(pid, name, extruder, m):
    return f'''    <part id="{pid}" subtype="normal_part">
      <metadata key="name" value="{name}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="extruder" value="{extruder}"/>
      <metadata key="source_file" value="{name}.stl"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="{pid - 1}"/>
      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
'''

def build(name, stl_dir, image_dir):
    parts, colours, changes, thumb, description = PROJECTS[name]
    meshes = [(p, e, trimesh.load(os.path.join(stl_dir, p + ".stl"))) for p, e in parts]
    lo, hi = meshes[0][2].bounds
    # turned 180 degrees so the rind (and the seam) faces the back of the printer
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    transform = f"-1 0 0 0 -1 0 0 0 1 {BED / 2 + cx:.4f} {BED / 2 + cy:.4f} {-lo[2]:.4f}"
    today = datetime.date.today().isoformat()
    oid = len(meshes) + 1

    components = "".join(
        f'    <component p:path="/3D/Objects/object_1.model" objectid="{i + 1}" '
        f'p:UUID="000{i + 1}0000-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
        for i in range(len(meshes)))
    model = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" {NS}>
 <metadata name="Application">BambuStudio-{APP_VERSION}</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">QR Cheese Wheel: {name}</metadata>
 <metadata name="Description">{description}</metadata>
 <metadata name="CreationDate">{today}</metadata>
 <metadata name="ModificationDate">{today}</metadata>
 <resources>
  <object id="{oid}" p:UUID="00000001-61cb-4c03-9d28-80fed5dfa1dc" type="model">
   <components>
{components}   </components>
  </object>
 </resources>
 <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">
  <item objectid="{oid}" p:UUID="00000002-b1ec-4553-aec9-835e5b724bb4" transform="{transform}" printable="1"/>
 </build>
</model>
'''
    objects = "".join(
        f'  <object id="{i + 1}" p:UUID="000{i + 1}0000-81cb-4c03-9d28-80fed5dfa1dc" type="model">\n{mesh_xml(m)}  </object>\n'
        for i, (_, _, m) in enumerate(meshes))
    sub = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" {NS}>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
{objects} </resources>
 <build/>
</model>
'''
    model_settings = f'''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="{oid}">
    <metadata key="name" value="{name}"/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{sum(len(m.faces) for _, _, m in meshes)}"/>
{"".join(part_settings(i + 1, p, e, m) for i, (p, e, m) in enumerate(meshes))}  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>
    <metadata key="thumbnail_no_light_file" value="Metadata/plate_1.png"/>
    <model_instance>
      <metadata key="object_id" value="0"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="101"/>
    </model_instance>
  </plate>
</config>
'''
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
    model_rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/Objects/object_1.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>'''

    def png(size):
        im = Image.open(os.path.join(image_dir, thumb)).convert("RGB")
        s = min(im.size); im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
        b = io.BytesIO(); im.resize((size, size), Image.LANCZOS).save(b, "PNG"); return b.getvalue()

    out = os.path.join(stl_dir, name + ".3mf")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("3D/_rels/3dmodel.model.rels", model_rels)
        z.writestr("3D/Objects/object_1.model", sub)
        z.writestr("Metadata/model_settings.config", model_settings)
        z.writestr("Metadata/project_settings.config", json.dumps(project_settings(colours, changes), indent=4))
        z.writestr("Metadata/plate_1.png", png(512))
        z.writestr("Metadata/plate_1_small.png", png(128))
    print(f"wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB)")

if __name__ == "__main__":
    d = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "stl")
    # thumbnails from that build's renders if you made them, else the sample's
    images = d if os.path.exists(os.path.join(d, "wheel_open.png")) else os.path.join(HERE, "images")
    for name in PROJECTS:
        build(name, d, images)
