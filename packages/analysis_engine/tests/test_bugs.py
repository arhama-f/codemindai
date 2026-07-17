from pathlib import Path

from codemind_analysis_engine import analyze_file
from codemind_code_parser import parse_file

DEMO_REPO_SRC = Path(__file__).resolve().parents[3] / "fixtures" / "demo-repo" / "src"


def _read(relative_path: str) -> str:
    return (DEMO_REPO_SRC / relative_path).read_text()


def _analyze(path: str, relative_path: str):
    source = _read(relative_path)
    symbols = parse_file(path, source).symbols
    return analyze_file(path, source, symbols)


def test_unsafe_division_fires_on_divide_but_not_percentage_of():
    findings = _analyze("src/utils/math.ts", "utils/math.ts")
    division_findings = [f for f in findings if f.check_id == "unsafe-division"]

    assert len(division_findings) == 1
    finding = division_findings[0]
    assert finding.category == "bug"
    assert finding.severity == "high"
    assert finding.start_line == 15
    assert finding.end_line == 15
    assert "b" in finding.title


def test_empty_catch_block_fires_on_delete_user():
    findings = _analyze("src/services/userService.ts", "services/userService.ts")
    catch_findings = [f for f in findings if f.check_id == "empty-catch-block"]

    assert len(catch_findings) == 1
    assert catch_findings[0].start_line == 25


def test_unreachable_code_after_return_fires_on_truncate():
    findings = _analyze("src/utils/string.ts", "utils/string.ts")
    unreachable_findings = [f for f in findings if f.check_id == "unreachable-code-after-return"]

    assert len(unreachable_findings) == 1
    assert unreachable_findings[0].severity == "low"


def test_no_bug_findings_on_clean_files():
    findings = _analyze("src/models/user.ts", "models/user.ts")
    assert findings == []
