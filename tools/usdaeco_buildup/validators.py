"""Static/default-time validation, including catalog class prims."""
import math
from .profiles import apply_profile, load_profile
from pxr import Usd, UsdValidation
from . import ARRAYS, SIZE_TOLERANCE

KEYWORD = "UsdAecoBuildUpValidators"


def _issue(name, prim, message, error=False):
    return UsdValidation.ValidationError(name,
        UsdValidation.ValidationErrorType.Error if error else UsdValidation.ValidationErrorType.Warn,
        [UsdValidation.ValidationErrorSite(prim.GetStage(), prim.GetPath())], message)


def _catalogs(stage):
    # Default traversal skips classes. Validate each authored section, plus
    # occurrence overrides, without repeating inherited-only catalog findings.
    for prim in Usd.PrimRange.Stage(stage, Usd.PrimAllPrimsPredicate):
        if not prim.IsActive() or not prim.HasAPI("AecoBuildUpAPI"):
            continue
        if prim.IsAbstract() or not prim.GetInherits().GetAllDirectInherits() or any(
            any(spec.owner.path == prim.GetPath() for spec in
                prim.GetAttribute("aeco:buildUp:" + n).GetPropertyStack())
            for n in (*ARRAYS, "totalThickness")):
            yield prim


def _lengths(stage, time_range):
    issues = []
    for prim in _catalogs(stage):
        sizes = [len(prim.GetAttribute("aeco:buildUp:" + n).Get() or []) for n in ARRAYS]
        if len(set(sizes)) != 1:
            issues.append(_issue("BuildUpArrayLengths", prim, "Build-up array lengths disagree: " + str(sizes), True))
    return issues


def _total(stage, time_range):
    issues = []
    for prim in _catalogs(stage):
        attr = prim.GetAttribute("aeco:buildUp:totalThickness")
        total = attr.Get()
        values = prim.GetAttribute("aeco:buildUp:thicknesses").Get() or []
        if not attr.HasAuthoredValueOpinion() or total is None:
            continue  # schema fallback is not a reported result
        expected = sum(values)
        if not math.isfinite(total) or not math.isfinite(expected) or abs(total - expected) > SIZE_TOLERANCE:
            issues.append(_issue("BuildUpTotalMismatch", prim, "Reported total differs from layer sum"))
    return issues


def register():
    from . import VALIDATOR_DIR
    import sys
    from pxr import Plug
    if str(VALIDATOR_DIR.parent) not in sys.path:
        sys.path.insert(0, str(VALIDATOR_DIR.parent))
    Plug.Registry().RegisterPlugins(str(VALIDATOR_DIR))
    registry = UsdValidation.ValidationRegistry()
    metadata = registry.GetValidatorMetadataForKeyword(KEYWORD)
    if len(metadata) != 2 or not all(registry.GetOrLoadValidatorByName(m.name) for m in metadata):
        raise RuntimeError("build-up validator plugin did not load its two rules")


def require_core_validators():
    """Fail loudly if the core Python plugin or any declared rule is missing."""
    from usdaeco_tools import validators
    validators.register()
    import usdAecoValidators
    registry = UsdValidation.ValidationRegistry()
    metadata = registry.GetValidatorMetadataForKeyword(validators.KEYWORD)
    if not metadata or not all(registry.GetOrLoadValidatorByName(m.name) for m in metadata):
        raise RuntimeError("usdAecoValidators did not load its declared rules")
    return metadata


def validate_stage(stage, include_core=False, include_builtin=True, profile=None):
    register()
    keywords = [KEYWORD]
    if include_core:
        require_core_validators()
        keywords.append("UsdAecoValidators")
    if include_builtin and load_profile(profile).get("include_builtin", True):
        keywords.append("UsdCoreValidators")
    registry = UsdValidation.ValidationRegistry()
    names = [m.name for key in keywords for m in registry.GetValidatorMetadataForKeyword(key)]
    return apply_profile(list(UsdValidation.ValidationContext(registry.GetOrLoadValidatorsByName(names)).Validate(stage)), profile)


def split(issues):
    return ([e for e in issues if e.GetType() == UsdValidation.ValidationErrorType.Error],
            [e for e in issues if e.GetType() != UsdValidation.ValidationErrorType.Error])
