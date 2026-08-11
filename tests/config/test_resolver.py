from pathlib import Path
from unittest.mock import Mock, patch

from diffsage.config.defaults import DEFAULT_CONFIG
from diffsage.config.resolver import resolve_settings
from diffsage.config.schema import PartialDiffSageConfig, PartialNetworkConfig


def test_resolver_uses_defaults_when_no_config_files_exist(clean_diffsage_env):
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


def test_resolver_uses_global_config_values(clean_diffsage_env):
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


def test_resolver_uses_local_config_values(clean_diffsage_env):
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


def test_resolver_uses_env_config_values(clean_diffsage_env, monkeypatch):
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
