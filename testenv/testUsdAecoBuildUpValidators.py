#!/pxrpythonsubst
"""The registered rules find defects on classes and occurrence overrides."""
import unittest
import bootstrap
from pxr import Plug, Usd, UsdValidation
from usdaeco_buildup import ROOT, validators
from usdAecoBuildUpValidators import validatorTokens as tokens


def fresh():
    stage = Usd.Stage.Open(str(ROOT / "usdAecoBuildUp/examples/layered_type.usda"))
    stage.SetEditTarget(stage.GetSessionLayer())
    return stage


class TestValidators(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Plug.Registry().RegisterPlugins(str(ROOT / "usdAecoBuildUpValidators"))

    def findings(self, stage):
        return validators.validate_stage(stage, include_builtin=False)

    def test_plugin_listing(self):
        validators.register()
        validators.register()
        registry = UsdValidation.ValidationRegistry()
        metadata = registry.GetValidatorMetadataForKeyword(tokens.KEYWORD)
        self.assertEqual({m.name for m in metadata},
                         {tokens.ARRAY_LENGTHS_CHECKER, tokens.TOTAL_MISMATCH_CHECKER})
        self.assertTrue(all(registry.GetOrLoadValidatorByName(m.name) for m in metadata))

    def test_BuildUpArrayLengths(self):
        stage = fresh()
        catalog = stage.GetPrimAtPath("/_TypeCatalog/LayeredSection")
        catalog.GetAttribute("aeco:buildUp:priorities").Set([50])
        errors = self.findings(stage)
        self.assertEqual([e.GetName() for e in errors], ["BuildUpArrayLengths"])
        self.assertEqual(errors[0].GetType(), UsdValidation.ValidationErrorType.Error)
        self.assertEqual(errors[0].GetSites()[0].GetPrim(), catalog)

    def test_BuildUpTotalMismatch(self):
        stage = fresh()
        occurrence = stage.GetPrimAtPath("/Example")
        occurrence.GetAttribute("aeco:buildUp:totalThickness").Set(.3)
        errors = self.findings(stage)
        self.assertEqual([e.GetName() for e in errors], ["BuildUpTotalMismatch"])
        self.assertEqual(errors[0].GetType(), UsdValidation.ValidationErrorType.Warn)
        self.assertEqual(errors[0].GetSites()[0].GetPrim(), occurrence)

    def test_unreported_and_nonfinite_total(self):
        stage = Usd.Stage.CreateInMemory()
        catalog = stage.CreateClassPrim("/Catalog")
        catalog.ApplyAPI("AecoBuildUpAPI")
        self.assertEqual(self.findings(stage), [])
        catalog.GetAttribute("aeco:buildUp:totalThickness").Set(float("nan"))
        self.assertEqual([e.GetName() for e in self.findings(stage)], ["BuildUpTotalMismatch"])
        catalog.GetAttribute("aeco:buildUp:totalThickness").Block()
        self.assertEqual(self.findings(stage), [])


if __name__ == "__main__":
    unittest.main()
