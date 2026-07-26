def build_commit_prompt(diff: str) -> str:
    """Build a prompt for generating a Git commit message."""

    return f"""
Generate a concise Conventional Commit message for the following Git diff.

Requirements:
- Return only the commit message.
- Use the Conventional Commits specification.
- Keep the subject under 72 characters.
- Leave one blank line after the subject.
- Use 3–6 bullet points for the body when appropriate.
- Use dashes (-) as bullets
- Start each bullet with an imperative verb (e.g., Add, Update,
  Remove, Refactor, Fix).
- End each line with a period
- Each bullet should describe one significant change.
- Keep each bullet concise.
- Do not use Markdown headings or explanations outside the commit.

Git diff:

{diff}
""".strip()
