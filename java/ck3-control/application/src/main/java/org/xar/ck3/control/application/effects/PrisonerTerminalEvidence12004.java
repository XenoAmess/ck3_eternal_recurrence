package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.prisoners.PrisonerActionBinding12004;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerMaterial12004;

/** Actual negative-terminal originals. The shared terminal model supplies no success, payment or replay credit. */
public final class PrisonerTerminalEvidence12004 {
    public static final String SCHEMA = "xar.java.prisoner-terminal-originals/v1";
    private PrisonerTerminalEvidence12004() { }
    public record Originals(NativeEffectSnapshots.Pair frames, PlanningReadReceipt selected,
            PlanningReadReceipt after, NativeActionPort.DispatchOutcome dispatch, RawJson compatible, ExactRef basis) {
        public Originals { Objects.requireNonNull(frames); Objects.requireNonNull(selected); Objects.requireNonNull(after);
            Objects.requireNonNull(dispatch); Objects.requireNonNull(compatible); Objects.requireNonNull(basis); }
    }
    public static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch, NativeEffectSnapshots.Pair pair,
            PlanningReadReceipt selected, PlanningReadReceipt afterRead, PrisonerMaterial12004.Custody custody,
            RawJson compatible, ActionPorts.OutcomeArchive archive, Optional<ExactRef> replayBasis) {
        Objects.requireNonNull(replayBasis); BigInteger target = BigInteger.valueOf(custody.frame().target());
        ActionTerminalObservation.Disposition disposition;
        if (custody instanceof PrisonerMaterial12004.HeldByOther transferred)
            disposition = new ActionTerminalObservation.PrisonerTransferred(target, BigInteger.valueOf(transferred.jailer()));
        else { StrictJson.require(custody instanceof PrisonerMaterial12004.Dead, "only observed transfer/death is a negative terminal");
            disposition = new ActionTerminalObservation.PrisonerTargetDead(target); }
        ExactRef dispatchRef = archive.referenceOf(dispatch);
        StrictJson.require(dispatch.equals(archive.load(dispatchRef)), "original prisoner submission archive differs");
        NativeRecordedEvidenceVerifier.requireRead(selected, archive); NativeRecordedEvidenceVerifier.requireRead(afterRead, archive);
        StrictJson.require(PrisonerActionBinding12004.selectedFrameMatches(command,selected)
                &&selected.request().source().equals(command.source())&&selected.request().sessionId().equals(command.sessionId()),
                "terminal selected collection crossed original native identity/source/session");
        ExactRef basis = replayBasis.orElseGet(() -> preserve(command, attempt, pair, selected, afterRead, dispatchRef, compatible, archive));
        var after = pair.after();
        var terminal = new ActionTerminalObservation(ActionCodec.bodySha256(command), attempt.requestId(), disposition,
                command.before(), after.identity(), command.source(), command.sessionId(), new ObservationProvenance.Query(afterRead.requestId()),
                after.observedAt(), after.originalEvidence(), dispatchRef, selected, afterRead, List.of(basis));
        ActionEffects.validate(command, attempt, dispatch, new ActionState.NonAppliedTerminal(terminal));
        return new NativeEffectRegistry.Projected(new ActionPorts.TerminalObserved(terminal), Optional.of(compatible));
    }
    private static ExactRef preserve(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            PlanningReadReceipt selected, PlanningReadReceipt after, ExactRef submission, RawJson compatible, ActionPorts.OutcomeArchive archive) {
        NativeEffectEvidence.FrameBasis beforeFrame = NativeEffectEvidence.basis(pair.before()), afterFrame = NativeEffectEvidence.basis(pair.after());
        for (var frame : List.of(beforeFrame, afterFrame)) {
            exact(frame.nativeFrame(), archive.loadNativeFrame(frame.nativeFrame())); exact(frame.driverFacts(), archive.loadMaterial(frame.driverFacts()).bytes());
        }
        ExactRef material = archive.preserveMaterial(compatible); exact(material, archive.loadMaterial(material).bytes());
        ObjectNode body = StrictJson.object().put("schema", SCHEMA).put("command_body_sha256", ActionCodec.bodySha256(command)).put("attempt_request_id", attempt.requestId());
        body.set("before", frame(beforeFrame)); body.set("after", frame(afterFrame)); body.set("selected_read", archive.readReferenceOf(selected).toJson());
        body.set("after_read", archive.readReferenceOf(after).toJson()); body.set("original_submission", submission.toJson()); body.set("compatible_material", material.toJson());
        RawJson original = new RawJson(StrictJson.canonical(body)); ExactRef reference = archive.preserveMaterial(original);
        exact(reference, archive.loadMaterial(reference).bytes()); return reference;
    }
    public static Originals load(ActionReceipt receipt, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames) {
        StrictJson.require(receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.NonAppliedTerminal,
                "canonical prisoner non-success settlement required");
        var settled = (ActionState.Settled) receipt.state(); var terminal = ((ActionState.NonAppliedTerminal) settled.settlement()).observation();
        ActionEffects.validate(receipt.command(), settled.attempt(), settled.dispatch(), settled.settlement());
        StrictJson.require(terminal.supportingEvidence().size() == 1, "one exact terminal original basis required");
        ExactRef basis = terminal.supportingEvidence().getFirst(); RawJson raw = archive.loadMaterial(basis); exact(basis, raw.bytes());
        ObjectNode body = StrictJson.object(StrictJson.parse(raw.bytes()), Set.of("schema", "command_body_sha256", "attempt_request_id", "before", "after",
                "selected_read", "after_read", "original_submission", "compatible_material"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(body.get("schema"))) && receipt.bodySha256().equals(StrictJson.text(body.get("command_body_sha256")))
                && settled.attempt().requestId().equals(StrictJson.text(body.get("attempt_request_id"))), "terminal basis crossed original command/attempt");
        var before = frames.load(frame(body.get("before")), archive); var after = frames.load(frame(body.get("after")), archive);
        StrictJson.require(before.identity().equals(receipt.command().before()) && before.source().equals(receipt.command().source())
                && before.sessionId().equals(receipt.command().sessionId()) && before.originalEvidence().equals(settled.attempt().guard().nativeEvidence()), "terminal original before frame differs");
        StrictJson.require(after.identity().equals(terminal.after()) && after.source().equals(terminal.source()) && after.sessionId().equals(terminal.sessionId())
                && after.originalEvidence().equals(terminal.originalEvidence()) && after.observedAt().equals(terminal.observedAt()), "terminal actual after frame differs");
        PlanningReadReceipt selected = archive.loadRead(ExactRef.fromJson(body.get("selected_read"))), afterRead = archive.loadRead(ExactRef.fromJson(body.get("after_read")));
        NativeRecordedEvidenceVerifier.requireRead(selected, archive); NativeRecordedEvidenceVerifier.requireRead(afterRead, archive);
        StrictJson.require(selected.equals(terminal.selectedCollection()) && afterRead.equals(terminal.afterCollection()), "terminal read originals differ");
        ExactRef dispatchRef = ExactRef.fromJson(body.get("original_submission")); var dispatch = archive.load(dispatchRef);
        StrictJson.require(dispatchRef.equals(terminal.originalSubmission()) && archive.referenceOf(dispatch).equals(dispatchRef)
                && dispatch.equals(settled.dispatch()), "terminal native submission differs from canonical original");
        ExactRef material = ExactRef.fromJson(body.get("compatible_material")); RawJson compatible = archive.loadMaterial(material); exact(material, compatible.bytes());
        return new Originals(new NativeEffectSnapshots.Pair(before, after), selected, afterRead, dispatch, compatible, basis);
    }
    public static void requireSame(ActionState.NonAppliedTerminal original, NativeEffectRegistry.Projected replayed,
            RawJson compatible, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(replayed.result() instanceof ActionPorts.TerminalObserved, "archive replay did not observe negative terminal disposition");
        var observed = ((ActionPorts.TerminalObserved) replayed.result()).observation();
        StrictJson.require(java.util.Arrays.equals(StrictJson.canonical(ActionTerminalCodec.encode(original.observation(), archive::readReferenceOf)),
                StrictJson.canonical(ActionTerminalCodec.encode(observed, archive::readReferenceOf))) && replayed.compatibleResult().equals(Optional.of(compatible)),
                "terminal original replay or non-success history changed");
    }
    private static ObjectNode frame(NativeEffectEvidence.FrameBasis frame) { ObjectNode body = StrictJson.object(); body.set("native_frame", frame.nativeFrame().toJson()); body.set("driver_facts", frame.driverFacts().toJson()); return body; }
    private static NativeEffectEvidence.FrameBasis frame(JsonNode raw) { var body = StrictJson.object(raw, Set.of("native_frame", "driver_facts")); return new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(body.get("native_frame")), ExactRef.fromJson(body.get("driver_facts"))); }
    private static void exact(ExactRef reference, byte[] raw) { StrictJson.require(reference.bytes() == raw.length && reference.sha256().equals(ActionCodec.sha256(raw)), "terminal original bytes/SHA changed"); }
}
