package org.xar.ck3.control.application.action;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.advance.PreparedCleanupEvidence;
import org.xar.ck3.control.application.advance.PreparedCleanupSuccessorEvidence;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure DATA shape of one retained Life execution with a reserved, absent sixth
 * lifecycle. A caller supplies the complete canonical latest-action list and
 * actual predecessor state under its own source-owned writer/session. This class
 * neither proves WAL completeness nor issues a Root capability, NoDispatch,
 * NoEffect, ACK, Native permission or gameplay/cycle credit. */
public final class ReservedLifeRetirementSubject {
    private ReservedLifeRetirementSubject() { }

    public record Description(ExactRef preparationReference,
            PreparedCleanupSuccessorEvidence.Descriptor preparation,ActionCommand command6,
            ActionReceipt originalParent5,List<ActionReceipt> firstFive) {
        public Description {
            Objects.requireNonNull(preparationReference);Objects.requireNonNull(preparation);Objects.requireNonNull(command6);
            Objects.requireNonNull(originalParent5);firstFive=List.copyOf(firstFive);
        }
    }

    public static Description require(CompositeOperatorQuarantineRequest request,ContinuityState currentState,
            ActionReceipt parent,List<ActionReceipt> completeCanonical,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(request);Objects.requireNonNull(currentState);Objects.requireNonNull(parent);Objects.requireNonNull(archive);
        StrictJson.require(request.reservedTailInterruption(),"reserved Life subject requires its explicit v3 request scope");
        request.requireParent(parent);
        StrictJson.require(currentState.machineId().equals(request.machineId())&&currentState.sequence()==request.expectedHeadSequence()
                &&ContinuityJson.digest(currentState.toJson()).equals(request.expectedHeadDigest()),
                "reserved Life subject changed the exact supplied predecessor state");
        StrictJson.require(parent.sequence()<=currentState.sequence(),"reserved Life original parent is later than its predecessor state");
        requireReceiptReference(parent,request.originalReceipt(),archive);
        var unknown=(ActionState.CompositeUnknown)parent.state();var execution=unknown.execution();
        var canonical=List.copyOf(completeCanonical);var byId=new HashMap<String,ActionReceipt>();
        for(var action:canonical) {
            StrictJson.require(action.sequence()<=currentState.sequence()&&byId.putIfAbsent(action.command().actionId(),action)==null,
                    "complete canonical latest-action DATA contains duplicate identities or a future receipt");
            StrictJson.require(action.equals(parent)||action.settled(),"reserved Life retirement cannot hide another unresolved canonical action");
        }
        StrictJson.require(parent.equals(byId.get(parent.command().actionId())),"reserved Life original parent is absent or changed in canonical DATA");
        var tail=execution.children().get(5);
        StrictJson.require(!byId.containsKey(tail.actionId()),"reserved Life sixth identity already has a canonical lifecycle");
        var preparationReference=unknown.evidence().getLast();
        var prepared=PreparedCleanupSuccessorEvidence.loadDescriptor(preparationReference,archive);
        var originalParent5=originalUnknown(prepared.parentReference(),archive);
        var old=(ActionState.CompositeUnknown)originalParent5.state();var previous=old.execution();
        StrictJson.require(originalParent5.command().equals(parent.command())&&originalParent5.bodySha256().equals(parent.bodySha256())
                &&originalParent5.sequence()<parent.sequence()&&previous.children().size()==5
                &&previous.handlerId().equals(execution.handlerId())&&previous.startedAt().equals(execution.startedAt())
                &&previous.guard().equals(execution.guard())&&previous.children().equals(execution.children().subList(0,5))
                &&old.reason().startsWith(PreparedCleanupEvidence.CURSOR_PREFIX)&&old.evidence().size()>=2
                &&unknown.evidence().subList(0,unknown.evidence().size()-1).equals(old.evidence())
                &&old.evidence().getFirst().equals(prepared.authorizationReference()),
                "reserved Life successor changed its original five-reservation parent, guard or evidence prefix");
        var firstFive=new ArrayList<ActionReceipt>();long sequence=0;
        for(int i=0;i<5;i++) {
            var binding=execution.children().get(i);var child=byId.get(binding.actionId());
            StrictJson.require(child!=null&&child.settled()&&child.bodySha256().equals(binding.bodySha256())
                    &&child.sequence()>sequence&&child.sequence()<parent.sequence(),
                    "reserved Life subject changed a settled canonical original or its exact ordinal/reference");
            requireReceiptReference(child,prepared.childReferences().get(i),archive);
            requireSameOwner(parent.command(),child.command());
            firstFive.add(child);sequence=child.sequence();
        }
        var fourth=firstFive.get(3);var fifth=firstFive.get(4);
        StrictJson.require(fourth.state() instanceof ActionState.CleanupNoEffectConfirmed
                &&((ActionState.CleanupNoEffectConfirmed)fourth.state()).proofReference().equals(prepared.aProofReference())
                &&prepared.aTerminalReference().equals(prepared.childReferences().get(3))
                &&fifth.state() instanceof ActionState.PreparedCleanupNoEffectConfirmed,
                "reserved Life subject changed its canonical C4/C5 terminal DATA roles");
        var c5=(ActionState.PreparedCleanupNoEffectConfirmed)fifth.state();
        StrictJson.require(c5.proofReference().equals(prepared.c5NoEffectProofReference())
                &&prepared.c5TerminalReference().equals(prepared.childReferences().getLast())
                &&c5.originalPreparedState().preparationReference().equals(old.evidence().getLast()),
                "reserved Life subject changed the exact original C5 preparation or proof reference");
        requireSixth(parent,firstFive,prepared,tail);
        return new Description(preparationReference,prepared,prepared.command(),originalParent5,firstFive);
    }

    private static void requireSixth(ActionReceipt parent,List<ActionReceipt> firstFive,
            PreparedCleanupSuccessorEvidence.Descriptor prepared,CompositeExecution.Child tail) {
        var command=prepared.command();var operation=command.operation();var fifth=firstFive.getLast();
        var arguments=new OpportunityJson.Obj(Map.of());
        StrictJson.require(operation.value().startsWith(ClockStatusRead.CANCEL_PREFIX)&&operation.equals(fifth.command().operation())
                &&AdvancePrimitives.supports(operation)&&command.arguments().members().isEmpty(),
                "reserved Life tail is not the original generation-bound CANCEL preparation");
        var expected=new ActionCommand(ActionIds.child(parent.command().actionId(),6,operation),command.before(),
                parent.command().source(),parent.command().sessionId(),operation,arguments,
                AdvancePrimitives.expected(command.before(),parent.command().source(),operation,arguments),
                parent.command().claims(),prepared.deadline());
        StrictJson.require(command.equals(expected)&&command.actionId().equals(tail.actionId())&&ActionCodec.bodySha256(command).equals(tail.bodySha256())
                &&prepared.nativeRequestId().equals(RequestIds.forCommand(command))&&command.deadline().equals(prepared.deadline()),
                "reserved Life tail changed its derived sixth identity, full body, native request or original deadline");
        requireSameOwner(parent.command(),command);var identity=command.before();var prior=fifth.command().before();
        StrictJson.require(identity.frame().identity().dateRaw().equals(prior.frame().identity().dateRaw()),
                "reserved Life sixth preparation changed its retained partial date");
        var requestIds=new HashSet<String>();requestIds.add(RequestIds.forCommand(parent.command()));
        for(var child:firstFive) {
            StrictJson.require(!command.actionId().equals(child.command().actionId())&&!tail.bodySha256().equals(child.bodySha256()),
                    "reserved Life sixth preparation reuses an original action identity or body");
            requestIds.add(RequestIds.forCommand(child.command()));
            ActionTransitions.attempt(child.state()).ifPresent(value->requestIds.add(value.requestId()));
            ActionTransitions.dispatch(child.state()).ifPresent(value->requestIds.add(value.requestId()));
        }
        StrictJson.require(!requestIds.contains(prepared.nativeRequestId()),"reserved Life sixth native request reuses an original request ID");
    }

    private static void requireSameOwner(ActionCommand parent,ActionCommand child) {
        StrictJson.require(child.source().equals(parent.source())&&child.sessionId().equals(parent.sessionId())
                &&child.origin() instanceof CommandOrigin.Gameplay&&child.before().machineId().equals(parent.before().machineId())
                &&child.before().game().equals(parent.before().game())
                &&child.before().frame().episodeRunId().equals(parent.before().frame().episodeRunId())
                &&child.before().frame().identity().player().equals(parent.before().frame().identity().player()),
                "reserved Life original command changed its source, session, Game, episode or player");
    }

    /** Compare an already supplied canonical receipt to bounded exact DATA bytes.
     * Do not call receiptReferenceOf: NativeOutcomeArchive deliberately performs
     * full domain-proof originals replay there, which this descriptor role does not grant. */
    private static void requireReceiptReference(ActionReceipt receipt,ExactRef reference,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(reference.bytes()>0&&reference.bytes()<=ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES,
                "reserved Life bounded exact canonical receipt reference required");
        byte[] bytes=archive.loadMaterial(reference).bytes();
        StrictJson.require(bytes.length==reference.bytes()&&ActionCodec.sha256(bytes).equals(reference.sha256())
                &&Arrays.equals(bytes,ActionReceiptCodec.encodeReceipt(receipt,archive)),
                "reserved Life canonical receipt reference or complete bytes changed");
    }

    /** DATA-only receipt decoding, after rejecting any state which could require
     * receipt/effect loading. The installed source still verifies original authority. */
    private static ActionReceipt originalUnknown(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(reference.bytes()>0&&reference.bytes()<=ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES,
                "reserved Life bounded original five-parent receipt required");
        byte[] bytes=archive.loadMaterial(reference).bytes();
        StrictJson.require(reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),
                "reserved Life original five-parent receipt bytes changed");
        var headers=DriverJson.object(bytes,ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);
        var state=OpportunityJson.object(headers.get("state"),"original parent state");
        StrictJson.require(new OpportunityJson.Text("COMPOSITE_UNKNOWN").equals(state.get("kind")),
                "reserved Life original five-parent must be UNKNOWN DATA");
        var original=ActionReceiptCodec.decodeReceipt(bytes,archive);
        StrictJson.require(original.state() instanceof ActionState.CompositeUnknown
                &&Arrays.equals(bytes,ActionReceiptCodec.encodeReceipt(original,archive)),
                "reserved Life original five-parent canonical receipt differs");
        return original;
    }
}
