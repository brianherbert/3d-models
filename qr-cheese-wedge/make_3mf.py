#!/usr/bin/env python3
"""
Build cheese_wedge.3mf: a Bambu Studio project with the wedge on an A1 plate,
two filaments (cheese yellow and a dark one for the QR code) already assigned,
and the print settings chosen.

    python3 make_3mf.py [stl_dir]         (after build_wedge.py; writes stl_dir/cheese_wedge.3mf)

Same approach as the horse head's tools/make_3mf.py: it selects Bambu's own
system presets

    printer   Bambu Lab A1 0.4 nozzle
    filament  Bambu PLA Basic @BBL A1   (twice: slot 1 yellow, slot 2 dark)
    process   0.16mm High Quality @BBL A1

and lists only the keys it changes, so Bambu Studio fills everything else from
the presets installed on your computer.  bambu_profiles/*.json are those
presets with their inheritance resolved.

The wedge is one object with two parts: the body on filament 1 and the QR
modules on filament 2.  The QR sits entirely above the body's top face, so the
slicer makes one filament change at that layer and none below it.
"""
import io, json, os, sys, zipfile, datetime
import trimesh
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))

PRINTER = "Bambu Lab A1 0.4 nozzle"
FILAMENT = "Bambu PLA Basic @BBL A1"
PROCESS = "0.16mm High Quality @BBL A1"
PROCESS_CHANGES = {
    "seam_position": "back",           # the plate is turned so the seam runs down the rind, the least-seen face
    "brim_type": "no_brim",            # big flat footprint, no brim needed
    "enable_support": "0",             # every hole has a 45-degree roof
    "sparse_infill_density": "12%",    # it's a paperweight, not a bracket
}
APP_VERSION = "02.00.00.95"
COLOURS = ["#F7C64A", "#2B1D14"]      # cheese yellow, dark brown/black for the code
BED = 256.0
TITLE = "QR Cheese Wedge"

def load(name):
    d = json.load(open(os.path.join(HERE, "bambu_profiles", name)))
    for k in [k for k in d if k.startswith("_")]: d.pop(k)
    return d

META = {"type", "name", "from", "instantiation", "setting_id", "include", "inherits", "description",
        "compatible_printers", "compatible_printers_condition", "compatible_prints",
        "compatible_prints_condition", "renamed_from", "filament_id", "version"}

def project_settings():
    printer, process, filament = load("printer.json"), load("process.json"), load("filament.json")
    cfg = {}
    for part in (printer, process):
        for k, v in part.items():
            if k not in META: cfg[k] = v
    for k, v in filament.items():         # filament settings are per-filament lists: one entry per slot
        if k not in META: cfg[k] = v * 2 if isinstance(v, list) and len(v) == 1 else v
    cfg.update(PROCESS_CHANGES)
    cfg.update({
        "version": APP_VERSION, "name": "project_settings", "from": "project",
        "print_settings_id": PROCESS,
        "printer_settings_id": PRINTER,
        "filament_settings_id": [FILAMENT, FILAMENT],
        "filament_ids": [filament["filament_id"]] * 2,
        "filament_colour": COLOURS,
        "filament_map": ["1", "1"],
        "filament_self_index": ["1", "2"],
        "flush_volumes_matrix": ["0", "280", "280", "0"],   # dark into yellow needs a generous purge
        "flush_volumes_vector": ["140", "140", "140", "140"],
        "print_compatible_printers": process.get("compatible_printers", [PRINTER]),
        "curr_bed_type": "Textured PEI Plate",
        # one entry per preset: print, each filament, printer
        "different_settings_to_system": [";".join(sorted(k for k, v in PROCESS_CHANGES.items() if process.get(k) != v)),
                                         "filament_type", "filament_type", "printable_height"],
    })
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

def build(stl_dir, image_dir):
    body = trimesh.load(os.path.join(stl_dir, "cheese_body.stl"))
    qr = trimesh.load(os.path.join(stl_dir, "cheese_qr.stl"))
    # turned 180 degrees so the rind (and the seam) faces the back of the printer
    lo, hi = body.bounds
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    transform = f"-1 0 0 0 -1 0 0 0 1 {BED / 2 + cx:.4f} {BED / 2 + cy:.4f} {-lo[2]:.4f}"
    today = datetime.date.today().isoformat()

    model = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" {NS}>
 <metadata name="Application">BambuStudio-{APP_VERSION}</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">{TITLE}</metadata>
 <metadata name="Description">A Swiss-cheese wedge with a QR code on top.</metadata>
 <metadata name="CreationDate">{today}</metadata>
 <metadata name="ModificationDate">{today}</metadata>
 <resources>
  <object id="3" p:UUID="00000001-61cb-4c03-9d28-80fed5dfa1dc" type="model">
   <components>
    <component p:path="/3D/Objects/object_1.model" objectid="1" p:UUID="00010000-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
    <component p:path="/3D/Objects/object_1.model" objectid="2" p:UUID="00020000-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
   </components>
  </object>
 </resources>
 <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">
  <item objectid="3" p:UUID="00000002-b1ec-4553-aec9-835e5b724bb4" transform="{transform}" printable="1"/>
 </build>
</model>
'''
    sub = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" {NS}>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
  <object id="1" p:UUID="00010000-81cb-4c03-9d28-80fed5dfa1dc" type="model">
{mesh_xml(body)}  </object>
  <object id="2" p:UUID="00020000-81cb-4c03-9d28-80fed5dfa1dc" type="model">
{mesh_xml(qr)}  </object>
 </resources>
 <build/>
</model>
'''
    model_settings = f'''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="3">
    <metadata key="name" value="cheese_wedge"/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{len(body.faces) + len(qr.faces)}"/>
{part_settings(1, "cheese_body", 1, body)}{part_settings(2, "cheese_qr", 2, qr)}  </object>
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
        im = Image.open(os.path.join(image_dir, "wedge_iso.png")).convert("RGB")
        s = min(im.size); im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
        b = io.BytesIO(); im.resize((size, size), Image.LANCZOS).save(b, "PNG"); return b.getvalue()

    out = os.path.join(stl_dir, "cheese_wedge.3mf")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("3D/_rels/3dmodel.model.rels", model_rels)
        z.writestr("3D/Objects/object_1.model", sub)
        z.writestr("Metadata/model_settings.config", model_settings)
        z.writestr("Metadata/project_settings.config", json.dumps(project_settings(), indent=4))
        z.writestr("Metadata/plate_1.png", png(512))
        z.writestr("Metadata/plate_1_small.png", png(128))
    print(f"wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB)")

if __name__ == "__main__":
    d = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "stl")
    build(d, sys.argv[2] if len(sys.argv) > 2 else (os.path.join(HERE, "images") if d == os.path.join(HERE, "stl") else d))
