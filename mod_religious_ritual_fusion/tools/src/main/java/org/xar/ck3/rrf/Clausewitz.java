package org.xar.ck3.rrf;

import java.util.ArrayList;
import java.util.List;
import java.util.function.UnaryOperator;

/** Token-based Clausewitz reader. Repeated keys, ordering, quoted atoms and list values are preserved. */
public final class Clausewitz {
    private Clausewitz() { }
    public sealed interface Value permits Atom, Block { String render(); }
    public record Atom(String token) implements Value {
        public Atom { if (token == null || token.isEmpty()) throw new IllegalArgumentException("empty atom"); }
        @Override public String render() { return token; }
    }
    public record Entry(String key, String operator, Value value) {
        public Entry { if (key == null || operator == null || value == null) throw new IllegalArgumentException("null AST entry"); }
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
    public static Block parse(String source) {
        Parser parser = new Parser(source);
        Block result = parser.block(false);
        if (parser.peek() != null) throw new IllegalArgumentException("trailing token");
        return result;
    }
    public static Block mapAtoms(Block block, UnaryOperator<String> mapper) {
        return new Block(block.entries().stream().map(e -> new Entry(mapper.apply(e.key()), e.operator(),
                e.value() instanceof Block child ? mapAtoms(child, mapper) : new Atom(mapper.apply(((Atom) e.value()).token())))).toList());
    }
    private static final class Parser {
        private final String source;
        private int offset;
        private String lookahead;
        Parser(String source) { this.source = source; }
        String peek() { if (lookahead == null) lookahead = token(); return lookahead; }
        String next() { String token = peek(); lookahead = null; return token; }
        Block block(boolean braced) {
            List<Entry> result = new ArrayList<>();
            while (peek() != null && !peek().equals("}")) {
                String key = next();
                if (key.equals("{")) { result.add(new Entry("", "", block(true))); continue; }
                if (isOperator(peek())) {
                    String operator = next();
                    String value = next();
                    if (value == null || value.equals("}")) throw failure("missing value after " + key);
                    result.add(new Entry(key, operator, value.equals("{") ? block(true) : new Atom(value)));
                } else result.add(new Entry("", "", new Atom(key)));
            }
            if (braced) { if (!"}".equals(next())) throw failure("unclosed block"); }
            else if (peek() != null) throw failure("unexpected closing brace");
            return new Block(result);
        }
        private static boolean isOperator(String token) { return token != null && List.of("=", "?=", "!=", "<", ">", "<=", ">=").contains(token); }
        private IllegalArgumentException failure(String reason) { return new IllegalArgumentException(reason + " at offset " + offset); }
        private String token() {
            while (offset < source.length()) {
                char c = source.charAt(offset);
                if (Character.isWhitespace(c) || c == '\ufeff') { offset++; continue; }
                if (c == '#') { while (offset < source.length() && source.charAt(offset) != '\n') offset++; continue; }
                break;
            }
            if (offset == source.length()) return null;
            int start = offset;
            char c = source.charAt(offset++);
            if (c == '"') {
                boolean escaped = false;
                while (offset < source.length()) {
                    char q = source.charAt(offset++);
                    if (q == '"' && !escaped) return source.substring(start, offset);
                    escaped = q == '\\' && !escaped;
                }
                throw failure("unterminated quoted atom");
            }
            if (c == '{' || c == '}') return Character.toString(c);
            if (c == '=' || c == '!' || c == '<' || c == '>' || c == '?') {
                if (offset < source.length() && source.charAt(offset) == '=') offset++;
                return source.substring(start, offset);
            }
            while (offset < source.length()) {
                char t = source.charAt(offset);
                if (Character.isWhitespace(t) || "{}=!?<>#".indexOf(t) >= 0) break;
                offset++;
            }
            return source.substring(start, offset);
        }
    }
}
