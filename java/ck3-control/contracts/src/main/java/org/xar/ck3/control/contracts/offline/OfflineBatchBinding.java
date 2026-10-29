package org.xar.ck3.control.contracts.offline;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Versioned offline scan identity. It preserves the actual source messages, without inventing a control sequence. */
public final class OfflineBatchBinding {
    public static final String MANIFEST_V3 = "xar.offline-episode-incident-batch/v3";
    public static final String REPORT_V3 = "xar.vanilla-event-offline-source-batch/v3";
    public static final String MANIFEST_V2 = "xar.offline-episode-incident-batch/v2";
    public static final String REPORT_V1 = "xar.vanilla-event-offline-source-batch/v1";
    public static final String REPORT_V2 = "xar.vanilla-event-offline-source-batch/v2";
    private OfflineBatchBinding() { }
    public sealed interface Binding permits LegacyCompleted, ObservedScan { }
    public record LegacyCompleted(BigInteger completedControlSequence) implements Binding {
        public LegacyCompleted {
            Objects.requireNonNull(completedControlSequence);
            StrictJson.require(completedControlSequence.signum() >= 0, "Original nonnegative completed control sequence required");
        }
    }
    /** Versioned actor domain only. Native revisions, dates and all other identities remain unsigned64. */
    public sealed interface FrameActor permits LegacyUnsignedActor, NativeObservedActor {
        String decimal();
        JsonNode toJson();
    }
    public record LegacyUnsignedActor(CrossJsDecimalUInt64 original) implements FrameActor {
        public LegacyUnsignedActor { positive(original); }
        @Override public String decimal() { return original.decimal(); }
        @Override public JsonNode toJson() { return com.fasterxml.jackson.databind.node.TextNode.valueOf(decimal()); }
    }
    public record NativeObservedActor(NativeCharacterId original) implements FrameActor {
        public NativeObservedActor { Objects.requireNonNull(original); }
        @Override public String decimal() { return original.asBigInteger().toString(); }
        @Override public JsonNode toJson() { return original.toJson(); }
    }
    public record Frame(FrameActor playedCharacterId, CrossJsDecimalUInt64 nativeRevision,
            CrossJsDecimalUInt64 dateRaw, String snapshotId, CrossJsDecimalUInt64 revision, String episodeRunId) {
        public Frame {
            Objects.requireNonNull(playedCharacterId); positive(nativeRevision); Objects.requireNonNull(dateRaw); positive(revision);
            bounded(snapshotId); bounded(episodeRunId);
        }
        /** Original v2 constructor preserves its positive decimal-unsigned64 domain exactly. */
        public Frame(CrossJsDecimalUInt64 actor,CrossJsDecimalUInt64 nativeRevision,CrossJsDecimalUInt64 dateRaw,
                String snapshotId,CrossJsDecimalUInt64 revision,String episodeRunId) {
            this(new LegacyUnsignedActor(actor),nativeRevision,dateRaw,snapshotId,revision,episodeRunId);
        }
        /** Actual public scan producer supplies the shared native signed-i32 identity; no sign conversion. */
        public Frame(NativeCharacterId actor,CrossJsDecimalUInt64 nativeRevision,CrossJsDecimalUInt64 dateRaw,
                String snapshotId,CrossJsDecimalUInt64 revision,String episodeRunId) {
            this(new NativeObservedActor(actor),nativeRevision,dateRaw,snapshotId,revision,episodeRunId);
        }
        public ObjectNode toJson() {
            ObjectNode value = StrictJson.object(); value.set("played_character_id", playedCharacterId.toJson());
            value.put("native_revision", nativeRevision.decimal()); value.put("date_raw", dateRaw.decimal());
            value.put("snapshot_id", snapshotId); value.put("revision", revision.decimal()); value.put("episode_run_id", episodeRunId); return value;
        }
    }
    public record Observation(String machineId, GameGeneration game, long observationVersion, Frame frame) {
        public Observation {
            machine(machineId); Objects.requireNonNull(game); Objects.requireNonNull(frame);
            StrictJson.require(observationVersion >= 1 && observationVersion <= StrictJson.MAX_SAFE_INTEGER, "Exact observation version required");
        }
        public ObjectNode toJson() {
            ObjectNode value = StrictJson.object(); value.put("machine_id", machineId); value.set("game", game.toJson());
            value.put("observation_version", observationVersion); value.set("frame", frame.toJson()); return value;
        }
    }
    public record Source(String machineId, String observedAtUtc, String exactBuild, ExactRef sourceRef) {
        public Source { machine(machineId); StrictJson.utc(observedAtUtc); bounded(exactBuild); Objects.requireNonNull(sourceRef); }
        public ObjectNode toJson() {
            ObjectNode value = StrictJson.object(); value.put("machine_id", machineId); value.put("observed_at_utc", observedAtUtc);
            value.put("exact_build", exactBuild); value.set("source_ref", sourceRef.toJson()); return value;
        }
    }
    public record ObservedScan(String sessionId, Observation observation, Source source, ExactRef indexRef) implements Binding {
        public ObservedScan {
            bounded(sessionId); Objects.requireNonNull(observation); Objects.requireNonNull(source); Objects.requireNonNull(indexRef);
            StrictJson.require(observation.machineId().equals(source.machineId()), "Actual scan observation and source machines differ");
        }
    }

    public static Binding manifest(JsonNode value) {
        ObjectNode row = object(value);
        if (row.path("schema").isTextual() && (MANIFEST_V2.equals(row.path("schema").textValue()) || MANIFEST_V3.equals(row.path("schema").textValue()))) {
            StrictJson.object(row, Set.of("schema", "session_id", "scan_observation", "scan_source", "index_ref", "new_incidents"));
            boundedIncidents(row.get("new_incidents"));
            return new ObservedScan(text(row, "session_id"), observation(row.get("scan_observation"), MANIFEST_V3.equals(row.path("schema").textValue())), source(row.get("scan_source")), ExactRef.fromJson(row.get("index_ref")));
        }
        // Historical v1 was emitted without an envelope schema. Never reinterpret a v2/v3 document as that record.
        StrictJson.require(!row.has("schema") || row.path("schema").isTextual() && "xar.offline-episode-incident-batch/v1".equals(row.path("schema").textValue()), "Unsupported offline incident manifest version");
        StrictJson.require(!row.has("scan_observation") && !row.has("scan_source") && !row.has("index_ref") && !row.has("session_id"), "Legacy sequence cannot stand in for an actual scan");
        JsonNode sequence = row.get("completed_control_sequence");
        StrictJson.require(sequence != null && sequence.isIntegralNumber() && sequence.bigIntegerValue().signum() >= 0, "Original completed control sequence required for legacy v1 only");
        boundedIncidents(row.get("new_incidents")); return new LegacyCompleted(sequence.bigIntegerValue());
    }

    public static Observation observation(JsonNode value) { return observation(value,false); }
    public static Observation nativeObservation(JsonNode value) { return observation(value,true); }
    private static Observation observation(JsonNode value,boolean nativeActor) {
        ObjectNode row = StrictJson.object(value, Set.of("machine_id", "game", "observation_version", "frame"));
        ObjectNode frame = StrictJson.object(row.get("frame"), Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id"));
        return new Observation(text(row, "machine_id"), GameGeneration.fromJson(row.get("game")),
                StrictJson.integer(row.get("observation_version"), 1, StrictJson.MAX_SAFE_INTEGER),
                new Frame(nativeActor ? new NativeObservedActor(NativeCharacterId.fromJson(frame.get("played_character_id"))) : new LegacyUnsignedActor(decimal(frame, "played_character_id")), decimal(frame, "native_revision"), decimal(frame, "date_raw"),
                        text(frame, "snapshot_id"), decimal(frame, "revision"), text(frame, "episode_run_id")));
    }
    public static Source source(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("machine_id", "observed_at_utc", "exact_build", "source_ref"));
        return new Source(text(row, "machine_id"), text(row, "observed_at_utc"), text(row, "exact_build"), ExactRef.fromJson(row.get("source_ref")));
    }

    /** Exact report-to-original identity check, also used before an incident journal accepts completion. */
    public static void requireReport(JsonNode report, Binding original, ExactRef manifest) {
        ObjectNode row = object(report);
        StrictJson.require(row.path("manifest").isObject(), "Source-bound report manifest required");
        ObjectNode ref = object(row.get("manifest"));
        StrictJson.require(manifest.path().equals(text(ref, "path")) && manifest.sha256().equals(text(ref, "sha256")), "Report changed its actual manifest source");
        if (original instanceof ObservedScan actual) {
            StrictJson.require(reportSchema(actual).equals(text(row, "schema")) && !row.has("completed_control_sequence")
                    && actual.sessionId().equals(text(row, "session_id"))
                    && actual.observation().equals(observationForReport(row))
                    && actual.source().equals(source(row.get("scan_source")))
                    && actual.indexRef().equals(ExactRef.fromJson(row.get("index_ref")))
                    && manifest.equals(ExactRef.fromJson(ref)) && actual.observation().machineId().equals(text(row, "machine_id")), "Report crossed its actual source-bound scan");
        } else {
            LegacyCompleted legacy = (LegacyCompleted) original;
            StrictJson.require(REPORT_V1.equals(text(row, "schema")) && row.path("completed_control_sequence").isIntegralNumber()
                    && legacy.completedControlSequence().equals(row.path("completed_control_sequence").bigIntegerValue())
                    && !row.has("scan_observation") && !row.has("scan_source"), "Legacy report changed its original completed sequence");
        }
    }
    public static void addReportBinding(ObjectNode report, Binding binding) {
        if (binding instanceof ObservedScan actual) {
            report.put("schema", reportSchema(actual)); report.put("session_id", actual.sessionId());
            report.set("scan_observation", actual.observation().toJson()); report.set("scan_source", actual.source().toJson()); report.set("index_ref", actual.indexRef().toJson());
        } else {
            report.put("schema", REPORT_V1); report.put("completed_control_sequence", ((LegacyCompleted) binding).completedControlSequence());
        }
    }
    public static String manifestSchema(Binding binding) {
        Objects.requireNonNull(binding);
        return binding instanceof ObservedScan actual ? nativeActor(actual) ? MANIFEST_V3 : MANIFEST_V2 : "xar.offline-episode-incident-batch/v1";
    }
    public static String reportSchema(Binding binding) {
        Objects.requireNonNull(binding);
        return binding instanceof ObservedScan actual ? nativeActor(actual) ? REPORT_V3 : REPORT_V2 : REPORT_V1;
    }
    /** Select by the explicit report version, never by token sign/type or a fallback alias. */
    public static Observation observationForReport(JsonNode report) {
        ObjectNode row=object(report);String schema=text(row,"schema");
        StrictJson.require(REPORT_V2.equals(schema)||REPORT_V3.equals(schema),"Versioned observed report required");
        return observation(row.get("scan_observation"),REPORT_V3.equals(schema));
    }
    private static boolean nativeActor(ObservedScan actual) {
        return actual.observation().frame().playedCharacterId() instanceof NativeObservedActor;
    }
    private static void boundedIncidents(JsonNode value) { StrictJson.require(value != null && value.isArray() && value.size() <= 256, "Finite original incident array required"); }
    private static CrossJsDecimalUInt64 decimal(ObjectNode row, String field) { return new CrossJsDecimalUInt64(text(row, field)); }
    private static void positive(CrossJsDecimalUInt64 value) { Objects.requireNonNull(value); StrictJson.require(!value.decimal().equals("0"), "Positive original frame identity required"); }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "Original offline object required"); return (ObjectNode)value;
    }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static void machine(String value) { StrictJson.require(value != null && !value.equals("unknown") && value.matches("[a-z0-9][a-z0-9-]{0,63}"), "Explicit source machine required"); }
    private static void bounded(String value) { StrictJson.text(value); StrictJson.require(value.length() <= 4096, "Bounded original scan field required"); }
}
