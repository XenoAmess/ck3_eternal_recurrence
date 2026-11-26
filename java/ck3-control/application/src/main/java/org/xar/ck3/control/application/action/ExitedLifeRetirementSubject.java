package org.xar.ck3.control.application.action;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.application.advance.AdvancePlan;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** The archived two-child Life subject for an independent exited-owner operator decision. */
public final class ExitedLifeRetirementSubject {
    private ExitedLifeRetirementSubject() { }

    public record Originals(ActionReceipt arm, ActionReceipt resume, CheckpointPair savedPair) { }

    static Originals requireOriginals(CompositeOperatorQuarantineRequest request, WriterContracts.Head predecessor,
            ActionReceipt parent, ActionPorts.OutcomeArchive archive) {
        var exited = request.exitedLife().orElseThrow();
        request.requireParent(parent);
        var state = predecessor.state();
        require(!predecessor.snapshotNeedsRecovery() && predecessor.indexRepairs().isEmpty()
                && state.sequence()==request.expectedHeadSequence() && predecessor.digest().equals(request.expectedHeadDigest())
                && state.machineId().equals(request.machineId()) && state.status()==ContinuityState.Status.REPAIR_REQUIRED
                && parent.sequence()<state.sequence() && archive.receiptReferenceOf(parent).equals(request.originalReceipt()),
                "exited Life requires its actual complete interrupted writer predecessor and original parent");
        var owner = new SessionIdentity(request.machineId(), request.game(), exited.ownerSessionId());
        CheckpointPair pair = importedSavedPair(state, owner, parent, exited);
        var canonical = ContinuityActionJournal.receipts(state, archive);
        require(canonical.contains(parent), "exited Life parent is absent from its actual canonical action prefix");
        var execution = ((ActionState.CompositeUnknown) parent.state()).execution();
        var arm = child(parent, execution.children().getFirst(), 1, canonical);
        var resume = child(parent, execution.children().getLast(), 2, canonical);
        require(arm.sequence()<resume.sequence() && canonical.stream().allMatch(action ->
                action.settled() || action.equals(parent) || action.equals(resume)),
                "exited Life cannot retire another unresolved action or an unordered original pair");
        var plan = AdvancePlan.decode(parent.command());
        require(plan.clockMode()==AdvancePlan.ClockMode.CAMPAIGN_SENTINEL && plan.dailyWatch().isEmpty()
                && parent.command().expected().observerSchema().equals(AdvancePlan.OBSERVER)
                && parent.command().expected().values().equals(plan.expected())
                && arm.command().operation().value().equals(plan.armStep())
                && arm.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied,
                "exited Life requires the original campaign sentinel ARM with its settled control result");
        var armState = (ActionState.Settled) arm.state();
        ActionEffects.validate(arm.command(), armState.attempt(), armState.dispatch(), armState.settlement());
        require(resume.command().operation().value().equals("resume-map") && resume.state() instanceof ActionState.Unknown,
                "exited Life requires the original RESUME UNKNOWN");
        var armCustody = acknowledgement(arm);
        var resumeCustody = acknowledgement(resume);
        require(armCustody.session().equals(resumeCustody.session())
                && armCustody.custodyEpoch().equals(resumeCustody.custodyEpoch())
                && resumeCustody.writeEntered().order().compareTo(armCustody.responseReceived().order())>0,
                "exited Life requires its original in-order same-connection ARM and RESUME acknowledgements");
        return new Originals(arm, resume, pair);
    }

    private static ActionReceipt child(ActionReceipt parent, CompositeExecution.Child binding, int ordinal, List<ActionReceipt> canonical) {
        var receipt = canonical.stream().filter(row -> row.command().actionId().equals(binding.actionId())).findFirst().orElseThrow();
        var command = receipt.command();
        var original = parent.command();
        require(receipt.bodySha256().equals(binding.bodySha256()) && receipt.sequence()<parent.sequence()
                && command.actionId().equals(ActionIds.child(original.actionId(), ordinal, command.operation()))
                && command.before().equals(original.before()) && command.source().equals(original.source())
                && command.sessionId().equals(original.sessionId()) && command.deadline().equals(original.deadline())
                && command.claims().equals(original.claims()) && command.arguments().members().isEmpty()
                && command.expected().equals(AdvancePrimitives.expected(command.before(), command.source(),
                        command.operation(), command.arguments())),
                "exited Life changed an original derived child body, source, frame or deadline");
        return receipt;
    }

    private static NativeRequestChronology acknowledgement(ActionReceipt original) {
        var command = original.command();
        var attempt = ActionTransitions.attempt(original.state()).orElseThrow();
        var ack = original.ack().orElseThrow();
        var custody = ack.custody().orElseThrow();
        var guard = attempt.guard();
        require(attempt.requestId().equals(ack.requestId()) && RequestIds.forCommand(command).equals(attempt.requestId())
                && command.origin().acceptsGuard(guard.origin()) && command.source().equals(guard.source())
                && command.sessionId().equals(guard.sessionId()) && command.operation().equals(guard.operation())
                && !custody.writeEntered().observedAt().isBefore(attempt.submittedAt())
                && custody.responseReceived().observedAt().isBefore(command.deadline()),
                "exited Life acknowledgement differs from the exact original action request and finite window");
        AdvancePrimitives.nativeResult(ack, command.operation().value());
        custody.verify(ack, guard);
        return custody;
    }

    private static CheckpointPair importedSavedPair(ContinuityState state, SessionIdentity owner, ActionReceipt parent,
            CompositeOperatorQuarantineRequest.ExitedLife exited) {
        var whole = state.toJson();
        require(!whole.hasNonNull(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)
                && !whole.hasNonNull(WriterContracts.GAMEPLAY_ENTRY_FIELD),
                "exited Life retirement requires the original imported saved frontier");
        var marker = SavedContinuityBootstrap.request(ContinuityJson.object(whole.get(SavedContinuityBootstrap.FIELD))).detailsObject();
        var batch = StrictJson.object(whole.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD),
                java.util.Set.of("batch_id", "boundary", "evidence_id", "session"));
        var cycle = ContinuityJson.object(whole.get(WriterContracts.ORDINARY_CYCLE_FIELD));
        require(OrdinaryCycleTransitions.sessionFromJson(marker.get("session")).equals(owner)
                && "BATCH_INTERRUPTED".equals(StrictJson.text(batch.get("boundary")))
                && OrdinaryCycleTransitions.sessionFromJson(batch.get("session")).equals(owner)
                && OrdinaryCycleTransitions.sessionFromJson(cycle.get("session")).equals(owner)
                && cycle.path("pending_receipt").isNull() && cycle.path("retained_legacy_pending_digest").isNull()
                && cycle.hasNonNull("head") && ContinuityJson.same(whole.get("game_binding"), owner.game().toJson())
                && ContinuityJson.same(whole.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD), marker.get("full_driver"))
                && StrictJson.integer(marker.get("saved_completed_cycles"),0,StrictJson.MAX_SAFE_INTEGER)==state.settledCycles()
                && StrictJson.integer(marker.get("saved_date_raw"),0,StrictJson.MAX_SAFE_INTEGER)==state.settledDateRaw(),
                "exited Life changed the original imported saved basis or interrupted batch ownership");
        var pair = CheckpointPairCodec.decode(StrictJson.canonical(marker.get("checkpoint_pair")));
        var before = parent.command().before().frame();
        require(ActionCodec.sha256(CheckpointPairCodec.encode(pair)).equals(exited.savedPairSha256())
                && pair.frame().machineId().equals(owner.machineId())
                && pair.frame().frame().episodeRunId().equals(before.episodeRunId())
                && pair.frame().frame().identity().player().equals(before.identity().player())
                && pair.frame().frame().identity().dateRaw().equals(BigInteger.valueOf(state.settledDateRaw()))
                && before.identity().dateRaw().compareTo(pair.frame().frame().identity().dateRaw())>=0,
                "exited Life changed the exact confirmed checkpoint pair, actor or saved date");
        return pair;
    }
}
