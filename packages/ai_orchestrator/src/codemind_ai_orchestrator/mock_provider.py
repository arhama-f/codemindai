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


class MockAIProvider(AIProvider):
    """Fully deterministic, template-based provider — no external model calls.
    Derives every summary only from already-computed structured inputs (counts
    and names), never timestamps or randomness, so callers can assert exact
    strings in tests."""

    async def summarize_file(
        self, *, file_path: str, content: str, symbols: list[ParsedSymbol]
    ) -> str:
        functions = [s for s in symbols if s.kind == "function"]
        classes = [s for s in symbols if s.kind == "class"]
        exported_names = [s.name for s in symbols if s.exported and s.kind != "method"]
        names_part = ", ".join(exported_names[:5]) if exported_names else "none"
        return (
            f"`{file_path}` defines {len(functions)} function(s) and {len(classes)} class(es). "
            f"Exports: {names_part}."
        )

    async def summarize_directory(
        self, *, dir_path: str, file_summaries: list[FileSummaryDTO]
    ) -> str:
        total_files = len(file_summaries)
        kind_counts: dict[str, int] = {}
        for file_summary in file_summaries:
            for symbol in file_summary.symbols:
                kind_counts[symbol.kind] = kind_counts.get(symbol.kind, 0) + 1
        total_symbols = sum(kind_counts.values())
        kinds_part = ", ".join(f"{kind}: {count}" for kind, count in sorted(kind_counts.items()))
        label = "repository root" if dir_path in (".", "") else f"`{dir_path}`"
        return (
            f"Directory {label} contains {total_files} file(s) with "
            f"{total_symbols} top-level symbol(s): {kinds_part}."
        )

    async def identify_subsystems(self, *, file_paths: list[str]) -> list[SubsystemDTO]:
        groups: dict[str, list[str]] = {}
        for path in file_paths:
            parts = path.split("/")
            if parts and parts[0] == "src":
                parts = parts[1:]
            name = parts[0] if len(parts) > 1 else "root"
            groups.setdefault(name, []).append(path)

        return [
            SubsystemDTO(name=name, file_paths=paths) for name, paths in sorted(groups.items())
        ]

    async def answer_repository_question(
        self, *, question: str, citations: list[RetrievedChunkDTO]
    ) -> str:
        if not citations:
            return "I couldn't find relevant code for that question in this repository."

        sentences = []
        for citation in citations:
            excerpt = " ".join(citation.snippet.split())[:160]
            sentences.append(
                f"In `{citation.file_path}:{citation.start_line}-{citation.end_line}` — {excerpt}"
            )

        closing = f'These are the most relevant locations found for: "{question}".'
        return " ".join(sentences) + " " + closing

    async def propose_fix(
        self, *, finding: FindingDetailDTO, file_content: str
    ) -> ProposedFixDTO:
        explanation = (
            f"Mock proposed fix for `{finding.check_id}` ({finding.category}/{finding.severity}): "
            f"{finding.recommended_fix}"
        )
        marker = (
            f"// TODO(codemind): placeholder fix for finding '{finding.check_id}' — "
            "mock provider does not modify code semantics.\n"
        )
        return ProposedFixDTO(
            explanation=explanation,
            updated_file_content=marker + file_content,
            test_file_path=None,
            test_file_content=None,
        )

    async def summarize_pr_review(
        self, *, pr_title: str, findings: list[FindingDraftDTO]
    ) -> str:
        if not findings:
            return f'No issues found in the diff for "{pr_title}".'

        severity_counts: dict[str, int] = {}
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
        counts_part = ", ".join(
            f"{count} {severity}" for severity, count in sorted(severity_counts.items())
        )
        return (
            f'CodeMind found {len(findings)} issue(s) in the diff for "{pr_title}": '
            f"{counts_part}. See inline comments for details."
        )
