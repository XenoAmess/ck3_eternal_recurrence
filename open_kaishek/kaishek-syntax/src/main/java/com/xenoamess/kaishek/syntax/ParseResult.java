package com.xenoamess.kaishek.syntax;

import java.io.IOException;
import java.io.OutputStream;
import java.util.List;

public final class ParseResult {
    private final byte[] source;
    private final Document document;
    private final List<Diagnostic> diagnostics;

    ParseResult(byte[] source, Document document, List<Diagnostic> diagnostics) {
        this.source = source.clone(); this.document = document;
        this.diagnostics = List.copyOf(diagnostics);
    }
    public Document document() { return document; }
    public List<Diagnostic> diagnostics() { return diagnostics; }
    public boolean hasErrors() { return diagnostics.stream().anyMatch(d -> d.severity() == Diagnostic.Severity.ERROR); }
    public boolean hasUtf8Bom() { return source.length >= 3 && (source[0] & 0xff) == 0xef && (source[1] & 0xff) == 0xbb && (source[2] & 0xff) == 0xbf; }
    /** Returns the dominant newline sequence, or the empty string for a file without newlines. */
    public String newlineStyle() {
        int crlf = 0, lf = 0, cr = 0;
        String first = "";
        for (int i = 0; i < source.length; i++) {
            if (source[i] == '\r') {
                String style = (i + 1 < source.length && source[i + 1] == '\n') ? "\r\n" : "\r";
                if (first.isEmpty()) first = style;
                if ("\r\n".equals(style)) { crlf++; i++; } else cr++;
            } else if (source[i] == '\n') {
                if (first.isEmpty()) first = "\n";
                lf++;
            }
        }
        if (crlf == 0 && lf == 0 && cr == 0) return "";
        int best = Math.max(crlf, Math.max(lf, cr));
        // Preserve first-seen style for ties, while selecting the actual
        // majority for mixed files.
        if ("\r\n".equals(first) && crlf == best) return "\r\n";
        if ("\n".equals(first) && lf == best) return "\n";
        if ("\r".equals(first) && cr == best) return "\r";
        if (crlf == best) return "\r\n";
        if (lf == best) return "\n";
        return "\r";
    }
    public byte[] source() { return source.clone(); }
    /** Emit the exact bytes supplied to {@link Parser#parse(byte[])}. */
    public byte[] emit() { return source.clone(); }
    public void emitTo(OutputStream out) throws IOException { out.write(source); }
}
