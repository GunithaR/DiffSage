from diffsage.prompts.commit import build_commit_prompt


def test_build_commit_prompt_includes_diff():
    diff = """\
diff --git a/README.md b/README.md
+New Content
"""

    prompt = build_commit_prompt(diff)

    assert "diff --git a/README.md b/README.md" in prompt
    assert "+New Content" in prompt

def test_build_commit_prompt_contains_commit_instructions():
    prompt = build_commit_prompt("dummy diff")

    assert "Conventional Commit" in prompt
    assert "Return only the commit message" in prompt
    assert "Do not include explanations" in prompt