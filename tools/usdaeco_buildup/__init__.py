"""Queries and dependency registration for usdAecoBuildUp."""
import os
from pathlib import Path
import sys

__version__ = "0.2.3"
ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = (ROOT / "usdAecoBuildUp" if (ROOT / "usdAecoBuildUp/schema.usda").is_file()
              else ROOT / "plugins/usdAecoBuildUp/resources")
VALIDATOR_DIR = (ROOT / "usdAecoBuildUpValidators" if (ROOT / "usdAecoBuildUpValidators").is_dir()
                 else ROOT / "python/usdAecoBuildUpValidators")
APIS = ("AecoBuildUpAPI",)
ARRAYS = ("thicknesses", "functions", "materials", "priorities")
FUNCTIONS = ("structure", "substrate", "insulation", "finish", "membrane", "other")
SIZE_TOLERANCE = 1e-8  # SI metres


def core_root():
    return Path(os.environ.get("AECO_CORE_ROOT", os.environ.get(
        "CORE_DIR", ROOT.parent / "usdaeco-core")))


def register_plugins(plugin_dir=None, extra=()):
    """Register the full closure before constructing a stage or SchemaRegistry.

    Additional downstream resource paths may be supplied in dependency order.
    The shared kit rejects missing/old dependencies and duplicate plugin copies.
    """
    kit = Path(os.environ.get("TOOLCHAIN_DIR", ROOT.parent / "usdaeco-toolchain"))
    if str(kit / "tools") not in sys.path:
        sys.path.insert(0, str(kit / "tools"))
    from usdaeco_check import plugin_requires
    from pxr import Plug
    sys.path[:0] = [str(VALIDATOR_DIR.parent), str(core_root() / "tools"), str(core_root())]
    paths = [os.environ.get("CORE_PLUGIN_DIR", core_root() / "out/plugins/usdAeco/resources"),
             plugin_dir or os.environ.get("BUILDUP_PLUGIN_DIR", SCHEMA_DIR),
             *extra]
    result = plugin_requires(paths)
    if not result:
        raise RuntimeError(result.detail)
    core = Plug.Registry().GetPluginWithName("usdAeco")
    if "aecoDerived" not in core.metadata.get("SdfMetadata", {}):
        raise RuntimeError("usdAeco must register aecoDerived property metadata")
    Plug.Registry().RegisterPlugins(str(VALIDATOR_DIR))
    Plug.Registry().RegisterPlugins(str(core_root() / "usdAecoValidators"))
    return Plug.Registry().GetPluginWithName("usdAecoBuildUp")


def layers_of(type_prim):
    """Ordered (thickness_m, function, material, priority) tuples.

    Missing API returns []; mismatched arrays raise ValueError instead of
    silently dropping layers through zip. Resolved inherited values work too.
    """
    if not type_prim or not type_prim.HasAPI("AecoBuildUpAPI"):
        return []
    arrays = [list(type_prim.GetAttribute("aeco:buildUp:" + n).Get() or []) for n in ARRAYS]
    if len({len(a) for a in arrays}) != 1:
        raise ValueError("Build-up arrays must have equal lengths")
    return list(zip(*arrays))
