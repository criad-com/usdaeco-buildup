#!/usr/bin/env python3
"""Build and verify the library; print N checks, M failed."""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
KIT = Path(os.environ.get("TOOLCHAIN_DIR", ROOT.parent / "usdaeco-toolchain"))
sys.path[:0] = [str(ROOT / "tools"), str(KIT / "tools"), str(ROOT / "testenv")]
from usdaeco_check import Report
from usdaeco_buildup import APIS, core_root, layers_of, register_plugins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core-plugin')
    parser.add_argument('--plugin')
    parser.add_argument('--report', type=Path)
    parser.add_argument("--profile", type=Path, default=ROOT / "conformance/profiles/buildup.json",
                        help="Severity overlay for example conformance; seeded contract probes retain default grades")
    args = parser.parse_args()
    if args.core_plugin: os.environ['CORE_PLUGIN_DIR'] = args.core_plugin
    print("== stage: build", flush=True)
    report = Report()
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    environment = {**os.environ, "PYTHON": sys.executable}
    environment.pop("PYTHONPATH", None)
    environment.pop("PXR_PLUGINPATH_NAME", None)
    with (out / "build.log").open("w") as log:
        build = subprocess.run(["bash", str(ROOT / "build.sh"), "--install-root", str(out)],
                               env=environment, stdout=log, stderr=subprocess.STDOUT)
    if not report.check("build codeless install layout", build.returncode == 0, "out/build.log"):
        return report.finish()
    register_plugins(args.plugin or out / "plugins/usdAecoBuildUp/resources")
    sys.path.insert(0, str(core_root() / 'tools'))
    from pxr import Plug, Sdf, Usd, UsdValidation
    from usdaeco_check import can_apply, link_check, plugin_requires, registry_probe, term_sweep, validate_examples
    from usdaeco_check.plugins import check_requirements
    from usdaeco_buildup import validators
    core_rules = validators.require_core_validators()
    report.check("core validator plugin loaded", bool(core_rules), f"{len(core_rules)} core rules loaded")
    print("== stage: legacy contracts", flush=True)
    profiled = validators.validate_stage(Usd.Stage.Open(str(ROOT/'usdAecoBuildUp/examples/layered_type.usda')), include_core=True, profile=args.profile)
    report.check('profile example conformance', not validators.split(profiled)[0])

    if not report.run('plugin requirements', plugin_requires):
        return report.finish()
    report.add(registry_probe(APIS))
    plugin = Plug.Registry().GetPluginWithName('usdAecoBuildUp')
    manifest = json.loads((ROOT/'library.json').read_text())
    report.check('codeless manifest', plugin.isResource and plugin.name == manifest['name'] and
        plugin.metadata['aeco'] == {key: manifest[key] for key in ('version', 'tier', 'requires')})
    stage = Usd.Stage.CreateInMemory()
    catalog = stage.CreateClassPrim('/Catalog')
    report.add(can_apply([(catalog, 'AecoBuildUpAPI', True)]))
    # USD cannot restrict an API to the class specifier via CanApplyAPI.
    definition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(APIS[0])
    names = list(definition.GetPropertyNames())
    report.check('five properties and one derived flag', len(names) == 5 and
        {n for n in names if definition.GetPropertyMetadata(n, 'aecoDerived')} == {'aeco:buildUp:totalThickness'})
    source = Sdf.Layer.FindOrOpen(str(ROOT/'usdAecoBuildUp/schema.usda'))
    report.check('all properties documented', all(p.documentation for p in source.GetPrimAtPath('/AecoBuildUpAPI').properties))
    validators.register(); validators.register()
    report.check('two validators registered idempotently', len(UsdValidation.ValidationRegistry().GetValidatorMetadataForKeyword(validators.KEYWORD)) == 2)
    # Validate the two public roots as composed stages. Archived input/derived
    # overlays are partial layers, not additional standalone entry points.
    with tempfile.TemporaryDirectory() as temporary:
        for path in sorted((ROOT / "examples").glob("*.usda")):
            wrapper = Sdf.Layer.CreateNew(str(Path(temporary) / path.name))
            wrapper.ImportFromString(path.read_text())
            wrapper.subLayerPaths = [str((path.parent / p).resolve()) for p in wrapper.subLayerPaths]
            wrapper.Save()
        report.add(validate_examples(temporary, [], validators=[lambda s: validators.validate_stage(s, include_core=True, include_builtin=False)]))
    def fresh():
        stage = Usd.Stage.Open(str(ROOT/'usdAecoBuildUp/examples/layered_type.usda'))
        stage.SetEditTarget(stage.GetSessionLayer())
        return stage
    s=fresh(); typ=s.GetPrimAtPath('/_TypeCatalog/LayeredSection'); occurrence=s.GetPrimAtPath('/Example')
    report.check('ordered catalog query and inheritance', layers_of(typ) == layers_of(occurrence) == [
        (.02,'finish','Plaster',10),(.16,'structure','Masonry',50),(.02,'finish','Plaster',10)])
    typ.GetAttribute('aeco:buildUp:materials').Set(['Render','Block','Render'])
    report.check('type edits broadcast', layers_of(occurrence)[1][2] == 'Block')
    occurrence.GetAttribute('aeco:buildUp:materials').Set(['A','B','C'])
    report.check('occurrence override wins', layers_of(occurrence)[1][2] == 'B' and layers_of(typ)[1][2] == 'Block')
    typ.GetAttribute('aeco:buildUp:priorities').Set([50])
    issues = validators.validate_stage(s, include_builtin=False)
    report.check('seed array lengths on class detected as error', any(e.GetName()=='BuildUpArrayLengths' and e.GetType()==UsdValidation.ValidationErrorType.Error for e in issues))
    try: layers_of(typ)
    except ValueError: refused=True
    else: refused=False
    report.check('query refuses truncated arrays', refused)
    s=fresh(); s.GetPrimAtPath('/_TypeCatalog/LayeredSection').GetAttribute('aeco:buildUp:totalThickness').Set(.3)
    issues=validators.validate_stage(s,include_builtin=False)
    report.check('seed total mismatch detected as warning', any(e.GetName()=='BuildUpTotalMismatch' and e.GetType()==UsdValidation.ValidationErrorType.Warn for e in issues))
    refused=[]
    for core in (None, {'version':'0.6.0','tier':'core','requires':{}},
                 {'version':'0.8.4','tier':'core','requires':{}}):
        metadata={'usdAecoBuildUp':plugin.metadata['aeco']}
        if core: metadata['usdAeco']=core
        try: check_requirements(metadata)
        except ValueError: refused.append(True)
        else: refused.append(False)
    report.check('missing and old core refused', all(refused))
    environment={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PXR_PLUGINPATH_NAME','PXR_AR_DEFAULT_SEARCH_PATH')}
    probe=subprocess.run([sys.executable,'-c', '''
import sys
from pxr import Plug,Usd
assert not any(p.name.startswith('usdAeco') for p in Plug.Registry().GetAllPlugins())
s=Usd.Stage.Open(sys.argv[1]); assert s and not s.GetCompositionErrors()
assert list(s.GetPrimAtPath('/Example').GetAttribute('aeco:buildUp:thicknesses').Get()) == [.02,.16,.02]
assert not any(p.name.startswith('usdAeco') for p in Plug.Registry().GetAllPlugins())
print('plugin-free stage composes; inherited layer widths readable')
''',str(ROOT/'usdAecoBuildUp/examples/layered_type.usda')], env=environment, text=True,capture_output=True)
    report.check('vanilla probe',probe.returncode==0,probe.stdout.strip() or probe.stderr.strip())
    report.add(link_check(ROOT/'README.md')); report.add(link_check(ROOT/'docs'))
    report.add(term_sweep([ROOT/n for n in ('usdAecoBuildUp','usdAecoBuildUpValidators','tools','docs','examples','README.md','check.py','flake.nix','dependencies.json')],
        [r'\b(?:10\.\d{1,3}|192\.168)\.\d{1,3}\.\d{1,3}\b',r'[/]Volumes[/]']))
    print("== stage: structure and release evidence", flush=True)
    from usdaeco_buildup.structure import check_structure, legacy_contract
    raw_structure = []
    deps = [os.environ.get("CORE_PLUGIN_DIR", core_root() / "out/plugins/usdAeco/resources")]
    for result in check_structure(ROOT, deps, raw_results=raw_structure):
        report.add(result)
    report.run("v0.1.2 Sdf property and applicability comparison", lambda: legacy_contract(ROOT) == 5)
    registry = UsdValidation.ValidationRegistry()
    metadata = registry.GetValidatorMetadataForKeyword(validators.KEYWORD)
    report.check("validator plugin listing", len(metadata) == 2 and
                 all(registry.GetOrLoadValidatorByName(m.name) for m in metadata),
                 ", ".join(sorted(m.name for m in metadata)))
    from usdaeco_check.images import image_info
    image = ROOT / "usdAecoBuildUp/userDoc/usdAecoBuildUpExample.png"
    measured = image_info(image)
    rendered = json.loads((image.parent / "render.json").read_text())["renders"][0]
    report.check("committed non-uniform render matches manifest",
                 all(rendered[key] == value for key, value in measured.items()),
                 f"{measured['width']}x{measured['height']}, {measured['bytes']} bytes")
    from testUsdAecoBuildUpExample import preview_contract
    report.run("derived layers mute without changing section drivers", preview_contract)
    command = subprocess.run([sys.executable, str(ROOT / "tools/aeco_buildup.py"), "layers",
                              str(ROOT / "examples/minimal.usda"), "/Example"],
                             env=environment, capture_output=True, text=True)
    report.check("source CLI reads the minimal alias", command.returncode == 0 and
                 len(json.loads(command.stdout)) == 3)
    install_env = {**environment, "CORE_PLUGIN_DIR": str(Path(deps[0]).resolve()),
                   "AECO_CORE_ROOT": str(core_root().resolve()), "TOOLCHAIN_DIR": str(KIT.resolve())}
    installed = subprocess.run([sys.executable, "-c", '''
import sys
from pathlib import Path
sys.path[:0] = [sys.argv[1], sys.argv[2]]
import usdaeco_buildup
assert Path(usdaeco_buildup.__file__).is_relative_to(Path(sys.argv[1]))
from usdaeco_buildup.cli import main
raise SystemExit(main(["validators"]))
''', str(out / "python"), str(KIT.resolve() / "tools")], env=install_env,
        cwd=out, capture_output=True, text=True)
    report.check("installed companion loads both validators", installed.returncode == 0 and
                 len(installed.stdout.strip().splitlines()) == 2,
                 installed.stdout.strip() if installed.returncode == 0 else installed.stderr[-600:])
    report.check("checked dependency releases", Plug.Registry().GetPluginWithName("usdAeco").metadata["aeco"]["version"] == "0.9.2"
                 and json.loads((KIT / "library.json").read_text())["version"] == "0.3.8",
                 "core v0.9.2; toolchain v0.3.8")
    print("== stage: published example (S27 and S28)", flush=True)
    from usdaeco_check.example import check_example
    os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    report.add(check_example(ROOT / "examples/datacentre"))
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps({'checks':[asdict(r) for r in report.results],
            'failed':report.failed, 'raw_structure':[asdict(r) for r in raw_structure],
            'importer':'Not applicable: shared catalog library'},indent=2)+'\n')
    return report.finish()

if __name__=='__main__': raise SystemExit(main())
