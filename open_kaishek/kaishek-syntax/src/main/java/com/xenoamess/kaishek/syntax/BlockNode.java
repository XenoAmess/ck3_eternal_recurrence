package com.xenoamess.kaishek.syntax;

import java.util.List;

/** A brace-delimited block; braces themselves are represented as children. */
public final class BlockNode extends Node {
    BlockNode(SourceSpan span, byte[] source, List<CstNode> children) { super(SyntaxKind.BLOCK, span, source, children); }
    public List<EntryNode> entries() { return children().stream().filter(EntryNode.class::isInstance).map(EntryNode.class::cast).toList(); }
}
