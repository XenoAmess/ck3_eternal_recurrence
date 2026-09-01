package com.xenoamess.kaishek.ir;

import com.xenoamess.kaishek.profile.UnsupportedReason;
import java.util.Objects;
import java.util.Optional;

public record Diagnostic(DiagnosticSeverity severity, String code, String message,
                         SourceSpan span, UnsupportedReason unsupportedReason) {
    public Diagnostic(DiagnosticSeverity severity, String code, String message,
                      com.xenoamess.kaishek.syntax.SourceSpan span, UnsupportedReason unsupportedReason) {
        this(severity, code, message, new SourceSpan("<input>", span.start(), span.end(), 1, 1, 1, 1), unsupportedReason);
    }
    public Diagnostic {
        severity = Objects.requireNonNull(severity, "severity");
        if (code == null || code.isBlank()) throw new IllegalArgumentException("code is blank");
        if (message == null || message.isBlank()) throw new IllegalArgumentException("message is blank");
        span = Objects.requireNonNull(span, "span");
        if (code.startsWith("UNSUPPORTED") && unsupportedReason == null)
            throw new IllegalArgumentException("unsupported diagnostic requires reason");
    }
    public Optional<UnsupportedReason> reason() { return Optional.ofNullable(unsupportedReason); }
}
