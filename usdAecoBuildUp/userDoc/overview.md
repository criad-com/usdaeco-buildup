# Layered sections

`AecoBuildUpAPI` decorates a catalog class beside `AecoTypeAPI`. Walls, floors,
roofs and ceilings inherit the same ordered section arrays. The section is an
aspect of an existing catalog or occurrence; it introduces no typed referent.

The [minimal example](../examples/minimal.usda) composes the
[three-layer catalog](../examples/layered_type.usda) with a separate derived
wall-section illustration. The exterior-to-interior widths are 20 mm plaster,
160 mm masonry and 20 mm plaster. The finish cutbacks expose the section;
their heights are illustrative and are not build-up properties.

![Layered wall section](usdAecoBuildUpExample.png)

Geometry uses native Cube prims marked with `AecoDerivedGeometryAPI`, role
`proxy`, approximation `defaultDims`, and purpose `proxy`. Opening the minimal
stage directly shows the section in a stock viewer. The shared kit uses
`usdrecord` and Embree; [the standalone result](../../examples/datacentre/result/example.usdc)
also has a committed [plugin-free render](../../examples/datacentre/result/vanilla.png).
Drivers and the reported 0.20 m total live in separate layers. Muting the
derived layers leaves the editable section arrays intact.

Every stage uses only stock prim types, so there are no Aeco typed prims that
need `fallbackPrimTypes`. A viewer with no family plugins still composes the
same catalog values, transforms and image geometry.

See the [schema reference](../../docs/README.md) for properties and rules,
and [the use-case discussion](../../docs/usecase.md) for shared-section scope.
