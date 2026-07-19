from codemind_analysis_engine import filter_findings_to_added_lines
from codemind_shared_types.schemas import FindingDraftDTO


def _finding(start_line: int) -> FindingDraftDTO:
    return FindingDraftDTO(
        check_id="unsafe-division",
        category="bug",
        title="Unguarded division",
        severity="high",
        confidence="medium",
        explanation="explanation",
        recommended_fix="fix",
        file_path="src/utils/math.ts",
        start_line=start_line,
        end_line=start_line,
        evidence=[],
    )


def test_keeps_only_findings_on_added_lines():
    findings = [_finding(2), _finding(5), _finding(9)]
    result = filter_findings_to_added_lines(findings, added_lines={5, 9})
    assert {f.start_line for f in result} == {5, 9}


def test_returns_empty_list_when_no_findings_overlap_added_lines():
    findings = [_finding(2), _finding(3)]
    assert filter_findings_to_added_lines(findings, added_lines={100}) == []


def test_returns_empty_list_for_empty_added_lines():
    findings = [_finding(2)]
    assert filter_findings_to_added_lines(findings, added_lines=set()) == []


def test_empty_findings_list_returns_empty():
    assert filter_findings_to_added_lines([], added_lines={1, 2}) == []
