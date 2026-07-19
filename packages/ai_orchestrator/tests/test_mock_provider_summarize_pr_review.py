from codemind_ai_orchestrator.mock_provider import MockAIProvider
from codemind_shared_types.schemas import FindingDraftDTO

HIGH_FINDING = FindingDraftDTO(
    check_id="unsafe-division",
    category="bug",
    title="Unguarded division",
    severity="high",
    confidence="medium",
    explanation="explanation",
    recommended_fix="fix",
    file_path="src/utils/math.ts",
    start_line=2,
    end_line=2,
    evidence=[],
)

MEDIUM_FINDING = FindingDraftDTO(
    check_id="array-scan-in-loop",
    category="performance",
    title="Linear scan in loop",
    severity="medium",
    confidence="medium",
    explanation="explanation",
    recommended_fix="fix",
    file_path="src/utils/collections.ts",
    start_line=5,
    end_line=5,
    evidence=[],
)


async def test_summarize_pr_review_with_no_findings():
    provider = MockAIProvider()
    summary = await provider.summarize_pr_review(pr_title="Fix divide bug", findings=[])
    assert "No issues found" in summary
    assert "Fix divide bug" in summary


async def test_summarize_pr_review_with_findings_includes_counts_by_severity():
    provider = MockAIProvider()
    summary = await provider.summarize_pr_review(
        pr_title="Fix divide bug", findings=[HIGH_FINDING, MEDIUM_FINDING]
    )
    assert "2 issue(s)" in summary
    assert "1 high" in summary
    assert "1 medium" in summary
    assert "Fix divide bug" in summary


async def test_summarize_pr_review_is_deterministic():
    provider = MockAIProvider()
    s1 = await provider.summarize_pr_review(pr_title="X", findings=[HIGH_FINDING])
    s2 = await provider.summarize_pr_review(pr_title="X", findings=[HIGH_FINDING])
    assert s1 == s2
