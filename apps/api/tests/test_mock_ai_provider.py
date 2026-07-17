from codemind_ai_orchestrator import MockAIProvider
from codemind_shared_types.schemas import FileSummaryDTO, ParsedSymbol, RetrievedChunkDTO

provider = MockAIProvider()


async def test_summarize_file_counts_functions_and_classes():
    symbols = [
        ParsedSymbol(name="add", kind="function", start_line=1, end_line=3, exported=True),
        ParsedSymbol(name="subtract", kind="function", start_line=5, end_line=7, exported=True),
    ]
    result = await provider.summarize_file(file_path="src/utils/math.ts", content="", symbols=symbols)
    assert result == "`src/utils/math.ts` defines 2 function(s) and 0 class(es). Exports: add, subtract."


async def test_summarize_file_with_no_exports():
    result = await provider.summarize_file(file_path="src/empty.ts", content="", symbols=[])
    assert result == "`src/empty.ts` defines 0 function(s) and 0 class(es). Exports: none."


async def test_summarize_directory_aggregates_symbol_kinds():
    file_summaries = [
        FileSummaryDTO(
            file_path="src/utils/math.ts",
            summary="...",
            symbols=[
                ParsedSymbol(name="add", kind="function", start_line=1, end_line=3),
                ParsedSymbol(name="divide", kind="function", start_line=14, end_line=16),
            ],
        ),
        FileSummaryDTO(
            file_path="src/models/user.ts",
            summary="...",
            symbols=[ParsedSymbol(name="User", kind="interface", start_line=3, end_line=8)],
        ),
    ]
    result = await provider.summarize_directory(dir_path="src/utils", file_summaries=file_summaries)
    assert result == (
        "Directory `src/utils` contains 2 file(s) with 3 top-level symbol(s): "
        "function: 2, interface: 1."
    )


async def test_summarize_directory_root_uses_repository_root_label():
    result = await provider.summarize_directory(dir_path=".", file_summaries=[])
    assert result == "Directory repository root contains 0 file(s) with 0 top-level symbol(s): ."


async def test_identify_subsystems_groups_by_top_level_directory():
    subsystems = await provider.identify_subsystems(
        file_paths=[
            "src/utils/math.ts",
            "src/utils/string.ts",
            "src/models/user.ts",
            "src/index.ts",
        ]
    )
    by_name = {s.name: s.file_paths for s in subsystems}
    assert by_name["utils"] == ["src/utils/math.ts", "src/utils/string.ts"]
    assert by_name["models"] == ["src/models/user.ts"]
    assert by_name["root"] == ["src/index.ts"]


async def test_answer_repository_question_with_citations():
    citations = [
        RetrievedChunkDTO(
            file_path="src/utils/math.ts",
            start_line=14,
            end_line=16,
            snippet="export function divide(a: number, b: number): number {\n  return a / b;\n}",
        )
    ]
    answer = await provider.answer_repository_question(question="where is divide?", citations=citations)
    assert "In `src/utils/math.ts:14-16`" in answer
    assert 'These are the most relevant locations found for: "where is divide?".' in answer


async def test_answer_repository_question_with_no_citations():
    answer = await provider.answer_repository_question(question="what does nothing do?", citations=[])
    assert answer == "I couldn't find relevant code for that question in this repository."
