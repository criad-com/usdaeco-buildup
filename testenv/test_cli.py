"""The command line reports actionable sites and exits according to severity."""
from pxr import Usd
from usdaeco_buildup.cli import main


def test_cli_finding_site_and_severity(tmp_path, capsys):
    path = tmp_path / "defect.usda"
    stage = Usd.Stage.CreateNew(str(path))
    prim = stage.DefinePrim("/Example", "Xform")
    stage.SetDefaultPrim(prim)
    prim.ApplyAPI("AecoBuildUpAPI")
    prim.GetAttribute("aeco:buildUp:thicknesses").Set([.2])
    stage.GetRootLayer().Save()
    assert main(["check", str(path)]) == 1
    output = capsys.readouterr().out
    assert "BuildUpArrayLengths: /Example:" in output
    profile = tmp_path / "advisory.json"
    profile.write_text('{"severity_overrides": {"buildUpArrayLengths": "warn"}}')
    assert main(["check", str(path), "--profile", str(profile)]) == 0
    output = capsys.readouterr().out
    assert "BuildUpArrayLengths: /Example:" in output
    assert "0 errors, 1 non-errors" in output
