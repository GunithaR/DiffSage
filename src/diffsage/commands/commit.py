from rich.console import Console

from diffsage.config.loader import load_settings
from diffsage.exceptions.git import (
    NotGitRepositoryError, 
    NoStagedChangesError,
)
from diffsage.git.client import GitClient
from diffsage.services.ai_service import AIService
from diffsage.services.commit_service import CommitService
from diffsage.services.editor import EditorService
from diffsage.services.git_service import GitService
from diffsage.services.prompt_service import PromptService
from diffsage.ui.commit_view import CommitView


console = Console()


def generate_message(commit_service: CommitService) -> str:
    try:
        return commit_service.generate_commit_message()

    except NotGitRepositoryError:
        console.print("[red]Not inside a Git repository[/red]")
        raise SystemExit(1)

    except NoStagedChangesError:
        console.print("[yellow]No staged changes found[/yellow]")
        raise SystemExit(1)

def commit() -> None:
    git_client = GitClient()

    settings = load_settings()

    git_service = GitService(git_client)
    ai_service = AIService(settings)
    prompt_service = PromptService()

    commit_service = CommitService(
        git_client,
        git_service,
        prompt_service,
        ai_service,
    )

    editor = EditorService()
    view = CommitView()

    with view.generating():
        message = generate_message(commit_service)

    view.show_commit(message)

    while True:
        console.print()
        choice = console.input(
            "[bold cyan][Y][/bold cyan] Commit  "
            "[bold cyan][E][/bold cyan] Edit  "
            "[bold cyan][R][/bold cyan] Regenerate  "
            "[bold cyan][N][/bold cyan] Cancel: "
        )
        choice = choice.strip().lower()

        if choice in ("", "y"):
            git_client.commit(message)
            console.print(
                f"[bold green]✓ Commit created successfully![/bold green] {message.splitlines()[0]}"
            )
            break

        if choice == "e":
            message = editor.edit(message)
            view.show_commit(message)
            continue

        if choice == "r":
            with view.generating():
                message = generate_message(commit_service)
            view.show_commit(message)
            continue

        if choice == "n":
            console.print("[yellow]Cancelled.[/yellow]")
            break

        console.print("[red]Invalid option. Please choose Y, E, R or N.[/red]")
