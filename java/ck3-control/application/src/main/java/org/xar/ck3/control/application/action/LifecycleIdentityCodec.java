package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Set;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** One closed durable representation. Missing, JSON null and an actual dead character are separate branches. */
public final class LifecycleIdentityCodec {
    public static final String SCHEMA = "xar.java.lifecycle-terminal-identity/v1";
    private LifecycleIdentityCodec() { }
    public static ObjectNode encode(LifecycleIdentity value) {
        var row = StrictJson.object(); row.put("schema", SCHEMA); row.put("machine_id", value.machineId()); row.set("game", value.game().toJson());
        row.put("session_id", value.sessionId()); row.put("connection_generation", decimal(value.connectionGeneration()));
        var subject = row.putObject("subject"); subject.put("character_id", characterDecimal(value.subject().characterId()));
        subject.put("episode_run_id", value.subject().episodeRunId()); subject.put("episode_epoch", value.subject().episodeEpoch()); subject.put("driver_version", value.subject().driverVersion());
        var frame = row.putObject("frame"); frame.put("snapshot_id", value.frame().snapshotId()); frame.put("revision", decimal(value.frame().revision()));
        frame.put("native_revision", decimal(value.frame().nativeRevision())); frame.put("date_raw", value.frame().dateRaw().toString());
        frame.put("paused", value.frame().paused()); frame.put("map_ready", value.frame().mapReady());
        var player = row.putObject("current_player");
        switch (value.currentPlayer()) {
            case LifecycleIdentity.Missing ignored -> player.put("kind", "MISSING");
            case LifecycleIdentity.Null ignored -> player.put("kind", "NULL");
            case LifecycleIdentity.Character actual -> { player.put("kind", "CHARACTER"); player.put("character_id", characterDecimal(actual.characterId())); player.put("alive", actual.alive()); }
        }
        row.put("terminal_reason", value.terminalReason().wire());
        var evidence = row.putObject("evidence"); evidence.set("native_packet", value.nativeEvidence().toJson()); evidence.set("hello_packet", value.capabilityEvidence().toJson());
        evidence.set("observation_manifest", value.evidence().observationManifest().toJson()); evidence.set("original_driver", value.evidence().originalDriver().toJson());
        evidence.set("complete_source_qualification", ExactRef.optionalToJson(value.evidence().completeSourceQualification())); row.put("observed_at", value.observedAt().toString()); return row;
    }
    public static LifecycleIdentity decode(JsonNode value) {
        var row = StrictJson.object(value, Set.of("schema", "machine_id", "game", "session_id", "connection_generation", "subject", "frame", "current_player", "terminal_reason", "evidence", "observed_at"));
        StrictJson.require(text(row, "schema").equals(SCHEMA), "exact lifecycle terminal identity schema required");
        var subject = StrictJson.object(row.get("subject"), Set.of("character_id", "episode_run_id", "episode_epoch", "driver_version"));
        var frame = StrictJson.object(row.get("frame"), Set.of("snapshot_id", "revision", "native_revision", "date_raw", "paused", "map_ready"));
        String date = text(frame, "date_raw"); BigInteger exactDate = new BigInteger(date);
        StrictJson.require(exactDate.toString().equals(date), "canonical signed lifecycle date string required");
        var player = StrictJson.object(row.get("current_player"), fieldNames(row.get("current_player")));
        LifecycleIdentity.CurrentPlayer actual = switch (text(player, "kind")) {
            case "MISSING" -> { StrictJson.object(player, Set.of("kind")); yield new LifecycleIdentity.Missing(); }
            case "NULL" -> { StrictJson.object(player, Set.of("kind")); yield new LifecycleIdentity.Null(); }
            case "CHARACTER" -> { StrictJson.object(player, Set.of("kind", "character_id", "alive")); yield new LifecycleIdentity.Character(characterValue(player, "character_id"), bool(player, "alive")); }
            default -> throw new IllegalArgumentException("unknown lifecycle current-player presence");
        };
        var evidence = StrictJson.object(row.get("evidence"), Set.of("native_packet", "hello_packet", "observation_manifest", "original_driver"),Set.of("complete_source_qualification"));
        return new LifecycleIdentity(text(row, "machine_id"), GameGeneration.fromJson(row.get("game")), text(row, "session_id"), positive(row, "connection_generation"),
                new LifecycleIdentity.Subject(characterValue(subject, "character_id"), text(subject, "episode_run_id"),
                        StrictJson.integer(subject.get("episode_epoch"), 0, StrictJson.MAX_SAFE_INTEGER), StrictJson.integer(subject.get("driver_version"), 0, StrictJson.MAX_SAFE_INTEGER)),
                new LifecycleIdentity.Frame(text(frame, "snapshot_id"), positive(frame, "revision"), positive(frame, "native_revision"), exactDate, bool(frame, "paused"), bool(frame, "map_ready")),
                actual, LifecycleIdentity.TerminalReason.fromWire(text(row, "terminal_reason")),
                new LifecycleIdentity.Evidence(ExactRef.fromJson(evidence.get("native_packet")), ExactRef.fromJson(evidence.get("hello_packet")),
                        ExactRef.fromJson(evidence.get("observation_manifest")), ExactRef.fromJson(evidence.get("original_driver")), ExactRef.optionalFromJson(evidence.get("complete_source_qualification"))),
                Instant.parse(text(row, "observed_at")));
    }
    private static Set<String> fieldNames(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "current-player presence object required");
        var names = new java.util.HashSet<String>(); value.fieldNames().forEachRemaining(names::add); return Set.copyOf(names);
    }
    private static String text(ObjectNode row, String key) { return StrictJson.text(row.get(key)); }
    private static BigInteger positive(ObjectNode row, String key) {
        BigInteger value = new BigInteger(new CrossJsDecimalUInt64(text(row, key)).decimal()); FrontendFrame.positive(value); return value;
    }
    private static String decimal(BigInteger value) { return new CrossJsDecimalUInt64(value.toString()).decimal(); }
    /** v1 durable actor fields remain canonical decimal strings; public native actor JSON remains integer-only. */
    private static String characterDecimal(BigInteger value) { return NativeCharacterId.of(value).asBigInteger().toString(); }
    private static BigInteger characterValue(ObjectNode row,String key) {
        String raw=text(row,key);BigInteger value=new BigInteger(raw);
        StrictJson.require(value.toString().equals(raw),"canonical signed native character decimal required");
        return NativeCharacterId.of(value).asBigInteger();
    }
    private static boolean bool(ObjectNode row, String key) { var node = row.get(key); StrictJson.require(node != null && node.isBoolean(), "actual native boolean required"); return node.booleanValue(); }
}
