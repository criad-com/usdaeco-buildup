# Office build-ups on the demo data centre

Open [result/example.usdc](result/example.usdc) directly in stock `usdview`.
It contains the full v0.4.8 `clash` publication of `demo-datacentre-01`, with
three promoted office build-up catalogs. No sibling checkout or family plugin
is needed to view the crate.

![Facility cutaway rendered with stock USD](result/vanilla.png)

The office wing is at the front of the facility. Blue identifies plasterboard
partitions, orange identifies blockwork, and green identifies the WC lining.
The view hides only roof/ceiling bodies and the office facade/upper floor to
reveal both storeys. Every source prim remains active and in its original
location; the presentation opinions are removable.

With the environment in the root README, run from the repository root:

```sh
export AECO_DATACENTRE_ROOT="../usdaeco-datacentre"
env -u PYTHONPATH PYTHONPATH="$AECO_CORE_ROOT:$PWD" "$PYTHON" examples/datacentre/run.py --publish
```

The runner checks v0.4.8 and creates the ignored `inputs/source` alias to that
checkout. It composes `inputs/source/dist/clash/dc.usda` below its own layers.
Publication archives portable relative paths through this alias; relocating a
checkout only requires setting `AECO_DATACENTRE_ROOT` and rerunning. Sources
remain read-only. The source manifest records generator v0.4.4; those published
layers are unchanged in v0.4.8. Ordinary runs write `out/`; publication updates
`result/`, `renders/` and `manifest.json`, but never overwrites expected findings.

[inputs/build-ups.json](inputs/build-ups.json) declares the demonstration
recipes and the office envelope. Selection uses the source IFC wall
classification, type model and placement. WC partitions are selected by their
adjacency to the published WC space boundary. The source has no separate WC
lining type, so that specialization is authored here and inherits the original
partition type. No duplicate element identity or new wall classification is
introduced. External precast walls retain their original catalog.

| Recipe | Walls | Layers, outside to inside | Total |
|---|---:|---|---:|
| Plasterboard partition | 16 | 25 mm board / 100 mm stud and insulation zone / 25 mm board | 150 mm |
| Finished blockwork | 2 | 15 mm plaster / 170 mm dense blockwork / 15 mm plaster | 200 mm |
| WC lining | 2 | 25 mm board / 100 mm stud zone / 15 mm moisture-resistant board / 10 mm tile | 150 mm |

These are example assumptions, not extracted material specifications or fire
performance claims. Their totals must match published wall widths. Two walls
per recipe get layer bodies: six walls, 20 cubes. Dimensions come from the
published gross quantities and resolved driver arrays. These rectangular
proxies omit openings, joins and individual studs and declare `defaultDims`.
The other promoted walls retain their original meshes and openings.

![Exploded WC layered section](renders/exploded.png)

The exploded study is a 1.4 by 1.8 m sample of one selected WC wall, with
380 mm separation for legibility. Its presentation opinions are confined to
`out/exploded.usda`; they never enter `result/example.usdc`. The full facility
render uses the `overview` camera; the study uses `exploded`. Both are 960×600.

The manifest census is read and checked on every run: 2,980 elements,
35 spaces, two levels, 6,244 ports, 3,015 meshes, two proxy-classified elements
and zero unparented elements. All eight core validators and both build-up
validators execute through UsdValidation, along with built-in core checks.
There are zero errors and two existing `proxyClassified` warnings. Missing
core validators fail loudly. The expected file retains these warnings.

The [own-layer archive](result/README.md) separates catalog drivers, derived
totals and cubes, camera/presentation opinions and the exploded study. Muting
derived opinions leaves all driver arrays and source identities unchanged.
The original source layers are hashed, not copied into that archive; the
flattened crate includes their full composition. `tools/check_relocation.py`
checks fresh results in two checkout/source layouts. The
[small synthetic section](../minimal/README.md) remains independently useful.
