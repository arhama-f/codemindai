from pathlib import Path

from codemind_code_parser import parse_file, parse_tree

DEMO_REPO_SRC = Path(__file__).resolve().parents[3] / "fixtures" / "demo-repo" / "src"


def _read(relative_path: str) -> str:
    return (DEMO_REPO_SRC / relative_path).read_text()


def test_math_ts_extracts_five_exported_functions():
    parsed = parse_file("src/utils/math.ts", _read("utils/math.ts"))

    assert parsed.imports == []
    assert [(s.name, s.kind, s.start_line, s.end_line, s.exported) for s in parsed.symbols] == [
        ("add", "function", 1, 3, True),
        ("subtract", "function", 5, 7, True),
        ("multiply", "function", 9, 11, True),
        ("divide", "function", 14, 16, True),
        ("percentageOf", "function", 18, 23, True),
    ]


def test_user_service_ts_extracts_class_with_methods_and_import():
    parsed = parse_file("src/services/userService.ts", _read("services/userService.ts"))

    assert len(parsed.imports) == 1
    assert parsed.imports[0].specifier == "../models/user"
    assert parsed.imports[0].imported_names == ["User"]

    by_kind = {"class": [], "method": []}
    for symbol in parsed.symbols:
        by_kind.setdefault(symbol.kind, []).append(symbol)

    assert len(by_kind["class"]) == 1
    class_symbol = by_kind["class"][0]
    assert class_symbol.name == "UserService"
    assert (class_symbol.start_line, class_symbol.end_line) == (3, 27)
    assert class_symbol.exported is True

    method_names = [m.name for m in by_kind["method"]]
    assert method_names == ["createUser", "getUserById", "listUsers", "deleteUser"]
    assert [(m.start_line, m.end_line) for m in by_kind["method"]] == [
        (6, 9),
        (11, 13),
        (15, 17),
        (21, 26),
    ]


def test_user_model_ts_extracts_type_alias_and_interface():
    parsed = parse_file("src/models/user.ts", _read("models/user.ts"))

    assert parsed.imports == []
    assert [(s.name, s.kind, s.start_line, s.end_line) for s in parsed.symbols] == [
        ("UserRole", "type_alias", 1, 1),
        ("User", "interface", 3, 8),
    ]


def test_index_ts_extracts_all_import_specifiers():
    parsed = parse_file("src/index.ts", _read("index.ts"))

    specifiers = [(imp.specifier, imp.imported_names) for imp in parsed.imports]
    assert specifiers == [
        ("./utils/math", ["add", "divide"]),
        ("./utils/string", ["capitalize"]),
        ("./models/user", ["User"]),
        ("./services/userService", ["UserService"]),
    ]


def test_parse_tree_returns_raw_tree_sitter_tree():
    tree = parse_tree("src/utils/math.ts", _read("utils/math.ts"))

    assert tree.root_node.type == "program"
    function_nodes = [c for c in tree.root_node.children if c.type == "export_statement"]
    assert len(function_nodes) == 5


def test_user_card_tsx_parses_without_error():
    parsed = parse_file("src/components/UserCard.tsx", _read("components/UserCard.tsx"))

    assert parsed.imports[0].specifier == "../models/user"
    names_and_kinds = [(s.name, s.kind) for s in parsed.symbols]
    assert ("UserCardProps", "interface") in names_and_kinds
    assert ("UserCard", "function") in names_and_kinds
