# Schema reference

Authoritative source: [schema.usda](../usdAecoBuildUp/schema.usda).
All dimensional values are **SI metres**, independent of geometry's stage units.

## AecoBuildUpAPI

Single-apply on catalog class prims beside `AecoTypeAPI`. Occurrences inherit
values through ordinary USD `inherits`; occurrence overrides remain stronger.
USD `CanApplyAPI` cannot constrain a prim specifier to `class`. The unrestricted
v0.1.2 applicability is preserved; catalog use is an authoring convention.

| Property (`aeco:buildUp:`) | Type and fallback | Ownership and meaning |
|---|---|---|
| thicknesses | double[] · [] | Driver; exterior-to-interior widths; zero-width membranes allowed |
| functions | token[] · [] | Driver; structure, substrate, insulation, finish, membrane, other |
| materials | string[] · [] | Driver; material names aligned with widths |
| priorities | int[] · [] | Driver; native join priority, 0 unspecified |
| totalThickness | double · 0 | Derived; reported sum, with schema property metadata `aecoDerived = true` |

Rendering materials use UsdShade. The library adds no geometry schema, identity,
kind tokens, grouping or connectivity mechanism. Derived values are authored in
a separate layer. Stage data does not redeclare the `aecoDerived` metadata.

## Validators and queries

The Python plugin keyword is `UsdAecoBuildUpValidators`. Names are prefixed
`usdAecoBuildUpValidators:`. Both stage callbacks wrap the legacy rules through
`usdaeco_check.validation.wrap_legacy`. Stage scope is necessary to visit catalog
classes that default traversal omits and to suppress inherited-only duplicates.
Locally overridden occurrences are checked independently.

| Validator | Error name | Severity and meaning |
|---|---|---|
| BuildUpArrayLengthsChecker | BuildUpArrayLengths | Error: four array lengths differ |
| BuildUpTotalMismatchChecker | BuildUpTotalMismatch | Warn: authored total differs from sum by more than 1e-8 m or is nonfinite |

An unreported or blocked total is not an observed measurement. Validation is at
default time. `register()` remains idempotent and loads the declared plugin.
`validate_stage(stage)` includes USD built-in validators; `include_core=True`
adds core semantic rules. A profile path or dictionary changes severity only.
Old `buildUpArrayLengths` and `buildUpTotalMismatch` profile keys map to their
ProperCase equivalents, with canonical keys taking precedence.

`layers_of(prim)` returns ordered `(thickness_m, function, material, priority)`
tuples. It accepts classes and occurrences, returns `[]` for a missing API and
raises `ValueError` on mismatched arrays instead of silently truncating them.

The [catalog stage](../examples/layered_type.usda) has three layers and no
geometry. The [minimal preview](../examples/minimal.usda) adds marked native
Cube proxies in a removable derived layer. See [acceptance](acceptance.md) for
measured checks and [scope](usecase.md) for alternatives.
