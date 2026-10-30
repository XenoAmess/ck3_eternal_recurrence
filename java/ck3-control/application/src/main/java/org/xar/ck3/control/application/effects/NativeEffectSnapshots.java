package org.xar.ck3.control.application.effects;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue;

/** Both frames come from the one real held Native endpoint and the sole Driver semantic assembler. */
public final class NativeEffectSnapshots {
    public record Pair(Complete before, Complete after, java.util.Optional<ReconciliationIdentity> reconciliation) {
        /** Ordinary effects retain the original same-connection contract. */
        public Pair(Complete before, Complete after) { this(before,after,java.util.Optional.empty()); }
        public Pair {
            Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(reconciliation);
            StrictJson.require(before.identity().machineId().equals(after.identity().machineId())
                    && before.identity().game().equals(after.identity().game())
                    && before.sessionId().equals(after.sessionId())
                    && before.source().equals(after.source())
                    && before.identity().frame().episodeRunId().equals(after.identity().frame().episodeRunId())
                    && before.identity().frame().identity().player().equals(after.identity().frame().identity().player()), "postcondition crossed native Game/actor/episode/source/session");
            boolean reconnected = !before.connectionGeneration().equals(after.connectionGeneration());
            if (reconnected) {
                ReconciliationIdentity identity=reconciliation.orElseThrow(
                        ()->new IllegalArgumentException("cross-connection effect requires its original pending reconciliation DATA"));
                ReconciliationIdentity.requireSamePhysicalSubject(before.identity(),after.identity());
                StrictJson.require(after.connectionGeneration().compareTo(before.connectionGeneration())>0
                        &&identity.pending().originalBefore().equals(before.identity())
                        &&identity.factual().equals(after.identity())&&identity.source().equals(after.source())
                        &&identity.sessionId().equals(after.sessionId())&&identity.connectionGeneration().equals(after.connectionGeneration())
                        &&identity.nativeEvidence().equals(after.originalEvidence())
                        &&!before.originalEvidence().equals(after.originalEvidence())
                        &&!after.observedAt().isBefore(before.observedAt()),
                        "reconnected effect changed the original pending or current physical frame");
            }
            StrictJson.require(!before.identity().frame().snapshotId().equals(after.identity().frame().snapshotId())
                    && after.identity().frame().identity().nativeRevision().compareTo(before.identity().frame().identity().nativeRevision()) > 0
                    && (reconnected || after.identity().frame().revision().compareTo(before.identity().frame().revision()) > 0)
                    && after.identity().frame().identity().dateRaw().compareTo(before.identity().frame().identity().dateRaw()) >= 0,
                    "ordinary mutable effect requires a distinct later Native and public frame");
        }
    }
    private final java.util.function.Supplier<HeldDriverObservationPort> held;
    private final ActionPorts.OutcomeArchive archive;
    private final java.util.Optional<NativeEffectEvidence.FrameLoader> originalFrames;
    /** DATA callback only. The installed Root producer must hold its private pending-event source custody.
     * Empty means no private scope; an active scope failure must throw and never fall back to ordinary observation. */
    @FunctionalInterface public interface ActualAfterPort {
        java.util.Optional<Complete> observe(ActionCommand original,java.time.Instant deadline)
                throws java.io.IOException,InterruptedException;
    }
    private final java.util.Optional<ActualAfterPort> privateAfter;
    public NativeEffectSnapshots(HeldDriverObservationPort held, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(held); this.held = () -> held; this.archive = Objects.requireNonNull(archive);
        this.originalFrames = java.util.Optional.empty();
        this.privateAfter = java.util.Optional.empty();
    }
    /** Production roots replay the original guard closure; an empty cold memory cache grants no new before frame. */
    public NativeEffectSnapshots(HeldDriverObservationPort held, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader actualOriginalFrames) {
        Objects.requireNonNull(held); this.held = () -> held; this.archive = Objects.requireNonNull(archive);
        this.originalFrames = java.util.Optional.of(Objects.requireNonNull(actualOriginalFrames));
        this.privateAfter = java.util.Optional.empty();
    }
    /** Resolve the one currently adopted physical Game lazily; no placeholder held endpoint is manufactured. */
    public NativeEffectSnapshots(java.util.function.Supplier<HeldDriverObservationPort> actualCurrentHeld,
            ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader actualOriginalFrames) {
        this.held = Objects.requireNonNull(actualCurrentHeld); this.archive = Objects.requireNonNull(archive);
        this.originalFrames = java.util.Optional.of(Objects.requireNonNull(actualOriginalFrames));
        this.privateAfter = java.util.Optional.empty();
    }
    /** Same original guard/frame loader, with one source-owned private after observation; no Ready is constructed. */
    public NativeEffectSnapshots(java.util.function.Supplier<HeldDriverObservationPort> actualCurrentHeld,
            ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader actualOriginalFrames,ActualAfterPort actualPrivateAfter){
        this.held=Objects.requireNonNull(actualCurrentHeld);this.archive=Objects.requireNonNull(archive);
        this.originalFrames=java.util.Optional.of(Objects.requireNonNull(actualOriginalFrames));
        this.privateAfter=java.util.Optional.of(Objects.requireNonNull(actualPrivateAfter));
    }
    private Complete observeAfter(ActionCommand command,java.time.Instant deadline,HeldDriverObservationPort alreadyResolved)
            throws java.io.IOException,InterruptedException {
        if(privateAfter.isPresent()){
            var actual=Objects.requireNonNull(privateAfter.orElseThrow().observe(command,deadline));
            if(actual.isPresent())return actual.orElseThrow();
        }
        return (alreadyResolved==null?Objects.requireNonNull(held.get(),"current physical held Game is not adopted"):alreadyResolved).observe(deadline);
    }
    public ExactRef evidence(ActionCommand command, ActionState.Attempt attempt, Pair pair, List<PlanningReadReceipt> independentReads,
            RawJson compatible) { return NativeEffectEvidence.preserve(command, attempt, pair, independentReads, compatible, archive); }
    public ExactRef evidence(ActionCommand command, ActionState.Attempt attempt, Pair pair, List<PlanningReadReceipt> independentReads,
            RawJson compatible, List<ExactRef> supportingMaterials) {
        return NativeEffectEvidence.preserve(command, attempt, pair, independentReads, compatible, supportingMaterials, archive);
    }
    /** Reads an explicitly retained original domain body from the identical immutable archive. */
    public RawJson material(ExactRef reference) {
        RawJson body = archive.loadMaterial(reference); RootGuardChecks.exact(reference, body.bytes()); return body;
    }
    public List<PlanningReadReceipt> reads(List<ExactRef> originalReferences) {
        StrictJson.require(originalReferences != null && originalReferences.size() <= 16, "bounded original query receipt list required");
        return originalReferences.stream().map(reference -> {
            PlanningReadReceipt receipt = archive.loadRead(reference);
            StrictJson.require(archive.readReferenceOf(receipt).equals(reference), "original query receipt identity changed");
            NativeRecordedEvidenceVerifier.requireRead(receipt, archive); return receipt;
        }).toList();
    }
    /** Gives pure domain replay the same scoped immutable archive; it creates no writer session. */
    public <T> T withArchive(java.util.function.Function<ActionPorts.OutcomeArchive, T> work) {
        return Objects.requireNonNull(work).apply(archive);
    }
    /** Concrete adapter to the sole event verifier, using the same held Native publication and Driver assembler. */
    public org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort.IndependentReadPort eventReads() {
        return (command, deadline) -> {
            Complete actual;
            try { actual = ActionReconciliationScope.activeFor(command) ? ActionReconciliationScope.requireFrame(command)
                    : observeAfter(command,deadline,null); }
            catch (java.io.IOException unavailable) { throw new java.io.UncheckedIOException("original pending event read scope unavailable",unavailable); }
            return new org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort.BoundSnapshot(
                    actual.identity(), actual.source(), actual.sessionId(), actual.semantic(), publication(actual),
                    actual.observedAt(), actual.originalEvidence());
        };
    }
    /** Only the explicit direct close profile may sample an unchanged retained SEM after the real ACK.
     * This performs one source-checked currentSnapshot sample on the identical physical held endpoint;
     * it never borrows the private Family/Event after callback or a reconciliation cached frame. */
    public NativeDirectFixedWindowObservation.Original readDirectFixedWindow(ActionCommand command,
            ActionState.Attempt attempt, NativeActionPort.AckReceived originalAck) {
        HeldDriverObservationPort actualHeld = Objects.requireNonNull(held.get(), "current physical held Game is not adopted");
        Complete before = originalFrames.isPresent() ? RootGuardEvidence.loadFrame(attempt.guard(), archive, originalFrames.orElseThrow())
                : actualHeld.requireRetained(command.before(), attempt.guard().nativeEvidence());
        java.time.Instant deadline = ActionObservationWindow.deadline(command);
        try {
            var sampled = actualHeld.sampleCurrentFull(deadline);
            return NativeDirectFixedWindowObservation.capture(command, attempt, originalAck, before, sampled.full(),
                    sampled.sample().data(), deadline, archive);
        } catch (java.io.IOException unavailable) {
            throw new java.io.UncheckedIOException("actual direct fixed-window currentSnapshot sample is unavailable", unavailable);
        }
    }
    /** Original pending receipt only, under the coordinator's actual same-writer reconciliation callback. */
    public java.util.Optional<ActionReceipt> pendingDirectFixedWindow(ActionCommand command, ActionState.Attempt attempt) {
        if (!ActionReconciliationScope.activeFor(command)) return java.util.Optional.empty();
        try {
            var identity = ActionReconciliationScope.requireIdentity(command, attempt);
            ActionReceipt actual = archive.loadReceipt(identity.pending().originalReceipt());
            StrictJson.require(actual.command().actionId().equals(command.actionId())
                    && actual.bodySha256().equals(ActionCodec.bodySha256(command))
                    && ActionTransitions.attempt(actual.state()).filter(attempt::equals).isPresent(),
                    "pending direct-window receipt differs from its original coordinator scope");
            if (!(actual.state() instanceof ActionState.Unknown unresolved) || unresolved.evidence().isEmpty()
                    || unresolved.evidence().getFirst().equals(attempt.guard().nativeEvidence()))
                return java.util.Optional.empty();
            return java.util.Optional.of(actual);
        } catch (java.io.IOException unavailable) {
            throw new java.io.UncheckedIOException("actual pending direct-window original scope unavailable", unavailable);
        }
    }
    public NativeDirectFixedWindowObservation.Original resolveDirectFixedWindow(ActionReceipt original,
            PlanningReadReceipt ownerQuery, Complete actualCurrent) {
        return NativeDirectFixedWindowObservation.resolvePending(original, ownerQuery, actualCurrent, archive,
                originalFrames.orElseThrow(() -> new IllegalStateException("direct-window actual full frame loader is absent")));
    }
    /** Explicit cold DATA profile; an ordinary Pair/Applied loader is never used for these same-frame originals. */
    public NativeDirectFixedWindowObservation.Original loadDirectFixedWindow(ActionReceipt receipt) {
        return NativeDirectFixedWindowObservation.load(receipt, archive, originalFrames.orElseThrow(
                () -> new IllegalStateException("direct fixed-window cold replay requires the actual full Driver frame loader")));
    }
    /** An unavailable direct result preserves its real after sample without becoming a compatible successful result. */
    public static NativeEffectRegistry.Projected withDirectFixedWindowEvidence(NativeEffectRegistry.Projected projected,
            NativeDirectFixedWindowObservation.Original actual) {
        StrictJson.require(projected.result() instanceof ActionPorts.Pending && projected.compatibleResult().isEmpty()
                && actual.completion().isEmpty(), "only an actual pending direct-window sample may enter this evidence path");
        var pending = (ActionPorts.Pending) projected.result();
        StrictJson.require(pending.evidence().isEmpty(), "direct-window pending sample has a single explicit original basis");
        return NativeEffectRegistry.Projected.pending(pending.reason(), List.of(actual.basis()));
    }
    public Pair read(ActionCommand command, ActionState.Attempt attempt) {
        var actual = originals(command, attempt, false, pendingReply(command.operation()));
        java.util.Optional<ReconciliationIdentity> reconciliation=java.util.Optional.empty();
        if(ActionReconciliationScope.activeFor(command)){
            try { reconciliation=java.util.Optional.of(ActionReconciliationScope.requireIdentity(command,attempt)); }
            catch(java.io.IOException unavailable){throw new java.io.UncheckedIOException(unavailable);}
        }
        return new Pair(actual.before(), actual.after(), reconciliation);
    }
    /**
     * A send is observed through independent storage queries, so the actual SEM may
     * remain cached. Only the dedicated typed family branch may borrow that frame;
     * it still has to prove query chronology, full storage and writer exclusion.
     */
    public org.xar.ck3.control.application.effects.family.FamilySendObservation.OriginalFrames readFamilySend(
            ActionCommand command, ActionState.Attempt attempt) {
        StrictJson.require(ActionReconciliationScope.activeFor(command)
                && java.util.Arrays.stream(org.xar.ck3.control.application.effects.family.FamilySendObservation.Profile.values())
                    .anyMatch(profile -> profile.observerSchema().equals(command.expected().observerSchema())),
                "cached SEM is available only to the canonical pending typed family-send observer");
        var actual = originals(command, attempt, true);
        var before = actual.before(); var after = actual.after();
        StrictJson.require(before.identity().machineId().equals(after.identity().machineId())
                && before.identity().game().equals(after.identity().game())
                && before.source().equals(after.source()) && before.sessionId().equals(after.sessionId())
                && before.connectionGeneration().equals(after.connectionGeneration())
                && before.identity().observationVersion() == after.identity().observationVersion()
                && before.identity().frame().episodeRunId().equals(after.identity().frame().episodeRunId())
                && before.identity().frame().identity().player().equals(after.identity().frame().identity().player())
                && before.identity().frame().identity().dateRaw().equals(after.identity().frame().identity().dateRaw())
                && after.identity().frame().identity().nativeRevision().compareTo(before.identity().frame().identity().nativeRevision()) >= 0
                && after.identity().frame().revision().compareTo(before.identity().frame().revision()) >= 0,
                "typed family send crossed the actual Game/player/episode/day/source/connection or regressed a frame");
        return actual;
    }
    private org.xar.ck3.control.application.effects.family.FamilySendObservation.OriginalFrames originals(
            ActionCommand command, ActionState.Attempt attempt, boolean cachedFamilySend) {
        return originals(command, attempt, cachedFamilySend, false);
    }
    private org.xar.ck3.control.application.effects.family.FamilySendObservation.OriginalFrames originals(
            ActionCommand command, ActionState.Attempt attempt, boolean cachedFamilySend, boolean pendingClosure) {
        boolean reconciliation = ActionReconciliationScope.activeFor(command);
        java.time.Instant observationDeadline = reconciliation ? command.deadline() : ActionObservationWindow.deadline(command);
        if (pendingClosure && !reconciliation) {
            java.time.Instant maximum = java.time.Instant.now().plus(ActionObservationWindow.MAXIMUM_WINDOW);
            if (maximum.isBefore(observationDeadline)) observationDeadline = maximum;
        }
        final java.time.Instant fixedDeadline = observationDeadline;
        HeldDriverObservationPort actualHeld = (reconciliation || privateAfter.isPresent()) && originalFrames.isPresent() ? null
                : Objects.requireNonNull(held.get(), "current physical held Game is not adopted");
        Complete before = originalFrames.isPresent() ? RootGuardEvidence.loadFrame(attempt.guard(), archive, originalFrames.orElseThrow())
                : actualHeld.requireRetained(command.before(), attempt.guard().nativeEvidence());
        StrictJson.require(before.identity().equals(command.before()) && before.source().equals(command.source())
                && before.sessionId().equals(command.sessionId()), "retained before-frame drift");
        Complete after;
        try { after = reconciliation ? ActionReconciliationScope.requireFrame(command, attempt)
                : observeAfter(command,fixedDeadline,actualHeld); }
        catch (java.io.IOException unavailable) { throw new java.io.UncheckedIOException("original pending observation scope unavailable", unavailable); }
        catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("independent effect observation interrupted; original action must not be replayed", interrupted);
        }
        StrictJson.require(cachedFamilySend || !after.observedAt().isBefore(attempt.submittedAt()), "Native publication predates submission");
        if (pendingClosure && !reconciliation) {
            Pair actual = awaitPendingClosure(attempt, new Pair(before, after), fixedDeadline,
                    deadline -> observeAfter(command, deadline, actualHeld));
            after = actual.after();
        }
        return new org.xar.ck3.control.application.effects.family.FamilySendObservation.OriginalFrames(before, after);
    }
    private static boolean pendingReply(OperationKey operation) {
        return List.of("accept-pending-character-interaction", "reject-pending-character-interaction",
                "block-pending-character-interaction", "acknowledge-pending-character-interaction").contains(operation.value());
    }

    @FunctionalInterface
    private interface PendingAfterRead {
        Complete read(java.time.Instant deadline) throws java.io.IOException, InterruptedException;
    }

    /** Waits on original read-only frames; the existing domain projector still decides completion. */
    private static Pair awaitPendingClosure(ActionState.Attempt attempt, Pair first,
            java.time.Instant fixedDeadline, PendingAfterRead reader) {
        java.math.BigInteger originalId = pendingInstance(first.before().semantic()).orElseThrow(
                () -> new IllegalArgumentException("original pending frame needs its canonical signed int32 instance"));
        Pair last = first;
        while (pendingInstance(last.after().semantic()).filter(originalId::equals).isPresent()) {
            java.time.Instant now = java.time.Instant.now();
            if (!now.isBefore(fixedDeadline)) return last;
            try {
                long sleepNanos = Math.min(50_000_000L, java.time.Duration.between(now, fixedDeadline).toNanos());
                Thread.sleep(sleepNanos / 1_000_000L, (int) (sleepNanos % 1_000_000L));
                if (!java.time.Instant.now().isBefore(fixedDeadline)) return last;
                Complete actual;
                try { actual = reader.read(fixedDeadline); }
                catch (IllegalArgumentException failure) {
                    if ("actual observation deadline expired".equals(failure.getMessage())
                            && !java.time.Instant.now().isBefore(fixedDeadline)) return last;
                    throw failure;
                }
                Pair candidate = new Pair(first.before(), actual);
                StrictJson.require(!actual.observedAt().isBefore(attempt.submittedAt()), "Native publication predates submission");
                requirePendingOrder(last.after(), actual);
                last = candidate;
            } catch (java.io.IOException | java.io.UncheckedIOException unavailable) {
                return last;
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                return last;
            }
        }
        return last;
    }

    private static void requirePendingOrder(Complete previous, Complete actual) {
        var before = previous.identity().frame();
        var after = actual.identity().frame();
        StrictJson.require(after.identity().nativeRevision().compareTo(before.identity().nativeRevision()) >= 0
                && after.revision().compareTo(before.revision()) >= 0
                && after.identity().dateRaw().compareTo(before.identity().dateRaw()) >= 0,
                "pending observation regressed its last actual frame");
        if (after.identity().nativeRevision().equals(before.identity().nativeRevision())
                && after.revision().equals(before.revision())) {
            StrictJson.require(actual.identity().equals(previous.identity())
                    && actual.semantic().equals(previous.semantic())
                    && actual.originalEvidence().equals(previous.originalEvidence())
                    && actual.fullBindingSha256().equals(previous.fullBindingSha256())
                    && actual.observedAt().equals(previous.observedAt()),
                    "cached pending frame changed without an actual Native/public revision");
        }
    }

    /** Empty does not mean absent: the unchanged actual semantic value is retained for the domain verifier. */
    private static java.util.Optional<java.math.BigInteger> pendingInstance(
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj semantic) {
        var value = semantic.get("pending_character_interaction");
        if (!(value instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj pending))
            return java.util.Optional.empty();
        var instance = pending.get("instance_id");
        if (instance == null) return java.util.Optional.empty();
        try {
            var id = org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(instance, "pending instance");
            return id.bitLength() <= 31 && !id.equals(java.math.BigInteger.valueOf(-1))
                    ? java.util.Optional.of(id) : java.util.Optional.empty();
        } catch (IllegalArgumentException malformed) {
            return java.util.Optional.empty();
        }
    }


    public static NativeEffectRegistry.Projected observed(ActionCommand command, ActionState.Attempt attempt,
            Complete after, String schema, List<ExpectedValue> actual, String actualReadIdentity, org.xar.ck3.control.application.action.RawJson compatible,
            List<org.xar.ck3.control.contracts.ExactRef> supportingEvidence) {
        return observed(command, attempt, after, schema, actual, new ObservationProvenance.Query(actualReadIdentity), compatible, supportingEvidence);
    }
    public static NativeEffectRegistry.Projected observed(ActionCommand command, ActionState.Attempt attempt,
            Complete after, String schema, List<ExpectedValue> actual, ObservationProvenance provenance, RawJson compatible,
            List<ExactRef> supportingEvidence) {
        StrictJson.require(ProposalLifecycle.compare(command.expected(), after.identity(), after.source(), schema, actual)
                == ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH, "independent Native material values differ from requested postcondition");
        var proof = new ActionState.EffectObservation(after.identity(), after.source(), after.sessionId(), schema, actual,
                provenance, after.observedAt(), after.originalEvidence(), supportingEvidence);
        ActionEffects.validate(command, attempt, new ActionState.Applied(proof));
        return new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(proof), java.util.Optional.of(compatible));
    }
    /** Unsolicited Native snapshots have an original packet identity, not an invented action ACK ID. */
    public static ObservationProvenance.Push publication(Complete actual) {
        return new ObservationProvenance.Push(actual.identity().frame().snapshotId(), actual.identity().frame().identity().nativeRevision(), actual.originalEvidence());
    }
    /** Attaches a durably preserved original basis to a pure projection before it reaches the writer. */
    public static NativeEffectRegistry.Projected withEvidence(NativeEffectRegistry.Projected projected, List<ExactRef> supporting) {
        if (!(projected.result() instanceof ActionPorts.EffectObserved observed)) return projected;
        var original = observed.observation();
        var bound = new ActionState.EffectObservation(original.after(), original.source(), original.sessionId(), original.observerSchema(),
                original.actual(), original.provenance(), original.observedAt(), original.originalEvidence(), supporting);
        return new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(bound), projected.compatibleResult());
    }
    public static void requireAfterRead(ActionCommand command, ActionState.Attempt attempt, Complete after,
            PlanningReadReceipt read, OperationKey operation) {
        boolean reconciliation = read.request().origin() instanceof CommandOrigin.Reconciliation;
        if (reconciliation) {
            var original = read.request().origin().requireReconciliation(); var pending = original.pending();
            StrictJson.require(pending.actionId().equals(command.actionId()) && pending.bodySha256().equals(ActionCodec.bodySha256(command))
                    && pending.requestId().equals(attempt.requestId()) && pending.originalBefore().equals(command.before())
                    && original.connectionGeneration().equals(after.connectionGeneration())
                    && original.nativeEvidence().equals(after.originalEvidence()), "reconciliation material query belongs to another original primitive");
            original.requireOriginalConnection(attempt.guard());
            var chronology = read.original().custody().orElseThrow(
                    () -> new IllegalArgumentException("reconciliation material query has no actual wire sampling custody"));
            chronology.verify(read);
            StrictJson.require(!chronology.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                    "reconciliation material query was sampled before the original submission");
        }
        var factual = reconciliation ? read.request().reconciliationBefore() : read.request().before();
        String binding = reconciliation ? read.request().origin().requireReconciliation().bindingSha256() : after.fullBindingSha256();
        StrictJson.require(factual.equals(after.identity()) && read.request().source().equals(after.source())
                && read.request().sessionId().equals(after.sessionId()) && read.request().operation().equals(operation)
                && readFrame(read.before().binding(), read.request()).equals(after.identity()) && readFrame(read.after().binding(), read.request()).equals(after.identity())
                && read.before().binding().nativeEvidence().equals(after.originalEvidence()) && read.after().binding().nativeEvidence().equals(after.originalEvidence())
                && read.before().binding().connectionGeneration().equals(after.connectionGeneration()) && read.after().binding().connectionGeneration().equals(after.connectionGeneration())
                && read.before().originalBindingSha256().equals(binding) && read.after().originalBindingSha256().equals(binding)
                && (reconciliation || !read.before().binding().observedAt().isBefore(attempt.submittedAt())) && !read.requestId().equals(attempt.requestId())
                && read.original().nativeOk(), "independent material read crossed the original after-frame/request/submission binding");
        StrictJson.require(read.request().source().equals(command.source()) && read.request().sessionId().equals(command.sessionId()), "independent material read source/session drift");
    }
    private static org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity readFrame(GuardEvidence guard, PlanningReadRequest request) {
        if (request.origin() instanceof CommandOrigin.Reconciliation reconciliation) {
            StrictJson.require(guard.origin() instanceof CommandOrigin.Reconciliation
                    && guard.origin().requireReconciliation().sameGuardFrame(reconciliation.identity()),
                    "reconciliation read guard changed its original pending identity");
            return guard.origin().requireReconciliation().factual();
        }
        StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay && guard.origin() instanceof CommandOrigin.Gameplay,
                "ordinary material query requires an explicit gameplay or reconciliation origin");
        return guard.observed();
    }
}
