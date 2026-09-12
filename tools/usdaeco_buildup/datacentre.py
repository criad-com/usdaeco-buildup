"""Promote classified office walls without replacing facility referents."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdValidation
from . import ROOT, ARRAYS, layers_of
from .validators import register, require_core_validators, validate_stage

EXAMPLE = ROOT / 'examples/datacentre'


def published_source():
    root = Path(os.environ.get('AECO_DATACENTRE_ROOT', ROOT.parent / 'usdaeco-datacentre'))
    path = Path(os.environ.get('AECO_DATACENTRE_STAGE', root / 'dist/clash/dc.usda')).resolve()
    manifest = json.loads(path.with_name('dc.manifest.json').read_text())
    if (manifest['facility'], manifest['variant']) != ('demo-datacentre-01', 'clash'):
        raise ValueError('Expected the published demo-datacentre-01 clash variant')
    for name, record in manifest['layers'].items():
        data = (path.parent / name).read_bytes()
        if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('Source layer differs from dc.manifest.json: ' + name)
    return path, manifest


def ancestors(prim):
    parent = prim.GetParent()
    while parent and not parent.IsPseudoRoot():
        yield parent
        parent = parent.GetParent()


def census(stage):
    prims = list(stage.Traverse())
    elements = [p for p in prims if p.HasAPI('AecoElementAPI')]
    spatial = {'AecoSite', 'AecoFacility', 'AecoFacilityPart', 'AecoLevel', 'AecoSpace'}
    return dict(elements=len(elements), levels=sum(p.GetTypeName() == 'AecoLevel' for p in prims),
                spaces=sum(p.GetTypeName() == 'AecoSpace' for p in prims),
                ports=sum(p.GetTypeName() == 'AecoPort' for p in prims),
                meshes=sum(p.IsA(UsdGeom.Mesh) for p in prims),
                unclassified=sum((p.GetAttribute('aeco:class:ifc:code').Get() or '').split('.')[0]
                                 in ('', 'IfcBuildingElementProxy') for p in elements),
                unparented=sum(not any(a.GetTypeName() in spatial for a in ancestors(p)) for p in elements))


def select_walls(stage, config):
    """Use IFC classification, model and placement; WC is its spatial boundary."""
    cache = UsdGeom.XformCache()
    wc, = [p for p in stage.Traverse() if p.GetTypeName() == 'AecoSpace' and p.GetName() == 'WC']
    extent = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['guide']).ComputeWorldBound(
        wc.GetChild('Extent')).ComputeAlignedRange()
    lo, hi = extent.GetMin(), extent.GetMax()
    xmin, ymin, xmax, ymax = config['office_envelope_xy']
    selected = []
    for prim in stage.Traverse():
        code = prim.GetAttribute('aeco:class:ifc:code').Get() or ''
        if not prim.HasAPI('AecoElementAPI') or not code.startswith('IfcWall.'):
            continue
        length = prim.GetAttribute('aeco:props:Qto_WallBaseQuantities:Length').Get()
        height = prim.GetAttribute('aeco:props:Qto_WallBaseQuantities:Height').Get()
        width = prim.GetAttribute('aeco:props:Qto_WallBaseQuantities:Width').Get()
        if not all(v and v > 0 for v in (length, height, width)):
            raise ValueError('Wall quantities are incomplete: ' + str(prim.GetPath()))
        matrix = cache.GetLocalToWorldTransform(prim)
        mid = matrix.Transform(Gf.Vec3d(length / 2, 0, 0))
        if not (xmin <= mid[0] <= xmax and ymin <= mid[1] < ymax):
            continue
        if prim.GetAttribute('aeco:props:Pset_WallCommon:IsExternal').Get():
            continue
        model = prim.GetAttribute('aeco:type:model').Get()
        recipe = next((r for r in config['recipes'] if r['source_model'] == model
                       and r['ifc_code'] == code and r['name'] != 'WcLining'), None)
        if recipe is None:
            raise ValueError('Office wall classification has no recipe')
        on_wc = (abs(mid[2] - lo[2]) < 1e-5 and lo[0] - 1e-5 <= mid[0] <= hi[0] + 1e-5
                 and lo[1] - 1e-5 <= mid[1] <= hi[1] + 1e-5
                 and min(abs(mid[0]-lo[0]), abs(mid[0]-hi[0]),
                         abs(mid[1]-lo[1]), abs(mid[1]-hi[1])) < 1e-5)
        if on_wc and code == 'IfcWall.PARTITIONING':
            recipe = next(r for r in config['recipes'] if r['name'] == 'WcLining')
        if abs(sum(recipe['thicknesses']) - width) > 1e-8:
            raise ValueError('Recipe total differs from the published wall width')
        selected.append((prim, recipe, length, height))
    return sorted(selected, key=lambda row: str(row[0].GetPath()))


def new_overlay(stage, out, name):
    layer = Sdf.Layer.CreateNew(str(out / name))
    stage.GetRootLayer().subLayerPaths.insert(0, name)
    return layer


def mark(prim, source):
    prim.ApplyAPI('AecoDerivedGeometryAPI')
    for name, value, value_type in (
        ('source', source.GetAttribute('aeco:id').Get(), Sdf.ValueTypeNames.String),
        ('role', 'proxy', Sdf.ValueTypeNames.Token),
        ('approx', 'defaultDims', Sdf.ValueTypeNames.Token),
        ('stamp', 'aeco-buildup 0.2.4 gross rectangular preview', Sdf.ValueTypeNames.String),
    ):
        prim.CreateAttribute('aeco:derived:' + name, value_type, custom=False).Set(value)


def promote(stage, out, selected):
    drivers = new_overlay(stage, out, 'buildup.drivers.usda')
    catalog = stage.GetDefaultPrim().GetPath().AppendChild('_TypeCatalog')
    types = {}
    with Usd.EditContext(stage, drivers):
        for wall, recipe, _, _ in selected:
            path = catalog.AppendChild('OfficeBuildUp_' + recipe['name'])
            if recipe['name'] not in types:
                original, = wall.GetInherits().GetAllDirectInherits()
                typ = stage.CreateClassPrim(path)
                typ.GetInherits().AddInherit(original)
                typ.ApplyAPI('AecoBuildUpAPI')
                typ.SetDisplayName(recipe['label'])
                for key, kind in zip(ARRAYS, (Sdf.ValueTypeNames.DoubleArray, Sdf.ValueTypeNames.TokenArray,
                                              Sdf.ValueTypeNames.StringArray, Sdf.ValueTypeNames.IntArray)):
                    typ.CreateAttribute('aeco:buildUp:' + key, kind, custom=False).Set(recipe[key])
                types[recipe['name']] = path
            wall.GetInherits().SetInherits([path])
    drivers.Save()
    return types


def derive(stage, out, selected, types, per_recipe):
    layer = new_overlay(stage, out, 'buildup.derived.usda')
    chosen = []
    counts = Counter()
    with Usd.EditContext(stage, layer):
        for path in types.values():
            typ = stage.GetPrimAtPath(path)
            typ.CreateAttribute('aeco:buildUp:totalThickness', Sdf.ValueTypeNames.Double,
                                custom=False).Set(sum(row[0] for row in layers_of(typ)))
        for wall, recipe, length, height in selected:
            if counts[recipe['name']] >= per_recipe:
                continue
            counts[recipe['name']] += 1
            chosen.append(wall.GetPath())
            rows = layers_of(wall)
            sign = 1
            if recipe['name'] == 'WcLining':
                wc, = [p for p in stage.Traverse() if p.GetTypeName() == 'AecoSpace' and p.GetName() == 'WC']
                center = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['guide']).ComputeWorldBound(
                    wc.GetChild('Extent')).ComputeAlignedRange().GetMidpoint()
                local = UsdGeom.XformCache().GetLocalToWorldTransform(wall).GetInverse().Transform(center)
                sign = 1 if local[1] > 0 else -1
            offset = -sum(row[0] for row in rows) / 2
            for index, row in enumerate(rows):
                cube = UsdGeom.Cube.Define(stage, wall.GetPath().AppendChild(f'BuildUpLayer{index + 1}'))
                cube.CreateSizeAttr(1)
                cube.AddTranslateOp().Set((length / 2, sign * (offset + row[0] / 2), height / 2))
                cube.AddScaleOp().Set((length, row[0], height))
                cube.CreatePurposeAttr('proxy')
                cube.CreateDisplayColorAttr([recipe['layer_colors'][index]])
                cube.GetPrim().SetDisplayName(row[2])
                mark(cube.GetPrim(), wall)
                offset += row[0]
    layer.Save()
    return chosen


def present(stage, out, selected, chosen):
    """Retain the facility; lift only roof/ceiling visibility for a cutaway."""
    layer = new_overlay(stage, out, 'presentation.usda')
    colors = {wall.GetPath(): recipe['color'] for wall, recipe, _, _ in selected}
    hidden = Counter()
    with Usd.EditContext(stage, layer):
        for prim in stage.Traverse():
            if not prim.IsA(UsdGeom.Gprim):
                continue
            parent = prim.GetParent()
            codes = [a.GetAttribute('aeco:class:ifc:code').Get() or '' for a in (parent, *ancestors(parent))]
            cover = any(c.startswith(('IfcRoof', 'IfcSlab.ROOF', 'IfcCovering.CEILING')) for c in codes)
            office_facade = (parent.GetAttribute('aeco:props:Pset_WallCommon:IsExternal').Get()
                             and UsdGeom.XformCache().GetLocalToWorldTransform(parent).ExtractTranslation()[1] < 0)
            office_floor = any(c == 'IfcSlab.FLOOR' for c in codes) and any(a.GetName() == 'L01_Office' for a in ancestors(prim))
            if office_facade or office_floor:
                UsdGeom.Imageable(prim).CreateVisibilityAttr('invisible')
                hidden['office_facade_and_upper_floor_bodies'] += 1
            if cover:
                UsdGeom.Imageable(prim).CreateVisibilityAttr('invisible')
                hidden['roof_and_ceiling_bodies'] += 1
            if parent.GetPath() in colors:
                # The facility mesh retains its openings; representatives show gross layers.
                UsdGeom.Gprim(prim).CreateDisplayColorAttr([colors[parent.GetPath()]])
                prim.CreateRelationship('material:binding').SetTargets([])
                if parent.GetPath() in chosen and prim.GetName() == 'Geom':
                    UsdGeom.Imageable(prim).CreateVisibilityAttr('invisible')
        camera = UsdGeom.Camera(stage.GetPrimAtPath('/Renders/overview'))
        camera.MakeMatrixXform().Set(Gf.Matrix4d().SetLookAt(
            Gf.Vec3d(86, -104, 98), Gf.Vec3d(32, 9, 1), Gf.Vec3d(0, 0, 1)).GetInverse())
        camera.CreateProjectionAttr('orthographic')
        camera.CreateHorizontalApertureAttr(1080)
        camera.CreateVerticalApertureAttr(675)
        camera.CreateClippingRangeAttr(Gf.Vec2f(.1, 1000))
    layer.Save()
    return dict(hidden)


def validation_summary(stage):
    register()
    core = require_core_validators()
    if len(core) != 8:
        raise RuntimeError('Expected all eight pinned core validators')
    issues = validate_stage(stage, include_core=True)
    if any(e.GetType() == UsdValidation.ValidationErrorType.Error for e in issues):
        raise ValueError('Facility validation has errors: ' + ', '.join(e.GetName() for e in issues))
    return {'name': 'Validation', 'buildup_rules': 2, 'core_rules': len(core), 'errors': 0,
            'findings': [{'name': name, 'count': count} for name, count in sorted(Counter(e.GetName() for e in issues).items())]}


def hook(stage, out):
    source, manifest = published_source()
    base = Usd.Stage.Open(str(source))
    actual = census(base)
    if actual != manifest['counts']:
        raise ValueError('Published census differs from dc.manifest.json')
    config = json.loads((EXAMPLE / 'inputs/build-ups.json').read_text())
    selected = select_walls(stage, config)
    if {r['name'] for _, r, _, _ in selected} != {r['name'] for r in config['recipes']}:
        raise ValueError('Not all three build-up recipes have office occurrences')
    types = promote(stage, out, selected)
    chosen = derive(stage, out, selected, types, config['representatives_per_recipe'])
    review = present(stage, out, selected, chosen)
    write_study(stage, out, selected, chosen)
    stats = Counter(r['name'] for _, r, _, _ in selected)
    return [{'name': 'PublishedCounts', 'counts': actual, 'source_prims': len(list(base.TraverseAll()))},
            {'name': 'BuildUpPromotion', 'types': len(types), 'walls': len(selected), 'by_recipe': dict(stats)},
            {'name': 'DerivedLayers', 'walls': len(chosen),
             'bodies': sum(len(layers_of(stage.GetPrimAtPath(p))) for p in chosen)},
            {'name': 'FacilityCutaway', **review}, validation_summary(stage)]


def write_study(stage, out, selected, chosen):
    """An owned exploded WC section; these opinions never enter the facility view."""
    wall, recipe, length, height = next(row for row in selected
        if row[1]['name'] == 'WcLining' and row[0].GetPath() in chosen)
    layer = Sdf.Layer.CreateNew(str(out / 'exploded.usda'))
    layer.subLayerPaths = list(stage.GetRootLayer().subLayerPaths)
    study = Usd.Stage.Open(layer)
    for key in ('upAxis', 'metersPerUnit', 'fallbackPrimTypes'):
        study.SetMetadata(key, stage.GetMetadata(key))
    study.SetDefaultPrim(study.GetPrimAtPath(stage.GetDefaultPrim().GetPath()))
    bodies = []
    for prim in study.Traverse():
        if not prim.IsA(UsdGeom.Gprim):
            continue
        if prim.GetParent().GetPath() == wall.GetPath() and prim.GetName().startswith('BuildUpLayer'):
            index = int(prim.GetName().removeprefix('BuildUpLayer')) - 1
            prim.GetAttribute('xformOp:translate').Set((length / 2, index * .38, height / 2))
            prim.GetAttribute('xformOp:scale').Set((1.4, recipe['thicknesses'][index], 1.8))
            UsdGeom.Gprim(prim).CreateDisplayColorAttr([recipe['layer_colors'][index]])
            bodies.append(prim)
        else:
            UsdGeom.Imageable(prim).CreateVisibilityAttr('invisible')
    bounds = Gf.Range3d()
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['proxy', 'render'])
    for prim in bodies:
        bounds.UnionWith(cache.ComputeWorldBound(prim).ComputeAlignedRange())
    camera = UsdGeom.Camera.Define(study, '/Renders/exploded')
    matrix = UsdGeom.XformCache().GetLocalToWorldTransform(wall)
    direction = matrix.TransformDir(Gf.Vec3d(1.5, 2, 1)).GetNormalized()
    center = bounds.GetMidpoint()
    camera.MakeMatrixXform().Set(Gf.Matrix4d().SetLookAt(
        center + direction * 9, center, Gf.Vec3d(0, 0, 1)).GetInverse())
    camera.CreateFocalLengthAttr(45)
    camera.CreateHorizontalApertureAttr(24)
    camera.CreateVerticalApertureAttr(15)
    camera.CreateClippingRangeAttr(Gf.Vec2f(.1, 100))
    layer.Save()
