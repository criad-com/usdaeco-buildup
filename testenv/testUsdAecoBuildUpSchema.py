#!/pxrpythonsubst
"""Published schema metadata, catalog inheritance and source compatibility."""
import unittest
import bootstrap
from pxr import Plug, Usd
from usdaeco_buildup import APIS, ROOT, layers_of
from usdaeco_buildup.structure import legacy_contract


class TestSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Plug.Registry().RegisterPlugins(str(ROOT / "usdAecoBuildUp"))

    def test_registry(self):
        registry = Usd.SchemaRegistry()
        self.assertTrue(registry.FindAppliedAPIPrimDefinition(APIS[0]))
        stage = Usd.Stage.CreateInMemory()
        catalog = stage.CreateClassPrim("/Catalog")
        self.assertTrue(catalog.CanApplyAPI(APIS[0]))
        definition = registry.FindAppliedAPIPrimDefinition(APIS[0])
        self.assertEqual(len(definition.GetPropertyNames()), 5)
        self.assertEqual({n for n in definition.GetPropertyNames()
                          if definition.GetPropertyMetadata(n, "aecoDerived")},
                         {"aeco:buildUp:totalThickness"})

    def test_v012_sdf_surface(self):
        self.assertEqual(legacy_contract(ROOT), 5)

    def test_catalog_query_and_overrides(self):
        stage = Usd.Stage.Open(str(ROOT / "usdAecoBuildUp/examples/layered_type.usda"))
        stage.SetEditTarget(stage.GetSessionLayer())
        catalog = stage.GetPrimAtPath("/_TypeCatalog/LayeredSection")
        occurrence = stage.GetPrimAtPath("/Example")
        self.assertEqual(layers_of(catalog), layers_of(occurrence))
        self.assertEqual(len(layers_of(catalog)), 3)
        catalog.GetAttribute("aeco:buildUp:materials").Set(["Render", "Block", "Render"])
        self.assertEqual(layers_of(occurrence)[1][2], "Block")
        occurrence.GetAttribute("aeco:buildUp:materials").Set(["A", "B", "C"])
        self.assertEqual(layers_of(occurrence)[1][2], "B")
        self.assertEqual(layers_of(catalog)[1][2], "Block")
        catalog.GetAttribute("aeco:buildUp:priorities").Set([50])
        with self.assertRaises(ValueError):
            layers_of(catalog)


if __name__ == "__main__":
    unittest.main()
