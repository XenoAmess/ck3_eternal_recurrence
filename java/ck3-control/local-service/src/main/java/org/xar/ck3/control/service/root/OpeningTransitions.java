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
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile;

/** Transition producer owned by the original OPENING_GATE registration; no second writer or SAVE authority. */
public final class OpeningTransitions implements OrdinaryPlanCompletion {
    public static final String PRODUCER_SCHEMA="xar.java-opening-transitions/v5";
    public record CheckpointRequired(ActionReceipt originalFocus) {
        public CheckpointRequired {Objects.requireNonNull(originalFocus);StrictJson.require(originalFocus.command().operation().equals(GovernancePolicies.FOCUS)
                &&originalFocus.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,"actual applied opening focus required");}
    }
    private enum Kind { PENDING,RECEIPT,CHECKPOINT,EXISTING,CONSUME,IMPORTED_UNISSUED_REBIND,COMMITTED_IMPORTED_UNISSUED_REBIND,EXTERNAL_UNISSUED_REBIND }
    private record Input(Kind kind,ExactRef previous,ExactRef original) { }
    private record CommittedImport(ContinuityStorePort.Session session, RootCommittedOrdinaryRestoration proof) { }
    private record ImportedRebind(SavedAttachmentSourceStore.ImportedOrigin origin, CheckpointPair pair,
            SemanticEvidence semantic, G2Source source, String sessionId, ExactRef basis) { }
    private final RootRuntimeContext context;private final List<ExactRef> producers;
    private final ThreadLocal<CommittedImport> committedImport = new ThreadLocal<>();
    private GovernanceRuntimeInstaller.Installed nativeGovernance;
    private OpeningReadProfile.Bindings readOnlyOpening;
    public OpeningTransitions(RootRuntimeContext context,List<ExactRef> producers){this.context=Objects.requireNonNull(context);this.producers=List.copyOf(producers);}
    public void bindNative(GovernanceRuntimeInstaller.Installed actual){nativeGovernance=Objects.requireNonNull(actual);}
    void bindReadOnlyOpening(OpeningReadProfile.Bindings actual) {
        StrictJson.require(nativeGovernance==null&&readOnlyOpening==null,"readonly Opening binds once independently of legacy Native governance");
        readOnlyOpening=Objects.requireNonNull(actual);
    }

    private ContinuityStorePort.Session session()throws IOException{var same=context.borrowedSession();context.writer().requireSession(same);return same;}
    void rebindImportedUnissued(ContinuityStorePort.Session same,RootRestorationOriginalProof.Original restored)throws IOException {
        var current=body(same);
        if(!unissuedAtImportedEntry(GovernanceOpeningDocument.decode(current.canonicalBody())))return;
        var input=StrictJson.object();
        input.set("restoration_basis",restored.basis().toJson());
        publish(same,Kind.IMPORTED_UNISSUED_REBIND,current.reference().payload(),input);
    }
    /** The registered producer may borrow only the installed committed attachment and this actual writer session. */
    void rebindCommittedImportedUnissued(ContinuityStorePort.Session same, RootCommittedOrdinaryRestoration restored)
            throws IOException {
        Objects.requireNonNull(restored).requireCurrent(same, context);
        var attached = attachedOpening(restored);
        var current = body(same);
        var document = GovernanceOpeningDocument.decode(current.canonicalBody());
        if (!requiresCommittedUnissuedRebind(attached, current.reference(), document, restored.successor(),
                restored.source(), restored.basis())) return;
        StrictJson.require(committedImport.get() == null, "one actual committed Opening import per held writer scope");
        var original = StrictJson.object();
        original.set("committed_restoration_basis", restored.basis().toJson());
        original.set("semantic", semantic(restored.semantic()));
        committedImport.set(new CommittedImport(same, restored));
        try {
            publish(same, Kind.COMMITTED_IMPORTED_UNISSUED_REBIND, attached.payload(), original);
        } finally {
            committedImport.remove();
        }
    }

    void rebindExternalUnissued(ContinuityStorePort.Session same, SemanticEvidence observed) throws IOException {
        context.writer().requireSession(same);
        context.requireActiveGame();
        var current = body(same);
        var old = GovernanceOpeningDocument.decode(current.canonicalBody());
        var owner = new SessionIdentity(context.game().machineId(), context.game().generation(), context.game().sessionId());
        if (old.observed().game().equals(owner.game())) {
            StrictJson.require(old.sessionId().equals(owner.sessionId()), "external opening changed its current owning session");
            return;
        }
        if (retainsExternalReadOnlyCompletion(old)) {
            GovernanceOpeningDocument.requireSameEpisode(old, observed.frame(), context.source());
            RootGovernanceOpeningInputs.externalOpeningEvidence(same, context.archive().withSession(same),
                    owner, old, observed.frame(), current)
                    .orElseThrow(() -> new IOException("actual completed external opening origin is unavailable"));
            context.semanticVerifier().verify(same, owner, observed);
            return;
        }
        var evidence = namedOpeningEvidence(same, old, observed, current, owner);
        var input = StrictJson.object();
        input.set("named_origin", evidence.getFirst().toJson());
        input.set("semantic", semantic(observed));
        publish(same, Kind.EXTERNAL_UNISSUED_REBIND, current.reference().payload(), input);
    }

    static boolean retainsExternalReadOnlyCompletion(GovernanceOpeningDocument.Document old) {
        return old.stage() == OpeningStage.COMPLETE && old.preparedCommand().isEmpty()
                && old.actionReceipt().isEmpty() && old.checkpoint().isEmpty()
                && old.existingObserved().filter(actual -> actual.machineId().equals(old.observed().machineId())
                        && actual.game().equals(old.observed().game())
                        && actual.frame().episodeRunId().equals(old.observed().frame().episodeRunId())
                        && actual.frame().identity().player().equals(old.observed().frame().identity().player())
                        && actual.frame().identity().dateRaw().equals(old.observed().frame().identity().dateRaw())).isPresent();
    }

    private List<ExactRef> namedOpeningEvidence(ContinuityStorePort.Session same, GovernanceOpeningDocument.Document old,
            SemanticEvidence observed, DomainBodies.Available current, SessionIdentity owner) throws IOException {
        StrictJson.require(unissuedAtImportedEntry(old), "external opening can carry only the original unissued gate");
        GovernanceOpeningDocument.requireSameEpisode(old, observed.frame(), context.source());
        return RootGovernanceOpeningInputs.externalOpeningEvidence(same, context.archive().withSession(same),
                owner, old, observed.frame(), current).orElseThrow(() -> new IOException("actual external opening origin is unavailable"));
    }

    static byte[] externalUnissuedDocument(GovernanceOpeningDocument.Document old, ObservationIdentity observation,
            G2Source source, SessionIdentity owner, List<ExactRef> evidence) {
        StrictJson.require(unissuedAtImportedEntry(old)
                && owner.machineId().equals(observation.machineId()) && owner.game().equals(observation.game())
                && !old.observed().game().equals(owner.game()) && !old.sessionId().equals(owner.sessionId())
                && observation.frame().identity().dateRaw().compareTo(old.observed().frame().identity().dateRaw()) >= 0,
                "external opening rebind requires a new actual owner and the original unissued lifecycle");
        GovernanceOpeningDocument.requireSameEpisode(old, observation, source);
        var retained = new LinkedHashSet<>(old.originals());
        retained.addAll(evidence);
        return GovernanceOpeningDocument.encode(new GovernanceOpeningDocument.Document(observation, source, owner.sessionId(),
                OpeningStage.AWAIT_SUBMIT, Optional.empty(), Optional.empty(), List.copyOf(retained)));
    }

    private static DomainBodies.BodyRef attachedOpening(RootCommittedOrdinaryRestoration restored) throws IOException {
        return DomainBodies.reference(restored.attachmentHead(), DomainBodies.Slot.OPENING_GATE)
                .orElseThrow(() -> new IOException("committed imported attachment lacks its retained Opening member"));
    }

    static boolean requiresCommittedUnissuedRebind(DomainBodies.BodyRef attached, DomainBodies.BodyRef current,
            GovernanceOpeningDocument.Document document, SessionIdentity successor, G2Source source, ExactRef basis) {
        if (attached.equals(current)) return unissuedAtImportedEntry(document);
        StrictJson.require(document.observed().machineId().equals(successor.machineId())
                && document.observed().game().equals(successor.game()) && document.sessionId().equals(successor.sessionId())
                && document.source().equals(source) && document.originals().containsAll(List.of(attached.payload(), basis)),
                "committed imported Opening cannot replace another existing slot or proof");
        return false;
    }

    private RootCommittedOrdinaryRestoration requireCommittedImport(ContinuityStorePort.Session same) throws IOException {
        var actual = committedImport.get();
        if (actual == null || actual.session() != same)
            throw new IOException("actual private committed Opening import is not active in this writer scope");
        return actual.proof();
    }

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
        if(receipt.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)return Optional.empty();
        if(receipt.command().before().game().equals(context.game().generation()))return Optional.empty();
        return Optional.of(new CheckpointRequired(receipt));
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
                if(retained.isEmpty()) {
                    requireExisting(document,retained);
                } else {
                if(!retained.orElseThrow().settled())return new Unchanged("opening exact original pending/UNKNOWN preserved");var actual=retained.orElseThrow();var original=receiptRef(same,actual);
                if(document.actionReceipt().isEmpty()||!document.actionReceipt().orElseThrow().equals(original)){var payload=StrictJson.object();payload.set("receipt",original.toJson());return planning(same,Kind.RECEIPT,before,payload);}
                if(actual.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)return new Unchanged("opening confirmed rejection retained without completion credit");
                if(document.checkpoint().isEmpty()&&request.before().game().equals(actual.command().before().game())) {
                    var consumed=GovernanceReceipts.consumeOpeningSameGame(actual,request,document.checkpoint());
                    if(consumed.status()!=GovernanceReceipts.Status.CONSUMED)return new Unchanged(consumed.reason());
                    return planning(same,Kind.CONSUME,before,current(same,request));
                }
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
            }
            if(planned.trace().finalPlan().isEmpty())return new Unchanged("opening has no actual existing-focus producer plan");
            var intent=planned.trace().finalPlan().orElseThrow().detail().get("opening_required_gate_intent");
            if(!new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("consume_verified_existing_focus_on_following_turn").equals(intent))return new Unchanged("opening has no verified existing-focus intent");
            if(document.existingObserved().filter(observed->observed.frame().snapshotId().equals(request.before().frame().snapshotId())).isPresent())
                return new Unchanged("existing opening focus awaits a different actual formal snapshot");
            final ExactRef original;
            if(readOnlyOpening!=null) {
                var contract=readOnlyOpening.current();StrictJson.require(context.readCatalog().containsIdentity(contract),"readonly Opening current definition is not the identical installed catalog member");
                var readRequest=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),contract.operation(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),request.deadline());
                var result=context.reads().read(same,contract,readRequest);
                if(!(result instanceof PlanningReadResult.Known<OpeningReadProfile.Data> known))return new Unchanged("actual readonly Opening current query unavailable");
                context.archive().inSession(same,archive->{org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(known.receipt(),archive);return Boolean.TRUE;});
                requireReadOnlyExisting(known.receipt(),contract);original=known.originalReceipt();
            }else {
                if(nativeGovernance==null)throw new IOException("actual native LIFE installation missing");
                var definitions=nativeGovernance.planningReads();
                var result=context.reads().read(same,definitions.formal(),new PlanningReadRequest(request.before(),request.source(),request.sessionId(),definitions.formal().operation(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),request.deadline()));
                if(!(result instanceof PlanningReadResult.Known<org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj> known))return new Unchanged("actual existing-focus formal query unavailable");
                original=known.originalReceipt();
            }
            var payload=current(same,request);payload.set("query",original.toJson());return planning(same,Kind.EXISTING,before,payload);
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
        var body=context.archive().preserveArtifact(same,expected,1_048_576);byte[] encoded=encodeInput(input);var request=new DomainBodies.ImportRequest(DomainBodies.Slot.OPENING_GATE,GovernanceOpeningDocument.SCHEMA,body,encoded,importEvidence(same,input),"opening-"+ActionCodec.sha256(encoded));
        var prepared=same.previewImport(request);StrictJson.require(prepared.predecessor().digest().equals(head.digest()),"opening preparation crossed its head");var committed=same.commitImport(prepared);var actual=body(same);
        StrictJson.require(committed.disposition()!=WriterContracts.Disposition.NO_CHANGE&&actual.reference().payload().equals(body)&&Arrays.equals(actual.canonicalBody(),expected),"opening actual commit/readback required");return Optional.of(committed);}
    public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] body)throws IOException{
        var same=session();StrictJson.require(head.digest().equals(same.head().digest())&&request.slot()==DomainBodies.Slot.OPENING_GATE&&request.contractSchema().equals(GovernanceOpeningDocument.SCHEMA),"opening head/slot/schema changed");
        var input=decodeInput(request.producerInput());StrictJson.require(request.evidence().equals(importEvidence(same,input)),"opening original evidence differs");byte[] expected=reduce(same,head,previous.orElseThrow(),input);
        StrictJson.require(Arrays.equals(expected,body),"actual opening reducer differs from proposed body");return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",head.digest()).put("body",ActionCodec.sha256(body)).put("input",ActionCodec.sha256(request.producerInput()))));}
    private List<ExactRef> importEvidence(ContinuityStorePort.Session same, Input input) throws IOException {
        var exact = List.of(input.previous(), input.original());
        if (input.kind() == Kind.EXTERNAL_UNISSUED_REBIND) {
            var original = StrictJson.object(StrictJson.parse(load(same, input.original())), Set.of("named_origin", "semantic"));
            var retained = new LinkedHashSet<>(exact);
            retained.add(ExactRef.fromJson(original.get("named_origin")));
            retained.addAll(semantic(original.get("semantic")).references());
            return List.copyOf(retained);
        }
        if (input.kind() != Kind.COMMITTED_IMPORTED_UNISSUED_REBIND) return exact;
        var restored = requireCommittedImport(same);
        var retained = new LinkedHashSet<>(exact);
        retained.add(restored.basis());
        retained.add(restored.attachment().reference());
        retained.add(restored.importedOrigin().targetEntry().reference());
        retained.addAll(restored.semantic().references());
        return List.copyOf(retained);
    }

    private byte[] reduce(ContinuityStorePort.Session same,WriterContracts.Head head,DomainBodies.BodyRef previous,Input input)throws IOException{
        requireRetainedPrevious(head,previous,input.previous());
        var old=GovernanceOpeningDocument.decode(readBody(same,previous.payload()));var payload=StrictJson.parse(load(same,input.original()));var refs=new ArrayList<>(old.originals());old.preparedCommand().ifPresent(refs::add);refs.add(input.original());
        if (input.kind() == Kind.EXTERNAL_UNISSUED_REBIND) {
            var exact = StrictJson.object(payload, Set.of("named_origin", "semantic"));
            var observation = semantic(exact.get("semantic"));
            var owner = new SessionIdentity(context.game().machineId(), context.game().generation(), context.game().sessionId());
            var retained = body(same);
            StrictJson.require(retained.reference().equals(previous), "external opening predecessor body differed");
            var evidence = namedOpeningEvidence(same, old, observation, retained, owner);
            StrictJson.require(ExactRef.fromJson(exact.get("named_origin")).equals(evidence.getFirst()),
                    "external opening changed its original named-save rebind");
            context.semanticVerifier().verify(same, owner, observation);
            refs.addAll(evidence);
            refs.addAll(observation.references());
            return externalUnissuedDocument(old, observation.frame(), context.source(), owner, refs);
        }
        if(input.kind()==Kind.IMPORTED_UNISSUED_REBIND){
            var exact=StrictJson.object(payload,Set.of("restoration_basis"));
            var basis=ExactRef.fromJson(exact.get("restoration_basis"));
            var restored=context.restorationOriginal(same);
            StrictJson.require(restored.basis().equals(basis)&&DomainBodies.reference(restored.attachmentHead(),DomainBodies.Slot.OPENING_GATE)
                    .filter(previous::equals).isPresent(),"imported Opening must start at its retained target attachment member");
            restored.requireImportPredecessor(same,head);
            if(!(restored.material() instanceof SavedAttachmentSourceStore.SavedMaterial saved))
                throw new IOException("imported Opening rebind requires ordinary saved material");
            var imported=saved.importedOrigin().orElseThrow(()->new IOException("Opening rebind requires its exact independent imported SAVE"));
            return importedTargetOpening(same, previous, old, new ImportedRebind(imported, restored.pair(),
                    restored.semantic(), restored.source(), restored.sessionId(), basis), refs);
        }
        if (input.kind() == Kind.COMMITTED_IMPORTED_UNISSUED_REBIND) {
            var exact = StrictJson.object(payload, Set.of("committed_restoration_basis", "semantic"));
            var restored = requireCommittedImport(same);
            restored.requireCurrent(same, context);
            var source = restored.importedOrigin();
            var successor = restored.successor();
            StrictJson.require(restored.basis().equals(ExactRef.fromJson(exact.get("committed_restoration_basis")))
                    && restored.semantic().equals(semantic(exact.get("semantic"))) && attachedOpening(restored).equals(previous)
                    && source.owner().equals(restored.departed())
                    && restored.semantic().frame().game().equals(successor.game())
                    && restored.semantic().frame().machineId().equals(successor.machineId()),
                    "committed imported Opening crossed its exact attachment, original target or new successor SEM");
            refs.add(restored.attachment().reference());
            return importedTargetOpening(same, previous, old, new ImportedRebind(source, restored.pair(),
                    restored.semantic(), restored.source(), successor.sessionId(), restored.basis()), refs);
        }
        if(input.kind()==Kind.PENDING){StrictJson.object(payload,Set.of("command"));var original=ExactRef.fromJson(payload.get("command"));var command=command(same,original);
            Optional<ActionReceipt> previousCanonical=Optional.empty();
            if(old.preparedCommand().isPresent())previousCanonical=canonical(same,command(same,old.preparedCommand().orElseThrow()).actionId());
            return pending(old,command,original,refs,previousCanonical,canonical(same,command.actionId()));}
        if(input.kind()==Kind.RECEIPT){StrictJson.object(payload,Set.of("receipt"));var original=ExactRef.fromJson(payload.get("receipt"));var actual=receipt(same,original);validate(same,actual);
            var command=command(same,old.preparedCommand().orElseThrow(()->new IOException("opening result has no original prepared command")));StrictJson.require(Arrays.equals(ActionCodec.encodeCommand(command),ActionCodec.encodeCommand(actual.command()))&&actual.settled(),"opening result differs from original command or remains UNKNOWN");refs.add(original);
            return encode(old,old.observed(),actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED?OpeningStage.AWAIT_CONSUMPTION:OpeningStage.AWAIT_RECEIPT,Optional.of(original),Optional.empty(),refs,old.preparedCommand(),old.existingObserved());}
        PlanningRequest current=PlanningWire.decodeRequest(load(same,ExactRef.fromJson(payload.get("request"))));SemanticEvidence proof=semantic(payload.get("semantic"));
        GovernanceOpeningDocument.requireSameEpisode(old,current.before(),current.source());StrictJson.require(proof.frame().equals(current.before()),"opening formal request differs from actual semantic frame");
        context.semanticVerifier().verify(same,new SessionIdentity(current.before().machineId(),current.before().game(),current.sessionId()),proof);refs.addAll(proof.references());refs.add(ExactRef.fromJson(payload.get("request")));
        if(input.kind()==Kind.EXISTING){StrictJson.object(payload,Set.of("request","semantic","query"));requireExisting(old,old.preparedCommand().isPresent()?canonical(same,command(same,old.preparedCommand().orElseThrow()).actionId()):Optional.empty());
            var read=context.archive().inSession(same,archive->archive.loadRead(ExactRef.fromJson(payload.get("query"))));StrictJson.require(read.request().before().equals(current.before())&&read.request().source().equals(current.source()),"existing focus read crossed its actual frame/source");
            if(readOnlyOpening!=null&&read.contractId().equals(readOnlyOpening.current().contractId())) {
                context.archive().inSession(same,archive->{org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(read,archive);return Boolean.TRUE;});
                requireReadOnlyExisting(read,readOnlyOpening.current());
            }else {
                var query=Objects.requireNonNull(nativeGovernance,"actual LIFE replay missing").planningReads().formal().decode(read);
                StrictJson.require(GovernancePolicies.existingFocus(query),"actual LIFE read has no qualified existing focus/progress");
            }
            refs.add(ExactRef.fromJson(payload.get("query")));
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
        StrictJson.object(payload,Set.of("request","semantic"));StrictJson.require(input.kind()==Kind.CONSUME
                &&GovernanceReceipts.consumeOpeningSameGame(focus,current,old.checkpoint()).status()==GovernanceReceipts.Status.CONSUMED,
                "opening has not reached actual following-turn original focus consumption");
        return encode(old,old.observed(),OpeningStage.COMPLETE,old.actionReceipt(),old.checkpoint(),refs,old.preparedCommand(),old.existingObserved());}
    /** Pure archival replay. Native/source/current writer qualification stays with the installed catalog and retained original verifier. */
    static void requireReadOnlyExisting(PlanningReadReceipt read,ReadContract<OpeningReadProfile.Data> contract) {
        StrictJson.require(OpeningReadProfile.isCurrentOperation(contract.operation())&&read.contractId().equals(contract.contractId())
                &&read.request().operation().equals(contract.operation())&&read.request().arguments().members().isEmpty(),"exact readonly current-focus receipt required");
        var data=contract.replay(read);var id=read.request().before().frame().identity();
        requireReadOnlyExistingData(data,new OpeningReadProfile.Frame(id.nativeRevision(),id.dateRaw(),id.player()));
    }
    static void requireReadOnlyExistingData(OpeningReadProfile.Data data,OpeningReadProfile.Frame expected) {
        data.requireApplicationMainOrigin();StrictJson.require(readOnlyExistingMatches(data,expected),
                "readonly Opening existing focus lacks its original actual current frame/progress");
    }
    /** DATA predicate only. Its caller must separately verify the original read, catalog, writer and main-ticket origin. */
    static boolean readOnlyExistingMatches(OpeningReadProfile.Data data,OpeningReadProfile.Frame expected) {
        return data.kind()==OpeningReadProfile.Kind.CURRENT&&data.available()&&data.progress().filter(OpeningReadProfile.FocusProgress::present).isPresent()
                &&data.frame().filter(expected::equals).isPresent();
    }
    static void requireExisting(GovernanceOpeningDocument.Document document,Optional<ActionReceipt> canonical) {
        StrictJson.require(document.actionReceipt().isEmpty()&&document.checkpoint().isEmpty()
                &&(document.preparedCommand().isEmpty()||document.stage()==OpeningStage.AWAIT_RECEIPT&&canonical.isEmpty()),
                "submitted opening action precedes observing existing focus");
    }
    private byte[] importedTargetOpening(ContinuityStorePort.Session same, DomainBodies.BodyRef previous,
            GovernanceOpeningDocument.Document old, ImportedRebind actual, List<ExactRef> evidence) throws IOException {
        var imported = actual.origin();
        var entry = same.readHistoricalTransition(imported.targetEntry());
        var marker = ContinuityJson.parseObject(entry.details(), 1_048_576);
        StrictJson.require(imported.owner().equals(OrdinaryCycleTransitions.sessionFromJson(marker.get("session"))),
                "imported Opening lost the original target entry owner");
        boolean pending = context.core().journal().locked(same, view -> view.unresolved().stream().anyMatch(receipt ->
                receipt.command().operation().equals(GovernancePolicies.FOCUS)
                        && receipt.command().origin().game().equals(imported.owner().game())
                        && receipt.command().sessionId().equals(imported.owner().sessionId())));
        StrictJson.require(!pending, "imported Opening cannot replace an unresolved original focus command");
        evidence.add(previous.payload());
        evidence.add(actual.basis());
        evidence.add(imported.targetEntry().reference());
        evidence.add(actual.semantic().semantic());
        return importedUnissuedDocument(old, imported.owner(), ProposalLifecycleCodec.decodeObservation(marker.get("opening")),
                G2Wire.source(marker.get("source")), actual.pair(), actual.semantic().frame(), actual.source(), actual.sessionId(), evidence);
    }

    private static boolean unissuedAtImportedEntry(GovernanceOpeningDocument.Document original) {
        return original.stage()==OpeningStage.AWAIT_SUBMIT&&original.preparedCommand().isEmpty()
                &&original.actionReceipt().isEmpty()&&original.checkpoint().isEmpty()&&original.existingObserved().isEmpty();
    }
    /** Material projection after replay of the actual v5 target entry and replacement attachment. */
    static byte[] importedUnissuedDocument(GovernanceOpeningDocument.Document old,SessionIdentity target,
            ObservationIdentity entry,G2Source entrySource,CheckpointPair physical,
            ObservationIdentity restored,G2Source restoredSource,String session,List<ExactRef> evidence) {
        var saved=physical.frame();
        StrictJson.require(unissuedAtImportedEntry(old)&&old.observed().equals(entry)&&old.source().equals(entrySource)
                &&old.sessionId().equals(target.sessionId())&&entry.game().equals(target.game())&&entry.machineId().equals(target.machineId())
                &&!target.game().equals(saved.game())&&!restored.game().equals(target.game())&&!restored.game().equals(saved.game())
                &&!session.equals(target.sessionId())&&restored.machineId().equals(target.machineId())
                &&entrySource.exactBuild().equals(restoredSource.exactBuild())
                &&entry.frame().identity().dateRaw().equals(saved.frame().identity().dateRaw())
                &&restored.frame().identity().dateRaw().equals(saved.frame().identity().dateRaw()),
                "imported Opening requires its original unissued target anchor and actual restored physical date");
        GovernanceOpeningDocument.requireSameEpisode(old,restored,entrySource);
        StrictJson.require(saved.machineId().equals(restored.machineId())
                &&saved.frame().episodeRunId().equals(restored.frame().episodeRunId())
                &&saved.frame().identity().player().equals(restored.frame().identity().player()),
                "imported Opening SAVE and restored actor/episode differ");
        var originalEvidence=new LinkedHashSet<>(old.originals());originalEvidence.addAll(evidence);
        return GovernanceOpeningDocument.encode(new GovernanceOpeningDocument.Document(restored,restoredSource,session,
                OpeningStage.AWAIT_SUBMIT,Optional.empty(),Optional.empty(),List.copyOf(originalEvidence)));
    }
    static byte[] pending(GovernanceOpeningDocument.Document old,ActionCommand command,ExactRef original,List<ExactRef> refs,
            Optional<ActionReceipt> previousCanonical,Optional<ActionReceipt> nextCanonical) {
        GovernanceOpeningDocument.requireSameEpisode(old,command.before(),command.source());
        StrictJson.require(command.operation().equals(GovernancePolicies.FOCUS)&&command.origin() instanceof CommandOrigin.Gameplay&&old.stage()!=OpeningStage.COMPLETE
                &&(old.preparedCommand().isEmpty()||old.preparedCommand().orElseThrow().equals(original)
                    ||old.stage()==OpeningStage.AWAIT_RECEIPT&&old.actionReceipt().isEmpty()&&old.checkpoint().isEmpty()
                        &&previousCanonical.isEmpty()&&nextCanonical.isEmpty()),"opening pending cannot overwrite another original or completed gate");
        var retained=new ArrayList<>(refs);old.preparedCommand().ifPresent(retained::add);retained.add(original);
        return encode(old,command.before(),OpeningStage.AWAIT_RECEIPT,Optional.empty(),Optional.empty(),retained,Optional.of(original),Optional.empty());
    }
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
