from diffsage.models.git import CommitContext, PullRequestContext
from diffsage.models.pull_request_analysis import PullRequestAnalysis


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

        return """
    Generate a concise Conventional Commit message for the following Git diff.

    Requirements:
    - Return only the commit message.
    - Follow the Conventional Commits specification.
    - Keep the subject under 72 characters.
    - Write the subject in the imperative mood.
    - Leave exactly one blank line after the subject.
    - For simple changes, return only the subject line.
    - For changes affecting multiple files, features, 
      refactoring, architecture, or significant fixes, always include a body.
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
        return f"{self._build_commit_instructions()}\n\n{self._build_commit_context(context)}"

    def _build_pull_request_context(
        self,
        context: PullRequestContext,
        analysis: PullRequestAnalysis,
    ) -> str:
        lines: list[str] = []

        lines.extend(
            [
                "Current Branch:",
                context.current_branch,
                "",
                "Base Branch:",
                context.base_branch,
                "",
                "Merge Base:",
                context.merge_base,
                "",
                "Commits:",
            ]
        )

        for commit in context.commits:
            lines.append(
                f"{commit.hash} | {commit.author} | "
                f"{commit.message} | {commit.date}"
            )

        lines.extend(
            [
                "",
                "Changed Files:",
            ]
        )

        lines.extend(context.changed_files)

        lines.extend(
            [
                "",
                "Branch Diff:",
                context.diff,
                "",
                "Deterministic Analysis:",
                f"Changed Areas: {', '.join(analysis.changed_areas)}",
                (
                    "Changed Categories: "
                    + ", ".join(
                        category.value 
                        for category in analysis.change_categories
                    )
                ),
                "",
                f"Risk Level: {analysis.risk_level.value}",
                "Risk Signals:",
            ]
        )

        lines.extend(analysis.risk_signals)

        lines.extend(
            [
                "",
                "Testing Evidence:",
                "No repository tests, linters, audits, or quality checks were executed by DiffSage.",
                "",
                "Reviewer Focus:",
            ]
        )

        lines.extend(analysis.reviewer_focus)

        return "\n".join(lines)

    def _build_pull_request_instructions(self) -> str:
        return """
    Generate a structured pull request draft from the supplied Git repository evidence.

    Requirements:
    - Generate a concise, descriptive pull request title.
    - Explain what changed in the Summary.
    - Explain the motivation or purpose in Why.
    - Describe the significant changes in Changes.
    - Report testing evidence only from the supplied repository evidence.
    - Do not claim that tests, linters, audits, or quality checks passed unless the supplied evidence explicitly confirms they were executed and passed.
    - If DiffSage did not execute repository checks, state that clearly.
    - Treat the supplied risk level as authoritative.
    - Do not upgrade, downgrade, or replace the supplied risk classification.
    - Explain the risk using the supplied risk signals and actual Git diff.
    - Identify the areas reviewers should focus on using the supplied reviewer-focus signals.
    - Identify breaking changes only when supported by repository evidence.
    - Do not invent repository facts, changes, tests, risks, or breaking changes.
    - Use the supplied Git diff and commit history to understand the actual meaning of the changes.
    - Treat deterministic analysis as repository evidence, not as a substitute for inspecting the diff.
    - Return only the requested structured pull request content.
    """.strip()

    def build_pull_request_prompt(
        self,
        context: PullRequestContext,
        analysis: PullRequestAnalysis,
    ) -> str:
        return (
            f"{self._build_pull_request_instructions()}\n\n"
            f"{self._build_pull_request_context(context, analysis)}"
        )