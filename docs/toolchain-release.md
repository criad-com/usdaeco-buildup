# Public re-pin release evidence

Version 0.2.5 pins toolchain v0.3.10, core v0.9.4 and data-centre v0.4.8.
Every family flake input uses a public release tag. The checked source revisions
are provenance only; public release trees have different commit identities.
Core and data-centre are source inputs (`flake = false`). The shared kit builds
the core plugin and installs its Python companions, preserving the plugin-set
closure without resolving core's example-only inputs.

| Dependency | Public tag | Checked source revision |
|---|---|---|
| usdaeco-toolchain | v0.3.10 | `59d3da5ff5114089b54efaaae38efdd7fe1b8e73` |
| usdaeco-core | v0.9.4 | `80a099e14e7bb825b207548d0a4f8a93e9ffa62f` |
| usdaeco-datacentre | v0.4.8 | `9e22b14c4909e50806805e735f93b1b425ac48cb` |

Checks ran from source with Python 3.13 and OpenUSD 26.8, without installing
the package. All three sibling checkouts were clean and matched the peeled
release tags. Core was explicitly importable; the gate required all eight
core validators to load through UsdValidation. The schema requirement remains
`usdAeco >=0.9,<1.0`; the Python toolchain range remains `>=0.3.1,<0.4`.
All three historical fixtures are unchanged and are not flake inputs.

| Acceptance | Measured result |
|---|---|
| Family gate | **67 checks, 0 failed, 0 not run** |
| Raw structure lint | **29 checks, 0 failed**, including tag-only S05 |
| Explicit example rules | **7/7 PASS**: S20, S21, S22, S23, S27, S28 and S29 |
| Source pytest | **34 passed**; initial schema smoke **3 passed** |
| Validator loading | **2 build-up rules + 8 core rules** |
| Direct pins | **3/3 exact tags and checked revisions recorded** |
| Requirements and fixtures | **2 supported ranges + 3 fixture records unchanged** |
| Schema | Source and generated schema bytes unchanged |
| Facility publication | **12,379 prims**, **2,670,845 bytes**, **7/8 result files byte-identical** |
| USD and findings | Crate, **5 archived USD layers**, **3 source layers** and expected findings byte-identical |
| Rendering | **3 fresh 960×600 renders**; all committed images retained |
| Result freshness | **25.130 s** within the **180 s** budget; S27/S28 pass |
| Sanitization | S25 and full publication sweep pass: **75 files, 0 findings**; **0 obsolete public-owner references** |
| Patch whitespace | `git diff --check` clean |
| Nix | **1 attempt**; current-platform outputs evaluated; **90 s timeout**, builds **not proven** |

The documented `examples/datacentre/run.py --publish` command rebuilt the
facility, editable layers, manifest and all three images. The resulting crate
and all five archived USD layers were byte-identical to the existing publication,
including the v0.2.4 derivation stamp. Source-layer hashes and source manifest
hash were also unchanged. The only changed result file is its README's source
tag. The parent manifest changes only dependency provenance and that README's
hash. The same schema, USD, findings and image byte comparisons pass against
the v0.2.4 mainline publication.

Upstream core 0.9.3/0.9.4 changelog entries preserve the schema contract and
result files. Data-centre 0.4.7/0.4.8 entries retain all published stages and
images; only rendering receipt provenance changes upstream. Toolchain 0.3.10
changes public tags and S05 enforcement while retaining its USD output and
nixpkgs revision. No geometry behavior change was observed.

## Deviations

- Keep the already prepared, unreleased 0.2.5 package version and update the
  existing release PR. It remains the patch increment from mainline 0.2.4;
  no additional version increment is needed. All four version declarations
  (library, Python project, source package and generated plugin) agree.
- Fresh Embree samples differ slightly from committed PNGs. Mean absolute RGB
  channel differences on the 0–255 scale were **0.463525** for the overview,
  **0.048019** for the exploded study and **0.461706** for the vanilla result.
  Retain the committed images after fresh-render verification, as allowed by
  S28. This keeps the final publication diff confined to provenance.
- The single `nix flake check --offline --no-write-lock-file` attempt used
  canonical local paths for the three release siblings, the stable core for
  `toolchain/core`, and an isolated exact v0.4.0 source snapshot for
  `toolchain/aeco-toolchain`. The kit's source repository was found under the
  same forge owner as this library. The nested core test-fixture override uses
  v0.9.4; the toolchain's own fixture checks were not run by this consumer.
  Empty substituters and bounded connection times were used. Nix evaluated
  both packages, both checks, the default dev shell and both apps for
  `aarch64-darwin`, then entered dependency builds. A **90-second timeout**
  stopped the attempt (wrapper status **124**). No retry was made; completed
  builds, the second platform and online public resolution remain **not proven**.

Public tag availability follows the supplied release table and the pinned
kit's release evidence. Independent online resolution, review, merge and
release tagging remain pending.
