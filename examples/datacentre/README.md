# Minimal layered wall section

Open `result/example.usdc` in any stock USD viewer. It contains one wall
occurrence and three coloured proxy Cubes: 20 mm plaster, 160 mm masonry,
20 mm plaster. Cutback heights and the 0.70 m length illustrate the section.

![Section rendered without family plugins](result/vanilla.png)

From the repository root, with the environment in the main README:

```sh
env -u PYTHONPATH "$PYTHON" examples/datacentre/run.py --publish
```

The shared harness runs in **minimal** mode. Its data-centre v0.4.5 pin is
contract metadata; this library does not compose facility data. Leave
`AECO_DATACENTRE_ROOT` and `AECO_DATACENTRE_STAGE` unset. Ordinary runs write
`out/`; publication refreshes `result/`, `renders/` and `manifest.json`.
Expected findings are empty, including the loaded core validators.

`result/example.usdc` is flattened and self-contained. `result/layers/`
archives the example's cameras, catalog drivers, occurrence and separate
derived layers for inspection. The material colours match the module's
userDoc view. `result/vanilla.png` is independently rendered with stock USD,
Embree and proxy/render purposes, with no family plugins or sibling stages.

For editable composition use [the minimal root](../minimal.usda). Muting
its derived layers removes geometry and the reported total without changing
the four catalog driver arrays. Rebuild that preview with
`tools/render_example.py --publish` before publishing this result after edits.
