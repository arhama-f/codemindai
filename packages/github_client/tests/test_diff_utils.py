from codemind_github_client.diff_utils import parse_patch_added_lines


def test_single_hunk_single_addition():
    patch = "@@ -1,3 +1,4 @@\n context1\n+added line\n context2\n context3"
    assert parse_patch_added_lines(patch) == {2}


def test_multiple_additions_in_one_hunk():
    patch = "@@ -5,2 +5,4 @@\n context\n+first added\n+second added\n context"
    assert parse_patch_added_lines(patch) == {6, 7}


def test_removed_lines_do_not_consume_new_line_numbers():
    patch = "@@ -1,4 +1,3 @@\n context1\n-removed line\n+added line\n context2"
    # new file: line 1 = context1, line 2 = added line, line 3 = context2
    assert parse_patch_added_lines(patch) == {2}


def test_context_only_hunk_has_no_additions():
    patch = "@@ -1,3 +1,3 @@\n context1\n context2\n context3"
    assert parse_patch_added_lines(patch) == set()


def test_multiple_hunks():
    patch = (
        "@@ -1,2 +1,3 @@\n"
        " context1\n"
        "+added at line 2\n"
        " context3\n"
        "@@ -20,2 +21,3 @@\n"
        " context\n"
        "+added at line 22\n"
        " context"
    )
    assert parse_patch_added_lines(patch) == {2, 22}


def test_diff_header_lines_are_not_treated_as_content():
    patch = "--- a/file.ts\n+++ b/file.ts\n@@ -1,2 +1,3 @@\n context\n+added\n context"
    assert parse_patch_added_lines(patch) == {2}


def test_empty_patch_returns_empty_set():
    assert parse_patch_added_lines("") == set()
