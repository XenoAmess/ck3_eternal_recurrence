package org.xar.ck3.control.wave2.military.prewaradmission;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.Declaration;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.DetachedObject;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.Diagnostics;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.Field;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.Hello;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.PlayedCharacter;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.QueryEnvelope;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionInput.Snapshot;

/** One strict projected JSON entry. Rich SDK containers require an explicit projection, not exact old keys. */
public final class PrewarAdmissionCodec {
    public static final String SCHEMA = "xar.ck3.ordinary-prewar-admission.input/v1";
    public static final String QUERY_KEY = "prewar_force_coalition_coverage_v2_query";
    public static final String DOMAIN_KEY = "prewar_force_coalition_coverage_v2";
    private static final Set<String> SNAPSHOT_FIELDS = Set.of("paused", "map_ready", "played_character", "diagnostics",
            "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "capture_epoch", "declarable_wars", QUERY_KEY);
    private static final Set<String> DECLARATION_FIELDS = Set.of("declaration_id", "target_character_id", "casus_belli_index",
            "casus_belli_key", "configuration_index", "claimant_character_id", "target_title_ids");
    private static final Set<String> QUERY_FIELDS = Set.of("queried_snapshot_id", "queried_revision", "queried_native_revision",
            "queried_date_raw", "queried_actor_character_id", "queried_connection_generation", "queried_episode_run_id",
            "accepted", "status", "execution_receipt", "native_request_id", DOMAIN_KEY);

    private static final Set<String> PLAYED_FIELDS = Set.of("alive", "character_id");
    private static final Set<String> DIAGNOSTICS_FIELDS = Set.of("hello", "connection_generation");
    private static final Set<String> HELLO_FIELDS = Set.of("bridge_version", "expected_ck3_version", "expected_ck3_sha256");

    private PrewarAdmissionCodec() { }

    /** Named projection of the actual rich legacy container; original numeric tokens are never reencoded. */
    public static PrewarAdmissionInput decodeLegacyContainer(JsonNode snapshot, JsonNode declaration) {
        ObjectNode request = StrictJson.object().put("schema", SCHEMA);
        request.set("snapshot", projectLegacySnapshot(snapshot));
        request.set("declaration", projectKnown(declaration, DECLARATION_FIELDS));
        return decodeProjected(request);
    }

    private static JsonNode projectLegacySnapshot(JsonNode value) {
        require(value != null, "legacy snapshot field missing");
        if (value.isNull()) return value;
        ObjectNode row = projectKnown(value, SNAPSHOT_FIELDS);
        if (row.hasNonNull("played_character")) {
            row.set("played_character", projectKnown(row.get("played_character"), PLAYED_FIELDS));
        }
        if (row.hasNonNull("diagnostics")) {
            ObjectNode diagnostics = projectKnown(row.get("diagnostics"), DIAGNOSTICS_FIELDS);
            if (diagnostics.hasNonNull("hello")) diagnostics.set("hello",
                    projectKnown(diagnostics.get("hello"), HELLO_FIELDS));
            row.set("diagnostics", diagnostics);
        }
        if (row.hasNonNull("declarable_wars")) {
            require(row.get("declarable_wars").isArray(), "legacy declaration catalogue array required");
            ArrayNode choices = StrictJson.object().putArray("choices");
            for (JsonNode choice : row.get("declarable_wars")) choices.add(projectKnown(choice, DECLARATION_FIELDS));
            row.set("declarable_wars", choices);
        }
        if (row.hasNonNull(QUERY_KEY)) row.set(QUERY_KEY, projectKnown(row.get(QUERY_KEY), QUERY_FIELDS));
        return row;
    }

    private static ObjectNode projectKnown(JsonNode value, Set<String> fields) {
        require(value instanceof ObjectNode, "legacy projected container must be an object");
        ObjectNode result = StrictJson.object();
        for (String field : fields) if (value.has(field)) result.set(field, value.get(field).deepCopy());
        return result;
    }

    public static PrewarAdmissionInput decode(byte[] raw) { return decodeProjected(StrictJson.parse(raw)); }

    /** Also used by a parsed native adapter; validators see numeric node types before any reserialization. */
    public static PrewarAdmissionInput decodeProjected(JsonNode value) {
        ObjectNode root = StrictJson.object(value, Set.of("schema", "snapshot", "declaration"));
        require(text(root.get("schema")).equals(SCHEMA), "wrong prewar admission input schema");
        return new PrewarAdmissionInput(field(root, "snapshot", PrewarAdmissionCodec::snapshot), declaration(root.get("declaration")));
    }

    public static byte[] encode(PrewarAdmissionInput input) {
        ObjectNode root = StrictJson.object().put("schema", SCHEMA);
        put(root, "snapshot", input.snapshot(), PrewarAdmissionCodec::snapshotNode);
        root.set("declaration", declarationNode(input.declaration()));
        return StrictJson.canonical(root);
    }

    public static ObjectNode snapshotNode(Snapshot row) {
        ObjectNode result = StrictJson.object();
        put(result, "paused", row.paused(), PrewarAdmissionCodec::booleanNode);
        put(result, "map_ready", row.mapReady(), PrewarAdmissionCodec::booleanNode);
        put(result, "played_character", row.playedCharacter(), value -> {
            ObjectNode node = StrictJson.object();
            put(node, "alive", value.alive(), PrewarAdmissionCodec::booleanNode);
            put(node, "character_id", value.characterId(), PrewarAdmissionCodec::integerNode);
            return node;
        });
        put(result, "diagnostics", row.diagnostics(), value -> {
            ObjectNode node = StrictJson.object();
            put(node, "connection_generation", value.connectionGeneration(), PrewarAdmissionCodec::integerNode);
            put(node, "hello", value.hello(), hello -> {
                ObjectNode child = StrictJson.object();
                put(child, "bridge_version", hello.bridgeVersion(), PrewarAdmissionCodec::textNode);
                put(child, "expected_ck3_version", hello.expectedCk3Version(), PrewarAdmissionCodec::textNode);
                put(child, "expected_ck3_sha256", hello.expectedCk3Sha256(), PrewarAdmissionCodec::textNode);
                return child;
            });
            return node;
        });
        put(result, "snapshot_id", row.snapshotId(), PrewarAdmissionCodec::textNode);
        put(result, "revision", row.revision(), PrewarAdmissionCodec::integerNode);
        put(result, "native_revision", row.nativeRevision(), PrewarAdmissionCodec::integerNode);
        put(result, "date_raw", row.dateRaw(), PrewarAdmissionCodec::integerNode);
        put(result, "episode_run_id", row.episodeRunId(), PrewarAdmissionCodec::textNode);
        put(result, "capture_epoch", row.captureEpoch(), PrewarAdmissionCodec::integerNode);
        put(result, "declarable_wars", row.declarableWars(), rows -> array(rows, PrewarAdmissionCodec::declarationNode));
        put(result, QUERY_KEY, row.query(), PrewarAdmissionCodec::queryNode);
        return result;
    }

    public static ObjectNode declarationNode(Declaration row) {
        ObjectNode result = StrictJson.object();
        put(result, "declaration_id", row.declarationId(), PrewarAdmissionCodec::textNode);
        put(result, "target_character_id", row.targetCharacterId(), PrewarAdmissionCodec::integerNode);
        put(result, "casus_belli_index", row.casusBelliIndex(), PrewarAdmissionCodec::integerNode);
        put(result, "casus_belli_key", row.casusBelliKey(), PrewarAdmissionCodec::textNode);
        put(result, "configuration_index", row.configurationIndex(), PrewarAdmissionCodec::integerNode);
        put(result, "claimant_character_id", row.claimantCharacterId(), PrewarAdmissionCodec::integerNode);
        put(result, "target_title_ids", row.targetTitleIds(), rows -> array(rows, PrewarAdmissionCodec::integerNode));
        return result;
    }

    private static Snapshot snapshot(JsonNode value) {
        ObjectNode row = projected(value, SNAPSHOT_FIELDS);
        return new Snapshot(field(row, "paused", PrewarAdmissionCodec::bool), field(row, "map_ready", PrewarAdmissionCodec::bool),
                field(row, "played_character", PrewarAdmissionCodec::played), field(row, "diagnostics", PrewarAdmissionCodec::diagnostics),
                field(row, "snapshot_id", PrewarAdmissionCodec::text), field(row, "revision", PrewarAdmissionCodec::integer),
                field(row, "native_revision", PrewarAdmissionCodec::integer), field(row, "date_raw", PrewarAdmissionCodec::integer),
                field(row, "episode_run_id", PrewarAdmissionCodec::text), field(row, "capture_epoch", PrewarAdmissionCodec::integer),
                field(row, "declarable_wars", node -> list(node, PrewarAdmissionCodec::declaration)),
                field(row, QUERY_KEY, PrewarAdmissionCodec::query));
    }

    private static PlayedCharacter played(JsonNode value) {
        ObjectNode row = projected(value, PLAYED_FIELDS);
        return new PlayedCharacter(field(row, "alive", PrewarAdmissionCodec::bool), field(row, "character_id", PrewarAdmissionCodec::integer));
    }

    private static Diagnostics diagnostics(JsonNode value) {
        ObjectNode row = projected(value, DIAGNOSTICS_FIELDS);
        return new Diagnostics(field(row, "hello", node -> {
            ObjectNode hello = projected(node, HELLO_FIELDS);
            return new Hello(field(hello, "bridge_version", PrewarAdmissionCodec::text),
                    field(hello, "expected_ck3_version", PrewarAdmissionCodec::text), field(hello, "expected_ck3_sha256", PrewarAdmissionCodec::text));
        }), field(row, "connection_generation", PrewarAdmissionCodec::integer));
    }

    private static Declaration declaration(JsonNode value) {
        ObjectNode row = projected(value, DECLARATION_FIELDS);
        return new Declaration(field(row, "declaration_id", PrewarAdmissionCodec::text), field(row, "target_character_id", PrewarAdmissionCodec::integer),
                field(row, "casus_belli_index", PrewarAdmissionCodec::integer), field(row, "casus_belli_key", PrewarAdmissionCodec::text),
                field(row, "configuration_index", PrewarAdmissionCodec::integer), field(row, "claimant_character_id", PrewarAdmissionCodec::integer),
                field(row, "target_title_ids", node -> list(node, PrewarAdmissionCodec::integer)));
    }

    private static QueryEnvelope query(JsonNode value) {
        ObjectNode row = projected(value, QUERY_FIELDS);
        return new QueryEnvelope(field(row, "queried_snapshot_id", PrewarAdmissionCodec::text), field(row, "queried_revision", PrewarAdmissionCodec::integer),
                field(row, "queried_native_revision", PrewarAdmissionCodec::integer), field(row, "queried_date_raw", PrewarAdmissionCodec::integer),
                field(row, "queried_actor_character_id", PrewarAdmissionCodec::integer), field(row, "queried_connection_generation", PrewarAdmissionCodec::integer),
                field(row, "queried_episode_run_id", PrewarAdmissionCodec::text), field(row, "accepted", PrewarAdmissionCodec::bool),
                field(row, "status", PrewarAdmissionCodec::text), field(row, "execution_receipt", PrewarAdmissionCodec::detached),
                field(row, "native_request_id", PrewarAdmissionCodec::text), field(row, DOMAIN_KEY, PrewarAdmissionCodec::detached));
    }

    private static ObjectNode queryNode(QueryEnvelope row) {
        ObjectNode result = StrictJson.object();
        put(result, "queried_snapshot_id", row.queriedSnapshotId(), PrewarAdmissionCodec::textNode);
        put(result, "queried_revision", row.queriedRevision(), PrewarAdmissionCodec::integerNode);
        put(result, "queried_native_revision", row.queriedNativeRevision(), PrewarAdmissionCodec::integerNode);
        put(result, "queried_date_raw", row.queriedDateRaw(), PrewarAdmissionCodec::integerNode);
        put(result, "queried_actor_character_id", row.queriedActorCharacterId(), PrewarAdmissionCodec::integerNode);
        put(result, "queried_connection_generation", row.queriedConnectionGeneration(), PrewarAdmissionCodec::integerNode);
        put(result, "queried_episode_run_id", row.queriedEpisodeRunId(), PrewarAdmissionCodec::textNode);
        put(result, "accepted", row.accepted(), PrewarAdmissionCodec::booleanNode);
        put(result, "status", row.status(), PrewarAdmissionCodec::textNode);
        put(result, "execution_receipt", row.executionReceipt(), DetachedObject::copy);
        put(result, "native_request_id", row.nativeRequestId(), PrewarAdmissionCodec::textNode);
        put(result, DOMAIN_KEY, row.coverage(), DetachedObject::copy);
        return result;
    }

    private static DetachedObject detached(JsonNode value) {
        require(value instanceof ObjectNode, "detached native boundary object required");
        return new DetachedObject((ObjectNode) value);
    }
    private static ObjectNode projected(JsonNode value, Set<String> fields) {
        require(value instanceof ObjectNode, "projected JSON object required");
        ObjectNode row = (ObjectNode) value;
        row.fieldNames().forEachRemaining(name -> require(fields.contains(name), "unknown projected field: " + name));
        return row;
    }
    private static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "exact JSON integer required"); return node.bigIntegerValue(); }
    private static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "exact JSON boolean required"); return node.booleanValue(); }
    private static String text(JsonNode node) {
        require(node != null && node.isTextual(), "exact JSON text required");
        if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); }
        return node.textValue();
    }
    private static JsonNode integerNode(BigInteger value) { return StrictJson.object().numberNode(value); }
    private static JsonNode textNode(String value) { return StrictJson.object().textNode(value); }
    private static JsonNode booleanNode(Boolean value) { return StrictJson.object().booleanNode(value); }
    private static <T> Field<T> field(ObjectNode row, String name, Function<JsonNode, T> parser) {
        if (!row.has(name)) { return Field.missing(); }
        return row.get(name).isNull() ? Field.nullValue() : Field.of(parser.apply(row.get(name)));
    }
    private static <T> List<T> list(JsonNode node, Function<JsonNode, T> parser) {
        require(node instanceof ArrayNode, "exact JSON array required");
        List<T> result = new ArrayList<>();
        node.forEach(value -> result.add(parser.apply(value)));
        return List.copyOf(result);
    }
    private static <T> ArrayNode array(List<T> rows, Function<T, JsonNode> writer) {
        ArrayNode result = StrictJson.object().arrayNode(); rows.forEach(row -> result.add(writer.apply(row))); return result;
    }
    private static <T> void put(ObjectNode row, String name, Field<T> field, Function<T, JsonNode> writer) {
        switch (field.presence()) {
            case MISSING -> { }
            case NULL -> row.putNull(name);
            case VALUE -> row.set(name, writer.apply(field.value()));
        }
    }
}
