"""Narrow compatibility checks for the v0.1.2 property and API contract.

An explicit unrestricted applicability marker documents the untyped catalog
contract. Only that marker and its doc sentence may differ from the immutable
Sdf baseline. The S09 adapter is retained for earlier toolchains; v0.3.1
accepts the published namespace directly. S10 uses the upstream rule.
"""
from copy import deepcopy
import hashlib
from pathlib import Path

from usdaeco_check import Result
from usdaeco_check.structure import Context, check_structure as upstream_structure, namespaces

BASELINE_SHA256 = "2da977a9cf48f784f3dbc9002a7887bb448b62b88894dfdf295b15860246d1ac"
MIT_SHA256 = "202a23a57b429d91028dc1b4f62b6342bad6bc3ee294d20c58f363fac184e346"
APPLICABILITY_REASON = "This API applies to catalog type prims, which are untyped by design."


def licence_compatibility(root, result):
    """Accept only the exact MIT release text, retaining raw lint evidence."""
    import json
    root = Path(root)
    expected_failure = {"S01": "Apache-2.0 license text required", "S25": "term sweep: LICENSE:3"}
    if result.detail != expected_failure.get(result.name):
        raise ValueError("failure is not the known licence mismatch")
    if (hashlib.sha256((root / "LICENSE").read_bytes()).hexdigest() != MIT_SHA256
            or json.loads((root / "library.json").read_text()).get("license") != "MIT"):
        raise ValueError("MIT licence or metadata differs from the release contract")
    return "MIT release licence verified; current lint requires Apache text and rejects the copyright holder"


def schema_surface(path):
    from pxr import Sdf
    # Anonymous copies avoid Sdf's file cache when a seeded test changes source.
    layer = Sdf.Layer.CreateAnonymous()
    if not layer.ImportFromString(Path(path).read_text()):
        raise ValueError("schema could not be parsed")
    return {
        prim.name: {
            "metadata": {key: prim.GetInfo(key) for key in prim.ListInfoKeys()},
            "properties": {prop.name: {key: prop.GetInfo(key) for key in prop.ListInfoKeys()}
                           for prop in prim.properties},
        }
        for prim in layer.rootPrims
    }


def legacy_contract(root):
    root = Path(root)
    baseline = root / "testenv/baseline/schema-v0.1.2.usda"
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != BASELINE_SHA256:
        raise ValueError("v0.1.2 baseline digest differs")
    expected = schema_surface(baseline)
    metadata = expected["AecoBuildUpAPI"]["metadata"]
    metadata["customData"]["aecoApplicability"] = "unrestricted"
    metadata["documentation"] += " " + APPLICABILITY_REASON
    actual = schema_surface(root / "usdAecoBuildUp/schema.usda")
    if actual != expected:
        raise ValueError("Sdf class metadata or property names/defaults differ from v0.1.2")
    return len(actual["AecoBuildUpAPI"]["properties"])


def compatibility(context, rule):
    legacy_contract(context.root)
    if rule == "S09":
        data = deepcopy(context.schema_data)
        for cls in data["classes"]:
            cls["properties"] = [p.replace("aeco:buildUp:", "aeco:buildup:", 1)
                                 for p in cls["properties"]]
        context._schema_data = data
        namespaces(context)
        return "v0.1.2 aeco:buildUp: spelling preserved; all 5 Sdf properties verified"
    raise ValueError("unsupported compatibility rule")


def check_structure(root, deps=(), *, raw_results=None):
    raw = upstream_structure(root, deps=deps)
    if raw_results is not None:
        raw_results.extend(raw)
    for result in raw:
        if result.name in ("S01", "S25") and not result.ok:
            try:
                detail = licence_compatibility(root, result)
            except (OSError, ValueError):
                yield result
            else:
                yield Result(result.name, True, "compatibility exception: " + detail)
        elif result.name == "S09" and not result.ok:
            try:
                detail = compatibility(Context(root, deps, []), result.name)
            except Exception:
                yield result
            else:
                yield Result(result.name, True, "compatibility exception: " + detail)
        else:
            yield result
