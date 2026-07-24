from diffsage.models.git import CommitContext

class PromptService:
    def build_commit_prompt(
            self,
            context: CommitContext,
    ) -> str:

        lines: list[str] = [] 

        lines.extend([
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
        ])

        for commit in context.recent_commits:
            lines.append(
                f"{commit.hash} | {commit.author} | {commit.message} | {commit.date}"
            )
    
        return "\n".join(lines)
    