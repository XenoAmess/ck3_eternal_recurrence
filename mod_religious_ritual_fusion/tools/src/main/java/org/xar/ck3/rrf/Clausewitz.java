package org.xar.ck3.rrf;

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
        return fromShared(org.xar.ck3.save.Clausewitz.parse(source));
    }
    public static Block fromShared(org.xar.ck3.save.Clausewitz.Block block) {
        return new Block(block.entries().stream().map(e -> new Entry(e.key(), e.operator(),
                e.value() instanceof org.xar.ck3.save.Clausewitz.Block child ? fromShared(child)
                : new Atom(((org.xar.ck3.save.Clausewitz.Atom) e.value()).token()))).toList());
    }
    public static Block mapAtoms(Block block, UnaryOperator<String> mapper) {
        return new Block(block.entries().stream().map(e -> new Entry(mapper.apply(e.key()), e.operator(),
                e.value() instanceof Block child ? mapAtoms(child, mapper) : new Atom(mapper.apply(((Atom) e.value()).token())))).toList());
    }
}
