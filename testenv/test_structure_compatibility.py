"""Compatibility exceptions cannot hide schema changes or baseline edits."""
from pathlib import Path
import shutil
import pytest
from usdaeco_buildup import ROOT
from usdaeco_buildup.structure import APPLICABILITY_REASON, legacy_contract, licence_compatibility
from usdaeco_check import Result
from usdaeco_check.structure import Context, applicability


@pytest.mark.parametrize("before,after", [
    ("aeco:buildUp:materials", "aeco:foreign:materials"),
    ("totalThickness = 0", "totalThickness = 1"),
    ('token apiSchemaType = "singleApply"',
     'token apiSchemaType = "singleApply"\n        token[] apiSchemaCanOnlyApplyTo = ["Typed"]'),
    ('string aecoApplicability = "unrestricted"', ''),
    (APPLICABILITY_REASON, ''),
    ('string className = "BuildUpAPI"',
     'string className = "BuildUpAPI"\n        string unexpected = "metadata"'),
])
def test_schema_drift_is_refused(tmp_path, before, after):
    (tmp_path / "usdAecoBuildUp").mkdir()
    (tmp_path / "testenv/baseline").mkdir(parents=True)
    baseline = "testenv/baseline/schema-v0.1.2.usda"
    shutil.copyfile(ROOT / baseline, tmp_path / baseline)
    source = (ROOT / "usdAecoBuildUp/schema.usda").read_text()
    (tmp_path / "usdAecoBuildUp/schema.usda").write_text(source.replace(before, after))
    with pytest.raises(ValueError, match="differ from v0.1.2"):
        legacy_contract(tmp_path)
    # Matching edits to the baseline cannot widen the exception.
    (tmp_path / baseline).write_text(source.replace(before, after))
    with pytest.raises(ValueError, match="baseline digest differs"):
        legacy_contract(tmp_path)


def test_untyped_catalog_applicability_passes_upstream_s10():
    applicability(Context(ROOT, [], []))


@pytest.mark.parametrize("result", [
    Result("S01", False, "missing required root file"),
    Result("S25", False, "term sweep: LICENSE:3, README.md:1"),
])
def test_licence_exception_preserves_other_failures(result):
    with pytest.raises(ValueError, match="not the known licence mismatch"):
        licence_compatibility(ROOT, result)


def test_licence_exception_requires_exact_text(tmp_path):
    shutil.copyfile(ROOT / "library.json", tmp_path / "library.json")
    shutil.copyfile(ROOT / "LICENSE", tmp_path / "LICENSE")
    result = Result("S25", False, "term sweep: LICENSE:3")
    assert licence_compatibility(tmp_path, result)
    with (tmp_path / "LICENSE").open("a") as stream:
        stream.write("changed licence\n")
    with pytest.raises(ValueError, match="differs from the release contract"):
        licence_compatibility(tmp_path, result)
