from codemind_code_parser import parse_tree
from codemind_analysis_engine.traversal import (
    enclosing_function,
    find_all,
    is_loop,
    line_range,
    node_text,
)

SOURCE = """function divide(a: number, b: number): number {
  return a / b;
}

function loopTest(items: string[]) {
  for (const x of items) {
    for (const y of items) {
      console.log(x, y);
    }
  }
}
"""


def test_find_all_collects_matching_descendant_nodes():
    tree = parse_tree("src/sample.ts", SOURCE)
    binary_expressions = find_all(tree.root_node, {"binary_expression"})
    assert len(binary_expressions) == 1
    assert node_text(SOURCE.encode("utf-8"), binary_expressions[0]) == "a / b"


def test_find_all_finds_nested_loops():
    tree = parse_tree("src/sample.ts", SOURCE)
    loops = find_all(tree.root_node, {"for_statement", "for_in_statement"})
    assert len(loops) == 2
    assert all(is_loop(loop) for loop in loops)


def test_enclosing_function_walks_up_to_nearest_function():
    tree = parse_tree("src/sample.ts", SOURCE)
    [binary_expression] = find_all(tree.root_node, {"binary_expression"})
    function_node = enclosing_function(binary_expression)
    assert function_node is not None
    assert function_node.type == "function_declaration"
    name_node = function_node.child_by_field_name("name")
    assert node_text(SOURCE.encode("utf-8"), name_node) == "divide"


def test_enclosing_function_returns_none_at_top_level():
    tree = parse_tree("src/sample.ts", SOURCE)
    function_node = tree.root_node.children[0]
    assert enclosing_function(function_node) is None


def test_line_range_returns_one_indexed_lines():
    tree = parse_tree("src/sample.ts", SOURCE)
    function_node = tree.root_node.children[0]
    assert line_range(function_node) == (1, 3)
