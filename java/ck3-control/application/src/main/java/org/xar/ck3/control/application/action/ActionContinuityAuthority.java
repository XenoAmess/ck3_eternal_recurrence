package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Installed as one branch of the writer's fixed authority router. It never changes batch/day/SAVE credit. */
public final class ActionContinuityAuthority implements WriterContracts.TransitionAuthority {
    private final ActionPorts.OutcomeArchive archive;
    private final ActionPorts.GuardPort guard;
    private final ActionPorts.RecordedEvidenceVerifier evidenceVerifier;
    private final String authorityId;
    private final java.time.Clock clock;
    private final ActionPorts.PreparationPort protocolIdentityPolicy;
    private volatile PhysicalActionRegistry physicalActions;
    public synchronized void bindPhysicalActions(PhysicalActionRegistry actual) {
        StrictJson.require(physicalActions == null, "actual physical registry is installed once on the same writer authority");
        physicalActions = java.util.Objects.requireNonNull(actual);
    }
    public ActionContinuityAuthority(String authorityId, ActionPorts.OutcomeArchive archive, ActionPorts.GuardPort guard, ActionPorts.RecordedEvidenceVerifier evidenceVerifier, java.time.Clock clock) {
        this(authorityId, archive, guard, evidenceVerifier, clock, new ActionPorts.PreparationPort() {
            @Override public NativeRequest prepare(ActionCommand command) { throw new IllegalStateException("identity policy cannot prepare a native request"); }
        });
    }
    public ActionContinuityAuthority(String authorityId, ActionPorts.OutcomeArchive archive, ActionPorts.GuardPort guard,
            ActionPorts.RecordedEvidenceVerifier evidenceVerifier, java.time.Clock clock, ActionPorts.PreparationPort actualProtocolIdentityPolicy) {
        this.protocolIdentityPolicy = java.util.Objects.requireNonNull(actualProtocolIdentityPolicy);
        this.archive = java.util.Objects.requireNonNull(archive); this.guard = java.util.Objects.requireNonNull(guard);
        this.evidenceVerifier = java.util.Objects.requireNonNull(evidenceVerifier);
        this.authorityId = StrictJson.text(authorityId); this.clock = java.util.Objects.requireNonNull(clock);
    }
    @Override public String revalidate(ContinuityState predecessor, WriterContracts.Request request) {
        throw new IllegalStateException("action qualification requires the actual original writer Head under its held lock");
    }
    @Override public String revalidate(WriterContracts.Head actualLockedHead, WriterContracts.Request request) {
        ContinuityState predecessor = actualLockedHead.state();
        ActionReceipt receipt = receipt(request); ProtocolIdentityAdmission.requireUnique(ContinuityActionJournal.receipts(predecessor, archive), receipt.command()); ActionTransitions.validate(ContinuityActionJournal.lookup(predecessor, receipt.command().actionId(), archive), receipt.command(), receipt.bodySha256(), receipt.state());
        ActionRecord record = archive.loadRecord(org.xar.ck3.control.contracts.ExactRef.fromJson(request.detailsObject().get("receipt_ref")));
        StrictJson.require(record.previous().equals(ContinuityActionJournal.recordHead(predecessor)), "action record predecessor changed under writer lock");
        PhysicalActionRegistry physical = physicalActions;
        if (receipt.state() instanceof PhysicalActionState || physical != null && physical.find(receipt.command().operation()).isPresent()) {
            StrictJson.require(physical != null, "actual physical source replay is unavailable");
            var binding = physical.require(receipt.command());
            try {
                binding.producer().verifyArchived(actualLockedHead, receipt, archive);
                if (receipt.state() instanceof ActionState.IntentDurable || receipt.state() instanceof PhysicalActionState value && value.phase() == PhysicalActionState.Phase.SUBMITTING)
                    ActionCoordinator.verifyGuard(receipt.command(), binding.producer().guard(actualLockedHead, receipt.command()), authorityId, clock.instant());
            } catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
            return ActionCodec.sha256(ActionReceiptCodec.encodeReceipt(receipt, archive));
        }
        evidenceVerifier.verify(actualLockedHead, receipt);
        if (receipt.state() instanceof ActionState.CompositeSettled settled)
            ActionEffects.validateCompositeChildren(receipt.command(), settled.execution(), settled.settlement(), settled.execution().children().stream()
                    .map(child -> ContinuityActionJournal.lookup(predecessor, child.actionId(), archive).orElseThrow()).toList());
        if (receipt.state() instanceof ActionState.IntentDurable || receipt.state() instanceof ActionState.Submitting) {
            protocolIdentityPolicy.requireProtocolIdentity(receipt.command());
        }
        return ActionCodec.sha256(ActionReceiptCodec.encodeReceipt(receipt, archive));
    }
    @Override public ContinuityState reduce(ContinuityState predecessor, WriterContracts.Request request) {
        ActionReceipt receipt = receipt(request); ProtocolIdentityAdmission.requireUnique(ContinuityActionJournal.receipts(predecessor, archive), receipt.command()); StrictJson.require(receipt.sequence() == Math.addExact(predecessor.sequence(), 1), "action event must consume actual next writer sequence");
        StrictJson.require(receipt.command().origin().machineId().equals(predecessor.machineId()), "action machine must equal canonical writer machine");
        ActionTransitions.validate(ContinuityActionJournal.lookup(predecessor, receipt.command().actionId(), archive), receipt.command(), receipt.bodySha256(), receipt.state());
        ObjectNode next = predecessor.toJson();
        ActionRecord record = archive.loadRecord(org.xar.ck3.control.contracts.ExactRef.fromJson(request.detailsObject().get("receipt_ref")));
        StrictJson.require(record.previous().equals(ContinuityActionJournal.recordHead(predecessor)), "action record predecessor changed");
        next.set(ContinuityActionJournal.STATE_FIELD, request.detailsObject().get("receipt_ref"));
        // The one writer assigns the sequence after pure reduction and validates it again at commit.
        return ContinuityState.fromJson(next, predecessor.machineId());
    }
    private ActionReceipt receipt(WriterContracts.Request request) {
        StrictJson.require(request.kind().equals(ContinuityActionJournal.KIND), "wrong reducer event kind");
        ObjectNode details = StrictJson.object(request.detailsObject(), Set.of("evidence_id", "source", "receipt_ref"));
        ActionReceipt receipt = archive.loadRecord(org.xar.ck3.control.contracts.ExactRef.fromJson(details.get("receipt_ref"))).receipt();
        StrictJson.require(ActionCodec.text(details, "evidence_id").equals(receipt.command().actionId() + ":" + receipt.sequence())
                && details.get("source").equals(ProposalLifecycleCodec.source(receipt.command().source())), "action event source/identity drift"); return receipt;
    }
}
