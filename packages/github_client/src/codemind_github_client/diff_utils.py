import re

_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def parse_patch_added_lines(patch: str) -> set[int]:
    """Returns the set of new-file line numbers that are additions ('+' lines)
    in a unified-diff patch string, as returned by GitHub's PR files API.
    These are the only lines GitHub's pull request review API allows a line
    comment to be attached to."""
    added: set[int] = set()
    new_line: int | None = None

    for line in patch.splitlines():
        match = _HUNK_HEADER.match(line)
        if match:
            new_line = int(match.group(1))
            continue
        if new_line is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added.add(new_line)
            new_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            pass  # removed line — doesn't exist in the new file, no line number to consume
        else:
            new_line += 1

    return added
