package com.xenoamess.kaishek.syntax;

import java.util.List;

class Node implements CstNode {
    private final SyntaxKind kind; private final SourceSpan span; private final byte[] source; private final List<CstNode> children;
    Node(SyntaxKind kind, SourceSpan span, byte[] source) { this(kind, span, source, List.of()); }
    Node(SyntaxKind kind, SourceSpan span, byte[] source, List<CstNode> children) {
        this.kind = kind; this.span = span; this.source = source; this.children = List.copyOf(children);
    }
    @Override public SyntaxKind kind() { return kind; }
    @Override public SourceSpan span() { return span; }
    @Override public byte[] source() { return source.clone(); }
    @Override public List<CstNode> children() { return children; }
}
