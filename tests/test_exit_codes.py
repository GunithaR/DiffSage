"""Exit codes are a stable contract for scripts and CI: every error has a deliberate code,
and the README documents exactly the codes the program uses."""

import re
from pathlib import Path

import diffsage.exceptions as exceptions
from diffsage.exceptions import DiffSageError
from diffsage.exit_codes import ExitCode

README = Path(__file__).parent.parent / "README.md"

# Every DiffSage error, by name, with the code it must exit with. A new error class fails
# test_every_error_has_a_deliberate_exit_code until it is added here.
EXPECTED = {
    "DiffSageError": ExitCode.ERROR,
    "EditorError": ExitCode.ERROR,
    "NoTerminalError": ExitCode.USAGE,
    "ConfigError": ExitCode.CONFIGURATION,
    "LocalConfigUnavailableError": ExitCode.CONFIGURATION,
    "UnknownConfigurationKeyError": ExitCode.CONFIGURATION,
    "InvalidConfigurationValueError": ExitCode.CONFIGURATION,
    "CredentialNotFoundError": ExitCode.CREDENTIALS,
    "InvalidCredentialError": ExitCode.CREDENTIALS,
    "InvalidCredentialsFileError": ExitCode.CREDENTIALS,
    "AuthenticationError": ExitCode.CREDENTIALS,
    "GitHubAuthenticationError": ExitCode.CREDENTIALS,
    "GitError": ExitCode.GIT,
    "NotGitRepositoryError": ExitCode.GIT,
    "NoStagedChangesError": ExitCode.GIT,
    "BaseBranchNotFoundError": ExitCode.GIT,
    "RemoteBranchNotFoundError": ExitCode.GIT,
    "UnpushedChangesError": ExitCode.GIT,
    "RemoteAheadError": ExitCode.GIT,
    "BranchesDivergedError": ExitCode.GIT,
    "RemoteUnavailableError": ExitCode.GIT,
    "FetchFailedError": ExitCode.GIT,
    "CommitFailedError": ExitCode.GIT,
    "DetachedHeadError": ExitCode.GIT,
    "SameBranchError": ExitCode.GIT,
    "ProviderError": ExitCode.AI_PROVIDER,
    "RateLimitError": ExitCode.AI_PROVIDER,
    "ModelNotFoundError": ExitCode.AI_PROVIDER,
    "ProviderUnavailableError": ExitCode.AI_PROVIDER,
    "InvalidRequestError": ExitCode.AI_PROVIDER,
    "EmptyResponseError": ExitCode.AI_PROVIDER,
    "ContentBlockedError": ExitCode.AI_PROVIDER,
    "ResponseTruncatedError": ExitCode.AI_PROVIDER,
    "InvalidCommitMessageError": ExitCode.AI_OUTPUT,
    "InvalidPullRequestDraftError": ExitCode.AI_OUTPUT,
    "GitHubError": ExitCode.GITHUB,
    "GitHubCLIUnavailableError": ExitCode.GITHUB,
    "PullRequestExistsError": ExitCode.GITHUB,
}


def all_error_classes() -> dict[str, type[DiffSageError]]:
    found: dict[str, type[DiffSageError]] = {}
    pending = [DiffSageError]

    while pending:
        cls = pending.pop()
        pending.extend(cls.__subclasses__())

        # Only DiffSage's own errors; tests define throwaway subclasses of their own.
        if cls.__module__.startswith("diffsage."):
            found[cls.__name__] = cls

    return found


def test_every_error_has_a_deliberate_exit_code() -> None:
    classes = all_error_classes()

    assert set(classes) == set(EXPECTED), "add new error classes to EXPECTED"
    assert {name: cls.exit_code for name, cls in classes.items()} == EXPECTED


def test_every_error_class_is_exported() -> None:
    assert set(all_error_classes()) <= set(exceptions.__all__)


def test_readme_documents_exactly_the_exit_codes_in_use() -> None:
    section = README.read_text(encoding="utf-8").split("# Exit Codes", 1)[1].split("\n# ", 1)[0]
    documented = [int(code) for code in re.findall(r"^\| (\d+) \|", section, re.M)]

    assert documented == [int(code) for code in ExitCode]
