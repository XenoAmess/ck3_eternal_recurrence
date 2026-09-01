package com.xenoamess.kaishek.syntax;

/** Token classes emitted by the lossless lexer. */
public enum LexemeKind {
    BOM, WHITESPACE, NEWLINE, COMMENT, BARE_VALUE, STRING, NUMBER,
    VARIABLE, OPERATOR, LBRACE, RBRACE, ERROR
}
