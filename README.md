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

Open the [standalone facility](examples/datacentre/result/example.usdc) in stock
`usdview`. It contains the complete pinned `clash` variant of
`demo-datacentre-01`, with 20 office-wing walls inheriting three build-ups:
16 plasterboard partitions, two blockwork walls and two WC lined partitions.
Six representative walls have 20 derived layer bodies. Blue, orange and green
identify the three recipes. The cutaway hides roof/ceiling bodies, the office
facade and its upper floor so both storeys can be reviewed; all source prims
remain in the crate.

![Facility with promoted office walls](examples/datacentre/result/vanilla.png)

With the environment below and the pinned data-centre checkout available:

```sh
export AECO_DATACENTRE_ROOT="../usdaeco-datacentre"
env -u PYTHONPATH PYTHONPATH="$AECO_CORE_ROOT:$PWD" "$PYTHON" examples/datacentre/run.py --publish
```

The [example instructions](examples/datacentre/README.md) explain the source
alias, assumed recipes, manifest-derived counts and
[exploded WC section](examples/datacentre/renders/exploded.png). Ordinary runs
write ignored `out/`; `--publish` updates the self-contained crate, editable
own layers, renders and manifest. Expected findings are never silently replaced.

The [small synthetic section](examples/minimal/README.md) remains useful for
learning inheritance and muting without a facility checkout. Its stable
[entry point](examples/minimal.usda) still supports:

```sh
env -u PYTHONPATH "$PYTHON" tools/aeco_buildup.py layers examples/minimal.usda /Example
env -u PYTHONPATH "$PYTHON" tools/render_example.py
```

## Build and check

Use Python 3.11+ with OpenUSD 26.8+, jinja2, packaging, numpy and pytest.
Rendering needs the standard `usdrecord` utility with Embree; Pillow supports
image tooling. Place built core v0.9.4 and toolchain v0.3.10 checkouts beside this
repository and data-centre v0.4.8, or set the overrides below. Each checkout
must match its declared release tag. Source checks need no package install
or build backend.

```sh
export PYTHON=python3
export TOOLCHAIN_DIR="../usdaeco-toolchain"
export AECO_CORE_ROOT="../usdaeco-core"
export CORE_PLUGIN_DIR="$AECO_CORE_ROOT/out/plugins/usdAeco/resources"
export AECO_DATACENTRE_ROOT="../usdaeco-datacentre"
env -u PYTHONPATH ./build.sh
env -u PYTHONPATH PYTHONPATH="$AECO_CORE_ROOT:$PWD" "$PYTHON" check.py --report out/check.json
env -u PYTHONPATH "$PYTHON" -m pytest -q
env -u PYTHONPATH "$PYTHON" tools/check_structure.py
env -u PYTHONPATH "$PYTHON" tools/check_relocation.py --reuse-current-run
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
validator and companion together under `out/python/`. The published facility composes
with no family plugins; every Aeco typed prim has a stock fallback.

Flake inputs use public release refs. The
[toolchain instructions](https://github.com/criad-com/usdaeco-toolchain#build-and-check)
describe local registry files and `--override-input`. Apply overrides to
transitive inputs too; keep deployment lockfiles uncommitted. Nix offers
`default` and `pluginSet` packages, `library` and `structure` checks, a dev shell,
and `example` and `render` apps.

## Family

This section-tier library requires `usdAeco >=0.9,<1.0`. Checks target core
v0.9.4 and toolchain v0.3.10 as recorded in [dependencies.json](dependencies.json).
The example consumes the complete data-centre v0.4.8 `clash` publication.
Its source manifest records generator v0.4.4 and the original converter/core
provenance; the publication is retained unchanged in the v0.4.8 release.
The [family manifest](https://github.com/criad-com/usdaeco-scenarios/blob/main/family.json)
lists consumers. The shared section schema still depends only on core.

## Layout

| Path | Contents |
|---|---|
| usdAecoBuildUp/ | Flat schema, generated resources, userDoc and minimal/catalog stages |
| usdAecoBuildUpValidators/ | Two Python UsdValidation stage rules |
| tools/usdaeco_buildup/ | Ordered section query, validation, profiles and CLI |
| testenv/ | Registry and defect tests, source bootstrap, v0.1.2 Sdf baseline |
| conformance/, docs/ | Default profile, property reference, scope and compatibility notes |
| examples/ | Facility publication, small synthetic section and stable aliases |
| out/ | Ignored installation, reports and preview artifacts |

## Status

Version 0.2.5 pins public releases of toolchain v0.3.10, core v0.9.4 and
data-centre v0.4.8. Core and data-centre are source inputs; the shared kit
builds the core plugin without resolving its example-only dependencies.
The supported requirement ranges and section derivation remain unchanged.
Verified: **67 checks, 0 failed; 29 raw structure checks, 0 failed; 34 tests
passed**. The republished crate and five USD layers are byte-identical; only
publication provenance changes. The single offline Nix attempt evaluated the
current-platform outputs, then timed out during dependency builds; completed
Nix builds and online resolution remain unproven.
See [release evidence and deviations](docs/toolchain-release.md) for measured
checks and the offline Nix outcome.

The schema declares `aecoApplicability = "unrestricted"` because catalog type
prims are untyped by design, passing S10 directly. The Sdf comparison permits
only that customData addition and its explanatory doc sentence. Toolchain
v0.3.10 also accepts the published `aeco:buildUp:` spelling directly (S09).
Raw lint results remain visible in `out/check.json`. The MIT release licence
passes S01/S25 directly with toolchain v0.3.10; compatibility handling remains
for earlier toolchains. Other term hits still fail.

Validator errors are now `BuildUpArrayLengths` and `BuildUpTotalMismatch`.
Existing profiles using the former lower-camel names still work; canonical
names take precedence when both forms occur. Rule selection uses the plugin
keyword `UsdAecoBuildUpValidators`.

## Licence

[MIT](LICENSE). No third-party code is vendored here. The separate family
importer imports IfcOpenShell (LGPL-3.0); this section library has no importer
or IfcOpenShell dependency.
