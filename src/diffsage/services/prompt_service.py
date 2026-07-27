from diffsage.models.git import CommitContext


class PromptService:
    def _build_commit_context(
        self,
        context: CommitContext,
    ) -> str:
        lines: list[str] = []

        lines.extend(
            [
                "Branch:",
                context.branch,
                "",
                "Staged Diff:",
                context.staged_diff,
                "",
                "Unstaged Diff:",
                context.unstaged_diff,
                "",
                "Recent Commits:",
            ]
        )

        for commit in context.recent_commits:
            lines.append(f"{commit.hash} | {commit.author} | {commit.message} | {commit.date}")

        return "\n".join(lines)

    def _build_commit_instructions(self) -> str:
        """Build a prompt for generating a Git commit message."""

        return f"""
    Generate a concise Conventional Commit message for the following Git diff.

    Requirements:
    - Return only the commit message.
    - Follow the Conventional Commits specification.
    - Keep the subject under 72 characters.
    - Write the subject in the imperative mood.
    - Leave exactly one blank line after the subject.
    - For simple changes, return only the subject line.
    - For changes affecting multiple files, features, refactoring, architecture, or significant fixes, always include a body.
    - If a body is included, it MUST contain 3–6 bullet points.
    - Use dashes (-) for bullets.
    - Do not write body paragraphs.
    - Start each bullet with an imperative verb (e.g., Add, Update, Remove, Refactor, Fix).
    - End each bullet with a period.
    - Each bullet should describe one significant change.
    - Keep each bullet concise.
    - Do not include Markdown headings, explanations, or code fences.

    Repository Context:

    """.strip()

    def build_commit_prompt(self, context: CommitContext) -> str:
        return(
            f"{self._build_commit_instructions()}\n\n"
            f"{self._build_commit_context(context)}"
        )

