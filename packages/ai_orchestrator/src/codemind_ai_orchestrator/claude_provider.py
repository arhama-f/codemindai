import json

import anthropic

from codemind_ai_orchestrator.interface import AIProvider
from codemind_shared_types.schemas import (
    FileSummaryDTO,
    FindingDetailDTO,
    ParsedSymbol,
    ProposedFixDTO,
    RetrievedChunkDTO,
    SubsystemDTO,
)

DEFAULT_MODEL = "claude-opus-4-8"

FIX_SCHEMA = {
    "type": "object",
    "properties": {
        "explanation": {"type": "string"},
        "updated_file_content": {"type": "string"},
        "test_file_path": {"type": ["string", "null"]},
        "test_file_content": {"type": ["string", "null"]},
    },
    "required": ["explanation", "updated_file_content", "test_file_path", "test_file_content"],
    "additionalProperties": False,
}

_NOT_IMPLEMENTED_MSG = (
    "ClaudeAIProvider only implements propose_fix (round 4 scope). Indexing/summarization "
    "still runs through MockAIProvider — see apps/api/src/codemind_api/providers.py."
)


def _build_prompt(finding: FindingDetailDTO, file_content: str) -> str:
    evidence_text = "\n".join(
        f"- {e.file_path}:{e.start_line}-{e.end_line}\n  {e.snippet}" for e in finding.evidence
    )
    return (
        f"You are fixing a {finding.category} finding in a TypeScript codebase.\n\n"
        f"Check: {finding.check_id}\n"
        f"Title: {finding.title}\n"
        f"Severity: {finding.severity} (confidence: {finding.confidence})\n"
        f"Explanation: {finding.explanation}\n"
        f"Recommended fix: {finding.recommended_fix}\n\n"
        f"Evidence:\n{evidence_text}\n\n"
        f"Full current content of {finding.file_path}:\n"
        f"```\n{file_content}\n```\n\n"
        "Return the full updated file content with the fix applied (not a diff — the "
        "complete file text), a short explanation of the change, and optionally a new "
        "test file (path + content) that exercises the fix. If a test isn't warranted, "
        "leave the test fields null."
    )


class ClaudeAIProvider(AIProvider):
    """Real AI provider backed by the Claude API, used only for `propose_fix`
    (round 4's scope — see docs/architecture.md). Never exercised by the
    automated test suite; wired in only when ANTHROPIC_API_KEY is configured.

    The other AIProvider methods are intentionally not implemented here —
    indexing/summarization stays on MockAIProvider this round, and faking
    those calls on this provider would misrepresent what's actually AI-backed.
    """

    def __init__(self, *, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def summarize_file(
        self, *, file_path: str, content: str, symbols: list[ParsedSymbol]
    ) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    async def summarize_directory(
        self, *, dir_path: str, file_summaries: list[FileSummaryDTO]
    ) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    async def identify_subsystems(self, *, file_paths: list[str]) -> list[SubsystemDTO]:
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    async def answer_repository_question(
        self, *, question: str, citations: list[RetrievedChunkDTO]
    ) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    async def propose_fix(
        self, *, finding: FindingDetailDTO, file_content: str
    ) -> ProposedFixDTO:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=8192,
            output_config={"format": {"type": "json_schema", "schema": FIX_SCHEMA}},
            messages=[{"role": "user", "content": _build_prompt(finding, file_content)}],
        )
        content_block = response.content[0]
        if content_block.type != "text":
            raise RuntimeError(f"Expected a text content block, got {content_block.type!r}")
        result = json.loads(content_block.text)
        return ProposedFixDTO(**result)
