import posixpath

_CANDIDATE_SUFFIXES = ("", ".ts", ".tsx", "/index.ts", "/index.tsx")


def resolve_import_path(from_file_path: str, specifier: str, known_paths: set[str]) -> str | None:
    """Resolves a relative import specifier against the set of known file paths
    in the same index. Returns None for external packages (non-relative
    specifiers) or specifiers that don't resolve to any known file."""
    if not specifier.startswith("."):
        return None

    from_dir = posixpath.dirname(from_file_path)
    base = posixpath.normpath(posixpath.join(from_dir, specifier))

    for suffix in _CANDIDATE_SUFFIXES:
        candidate = f"{base}{suffix}"
        if candidate in known_paths:
            return candidate

    return None
