from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from diffsage.config.defaults import DEFAULT_CONFIG
from diffsage.config.resolver import (
    configuration_sources,
    resolve_config_path,
    resolve_settings,
)
from diffsage.config.schema import PartialDiffSageConfig, PartialNetworkConfig
from diffsage.config.scope import ConfigScope
from diffsage.exceptions import LocalConfigUnavailableError


@pytest.mark.usefixtures("clean_diffsage_env")
def test_resolver_uses_defaults_when_no_config_files_exist():
    with (
        patch(
            "diffsage.config.resolver.load_dotenv",
            return_value=None,
        ),
        patch(
            "diffsage.config.resolver.get_global_config_path",
            return_value=Path("/does/not/exist/config.toml"),
        ),
        patch(
            "diffsage.config.resolver.get_local_config_path",
            return_value=Path("/does/not/exist/.diffsage.toml"),
        ),
        patch("diffsage.config.resolver.load_config") as mock_loader,
    ):
        settings = resolve_settings()

    assert settings.provider == DEFAULT_CONFIG.ai.provider
    assert settings.ai_model == DEFAULT_CONFIG.ai.model
    assert settings.timeout == DEFAULT_CONFIG.network.timeout
    mock_loader.assert_not_called()


@pytest.mark.usefixtures("clean_diffsage_env")
def test_resolver_uses_global_config_values():
    mock_global_path = Mock(spec=Path)
    mock_global_path.exists.return_value = True

    with (
        patch(
            "diffsage.config.resolver.load_dotenv",
            return_value=None,
        ),
        patch(
            "diffsage.config.resolver.get_global_config_path",
            return_value=mock_global_path,
        ),
        patch(
            "diffsage.config.resolver.get_local_config_path",
            return_value=Path("/does/not/exist/.diffsage.toml"),
        ),
        patch(
            "diffsage.config.resolver.load_config",
            return_value=PartialDiffSageConfig(
                network=PartialNetworkConfig(
                    timeout=50,
                )
            ),
        ) as mock_loader,
    ):
        settings = resolve_settings()

    assert settings.timeout == 50
    assert settings.provider == DEFAULT_CONFIG.ai.provider
    assert settings.ai_model == DEFAULT_CONFIG.ai.model
    mock_loader.assert_called_once()


@pytest.mark.usefixtures("clean_diffsage_env")
def test_resolver_uses_local_config_values():
    mock_global_path = Mock(spec=Path)
    mock_global_path.exists.return_value = True

    mock_local_path = Mock(spec=Path)
    mock_local_path.exists.return_value = True

    global_config = PartialDiffSageConfig(
        network=PartialNetworkConfig(
            timeout=50,
        )
    )

    local_config = PartialDiffSageConfig(
        network=PartialNetworkConfig(
            timeout=100,
        )
    )

    with (
        patch(
            "diffsage.config.resolver.load_dotenv",
            return_value=None,
        ),
        patch(
            "diffsage.config.resolver.get_global_config_path",
            return_value=mock_global_path,
        ),
        patch(
            "diffsage.config.resolver.get_local_config_path",
            return_value=mock_local_path,
        ),
        patch(
            "diffsage.config.resolver.load_config",
            side_effect=[
                global_config,
                local_config,
            ],
        ) as mock_loader,
    ):
        settings = resolve_settings()

    assert settings.timeout == 100
    assert mock_loader.call_count == 2


@pytest.mark.usefixtures("clean_diffsage_env")
def test_resolver_uses_env_config_values(monkeypatch):
    mock_global_path = Mock(spec=Path)
    mock_global_path.exists.return_value = True

    mock_local_path = Mock(spec=Path)
    mock_local_path.exists.return_value = True

    global_config = PartialDiffSageConfig(
        network=PartialNetworkConfig(
            timeout=50,
        )
    )

    local_config = PartialDiffSageConfig(
        network=PartialNetworkConfig(
            timeout=100,
        )
    )

    with (
        patch(
            "diffsage.config.resolver.load_dotenv",
            return_value=None,
        ),
        patch(
            "diffsage.config.resolver.get_global_config_path",
            return_value=mock_global_path,
        ),
        patch(
            "diffsage.config.resolver.get_local_config_path",
            return_value=mock_local_path,
        ),
        patch(
            "diffsage.config.resolver.load_config",
            side_effect=[
                global_config,
                local_config,
            ],
        ) as mock_loader,
    ):
        monkeypatch.setenv(
            "DIFFSAGE_TIMEOUT",
            "200",
        )
        settings = resolve_settings()

        assert settings.timeout == 200
        assert mock_loader.call_count == 2


@pytest.mark.usefixtures("isolated_env")
def test_resolve_config_path_local_outside_repository_raises() -> None:
    with pytest.raises(LocalConfigUnavailableError, match="needs a Git repository"):
        resolve_config_path(ConfigScope.LOCAL)


def test_resolve_config_path_local_inside_repository(git_repo) -> None:
    assert resolve_config_path(ConfigScope.LOCAL) == git_repo / ".diffsage.toml"


@pytest.mark.usefixtures("isolated_env")
def test_configuration_sources_is_empty_without_files_or_variables() -> None:
    sources = configuration_sources()

    assert sources.global_file is None
    assert sources.local_file is None
    assert sources.environment == []


def test_configuration_sources_lists_existing_files_and_set_variables(
    isolated_env, git_repo, monkeypatch
) -> None:
    isolated_env.config_dir.mkdir(parents=True, exist_ok=True)
    global_file = isolated_env.config_dir / "config.toml"
    global_file.write_text("[network]\ntimeout = 40\n")
    monkeypatch.setenv("DIFFSAGE_MAX_RETRIES", "7")

    sources = configuration_sources()

    assert sources.global_file == global_file
    assert sources.local_file is None
    assert sources.environment == ["DIFFSAGE_MAX_RETRIES"]

    (git_repo / ".diffsage.toml").write_text("[network]\ntimeout = 50\n")

    assert configuration_sources().local_file == git_repo / ".diffsage.toml"
