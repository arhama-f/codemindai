from tree_sitter import Node

_FUNCTION_NODE_TYPES = {
    "function_declaration",
    "method_definition",
    "arrow_function",
    "function_expression",
}

_LOOP_NODE_TYPES = {
    "for_statement",
    "for_in_statement",
    "while_statement",
    "do_statement",
}


def find_all(node: Node, types: set[str]) -> list[Node]:
    """Recursively collects all descendant nodes (including `node` itself)
    whose type is in `types`."""
    matches = []
    if node.type in types:
        matches.append(node)
    for child in node.children:
        matches.extend(find_all(child, types))
    return matches


def enclosing_function(node: Node) -> Node | None:
    """Walks up from `node` to the nearest enclosing function-like node."""
    current = node.parent
    while current is not None:
        if current.type in _FUNCTION_NODE_TYPES:
            return current
        current = current.parent
    return None


def is_loop(node: Node) -> bool:
    return node.type in _LOOP_NODE_TYPES


def node_text(source: bytes, node: Node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8")


def line_range(node: Node) -> tuple[int, int]:
    return node.start_point[0] + 1, node.end_point[0] + 1
