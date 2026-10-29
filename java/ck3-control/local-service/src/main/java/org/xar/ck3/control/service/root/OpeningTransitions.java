package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** Transition producer owned by the original OPENING_GATE registration; no second writer or SAVE authority. */
public final class OpeningTransitions implements OrdinaryPlanCompletion {
    public static final String PRODUCER_SCHEMA="xar.java-opening-transitions/v5";
    public record CheckpointRequired(ActionReceipt originalFocus) {
        public CheckpointRequired {Objects.requireNonNull(originalFocus);StrictJson.require(originalFocus.command().operation().equals(GovernancePolicies.FOCUS)
                &&originalFocus.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,"actual applied opening focus required");}
    }
    private enum Kind { PENDING,RECEIPT,CHECKPOINT,EXISTING,CONSUME }
    private record Input(Kind kind,ExactRef previous,ExactRef original) { }
    private final RootRuntimeContext context;private final List<ExactRef> producers;
    private GovernanceRuntimeInstaller.Installed nativeGovernance;
    public OpeningTransitions(RootRuntimeContext context,List<ExactRef> producers){this.context=Objects.requireNonNull(context);this.producers=List.copyOf(producers);}
    public void bindNative(GovernanceRuntimeInstaller.Installed actual){nativeGovernance=Objects.requireNonNull(actual);}
    private ContinuityStorePort.Session session()throws IOException{var same=context.borrowedSession();context.writer().requireSession(same);return same;}
    public RootDomainIntentPreparation.Binding pendingBinding(ExactRef implementation){return new RootDomainIntentPreparation.Binding("opening-focus",implementation,
            command->command.operation().equals(GovernancePolicies.FOCUS),(same,command)->{try{
                context.writer().requireSession(same);context.requireCurrent(command.deadline());var before=body(same);var document=GovernanceOpeningDocument.decode(before.canonicalBody());
                if(document.stage()==OpeningStage.COMPLETE)return;GovernanceOpeningDocument.requireSameEpisode(document,command.before(),command.source());
                StrictJson.require(command.before().game().equals(context.game().generation())&&command.sessionId().equals(context.game().sessionId()),"opening pending crossed actual Game/session");
                var payload=StrictJson.object();payload.set("command",material(same,ActionCodec.encodeCommand(command)).toJson());publish(same,Kind.PENDING,before.reference().payload(),payload);
            }catch(IOException failure){throw new UncheckedIOException("opening pending publication unavailable",failure);}});}
    public Optional<CheckpointRequired> requiresCheckpoint(ContinuityStorePort.Session same)throws IOException{
        context.writer().requireSession(same);var document=GovernanceOpeningDocument.decode(body(same).canonicalBody());
        if(document.stage()!=OpeningStage.AWAIT_CONSUMPTION||document.checkpoint().isPresent()||document.actionReceipt().isEmpty())return Optional.empty();
        var receipt=receipt(same,document.actionReceipt().orElseThrow());validate(same,receipt);
        return receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED?Optional.of(new CheckpointRequired(receipt)):Optional.empty();
    }
    @Override public ExecutionDisposition afterExecution(ActionReceipt actual){
        if(!actual.command().operation().equals(GovernancePolicies.FOCUS)||!actual.settled())return new Unchanged("opening retains actual unresolved/other-domain receipt");
        try{var same=session();var before=body(same);var document=GovernanceOpeningDocument.decode(before.canonicalBody());
            if(document.stage()==OpeningStage.COMPLETE||document.preparedCommand().isEmpty())return new Unchanged("receipt is outside the pending opening lifecycle");
            var head=same.head();var payload=StrictJson.object();payload.set("receipt",receiptRef(same,actual).toJson());var changed=publish(same,Kind.RECEIPT,before.reference().payload(),payload);
            return changed.<ExecutionDisposition>map(value->new Published(head,value)).orElseGet(()->new Unchanged("opening exact result already retained"));
        }catch(IOException|IllegalArgumentException|IllegalStateException failure){return new Blocked("actual opening receipt unavailable: "+failure.getMessage(),List.of());}}
    @Override public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned){
        try{var same=session();var before=body(same);var document=GovernanceOpeningDocument.decode(before.canonicalBody());
            if(document.stage()==OpeningStage.COMPLETE)return new Unchanged("opening complete at its actual published frontier");GovernanceOpeningDocument.requireSameEpisode(document,request.before(),request.source());
            if(document.preparedCommand().isPresent()){
                var command=command(same,document.preparedCommand().orElseThrow());var retained=canonical(same,command.actionId());
                if(retained.isEmpty()||!retained.orElseThrow().settled())return new Unchanged("opening exact original pending/UNKNOWN preserved");var actual=retained.orElseThrow();var original=receiptRef(same,actual);
                if(document.actionReceipt().isEmpty()||!document.actionReceipt().orElseThrow().equals(original)){var payload=StrictJson.object();payload.set("receipt",original.toJson());return planning(same,Kind.RECEIPT,before,payload);}
                if(actual.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)return new Unchanged("opening confirmed rejection retained without completion credit");
                if(document.checkpoint().isEmpty()){
                    CheckpointPair pair;
                    if(!request.before().game().equals(actual.command().before().game()))try {
                        context.requireRestoration(request.deadline());pair=context.restorationOriginal(same).pair();
                    }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("opening retained checkpoint source interrupted",interrupted);}
                    else {
                        var state=same.head().state();var saved=state.toJson();
                        if(saved.has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD)) {
                            var ordinary=StrictJson.object(saved.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD),Set.of("pair","state"));pair=CheckpointPairCodec.decode(StrictJson.canonical(ordinary.get("pair")));
                        } else {
                            var window=org.xar.ck3.control.continuity.EpisodeWindow.state(state);
                            if(window.isEmpty()||window.orElseThrow().phase()!=org.xar.ck3.control.continuity.EpisodeWindow.Phase.ACTIVE)return checkpointRequired(same,before,document);
                            var baseline=window.orElseThrow().baseline().orElseThrow();pair=CheckpointPairCodec.decode(load(same,baseline.pairRef()));
                            StrictJson.require(pair.saveActionId().equals(baseline.saveActionId())&&ActionCodec.sha256(CheckpointPairCodec.encode(pair)).equals(baseline.pairDigest()),
                                    "opening first SAVE differs from its actual canonical BASELINE pair");
                        }
                    }
                    if(!pair.frame().frame().episodeRunId().equals(request.before().frame().episodeRunId())
                            || !pair.frame().frame().identity().player().equals(request.before().frame().identity().player())
                            || pair.frame().frame().identity().nativeRevision().compareTo(actual.applied().orElseThrow().observation().after().frame().identity().nativeRevision())<0)
                        return checkpointRequired(same,before,document);
                    return planning(same,Kind.CHECKPOINT,before,checkpointPayload(same,request,pair,actual));
                }
                return planning(same,Kind.CONSUME,before,current(same,request));
            }
            if(planned.trace().finalPlan().isEmpty())return new Unchanged("opening has no actual existing-focus producer plan");
            var intent=planned.trace().finalPlan().orElseThrow().detail().get("opening_required_gate_intent");
            if(!new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("consume_verified_existing_focus_on_following_turn").equals(intent))return new Unchanged("opening has no verified existing-focus intent");
            if(document.existingObserved().filter(observed->observed.frame().snapshotId().equals(request.before().frame().snapshotId())).isPresent())
                return new Unchanged("existing opening focus awaits a different actual formal snapshot");
            var definitions=Objects.requireNonNull(nativeGovernance,"actual native LIFE installation missing").planningReads();
            var result=context.reads().read(same,definitions.formal(),new PlanningReadRequest(request.before(),request.source(),request.sessionId(),definitions.formal().operation(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),request.deadline()));
            if(!(result instanceof PlanningReadResult.Known<org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj> known))return new Unchanged("actual existing-focus formal query unavailable");
            var payload=current(same,request);payload.set("query",known.originalReceipt().toJson());return planning(same,Kind.EXISTING,before,payload);
        }catch(IOException|IllegalArgumentException|IllegalStateException failure){return new Blocked("actual opening consumption unavailable: "+failure.getMessage(),List.of());}}
    private ObjectNode checkpointPayload(ContinuityStorePort.Session same,PlanningRequest request,CheckpointPair pair,ActionReceipt focus)throws IOException {
        var payload=current(same,request);Optional<ExactRef> basis=Optional.empty();SavedCheckpointMaterial material;
        if(!request.before().game().equals(focus.command().before().game()))try {
            var binding=context.requireRestoration(request.deadline());StrictJson.require(binding.pair().equals(pair),"opening restored checkpoint differs from actual admitted pair");
            var proof=context.restorationOriginal(same);StrictJson.require(proof.pair().equals(pair),"retained restoration original differs from the actual admitted pair");
            basis=Optional.of(proof.basis());material=proof.material();
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("opening restoration source capture interrupted",interrupted);}
        else material=context.savedMaterials().currentPhysical(same,pair);
        var save=canonical(same,pair.saveActionId()).orElseThrow(()->new IOException("opening SAVE is absent from canonical actions"));
        return new OpeningCheckpointInput(ExactRef.fromJson(payload.get("request")),semantic(payload.get("semantic")),pair,receiptRef(same,save),material.kind(),material.witness(),basis).toJson();
    }
    private PlanningDisposition checkpointRequired(ContinuityStorePort.Session same,DomainBodies.Available before,GovernanceOpeningDocument.Document document)throws IOException {
        var actual=requiresCheckpoint(same).orElseThrow(()->new IOException("opening checkpoint request lacks the actual validated applied focus"));
        return new OrdinaryPlanCompletion.CheckpointRequired(actual.originalFocus(),List.of(before.reference().payload(),document.actionReceipt().orElseThrow(),document.preparedCommand().orElseThrow()));
    }
    private PlanningDisposition planning(ContinuityStorePort.Session same,Kind kind,DomainBodies.Available before,ObjectNode original)throws IOException{
        var head=same.head();var changed=publish(same,kind,before.reference().payload(),original);return changed.<PlanningDisposition>map(value->new Published(head,value)).orElseGet(()->new Unchanged("opening awaits a following actual formal frame"));}
    private ObjectNode current(ContinuityStorePort.Session same,PlanningRequest request)throws IOException{
        return context.readiness().current(same,request.before(),request.deadline(),lease->{StrictJson.require(lease.frame().source().equals(request.source())&&lease.frame().sessionId().equals(request.sessionId()),"opening formal source differs");
            var value=StrictJson.object();value.set("request",material(same,PlanningWire.encodeRequest(request)).toJson());value.set("semantic",semantic(lease.semantic()));return value;});}
    private Optional<WriterContracts.Receipt> publish(ContinuityStorePort.Session same,Kind kind,ExactRef previous,ObjectNode original)throws IOException{
        context.writer().requireSession(same);var head=same.head();var input=new Input(kind,previous,material(same,StrictJson.canonical(original)));var old=DomainBodies.reference(head.state(),DomainBodies.Slot.OPENING_GATE).orElseThrow();
        byte[] expected=reduce(same,head,old,input);if(Arrays.equals(expected,readBody(same,previous)))return Optional.empty();
        var body=context.archive().preserveArtifact(same,expected,1_048_576);byte[] encoded=encodeInput(input);var request=new DomainBodies.ImportRequest(DomainBodies.Slot.OPENING_GATE,GovernanceOpeningDocument.SCHEMA,body,encoded,List.of(previous,input.original()),"opening-"+ActionCodec.sha256(encoded));
        var prepared=same.previewImport(request);StrictJson.require(prepared.predecessor().digest().equals(head.digest()),"opening preparation crossed its head");var committed=same.commitImport(prepared);var actual=body(same);
        StrictJson.require(committed.disposition()!=WriterContracts.Disposition.NO_CHANGE&&actual.reference().payload().equals(body)&&Arrays.equals(actual.canonicalBody(),expected),"opening actual commit/readback required");return Optional.of(committed);}
    public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] body)throws IOException{
        var same=session();StrictJson.require(head.digest().equals(same.head().digest())&&request.slot()==DomainBodies.Slot.OPENING_GATE&&request.contractSchema().equals(GovernanceOpeningDocument.SCHEMA),"opening head/slot/schema changed");
        var input=decodeInput(request.producerInput());StrictJson.require(request.evidence().equals(List.of(input.previous(),input.original())),"opening original evidence differs");byte[] expected=reduce(same,head,previous.orElseThrow(),input);
        StrictJson.require(Arrays.equals(expected,body),"actual opening reducer differs from proposed body");return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",head.digest()).put("body",ActionCodec.sha256(body)).put("input",ActionCodec.sha256(request.producerInput()))));}
    private byte[] reduce(ContinuityStorePort.Session same,WriterContracts.Head head,DomainBodies.BodyRef previous,Input input)throws IOException{
        requireRetainedPrevious(head,previous,input.previous());
        var old=GovernanceOpeningDocument.decode(readBody(same,previous.payload()));var payload=StrictJson.parse(load(same,input.original()));var refs=new ArrayList<>(old.originals());refs.add(input.original());
        if(input.kind()==Kind.PENDING){StrictJson.object(payload,Set.of("command"));var original=ExactRef.fromJson(payload.get("command"));var command=command(same,original);GovernanceOpeningDocument.requireSameEpisode(old,command.before(),command.source());
            StrictJson.require(command.operation().equals(GovernancePolicies.FOCUS)&&command.origin() instanceof CommandOrigin.Gameplay&&old.stage()!=OpeningStage.COMPLETE
                    &&(old.preparedCommand().isEmpty()||old.preparedCommand().orElseThrow().equals(original)),"opening pending cannot overwrite another original or completed gate");refs.add(original);
            return encode(old,command.before(),OpeningStage.AWAIT_RECEIPT,Optional.empty(),Optional.empty(),refs,Optional.of(original),Optional.empty());}
        if(input.kind()==Kind.RECEIPT){StrictJson.object(payload,Set.of("receipt"));var original=ExactRef.fromJson(payload.get("receipt"));var actual=receipt(same,original);validate(same,actual);
            var command=command(same,old.preparedCommand().orElseThrow(()->new IOException("opening result has no original prepared command")));StrictJson.require(Arrays.equals(ActionCodec.encodeCommand(command),ActionCodec.encodeCommand(actual.command()))&&actual.settled(),"opening result differs from original command or remains UNKNOWN");refs.add(original);
            return encode(old,old.observed(),actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED?OpeningStage.AWAIT_CONSUMPTION:OpeningStage.AWAIT_RECEIPT,Optional.of(original),Optional.empty(),refs,old.preparedCommand(),old.existingObserved());}
        PlanningRequest current=PlanningWire.decodeRequest(load(same,ExactRef.fromJson(payload.get("request"))));SemanticEvidence proof=semantic(payload.get("semantic"));
        GovernanceOpeningDocument.requireSameEpisode(old,current.before(),current.source());StrictJson.require(proof.frame().equals(current.before()),"opening formal request differs from actual semantic frame");
        context.semanticVerifier().verify(same,new SessionIdentity(current.before().machineId(),current.before().game(),current.sessionId()),proof);refs.addAll(proof.references());refs.add(ExactRef.fromJson(payload.get("request")));
        if(input.kind()==Kind.EXISTING){StrictJson.object(payload,Set.of("request","semantic","query"));StrictJson.require(old.preparedCommand().isEmpty()&&old.actionReceipt().isEmpty(),"submitted opening action precedes observing existing focus");
            var read=context.archive().inSession(same,archive->archive.loadRead(ExactRef.fromJson(payload.get("query"))));StrictJson.require(read.request().before().equals(current.before())&&read.request().source().equals(current.source()),"existing focus read crossed its actual frame/source");
            var query=Objects.requireNonNull(nativeGovernance,"actual LIFE replay missing").planningReads().formal().decode(read);StrictJson.require(GovernancePolicies.existingFocus(query),"actual LIFE read has no qualified existing focus/progress");refs.add(ExactRef.fromJson(payload.get("query")));
            boolean following=old.existingObserved().isPresent()&&!old.existingObserved().orElseThrow().frame().snapshotId().equals(current.before().frame().snapshotId());
            return encode(old,old.observed(),following?OpeningStage.COMPLETE:OpeningStage.AWAIT_SUBMIT,Optional.empty(),Optional.empty(),refs,Optional.empty(),Optional.of(current.before()));}
        var focus=receipt(same,old.actionReceipt().orElseThrow(()->new IOException("opening lacks independent material focus receipt")));validate(same,focus);
        if(input.kind()==Kind.CHECKPOINT){var checkpoint=OpeningCheckpointInput.fromJson(payload);var pair=checkpoint.pair();
            var material=context.savedMaterials().loadRetainedOriginal(same,checkpoint.materialKind(),checkpoint.savedMaterial(),pair);StrictJson.require(material.kind()==checkpoint.materialKind()&&material.witness().equals(checkpoint.savedMaterial())&&material.pair().equals(pair)&&material.session().game().equals(focus.command().before().game())
                    &&pair.frame().frame().episodeRunId().equals(current.before().frame().episodeRunId())&&pair.frame().frame().identity().player().equals(current.before().frame().identity().player()),"opening checkpoint is not the qualified actual same-campaign pair");
            var save=receipt(same,checkpoint.saveReceipt());validate(same,save);StrictJson.require(save.command().actionId().equals(pair.saveActionId())&&save.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                    &&save.applied().orElseThrow().observation().actual().contains(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("checkpoint_pair_verified"),true))
                    &&pair.frame().frame().identity().nativeRevision().compareTo(focus.applied().orElseThrow().observation().after().frame().identity().nativeRevision())>=0,"opening SAVE lacks actual physical pair after focus effect");
            refs.add(material.reference());refs.add(checkpoint.saveReceipt());refs.add(pair.save().reference());refs.add(pair.driver().reference());refs.add(pair.nativeAckRef());var fact=new CheckpointFact(focus.command().actionId(),pair.frame(),checkpoint.saveReceipt());
            boolean restored=!current.before().game().equals(focus.command().before().game());
            if(restored){
                var basis=checkpoint.restorationBasis().orElseThrow(()->new IOException("restored opening checkpoint lacks its actual retained private basis"));var original=RootRestorationOriginalProof.replayOriginal(context,same,basis);
                var attachment=original.attachmentHead();StrictJson.require(attachment.sequence()<=head.state().sequence(),"opening checkpoint cannot precede its actual replacement attachment");
                same.requireHistoricalState(attachment.sequence(),org.xar.ck3.control.continuity.ContinuityJson.digest(attachment.toJson()));
                var first=original.semantic().frame();StrictJson.require(original.pair().equals(pair)&&original.material().kind()==material.kind()&&original.material().witness().equals(material.witness())
                        &&original.game().equals(current.before().game())&&original.sessionId().equals(current.sessionId())&&original.source().equals(current.source())
                        &&first.frame().episodeRunId().equals(current.before().frame().episodeRunId())&&first.frame().identity().player().equals(current.before().frame().identity().player())
                        &&first.frame().identity().dateRaw().compareTo(current.before().frame().identity().dateRaw())<=0
                        &&first.frame().identity().nativeRevision().compareTo(current.before().frame().identity().nativeRevision())<=0,"opening historical replacement source differs from actual admitted attachment");
                refs.add(basis);refs.addAll(original.evidence());
            }else StrictJson.require(checkpoint.restorationBasis().isEmpty(),"same-Game checkpoint cannot substitute a replacement proof");
            boolean consumed=restored&&GovernanceReceipts.consumeAtFrame(focus,pair.frame(),Optional.of(fact),true).status()==GovernanceReceipts.Status.CONSUMED;
            return encode(old,old.observed(),consumed?OpeningStage.COMPLETE:OpeningStage.AWAIT_CONSUMPTION,old.actionReceipt(),Optional.of(fact),refs,old.preparedCommand(),old.existingObserved());}
        StrictJson.object(payload,Set.of("request","semantic"));StrictJson.require(input.kind()==Kind.CONSUME&&old.checkpoint().isPresent()&&GovernanceReceipts.consume(focus,current,old.checkpoint(),true).status()==GovernanceReceipts.Status.CONSUMED,"opening has not reached actual following-turn action/checkpoint consumption");
        return encode(old,old.observed(),OpeningStage.COMPLETE,old.actionReceipt(),old.checkpoint(),refs,old.preparedCommand(),old.existingObserved());}
    private static byte[] encode(GovernanceOpeningDocument.Document old,ObservationIdentity observed,OpeningStage stage,Optional<ExactRef> action,Optional<CheckpointFact> checkpoint,List<ExactRef> refs,Optional<ExactRef> command,Optional<ObservationIdentity> existing){return GovernanceOpeningDocument.encode(new GovernanceOpeningDocument.Document(observed,old.source(),old.sessionId(),stage,action,checkpoint,refs.stream().distinct().toList(),command,existing));}
    private void validate(ContinuityStorePort.Session same,ActionReceipt actual)throws IOException{var canonical=canonical(same,actual.command().actionId()).orElseThrow(()->new IOException("opening result absent from canonical actions"));context.archive().inSession(same,archive->{StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(actual,archive),ActionReceiptCodec.encodeReceipt(canonical,archive)),"opening caller receipt is not canonical");return Boolean.TRUE;});
        if(actual.state() instanceof ActionState.Settled settled)ActionEffects.validate(actual.command(),settled.attempt(),settled.settlement());if(actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&actual.command().operation().equals(GovernancePolicies.FOCUS))context.bindings().actualArchivedVerifier(actual.command().operation()).orElseThrow(()->new IOException("actual native material replay missing")).verifier().verify(same.head(),actual,context.archive().withSession(same));}
    private Optional<ActionReceipt> canonical(ContinuityStorePort.Session same,String id)throws IOException{var state=same.head().state();return context.archive().inSession(same,archive->ContinuityActionJournal.lookup(state,id,archive));}
    private ExactRef receiptRef(ContinuityStorePort.Session same,ActionReceipt value){return context.archive().inSession(same,archive->archive.receiptReferenceOf(value));}
    private ActionReceipt receipt(ContinuityStorePort.Session same,ExactRef ref){return context.archive().inSession(same,archive->archive.loadReceipt(ref));}
    private ActionCommand command(ContinuityStorePort.Session same,ExactRef ref){return ActionCodec.decodeCommand(load(same,ref));}
    private byte[] load(ContinuityStorePort.Session same,ExactRef ref){return context.archive().inSession(same,archive->archive.loadMaterial(ref)).bytes();}
    private ExactRef material(ContinuityStorePort.Session same,byte[] bytes){return context.archive().inSession(same,archive->archive.preserveMaterial(new RawJson(bytes)));}
    /** Historical producer references remain trace data; the retained payload must still be the exact canonical member. */
    static void requireRetainedPrevious(WriterContracts.Head head,DomainBodies.BodyRef previous,ExactRef expectedPayload) {
        StrictJson.require(previous.payload().equals(expectedPayload)
                &&DomainBodies.reference(head.state(),DomainBodies.Slot.OPENING_GATE).filter(previous::equals).isPresent(),
                "opening original body/canonical head changed");
    }
    private byte[] readBody(ContinuityStorePort.Session same,ExactRef ref)throws IOException{return context.archive().readArtifact(same,ref,1_048_576);}
    private DomainBodies.Available body(ContinuityStorePort.Session same)throws IOException{context.writer().requireSession(same);var value=same.readDomain(DomainBodies.Slot.OPENING_GATE);if(value instanceof DomainBodies.Available actual)return actual;throw new IOException("actual registered opening original unavailable");}
    private static ObjectNode semantic(SemanticEvidence value){return OpeningCheckpointInput.semanticToJson(value);}
    private static SemanticEvidence semantic(com.fasterxml.jackson.databind.JsonNode raw){return OpeningCheckpointInput.semanticFromJson(raw);}
    private static byte[] encodeInput(Input input){var row=StrictJson.object().put("schema",PRODUCER_SCHEMA).put("kind",input.kind().name());row.set("previous",input.previous().toJson());row.set("original",input.original().toJson());return StrictJson.canonical(row);}
    private static Input decodeInput(byte[] bytes){var row=StrictJson.object(StrictJson.parse(bytes),Set.of("schema","kind","previous","original"));StrictJson.require(StrictJson.text(row.get("schema")).equals(PRODUCER_SCHEMA),"exact opening transition schema required; historical input without saved-material file identity is incomplete");return new Input(Kind.valueOf(StrictJson.text(row.get("kind"))),ExactRef.fromJson(row.get("previous")),ExactRef.fromJson(row.get("original")));}
}
