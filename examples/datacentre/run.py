#!/usr/bin/env python3
"""Publish the minimal section through the shared example contract."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from usdaeco_buildup import register_plugins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if any(os.environ.get(key) for key in ("AECO_DATACENTRE_ROOT", "AECO_DATACENTRE_STAGE")):
        parser.error("this library example requires minimal mode; unset data-centre source overrides")
    os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    register_plugins()
    from usdaeco_buildup.validators import require_core_validators, KEYWORD
    require_core_validators()
    from usdaeco_buildup.example import publish_section
    from usdaeco_check.example import run_example
    run_example(Path(__file__).parent, publish_section,
                minimal=ROOT / "usdAecoBuildUp/examples/minimal.usda",
                keywords=[KEYWORD, "UsdAecoValidators", "UsdCoreValidators"],
                publish=args.publish)


if __name__ == "__main__":
    main()
