package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
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
    private final java.util.function.Supplier<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> borrowedSessions;
    private volatile PhysicalActionRegistry physicalActions;
    private final ThreadLocal<WriterContracts.Head> validationHead = new ThreadLocal<>();
    private final ThreadLocal<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> validationSession = new ThreadLocal<>();
    private final ThreadLocal<ActionPorts.OutcomeArchive> validationArchive = new ThreadLocal<>();
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
        this(authorityId, archive, guard, evidenceVerifier, clock, actualProtocolIdentityPolicy, null);
    }
    /** Explicit opt-in; the supplier must borrow the identical writer's currently held Session. */
    public ActionContinuityAuthority(String authorityId, ActionPorts.OutcomeArchive archive, ActionPorts.GuardPort guard,
            ActionPorts.RecordedEvidenceVerifier evidenceVerifier, java.time.Clock clock, ActionPorts.PreparationPort actualProtocolIdentityPolicy,
            java.util.function.Supplier<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> borrowedSessions) {
        this.protocolIdentityPolicy = java.util.Objects.requireNonNull(actualProtocolIdentityPolicy);
        this.archive = java.util.Objects.requireNonNull(archive); this.guard = java.util.Objects.requireNonNull(guard);
        this.evidenceVerifier = java.util.Objects.requireNonNull(evidenceVerifier);
        this.authorityId = StrictJson.text(authorityId); this.clock = java.util.Objects.requireNonNull(clock);
        this.borrowedSessions = borrowedSessions;
    }
    @Override public String revalidate(ContinuityState predecessor, WriterContracts.Request request) {
        throw new IllegalStateException("action qualification requires the actual original writer Head under its held lock");
    }
    @Override public String revalidate(WriterContracts.Head actualLockedHead, WriterContracts.Request request) {
        ContinuityState predecessor = actualLockedHead.state();
        ActionReceipt receipt = receipt(request);
        List<ActionReceipt> canonicalReceipts = canonicalReceipts(predecessor);
        if (!(receipt.state() instanceof ActionState.CompositeOperatorQuarantined)) CompositeOperatorQuarantinePolicy.requireNewActionAllowed(canonicalReceipts.stream().filter(value -> !value.command().actionId().equals(receipt.command().actionId())).toList(), receipt.command());
        ProtocolIdentityAdmission.requireUnique(canonicalReceipts, receipt.command());
        Optional<ActionReceipt> existing = canonicalReceipts.stream().filter(r -> r.command().actionId().equals(receipt.command().actionId())).findFirst();
        ActionTransitions.validate(existing, receipt.command(), receipt.bodySha256(), receipt.state());
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
        // This terminal has no native Attempt. The actual writer independently checks every canonical event.
        if (receipt.state() instanceof ActionState.IntentAbandoned)
            IntentAbandonmentProof.verify(predecessor, receipt, archive);
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
        ActionReceipt receipt = receipt(request);
        List<ActionReceipt> canonicalReceipts = canonicalReceipts(predecessor);
        if (!(receipt.state() instanceof ActionState.CompositeOperatorQuarantined)) CompositeOperatorQuarantinePolicy.requireNewActionAllowed(canonicalReceipts.stream().filter(value -> !value.command().actionId().equals(receipt.command().actionId())).toList(), receipt.command());
        ProtocolIdentityAdmission.requireUnique(canonicalReceipts, receipt.command());
        StrictJson.require(receipt.sequence() == Math.addExact(predecessor.sequence(), 1), "action event must consume actual next writer sequence");
        StrictJson.require(receipt.command().origin().machineId().equals(predecessor.machineId()), "action machine must equal canonical writer machine");
        Optional<ActionReceipt> existing = canonicalReceipts.stream().filter(r -> r.command().actionId().equals(receipt.command().actionId())).findFirst();
        ActionTransitions.validate(existing, receipt.command(), receipt.bodySha256(), receipt.state());
        ObjectNode next = predecessor.toJson();
        ActionRecord record = archive.loadRecord(org.xar.ck3.control.contracts.ExactRef.fromJson(request.detailsObject().get("receipt_ref")));
        StrictJson.require(record.previous().equals(ContinuityActionJournal.recordHead(predecessor)), "action record predecessor changed");
        next.set(ContinuityActionJournal.STATE_FIELD, request.detailsObject().get("receipt_ref"));
        // The one writer assigns the sequence after pure reduction and validates it again at commit.
        return ContinuityState.fromJson(next, predecessor.machineId());
    }
    @Override public <T> T withReadValidation(WriterContracts.Head actualLockedHead, WriterContracts.Request request,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.SessionWork<T> work) throws java.io.IOException {
        java.util.Objects.requireNonNull(actualLockedHead); java.util.Objects.requireNonNull(request);
        java.util.Objects.requireNonNull(same); java.util.Objects.requireNonNull(work);
        if (borrowedSessions == null) return work.run(same);
        ActionReceipt proposed = receipt(request);
        PhysicalActionRegistry physical = physicalActions;
        // Only the observed ordinary pre-dispatch path is widened. Terminal/domain/physical callbacks keep their old scopes.
        if (!(proposed.state() instanceof ActionState.IntentDurable || proposed.state() instanceof ActionState.Submitting)
                || proposed.command().expectation() instanceof CommandExpectation.OperatorRebind
                || physical != null && physical.find(proposed.command().operation()).isPresent())
            return work.run(same);
        StrictJson.require(validationHead.get() == null && validationSession.get() == null && validationArchive.get() == null,
                "read validation cannot nest a separate writer/head scope");
        StrictJson.require(borrowedSessions.get() == same, "read validation must borrow the identical original writer Session");
        requireValidationHead(actualLockedHead, same);
        return archive.inHistoricalReadScope(same, new ActionPorts.HistoricalReadLimits(4096, 256L * 1024 * 1024, 8192), scoped -> {
            try {
                validationHead.set(actualLockedHead); validationSession.set(same); validationArchive.set(scoped);
                requireValidationHead(actualLockedHead, same);
                T result = work.run(same);
                requireValidationHead(actualLockedHead, same);
                return result;
            } finally {
                validationArchive.remove(); validationSession.remove(); validationHead.remove();
            }
        });
    }
    private static void requireValidationHead(WriterContracts.Head captured,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) throws java.io.IOException {
        WriterContracts.Head actual = same.head();
        StrictJson.require(java.util.Arrays.equals(captured.state().canonicalBytes(), actual.state().canonicalBytes())
                && captured.documents().equals(actual.documents()) && captured.absent().equals(actual.absent())
                && captured.indexRepairs().equals(actual.indexRepairs())
                && captured.snapshotNeedsRecovery() == actual.snapshotNeedsRecovery(),
                "read validation left its exact original captured writer head");
    }
    private List<ActionReceipt> canonicalReceipts(ContinuityState predecessor) {
        WriterContracts.Head captured = validationHead.get();
        if (captured != null) {
            var same = validationSession.get();
            var scoped = validationArchive.get();
            StrictJson.require(same != null && scoped != null && borrowedSessions != null && borrowedSessions.get() == same,
                    "canonical history requires the same live validation Session/archive");
            try { requireValidationHead(captured, same); }
            catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
            StrictJson.require(java.util.Arrays.equals(predecessor.canonicalBytes(), captured.state().canonicalBytes()),
                    "canonical history changed its validation predecessor");
            // Re-run the complete original traversal and every mutable read check; only the still-live scope is shared.
            return ContinuityActionJournal.receipts(predecessor, scoped);
        }
        if (borrowedSessions == null) return ContinuityActionJournal.receipts(predecessor, archive);
        try {
            var same = java.util.Objects.requireNonNull(borrowedSessions.get());
            return archive.inHistoricalReadScope(same, new ActionPorts.HistoricalReadLimits(4096, 256L * 1024 * 1024, 8192),
                    scoped -> ContinuityActionJournal.receipts(predecessor, scoped));
        } catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
    }
    private ActionReceipt receipt(WriterContracts.Request request) {
        StrictJson.require(request.kind().equals(ContinuityActionJournal.KIND), "wrong reducer event kind");
        ObjectNode details = StrictJson.object(request.detailsObject(), Set.of("evidence_id", "source", "receipt_ref"));
        ActionReceipt receipt = archive.loadRecord(org.xar.ck3.control.contracts.ExactRef.fromJson(details.get("receipt_ref"))).receipt();
        StrictJson.require(ActionCodec.text(details, "evidence_id").equals(receipt.command().actionId() + ":" + receipt.sequence())
                && details.get("source").equals(ProposalLifecycleCodec.source(receipt.command().source())), "action event source/identity drift"); return receipt;
    }
}
