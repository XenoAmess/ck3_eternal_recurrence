package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One public Start producer over the existing native family, canonical writer and original quote. It never dispatches. */
public final class SwaySelectedStart {
    public sealed interface Decision permits NewStart,ExistingStart,Retained { }
    public record NewStart(ActionCommand command) implements Decision {public NewStart {Objects.requireNonNull(command);require(command.operation().value().startsWith(SwayNativeWire.START),"actual native Start required");}}
    public record ExistingStart(String actionId,ExactRef canonicalReceipt) implements Decision {public ExistingStart {SwayNativeWire.action(actionId,false);Objects.requireNonNull(canonicalReceipt);}}
    public record Retained(RawJson result) implements Decision {public Retained {Objects.requireNonNull(result);}}
    @FunctionalInterface public interface RestorationSources {List<ExactRef> require(ContinuityStorePort.Session same,SwayNativeWire.TargetRead current,java.time.Instant deadline)throws IOException;}
    private final SwayCanonicalDomain domain;private final ActionPorts.OutcomeArchive archive;private final PlanningReadPort reads;
    private final SwayActionLifecycle.RegisteredReads definitions;private final SwayRootActions actions;private final RestorationSources restoration;
    public SwaySelectedStart(SwayCanonicalDomain domain,ActionPorts.OutcomeArchive archive,PlanningReadPort reads,SwayActionLifecycle.RegisteredReads definitions,SwayRootActions actions,RestorationSources restoration) {
        this.domain=Objects.requireNonNull(domain);this.archive=Objects.requireNonNull(archive);this.reads=Objects.requireNonNull(reads);this.definitions=Objects.requireNonNull(definitions);this.actions=Objects.requireNonNull(actions);this.restoration=Objects.requireNonNull(restoration);
    }
    public RawJson target(ContinuityStorePort.Session same,Complete current,SwayDriverCodec.TargetRequest request,java.time.Instant deadline)throws IOException {
        require(current.identity().frame().revision().equals(request.expectedRevision()),"public Sway target expected revision is stale");
        var known=target(same,current,request.targetCharacterId(),deadline);var originals=archive.withSession(same);verify(known.receipt(),current,originals);
        return SwayDriverCodec.quote(known.receipt(),known.value(),originals.readReferenceOf(known.receipt()));
    }
    public Decision prepare(ContinuityStorePort.Session same,Complete current,SwayDriverCodec.StartRequest request,java.time.Instant deadline)throws IOException {
        var originals=archive.withSession(same);var quote=verifyQuote(request.readback(),originals);var original=originals.loadRead(request.readback().originalRead());
        var canonical=ContinuityActionJournal.lookup(same.head().state(),request.actionId(),originals);
        if(canonical.isPresent()) {
            var actual=canonical.orElseThrow();requireOriginalCommand(actual,request,originals);
            if(actual.command().before().game().equals(current.identity().game())&&actual.command().sessionId().equals(current.sessionId())&&actual.command().source().equals(current.source()))return new ExistingStart(request.actionId(),originals.receiptReferenceOf(actual));
            return recoverRetained(same,current,request.actionId(),quote,originals,deadline);
        }
        var ledger=domain.load(same).ledger();
        if(ledger.pending().isPresent()) {
            if(ledger.pending().orElseThrow().actionId().equals(request.actionId()))return recoverRetained(same,current,request.actionId(),quote,originals,deadline);
            return retained("pending_recovery","another original pending Start is preserved; no new public action",request.actionId(),List.of(request.readback().originalRead()));
        }
        if(SwayFormalState.historicalPendingUnresolved(ledger))return retained("pending_recovery","historical UNKNOWN remains observation only; no new public action",request.actionId(),List.of(request.readback().originalRead()));
        require(current.identity().equals(original.request().before())&&current.source().equals(original.request().source())&&current.sessionId().equals(original.request().sessionId()),"public Start quote crossed its exact current original frame/source/session");
        require(current.identity().frame().revision().equals(request.readback().expectedRevision()),"public Start quote revision is stale");
        var context=SwayCanonicalDomain.context(current,quote.binding());
        try {SwayFormalState.reduce(ledger,new SwayFormalState.StartIntent(request.actionId(),quote,context,SwayFormalState.StartAdmission.PUBLIC_NATIVE_FINAL));}
        catch(IllegalArgumentException declined){return retained("no_positive_opportunity",declined.getMessage()==null?"original Start reducer declined":declined.getMessage(),request.actionId(),List.of(request.readback().originalRead()));}
        actions.issueStart(quote.target());var args=StrictJson.object();args.put("schema",SwayNativeBindings.PUBLIC_START_ARGUMENTS);args.put("target_character_id",quote.target());args.set("original_target_read",request.readback().originalRead().toJson());
        var expected=new ExpectedPostcondition(1,current.identity(),current.source(),SwayActionLifecycle.START_OBSERVER,List.of(new ExpectedBoolean(new FieldKey("sway.exact_active_observed"),true),new ExpectedText(new FieldKey("sway.action_id"),request.actionId()),new ExpectedInteger(new FieldKey("sway.actor_character_id"),current.identity().frame().identity().player()),new ExpectedInteger(new FieldKey("sway.target_character_id"),BigInteger.valueOf(quote.target()))));
        var claims=new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(BigInteger.valueOf(quote.binding().actor()),BigInteger.valueOf(quote.target())),Set.of("sway-slot"));
        return new NewStart(new ActionCommand(request.actionId(),current.identity(),current.source(),current.sessionId(),new OperationKey(SwayNativeWire.START+quote.target()),OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)),"actual original public Sway Start"),expected,claims,deadline));
    }
    public RawJson receipt(ContinuityStorePort.Session same,Complete current,SwayDriverCodec.ReceiptRequest request,java.time.Instant deadline)throws IOException {
        require(current.identity().frame().revision().equals(request.expectedRevision()),"public Sway receipt expected revision is stale");var originals=archive.withSession(same);
        var canonical=ContinuityActionJournal.lookup(same.head().state(),request.actionId(),originals).orElseThrow(()->new IOException("public receipt requires its actual original canonical Start"));
        var command=canonical.command();require(command.operation().value().equals(SwayNativeWire.START+request.targetCharacterId()),"public receipt target differs from canonical original Start");
        require(command.before().game().equals(current.identity().game())&&command.source().equals(current.source())&&command.sessionId().equals(current.sessionId()),"cold receipt cannot query a replacement Game using the old native mailbox; use retained Start recovery");
        var fields=SwayNativeBindings.args(command.arguments(),Set.of("schema","target_character_id","original_target_read"));SwayNativeBindings.startAdmission(fields);var origin=originals.loadRead(ExactRef.fromJson(fields.get("original_target_read")));NativeRecordedEvidenceVerifier.requireRead(origin,originals);
        var quote=SwayNativeWire.target(origin.original().originalFrame().bytes(),origin.requestId(),SwayNativeBindings.bind(origin,new OperationKey(SwayNativeWire.TARGET+request.targetCharacterId())),request.targetCharacterId());
        var ack=SwayDriverCodec.ack(canonical,quote).orElseThrow(()->new IOException("public receipt pre_capture_epoch lacks its original native Start ACK; UNKNOWN remains retained"));
        require(ack.preCaptureEpoch().equals(request.preCaptureEpoch()),"public receipt pre_capture_epoch differs from its actual original Start ACK");
        var contract=definitions.receipt(request.targetCharacterId(),request.actionId(),request.preCaptureEpoch());var args=StrictJson.object();args.put("action_id",request.actionId());
        var result=reads.read(same,contract,new PlanningReadRequest(current.identity(),current.source(),current.sessionId(),contract.operation(),arguments(args),deadline));
        if(!(result instanceof PlanningReadResult.Known<SwayNativeWire.AppliedReceipt> known))throw new IOException("actual original public Sway receipt unavailable");
        verify(known.receipt(),current,originals);return SwayDriverCodec.receipt(known.receipt(),known.value(),originals.readReferenceOf(known.receipt()));
    }
    private Retained recoverRetained(ContinuityStorePort.Session same,Complete current,String actionId,SwayNativeWire.TargetRead original,ActionPorts.OutcomeArchive originals,java.time.Instant deadline)throws IOException {
        var ledger=domain.load(same).ledger();var pending=ledger.pending();
        if(pending.isEmpty()||!pending.orElseThrow().actionId().equals(actionId))return retained("retained_original","original action belongs to another physical Game; no old command or native mailbox is replayed",actionId,List.of());
        require(pending.orElseThrow().original().equals(original),"retained caller Start differs from its durable original quote");
        require(original.binding().before().machineId().equals(current.identity().machineId())&&original.binding().before().frame().episodeRunId().equals(current.identity().frame().episodeRunId())&&original.binding().actor()==current.identity().frame().identity().player().longValueExact(),"cold public recovery changed original actor/episode");
        var known=target(same,current,original.target(),deadline);verify(known.receipt(),current,originals);var ref=originals.readReferenceOf(known.receipt());
        try {
            var retainedSources=original.binding().before().game().equals(current.identity().game())?List.<ExactRef>of():restoration.require(same,known.value(),deadline);
            domain.commit(same,new SwayFormalState.Recovered(known.value()),new SwayTransitionCodec.Proofs(List.of(ref),Optional.empty(),Optional.empty(),retainedSources));
            return retained("original_instance_observed","actual source-bound original instance observed; canonical action history remains unchanged and an old UNKNOWN is never resubmitted",actionId,List.of(ref));
        }catch(IOException|IllegalArgumentException unavailable){return retained("pending_recovery",unavailable.getMessage()==null?"actual source-bound restoration unavailable":unavailable.getMessage(),actionId,List.of(ref));}
    }
    public static SwayNativeWire.TargetRead verifyQuote(SwayDriverCodec.Quote quote,ActionPorts.OutcomeArchive originals) {
        var read=originals.loadRead(quote.originalRead());require(originals.readReferenceOf(read).equals(quote.originalRead()),"public quote original ref differs");NativeRecordedEvidenceVerifier.requireRead(read,originals);
        var value=SwayNativeWire.target(read.original().originalFrame().bytes(),read.requestId(),SwayNativeBindings.bind(read,new OperationKey(SwayNativeWire.TARGET+quote.targetCharacterId())),quote.targetCharacterId());
        require(read.request().before().frame().revision().equals(quote.expectedRevision())&&SwayDriverCodec.quote(read,value,quote.originalRead()).equals(quote.presentation()),"public readback differs from its actual whole guarded archived target producer");return value;
    }
    public static void requireOriginalCommand(ActionReceipt actual,SwayDriverCodec.StartRequest request,ActionPorts.OutcomeArchive originals) {
        var command=actual.command();require(command.actionId().equals(request.actionId())&&command.operation().value().equals(SwayNativeWire.START+request.readback().targetCharacterId())&&ActionCodec.bodySha256(command).equals(actual.bodySha256()),"caller Start ID collides with another canonical operation/body");
        var fields=SwayNativeBindings.args(command.arguments(),Set.of("schema","target_character_id","original_target_read"));SwayNativeWire.equals(fields,"schema",SwayNativeBindings.PUBLIC_START_ARGUMENTS);
        require(ExactRef.fromJson(fields.get("original_target_read")).equals(request.readback().originalRead()),"caller Start ID was already bound to a different original quote");
        var origin=originals.loadRead(request.readback().originalRead());require(command.before().equals(origin.request().before())&&command.source().equals(origin.request().source())&&command.sessionId().equals(origin.request().sessionId()),"canonical Start crossed its actual original quote owner");
    }
    private PlanningReadResult.Known<SwayNativeWire.TargetRead> target(ContinuityStorePort.Session same,Complete current,long target,java.time.Instant deadline)throws IOException {
        var contract=definitions.target(target);var args=StrictJson.object();args.put("target_character_id",target);
        var result=reads.read(same,contract,new PlanningReadRequest(current.identity(),current.source(),current.sessionId(),contract.operation(),arguments(args),deadline));
        if(result instanceof PlanningReadResult.Known<SwayNativeWire.TargetRead> known)return known;throw new IOException("actual public Sway target unavailable");
    }
    private static void verify(PlanningReadReceipt read,Complete current,ActionPorts.OutcomeArchive originals) {
        NativeRecordedEvidenceVerifier.requireRead(read,originals);require(read.request().before().equals(current.identity())&&read.request().source().equals(current.source())&&read.request().sessionId().equals(current.sessionId()),"public Sway read crossed its actual current frame/source/session");
    }
    private static OpportunityJson.Obj arguments(com.fasterxml.jackson.databind.node.ObjectNode row){return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)),"actual public Sway native arguments");}
    private static Retained retained(String status,String detail,String actionId,List<ExactRef> evidence){return new Retained(SwayDriverCodec.retained(status,detail,actionId,evidence));}
}
