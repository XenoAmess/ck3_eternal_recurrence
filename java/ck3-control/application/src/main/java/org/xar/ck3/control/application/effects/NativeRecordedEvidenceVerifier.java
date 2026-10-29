package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Re-opens original archive bodies under the real writer lock. It never queries Native or submits an action. */
public final class NativeRecordedEvidenceVerifier implements ActionPorts.RecordedEvidenceVerifier {
    /** The real terminal implementation lives at Root; application never imports local-service. */
    @FunctionalInterface public interface TerminalGuardVerifier {
        void verify(GuardEvidence guard, ActionPorts.OutcomeArchive sameArchive, ContinuityStorePort.Session same,
                OriginalEvidencePort originals) throws IOException;
    }
    /** Root replays the canonical pending identity and its physical originals; this is never ordinary Ready. */
    @FunctionalInterface public interface ReconciliationGuardVerifier {
        org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete verify(GuardEvidence guard,
                ActionPorts.OutcomeArchive sameArchive, ContinuityStorePort.Session same,
                OriginalEvidencePort originals) throws IOException;
    }
    /** Root replays its finite operator guard under the actual writer; no ordinary Ready is borrowed. */
    @FunctionalInterface public interface OperatorGuardVerifier {
        void verify(ActionCommand command, GuardEvidence guard, ActionPorts.OutcomeArchive sameArchive,
                ContinuityStorePort.Session same, OriginalEvidencePort originals) throws IOException;
    }
    /** Actual ancestry/claim/preflight replay; a locator codec never supplies this authority. */
    @FunctionalInterface public interface DerivedGuardVerifier {
        void verify(WriterContracts.Head actualHead, ActionReceipt child, GuardEvidence originalGuard, ActionPorts.OutcomeArchive sameArchive);
    }
    @FunctionalInterface public interface ArchivedVerifier {
        /** Re-derive domain values from original evidence; a shape check or comparison to expected values alone is insufficient. */
        void verify(WriterContracts.Head actualLockedHead, ActionReceipt proposed, ActionPorts.OutcomeArchive sameWriterArchive);
    }
    public record Binding(OperationKey operation, ExactRef definitionSource, ArchivedVerifier verifier) {
        public Binding { Objects.requireNonNull(operation); Objects.requireNonNull(definitionSource); Objects.requireNonNull(verifier); StrictJson.require(definitionSource.bytes() > 0, "real domain verifier source required"); }
    }
    private final ActionPorts.OutcomeArchive archive;
    private final Supplier<ContinuityStorePort.Session> borrowedSession;
    private final OriginalEvidencePort originals;
    private final NativeEffectEvidence.FrameLoader frames;
    private final Map<OperationKey, Binding> bindings;
    private final RootExecutableBindings catalog;
    private final java.util.Optional<TerminalGuardVerifier> terminalGuards;
    private final java.util.Optional<DerivedGuardVerifier> derivedGuards;
    private final java.util.Optional<ReconciliationGuardVerifier> reconciliationGuards;
    private final java.util.Optional<OperatorGuardVerifier> operatorGuards;
    public NativeRecordedEvidenceVerifier(ActionPorts.OutcomeArchive archive, Supplier<ContinuityStorePort.Session> borrowedSession,
            OriginalEvidencePort originals, NativeEffectEvidence.FrameLoader frames, List<Binding> bindings) {
        this(archive, borrowedSession, originals, frames, bindings, java.util.Optional.empty());
    }
    /** Retains the exact finite domain callbacks while installing the actual Root reconciliation replay. */
    public NativeRecordedEvidenceVerifier(ActionPorts.OutcomeArchive archive, Supplier<ContinuityStorePort.Session> borrowedSession,
            OriginalEvidencePort originals, NativeEffectEvidence.FrameLoader frames, List<Binding> bindings,
            ReconciliationGuardVerifier actualReconciliationGuardVerifier) {
        this(archive, borrowedSession, originals, frames, bindings,
                java.util.Optional.of(Objects.requireNonNull(actualReconciliationGuardVerifier)));
    }
    private NativeRecordedEvidenceVerifier(ActionPorts.OutcomeArchive archive, Supplier<ContinuityStorePort.Session> borrowedSession,
            OriginalEvidencePort originals, NativeEffectEvidence.FrameLoader frames, List<Binding> bindings,
            java.util.Optional<ReconciliationGuardVerifier> actualReconciliationGuardVerifier) {
        this.archive = Objects.requireNonNull(archive); this.borrowedSession = Objects.requireNonNull(borrowedSession);
        this.originals = Objects.requireNonNull(originals); this.frames = Objects.requireNonNull(frames);
        StrictJson.require(bindings != null && bindings.size() <= 4096, "finite exact archived verifier registry required");
        var index = new HashMap<OperationKey, Binding>();
        for (var binding : List.copyOf(bindings)) StrictJson.require(index.putIfAbsent(binding.operation(), binding) == null, "two archived verifiers claim one exact operation");
        this.bindings = Map.copyOf(index); this.catalog = null; this.terminalGuards = java.util.Optional.empty(); this.derivedGuards = java.util.Optional.empty();
        this.reconciliationGuards = Objects.requireNonNull(actualReconciliationGuardVerifier);
        this.operatorGuards = java.util.Optional.empty();
    }
    /** The same live catalog that owns executable objects also owns their exact archived replay. */
    public NativeRecordedEvidenceVerifier(ActionPorts.OutcomeArchive archive, Supplier<ContinuityStorePort.Session> borrowedSession,
            OriginalEvidencePort originals, NativeEffectEvidence.FrameLoader frames, RootExecutableBindings actualCatalog) {
        this.archive = Objects.requireNonNull(archive); this.borrowedSession = Objects.requireNonNull(borrowedSession);
        this.originals = Objects.requireNonNull(originals); this.frames = Objects.requireNonNull(frames);
        this.catalog = Objects.requireNonNull(actualCatalog); this.bindings = Map.of();
        this.terminalGuards = java.util.Optional.empty(); this.derivedGuards = java.util.Optional.empty(); this.reconciliationGuards = java.util.Optional.empty(); this.operatorGuards = java.util.Optional.empty();
    }
    public NativeRecordedEvidenceVerifier(ActionPorts.OutcomeArchive archive, Supplier<ContinuityStorePort.Session> borrowedSession,
            OriginalEvidencePort originals, NativeEffectEvidence.FrameLoader frames, RootExecutableBindings actualCatalog,
            TerminalGuardVerifier actualTerminalGuardVerifier) {
        this.archive = Objects.requireNonNull(archive); this.borrowedSession = Objects.requireNonNull(borrowedSession);
        this.originals = Objects.requireNonNull(originals); this.frames = Objects.requireNonNull(frames);
        this.catalog = Objects.requireNonNull(actualCatalog); this.bindings = Map.of();
        this.terminalGuards = java.util.Optional.of(Objects.requireNonNull(actualTerminalGuardVerifier));
        this.derivedGuards = java.util.Optional.empty();
        this.reconciliationGuards = java.util.Optional.empty(); this.operatorGuards = java.util.Optional.empty();
    }
    public NativeRecordedEvidenceVerifier(ActionPorts.OutcomeArchive archive, Supplier<ContinuityStorePort.Session> borrowedSession,
            OriginalEvidencePort originals, NativeEffectEvidence.FrameLoader frames, RootExecutableBindings actualCatalog,
            TerminalGuardVerifier actualTerminalGuardVerifier, DerivedGuardVerifier actualDerivedGuardVerifier) {
        this.archive = Objects.requireNonNull(archive); this.borrowedSession = Objects.requireNonNull(borrowedSession);
        this.originals = Objects.requireNonNull(originals); this.frames = Objects.requireNonNull(frames);
        this.catalog = Objects.requireNonNull(actualCatalog); this.bindings = Map.of();
        this.terminalGuards = java.util.Optional.of(Objects.requireNonNull(actualTerminalGuardVerifier));
        this.derivedGuards = java.util.Optional.of(Objects.requireNonNull(actualDerivedGuardVerifier));
        this.reconciliationGuards = java.util.Optional.empty(); this.operatorGuards = java.util.Optional.empty();
    }
    public NativeRecordedEvidenceVerifier(ActionPorts.OutcomeArchive archive, Supplier<ContinuityStorePort.Session> borrowedSession,
            OriginalEvidencePort originals, NativeEffectEvidence.FrameLoader frames, RootExecutableBindings actualCatalog,
            TerminalGuardVerifier actualTerminalGuardVerifier, DerivedGuardVerifier actualDerivedGuardVerifier,
            ReconciliationGuardVerifier actualReconciliationGuardVerifier) {
        this.archive = Objects.requireNonNull(archive); this.borrowedSession = Objects.requireNonNull(borrowedSession);
        this.originals = Objects.requireNonNull(originals); this.frames = Objects.requireNonNull(frames);
        this.catalog = Objects.requireNonNull(actualCatalog); this.bindings = Map.of();
        this.terminalGuards = java.util.Optional.of(Objects.requireNonNull(actualTerminalGuardVerifier));
        this.derivedGuards = java.util.Optional.of(Objects.requireNonNull(actualDerivedGuardVerifier));
        this.reconciliationGuards = java.util.Optional.of(Objects.requireNonNull(actualReconciliationGuardVerifier));
        this.operatorGuards = java.util.Optional.empty();
    }
    /** Actual Root installation supplies the private operator codec without an application-to-host dependency. */
    public NativeRecordedEvidenceVerifier(ActionPorts.OutcomeArchive archive, Supplier<ContinuityStorePort.Session> borrowedSession,
            OriginalEvidencePort originals, NativeEffectEvidence.FrameLoader frames, RootExecutableBindings actualCatalog,
            TerminalGuardVerifier actualTerminalGuardVerifier, DerivedGuardVerifier actualDerivedGuardVerifier,
            ReconciliationGuardVerifier actualReconciliationGuardVerifier, OperatorGuardVerifier actualOperatorGuardVerifier) {
        this.archive = Objects.requireNonNull(archive); this.borrowedSession = Objects.requireNonNull(borrowedSession);
        this.originals = Objects.requireNonNull(originals); this.frames = Objects.requireNonNull(frames);
        this.catalog = Objects.requireNonNull(actualCatalog); this.bindings = Map.of();
        this.terminalGuards = java.util.Optional.of(Objects.requireNonNull(actualTerminalGuardVerifier));
        this.derivedGuards = java.util.Optional.of(Objects.requireNonNull(actualDerivedGuardVerifier));
        this.reconciliationGuards = java.util.Optional.of(Objects.requireNonNull(actualReconciliationGuardVerifier));
        this.operatorGuards = java.util.Optional.of(Objects.requireNonNull(actualOperatorGuardVerifier));
    }
    @Override public void verify(WriterContracts.Head actualLockedHead, ActionReceipt proposed) {
        Objects.requireNonNull(proposed);
        try {
            var session = RootGuardChecks.session(borrowedSession, actualLockedHead);
            ActionPorts.OutcomeArchive archive = this.archive.withSession(session);
            StrictJson.require(proposed.command().origin().machineId().equals(actualLockedHead.state().machineId()), "action evidence crossed the canonical writer machine");
            byte[] encoded = ActionReceiptCodec.encodeReceipt(proposed, archive);
            ActionReceipt decoded = ActionReceiptCodec.decodeReceipt(encoded, archive);
            StrictJson.require(java.util.Arrays.equals(encoded, ActionReceiptCodec.encodeReceipt(decoded, archive)), "full archived action receipt roundtrip changed");
            StrictJson.require(proposed.bodySha256().equals(ActionCodec.bodySha256(proposed.command())), "canonical action body changed under writer lock");
            ActionTransitions.attempt(proposed.state()).ifPresent(attempt -> {
                NativeRequest request = archive.loadRequest(archive.requestReferenceOf(attempt.preparedRequest()));
                StrictJson.require(request.equals(attempt.preparedRequest()), "actual archived primitive changed");
                NativeStepDiscriminator.requireRequest(proposed.command().operation(), ExecutableStepBindings.Kind.ACTION, request);
                StrictJson.require(proposed.command().origin().acceptsGuard(attempt.guard().origin()) && attempt.guard().source().equals(proposed.command().source())
                        && attempt.guard().sessionId().equals(proposed.command().sessionId()) && attempt.guard().operation().equals(proposed.command().operation()), "original attempt origin/source/session/operation drift");
                guard(session, attempt.guard(), archive, actualLockedHead, proposed);
            });
            ActionTransitions.composite(proposed.state()).ifPresent(composite -> {
                var guard = composite.guard();
                StrictJson.require(proposed.command().origin().acceptsGuard(guard.origin()) && guard.source().equals(proposed.command().source())
                        && guard.sessionId().equals(proposed.command().sessionId()) && guard.operation().equals(proposed.command().operation()), "original composite guard binding drift");
                guard(session, guard, archive, actualLockedHead, proposed);
            });
            ActionTransitions.dispatch(proposed.state()).ifPresent(dispatch -> StrictJson.require(dispatch.equals(archive.load(archive.referenceOf(dispatch))), "actual archived dispatch changed"));
            if (proposed.state() instanceof ActionState.Settled primitive)
                ActionEffects.validate(proposed.command(), primitive.attempt(), primitive.dispatch(), primitive.settlement());
            ActionState.Settlement settlement = settlement(proposed.state());
            if (settlement == null) return;
            Binding binding = catalog == null ? bindings.get(proposed.command().operation())
                    : catalog.actualArchivedVerifier(proposed.command().operation()).orElse(null);
            StrictJson.require(binding != null, "settlement has no installed original-evidence domain verifier");
            RootGuardChecks.source(session, binding.definitionSource());
            if (settlement instanceof ActionState.CompositeRejected rejected) {
                var execution = ActionTransitions.composite(proposed.state()).orElseThrow(() -> new IllegalArgumentException("negative parent has no original composite execution"));
                List<ActionReceipt> children = new java.util.ArrayList<>();
                for (var child : rejected.children()) {
                    var actual = org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(actualLockedHead.state(), child.actionId(), archive)
                            .orElseThrow(() -> new IllegalArgumentException("negative composite child is absent from the actual writer head"));
                    StrictJson.require(actual.bodySha256().equals(child.bodySha256()) && !actual.command().actionId().equals(proposed.command().actionId()), "negative composite child identity changed"); children.add(actual);
                }
                ActionEffects.validateCompositeChildren(execution, rejected, children);
                // The shared reducer only accepts genuine primitive rejected/zero-dispatch children here.
                for (var child : children) verify(actualLockedHead, child);
                if (!rejected.evidence().isEmpty()) {
                    requireMaterialEvidence(rejected.evidence(), archive);
                    binding.verifier().verify(actualLockedHead, proposed, archive);
                }
                RootGuardChecks.session(borrowedSession, actualLockedHead); return;
            }
            if (settlement instanceof ActionState.Applied applied) {
                var effect = applied.observation(); requireMaterialEvidence(effect.supportingEvidence(), archive);
                RootGuardChecks.exact(effect.originalEvidence(), archive.loadNativeFrame(effect.originalEvidence()));
                NativeEffectEvidence.loadIfPresent(proposed, archive, frames).ifPresent(original -> {
                    original.reconciliationGuard().ifPresent(actual -> guard(session, actual, archive, actualLockedHead, proposed));
                    original.independentReads().forEach(read -> verifyRead(session, read, archive, actualLockedHead, proposed));
                });
            } else if (settlement instanceof ActionState.PauseConfirmed pause) {
                StrictJson.require(proposed.state() instanceof ActionState.Settled,
                        "pause confirmation requires its original native primitive attempt");
                var primitive = (ActionState.Settled) proposed.state();
                var effect = pause.observation();
                PauseConfirmation.validate(proposed.command(), primitive.attempt(), primitive.dispatch(), effect);
                RootGuardChecks.exact(effect.originalEvidence(), archive.loadNativeFrame(effect.originalEvidence()));
                // The unique primitive sidecar loader reopens its native Push and full Driver
                // originals, checks the command SHA, and rebuilds the exact observed frame.
                org.xar.ck3.control.application.advance.AdvancePrimitiveEvidence.load(proposed, archive, frames);
                requireNonEffectCompletion(proposed);
            } else if (settlement instanceof ActionState.ControlSequenceCompleted sequence) {
                StrictJson.require(proposed.state() instanceof ActionState.CompositeSettled,
                        "control sequence requires its original composite execution");
                var observed = sequence.observation();
                StrictJson.require(observed.parent().equals(proposed.command()),
                        "control sequence changed its original parent command");
                var execution = ActionTransitions.composite(proposed.state()).orElseThrow();
                List<ActionReceipt> children = new java.util.ArrayList<>();
                for (var child : observed.children()) {
                    var canonical = org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(
                            actualLockedHead.state(), child.actionId(), archive)
                            .orElseThrow(() -> new IllegalArgumentException("control child is absent from the actual writer head"));
                    StrictJson.require(!canonical.command().actionId().equals(proposed.command().actionId())
                            && canonical.bodySha256().equals(child.bodySha256())
                            && canonical.equals(archive.loadReceipt(child.canonicalReceipt())),
                            "control child locator differs from the actual canonical writer receipt");
                    children.add(canonical);
                }
                ActionEffects.validateCompositeChildren(execution, sequence, children);
                requireMaterialEvidence(List.of(observed.proof()), archive);
                for (var child : children) verify(actualLockedHead, child);
                requireNonEffectCompletion(proposed);
                // Mixed original locators and retry/after proof remain the mandatory identical
                // installed source callback responsibility. Existing guard routing is unchanged:
                // this DATA branch cannot admit a future running public pause private guard.
            } else if (settlement instanceof ActionState.FixtureStarted) {
                StrictJson.require(proposed.state() instanceof ActionState.Settled,
                        "fixture first-map completion requires its original frontend Start primitive");
                // ActionEffects above revalidates the original Start ACK and independent READ
                // custody. Its mixed SEM/Driver/source originals are owned by the identical
                // installed verifier below; none is reinterpreted as generic material.
                requireNonEffectCompletion(proposed);
            } else if (settlement instanceof ActionState.FixtureBusinessCompleted completed) {
                StrictJson.require(proposed.state() instanceof ActionState.CompositeSettled,
                        "fixture business completion requires its original upfront frontend composite");
                var execution = ActionTransitions.composite(proposed.state()).orElseThrow();
                ActionEffects.validateComposite(proposed.command(), execution, completed);
                List<ActionReceipt> children = new java.util.ArrayList<>();
                for (var child : execution.children()) {
                    var canonical = org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(
                            actualLockedHead.state(), child.actionId(), archive)
                            .orElseThrow(() -> new IllegalArgumentException("fixture child is absent from the actual writer head"));
                    StrictJson.require(!canonical.command().actionId().equals(proposed.command().actionId())
                            && canonical.bodySha256().equals(child.bodySha256()),
                            "fixture child differs from its original canonical reservation");
                    children.add(canonical);
                }
                ActionEffects.validateCompositeChildren(execution, completed, children);
                requireRead(completed.observation().evidence().campaignRootRead(), archive);
                for (var child : children) verify(actualLockedHead, child);
                requireNonEffectCompletion(proposed);
                // Entry Prepared/Receipt, qualification and first-map originals have distinct
                // archive roles. The mandatory same installed source callback below must
                // deeply replay them; no private Held scope is reopened here.
            } else if (settlement instanceof ActionState.DirectFixedWindowCompleted completed) {
                StrictJson.require(proposed.state() instanceof ActionState.Settled,
                        "direct fixed-window completion requires its exact original primitive attempt");
                var primitive = (ActionState.Settled) proposed.state();
                completed.completion().validate(proposed.command(), primitive.attempt(), primitive.dispatch(), archive);
                requireNonEffectCompletion(proposed);
                // The sole Completion/installed domain replay owns direct sampling and later
                // owner-query variants, original ACK custody and their mixed original roles.
                // No local same-frame rule, generic material cast, Pending success or Pair
                // relaxation substitutes for the mandatory identical source callback below.
            } else if (settlement instanceof ActionState.FamilySendConfirmed send) {
                var observed = send.observation();
                var primitive = (ActionState.Settled) proposed.state();
                observed.validate(proposed.command(), primitive.attempt(), primitive.dispatch(), archive);
                observed.loadFrames(archive, frames);
                verifyRead(session, observed.beforeStorage(), archive, actualLockedHead, proposed);
                verifyRead(session, observed.afterStorage(), archive, actualLockedHead, proposed);
            } else if (settlement instanceof ActionState.OperatorRebound rebound) {
                StrictJson.require(proposed.state() instanceof ActionState.Settled,
                        "operator identity completion requires its exact original primitive attempt");
                var primitive = (ActionState.Settled) proposed.state();
                rebound.observation().validate(proposed.command(), primitive.attempt(), primitive.dispatch());
                requireNonEffectCompletion(proposed);
                // Completion carries mixed native/store original locators. Its DATA fields do
                // not define archive roles. The mandatory identical installed callback below
                // must replay the actual issuer, independent after and canonical rebind closure.
            } else if (settlement instanceof ActionState.NativeSourceCompleted source) {
                StrictJson.require(proposed.state() instanceof ActionState.Settled,
                        "native source completion requires its exact original primitive attempt");
                var primitive = (ActionState.Settled) proposed.state();
                var observed = source.observation();
                observed.validate(proposed.command(), primitive.attempt(), primitive.dispatch());
                StrictJson.require(observed.originalDispatch().equals(archive.referenceOf(primitive.dispatch()))
                        && archive.load(observed.originalDispatch()).equals(primitive.dispatch()),
                        "native source completion changed its actual original archived dispatch");
                requireMaterialEvidence(List.of(observed.independentClipboard(), observed.afterScope(), observed.compatibleResult()), archive);
                requireNonEffectCompletion(proposed);
                // sourceOriginals includes source files and native custody, not only JSON material.
                // The identical installed domain callback below must deeply replay all of them.
            } else if (settlement instanceof ActionState.NormalExitPhaseConfirmed phase) {
                StrictJson.require(proposed.state() instanceof ActionState.Settled,
                        "normal-exit UI phase requires its exact original primitive attempt");
                var primitive = (ActionState.Settled) proposed.state();
                var observed = phase.observation();
                observed.validate(proposed.command(), primitive.attempt(), primitive.dispatch(), archive);
                verifyRead(session, observed.beforeContext(), archive, actualLockedHead, proposed);
                verifyRead(session, observed.afterContext(), archive, actualLockedHead, proposed);
                requireNonEffectCompletion(proposed);
                // DATA/guard custody does not establish UI semantics. The registered domain
                // must re-decode the original ACK and both contexts before this can settle.
            } else if (settlement instanceof ActionState.ControlApplied control) {
                StrictJson.require(proposed.state() instanceof ActionState.Settled,
                        "native control requires its exact original primitive attempt");
                var primitive = (ActionState.Settled) proposed.state();
                var actualAck = ActionEffects.controlAcknowledgement(proposed.command(), primitive.attempt(), primitive.dispatch(), control);
                if (control.reconciledAck().isPresent()) {
                    // The late ACK is an already received original. This lookup never preserves,
                    // publishes or replaces the canonical UNKNOWN dispatch.
                    var received = control.reconciledAck().orElseThrow();
                    var receivedRef = received.reference(archive);
                    StrictJson.require(actualAck.equals(archive.load(receivedRef)),
                            "late control ACK changed its actual archived original");
                    actualAck.custody().orElseThrow(() -> new IllegalArgumentException("actual late control chronology is unavailable"))
                            .verify(actualAck, primitive.attempt().guard());
                    NativeRequestChronology.requireSampledAfter(control.read(), primitive.attempt(), actualAck);
                    control.supportingReads().forEach(read -> NativeRequestChronology.requireSampledAfter(read, primitive.attempt(), actualAck));
                }
                verifyRead(session, control.read(), archive, actualLockedHead, proposed); control.supportingReads().forEach(read -> verifyRead(session, read, archive, actualLockedHead, proposed));
            } else if (settlement instanceof ActionState.CompositeControlApplied control) {
                var observed = control.observation(); requireMaterialEvidence(observed.semantic().supportingEvidence(), archive);
                RootGuardChecks.exact(observed.semantic().originalEvidence(), archive.loadNativeFrame(observed.semantic().originalEvidence()));
                verifyRead(session, observed.terminalStatus(), archive, actualLockedHead, proposed); observed.supportingReads().forEach(read -> verifyRead(session, read, archive, actualLockedHead, proposed));
            } else if (settlement instanceof ActionState.FrontendApplied frontend) {
                requireMaterialEvidence(frontend.observation().supportingEvidence(), archive);
                original(session, frontend.observation().originalEvidence());
            } else if (settlement instanceof ActionState.NonAppliedTerminal terminal) {
                var observed = terminal.observation(); requireMaterialEvidence(observed.supportingEvidence(), archive);
                RootGuardChecks.exact(observed.originalEvidence(), archive.loadNativeFrame(observed.originalEvidence()));
                verifyRead(session, observed.selectedCollection(), archive, actualLockedHead, proposed); verifyRead(session, observed.afterCollection(), archive, actualLockedHead, proposed);
                var dispatch = ActionTransitions.dispatch(proposed.state()).orElseThrow();
                StrictJson.require(archive.referenceOf(dispatch).equals(observed.originalSubmission()), "terminal original submission differs from the canonical attempt dispatch");
            } else if (settlement instanceof ActionState.LifecycleControlApplied control) {
                requireMaterialEvidence(control.observation().supportingEvidence(), archive);
                verifyRead(session, control.observation().beforeStatus(), archive, actualLockedHead, proposed); verifyRead(session, control.observation().independentRead(), archive, actualLockedHead, proposed);
            }
            // Domain-owned Frontend and composite control branches also require an exact binding and perform their own complete archive replay.
            binding.verifier().verify(actualLockedHead, proposed, archive);
            RootGuardChecks.session(borrowedSession, actualLockedHead);
        } catch (IOException failure) { throw new UncheckedIOException("actual lock-held original-evidence revalidation unavailable", failure); }
    }
    public static void requireMaterialEvidence(List<ExactRef> references, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(references != null && !references.isEmpty() && references.size() <= 64, "real bounded domain evidence basis is required for settlement");
        var unique = new java.util.HashSet<ExactRef>();
        for (ExactRef reference : references) {
            StrictJson.require(unique.add(reference), "duplicate domain evidence basis");
            RootGuardChecks.exact(reference, archive.loadMaterial(reference).bytes());
        }
    }
    public static void requireRead(PlanningReadReceipt read, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(read.equals(archive.loadRead(archive.readReferenceOf(read))), "actual independent read receipt changed");
        StrictJson.require(read.original().equals(archive.load(archive.referenceOf(read.original()))), "actual independent native read outcome changed");
    }
    private static void requireNonEffectCompletion(ActionReceipt proposed) {
        StrictJson.require(proposed.outcome() == ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT
                && !proposed.visibleGameplay() && !proposed.eligibleAdvance() && proposed.applied().isEmpty(),
                "native identity/source/UI/control completion cannot grant an Applied gameplay or day effect");
    }
    private void verifyRead(ContinuityStorePort.Session session, PlanningReadReceipt read, ActionPorts.OutcomeArchive archive, WriterContracts.Head head, ActionReceipt proposed) {
        requireRead(read, archive);
        for (var guard : List.of(read.before().binding(), read.after().binding())) {
            guard(session, guard, archive, head, proposed);
        }
    }
    private void guard(ContinuityStorePort.Session session, GuardEvidence guard, ActionPorts.OutcomeArchive archive, WriterContracts.Head head, ActionReceipt proposed) {
        original(session, guard.capabilityEvidence());
        if (proposed.command().expectation() instanceof CommandExpectation.OperatorRebind) {
            try {
                operatorGuards.orElseThrow(() -> new IllegalStateException("actual Root operator historical guard verifier is not installed"))
                        .verify(proposed.command(), guard, archive, session, originals);
            } catch (IOException failure) { throw new UncheckedIOException("actual Root operator historical originals unavailable", failure); }
            return;
        }
        if (guard.origin() instanceof CommandOrigin.Gameplay) {
            if (RootExecutableBindings.isPublicPauseParent(proposed.command())) {
                if (catalog == null) throw new IllegalStateException("actual source-owned public-pause Root catalog is not installed");
                try {
                    var actual = catalog.requirePublicPauseAuthority(proposed.command());
                    RootGuardChecks.source(session, actual.definitionSource());
                    actual.verifyArchivedParent(proposed.command(), guard, archive, session, originals);
                } catch (IOException failure) {
                    throw new UncheckedIOException("actual public-pause parent historical originals unavailable", failure);
                }
                return;
            }
            RootGuardEvidence.loadFrame(guard, archive, frames);
            try { RootGuardEvidence.requireHistory(guard, archive, session); }
            catch (IOException failure) { throw new UncheckedIOException("original Root guard is not an ancestor of the actual writer head", failure); }
            if (guard.supportingEvidence().size() == 2)
                derivedGuards.orElseThrow(() -> new IllegalStateException("actual Root derived-child historical verifier is not installed")).verify(head, proposed, guard, archive);
        }
        else if (guard.origin() instanceof CommandOrigin.Frontend) frontend(session, guard, archive);
        else if (guard.origin() instanceof CommandOrigin.Reconciliation reconciliation) {
            try {
                var rebuilt = reconciliationGuards.orElseThrow(() -> new IllegalStateException("actual Root reconciliation guard verifier is not installed"))
                        .verify(guard, archive, session, originals);
                var identity = reconciliation.identity();
                StrictJson.require(rebuilt.identity().equals(identity.factual()) && rebuilt.source().equals(identity.source())
                        && rebuilt.sessionId().equals(identity.sessionId()) && rebuilt.connectionGeneration().equals(identity.connectionGeneration())
                        && rebuilt.originalEvidence().equals(identity.nativeEvidence())
                        && NativeEffectEvidence.basis(rebuilt).driverFacts().equals(identity.evidence().observationManifest()),
                        "Root reconciliation replay returned a different original factual frame");
            } catch (IOException failure) { throw new UncheckedIOException("same-writer reconciliation originals unavailable", failure); }
        }
        else if (guard.origin() instanceof CommandOrigin.LifecycleTerminal) {
            try { terminalGuards.orElseThrow(() -> new IllegalStateException("actual Root terminal guard verifier is not installed")).verify(guard, archive, session, originals); }
            catch (IOException failure) { throw new UncheckedIOException("same-writer terminal originals unavailable", failure); }
        } else throw new IllegalArgumentException("unregistered command origin has no original-evidence verifier");
    }
    private void original(ContinuityStorePort.Session session, ExactRef reference) {
        try { RootGuardChecks.exact(reference, originals.read(session, reference, StrictJson.EXPLICIT_MAX_BYTES)); }
        catch (IOException failure) { throw new UncheckedIOException("same-writer original packet unavailable", failure); }
    }
    private void frontend(ContinuityStorePort.Session session, GuardEvidence guard, ActionPorts.OutcomeArchive archive) {
        try { RootFrontendGuardEvidence.verify(guard, archive, session, originals); }
        catch (IOException failure) { throw new UncheckedIOException("same-writer frontend originals unavailable", failure); }
    }
    public static ActionState.Settlement settlement(ActionState state) {
        if (state instanceof ActionState.Settled settled) return settled.settlement();
        if (state instanceof ActionState.CompositeSettled settled) return settled.settlement();
        return null;
    }
}
