"""Query ordered sections and run the registered build-up validators."""
import argparse
import json
from pathlib import Path


def _site_path(site):
    target = site.GetProperty() or site.GetPrim()
    if target:
        return str(target.GetPath())
    spec = site.GetPropertySpec() or site.GetPrimSpec()
    return str(spec.path) if spec else "/"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    query = commands.add_parser("layers", help="Print ordered section tuples as JSON")
    query.add_argument("stage", type=Path)
    query.add_argument("prim")
    check = commands.add_parser("check", help="Validate catalogs and occurrences")
    check.add_argument("stage", type=Path)
    check.add_argument("--profile", type=Path)
    check.add_argument("--include-core", action="store_true")
    commands.add_parser("validators", help="List the two registered validators")
    args = parser.parse_args(argv)
    from . import layers_of, register_plugins, validators
    try:
        register_plugins()
        from pxr import Usd, UsdValidation
        validators.register()
        if args.command == "validators":
            registry = UsdValidation.ValidationRegistry()
            for metadata in sorted(registry.GetValidatorMetadataForKeyword(validators.KEYWORD), key=lambda m: m.name):
                print(metadata.name)
            return 0
        stage = Usd.Stage.Open(str(args.stage))
        if not stage or stage.GetCompositionErrors():
            raise ValueError("stage does not compose")
        if args.command == "layers":
            prim = stage.GetPrimAtPath(args.prim)
            if not prim:
                raise ValueError("prim does not exist: " + args.prim)
            print(json.dumps(layers_of(prim), indent=2))
            return 0
        issues = validators.validate_stage(stage, include_core=args.include_core, profile=args.profile)
        errors, warnings = validators.split(issues)
        for issue in issues:
            sites = ", ".join(_site_path(site) for site in issue.GetSites())
            print(f"{issue.GetName()}: {sites}: {issue.GetMessage()}")
        print(f"{len(errors)} errors, {len(warnings)} non-errors")
        return int(bool(errors))
    except Exception as error:
        parser.exit(1, f"aeco-buildup: {error}\n")
