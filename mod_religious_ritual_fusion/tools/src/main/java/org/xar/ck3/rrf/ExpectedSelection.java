package org.xar.ck3.rrf;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.rrf.Contracts.Catalog;
import org.xar.ck3.rrf.Contracts.Definition;
import org.xar.ck3.rrf.Contracts.Kind;

/** One selection contract for fixture generation and independent saved-AST comparison. */
public record ExpectedSelection(List<ExpectedSelection.TenetKey> coreTenets) {
    public ExpectedSelection {
        coreTenets = List.copyOf(coreTenets);
        if (coreTenets.size() < 3 || coreTenets.size() > 100) throw new IllegalArgumentException("expected core selection must contain 3..100 entries");
        unique(coreTenets, "expected core selection");
    }
    public record TenetKey(String value) {
        public TenetKey { Contracts.identifier(value); if (!value.startsWith("tenet_")) throw new IllegalArgumentException("tenet catalog key required"); }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING) public static TenetKey fromJson(JsonNode node) {
            if (node == null || !node.isTextual()) throw new IllegalArgumentException("tenet key must be a string");
            return new TenetKey(node.textValue());
        }
        @JsonValue public String value() { return value; }
    }
    public void requireCatalog(Catalog catalog) {
        for (TenetKey key : coreTenets) {
            Definition definition = catalog.definitions().stream().filter(row -> row.id().equals(key.value())).findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("unknown expected tenet: " + key.value()));
            if (definition.kind() != Kind.TENET || !definition.visible() || !definition.blockedReasons().isEmpty()) throw new IllegalArgumentException("expected key is not a real visible catalog tenet: " + key.value());
        }
    }
    public void requireSources(List<TenetKey> sourceA, List<TenetKey> sourceB) {
        unique(sourceA, "source A cores"); unique(sourceB, "source B cores");
        Set<TenetKey> a = Set.copyOf(sourceA), b = Set.copyOf(sourceB);
        Set<TenetKey> reachable = new LinkedHashSet<>(a); reachable.addAll(b);
        if (!reachable.containsAll(coreTenets)) throw new IllegalArgumentException("expected selection is outside the source union; current fixture reaches only " + reachable.size() + " cores");
        if (coreTenets.stream().noneMatch(key -> a.contains(key) && !b.contains(key))
                || coreTenets.stream().noneMatch(key -> b.contains(key) && !a.contains(key))) throw new IllegalArgumentException("expected selection needs an exclusive core contribution from both sources");
    }
    public void requireExact(List<TenetKey> observed, String label) {
        unique(observed, label);
        if (observed.size() != coreTenets.size() || !Set.copyOf(observed).equals(Set.copyOf(coreTenets))) throw new IllegalArgumentException(label + " differs from the frozen exact core selection");
    }
    public static void unique(List<TenetKey> values, String label) {
        if (Set.copyOf(values).size() != values.size()) throw new IllegalArgumentException(label + " contains duplicate cores");
    }
}
