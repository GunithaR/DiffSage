from importlib.metadata import version

from typer.testing import CliRunner

from diffsage.cli import app

runner = CliRunner()


def test_version_option() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == version("diffsage")


def test_short_version_option() -> None:
    result = runner.invoke(app, ["-v"])

    assert result.exit_code == 0
    assert result.stdout.strip() == version("diffsage")
