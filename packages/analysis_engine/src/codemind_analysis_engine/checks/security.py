import re

from tree_sitter import Node

from codemind_analysis_engine.traversal import find_all, line_range, node_text
from codemind_shared_types.schemas import FindingDraftDTO, FindingEvidenceDTO, ParsedSymbol

_SECRET_NAME_PATTERN = re.compile(
    r"api[_-]?key|secret|token|password|access[_-]?key", re.IGNORECASE
)


def check_hardcoded_secret(
    path: str, source: bytes, root: Node, symbols: list[ParsedSymbol]
) -> list[FindingDraftDTO]:
    """Flags `const apiKey = "..."`-shaped declarations: a secret-sounding
    name assigned a string literal (not `process.env.X` or similar)."""
    findings = []
    for node in find_all(root, {"variable_declarator"}):
        name_node = node.child_by_field_name("name")
        value_node = node.child_by_field_name("value")
        if name_node is None or value_node is None:
            continue
        if value_node.type != "string":
            continue

        name = node_text(source, name_node)
        if not _SECRET_NAME_PATTERN.search(name):
            continue

        start_line, end_line = line_range(node)
        findings.append(
            FindingDraftDTO(
                check_id="hardcoded-secret",
                category="security",
                title=f"Hardcoded secret in `{name}`",
                severity="critical",
                confidence="medium",
                explanation=(
                    f"`{name}` is assigned a string literal directly in source. If this is "
                    "a real credential, it's exposed to anyone with repository access and "
                    "will be baked into version control history."
                ),
                recommended_fix=(
                    "Move the value to an environment variable or secret manager and read "
                    f"it at runtime, e.g. `process.env.{name.upper()}`."
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
                        snippet=node_text(source, node),
                    )
                ],
            )
        )
    return findings


def check_unsafe_dangerously_set_inner_html(
    path: str, source: bytes, root: Node, symbols: list[ParsedSymbol]
) -> list[FindingDraftDTO]:
    """Flags JSX `dangerouslySetInnerHTML` usage — a common XSS vector."""
    if not path.endswith(".tsx"):
        return []

    findings = []
    for node in find_all(root, {"jsx_attribute"}):
        if not node.children or node_text(source, node.children[0]) != "dangerouslySetInnerHTML":
            continue

        start_line, end_line = line_range(node)
        findings.append(
            FindingDraftDTO(
                check_id="unsafe-dangerously-set-inner-html",
                category="security",
                title="Unsanitized HTML rendered via dangerouslySetInnerHTML",
                severity="high",
                confidence="high",
                explanation=(
                    "This renders raw HTML without sanitization. If the value can contain "
                    "user-controlled input, this is a cross-site scripting (XSS) vector."
                ),
                recommended_fix=(
                    "Sanitize the HTML before rendering (e.g. with a library like DOMPurify), "
                    "or avoid `dangerouslySetInnerHTML` and render plain text/structured "
                    "elements instead."
                ),
                suggested_test=(
                    "Render this component with a value containing a `<script>` tag and "
                    "assert it's neutralized, not executed."
                ),
                execution_path="Any render where the HTML source includes user-controlled input.",
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


def check_sensitive_data_logging(
    path: str, source: bytes, root: Node, symbols: list[ParsedSymbol]
) -> list[FindingDraftDTO]:
    """Flags `console.*(...)` calls where an argument's text looks like a
    secret-sounding variable name (e.g. logging an API key)."""
    findings = []
    for node in find_all(root, {"call_expression"}):
        function_node = node.child_by_field_name("function")
        if function_node is None or function_node.type != "member_expression":
            continue
        object_node = function_node.child_by_field_name("object")
        if object_node is None or node_text(source, object_node) != "console":
            continue

        arguments = node.child_by_field_name("arguments")
        if arguments is None:
            continue

        matched_args = [
            node_text(source, arg)
            for arg in arguments.named_children
            if _SECRET_NAME_PATTERN.search(node_text(source, arg))
        ]
        if not matched_args:
            continue

        start_line, end_line = line_range(node)
        findings.append(
            FindingDraftDTO(
                check_id="sensitive-data-logging",
                category="security",
                title=f"Possible secret logged: {', '.join(matched_args)}",
                severity="medium",
                confidence="medium",
                explanation=(
                    f"This log call includes `{', '.join(matched_args)}`, whose name suggests "
                    "sensitive data (a key/token/secret/password). Logs are often stored, "
                    "shipped to third parties, or visible to more people than the data itself."
                ),
                recommended_fix=(
                    "Remove the sensitive value from the log line, or redact/mask it before "
                    "logging."
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
                        snippet=node_text(source, node),
                    )
                ],
            )
        )
    return findings
