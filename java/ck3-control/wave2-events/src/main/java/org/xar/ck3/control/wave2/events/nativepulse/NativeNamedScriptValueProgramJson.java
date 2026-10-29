package org.xar.ck3.control.wave2.events.nativepulse;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeNamedScriptValueProgram.*;

/** Nested Math/Raw inputs and outputs delegate their existing unique codecs. */
public final class NativeNamedScriptValueProgramJson {
    private NativeNamedScriptValueProgramJson() { }
    /** Separate observed-load schema; original v1 input/result bytes and legacy archives remain unchanged. */
    public static byte[] encode(ObservedLoad input) {
        ObjectNode row = StrictJson.object().put("schema", "xar.native-named-load-observed/v1");
        row.set("original", StrictJson.parse(encode(input.original()), NativeScriptMathProgramJson.MAX_BYTES));
        LoadObservation value = input.observation(); ObjectNode observation = row.putObject("observation")
            .put("math_object_u64", value.mathObjectU64().toString()).put("primary_vtable_rva", value.primaryVtableRva()).put("finalizer_slot_28_rva", value.finalizerSlot28Rva());
        observation.set("original_observation", value.originalObservation().toJson());
        var before = observation.putArray("nodes_before_u64"); value.nodesBefore().forEach(node -> before.add(node.toString()));
        var after = observation.putArray("nodes_after_u64"); value.nodesAfter().forEach(node -> after.add(node.toString()));
        return StrictJson.canonical(row, NativeScriptMathProgramJson.MAX_BYTES);
    }
    public static ObservedLoad decodeObserved(byte[] bytes) {
        ObjectNode row = StrictJson.object(StrictJson.parse(bytes, NativeScriptMathProgramJson.MAX_BYTES), Set.of("schema", "original", "observation"));
        StrictJson.require("xar.native-named-load-observed/v1".equals(StrictJson.text(row.get("schema"))), "exact observed-load schema required");
        ObjectNode value = StrictJson.object(row.get("observation"), Set.of("original_observation", "math_object_u64", "primary_vtable_rva", "finalizer_slot_28_rva", "nodes_before_u64", "nodes_after_u64"));
        return new ObservedLoad(decode(StrictJson.canonical(row.get("original"), NativeScriptMathProgramJson.MAX_BYTES)),
            new LoadObservation(ExactRef.fromJson(value.get("original_observation")), u64(value.get("math_object_u64")),
                StrictJson.integer(value.get("primary_vtable_rva"), 0, Integer.MAX_VALUE), StrictJson.integer(value.get("finalizer_slot_28_rva"), 0, Integer.MAX_VALUE),
                nodes(value.get("nodes_before_u64")), nodes(value.get("nodes_after_u64"))));
    }
    private static List<BigInteger> nodes(JsonNode value) {
        StrictJson.require(value.isArray() && value.size() <= 256, "explicit bounded original node addresses required");
        List<BigInteger> nodes = new ArrayList<>(); for (JsonNode node : value) nodes.add(u64(node)); return List.copyOf(nodes);
    }
    public static byte[] encode(Input input) {
        ObjectNode out = StrictJson.object().put("schema", "xar.native-named-kind3-original/v1").put("lexical_kind_1c8", input.originalLexicalKind1C8());
        out.set("original_load_source", input.originalLoadSource().toJson()); Before before = input.before();
        ObjectNode memory = out.putObject("before").put("definition_u64", before.definitionU64().toString()).put("primary_vtable_rva", before.primaryVtableRva())
            .put("secondary_vtable_rva", before.secondaryVtableRva()).put("stored_raw_68", Long.toString(before.storedRaw68())).put("raw_ready_7b", before.rawReady7B());
        if (before.dynamic70().isEmpty()) memory.putNull("dynamic_70_u64"); else memory.put("dynamic_70_u64", before.dynamic70().orElseThrow().toString());
        out.set("original_math", StrictJson.parse(NativeScriptMathProgramJson.encode(input.originalMath()), NativeScriptMathProgramJson.MAX_BYTES));
        if (input.originalRawConsumer().isEmpty()) out.putNull("original_raw_consumer"); else out.set("original_raw_consumer", StrictJson.parse(NativeRawScriptValueJson.encode(input.originalRawConsumer().orElseThrow()), NativeRawScriptValueJson.MAX_BYTES));
        return StrictJson.canonical(out, NativeScriptMathProgramJson.MAX_BYTES);
    }
    public static Input decode(byte[] bytes) {
        ObjectNode row = StrictJson.object(StrictJson.parse(bytes, NativeScriptMathProgramJson.MAX_BYTES), Set.of("schema", "lexical_kind_1c8", "original_load_source", "before", "original_math", "original_raw_consumer"));
        StrictJson.require("xar.native-named-kind3-original/v1".equals(StrictJson.text(row.get("schema"))), "exact named kind3 original schema required");
        ObjectNode memory = StrictJson.object(row.get("before"), Set.of("definition_u64", "primary_vtable_rva", "secondary_vtable_rva", "stored_raw_68", "raw_ready_7b", "dynamic_70_u64"));
        JsonNode old = memory.get("dynamic_70_u64"); JsonNode raw = row.get("original_raw_consumer");
        Before before = new Before(u64(memory.get("definition_u64")), StrictJson.integer(memory.get("primary_vtable_rva"), 0, Integer.MAX_VALUE),
            StrictJson.integer(memory.get("secondary_vtable_rva"), 0, Integer.MAX_VALUE), signed(memory.get("stored_raw_68")), bool(memory.get("raw_ready_7b")), old.isNull() ? Optional.empty() : Optional.of(u64(old)));
        return new Input(ExactRef.fromJson(row.get("original_load_source")), (int) StrictJson.integer(row.get("lexical_kind_1c8"), 0, Integer.MAX_VALUE), before,
            NativeScriptMathProgramJson.decode(StrictJson.canonical(row.get("original_math"), NativeScriptMathProgramJson.MAX_BYTES)),
            raw.isNull() ? Optional.empty() : Optional.of(NativeRawScriptValueJson.decode(StrictJson.canonical(raw, NativeRawScriptValueJson.MAX_BYTES))));
    }
    public static byte[] encode(Result result) {
        ObjectNode row = StrictJson.object().put("schema", "xar.native-named-kind3-derived/v1").put("status", result.status().name())
            .put("static_kind3_writer_route_reviewed", result.staticKindThreeWriterRouteReviewed()).put("complete_native_ast", result.completeNativeAst())
            .put("current_loaded_source_qualified", result.currentLoadedSourceQualified()).put("native_game_executed", result.nativeGameExecuted());
        row.set("math", StrictJson.parse(NativeScriptMathProgramJson.encode(result.math()), NativeScriptMathProgramJson.MAX_BYTES));
        if (result.raw().isEmpty()) row.putNull("raw"); else row.set("raw", StrictJson.parse(NativeRawScriptValueJson.encode(result.raw().orElseThrow()), NativeRawScriptValueJson.MAX_BYTES));
        return StrictJson.canonical(row, NativeScriptMathProgramJson.MAX_BYTES);
    }
    private static BigInteger u64(JsonNode value) { String text = StrictJson.text(value); BigInteger result = new BigInteger(text); NativeRawScriptValue.u64(result);
        StrictJson.require(result.toString().equals(text), "canonical u64 decimal string required"); return result; }
    private static long signed(JsonNode value) { String text = StrictJson.text(value); long result = Long.parseLong(text); StrictJson.require(Long.toString(result).equals(text), "canonical signed64 decimal string required"); return result; }
    private static boolean bool(JsonNode value) { StrictJson.require(value.isBoolean(), "actual JSON boolean required"); return value.booleanValue(); }
}
