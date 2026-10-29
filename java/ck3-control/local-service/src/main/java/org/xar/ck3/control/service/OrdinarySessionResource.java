package org.xar.ck3.control.service;

import com.fasterxml.jackson.databind.node.ObjectNode;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.EnumMap;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.planning.PlanningWire;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.application.session.BatchLimitsWire;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.SessionController;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.StrictJson;

/** Thin local boundary; status and stop ACK are never recorded as native/SAVE completion. */
@Path("/v1/ordinary-session")
@Produces(MediaType.APPLICATION_JSON)
public final class OrdinarySessionResource {
    private final OrdinarySessionHost host;
    @Inject public OrdinarySessionResource(OrdinarySessionHost host) { this.host = Objects.requireNonNull(host); }

    @GET @Path("/status") public Response status() {
        ObjectNode row = envelope("xar.ordinary-session-status/v1");
        if (host.current().isEmpty()) {
            row.put("status", "UNAVAILABLE"); row.put("detail", "Root has not installed the complete qualified ordinary production graph");
            return json(503, row);
        }
        SessionController controller = host.current().orElseThrow(); row.put("status", controller.isRetired() ? "RETIRED" : controller.isRunning() ? "RUNNING_BATCH"
                : controller.isQuarantined() ? "RECONCILIATION_REQUIRED" : "IDLE");
        row.set("session", identity(controller));
        controller.lastReport().ifPresentOrElse(report -> row.set("last_batch", report(report)), () -> row.putNull("last_batch"));
        return json(200, row);
    }
    @POST @Path("/{sessionId}/batch") @Consumes(MediaType.APPLICATION_JSON)
    public Response batch(@PathParam("sessionId") String sessionId, byte[] raw) {
        BatchLimits limits;
        try { limits = BatchLimitsWire.decode(raw); }
        catch (IllegalArgumentException failure) { return error(400, "INVALID_REQUEST", failure.getMessage()); }
        try { return json(200, report(host.batch(sessionId, limits))); }
        catch (IllegalArgumentException failure) { return error(409, "SESSION_REJECTED", failure.getMessage()); }
        catch (IllegalStateException failure) { return error(503, "UNAVAILABLE", failure.getMessage()); }
    }
    @POST @Path("/{sessionId}/stop") public Response stop(@PathParam("sessionId") String sessionId) {
        try {
            host.requestStop(sessionId); ObjectNode row = envelope("xar.ordinary-session-stop-requested/v1");
            row.put("session_id", sessionId); row.put("status", "STOP_REQUESTED"); row.put("business_completion", false); return json(202, row);
        } catch (IllegalArgumentException failure) { return error(409, "SESSION_REJECTED", failure.getMessage()); }
        catch (IllegalStateException failure) { return error(503, "UNAVAILABLE", failure.getMessage()); }
    }
    private static ObjectNode identity(SessionController controller) {
        var session = controller.identity(); ObjectNode row = StrictJson.object(); row.put("machine_id", session.machineId());
        row.put("session_id", session.sessionId()); row.put("game_pid", session.game().pid());
        row.put("game_creation_filetime", session.game().creationFiletime().value().toString()); return row;
    }
    /** Finite public summary. Full typed turns remain with the actual controller and sole action/writer evidence. */
    public static ObjectNode report(BatchReport report) {
        ObjectNode row = envelope("xar.ordinary-session-batch-result/v1"); row.put("machine_id", report.session().machineId());
        row.put("game_pid", report.session().game().pid()); row.put("game_creation_filetime", report.session().game().creationFiletime().value().toString());
        row.put("session_id", report.session().sessionId()); row.put("batch_id", report.batchId()); row.put("terminal", report.terminal().name());
        row.put("detail", report.detail()); row.put("began_at_utc", report.began().utc().toString()); row.put("ended_at_utc", report.ended().utc().toString());
        row.put("full_wall_nanos", Long.toString(report.fullWallNanos())); row.put("attempted_turns", report.turns().size() + report.reconciliations().size()+report.lifecycleTurns().size()+report.readPublicationReconciliations().size());
        row.put("original_action_reconciliation_count", report.reconciliations().size());
        row.put("zero_dispatch_revision_replan_count", report.revisionReplans().size());
        row.put("applied_turns", report.turns().stream().filter(turn -> turn.receipt().outcome() == org.xar.ck3.control.application.action.ActionReceipt.Outcome.APPLIED_CONFIRMED).count());
        row.put("ordinary_action_positive_ack_count", report.turns().stream().filter(turn -> turn.receipt().ack().filter(ack -> ack.nativeOk()).isPresent()).count());
        row.put("committed_saved_days", report.committedSavedDays()); row.put("eligible_advances_since_save", report.eligibleAdvancesSinceSave()); row.put("dirty_since_save", report.dirtySinceSave());
        report.committedLedgerHead().ifPresentOrElse(ref -> row.set("committed_ledger_head", ref.toJson()), () -> row.putNull("committed_ledger_head"));
        report.lastSavedPair().ifPresentOrElse(pair -> row.set("last_saved_pair", StrictJson.parse(CheckpointPairCodec.encode(pair))), () -> row.putNull("last_saved_pair"));
        var tails = row.putArray("last_actions"); int first = Math.max(0, report.turns().size() - 128);
        row.put("reported_action_tail_count", report.turns().size() - first);
        for (int index = first; index < report.turns().size(); index++) {
            var turn = report.turns().get(index); ObjectNode item = tails.addObject(); item.put("turn_index", turn.index());
            item.put("action_id", turn.receipt().command().actionId()); item.put("body_sha256", turn.receipt().bodySha256()); item.put("outcome", turn.receipt().outcome().name());
            item.put("writer_sequence", turn.receipt().sequence()); item.put("visible_gameplay", turn.facts().visibleGameplay()); item.put("eligible_advance", turn.facts().eligibleAdvance());
            var refs = item.putArray("independent_native_evidence"); turn.facts().independentEvidence().forEach(ref -> refs.add(ref.toJson()));
        }
        var reconciled = row.putArray("last_original_action_reconciliations");
        for (int index = Math.max(0, report.reconciliations().size() - 128); index < report.reconciliations().size(); index++) {
            var original = report.reconciliations().get(index); ObjectNode item = reconciled.addObject(); item.put("turn_index", original.index());
            item.put("action_id", original.originalReceipt().command().actionId()); item.put("original_body_sha256", original.originalReceipt().bodySha256());
            item.put("outcome", original.originalReceipt().outcome().name()); item.put("writer_sequence", original.originalReceipt().sequence()); item.put("new_action_submitted", false);
        }
        row.put("lifecycle_turn_count",report.lifecycleTurns().size());
        var lifecycle=row.putArray("last_lifecycle_turns");
        for(int index=Math.max(0,report.lifecycleTurns().size()-128);index<report.lifecycleTurns().size();index++) {
            var turn=report.lifecycleTurns().get(index);ObjectNode item=lifecycle.addObject();
            item.put("turn_index",turn.index());item.set("current_lifecycle_identity",org.xar.ck3.control.application.action.LifecycleIdentityCodec.encode(turn.current()));
            item.put("action_id",turn.receipt().command().actionId());item.put("body_sha256",turn.receipt().bodySha256());
            item.put("outcome",turn.receipt().outcome().name());item.put("writer_sequence",turn.receipt().sequence());item.put("reconciliation",turn.reconciliation());
            item.put("visible_gameplay",false);item.put("eligible_advance",false);
            turn.successorUiContinuation().ifPresent(pass->item.set("successor_ui_continuation",
                    org.xar.ck3.control.application.session.SuccessorUiContinuationJson.encode(pass)));
        }
        report.lastTerminalObservation().ifPresentOrElse(observed->{
            ObjectNode value=row.putObject("last_terminal_observation");value.set("identity",org.xar.ck3.control.application.action.LifecycleIdentityCodec.encode(observed.identity()));
            var decision=observed.decision();
            if(decision instanceof org.xar.ck3.control.application.session.SessionPorts.TerminalBlocked blocked){value.put("decision","BLOCKED");value.put("reason",blocked.reason());var refs=value.putArray("evidence");blocked.evidence().forEach(ref->refs.add(ref.toJson()));}
            else if(decision instanceof org.xar.ck3.control.application.session.SessionPorts.TerminalWait waiting){value.put("decision","WAIT");value.put("reason",waiting.reason());}
            else if(decision instanceof org.xar.ck3.control.application.session.SessionPorts.TerminalReconciliation original){value.put("decision","RECONCILE");value.put("action_id",original.actionId());}
            else {value.put("decision","ACTION");value.put("action_id",((org.xar.ck3.control.application.session.SessionPorts.TerminalAction)decision).command().actionId());}
        },()->row.putNull("last_terminal_observation"));
        EnumMap<BatchReport.Phase, Long> totals = new EnumMap<>(BatchReport.Phase.class);
        EnumMap<BatchReport.Phase, Integer> failures = new EnumMap<>(BatchReport.Phase.class);
        for (var span : report.phases()) {
            totals.merge(span.phase(), span.ended().elapsedNanos() - span.began().elapsedNanos(), Long::sum);
            if (span.terminal() != BatchReport.PhaseTerminal.RETURNED) failures.merge(span.phase(), 1, Integer::sum);
        }
        var phases = row.putArray("phase_totals"); totals.forEach((phase,nanos) -> {
            ObjectNode item = phases.addObject(); item.put("phase", phase.name()); item.put("elapsed_nanos", Long.toString(nanos)); item.put("nonreturned_spans", failures.getOrDefault(phase, 0));
        });
        var readParents=row.putArray("last_read_publication_reconciliations");
        for(int i=Math.max(0,report.readPublicationReconciliations().size()-128);i<report.readPublicationReconciliations().size();i++) {
            var original=report.readPublicationReconciliations().get(i);ObjectNode item=readParents.addObject();item.put("turn_index",original.index());
            item.put("action_id",original.originalReceipt().command().actionId());item.put("body_sha256",original.originalReceipt().bodySha256());item.put("outcome",original.originalReceipt().outcome().name());
            item.put("writer_sequence",original.originalReceipt().sequence());item.put("new_action_submitted",false);
            item.put("read_event_identity",original.readPublication().actual().eventIdentity());item.put("read_predecessor_head_sha256",original.readPublication().predecessor().digest());
            item.put("read_published_head_sha256",org.xar.ck3.control.continuity.ContinuityJson.digest(original.readPublication().actual().head().toJson()));
        }
        report.lastPlan().ifPresentOrElse(plan -> row.set("last_plan", PlanningWire.trace(plan)), () -> row.putNull("last_plan"));
        report.lastLifecycle().ifPresentOrElse(state -> {
            ObjectNode value = row.putObject("last_inner_process"); value.set("actual_evidence", state.evidence().toJson());
            if (state instanceof GameLifecycle.Exited exited) {
                value.put("status", "EXITED"); value.put("exit_code", exited.exitCode()); value.put("timed_out", exited.timedOut()); value.put("terminal", exited.terminal().name());
            } else if (state instanceof GameLifecycle.Unavailable unavailable) { value.put("status", "UNAVAILABLE"); value.put("reason", unavailable.reason()); }
            else value.put("status", "RUNNING");
        }, () -> row.putNull("last_inner_process"));
        var pending = row.putArray("pending_offline_analysis"); report.pendingAnalysisBatchIds().forEach(pending::add);
        var failed = row.putArray("failed_offline_analysis"); report.failedAnalysisBatchIds().forEach(failed::add);
        var complete = row.putArray("completed_offline_analysis"); report.completedAnalyses().forEach(result -> {
            ObjectNode item = complete.addObject(); item.put("batch_id", result.batchId()); item.put("persisted_review_count", result.persistedReviews().size()); item.set("published_knowledge", result.publishedKnowledge().toJson());
        });
        return row;
    }
    private static ObjectNode envelope(String schema) { ObjectNode row = StrictJson.object(); row.put("schema", schema); return row; }
    private static Response error(int status, String code, String message) {
        ObjectNode row = envelope("xar.ordinary-session-error/v1"); row.put("code", code); row.put("detail", message); return json(status, row);
    }
    private static Response json(int status, ObjectNode row) {
        return Response.status(status).entity(StrictJson.canonical(row, 1_048_576)).type(MediaType.APPLICATION_JSON_TYPE)
                .header("X-Xar-Contract-Revision", "xar.ordinary-session/v1").build();
    }
}
