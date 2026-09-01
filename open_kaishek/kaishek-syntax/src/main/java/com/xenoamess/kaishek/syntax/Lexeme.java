package com.xenoamess.kaishek.syntax;

/** A lexical item retaining its exact source span and bytes. */
public record Lexeme(LexemeKind kind, SourceSpan span, byte[] source, boolean malformed) {
    public Lexeme { source = source.clone(); }
    /** Do not expose the mutable backing array retained by this record. */
    @Override public byte[] source() { return source.clone(); }
    public byte[] raw() { return java.util.Arrays.copyOfRange(source, span.start(), span.end()); }
    public String text() { return new String(raw(), java.nio.charset.StandardCharsets.UTF_8); }
}
