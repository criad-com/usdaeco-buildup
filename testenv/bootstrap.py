"""Register resources before constructing either USD registry singleton."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
from usdaeco_buildup import register_plugins
register_plugins()
