package org.xar.ck3.control.wave3.development.constructionquery;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructionmode3.ConstructionMode3;
import org.xar.ck3.control.wave2.development.constructionmode3.ConstructionMode3Codec;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.Field;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.Presence;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.Snapshot;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueCodec;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueModel;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryModel.*;

/** Original observation finalizer boundary. No provider, native transport, process or ledger is opened. */
public final class ConstructionQueryCodec {
    public static final String SCHEMA = "xar.construction-query-observation-input.v1";
    public static final int MAX_BYTES = 262_144;
    private static final ObjectMapper JSON = new ObjectMapper();
    private ConstructionQueryCodec() { }

    public static Observation decode(byte[] raw) { return decodeNode(StrictJson.parse(raw, MAX_BYTES)); }
    public static byte[] finalizeObservation(byte[] raw) {
        JsonNode request = StrictJson.parse(raw, MAX_BYTES); Observation observation = decodeNode(request);
        Result result = ConstructionQueryPolicy.finalizeObservation(observation); ObjectNode output = StrictJson.object();
        if (result instanceof Rejected rejected) {
            output.put("status", "read_rejected"); output.put("reason", rejected.reason().wire()); return emit(output);
        }
        SourceBuild build = observation.build();
        if (build.build() != ConstructionValueModel.Build.V11906) { output.put("exact_ck3_build", build.build().wire()); output.put("exe_sha256", build.sha256()); }
        output.put("native_query_request_id", observation.requestId());
        if (result instanceof SourceRed) {
            output.put("status", "source_red"); output.set("native_result", request.get("native_envelope").get("result").deepCopy());
            output.set("source_frame", sourceFrame(observation.starting(), observation.starting().core().publicRevision().value()));
            ObjectNode ending = output.putObject("ending_frame");
            putValueOrNull(ending, "snapshot_id", observation.ending().core().snapshotId());
            putValueOrNull(ending, "revision", observation.ending().core().publicRevision());
            putValueOrNull(ending, "episode_run_id", observation.ending().episode()); return emit(output);
        }
        Ready ready = (Ready) result;
        if (!(observation.envelope().result().value() instanceof NativeResult nativeResult))
            throw new IllegalStateException("a ready construction source requires its typed admitted native result");
        ObjectNode source = sourceFrame(observation.starting(), observation.expectedRevision());
        JsonNode originalWorld = request.get("native_envelope").get("result").get("private_probe").get("player_world_building_sources");
        ObjectNode world = ((ObjectNode) originalWorld).deepCopy();
        if (world.has(ConstructionMode3.FIELD)) {
            // Its own normalizer consumes only these identities and the copied optional packet, not the legal-sample body.
            ObjectNode minimalWorld = StrictJson.object();
            for (String field : Set.of("snapshot_revision", "date_raw", "player_character_id", ConstructionMode3.FIELD)) {
                if (world.has(field)) { minimalWorld.set(field, world.get(field).deepCopy()); }
            }
            ArrayNode identities = minimalWorld.putArray("active_constructions");
            for (JsonNode row : world.get("active_constructions")) {
                ObjectNode identity = identities.addObject();
                for (String field : Set.of("barony_title_id", "province_id")) { if (row.has(field)) { identity.set(field, row.get(field).deepCopy()); } }
            }
            ObjectNode mode3Request = StrictJson.object(); mode3Request.put("schema", ConstructionMode3Codec.REQUEST_SCHEMA);
            mode3Request.set("world", minimalWorld); mode3Request.set("source_frame", source.deepCopy());
            ObjectNode identity = mode3Request.putObject("build"); identity.put("game_version", build.build().wire()); identity.put("executable_sha256", build.sha256());
            mode3Request.put("barony_title_id", 0); mode3Request.put("province_id", 0);
            JsonNode normalized = StrictJson.parse(ConstructionMode3Codec.evaluateProjection(mode3Request));
            world.set(ConstructionMode3.FIELD, normalized.get("world").get(ConstructionMode3.FIELD));
            normalized.get("observation").properties().forEach(entry -> output.set(entry.getKey(), entry.getValue()));
        }
        output.set("world", world); output.set("source_frame", source);
        output.put("proof_epoch", nativeResult.probe().value().proofEpoch().value());
        output.put("status", switch (ready.kind()) {
            case MATERIAL_SOURCE -> "material_source";
            case SELECTED -> "selected";
            case NO_LEGAL_BUDGETED_BUILDING -> "no_legal_budgeted_building";
            case EVIDENCE_INSUFFICIENT -> "evidence_insufficient";
        });
        if (ready.kind() == ReadyKind.SELECTED) {
            output.set("candidate", StrictJson.parse(ConstructionValueCodec.encodeSelection(new ConstructionValueModel.Selected(ready.candidate()))));
        } else if (ready.kind() == ReadyKind.EVIDENCE_INSUFFICIENT) { output.put("reason", "positive_income_candidate_coverage_incomplete"); }
        return emit(output);
    }

    private static Observation decodeNode(JsonNode request) {
        StrictJson.object(request, Set.of("schema", "starting_snapshot", "ending_snapshot", "native_envelope", "expected_revision",
                "native_query_request_id", "material_receipt", "wartime_observation"));
        StrictJson.require(SCHEMA.equals(text(request.get("schema"))), "construction query observation schema required");
        JsonNode starting = object(request.get("starting_snapshot"));
        return new Observation(frame(starting), frame(object(request.get("ending_snapshot"))), envelope(request.get("native_envelope")),
                integer(request.get("expected_revision")), text(request.get("native_query_request_id")), bool(request.get("material_receipt")),
                bool(request.get("wartime_observation")), sourceBuild(starting));
    }
    private static SourceBuild sourceBuild(JsonNode snapshot) {
        JsonNode hello = part(part(snapshot, "diagnostics"), "hello");
        if (hello == null) { return new SourceBuild(ConstructionValueModel.Build.V11906, ConstructionQueryModel.expectedSha(ConstructionValueModel.Build.V11906)); }
        JsonNode version = hello.has("expected_ck3_version") ? hello.get("expected_ck3_version") : hello.get("game_version");
        JsonNode sha = hello.has("expected_ck3_sha256") ? hello.get("expected_ck3_sha256") : hello.get("executable_sha256");
        return new SourceBuild(ConstructionValueModel.Build.fromWire(text(version)), text(sha).toUpperCase(Locale.ROOT));
    }
    private static Frame frame(JsonNode node) {
        JsonNode played = part(node, "played_character");
        Snapshot core = new Snapshot(read(node, "paused", ConstructionQueryCodec::bool), read(node, "active_wars", ConstructionQueryCodec::count),
                read(played, "character_id", ConstructionQueryCodec::integer), read(node, "native_revision", ConstructionQueryCodec::integer),
                read(node, "revision", ConstructionQueryCodec::integer), read(node, "snapshot_id", ConstructionQueryCodec::text), read(node, "date_raw", ConstructionQueryCodec::integer));
        return new Frame(core, read(node, "map_ready", ConstructionQueryCodec::bool), read(played, "alive", ConstructionQueryCodec::bool),
                read(node, "player_armies", ConstructionQueryCodec::count), presence(node.get("active_event")),
                presence(node.get("pending_character_interaction")), read(node, "episode_run_id", ConstructionQueryCodec::text));
    }
    private static Envelope envelope(JsonNode value) {
        if (value.isNull()) { return new Envelope(Field.missing(), Field.missing(), Field.missing(), Field.missing(), Field.missing()); }
        JsonNode node = object(value);
        return new Envelope(read(node, "type", ConstructionQueryCodec::text), read(node, "protocol_version", ConstructionQueryCodec::integer),
                read(node, "request_id", ConstructionQueryCodec::text), read(node, "ok", ConstructionQueryCodec::bool), read(node, "result", result -> {
                    object(result);
                    JsonNode step=result.get("step"),accepted=result.get("accepted");
                    if(step==null||!step.isTextual()||!ConstructionQueryPolicy.QUERY_NATIVE.equals(step.textValue()))
                        return new NativeAdmissionMismatch(AdmissionField.STEP);
                    if(accepted==null||!accepted.isBoolean()||!accepted.booleanValue())
                        return new NativeAdmissionMismatch(AdmissionField.ACCEPTED);
                    return new NativeResult(read(result, "step", ConstructionQueryCodec::text), read(result, "accepted", ConstructionQueryCodec::bool),
                            read(result, "private_probe", probe -> {
                                object(probe); return new Probe(read(probe, "advertised", ConstructionQueryCodec::bool), read(probe, "snapshot_revision", ConstructionQueryCodec::integer),
                                        read(probe, "date_raw", ConstructionQueryCodec::integer), read(probe, "proof_epoch", ConstructionQueryCodec::integer),
                                        read(probe, "player_world_building_sources", world -> {
                                            object(world); return new SourceWorld(read(world, "status", ConstructionQueryCodec::text), read(world, "snapshot_revision", ConstructionQueryCodec::integer),
                                                    read(world, "date_raw", ConstructionQueryCodec::integer), read(world, "player_character_id", ConstructionQueryCodec::integer),
                                                    read(world, "native_final_legality_evaluated", ConstructionQueryCodec::bool), read(world, "native_cost_evaluated", ConstructionQueryCodec::bool),
                                                    ConstructionValueCodec.worldProjection(world));
                                        }));
                            }));
                }));
    }
    private static ObjectNode sourceFrame(Frame frame, BigInteger publicRevision) {
        ObjectNode node = StrictJson.object(); Snapshot core = frame.core();
        putValueOrNull(node, "snapshot_id", core.snapshotId()); node.put("revision", publicRevision); putValueOrNull(node, "native_revision", core.nativeRevision());
        putValueOrNull(node, "date_raw", core.dateRaw()); putValueOrNull(node, "episode_run_id", frame.episode()); putValueOrNull(node, "actor_character_id", core.actorId()); return node;
    }
    private static <T> void putValueOrNull(ObjectNode node, String key, Field<T> field) {
        if (!field.known()) { node.putNull(key); }
        else if (field.value() instanceof String text) { node.put(key, text); }
        else if (field.value() instanceof BigInteger integer) { node.put(key, integer); }
        else { throw new IllegalArgumentException("only typed source text/integer fields can be emitted"); }
    }
    private static byte[] emit(JsonNode node) {
        try { byte[] bytes = JSON.writeValueAsBytes(retainFloatingKind(node)); StrictJson.require(bytes.length <= MAX_BYTES, "construction query output byte budget exceeded"); return bytes; }
        catch (JsonProcessingException failure) { throw new IllegalArgumentException("query projection serialization failed", failure); }
    }
    private static JsonNode retainFloatingKind(JsonNode node) {
        if (node.isFloatingPointNumber() && node.decimalValue().scale() == 0) { return DecimalNode.valueOf(node.decimalValue().setScale(1)); }
        if (node.isObject()) { ((ObjectNode) node).properties().forEach(entry -> ((ObjectNode) node).set(entry.getKey(), retainFloatingKind(entry.getValue()))); }
        else if (node.isArray()) { for (int index = 0; index < node.size(); index++) { ((ArrayNode) node).set(index, retainFloatingKind(node.get(index))); } }
        return node;
    }
    private static JsonNode object(JsonNode node) { StrictJson.require(node != null && node.isObject(), "declared native query object required"); return node; }
    private static JsonNode part(JsonNode node, String field) { JsonNode value = node == null ? null : node.get(field); return value != null && value.isObject() ? value : null; }
    private static BigInteger integer(JsonNode node) { StrictJson.require(node != null && node.isIntegralNumber(), "exact native integer token required"); return node.bigIntegerValue(); }
    private static Boolean bool(JsonNode node) { StrictJson.require(node != null && node.isBoolean(), "actual native boolean token required"); return node.booleanValue(); }
    private static Integer count(JsonNode node) { StrictJson.require(node.isArray(), "native array projection required"); return node.size(); }
    private static String text(JsonNode node) { StrictJson.require(node != null && node.isTextual(), "native string token required"); if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); } return node.textValue(); }
    private static Presence presence(JsonNode node) { return node == null ? Presence.MISSING : node.isNull() ? Presence.NULL : Presence.VALUE; }
    private static <T> Field<T> read(JsonNode node, String field, Function<JsonNode, T> parser) {
        JsonNode value = node == null ? null : node.get(field); return value == null ? Field.missing() : value.isNull() ? Field.nil() : Field.of(parser.apply(value));
    }
}
