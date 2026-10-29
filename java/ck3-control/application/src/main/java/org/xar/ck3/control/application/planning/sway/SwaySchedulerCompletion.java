package org.xar.ck3.control.application.planning.sway;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Immutable recorded DATA. Only SwayCanonicalDomain's same-writer replay qualifies completion. */
public record SwaySchedulerCompletion(String parentActionId, String bodySha256, ExactRef originalRun,
        SwayCanonicalDomain.PublicationWitness witness, NativeEffectEvidence.FrameBasis finalFrame,
        List<ExactRef> finalReads, List<ExactRef> childReceiptRefs, Optional<ActionCommand> exactContinuation,
        Optional<FullPlanOriginals> fullPlanOriginals, Continuation continuation, Business business) {
    public enum Continuation { NOT_NEEDED, FRESH_FULL_PLAN_REQUIRED }
    public record FullPlanOriginals(ExactRef request, ExactRef result) { public FullPlanOriginals { Objects.requireNonNull(request); Objects.requireNonNull(result); StrictJson.require(!request.equals(result), "fullplan request and selected result are separate originals"); } }
    public sealed interface Business permits NoNewBusiness, NewStartConfirmed { }
    public record NoNewBusiness() implements Business { }
    public record NewStartConfirmed(String childActionId, String childBodySha256) implements Business {
        public NewStartConfirmed { StrictJson.text(childActionId); digest(childBodySha256); }
    }
    public SwaySchedulerCompletion {
        StrictJson.text(parentActionId); digest(bodySha256); Objects.requireNonNull(originalRun); Objects.requireNonNull(witness); Objects.requireNonNull(finalFrame);
        finalReads = List.copyOf(finalReads); childReceiptRefs = List.copyOf(childReceiptRefs); Objects.requireNonNull(exactContinuation); Objects.requireNonNull(fullPlanOriginals); Objects.requireNonNull(continuation); Objects.requireNonNull(business);
        StrictJson.require(!finalReads.isEmpty() && finalReads.size() <= 4 && finalReads.stream().distinct().count() == finalReads.size(), "actual finite independent final reads required");
        StrictJson.require(childReceiptRefs.size() <= 1 && childReceiptRefs.stream().distinct().count() == childReceiptRefs.size(), "ordinary Sway has at most one original Start child");
        exactContinuation.ifPresent(value -> StrictJson.require(!value.actionId().equals(parentActionId) && !value.operation().equals(OrdinarySwayPolicy.OPERATION), "continuation must be the fresh full planner's independent command"));
        StrictJson.require(exactContinuation.isEmpty() || fullPlanOriginals.isPresent(), "selected continuation requires the real fullplan request/result originals");
        StrictJson.require(continuation == Continuation.FRESH_FULL_PLAN_REQUIRED || exactContinuation.isEmpty() && fullPlanOriginals.isEmpty(), "a Started Sway parent has no ordinary fallback selection");
    }
    public void validateParent(ActionCommand parent) {
        StrictJson.require(parent.operation().equals(OrdinarySwayPolicy.OPERATION) && parent.actionId().equals(parentActionId) && ActionCodec.bodySha256(parent).equals(bodySha256), "Sway scheduler proof crossed original parent/body");
        exactContinuation.ifPresent(value -> StrictJson.require(value.before().machineId().equals(parent.before().machineId()) && value.before().game().equals(parent.before().game()) && value.before().frame().episodeRunId().equals(parent.before().frame().episodeRunId()) && value.before().frame().identity().player().equals(parent.before().frame().identity().player()) && value.source().equals(parent.source()) && value.sessionId().equals(parent.sessionId()), "fresh fullplan continuation crossed original parent scope"));
    }
    public Optional<NewStartConfirmed> newlyAppliedBusiness() { return business instanceof NewStartConfirmed value ? Optional.of(value) : Optional.empty(); }
    public List<ExactRef> originalEvidence() {
        var refs = new ArrayList<ExactRef>(List.of(originalRun, witness.event(), witness.predecessor().payload(), witness.result().payload(), witness.producerInput(), finalFrame.nativeFrame(), finalFrame.driverFacts())); refs.addAll(finalReads); refs.addAll(childReceiptRefs); fullPlanOriginals.ifPresent(value -> { refs.add(value.request()); refs.add(value.result()); }); return refs.stream().distinct().toList();
    }
    public byte[] encode() { return SwaySchedulerCompletionCodec.encode(this); }
    @Override public boolean equals(Object other) { return other instanceof SwaySchedulerCompletion value && java.util.Arrays.equals(encode(), value.encode()); }
    @Override public int hashCode() { return java.util.Arrays.hashCode(encode()); }
    private static void digest(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "exact SHA256 required"); }
}
