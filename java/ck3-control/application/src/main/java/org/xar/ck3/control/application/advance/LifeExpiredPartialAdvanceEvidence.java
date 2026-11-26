package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.node.BooleanNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Original evidence and complete archived replay for a finite expired clock with real partial game-date progress. */
public final class LifeExpiredPartialAdvanceEvidence {
    public static final String SCHEMA = "xar.ck3.java-life-expired-partial-evidence/v1";
    public static final String TERMINAL_SCHEMA = "xar.ck3.java-life-expired-partial-terminal/v1";
    private static final String REASON = "original Life expired before its target; archived partial progress, reconciliation only";
    public static final String EXPIRY_STATUS_FIELD = "date_sentinel_expiry";
    public static final String EXPIRY_STATUS_SCHEMA = "ck3_1210_date_sentinel_expiry_v1";
    private static final ExactCk3Build PROFILE = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final int DATE_SENTINEL_FAILURE_EXPIRED = 1 << 5;
    private static final Set<String> FIELDS = Set.of("schema", "parent_receipt", "child_receipts", "status_read", "ending");
    private final ActionPorts.OutcomeArchive archive;
    private final LifeAdvanceEvidence.BoundFrameVerifier frames;
    private final AdvancePrimitiveArchivedReplay primitives;

    public LifeExpiredPartialAdvanceEvidence(ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames, AdvancePrimitiveArchivedReplay primitives) {
        this.archive = Objects.requireNonNull(archive);
        this.frames = Objects.requireNonNull(frames);
        this.primitives = Objects.requireNonNull(primitives);
    }

    /** The provider must take both observations in the original parent's independent held read scope. */
    public record Capture(ClockStatusRead.Observation status, AdvanceObservationPort.Frame ending) {
        public Capture { Objects.requireNonNull(status); Objects.requireNonNull(ending); }
    }
    /** Archive-derived facts only. The original action receipts retain their unchanged outcomes and deadlines. */
    public record Observed(ActionReceipt parent, List<ActionReceipt> children,
            AdvanceObservationPort.Frame ending, BigInteger generation, long elapsedGameDays) {
        public Observed { children = List.copyOf(children); }
    }

    /** Absence of this separate Native payload cannot be inferred from generic FAILED status or diagnostics. */
    static Optional<ExpiryStatus> expiryStatus(NativeActionPort.AckReceived original) {
        var slot = ClockStatusRead.decode(original);
        var token = StrictJson.parse(original.originalResultToken().orElseThrow().bytes());
        if (!token.has(EXPIRY_STATUS_FIELD)) return Optional.empty();
        var value = StrictJson.object(token.get(EXPIRY_STATUS_FIELD), Set.of("schema", "generation", "original_deadline_unix_ms",
                "failure_flags", "armed", "shutdown_safe", "access_cleanup_unknown"));
        BigInteger generation = StrictJson.integer(value.get("generation"), BigInteger.ONE, StrictJson.UINT64_MAX);
        require(EXPIRY_STATUS_SCHEMA.equals(StrictJson.text(value.get("schema"))) && slot.state() == State.FAILED
                && generation.toString().equals(slot.generation().decimal())
                && StrictJson.integer(value.get("failure_flags"), 0, 0xffff_ffffL) == DATE_SENTINEL_FAILURE_EXPIRED
                && BooleanNode.FALSE.equals(value.get("armed")) && BooleanNode.TRUE.equals(value.get("shutdown_safe"))
                && BooleanNode.FALSE.equals(value.get("access_cleanup_unknown")), "native source did not prove this exact disarmed expiry");
        return Optional.of(new ExpiryStatus(generation, StrictJson.integer(value.get("original_deadline_unix_ms"), 1, Long.MAX_VALUE)));
    }

    record ExpiryStatus(BigInteger generation, long nativeDeadlineMillis) { }

    /** Selects the canonical original ARM and its independently confirmed Core resume, after the original parent window. */
    static boolean accepts(ActionReceipt parent, List<ActionReceipt> children, Instant now) {
        if (!(parent.state() instanceof ActionState.CompositeUnknown) || !now.isAfter(parent.command().deadline())
                || !PROFILE.executableSha256().equalsIgnoreCase(parent.command().source().exactBuild())
                || children.size() < 2 || children.size() > 4) return false;
        var resume = children.getLast();
        var arm = children.get(children.size() - 2);
        if (!(resume.state() instanceof ActionState.Settled resumed && resumed.settlement() instanceof ActionState.ResumeCoreApplied)
                || !(arm.state() instanceof ActionState.Settled armed && armed.settlement() instanceof ActionState.ControlApplied)
                || resume.sequence() >= parent.sequence()) return false;
        var actions = new ArrayList<>(children);
        actions.add(parent);
        if (ContinuityBatchJournal.readOnlyLifeRecoveryRoot(actions).filter(parent::equals).isEmpty()) return false;
        var plan = AdvancePlan.decode(parent.command());
        return parent.command().operation().value().equals("life-advance")
                && plan.clockMode() == AdvancePlan.ClockMode.CAMPAIGN_SENTINEL && plan.horizonDays() > 1 && plan.dailyWatch().isEmpty()
                && arm.command().operation().value().equals(plan.armStep())
                && resume.command().operation().value().equals("resume-map");
    }

    private record Proof(ExactRef reference, Observed observed) { }

    Optional<ActionPorts.EffectObserved> settle(ActionReceipt parent, List<ActionReceipt> children,
            AdvanceObservationPort.Frame starting, Capture actual) {
        if (expiryStatus(actual.status().receipt().original()).isEmpty()
                || !boundPhysicalFrame(actual.status(), actual.ending())
                || !(actual.ending().provenance() instanceof ObservationProvenance.FreshSnapshotQuery fresh)
                || !(fresh.basis() instanceof ObservationProvenance.LiveAfterSetter
                        || fresh.basis() instanceof ObservationProvenance.SameGameWatch)) return Optional.empty();
        var ending = LifeAdvanceEvidence.preserveFrame(actual.ending(), archive);
        var restored = LifeAdvanceEvidence.restore(parent.command(), ending, archive, frames);
        var observed = verify(parent, children, actual.status(), restored);
        List<Value> references = children.stream().map(child -> reference(archive.receiptReferenceOf(child))).toList();
        var proof = new Obj(Map.of("schema", new Text(SCHEMA), "parent_receipt", reference(archive.receiptReferenceOf(parent)),
                "child_receipts", new Arr(references), "status_read", reference(archive.readReferenceOf(actual.status().receipt())),
                "ending", LifeAdvanceEvidence.frame(ending)));
        return Optional.of(terminal(starting, new Proof(archive.preserveMaterial(new RawJson(DriverJson.encode(proof))), observed)));
    }

    /** An existing observation-only receipt may settle through the same archived proof. */
    Optional<ActionPorts.EffectObserved> settleRetained(ActionReceipt current, List<ActionReceipt> children,
            AdvanceObservationPort.Frame starting) {
        if (!(current.state() instanceof ActionState.CompositeUnknown state) || !state.reason().equals(REASON)) return Optional.empty();
        require(state.evidence().size() == 1, "expired partial cursor lacks its single original proof");
        var reference = state.evidence().getFirst();
        var observed = replay(reference);
        require(observed.children().equals(children) && isPredecessor(current, observed.parent(), reference),
                "retained partial expiry changed the original canonical parent or children");
        return Optional.of(terminal(starting, new Proof(reference, observed)));
    }

    static boolean isPredecessor(ActionReceipt current, ActionReceipt original, ExactRef proof) {
        if (current.equals(original)) return true;
        return current.state() instanceof ActionState.CompositeUnknown cursor
                && original.state() instanceof ActionState.CompositeUnknown prior
                && current.sequence() > original.sequence() && current.command().equals(original.command())
                && current.bodySha256().equals(original.bodySha256()) && cursor.execution().equals(prior.execution())
                && cursor.reason().equals(REASON) && cursor.evidence().equals(List.of(proof));
    }

    private ActionPorts.EffectObserved terminal(AdvanceObservationPort.Frame starting, Proof captured) {
        var evidence = captured.observed();
        var parent = evidence.parent();
        var startingRecord = LifeAdvanceEvidence.preserveFrame(starting, archive);
        verifyStarting(parent, startingRecord, evidence.ending());
        var body = new Obj(Map.of("schema", new Text(TERMINAL_SCHEMA), "expiry", reference(captured.reference()),
                "starting", LifeAdvanceEvidence.frame(startingRecord)));
        var saved = archive.preserveMaterial(new RawJson(DriverJson.encode(body)));
        return new ActionPorts.EffectObserved(observation(parent.command(), evidence.ending(), saved));
    }

    private record OriginalData(ActionReceipt parent, List<ActionReceipt> children,
            LifeAdvanceEvidence.FrameRecord ending, PlanningReadReceipt status) { }

    /** Prior receipts and exact frame/read references only. Full replay owns qualification. */
    public record TerminalData(ExactRef reference, ExactRef expiryReference, ActionReceipt original,
            List<ActionReceipt> children, LifeAdvanceEvidence.FrameRecord starting,
            LifeAdvanceEvidence.FrameRecord ending, PlanningReadReceipt status) {
        public TerminalData { children = List.copyOf(children); }
    }

    static boolean isTerminalSchema(Obj body) {
        return new Text(TERMINAL_SCHEMA).equals(body.get("schema"));
    }

    /** Structural selector only. Original bytes, history and terminal authority are not checked here. */
    public static boolean terminalShape(ActionReceipt receipt) {
        var command = receipt.command();
        if (!(receipt.state() instanceof ActionState.CompositeSettled settled)
                || !(settled.settlement() instanceof ActionState.Applied applied)
                || !settled.execution().handlerId().equals(LifeAdvanceComposite.HANDLER)
                || !command.operation().value().equals("life-advance")
                || !PROFILE.executableSha256().equalsIgnoreCase(command.source().exactBuild())) return false;
        var effect = applied.observation();
        if (!receipt.visibleGameplay() || receipt.eligibleAdvance() || effect.supportingEvidence().size() != 1
                || !effect.observedAt().isAfter(command.deadline())
                || !(effect.provenance() instanceof ObservationProvenance.FreshSnapshotQuery fresh)
                || !(fresh.basis() instanceof ObservationProvenance.LiveAfterSetter || fresh.basis() instanceof ObservationProvenance.SameGameWatch)
                || !effect.actual().contains(new ExpectedText(new FieldKey("progress_status"),
                        AdvanceResult.progressStatus(AdvanceClock.ProgressStatus.WALL_TIMEOUT_WITH_DATE_PROGRESS)))) return false;
        try {
            var plan = AdvancePlan.decode(command);
            return plan.clockMode() == AdvancePlan.ClockMode.CAMPAIGN_SENTINEL && plan.horizonDays() > 1 && plan.dailyWatch().isEmpty();
        } catch (IllegalArgumentException invalid) { return false; }
    }

    /** Decodes only the exact durable originals. Does not grant current observation or terminal authority. */
    public static Optional<TerminalData> readTerminalData(ActionReceipt receipt, ActionPorts.OutcomeArchive archive) {
        if (!terminalShape(receipt)) return Optional.empty();
        var settled = (ActionState.CompositeSettled) receipt.state();
        var effect = receipt.applied().orElseThrow().observation();
        var reference = effect.supportingEvidence().getFirst();
        var body = exactMaterial(reference, archive);
        if (!isTerminalSchema(body)) return Optional.empty();
        require(body.members().keySet().equals(Set.of("schema", "expiry", "starting")), "expired Life terminal fields differ");
        var expiryRef = exact(body.get("expiry"));
        require(!expiryRef.equals(reference), "expired Life terminal repeats its own proof reference");
        var prior = loadOriginal(expiryRef, archive);
        var first = LifeAdvanceEvidence.decodeFrame(object(body.get("starting"), "starting"), false);
        var end = prior.ending();
        var original = prior.parent();
        require(accepts(original, prior.children(), end.observedAt())
                && original.state() instanceof ActionState.CompositeUnknown unknown && unknown.execution().equals(settled.execution())
                && original.command().equals(receipt.command()) && original.bodySha256().equals(receipt.bodySha256())
                && original.sequence() < receipt.sequence()
                && first.identity().equals(receipt.command().before()) && end.identity().equals(effect.after())
                && end.provenance().equals(effect.provenance()) && end.observedAt().equals(effect.observedAt())
                && end.nativeFrame().equals(effect.originalEvidence()) && receipt.visibleGameplay() && !receipt.eligibleAdvance(),
                "expired Life terminal differs from the exact prior parent, child vector or frames");
        var status = originalStatus(prior.status(), archive);
        status.requirePhysicalParent(receipt.command());
        var plan = AdvancePlan.decode(receipt.command());
        requireExpirySlot(receipt.command(), plan, prior.children().get(prior.children().size() - 2), status);
        require(boundPhysicalFrame(status, end.identity(), end.nativeFrame(), end.observedAt()),
                "expired Life terminal requires exact native expiry Status bound to the complete ending Frame");
        partialDays(plan, status.status(), end.identity().frame().identity().dateRaw());
        return Optional.of(new TerminalData(reference, expiryRef, original, prior.children(), first, end, prior.status()));
    }

    LifeAdvanceEvidence.Recorded verifyTerminal(ActionReceipt receipt, TerminalData data) {
        verifyFrameBytes(data.starting());
        verifyFrameBytes(data.ending());
        var original = new OriginalData(data.original(), data.children(), data.ending(), data.status());
        var observed = replay(original);
        verifyStarting(data.original(), data.starting(), observed.ending());
        require(receipt.applied().orElseThrow().observation().equals(observation(receipt.command(), observed.ending(), data.reference())),
                "expired Life terminal did not rederive its exact visible partial progress");
        return new LifeAdvanceEvidence.Recorded(data.starting(), data.ending(), Optional.empty());
    }

    private void verifyStarting(ActionReceipt parent, LifeAdvanceEvidence.FrameRecord record, AdvanceObservationPort.Frame ending) {
        require(frames instanceof LifeAdvanceEvidence.EntryFrameReader, "expiry terminal requires the installed original Life entry reader");
        var execution = ((ActionState.CompositeUnknown) parent.state()).execution();
        var starting = LifeAdvanceEvidence.restore(parent.command(), record, archive, frames);
        var actual = ((LifeAdvanceEvidence.EntryFrameReader) frames).read(parent.command(), execution.guard(), archive).orElseThrow();
        require(actual.equals(starting) && starting.identity().equals(parent.command().before()),
                "expiry terminal starting frame differs from its original canonical Life guard");
        AdvanceWait.binding(parent.command(), starting, ending);
    }

    private void verifyFrameBytes(LifeAdvanceEvidence.FrameRecord frame) {
        requireBytes(frame.nativeFrame(), archive.loadNativeFrame(frame.nativeFrame()));
        requireBytes(frame.driverFacts(), archive.loadFullMaterial(frame.driverFacts()).bytes());
        requireBytes(frame.semantic(), archive.loadFullMaterial(frame.semantic()).bytes());
    }

    private static void requireBytes(ExactRef reference, byte[] bytes) {
        require(bytes.length == reference.bytes() && ActionCodec.sha256(bytes).equals(reference.sha256()),
                "expired partial evidence differs from its original archive");
    }

    private static ActionState.EffectObservation observation(ActionCommand parent, AdvanceObservationPort.Frame ending, ExactRef proof) {
        return LifeAdvanceComposite.observation(parent, AdvancePlan.decode(parent), ending,
                AdvanceClock.ProgressStatus.WALL_TIMEOUT_WITH_DATE_PROGRESS, null, List.of(proof));
    }

    public Observed replay(ExactRef original) {
        return replay(loadOriginal(original, archive));
    }

    private Observed replay(OriginalData original) {
        var status = originalStatus(original.status(), archive);
        var ending = LifeAdvanceEvidence.restore(original.parent().command(), original.ending(), archive, frames);
        return verify(original.parent(), original.children(), status, ending);
    }

    private static ClockStatusRead.Observation originalStatus(PlanningReadReceipt read, ActionPorts.OutcomeArchive archive) {
        return new ClockStatusRead.Observation(ClockStatusRead.decode(read.original()), read, archive.referenceOf(read.original()));
    }

    private static OriginalData loadOriginal(ExactRef reference, ActionPorts.OutcomeArchive archive) {
        var body = exactMaterial(reference, archive);
        require(body.members().keySet().equals(FIELDS) && new Text(SCHEMA).equals(body.get("schema")), "exact expired partial evidence schema required");
        var childRefs = array(body.get("child_receipts"), "child_receipts");
        require(childRefs.size() >= 2 && childRefs.size() <= 4, "expired partial requires the complete finite child prefix");
        var parent = receipt(exact(body.get("parent_receipt")), archive);
        var children = childRefs.stream().map(ref -> receipt(exact(ref), archive)).toList();
        var statusRef = exact(body.get("status_read"));
        var read = archive.loadRead(statusRef);
        require(statusRef.equals(archive.readReferenceOf(read)), "expired partial Status differs from its archived original");
        var ending = LifeAdvanceEvidence.decodeFrame(object(body.get("ending"), "ending"), false);
        return new OriginalData(parent, children, ending, read);
    }

    private static Obj exactMaterial(ExactRef reference, ActionPorts.OutcomeArchive archive) {
        byte[] bytes = archive.loadMaterial(reference).bytes();
        requireBytes(reference, bytes);
        return DriverJson.object(bytes, RawJson.MAXIMUM_BYTES);
    }

    private Observed verify(ActionReceipt parent, List<ActionReceipt> children,
            ClockStatusRead.Observation status, AdvanceObservationPort.Frame ending) {
        require(accepts(parent, children, ending.observedAt()), "expiry evidence needs the original Core-confirmed timeline after its deadline");
        require(receipt(archive.receiptReferenceOf(parent)).equals(parent), "expiry parent is not its original immutable receipt");
        for (var child : children) {
            require(receipt(archive.receiptReferenceOf(child)).equals(child), "expiry child is not its original immutable receipt");
            primitives.verify(child, archive);
        }
        var arm = children.get(children.size() - 2);
        var resume = children.getLast();
        var core = (ActionState.ResumeCoreApplied) ((ActionState.Settled) resume.state()).settlement();
        var coreParent = receipt(core.observation().parentReceipt());
        require(coreParent.state() instanceof ActionState.CompositeRunning running
                && coreParent.command().equals(parent.command()) && coreParent.bodySha256().equals(parent.bodySha256())
                && running.execution().equals(((ActionState.CompositeUnknown) parent.state()).execution())
                && coreParent.sequence() < resume.sequence(), "Core resume reservation changed the original Life body or its child prefix");
        var command = parent.command();
        var plan = AdvancePlan.decode(command);
        var expiry = requireExpirySlot(command, plan, arm, status);
        var armAck = originalAck(arm, FullSnapshotDateSentinelArm.additionalFields(arm.command(), PROFILE));
        var resumeAck = originalAck(resume, FullSnapshotClockControl.additionalFields(resume.command(), PROFILE));
        AdvancePrimitives.nativeResult(resume.ack().orElseThrow(), "resume-map");
        require(armAck.session().equals(resumeAck.session()) && armAck.custodyEpoch().equals(resumeAck.custodyEpoch())
                && resumeAck.writeEntered().order().compareTo(armAck.responseReceived().order()) > 0
                && !resumeAck.writeEntered().observedAt().isBefore(armAck.responseReceived().observedAt()), "resume did not follow the original ARM ACK in its held session");
        status.requirePhysicalParent(command);
        NativeRecordedEvidenceVerifier.requireRead(status.receipt(), archive);
        require(status.originalEvidence().equals(archive.referenceOf(status.receipt().original())), "expiry status changed its original native ACK");
        var full = ending.identity();
        var physical = status.physicalIdentity().orElseThrow();
        require(ending.source().equals(command.source()) && ending.sessionId().equals(command.sessionId())
                && full.machineId().equals(command.before().machineId()) && full.game().equals(command.before().game())
                && full.observationVersion() == command.before().observationVersion()
                && full.frame().episodeRunId().equals(command.before().frame().episodeRunId())
                && full.frame().identity().player().equals(command.before().frame().identity().player())
                && full.frame().identity().nativeRevision().compareTo(resume.command().before().frame().identity().nativeRevision()) > 0
                && full.frame().revision().compareTo(command.before().frame().revision()) >= 0
                && boundPhysicalFrame(status, ending)
                && AdvancePolicy.truth(ending.semantic(), "paused") && AdvancePolicy.truth(ending.semantic(), "map_ready")
                && AdvancePolicy.truth(object(ending.semantic().get("played_character"), "original living actor"), "alive"),
                "expiry status and complete independent paused frame crossed their original Game/session/actor or occurrence");
        require(ending.provenance() instanceof ObservationProvenance.FreshSnapshotQuery,
                "expiry frame needs the original Core-confirmed resume's independent Full read");
        var fresh = (ObservationProvenance.FreshSnapshotQuery) ending.provenance();
        var fullAck = archive.load(fresh.readAcknowledgement());
        require(fullAck instanceof NativeActionPort.AckReceived acknowledged && acknowledged.nativeOk()
                && acknowledged.requestId().equals(fresh.requestId()), "expiry requires the exact acknowledged independent Full read");
        var fullCustody = ((NativeActionPort.AckReceived) fullAck).custody().orElseThrow();
        var statusCustody = status.receipt().original().custody().orElseThrow();
        fullCustody.verify((NativeActionPort.AckReceived) fullAck);
        statusCustody.verify(status.receipt());
        requireFreshBasis(fresh.basis(), archive.receiptReferenceOf(parent), archive.receiptReferenceOf(resume),
                archive.referenceOf(resume.ack().orElseThrow()), resumeAck, fullCustody);
        require(fresh.independentOf(resumeAck.requestId()) && fresh.independentOf(armAck.requestId())
                && fresh.independentOf(statusCustody.requestId()) && fullCustody.session().equals(physical.transport())
                && !statusCustody.requestId().equals(armAck.requestId()) && !statusCustody.requestId().equals(resumeAck.requestId())
                && statusCustody.session().equals(fullCustody.session()) && statusCustody.custodyEpoch().equals(fullCustody.custodyEpoch())
                && fullCustody.writeEntered().observedAt().isAfter(command.deadline())
                && fresh.snapshotReceived().observedAt().equals(ending.observedAt())
                && statusCustody.writeEntered().order().compareTo(fullCustody.responseReceived().order()) > 0
                && statusCustody.writeEntered().order().compareTo(fresh.snapshotReceived().order()) > 0
                && !statusCustody.writeEntered().observedAt().isBefore(ending.observedAt()),
                "expiry observation did not independently sample the original clock and Full frame after the original deadline");

        long days = partialDays(plan, status.status(), full.frame().identity().dateRaw());
        return new Observed(parent, children, ending, expiry.generation(), days);
    }

    private static boolean boundPhysicalFrame(ClockStatusRead.Observation status, AdvanceObservationPort.Frame ending) {
        return boundPhysicalFrame(status, ending.identity(), ending.originalEvidence(), ending.observedAt());
    }

    private static boolean boundPhysicalFrame(ClockStatusRead.Observation status,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity ending, ExactRef evidence, Instant observedAt) {
        var frame = ending.frame();
        return status.physicalIdentity().filter(physical -> physical.snapshotId().equals(frame.snapshotId())
                && physical.nativeRevision().equals(frame.identity().nativeRevision())
                && physical.nativeEvidence().equals(evidence) && physical.observedAt().equals(observedAt)).isPresent();
    }

    static void requireFreshBasis(ObservationProvenance.FreshSnapshotBasis basis, ExactRef parent, ExactRef resume,
            ExactRef resumeAcknowledgement, NativeRequestChronology resumeAck, NativeRequestChronology fullRead) {
        boolean original = basis instanceof ObservationProvenance.LiveAfterSetter same
                && same.setterAcknowledgement().equals(resumeAcknowledgement)
                && fullRead.session().equals(resumeAck.session()) && fullRead.custodyEpoch().equals(resumeAck.custodyEpoch())
                && fullRead.writeEntered().order().compareTo(resumeAck.responseReceived().order()) > 0;
        boolean reconnected = basis instanceof ObservationProvenance.SameGameWatch watch
                && watch.originalParentReceipt().equals(parent) && watch.originalResumeReceipt().equals(resume)
                && fullRead.session().connectionGeneration().compareTo(resumeAck.session().connectionGeneration()) > 0;
        require((original || reconnected)
                && fullRead.session().game().equals(resumeAck.session().game())
                && fullRead.session().machineId().equals(resumeAck.session().machineId())
                && fullRead.session().sessionId().equals(resumeAck.session().sessionId()),
                "expiry Full read lacks its original held ACK or exact same-Game Core-confirmed watch");
    }

    private static ExpiryStatus requireExpirySlot(ActionCommand parent, AdvancePlan plan, ActionReceipt arm,
            ClockStatusRead.Observation status) {
        var expiry = expiryStatus(status.receipt().original())
                .orElseThrow(() -> new IllegalArgumentException("source-owned native expiry status is absent"));
        var originalSlot = AdvancePrimitives.acknowledgedSentinel(arm.ack().orElseThrow(), plan.armStep());
        AdvanceClock.validateArm(originalSlot, plan);
        AdvanceClock.requireSameSlot(originalSlot, status.status());
        require(expiry.nativeDeadlineMillis() == arm.command().deadline().toEpochMilli()
                && !arm.command().deadline().isAfter(parent.deadline()), "expiry status changed the original ARM deadline");
        return expiry;
    }

    static long partialDays(AdvancePlan plan, Status status, BigInteger currentDate) {
        BigInteger elapsed = currentDate.subtract(plan.startingDateRaw());
        BigInteger[] dayPosition = elapsed.divideAndRemainder(AdvancePlan.DAY);
        require(status.state() == State.FAILED && status.abnormal() && status.pauseObserved() && !status.terminalObserved()
                && elapsed.signum() > 0 && dayPosition[1].signum() == 0 && currentDate.compareTo(plan.targetDateRaw()) < 0
                && BigInteger.valueOf(status.lastObservedDateRaw()).equals(currentDate)
                && BigInteger.valueOf(status.triggerDateRaw()).equals(currentDate)
                && BigInteger.valueOf(status.completedDailyTicks()).equals(dayPosition[0])
                && BigInteger.valueOf(status.signedDateDeltaFromTargetRaw()).equals(currentDate.subtract(plan.targetDateRaw()))
                && status.overshootDays() == 0 && !status.triggerReasons().contains("date_deadline"),
                "expiry lacks a strictly partial same-generation whole-day advance");
        return dayPosition[0].longValueExact();
    }

    private NativeRequestChronology originalAck(ActionReceipt original, RawJson expectedFields) {
        require(receipt(archive.receiptReferenceOf(original)).equals(original), "expiry original action is not its archived immutable receipt");
        var attempt = ActionTransitions.attempt(original.state()).orElseThrow();
        var request = attempt.preparedRequest(); var command = original.command();
        var ack = original.ack().orElseThrow();
        require(ack.nativeOk() && ack.requestId().equals(attempt.requestId()) && request.step().equals(command.operation().value())
                && request.additionalFields().equals(expectedFields) && request.equals(archive.loadRequest(archive.requestReferenceOf(request)))
                && ack.equals(archive.load(archive.referenceOf(ack))), "expiry original request/ACK differs from its actual source-bound reservation");
        var chronology = ack.custody().orElseThrow();
        chronology.verify(ack, attempt.guard());
        require(!chronology.writeEntered().observedAt().isBefore(attempt.submittedAt())
                && !chronology.responseReceived().observedAt().isAfter(command.deadline()), "original expiry child escaped the unchanged action deadline");
        ByteBuffer wire = ByteBuffer.wrap(ack.outbound().orElseThrow().originalPacket()).order(ByteOrder.LITTLE_ENDIAN);
        require(wire.remaining() >= 5 && wire.getInt() == wire.remaining(), "expiry original outbound framing differs");
        byte[] body = new byte[wire.remaining()]; wire.get(body);
        var json = ContinuityJson.object(StrictJson.parse(body));
        require("execute_step".equals(StrictJson.text(json.remove("type"))) && StrictJson.integer(json.remove("protocol_version"), 1, 1) == 1
                && attempt.requestId().equals(StrictJson.text(json.remove("request_id"))) && request.step().equals(StrictJson.text(json.remove("step")))
                && command.before().frame().identity().nativeRevision().equals(StrictJson.integer(json.remove("expected_revision"), BigInteger.ONE, StrictJson.UINT64_MAX))
                && java.util.Arrays.equals(StrictJson.canonical(json), request.additionalFields().bytes()), "expiry original outbound command fields or deadline changed");
        return chronology;
    }

    private ActionReceipt receipt(ExactRef ref) { return receipt(ref, archive); }

    private static ActionReceipt receipt(ExactRef ref, ActionPorts.OutcomeArchive archive) {
        var original = archive.loadReceipt(ref);
        require(archive.receiptReferenceOf(original).equals(ref), "expired partial evidence changed its original receipt");
        return original;
    }

    private static Value reference(ExactRef value) { return DriverJson.fromNode(value.toJson()); }
    private static ExactRef exact(Value value) { return ExactRef.fromJson(toNode(value)); }
}
