"""The minimal wall occurrence and its illustrative derived section bodies."""
import shutil

from . import ROOT, layers_of

# Version of the unchanged derivation; packaging-only releases retain its stamp.
SECTION_DERIVATION_VERSION = "0.2.2"


def derive_section(stage, target):
    """Write proxy Cubes at the resolved layer offsets; never edit drivers."""
    from pxr import Sdf, Usd, UsdGeom
    occurrence = stage.GetPrimAtPath("/Example")
    rows = layers_of(occurrence)
    source_id = occurrence.GetAttribute("aeco:id").Get()
    if len(rows) != 3 or not source_id:
        raise ValueError("the illustration requires the three-layer wall occurrence")
    layer = Sdf.Layer.CreateAnonymous()
    derived = Usd.Stage.Open(layer)
    offset = 0
    colors = [(0.55, 0.68, 0.80), (0.65, 0.30, 0.16), (0.83, 0.85, 0.80)]
    # Cutbacks reveal all layers; length and heights are illustrative dimensions.
    for index, (width, function, material, priority) in enumerate(rows):
        cube = UsdGeom.Cube.Define(derived, f"/Example/Layer{index + 1}")
        cube.CreateSizeAttr(1)
        height = (1.0, 0.90, 0.72)[index]
        cube.AddTranslateOp().Set((offset + width / 2, .35, height / 2))
        cube.AddScaleOp().Set((width, .7, height))
        cube.CreatePurposeAttr("proxy")
        cube.CreateDisplayColorAttr([colors[index]])
        prim = cube.GetPrim()
        prim.SetDisplayName(material)
        prim.ApplyAPI("AecoDerivedGeometryAPI")
        for name, value, value_type in (
            ("source", source_id, Sdf.ValueTypeNames.String),
            ("role", "proxy", Sdf.ValueTypeNames.Token),
            ("approx", "defaultDims", Sdf.ValueTypeNames.Token),
            ("stamp", f"aeco-buildup {SECTION_DERIVATION_VERSION} section illustration", Sdf.ValueTypeNames.String),
        ):
            prim.CreateAttribute("aeco:derived:" + name, value_type, custom=False).Set(value)
        offset += width
    target.parent.mkdir(parents=True, exist_ok=True)
    layer.Export(str(target))
    return rows


def publish_section(stage, out):
    """Archive this example's own layers and regenerate its derived opinions."""
    from pxr import Sdf, Usd
    module = out / "module"
    shutil.copytree(ROOT / "usdAecoBuildUp/examples", module)
    rows = derive_section(stage, module / "data/section.derived.usda")
    layer = Sdf.Layer.CreateAnonymous()
    derived = Usd.Stage.Open(layer)
    catalog = derived.OverridePrim("/_TypeCatalog/LayeredSection")
    catalog.CreateAttribute("aeco:buildUp:totalThickness", Sdf.ValueTypeNames.Double,
                            custom=False).Set(sum(row[0] for row in rows))
    layer.Export(str(module / "data/layered_type.derived.usda"))
    root = stage.GetRootLayer()
    root.subLayerPaths = [*root.subLayerPaths[:-1], "module/minimal.usda"]
    return []
