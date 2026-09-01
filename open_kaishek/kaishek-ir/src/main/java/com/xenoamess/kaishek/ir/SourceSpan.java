package com.xenoamess.kaishek.ir;

/** Half-open source range; line/column are one-based, offsets are zero-based. */
public record SourceSpan(String source, int startOffset, int endOffset,
                         int startLine, int startColumn, int endLine, int endColumn) {
    public SourceSpan {
        if (source == null || source.isBlank()) throw new IllegalArgumentException("source is blank");
        if (startOffset < 0 || endOffset < startOffset) throw new IllegalArgumentException("invalid offsets");
        if (startLine < 1 || endLine < startLine || startColumn < 1 || endColumn < 1
                || (startLine == endLine && endColumn < startColumn))
            throw new IllegalArgumentException("invalid line/column");
    }
    public static SourceSpan unknown(String source) { return new SourceSpan(source, 0, 0, 1, 1, 1, 1); }

    /**
     * Convert the parser's byte-offset span to the richer IR span contract.
     * Paradox source files are byte-oriented (and may contain a UTF-8 BOM),
     * therefore line/column calculation deliberately walks the original
     * bytes instead of re-encoding a Java String and risking offset drift.
     * Columns are one-based byte columns; this is deterministic even for a
     * malformed UTF-8 fixture and keeps the original source offsets lossless.
     */
    public static SourceSpan from(String sourceName, byte[] sourceBytes,
                                  com.xenoamess.kaishek.syntax.SourceSpan span) {
        if (sourceBytes == null || span == null) throw new NullPointerException();
        if (span.end() > sourceBytes.length) throw new IllegalArgumentException("span exceeds source bytes");
        Position start = position(sourceBytes, span.start());
        Position end = position(sourceBytes, span.end());
        return new SourceSpan(sourceName, span.start(), span.end(),
                start.line(), start.column(), end.line(), end.column());
    }

    private static Position position(byte[] bytes, int offset) {
        int line = 1;
        int column = 1;
        for (int i = 0; i < offset; i++) {
            byte value = bytes[i];
            if (value == '\n') {
                line++;
                column = 1;
            } else if (value == '\r') {
                // CRLF is one logical newline.  The following LF is skipped
                // by this branch's look-ahead so a CRLF span does not create
                // an artificial blank line.
                if (i + 1 < offset && bytes[i + 1] == '\n') i++;
                line++;
                column = 1;
            } else {
                column++;
            }
        }
        return new Position(line, column);
    }

    private record Position(int line, int column) { }
}
