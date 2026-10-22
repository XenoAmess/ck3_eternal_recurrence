package org.xar.ck3.control.diagnostics;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.diagnostics.NativeClockFailureObservation.*;

/** Strict diagnostic-only boundary. Source-pin equality is checked against caller-supplied evidence. */
public final class NativeClockFailureCodec {
    public static final int MAX_BYTES = 16_384;
    private NativeClockFailureCodec() { }

    public static NativeClockFailureObservation parse(byte[] raw, SourcePin expectedSource) {
        StrictJson.require(expectedSource != null, "external source pin required");
        StrictJson.require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded failure projection required");
        ObjectNode row = object(StrictJson.parse(raw), "schema", "machine_id", "observed_at_utc", "source",
                "wait_identity", "target_date_raw", "credit", "never_replay", "starting", "wait_final",
                "progress", "cleanup_attempts", "cleanup_tail");
        StrictJson.require(NativeClockFailureObservation.SCHEMA.equals(text(row, "schema")), "unsupported observation schema");
        StrictJson.require(integer(row, "credit", 0, 0) == 0, "failed clocks grant zero credit");
        StrictJson.trueValue(row.get("never_replay"));
        ObjectNode src = object(row.get("source"), "schema", "sha256", "control_sequence", "projection_notice");
        SourceEvidence source = new SourceEvidence(text(src, "schema"), text(src, "sha256"),
                integer(src, "control_sequence", 1, Integer.MAX_VALUE), text(src, "projection_notice"));
        StrictJson.require(source.sourceSha256().equals(expectedSource.sha256())
                && source.controlSequence() == expectedSource.controlSequence(), "failure source pin mismatch");
        ObjectNode id = object(row.get("wait_identity"), "bridge", "episode_character_id", "episode_id");
        WaitIdentity identity = new WaitIdentity(bridge(id.get("bridge")),
                safe(id, "episode_character_id", 1), text(id, "episode_id"));
        JsonNode attempts = row.get("cleanup_attempts");
        StrictJson.require(attempts.isArray() && attempts.size() <= 8, "bounded cleanup array required");
        List<PauseAttempt> parsed = new ArrayList<>();
        for (JsonNode attempt : attempts) {
            ObjectNode value = object(attempt, "native_request_id", "status", "accepted");
            PauseAckStatus status = switch (text(value, "status")) {
                case "submitted" -> PauseAckStatus.SUBMITTED;
                case "already_observed" -> PauseAckStatus.ALREADY_OBSERVED;
                case "rejected" -> PauseAckStatus.REJECTED;
                case "unavailable" -> PauseAckStatus.UNAVAILABLE;
                default -> throw new org.xar.ck3.control.contracts.ContractViolationException("unsupported pause ACK status");
            };
            parsed.add(new PauseAttempt(text(value, "native_request_id"), status, nullableBoolean(value.get("accepted"))));
        }
        ObjectNode tail = object(row.get("cleanup_tail"), "heartbeat", "owner", "observer_completed_ms", "paused_after_cleanup");
        NativeClockFailureObservation result = new NativeClockFailureObservation(text(row, "machine_id"),
                text(row, "observed_at_utc"), source, identity, safe(row, "target_date_raw", 0),
                frame(row.get("starting")), frame(row.get("wait_final")), progress(row.get("progress")), parsed,
                new CleanupTail(heartbeat(tail.get("heartbeat")), owner(tail.get("owner")),
                        decimal(tail, "observer_completed_ms"), nullableBoolean(tail.get("paused_after_cleanup"))));
        validate(result);
        return result;
    }

    /** Canonical new-schema JSON only; this never serializes the legacy response or its float timings. */
    public static byte[] encode(NativeClockFailureObservation value) {
        validate(value);
        ObjectNode row = StrictJson.object();
        row.put("schema", NativeClockFailureObservation.SCHEMA);
        row.put("machine_id", value.machineId()); row.put("observed_at_utc", value.observedAtUtc());
        ObjectNode source = StrictJson.object();
        source.put("schema", value.source().sourceSchema()); source.put("sha256", value.source().sourceSha256());
        source.put("control_sequence", value.source().controlSequence()); source.put("projection_notice", value.source().projectionNotice());
        row.set("source", source);
        ObjectNode identity = StrictJson.object();
        identity.set("bridge", encodeBridge(value.waitIdentity().bridge()));
        identity.put("episode_character_id", value.waitIdentity().episodeCharacterId());
        identity.put("episode_id", value.waitIdentity().episodeId()); row.set("wait_identity", identity);
        row.put("target_date_raw", value.targetDateRaw()); row.put("credit", 0); row.put("never_replay", true);
        row.set("starting", encodeFrame(value.starting())); row.set("wait_final", encodeFrame(value.waitFinal()));
        row.set("progress", encodeProgress(value.progress()));
        var attempts = row.putArray("cleanup_attempts");
        for (PauseAttempt attempt : value.cleanupAttempts()) {
            ObjectNode encoded = StrictJson.object();
            encoded.put("native_request_id", attempt.nativeRequestId());
            encoded.put("status", attempt.status().name().toLowerCase(Locale.ROOT));
            putNullableBoolean(encoded, "accepted", attempt.accepted()); attempts.add(encoded);
        }
        ObjectNode tail = StrictJson.object();
        tail.set("heartbeat", encodeHeartbeat(value.cleanupTail().heartbeat()));
        tail.set("owner", encodeOwner(value.cleanupTail().owner()));
        tail.put("observer_completed_ms", value.cleanupTail().observerCompletedMillis().decimal());
        putNullableBoolean(tail, "paused_after_cleanup", value.cleanupTail().pausedAfterCleanup());
        row.set("cleanup_tail", tail);
        return StrictJson.canonical(row, MAX_BYTES);
    }

    private static ObjectNode encodeBridge(BridgeIdentity value) {
        ObjectNode row = StrictJson.object(); row.put("bridge_pid", value.bridgePid());
        row.put("connection_generation", value.connectionGeneration()); return row;
    }

    private static ObjectNode encodeHeartbeat(Heartbeat value) {
        ObjectNode row = StrictJson.object(); row.put("sequence", value.sequence().decimal());
        row.put("monotonic_ms", value.monotonicMillis().decimal()); return row;
    }

    private static ObjectNode encodeOwner(Owner value) {
        ObjectNode row = StrictJson.object(); row.put("pump_epochs", value.pumpEpochs().decimal());
        row.put("verified_pump_epochs", value.verifiedPumpEpochs().decimal()); return row;
    }

    private static ObjectNode encodeFrame(ClockFrame value) {
        ObjectNode row = StrictJson.object(); row.put("date_raw", value.dateRaw()); row.put("revision", value.revision());
        row.put("native_revision", value.nativeRevision()); row.put("speed", value.speed()); row.put("paused", value.paused());
        row.set("bridge", encodeBridge(value.bridge())); row.put("episode_character_id", value.episodeCharacterId());
        row.set("heartbeat", encodeHeartbeat(value.heartbeat())); row.set("owner", encodeOwner(value.owner()));
        ObjectNode observer = StrictJson.object(); observer.put("started_ms", value.observer().startedMillis().decimal());
        observer.put("completed_ms", value.observer().completedMillis().decimal());
        observer.put("read_in_progress", value.observer().readInProgress()); observer.put("last_read_available", value.observer().lastReadAvailable());
        row.set("observer", observer); return row;
    }

    private static ObjectNode encodeProgress(WaitProgress value) {
        ObjectNode row = StrictJson.object(); row.put("arm_generation", value.armGeneration().decimal()); row.put("flags", value.flags().decimal());
        row.put("elapsed_ms", value.elapsedMillis()); row.put("heartbeat_events", value.heartbeatEvents());
        row.put("maximum_heartbeat_gap_ms", value.maximumHeartbeatGapMillis());
        row.set("owner", encodeMetric(value.owner())); row.set("verified", encodeMetric(value.verified()));
        row.set("heartbeat", encodeMetric(value.heartbeat())); row.set("observer", encodeMetric(value.observer()));
        row.put("native_event_time_verified", value.nativeEventTimeVerified()); row.put("atomic_observation", value.atomicObservation());
        return row;
    }

    private static ObjectNode encodeMetric(Metric value) {
        ObjectNode row = StrictJson.object(); row.put("first", value.first().decimal()); row.put("last", value.last().decimal());
        if (value.lastChangeMillis() == null) { row.putNull("last_change_ms"); } else { row.put("last_change_ms", value.lastChangeMillis()); }
        row.put("changes", value.changes()); row.put("delta", value.delta().decimal());
        row.put("missing", value.missing()); row.put("resets", value.resets()); return row;
    }

    private static void putNullableBoolean(ObjectNode row, String key, Boolean value) {
        if (value == null) { row.putNull(key); } else { row.put(key, value); }
    }

    static void validate(NativeClockFailureObservation value) {
        StrictJson.require(value != null, "clock observation required");
        WaitProgress progress = value.progress();
        checkMetric(progress.owner(), progress.elapsedMillis());
        checkMetric(progress.verified(), progress.elapsedMillis());
        checkMetric(progress.heartbeat(), progress.elapsedMillis());
        checkMetric(progress.observer(), progress.elapsedMillis());
        StrictJson.require(progress.heartbeatEvents() >= progress.heartbeat().changes(), "heartbeat changes exceed received events");
        StrictJson.require(!progress.atomicObservation(), "source diagnostic is not an atomic observation");
        StrictJson.require(!progress.nativeEventTimeVerified(), "source diagnostic does not verify native event time");
    }

    private static void checkMetric(Metric metric, int elapsed) {
        StrictJson.require(metric.lastChangeMillis() == null || metric.lastChangeMillis() <= elapsed, "metric time outside observation window");
        if (metric.resets() == 0) {
            BigInteger difference = number(metric.last()).subtract(number(metric.first()));
            StrictJson.require(difference.signum() >= 0 && difference.equals(number(metric.delta())), "metric delta mismatch or unreported reset");
            StrictJson.require(metric.changes() != 0 || (difference.signum() == 0 && metric.lastChangeMillis() == null),
                    "unchanged metric must have zero delta and an unobserved change time");
            StrictJson.require(metric.changes() == 0 || metric.lastChangeMillis() != null,
                    "observed change requires an actual change time");
        }
    }

    static BigInteger number(CrossJsDecimalUInt64 value) { return new BigInteger(value.decimal()); }

    private static ClockFrame frame(JsonNode raw) {
        ObjectNode row = object(raw, "date_raw", "revision", "native_revision", "speed", "paused", "bridge",
                "episode_character_id", "heartbeat", "owner", "observer");
        return new ClockFrame(safe(row, "date_raw", 0),
                StrictJson.integer(row.get("revision"), 1, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(row.get("native_revision"), 1, StrictJson.MAX_SAFE_INTEGER),
                integer(row, "speed", 1, 5), bool(row.get("paused")), bridge(row.get("bridge")),
                safe(row, "episode_character_id", 1), heartbeat(row.get("heartbeat")),
                owner(row.get("owner")), observer(row.get("observer")));
    }

    private static BridgeIdentity bridge(JsonNode raw) {
        ObjectNode row = object(raw, "bridge_pid", "connection_generation");
        return new BridgeIdentity(StrictJson.integer(row.get("bridge_pid"), 1, 0xffff_ffffL),
                StrictJson.integer(row.get("connection_generation"), 1, StrictJson.MAX_SAFE_INTEGER));
    }

    private static Heartbeat heartbeat(JsonNode raw) {
        ObjectNode row = object(raw, "sequence", "monotonic_ms");
        return new Heartbeat(decimal(row, "sequence"), decimal(row, "monotonic_ms"));
    }

    private static Owner owner(JsonNode raw) {
        ObjectNode row = object(raw, "pump_epochs", "verified_pump_epochs");
        return new Owner(decimal(row, "pump_epochs"), decimal(row, "verified_pump_epochs"));
    }

    private static Observer observer(JsonNode raw) {
        ObjectNode row = object(raw, "started_ms", "completed_ms", "read_in_progress", "last_read_available");
        return new Observer(decimal(row, "started_ms"), decimal(row, "completed_ms"),
                bool(row.get("read_in_progress")), bool(row.get("last_read_available")));
    }

    private static WaitProgress progress(JsonNode raw) {
        ObjectNode row = object(raw, "arm_generation", "flags", "elapsed_ms", "heartbeat_events", "maximum_heartbeat_gap_ms", "owner", "verified",
                "heartbeat", "observer", "native_event_time_verified", "atomic_observation");
        return new WaitProgress(decimal(row, "arm_generation"), decimal(row, "flags"), integer(row, "elapsed_ms", 1, Integer.MAX_VALUE),
                integer(row, "heartbeat_events", 0, Integer.MAX_VALUE), integer(row, "maximum_heartbeat_gap_ms", 0, Integer.MAX_VALUE),
                metric(row.get("owner")), metric(row.get("verified")), metric(row.get("heartbeat")), metric(row.get("observer")),
                bool(row.get("native_event_time_verified")), bool(row.get("atomic_observation")));
    }

    private static Metric metric(JsonNode raw) {
        ObjectNode row = object(raw, "first", "last", "last_change_ms", "changes", "delta", "missing", "resets");
        JsonNode changed = row.get("last_change_ms");
        Integer lastChange = changed.isNull() ? null : integer(row, "last_change_ms", 0, Integer.MAX_VALUE);
        return new Metric(decimal(row, "first"), decimal(row, "last"), lastChange,
                integer(row, "changes", 0, Integer.MAX_VALUE), decimal(row, "delta"),
                integer(row, "missing", 0, Integer.MAX_VALUE), integer(row, "resets", 0, Integer.MAX_VALUE));
    }

    private static ObjectNode object(JsonNode node, String... keys) { return StrictJson.object(node, Set.of(keys)); }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static CrossJsDecimalUInt64 decimal(ObjectNode row, String field) { return new CrossJsDecimalUInt64(text(row, field)); }
    private static int integer(ObjectNode row, String field, int minimum, int maximum) {
        return Math.toIntExact(StrictJson.integer(row.get(field), minimum, maximum));
    }
    private static long safe(ObjectNode row, String field, long minimum) {
        return StrictJson.integer(row.get(field), minimum, StrictJson.MAX_SAFE_INTEGER);
    }
    private static boolean bool(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "exact JSON boolean required");
        return node.booleanValue();
    }
    private static Boolean nullableBoolean(JsonNode node) {
        StrictJson.require(node != null, "required nullable field must not be missing");
        return node.isNull() ? null : bool(node);
    }
}
