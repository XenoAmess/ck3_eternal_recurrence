package com.xenoamess.kaishek.validator;

import java.util.Objects;
import com.xenoamess.kaishek.syntax.SourceSpan;

public record Diagnostic(String code, Severity severity, String message, String path, SourceSpan span) {
    public Diagnostic {
        Objects.requireNonNull(code); Objects.requireNonNull(severity); Objects.requireNonNull(message);
        path = path == null ? "" : path; span = span == null ? new SourceSpan(0, 0) : span;
    }
    public enum Severity { ERROR, WARNING, INFO }
}
