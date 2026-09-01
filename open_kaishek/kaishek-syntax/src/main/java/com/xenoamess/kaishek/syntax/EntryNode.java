package com.xenoamess.kaishek.syntax;

import java.util.List;

/** One key/operator/value production. Trivia remains in children(). */
public final class EntryNode extends Node {
    private final CstNode key, operator, value;
    EntryNode(SourceSpan span, byte[] source, List<CstNode> children, CstNode key, CstNode operator, CstNode value) {
        super(SyntaxKind.ENTRY, span, source, children); this.key = key; this.operator = operator; this.value = value;
    }
    public CstNode key() { return key; }
    public CstNode operator() { return operator; }
    public CstNode value() { return value; }
}
