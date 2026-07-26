from rich.console import Console

from diffsage.config.loader import load_settings
from diffsage.git.client import GitClient
from diffsage.prompts.commit import build_commit_prompt
from diffsage.services.ai_service import AIService

def commit() -> None:
    """Generate an AI-powered Git commit message."""

    git = GitClient()

    console = Console()

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

    console.print()
    console.print("[green]Suggested commit message: [/green]")
    console.print(response.content)