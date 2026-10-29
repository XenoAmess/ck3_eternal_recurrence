package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.shape;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonDiacNumericCodec.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Exact Rule43 recursive short-circuit/root admission and following Diac selection. */
public final class BattlePersonDiacCodec {
    private BattlePersonDiacCodec() { }
    private static final BigInteger NODE58 = BigInteger.valueOf(0x855AB0L), NODE60A = BigInteger.valueOf(0x9CFEC0L), NODE60B = BigInteger.valueOf(0x9CFEE0L), AND = BigInteger.valueOf(0x372F780L), REFERENCE = BigInteger.valueOf(0x3730940L), VALIDATOR = BigInteger.valueOf(0x22565B0L);
    public enum Verdict {
        TRUE, FALSE, UNKNOWN;
        public static Verdict from(Optional<Boolean> value) { return value.isEmpty() ? UNKNOWN : value.orElseThrow() ? TRUE : FALSE; }
        public Optional<Boolean> asOptional() { return this == UNKNOWN ? Optional.empty() : Optional.of(this == TRUE); }
    }
    public enum Lookup {
        REGISTRY_FULL_GENERATION("registry_full_generation"), NATIVE_FALLBACK("native_fallback");
        private final String wire; Lookup(String wire) { this.wire = wire; } public String wire() { return wire; }
        static Lookup decode(String value, String field) { for (Lookup route : values()) if (route.wire.equals(value)) return route; throw bad(field, "unknown full-generation lookup selection"); }
    }
    public enum Descriptor {
        REGISTRY_KIND4("registry_kind4"), NATIVE_DESCRIPTOR_FALLBACK("native_descriptor_fallback");
        private final String wire; Descriptor(String wire) { this.wire = wire; } public String wire() { return wire; }
        static Descriptor decode(String value, String field) { for (Descriptor d : values()) if (d.wire.equals(value)) return d; throw bad(field, "unknown loaded descriptor selection"); }
    }
    public enum Family {
        PRIMARY_620("primary_620"), SECONDARY_658("secondary_658"), NONE("none");
        private final String wire; Family(String wire) { this.wire = wire; } public String wire() { return wire; }
        static Family decode(String value, String field) { for (Family f : values()) if (f.wire.equals(value)) return f; throw bad(field, "unknown selected family"); }
    }
    public record Node(String path, Optional<String> identity, Optional<BigInteger> slot58, Optional<BigInteger> slot60, Optional<BigInteger> slotC8,
            Optional<Integer> childrenCount, Optional<Boolean> childrenArrayPresent, Optional<Integer> referenceArgumentsCount,
            Optional<Integer> referenceCompare, Optional<Boolean> nestedPresent, List<Node> children, Verdict result, Optional<String> reason) {
        public Node { require(path != null && !path.isEmpty(), "Rule43 node", "native occurrence path required"); children = List.copyOf(children); Objects.requireNonNull(result); Objects.requireNonNull(reason); }
        public ObjectNode toJson() { ObjectNode row = object().put("path", path); putText(row, "identity", identity); putText(row, "reason", reason); putNumber(row, "slot58_rva", slot58); putNumber(row, "slot60_rva", slot60); putNumber(row, "slotc8_rva", slotC8); putInt(row, "children_count_raw", childrenCount); putInt(row, "reference_arguments_count_raw", referenceArgumentsCount); putInt(row, "reference_compare_raw", referenceCompare); putBool(row, "children_array_present", childrenArrayPresent); putBool(row, "nested_present", nestedPresent); putBool(row, "result", result.asOptional()); ArrayNode a = row.putArray("children"); children.forEach(c -> a.add(c.toJson())); return row; }
    }
    public record Admission(int inputCharacterFullId, int sourceConstructedRootKind, BigInteger expectedValidatorRva, Optional<Integer> mode,
            Optional<String> providerIdentity, Optional<String> ruleIdentity, Optional<Integer> registryCount, Optional<Descriptor> descriptor,
            Optional<BigInteger> loadedValidatorRva, Optional<Lookup> rootLookup, Optional<String> rootObjectIdentity, Optional<BigInteger> rootTag,
            Optional<Integer> rootFullId, Verdict rootValid, List<Node> nodes, Verdict result, Optional<String> reason) {
        public Admission { nodes = List.copyOf(nodes); Objects.requireNonNull(rootValid); Objects.requireNonNull(result); Objects.requireNonNull(reason); }
        public ObjectNode toJson() {
            ObjectNode row = object().put("input_character_full_id", inputCharacterFullId).put("source_constructed_root_kind", sourceConstructedRootKind).put("expected_validator_rva", expectedValidatorRva);
            putInt(row, "mode_raw", mode); putText(row, "provider_identity", providerIdentity); putText(row, "rule_identity", ruleIdentity); putInt(row, "registry_count_raw", registryCount); putText(row, "descriptor_selection", descriptor.map(Descriptor::wire)); putText(row, "root_lookup_selection", rootLookup.map(Lookup::wire)); putText(row, "root_object_identity", rootObjectIdentity); putText(row, "reason", reason); putNumber(row, "loaded_validator_rva", loadedValidatorRva); putNumber(row, "root_tag_raw", rootTag); putInt(row, "root_full_id_raw", rootFullId); putBool(row, "root_valid", rootValid.asOptional()); putBool(row, "result", result.asOptional()); ArrayNode a = row.putArray("nodes"); nodes.forEach(n -> a.add(n.toJson())); return row;
        }
    }
    public record Selection(Optional<String> sourceCharacterIdentity, Optional<Lookup> lookup, Optional<String> diacIdentity,
            Optional<String> earlyCharacterLookup, Optional<Integer> requestedDiacId, Optional<Integer> diacFullId,
            Optional<Integer> diacOwnerFullId, Optional<Integer> ruleCharacterFullId, Optional<BigInteger> diacTag,
            Verdict diacValid, Verdict ownerMatches, Optional<Admission> rule, Optional<String> reason) {
        public Selection { Objects.requireNonNull(diacValid); Objects.requireNonNull(ownerMatches); Objects.requireNonNull(rule); Objects.requireNonNull(reason); }
        public ObjectNode toJson() { ObjectNode row = object(); putText(row, "source_character_identity", sourceCharacterIdentity); putText(row, "lookup_selection", lookup.map(Lookup::wire)); putText(row, "diac_identity", diacIdentity); putText(row, "early_character_lookup_selection", earlyCharacterLookup); putText(row, "reason", reason); putInt(row, "requested_diac_id_raw", requestedDiacId); putInt(row, "diac_full_id_raw", diacFullId); putInt(row, "diac_owner_full_id_raw", diacOwnerFullId); putInt(row, "rule_character_full_id_raw", ruleCharacterFullId); putNumber(row, "diac_tag_raw", diacTag); putBool(row, "diac_valid", diacValid.asOptional()); putBool(row, "owner_matches", ownerMatches.asOptional()); if (rule.isPresent()) row.set("rule", rule.orElseThrow().toJson()); else row.putNull("rule"); return row; }
    }
    public record Following(State state, int characterId, Optional<Integer> currentCharacterFullId, Selection primary,
            Optional<Selection> secondary, Optional<Family> selectedFamily, Optional<Inputs> numericInputs) {
        public Following { Objects.requireNonNull(state); Objects.requireNonNull(currentCharacterFullId); Objects.requireNonNull(primary); Objects.requireNonNull(secondary); Objects.requireNonNull(selectedFamily); Objects.requireNonNull(numericInputs); }
        public ObjectNode toJson() { ObjectNode row = state.toJson().put("character_id", characterId); putInt(row, "current_character_full_id_raw", currentCharacterFullId); row.set("primary", primary.toJson()); if (secondary.isPresent()) row.set("secondary", secondary.orElseThrow().toJson()); else row.putNull("secondary"); putText(row, "selected_family", selectedFamily.map(Family::wire)); if (numericInputs.isPresent()) row.set("numeric_inputs", numericInputs.orElseThrow().toJson()); else row.putNull("numeric_inputs"); return row; }
    }

    /** Unique Late-facade leaf ABI. Explicit JSON null remains NullNode. */
    public static JsonNode normalize(JsonNode raw, String field) { return decode(raw, field).<JsonNode>map(Following::toJson).orElse(NullNode.instance); }
    public static Optional<Following> decode(JsonNode raw, String field) {
        Objects.requireNonNull(field); if (nil(raw)) return Optional.empty();
        ObjectNode row = shape(raw, field, "status", "ready", "reason", "character_id", "current_character_full_id_raw", "primary", "secondary", "selected_family", "numeric_inputs");
        State state = state(row, field); int actor = requiredInt(row.get("character_id"), field + ".character_id", 32, false); Optional<Integer> current = intNumber(row.get("current_character_full_id_raw"), field + ".current_character_full_id_raw", 32, false);
        Selection primary = selection(row.get("primary"), field + ".primary"); Optional<Selection> secondary = nil(row.get("secondary")) ? Optional.empty() : Optional.of(selection(row.get("secondary"), field + ".secondary"));
        Optional<Family> claimed = optionalText(row.get("selected_family"), field + ".selected_family").map(s -> Family.decode(s, field)); Optional<Inputs> numeric = nil(row.get("numeric_inputs")) ? Optional.empty() : Optional.of(BattlePersonDiacNumericCodec.decode(row.get("numeric_inputs")));
        require(current.isEmpty() || current.orElseThrow() == actor, field, "current Character18 differs from enclosing actor");
        Verdict primaryResult = primary.rule().map(Admission::result).orElse(Verdict.UNKNOWN); boolean proceed = primary.diacValid() == Verdict.FALSE || primary.diacValid() == Verdict.TRUE && primaryResult == Verdict.FALSE;
        Optional<Family> family = Optional.empty(); if (primary.diacValid() == Verdict.TRUE && primaryResult == Verdict.TRUE) family = Optional.of(Family.PRIMARY_620);
        require(proceed || secondary.isEmpty(), field, "secondary read after unknown/accepted primary");
        if (proceed && secondary.isPresent()) {
            Selection selected = secondary.orElseThrow();
            if (selected.diacValid() == Verdict.FALSE) family = Optional.of(Family.NONE);
            else if (selected.diacValid() == Verdict.TRUE) {
                Verdict matches = current.isEmpty() || selected.diacOwnerFullId().isEmpty() ? Verdict.UNKNOWN : current.equals(selected.diacOwnerFullId()) ? Verdict.TRUE : Verdict.FALSE;
                require(selected.ownerMatches() == matches, field, "secondary owner comparison differs from raw DWORDs"); Verdict ruleResult = selected.rule().map(Admission::result).orElse(Verdict.UNKNOWN);
                if (matches == Verdict.FALSE || matches == Verdict.TRUE && ruleResult == Verdict.FALSE) family = Optional.of(Family.NONE);
                else if (matches == Verdict.TRUE && ruleResult == Verdict.TRUE) family = Optional.of(Family.SECONDARY_658);
            }
        }
        require(family.equals(claimed), field, "native primary/secondary selection disagrees");
        require(family.isPresent() && family.orElseThrow() != Family.NONE || numeric.isEmpty(), field, "unselected family published numeric inputs");
        if (numeric.isPresent()) { Optional<Integer> scope = family.equals(Optional.of(Family.PRIMARY_620)) ? primary.diacOwnerFullId() : current; require(numeric.orElseThrow().scopeCharacterFullId().isEmpty() || numeric.orElseThrow().scopeCharacterFullId().equals(scope), field, "numeric scope differs from actual caller full-ID source"); }
        boolean complete = family.equals(Optional.of(Family.NONE)) || family.isPresent() && family.orElseThrow() != Family.NONE && numeric.isPresent() && numeric.orElseThrow().state().ready();
        require(state.ready() == (complete && state.reason().isEmpty()), field, "bounded whole-source readiness disagrees"); return Optional.of(new Following(state, actor, current, primary, secondary, family, numeric));
    }
    private static Selection selection(JsonNode raw, String field) {
        ObjectNode row = shape(raw, field, "source_character_identity", "lookup_selection", "diac_identity", "early_character_lookup_selection", "requested_diac_id_raw", "diac_full_id_raw", "diac_owner_full_id_raw", "rule_character_full_id_raw", "diac_tag_raw", "diac_valid", "owner_matches", "rule", "reason");
        Optional<String> source = optionalText(row.get("source_character_identity"), field + ".source_character_identity"), identity = optionalText(row.get("diac_identity"), field + ".diac_identity"), early = optionalText(row.get("early_character_lookup_selection"), field + ".early_character_lookup_selection"), reason = optionalText(row.get("reason"), field + ".reason");
        Optional<Lookup> lookup = optionalText(row.get("lookup_selection"), field + ".lookup_selection").map(s -> Lookup.decode(s, field)); Optional<Integer> requested = intNumber(row.get("requested_diac_id_raw"), field + ".requested_diac_id_raw", 32, false), full = intNumber(row.get("diac_full_id_raw"), field + ".diac_full_id_raw", 32, false), owner = intNumber(row.get("diac_owner_full_id_raw"), field + ".diac_owner_full_id_raw", 32, false), character = intNumber(row.get("rule_character_full_id_raw"), field + ".rule_character_full_id_raw", 32, false);
        Optional<BigInteger> tag = optionalNumber(row.get("diac_tag_raw"), field + ".diac_tag_raw", 32, true); Verdict valid = Verdict.from(optionalBool(row.get("diac_valid"), field + ".diac_valid")), matches = Verdict.from(optionalBool(row.get("owner_matches"), field + ".owner_matches"));
        Verdict calculated = tag.isEmpty() ? Verdict.UNKNOWN : !tag.orElseThrow().equals(BigInteger.valueOf(0x44696163L)) ? Verdict.FALSE : full.isEmpty() ? Verdict.UNKNOWN : full.orElseThrow() != -1 ? Verdict.TRUE : Verdict.FALSE;
        require(valid == calculated, field, "Diac tag/full-ID predicate disagrees"); if (lookup.equals(Optional.of(Lookup.REGISTRY_FULL_GENERATION)) && full.isPresent()) require(full.equals(requested), field, "Diac generation disagrees");
        Optional<Admission> rule = nil(row.get("rule")) ? Optional.empty() : Optional.of(admission(row.get("rule"), field + ".rule"));
        if (rule.isPresent()) require(valid == Verdict.TRUE && character.equals(Optional.of(rule.orElseThrow().inputCharacterFullId())), field, "rule input differs from selected Character18");
        return new Selection(source, lookup, identity, early, requested, full, owner, character, tag, valid, matches, rule, reason);
    }
    private static Admission admission(JsonNode raw, String field) {
        ObjectNode row = shape(raw, field, "input_character_full_id", "source_constructed_root_kind", "expected_validator_rva", "mode_raw", "provider_identity", "rule_identity", "registry_count_raw", "descriptor_selection", "loaded_validator_rva", "root_lookup_selection", "root_object_identity", "root_tag_raw", "root_full_id_raw", "root_valid", "nodes", "result", "reason");
        int actor = requiredInt(row.get("input_character_full_id"), field + ".input_character_full_id", 32, false), rootKind = requiredInt(row.get("source_constructed_root_kind"), field + ".source_constructed_root_kind", 16, true); BigInteger expected = number(row.get("expected_validator_rva"), field + ".expected_validator_rva", 64, true, false).bigIntegerValue();
        require(rootKind == 4 && expected.equals(VALIDATOR), field, "source kind/expected validator differs from exact .3");
        Optional<String> provider = optionalText(row.get("provider_identity"), field + ".provider_identity"), identity = optionalText(row.get("rule_identity"), field + ".rule_identity"), rootIdentity = optionalText(row.get("root_object_identity"), field + ".root_object_identity"), reason = optionalText(row.get("reason"), field + ".reason");
        Optional<Integer> count = intNumber(row.get("registry_count_raw"), field + ".registry_count_raw", 32, false), full = intNumber(row.get("root_full_id_raw"), field + ".root_full_id_raw", 32, false), mode = intNumber(row.get("mode_raw"), field + ".mode_raw", 8, true);
        Optional<BigInteger> tag = optionalNumber(row.get("root_tag_raw"), field + ".root_tag_raw", 32, true), loaded = optionalNumber(row.get("loaded_validator_rva"), field + ".loaded_validator_rva", 64, true);
        Optional<Descriptor> descriptor = optionalText(row.get("descriptor_selection"), field + ".descriptor_selection").map(s -> Descriptor.decode(s, field)); Optional<Lookup> lookup = optionalText(row.get("root_lookup_selection"), field + ".root_lookup_selection").map(s -> Lookup.decode(s, field));
        if (descriptor.isPresent()) require(count.isPresent() && descriptor.orElseThrow() == (count.orElseThrow() > 4 ? Descriptor.REGISTRY_KIND4 : Descriptor.NATIVE_DESCRIPTOR_FALLBACK), field, "loaded descriptor selection disagrees");
        Verdict root = Verdict.UNKNOWN;
        if (loaded.equals(Optional.of(expected)) && lookup.isPresent() && rootIdentity.isPresent() && tag.isPresent()) root = !tag.orElseThrow().equals(BigInteger.valueOf(0x43686172L)) ? Verdict.FALSE : full.isEmpty() ? Verdict.UNKNOWN : full.orElseThrow() != -1 ? Verdict.TRUE : Verdict.FALSE;
        Verdict rootClaim = Verdict.from(optionalBool(row.get("root_valid"), field + ".root_valid")); require(root == rootClaim, field, "root selected tag/full-ID predicate disagrees");
        if (lookup.equals(Optional.of(Lookup.REGISTRY_FULL_GENERATION)) && full.isPresent()) require(full.orElseThrow() == actor, field, "registry generation differs from raw root ID");
        List<JsonNode> rawNodes = ordered(row.get("nodes"), field + ".nodes"); require(rawNodes.size() <= 1 && (root == Verdict.TRUE || rawNodes.isEmpty()), field, "rule node demand disagrees with root admission");
        List<Node> nodes = new ArrayList<>(); for (JsonNode node : rawNodes) nodes.add(node(node, field + ".nodes[0]", mode, "rule43"));
        Verdict result = Verdict.from(optionalBool(row.get("result"), field + ".result")); Admission rule = new Admission(actor, rootKind, expected, mode, provider, identity, count, descriptor, loaded, lookup, rootIdentity, tag, full, root, nodes, result, reason); verdict(result, evaluateAdmission(rule), reason, field); return rule;
    }
    private static Node node(JsonNode raw, String field, Optional<Integer> mode, String path) {
        ObjectNode row = shape(raw, field, "path", "identity", "slot58_rva", "slot60_rva", "slotc8_rva", "children_count_raw", "children_array_present", "reference_arguments_count_raw", "reference_compare_raw", "nested_present", "children", "result", "reason");
        String actualPath = text(row.get("path"), field + ".path", false, true).textValue(); require(path.equals(actualPath), field, "native occurrence path disagrees");
        Optional<String> identity = optionalText(row.get("identity"), field + ".identity"), reason = optionalText(row.get("reason"), field + ".reason"); Optional<BigInteger> slot58 = optionalNumber(row.get("slot58_rva"), field + ".slot58_rva", 64, true), slot60 = optionalNumber(row.get("slot60_rva"), field + ".slot60_rva", 64, true), slotC8 = optionalNumber(row.get("slotc8_rva"), field + ".slotc8_rva", 64, true);
        Optional<Integer> count = intNumber(row.get("children_count_raw"), field + ".children_count_raw", 32, false), args = intNumber(row.get("reference_arguments_count_raw"), field + ".reference_arguments_count_raw", 32, false), compare = intNumber(row.get("reference_compare_raw"), field + ".reference_compare_raw", 8, true);
        Optional<Boolean> present = optionalBool(row.get("children_array_present"), field + ".children_array_present"), nested = optionalBool(row.get("nested_present"), field + ".nested_present"); Verdict result = Verdict.from(optionalBool(row.get("result"), field + ".result"));
        List<JsonNode> rows = ordered(row.get("children"), field + ".children"); boolean reference = slotC8.equals(Optional.of(REFERENCE)); List<Node> children = new ArrayList<>();
        for (int i = 0; i < rows.size(); i++) children.add(node(rows.get(i), field + ".children[" + i + "]", mode, path + (reference ? "/reference" : "/child" + i)));
        if (reference) require(children.size() <= 1 && (nested.equals(Optional.of(true)) || children.isEmpty()), field, "reference child demand disagrees");
        else {
            if (!children.isEmpty()) require(count.isPresent() && count.orElseThrow() > 0 && children.size() <= count.orElseThrow(), field, "conjunction child prefix disagrees");
            for (int i = 0; i + 1 < children.size(); i++) require(children.get(i).result() == Verdict.TRUE, field, "traversed a child after native short circuit");
        }
        Node node = new Node(actualPath, identity, slot58, slot60, slotC8, count, present, args, compare, nested, children, result, reason); verdict(result, evaluateNode(node, mode), reason, field); return node;
    }
    public static Verdict evaluateNode(Node node, Optional<Integer> mode) {
        Objects.requireNonNull(node); Objects.requireNonNull(mode);
        if (node.identity().isEmpty() || !node.slot58().equals(Optional.of(NODE58)) || !(node.slot60().equals(Optional.of(NODE60A)) || node.slot60().equals(Optional.of(NODE60B)))) return Verdict.UNKNOWN;
        if (node.slotC8().equals(Optional.of(AND))) {
            if (mode.equals(Optional.of(2)) || mode.equals(Optional.of(4))) return Verdict.UNKNOWN;
            if (node.childrenCount().isEmpty() || node.childrenCount().orElseThrow() < 0 || node.childrenArrayPresent().isEmpty()) return Verdict.UNKNOWN;
            if (node.childrenCount().orElseThrow() == 0) return Verdict.TRUE;
            for (Node child : node.children()) { Verdict selected = evaluateNode(child, mode); if (selected != Verdict.TRUE) return selected; }
            return node.children().size() == node.childrenCount().orElseThrow() ? Verdict.TRUE : Verdict.UNKNOWN;
        }
        if (node.slotC8().equals(Optional.of(REFERENCE))) {
            if (!node.referenceArgumentsCount().equals(Optional.of(0)) || node.nestedPresent().isEmpty()) return Verdict.UNKNOWN;
            Verdict nested = Verdict.FALSE;
            if (node.nestedPresent().orElseThrow()) { if (node.children().isEmpty()) return Verdict.UNKNOWN; nested = evaluateNode(node.children().getFirst(), mode); if (nested == Verdict.UNKNOWN) return Verdict.UNKNOWN; }
            return node.referenceCompare().isEmpty() ? Verdict.UNKNOWN : node.referenceCompare().orElseThrow() == (nested == Verdict.TRUE ? 1 : 0) ? Verdict.TRUE : Verdict.FALSE;
        }
        return Verdict.UNKNOWN;
    }
    public static Verdict evaluateAdmission(Admission rule) {
        Objects.requireNonNull(rule);
        if (rule.mode().isEmpty() || rule.providerIdentity().isEmpty() || rule.ruleIdentity().isEmpty() || !rule.loadedValidatorRva().equals(Optional.of(VALIDATOR))) return Verdict.UNKNOWN;
        if (rule.rootValid() == Verdict.FALSE) return Verdict.FALSE;
        if (rule.rootValid() != Verdict.TRUE || rule.nodes().isEmpty()) return Verdict.UNKNOWN;
        return evaluateNode(rule.nodes().getFirst(), rule.mode());
    }
    public static List<Request> emit(Following leaf) {
        require(leaf.state().ready(), "following_diac_2920d60", "Required native input unavailable: " + leaf.state().reason().orElse("null"));
        if (leaf.selectedFamily().equals(Optional.of(Family.NONE))) return List.of();
        return BattlePersonDiacNumericCodec.emit(leaf.numericInputs().orElseThrow());
    }
    public static List<Request> emitFromCurrentSourceInputs(JsonNode section) {
        require(section != null && section.isObject(), "current_context_source_inputs", "Required native input unavailable: following_diac_2920d60"); JsonNode raw = section.get("following_diac_2920d60");
        Following leaf = decode(raw == null ? NullNode.instance : raw, "following_diac_2920d60").orElseThrow(() -> bad("following_diac_2920d60", "Required native input unavailable"));
        require(leaf.characterId() == requiredInt(section.get("character_id"), "current_context_source_inputs.character_id", 32, false), "following_diac_2920d60", "character differs from source actor"); return emit(leaf);
    }
    public sealed interface UnknownOccurrence permits UnknownRoot, UnknownNode { ObjectNode toJson(); }
    public record UnknownRoot(Optional<String> reason, Optional<BigInteger> loadedValidator) implements UnknownOccurrence {
        @Override public ObjectNode toJson() { ObjectNode row = object().put("path", "root"); putText(row, "reason", reason); putNumber(row, "loaded_validator_rva", loadedValidator); return row; }
    }
    public record UnknownNode(Node node) implements UnknownOccurrence {
        @Override public ObjectNode toJson() { ObjectNode row = object().put("path", node.path()); putText(row, "identity", node.identity()); putText(row, "reason", node.reason()); putNumber(row, "slot58_rva", node.slot58()); putNumber(row, "slot60_rva", node.slot60()); putNumber(row, "slotc8_rva", node.slotC8()); putInt(row, "children_count_raw", node.childrenCount()); putInt(row, "reference_arguments_count_raw", node.referenceArgumentsCount()); return row; }
    }
    public static Optional<UnknownOccurrence> firstUnknownNode(Admission rule) {
        if (rule.result() != Verdict.UNKNOWN) return Optional.empty(); if (rule.nodes().isEmpty()) return Optional.of(new UnknownRoot(rule.reason(), rule.loadedValidatorRva())); Node node = rule.nodes().getFirst(); while (!node.children().isEmpty() && node.children().getLast().result() == Verdict.UNKNOWN) node = node.children().getLast(); return Optional.of(new UnknownNode(node));
    }
    private static void verdict(Verdict actual, Verdict calculated, Optional<String> reason, String field) { require(actual == calculated && (actual != Verdict.UNKNOWN) == reason.isEmpty(), field, "bounded verdict/reason disagrees with demanded raw inputs"); }
}
