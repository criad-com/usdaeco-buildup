"""The preview is a removable derived representation of unchanged drivers."""
import os
import subprocess
import sys

import pytest
from pxr import Usd, UsdGeom
from usdaeco_buildup import ROOT, layers_of


def preview_contract(path="usdAecoBuildUp/examples/minimal.usda"):
    stage = Usd.Stage.Open(str(ROOT / path))
    occurrence = stage.GetPrimAtPath("/Example")
    assert occurrence.HasAPI("AecoElementAPI")
    assert occurrence.GetAttribute("aeco:class:ifc:code").Get() == "IfcWall"
    assert str(occurrence.GetInherits().GetAllDirectInherits()[0]) == "/_TypeCatalog/LayeredSection"
    rows = layers_of(occurrence)
    gprims = [p for p in stage.Traverse() if p.IsA(UsdGeom.Gprim)]
    assert len(gprims) == 3
    assert all(p.IsA(UsdGeom.Cube) and p.HasAPI("AecoDerivedGeometryAPI") and
               p.GetAttribute("aeco:derived:source").Get() == occurrence.GetAttribute("aeco:id").Get() and
               p.GetAttribute("aeco:derived:role").Get() == "proxy" and
               UsdGeom.Imageable(p).ComputePurpose() == "proxy" for p in gprims)
    offset = 0
    for prim, row in zip(gprims, rows):
        assert prim.GetParent() == occurrence
        assert prim.GetAttribute("size").Get() == 1
        assert prim.GetAttribute("xformOp:scale").Get()[0] == pytest.approx(row[0])
        assert prim.GetAttribute("xformOp:translate").Get()[0] == pytest.approx(offset + row[0] / 2)
        assert prim.GetDisplayName() == row[2]
        assert prim.GetAttribute("primvars:displayColor").HasAuthoredValueOpinion()
        assert all(spec.layer.realPath.endswith("section.derived.usda") for spec in prim.GetPrimStack())
        offset += row[0]
    for layer in stage.GetLayerStack():
        if layer.realPath.endswith(".derived.usda"):
            stage.MuteLayer(layer.identifier)
    assert layers_of(occurrence) == rows
    assert not occurrence.GetAttribute("aeco:buildUp:totalThickness").HasAuthoredValueOpinion()
    assert not any(p.IsA(UsdGeom.Gprim) for p in stage.Traverse())
    return True


@pytest.mark.parametrize("path", ["examples/minimal.usda", "usdAecoBuildUp/examples/minimal.usda"])
def test_preview_layers(path):
    assert preview_contract(path)


def test_vanilla_visible_section():
    environment = {key: value for key, value in os.environ.items()
                   if key not in ("PYTHONPATH", "PXR_PLUGINPATH_NAME", "PXR_AR_DEFAULT_SEARCH_PATH")}
    probe = subprocess.run([sys.executable, "-I", "-c", '''
import sys
from pxr import Plug, Usd, UsdGeom
for path in sys.argv[1:]:
    stage = Usd.Stage.Open(path)
    assert stage and not stage.GetCompositionErrors()
    bodies = [prim for prim in stage.Traverse() if prim.IsA(UsdGeom.Gprim)]
    assert len(bodies) == 3
    assert all(prim.IsA(UsdGeom.Cube) and UsdGeom.Imageable(prim).ComputePurpose() == "proxy" for prim in bodies)
    bounds = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "proxy", "render"])
    assert not bounds.ComputeWorldBound(stage.GetDefaultPrim()).GetRange().IsEmpty()
assert not any(p.name.startswith("usdAeco") for p in Plug.Registry().GetAllPlugins())
''', *[str(ROOT / p) for p in ("examples/minimal.usda", "usdAecoBuildUp/examples/minimal.usda",
                               "examples/datacentre/result/example.usdc")]],
                           env=environment, capture_output=True, text=True)
    assert probe.returncode == 0, probe.stderr


def test_section_regenerates_from_drivers(tmp_path):
    from usdaeco_buildup.example import derive_section
    stage = Usd.Stage.Open(str(ROOT / "examples/minimal.usda"))
    stage.SetEditTarget(stage.GetSessionLayer())
    occurrence = stage.GetPrimAtPath("/Example")
    occurrence.GetAttribute("aeco:buildUp:thicknesses").Set([.03, .20, .01])
    before = stage.GetSessionLayer().ExportToString()
    target = tmp_path / "section.derived.usda"
    derive_section(stage, target)
    assert stage.GetSessionLayer().ExportToString() == before
    derived = Usd.Stage.Open(str(target))
    body = derived.GetPrimAtPath("/Example/Layer3")
    assert body.GetAttribute("xformOp:translate").Get()[0] == pytest.approx(.235)
    assert body.GetAttribute("xformOp:scale").Get()[0] == pytest.approx(.01)
