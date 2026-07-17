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


def test_nested_loop_quadratic_fires_on_has_duplicate_pairs():
    findings = _analyze("src/utils/collections.ts", "utils/collections.ts")
    nested_loop_findings = [f for f in findings if f.check_id == "nested-loop-quadratic"]

    assert len(nested_loop_findings) == 1
    assert nested_loop_findings[0].start_line == 4
    assert len(nested_loop_findings[0].evidence) == 2


def test_array_scan_in_loop_fires_on_dedupe():
    findings = _analyze("src/utils/collections.ts", "utils/collections.ts")
    scan_findings = [f for f in findings if f.check_id == "array-scan-in-loop"]

    assert len(scan_findings) == 1
    assert scan_findings[0].start_line == 19
    assert "includes" in scan_findings[0].title


def test_array_rebuild_in_loop_fires_on_merge_all():
    findings = _analyze("src/utils/collections.ts", "utils/collections.ts")
    rebuild_findings = [f for f in findings if f.check_id == "array-rebuild-in-loop"]

    assert len(rebuild_findings) == 1
    assert rebuild_findings[0].start_line == 31
    assert "result" in rebuild_findings[0].title


def test_no_performance_findings_on_clean_files():
    findings = _analyze("src/models/user.ts", "models/user.ts")
    assert findings == []
