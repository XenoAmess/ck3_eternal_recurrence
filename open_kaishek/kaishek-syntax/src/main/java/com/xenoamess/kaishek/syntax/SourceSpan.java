package com.xenoamess.kaishek.syntax;

/** Half-open byte offsets into the original input. */
public record SourceSpan(int start, int end) {
    public SourceSpan {
        if (start < 0 || end < start) throw new IllegalArgumentException("invalid source span");
    }
    public int length() { return end - start; }
}
