#!/usr/bin/env python3
"""
Build horse_head.3mf: a Bambu Studio project with the model on an A1 plate
and the print settings already chosen.

    python3 tools/make_3mf.py            (run from the model folder, after build_horse.py)

The project selects Bambu's own system presets:

    printer   Bambu Lab A1 0.4 nozzle
    filament  Bambu PLA Basic @BBL A1
    process   0.16mm High Quality @BBL A1   (slow outer wall, gyroid infill)

and changes only the settings in PROCESS_CHANGES.  The full preset values are
written too, as Bambu Studio expects, but the project also lists which keys
were changed ("different_settings_to_system").  On opening, Bambu Studio takes
every other value from the presets installed on your computer, so the file
doesn't go stale when Bambu updates its profiles.

tools/bambu_profiles/*.json are those three presets with their inheritance
resolved, taken from the Bambu Studio repository (resources/profiles/BBL).
"""
import io, json, os, sys, zipfile, datetime
import numpy as np, trimesh
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PRINTER = "Bambu Lab A1 0.4 nozzle"
FILAMENT = "Bambu PLA Basic @BBL A1"
PROCESS = "0.16mm High Quality @BBL A1"
# What this model needs on top of the High Quality preset.
PROCESS_CHANGES = {
    "wall_loops": "3",                 # stronger shell around the hollow jaw and the hinge
    "wall_generator": "arachne",       # smooth variable-width walls in the thin ears and jaw
    "seam_position": "back",           # the plate is rotated so "back" is the back of the neck, under the mane
    "brim_type": "no_brim",            # the plinth is wide enough
    "enable_support": "0",             # the model carries its own support pillar
}
APP_VERSION = "02.00.00.95"           # a 2.x version, so current Bambu Studio opens it without a "newer version" prompt
FILAMENT_COLOUR = "#E8D3B0"
BED = 256.0
TITLE = "Horse Head with a Secret Compartment"

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
    for part in (printer, process, filament):
        for k, v in part.items():
            if k not in META: cfg[k] = v
    for k, v in PROCESS_CHANGES.items():
        cfg[k] = v                    # (brim_type is not in the A1 presets: they use Bambu's built-in default, auto brim)
    cfg.update({
        "version": APP_VERSION, "name": "project_settings", "from": "project",
        "print_settings_id": PROCESS,
        "printer_settings_id": PRINTER,
        "filament_settings_id": [FILAMENT],
        "filament_ids": [filament["filament_id"]],
        "filament_colour": [FILAMENT_COLOUR],
        "filament_map": ["1"],
        "filament_self_index": ["1"],
        "print_compatible_printers": process.get("compatible_printers", [PRINTER]),
        "curr_bed_type": "Textured PEI Plate",
        # one entry per preset: print, each filament, printer.  The filament and
        # printer entries name a key whose value is unchanged, so those presets
        # are refreshed from the installed system presets and load unmodified.
        "different_settings_to_system": [";".join(sorted(k for k, v in PROCESS_CHANGES.items() if process.get(k) != v)),
                                         "filament_type", "printable_height"],
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

def build():
    m = trimesh.load(os.path.join(ROOT, "stl", "horse_head.stl"))
    # place on the A1 plate: turned 180 degrees so the face looks toward the front of the printer
    lo, hi = m.bounds
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    tx, ty, tz = BED / 2 + cx, BED / 2 + cy, -lo[2]       # after (x, y) -> (-x, -y)
    transform = f"-1 0 0 0 -1 0 0 0 1 {tx:.4f} {ty:.4f} {tz:.4f}"
    today = datetime.date.today().isoformat()

    model = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" {NS}>
 <metadata name="Application">BambuStudio-{APP_VERSION}</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">{TITLE}</metadata>
 <metadata name="Description">Print-in-place horse bust with a hinged jaw and a hidden compartment.</metadata>
 <metadata name="CreationDate">{today}</metadata>
 <metadata name="ModificationDate">{today}</metadata>
 <resources>
  <object id="2" p:UUID="00000001-61cb-4c03-9d28-80fed5dfa1dc" type="model">
   <components>
    <component p:path="/3D/Objects/object_1.model" objectid="1" p:UUID="00010000-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
   </components>
  </object>
 </resources>
 <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">
  <item objectid="2" p:UUID="00000002-b1ec-4553-aec9-835e5b724bb4" transform="{transform}" printable="1"/>
 </build>
</model>
'''
    sub = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" {NS}>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
  <object id="1" p:UUID="00010000-81cb-4c03-9d28-80fed5dfa1dc" type="model">
{mesh_xml(m)}  </object>
 </resources>
 <build/>
</model>
'''
    model_settings = f'''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="2">
    <metadata key="name" value="horse_head"/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{len(m.faces)}"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="horse_head"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="horse_head.stl"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="0"/>
      <metadata key="source_offset_y" value="0"/>
      <metadata key="source_offset_z" value="0"/>
      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
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
        im = Image.open(os.path.join(ROOT, "images", "horse_closed.png")).convert("RGB")
        s = min(im.size); im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
        b = io.BytesIO(); im.resize((size, size), Image.LANCZOS).save(b, "PNG"); return b.getvalue()

    out = os.path.join(ROOT, "horse_head.3mf")
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
    print(f"wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB), model at plate ({tx:.1f}, {ty:.1f})")

if __name__ == "__main__":
    build()
