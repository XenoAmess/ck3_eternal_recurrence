package com.xenoamess.kaishek.syntax;

/** A recoverable syntax problem. Offsets always refer to original bytes. */
public record Diagnostic(String code, Severity severity, String message, SourceSpan span) {
    public enum Severity { INFO, WARNING, ERROR }
    public Diagnostic(String code, Severity severity, String message, int start, int end) {
        this(code, severity, message, new SourceSpan(start, end));
    }
}
