"""Facility preservation, driver separation and defects on promoted catalogs."""
import json
from pathlib import Path

import pytest
from pxr import Sdf, Usd, UsdGeom
from usdaeco_buildup import ROOT, layers_of
from usdaeco_buildup.datacentre import census, hook, published_source, select_walls
from usdaeco_buildup.validators import validate_stage


@pytest.fixture
def facility(tmp_path):
    source, manifest = published_source()
    base = Usd.Stage.Open(str(source))
    layer = Sdf.Layer.CreateNew(str(tmp_path / 'example.usda'))
    layer.subLayerPaths = [str(ROOT / 'examples/datacentre/inputs/cameras.usda'), str(source)]
    stage = Usd.Stage.Open(layer)
    stage.SetDefaultPrim(stage.GetPrimAtPath(base.GetDefaultPrim().GetPath()))
    for key in ('upAxis', 'metersPerUnit', 'fallbackPrimTypes'):
        stage.SetMetadata(key, base.GetMetadata(key))
    findings = hook(stage, tmp_path)
    return stage, base, findings


def test_promotion_preserves_facility(facility):
    stage, base, findings = facility
    assert census(stage) == census(base) == published_source()[1]['counts']
    before, after = UsdGeom.XformCache(), UsdGeom.XformCache()
    for prim in base.TraverseAll():
        actual = stage.GetPrimAtPath(prim.GetPath())
        assert actual and actual.GetTypeName() == prim.GetTypeName()
        assert actual.IsActive() == prim.IsActive()
        assert actual.GetParent().GetPath() == prim.GetParent().GetPath()
        assert actual.GetAttribute('aeco:id').Get() == prim.GetAttribute('aeco:id').Get()
        if prim.IsA(UsdGeom.Xformable):
            assert before.GetLocalToWorldTransform(prim) == after.GetLocalToWorldTransform(actual)
    expected = json.loads((ROOT / 'examples/datacentre/expected/findings.json').read_text())
    assert findings == expected


def test_catalog_inheritance_and_derived_muting(facility):
    stage, base, _ = facility
    walls = [p for p in stage.Traverse() if p.HasAPI('AecoElementAPI') and p.HasAPI('AecoBuildUpAPI')]
    rows = {p.GetPath(): layers_of(p) for p in walls}
    assert len(rows) == 20
    for wall in walls:
        typ = stage.GetPrimAtPath(wall.GetInherits().GetAllDirectInherits()[0])
        assert typ.IsAbstract() and not typ.GetAttribute('aeco:id').Get()
        assert layers_of(typ) == layers_of(wall)
    derived, = [l for l in stage.GetLayerStack() if l.realPath.endswith('buildup.derived.usda')]
    stage.MuteLayer(derived.identifier)
    assert not any(p.GetName().startswith('BuildUpLayer') for p in stage.Traverse())
    for path, row in rows.items():
        wall = stage.GetPrimAtPath(path)
        assert layers_of(wall) == row
        assert not wall.GetAttribute('aeco:buildUp:totalThickness').HasAuthoredValueOpinion()
    presentation, = [l for l in stage.GetLayerStack() if l.realPath.endswith('presentation.usda')]
    stage.MuteLayer(presentation.identifier)
    for prim in base.Traverse():
        if prim.IsA(UsdGeom.Gprim):
            assert UsdGeom.Imageable(stage.GetPrimAtPath(prim.GetPath())).ComputeVisibility() == UsdGeom.Imageable(prim).ComputeVisibility()


def test_layer_body_dimensions_and_source(facility):
    stage, _, _ = facility
    bodies = [p for p in stage.Traverse() if p.GetName().startswith('BuildUpLayer')]
    assert len(bodies) == 20
    for body in bodies:
        wall = body.GetParent()
        row = layers_of(wall)[int(body.GetName().removeprefix('BuildUpLayer')) - 1]
        assert body.GetAttribute('aeco:derived:source').Get() == wall.GetAttribute('aeco:id').Get()
        assert not body.GetAttribute('aeco:id').Get()
        assert body.GetAttribute('aeco:derived:approx').Get() == 'defaultDims'
        assert UsdGeom.Imageable(body).ComputePurpose() == 'proxy'
        scale = body.GetAttribute('xformOp:scale').Get()
        assert scale[1] == pytest.approx(row[0])
        assert scale[0] == wall.GetAttribute('aeco:props:Qto_WallBaseQuantities:Length').Get()
        assert scale[2] == wall.GetAttribute('aeco:props:Qto_WallBaseQuantities:Height').Get()
        assert all(s.layer.realPath.endswith(('buildup.derived.usda', 'presentation.usda')) for s in body.GetPrimStack())


@pytest.mark.parametrize('attribute,value,error', [
    ('priorities', [50], 'BuildUpArrayLengths'),
    ('totalThickness', .9, 'BuildUpTotalMismatch'),
])
def test_promoted_catalog_defects(facility, attribute, value, error):
    stage, _, _ = facility
    assert not any(e.GetName() == error for e in validate_stage(stage))
    typ = next(p for p in stage.TraverseAll() if p.IsAbstract() and p.HasAPI('AecoBuildUpAPI'))
    stage.SetEditTarget(stage.GetSessionLayer())
    typ.GetAttribute('aeco:buildUp:' + attribute).Set(value)
    assert any(e.GetName() == error for e in validate_stage(stage))


def test_recipe_rejects_width_drift(facility):
    stage, _, _ = facility
    config = json.loads((ROOT / 'examples/datacentre/inputs/build-ups.json').read_text())
    config['recipes'][0]['thicknesses'][1] += .01
    with pytest.raises(ValueError, match='published wall width'):
        select_walls(stage, config)


def published_facility_contract():
    source, manifest = published_source()
    base = Usd.Stage.Open(str(source))
    stage = Usd.Stage.Open(str(ROOT / 'examples/datacentre/result/example.usdc'))
    assert stage and not stage.GetCompositionErrors()
    assert census(stage) == manifest['counts']
    for prim in base.Traverse():
        assert stage.GetPrimAtPath(prim.GetPath()), str(prim.GetPath())
    assert len([p for p in stage.Traverse() if p.HasAPI('AecoElementAPI') and p.HasAPI('AecoBuildUpAPI')]) == 20
    return True


def test_published_facility():
    assert published_facility_contract()
