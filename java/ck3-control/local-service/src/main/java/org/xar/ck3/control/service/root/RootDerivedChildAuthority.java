package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceComposite;
import org.xar.ck3.control.application.battleadvance.BattleAdvancePlan;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot;
import org.xar.ck3.control.application.readiness.ReadinessAuthority.PhysicalReadLease;
import org.xar.ck3.control.application.routecontact.RouteContactComposite;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Same-Root timeline child admission and cold replay. Dynamic binding resolution alone grants nothing. */
public final class RootDerivedChildAuthority {
    private RootDerivedChildAuthority() { }

    public static Installed install(RootRuntimeContext context, RootExecutableBindings bindings,
            RootAdvanceInfrastructureFactory.Installed infrastructure) {
        Objects.requireNonNull(context); Objects.requireNonNull(bindings); Objects.requireNonNull(infrastructure);
        require(context.bindings() == bindings, "derived authority needs the actual already-bound Root inventory");
        infrastructure.requireOwner(context, bindings);
        return new Installed(context, bindings, infrastructure);
    }
    public static final class Installed {
        private final RootRuntimeContext context;
        private final RootExecutableBindings bindings;
        private final RootAdvanceInfrastructureFactory.Installed infrastructure;
        private final RootActionGuard.DerivedChildAdmission admission;
        private final NativeRecordedEvidenceVerifier.DerivedGuardVerifier replay;
        private Installed(RootRuntimeContext context, RootExecutableBindings bindings,
                RootAdvanceInfrastructureFactory.Installed infrastructure) {
            this.context = context; this.bindings = bindings; this.infrastructure = infrastructure;
            this.admission = createAdmission();
            this.replay = this::verifyArchived;
        }
        private RootActionGuard.DerivedChildAdmission createAdmission() {
            return new RootActionGuard.DerivedChildAdmission() {
                @Override public ExactRef verify(ContinuityStorePort.Session same,WriterContracts.Head head,ActionCommand child,
                        LeaseSnapshot lease,ExecutableStepBindings.InstalledStep definition,ActionPorts.OutcomeArchive archive)throws IOException {
                    return admit(same,head,child,new PhysicalReadLease(lease.frame(),lease.driver(),lease.capabilities(),lease.semantic(),
                            lease.bridgeCapabilities(),lease.originalHello(),lease.originalHeartbeat(),lease.validUntil(),lease.originalSourceQualification()),definition,archive);
                }
                @Override public ExactRef verifyPhysical(ContinuityStorePort.Session same,WriterContracts.Head head,ActionCommand child,
                        PhysicalReadLease lease,ExecutableStepBindings.InstalledStep definition,ActionPorts.OutcomeArchive archive)throws IOException {
                    require(child.operation().value().equals("pause-map"),"physical derived admission is only an exact pause child");
                    var scope=ActionChildPlanningScope.reservedParent(same,head,child).orElseThrow(
                            ()->new IOException("physical pause has no actual canonical reserved parent"));
                    var parent=ContinuityActionJournal.lookup(head.state(),scope.actionId(),archive).orElseThrow();
                    require(RootExecutableBindings.isPublicPauseParent(parent.command())
                            ||!org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(lease.frame().semantic().get("paused"),"paused"),
                            "internal physical derived admission remains limited to a running cleanup pause");
                    return admit(same,head,child,lease,definition,archive);
                }
            };
        }
        public RootActionGuard.DerivedChildAdmission admission() { return this.admission; }
        public NativeRecordedEvidenceVerifier.DerivedGuardVerifier replay() { return this.replay; }
        public void requireOwner(RootRuntimeContext actualContext, RootExecutableBindings actualBindings) {
            require(context == actualContext && bindings == actualBindings && context.bindings() == bindings,
                    "derived child authority crossed its actual Root/context/inventory");
            infrastructure.requireOwner(context, bindings);
        }
        private ExactRef admit(ContinuityStorePort.Session same, WriterContracts.Head head, ActionCommand child,
                PhysicalReadLease lease, ExecutableStepBindings.InstalledStep definition, ActionPorts.OutcomeArchive archive) throws IOException {
            requireOwner(context, bindings); context.writer().requireSession(same); unchanged(same, head);
            context.requireCurrent(child.deadline()); infrastructure.timings().requireOriginal(archive);
            require(child.origin() instanceof CommandOrigin.Gameplay && child.source().equals(context.source())
                    && child.sessionId().equals(context.game().sessionId()) && child.before().game().equals(context.game().generation()),
                    "derived child changed the actual physical Root source/Game/session");
            var scope = ActionChildPlanningScope.reservedParent(same, head, child).orElseThrow(
                    () -> new IOException("INCOMPLETE: no original same-writer composite Children callback owns this child"));
            var parent = ContinuityActionJournal.lookup(head.state(), scope.actionId(), archive).orElseThrow();
            require(parent.bodySha256().equals(scope.bodySha256()) && parent.state() instanceof ActionState.CompositeRunning,
                    "derived child lost its actual running canonical parent");
            var running = ((ActionState.CompositeRunning) parent.state()).execution();
            require(running.handlerId().equals(scope.handlerId()), "derived child escaped its actual source-owned handler");
            if(RootExecutableBindings.isPublicPauseParent(parent.command())){
                requireUnsubmitted(ContinuityActionJournal.lookup(head.state(),child.actionId(),archive),child);
                var actual=bindings.requirePublicPauseAuthority(parent.command());
                ExactRef proof=Objects.requireNonNull(actual.verifyReservedPause(same,head,child,lease,definition,archive));
                unchanged(same,head);return proof;
            }
            var parentBinding = parentBinding(parent, running.handlerId());
            requireChildDefinition(child, definition);
            requireUnsubmitted(ContinuityActionJournal.lookup(head.state(), child.actionId(), archive), child);
            var before = RootGuardEvidence.loadFrame(running.guard(), archive, context.frameLoader());
            RootGuardEvidence.requireHistory(running.guard(), archive, same);
            var previous = preceding(head.state(), parent, child, archive);
            qualify(parent, parentBinding, child, before, lease.frame(), previous, archive);
            var parentBasis = NativeEffectEvidence.basis(before); var basis = NativeEffectEvidence.basis(lease.frame());
            var verifier = bindings.actualArchivedVerifier(child.operation()).orElseThrow();
            var proof = new RootDerivedChildEvidence(head.state().sequence(), head.digest(), running.handlerId(),
                    archive.preserveReceipt(parent), parent.bodySha256(), ActionCodec.bodySha256(child), running.children().size(),
                    parentBasis.nativeFrame(), parentBasis.driverFacts(), basis.nativeFrame(), basis.driverFacts(),
                    parentBinding.implementationSource(), parentBinding.decoderSource(), definition.implementationSource(),
                    definition.decoderSource(), verifier.definitionSource(), lease.originalSourceQualification(),
                    previous.stream().map(archive::preserveReceipt).toList());
            for (var source : sources(proof)) pin(same, source);
            if(lease.originalSourceQualification().isPresent())pin(same, lease.originalSourceQualification().orElseThrow());
            var raw = proof.encode(); ExactRef original = archive.preserveMaterial(raw);
            require(raw.equals(archive.loadMaterial(original)), "derived child proof did not roundtrip its immutable original");
            unchanged(same, head); return original;
        }
        private void verifyArchived(WriterContracts.Head head, ActionReceipt child, GuardEvidence guard, ActionPorts.OutcomeArchive archive) {
            try {
                requireOwner(context, bindings); var same = context.borrowedSession(); context.writer().requireSession(same); unchanged(same, head);
                RootDerivedChildEvidence proof = RootDerivedChildEvidence.requireGuard(guard, archive);
                var point = RootGuardEvidence.writerPoint(guard, archive);
                require(point.sequence() == proof.actualHeadSequence() && point.digest().equals(proof.actualHeadDigest()),
                        "derived proof changed the original Root guard's exact writer admission point");
                require(child.bodySha256().equals(proof.childBodySha256()) && child.bodySha256().equals(ActionCodec.bodySha256(child.command()))
                        && ActionTransitions.attempt(child.state()).map(attempt -> attempt.guard().equals(guard)).orElse(false),
                        "derived replay needs the exact actual child's original primitive Attempt");
                requireCanonicalOrPreview(head, child, archive);
                var historical = same.requireHistoricalState(proof.actualHeadSequence(), proof.actualHeadDigest());
                var parent = archive.loadReceipt(proof.parentReceipt());
                ContinuityActionJournal.requireHistoricalReceipt(historical, parent, archive);
                ContinuityActionJournal.requireHistoricalReceipt(head.state(), parent, archive);
                require(parent.bodySha256().equals(proof.parentBodySha256()) && parent.state() instanceof ActionState.CompositeRunning,
                        "derived proof changed its historical original running parent");
                var running = ((ActionState.CompositeRunning) parent.state()).execution();
                require(running.handlerId().equals(proof.handlerId()) && running.children().size() == proof.childOrdinal(),
                        "derived proof changed its historical reserved ordinal or handler");
                requireUnsubmitted(ContinuityActionJournal.lookup(historical, child.command().actionId(), archive), child.command());
                if(RootExecutableBindings.isPublicPauseParent(parent.command())){
                    RootGuardEvidence.requireHistory(running.guard(),archive,same);RootGuardEvidence.requireHistory(guard,archive,same);
                    bindings.requirePublicPauseAuthority(parent.command()).verifyArchivedChild(head,child,guard,archive,same,context.originals());
                    unchanged(same,head);return;
                }
                var parentBinding = parentBinding(parent, proof.handlerId());
                var definition = bindings.resolve(child.command().operation(),child.command().origin()).orElseThrow(); requireChildDefinition(child.command(), definition);
                var verifier = bindings.actualArchivedVerifier(child.command().operation()).orElseThrow();
                require(parentBinding.implementationSource().equals(proof.parentImplementation()) && parentBinding.decoderSource().equals(proof.parentDecoder())
                        && definition.implementationSource().equals(proof.childImplementation()) && definition.decoderSource().equals(proof.childDecoder())
                        && verifier.definitionSource().equals(proof.childVerifier()), "derived historical source/decoder/verifier changed");
                var previous = preceding(historical, parent, child.command(), archive);
                require(previous.stream().map(archive::receiptReferenceOf).toList().equals(proof.previousChildren()),
                        "derived replay changed preceding canonical child originals or their order");
                var before = context.frameLoader().load(new NativeEffectEvidence.FrameBasis(proof.parentNative(), proof.parentDriver()), archive);
                var current = context.frameLoader().load(new NativeEffectEvidence.FrameBasis(proof.beforeNative(), proof.beforeDriver()), archive);
                require(before.equals(RootGuardEvidence.loadFrame(running.guard(), archive, context.frameLoader()))
                        && current.equals(RootGuardEvidence.loadFrame(guard, archive, context.frameLoader()))
                        && RootGuardEvidence.sourceQualification(guard, archive).equals(proof.sourceQualification()),
                        "derived proof lost the complete actual parent/current native/Driver/source origins");
                RootGuardEvidence.requireHistory(running.guard(), archive, same); RootGuardEvidence.requireHistory(guard, archive, same);
                qualify(parent, parentBinding, child.command(), before, current, previous, archive);
                for (var source : sources(proof)) pin(same, source);
                if(proof.sourceQualification().isPresent())pin(same, proof.sourceQualification().orElseThrow());
                unchanged(same, head);
            } catch (IOException failure) { throw new UncheckedIOException("INCOMPLETE: actual original derived-child read/replay authority unavailable", failure); }
        }
        private RootExecutableBindings.CompositeBinding parentBinding(ActionReceipt parent, String handlerId) throws IOException {
            require(parent.command().origin() instanceof CommandOrigin.Gameplay && parent.bodySha256().equals(ActionCodec.bodySha256(parent.command())),
                    "only an intact original gameplay parent can derive a timeline child");
            var actual = bindings.composites().find(parent.command().operation()).orElseThrow();
            var matches = bindings.compositeBindings().stream().filter(value -> value.handler() == actual
                    && value.handler().handlerId().equals(handlerId) && value.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).toList();
            require(matches.size() == 1, "derived parent is not the actual unique registered source-owned handler");
            if (actual instanceof RouteContactComposite)
                throw new IOException("INCOMPLETE: Route original Entry/proof/history does not yet have a durable pure derived-admission provider");
            require(actual instanceof LifeAdvanceComposite || actual instanceof BattleAdvanceComposite,
                    "this actual parent handler has no installed timeline derived authority");
            return matches.getFirst();
        }
        private void requireChildDefinition(ActionCommand child, ExecutableStepBindings.InstalledStep definition) {
            var actual = bindings.resolve(child.operation(),child.origin()).orElseThrow();
            var effect = bindings.actualActionBinding(child.operation()).orElseThrow(); var source = infrastructure.sources();
            require(definition.equals(actual) && definition.kind() == ExecutableStepBindings.Kind.ACTION
                    && definition.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP && AdvancePrimitives.supports(child.operation())
                    && effect.preparation() == infrastructure.primitives() && definition.implementationSource().equals(source.primitiveProducer())
                    && definition.decoderSource().equals(source.primitiveDecoder())
                    && bindings.actualArchivedVerifier(child.operation()).orElseThrow().definitionSource().equals(source.primitiveVerifier())
                    && definition.requiredCapability().equals(AdvancePrimitives.prepareRequest(child).requiredCapability()),
                    "derived timeline child lacks the identical actual primitive producer/decoder/verifier/capability");
        }
        private void qualify(ActionReceipt parent, RootExecutableBindings.CompositeBinding parentBinding, ActionCommand child,
                Complete original, Complete current, List<ActionReceipt> previous, ActionPorts.OutcomeArchive archive) {
            ActionCommand command = parent.command();
            require(original.identity().equals(command.before()) && original.source().equals(command.source()) && original.sessionId().equals(command.sessionId())
                    && current.identity().equals(child.before()) && current.source().equals(child.source()) && current.sessionId().equals(child.sessionId())
                    && original.connectionGeneration().equals(current.connectionGeneration()), "derived child changed original/current complete source or connection");
            var first = original.identity(); var last = current.identity();
            require(first.machineId().equals(last.machineId()) && first.game().equals(last.game())
                    && first.frame().episodeRunId().equals(last.frame().episodeRunId())
                    && first.frame().identity().player().equals(last.frame().identity().player())
                    && first.observationVersion() == last.observationVersion()
                    && last.frame().revision().compareTo(first.frame().revision()) >= 0
                    && last.frame().identity().nativeRevision().compareTo(first.frame().identity().nativeRevision()) >= 0
                    && last.frame().identity().dateRaw().compareTo(first.frame().identity().dateRaw()) >= 0,
                    "derived child changed original Game/actor/episode or regressed its public/native/date identity");
            require(command.source().equals(child.source()) && command.sessionId().equals(child.sessionId()) && command.claims().equals(child.claims())
                    && !child.deadline().isAfter(command.deadline()), "derived child changed original intent source/session/claims/deadline");
            var frame = frame(current);
            require(child.equals(AdvancePrimitives.child(command, frame, child.actionId(), child.operation().value(), child.deadline())),
                    "derived child body differs from the actual shared timeline child producer");
            var intent = intent(command, parentBinding.handler());
            String step = child.operation().value();
            if (step.startsWith(ClockStatusRead.ARM_PREFIX)) require(intent.arm().filter(step::equals).isPresent(), "derived arm differs from the exact original typed parent plan");
            if (step.startsWith("set-speed-")) require(step.equals("set-speed-" + intent.speed()), "derived speed differs from original typed parent plan");
            for (ActionReceipt old : previous) infrastructure.replay().verify(old, archive);
            if (step.startsWith(ClockStatusRead.CANCEL_PREFIX)) {
                var generation = AdvancePrimitives.cancelGeneration(step);
                var armed = previous.stream().filter(old -> intent.arm().filter(old.command().operation().value()::equals).isPresent()
                        && old.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED).toList();
                require(armed.size() == 1 && AdvancePrimitives.acknowledgedSentinel(armed.getFirst().ack().orElseThrow(),
                        armed.getFirst().command().operation().value()).generation().decimal().equals(generation.toString()),
                        "derived cancellation has no unique confirmed original same-generation arm and independent Status");
            }
        }
    }
    private record Intent(Optional<String> arm, int speed) { }
    private static Intent intent(ActionCommand parent, CompositeActionPort handler) {
        if (handler instanceof LifeAdvanceComposite) {
            var plan = AdvancePlan.decode(parent);
            require(plan.startingDateRaw().equals(parent.before().frame().identity().dateRaw())
                    && parent.expected().observerSchema().equals(AdvancePlan.OBSERVER) && parent.expected().values().equals(plan.expected()),
                    "derived life intent changed its original typed date/expected contract");
            return new Intent(plan.clockMode() == AdvancePlan.ClockMode.POLLED ? Optional.empty() : Optional.of(plan.armStep()), plan.speed());
        }
        require(handler instanceof BattleAdvanceComposite, "no concrete actual parent plan decoder is installed");
        var plan = BattleAdvancePlan.decode(parent);
        require(BigInteger.valueOf(plan.startingDateRaw()).equals(parent.before().frame().identity().dateRaw())
                && parent.expected().observerSchema().equals(BattleAdvancePlan.OBSERVER) && parent.expected().values().equals(plan.expected())
                && parent.claims().armyIds().containsAll(plan.watchArmyIds().stream().map(BigInteger::valueOf).toList()),
                "derived tactical intent changed its original typed date/expected/complete watch claims");
        return new Intent(Optional.of(plan.armStep()), plan.speed());
    }
    private static AdvanceObservationPort.Frame frame(Complete actual) {
        return new AdvanceObservationPort.Frame(actual.identity(), actual.source(), actual.sessionId(), actual.semantic(),
                new ObservationProvenance.Push(actual.identity().frame().snapshotId(), actual.identity().frame().identity().nativeRevision(), actual.originalEvidence()),
                actual.observedAt(), actual.originalEvidence());
    }
    private static List<ActionReceipt> preceding(ContinuityState state, ActionReceipt parent, ActionCommand child, ActionPorts.OutcomeArchive archive) {
        var running = ((ActionState.CompositeRunning) parent.state()).execution(); var keys = running.children();
        require(!keys.isEmpty() && keys.getLast().equals(new CompositeExecution.Child(child.actionId(), ActionCodec.bodySha256(child)))
                && child.actionId().equals(ActionIds.child(parent.command().actionId(), keys.size(), child.operation())),
                "derived child is not the exact last reserved canonical child ID/body/ordinal");
        var previous = new ArrayList<ActionReceipt>();
        for (var key : keys.subList(0, keys.size() - 1)) {
            var old = ContinuityActionJournal.lookup(state, key.actionId(), archive).orElseThrow();
            require(old.settled() && old.bodySha256().equals(key.bodySha256()), "UNKNOWN preceding child forbids subsequent submission or cleanup"); previous.add(old);
        }
        return List.copyOf(previous);
    }
    private static List<ExactRef> sources(RootDerivedChildEvidence proof) {
        return List.of(proof.parentImplementation(), proof.parentDecoder(), proof.childImplementation(), proof.childDecoder(), proof.childVerifier());
    }
    /** Pure original-state check shared by live admission and historical replay; it grants no native permission. */
    static void requireUnsubmitted(Optional<ActionReceipt> canonical, ActionCommand child) {
        canonical.ifPresent(original -> require(original.command().equals(child)
                && original.bodySha256().equals(ActionCodec.bodySha256(child)) && original.state() instanceof ActionState.IntentDurable,
                "only an absent child or its exact unsubmitted IntentDurable can revalidate admission; Attempt/UNKNOWN never replay"));
    }
    /** The real writer validates a candidate before commit; archived events retain complete receipt membership. */
    static void requireCanonicalOrPreview(WriterContracts.Head head, ActionReceipt child, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(head); Objects.requireNonNull(child); Objects.requireNonNull(archive);
        if (child.sequence() <= head.state().sequence()) {
            ContinuityActionJournal.requireHistoricalReceipt(head.state(), child, archive);
            return;
        }
        require(child.sequence() == Math.addExact(head.state().sequence(), 1),
                "derived child candidate is not the actual sole next writer event");
        var canonical = ContinuityActionJournal.lookup(head.state(), child.command().actionId(), archive).orElseThrow(
                () -> new IllegalArgumentException("derived child candidate has no surviving canonical predecessor"));
        require(canonical.command().equals(child.command()) && canonical.bodySha256().equals(child.bodySha256()),
                "derived child candidate changed its complete canonical predecessor body");
        ActionTransitions.validate(Optional.of(canonical), child.command(), child.bodySha256(), child.state());
    }
    private static void pin(ContinuityStorePort.Session same, ExactRef original) throws IOException {
        same.verifyPin(same.capturePin(original, 16 * 1024 * 1024));
    }
    private static void unchanged(ContinuityStorePort.Session same, WriterContracts.Head head) throws IOException {
        require(same.head().digest().equals(head.digest()) && same.head().documents().equals(head.documents()), "derived authority escaped or mutated its original locked writer Head");
    }
}

