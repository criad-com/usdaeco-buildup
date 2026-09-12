# Facility example release evidence

Historical v0.2.4 evidence. Current verification is recorded in the
[v0.2.5 release evidence](toolchain-release.md).

Version 0.2.4 replaces the minimal publication with the complete data-centre
v0.4.6 clash publication, while preserving the small module example and schema.
Checks use core v0.9.2 and toolchain v0.3.8 with OpenUSD 26.8 and source imports.
The core checkout's Git tree equals the v0.9.2 release tree; the data-centre and
toolchain tracked trees match their pins. The clash publication is unchanged
between data-centre v0.4.4 and v0.4.6.

| Acceptance | Measured result |
|---|---|
| Family gate | **67 checks, 0 failed, 0 not run** |
| Raw structure lint | **29 checks, 0 failed**; 23 applicable rules and six library story/example exclusions |
| Explicit example rules | **7/7 PASS**: S20, S21, S22, S23, S27, S28 and S29 |
| Source pytest | **34 passed**, including seven new facility/promotion tests; no package installation |
| Facility source | **12,354 prims**, all retained; census verified against the pinned manifest |
| Published census | **2,980 elements, 35 spaces, two levels, 6,244 ports, 3,015 meshes, two proxy-classified elements, zero unparented** |
| Office promotion | **20 walls**, three catalogs: 16 plasterboard, two blockwork, two WC lining |
| Derived geometry | **Six walls, 20 layer bodies**; driver arrays survive derived-layer muting |
| Validation | **2 build-up + 8 core rules loaded**, zero errors, two existing proxy-classification warnings |
| Published result | **12,379 prims; 2,670,845 bytes; eight files**; full census and source paths preserved |
| Own-layer size | Largest USDA **650,137 bytes**, below the 2 MB cap |
| Stock render | **960×600, 291,058 bytes**; full facility with an office cutaway, no family plugins |
| Owned renders | Overview **290,453 bytes**; exploded WC section **58,528 bytes**, both 960×600 |
| Two-layout ResultStale | **2 checks, 0 failed**; current output compared, then fresh run with relocated checkout and source |
| S27–S29 | Independent plugin-free crate open/render and portable archived source paths all pass |
| Example runtime | **21.710 s** in the full gate; **19.011 s** relocated; 180 s budget |
| Schema compatibility | All **five properties** retain the v0.1.2 contract; no schema source change |
| Sanitization/public names | S25 passes, targeted sweep checks **64 text files**, no matches; obsolete public-owner URLs absent |
| Nix | **One attempt, exit 1** during transitive input resolution; builds/platform checks **not proven** |

Run the root README commands against the exact dependency releases. The full
gate writes `out/check.json` and the standalone lint prints its raw S01–S29
results. After the full gate, `tools/check_relocation.py --reuse-current-run`
compares its current output and then runs a relocated copy from source. It
relocates the data-centre publication too, proving `inputs/source` portability.
The two-layout check compares authored layers byte-for-byte and crates using
the shared normalized Sdf comparison; render pixels are not promised identical.

The Nix attempt used `--offline --no-write-lock-file`, empty substituters and
local overrides for the three direct inputs. Resolution still returned HTTP
404 for a transitive data-centre v0.4.1 reference retained by frozen core
v0.9.2. The one-attempt limit was respected. No Nix build or second platform
result is claimed, and no unrelated dependency was re-pinned.

## Deviations

- Main already contained the v0.2.3 public-name release, so this patch is v0.2.4.
  Public references already use github.com/criad-com; no rename remained.
- The source contains partition and solid-wall classifications, total widths
  and type models, but no explicit WC lining catalog or material layer arrays.
  The three documented recipes are example assumptions; the WC catalog is a
  specialization selected by adjacency to the source WC spatial boundary.
- Layer bodies are gross rectangular previews with `defaultDims`, not an
  opening/join evaluator. The exploded sample changes dimensions and spacing
  only in its separate study layer.
- The full facility cutaway keeps every prim and placement. Roof/ceiling,
  office facade and upper-floor visibility changes belong to presentation.
- The shared core checkout advanced beyond the declared dependency. Checks
  use the existing core v0.9.2 release checkout; the dependency pin is unchanged.
- Renders are 960×600 to satisfy the 400 KB image cap on the detailed facility.
- This remains a section library. The raw lint skips story/example rules;
  the full gate explicitly exercises the applicable example rules, including
  S27–S29, without changing the library's tier or runtime requirements.

- The single Nix attempt failed at a frozen core input's transitive reference.
  Nix builds and platform checks remain unproven; the source gate is green.

## What remains

Review and merge this PR, then tag v0.2.4. Nix verification needs the transitive
input closure corrected or overridden in a separate authorized change. A
production wall evaluator with openings/joins and verified material recipes
remains outside this shared-section example.
