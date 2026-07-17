import tree_sitter_typescript as tsts
from tree_sitter import Language, Node, Parser

from codemind_shared_types.schemas import ParsedFile, ParsedImport, ParsedSymbol

_TS_LANGUAGE = Language(tsts.language_typescript(), "typescript")
_TSX_LANGUAGE = Language(tsts.language_tsx(), "tsx")

_TOP_LEVEL_KIND_BY_NODE_TYPE = {
    "function_declaration": "function",
    "class_declaration": "class",
    "interface_declaration": "interface",
    "type_alias_declaration": "type_alias",
    "enum_declaration": "enum",
}


def _parser_for(path: str) -> Parser:
    parser = Parser()
    parser.set_language(_TSX_LANGUAGE if path.endswith(".tsx") else _TS_LANGUAGE)
    return parser


def _text(source: bytes, node: Node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8")


def _extract_methods(
    source: bytes, class_node: Node, class_name: str, exported: bool
) -> list[ParsedSymbol]:
    body = class_node.child_by_field_name("body")
    if body is None:
        return []

    methods = []
    for member in body.children:
        if member.type != "method_definition":
            continue
        name_node = member.child_by_field_name("name")
        if name_node is None:
            continue
        method_name = _text(source, name_node)
        methods.append(
            ParsedSymbol(
                name=method_name,
                kind="method",
                start_line=member.start_point[0] + 1,
                end_line=member.end_point[0] + 1,
                signature=f"{class_name}.{method_name}",
                exported=exported,
            )
        )
    return methods


def _extract_top_level_symbol(
    source: bytes, node: Node, exported: bool
) -> tuple[ParsedSymbol | None, list[ParsedSymbol]]:
    kind = _TOP_LEVEL_KIND_BY_NODE_TYPE.get(node.type)
    if kind is None:
        return None, []

    name_node = node.child_by_field_name("name")
    if name_node is None:
        return None, []

    name = _text(source, name_node)
    symbol = ParsedSymbol(
        name=name,
        kind=kind,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        exported=exported,
    )

    methods = _extract_methods(source, node, name, exported) if kind == "class" else []
    return symbol, methods


def _extract_import(source: bytes, node: Node) -> ParsedImport | None:
    source_node = node.child_by_field_name("source")
    if source_node is None:
        return None
    specifier = _text(source, source_node).strip("\"'")

    imported_names: list[str] = []
    clause = next((c for c in node.children if c.type == "import_clause"), None)
    if clause is not None:
        for child in clause.children:
            if child.type == "identifier":
                imported_names.append(_text(source, child))
            elif child.type == "named_imports":
                for spec in child.children:
                    if spec.type != "import_specifier":
                        continue
                    ident = next((c for c in spec.children if c.type == "identifier"), None)
                    if ident is not None:
                        imported_names.append(_text(source, ident))
            elif child.type == "namespace_import":
                ident = next((c for c in child.children if c.type == "identifier"), None)
                if ident is not None:
                    imported_names.append(_text(source, ident))

    return ParsedImport(specifier=specifier, imported_names=imported_names)


def parse_file(path: str, source: str) -> ParsedFile:
    """Parses a single .ts/.tsx file's top-level symbols and imports.

    Only top-level declarations are extracted as symbols (plus one level down
    for class methods) — nested/local declarations are out of scope for this
    slice's code intelligence model.
    """
    parser = _parser_for(path)
    source_bytes = source.encode("utf-8")
    tree = parser.parse(source_bytes)

    symbols: list[ParsedSymbol] = []
    imports: list[ParsedImport] = []

    for node in tree.root_node.children:
        if node.type == "import_statement":
            parsed_import = _extract_import(source_bytes, node)
            if parsed_import is not None:
                imports.append(parsed_import)
            continue

        exported = False
        target = node
        if node.type == "export_statement":
            declaration = node.child_by_field_name("declaration")
            if declaration is None:
                # `export default ...` / `export { x }` re-exports: no declaration to extract.
                continue
            target = declaration
            exported = True

        symbol, methods = _extract_top_level_symbol(source_bytes, target, exported)
        if symbol is not None:
            symbols.append(symbol)
            symbols.extend(methods)

    return ParsedFile(symbols=symbols, imports=imports)
