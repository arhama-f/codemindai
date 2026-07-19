from codemind_shared_types.schemas import FindingDraftDTO


def filter_findings_to_added_lines(
    findings: list[FindingDraftDTO], added_lines: set[int]
) -> list[FindingDraftDTO]:
    """Keeps only findings whose `start_line` is a line added by the diff —
    issues actually introduced by this change, not pre-existing ones outside
    it. Also a hard requirement of GitHub's PR review API: a line comment can
    only be attached to a line that appears in the diff."""
    return [finding for finding in findings if finding.start_line in added_lines]
