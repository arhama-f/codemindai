from collections.abc import Callable

from tree_sitter import Node

from codemind_analysis_engine.checks.bugs import (
    check_empty_catch_block,
    check_unreachable_code_after_return,
    check_unsafe_division,
)
from codemind_analysis_engine.checks.performance import (
    check_array_rebuild_in_loop,
    check_array_scan_in_loop,
    check_nested_loop_quadratic,
)
from codemind_analysis_engine.checks.security import (
    check_hardcoded_secret,
    check_sensitive_data_logging,
    check_unsafe_dangerously_set_inner_html,
)
from codemind_code_parser import parse_tree
from codemind_shared_types.schemas import FindingDraftDTO, ParsedSymbol

CheckFunc = Callable[[str, bytes, Node, list[ParsedSymbol]], list[FindingDraftDTO]]

CHECKS: list[CheckFunc] = [
    check_unsafe_division,
    check_empty_catch_block,
    check_unreachable_code_after_return,
    check_hardcoded_secret,
    check_unsafe_dangerously_set_inner_html,
    check_sensitive_data_logging,
    check_nested_loop_quadratic,
    check_array_scan_in_loop,
    check_array_rebuild_in_loop,
]


def analyze_file(path: str, source: str, symbols: list[ParsedSymbol]) -> list[FindingDraftDTO]:
    """Parses `source` once and runs every registered check against the same
    tree, returning every check's findings combined."""
    tree = parse_tree(path, source)
    source_bytes = source.encode("utf-8")

    findings: list[FindingDraftDTO] = []
    for check in CHECKS:
        findings.extend(check(path, source_bytes, tree.root_node, symbols))
    return findings
