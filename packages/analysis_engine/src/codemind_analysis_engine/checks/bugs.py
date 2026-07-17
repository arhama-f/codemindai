import re

from tree_sitter import Node

from codemind_analysis_engine.traversal import enclosing_function, find_all, line_range, node_text
from codemind_shared_types.schemas import FindingDraftDTO, FindingEvidenceDTO, ParsedSymbol

_DIVISION_OPERATORS = {"/", "%"}
_TERMINATING_STATEMENT_TYPES = {"return_statement", "throw_statement"}


def _has_zero_guard(function_text: str, divisor_name: str) -> bool:
    name = re.escape(divisor_name)
    patterns = [
        rf"\b{name}\b\s*(===|==|!==|!=)\s*0\b",
        rf"\b0\b\s*(===|==|!==|!=)\s*{name}\b",
        rf"!\s*{name}\b",
        rf"\b{name}\b\s*[<>]=?\s*0\b",
    ]
    return any(re.search(pattern, function_text) for pattern in patterns)


def check_unsafe_division(
    path: str, source: bytes, root: Node, symbols: list[ParsedSymbol]
) -> list[FindingDraftDTO]:
    """Flags `x / y` or `x % y` where `y` is a plain identifier and the
    enclosing function has no visible guard against `y` being zero."""
    findings = []
    for node in find_all(root, {"binary_expression"}):
        operator = node.child_by_field_name("operator")
        if operator is None or node_text(source, operator) not in _DIVISION_OPERATORS:
            continue

        right = node.child_by_field_name("right")
        if right is None or right.type != "identifier":
            continue

        function_node = enclosing_function(node)
        if function_node is None:
            continue

        divisor_name = node_text(source, right)
        if _has_zero_guard(node_text(source, function_node), divisor_name):
            continue

        start_line, end_line = line_range(node)
        findings.append(
            FindingDraftDTO(
                check_id="unsafe-division",
                category="bug",
                title=f"Unguarded division by `{divisor_name}`",
                severity="high",
                confidence="medium",
                explanation=(
                    f"`{node_text(source, node)}` divides by `{divisor_name}` without a "
                    "preceding check that it isn't zero. If it can be zero, this silently "
                    "returns `Infinity`/`NaN` instead of failing predictably."
                ),
                recommended_fix=(
                    f"Add a guard before dividing, e.g. `if ({divisor_name} === 0) {{ ... }}`, "
                    "and decide what should happen in that case."
                ),
                suggested_test=(
                    f"Call this function with `{divisor_name} = 0` and assert it doesn't "
                    "return `Infinity`/`NaN`."
                ),
                execution_path=f"Any call where `{divisor_name}` is 0.",
                file_path=path,
                start_line=start_line,
                end_line=end_line,
                evidence=[
                    FindingEvidenceDTO(
                        file_path=path,
                        start_line=start_line,
                        end_line=end_line,
                        snippet=node_text(source, node),
                    )
                ],
            )
        )
    return findings


def check_empty_catch_block(
    path: str, source: bytes, root: Node, symbols: list[ParsedSymbol]
) -> list[FindingDraftDTO]:
    """Flags `catch` blocks with no body — errors silently discarded."""
    findings = []
    for node in find_all(root, {"catch_clause"}):
        body = node.child_by_field_name("body")
        if body is None or body.named_child_count > 0:
            continue

        start_line, end_line = line_range(node)
        findings.append(
            FindingDraftDTO(
                check_id="empty-catch-block",
                category="bug",
                title="Empty catch block swallows errors",
                severity="medium",
                confidence="high",
                explanation=(
                    "This catch block has no body — any error thrown here is silently "
                    "discarded, making failures invisible to callers and logs."
                ),
                recommended_fix=(
                    "At minimum log the error (e.g. `console.error(e)`), or handle/rethrow it "
                    "explicitly."
                ),
                suggested_test=(
                    "Force the try block to throw and assert the error is observable "
                    "(logged, rethrown, or reflected in the return value)."
                ),
                execution_path="Any call where the code inside the try block throws.",
                file_path=path,
                start_line=start_line,
                end_line=end_line,
                evidence=[
                    FindingEvidenceDTO(
                        file_path=path,
                        start_line=start_line,
                        end_line=end_line,
                        snippet=node_text(source, node),
                    )
                ],
            )
        )
    return findings


def check_unreachable_code_after_return(
    path: str, source: bytes, root: Node, symbols: list[ParsedSymbol]
) -> list[FindingDraftDTO]:
    """Flags statements following a return/throw within the same block."""
    findings = []
    for block in find_all(root, {"statement_block"}):
        named_children = [c for c in block.children if c.is_named]
        terminator_index = next(
            (i for i, c in enumerate(named_children) if c.type in _TERMINATING_STATEMENT_TYPES),
            None,
        )
        if terminator_index is None:
            continue

        unreachable = named_children[terminator_index + 1 :]
        if not unreachable:
            continue

        first_unreachable = unreachable[0]
        start_line = first_unreachable.start_point[0] + 1
        end_line = unreachable[-1].end_point[0] + 1

        findings.append(
            FindingDraftDTO(
                check_id="unreachable-code-after-return",
                category="bug",
                title="Unreachable code after return/throw",
                severity="low",
                confidence="high",
                explanation=(
                    "This code appears after a `return`/`throw` in the same block, so it can "
                    "never execute."
                ),
                recommended_fix=(
                    "Remove the dead code, or move it before the return/throw if it was "
                    "meant to run first."
                ),
                suggested_test=None,
                execution_path=None,
                file_path=path,
                start_line=start_line,
                end_line=end_line,
                evidence=[
                    FindingEvidenceDTO(
                        file_path=path,
                        start_line=start_line,
                        end_line=end_line,
                        snippet=node_text(source, first_unreachable),
                    )
                ],
            )
        )
    return findings
