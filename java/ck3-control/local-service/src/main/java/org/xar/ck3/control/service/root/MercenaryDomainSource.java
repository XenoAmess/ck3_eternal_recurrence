package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;

/** One durable mercenary producer. Imports re-run this original reducer under the original writer, before publication. */
public final class MercenaryDomainSource {
    private static final int MAX=ContinuityJson.DOMAIN_MAX_BYTES;
    private final List<ExactRef> sources;
    private RootApplicationAssembly.Core core;
    private DomainBodies.Registration registered;
    private final ThreadLocal<Transition> active=new ThreadLocal<>();
    public record Publication(WriterContracts.Head predecessor,WriterContracts.Receipt receipt) {
        public Publication { Objects.requireNonNull(predecessor);Objects.requireNonNull(receipt); }
    }
    public MercenaryDomainSource(List<ExactRef> sources) {
        this.sources=List.copyOf(sources);StrictJson.require(!this.sources.isEmpty()&&this.sources.size()<=64,"actual mercenary producer/codec/reducer sources required");
    }
    public synchronized void bindCore(RootApplicationAssembly.Core actual) {
        StrictJson.require(core==null,"mercenary domain Core link is once bound");core=Objects.requireNonNull(actual);
    }
    private synchronized RootApplicationAssembly.Core core() { StrictJson.require(core!=null,"actual mercenary Core is not bound");return core; }
    public synchronized DomainBodies.Registration registration() {
        if(registered!=null)return registered;
        registered=new DomainBodies.Registration(DomainBodies.Slot.MERCENARY,MercenaryProcurement.SCHEMA,MAX,sources,new DomainBodies.Verifier() {
            @Override public String verify(ContinuityState state,Optional<DomainBodies.BodyRef> prior,DomainBodies.ImportRequest request,byte[] original)throws IOException {
                throw new IOException("mercenary reducer requires the actual original Head, documents and borrowed Session");
            }
            @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> prior,DomainBodies.ImportRequest request,byte[] original)throws IOException {
                Session session=core().writer().borrowedSession();core().writer().requireSession(session);
                Transition producer=Objects.requireNonNull(active.get(),"only the actual scoped mercenary producer may import state");
                StrictJson.require(head.digest().equals(session.head().digest())&&request.slot()==DomainBodies.Slot.MERCENARY
                        &&request.contractSchema().equals(MercenaryProcurement.SCHEMA)&&Arrays.equals(request.producerInput(),canonicalInput(producer.input()))
                        &&request.evidence().equals(producer.evidence()),"mercenary import crossed its actual producer/predecessor/input/evidence");
                Optional<MercenaryProcurement.Ledger> previous=read(session,prior);
                byte[] derived=MercenaryProcurement.encode(producer.replay(session,previous));
                StrictJson.require(Arrays.equals(derived,original),"original mercenary reducer does not produce the proposed complete body");
                return ActionCodec.sha256(concat(head.digest(),request.producerInput(),derived));
            }
        });return registered;
    }
    public List<ExactRef> producerSources() { return sources; }
    public MercenaryProcurement.Ledger read(Session session)throws IOException {
        return read(session,DomainBodies.reference(session.head().state(),DomainBodies.Slot.MERCENARY))
                .orElseThrow(()->new IOException("original mercenary body is unimported; restore cannot initialize empty pending"));
    }
    private Optional<MercenaryProcurement.Ledger> read(Session session,Optional<DomainBodies.BodyRef> expected)throws IOException {
        core().writer().requireSession(session);var actual=session.readDomain(DomainBodies.Slot.MERCENARY);
        if(expected.isEmpty()) {
            StrictJson.require(actual instanceof DomainBodies.Unavailable unavailable&&unavailable.reason()==DomainBodies.Reason.UNIMPORTED,
                    "absence is only the actual unimported slot, not a bad source/body");return Optional.empty();
        }
        if(!(actual instanceof DomainBodies.Available available))throw new IOException("actual original mercenary domain body unavailable");
        var reference=available.reference();StrictJson.require(reference.equals(expected.orElseThrow())&&available.head().equals(session.persistedHead())
                &&reference.contractSchema().equals(MercenaryProcurement.SCHEMA),"mercenary original body/head/contract closure changed");
        for(var pin:available.headSources())session.verifyPin(pin);
        var pin=session.capturePin(reference.payload(),MAX);StrictJson.require(pin.identity().equals(reference.identity()),"mercenary native body identity changed");
        byte[] raw=session.readPinned(pin,MAX);StrictJson.require(CanonicalFinanceStateSource.sameOriginalBody(raw,available.canonicalBody(),MAX),"original mercenary body differs from current imported canonical body");
        session.verifyPin(pin);return Optional.of(MercenaryProcurement.decode(raw));
    }
    public Publication initializeFresh(RootRuntimeContext context,Session session,RootInitialEpisodeProof proof)throws IOException {
        Objects.requireNonNull(proof);proof.requireCurrent(session);
        return publish(session,new Fresh(context,proof)).orElseThrow(()->new IOException("fresh initialization did not publish the actual body"));
    }
    public Publication initializeFresh(RootRuntimeContext context,Session session,FreshCampaignContext actual)throws IOException {
        requireContext(context,session);Objects.requireNonNull(actual);
        StrictJson.require(actual.context()==context,"fresh campaign mercenary input crossed its actual context");
        actual.requireCurrent(session);actual.requireInitializationPredecessor(session,session.head());
        ExactRef basis=actual.preserveOriginal(session);
        return publish(session,new CampaignFresh(context,actual,basis)).orElseThrow(()->new IOException("fresh campaign mercenary initialization did not publish its actual body"));
    }
    public DomainBodies.BodyRef initializeNext(RootRuntimeContext context,Session same,RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
        requireContext(context,same);proof.requireCurrent(same,context);
        var original=DomainBodies.reference(same.head().state(),DomainBodies.Slot.MERCENARY);var retained=read(same,original).orElseThrow();
        Value existing=retained.original().get("episode_finance_basis_v2");
        if(existing instanceof Obj basis&&ref(proof.baselineMaterial().reference()).equals(basis.get("baseline_material"))
                &&ref(proof.currentSemantic().originalDriver()).equals(basis.get("current_driver"))) {
            StrictJson.require(new Text(proof.kind().name()).equals(basis.get("initialization_kind"))
                    &&ref(proof.savedSemantic().semantic()).equals(basis.get("original_saved_semantic"))
                    &&ref(proof.savedSemantic().originalDriver()).equals(basis.get("first_saved_driver"))
                    &&ref(proof.currentSemantic().semantic()).equals(basis.get("current_semantic"))
                    &&OrdinaryFinanceCollector.sourceFrame(proof.currentSemantic().frame()).equals(basis.get("current_frame")),"recorded finance initialization differs from actual original/current provenance");
            proof.requireCurrent(same,context);
            return DomainBodies.reference(same.head().state(),DomainBodies.Slot.MERCENARY).orElseThrow();
        }
        var cash=proof.read(same,context,context.finance().definitions().contract(FinanceReadContracts.Query.CASH),new Obj(java.util.Map.of()),proof.deadline());
        publish(same,new Next(context,proof,cash));proof.requireCurrent(same,context);
        return DomainBodies.reference(same.head().state(),DomainBodies.Slot.MERCENARY).orElseThrow(()->new IOException("actual next mercenary body was not imported"));
    }
    public Publication begin(RootRuntimeContext context,Session session,ActionCommand command,FinanceEvidenceArchive quotes)throws IOException {
        return publish(session,new Begin(context,command,quotes)).orElseThrow(()->new IOException("mercenary before-INTENT pending publication did not change state"));
    }
    public Optional<Publication> afterPlanning(RootRuntimeContext context,Session session,PlanningRequest request)throws IOException {
        requireContext(context,session);var previous=read(session);
        // No claim can gain an inventory observation; another Native capture only invalidates the original plan.
        if(previous.pending().isEmpty()&&previous.observed().isEmpty())return Optional.empty();
        Complete frame=context.collector().currentPlanning(session,request,request.deadline(),(original,lease)->lease.frame());
        return publish(session,new Inventory(context,request,NativeEffectEvidence.basis(frame)));
    }
    public Optional<Publication> afterExecution(RootRuntimeContext context,Session session,ActionReceipt actual)throws IOException {
        if(!actual.command().operation().equals(OrdinaryFinancePolicies.MERCENARY))return Optional.empty();
        var archive=core().archive().withSession(session);ExactRef reference=archive.receiptReferenceOf(actual);
        StrictJson.require(actual.equals(archive.loadReceipt(reference)),"original mercenary action receipt archive changed");
        return publish(session,new Outcome(context,reference));
    }
    private Optional<Publication> publish(Session session,Transition transition)throws IOException {
        core().writer().requireSession(session);StrictJson.require(active.get()==null,"mercenary producer cannot nest a domain import");
        WriterContracts.Head head=session.head();var previous=read(session,DomainBodies.reference(head.state(),DomainBodies.Slot.MERCENARY));
        byte[] next=MercenaryProcurement.encode(transition.replay(session,previous));
        StrictJson.require(next.length<=MAX,"original mercenary body exceeds the actual registered continuity domain bound");
        if(previous.isPresent()&&Arrays.equals(next,MercenaryProcurement.encode(previous.orElseThrow())))return Optional.empty();
        var archive=core().archive().withSession(session);RawJson raw=new RawJson(next);ExactRef body=archive.preserveMaterial(raw);
        StrictJson.require(raw.equals(archive.loadMaterial(body)),"original complete mercenary body archive readback changed");
        byte[] input=canonicalInput(transition.input());
        var request=new DomainBodies.ImportRequest(DomainBodies.Slot.MERCENARY,MercenaryProcurement.SCHEMA,body,input,transition.evidence(),
                "mercenary:"+ActionCodec.sha256(concat(head.digest(),input,next)));
        active.set(transition);
        try { var prepared=session.previewImport(request);var receipt=session.commitImport(prepared);return Optional.of(new Publication(head,receipt)); }
        finally { active.remove(); }
    }
    private sealed interface Transition permits Fresh,CampaignFresh,Next,Begin,Inventory,Outcome {
        RawJson input();List<ExactRef> evidence();MercenaryProcurement.Ledger replay(Session session,Optional<MercenaryProcurement.Ledger> previous)throws IOException;
    }
    private final class Next implements Transition {
        private final RootRuntimeContext context;private final RootApplicationAssembly.EpisodeDomainInitializationProof proof;
        private final RootNextEpisodeDomainReads.Captured<FinanceReadContracts.Packet> captured;
        private Next(RootRuntimeContext context,RootApplicationAssembly.EpisodeDomainInitializationProof proof,RootNextEpisodeDomainReads.Captured<FinanceReadContracts.Packet> captured) {this.context=context;this.proof=Objects.requireNonNull(proof);this.captured=Objects.requireNonNull(captured);}
        private DomainBodies.BodyRef gift() {try{return DomainBodies.reference(uncheckedSession().head().state(),DomainBodies.Slot.FACTION).orElseThrow(()->new IOException("actual old gift obligations unavailable"));}
            catch(IOException failure){throw new java.io.UncheckedIOException(failure);}}
        private DomainBodies.BodyRef originalDomain(DomainBodies.Slot slot) {try{return proof.oldDomain(slot);}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}}
        @Override public RawJson input() {return json(obj("kind",new Text("actual_episode_finance_initialization"),"initialization_kind",new Text(proof.kind().name()),"baseline_material",ref(proof.baselineMaterial().reference()),
                "parent_receipt",ref(context.archive().withSession(uncheckedSession()).receiptReferenceOf(proof.parent())),
                "original_baseline_mercenary_body",ref(originalDomain(DomainBodies.Slot.MERCENARY).payload()),"original_baseline_gift_body",ref(originalDomain(DomainBodies.Slot.FACTION).payload()),
                "saved_semantic",ref(proof.savedSemantic().semantic()),"saved_driver",ref(proof.savedSemantic().originalDriver()),
                "current_semantic",ref(proof.currentSemantic().semantic()),"current_driver",ref(proof.currentSemantic().originalDriver()),
                "retained_gift_body",ref(gift().payload()),"cash_source_proof",captured.sourceProof().<Value>map(MercenaryDomainSource::ref).orElse(Nil.INSTANCE),
                "before_frame",OrdinaryFinanceCollector.sourceFrame(proof.parent().command().before()),
                "original_saved_frame",OrdinaryFinanceCollector.sourceFrame(proof.savedSemantic().frame()),"current_frame",OrdinaryFinanceCollector.sourceFrame(proof.currentSemantic().frame())));}
        private Session uncheckedSession() {try{return context.borrowedSession();}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}}
        @Override public List<ExactRef> evidence() {var refs=new java.util.LinkedHashSet<ExactRef>(proof.savedSemantic().references());refs.add(proof.baselineMaterial().reference());
            refs.addAll(proof.currentSemantic().references());refs.add(context.archive().withSession(uncheckedSession()).receiptReferenceOf(proof.parent()));refs.add(gift().payload());captured.sourceProof().ifPresent(refs::add);refs.addAll(captured.semantic().references());
            refs.add(originalDomain(DomainBodies.Slot.MERCENARY).payload());refs.add(originalDomain(DomainBodies.Slot.FACTION).payload());
            if(captured.result() instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known)refs.add(known.originalReceipt());return List.copyOf(refs);}
        @Override public MercenaryProcurement.Ledger replay(Session same,Optional<MercenaryProcurement.Ledger> previous)throws IOException {
            requireContext(context,same);proof.requireCurrent(same,context);captured.requireOriginals(same,context,proof);
            var saved=proof.savedSemantic();context.semanticVerifier().verify(same,proof.baselineMaterial().session(),saved);
            var current=proof.currentSemantic();context.semanticVerifier().verify(same,proof.afterSession(),current);
            var snapshot=org.xar.ck3.control.application.driver.DriverJson.object(context.archive().readArtifact(same,saved.semantic(),RawJson.MAXIMUM_BYTES),RawJson.MAXIMUM_BYTES);
            var currentSnapshot=org.xar.ck3.control.application.driver.DriverJson.object(context.archive().readArtifact(same,current.semantic(),RawJson.MAXIMUM_BYTES),RawJson.MAXIMUM_BYTES);
            var oldGift=same.readDomain(DomainBodies.Slot.FACTION);StrictJson.require(oldGift instanceof DomainBodies.Available,"actual old gift obligations unreadable");
            var retained=(DomainBodies.Available)oldGift;StrictJson.require(retained.reference().equals(gift())&&retained.head().equals(same.persistedHead()),"old gift obligations crossed the actual locked head");
            var originalGift=proof.oldDomain(DomainBodies.Slot.FACTION);var giftPin=same.capturePin(originalGift.payload(),MAX);StrictJson.require(giftPin.identity().equals(originalGift.identity()),"original BASELINE gift file identity drift");
            StrictJson.require(CanonicalFinanceStateSource.sameOriginalBody(same.readPinned(giftPin,MAX),retained.canonicalBody(),MAX),"episode initialization must preserve the original BASELINE gift obligations");same.verifyPin(giftPin);
            org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec.decodeLedger(retained.canonicalBody());
            var before=MercenaryProcurement.fromObservation(proof.parent().command().before());var savedFrame=MercenaryProcurement.fromSnapshot(snapshot);var currentFrame=MercenaryProcurement.fromSnapshot(currentSnapshot);
            StrictJson.require(before.player().equals(proof.predecessorDriver().session().actorId())&&before.episodeId().equals(proof.predecessorDriver().session().episodeRunId())
                    &&savedFrame.player().equals(proof.firstSavedDriver().session().actorId())&&savedFrame.episodeId().equals(proof.firstSavedDriver().session().episodeRunId())
                    &&currentFrame.player().equals(proof.currentDriver().session().actorId())&&currentFrame.episodeId().equals(proof.currentDriver().session().episodeRunId()),
                    "finance actor/episode differs from original saved or actual current Driver owner");
            MercenaryProcurement.NextCash cash;
            if(captured.result() instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known) {
                var packet=context.finance().definitions().decodeOriginal(FinanceReadContracts.Query.CASH,known.receipt(),captured.frame().semantic());
                StrictJson.require(packet.originalResult().equals(known.value().originalResult()),"next current-cash packet changed after original capture");
                var raw=object(packet.result().get("war_cash_current_resources"),"actual next current native cash");
                var normalized=org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.normalize(org.xar.ck3.control.application.driver.DriverJson.encode(raw),org.xar.ck3.control.application.driver.DriverJson.encode(captured.frame().semantic()));
                cash=new MercenaryProcurement.NextCashObserved(normalized,known.originalReceipt(),captured.sourceProof());
            } else cash=new MercenaryProcurement.NextCashUnavailable(((PlanningReadResult.Unavailable<FinanceReadContracts.Packet>)captured.result()).reason(),captured.sourceProof());
            var origin=switch(proof.kind()){case NEXT->MercenaryProcurement.EpisodeOrigin.NEXT;case RESTORED_FIRST->MercenaryProcurement.EpisodeOrigin.RESTORED_FIRST;};
            return MercenaryProcurement.initializeEpisode(previous.orElseThrow(()->new IOException("episode finance has no original prior mercenary obligations")),
                    new MercenaryProcurement.EpisodeBasis(origin,before,savedFrame,currentFrame,snapshot,currentSnapshot,proof.baselineMaterial().reference(),saved.semantic(),saved.originalDriver(),
                            current.semantic(),current.originalDriver(),retained.reference().payload(),cash));
        }
    }
    private final class Fresh implements Transition {
        private final RootRuntimeContext context;private final RootInitialEpisodeProof proof;
        private Fresh(RootRuntimeContext context,RootInitialEpisodeProof proof) { this.context=context;this.proof=proof; }
        @Override public RawJson input() { return json(obj("kind",new Text("actual_fresh_gameplay_entry"),"episode",new Text(proof.episodeId()),"initial_frame",OrdinaryFinanceCollector.sourceFrame(proof.currentObservation()))); }
        @Override public List<ExactRef> evidence() { return proof.evidence(); }
        @Override public MercenaryProcurement.Ledger replay(Session session,Optional<MercenaryProcurement.Ledger> previous)throws IOException {
            requireContext(context,session);proof.requireCurrent(session);proof.requireInitializationPredecessor(session,session.head());StrictJson.require(previous.isEmpty()&&proof.source().equals(context.source())
                    &&proof.sessionId().equals(context.game().sessionId()),"fresh initial proof cannot replace an existing or prior-Game mercenary body");
            core().actions().withFrozen(session,lease->{StrictJson.require(lease.snapshot().actions().stream().allMatch(receipt->receipt.command().origin() instanceof CommandOrigin.Frontend&&receipt.settled()),
                    "fresh mercenary initialization requires no previous gameplay or unresolved action chain");lease.assertCurrent();return null;});
            return MercenaryProcurement.emptyFreshEpisode();
        }
    }
    /** Fresh-observed initialization keeps its own durable DATA schema and exact evidence. */
    private final class CampaignFresh implements Transition {
        private final RootRuntimeContext context;private final FreshCampaignContext actual;private final ExactRef basis;
        private CampaignFresh(RootRuntimeContext context,FreshCampaignContext actual,ExactRef basis) {
            this.context=context;this.actual=actual;this.basis=basis;
        }
        @Override public RawJson input() {return json(obj("kind",new Text("actual_fresh_campaign_mercenary_body"),
                "initial_basis",ref(basis),"episode",new Text(actual.episodeId()),"initial_frame",OrdinaryFinanceCollector.sourceFrame(actual.currentObservation())));}
        @Override public List<ExactRef> evidence() {var refs=new java.util.LinkedHashSet<ExactRef>(actual.evidence());refs.add(basis);return List.copyOf(refs);}
        @Override public MercenaryProcurement.Ledger replay(Session same,Optional<MercenaryProcurement.Ledger> previous)throws IOException {
            requireContext(context,same);actual.requireCurrent(same);actual.requireInitializationPredecessor(same,same.head());
            var original=FreshCampaignContext.replayOriginal(context,same,basis);original.requireInitializationPredecessor(same,same.head());
            StrictJson.require(previous.isEmpty()&&actual.context()==context&&original.source().equals(context.source())
                    &&original.sessionId().equals(context.game().sessionId())&&original.observation().equals(actual.currentObservation())
                    &&original.episodeId().equals(actual.episodeId())&&original.firstDriver().equals(actual.adopted().seed().fullDriver())
                    &&evidence().containsAll(original.evidence()),"fresh campaign mercenary body cannot replace existing obligations or cross its observed owner");
            core().actions().withFrozen(same,lease->{StrictJson.require(lease.snapshot().actions().stream().allMatch(receipt->receipt.command().origin() instanceof CommandOrigin.Frontend&&receipt.settled()),
                    "fresh campaign mercenary initialization requires no previous gameplay or unresolved action chain");lease.assertCurrent();return null;});
            return MercenaryProcurement.emptyFreshEpisode();
        }
    }
    private final class Begin implements Transition {
        private final RootRuntimeContext context;private final ActionCommand command;private final FinanceEvidenceArchive quotes;
        private Begin(RootRuntimeContext context,ActionCommand command,FinanceEvidenceArchive quotes) { this.context=context;this.command=command;this.quotes=quotes; }
        @Override public RawJson input() { return new RawJson(ActionCodec.encodeCommand(command)); }
        @Override public List<ExactRef> evidence() { return List.of(FinanceEvidenceArchive.reference(command.arguments())); }
        @Override public MercenaryProcurement.Ledger replay(Session session,Optional<MercenaryProcurement.Ledger> previous)throws IOException {
            requireContext(context,session);quotes.verify(session,command);
            core().actions().withFrozen(session,lease->{StrictJson.require(lease.find(command.actionId()).isEmpty(),"original mercenary INTENT already exists; no new pending may be created");lease.assertCurrent();return null;});
            context.collector().current(session,command.before(),command.deadline(),lease->{
                StrictJson.require(lease.frame().identity().equals(command.before())&&lease.frame().source().equals(command.source())
                        &&lease.frame().sessionId().equals(command.sessionId()),"before-INTENT current mercenary frame drift");return null;});
            return MercenaryProcurement.begin(previous.orElseThrow(()->new IOException("actual mercenary body missing before INTENT")),command);
        }
    }
    private final class Inventory implements Transition {
        private final RootRuntimeContext context;private final PlanningRequest request;private final NativeEffectEvidence.FrameBasis basis;
        private Inventory(RootRuntimeContext context,PlanningRequest request,NativeEffectEvidence.FrameBasis basis) { this.context=context;this.request=request;this.basis=basis; }
        @Override public RawJson input() { return json(obj("kind",new Text("independent_original_player_inventory"),"native_frame",ref(basis.nativeFrame()),"driver_facts",ref(basis.driverFacts()))); }
        @Override public List<ExactRef> evidence() { return List.of(basis.nativeFrame(),basis.driverFacts()); }
        @Override public MercenaryProcurement.Ledger replay(Session session,Optional<MercenaryProcurement.Ledger> previous)throws IOException {
            requireContext(context,session);Complete frame=core().frameLoader().load(basis,core().archive().withSession(session));
            StrictJson.require(frame.identity().equals(request.before())
                    &&frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId()),"original inventory frame crossed actual current source/Game/session");
            context.collector().currentPlanning(session,request,request.deadline(),(original,lease)->{StrictJson.require(lease.frame().identity().equals(frame.identity()),"inventory no longer current inside writer");return null;});
            return MercenaryProcurement.refreshInventory(previous.orElseThrow(()->new IOException("original mercenary body absent")),frame.semantic());
        }
    }
    private final class Outcome implements Transition {
        private final RootRuntimeContext context;private final ExactRef receiptRef;
        private Outcome(RootRuntimeContext context,ExactRef receiptRef) { this.context=context;this.receiptRef=receiptRef; }
        @Override public RawJson input() { return json(obj("kind",new Text("original_mercenary_action_outcome"),"receipt",ref(receiptRef))); }
        @Override public List<ExactRef> evidence() { return List.of(receiptRef); }
        @Override public MercenaryProcurement.Ledger replay(Session session,Optional<MercenaryProcurement.Ledger> previous)throws IOException {
            requireContext(context,session);var archive=core().archive().withSession(session);ActionReceipt receipt=archive.loadReceipt(receiptRef);
            StrictJson.require(receiptRef.equals(archive.receiptReferenceOf(receipt))&&receipt.command().operation().equals(OrdinaryFinancePolicies.MERCENARY),"original mercenary outcome receipt identity/operation changed");
            ActionReceipt canonical=core().actions().withFrozen(session,lease->{var original=lease.find(receipt.command().actionId()).orElseThrow();lease.assertCurrent();return original;});
            StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(receipt,archive),ActionReceiptCodec.encodeReceipt(canonical,archive)),"outcome is outside the actual canonical action chain");
            MercenaryProcurement.Ledger ledger=previous.orElseThrow(()->new IOException("original mercenary pending body absent"));
            if(ledger.pending().isEmpty())return ledger;
            String requestId=RequestIds.forActionBody(receipt.bodySha256());
            StrictJson.require(ledger.pending().orElseThrow().requestId().equals(requestId),"canonical action differs from the unresolved mercenary request");
            if(receipt.state() instanceof ActionState.RejectedBeforeDispatch rejected) {
                var dispatch=rejected.dispatch();var reference=archive.referenceOf(dispatch);
                StrictJson.require(dispatch.requestId().equals(requestId)&&dispatch.proof().stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                        &&dispatch.proof().requestBytesWritten()==0&&dispatch.equals(archive.load(reference)),"canonical mercenary zero-dispatch proof is unavailable or changed");
                RootGuardEvidence.loadFrame(rejected.attempt().guard(),archive,core().frameLoader());
                return MercenaryProcurement.rejectBeforeDispatch(ledger,requestId,new MercenaryProcurement.ZeroDispatchEvidence(reference,dispatch.proof()));
            }
            var attempt=attempt(receipt.state());
            if(attempt.isPresent()&&receipt.ack().isPresent()) {
                Complete before=RootGuardEvidence.loadFrame(attempt.orElseThrow().guard(),archive,core().frameLoader());
                ledger=MercenaryProcurement.acknowledge(ledger,requestId,HireMercenaryAck.decode(receipt.command(),attempt.orElseThrow(),receipt.ack().orElseThrow(),before));
            }
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Applied) {
                context.bindings().actualArchivedVerifier(receipt.command().operation()).orElseThrow().verifier().verify(session.head(),receipt,archive);
                var original=NativeEffectEvidence.load(receipt,archive,core().frameLoader());
                StrictJson.require(original.independentReads().size()==1,"actual employment material has exactly its original market read");
                var read=original.independentReads().getFirst();Complete after=original.frames().after();
                var packet=context.finance().definitions().decodeOriginal(FinanceReadContracts.Query.MERCENARIES,read,after.semantic());
                var market=NativeMercenaryMarket.decode(packet,after.identity(),after.source(),after.sessionId(),after.semantic());
                if(ledger.pending().isPresent())ledger=MercenaryProcurement.observeEmployment(ledger,requestId,after.semantic(),market);
            }
            return ledger;
        }
    }
    private void requireContext(RootRuntimeContext context,Session session)throws IOException {
        StrictJson.require(context.core()==core()&&context.borrowedSession()==session,"mercenary producer must retain its actual Core and unique writer Session");
        core().writer().requireSession(session);context.game().verify();
    }
    private static Optional<ActionState.Attempt> attempt(ActionState state) {
        if(state instanceof ActionState.AckReceived value)return Optional.of(value.attempt());
        if(state instanceof ActionState.Settled value)return Optional.of(value.attempt());
        if(state instanceof ActionState.Unknown value)return value.attempt();return Optional.empty();
    }
    private static RawJson json(Obj value) { return new RawJson(encode(value)); }
    static byte[] canonicalInput(RawJson input) { return WriterContracts.canonical(input.bytes()); }
    private static Obj ref(ExactRef value) { return object(parse(StrictJson.canonical(value.toJson())),"actual original reference"); }
    private static byte[] concat(String head,byte[] input,byte[] output) {
        byte[] prefix=head.getBytes(java.nio.charset.StandardCharsets.US_ASCII);byte[] result=new byte[prefix.length+input.length+output.length];
        System.arraycopy(prefix,0,result,0,prefix.length);System.arraycopy(input,0,result,prefix.length,input.length);System.arraycopy(output,0,result,prefix.length+input.length,output.length);return result;
    }
}
