"""Stage rules include catalog classes and suppress inherited-only duplicates."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"),
    str(Path(os.environ.get("TOOLCHAIN_DIR", ROOT.parent / "usdaeco-toolchain")) / "tools")]
from usdaeco_buildup import validators as legacy
from usdaeco_check.validation import register_stage_validator, wrap_legacy
from . import validatorTokens as tokens

register_stage_validator(tokens.ARRAY_LENGTHS_CHECKER,
    wrap_legacy(tokens.ARRAY_LENGTHS_CHECKER, lambda stage: legacy._lengths(stage, None)))
register_stage_validator(tokens.TOTAL_MISMATCH_CHECKER,
    wrap_legacy(tokens.TOTAL_MISMATCH_CHECKER, lambda stage: legacy._total(stage, None)))
