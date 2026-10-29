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
import static org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionFields.*;
import org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionNameIndex.Name;

/** Single exact persisted contract for the four native fields' original inputs and derived consumers. */
public final class NativeOnActionFieldsJson {
    public static final String SCHEMA = "xar.native-on-action-four-field-original/v1";
    public static final int MAX_BYTES = 1_048_576;
    private NativeOnActionFieldsJson() { }
    public static byte[] encode(Input input) {
        ObjectNode out = StrictJson.object().put("schema", SCHEMA).put("exe_sha256", NativePlayableAnnualGate.EXECUTABLE_SHA256);
        out.set("original_observation", input.originalObservation().toJson());
        out.set("event_original_random", random(input.eventOriginalRandom()));
        out.set("action_original_random", random(input.actionOriginalRandom()));
        out.put("event_scope_before_0258_u16", input.eventScopeBefore0258U16());
        ObjectNode table = out.putObject("action_name_index"); ArrayNode entries = table.putArray("definitions"), hashes = table.putArray("parallel_hashes_u32");
        for (NativeOnActionNameIndex.Entry entry : input.actions().definitions()) entries.addObject().put("name", entry.name().text())
            .put("address_u64", entry.address().toString()).put("native_hash_u32", Long.toString(entry.nativeHashU32()));
        for (long hash : input.actions().parallelHashes()) hashes.add(Long.toString(hash));
        ArrayNode blocks = out.putArray("original_blocks");
        for (Block block : input.originalBlocks()) {
            ObjectNode row = blocks.addObject().put("field", block.field().name()); row.set("original_source_piece", block.originalSourcePiece().toJson());
            ArrayNode tokens = row.putArray("tokens");
            for (Token token : block.tokens()) {
                ObjectNode value = tokens.addObject();
                if (token instanceof DelayDirective directive) {
                    value.put("kind", "DELAY").put("unit_token", directive.nativeUnitToken()); value.set("update", update(directive.update()));
                } else if (token instanceof EventReference event) {
                    value.put("kind", "EVENT").put("name", event.requestedName().text());
                    if (event.originalLookup().isEmpty()) value.putNull("original_lookup");
                    else value.set("original_lookup", target(event.originalLookup().orElseThrow()));
                } else value.put("kind", "ACTION").put("name", ((ActionReference) token).requestedName().text());
            }
        }
        ArrayNode predicates = out.putArray("original_predicates");
        for (Predicate predicate : input.originalPredicates()) predicates.addObject().put("field", predicate.field().name()).put("row_index", predicate.rowIndex())
            .put("address_u64", predicate.address().toString()).put("eligible", predicate.eligible());
        return StrictJson.canonical(out, MAX_BYTES);
    }
    public static Input decode(byte[] raw) {
        ObjectNode root = exact(StrictJson.parse(raw, MAX_BYTES), "schema", "exe_sha256", "original_observation", "event_original_random", "action_original_random",
            "event_scope_before_0258_u16", "action_name_index", "original_blocks", "original_predicates");
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))), "exact four-field original schema required");
        String executableSha256 = StrictJson.text(root.get("exe_sha256"));
        StrictJson.require(executableSha256.matches("[0-9a-f]{64}"), "canonical executable SHA-256 required");
        var executable = NativePlayableAnnualGate.Executable.exact(executableSha256)
            .orElseThrow(() -> new IllegalArgumentException("source-reviewed executable required"));
        ObjectNode table = exact(root.get("action_name_index"), "definitions", "parallel_hashes_u32");
        List<NativeOnActionNameIndex.Entry> definitions = new ArrayList<>(); List<Long> hashes = new ArrayList<>();
        for (JsonNode rawEntry : array(table.get("definitions"), 8192)) {
            ObjectNode entry = exact(rawEntry, "name", "address_u64", "native_hash_u32");
            definitions.add(new NativeOnActionNameIndex.Entry(name(entry.get("name")), pointer(entry.get("address_u64")), decimalU32(entry.get("native_hash_u32"))));
        }
        for (JsonNode hash : array(table.get("parallel_hashes_u32"), 8192)) hashes.add(decimalU32(hash));
        List<Block> blocks = new ArrayList<>();
        for (JsonNode rawBlock : array(root.get("original_blocks"), 1024)) {
            ObjectNode block = exact(rawBlock, "field", "original_source_piece", "tokens"); List<Token> tokens = new ArrayList<>();
            for (JsonNode rawToken : array(block.get("tokens"), 8192)) {
                StrictJson.require(rawToken != null && rawToken.isObject(), "token object required"); String kind = StrictJson.text(rawToken.get("kind"));
                switch (kind) {
                    case "DELAY" -> { ObjectNode token = exact(rawToken, "kind", "unit_token", "update"); tokens.add(new DelayDirective(integer(token.get("unit_token")), update(token.get("update")))); }
                    case "EVENT" -> { ObjectNode token = exact(rawToken, "kind", "name", "original_lookup"); JsonNode lookup = token.get("original_lookup");
                        tokens.add(new EventReference(name(token.get("name")), lookup.isNull() ? Optional.empty() : Optional.of(target(lookup)))); }
                    case "ACTION" -> tokens.add(new ActionReference(name(exact(rawToken, "kind", "name").get("name"))));
                    default -> throw new IllegalArgumentException("unknown original native reader token");
                }
            }
            blocks.add(new Block(field(block.get("field")), ExactRef.fromJson(block.get("original_source_piece")), tokens));
        }
        List<Predicate> predicates = new ArrayList<>();
        for (JsonNode rawPredicate : array(root.get("original_predicates"), 32768)) {
            ObjectNode predicate = exact(rawPredicate, "field", "row_index", "address_u64", "eligible");
            predicates.add(new Predicate(field(predicate.get("field")), integer(predicate.get("row_index")), pointer(predicate.get("address_u64")), bool(predicate.get("eligible"))));
        }
        return new Input(executable, ExactRef.fromJson(root.get("original_observation")), blocks,
            new NativeOnActionNameIndex.Table(executable, definitions, hashes), integer(root.get("event_scope_before_0258_u16")), predicates,
            random(root.get("event_original_random")), random(root.get("action_original_random")));
    }
    /** Canonical derived output is recomputed from original bytes during replay; no stored success flag is trusted. */
    public static byte[] encode(Projection projection) {
        ObjectNode root = StrictJson.object().put("schema", "xar.native-on-action-four-field-derived/v1")
            .put("status", projection.status().name()).put("event_scope_u16", projection.postloaded().eventScopeU16())
            .put("complete_native_dispatcher", projection.completeNativeDispatcher()).put("current_loaded_source_qualified", projection.currentLoadedSourceQualified())
            .put("native_game_executed", projection.nativeGameExecuted()).put("unresolved_row", projection.unresolvedRow());
        if (projection.unresolvedField().isEmpty()) root.putNull("unresolved_field"); else root.put("unresolved_field", projection.unresolvedField().orElseThrow().name());
        root.set("after_event_random", random(projection.afterEventRandom())); root.set("after_action_random", random(projection.afterActionRandom()));
        ArrayNode fields = root.putArray("fields");
        for (FieldRows field : projection.postloaded().definition().fields()) {
            ObjectNode out = fields.addObject().put("field", field.field().name()); ArrayNode rows = out.putArray("rows");
            for (Row row : field.rows()) {
                ObjectNode value = rows.addObject().put("name", row.name().text()); value.set("delay", delay(row.delay()));
                if (row instanceof EventRow event) { value.put("kind", "EVENT"); value.set("target", target(event.target())); }
                else { value.put("kind", "ACTION"); Optional<BigInteger> address = ((ActionRow) row).resolvedAddress();
                    if (address.isEmpty()) value.putNull("resolved_address_u64"); else value.put("resolved_address_u64", address.orElseThrow().toString()); }
            }
        }
        ArrayNode diagnostics = root.putArray("diagnostics");
        for (Diagnostic diagnostic : projection.postloaded().definition().diagnostics()) diagnostics.addObject().put("field", diagnostic.field().name())
            .put("block", diagnostic.block()).put("token_or_row", diagnostic.token()).put("code", diagnostic.code().name());
        ArrayNode emissions = root.putArray("emissions");
        for (Emission emission : projection.emissions()) emissions.addObject().put("field", emission.field().name()).put("row_index", emission.rowIndex())
            .put("address_u64", emission.address().toString()).put("delay_days", emission.delayDays());
        return StrictJson.canonical(root, MAX_BYTES);
    }
    private static ObjectNode update(DelayUpdate update) {
        ObjectNode out = StrictJson.object();
        if (update instanceof Scalar scalar) { out.put("kind", "SCALAR"); out.set("value", write(scalar.value())); }
        else { Range range = (Range) update; out.put("kind", "RANGE"); out.set("minimum", write(range.minimum())); out.set("maximum", write(range.maximum())); }
        return out;
    }
    private static DelayUpdate update(JsonNode raw) {
        StrictJson.require(raw != null && raw.isObject(), "delay update required"); String kind = StrictJson.text(raw.get("kind"));
        if (kind.equals("SCALAR")) return new Scalar(write(exact(raw, "kind", "value").get("value")));
        StrictJson.require(kind.equals("RANGE"), "explicit delay update kind required"); ObjectNode row = exact(raw, "kind", "minimum", "maximum");
        return new Range(write(row.get("minimum")), write(row.get("maximum")));
    }
    private static ObjectNode write(Write write) {
        ObjectNode out = StrictJson.object();
        if (write instanceof LiteralWrite literal) out.put("kind", "LITERAL").put("value", literal.value());
        else if (write instanceof CompiledWrite compiled) { out.put("kind", "COMPILED"); out.set("value", compiled(compiled.value())); }
        else out.put("kind", "NO_WRITE").put("diagnosis", ((NoWrite) write).diagnosis());
        return out;
    }
    private static Write write(JsonNode raw) {
        StrictJson.require(raw != null && raw.isObject(), "original delay write required"); String kind = StrictJson.text(raw.get("kind"));
        return switch (kind) {
            case "LITERAL" -> new LiteralWrite(integer(exact(raw, "kind", "value").get("value")));
            case "COMPILED" -> new CompiledWrite(compiled(exact(raw, "kind", "value").get("value")));
            case "NO_WRITE" -> new NoWrite(StrictJson.text(exact(raw, "kind", "diagnosis").get("diagnosis")));
            default -> throw new IllegalArgumentException("unknown original native delay write");
        };
    }
    private static ObjectNode compiled(CompiledValue value) { return StrictJson.object().put("address_u64", value.address().toString())
        .put("integer_ready", value.integerReady()).put("integer_value", value.integerValue()); }
    private static CompiledValue compiled(JsonNode raw) { ObjectNode row = exact(raw, "address_u64", "integer_ready", "integer_value");
        return new CompiledValue(pointer(row.get("address_u64")), bool(row.get("integer_ready")), integer(row.get("integer_value"))); }
    private static ObjectNode delay(Delay value) { ObjectNode out = StrictJson.object().put("unit_days", value.unitDays()).put("minimum_literal", value.minimumLiteral()).put("maximum_literal", value.maximumLiteral());
        if (value.minimumCompiled().isEmpty()) out.putNull("minimum_compiled"); else out.set("minimum_compiled", compiled(value.minimumCompiled().orElseThrow()));
        if (value.maximumCompiled().isEmpty()) out.putNull("maximum_compiled"); else out.set("maximum_compiled", compiled(value.maximumCompiled().orElseThrow())); return out; }
    private static ObjectNode target(EventTarget target) { return StrictJson.object().put("address_u64", target.address().toString()).put("signature", target.signature()).put("root_scope_u16", target.rootScopeU16()); }
    private static EventTarget target(JsonNode raw) { ObjectNode row = exact(raw, "address_u64", "signature", "root_scope_u16");
        return new EventTarget(pointer(row.get("address_u64")), integer(row.get("signature")), integer(row.get("root_scope_u16"))); }
    private static ObjectNode random(RandomState value) { return StrictJson.object().put("counter_u32", Long.toString(value.counterU32())).put("seed_u32", Long.toString(value.seedU32())); }
    private static RandomState random(JsonNode raw) { ObjectNode row = exact(raw, "counter_u32", "seed_u32"); return new RandomState(decimalU32(row.get("counter_u32")), decimalU32(row.get("seed_u32"))); }
    private static ObjectNode exact(JsonNode raw, String... keys) { return StrictJson.object(raw, Set.of(keys)); }
    private static ArrayNode array(JsonNode raw, int maximum) { StrictJson.require(raw instanceof ArrayNode && raw.size() <= maximum, "bounded explicit JSON array required"); return (ArrayNode) raw; }
    private static int integer(JsonNode raw) { return (int) StrictJson.integer(raw, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static boolean bool(JsonNode raw) { StrictJson.require(raw != null && raw.isBoolean(), "actual JSON boolean required"); return raw.booleanValue(); }
    private static Name name(JsonNode raw) { StrictJson.require(raw != null && raw.isTextual(), "exact name string required"); return new Name(raw.textValue()); }
    private static Field field(JsonNode raw) { return Field.valueOf(StrictJson.text(raw)); }
    private static BigInteger decimal(JsonNode raw, BigInteger maximum) { String text = StrictJson.text(raw); StrictJson.require(text.matches("0|[1-9][0-9]{0,19}"), "canonical unsigned decimal string required");
        BigInteger value = new BigInteger(text); StrictJson.require(value.compareTo(maximum) <= 0, "unsigned decimal outside original native domain"); return value; }
    private static BigInteger pointer(JsonNode raw) { BigInteger value = decimal(raw, StrictJson.UINT64_MAX); NativeOnActionNameIndex.pointer(value); return value; }
    private static long decimalU32(JsonNode raw) { return decimal(raw, BigInteger.valueOf(0xffffffffL)).longValueExact(); }
}
