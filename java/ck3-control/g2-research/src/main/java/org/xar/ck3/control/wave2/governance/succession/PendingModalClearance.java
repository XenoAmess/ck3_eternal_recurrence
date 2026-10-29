package org.xar.ck3.control.wave2.governance.succession;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.BoundFrame;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.ClearanceState;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.Close;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.CloseState;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.Query;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.Scene;

/**
 * Pure evidence comparison for the original post-Continue once-Close only. Root must replay the
 * actual read guards, source qualification and native/semantic ancestry before supplying capture.
 * This class cannot submit, settle a writer row, qualify Root, advance a day or finish inheritance.
 */
public final class PendingModalClearance {
    private PendingModalClearance() { }

    /** Exact scene materials, not an executable admission or an EVENT-resolution receipt. */
    public static final class SceneQuery {
        private final Query query;
        private final ExactRef actualRead, fullSemantic, actualNative;
        private final Instant observedAtUtc;
        private SceneQuery(Query query, ExactRef actualRead, ExactRef fullSemantic, ExactRef actualNative, Instant observedAtUtc) {
            this.query = query; this.actualRead = actualRead;
            this.fullSemantic = fullSemantic; this.actualNative = actualNative;
            this.observedAtUtc = observedAtUtc;
        }
        public Query query() { return query; }
        public ExactRef actualRead() { return actualRead; }
        public ExactRef fullSemantic() { return fullSemantic; }
        public ExactRef actualNative() { return actualNative; }
        public Instant observedAtUtc() { return observedAtUtc; }
    }

    /**
     * Check the complete retained normalized SEM, without trimming history or normalizing it again.
     * References alone never establish that these bytes came from an actual source-qualified read.
     * The private Root caller owns that additional check, both live and on archived replay.
     */
    public static SceneQuery capture(Query query, ExactRef actualRead, ExactRef fullSemantic,
            ExactRef actualNative, byte[] originalSemantic, Instant actualObservedAtUtc) {
        Objects.requireNonNull(query); nonempty(actualRead); nonempty(fullSemantic); nonempty(actualNative);
        Objects.requireNonNull(originalSemantic); Objects.requireNonNull(actualObservedAtUtc);
        StrictJson.require(originalSemantic.length == fullSemantic.bytes()
                && G2RetainedNativeSourceProvider.sha256(originalSemantic).equals(fullSemantic.sha256()),
                "complete actual semantic bytes/SHA differ from their retained original");
        JsonNode semantic = FullJsonTree.parse(originalSemantic, FullJsonTree.MAXIMUM_BYTES);
        var frame = query.binding().frame();
        StrictJson.require(semantic.isObject()
                && StrictJson.text(field(semantic, "snapshot_id")).equals(frame.snapshotId())
                && integer(semantic, "revision").equals(frame.publicRevision())
                && integer(semantic, "native_revision").equals(frame.nativeRevision())
                && StrictJson.integer(field(semantic, "date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE) == frame.dateRaw()
                && StrictJson.integer(field(semantic, "local_player_id"), 0, Integer.MAX_VALUE) == frame.localPlayerId()
                && StrictJson.integer(field(field(semantic, "played_character"), "character_id"), 1, Integer.MAX_VALUE) == frame.actorCharacterId(),
                "captured complete semantic frame differs from its actual timeline query");
        StrictJson.trueValue(field(semantic, "paused"));
        StrictJson.trueValue(field(semantic, "map_ready"));
        StrictJson.trueValue(field(field(semantic, "played_character"), "alive"));
        StrictJson.require(Scene.fromSnapshot(semantic).equals(query.binding().scene()),
                "timeline scene differs from the complete actual semantic original");
        return new SceneQuery(query, actualRead, fullSemantic, actualNative, actualObservedAtUtc);
    }

    public static final class Result {
        private final ClearanceState state;
        private final Query initial;
        private final Close close;
        private final List<SceneQuery> queries;
        private Result(ClearanceState state, Query initial, Close close, List<SceneQuery> queries) {
            this.state = state; this.initial = initial; this.close = close; this.queries = queries;
        }
        public ClearanceState state() { return state; }
        public List<SceneQuery> queries() { return queries; }
        public boolean naturalDeathProven() { return false; }
        public boolean savedContinuationProven() { return false; }
        public boolean submissionAuthorized() { return false; }
        public boolean finalUiProven() { return false; }
        public boolean dayAdvanceProven() { return false; }
        /** DATA diagnostics only; importing this JSON cannot reconstruct an admission. */
        public byte[] originalProof() {
            ObjectNode out = StrictJson.object().put("schema", "xar.java.pending-modal-clearance/v1")
                    .put("machine_id", initial.binding().session().machineId())
                    .put("observed_at_utc", queries.getLast().observedAtUtc().toString())
                    .put("state", state.name()).put("modal_clear_observed", state == ClearanceState.CLEARED_OBSERVED)
                    .put("final_ui_qualified", false).put("day_advance_qualified", false)
                    .put("natural_cause_qualified", false).put("saved_continuation_qualified", false)
                    .put("submission_authorized", false).put("replay_authorized", false);
            out.set("initial_query", initial.original().toJson()); out.set("close", close.original().toJson());
            var rows = out.putArray("subsequent_queries");
            for (SceneQuery value : queries) {
                ObjectNode row = rows.addObject(); row.set("query", value.query().original().toJson());
                row.set("actual_read", value.actualRead().toJson());
                row.set("full_semantic", value.fullSemantic().toJson()); row.set("actual_native", value.actualNative().toJson());
                row.put("observed_at_utc", value.observedAtUtc().toString());
            }
            return StrictJson.canonical(out);
        }
    }

    /**
     * Scene equality still binds preparation to the submitted Close. Only fresh post-ACK reads may
     * contain changed active_event/pending_character_interaction objects from their full originals.
     * Their presence is not clearance of that decision: the final UI stage must resolve them later.
     */
    public static Result inspect(Query initial, Close close, List<SceneQuery> fresh) {
        Objects.requireNonNull(initial); Objects.requireNonNull(close); fresh = List.copyOf(fresh);
        StrictJson.require(!fresh.isEmpty() && fresh.size() <= 8, "one-to-eight actual post-Close queries required");
        ClearanceState state = ClearanceState.CLEARED_OBSERVED;
        if (!NativeTimelineBlocker12004.sameContinuation(initial.binding(), close.binding())) state = ClearanceState.FRAME_CHANGED;
        else if (!initial.context().supportedCloseObserved()) state = ClearanceState.INITIAL_CLOSE_NOT_OBSERVED;
        else if (close.state() != CloseState.SUBMITTED_PENDING || close.ack().isEmpty()) state = ClearanceState.SUBMISSION_UNKNOWN;
        else if (close.ack().orElseThrow().actionObservationRevision().compareTo(initial.observationRevision()) < 0)
            state = ClearanceState.OBSERVATION_REGRESSED;
        if (state != ClearanceState.CLEARED_OBSERVED) return new Result(state, initial, close, fresh);
        BoundFrame previous = close.binding();
        BigInteger sequence = initial.sequence(), observed = close.ack().orElseThrow().actionObservationRevision();
        Set<String> requests = new HashSet<>(); requests.add(initial.requestId()); requests.add(close.requestId());
        Set<ExactRef> packets = new HashSet<>(); packets.add(initial.original()); packets.add(close.original());
        Set<String> hashes = new HashSet<>(); hashes.add(initial.original().sha256()); hashes.add(close.original().sha256());
        Set<ExactRef> readOriginals = new HashSet<>();
        Query last = null;
        for (SceneQuery captured : fresh) {
            Query next = captured.query();
            if (!sameModalEpisode(previous, next.binding())) { state = ClearanceState.FRAME_CHANGED; break; }
            if (next.sequence().compareTo(sequence) <= 0 || next.observationRevision().compareTo(observed) <= 0
                    || !requests.add(next.requestId()) || !packets.add(next.original()) || !hashes.add(next.original().sha256())
                    || !readOriginals.add(captured.actualRead())) {
                state = ClearanceState.POST_QUERY_NOT_NEWER; break;
            }
            previous = next.binding(); sequence = next.sequence(); observed = next.observationRevision(); last = next;
        }
        if (state == ClearanceState.CLEARED_OBSERVED && (last == null || !last.context().clearedObserved()))
            state = ClearanceState.MODAL_OR_PREDICATES_UNCLEARED;
        return new Result(state, initial, close, fresh);
    }

    private static boolean sameModalEpisode(BoundFrame before, BoundFrame after) {
        var a = before.frame(); var b = after.frame();
        return before.session().equals(after.session())
                && before.scene().terminalReason().equals(after.scene().terminalReason())
                && a.dateRaw() == b.dateRaw() && a.actorCharacterId() == b.actorCharacterId()
                && a.localPlayerId() == b.localPlayerId()
                && b.publicRevision().compareTo(a.publicRevision()) >= 0
                && b.nativeRevision().compareTo(a.nativeRevision()) >= 0;
    }
    private static JsonNode field(JsonNode object, String key) {
        StrictJson.require(object != null && object.isObject() && object.has(key), "missing complete semantic field: " + key);
        return object.get(key);
    }
    private static BigInteger integer(JsonNode object, String key) {
        JsonNode value = field(object, key);
        StrictJson.require(value.isIntegralNumber(), "exact integer complete semantic field required: " + key);
        return value.bigIntegerValue();
    }
    private static void nonempty(ExactRef ref) {
        StrictJson.require(Objects.requireNonNull(ref).bytes() > 0, "nonempty actual original reference required");
    }
}
