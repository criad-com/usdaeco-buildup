# usdAecoBuildUp — shared layered sections for OpenUSD

## Use case

Share layered build-ups between walls, floors, roofs and ceilings. A catalog
class owns four ordered driver arrays; occurrences inherit them and can
supply stronger local overrides. Read [the use case](docs/usecase.md) and
[the property reference](docs/README.md).

## The schema on an index card

| Schema | Properties in `aeco:buildUp:` | Contract |
|---|---|---|
| `AecoBuildUpAPI` | `thicknesses`, `functions`, `materials`, `priorities` | Four equal-length arrays in exterior-to-interior order; lengths in SI metres |
| Same API | `totalThickness` | Derived sum; fallback 0 means unreported or empty |

One applied API, five properties, no concrete types. The catalog remains an
ordinary class prim beside `AecoTypeAPI`. Its applicability and property names
are unchanged from v0.1.2. Rendering materials use UsdShade.

## The example

Open [examples/minimal.usda](examples/minimal.usda) directly in `usdview`.
One wall occurrence inherits a 20/160/20 mm plaster/masonry/plaster catalog
section. Three coloured proxy Cubes show the layer offsets without running
tools or loading family plugins. Finish cutbacks expose the section; their
heights and the 0.70 m length are illustrative. The bodies carry the core
representation mark and live in a separate derived layer.

The [published result](examples/datacentre/result/example.usdc) is flattened
and self-contained. Its [own layers](examples/datacentre/result/README.md)
remain available as text, and [vanilla.png](examples/datacentre/result/vanilla.png)
records a fresh stock-USD render. See [the example instructions](examples/datacentre/README.md).

```sh
env -u PYTHONPATH "$PYTHON" tools/aeco_buildup.py layers examples/minimal.usda /Example
env -u PYTHONPATH "$PYTHON" tools/render_example.py
env -u PYTHONPATH "$PYTHON" examples/datacentre/run.py --publish
```

The query prints three ordered rows. Rendering writes `out/preview/`; add
`--publish` to refresh the committed image, derived illustration and render
manifest. The shared `run.py --publish` command then refreshes the standalone
result, renders and example manifest in minimal mode. Leave data-centre source
overrides unset. The [catalog-only stage](examples/layered_type.usda) remains available.

![Layered wall section](usdAecoBuildUp/userDoc/usdAecoBuildUpExample.png)

## Build and check

Use Python 3.11+ with OpenUSD 26.8+, jinja2, packaging, numpy and pytest.
Rendering needs the standard `usdrecord` utility with Embree; Pillow supports
image tooling. Place built core v0.9.2 and toolchain v0.3.8 checkouts beside this
repository, or set the overrides below. Source checks need no package install
or build backend.

```sh
export PYTHON=python3
export TOOLCHAIN_DIR="../usdaeco-toolchain"
export AECO_CORE_ROOT="../usdaeco-core"
export CORE_PLUGIN_DIR="$AECO_CORE_ROOT/out/plugins/usdAeco/resources"
env -u PYTHONPATH ./build.sh
env -u PYTHONPATH PYTHONPATH="$AECO_CORE_ROOT:$PWD" "$PYTHON" check.py --report out/check.json
env -u PYTHONPATH "$PYTHON" -m pytest -q
env -u PYTHONPATH "$PYTHON" tools/check_structure.py
env -u PYTHONPATH "$PYTHON" tools/aeco_buildup.py validators
env -u PYTHONPATH "$PYTHON" tools/aeco_buildup.py check examples/minimal.usda --include-core
nix flake check --no-write-lock-file
```

`build.sh` regenerates resource files beside `usdAecoBuildUp/schema.usda`;
`check.py` builds the installation into ignored `out/`, checks generated-file
drift, fails if the core validator plugin cannot load, and runs `check_example()`
for stale results (S27) and the isolated vanilla render (S28). It prints the
family `N checks, M failed` line. The schema Sdf baseline
is the exact v0.1.2 source, with a pinned digest; only the explicit unrestricted
applicability marker and its doc sentence may differ. The two Python validators
wrap the existing catalog traversal and checks through the shared validation kit.
The `aeco-buildup` package entry point and `tools/aeco_buildup.py` expose the
same CLI.

For viewers, load core first because it registers `aecoDerived`:

```sh
export PXR_PLUGINPATH_NAME="$CORE_PLUGIN_DIR:$PWD/out/plugins/usdAecoBuildUp/resources:$PWD/usdAecoBuildUpValidators"
```

Python validator loading also needs the companion modules importable; the
source CLI and tests set up their import paths. An installation has its
validator and companion together under `out/python/`. Every example composes
with no family plugins; only stock prim types are used.

Flake inputs use public release refs. The
[toolchain instructions](https://github.com/criad-com/usdaeco-toolchain#build-and-check)
describe local registry files and `--override-input`. Apply overrides to
transitive inputs too; keep deployment lockfiles uncommitted. Nix offers
`default` and `pluginSet` packages, `library` and `structure` checks, a dev shell,
and `example` and `render` apps.

## Family

This section-tier library requires `usdAeco >=0.9,<1.0`. Checks target core
v0.9.2 and toolchain v0.3.8 as recorded in [dependencies.json](dependencies.json).
The harness also records data-centre v0.4.5; this minimal library example does
not consume that data or prove facility composition.
The [family manifest](https://github.com/criad-com/usdaeco-scenarios/blob/main/family.json)
lists consumers. The wall use case owns the full workflow and data-centre
example; this shared library has no importer or independent facility example.

## Layout

| Path | Contents |
|---|---|
| usdAecoBuildUp/ | Flat schema, generated resources, userDoc and minimal/catalog stages |
| usdAecoBuildUpValidators/ | Two Python UsdValidation stage rules |
| tools/usdaeco_buildup/ | Ordered section query, validation, profiles and CLI |
| testenv/ | Registry and defect tests, source bootstrap, v0.1.2 Sdf baseline |
| conformance/, docs/ | Default profile, property reference, scope and compatibility notes |
| examples/ | Stable aliases and the minimal publication harness with committed result/ |
| out/ | Ignored installation, reports and preview artifacts |

## Status

Version 0.2.3 updates public names to github.com/criad-com and checks against
toolchain v0.3.8. Verified: 59 checks, 0 failed; 29 raw structure rules passed;
27 source tests passed. [Release checks](docs/public-names.md) record the Nix
limitation. Since v0.2.1, the layered section is visible by default with a
standalone result and plugin-free render.
All five properties and runtime applicability remain unchanged.
See [the v0.2.1 acceptance notes](docs/acceptance.md) for that release's numbers and limits.

The schema declares `aecoApplicability = "unrestricted"` because catalog type
prims are untyped by design, passing S10 directly. The Sdf comparison permits
only that customData addition and its explanatory doc sentence. Toolchain
v0.3.8 also accepts the published `aeco:buildUp:` spelling directly (S09).
Raw lint results remain visible in `out/check.json`. The MIT release licence
passes S01/S25 directly with toolchain v0.3.8; compatibility handling remains
for earlier toolchains. Other term hits still fail.

Validator errors are now `BuildUpArrayLengths` and `BuildUpTotalMismatch`.
Existing profiles using the former lower-camel names still work; canonical
names take precedence when both forms occur. Rule selection uses the plugin
keyword `UsdAecoBuildUpValidators`.

## Licence

[MIT](LICENSE). No third-party code is vendored here. The separate family
importer imports IfcOpenShell (LGPL-3.0); this section library has no importer
or IfcOpenShell dependency.
