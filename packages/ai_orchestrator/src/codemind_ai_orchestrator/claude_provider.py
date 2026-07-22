import json

import anthropic

from codemind_ai_orchestrator.interface import AIProvider
from codemind_shared_types.schemas import (
    FileSummaryDTO,
    FindingDetailDTO,
    FindingDraftDTO,
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
    "ClaudeAIProvider only implements propose_fix, summarize_pr_review, "
    "explain_finding, and answer_repository_question. Indexing-time "
    "summarization still runs through MockAIProvider — see "
    "apps/api/src/codemind_api/providers.py."
)


def _extract_text(response: anthropic.types.Message) -> str:
    content_block = response.content[0]
    if content_block.type != "text":
        raise RuntimeError(f"Expected a text content block, got {content_block.type!r}")
    return content_block.text


def _build_ask_prompt(question: str, citations: list[RetrievedChunkDTO]) -> str:
    if not citations:
        return (
            f'A user asked the following question about a codebase, but no relevant code '
            f'was found:\n\n"{question}"\n\n'
            "Write a brief, honest response explaining that no relevant code was found for "
            "this question in the repository. Do not speculate about what the answer might be."
        )
    citations_text = "\n\n".join(
        f"- {c.file_path}:{c.start_line}-{c.end_line}\n```\n{c.snippet}\n```" for c in citations
    )
    return (
        f'A user asked the following question about a codebase:\n\n"{question}"\n\n'
        f"Here is the relevant code, found via semantic search:\n\n{citations_text}\n\n"
        "Answer the question directly, citing specific files and line ranges from the "
        "code above. Do not reference code that isn't shown above. Keep the answer "
        "focused and concise — a few sentences unless the question needs more detail."
    )


def _build_pr_review_prompt(pr_title: str, findings: list[FindingDraftDTO]) -> str:
    findings_text = "\n\n".join(
        f"- {f.severity}/{f.category} at {f.file_path}:{f.start_line} — {f.title}\n"
        f"  {f.explanation}"
        for f in findings
    )
    return (
        f'Write a short (2-4 sentence) summary for a GitHub pull request review comment.\n\n'
        f'PR title: "{pr_title}"\n\n'
        f"Findings in this PR's diff:\n{findings_text}\n\n"
        "Write only the summary paragraph — no preamble, no markdown headers. It will be "
        "posted as the top-level body of a PR review, above the inline comments."
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


def _build_explain_prompt(finding: FindingDetailDTO) -> str:
    evidence_text = "\n".join(
        f"- {e.file_path}:{e.start_line}-{e.end_line}\n  {e.snippet}" for e in finding.evidence
    )
    return (
        f"You are explaining a {finding.category} finding in a TypeScript codebase to a "
        "developer who will decide whether and how to fix it.\n\n"
        f"Check: {finding.check_id}\n"
        f"Title: {finding.title}\n"
        f"Severity: {finding.severity} (confidence: {finding.confidence})\n"
        f"Template explanation: {finding.explanation}\n"
        f"Template recommended fix: {finding.recommended_fix}\n\n"
        f"Evidence:\n{evidence_text}\n\n"
        "Write a deeper explanation (a short paragraph) of why this is a real problem here "
        "specifically — the concrete failure mode or real-world impact given this evidence, "
        "not a generic description of the check. Do not repeat the template text verbatim. "
        "Return only the explanation text, no headers or preamble."
    )


class ClaudeAIProvider(AIProvider):
    """Real AI provider backed by the Claude API: `propose_fix` and
    `summarize_pr_review` write AI-generated text to a real GitHub PR;
    `answer_repository_question` composes a real answer over already-real
    (embedding-based) retrieval for `/ask`; `explain_finding` composes a
    deeper, evidence-specific explanation for a single finding (see
    docs/architecture.md). Never exercised by the automated test suite;
    wired in only when ANTHROPIC_API_KEY is set.

    The other AIProvider methods are intentionally not implemented here —
    indexing-time summarization stays on MockAIProvider, and faking those
    calls on this provider would misrepresent what's actually AI-backed.
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
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": _build_ask_prompt(question, citations)}],
        )
        return _extract_text(response)

    async def propose_fix(
        self, *, finding: FindingDetailDTO, file_content: str
    ) -> ProposedFixDTO:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=8192,
            output_config={"format": {"type": "json_schema", "schema": FIX_SCHEMA}},
            messages=[{"role": "user", "content": _build_prompt(finding, file_content)}],
        )
        result = json.loads(_extract_text(response))
        return ProposedFixDTO(**result)

    async def summarize_pr_review(
        self, *, pr_title: str, findings: list[FindingDraftDTO]
    ) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": _build_pr_review_prompt(pr_title, findings)}
            ],
        )
        return _extract_text(response)

    async def explain_finding(self, *, finding: FindingDetailDTO) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": _build_explain_prompt(finding)}],
        )
        return _extract_text(response)
