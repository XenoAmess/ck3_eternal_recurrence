package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.RootPublicStepExecution;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original public argument names and presence; this codec grants no Native or action authority. */
public final class PublicPlanningCodec {
    public static final String H2743_STEP = "query-h2743-preaction-existing-truce-v1";
    private static final Set<String> FRAME_FIELDS = Set.of("snapshot_id", "revision", "native_revision", "date_raw",
            "actor_character_id", "episode_run_id", "war_id", "connection_generation");
    private PublicPlanningCodec() { }
    public record PlanRequest() { }
    public sealed interface Revision permits RevisionMissing, RevisionNull, RevisionValue { }
    public record RevisionMissing() implements Revision { }
    public record RevisionNull() implements Revision { }
    public record RevisionValue(BigInteger value) implements Revision {
        public RevisionValue { nonnegativeUint64(value); }
    }
    public sealed interface Frame permits FrameMissing, FrameNull, FrameValue { }
    public record FrameMissing() implements Frame { }
    public record FrameNull() implements Frame { }
    public record FrameValue(H2743Frame value) implements Frame {
        public FrameValue { Objects.requireNonNull(value); }
    }
    public record H2743Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision, long dateRaw,
            long actorCharacterId, String episodeRunId, long warId, BigInteger connectionGeneration) {
        public H2743Frame {
            StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            uint64(revision); uint64(nativeRevision); uint64(connectionGeneration);
            StrictJson.require(dateRaw >= 0 && dateRaw <= Integer.MAX_VALUE && actorCharacterId >= 0
                    && actorCharacterId < 0xffff_ffffL && warId >= 0 && warId < 0xffff_ffffL,
                    "bounded original H2743 frame integers required");
        }
    }
    public record ExecuteRequest(OperationKey step, Revision expectedRevision, Frame expectedH2743Frame) {
        public ExecuteRequest {
            Objects.requireNonNull(step); Objects.requireNonNull(expectedRevision); Objects.requireNonNull(expectedH2743Frame);
            boolean special = H2743_STEP.equals(step.value());
            if(expectedH2743Frame instanceof FrameValue&&!special
                    ||special&&!(expectedRevision instanceof RevisionValue&&expectedH2743Frame instanceof FrameValue))
                throw h2743ClaimRequired();
        }
        public boolean h2743() { return H2743_STEP.equals(step.value()); }
        public void requireCurrent(PlanningRequest original) {
            Objects.requireNonNull(original);
            if (expectedRevision instanceof RevisionValue value)
                StrictJson.require(value.value().equals(original.before().frame().revision()), "public expected_revision is stale");
            if (expectedH2743Frame instanceof FrameValue value) requireH2743Current(value.value(), original);
        }
    }
    public static PlanRequest decodePlan(PublicBindings.Arguments original) {
        Objects.requireNonNull(original);
        if (original instanceof PublicBindings.Missing) return new PlanRequest();
        StrictJson.object(object(original), Set.of()); return new PlanRequest();
    }
    public static ExecuteRequest decodeExecute(PublicBindings.Arguments original) {
        ObjectNode row = object(original);
        var names = new java.util.HashSet<String>(); row.properties().forEach(entry -> names.add(entry.getKey()));
        StrictJson.require(names.contains("step") && Set.of("step", "expected_revision", "expected_h2743_frame").containsAll(names),
                "exact original execute_step fields required");
        String step=StrictJson.text(row.get("step"));
        // Match the original Service's explicit H2743 preflight before a reader can run.
        // The public wire additionally admits canonical decimal uint64 strings.
        boolean h2743=H2743_STEP.equals(step);
        boolean frameClaim=row.hasNonNull("expected_h2743_frame");
        // The original Service excludes these typed facades before its H2743 branch.
        if(frameClaim)RootPublicStepExecution.requireGenericFacade(new OperationKey(step));
        if(h2743||frameClaim) {
            JsonNode rawRevision=row.get("expected_revision");
            if(!h2743||rawRevision==null||rawRevision.isNull()||!frameClaim
                    ||!(rawRevision.isIntegralNumber()||rawRevision.isTextual()))
                throw h2743ClaimRequired();
        }
        Revision revision = !row.has("expected_revision") ? new RevisionMissing()
                : row.get("expected_revision").isNull() ? new RevisionNull()
                : new RevisionValue(PublicUnsigned64.parse(row.get("expected_revision"), PublicUnsigned64.Minimum.ZERO,
                        PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL));
        Frame frame = !row.has("expected_h2743_frame") ? new FrameMissing()
                : row.get("expected_h2743_frame").isNull() ? new FrameNull()
                : new FrameValue(frame(row.get("expected_h2743_frame")));
        return new ExecuteRequest(new OperationKey(step), revision, frame);
    }
    public static RawJson encodeExecute(ExecuteRequest request) {
        Objects.requireNonNull(request); ObjectNode row = StrictJson.object(); row.put("step", request.step().value());
        if (request.expectedRevision() instanceof RevisionNull) row.putNull("expected_revision");
        else if (request.expectedRevision() instanceof RevisionValue value) row.put("expected_revision", PublicUnsigned64.canonical(value.value(), PublicUnsigned64.Minimum.ZERO));
        if (request.expectedH2743Frame() instanceof FrameNull) row.putNull("expected_h2743_frame");
        else if (request.expectedH2743Frame() instanceof FrameValue value) row.set("expected_h2743_frame", encodeFrame(value.value()));
        return new RawJson(StrictJson.canonical(row));
    }
    private static PublicServiceFailure h2743ClaimRequired() {
        return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                "H2743 read-only query requires an explicit before-frame claim", Optional.empty());
    }
    private static ObjectNode object(PublicBindings.Arguments original) {
        StrictJson.require(original instanceof PublicBindings.Value, "present non-null public argument object required");
        JsonNode parsed = StrictJson.parse(((PublicBindings.Value) original).original().bytes());
        StrictJson.require(parsed.isObject(), "public arguments must be an object"); return (ObjectNode) parsed;
    }
    private static H2743Frame frame(JsonNode value) {
        ObjectNode row = StrictJson.object(value, FRAME_FIELDS);
        return new H2743Frame(StrictJson.text(row.get("snapshot_id")), integer(row.get("revision")), integer(row.get("native_revision")),
                StrictJson.integer(row.get("date_raw"), 0, Integer.MAX_VALUE), StrictJson.integer(row.get("actor_character_id"), 0, 0xffff_fffeL),
                StrictJson.text(row.get("episode_run_id")), StrictJson.integer(row.get("war_id"), 0, 0xffff_fffeL), integer(row.get("connection_generation")));
    }
    private static ObjectNode encodeFrame(H2743Frame value) {
        ObjectNode row = StrictJson.object(); row.put("snapshot_id", value.snapshotId()); row.put("revision", PublicUnsigned64.canonical(value.revision(), PublicUnsigned64.Minimum.ONE));
        row.put("native_revision", PublicUnsigned64.canonical(value.nativeRevision(), PublicUnsigned64.Minimum.ONE)); row.put("date_raw", value.dateRaw()); row.put("actor_character_id", value.actorCharacterId());
        row.put("episode_run_id", value.episodeRunId()); row.put("war_id", value.warId()); row.put("connection_generation", PublicUnsigned64.canonical(value.connectionGeneration(), PublicUnsigned64.Minimum.ONE)); return row;
    }
    private static void requireH2743Current(H2743Frame claim, PlanningRequest original) {
        ObjectNode actual = (ObjectNode) OpportunityJson.toNode(original.observations().snapshot());
        StrictJson.require(actual.path("paused").isBoolean() && actual.path("paused").booleanValue()
                && actual.path("map_ready").isBoolean() && actual.path("map_ready").booleanValue(), "H2743 requires original paused map-ready frame");
        JsonNode played = actual.get("played_character");
        StrictJson.require(played != null && played.isObject() && played.path("alive").isBoolean() && played.path("alive").booleanValue(),
                "H2743 requires the actual living played character");
        JsonNode diagnostics = actual.get("diagnostics");
        StrictJson.require(diagnostics != null && diagnostics.isObject(), "H2743 actual connection diagnostics required");
        H2743Frame observed = new H2743Frame(StrictJson.text(actual.get("snapshot_id")), observedInteger(actual.get("revision")), observedInteger(actual.get("native_revision")),
                StrictJson.integer(actual.get("date_raw"), 0, Integer.MAX_VALUE), StrictJson.integer(played.get("character_id"), 0, 0xffff_fffeL),
                StrictJson.text(actual.get("episode_run_id")), 16_777_231, observedInteger(diagnostics.get("connection_generation")));
        StrictJson.require(observed.equals(claim) && observed.revision().equals(original.before().frame().revision())
                && observed.snapshotId().equals("native:" + observed.nativeRevision()) && observed.dateRaw() == 53_217_264
                && observed.actorCharacterId() == 29_829 && observed.episodeRunId().equals("native-29829-2bc2d599f7f9"),
                "H2743 original exact episode/date/player/native frame differs");
        JsonNode wars = actual.get("active_wars"); StrictJson.require(wars != null && wars.isArray(), "H2743 active_wars array required");
        JsonNode matched = null; int count = 0;
        for (JsonNode war : wars) if (war.isObject() && war.path("war_id").isIntegralNumber()
                && war.path("war_id").bigIntegerValue().equals(BigInteger.valueOf(16_777_231))) { matched = war; count++; }
        StrictJson.require(count == 1, "H2743 exact current WarID must occur once");
        StrictJson.require("defender".equals(StrictJson.text(matched.get("player_side")))
                && matched.path("player_is_primary_war_leader").isBoolean() && matched.path("player_is_primary_war_leader").booleanValue()
                && StrictJson.integer(matched.get("primary_opponent_character_id"), 0, 0xffff_fffeL) == 30_097,
                "H2743 actual primary parties differ");
        JsonNode titles = matched.get("targeted_title_ids");
        StrictJson.require(titles != null && titles.isArray() && titles.size() == 1 && StrictJson.integer(titles.get(0), 0, 0xffff_fffeL) == 2_128,
                "H2743 original exact targeted title differs");
    }
    private static BigInteger observedInteger(JsonNode value) {
        if (value != null && value.isIntegralNumber())
            return StrictJson.integer(value, BigInteger.ONE, StrictJson.UINT64_MAX);
        return integer(value);
    }
    private static BigInteger integer(JsonNode value) {
        return PublicUnsigned64.parse(value, PublicUnsigned64.Minimum.ONE, PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);
    }
    private static void nonnegativeUint64(BigInteger value) {
        StrictJson.require(value != null && value.signum() >= 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "nonnegative exact uint64 expected_revision required");
    }
    private static void uint64(BigInteger value) {
        StrictJson.require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive exact uint64 required");
    }
}
