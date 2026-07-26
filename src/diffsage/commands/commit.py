from rich.console import Console

from diffsage.config.loader import load_settings
from diffsage.git.client import GitClient
from diffsage.prompts.commit import build_commit_prompt
from diffsage.services.ai_service import AIService
from diffsage.services.editor import EditorService

console = Console()

def generate_commit_message(git: GitClient) -> str:
    """Generate an AI-powered Git commit message."""

    if not git.is_git_repository():
        console.print("[red]Not inside a Git repository[/red]")
        raise SystemExit(1)

    diff = git.staged_diff()

    if not diff:
        console.print("[yellow]No staged changes found[/yellow]")
        raise SystemExit(1)

    prompt = build_commit_prompt(diff)

    settings = load_settings()
    ai = AIService(settings)

    response = ai.ask(prompt)

    return response.content

def display_commit_message(message: str) -> None:
    console.print()
    console.print("[green]Suggested commit message:[/green]")
    console.print(message)

def commit() -> None:
    git = GitClient()
    editor = EditorService()

    message = generate_commit_message(git)
    display_commit_message(message)

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
            git.commit(message)
            console.print(f"[bold green]✓ Commit created successfully![/bold green] {message.splitlines()[0]}")
            break

        if choice == "e":
            message = editor.edit(message)
            display_commit_message(message)
            continue

        if choice == "r":
            message = generate_commit_message(git)
            display_commit_message(message)
            continue

        if choice == "n":
            console.print("[yellow]Cancelled.[/yellow]")
            break

        console.print("[red]Invalid option. Please choose Y, E, R or N.[/red]")

