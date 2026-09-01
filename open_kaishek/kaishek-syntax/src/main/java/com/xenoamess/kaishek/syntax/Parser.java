package com.xenoamess.kaishek.syntax;

import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
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
            // Java's String(byte[], UTF_8) replaces malformed sequences with
            // U+FFFD.  That is useful for display, but unsafe for a lossless
            // parser: an invalid source byte must remain an explicit error so
            // the validator/IR cannot accidentally execute a repaired token.
            validateUtf8();
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
                    out.add(new Token(T.STRING,s,i,null,!closed || decodeUtf8(s, i) == null)); continue;
                }
                if (c == '{') { i++; out.add(new Token(T.LBRACE,s,i,null,false)); continue; }
                if (c == '}') { i++; out.add(new Token(T.RBRACE,s,i,null,false)); continue; }
                String op = null;
                if ((c == '!' || c == '<' || c == '>' || c == '?') && i + 1 < b.length && b[i+1] == '=') { op = new String(b,s,2,java.nio.charset.StandardCharsets.ISO_8859_1); i += 2; }
                else if (c == '=' || c == '<' || c == '>') { op = Character.toString((char)c); i++; }
                if (op != null) { out.add(new Token(T.OP,s,i,op,false)); continue; }
                while (i < b.length && !isDelimiter(b[i] & 0xff)) i++;
                if (i == s) { i++; diagnostics.add(new Diagnostic("INVALID_BYTE", Diagnostic.Severity.ERROR, "invalid byte in token", s, i)); out.add(new Token(T.BAD,s,i,null,true)); continue; }
                String text = decodeUtf8(s, i);
                if (text == null) {
                    // validateUtf8() has already recorded the precise source
                    // error; retain a recovery token so byte spans and
                    // round-trip output remain available to callers.
                    out.add(new Token(T.BAD, s, i, null, true));
                    continue;
                }
                T kind = text.startsWith("$") || text.startsWith("@") ? T.VARIABLE : NUMBER.matcher(text).matches() ? T.NUMBER : T.BARE;
                out.add(new Token(kind,s,i,null,false));
            }
            return out;
        }

        /** Record every malformed UTF-8 sequence without rewriting input. */
        private void validateUtf8() {
            for (int i = 0; i < b.length;) {
                int first = b[i] & 0xff;
                int length;
                int secondMin = 0x80;
                int secondMax = 0xbf;
                if (first <= 0x7f) {
                    i++;
                    continue;
                } else if (first >= 0xc2 && first <= 0xdf) {
                    length = 2;
                } else if (first == 0xe0) {
                    length = 3;
                    secondMin = 0xa0;
                } else if ((first >= 0xe1 && first <= 0xec) || (first >= 0xee && first <= 0xef)) {
                    length = 3;
                } else if (first == 0xed) {
                    length = 3;
                    secondMax = 0x9f;
                } else if (first == 0xf0) {
                    length = 4;
                    secondMin = 0x90;
                } else if (first >= 0xf1 && first <= 0xf3) {
                    length = 4;
                } else if (first == 0xf4) {
                    length = 4;
                    secondMax = 0x8f;
                } else {
                    invalidUtf8(i, i + 1);
                    i++;
                    continue;
                }
                int end = Math.min(b.length, i + length);
                boolean valid = end - i == length;
                if (valid) {
                    int second = b[i + 1] & 0xff;
                    valid = second >= secondMin && second <= secondMax;
                    for (int j = 2; valid && j < length; j++) {
                        int continuation = b[i + j] & 0xff;
                        valid = continuation >= 0x80 && continuation <= 0xbf;
                    }
                }
                if (valid) {
                    i += length;
                } else {
                    invalidUtf8(i, end);
                    // Advance one byte so a following malformed lead is not
                    // hidden behind the first recovery diagnostic.
                    i++;
                }
            }
        }

        private void invalidUtf8(int start, int end) {
            diagnostics.add(new Diagnostic("INVALID_BYTE", Diagnostic.Severity.ERROR,
                    "invalid UTF-8 byte sequence", start, Math.max(start + 1, end)));
        }

        /** Decode a token strictly; null means malformed UTF-8. */
        private String decodeUtf8(int start, int end) {
            try {
                return java.nio.charset.StandardCharsets.UTF_8.newDecoder()
                        .onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT)
                        .decode(ByteBuffer.wrap(b, start, end - start)).toString();
            } catch (CharacterCodingException ex) {
                return null;
            }
        }

        private static boolean isDelimiter(int c) { return c == ' ' || c == '\t' || c == '\f' || c == '\r' || c == '\n' || c == '#' || c == '{' || c == '}' || c == '=' || c == '<' || c == '>' || c == '?'; }

        int parseSequence(List<Token> ts, int pos, int end, List<CstNode> out, boolean inBlock) {
            while (pos < end) {
                Token t = ts.get(pos);
                if (isTrivia(t)) { out.add(node(t)); pos++; continue; }
                if (t.type == T.RBRACE) {
                    if (inBlock) return pos;
                    diagnostics.add(new Diagnostic("UNEXPECTED_RBRACE", Diagnostic.Severity.ERROR,
                            "closing brace without matching block", t.start, t.end));
                    out.add(node(SyntaxKind.ERROR, t)); pos++; continue;
                }
                if (t.type == T.LBRACE) {
                    diagnostics.add(new Diagnostic("UNEXPECTED_LBRACE", Diagnostic.Severity.ERROR,
                            "opening brace without a declaration", t.start, t.end));
                    out.add(node(SyntaxKind.ERROR, t)); pos++; continue;
                }

                int entryStart = t.start;
                List<CstNode> ec = new ArrayList<>();
                CstNode key = node(keyKind(t), t); ec.add(key); pos++;
                pos = appendTrivia(ts, pos, end, ec);

                CstNode operator = null;
                CstNode value;
                // A few GUI productions use a declaration header without an
                // equals sign (`types Name {}` and
                // `blockoverride "name" {}`).  Parse the header losslessly
                // instead of turning its braces into unmatched top-level
                // tokens.
                if (pos >= end || ts.get(pos).type != T.OP) {
                    int blockAt = isNoEqualsHeaderKey(t) ? findHeaderBlock(ts, pos, end) : -1;
                    if (blockAt >= 0) {
                        while (pos < blockAt) { ec.add(node(ts.get(pos))); pos++; }
                        BlockResult block = parseBlock(ts, pos, end);
                        value = block.node(); ec.add(value); pos = block.next();
                        out.add(new EntryNode(new SourceSpan(entryStart, value.span().end()), b, ec, key, null, value));
                        continue;
                    }
                    // `type Name = hbox { ... }` has a declaration prefix
                    // before its operator.  Restrict this recovery to the
                    // known header keyword so ordinary list items remain
                    // unambiguous.
                    int prefixOp = isHeaderKey(t) ? findHeaderOperator(ts, pos, end) : -1;
                    if (prefixOp >= 0) {
                        while (pos < prefixOp) { ec.add(node(ts.get(pos))); pos++; }
                    } else {
                        if (inBlock) {
                            out.add(new Node(SyntaxKind.LIST_ITEM,
                                    new SourceSpan(entryStart, t.end), b, ec));
                            continue;
                        }
                        diagnostics.add(new Diagnostic("MISSING_OPERATOR", Diagnostic.Severity.ERROR,
                                "expected '=' or comparison operator after key", t.start, t.end));
                        out.add(new EntryNode(new SourceSpan(entryStart, t.end), b, ec, key, null, null));
                        continue;
                    }
                }

                if (pos < end && ts.get(pos).type == T.OP) {
                    Token ot = ts.get(pos++);
                    operator = node(SyntaxKind.OPERATOR, ot); ec.add(operator);
                }
                pos = appendTrivia(ts, pos, end, ec);
                if (pos >= end || (inBlock && ts.get(pos).type == T.RBRACE)) {
                    int at = operator == null ? entryStart : operator.span().end();
                    diagnostics.add(new Diagnostic("MISSING_VALUE", Diagnostic.Severity.ERROR,
                            "operator has no value", at, at));
                    out.add(new EntryNode(new SourceSpan(entryStart, Math.max(at, t.end)), b, ec, key, operator, null));
                    continue;
                }

                ValueResult parsedValue = parseValue(ts, pos, end);
                value = parsedValue.node(); pos = parsedValue.next(); ec.add(value);
                out.add(new EntryNode(new SourceSpan(entryStart, value.span().end()), b, ec, key, operator, value));
            }
            return pos;
        }

        /** Consume trivia into an entry/header while retaining exact spans. */
        private int appendTrivia(List<Token> ts, int pos, int end, List<CstNode> out) {
            while (pos < end && isTrivia(ts.get(pos))) { out.add(node(ts.get(pos))); pos++; }
            return pos;
        }

        /**
         * Find the brace used by a no-equals GUI declaration.  GUI headers
         * permit trivia (including a line break and comments) between the
         * label and the opening brace, so the look-ahead is deliberately
         * trivia-tolerant.  We still require exactly one label token; this
         * keeps ordinary list items from absorbing an unrelated later block.
         */
        private int findHeaderBlock(List<Token> ts, int pos, int end) {
            int q = pos;
            boolean labelSeen = false;
            while (q < end) {
                Token x = ts.get(q);
                if (isTrivia(x)) {
                    q++; continue;
                }
                if (x.type == T.LBRACE) return labelSeen ? q : -1;
                if (!labelSeen && isHeaderLabel(x)) {
                    labelSeen = true;
                    q++;
                    continue;
                }
                return -1;
            }
            return -1;
        }

        private static boolean isHeaderLabel(Token t) {
            return t.type == T.BARE || t.type == T.STRING || t.type == T.NUMBER ||
                    t.type == T.VARIABLE;
        }

        /**
         * No-equals declarations are a small, known GUI grammar production.
         * Keeping the keyword allow-list here prevents malformed ordinary
         * script such as `foo bar { ... }` from being silently accepted as a
         * declaration while still covering the forms used by CK3 GUI files.
         */
        private boolean isNoEqualsHeaderKey(Token t) {
            if (t.type != T.BARE) return false;
            return Set.of("types", "template", "block", "blockoverride")
                    .contains(tokenText(t));
        }

        private int findHeaderOperator(List<Token> ts, int pos, int end) {
            int q = pos;
            while (q < end) {
                Token x = ts.get(q);
                if (isTrivia(x)) {
                    if (containsLineBreak(x)) return -1;
                    q++; continue;
                }
                if (x.type == T.OP) return q;
                if (x.type == T.LBRACE || x.type == T.RBRACE) return -1;
                q++;
            }
            return -1;
        }

        private boolean isHeaderKey(Token t) {
            return t.type == T.BARE && "type".equals(tokenText(t));
        }

        private String tokenText(Token t) {
            return new String(b, t.start, t.end - t.start, java.nio.charset.StandardCharsets.UTF_8);
        }

        private ValueResult parseValue(List<Token> ts, int pos, int end) {
            Token first = ts.get(pos);
            if (first.type == T.LBRACE) {
                BlockResult block = parseBlock(ts, pos, end);
                return new ValueResult(block.node(), block.next());
            }
            List<CstNode> parts = new ArrayList<>();
            CstNode firstNode = node(valueKind(first), first); parts.add(firstNode);
            int valueEnd = first.end; pos++;
            if (first.malformed)
                diagnostics.add(new Diagnostic("MALFORMED_VALUE", Diagnostic.Severity.ERROR,
                        "malformed value", first.start, first.end));

            // Inline math/conditional expressions are token sequences.  A
            // same-line token followed by an operator starts the next entry;
            // a same-line brace is a typed-block suffix (`= hbox { ... }`).
            while (pos < end) {
                int q = pos; boolean lineBreak = false; List<CstNode> pending = new ArrayList<>();
                while (q < end && isTrivia(ts.get(q))) {
                    Token tr = ts.get(q); pending.add(node(tr));
                    if (containsLineBreak(tr)) { lineBreak = true; break; }
                    q++;
                }
                if (q >= end || lineBreak || ts.get(q).type == T.RBRACE) break;
                if (ts.get(q).type == T.LBRACE) {
                    parts.addAll(pending);
                    BlockResult block = parseBlock(ts, q, end);
                    parts.add(block.node()); pos = block.next(); valueEnd = block.node().span().end();
                    break;
                }
                int look = q + 1; boolean lookBreak = false;
                while (look < end && isTrivia(ts.get(look))) {
                    if (containsLineBreak(ts.get(look))) { lookBreak = true; break; }
                    look++;
                }
                if (lookBreak || (look < end && ts.get(look).type == T.OP)) break;
                parts.addAll(pending);
                Token more = ts.get(q); parts.add(node(valueKind(more), more));
                valueEnd = more.end; pos = q + 1;
                if (more.malformed)
                    diagnostics.add(new Diagnostic("MALFORMED_VALUE", Diagnostic.Severity.ERROR,
                            "malformed value", more.start, more.end));
            }
            CstNode value = parts.size() == 1 ? parts.get(0) :
                    new Node(SyntaxKind.VALUE, new SourceSpan(first.start, valueEnd), b, parts);
            return new ValueResult(value, pos);
        }

        private BlockResult parseBlock(List<Token> ts, int openPos, int end) {
            Token open = ts.get(openPos); List<CstNode> children = new ArrayList<>();
            children.add(node(SyntaxKind.LBRACE, open));
            int pos = parseSequence(ts, openPos + 1, end, children, true);
            if (pos < end && ts.get(pos).type == T.RBRACE) {
                children.add(node(SyntaxKind.RBRACE, ts.get(pos))); pos++;
            } else {
                int at = pos < end ? ts.get(pos).start : b.length;
                diagnostics.add(new Diagnostic("UNCLOSED_BLOCK", Diagnostic.Severity.ERROR,
                        "block is not closed with '}'", open.start, at));
            }
            int blockEnd = children.isEmpty() ? open.end : children.get(children.size() - 1).span().end();
            return new BlockResult(new BlockNode(new SourceSpan(open.start, blockEnd), b, children), pos);
        }

        private record BlockResult(BlockNode node, int next) { }
        private record ValueResult(CstNode node, int next) { }

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
