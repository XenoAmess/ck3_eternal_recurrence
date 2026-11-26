package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionObservationWindow;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionReconciliationScope;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.NativeActionPort.DispatchOutcome;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeFull111OrdinaryEvent;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.Action;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.Lineage;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.Request;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.Target;
import org.xar.ck3.control.nativebridge.CurrentFull111EventRenderer;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Settles only the disappearance of the exact selected Full111 runtime event instance. */
final class RootFull111EventOptionEffects implements NativeEffectRegistry.Observer {
    static final String SCHEMA = "xar.ck3.full111-event-queue-postcondition/v2";
    private static final String ORIGINAL_SCHEMA = "xar.java-full111-event-queue-proof/v2";
    static final String RESULT_SCHEMA = "xar.java-full111-event-option-result/v2";

    private final RootRuntimeContext context;
    private final NativeGameTransport transport;

    RootFull111EventOptionEffects(RootRuntimeContext context, NativeGameTransport transport) {
        this.context = Objects.requireNonNull(context);
        this.transport = Objects.requireNonNull(transport);
    }

    static ExpectedPostcondition expected(PlanningRequest request, int instanceId, String definitionKey, int authoredOptionIndex) {
        return expected(request, new Target(instanceId, request.before().frame().identity().player().intValueExact(),
                definitionKey, authoredOptionIndex));
    }

    static ExpectedPostcondition expected(PlanningRequest request, Target target) {
        var diagnostics = OpportunityJson.object(request.observations().snapshot().get("diagnostics"), "diagnostics");
        var connection = OpportunityJson.integer(diagnostics.get("connection_generation"), "connection_generation");
        StrictJson.require(target.recipientCharacterId() == request.before().frame().identity().player().intValueExact()
                && connection.signum() > 0 && connection.compareTo(StrictJson.UINT64_MAX) <= 0,
                "Full111 option target requires this actual actor and connection");
        return new ExpectedPostcondition(1, request.before(), request.source(), SCHEMA, values(target, connection));
    }

    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, DispatchOutcome dispatch) {
        if (!(dispatch instanceof AckReceived selected) || !selected.nativeOk())
            return pending(attempt, "Full111 queue proof requires the known positive SELECT in its original held connection");
        try {
            var selectedCustody = custody(selected);
            selectedCustody.verify(selected, attempt.guard());
            var same = context.borrowedSession();
            var archive = context.archive().withSession(same);
            if (ActionReconciliationScope.activeFor(command))
                return context.reconciliation().currentForCommand(same, command,
                        lease -> recover(command, attempt, selected, lease, archive));

            var deadline = selectedCustody.responseReceived().observedAt().plus(ActionObservationWindow.MAXIMUM_WINDOW);
            if (!context.clock().instant().isBefore(deadline))
                return pending(attempt, "Full111 queue observation window expired after SELECT");
            var snapshot = transport.readFreshFullState(deadline);
            if (snapshot instanceof NativeFreshSnapshotPort.Unavailable unavailable)
                return pendingAfterRead(attempt, "Full111 independent post-SELECT snapshot unavailable: " + unavailable.reason(),
                        archive, unavailable);
            var fresh = (NativeFreshSnapshotPort.Received) snapshot;
            NativeFreshSnapshotPort.verifyAfter(selected, fresh);
            var proof = transport.readFull111EventQueue(attempt, selected, deadline);
            if (proof.isEmpty() || proof.orElseThrow().after() != fresh.originalFrame())
                return pendingAfterRead(attempt, "Full111 independent complete queue did not verify the selected instance absent",
                        archive, fresh);
            var queue = proof.orElseThrow();
            var before = RootGuardEvidence.loadFrame(attempt.guard(), archive, context.frameLoader());
            return context.remainingDomains().lifecycle().physical().withReceivedSnapshot(same, deadline, fresh.originalFrame(), lease -> {
                var after = lease.ordinary().orElseThrow(() -> new IOException("No complete Full111 ordinary after observation"));
                return settle(command, attempt, new NativeEffectSnapshots.Pair(before, after), selected,
                        fresh.acknowledgement(), fresh.snapshotReceived(), queue.original(), archive, deadline);
            });
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return pending(attempt, "Full111 independent after observation interrupted");
        } catch (IOException | UncheckedIOException | ContractViolationException unavailable) {
            return pending(attempt, "Full111 queue or exact after originals unavailable: " + unavailable.getMessage());
        }
    }

    private NativeEffectRegistry.Projected recover(ActionCommand command, ActionState.Attempt attempt, AckReceived selected,
            RootReconciliationAuthority.Lease lease, OutcomeArchive archive) throws IOException {
        var after = ActionReconciliationScope.requireFrame(command, attempt);
        var guard = ActionReconciliationScope.requireObservationGuard(command, attempt);
        var identity = guard.origin().requireReconciliation();
        var provenance = ActionReconciliationScope.requireProvenance(command, attempt);
        StrictJson.require(after == lease.complete() && guard.equals(lease.observationGuard())
                && identity.equals(lease.identity()) && provenance.equals(lease.provenance())
                && attempt.equals(lease.attempt()), "Full111 recovery changed its actual pending observer or frame");
        if (!(provenance instanceof ObservationProvenance.FreshSnapshotQuery read)
                || !(read.basis() instanceof ObservationProvenance.ColdAfterAcknowledgement original)
                || !original.originalReceipt().equals(identity.pending().originalReceipt()))
            return pending(attempt, "Full111 recovery requires its already authenticated post-SELECT snapshot");
        requirePendingOriginal(lease.canonical(), command, attempt, selected);
        var fresh = originalAck(archive, read.readAcknowledgement());
        StrictJson.require(read.requestId().equals(fresh.requestId()), "Full111 recovery changed its original Full query");
        var actual = lease.fullSnapshot().actual();
        NativeFreshSnapshotPort.verifyAfterOriginal(selected, fresh, actual, read.snapshotReceived());
        var deadline = recoveryEnd(command, guard);
        try {
            var proof = transport.readFull111EventQueue(attempt, selected, deadline);
            if (proof.isEmpty() || proof.orElseThrow().after() != actual)
                return pending(attempt, "Full111 recovery did not verify absence in the complete original queue");
            var frames = new NativeEffectSnapshots.Pair(lease.before(), after, Optional.of(identity));
            return settle(command, attempt, frames, selected, fresh, read.snapshotReceived(),
                    proof.orElseThrow().original(), archive, deadline);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return pending(attempt, "Full111 queue reconciliation interrupted");
        }
    }

    private static NativeEffectRegistry.Projected settle(ActionCommand command, ActionState.Attempt attempt,
            NativeEffectSnapshots.Pair frames, AckReceived selected, AckReceived fresh, NativeRequestChronology.Event snapshotReceived,
            AckReceived queue, OutcomeArchive archive, Instant deadline) throws IOException {
        var projected = project(command, attempt, frames, selected, fresh, snapshotReceived, queue, archive, deadline, List.of());
        var originals = new Originals(archive.preserve(selected), archive.preserve(fresh), snapshotReceived, archive.preserve(queue));
        var material = archive.preserveMaterial(originals.encode());
        var basis = NativeEffectEvidence.preserve(command, attempt, frames, List.of(),
                projected.compatibleResult().orElseThrow(), List.of(material), archive);
        return NativeEffectSnapshots.withEvidence(projected, List.of(basis, material));
    }

    static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef definitionSource,
            NativeEffectEvidence.FrameLoader frames) {
        return new NativeRecordedEvidenceVerifier.Binding(operation, definitionSource, (head, receipt, archive) -> {
            try { replay(receipt, archive, frames); }
            catch (IOException unavailable) { throw new UncheckedIOException("Full111 option queue replay could not verify originals", unavailable); }
        });
    }

    static NativeEffectEvidence.Original replay(ActionReceipt receipt, OutcomeArchive archive,
            NativeEffectEvidence.FrameLoader frames) throws IOException {
        var original = NativeEffectEvidence.load(receipt, archive, frames);
        StrictJson.require(original.independentReads().isEmpty() && original.supportingMaterials().size() == 1,
                "Full111 option requires its one same-connection queue proof");
        var settled = (ActionState.Settled) receipt.state();
        var proof = Originals.decode(archive.loadMaterial(original.supportingMaterials().getFirst()));
        var selected = originalAck(archive, proof.selected());
        StrictJson.require(selected.equals(settled.dispatch()), "Full111 option proof changed its canonical original SELECT");
        Instant deadline = observationEnd(selected);
        if (original.reconciliationGuard().isPresent()) {
            var guard = original.reconciliationGuard().orElseThrow();
            var reference = guard.origin().requireReconciliation().pending().originalReceipt();
            var pending = archive.loadReceipt(reference);
            StrictJson.require(reference.equals(archive.receiptReferenceOf(pending)),
                    "Full111 option recovery lost its exact original pending receipt");
            requirePendingOriginal(pending, receipt.command(), settled.attempt(), selected);
            deadline = recoveryEnd(receipt.command(), guard);
        }
        var applied = (ActionState.Applied) settled.settlement();
        var projected = project(receipt.command(), settled.attempt(), original.frames(), selected,
                originalAck(archive, proof.fresh()), proof.snapshotReceived(), originalAck(archive, proof.queue()),
                archive, deadline, applied.observation().supportingEvidence());
        NativeEffectEvidence.requireSame(settled.settlement(), projected, original.compatibleResult());
        return original;
    }

    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt,
            NativeEffectSnapshots.Pair frames, AckReceived selected, AckReceived fresh, NativeRequestChronology.Event snapshotReceived,
            AckReceived queue, OutcomeArchive archive, Instant deadline, List<ExactRef> supporting) throws IOException {
        var target = RootFull111EventOptionPreparation.target(command);
        var selection = Request.decodeSelectionRequest(attempt.preparedRequest());
        StrictJson.require(command.operation().value().equals(Action.SELECT.step()) && command.expected().observerSchema().equals(SCHEMA)
                && selection.target().equals(target) && !selection.deadline().isAfter(command.deadline())
                && frames.before().identity().equals(command.before())
                && frames.before().connectionGeneration().equals(attempt.guard().connectionGeneration())
                && selection.lineage().sourceRevision().equals(command.before().frame().identity().nativeRevision()),
                "Full111 option proof crossed its original command, target, deadline or private Native revision");
        var before = full(frames.before());
        var after = full(frames.after());
        var sampled = requireQueue(attempt, selected, fresh, before, after, snapshotReceived, queue, deadline);

        var beforeRaw = NativeWire.object(NativeWire.parse(before.state().bytes()));
        var afterRaw = NativeWire.object(NativeWire.parse(after.state().bytes()));
        var foreground = NativeFull111OrdinaryEvent.read(beforeRaw).orElseThrow(() -> new IOException("Original Full111 foreground absent"));
        StrictJson.require(foreground.instanceId() == target.instanceId() && target.authoredOptionIndex() < foreground.authoredOptionCount()
                && RootFull111EventRead.prefix(beforeRaw).equals(selection.core().prefix())
                && RootFull111EventRead.prefix(afterRaw).equals(sampled.core().prefix())
                && NativeFull111OrdinaryEvent.read(afterRaw).filter(event -> event.instanceId() == target.instanceId()).isEmpty(),
                "Exact Full111 foreground, living actor or Core differs from original SELECT and complete queue data");
        requirePreparation(command, attempt, selected, selection, foreground, before.observedAt(), archive);

        var actual = CurrentFull111EventOption.decodeOutcome(queue).target().orElseThrow();
        return NativeEffectSnapshots.observed(command, attempt, frames.after(), SCHEMA,
                values(actual, after.session().connectionGeneration()), new ObservationProvenance.Query(queue.requestId()),
                compatible(command, frames.after(), actual), supporting);
    }

    static Request requireQueue(ActionState.Attempt attempt, AckReceived selected, AckReceived fresh, ObservedFrame before,
            ObservedFrame after, NativeRequestChronology.Event snapshotReceived, AckReceived queue) throws IOException {
        return requireQueue(attempt, selected, fresh, before, after, snapshotReceived, queue, observationEnd(selected));
    }

    static Request requireQueue(ActionState.Attempt attempt, AckReceived selected, AckReceived fresh, ObservedFrame before,
            ObservedFrame after, NativeRequestChronology.Event snapshotReceived, AckReceived queue, Instant deadline) throws IOException {
        var sampled = Request.decodeQueueRequest(queue);
        StrictJson.require(CurrentFull111EventOption.confirmsAbsence(attempt, selected, sampled, queue),
                "Original Full111 queue did not independently prove complete absence of the selected instance");
        NativeFreshSnapshotPort.verifyAfterOriginal(selected, fresh, after, snapshotReceived);
        var freshCustody = custody(fresh);
        var queueCustody = custody(queue);
        var selectedOwner = CurrentFull111EventOption.decodeOutcome(selected).owner().orElseThrow();
        var queueOwner = CurrentFull111EventOption.decodeOutcome(queue).owner().orElseThrow();
        StrictJson.require(before.session().equals(queueCustody.session()) && after.nativeRevision().compareTo(before.nativeRevision()) > 0
                && follows(freshCustody.responseReceived(), queueCustody.writeEntered())
                && queueOwner.ticketSequence().compareTo(selectedOwner.ticketSequence()) > 0
                && !sampled.deadline().isAfter(deadline), "Full111 queue escaped the exact later Full or original observation window");
        return sampled;
    }

    static void requirePendingOriginal(ActionReceipt pending, ActionCommand command, ActionState.Attempt attempt, AckReceived selected) {
        StrictJson.require((pending.state() instanceof ActionState.Unknown || pending.state() instanceof ActionState.AckReceived)
                && !pending.settled() && pending.command().equals(command)
                && ActionTransitions.attempt(pending.state()).filter(attempt::equals).isPresent()
                && selected.nativeOk() && pending.ack().filter(selected::equals).isPresent(),
                "Full111 recovery requires the exact pending command, attempt and positive SELECT");
    }

    private static Instant observationEnd(AckReceived selected) throws IOException {
        return custody(selected).responseReceived().observedAt().plus(ActionObservationWindow.MAXIMUM_WINDOW);
    }

    private static Instant recoveryEnd(ActionCommand command, GuardEvidence guard) {
        StrictJson.require(!guard.validUntil().isAfter(command.deadline()),
                "Full111 recovery exceeded its original ordinary batch deadline");
        return guard.validUntil();
    }

    private static void requirePreparation(ActionCommand command, ActionState.Attempt attempt, AckReceived selected,
            Request selection, NativeFull111OrdinaryEvent foreground, Instant beforeObservedAt, OutcomeArchive archive) throws IOException {
        var refs = attempt.preparedRequest().preparationEvidence();
        StrictJson.require(refs.size() == 3 && refs.getFirst().equals(RootFull111EventOptionPreparation.rendererOriginal(command)),
                "Full111 option requires its planned renderer, fresh renderer and native prepare originals");
        requirePreparedRenderers(command.deadline(), beforeObservedAt, selection, foreground,
                originalAck(archive, refs.getFirst()), originalAck(archive, refs.get(1)), originalAck(archive, refs.getLast()), selected);
    }

    static void requirePreparedRenderers(Instant commandDeadline, Instant beforeObservedAt, Request selection,
            NativeFull111OrdinaryEvent foreground, AckReceived planned, AckReceived fresh, AckReceived prepared,
            AckReceived selected) throws IOException {
        var plannedModel = CurrentFull111EventRenderer.decodeOutcome(planned);
        var freshModel = CurrentFull111EventRenderer.decodeOutcome(fresh);
        var rendered = freshModel.source().orElseThrow(() -> new IOException("Full111 fresh renderer evidence unavailable"));
        var selectionLineage = selection.lineage();
        var claimed = new Lineage(selectionLineage.sourceRevision(), fresh.requestId(), freshModel.providerGeneration(),
                freshModel.querySequence(), Optional.empty(), BigInteger.ZERO, Optional.empty(), BigInteger.ZERO);
        var originalPrepare = new Request(Action.PREPARE, selection.core(), selection.target(), claimed, selection.deadline());
        var preparedResult = CurrentFull111EventOption.decodeOutcome(prepared);
        var selectedResult = CurrentFull111EventOption.decodeOutcome(selected);
        var plannedOrder = custody(planned);
        var freshOrder = custody(fresh);
        var prepareOrder = custody(prepared);
        var selectOrder = custody(selected);
        var plannedOwner = plannedModel.owner().orElseThrow();
        var freshOwner = freshModel.owner().orElseThrow();
        var prepareOwner = preparedResult.owner().orElseThrow();
        var selectOwner = selectedResult.owner().orElseThrow();
        StrictJson.require(List.of(planned.requestId(), fresh.requestId(), prepared.requestId(), selected.requestId()).stream().distinct().count() == 4
                && List.of(plannedOrder, freshOrder, prepareOrder).stream().allMatch(order -> order.session().equals(selectOrder.session())
                    && order.custodyEpoch().equals(selectOrder.custodyEpoch()))
                && !plannedOrder.writeEntered().observedAt().isBefore(beforeObservedAt)
                && follows(plannedOrder.responseReceived(), freshOrder.writeEntered())
                && follows(freshOrder.responseReceived(), prepareOrder.writeEntered())
                && follows(prepareOrder.responseReceived(), selectOrder.writeEntered())
                && plannedOwner.connectionGeneration().equals(selectOrder.session().connectionGeneration())
                && freshOwner.connectionGeneration().equals(selectOrder.session().connectionGeneration())
                && prepareOwner.connectionGeneration().equals(selectOrder.session().connectionGeneration())
                && freshOwner.ticketSequence().compareTo(plannedOwner.ticketSequence()) > 0
                && prepareOwner.ticketSequence().compareTo(freshOwner.ticketSequence()) > 0
                && selectOwner.ticketSequence().compareTo(prepareOwner.ticketSequence()) > 0
                && CurrentFull111EventOption.matchesPlannedRenderer(plannedModel, freshModel, selection.target())
                && rendered.options().stream().filter(CurrentFull111EventRenderer.Option::widgetVisible).findFirst()
                    .filter(first -> first.authoredOptionIndex() == selection.target().authoredOptionIndex()
                        && first.nativeCanSelect() && first.widgetEnabled()).isPresent()
                && foreground.instanceId() == rendered.instanceId() && foreground.authoredOptionCount() == rendered.authoredOptionCount()
                && freshModel.factsBefore().filter(selection.core().prefix()::equals).isPresent(),
                "Full111 option changed its planned stock source or the same-owner fresh renderer sequence");

        var plannedUntil = CurrentFull111EventOption.rendererDeadline(planned);
        var freshUntil = CurrentFull111EventOption.rendererDeadline(fresh);
        StrictJson.require(!plannedUntil.isAfter(commandDeadline) && !freshUntil.isAfter(commandDeadline)
                && !freshUntil.isAfter(freshOrder.writeEntered().observedAt().plus(CurrentFull111EventOption.RENDERER_RENEWAL_WINDOW))
                && plannedOrder.writeEntered().observedAt().isBefore(plannedUntil)
                && !plannedOrder.responseReceived().observedAt().isAfter(plannedUntil)
                && freshOrder.writeEntered().observedAt().isBefore(freshUntil)
                && !freshOrder.responseReceived().observedAt().isAfter(freshUntil)
                && !prepareOrder.responseReceived().observedAt().isAfter(freshUntil)
                && selectOrder.writeEntered().observedAt().isBefore(freshUntil)
                && freshUntil.equals(selection.deadline())
                && preparedResult.matchesSuccessfulRequest(originalPrepare)
                && preparedResult.lineage().filter(selectionLineage::equals).isPresent()
                && selectedResult.matchesSuccessfulRequest(selection)
                && Arrays.equals(prepared.outbound().orElseThrow().originalPacket(), originalPrepare.readPacket(prepared.requestId())),
                "Full111 option changed or exceeded its exact fresh renderer and prepare deadlines");
    }

    private static ObservedFrame full(Complete frame) throws IOException {
        return frame.originalProjection().orElseThrow(() -> new IOException("Original Full111 profile projection unavailable")).actual();
    }

    private static AckReceived originalAck(OutcomeArchive archive, ExactRef ref) throws IOException {
        if (archive.load(ref) instanceof AckReceived ack && ref.equals(archive.referenceOf(ack))) {
            custody(ack);
            return ack;
        }
        throw new IOException("Full111 option lost an exact retained native acknowledgement");
    }

    private static NativeRequestChronology custody(AckReceived ack) throws IOException {
        var original = ack.custody().orElseThrow(() -> new IOException("Full111 option native chronology unavailable"));
        original.verify(ack);
        return original;
    }

    private static boolean follows(NativeRequestChronology.Event before, NativeRequestChronology.Event after) {
        return after.order().compareTo(before.order()) > 0 && !after.observedAt().isBefore(before.observedAt());
    }

    private static List<ExpectedValue> values(Target target, BigInteger connection) {
        return List.of(new ExpectedInteger(new FieldKey("event_instance_id"), BigInteger.valueOf(target.instanceId())),
                new ExpectedInteger(new FieldKey("recipient_character_id"), BigInteger.valueOf(target.recipientCharacterId())),
                new ExpectedText(new FieldKey("event_definition_key"), target.definitionKey()),
                new ExpectedInteger(new FieldKey("authored_option_index"), BigInteger.valueOf(target.authoredOptionIndex())),
                new ExpectedBoolean(new FieldKey("event_queue_absent"), true),
                new ExpectedText(new FieldKey("connection_generation_decimal"), connection.toString()));
    }

    private static RawJson compatible(ActionCommand command, Complete after, Target observed) {
        var result = StrictJson.object().put("schema", RESULT_SCHEMA).put("step", command.operation().value())
                .put("progress_status", "postcondition").put("old_event_instance_id", observed.instanceId())
                .put("recipient_character_id", observed.recipientCharacterId()).put("event_definition_key", observed.definitionKey())
                .put("selected_native_option_index", observed.authoredOptionIndex()).put("event_queue_absent", true);
        result.set("active_event", OpportunityJson.toNode(after.semantic().get("active_event")));
        return new RawJson(StrictJson.canonical(result));
    }

    private static NativeEffectRegistry.Projected pending(ActionState.Attempt attempt, String reason) {
        return NativeEffectRegistry.Projected.pending(reason, List.of(attempt.guard().nativeEvidence()));
    }

    static NativeEffectRegistry.Projected pendingAfterRead(ActionState.Attempt attempt, String reason, OutcomeArchive archive,
            NativeFreshSnapshotPort.Result read) {
        var evidence = new LinkedHashSet<ExactRef>();
        evidence.add(attempt.guard().nativeEvidence());
        evidence.add(archive.preserve(read.dispatch()));
        var frame = switch (read) {
            case NativeFreshSnapshotPort.Received received -> Optional.of(received.originalFrame());
            case NativeFreshSnapshotPort.Unavailable unavailable -> unavailable.originalFrame();
        };
        frame.map(archive::preserveNativeFrame).ifPresent(evidence::add);
        return NativeEffectRegistry.Projected.pending(reason, List.copyOf(evidence));
    }

    record Originals(ExactRef selected, ExactRef fresh, NativeRequestChronology.Event snapshotReceived, ExactRef queue) {
        Originals {
            Set.of(selected, fresh, queue);
            Objects.requireNonNull(snapshotReceived);
        }

        RawJson encode() {
            var row = StrictJson.object().put("schema", ORIGINAL_SCHEMA).put("snapshot_order", snapshotReceived.order().toString())
                    .put("snapshot_observed_at", snapshotReceived.observedAt().toString());
            row.set("selected_ack", selected.toJson());
            row.set("fresh_full_ack", fresh.toJson());
            row.set("queue_ack", queue.toJson());
            return new RawJson(StrictJson.canonical(row));
        }

        static Originals decode(RawJson original) {
            var row = StrictJson.object(StrictJson.parse(original.bytes()), Set.of("schema", "selected_ack", "fresh_full_ack", "queue_ack",
                    "snapshot_order", "snapshot_observed_at"));
            var order = StrictJson.text(row.get("snapshot_order"));
            StrictJson.require(ORIGINAL_SCHEMA.equals(StrictJson.text(row.get("schema"))) && order.matches("[1-9][0-9]{0,19}"),
                    "Unknown Full111 event queue proof or invalid native snapshot order");
            var result = new Originals(ExactRef.fromJson(row.get("selected_ack")), ExactRef.fromJson(row.get("fresh_full_ack")),
                    new NativeRequestChronology.Event(new BigInteger(order), Instant.parse(StrictJson.text(row.get("snapshot_observed_at")))),
                    ExactRef.fromJson(row.get("queue_ack")));
            StrictJson.require(result.encode().equals(original), "Full111 event queue proof bytes lost canonical identity");
            return result;
        }
    }
}
