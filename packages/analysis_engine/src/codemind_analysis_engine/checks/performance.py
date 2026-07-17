from tree_sitter import Node

from codemind_analysis_engine.traversal import find_all, line_range, node_text
from codemind_shared_types.schemas import FindingDraftDTO, FindingEvidenceDTO, ParsedSymbol

_LOOP_TYPES = {"for_statement", "for_in_statement", "while_statement", "do_statement"}
_LINEAR_SCAN_METHODS = {"includes", "indexOf", "find", "findIndex"}


def _loop_body(node: Node) -> Node | None:
    return node.child_by_field_name("body")


def check_nested_loop_quadratic(
    path: str, source: bytes, root: Node, symbols: list[ParsedSymbol]
) -> list[FindingDraftDTO]:
    """Flags a loop nested inside another loop — an O(n^2)-shaped pattern."""
    findings = []
    for outer in find_all(root, _LOOP_TYPES):
        body = _loop_body(outer)
        if body is None:
            continue
        inner_loops = find_all(body, _LOOP_TYPES)
        if not inner_loops:
            continue

        inner = inner_loops[0]
        outer_start, outer_end = line_range(outer)
        inner_start, inner_end = line_range(inner)

        findings.append(
            FindingDraftDTO(
                check_id="nested-loop-quadratic",
                category="performance",
                title="Nested loop over the same data (O(n²)-shaped)",
                severity="medium",
                confidence="high",
                explanation=(
                    "A loop is nested inside another loop, so the work grows quadratically "
                    "with input size. For large inputs this can become a real bottleneck."
                ),
                recommended_fix=(
                    "Consider a lookup structure (e.g. a `Set`/`Map`) to avoid the inner scan, "
                    "or restructure the algorithm to avoid comparing every pair."
                ),
                suggested_test=(
                    "Benchmark this function with a large input and confirm runtime scales "
                    "roughly linearly after the fix, not quadratically."
                ),
                execution_path="Any call with a non-trivially-sized input list.",
                file_path=path,
                start_line=outer_start,
                end_line=outer_end,
                evidence=[
                    FindingEvidenceDTO(
                        file_path=path,
                        start_line=outer_start,
                        end_line=outer_end,
                        snippet=node_text(source, outer).splitlines()[0],
                    ),
                    FindingEvidenceDTO(
                        file_path=path,
                        start_line=inner_start,
                        end_line=inner_end,
                        snippet=node_text(source, inner).splitlines()[0],
                    ),
                ],
            )
        )
    return findings


def check_array_scan_in_loop(
    path: str, source: bytes, root: Node, symbols: list[ParsedSymbol]
) -> list[FindingDraftDTO]:
    """Flags `.includes()`/`.indexOf()`/`.find()`/`.findIndex()` calls inside a
    loop body — each iteration re-scans the target array linearly."""
    findings = []
    for loop in find_all(root, _LOOP_TYPES):
        body = _loop_body(loop)
        if body is None:
            continue

        for call in find_all(body, {"call_expression"}):
            function_node = call.child_by_field_name("function")
            if function_node is None or function_node.type != "member_expression":
                continue
            property_node = function_node.child_by_field_name("property")
            if property_node is None or node_text(source, property_node) not in _LINEAR_SCAN_METHODS:
                continue

            start_line, end_line = line_range(call)
            method_name = node_text(source, property_node)
            findings.append(
                FindingDraftDTO(
                    check_id="array-scan-in-loop",
                    category="performance",
                    title=f"`.{method_name}()` called inside a loop",
                    severity="low",
                    confidence="medium",
                    explanation=(
                        f"`.{method_name}()` performs a linear scan. Calling it once per loop "
                        "iteration makes the whole loop O(n²) in the size of the scanned array."
                    ),
                    recommended_fix=(
                        "Build a `Set`/`Map` once before the loop and check membership in "
                        "O(1), instead of re-scanning an array on every iteration."
                    ),
                    suggested_test=None,
                    execution_path="Any call where the loop and scanned array are both large.",
                    file_path=path,
                    start_line=start_line,
                    end_line=end_line,
                    evidence=[
                        FindingEvidenceDTO(
                            file_path=path,
                            start_line=start_line,
                            end_line=end_line,
                            snippet=node_text(source, call),
                        )
                    ],
                )
            )
    return findings


def check_array_rebuild_in_loop(
    path: str, source: bytes, root: Node, symbols: list[ParsedSymbol]
) -> list[FindingDraftDTO]:
    """Flags `x = [...x, ...y]`-shaped reassignment inside a loop — rebuilds
    the whole array each iteration instead of appending in place."""
    findings = []
    for loop in find_all(root, _LOOP_TYPES):
        body = _loop_body(loop)
        if body is None:
            continue

        for assignment in find_all(body, {"assignment_expression"}):
            left = assignment.child_by_field_name("left")
            right = assignment.child_by_field_name("right")
            if left is None or right is None or left.type != "identifier" or right.type != "array":
                continue

            target_name = node_text(source, left)
            spreads_target = any(
                child.type == "spread_element"
                and len(child.children) > 1
                and node_text(source, child.children[1]) == target_name
                for child in right.named_children
            )
            if not spreads_target:
                continue

            start_line, end_line = line_range(assignment)
            findings.append(
                FindingDraftDTO(
                    check_id="array-rebuild-in-loop",
                    category="performance",
                    title=f"`{target_name}` rebuilt from scratch every iteration",
                    severity="medium",
                    confidence="high",
                    explanation=(
                        f"`{target_name} = [...{target_name}, ...]` copies the entire array on "
                        "every iteration, making the loop O(n²) in the number of iterations."
                    ),
                    recommended_fix=(
                        f"Push/`concat` into `{target_name}` instead of spreading it into a "
                        "new array each time, e.g. `.push(...)` in place."
                    ),
                    suggested_test=None,
                    execution_path="Any call with a non-trivial number of loop iterations.",
                    file_path=path,
                    start_line=start_line,
                    end_line=end_line,
                    evidence=[
                        FindingEvidenceDTO(
                            file_path=path,
                            start_line=start_line,
                            end_line=end_line,
                            snippet=node_text(source, assignment),
                        )
                    ],
                )
            )
    return findings
