from codemind_shared_types.schemas import Chunk, ParsedSymbol

_FALLBACK_WINDOW_SIZE = 40


def chunk_file(content: str, symbols: list[ParsedSymbol]) -> list[Chunk]:
    """Splits a file into retrievable chunks: one chunk per top-level symbol
    span (class methods are covered by their enclosing class's chunk, not
    chunked separately), plus header/trailing chunks for any code outside all
    symbol spans. Falls back to a sliding window for files with no top-level
    symbols (e.g. plain scripts)."""
    lines = content.split("\n")
    total_lines = len(lines)

    top_level = sorted((s for s in symbols if s.kind != "method"), key=lambda s: s.start_line)

    if not top_level:
        return _sliding_window_chunks(lines)

    chunks: list[Chunk] = []
    chunk_index = 0

    first_start = top_level[0].start_line
    if first_start > 1:
        header_text = "\n".join(lines[0 : first_start - 1])
        if header_text.strip():
            chunks.append(
                Chunk(
                    chunk_index=chunk_index,
                    start_line=1,
                    end_line=first_start - 1,
                    content=header_text,
                )
            )
            chunk_index += 1

    for symbol in top_level:
        chunk_text = "\n".join(lines[symbol.start_line - 1 : symbol.end_line])
        chunks.append(
            Chunk(
                chunk_index=chunk_index,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                content=chunk_text,
            )
        )
        chunk_index += 1

    last_end = top_level[-1].end_line
    if last_end < total_lines:
        trailing_text = "\n".join(lines[last_end:total_lines])
        if trailing_text.strip():
            chunks.append(
                Chunk(
                    chunk_index=chunk_index,
                    start_line=last_end + 1,
                    end_line=total_lines,
                    content=trailing_text,
                )
            )
            chunk_index += 1

    return chunks


def _sliding_window_chunks(lines: list[str]) -> list[Chunk]:
    total_lines = len(lines)
    if total_lines == 0:
        return []

    chunks: list[Chunk] = []
    chunk_index = 0
    start = 0
    while start < total_lines:
        end = min(start + _FALLBACK_WINDOW_SIZE, total_lines)
        chunks.append(
            Chunk(
                chunk_index=chunk_index,
                start_line=start + 1,
                end_line=end,
                content="\n".join(lines[start:end]),
            )
        )
        chunk_index += 1
        start = end

    return chunks
