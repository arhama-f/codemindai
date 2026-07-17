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


def test_hardcoded_secret_and_sensitive_logging_fire_on_config_ts():
    findings = _analyze("src/config.ts", "config.ts")

    secret_findings = [f for f in findings if f.check_id == "hardcoded-secret"]
    assert len(secret_findings) == 1
    assert secret_findings[0].severity == "critical"
    assert secret_findings[0].start_line == 3

    logging_findings = [f for f in findings if f.check_id == "sensitive-data-logging"]
    assert len(logging_findings) == 1
    assert logging_findings[0].start_line == 4
    assert "apiKey" in logging_findings[0].title


def test_dangerously_set_inner_html_fires_on_user_card():
    findings = _analyze("src/components/UserCard.tsx", "components/UserCard.tsx")
    xss_findings = [f for f in findings if f.check_id == "unsafe-dangerously-set-inner-html"]

    assert len(xss_findings) == 1
    assert xss_findings[0].severity == "high"
    assert xss_findings[0].start_line == 16


def test_no_security_findings_on_clean_files():
    findings = _analyze("src/models/user.ts", "models/user.ts")
    assert findings == []
