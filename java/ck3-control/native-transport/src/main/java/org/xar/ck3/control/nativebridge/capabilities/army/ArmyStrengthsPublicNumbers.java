package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** Explicit schema paths at the JSON codec boundary. Native packets and typed numeric domains stay exact. */
public final class ArmyStrengthsPublicNumbers {
    private ArmyStrengthsPublicNumbers() { }
    public enum Domain { SIGNED_64, UNSIGNED_64, INTEGER }
    /** OBJECT_BRANCHES is declared only for an already decoded scalar/object union. */
    public enum Traversal { STRICT, OBJECT_BRANCHES }
    /** Canonical slash-prefixed fields, literal array indexes or '*'; '*' never means an object-key glob. */
    public record Rule(String exactPath, Domain domain, Traversal traversal) {
        public Rule {
            Objects.requireNonNull(exactPath); Objects.requireNonNull(domain); Objects.requireNonNull(traversal);
            require(exactPath.matches("/(?:[A-Za-z_][A-Za-z0-9_]*|0|[1-9][0-9]*|\\*)(?:/(?:[A-Za-z_][A-Za-z0-9_]*|0|[1-9][0-9]*|\\*))*"),
                    "public numeric path requires exact schema fields or explicit array wildcards");
        }
        public Rule(String exactPath, Domain domain) { this(exactPath, domain, Traversal.STRICT); }
        public Rule prefixed(String prefix) { return new Rule(Objects.requireNonNull(prefix) + exactPath, domain, traversal); }
    }
    public static RawJson encode(RawJson nativeJson, List<Rule> rules) {
        Objects.requireNonNull(nativeJson); rules = List.copyOf(rules);
        JsonNode projected = ArmyStrengthsCodec.parseValue(nativeJson).deepCopy();
        var unique = new HashSet<String>();
        for (Rule rule : rules) {
            require(unique.add(rule.exactPath()), "duplicate public numeric schema path");
            apply(projected, rule.exactPath().substring(1).split("/"), 0, rule.domain(), rule.traversal());
        }
        return new RawJson(ArmyJson.bytes(projected));
    }
    private static void apply(JsonNode node, String[] segments, int index, Domain domain, Traversal traversal) {
        if (node.isNull()) return;
        String segment = segments[index];
        if (segment.matches("0|[1-9][0-9]*")) {
            require(node instanceof ArrayNode, "literal numeric public path segment requires an actual array");
            ArrayNode array = (ArrayNode) node; int selected;
            try { selected = Integer.parseInt(segment); }
            catch (NumberFormatException invalid) { throw new IllegalArgumentException("public schema array index outside int32", invalid); }
            if (selected >= array.size() || array.get(selected).isNull()) return;
            if (index + 1 == segments.length) array.set(selected, integer(array.get(selected), domain));
            else apply(array.get(selected), segments, index + 1, domain, traversal);
            return;
        }
        if (segment.equals("*")) {
            require(node instanceof ArrayNode, "public numeric wildcard requires an actual array");
            ArrayNode array = (ArrayNode) node;
            if (index + 1 == segments.length) {
                for (int i = 0; i < array.size(); i++) if (!array.get(i).isNull()) array.set(i, integer(array.get(i), domain));
            } else for (JsonNode item : array) apply(item, segments, index + 1, domain, traversal);
            return;
        }
        if (!(node instanceof ObjectNode) && traversal == Traversal.OBJECT_BRANCHES && node.isValueNode()) return;
        require(node instanceof ObjectNode, "public numeric schema path crosses a non-object");
        ObjectNode object = (ObjectNode) node;
        JsonNode child = object.get(segment);
        if (child == null || child.isNull()) return;
        if (index + 1 < segments.length) { apply(child, segments, index + 1, domain, traversal); return; }
        object.set(segment, integer(child, domain));
    }
    private static JsonNode integer(JsonNode child, Domain domain) {
        require(child.isIntegralNumber(), "declared public wide integer must be an exact JSON integer before encoding");
        BigInteger value = child.bigIntegerValue();
        if (domain == Domain.SIGNED_64) require(value.bitLength() <= 63, "public signed64 schema value outside its exact domain");
        if (domain == Domain.UNSIGNED_64) require(value.signum() >= 0 && value.bitLength() <= 64, "public uint64 schema value outside its exact domain");
        return ArmyJson.empty().textNode(value.toString());
    }
}

