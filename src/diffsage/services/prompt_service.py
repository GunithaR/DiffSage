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

    def _build_diff_notes(self, notes: list[str] | None) -> str:
        """Explain what DiffSage removed from the diff, so the AI does not describe it."""

        if not notes:
            return ""

        lines = [
            "",
            "",
            "Diff Notes:",
            "DiffSage removed or redacted some content before sending this diff. Treat the "
            "placeholders as unchanged details, never as changes, and do not mention them.",
            *(f"- {note}" for note in notes),
        ]

        return "\n".join(lines)

    def build_commit_prompt(self, context: CommitContext, notes: list[str] | None = None) -> str:
        return (
            f"{self._build_commit_instructions()}\n\n{self._build_commit_context(context)}"
            f"{self._build_diff_notes(notes)}"
        )

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
            lines.append(f"{commit.hash} | {commit.author} | {commit.message} | {commit.date}")

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
                    + ", ".join(category.value for category in analysis.change_categories)
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
                "No repository tests, linters, audits, quality checks were executed by DiffSage.",
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
    - Report testing status only from supplied repository evidence.
    - Describe repository tests, linters, audits, or quality checks only when
    the supplied evidence provides information about them.
    - Do not claim that any check passed unless the supplied evidence explicitly
    confirms that it was executed and passed.
    - If testing evidence is unavailable, use a neutral statement such as
    "Testing status was not provided."
    - Do not mention DiffSage, its execution, its internal analysis, or whether
    DiffSage itself ran repository checks.
    - Treat the supplied risk level as authoritative.
    - Do not upgrade, downgrade, or replace the supplied risk classification.
    - Explain the risk using the supplied risk signals and actual Git diff.
    - Identify the areas reviewers should focus on using the supplied reviewer-focus signals.
    - Identify breaking changes only when supported by repository evidence.
    - Do not invent repository facts, changes, tests, risks, or breaking changes.
    - Use the supplied Git diff and commit history to understand the actual meaning of the changes.
    - Treat deterministic analysis as supporting evidence, not as substitute for inspect Git diff.
    - Return ONLY a valid JSON object.
    - The JSON object MUST contain exactly these fields:
        - title: string
        - summary: string
        - why: string
        - changes: array of strings
        - testing: array of strings
        - risks: array of strings
        - reviewer_focus: array of strings
        - breaking_changes: array of strings
    - Use an empty array when a list section has no applicable content.
    - Do not omit any required field.
    - Do not include Markdown.
    - Do not include code fences.
    - Do not include explanations outside the JSON object.
    """.strip()

    def build_pull_request_prompt(
        self,
        context: PullRequestContext,
        analysis: PullRequestAnalysis,
        notes: list[str] | None = None,
    ) -> str:
        return (
            f"{self._build_pull_request_instructions()}\n\n"
            f"{self._build_pull_request_context(context, analysis)}"
            f"{self._build_diff_notes(notes)}"
        )
