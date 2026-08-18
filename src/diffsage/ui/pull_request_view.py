from contextlib import contextmanager

from rich.panel import Panel
from rich.text import Text

from diffsage.models.pull_request import PullRequestDraft
from diffsage.ui.base import BaseView


class PullRequestView(BaseView):
    """Handles terminal rendering for the pull request command."""

    def _add_list_section(
        self,
        text: Text,
        heading: str,
        values: list[str],
    ) -> None:
        text.append(f"{heading}\n", style="bold cyan")

        if values:
            for value in values:
                text.append(f"• {value}\n")
        else:
            text.append("None\n", style="dim")

    @contextmanager
    def generating(self):
        with self._console.status("Generating pull request draft..."):
            yield

    def show_generated(self, draft: PullRequestDraft) -> None:
        content = Text()

        content.append("Title\n", style="bold cyan")
        content.append(f"{draft.title}\n\n")

        content.append("Summary\n", style="bold cyan")
        content.append(f"{draft.summary}\n\n")

        content.append("Why\n", style="bold cyan")
        content.append(f"{draft.why}\n\n")

        self._add_list_section(content, "Changes", draft.changes)
        content.append("\n")

        self._add_list_section(content, "Testing", draft.testing)
        content.append("\n")

        self._add_list_section(content, "Risks", draft.risks)
        content.append("\n")

        self._add_list_section(
            content,
            "Reviewer Focus",
            draft.reviewer_focus,
        )
        content.append("\n")

        self._add_list_section(
            content,
            "Breaking Changes",
            draft.breaking_changes,
        )

        self._console.print()
        self._console.print(
            Panel(
                content,
                title="[bold cyan]Pull Request Draft[/bold cyan]",
                expand=False,
            )
        )

    def show_not_git_repository(self) -> None:
        self._console.print("[red]Not inside a Git repository[/red]")

    def show_detached_head(self) -> None:
        self._console.print("[red]Cannot generate a pull request from a detached HEAD.[/red]")

    def show_base_branch_not_found(self) -> None:
        self._console.print("[red]Could not determine the base branch.[/red]")

    def show_same_branch(self) -> None:
        self._console.print("[yellow]Current branch and base branch are the same.[/yellow]")
