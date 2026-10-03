"""Stand-in for the GitHub CLI used by end-to-end tests.

Behaviour is read from the JSON state file named by FAKE_GH_STATE, and every
invocation is appended to that file so tests can assert on the calls made.
"""

import json
import os
import sys


def main(args: list[str]) -> int:
    state_path = os.environ["FAKE_GH_STATE"]

    with open(state_path, encoding="utf-8") as file:
        state = json.load(file)

    state["calls"].append(args)

    with open(state_path, "w", encoding="utf-8") as file:
        json.dump(state, file)

    if args == ["--version"]:
        print("gh version 2.0.0 (fake)")
        return 0

    if args[:2] == ["auth", "status"]:
        return 0 if state["authenticated"] else 1

    if args[:2] == ["pr", "create"]:
        if state["pr_create_error"]:
            print(state["pr_create_error"], file=sys.stderr)
            return 1

        print(state["pr_url"])
        return 0

    print(f"fake gh: unsupported command {args}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
