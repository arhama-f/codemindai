"""Shape/construction tests only — never calls the real Claude API. Network
behavior is verified once, manually, per the round 4 plan's final step."""

import pytest

from codemind_ai_orchestrator.claude_provider import (
    FIX_SCHEMA,
    ClaudeAIProvider,
    _build_prompt,
)
from codemind_shared_types.schemas import FindingDetailDTO, FindingEvidenceDTO

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


async def test_other_methods_raise_not_implemented():
    provider = ClaudeAIProvider(api_key="sk-test-not-a-real-key")
    with pytest.raises(NotImplementedError):
        await provider.summarize_file(file_path="x.ts", content="", symbols=[])
    with pytest.raises(NotImplementedError):
        await provider.summarize_directory(dir_path=".", file_summaries=[])
    with pytest.raises(NotImplementedError):
        await provider.identify_subsystems(file_paths=[])
    with pytest.raises(NotImplementedError):
        await provider.answer_repository_question(question="?", citations=[])
