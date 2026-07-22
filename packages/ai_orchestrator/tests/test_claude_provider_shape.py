"""Shape/construction tests only — never calls the real Claude API. Network
behavior is verified once, manually, per the round 4 plan's final step."""

import pytest

from codemind_ai_orchestrator.claude_provider import (
    FIX_SCHEMA,
    ClaudeAIProvider,
    _build_ask_prompt,
    _build_explain_prompt,
    _build_pr_review_prompt,
    _build_prompt,
)
from codemind_shared_types.schemas import (
    FindingDetailDTO,
    FindingDraftDTO,
    FindingEvidenceDTO,
    RetrievedChunkDTO,
)

FINDING = FindingDetailDTO(
    check_id="unsafe-division",
    category="bug",
    title="Unguarded division",
    severity="high",
    confidence="medium",
    explanation="`divide` divides by `b` without checking it is non-zero.",
    recommended_fix="Add a guard: if (b === 0) return 0; before the division.",
    file_path="src/utils/math.ts",
    start_line=1,
    end_line=3,
    evidence=[
        FindingEvidenceDTO(
            file_path="src/utils/math.ts", start_line=1, end_line=3, snippet="return a / b;"
        )
    ],
)


def test_construction_does_not_make_a_network_call():
    provider = ClaudeAIProvider(api_key="sk-test-not-a-real-key")
    assert provider._model == "claude-opus-4-8"


def test_fix_schema_requires_all_fields_and_forbids_extras():
    assert FIX_SCHEMA["additionalProperties"] is False
    assert set(FIX_SCHEMA["required"]) == {
        "explanation",
        "updated_file_content",
        "test_file_path",
        "test_file_content",
    }


def test_build_prompt_includes_finding_and_file_content():
    prompt = _build_prompt(FINDING, "export function divide(a, b) {\n  return a / b;\n}\n")
    assert "unsafe-division" in prompt
    assert "src/utils/math.ts" in prompt
    assert "return a / b;" in prompt
    assert FINDING.recommended_fix in prompt


async def test_indexing_time_methods_raise_not_implemented():
    provider = ClaudeAIProvider(api_key="sk-test-not-a-real-key")
    with pytest.raises(NotImplementedError):
        await provider.summarize_file(file_path="x.ts", content="", symbols=[])
    with pytest.raises(NotImplementedError):
        await provider.summarize_directory(dir_path=".", file_summaries=[])
    with pytest.raises(NotImplementedError):
        await provider.identify_subsystems(file_paths=[])


def test_build_ask_prompt_includes_question_and_citations():
    citations = [
        RetrievedChunkDTO(
            file_path="src/utils/math.ts",
            start_line=14,
            end_line=16,
            snippet="export function divide(a: number, b: number): number {\n  return a / b;\n}",
        )
    ]
    prompt = _build_ask_prompt("how do I divide two numbers?", citations)
    assert "how do I divide two numbers?" in prompt
    assert "src/utils/math.ts:14-16" in prompt
    assert "export function divide" in prompt


def test_build_ask_prompt_with_no_citations_asks_for_an_honest_no_match_response():
    prompt = _build_ask_prompt("what does this repo do?", [])
    assert "what does this repo do?" in prompt
    assert "no relevant code was found" in prompt
    assert "Do not speculate" in prompt


def test_build_explain_prompt_includes_finding_and_evidence():
    prompt = _build_explain_prompt(FINDING)
    assert "unsafe-division" in prompt
    assert "src/utils/math.ts" in prompt
    assert "return a / b;" in prompt
    assert FINDING.explanation in prompt
    assert "Do not repeat the template text verbatim" in prompt


def test_build_pr_review_prompt_includes_title_and_findings():
    findings = [
        FindingDraftDTO(
            check_id="unsafe-division",
            category="bug",
            title="Unguarded division",
            severity="high",
            confidence="medium",
            explanation="divides without a zero check",
            recommended_fix="add a guard",
            file_path="src/utils/math.ts",
            start_line=2,
            end_line=2,
            evidence=[],
        )
    ]
    prompt = _build_pr_review_prompt("Fix divide bug", findings)
    assert "Fix divide bug" in prompt
    assert "Unguarded division" in prompt
    assert "src/utils/math.ts:2" in prompt
    assert "divides without a zero check" in prompt
