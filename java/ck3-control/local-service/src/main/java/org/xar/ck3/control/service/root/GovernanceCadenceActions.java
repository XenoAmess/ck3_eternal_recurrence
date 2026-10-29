package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.planning.optionalcadence.*;

/** Canonical applied actions use the existing cadence action reducer under the same OPTIONAL_CADENCE registration. */
public final class GovernanceCadenceActions {
    public static final String INPUT="xar.java-governance-cadence-action/v1";
    private record Input(ExactRef previous,ExactRef receipt,CadenceModels.Domain domain) { }
    private final List<ExactRef> producers;private RootApplicationAssembly.Core core;private RootRuntimeContext context;private RootGovernanceDomains civicDomains;
    public GovernanceCadenceActions(List<ExactRef> producers){this.producers=List.copyOf(producers);}
    public void bindCore(RootApplicationAssembly.Core original){StrictJson.require(core==null,"cadence action source binds one Core");core=Objects.requireNonNull(original);}
    public void installContext(RootRuntimeContext actual){StrictJson.require(actual.core()==core,"cadence action source cannot change writers");context=actual;civicDomains=null;}
    public void bindCivicDomains(RootGovernanceDomains actual){StrictJson.require(civicDomains==null,"actual Council/Crown holder binds once per Game installation");civicDomains=Objects.requireNonNull(actual);}
    @FunctionalInterface public interface Publisher { Optional<WriterContracts.Receipt> publish(ContinuityStorePort.Session same,ActionReceipt actual)throws IOException; }
    public OrdinaryPlanCompletion lifestyleCompletion(){return new OrdinaryPlanCompletion(){
        @Override public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned){
            try{
                var same=core.writer().borrowedSession();core.writer().requireSession(same);
                var latest=core.journal().locked(same,locked->locked.snapshot().actions().stream().filter(receipt->lifestyle(receipt.command().operation())
                        &&receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&receipt.command().before().game().equals(request.before().game())
                        &&receipt.command().source().equals(request.source())&&receipt.command().sessionId().equals(request.sessionId())
                        &&receipt.command().before().frame().episodeRunId().equals(request.before().frame().episodeRunId()))
                        .max(java.util.Comparator.comparingLong(ActionReceipt::sequence)));
                if(latest.isEmpty())return new Unchanged("no canonical current-Game Lifestyle action to reconcile");
                var head=same.head();var changed=publish(same,latest.orElseThrow());return changed.<PlanningDisposition>map(value->new Published(head,value)).orElseGet(()->new Unchanged("latest actual Lifestyle action already consumed by cadence"));
            }catch(IOException|java.io.UncheckedIOException|IllegalArgumentException|IllegalStateException failure){return new Blocked("actual Lifestyle cadence recovery unavailable: "+failure.getMessage(),List.of());}
        }
        @Override public ExecutionDisposition afterExecution(ActionReceipt actual){
            if(!lifestyle(actual.command().operation())||actual.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)return new Unchanged("not a material applied Lifestyle action");
            try{var same=core.writer().borrowedSession();core.writer().requireSession(same);var head=same.head();var changed=publish(same,actual);
                return changed.<ExecutionDisposition>map(value->new Published(head,value)).orElseGet(()->new Unchanged("actual Lifestyle cadence already current"));
            }catch(IOException|java.io.UncheckedIOException|IllegalArgumentException|IllegalStateException failure){return new Blocked("actual Lifestyle cadence settlement unavailable: "+failure.getMessage(),List.of());}
        }
    };}
    private static boolean lifestyle(OperationKey operation){return operation.equals(GovernancePolicies.FOCUS)||operation.equals(GovernancePolicies.PERK);}
    public Optional<WriterContracts.Receipt> publish(ContinuityStorePort.Session same,ActionReceipt actual)throws IOException{
        core.writer().requireSession(same);if(actual.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)return Optional.empty();
        var old=available(same);var receipt=core.archive().inSession(same,archive->archive.receiptReferenceOf(actual));
        var input=new Input(old.reference().payload(),receipt,domain(actual.command().operation()));var head=same.head();byte[] output=reduce(same,head,old.reference(),input);
        if(Arrays.equals(output,old.canonicalBody()))return Optional.empty();var body=core.archive().preserveArtifact(same,output,1_048_576);byte[] bytes=encode(input);
        var request=new DomainBodies.ImportRequest(DomainBodies.Slot.OPTIONAL_CADENCE,CadenceModels.SCHEMA,body,bytes,List.of(input.previous(),input.receipt()),"cadence-action-"+ActionCodec.sha256(bytes));
        var prepared=same.previewImport(request);StrictJson.require(prepared.predecessor().digest().equals(head.digest()),"actual action cadence preview crossed head");var committed=same.commitImport(prepared);var published=available(same);
        StrictJson.require(committed.disposition()!=WriterContracts.Disposition.NO_CHANGE&&published.reference().payload().equals(body)&&Arrays.equals(output,published.canonicalBody()),"actual action cadence commit/readback required");return Optional.of(committed);
    }
    public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] body)throws IOException{
        var same=core.writer().borrowedSession();core.writer().requireSession(same);StrictJson.require(head.digest().equals(same.head().digest())&&request.slot()==DomainBodies.Slot.OPTIONAL_CADENCE&&request.contractSchema().equals(CadenceModels.SCHEMA),"actual action cadence source/head differs");
        var input=decode(request.producerInput());StrictJson.require(request.evidence().equals(List.of(input.previous(),input.receipt())),"actual cadence action evidence differs");byte[] expected=reduce(same,head,previous.orElseThrow(),input);
        StrictJson.require(Arrays.equals(expected,body),"actual applied action cadence reducer differs");return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",head.digest()).put("body",ActionCodec.sha256(expected)).put("input",ActionCodec.sha256(request.producerInput()))));
    }
    private byte[] reduce(ContinuityStorePort.Session same,WriterContracts.Head head,DomainBodies.BodyRef previous,Input input)throws IOException{
        StrictJson.require(previous.payload().equals(input.previous())&&DomainBodies.reference(head.state(),DomainBodies.Slot.OPTIONAL_CADENCE).filter(previous::equals).isPresent(),"cadence action original body/source custody differs");
        var archive=core.archive().withSession(same);var receipt=archive.loadReceipt(input.receipt());var canonical=ContinuityActionJournal.lookup(head.state(),receipt.command().actionId(),archive).orElseThrow(()->new IOException("actual action cadence receipt is absent from canonical history"));
        StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(receipt,archive),ActionReceiptCodec.encodeReceipt(canonical,archive))&&receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                &&input.domain()==domain(receipt.command().operation()),"cadence reset needs its exact canonical applied domain action");
        StrictJson.require(receipt.state() instanceof ActionState.Settled,"actual primitive governance settlement required");var settled=(ActionState.Settled)receipt.state();ActionEffects.validate(receipt.command(),settled.attempt(),settled.settlement());
        context.bindings().actualArchivedVerifier(receipt.command().operation()).orElseThrow(()->new IOException("actual action native material verifier missing")).verifier().verify(head,receipt,archive);
        if(input.domain()==CadenceModels.Domain.COUNCIL||input.domain()==CadenceModels.Domain.CROWN){
            if(civicDomains==null)throw new IOException("actual Council/Crown material holder was not bound");civicDomains.requireMaterialSettlement(same,receipt);
        }
        if(input.domain()==CadenceModels.Domain.FEAST){
            var read=same.readDomain(DomainBodies.Slot.FEAST);if(!(read instanceof DomainBodies.Available body))throw new IOException("actual settled Feast holder unavailable");
            var feast=FeastDomainRuntime.decode(body.canonicalBody());StrictJson.require(feast.pending().isEmpty()&&feast.resolved().filter(result->result.receipt().equals(input.receipt())&&result.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED).isPresent(),"Feast material must actually settle before cadence reset");
        }
        byte[] original=core.archive().readArtifact(same,input.previous(),1_048_576);var frame=receipt.command().before().frame();var state=CadenceJson.readState(original,frame.episodeRunId());
        var object=StrictJson.parse(original);StrictJson.require(StrictJson.text(object.get("episode_run_id")).equals(frame.episodeRunId()),"another episode cadence cannot reset without its actual episode transition");
        var current=new CadenceModels.Frame(frame.episodeRunId(),frame.identity().dateRaw(),frame.identity().nativeRevision());
        var priorAction=state.row(input.domain()).lastActualActionFrame();
        if(priorAction.isPresent()){
            var marker=priorAction.orElseThrow();int revision=marker.nativeRevision().compareTo(current.nativeRevision());int date=marker.dateRaw().compareTo(current.dateRaw());
            StrictJson.require((revision>=0&&date>=0)||(revision<=0&&date<=0),"actual action cadence marker has conflicting date/revision order");
            if(revision>=0&&date>=0)return WriterContracts.canonical(original);
        }
        return CadenceJson.writeState(OptionalCheckCadence.record(state,input.domain(),current,true));
    }
    private static CadenceModels.Domain domain(OperationKey operation){if(OrdinaryFeastPolicy.OWNED.contains(operation))return CadenceModels.Domain.FEAST;
        if(operation.equals(GovernancePolicies.FOCUS)||operation.equals(GovernancePolicies.PERK))return CadenceModels.Domain.LIFESTYLE;
        if(operation.equals(GovernancePolicies.COUNCIL)||operation.equals(GovernancePolicies.CORE_COUNCIL))return CadenceModels.Domain.COUNCIL;
        if(operation.equals(GovernancePolicies.CROWN))return CadenceModels.Domain.CROWN;throw new IllegalArgumentException("unregistered governance cadence action");}
    private DomainBodies.Available available(ContinuityStorePort.Session same)throws IOException{var read=same.readDomain(DomainBodies.Slot.OPTIONAL_CADENCE);if(read instanceof DomainBodies.Available actual)return actual;throw new IOException("actual action cadence body unavailable");}
    private static byte[] encode(Input input){var row=StrictJson.object().put("schema",INPUT).put("domain",input.domain().wire());row.set("previous",input.previous().toJson());row.set("receipt",input.receipt().toJson());return StrictJson.canonical(row);}
    private static Input decode(byte[] raw){var row=StrictJson.object(StrictJson.parse(raw),Set.of("schema","domain","previous","receipt"));StrictJson.require(StrictJson.text(row.get("schema")).equals(INPUT),"actual cadence action schema required");return new Input(ExactRef.fromJson(row.get("previous")),ExactRef.fromJson(row.get("receipt")),CadenceModels.Domain.fromWire(StrictJson.text(row.get("domain"))));}
}
