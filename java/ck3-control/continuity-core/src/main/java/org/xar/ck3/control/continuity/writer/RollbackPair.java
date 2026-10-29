package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Original completed-tail history + saved-frontier rollback, as one recoverable two-event transaction. */
public final class RollbackPair {
    public static final String HISTORY_KIND = "completed_unsaved_tail_recorded_v1";
    public static final String ROLLBACK_KIND = "saved_checkpoint_rollback_verified_v1";
    private RollbackPair() { }
    /** Only the installed authority can grant evidence eligibility; constructing this record is not qualification. */
    public record Evidence(ExactRef proof, byte[] savedBasis, byte[] currentFrame, long currentCycles,
                           List<Pin> qualificationSources, String preconditionDigest) {
        public Evidence {
            Objects.requireNonNull(proof); savedBasis = canonical(savedBasis); currentFrame = canonical(currentFrame);
            StrictJson.safe(currentCycles, 0); qualificationSources = List.copyOf(qualificationSources); requireDigest(preconditionDigest);
            StrictJson.require(qualificationSources.size() <= 256, "finite rollback producer/evidence/source closure");
        }
        @Override public byte[] savedBasis() { return savedBasis.clone(); }
        @Override public byte[] currentFrame() { return currentFrame.clone(); }
    }
    @FunctionalInterface public interface Authority {
        /** Must re-run the actual shared recovery verifier/reducer prerequisites against original sources. */
        Evidence revalidate(Head originalHead, ExactRef proof) throws IOException;
    }
    public record EventPlan(Request request, ContinuityState reduced, ContinuityState committed) {
        public EventPlan { Objects.requireNonNull(request); Objects.requireNonNull(reduced); Objects.requireNonNull(committed); }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("kind", request.kind()); row.set("details", request.detailsObject());
            row.set("reduced_state", reduced.toJson()); row.set("committed_state", committed.toJson()); return row;
        }
    }
    public record Plan(Head originalHead, Evidence evidence, EventPlan first, EventPlan second, String transactionId) {
        public Plan { Objects.requireNonNull(originalHead); Objects.requireNonNull(evidence); Objects.requireNonNull(first); Objects.requireNonNull(second); requireDigest(transactionId); }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.set("proof_ref", evidence.proof().toJson()); row.set("original_head", originalHead.state().toJson());
            row.put("precondition_digest", evidence.preconditionDigest()); row.set("saved_basis", object(evidence.savedBasis()));
            row.set("current_frame", object(evidence.currentFrame())); row.put("current_cycles", evidence.currentCycles());
            row.set("first", first.toJson()); row.set("second", second.toJson()); row.put("transaction_id", transactionId);
            var sources = row.putArray("qualification_sources"); evidence.qualificationSources().forEach(pin -> {
                ObjectNode entry = sources.addObject(); entry.set("ref", pin.reference().toJson());
                var id = pin.identity(); entry.put("volume", id.volumeSerialDecimal()); entry.put("file", id.fileIdDecimal());
                entry.put("creation", id.creationFiletimeDecimal()); entry.put("modified", id.modifiedInstant()); entry.put("bytes", id.bytes());
            }); return row;
        }
    }
    public record Commit(String transactionId, long previousSequence, long committedSequence, String committedDigest,
                         boolean recoveredAfterFirstEvent, int writes, int createdEvents) {
        public Commit { requireDigest(transactionId); requireDigest(committedDigest); StrictJson.safe(previousSequence, 0); StrictJson.safe(committedSequence, 1);
            StrictJson.require(writes >= 0 && createdEvents >= 0 && createdEvents <= 2, "rollback commit accounting"); }
    }
    public interface Store {
        Plan previewRollback(ExactRef proof) throws IOException;
        Commit commitRollback(Plan plan) throws IOException;
    }
    public static Plan plan(Head original, Evidence evidence) {
        ContinuityState before = original.state(); ObjectNode basis = object(evidence.savedBasis()), frame = object(evidence.currentFrame());
        StrictJson.require(StrictJson.text(basis.get("machine_id")).equals(before.machineId())
                && before.settledCycles() == evidence.currentCycles() && before.settledDateRaw() == number(frame, "date_raw"), "proof and actual completed frontier");
        ObjectNode origin = ContinuityJson.object(basis.get("origin"));
        for (String field : Set.of("start_date_raw", "target_date_raw", "target_days"))
            StrictJson.require(number(before.toJson(), field) == number(origin, field), "rollback never changes original campaign window");
        long savedCycles = number(basis, "completed_cycles"); ObjectNode savedFrame = ContinuityJson.object(basis.get("frame"));
        long savedDate = number(savedFrame, "date_raw");
        StrictJson.require(evidence.currentCycles() >= savedCycles && before.settledDateRaw() >= savedDate
                && (evidence.currentCycles() > savedCycles || before.settledDateRaw() > savedDate), "actual nonempty discarded completed tail");
        ObjectNode firstDetails = details(before, evidence, "unsaved-tail-history:" + evidence.proof().sha256());
        ContinuityState firstReduced = history(before, evidence);
        Request firstRequest = new Request(HISTORY_KIND, ContinuityJson.canonical(firstDetails), List.of(evidence.proof()));
        ContinuityState firstCommitted = commitProjection(firstReduced, firstRequest, before.sequence() + 1);
        ObjectNode secondDetails = details(before, evidence, "saved-checkpoint-rollback:" + evidence.proof().sha256());
        Request secondRequest = new Request(ROLLBACK_KIND, ContinuityJson.canonical(secondDetails), List.of(evidence.proof()));
        ContinuityState secondReduced = restore(firstCommitted, evidence);
        ContinuityState secondCommitted = commitProjection(secondReduced, secondRequest, before.sequence() + 2);
        ObjectNode identity = StrictJson.object(); identity.set("proof_ref", evidence.proof().toJson());
        identity.put("original_sequence", before.sequence()); identity.put("original_digest", original.digest());
        Plan result = new Plan(original, evidence, new EventPlan(firstRequest, firstReduced, firstCommitted),
                new EventPlan(secondRequest, secondReduced, secondCommitted), ContinuityJson.digest(identity)); validate(result); return result;
    }
    public static ContinuityState history(ContinuityState previous, Evidence evidence) {
        ObjectNode old = previous.toJson(), basis = object(evidence.savedBasis()), frame = object(evidence.currentFrame());
        StrictJson.require(previous.machineId().equals(StrictJson.text(basis.get("machine_id")))
                && previous.settledCycles() == evidence.currentCycles() && previous.settledDateRaw() == number(frame, "date_raw"), "actual completed current head");
        ObjectNode origin = ContinuityJson.object(basis.get("origin"));
        for (String field : Set.of("start_date_raw", "target_date_raw", "target_days"))
            StrictJson.require(number(old, field) == number(origin, field), "original campaign window");
        long savedCycles = number(basis, "completed_cycles"), savedDate = number(ContinuityJson.object(basis.get("frame")), "date_raw");
        StrictJson.require(savedCycles <= evidence.currentCycles() && savedDate <= previous.settledDateRaw(), "rollback cannot manufacture forward progress");
        old.put("status", "repair_required"); ObjectNode recovery = old.putObject("unsaved_tail_recovery");
        recovery.set("evidence_ref", evidence.proof().toJson()); recovery.put("phase", "historical_tail_recorded");
        recovery.put("saved_cycles", savedCycles); recovery.put("saved_date_raw", savedDate);
        recovery.put("historical_cycles", evidence.currentCycles()); recovery.put("historical_date_raw", number(frame, "date_raw"));
        recovery.put("rolled_back_cycles", evidence.currentCycles() - savedCycles); recovery.put("rolled_back_date_raw", number(frame, "date_raw") - savedDate);
        recovery.put("ordinary_cycle_credit", 0); recovery.put("game_day_credit", 0); recovery.put("original_actions_replayed", false); recovery.put("Driver_history_truncated", false);
        return ContinuityState.fromJson(old, previous.machineId());
    }
    public static ContinuityState restore(ContinuityState previous, Evidence evidence) {
        ObjectNode old = previous.toJson(), basis = object(evidence.savedBasis()), recovery = ContinuityJson.object(old.get("unsaved_tail_recovery"));
        StrictJson.require(StrictJson.text(recovery.get("phase")).equals("historical_tail_recorded")
                && ExactRef.fromJson(recovery.get("evidence_ref")).equals(evidence.proof())
                && previous.settledCycles() == evidence.currentCycles()
                && previous.settledDateRaw() == number(object(evidence.currentFrame()), "date_raw"), "exact retained historical-tail predecessor");
        old.put("last_settled_cycles", number(basis, "completed_cycles"));
        old.put("last_settled_date_raw", number(ContinuityJson.object(basis.get("frame")), "date_raw")); old.put("status", "repair_required");
        old.set("last_settled_source", ExactRef.fromJson(ContinuityJson.object(basis.get("refs")).get("settled_full_response")).toJson());
        recovery.put("phase", "saved_frontier_restored"); recovery.set("saved_target_frame", basis.get("frame").deepCopy()); recovery.put("requires_new_cold_binding", true);
        return ContinuityState.fromJson(old, previous.machineId());
    }
    public static void validate(Plan plan) {
        ContinuityState before = plan.originalHead().state(); StrictJson.require(plan.first().request().kind().equals(HISTORY_KIND)
                && plan.second().request().kind().equals(ROLLBACK_KIND), "ordered rollback kinds");
        long sequence = before.sequence(); int offset = 0; ContinuityState predecessor = before;
        for (EventPlan event : List.of(plan.first(), plan.second())) {
            offset++; ObjectNode details = event.request().detailsObject();
            StrictJson.require(StrictJson.text(details.get("machine_id")).equals(before.machineId())
                    && number(details, "ordinary_cycle_credit") == 0 && number(details, "game_day_credit") == 0
                    && falseValue(details.get("original_actions_replayed")) && falseValue(details.get("window_origin_reset")), "zero credit/no replay/origin reset");
            StrictJson.require(event.reduced().sequence() == sequence + offset - 1
                    && event.committed().sequence() == sequence + offset && event.reduced().status() == ContinuityState.Status.REPAIR_REQUIRED
                    && ContinuityJson.same(event.committed().toJson(), commitProjection(event.reduced(), event.request(), sequence + offset).toJson()), "exact reducer/committed projection");
            StrictJson.require(!ContinuityJson.same(predecessor.toJson(), event.reduced().toJson()), "rollback event must be a real transition");
            for (String field : Set.of("schema", "machine_id", "window_id", "start_date_raw", "target_date_raw", "target_days", "target_years", "calendar_year_days", "manual_repair_count", "automatic_recovery_count", "binding_lineage_count", "game", "game_binding", "latest_binding", "pending_cycle", "pending_checkpoint", "unknown_requests", "NEXT")) {
                ObjectNode prior = before.toJson(), after = event.reduced().toJson();
                StrictJson.require(prior.has(field) == after.has(field) && (!prior.has(field) || ContinuityJson.same(prior.get(field), after.get(field))), "preserved rollback field " + field);
            }
            for (String field : PRESERVED_RUNTIME_FIELDS) {
                ObjectNode prior = before.toJson(), after = event.reduced().toJson();
                StrictJson.require(prior.has(field) == after.has(field) && (!prior.has(field) || ContinuityJson.same(prior.get(field), after.get(field))), "preserved rollback runtime field " + field);
            }
            for (String field : List.of(DomainBodies.FIELD, ACTION_LIFECYCLE_FIELD,
                    ORDINARY_CYCLE_FIELD, ORDINARY_SAVED_CYCLE_FIELD, ORDINARY_CYCLE_REBIND_FIELD, ORDINARY_BATCH_BOUNDARY_FIELD,
                    DRIVER_HISTORY_BASELINE_FIELD, GAMEPLAY_ENTRY_FIELD, DRIVER_READ_HISTORY_FIELD)) {
                ObjectNode prior = before.toJson(), after = event.reduced().toJson();
                StrictJson.require(prior.has(field) == after.has(field) && (!prior.has(field) || ContinuityJson.same(prior.get(field), after.get(field))), "rollback cannot modify canonical domain/action/cycle history " + field);
            }
            predecessor = event.committed();
        }
        StrictJson.require(plan.first().committed().settledCycles() == before.settledCycles()
                && plan.first().committed().settledDateRaw() == before.settledDateRaw()
                && plan.second().committed().settledCycles() <= before.settledCycles()
                && plan.second().committed().settledDateRaw() <= before.settledDateRaw(), "actual frontier retained then rolled back");
    }
    private static ObjectNode details(ContinuityState before, Evidence evidence, String id) {
        ObjectNode details = StrictJson.object(); details.put("machine_id", before.machineId()); details.put("source", evidence.proof().path());
        details.set("proof_ref", evidence.proof().toJson()); details.put("ordinary_cycle_credit", 0); details.put("game_day_credit", 0);
        details.put("original_actions_replayed", false); details.put("window_origin_reset", false); details.put("evidence_id", id); return details;
    }
    private static ContinuityState commitProjection(ContinuityState state, Request request, long sequence) {
        ObjectNode row = state.toJson(); row.put("sequence", sequence); row.put("last_event_identity", request.identity()); return ContinuityState.fromJson(row, state.machineId());
    }
    private static long number(ObjectNode row, String field) { return StrictJson.integer(row.get(field), 0, StrictJson.MAX_SAFE_INTEGER); }
    private static boolean falseValue(com.fasterxml.jackson.databind.JsonNode value) { return value != null && value.isBoolean() && !value.booleanValue(); }
}

