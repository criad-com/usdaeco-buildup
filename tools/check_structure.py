#!/usr/bin/env python3
"""Run the family structure rules with the preserved catalog applicability."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
KIT = Path(os.environ.get("TOOLCHAIN_DIR", ROOT.parent / "usdaeco-toolchain"))
sys.path.insert(0, str(KIT / "tools"))
from usdaeco_buildup import core_root
from usdaeco_buildup.structure import check_structure
from usdaeco_check.structure import print_results

if __name__ == "__main__":
    deps = [os.environ.get("CORE_PLUGIN_DIR", core_root() / "out/plugins/usdAeco/resources")]
    raise SystemExit(print_results(list(check_structure(ROOT, deps))))
