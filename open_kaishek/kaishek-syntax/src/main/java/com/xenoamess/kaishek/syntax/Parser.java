package com.xenoamess.kaishek.syntax;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

/**
 * Small, dependency-free Paradox lexer/CST parser. The parser deliberately does
 * not apply game/schema semantics: unknown syntax is retained and reported, so
 * tooling can safely inspect and rewrite files without losing source bytes.
 */
public final class Parser {
    private Parser() { }

    public static ParseResult parse(byte[] bytes) {
        if (bytes == null) throw new NullPointerException("bytes");
        byte[] source = bytes.clone();
        State state = new State(source);
        List<Token> tokens = state.lex();
        List<CstNode> children = new ArrayList<>();
        state.parseSequence(tokens, 0, tokens.size(), children, false);
        return new ParseResult(source, new Document(source, children), state.diagnostics);
    }

    public static ParseResult parse(String text) { return parse(text.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }

    public static ParseResult parse(InputStream input) throws IOException { return parse(input.readAllBytes()); }

    /** Lex without building a tree. Lexemes still reference copied source bytes. */
    public static List<Lexeme> lex(byte[] bytes) {
        if (bytes == null) throw new NullPointerException("bytes");
        byte[] source = bytes.clone();
        State state = new State(source);
        List<Lexeme> result = new ArrayList<>();
        for (Token t : state.lex()) {
            LexemeKind kind = switch (t.type) {
                case TRIVIA -> t.start == 0 && t.end == 3 ? LexemeKind.BOM : state.containsLineBreak(t) ? LexemeKind.NEWLINE : LexemeKind.WHITESPACE;
                case COMMENT -> LexemeKind.COMMENT; case BARE -> LexemeKind.BARE_VALUE; case STRING -> LexemeKind.STRING;
                case NUMBER -> LexemeKind.NUMBER; case VARIABLE -> LexemeKind.VARIABLE; case OP -> LexemeKind.OPERATOR;
                case LBRACE -> LexemeKind.LBRACE; case RBRACE -> LexemeKind.RBRACE; case BAD -> LexemeKind.ERROR;
            };
            result.add(new Lexeme(kind, new SourceSpan(t.start, t.end), source, t.malformed));
        }
        return List.copyOf(result);
    }
    public static List<Lexeme> lex(String text) { return lex(text.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }

    private enum T { TRIVIA, COMMENT, BARE, STRING, NUMBER, VARIABLE, OP, LBRACE, RBRACE, BAD }
    private record Token(T type, int start, int end, String op, boolean malformed) { }
    private static final Pattern NUMBER = Pattern.compile("[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][+-]?\\d+)?");

    private static final class State {
        final byte[] b; final List<Diagnostic> diagnostics = new ArrayList<>();
        State(byte[] b) { this.b = b; }

        List<Token> lex() {
            List<Token> out = new ArrayList<>(); int i = 0;
            while (i < b.length) {
                int s = i; int c = b[i] & 0xff;
                if (i == 0 && b.length >= 3 && (b[0] & 0xff) == 0xef && (b[1] & 0xff) == 0xbb && (b[2] & 0xff) == 0xbf) {
                    i = 3; out.add(new Token(T.TRIVIA, s, i, null, false)); continue;
                }
                if (c == '\r' || c == '\n') {
                    i++; if (c == '\r' && i < b.length && b[i] == '\n') i++;
                    out.add(new Token(T.TRIVIA, s, i, null, false)); continue;
                }
                if (c == ' ' || c == '\t' || c == '\f') { do { i++; } while (i < b.length && (b[i] == ' ' || b[i] == '\t' || b[i] == '\f')); out.add(new Token(T.TRIVIA,s,i,null,false)); continue; }
                if (c == '#') { i++; while (i < b.length && b[i] != '\r' && b[i] != '\n') i++; out.add(new Token(T.COMMENT,s,i,null,false)); continue; }
                if (c == '"') {
                    i++; boolean closed = false;
                    while (i < b.length) { if (b[i] == '\\') { i += Math.min(2, b.length - i); } else if (b[i++] == '"') { closed = true; break; } }
                    if (!closed) { diagnostics.add(new Diagnostic("UNTERMINATED_STRING", Diagnostic.Severity.ERROR, "unterminated quoted string", s, i)); }
                    out.add(new Token(T.STRING,s,i,null,!closed)); continue;
                }
                if (c == '{') { i++; out.add(new Token(T.LBRACE,s,i,null,false)); continue; }
                if (c == '}') { i++; out.add(new Token(T.RBRACE,s,i,null,false)); continue; }
                String op = null;
                if ((c == '!' || c == '<' || c == '>' || c == '?') && i + 1 < b.length && b[i+1] == '=') { op = new String(b,s,2,java.nio.charset.StandardCharsets.ISO_8859_1); i += 2; }
                else if (c == '=' || c == '<' || c == '>') { op = Character.toString((char)c); i++; }
                if (op != null) { out.add(new Token(T.OP,s,i,op,false)); continue; }
                while (i < b.length && !isDelimiter(b[i] & 0xff)) i++;
                if (i == s) { i++; diagnostics.add(new Diagnostic("INVALID_BYTE", Diagnostic.Severity.ERROR, "invalid byte in token", s, i)); out.add(new Token(T.BAD,s,i,null,true)); continue; }
                String text = new String(b,s,i-s,java.nio.charset.StandardCharsets.UTF_8);
                T kind = text.startsWith("$") || text.startsWith("@") ? T.VARIABLE : NUMBER.matcher(text).matches() ? T.NUMBER : T.BARE;
                out.add(new Token(kind,s,i,null,false));
            }
            return out;
        }

        private static boolean isDelimiter(int c) { return c == ' ' || c == '\t' || c == '\f' || c == '\r' || c == '\n' || c == '#' || c == '{' || c == '}' || c == '=' || c == '<' || c == '>' || c == '?'; }

        int parseSequence(List<Token> ts, int pos, int end, List<CstNode> out, boolean inBlock) {
            while (pos < end) {
                Token t = ts.get(pos);
                if (isTrivia(t)) { out.add(node(t)); pos++; continue; }
                if (t.type == T.RBRACE) {
                    if (inBlock) return pos;
                    diagnostics.add(new Diagnostic("UNEXPECTED_RBRACE", Diagnostic.Severity.ERROR, "closing brace without matching block", t.start, t.end)); out.add(node(SyntaxKind.ERROR,t)); pos++; continue;
                }
                int entryStart = t.start; List<CstNode> ec = new ArrayList<>();
                CstNode key = node(keyKind(t), t); ec.add(key); pos++;
                while (pos < end && isTrivia(ts.get(pos))) { ec.add(node(ts.get(pos))); pos++; }
                CstNode operator = null, value = null;
                if (pos < end && ts.get(pos).type == T.OP) { Token ot = ts.get(pos++); operator = node(SyntaxKind.OPERATOR, ot); ec.add(operator); }
                else {
                    if (inBlock) { out.add(new Node(SyntaxKind.LIST_ITEM, new SourceSpan(entryStart, t.end), b, ec)); continue; }
                    diagnostics.add(new Diagnostic("MISSING_OPERATOR", Diagnostic.Severity.ERROR, "expected '=' or comparison operator after key", t.start, t.end));
                    out.add(new EntryNode(new SourceSpan(entryStart, t.end), b, ec, key, null, null)); continue;
                }
                while (pos < end && isTrivia(ts.get(pos))) { ec.add(node(ts.get(pos))); pos++; }
                if (pos >= end || (inBlock && ts.get(pos).type == T.RBRACE)) {
                    diagnostics.add(new Diagnostic("MISSING_VALUE", Diagnostic.Severity.ERROR, "operator has no value", ts.get(pos-1).start, ts.get(pos-1).end));
                    out.add(new EntryNode(new SourceSpan(entryStart, operator.span().end()), b, ec, key, operator, null)); continue;
                }
                Token vt = ts.get(pos);
                if (vt.type == T.LBRACE) {
                    int before = pos; List<CstNode> bc = new ArrayList<>(); pos++;
                    bc.add(node(SyntaxKind.LBRACE, vt)); int close = parseSequence(ts, pos, end, bc, true); pos = close;
                    if (pos < end && ts.get(pos).type == T.RBRACE) { bc.add(node(SyntaxKind.RBRACE, ts.get(pos))); pos++; }
                    else { int at = pos < end ? ts.get(pos).start : b.length; diagnostics.add(new Diagnostic("UNCLOSED_BLOCK", Diagnostic.Severity.ERROR, "block is not closed with '}'", vt.start, at)); }
                    int blockEnd = bc.isEmpty() ? vt.end : bc.get(bc.size()-1).span().end();
                    value = new BlockNode(new SourceSpan(vt.start, blockEnd), b, bc); ec.add(value);
                } else {
                    pos++; value = node(valueKind(vt), vt); ec.add(value);
                    if (vt.malformed) diagnostics.add(new Diagnostic("MALFORMED_VALUE", Diagnostic.Severity.ERROR, "malformed value", vt.start, vt.end));
                }
                out.add(new EntryNode(new SourceSpan(entryStart, value.span().end()), b, ec, key, operator, value));
            }
            return pos;
        }

        private boolean isTrivia(Token t) { return t.type == T.TRIVIA || t.type == T.COMMENT; }
        private CstNode node(Token t) {
            SyntaxKind k = t.type == T.COMMENT ? SyntaxKind.COMMENT : t.type == T.TRIVIA ? ((t.start == 0 && t.end == 3) ? SyntaxKind.BOM : (containsLineBreak(t) ? SyntaxKind.NEWLINE : SyntaxKind.WHITESPACE)) : valueKind(t);
            return node(k, t);
        }
        private boolean containsLineBreak(Token t) { for (int i=t.start; i<t.end; i++) if (b[i]=='\r' || b[i]=='\n') return true; return false; }
        private CstNode node(SyntaxKind k, Token t) { return new Node(k, new SourceSpan(t.start,t.end), b); }
        private static SyntaxKind keyKind(Token t) { return t.type == T.VARIABLE ? SyntaxKind.VARIABLE : SyntaxKind.KEY; }
        private static SyntaxKind valueKind(Token t) { return switch (t.type) { case STRING -> SyntaxKind.STRING; case NUMBER -> SyntaxKind.NUMBER; case VARIABLE -> SyntaxKind.VARIABLE; case BAD -> SyntaxKind.ERROR; default -> SyntaxKind.BARE_VALUE; }; }
    }
}
