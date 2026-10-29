package org.xar.ck3.control.wave2.military.disembark;

import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.military.disembark.DisembarkPenalty.Available;
import org.xar.ck3.control.wave2.military.disembark.DisembarkPenalty.Observation;
import org.xar.ck3.control.wave2.military.disembark.DisembarkPenalty.Projection;
import org.xar.ck3.control.wave2.military.disembark.DisembarkPenalty.SourceProvenance;
import org.xar.ck3.control.wave2.military.disembark.DisembarkPenalty.Unavailable;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.BooleanValue;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.IntegerValue;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.NullValue;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.ObjectValue;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.TextValue;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson.Value;
import static org.xar.ck3.control.wave2.military.disembark.EvidenceJson.member;
import static org.xar.ck3.control.wave2.military.disembark.EvidenceJson.object;
import static org.xar.ck3.control.wave2.military.disembark.EvidenceJson.text;

/** Complete leaf codec and declared projection seams for existing SDK containers. */
public final class DisembarkCodec {
    private static final Set<String> FIELDS = Set.of("schema_version", "source", "status", "remaining_days", "unavailable_reason");
    private DisembarkCodec() { }

    public static Observation normalize(byte[] bytes) { return normalize(EvidenceJson.parse(bytes)); }

    public static Observation normalize(Value value) {
        ObjectValue leaf = object(value); leaf.exactFields(FIELDS);
        if (!(leaf.required("schema_version") instanceof IntegerValue version) || !version.value().equals(java.math.BigInteger.ONE)) {
            throw new IllegalArgumentException("native disembark schema version must be exact integer 1");
        }
        if (!DisembarkPenalty.SOURCE.equals(string(leaf.required("source")))) { throw new IllegalArgumentException("native disembark source drift"); }
        String status = string(leaf.required("status"));
        Value days = leaf.required("remaining_days"); Value reason = leaf.required("unavailable_reason");
        if (status.equals("available")) {
            if (!(days instanceof IntegerValue integer) || reason != NullValue.INSTANCE) {
                throw new IllegalArgumentException("available disembark requires signed int32 observation and null reason");
            }
            try { return new Available(integer.value().intValueExact()); }
            catch (ArithmeticException error) { throw new IllegalArgumentException("native disembark days outside signed int32", error); }
        }
        if (status.equals("unavailable")) {
            if (days != NullValue.INSTANCE) { throw new IllegalArgumentException("unavailable disembark requires null days"); }
            return new Unavailable(string(reason));
        }
        throw new IllegalArgumentException("native disembark status malformed");
    }

    /** Explicit null raw denotes project(None), while normalize(null) remains invalid. */
    public static Projection decodeProjectionRequest(byte[] bytes) {
        ObjectValue request = object(EvidenceJson.parse(bytes)); request.exactFields(Set.of("raw", "source_provenance"));
        Value raw = request.required("raw");
        Optional<Observation> observation = raw == NullValue.INSTANCE ? Optional.empty() : Optional.of(normalize(raw));
        return DisembarkPenalty.project(observation, new SourceProvenance(object(request.required("source_provenance"))));
    }

    /** Called after the existing whole-row validator. Extra SDK fields remain outside this leaf's authority. */
    public static Optional<Observation> normalizeRowProjection(Value value) {
        ObjectValue row = object(value); Optional<Value> raw = row.member(DisembarkPenalty.LEAF);
        if (raw.isEmpty()) { return Optional.empty(); }
        if (!string(row.required("status")).equals("available")) {
            throw new IllegalArgumentException("native unavailable army cannot publish current disembark leaf");
        }
        return Optional.of(normalize(raw.orElseThrow()));
    }

    /** The real service creates the provenance from one held snapshot and its hello; no independent query is performed. */
    public static SourceProvenance sourceFromSnapshot(Value snapshotValue, Value helloValue) {
        ObjectValue snapshot = object(snapshotValue);
        ObjectValue hello = helloValue instanceof ObjectValue object ? object : new ObjectValue(List.of());
        return new SourceProvenance(object(
                member("snapshot_id", get(snapshot, "snapshot_id")), member("revision", get(snapshot, "revision")),
                member("native_revision", get(snapshot, "native_revision")), member("date_raw", get(snapshot, "date_raw")),
                member("game_version", get(hello, "game_version")), member("executable_sha256", get(hello, "executable_sha256"))));
    }

    /** Exact service row output. The enclosing service still owns whole-row and paused-scope qualification. */
    public static ObjectValue projectServiceRow(Value rowValue, SourceProvenance sameHeldSnapshot) {
        ObjectValue row = object(rowValue);
        Value id = row.required("army_id");
        if (!(id instanceof IntegerValue integer) || integer.value().signum() < 0
                || integer.value().compareTo(java.math.BigInteger.valueOf(Integer.MAX_VALUE)) > 0) {
            throw new IllegalArgumentException("declared public CUnit ID must be exact nonnegative int32");
        }
        Projection projection = DisembarkPenalty.project(normalizeRowProjection(row), sameHeldSnapshot);
        return object(member("army_id", id), member("projection", projectionValue(projection)));
    }

    public static byte[] encodeObservation(Observation observation) { return EvidenceJson.encode(observationValue(observation)); }
    public static ObjectValue observationValue(Observation observation) {
        Value days = observation instanceof Available available ? EvidenceJson.integer(available.remainingDays()) : NullValue.INSTANCE;
        Value reason = observation instanceof Unavailable unavailable ? text(unavailable.reason()) : NullValue.INSTANCE;
        return object(member("schema_version", EvidenceJson.integer(1)), member("source", text(DisembarkPenalty.SOURCE)),
                member("status", text(observation instanceof Available ? "available" : "unavailable")),
                member("remaining_days", days), member("unavailable_reason", reason));
    }
    public static byte[] encodeProjection(Projection projection) { return EvidenceJson.encode(projectionValue(projection)); }
    public static ObjectValue projectionValue(Projection projection) {
        return object(member("schema_version", EvidenceJson.integer(1)), member("source", text(DisembarkPenalty.PROJECTION_SOURCE)),
                member("status", text(projection.currentDaysReady() ? "available" : "unavailable")),
                member("current_disembark_days_ready", new BooleanValue(projection.currentDaysReady())),
                member("remaining_days", projection.remainingDays().<Value>map(EvidenceJson::integer).orElse(NullValue.INSTANCE)),
                member("unavailable_reason", projection.unavailableReason().<Value>map(EvidenceJson::text).orElse(NullValue.INSTANCE)),
                member("source_provenance", projection.sourceProvenance().document()),
                member("observed_current_disembark_penalty", projection.observed().<Value>map(DisembarkCodec::observationValue).orElse(NullValue.INSTANCE)),
                member("future_route_landing_days_ready", new BooleanValue(false)));
    }
    private static Value get(ObjectValue object, String key) { return object.member(key).orElse(NullValue.INSTANCE); }
    private static String string(Value value) {
        if (value instanceof TextValue text) { return text.value(); }
        throw new IllegalArgumentException("exact JSON string required");
    }
}
