package com.xenoamess.kaishek.syntax;

import java.util.List;

/** Public lexer facade. Parsing is preferred when diagnostics are needed. */
public final class Lexer {
    private Lexer() { }
    public static List<Lexeme> lex(byte[] source) { return Parser.lex(source); }
    public static List<Lexeme> lex(String source) { return Parser.lex(source); }
}
