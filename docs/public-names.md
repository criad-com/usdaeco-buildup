# Public-name release checks

Historical v0.2.3 evidence. Current verification is recorded in the
[v0.2.5 release evidence](toolchain-release.md).

Version 0.2.3 updates public names to github.com/criad-com and pins toolchain
v0.3.8. Checks ran from source with OpenUSD 26.8 against isolated release
checkouts of core v0.9.2 and toolchain v0.3.8. The data-centre pin remains
v0.4.5; this library's example uses minimal mode.

| Acceptance | Measured result |
|---|---|
| Family gate | 59 checks, 0 failed, 0 not run |
| Raw structure lint | 29 checks, 0 failed; S05 and S25 pass directly |
| Source pytest | 27 passed; no installed distribution or setuptools required |
| Public references | All 7 existing references updated; 0 obsolete public-owner references remain |
| Release metadata | Library, Python project, companion and resource plugin all report 0.2.3 |
| Dependency pins | Only toolchain changes, to v0.3.8; core, data-centre and historical fixtures unchanged |
| Validators | 2 build-up rules and all 8 core rules loaded; missing core import fails loudly |
| Schema compatibility | Source and generated schema unchanged; all 5 properties retain the v0.1.2 contract |
| Published result | All 10 result files and all 3 committed images byte-identical to v0.2.2 |
| Fresh-result verification | 8 plugin-free prims; own layers and normalized crate match; independent vanilla render passes |
| Example manifest | Only the toolchain pin changes; result hashes and source evidence unchanged |
| Nix | 1 attempt, exit 1 before input resolution; builds and platform checks not proven |

Run the commands in [Build and check](../README.md#build-and-check), using
checkouts at the exact declared tags. The gate's JSON report includes every
raw structure result. Library-only story/example rules report not applicable;
the full gate explicitly runs the shared example comparison and vanilla render.

## Deviations

- The unchanged section derivation retains its v0.2.2 stamp independently of
  the package version. This avoids republishing results for a public-name
  release while keeping the fresh-result comparison active. No result or
  image was republished; the manifest only records the required toolchain pin.
- The first gate encountered a shared core checkout that had advanced to
  v0.9.3 and correctly failed its exact-version check. The reported green run
  uses isolated core v0.9.2 and toolchain v0.3.8 release checkouts.
- The single offline Nix flake-check attempt used local release overrides,
  but the chosen temporary-directory path passed through a macOS symlink.
  Nix rejected that path before resolving the inputs. Input resolution and
  Nix builds remain unproven; the one-attempt limit prevented a retry.
