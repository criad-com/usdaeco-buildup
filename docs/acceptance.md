# Acceptance record

Version 0.2.1 targets core v0.9.1 and toolchain v0.3.1. The example runs in
minimal mode, with no data-centre checkout or installed distribution required.

| Acceptance | Measured result |
|---|---|
| Family gate | 58 checks, 0 failed; all existing checks retained |
| Library structure | 28/28 with the two licence exceptions below; raw lint 26/28 (S01, S25); S10 passes directly |
| Source tests | 27 passed; no setuptools or installed distribution required |
| Registry | AecoBuildUpAPI, registered Tf type UsdAecoBuildUpBuildUpAPI; 0 concrete types |
| Validators loaded | 2 build-up rules and all 8 declared core rules; missing core import fails loudly |
| Minimal/catalog roots | 2 composed roots; 0 errors and 0 warnings |
| Visible section | 1 wall occurrence, 3 proxy Cubes at the 20/160/20 mm layer offsets; both minimal entry points checked |
| Driver separation | Muting derived layers removes the bodies and reported total, preserving all four inherited driver arrays |
| Standalone result | Flattened 2,737-byte crate; 8 prims; 0 external assets; complete stock-type coverage; opens after isolated relocation |
| Result inventory | 10 files, 68,775 bytes total; 7 diffable own USDA layers |
| Vanilla image | 1280 × 800, 60,518 bytes; visibly shows the section; fresh stock USD/Embree process, proxy/render purposes |
| UserDoc image | 1280 × 800, 60,469 bytes; same three-layer section |
| Fresh-result check | check_example() passes normalized-crate and own-layer comparison (S27), plus independent vanilla re-render (S28) |
| Findings | 0, with built-in, core and build-up validators loaded |
| Generated resources | usdGenSchema --validate clean; generated schema unchanged from v0.2.0 |
| Schema comparison | All 5 properties match v0.2.0 and the digest-pinned v0.1.2 Sdf baseline; only the explicit unrestricted customData marker and its class doc sentence differ; generated schema and runtime applicability unchanged |
| Sanitization | No findings beyond the explicitly required LICENSE copyright line; raw S25 evidence retained |
| Nix acceptance | Not proven: the single offline flake-check attempt failed resolving public core v0.9.1 (HTTP 404) |

Run `check.py --report out/check.json` to reproduce the gate, including raw
structure results. Run `examples/datacentre/run.py --publish` to refresh the
[committed result](../examples/datacentre/result/README.md). Its
[manifest](../examples/datacentre/manifest.json) records every artifact hash.
Only the complete public roots are passed to validate_examples(); archived
camera and derived overlays are validated in the composed published stage.

## Deviations

- The release uses MIT. Toolchain v0.3.1 S01 still requires Apache-2.0 and S25
  rejects the required copyright holder. The local wrapper accepts only those
  exact failures after checking the complete MIT licence SHA-256 and the MIT
  declaration in library.json. Additional term hits, missing root files and
  changed licence bytes still fail. Raw S01/S25 failures remain in the report;
  unmodified lint and an unrestricted clean term sweep are not claimed.
- This shared library publishes in minimal mode. The harness requires a
  data-centre v0.4.1 pin in its manifest, but no facility data was consumed or
  validated. It has no importer or independent facility pipeline. Its finish
  cutbacks and length are illustrative; layer widths come from the drivers.
- One `nix flake check --offline --no-write-lock-file` attempt returned HTTP 404
  for the public core v0.9.1 input. Nix builds and both declared platforms are
  not proven. Python checks ran with OpenUSD 26.8; no retry or install occurred.
