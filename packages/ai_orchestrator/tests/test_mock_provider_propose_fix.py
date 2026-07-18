from codemind_ai_orchestrator.mock_provider import MockAIProvider
from codemind_shared_types.schemas import FindingDetailDTO, FindingEvidenceDTO

FINDING = FindingDetailDTO(
    check_id="unsafe-division",
    category="bug",
    title="Unguarded division",
    severity="high",
    confidence="medium",
    explanation="`divide` divides by `b` without checking it is non-zero.",
    recommended_fix="Add a guard: if (b === 0) return 0; before the division.",
    suggested_test=None,
    execution_path=None,
    file_path="src/utils/math.ts",
    start_line=1,
    end_line=3,
    evidence=[
        FindingEvidenceDTO(
            file_path="src/utils/math.ts", start_line=1, end_line=3, snippet="return a / b;"
        )
    ],
)

FILE_CONTENT = "export function divide(a, b) {\n  return a / b;\n}\n"


async def test_propose_fix_explanation_references_the_finding():
    provider = MockAIProvider()
    fix = await provider.propose_fix(finding=FINDING, file_content=FILE_CONTENT)
    assert "unsafe-division" in fix.explanation
    assert "bug/high" in fix.explanation
    assert FINDING.recommended_fix in fix.explanation


async def test_propose_fix_marks_up_content_deterministically_and_no_test_file():
    provider = MockAIProvider()
    fix = await provider.propose_fix(finding=FINDING, file_content=FILE_CONTENT)
    assert fix.updated_file_content.endswith(FILE_CONTENT)
    assert "unsafe-division" in fix.updated_file_content
    assert fix.test_file_path is None
    assert fix.test_file_content is None


async def test_propose_fix_is_deterministic_across_calls():
    provider = MockAIProvider()
    fix1 = await provider.propose_fix(finding=FINDING, file_content=FILE_CONTENT)
    fix2 = await provider.propose_fix(finding=FINDING, file_content=FILE_CONTENT)
    assert fix1 == fix2
