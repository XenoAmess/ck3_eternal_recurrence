package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Grant-only control observer. The Root coordinator is the sole dispatcher and claim writer. */
public final class GrantPickerControlEffects {
    public static final String OBSERVER="xar.java.grant-picker-control-post/v1";
    public static final String FIELD="grant.operation_observed";
    public static final String REJECTED="original source-qualified Grant result proves no native invocation";
    public record After(Context context,PlanningReadResult.Known<GrantResult> query) {
        public After { Objects.requireNonNull(context);Objects.requireNonNull(query); }
    }
    @FunctionalInterface public interface AfterQuery { After read(Context before,GrantRequest original); }
    @FunctionalInterface public interface Archive { ActionPorts.OutcomeArchive current(); }
    @FunctionalInterface public interface OriginalPreparation { void require(ActionCommand command,ActionState.Attempt attempt,ActionPorts.OutcomeArchive archive); }
    private final ReadContract<GrantResult> query;
    private final AfterQuery after;
    private final Archive archives;
    private final OriginalPreparation legacy;
    public GrantPickerControlEffects(ReadContract<GrantResult> identical,AfterQuery after,Archive archives,OriginalPreparation legacy) {
        query=Objects.requireNonNull(identical);this.after=Objects.requireNonNull(after);this.archives=Objects.requireNonNull(archives);
        this.legacy=Objects.requireNonNull(legacy);
        need(query.operation().value().equals(GrantTitleCodec.step(GrantOperation.QUERY)),"same installed grant query required");
    }
    public static List<ExpectedValue> expectedValues(){return List.of(new ExpectedBoolean(new FieldKey(FIELD),true));}
    public static Context context(ActionCommand command){return InteractionArguments.context(command);}
    public static GrantRequest request(ActionCommand command) {
        var body=InteractionArguments.parseApp(command.arguments());
        need(body.has("mutation_kind")&&body.get("mutation_kind").isTextual()&&body.get("mutation_kind").textValue().equals("GRANT"),"actual grant mutation body required");
        var value=InteractionArguments.grant(body);
        need(value.operation()!=GrantOperation.QUERY&&command.operation().value().equals(GrantTitleCodec.step(value.operation())),"exact grant logical operation required");
        need(command.expected().observerSchema().equals(OBSERVER)&&command.expected().values().equals(expectedValues()),"grant exact control expectation required");
        return value;
    }
    public NativeRequest prepare(ActionCommand command) {
        var value=request(command);return new NativeRequest(GrantTitleCodec.step(value.operation()),Optional.of(GrantTitleCodec.capability(value.operation())),GrantTitleCodec.request(context(command),value));
    }
    public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()||ack.originalResultToken().isEmpty())
            return NativeEffectRegistry.Projected.pending("original grant dispatch outcome remains unknown; no retry",List.of(attempt.guard().nativeEvidence()));
        Context before=context(command);GrantRequest original=request(command);
        GrantResult nativeResult=GrantTitleCodec.decode(ack.originalResultToken().orElseThrow(),before,original);
        if(knownNoDispatch(nativeResult)) {
            var archive=archives.current();original(command,attempt,dispatch,archive);
            var rejected=new ActionState.Rejected(attempt.requestId(),REJECTED,archive.referenceOf(dispatch));
            ActionEffects.validate(command,attempt,dispatch,rejected);
            return new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(rejected),Optional.empty());
        }
        // A claimed native status is retained separately. Only a separately sampled original query can settle it.
        if(!nativeResult.frameVerified()||nativeResult.dispatched()&&!nativeResult.nativeCompleted())
            return NativeEffectRegistry.Projected.pending("grant native result lacks a complete dispatched frame",List.of(archives.current().referenceOf(dispatch)));
        After actual=after.read(before,original);
        return project(command,attempt,dispatch,actual.query().receipt(),archives.current());
    }
    public NativeEffectRegistry.Projected project(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            PlanningReadReceipt independent,ActionPorts.OutcomeArchive archive) {
        GrantResult submitted=original(command,attempt,dispatch,archive);
        NativeRecordedEvidenceVerifier.requireRead(independent,archive);
        Context before=context(command),current=InteractionArguments.context(independent.request());
        need(current.source().equals(command.source())&&independent.request().before().equals(current.before()),"Grant independent original source/frame differs");
        GrantRequest requested=request(command),observedRequest=InteractionArguments.grant(InteractionArguments.parseApp(independent.request().arguments()));
        need(observedRequest.equals(queryRequest(requested)),"independent grant query changed recipient/ordered targets");
        GrantResult observed=query.replay(independent);
        if(!proves(before,current,requested,submitted,observed))return NativeEffectRegistry.Projected.pending("independent grant state does not prove the original operation",List.of(archive.readReferenceOf(independent)));
        var control=new ActionState.ControlApplied(independent,OBSERVER,expectedValues());
        ActionEffects.validate(command,attempt,dispatch,control);
        return new NativeEffectRegistry.Projected(new ActionPorts.ControlObserved(control),Optional.empty());
    }
    private GrantResult original(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,ActionPorts.OutcomeArchive archive) {
        need(dispatch instanceof NativeActionPort.AckReceived,"grant settlement requires original native ACK");
        var ack=(NativeActionPort.AckReceived)dispatch;
        need(ack.nativeOk()&&ack.originalResultToken().isPresent(),"original successful grant packet required");
        var expected=prepare(command);var prepared=attempt.preparedRequest();
        need(dispatch.requestId().equals(attempt.requestId())&&expected.step().equals(prepared.step())&&expected.requiredCapability().equals(prepared.requiredCapability())&&expected.additionalFields().equals(prepared.additionalFields()),"Grant original prepared request changed");
        legacy.require(command,attempt,archive);
        ack.custody().orElseThrow(()->new IllegalArgumentException("original Grant ACK custody absent")).verify(ack,attempt.guard());
        try {
            var wire=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow(()->new IllegalArgumentException("original Grant outbound absent")).originalPacket());
            need(wire.requestId().equals(attempt.requestId())&&wire.step().equals(command.operation().value())&&wire.expectedRevision().equals(Optional.of(command.before().frame().identity().nativeRevision()))
                    &&wire.expectedSnapshotRevision().isEmpty()&&StrictJson.parse(wire.normalizedAdditionalFields().value()).equals(StrictJson.parse(attempt.preparedRequest().additionalFields().bytes())),"Grant original outbound differs from exact immutable command");
        } catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
        return GrantTitleCodec.decode(ack.originalResultToken().orElseThrow(),context(command),request(command));
    }
    public static boolean knownNoDispatch(GrantResult result){return result.status()==GrantStatus.UNAVAILABLE&&!result.dispatched()&&result.frameVerified()&&result.ownerVerified()&&result.sourcePins()&&!result.transferVerified()&&!result.selectionVerified();}
    public static GrantRequest queryRequest(GrantRequest original){return new GrantRequest(GrantOperation.QUERY,original.recipient(),original.targets(),List.of(),Optional.empty(),Optional.empty());}
    /** Same-before/after holder equality alone can never prove a SEND. */
    public static boolean proves(Context before,Context current,GrantRequest original,GrantResult submitted,GrantResult observed) {
        if(submitted.operation()!=original.operation()||observed.operation()!=GrantOperation.QUERY||!submitted.frameVerified()||submitted.dispatched()&&!submitted.nativeCompleted()
                ||!observed.frameVerified()||!GrantTitleCodec.sameControl(before,current))return false;
        if(original.operation()!=GrantOperation.SEND&&!before.revision().equals(current.revision()))return false;
        return switch(original.operation()) {
            case QUERY->false;
            case PREPARE->submitted.status()==GrantStatus.PREPARED&&observed.after().complete()&&observed.after().visible()&&observed.after().bound();
            case SELECT->{var selected=new HashSet<>(original.expectedSelected());if(original.desiredSelected().orElseThrow())selected.add(original.title().orElseThrow());else selected.remove(original.title().orElseThrow());
                yield submitted.selectionVerified()&&observed.after().complete()&&new HashSet<>(observed.after().selected()).equals(selected);}
            case SEND->submitted.transferVerified()&&submitted.before().complete()&&submitted.before().holders().stream().allMatch(h->h.available()&&Objects.equals(h.holder(),before.actor().longValueExact()))
                    &&GrantTitleCodec.independentHolderTransfer(before,current,original,observed);
        };
    }
    public NativeRecordedEvidenceVerifier.Binding archived(GrantOperation operation,ExactRef source) {
        return new NativeRecordedEvidenceVerifier.Binding(new OperationKey(GrantTitleCodec.step(operation)),source,(head,receipt,archive)->{
            need(receipt.state() instanceof ActionState.Settled,"original grant control settlement absent");
            var settled=(ActionState.Settled)receipt.state();need(request(receipt.command()).operation()==operation,"Grant archived operation differs");
            if(settled.settlement() instanceof ActionState.Rejected rejected){
                need(knownNoDispatch(original(receipt.command(),settled.attempt(),settled.dispatch(),archive))&&rejected.equals(new ActionState.Rejected(settled.attempt().requestId(),REJECTED,archive.referenceOf(settled.dispatch()))),"Grant archived rejection lacks exact original non-invocation proof");
                ActionEffects.validate(receipt.command(),settled.attempt(),settled.dispatch(),rejected);return;
            }
            need(settled.settlement() instanceof ActionState.ControlApplied,"grant archive cannot borrow generic business Applied");
            var control=(ActionState.ControlApplied)settled.settlement();
            need(request(receipt.command()).operation()==operation&&control.supportingReads().isEmpty(),"grant archived operation/supporting reads differ");
            var replayed=project(receipt.command(),settled.attempt(),settled.dispatch(),control.read(),archive);
            need(replayed.result() instanceof ActionPorts.ControlObserved result&&result.observation().equals(control)&&replayed.compatibleResult().isEmpty(),"grant cold replay differs from original ACK/query/contract");
        });
    }
    private static void need(boolean value,String reason){StrictJson.require(value,reason);}
}
