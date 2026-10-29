package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatJson.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.military.combatwire.CombatEncounterScope;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputs;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputs;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec;

/**
 * Native-driver combat-query result acceptance and same-frame cache projection.
 * The caller supplies an actual read-authority receipt and its two real semantic
 * snapshots. This class grants model-input scope only; it cannot grant native
 * source custody, submission, restoration, or transition-fidelity qualification.
 * All JSON here is the private Java/original numeric domain. The one external
 * protocol encoder must encode identity/sequence/time fields before JavaScript.
 */
public final class CombatObservationCache {
    private static final BigInteger U64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final BigInteger I64_MIN = BigInteger.ONE.shiftLeft(63).negate();
    private static final BigInteger I64_MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    public enum Version { V2, V3 }
    public enum Status {
        AVAILABLE("available"), PARTIAL("partial"), UNAVAILABLE("unavailable");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        private static Status read(JsonNode value) {
            String raw = text(value, "combat query status");
            for (Status status : values()) if (status.wire.equals(raw)) return status;
            throw new CombatInputException("unknown combat query status");
        }
    }

    /** Exact Java memory identity; explicit null episode differs from missing JSON. */
    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision,
            BigInteger connectionGeneration, String episodeRunId, BigInteger dateRaw) {
        public Frame {
            require(snapshotId != null && !snapshotId.isBlank(), "snapshot_id must be nonblank");
            unsigned64(revision, false, "revision"); unsigned64(nativeRevision, false, "native_revision");
            unsigned64(connectionGeneration, false, "connection_generation");
            require(episodeRunId == null || !episodeRunId.isBlank(), "episode_run_id must be null or nonblank");
            require(dateRaw != null && dateRaw.compareTo(I64_MIN) >= 0 && dateRaw.compareTo(I64_MAX) <= 0, "date_raw must be signed64");
        }
        public static Frame decode(JsonNode value) {
            ObjectNode snapshot = object(value, "combat source snapshot");
            require(yes(snapshot.get("paused")), "combat query requires paused source snapshot");
            ObjectNode diagnostics = object(snapshot.get("diagnostics"), "combat source diagnostics");
            JsonNode episode = snapshot.get("episode_run_id");
            require(episode != null && (episode.isNull() || episode.isTextual()), "episode_run_id must be present as string/null");
            return new Frame(text(snapshot.get("snapshot_id"), "snapshot_id"), integer(snapshot.get("revision"), "revision"),
                    integer(snapshot.get("native_revision"), "native_revision"), integer(diagnostics.get("connection_generation"), "connection_generation"),
                    episode.isNull() ? null : episode.textValue(), integer(snapshot.get("date_raw"), "date_raw"));
        }
        public CombatInputs.Capture capture() {
            ObjectNode row = object().put("snapshot_id", snapshotId).put("revision", revision).put("native_revision", nativeRevision).put("date_raw", dateRaw);
            return new CombatInputs.Capture(row);
        }
        public ObjectNode toInternalJson() {
            ObjectNode row = capture().source().put("connection_generation", connectionGeneration);
            if (episodeRunId == null) row.putNull("episode_run_id"); else row.put("episode_run_id", episodeRunId);
            return row;
        }
    }

    public sealed interface Observation permits V2Observation, V3Observation {
        Version version(); Status status(); Frame frame(); CombatRequest request(); CombatEncounterScope scope();
        BigInteger querySequence(); ObjectNode normalizedJson();
        default CombatInputs.Capture capture() { return frame().capture(); }
        default FixedContactForecast.Forecast forecast(int sampleCount, int horizonDays) {
            CombatRequest request = request();
            FixedContactForecast.Request model = new FixedContactForecast.Request(BigInteger.valueOf(request.targetProvinceId()),
                    request.attackerEntryProvinceId() == null ? null : BigInteger.valueOf(request.attackerEntryProvinceId()),
                    bigIds(request.attackerArmyIds()), bigIds(request.defenderArmyIds()), capture(), sampleCount, horizonDays);
            if (this instanceof V2Observation v2) return FixedContactForecast.forecast(v2.inputs(), model);
            if (this instanceof V3Observation v3) return FixedContactForecast.forecast(v3.inputs(), model);
            throw new IllegalStateException("unhandled combat observation version");
        }
        /** Original driver's private projection shape, including original exact integer domain. */
        default ObjectNode toInternalJson() {
            ObjectNode row = object().put("status", status().wire()).put("query_sequence", querySequence()).put("target_province_id", request().targetProvinceId());
            row.set("combat_simulation_inputs", normalizedJson());
            if (request().attackerEntryProvinceId() == null) row.putNull("attacker_entry_province_id"); else row.put("attacker_entry_province_id", request().attackerEntryProvinceId());
            var attackers = row.putArray("attacker_army_ids"); request().attackerArmyIds().forEach(attackers::add);
            var defenders = row.putArray("defender_army_ids"); request().defenderArmyIds().forEach(defenders::add);
            row.put("queried_snapshot_id", frame().snapshotId()).put("queried_revision", frame().revision()).put("queried_native_revision", frame().nativeRevision());
            if (frame().episodeRunId() == null) row.putNull("episode_run_id"); else row.put("episode_run_id", frame().episodeRunId());
            return row;
        }
    }

    public static final class V2Observation implements Observation {
        private final Frame frame; private final CombatRequest request; private final CombatEncounterScope scope;
        private final BigInteger sequence; private final CombatSimulationInputs inputs;
        private V2Observation(Frame frame, CombatRequest request, CombatEncounterScope scope, BigInteger sequence, CombatSimulationInputs inputs) {
            this.frame = frame; this.request = request; this.scope = scope; this.sequence = sequence; this.inputs = inputs;
        }
        @Override public Version version() { return Version.V2; }
        @Override public Status status() { return inputs.completeness().inputObservationReady() ? Status.AVAILABLE : Status.PARTIAL; }
        @Override public Frame frame() { return frame; }
        @Override public CombatRequest request() { return request; }
        @Override public CombatEncounterScope scope() { return scope; }
        @Override public BigInteger querySequence() { return sequence; }
        public CombatSimulationInputs inputs() { return inputs; }
        @Override public ObjectNode normalizedJson() { return inputs.toJson(); }
    }
    public static final class V3Observation implements Observation {
        private final Frame frame; private final CombatRequest request; private final CombatEncounterScope scope;
        private final BigInteger sequence; private final CombatPhaseInputs inputs;
        private V3Observation(Frame frame, CombatRequest request, CombatEncounterScope scope, BigInteger sequence, CombatPhaseInputs inputs) {
            this.frame = frame; this.request = request; this.scope = scope; this.sequence = sequence; this.inputs = inputs;
        }
        @Override public Version version() { return Version.V3; }
        @Override public Status status() { return inputs.completeness().inputObservationReady() ? Status.AVAILABLE : Status.UNAVAILABLE; }
        @Override public Frame frame() { return frame; }
        @Override public CombatRequest request() { return request; }
        @Override public CombatEncounterScope scope() { return scope; }
        @Override public BigInteger querySequence() { return sequence; }
        public CombatPhaseInputs inputs() { return inputs; }
        @Override public ObjectNode normalizedJson() { return inputs.toJson(); }
    }

    private final CombatSimulationInputsCodec v2Codec;
    private final CombatPhaseInputsCodec v3Codec;
    private V2Observation v2;
    private V3Observation v3;
    public CombatObservationCache(CombatSimulationInputsCodec v2Codec, CombatPhaseInputsCodec v3Codec) {
        this.v2Codec = Objects.requireNonNull(v2Codec); this.v3Codec = Objects.requireNonNull(v3Codec);
    }

    /** No native query is sent here. Read authority owns actual request and receipt custody. */
    public synchronized Observation receive(Version version, JsonNode receipt, JsonNode starting, JsonNode ending,
            CombatRequest request, BigInteger expectedRevisionOrNull) {
        Observation observation = replay(version, receipt, starting, ending, request, expectedRevisionOrNull);
        if (observation instanceof V2Observation observed) v2 = observed;
        else if (observation instanceof V3Observation observed) v3 = observed;
        return observation;
    }

    /** Pure receipt revalidation for Known-read publication and history replay. No cache slot is read or written. */
    public synchronized Observation replay(Version version, JsonNode receipt, JsonNode starting, JsonNode ending,
            CombatRequest request, BigInteger expectedRevisionOrNull) {
        Objects.requireNonNull(version); Objects.requireNonNull(request);
        ObjectNode before = object(starting, "starting snapshot").deepCopy();
        ObjectNode after = object(ending, "ending snapshot").deepCopy();
        Frame start = Frame.decode(before), end = Frame.decode(after);
        if (expectedRevisionOrNull != null) {
            unsigned64(expectedRevisionOrNull, false, "expected_revision");
            require(start.revision().equals(expectedRevisionOrNull), "query expected revision differs from starting frame");
        }
        require(start.equals(end), "combat query crossed paused source frame");
        CombatEncounterScope scope = CombatEncounterScope.fromSnapshot(before, request);
        require(scope.equals(CombatEncounterScope.fromSnapshot(after, request)), "combat encounter scope changed during query");
        ObjectNode raw = object(receipt, "combat native receipt").deepCopy();
        CombatNativeEnvelope.validate(raw, CombatNativeEnvelope.Payload.COMBAT_INPUTS);
        String step = version == Version.V2 ? request.toStep() : CombatPhaseInputsCodec.toStep(request);
        require(is(raw.get("step"), step) && yes(raw.get("accepted")), "native receipt step/accepted mismatch");
        Status status = Status.read(raw.get("status"));
        require(version == Version.V2 ? status != Status.UNAVAILABLE : status != Status.PARTIAL, "status is outside query version");
        BigInteger sequence = unsigned64(integer(raw.get("query_sequence"), "query_sequence"), true, "query_sequence");
        Observation observation = normalize(version, raw.get("combat_simulation_inputs"), start, request, scope, sequence);
        require(observation.status() == status, "native status differs from complete normalized input readiness");
        return observation;
    }

    /** Unpaused snapshots return no projection without consuming the paused cache. */
    public synchronized Optional<V2Observation> projectV2(JsonNode snapshot, String episodeRunId) {
        if (!yes(field(snapshot, "paused")) || v2 == null) return Optional.empty();
        try {
            Observation projected = project(v2, snapshot, episodeRunId);
            if (projected instanceof V2Observation observed) return Optional.of(observed);
        } catch (IllegalArgumentException failure) { v2 = null; return Optional.empty(); }
        throw new IllegalStateException("v2 projection changed version");
    }
    public synchronized Optional<V3Observation> projectV3(JsonNode snapshot, String episodeRunId) {
        if (!yes(field(snapshot, "paused")) || v3 == null) return Optional.empty();
        try {
            Observation projected = project(v3, snapshot, episodeRunId);
            if (projected instanceof V3Observation observed) return Optional.of(observed);
        } catch (IllegalArgumentException failure) { v3 = null; return Optional.empty(); }
        throw new IllegalStateException("v3 projection changed version");
    }
    private Observation project(Observation previous, JsonNode snapshot, String episodeRunId) {
        ObjectNode current = object(snapshot, "projection snapshot").deepCopy();
        Frame frame = Frame.decode(current);
        require(Objects.equals(frame.episodeRunId(), episodeRunId), "projection episode argument differs from snapshot");
        // Identity rejection precedes scope/body normalization, including on reconnect.
        require(previous.frame().equals(frame), "cached combat input belongs to another source frame");
        CombatEncounterScope scope = CombatEncounterScope.fromSnapshot(current, previous.request());
        require(previous.scope().equals(scope), "cached combat encounter scope changed");
        Observation result = normalize(previous.version(), previous.normalizedJson(), frame, previous.request(), scope, previous.querySequence());
        require(result.status() == previous.status(), "cached combat input status changed on revalidation");
        return result;
    }
    private Observation normalize(Version version, JsonNode body, Frame frame, CombatRequest request,
            CombatEncounterScope scope, BigInteger sequence) {
        if (version == Version.V2) return new V2Observation(frame, request, scope, sequence, v2Codec.normalize(body, request, scope));
        return new V3Observation(frame, request, scope, sequence, v3Codec.normalize(body, request, scope));
    }
    /** Disconnect/new episode/restore callers invalidate both versions atomically. */
    public synchronized void clear() { v2 = null; v3 = null; }
    private static List<BigInteger> bigIds(List<Integer> values) { return values.stream().map(BigInteger::valueOf).toList(); }
    private static BigInteger unsigned64(BigInteger value, boolean positive, String name) {
        require(value != null && value.signum() >= (positive ? 1 : 0) && value.compareTo(U64_MAX) <= 0, name + " outside unsigned64 domain"); return value;
    }
}
