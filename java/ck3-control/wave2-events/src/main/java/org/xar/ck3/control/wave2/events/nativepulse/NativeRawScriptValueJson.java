package org.xar.ck3.control.wave2.events.nativepulse;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeRawScriptValue.*;

/** One exact original-input contract. All native qwords and raw signed64 values use decimal strings. */
public final class NativeRawScriptValueJson {
    public static final String SCHEMA = "xar.native-raw-script-value-original/v1";
    public static final int MAX_BYTES = 524288;
    private NativeRawScriptValueJson() { }

    public static byte[] encode(Input input) {
        ObjectNode root = StrictJson.object().put("schema", SCHEMA).put("purpose", "STATIC_ORIGINAL_RECONSTRUCTION")
            .put("exe_sha256", NativePlayableAnnualGate.EXECUTABLE_SHA256);
        root.set("original_observation", input.originalObservation().toJson()); root.set("original_ast_source", input.originalAstSource().toJson());
        root.set("value", pdx(input.value())); root.set("context", context(input.context())); optionalRandom(root, "original_random", input.originalRandom());
        ArrayNode rawCalls = root.putArray("original_raw_calls");
        for (OriginalRawCall call : input.originalRawCalls()) {
            ObjectNode row = rawCalls.addObject().put("output_raw", Long.toString(call.outputRaw()));
            row.set("leaf", leaf(call.leaf())); row.set("before", context(call.before()));
            optionalRandom(row, "random_before", call.randomBefore()); optionalRandom(row, "random_after", call.randomAfter());
            row.set("original_observation", call.originalObservation().toJson());
        }
        ArrayNode scopeCalls = root.putArray("original_scope_calls");
        for (OriginalScopeCall call : input.originalScopeCalls()) {
            ObjectNode row = scopeCalls.addObject(); row.set("leaf", leaf(call.leaf())); row.set("before", context(call.before()));
            row.set("output", scope(call.output())); row.set("original_observation", call.originalObservation().toJson());
        }
        return StrictJson.canonical(root, MAX_BYTES);
    }
    public static Input decode(byte[] bytes) {
        ObjectNode root = exact(StrictJson.parse(bytes, MAX_BYTES), "schema", "purpose", "exe_sha256", "original_observation", "original_ast_source",
            "value", "context", "original_random", "original_raw_calls", "original_scope_calls");
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))) && "STATIC_ORIGINAL_RECONSTRUCTION".equals(StrictJson.text(root.get("purpose"))), "exact original reconstruction schema required");
        var executable = NativePlayableAnnualGate.Executable.exact(StrictJson.text(root.get("exe_sha256")))
            .orElseThrow(() -> new IllegalArgumentException("exact source-reviewed executable required"));
        List<OriginalRawCall> rawCalls = new ArrayList<>();
        for (JsonNode raw : array(root.get("original_raw_calls"), 1024)) {
            ObjectNode row = exact(raw, "leaf", "before", "random_before", "random_after", "output_raw", "original_observation");
            rawCalls.add(new OriginalRawCall(leaf(row.get("leaf")), context(row.get("before")), optionalRandom(row.get("random_before")),
                optionalRandom(row.get("random_after")), signed(row.get("output_raw")), ExactRef.fromJson(row.get("original_observation"))));
        }
        List<OriginalScopeCall> scopeCalls = new ArrayList<>();
        for (JsonNode raw : array(root.get("original_scope_calls"), 1024)) {
            ObjectNode row = exact(raw, "leaf", "before", "output", "original_observation");
            scopeCalls.add(new OriginalScopeCall(leaf(row.get("leaf")), context(row.get("before")), scope(row.get("output")), ExactRef.fromJson(row.get("original_observation"))));
        }
        return new Input(executable, ExactRef.fromJson(root.get("original_observation")), ExactRef.fromJson(root.get("original_ast_source")),
            pdx(root.get("value")), context(root.get("context")), optionalRandom(root.get("original_random")), rawCalls, scopeCalls);
    }
    /** Recomputed output, never parsed as a qualification or trusted as a stored success flag. */
    public static byte[] encode(Result result) {
        ObjectNode root = StrictJson.object().put("schema", "xar.native-raw-script-value-derived/v1")
            .put("status", result.status().name()).put("branch", result.branch().name()).put("raw_calls_consumed", result.rawCallsConsumed())
            .put("scope_calls_consumed", result.scopeCallsConsumed()).put("diagnosis", result.diagnosis())
            .put("complete_native_ast", result.completeNativeAst()).put("current_loaded_source_qualified", result.currentLoadedSourceQualified())
            .put("native_game_executed", result.nativeGameExecuted());
        if (result.raw().isEmpty()) root.putNull("raw"); else root.put("raw", Long.toString(result.raw().orElseThrow()));
        optionalRandom(root, "after_random", result.afterRandom());
        ArrayNode trace = root.putArray("trace");
        for (Trace entry : result.trace()) {
            ObjectNode row = trace.addObject().put("kind", entry.kind().name()).put("ordinal", entry.ordinal());
            if (entry.leaf().isEmpty()) row.putNull("leaf"); else row.set("leaf", leaf(entry.leaf().orElseThrow()));
        }
        return StrictJson.canonical(root, MAX_BYTES);
    }
    private static ObjectNode pdx(Pdx value) {
        ObjectNode row = StrictJson.object().put("native_kind_c0", value.nativeKindC0()).put("stored_raw_98", Long.toString(value.storedRaw98()))
            .put("upper_raw_a0", Long.toString(value.upperRawA0()));
        optionalScript(row, "lower_a8", value.lowerA8()); optionalScript(row, "upper_b0", value.upperB0());
        if (value.overrideB8().isEmpty()) row.putNull("override_b8"); else row.set("override_b8", leaf(value.overrideB8().orElseThrow()));
        ArrayNode chain = row.putArray("scope_chain_08");
        for (ScopeStep step : value.scopeChain08()) {
            ObjectNode out = chain.addObject(); out.set("leaf", leaf(step.leaf()));
            out.putObject("original_accepted_types").put("first_u64", step.originalAcceptedTypes().firstU64().toString())
                .put("second_u64", step.originalAcceptedTypes().secondU64().toString());
        }
        return row;
    }
    private static Pdx pdx(JsonNode raw) {
        ObjectNode row = exact(raw, "native_kind_c0", "stored_raw_98", "upper_raw_a0", "lower_a8", "upper_b0", "override_b8", "scope_chain_08");
        List<ScopeStep> chain = new ArrayList<>();
        for (JsonNode element : array(row.get("scope_chain_08"), 512)) {
            ObjectNode step = exact(element, "leaf", "original_accepted_types"); ObjectNode mask = exact(step.get("original_accepted_types"), "first_u64", "second_u64");
            chain.add(new ScopeStep(leaf(step.get("leaf")), new ScopeMask(unsigned(mask.get("first_u64")), unsigned(mask.get("second_u64")))));
        }
        return new Pdx(integer(row.get("native_kind_c0"), 0, Integer.MAX_VALUE), signed(row.get("stored_raw_98")), signed(row.get("upper_raw_a0")),
            optionalScript(row.get("lower_a8")), optionalScript(row.get("upper_b0")), row.get("override_b8").isNull() ? Optional.empty() : Optional.of(leaf(row.get("override_b8"))), chain);
    }
    private static ObjectNode script(ScriptValue value) {
        ObjectNode row = StrictJson.object().put("stored_raw_68", Long.toString(value.storedRaw68())).put("raw_ready_7b", value.rawReady7B());
        if (value.dynamic70().isEmpty()) row.putNull("dynamic_70"); else row.set("dynamic_70", leaf(value.dynamic70().orElseThrow())); return row;
    }
    private static ScriptValue script(JsonNode raw) {
        ObjectNode row = exact(raw, "stored_raw_68", "raw_ready_7b", "dynamic_70");
        return new ScriptValue(signed(row.get("stored_raw_68")), bool(row.get("raw_ready_7b")),
            row.get("dynamic_70").isNull() ? Optional.empty() : Optional.of(leaf(row.get("dynamic_70"))));
    }
    private static void optionalScript(ObjectNode row, String field, Optional<ScriptValue> value) {
        if (value.isEmpty()) row.putNull(field); else row.set(field, script(value.orElseThrow()));
    }
    private static Optional<ScriptValue> optionalScript(JsonNode raw) { return raw.isNull() ? Optional.empty() : Optional.of(script(raw)); }
    private static ObjectNode leaf(Leaf leaf) { return StrictJson.object().put("object_address_u64", leaf.objectAddressU64().toString()).put("virtual_target_rva_u64", leaf.virtualTargetRvaU64().toString()); }
    private static Leaf leaf(JsonNode raw) { ObjectNode row = exact(raw, "object_address_u64", "virtual_target_rva_u64"); return new Leaf(unsigned(row.get("object_address_u64")), unsigned(row.get("virtual_target_rva_u64"))); }
    private static ObjectNode scope(Scope value) { return StrictJson.object().put("metadata_u64", value.metadataU64().toString()).put("payload_u64", value.payloadU64().toString()); }
    private static Scope scope(JsonNode raw) { ObjectNode row = exact(raw, "metadata_u64", "payload_u64"); return new Scope(unsigned(row.get("metadata_u64")), unsigned(row.get("payload_u64"))); }
    private static ObjectNode context(Context value) { ObjectNode row = StrictJson.object().put("word_08_u64", value.word08U64().toString()).put("word_10_u64", value.word10U64().toString())
        .put("word_18_u64", value.word18U64().toString()).put("mode_u8", value.modeU8()); row.set("current", scope(value.current())); return row; }
    private static Context context(JsonNode raw) { ObjectNode row = exact(raw, "current", "word_08_u64", "word_10_u64", "word_18_u64", "mode_u8");
        return new Context(scope(row.get("current")), unsigned(row.get("word_08_u64")), unsigned(row.get("word_10_u64")), unsigned(row.get("word_18_u64")), integer(row.get("mode_u8"), 0, 255)); }
    private static void optionalRandom(ObjectNode row, String field, Optional<Random> value) {
        if (value.isEmpty()) row.putNull(field); else { Random random = value.orElseThrow(); row.putObject(field).put("counter_u32", Long.toString(random.counterU32())).put("seed_u32", Long.toString(random.seedU32())); }
    }
    private static Optional<Random> optionalRandom(JsonNode raw) {
        if (raw.isNull()) return Optional.empty(); ObjectNode row = exact(raw, "counter_u32", "seed_u32");
        return Optional.of(new Random(unsigned32(row.get("counter_u32")), unsigned32(row.get("seed_u32"))));
    }
    /** Shared typed context boundary for concrete math-node consumers; JSON fields remain owned here. */
    public static ObjectNode encodeContext(Context value) { return context(value); }
    public static Context decodeContext(JsonNode raw) { return context(raw); }
    public static JsonNode encodeOptionalRandom(Optional<Random> value) {
        ObjectNode holder = StrictJson.object(); optionalRandom(holder, "value", value); return holder.get("value");
    }
    public static Optional<Random> decodeOptionalRandom(JsonNode raw) { return optionalRandom(raw); }
    private static ObjectNode exact(JsonNode raw, String... fields) { return StrictJson.object(raw, Set.of(fields)); }
    private static ArrayNode array(JsonNode raw, int cap) { StrictJson.require(raw instanceof ArrayNode && raw.size() <= cap, "bounded explicit array required"); return (ArrayNode) raw; }
    private static int integer(JsonNode raw, int minimum, int maximum) { return (int) StrictJson.integer(raw, minimum, maximum); }
    private static boolean bool(JsonNode raw) { StrictJson.require(raw != null && raw.isBoolean(), "actual JSON boolean required"); return raw.booleanValue(); }
    private static long signed(JsonNode raw) { String text = StrictJson.text(raw); long result = Long.parseLong(text); StrictJson.require(Long.toString(result).equals(text), "canonical signed64 decimal string required"); return result; }
    private static BigInteger unsigned(JsonNode raw) { String text = StrictJson.text(raw); BigInteger result = new BigInteger(text); NativeRawScriptValue.u64(result);
        StrictJson.require(result.toString().equals(text), "canonical unsigned64 decimal string required"); return result; }
    private static long unsigned32(JsonNode raw) { BigInteger result = unsigned(raw); StrictJson.require(result.bitLength() <= 32, "unsigned32 required"); return result.longValue(); }
}
