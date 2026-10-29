package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.shape;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Full literal Diac numeric normalization and exact loaded quantization; no evaluator calls. */
public final class BattlePersonDiacNumericCodec {
    private BattlePersonDiacNumericCodec() { }
    private static final BigInteger SCALE = BigInteger.valueOf(100_000);
    public enum AvailabilityStatus { AVAILABLE, PARTIAL, UNAVAILABLE; public String wire() { return name().toLowerCase(java.util.Locale.ROOT); } }
    public record State(AvailabilityStatus status, boolean ready, Optional<String> reason) {
        public State { Objects.requireNonNull(status); Objects.requireNonNull(reason); require(ready == (status == AvailabilityStatus.AVAILABLE) && (ready ? reason.isEmpty() : reason.isPresent()), "availability", "status/ready/reason disagree"); }
        public ObjectNode toJson() { ObjectNode row = object().put("status", status.wire()).put("ready", ready); putText(row, "reason", reason); return row; }
    }
    public record Properties(Optional<Integer> keysCount, Optional<Integer> valuesCount, Optional<List<Integer>> keys, Optional<List<BigInteger>> values) {
        public Properties { Objects.requireNonNull(keysCount); Objects.requireNonNull(valuesCount); keys = keys.map(List::copyOf); values = values.map(List::copyOf); }
        public boolean ready() { return keysCount.isPresent() && keysCount.orElseThrow() >= 0 && keysCount.equals(valuesCount) && keys.isPresent() && values.isPresent() && keys.orElseThrow().size() == keysCount.orElseThrow() && values.orElseThrow().size() == keysCount.orElseThrow(); }
        public ObjectNode toJson() { ObjectNode row = object(); putInt(row, "keys_count", keysCount); putInt(row, "values_count", valuesCount); if (keys.isPresent()) { ArrayNode a = row.putArray("keys_u16"); keys.orElseThrow().forEach(a::add); } else row.putNull("keys_u16"); if (values.isPresent()) { ArrayNode a = row.putArray("values_q64"); values.orElseThrow().forEach(a::add); } else row.putNull("values_q64"); return row; }
    }
    public enum Mapper { STATIC_5451F40, PROVIDER_50_C8; public String wire() { return name().toLowerCase(java.util.Locale.ROOT); } }
    public record Metadata(int nativeIndex, int keyU16, Mapper selection, Optional<String> identity, Optional<Integer> byteBA, Optional<Integer> byteB8) {
        public Metadata { Objects.requireNonNull(selection); Objects.requireNonNull(identity); Objects.requireNonNull(byteBA); Objects.requireNonNull(byteB8); }
        public ObjectNode toJson() { ObjectNode row = object().put("native_index", nativeIndex).put("key_u16", keyU16).put("selection", selection.wire()); putText(row, "metadata_identity", identity); putInt(row, "byte_ba_raw", byteBA); putInt(row, "byte_b8_raw", byteB8); return row; }
    }
    public record Declaration(State state, int nativeIndex, Optional<String> identity, Optional<BigInteger> scaleGate,
            Optional<Properties> properties, Optional<Boolean> metadataProviderLoaded, List<Metadata> metadata) {
        public Declaration { Objects.requireNonNull(state); Objects.requireNonNull(identity); Objects.requireNonNull(scaleGate); Objects.requireNonNull(properties); Objects.requireNonNull(metadataProviderLoaded); metadata = List.copyOf(metadata); }
        public ObjectNode toJson() { ObjectNode row = state.toJson().put("native_index", nativeIndex); putText(row, "declaration_identity", identity); putNumber(row, "scale_gate_280_raw", scaleGate); putBool(row, "metadata_provider_loaded", metadataProviderLoaded); if (properties.isPresent()) row.set("properties", properties.orElseThrow().toJson()); else row.putNull("properties"); ArrayNode a = row.putArray("metadata_rows"); metadata.forEach(m -> a.add(m.toJson())); return row; }
    }
    public record Inputs(State state, Optional<Integer> scopeCharacterFullId, Optional<String> scopeIdAddressIdentity,
            Optional<String> definitionBlockIdentity, Optional<Integer> declarationCount, Optional<Boolean> declarationArrayPresent, List<Declaration> declarations) {
        public Inputs { Objects.requireNonNull(state); Objects.requireNonNull(scopeCharacterFullId); Objects.requireNonNull(scopeIdAddressIdentity); Objects.requireNonNull(definitionBlockIdentity); Objects.requireNonNull(declarationCount); Objects.requireNonNull(declarationArrayPresent); declarations = List.copyOf(declarations); }
        public ObjectNode toJson() { ObjectNode row = state.toJson(); putInt(row, "scope_character_full_id", scopeCharacterFullId); putText(row, "scope_id_address_identity", scopeIdAddressIdentity); putText(row, "definition_block_identity", definitionBlockIdentity); putInt(row, "declaration_count_raw", declarationCount); putBool(row, "declaration_array_present", declarationArrayPresent); ArrayNode a = row.putArray("declarations"); declarations.forEach(d -> a.add(d.toJson())); return row; }
    }
    public record PropertyBlock(int keysCount, int valuesCount, List<Integer> keysU16, List<BigInteger> valuesQ64) {
        public PropertyBlock { keysU16 = List.copyOf(keysU16); valuesQ64 = List.copyOf(valuesQ64); require(keysCount >= 0 && keysCount == valuesCount && keysCount == keysU16.size() && keysCount == valuesQ64.size(), "computed Diac property block", "exact physical counts required"); }
        public ObjectNode toJson() { ObjectNode row = object().put("keys_count", keysCount).put("values_count", valuesCount).putNull("reason"); ArrayNode keys = row.putArray("keys_u16"), values = row.putArray("values_q64"); keysU16.forEach(keys::add); valuesQ64.forEach(values::add); return row; }
    }
    /** Bounded concrete form of the original NativeWeightedContributionRequest12003. */
    public record Request(int sourceOrdinal, String sourceName, int firstRowIndex, int rowCount, String definitionIdentity, PropertyBlock basePropertyBlock, BigInteger weightQ64) {
        public Request { require(sourceOrdinal == 0 && "325b080_literal_declaration".equals(sourceName) && firstRowIndex >= 0 && rowCount == 1 && definitionIdentity != null && definitionIdentity.startsWith("derived:325b080:"), "Diac request", "actual loaded producer identity required"); Objects.requireNonNull(basePropertyBlock); require(SCALE.equals(weightQ64), "Diac request", "loaded literal weight must be Q100000"); }
        public ObjectNode toJson() { ObjectNode row = object().put("source_ordinal", sourceOrdinal).put("source_name", sourceName).put("first_row_index", firstRowIndex).put("row_count", rowCount).put("definition_identity", definitionIdentity).put("weight_q64", weightQ64); row.set("base_property_block", basePropertyBlock.toJson()); return row; }
    }

    public static ObjectNode normalize(JsonNode raw) { return decode(raw).toJson(); }
    public static Inputs decode(JsonNode raw) {
        String field = "diac_literal_numeric_inputs_12003";
        ObjectNode row = shape(raw, field, "status", "ready", "reason", "scope_character_full_id", "scope_id_address_identity", "definition_block_identity", "declaration_count_raw", "declaration_array_present", "declarations");
        State state = state(row, field); Optional<Integer> actor = intNumber(row.get("scope_character_full_id"), field + ".scope_character_full_id", 32, false);
        Optional<String> address = optionalText(row.get("scope_id_address_identity"), field + ".scope_id_address_identity"), block = optionalText(row.get("definition_block_identity"), field + ".definition_block_identity");
        Optional<Integer> count = intNumber(row.get("declaration_count_raw"), field + ".declaration_count_raw", 32, false); Optional<Boolean> present = optionalBool(row.get("declaration_array_present"), field + ".declaration_array_present");
        List<JsonNode> rows = ordered(row.get("declarations"), field + ".declarations"); List<Declaration> declarations = new ArrayList<>(); for (int i = 0; i < rows.size(); i++) declarations.add(declaration(rows.get(i), field + ".declarations[" + i + "]", i));
        boolean complete = actor.isPresent() && address.isPresent() && block.isPresent() && count.isPresent() && count.orElseThrow() >= 0 && present.isPresent() && (count.orElseThrow() == 0 || present.orElseThrow()) && declarations.size() == count.orElseThrow() && declarations.stream().allMatch(d -> d.state().ready()) && state.reason().isEmpty();
        require(state.ready() == complete, field, "whole literal producer readiness disagrees"); return new Inputs(state, actor, address, block, count, present, declarations);
    }
    private static Declaration declaration(JsonNode raw, String field, int index) {
        ObjectNode row = shape(raw, field, "status", "ready", "reason", "native_index", "declaration_identity", "scale_gate_280_raw", "properties", "metadata_provider_loaded", "metadata_rows");
        State state = state(row, field); int nativeIndex = requiredInt(row.get("native_index"), field + ".native_index", 32, false); require(nativeIndex == index, field, "physical declaration order invalid");
        Optional<String> identity = optionalText(row.get("declaration_identity"), field + ".declaration_identity"); Optional<BigInteger> gate = optionalNumber(row.get("scale_gate_280_raw"), field + ".scale_gate_280_raw", 32, true); Optional<Boolean> provider = optionalBool(row.get("metadata_provider_loaded"), field + ".metadata_provider_loaded");
        Optional<Properties> properties = properties(row.get("properties"), field + ".properties"); List<JsonNode> rows = ordered(row.get("metadata_rows"), field + ".metadata_rows"); List<Metadata> metadata = new ArrayList<>();
        Optional<List<Integer>> keys = properties.flatMap(Properties::keys);
        for (int i = 0; i < rows.size(); i++) {
            String name = field + ".metadata_rows[" + i + "]"; ObjectNode item = shape(rows.get(i), name, "native_index", "key_u16", "selection", "metadata_identity", "byte_ba_raw", "byte_b8_raw");
            int nativeRow = requiredInt(item.get("native_index"), name + ".native_index", 32, false), key = requiredInt(item.get("key_u16"), name + ".key_u16", 16, true);
            require(nativeRow == i && (keys.isEmpty() || i < keys.orElseThrow().size() && key == keys.orElseThrow().get(i)), name, "physical per-key metadata order disagrees");
            Optional<String> selected = optionalText(item.get("selection"), name + ".selection"); Mapper mapper = key == 65535 ? Mapper.STATIC_5451F40 : Mapper.PROVIDER_50_C8; require(selected.equals(Optional.of(mapper.wire())), name, "actual metadata mapper selection disagrees");
            Optional<String> metadataIdentity = optionalText(item.get("metadata_identity"), name + ".metadata_identity"); Optional<Integer> ba = intNumber(item.get("byte_ba_raw"), name + ".byte_ba_raw", 8, true), b8 = intNumber(item.get("byte_b8_raw"), name + ".byte_b8_raw", 8, true);
            require(ba.equals(Optional.of(0)) || b8.isEmpty(), name, "BA branch skips the B8 read"); metadata.add(new Metadata(nativeRow, key, mapper, metadataIdentity, ba, b8));
        }
        if (gate.isPresent() && gate.orElseThrow().signum() != 0) require(properties.isEmpty() && provider.isEmpty() && metadata.isEmpty() && state.reason().equals(Optional.of("dynamic_scale_9d7060")), field, "dynamic scale keeps PC/provider/metadata undemanded");
        require(provider.equals(Optional.of(true)) || metadata.isEmpty(), field, "unavailable metadata provider cannot publish flag reads");
        if (gate.equals(Optional.of(BigInteger.ZERO)) && provider.equals(Optional.of(false))) require(state.reason().equals(Optional.of("metadata_provider_c85860_unavailable")), field, "null actual metadata provider requires precise unavailable input");
        boolean complete = identity.isPresent() && gate.equals(Optional.of(BigInteger.ZERO)) && provider.equals(Optional.of(true)) && properties.isPresent() && properties.orElseThrow().ready() && metadata.size() == properties.orElseThrow().keysCount().orElseThrow()
                && metadata.stream().allMatch(m -> m.identity().isPresent() && m.byteBA().isPresent() && (m.byteBA().orElseThrow() != 0 || m.byteB8().isPresent())) && state.reason().isEmpty();
        require(state.ready() == complete, field, "literal declaration numeric readiness disagrees"); return new Declaration(state, nativeIndex, identity, gate, properties, provider, metadata);
    }
    private static Optional<Properties> properties(JsonNode raw, String field) {
        if (nil(raw)) return Optional.empty(); ObjectNode row = shape(raw, field, "keys_count", "values_count", "keys_u16", "values_q64");
        Optional<List<Integer>> keys = nil(row.get("keys_u16")) ? Optional.empty() : Optional.of(ordered(row.get("keys_u16"), field + ".keys_u16").stream().map(k -> requiredInt(k, field + ".keys_u16[]", 16, true)).toList());
        Optional<List<BigInteger>> values = nil(row.get("values_q64")) ? Optional.empty() : Optional.of(ordered(row.get("values_q64"), field + ".values_q64").stream().map(v -> number(v, field + ".values_q64[]", 64, false, false).bigIntegerValue()).toList());
        return Optional.of(new Properties(intNumber(row.get("keys_count"), field + ".keys_count", 32, false), intNumber(row.get("values_count"), field + ".values_count", 32, false), keys, values));
    }
    public static BigInteger quantize(BigInteger raw, int byteBA, Optional<Integer> byteB8) {
        Objects.requireNonNull(raw); Objects.requireNonNull(byteB8); require(byteBA >= 0 && byteBA <= 255 && byteB8.map(v -> v >= 0 && v <= 255).orElse(true), "Diac quantizer", "raw BYTE operands required");
        if (byteBA != 0) return raw; require(byteB8.isPresent(), "Diac quantizer", "BA zero demands B8"); if ((byteB8.orElseThrow() & 1) != 0) return raw;
        return BattlePersonLateWire.wrap(raw.divide(SCALE), 32).multiply(SCALE);
    }
    public static PropertyBlock computeRow(Declaration row) {
        require(row.state().ready(), "Diac literal numeric declaration", "Required native input unavailable"); Properties source = row.properties().orElseThrow(); List<BigInteger> values = new ArrayList<>();
        for (int i = 0; i < source.values().orElseThrow().size(); i++) { Metadata metadata = row.metadata().get(i); values.add(quantize(source.values().orElseThrow().get(i), metadata.byteBA().orElseThrow(), metadata.byteB8())); }
        return new PropertyBlock(source.keysCount().orElseThrow(), source.valuesCount().orElseThrow(), source.keys().orElseThrow(), values);
    }
    public static List<Request> emitRow(Inputs normalized, int index) {
        require(index >= 0 && index < normalized.declarations().size(), "Diac declaration index", "Required native input unavailable"); Declaration row = normalized.declarations().get(index);
        PropertyBlock block = computeRow(row);
        return List.of(new Request(0, "325b080_literal_declaration", row.nativeIndex(), 1, "derived:325b080:" + row.identity().orElseThrow(() -> bad("Diac declaration", "Required native input unavailable")), block, SCALE));
    }
    public static List<Request> emit(Inputs normalized) {
        require(normalized.state().ready(), "Diac literal numeric producer", "Required native input unavailable"); List<Request> result = new ArrayList<>(); for (int i = 0; i < normalized.declarations().size(); i++) result.addAll(emitRow(normalized, i)); return List.copyOf(result);
    }
    static State state(ObjectNode raw, String field) { BattleContextJson.Availability actual = availability(raw, field); return new State(AvailabilityStatus.valueOf(actual.status().name()), actual.ready(), Optional.ofNullable(actual.reason())); }
    static Optional<BigInteger> optionalNumber(JsonNode raw, String field, int bits, boolean unsigned) { JsonNode value = number(raw, field, bits, unsigned, true); return nil(value) ? Optional.empty() : Optional.of(value.bigIntegerValue()); }
    static Optional<Integer> intNumber(JsonNode raw, String field, int bits, boolean unsigned) { return optionalNumber(raw, field, bits, unsigned).map(BigInteger::intValueExact); }
    static int requiredInt(JsonNode raw, String field, int bits, boolean unsigned) { return number(raw, field, bits, unsigned, false).bigIntegerValue().intValueExact(); }
    static Optional<String> optionalText(JsonNode raw, String field) { JsonNode value = text(raw, field, true, true); return nil(value) ? Optional.empty() : Optional.of(value.textValue()); }
    static Optional<Boolean> optionalBool(JsonNode raw, String field) { JsonNode value = bool(raw, field, true); return nil(value) ? Optional.empty() : Optional.of(value.booleanValue()); }
    static List<JsonNode> ordered(JsonNode raw, String field) { require(raw instanceof ArrayNode, field, "ordered occurrence list required"); List<JsonNode> result = new ArrayList<>(); raw.forEach(result::add); return List.copyOf(result); }
    static void putText(ObjectNode row, String key, Optional<String> value) { if (value.isPresent()) row.put(key, value.orElseThrow()); else row.putNull(key); }
    static void putNumber(ObjectNode row, String key, Optional<BigInteger> value) { if (value.isPresent()) row.put(key, value.orElseThrow()); else row.putNull(key); }
    static void putInt(ObjectNode row, String key, Optional<Integer> value) { if (value.isPresent()) row.put(key, value.orElseThrow()); else row.putNull(key); }
    static void putBool(ObjectNode row, String key, Optional<Boolean> value) { if (value.isPresent()) row.put(key, value.orElseThrow()); else row.putNull(key); }
}
