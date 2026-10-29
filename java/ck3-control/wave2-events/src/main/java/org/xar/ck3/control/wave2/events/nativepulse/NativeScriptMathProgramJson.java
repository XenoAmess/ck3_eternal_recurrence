package org.xar.ck3.control.wave2.events.nativepulse;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeScriptMathProgram.*;

/** Exact original token producer and every nested operand use one persisted contract each. */
public final class NativeScriptMathProgramJson {
    public static final int MAX_BYTES = 1048576;
    public static final String SCHEMA = "xar.native-script-math-original/v1";
    private NativeScriptMathProgramJson() { }
    public static byte[] encodeFactoryReview(FactoryReview review) {
        ObjectNode row = StrictJson.object().put("schema", "xar.native-script-math-factory-review/v1")
            .put("purpose", "STATIC_SOURCE_RECONSTRUCTION").put("allocation_bytes", review.allocationBytes())
            .put("operand_offset", review.operandOffset()).put("opcode_offset", review.opcodeOffset())
            .put("node_vtable_rva", review.nodeVtableRva()).put("load_vtable_slot", review.loadVtableSlot())
            .put("current_loaded_ast_qualified", review.currentLoadedAstQualified()).put("operand_load_closed", review.operandLoadClosed());
        row.set("original", review.original().toJson()); return StrictJson.canonical(row, MAX_BYTES);
    }
    /** Recomputes from the exact original bytes; JSON alone never constructs a reviewed factory. */
    public static FactoryReview replayFactoryReview(byte[] encoded, ExactRef original, byte[] retainedRaw) {
        FactoryReview review = reviewFactory(original, retainedRaw);
        StrictJson.require(java.util.Arrays.equals(encodeFactoryReview(review), encoded), "factory projection differs from exact original recomputation");
        return review;
    }
    public static byte[] encode(Input input) {
        ObjectNode out = StrictJson.object().put("schema", SCHEMA).put("purpose", "STATIC_SOURCE_RECONSTRUCTION")
            .put("exe_sha256", NativePlayableAnnualGate.EXECUTABLE_SHA256);
        out.set("original_observation", input.originalObservation().toJson());
        out.putObject("root").put("object_u64", input.root().originalObjectU64().toString()).put("primary_vtable_rva", input.root().primaryVtableRva())
            .put("base_vtable_rva", input.root().baseVtableRva()).put("entry", input.root().entry().name());
        // The original RawInput codec remains the sole owner of context/RNG/operand JSON fields.
        out.set("original_context", NativeRawScriptValueJson.encodeContext(input.originalContext()));
        out.set("original_random", NativeRawScriptValueJson.encodeOptionalRandom(input.originalRandom()));
        ArrayNode fields = out.putArray("original_fields");
        for (Field field : input.originalFields()) {
            ObjectNode row = fields.addObject().put("native_token", field.nativeToken()); row.set("original_source", field.originalSource().toJson());
            if (field instanceof SimpleField simple) { row.put("kind", "SIMPLE"); row.set("original_operand", StrictJson.parse(NativeRawScriptValueJson.encode(simple.originalOperand()), NativeRawScriptValueJson.MAX_BYTES)); }
            else row.put("kind", "UNREVIEWED").put("diagnosis", ((UnreviewedField) field).diagnosis());
        }
        return StrictJson.canonical(out, MAX_BYTES);
    }
    public static Input decode(byte[] bytes) {
        ObjectNode row = exact(StrictJson.parse(bytes, MAX_BYTES), "schema", "purpose", "exe_sha256", "original_observation", "root", "original_context", "original_random", "original_fields");
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))) && "STATIC_SOURCE_RECONSTRUCTION".equals(StrictJson.text(row.get("purpose"))), "exact math original source schema required");
        var executable = NativePlayableAnnualGate.Executable.exact(StrictJson.text(row.get("exe_sha256"))).orElseThrow(() -> new IllegalArgumentException("exact reviewed executable required"));
        ObjectNode binding = exact(row.get("root"), "object_u64", "primary_vtable_rva", "base_vtable_rva", "entry");
        Root root = new Root(u64(binding.get("object_u64")), StrictJson.integer(binding.get("primary_vtable_rva"), 0, Integer.MAX_VALUE),
            StrictJson.integer(binding.get("base_vtable_rva"), 0, Integer.MAX_VALUE), Entry.valueOf(StrictJson.text(binding.get("entry"))));
        List<Field> fields = new ArrayList<>();
        for (JsonNode raw : array(row.get("original_fields"), 256)) {
            StrictJson.require(raw.isObject(), "explicit original field object required"); String kind = StrictJson.text(raw.get("kind"));
            if (kind.equals("SIMPLE")) { ObjectNode field = exact(raw, "kind", "native_token", "original_source", "original_operand");
                fields.add(new SimpleField(integer(field.get("native_token")), ExactRef.fromJson(field.get("original_source")),
                    NativeRawScriptValueJson.decode(StrictJson.canonical(field.get("original_operand"), NativeRawScriptValueJson.MAX_BYTES)))); }
            else { StrictJson.require(kind.equals("UNREVIEWED"), "explicit known field branch required"); ObjectNode field = exact(raw, "kind", "native_token", "original_source", "diagnosis");
                fields.add(new UnreviewedField(integer(field.get("native_token")), ExactRef.fromJson(field.get("original_source")), StrictJson.text(field.get("diagnosis")))); }
        }
        return new Input(executable, ExactRef.fromJson(row.get("original_observation")), root,
            NativeRawScriptValueJson.decodeContext(row.get("original_context")), NativeRawScriptValueJson.decodeOptionalRandom(row.get("original_random")), fields);
    }
    /** Output is only recomputation material; it is never deserialized as native execution qualification. */
    public static byte[] encode(Result result) {
        ObjectNode out = StrictJson.object().put("schema", "xar.native-script-math-derived/v1").put("status", result.status().name())
            .put("reconstructed_prefix_raw", Long.toString(result.reconstructedPrefixRaw())).put("blocked_original_index", result.blockedOriginalIndex()).put("diagnosis", result.diagnosis())
            .put("complete_native_ast", result.completeNativeAst()).put("original_named_70_writer_closed", result.originalNamed70WriterClosed())
            .put("current_loaded_source_qualified", result.currentLoadedSourceQualified()).put("native_game_executed", result.nativeGameExecuted());
        out.set("after_random", NativeRawScriptValueJson.encodeOptionalRandom(result.afterRandom())); ArrayNode applied = out.putArray("applied");
        for (Applied step : result.applied()) {
            ObjectNode row = applied.addObject().put("original_index", step.originalIndex()).put("operator", step.operator().name()).put("native_opcode", step.operator().nativeOpcode())
                .put("before_raw", Long.toString(step.beforeRaw())).put("operand_raw", Long.toString(step.operandRaw())).put("after_raw", Long.toString(step.afterRaw()));
            if (step.diagnostic().isEmpty()) row.putNull("diagnostic"); else row.put("diagnostic", step.diagnostic().orElseThrow().name());
            row.set("original_operand_result", StrictJson.parse(NativeRawScriptValueJson.encode(step.originalOperandResult()), NativeRawScriptValueJson.MAX_BYTES));
        }
        return StrictJson.canonical(out, MAX_BYTES);
    }
    private static BigInteger u64(JsonNode raw) { String text = StrictJson.text(raw); BigInteger value = new BigInteger(text); NativeRawScriptValue.u64(value);
        StrictJson.require(value.toString().equals(text), "canonical unsigned64 decimal required"); return value; }
    private static int integer(JsonNode raw) { return (int) StrictJson.integer(raw, 0, Integer.MAX_VALUE); }
    private static ObjectNode exact(JsonNode raw, String... keys) { return StrictJson.object(raw, Set.of(keys)); }
    private static ArrayNode array(JsonNode raw, int cap) { StrictJson.require(raw instanceof ArrayNode && raw.size() <= cap, "bounded explicit original array required"); return (ArrayNode) raw; }
}
