#!/usr/bin/env python3
"""Derive the illustrative wall-section layer, then render it with the shared kit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
KIT = Path(os.environ.get("TOOLCHAIN_DIR", ROOT.parent / "usdaeco-toolchain"))
sys.path[:0] = [str(ROOT / "tools"), str(KIT / "tools")]


def derive(target):
    from usdaeco_buildup import register_plugins
    register_plugins()
    from pxr import Usd
    from usdaeco_buildup.example import derive_section
    stage = Usd.Stage.Open(str(ROOT / "usdAecoBuildUp/examples/minimal.usda"))
    return derive_section(stage, target)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true", help="Refresh committed preview layers and image")
    args = parser.parse_args(argv)
    output = ROOT / "out/preview"
    output.mkdir(parents=True, exist_ok=True)
    print("== stage: derive section illustration", flush=True)
    derived = output / "section.derived.usda"
    rows = derive(derived)
    from pxr import Sdf
    preview = Sdf.Layer.CreateAnonymous()
    preview.subLayerPaths = [str(derived), str(ROOT / "usdAecoBuildUp/examples/minimal.usda")]
    preview.Export(str(output / "preview.usda"))
    from usdaeco_render import render
    recorder = shutil.which("usdrecord") or str(Path(sys.executable).with_name("usdrecord"))
    print("== stage: render", flush=True)
    records = render(output / "preview.usda", output=output / "renders",
                     executable=recorder, purposes="guide,proxy,render")
    if args.publish:
        shutil.copyfile(derived, ROOT / "usdAecoBuildUp/examples/data/section.derived.usda")
        destination = ROOT / "usdAecoBuildUp/userDoc/usdAecoBuildUpExample.png"
        shutil.copyfile(output / "renders/usdAecoBuildUpExample.png", destination)
        records[0]["path"] = "userDoc/" + destination.name
        manifest = {
            "source": "examples/minimal.usda",
            "drivers_sha256": hashlib.sha256((ROOT / "usdAecoBuildUp/examples/data/layered_type.drivers.usda").read_bytes()).hexdigest(),
            "purposes": ["guide", "proxy", "render"],
            "layers": len(rows), "total_thickness_m": sum(row[0] for row in rows),
            "renders": records,
        }
        (destination.parent / "render.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for record in records:
        print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
