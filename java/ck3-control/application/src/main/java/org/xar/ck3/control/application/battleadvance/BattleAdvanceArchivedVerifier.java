package org.xar.ck3.control.application.battleadvance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceClock;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Re-derives tactical settlement from original archive bodies under the one writer lock. No native reads. */
public final class BattleAdvanceArchivedVerifier implements NativeRecordedEvidenceVerifier.ArchivedVerifier {
    /** Root must install its actual full Driver/semantic decoder. An envelope is not a complete frame. */
    private final NativeEffectEvidence.FrameLoader frames;
    private final BattleAdvancePlan.Configuration configuration;
    public BattleAdvanceArchivedVerifier(NativeEffectEvidence.FrameLoader frames, BattleAdvancePlan.Configuration configuration) {
        this.frames = Objects.requireNonNull(frames); this.configuration = Objects.requireNonNull(configuration);
    }
    public NativeRecordedEvidenceVerifier.Binding binding(OperationKey exactOperation, ExactRef actualDefinition) {
        require(BattleAdvanceStep.parse(exactOperation.value()).isPresent(), "archived battle verifier needs one exact supported operation");
        return new NativeRecordedEvidenceVerifier.Binding(exactOperation, actualDefinition, this);
    }
    @Override public void verify(WriterContracts.Head actualLockedHead, ActionReceipt proposed, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(actualLockedHead); Objects.requireNonNull(archive);
        require(proposed.state() instanceof ActionState.CompositeSettled, "battle archive proof requires a settled composite parent");
        var settled = (ActionState.CompositeSettled) proposed.state();
        ActionState.EffectObservation semantic;
        if (settled.settlement() instanceof ActionState.Applied applied) semantic = applied.observation();
        else {
            require(settled.settlement() instanceof ActionState.CompositeControlApplied, "battle settlement kind unavailable");
            semantic = ((ActionState.CompositeControlApplied) settled.settlement()).observation().semantic();
        }
        require(semantic.supportingEvidence().size() == 1, "one complete original battle basis is required");
        ExactRef basis = semantic.supportingEvidence().getFirst();
        RawJson material = archive.loadMaterial(basis); exact(basis, material.bytes());
        JsonNode node = StrictJson.parse(material.bytes());
        require(node.isObject() && "xar.ck3.battle-archived-basis/v2".equals(StrictJson.text(node.get("archived_basis_schema"))),
                "historical projection lacks the full archived battle basis");
        ActionCommand parent = proposed.command();
        require(StrictJson.text(node.get("parent_action_id")).equals(parent.actionId())
                && StrictJson.text(node.get("parent_body_sha256")).equals(proposed.bodySha256())
                && proposed.bodySha256().equals(ActionCodec.bodySha256(parent)), "archived battle parent body drift");
        var decoded = BattleAdvanceResultCodec.decode(material, BattleAdvanceResultCodec.Profile.JAVA_V1);
        BattleAdvancePlan plan = BattleAdvancePlan.decode(parent);
        require(decoded.plan().equals(Optional.of(plan)), "archived tactical plan differs from original intent");
        Frame starting = frame(reference(node.get("starting_frame_evidence")), reference(node.get("starting_driver_facts")), ObservationProvenanceCodec.decode(node.get("starting_provenance")), archive);
        Frame ending = frame(reference(node.get("ending_frame_evidence")), reference(node.get("ending_driver_facts")), ObservationProvenanceCodec.decode(node.get("ending_provenance")), archive);
        var before = BattleAdvanceFrame.decode(starting); var after = BattleAdvanceFrame.decode(ending);
        BattleAdvanceFrame.bind(parent, before, true); BattleAdvanceFrame.bind(parent, after, false);
        var step = BattleAdvanceStep.parse(parent.operation().value()).orElseThrow();
        require(plan.equals(BattleAdvancePlan.create(step, before, configuration)), "archived complete starting facts no longer derive the same plan");
        require(after.paused() && after.mapReady() && before.owner().same(after.owner(), false, false)
                && after.nativeRevision().compareTo(before.nativeRevision()) >= 0, "archived actual ending ownership/paused frame differs");
        long delta = (long) after.owner().dateRaw() - before.owner().dateRaw();
        require(delta >= 0 && delta % 24 == 0 && after.owner().dateRaw() <= plan.targetDateRaw(), "archived tactical date delta invalid");
        var boundary = BattleAdvanceFrame.boundary(before, after);
        require(boundary.isEmpty() || boundary.orElseThrow().kind() == BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED
                || BattleAdvanceFrame.isNew(before, after), "archived decision is not a new original-frame boundary");
        var recordedBoundary = BattleAdvanceResultCodec.decodeBoundary(decoded);
        require(boundary.isPresent() == recordedBoundary.isPresent()
                && (boundary.isEmpty() || boundary.orElseThrow().same(recordedBoundary.orElseThrow())), "archived boundary differs from original complete frames");
        List<ActionReceipt> children = children(node, settled.execution(), archive);
        ActionReceipt armChild = only(children, plan.armStep());
        Status arm = decoded.armed().orElseThrow(), stop = decoded.sentinel().orElseThrow();
        BattleSentinelValidation.arm(arm, plan.startingDateRaw(), plan.targetDateRaw(), plan.speed(), plan.mode(), plan.watchArmyIds(), plan.scope());
        NativeRecordedEvidenceVerifier.requireRead(control(armChild).read(), archive);
        require(arm.equals(AdvancePrimitives.acknowledgedSentinel(armChild.ack().orElseThrow(), plan.armStep()))
                && arm.equals(ClockStatusRead.decode(control(armChild).read().original())), "original arm ACK and independent Status do not bind the same slot");
        PlanningReadReceipt terminal = archive.loadRead(reference(node.get("terminal_status_read")));
        new BattleAdvanceArchivedReplay(frames).verify(parent, plan, starting, ending,
                new ClockStatusRead.Observation(ClockStatusRead.decode(terminal.original()), terminal, archive.referenceOf(terminal.original())), children, archive);
        NativeRecordedEvidenceVerifier.requireRead(terminal, archive);
        require(terminal.contractId().equals(ClockStatusRead.CONTRACT_ID) && terminal.request().operation().value().equals(ClockStatusRead.STEP)
                && terminal.request().source().equals(parent.source()) && terminal.request().sessionId().equals(parent.sessionId())
                && terminal.after().binding().observed().game().equals(parent.before().game())
                && ClockStatusRead.decode(terminal.original()).equals(stop), "archived final independent Status changed source or content");
        ExactRef statusOriginal = archive.referenceOf(terminal.original());
        JsonNode queries = node.get("status_query_evidence");
        require(queries != null && queries.isArray() && containsReference(queries, statusOriginal),
                "actual terminal query packet absent from archived basis");
        boolean canceled = node.get("player_decision_boundary_cancel") != null && !node.get("player_decision_boundary_cancel").isNull();
        if (boundary.isPresent()) BattleSentinelValidation.decision(stop, arm, plan.startingDateRaw(), plan.targetDateRaw(), after.owner().dateRaw(),
                plan.speed(), plan.mode(), plan.watchArmyIds(), boundary.orElseThrow(), canceled);
        else BattleSentinelValidation.stop(stop, arm, plan.startingDateRaw(), plan.targetDateRaw(), after.owner().dateRaw(), plan.speed(), plan.mode(), plan.watchArmyIds());
        long resumes = children.stream().filter(value -> value.command().operation().value().equals("resume-map")).count();
        require(resumes <= 1 && (resumes == 1 || canceled && delta == 0 && boundary.isPresent()), "archived tranche has no legal original resume/interruption sequence");
        if (canceled) {
            var cancel = control(only(children, ClockStatusRead.CANCEL_PREFIX + arm.generation().decimal()));
            NativeRecordedEvidenceVerifier.requireRead(cancel.read(), archive);
            require(ClockStatusRead.decode(cancel.read().original()).equals(stop), "original cancel child was not independently confirmed");
        }
        boolean controlOnly = canceled && delta == 0 && resumes == 0;
        require(semantic.after().equals(ending.identity()) && semantic.source().equals(ending.source()) && semantic.sessionId().equals(ending.sessionId())
                && semantic.provenance().equals(ending.provenance()) && semantic.observedAt().equals(ending.observedAt())
                && semantic.originalEvidence().equals(ending.originalEvidence()) && semantic.observerSchema().equals(BattleAdvancePlan.OBSERVER)
                && semantic.actual().equals(BattleAdvanceComposite.actualValues(plan, Math.toIntExact(delta / 24), boundary.isEmpty(), controlOnly)),
                "archived complete native frames do not re-derive the proposed semantic settlement");
        if (settled.settlement() instanceof ActionState.CompositeControlApplied control) {
            require(controlOnly && after.nativeRevision().equals(before.nativeRevision()), "same-revision control settlement differs from actual arm-to-cancel path");
            var observation = new ClockStatusRead.Observation(stop, terminal, statusOriginal);
            require(AdvanceClock.compositeControlTerminal(parent, observation, children, semantic).equals(control.observation()),
                    "archived cancellation/read/semantic chain differs from proposed control settlement");
        }
    }
    private Frame frame(ExactRef reference, ExactRef driverFacts, ObservationProvenance retained, ActionPorts.OutcomeArchive archive) {
        exact(reference, archive.loadNativeFrame(reference));
        exact(driverFacts, archive.loadFullMaterial(driverFacts).bytes());
        var complete = Objects.requireNonNull(frames.load(new NativeEffectEvidence.FrameBasis(reference, driverFacts), archive));
        var actual = new ObservationProvenance.Push(complete.identity().frame().snapshotId(), complete.identity().frame().identity().nativeRevision(), complete.originalEvidence());
        require(actual.equals(retained), "tactical frame provenance differs from the actual native push");
        Frame frame = new Frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic(), actual, complete.observedAt(), complete.originalEvidence());
        require(frame.originalEvidence().equals(reference), "full Driver frame decoder changed original native evidence identity"); return frame;
    }
    private static List<ActionReceipt> children(JsonNode node, CompositeExecution execution, ActionPorts.OutcomeArchive archive) {
        JsonNode rows = node.get("actions"); require(rows != null && rows.isArray() && rows.size() == execution.children().size(), "complete retained child list required");
        List<ActionReceipt> result = new ArrayList<>();
        for (int index = 0; index < rows.size(); index++) {
            JsonNode row = rows.get(index); ActionReceipt child = archive.loadReceipt(reference(row.get("receipt_evidence")));
            var retained = execution.children().get(index);
            require(child.settled() && (child.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                    || child.command().operation().value().equals("pause-map")
                    && child.state() instanceof ActionState.Settled pause && pause.settlement() instanceof ActionState.PauseConfirmed)
                    && child.command().actionId().equals(retained.actionId()) && child.bodySha256().equals(retained.bodySha256())
                    && child.command().actionId().equals(StrictJson.text(row.get("action_id")))
                    && child.bodySha256().equals(StrictJson.text(row.get("body_sha256")))
                    && child.command().operation().value().equals(StrictJson.text(row.get("step")))
                    && child.sequence() == StrictJson.integer(row.get("ledger_sequence"), 1, Long.MAX_VALUE), "archived child is unresolved, omitted or changed");
            result.add(child);
        }
        return List.copyOf(result);
    }
    private static ActionReceipt only(List<ActionReceipt> children, String step) {
        List<ActionReceipt> matches = children.stream().filter(value -> value.command().operation().value().equals(step)).toList();
        require(matches.size() == 1, "exactly one original confirmed child required: " + step); return matches.getFirst();
    }
    private static ActionState.ControlApplied control(ActionReceipt child) {
        require(child.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied,
                "native sentinel control child lacks independent Status settlement");
        return (ActionState.ControlApplied) ((ActionState.Settled) child.state()).settlement();
    }
    private static boolean containsReference(JsonNode rows, ExactRef expected) {
        for (JsonNode row : rows) if (reference(row).equals(expected)) return true; return false;
    }
    private static ExactRef reference(JsonNode node) {
        require(node != null && node.isObject(), "explicit archived reference object required");
        return new ExactRef(StrictJson.text(node.get("path")), StrictJson.integer(node.get("bytes"), 1, Long.MAX_VALUE), StrictJson.text(node.get("sha256")));
    }
    private static void exact(ExactRef expected, byte[] bytes) {
        require(expected.bytes() == bytes.length, "archived original byte length changed");
        try { require(java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)).equals(expected.sha256()), "archived original SHA-256 changed"); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
