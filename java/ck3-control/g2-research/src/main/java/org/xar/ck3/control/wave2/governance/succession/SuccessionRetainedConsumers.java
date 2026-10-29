package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.check;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.semantic.NativeSemanticFingerprint;

/** Pure original retained readers. The caller retains its Driver/WAL locks and writer. */
public final class SuccessionRetainedConsumers {
    public static final String SCHEMA = "xar.java-succession-retained-consumer/v1";
    private static final Set<String> FLAGS = Set.of("managed_restore_transaction", "rollback_war_failure",
            "succession_expectation", "rollback_war_failures", "session_binding_present");
    private static final List<String> FRAME = List.of("snapshot_id", "revision", "native_revision", "date_raw");
    private static final BigInteger SAFE = BigInteger.ONE.shiftLeft(53).subtract(BigInteger.ONE);
    private SuccessionRetainedConsumers() { }

    public static byte[] apply(byte[] body) {
        JsonNode request = SuccessionCodec.parse(body);
        check(SCHEMA.equals(text(request, "schema")), "retained consumer schema changed");
        String operation = text(request, "operation");
        JsonNode result = switch (operation) {
            case "restore" -> {
                exact(request, "expectation", "episode_run_id", "episode_character_id");
                JsonNode episode = field(request, "episode_character_id"), run = field(request, "episode_run_id");
                check(episode.isNull() ? run.isNull() : episode.isIntegralNumber() && run.isTextual() && !run.textValue().isEmpty(),
                        "driver state episode identity is malformed");
                if (!episode.isNull()) { NativeCharacterId.fromJson(episode); }
                JsonNode value = nullableExpectation(field(request, "expectation"));
                if (!value.isNull()) {
                    JsonNode binding = field(value, "binding");
                    check(field(binding, "episode_run_id").equals(field(request, "episode_run_id"))
                            && field(binding, "episode_character_id").equals(field(request, "episode_character_id")),
                            "driver succession expectation changed episode");
                }
                yield value;
            }
            case "retained_reader" -> {
                exact(request, "expectation");
                yield nullableExpectation(field(request, "expectation"));
            }
            case "wal_business" -> {
                exact(request, "fields");
                ObjectNode fields = object(field(request, "fields")).deepCopy();
                ObjectNode expectation = canonicalExpectation(field(fields, "succession_expectation"));
                ObjectNode binding = object(field(expectation, "binding"));
                FRAME.forEach(binding::remove);
                fields.set("succession_expectation", expectation);
                yield fields;
            }
            case "saved_basis_flags" -> {
                exact(request, "flags");
                ObjectNode flags = object(field(request, "flags")).deepCopy();
                SuccessionCodec.exact(flags, FLAGS);
                check(field(flags, "managed_restore_transaction").isNull()
                        && field(flags, "rollback_war_failure").isNull()
                        && field(flags, "rollback_war_failures").isArray()
                        && field(flags, "rollback_war_failures").isEmpty()
                        && field(flags, "session_binding_present").isBoolean()
                        && !field(flags, "session_binding_present").booleanValue(), "Driver flags preserve no pending transaction");
                JsonNode expectation = field(flags, "succession_expectation");
                if (!expectation.isNull()) { flags.set("succession_expectation", canonicalExpectation(expectation)); }
                savedJsonDomain(flags);
                yield flags;
            }
            case "invalidate" -> {
                exact(request, "state", "snapshot", "campaign_root_result", "turn_bundle");
                yield invalidation(request, false);
            }
            case "warm_refresh" -> {
                exact(request, "state", "snapshot", "campaign_root_result", "turn_bundle", "restore_kind");
                yield invalidation(request, true);
            }
            default -> throw new IllegalArgumentException("unknown retained consumer operation");
        };
        return SuccessionCodec.encode(result);
    }

    private static JsonNode invalidation(JsonNode request, boolean warm) {
        JsonNode sourceState = field(request, "state");
        if (warm && (!field(request, "restore_kind").isTextual()
                || !"same_pid_hot".equals(field(request, "restore_kind").textValue()) || !sourceState.isObject())) {
            return NullNode.instance;
        }
        ObjectNode state = object(sourceState).deepCopy();
        JsonNode retained = state.get("expectation");
        if (retained == null || retained.isNull()) { return warm ? NullNode.instance : decision(state); }
        SuccessionModel.Expectation previous = SuccessionCodec.decodeExpectation(SuccessionCodec.encode(retained));
        JsonNode snapshotWire = field(request, "snapshot");
        if (warm) {
            BigInteger revision = uint64(field(snapshotWire, "revision"), false);
            if (previous.binding().frame().revision().compareTo(revision) <= 0) { return NullNode.instance; }
        }
        SuccessionModel.Snapshot snapshot = SuccessionCodec.snapshot(snapshotWire);
        check(snapshot != null && snapshot.frame() != null && Boolean.TRUE.equals(snapshot.paused())
                && Boolean.TRUE.equals(snapshot.mapReady()) && Boolean.FALSE.equals(snapshot.terminal())
                && snapshot.terminalReason() == null && snapshot.actor() != null && snapshot.actor().alive()
                && Objects.equals(snapshot.actor().characterId(), snapshot.episodeCharacterId()),
                "estate refresh requires the current living paused episode");
        SuccessionModel.Binding old = previous.binding();
        check(previous.predecessorCharacterId() == snapshot.actor().characterId()
                && Objects.equals(old.episodeCharacterId(), snapshot.episodeCharacterId())
                && old.episodeRunId().equals(snapshot.episodeRunId()), "estate refresh crossed its actor or episode");
        check(old.frame().dateRaw() <= snapshot.frame().dateRaw()
                && old.frame().nativeRevision().compareTo(snapshot.frame().nativeRevision()) <= 0
                && (warm || old.frame().revision().compareTo(snapshot.frame().revision()) <= 0),
                "retained estate differs from current actor/episode sequence");

        CompletedRoot root = completedRoot(request, snapshot, warm);
        SuccessionModel.Expectation observed = SuccessionPolicy.freeze(root.bundle(), snapshot.episodeRunId(), snapshot.episodeCharacterId());
        ObjectNode output = decision(state);
        output.set("source_binding", field(SuccessionCodec.expectationNode(observed), "binding"));
        output.put("source_query_sequence", root.querySequence());
        if (warm) {
            state.putNull("expectation").putNull("reconciliation");
            output.put("status", "source_epoch_refresh_required").put("invalidated", true).put("refresh_required", true);
            output.set("previous_source_binding", field(SuccessionCodec.expectationNode(previous), "binding"));
            output.withArray("changed_fields").add("sdk_publication_revision_domain");
            output.put("estate_change_inferred", false);
            return output;
        }
        ArrayNode changed = output.withArray("changed_fields");
        if (previous.primary().title().titleId() != observed.primary().title().titleId()) { changed.add("primary_title_id"); }
        if (!Objects.equals(previous.expectedSuccessorCharacterId(), observed.expectedSuccessorCharacterId())) { changed.add("expected_successor_character_id"); }
        JsonNode oldRows = field(SuccessionCodec.expectationNode(previous), "title_expectations");
        JsonNode newRows = field(SuccessionCodec.expectationNode(observed), "title_expectations");
        if (!NativeSemanticFingerprint.equivalent(oldRows, newRows)) { changed.add("title_expectations"); }
        boolean different = !changed.isEmpty();
        output.put("status", different ? "invalidated" : "unchanged").put("invalidated", different).put("refresh_required", different);
        if (different) { state.putNull("expectation").putNull("reconciliation"); }
        return output;
    }

    /** Already completed root plus actual original bundle; no source-read or query permission. */
    private record CompletedRoot(BigInteger querySequence, SuccessionModel.TurnBundle bundle) { }

    private static CompletedRoot completedRoot(JsonNode request, SuccessionModel.Snapshot snapshot, boolean warm) {
        JsonNode envelope = field(request, "campaign_root_result");
        JsonNode root = field(envelope, "campaign_root_context");
        check("available".equals(text(envelope, "status")) && "available".equals(text(root, "status")), "available completed root required");
        check(SuccessionCodec.frame(field(envelope, "binding"), false).equals(snapshot.frame()), "completed root and snapshot do not share one frame");
        check(uint64(field(root, "snapshot_revision"), false).equals(snapshot.frame().nativeRevision())
                && int32(field(root, "date_raw")).intValue() == snapshot.frame().dateRaw(), "root native/date source changed");
        BigInteger sequence = uint64(field(envelope, "query_sequence"), true);
        if (warm) { check(field(field(root, "readiness"), "held_title_partition_ready").isBoolean()
                && field(field(root, "readiness"), "held_title_partition_ready").booleanValue(), "warm refresh requires original complete estate"); }
        JsonNode bundleWire = field(request, "turn_bundle");
        SuccessionModel.TurnBundle bundle = SuccessionCodec.turnBundle(bundleWire, true);
        check(bundle.frame().equals(snapshot.frame()), "bundle and completed root frame changed");
        JsonNode source = field(bundleWire, "source");
        check("game.command.query-campaign-root-context-v1".equals(text(source, "capability"))
                && uint64(field(source, "query_sequence"), true).equals(sequence)
                && field(source, "backend_id").equals(nullish(field(request, "snapshot").get("backend_id"))), "bundle completed-root provenance changed");
        JsonNode rows = field(field(field(field(bundleWire, "succession_state"), "value"), "partition"), "value");
        check(field(rows, "title_heirs").equals(field(root, "held_title_partition")), "full root and bundle title partition changed");
        check(NativeCharacterId.fromJson(field(root, "player_character_id")).value() == snapshot.actor().characterId()
                && field(root, "player_character_alive").isBoolean() && field(root, "player_character_alive").booleanValue(), "root actor differs from living snapshot");
        JsonNode heirs = field(root, "primary_title_succession_character_ids");
        check(heirs.isArray(), "root heirs must be an array");
        Integer first = null; int index = 0;
        for (JsonNode heir : heirs) {
            int id = NativeCharacterId.fromJson(heir).value();
            if (index++ == 0) { first = id; }
        }
        check(Objects.equals(first, bundle.primaryHeirCharacterId()), "root and bundle primary heir changed");
        return new CompletedRoot(sequence, bundle);
    }

    private static ObjectNode decision(ObjectNode state) {
        ObjectNode output = SuccessionCodec.objectNode();
        output.put("schema", "xar.ck3.succession-estate-invalidation/v1").put("status", "not_applicable")
                .put("invalidated", false).put("refresh_required", false).putNull("source_binding").putNull("source_query_sequence")
                .put("queries_performed", 0).put("submission_authorized", false);
        output.set("state", state); output.putArray("changed_fields");
        return output;
    }

    private static JsonNode nullableExpectation(JsonNode value) {
        return value.isNull() ? NullNode.instance : SuccessionCodec.parse(SuccessionCodec.normalize(SuccessionCodec.encode(value)));
    }
    private static ObjectNode canonicalExpectation(JsonNode value) {
        JsonNode normalized = nullableExpectation(value);
        check(!normalized.isNull() && normalized.equals(value), "expectation is not canonical");
        return object(normalized).deepCopy();
    }
    private static void savedJsonDomain(JsonNode value) {
        if (value.isIntegralNumber()) { check(value.bigIntegerValue().abs().compareTo(SAFE) <= 0, "JSON integer loses precision"); }
        if (value.isFloatingPointNumber()) { check(Double.isFinite(value.doubleValue()), "finite JSON number required"); }
        if (value.isContainerNode()) { value.forEach(SuccessionRetainedConsumers::savedJsonDomain); }
    }
    private static BigInteger uint64(JsonNode value, boolean positive) {
        check(value.isIntegralNumber(), "exact uint64 integer required");
        BigInteger number = value.bigIntegerValue(); SuccessionModel.uint64(number);
        check(!positive || number.signum() > 0, "positive sequence required"); return number;
    }
    private static BigInteger int32(JsonNode value) {
        check(value.isIntegralNumber() && value.canConvertToInt(), "exact int32 required"); return value.bigIntegerValue();
    }
    private static JsonNode field(JsonNode value, String name) { return SuccessionCodec.field(value, name); }
    private static JsonNode nullish(JsonNode value) { return value == null ? NullNode.instance : value; }
    private static String text(JsonNode value, String name) { return SuccessionCodec.text(field(value, name)); }
    private static ObjectNode object(JsonNode value) {
        if (value instanceof ObjectNode object) { return object; }
        throw new IllegalArgumentException("retained object required");
    }
    private static void exact(JsonNode value, String... fields) {
        var keys = new java.util.HashSet<>(Set.of("schema", "operation")); keys.addAll(List.of(fields));
        SuccessionCodec.exact(value, Set.copyOf(keys));
    }
}
