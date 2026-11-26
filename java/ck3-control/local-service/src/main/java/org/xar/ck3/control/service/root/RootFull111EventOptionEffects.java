package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
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
        if (!(dispatch instanceof AckReceived selected) || !selected.nativeOk() || ActionReconciliationScope.activeFor(command))
            return pending(attempt, "Full111 queue proof requires the known positive SELECT in its original held connection");
        try {
            var selectedCustody = custody(selected);
            selectedCustody.verify(selected, attempt.guard());
            var deadline = selectedCustody.responseReceived().observedAt().plus(ActionObservationWindow.MAXIMUM_WINDOW);
            if (!context.clock().instant().isBefore(deadline))
                return pending(attempt, "Full111 queue observation window expired after SELECT");
            if (!(transport.readFreshFullState(deadline) instanceof NativeFreshSnapshotPort.Received fresh))
                return pending(attempt, "Full111 independent post-SELECT snapshot unavailable");
            NativeFreshSnapshotPort.verifyAfter(selected, fresh);
            var proof = transport.readFull111EventQueue(attempt, selected, deadline);
            if (proof.isEmpty() || proof.orElseThrow().after() != fresh.originalFrame())
                return pending(attempt, "Full111 independent complete queue did not verify the selected instance absent");
            var queue = proof.orElseThrow();
            var same = context.borrowedSession();
            var archive = context.archive().withSession(same);
            var before = RootGuardEvidence.loadFrame(attempt.guard(), archive, context.frameLoader());
            return context.remainingDomains().lifecycle().physical().withReceivedSnapshot(same, deadline, fresh.originalFrame(), lease -> {
                var after = lease.ordinary().orElseThrow(() -> new IOException("No complete Full111 ordinary after observation"));
                var frames = new NativeEffectSnapshots.Pair(before, after);
                var projected = project(command, attempt, frames, selected, fresh.acknowledgement(), fresh.snapshotReceived(),
                        queue.original(), archive, List.of());
                var originals = new Originals(archive.preserve(selected), archive.preserve(fresh.acknowledgement()),
                        fresh.snapshotReceived(), archive.preserve(queue.original()));
                var material = archive.preserveMaterial(originals.encode());
                var basis = NativeEffectEvidence.preserve(command, attempt, frames, List.of(),
                        projected.compatibleResult().orElseThrow(), List.of(material), archive);
                return NativeEffectSnapshots.withEvidence(projected, List.of(basis, material));
            });
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return pending(attempt, "Full111 independent after observation interrupted");
        } catch (IOException | UncheckedIOException | ContractViolationException unavailable) {
            return pending(attempt, "Full111 queue or exact after originals unavailable: " + unavailable.getMessage());
        }
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
        StrictJson.require(original.independentReads().isEmpty() && original.supportingMaterials().size() == 1
                && original.reconciliationGuard().isEmpty(), "Full111 option requires its one same-connection queue proof");
        var settled = (ActionState.Settled) receipt.state();
        var proof = Originals.decode(archive.loadMaterial(original.supportingMaterials().getFirst()));
        var selected = originalAck(archive, proof.selected());
        StrictJson.require(selected.equals(settled.dispatch()), "Full111 option proof changed its canonical original SELECT");
        var applied = (ActionState.Applied) settled.settlement();
        var projected = project(receipt.command(), settled.attempt(), original.frames(), selected,
                originalAck(archive, proof.fresh()), proof.snapshotReceived(), originalAck(archive, proof.queue()),
                archive, applied.observation().supportingEvidence());
        NativeEffectEvidence.requireSame(settled.settlement(), projected, original.compatibleResult());
        return original;
    }

    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt,
            NativeEffectSnapshots.Pair frames, AckReceived selected, AckReceived fresh, NativeRequestChronology.Event snapshotReceived,
            AckReceived queue, OutcomeArchive archive, List<ExactRef> supporting) throws IOException {
        var target = RootFull111EventOptionPreparation.target(command);
        var selection = Request.decodeSelectionRequest(attempt.preparedRequest());
        var expectedAt = Instant.ofEpochMilli(command.deadline().toEpochMilli());
        StrictJson.require(command.operation().value().equals(Action.SELECT.step()) && command.expected().observerSchema().equals(SCHEMA)
                && selection.target().equals(target) && selection.deadline().equals(expectedAt)
                && frames.before().identity().equals(command.before())
                && frames.before().connectionGeneration().equals(attempt.guard().connectionGeneration())
                && selection.lineage().sourceRevision().equals(command.before().frame().identity().nativeRevision()),
                "Full111 option proof crossed its original command, target, deadline or private Native revision");
        var before = full(frames.before());
        var after = full(frames.after());
        var sampled = requireQueue(attempt, selected, fresh, before, after, snapshotReceived, queue);

        var beforeRaw = NativeWire.object(NativeWire.parse(before.state().bytes()));
        var afterRaw = NativeWire.object(NativeWire.parse(after.state().bytes()));
        var foreground = NativeFull111OrdinaryEvent.read(beforeRaw).orElseThrow(() -> new IOException("Original Full111 foreground absent"));
        StrictJson.require(foreground.instanceId() == target.instanceId() && target.authoredOptionIndex() < foreground.authoredOptionCount()
                && RootFull111EventRead.prefix(beforeRaw).equals(selection.core().prefix())
                && RootFull111EventRead.prefix(afterRaw).equals(sampled.core().prefix())
                && NativeFull111OrdinaryEvent.read(afterRaw).filter(event -> event.instanceId() == target.instanceId()).isEmpty(),
                "Exact Full111 foreground, living actor or Core differs from original SELECT and complete queue data");
        requirePreparation(command, attempt, selected, selection, foreground, archive);

        var actual = CurrentFull111EventOption.decodeOutcome(queue).target().orElseThrow();
        return NativeEffectSnapshots.observed(command, attempt, frames.after(), SCHEMA,
                values(actual, after.session().connectionGeneration()), new ObservationProvenance.Query(queue.requestId()),
                compatible(command, frames.after(), actual), supporting);
    }

    static Request requireQueue(ActionState.Attempt attempt, AckReceived selected, AckReceived fresh, ObservedFrame before,
            ObservedFrame after, NativeRequestChronology.Event snapshotReceived, AckReceived queue) throws IOException {
        var sampled = Request.decodeQueueRequest(queue);
        StrictJson.require(CurrentFull111EventOption.confirmsAbsence(attempt, selected, sampled, queue),
                "Original Full111 queue did not independently prove complete absence of the selected instance");
        NativeFreshSnapshotPort.verifyAfterOriginal(selected, fresh, after, snapshotReceived);
        var freshCustody = custody(fresh);
        var queueCustody = custody(queue);
        var deadline = custody(selected).responseReceived().observedAt().plus(ActionObservationWindow.MAXIMUM_WINDOW);
        var selectedOwner = CurrentFull111EventOption.decodeOutcome(selected).owner().orElseThrow();
        var queueOwner = CurrentFull111EventOption.decodeOutcome(queue).owner().orElseThrow();
        StrictJson.require(before.session().equals(queueCustody.session()) && after.nativeRevision().compareTo(before.nativeRevision()) > 0
                && follows(freshCustody.responseReceived(), queueCustody.writeEntered())
                && queueOwner.ticketSequence().compareTo(selectedOwner.ticketSequence()) > 0
                && !sampled.deadline().isAfter(deadline), "Full111 queue escaped the exact later Full or original observation window");
        return sampled;
    }

    private static void requirePreparation(ActionCommand command, ActionState.Attempt attempt, AckReceived selected,
            Request selection, NativeFull111OrdinaryEvent foreground, OutcomeArchive archive) throws IOException {
        var refs = attempt.preparedRequest().preparationEvidence();
        StrictJson.require(refs.size() == 2 && refs.getFirst().equals(RootFull111EventOptionPreparation.rendererOriginal(command)),
                "Full111 option requires its command renderer and native prepare originals");
        var renderer = originalAck(archive, refs.getFirst());
        var prepared = originalAck(archive, refs.getLast());
        var rendererModel = CurrentFull111EventRenderer.decodeOutcome(renderer);
        var rendered = rendererModel.source().orElseThrow(() -> new IOException("Full111 renderer evidence unavailable"));
        var selectionLineage = selection.lineage();
        var claimed = new Lineage(selectionLineage.sourceRevision(), renderer.requestId(), rendererModel.providerGeneration(),
                rendererModel.querySequence(), Optional.empty(), BigInteger.ZERO, Optional.empty(), BigInteger.ZERO);
        var originalPrepare = new Request(Action.PREPARE, selection.core(), selection.target(), claimed, selection.deadline());
        var preparedResult = CurrentFull111EventOption.decodeOutcome(prepared);
        var rendererOrder = custody(renderer);
        var prepareOrder = custody(prepared);
        var selectOrder = custody(selected);
        var rendererOwner = rendererModel.owner().orElseThrow();
        var prepareOwner = preparedResult.owner().orElseThrow();
        var selectOwner = CurrentFull111EventOption.decodeOutcome(selected).owner().orElseThrow();
        StrictJson.require(rendererOrder.session().equals(selectOrder.session()) && prepareOrder.session().equals(selectOrder.session())
                && rendererOrder.custodyEpoch().equals(selectOrder.custodyEpoch()) && prepareOrder.custodyEpoch().equals(selectOrder.custodyEpoch())
                && follows(rendererOrder.responseReceived(), prepareOrder.writeEntered())
                && follows(prepareOrder.responseReceived(), selectOrder.writeEntered())
                && rendererOwner.connectionGeneration().equals(selectOrder.session().connectionGeneration())
                && prepareOwner.connectionGeneration().equals(selectOrder.session().connectionGeneration())
                && prepareOwner.ticketSequence().compareTo(rendererOwner.ticketSequence()) > 0
                && selectOwner.ticketSequence().compareTo(prepareOwner.ticketSequence()) > 0
                && selection.target().matchesSelectable(rendered) && foreground.authoredOptionCount() == rendered.authoredOptionCount()
                && rendererModel.factsBefore().filter(selection.core().prefix()::equals).isPresent()
                && CurrentFull111EventOption.rendererDeadline(renderer).equals(selection.deadline())
                && preparedResult.matchesSuccessfulRequest(originalPrepare)
                && preparedResult.lineage().filter(selectionLineage::equals).isPresent()
                && Arrays.equals(prepared.outbound().orElseThrow().originalPacket(), originalPrepare.readPacket(prepared.requestId())),
                "Full111 option prepared target or native lease differs from its exact renderer and prepare originals");
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
