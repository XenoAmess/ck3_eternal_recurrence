package org.xar.ck3.save;

import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.Reader;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.UnaryOperator;

/** Ordered, lossless lexemes. No numeric coercion or interpretation of game effects. */
public final class Clausewitz {
    private Clausewitz() { }
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
    @JsonSubTypes({@JsonSubTypes.Type(value = Atom.class, name = "atom"), @JsonSubTypes.Type(value = Block.class, name = "block")})
    public sealed interface Value permits Atom, Block { String render(); }
    public record Atom(String token) implements Value {
        public Atom { if (token == null || token.isEmpty()) throw new IllegalArgumentException("empty atom"); }
        @Override public String render() { return token; }
    }
    public record Entry(String key, String operator, Value value) {
        public Entry {
            Objects.requireNonNull(key); Objects.requireNonNull(operator); Objects.requireNonNull(value);
            if (!operator.isEmpty() && !isOperator(operator)) throw new IllegalArgumentException("unknown operator");
            if (operator.isEmpty() != key.isEmpty()) throw new IllegalArgumentException("named/list entry mismatch");
        }
        public String render() { return operator.isEmpty() ? value.render() : key + " " + operator + " " + value.render(); }
    }
    public record Block(List<Entry> entries) implements Value {
        public Block { entries = List.copyOf(entries); }
        @Override public String render() { return "{ " + body() + " }"; }
        public String body() { return String.join(" ", entries.stream().map(Entry::render).toList()); }
        public List<Entry> named(String key) { return entries.stream().filter(e -> e.key().equals(key)).toList(); }
        public String atom(String key, String fallback) {
            List<Entry> found = named(key);
            if (found.isEmpty()) return fallback;
            if (found.size() != 1 || !(found.getFirst().value() instanceof Atom atom)) throw new IllegalArgumentException("expected one atom: " + key);
            return atom.token();
        }
        public Block block(String key) {
            List<Entry> found = named(key);
            if (found.isEmpty()) return new Block(List.of());
            if (found.size() != 1 || !(found.getFirst().value() instanceof Block block)) throw new IllegalArgumentException("expected one block: " + key);
            return block;
        }
    }
    /** SAVE preserves the historical melt token boundary; SCRIPT recognizes comparison operators. */
    public enum Syntax { SCRIPT, SAVE }
    public static final class Lexer {
        private final Reader reader;
        private final Syntax syntax;
        private final int maxToken;
        private int character = -2;
        private String lookahead;
        private long tokens;
        public Lexer(Reader reader, Syntax syntax, int maxToken) {
            this.reader = new BufferedReader(Objects.requireNonNull(reader), 65536);
            this.syntax = Objects.requireNonNull(syntax);
            if (maxToken < 1 || maxToken > 2 * 1024 * 1024) throw new IllegalArgumentException("token bound required");
            this.maxToken = maxToken;
        }
        public long tokens() { return tokens; }
        public String peek() throws IOException { if (lookahead == null) lookahead = token(); return lookahead; }
        public String next() throws IOException { String value = peek(); lookahead = null; if (value != null) tokens++; return value; }
        private int current() throws IOException { if (character == -2) character = reader.read(); return character; }
        private int take() throws IOException { int value = current(); character = -2; return value; }
        private String token() throws IOException {
            while (current() != -1) {
                if (Character.isWhitespace(current()) || current() == '\ufeff') { take(); continue; }
                if (current() == '#') { while (current() != -1 && take() != '\n') { } continue; }
                break;
            }
            if (current() == -1) return null;
            StringBuilder token = new StringBuilder(); int first = take(); token.append((char) first);
            if (first == '{' || first == '}') return token.toString();
            if (first == '"') {
                boolean escaped = false;
                while (current() != -1) {
                    int c = take(); token.append((char) c); check(token);
                    if (c == '"' && !escaped) return token.toString();
                    escaped = c == '\\' && !escaped;
                }
                throw new IOException("truncated quoted atom");
            }
            if (first == '=' || syntax == Syntax.SCRIPT && "!?<>".indexOf(first) >= 0) {
                if (syntax == Syntax.SCRIPT && current() == '=') token.append((char) take());
                return token.toString();
            }
            String delimiters = syntax == Syntax.SCRIPT ? "{}=!?<>#" : "{}=#";
            while (current() != -1 && !Character.isWhitespace(current()) && delimiters.indexOf(current()) < 0) {
                token.append((char) take()); check(token);
            }
            return token.toString();
        }
        private void check(StringBuilder token) throws IOException { if (token.length() > maxToken) throw new IOException("token cap exceeded"); }
    }
    public static Block parse(String source) {
        Objects.requireNonNull(source);
        try { return parse(new StringReader(source)); }
        catch (IOException error) { throw new IllegalArgumentException(error.getMessage(), error); }
    }
    public static Block parse(Reader reader) throws IOException { return new Parser(new Lexer(reader, Syntax.SCRIPT, 2 * 1024 * 1024)).block(false, 0); }
    public static Block mapAtoms(Block block, UnaryOperator<String> mapper) {
        return new Block(block.entries().stream().map(e -> new Entry(mapper.apply(e.key()), e.operator(),
                e.value() instanceof Block child ? mapAtoms(child, mapper) : new Atom(mapper.apply(((Atom) e.value()).token())))).toList());
    }
    public static boolean isOperator(String token) { return token != null && List.of("=", "?=", "!=", "<", ">", "<=", ">=").contains(token); }
    private static final class Parser {
        private final Lexer lexer;
        private Parser(Lexer lexer) { this.lexer = lexer; }
        private Block block(boolean braced, int depth) throws IOException {
            if (depth > 128) throw new IOException("AST nesting cap exceeded");
            List<Entry> result = new ArrayList<>();
            while (lexer.peek() != null && !lexer.peek().equals("}")) {
                String key = lexer.next();
                if (isOperator(key)) throw new IOException("unexpected operator");
                if (key.equals("{")) { result.add(new Entry("", "", block(true, depth + 1))); continue; }
                if (isOperator(lexer.peek())) {
                    String operator = lexer.next(); String value = lexer.next();
                    if (value == null || value.equals("}") || isOperator(value)) throw new IOException("missing assigned value");
                    result.add(new Entry(key, operator, value.equals("{") ? block(true, depth + 1) : new Atom(value)));
                } else result.add(new Entry("", "", new Atom(key)));
            }
            if (braced) { if (!"}".equals(lexer.next())) throw new IOException("truncated block"); }
            else if (lexer.peek() != null) throw new IOException("unexpected root closing brace");
            return new Block(result);
        }
    }
}
