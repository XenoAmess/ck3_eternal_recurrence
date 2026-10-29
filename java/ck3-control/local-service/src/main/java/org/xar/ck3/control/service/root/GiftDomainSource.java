package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.wave2.finance.giftpending.*;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.*;

/** Explicit new Java owner of Slot.FACTION for the original full GiftPendingCodec contract; no name-based inference. */
public final class GiftDomainSource {
    public record PendingFrameSource(String targetRelative,Class<?> actualClass) {
        public PendingFrameSource {StrictJson.text(targetRelative);Objects.requireNonNull(actualClass);}
    }
    /** Actual public product registration enrolls these exact selected sources before the Core is frozen. */
    public static List<PendingFrameSource> pendingFrameSourceTypes() {
        return List.of(
                new PendingFrameSource("local-service/src/main/java/org/xar/ck3/control/service/root/GiftDomainSource.java",GiftDomainSource.class),
                new PendingFrameSource("local-service/src/main/java/org/xar/ck3/control/service/root/FinanceRuntimeInstaller.java",FinanceRuntimeInstaller.class),
                new PendingFrameSource("local-service/src/main/java/org/xar/ck3/control/service/root/GiftPendingFrameWaitSource.java",GiftPendingFrameWaitSource.class),
                new PendingFrameSource("application/src/main/java/org/xar/ck3/control/service/root/GiftPendingFrameReadyFailure.java",GiftPendingFrameReadyFailure.class),
                new PendingFrameSource("wave2-finance/src/main/java/org/xar/ck3/control/wave2/finance/giftpendingframe/GiftPendingFramePolicy.java",org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy.class),
                new PendingFrameSource("wave2-finance/src/main/java/org/xar/ck3/control/wave2/finance/giftpendingframe/GiftPendingFrameCodec.java",org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFrameCodec.class));
    }
    private static final int MAX=ContinuityJson.DOMAIN_MAX_BYTES;
    private final List<ExactRef> sources;private RootApplicationAssembly.Core core;
    private DomainBodies.Registration registered;
    private final ThreadLocal<Transition> active=new ThreadLocal<>();
    public GiftDomainSource(List<ExactRef> sources) { this.sources=List.copyOf(sources);StrictJson.require(!this.sources.isEmpty(),"actual gift producer/codec/reducer sources required"); }
    public synchronized void bindCore(RootApplicationAssembly.Core actual) { StrictJson.require(core==null,"gift Core is once bound");core=Objects.requireNonNull(actual); }
    private synchronized RootApplicationAssembly.Core core() { StrictJson.require(core!=null,"actual gift Core unbound");return core; }
    public List<ExactRef> producerSources() { return sources; }
    public synchronized DomainBodies.Registration registration() {
        if(registered!=null)return registered;
        registered=new DomainBodies.Registration(DomainBodies.Slot.FACTION,GiftPendingModel.SCHEMA,MAX,sources,new DomainBodies.Verifier() {
            @Override public String verify(ContinuityState head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] raw)throws IOException {
                throw new IOException("gift requires the actual full original Head and live original writer Session");
            }
            @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] raw)throws IOException {
                Session session=core().writer().borrowedSession();core().writer().requireSession(session);
                Transition producer=Objects.requireNonNull(active.get(),"gift import must be issued by its actual scoped producer");
                StrictJson.require(head.digest().equals(session.head().digest())&&request.slot()==DomainBodies.Slot.FACTION
                        &&request.contractSchema().equals(GiftPendingModel.SCHEMA)&&Arrays.equals(request.producerInput(),canonicalInput(producer.input()))
                        &&request.evidence().equals(producer.evidence()),"gift import crossed its original head/input/evidence");
                byte[] expected=GiftPendingCodec.encodeLedger(producer.replay(session,read(session,previous)));
                StrictJson.require(Arrays.equals(expected,raw),"actual original GiftPendingReducer does not produce the proposed complete body");
                return digest(head.digest(),request.producerInput(),raw);
            }
        });return registered;
    }
    public Ledger read(Session session)throws IOException {
        return read(session,DomainBodies.reference(session.head().state(),DomainBodies.Slot.FACTION)).orElseThrow(()->new IOException("actual full faction-gift body absent; restore never assumes empty"));
    }
    private Optional<Ledger> read(Session session,Optional<DomainBodies.BodyRef> expected)throws IOException {
        core().writer().requireSession(session);var actual=session.readDomain(DomainBodies.Slot.FACTION);
        if(expected.isEmpty()) {
            StrictJson.require(actual instanceof DomainBodies.Unavailable unavailable&&unavailable.reason()==DomainBodies.Reason.UNIMPORTED,"missing gift slot is not bad/missing source or body");return Optional.empty();
        }
        if(!(actual instanceof DomainBodies.Available body))throw new IOException("actual original faction-gift body unavailable");
        StrictJson.require(body.reference().equals(expected.orElseThrow())
                &&body.reference().contractSchema().equals(GiftPendingModel.SCHEMA)&&body.head().equals(session.persistedHead()),"original full gift body/head/contract changed");
        for(var pin:body.headSources())session.verifyPin(pin);var pin=session.capturePin(body.reference().payload(),MAX);
        StrictJson.require(pin.identity().equals(body.reference().identity()),"gift original native identity changed");byte[] raw=session.readPinned(pin,MAX);
        StrictJson.require(CanonicalFinanceStateSource.sameOriginalBody(raw,body.canonicalBody(),MAX),"gift imported body differs from original bytes");
        session.verifyPin(pin);return Optional.of(GiftPendingCodec.decodeLedger(raw));
    }
    public MercenaryDomainSource.Publication initializeFresh(RootRuntimeContext context,Session session,RootInitialEpisodeProof proof)throws IOException {
        return publish(session,new Fresh(context,proof)).orElseThrow(()->new IOException("fresh gift body did not publish"));
    }
    public MercenaryDomainSource.Publication initializeFresh(RootRuntimeContext context,Session session,FreshCampaignContext actual)throws IOException {
        requireContext(context,session);Objects.requireNonNull(actual);
        StrictJson.require(actual.context()==context,"fresh campaign gift input crossed its actual context");
        actual.requireCurrent(session);actual.requireInitializationPredecessor(session,session.head());
        ExactRef basis=actual.preserveOriginal(session);
        return publish(session,new CampaignFresh(context,actual,basis)).orElseThrow(()->new IOException("fresh campaign gift initialization did not publish its actual body"));
    }
    public DomainBodies.BodyRef initializeNext(RootRuntimeContext context,Session same,RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
        proof.requireCurrent(same,context);publish(same,new Next(context,proof));proof.requireCurrent(same,context);
        return DomainBodies.reference(same.head().state(),DomainBodies.Slot.FACTION).orElseThrow(()->new IOException("actual next gift body was not imported"));
    }
    public MercenaryDomainSource.Publication begin(RootRuntimeContext context,Session session,ActionCommand command,FinanceEvidenceArchive quotes)throws IOException {
        return publish(session,new Begin(context,command,quotes)).orElseThrow(()->new IOException("actual gift pending did not publish before INTENT"));
    }
    public Optional<MercenaryDomainSource.Publication> afterExecution(RootRuntimeContext context,Session session,ActionReceipt actual)throws IOException {
        if(!actual.command().operation().equals(OrdinaryFinancePolicies.GIFT))return Optional.empty();
        var archive=core().archive().withSession(session);var ref=archive.receiptReferenceOf(actual);
        StrictJson.require(actual.equals(archive.loadReceipt(ref)),"actual gift receipt archive readback differs");return publish(session,new Outcome(context,ref));
    }
    public Optional<MercenaryDomainSource.Publication> markReplacedProcess(RootRuntimeContext context,Session session)throws IOException {
        Ledger previous=read(session);if(previous.pending().isEmpty()||CanonicalGiftColdProvider.sameProcess(previous.pending().orElseThrow(),context.game().generation()))return Optional.empty();
        return publish(session,new Replaced(context));
    }
    private Optional<MercenaryDomainSource.Publication> publish(Session session,Transition transition)throws IOException {
        core().writer().requireSession(session);StrictJson.require(active.get()==null,"gift producer cannot nest an import");
        var head=session.head();var previous=read(session,DomainBodies.reference(head.state(),DomainBodies.Slot.FACTION));
        byte[] next=GiftPendingCodec.encodeLedger(transition.replay(session,previous));
        StrictJson.require(next.length<=MAX,"original gift body exceeds the actual registered continuity domain bound");
        if(previous.isPresent()&&Arrays.equals(next,GiftPendingCodec.encodeLedger(previous.orElseThrow())))return Optional.empty();
        var archive=core().archive().withSession(session);var raw=new RawJson(next);var body=archive.preserveMaterial(raw);
        StrictJson.require(raw.equals(archive.loadMaterial(body)),"actual full gift body archive readback changed");
        byte[] input=canonicalInput(transition.input());
        var request=new DomainBodies.ImportRequest(DomainBodies.Slot.FACTION,GiftPendingModel.SCHEMA,body,input,transition.evidence(),"gift:"+digest(head.digest(),input,next));
        active.set(transition);try { var prepared=session.previewImport(request);return Optional.of(new MercenaryDomainSource.Publication(head,session.commitImport(prepared))); }
        finally { active.remove(); }
    }
    public sealed interface ColdPlanning permits ColdNotRequired,ColdReadOnly,ColdClassified { }
    public record ColdNotRequired() implements ColdPlanning { }
    public record ColdReadOnly(String reason) implements ColdPlanning { }
    public record ColdClassified(Optional<MercenaryDomainSource.Publication> publication) implements ColdPlanning {
        public ColdClassified { publication=Objects.requireNonNull(publication); }
    }
    public ColdPlanning afterPlanningCold(RootRuntimeContext context,Session session,org.xar.ck3.control.application.planning.PlanningRequest original,
            CanonicalGiftColdProvider provider)throws IOException {
        Ledger ledger=read(session);
        if(ledger.pending().isEmpty()||CanonicalGiftColdProvider.sameProcess(ledger.pending().orElseThrow(),context.game().generation()))return new ColdNotRequired();
        CanonicalGiftColdProvider.Read observed;
        try { observed=provider.observe(session,original,ledger.pending().orElseThrow()); }
        catch(IOException unavailable) { return new ColdReadOnly("actual cold Gift source unavailable: "+unavailable.getMessage()); }
        return switch(observed) {
            case CanonicalGiftColdProvider.AwaitingCanonical waiting -> new ColdReadOnly("independent Gift read awaits canonical READ publication: "+waiting.originalReceipt().sha256());
            case CanonicalGiftColdProvider.Unavailable unavailable -> new ColdReadOnly(unavailable.reason());
            case CanonicalGiftColdProvider.Ready ready -> new ColdClassified(publish(session,new Cold(context,provider,ready)));
        };
    }
    /** Capture only inside the collector's real complete public callback; the opaque result performs no I/O yet. */
    public Optional<PendingFrameWait> preparePendingFrame(RootRuntimeContext context,Session same,
            org.xar.ck3.control.application.planning.PlanningRequest original,
            org.xar.ck3.control.application.readiness.NativeReadinessCollector.PublicPlanningObservation observed)throws IOException {
        requireContext(context,same);Objects.requireNonNull(original);Objects.requireNonNull(observed).assertCurrent(same);
        var actual=observed.frame();
        StrictJson.require(actual.joined() instanceof org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete,
                "Gift pending capture requires the actual full current native/Driver/player join");
        var complete=(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete)actual.joined();
        StrictJson.require(complete.identity().equals(original.before())&&complete.source().equals(original.source())
                &&complete.sessionId().equals(original.sessionId())&&complete.semantic().equals(original.observations().snapshot())
                &&original.source().equals(context.source())&&original.sessionId().equals(context.game().sessionId())
                &&original.before().game().equals(context.game().generation()),"Gift pending capture crossed its actual original public request");
        Ledger ledger=read(same);if(ledger.pending().isEmpty())return Optional.empty();
        PendingAction pending=ledger.pending().orElseThrow();
        if(GiftProcessIdentity.compare(pending.sourceProcess(),context.game().generation())!=GiftProcessIdentity.Relation.SAME)return Optional.empty();
        var source=GiftPendingFrameWaitSource.frame(complete.semantic());
        if(source.nativeRevision().compareTo(pending.baseline().nativeSnapshotRevision())>0)return Optional.empty();
        org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy.requireWaitSource(pending,source);
        var body=DomainBodies.reference(same.head().state(),DomainBodies.Slot.FACTION).orElseThrow();
        var pins=new java.util.ArrayList<WriterContracts.Pin>();
        for(ExactRef ref:List.of(body.payload(),actual.originalHello(),actual.originalHeartbeat(),
                actual.originalDriver(),actual.snapshot().originalEvidence()))pins.add(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
        if(actual.originalSourceProof().isPresent())pins.add(same.capturePin(actual.originalSourceProof().orElseThrow(),WriterContracts.MAX_PIN_BYTES));
        actual.assertCurrent(same);for(var pin:pins)same.verifyPin(pin);
        String head=same.head().digest();
        var wait=new GiftPendingFrameWaitSource(context,original,pending,source,actual.snapshot().actual(),List.copyOf(pins),current->{
            requireContext(context,current);
            StrictJson.require(current.head().digest().equals(head)
                    &&DomainBodies.reference(current.head().state(),DomainBodies.Slot.FACTION).filter(body::equals).isPresent()
                    &&read(current).pending().filter(pending::equals).isPresent()
                    &&GiftProcessIdentity.compare(pending.sourceProcess(),context.game().generation())==GiftProcessIdentity.Relation.SAME,
                    "Gift bounded wait lost its actual original writer/head/pending/process");
        },head);
        return Optional.of(new PendingFrameWait(wait));
    }
    /** Only the real current producer above creates this token; copied PendingAction/Frame DATA cannot start a wait. */
    public static final class PendingFrameWait {
        private final GiftPendingFrameWaitSource actual;
        private PendingFrameWait(GiftPendingFrameWaitSource actual) {this.actual=Objects.requireNonNull(actual);}
        public void afterPlanning(org.xar.ck3.control.application.planning.PlanningResult planned)throws IOException,InterruptedException {
            actual.afterPlanning(planned);
        }
    }
    private sealed interface Transition permits Fresh,CampaignFresh,Next,Begin,Outcome,Replaced,Cold {
        RawJson input();List<ExactRef> evidence();Ledger replay(Session session,Optional<Ledger> previous)throws IOException;
    }
    private final class Next implements Transition {
        private final RootRuntimeContext context;private final RootApplicationAssembly.EpisodeDomainInitializationProof proof;
        private Next(RootRuntimeContext context,RootApplicationAssembly.EpisodeDomainInitializationProof proof){this.context=context;this.proof=Objects.requireNonNull(proof);}
        private DomainBodies.BodyRef finance() {
            try {return DomainBodies.reference(context.borrowedSession().head().state(),DomainBodies.Slot.MERCENARY).orElseThrow(()->new IOException("actual next finance baseline body unavailable"));}
            catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
        }
        @Override public RawJson input(){return json(obj("kind",new Text("actual_episode_gift_carry"),"initialization_kind",new Text(proof.kind().name()),"baseline_material",ref(proof.baselineMaterial().reference()),
                "original_saved_semantic",ref(proof.savedSemantic().semantic()),"current_semantic",ref(proof.currentSemantic().semantic()),"finance_baseline_body",ref(finance().payload()),
                "old_frame",OrdinaryFinanceCollector.sourceFrame(proof.parent().command().before()),"current_frame",OrdinaryFinanceCollector.sourceFrame(proof.currentSemantic().frame())));}
        @Override public List<ExactRef> evidence(){var refs=new java.util.LinkedHashSet<ExactRef>(proof.savedSemantic().references());refs.addAll(proof.currentSemantic().references());refs.add(proof.baselineMaterial().reference());refs.add(finance().payload());return List.copyOf(refs);}
        @Override public Ledger replay(Session same,Optional<Ledger> previous)throws IOException {
            requireContext(context,same);proof.requireCurrent(same,context);
            var actual=same.readDomain(DomainBodies.Slot.MERCENARY);
            StrictJson.require(actual instanceof DomainBodies.Available,"actual new-episode finance baseline is unavailable");
            var body=(DomainBodies.Available)actual;
            StrictJson.require(body.reference().equals(finance())&&body.head().equals(same.persistedHead()),"new finance baseline body crossed the original current writer head");
            Obj basis=object(MercenaryProcurement.decode(body.canonicalBody()).original().get("episode_finance_basis_v2"),"actual episode finance baseline");
            StrictJson.require(ref(proof.baselineMaterial().reference()).equals(basis.get("baseline_material"))
                    &&new Text(proof.kind().name()).equals(basis.get("initialization_kind"))
                    &&ref(proof.savedSemantic().semantic()).equals(basis.get("original_saved_semantic"))
                    &&ref(proof.currentSemantic().semantic()).equals(basis.get("current_semantic"))
                    &&OrdinaryFinanceCollector.sourceFrame(proof.currentSemantic().frame()).equals(basis.get("current_frame"))
                    &&ref(DomainBodies.reference(same.head().state(),DomainBodies.Slot.FACTION).orElseThrow().payload()).equals(basis.get("retained_gift_obligations"))
                    &&new IntegerValue(BigInteger.ZERO).equals(basis.get("funding_credited_raw")),"gift carry cannot adopt a foreign or credited finance baseline");
            // The v1 ledger retains its exact old request/actor/episode and every retired identity. NEXT is not settlement.
            return previous.orElseThrow(()->new IOException("next episode has no original gift obligations; absence cannot mean clear"));
        }
    }
    private final class Fresh implements Transition {
        private final RootRuntimeContext context;private final RootInitialEpisodeProof proof;
        private Fresh(RootRuntimeContext context,RootInitialEpisodeProof proof) { this.context=context;this.proof=Objects.requireNonNull(proof); }
        @Override public RawJson input() { return json(obj("kind",new Text("actual_initial_gift_body"),"episode",new Text(proof.episodeId()),"initial_frame",OrdinaryFinanceCollector.sourceFrame(proof.currentObservation()))); }
        @Override public List<ExactRef> evidence() { return proof.evidence(); }
        @Override public Ledger replay(Session session,Optional<Ledger> previous)throws IOException {
            requireContext(context,session);proof.requireCurrent(session);proof.requireInitializationPredecessor(session,session.head());StrictJson.require(previous.isEmpty()&&proof.source().equals(context.source())
                    &&proof.sessionId().equals(context.game().sessionId()),"fresh gift initialization cannot erase existing or prior-Game state");
            core().actions().withFrozen(session,lease->{StrictJson.require(lease.snapshot().actions().stream().allMatch(receipt->receipt.command().origin() instanceof CommandOrigin.Frontend&&receipt.settled()),
                    "fresh gift initialization requires no previous gameplay or unresolved action chain");lease.assertCurrent();return null;});return Ledger.empty();
        }
    }
    /** Fresh-observed initialization keeps its own durable DATA schema and exact evidence. */
    private final class CampaignFresh implements Transition {
        private final RootRuntimeContext context;private final FreshCampaignContext actual;private final ExactRef basis;
        private CampaignFresh(RootRuntimeContext context,FreshCampaignContext actual,ExactRef basis) {
            this.context=context;this.actual=actual;this.basis=basis;
        }
        @Override public RawJson input() {return json(obj("kind",new Text("actual_fresh_campaign_gift_body"),
                "initial_basis",ref(basis),"episode",new Text(actual.episodeId()),"initial_frame",OrdinaryFinanceCollector.sourceFrame(actual.currentObservation())));}
        @Override public List<ExactRef> evidence() {var refs=new java.util.LinkedHashSet<ExactRef>(actual.evidence());refs.add(basis);return List.copyOf(refs);}
        @Override public Ledger replay(Session same,Optional<Ledger> previous)throws IOException {
            requireContext(context,same);actual.requireCurrent(same);actual.requireInitializationPredecessor(same,same.head());
            var original=FreshCampaignContext.replayOriginal(context,same,basis);original.requireInitializationPredecessor(same,same.head());
            StrictJson.require(previous.isEmpty()&&actual.context()==context&&original.source().equals(context.source())
                    &&original.sessionId().equals(context.game().sessionId())&&original.observation().equals(actual.currentObservation())
                    &&original.episodeId().equals(actual.episodeId())&&original.firstDriver().equals(actual.adopted().seed().fullDriver())
                    &&evidence().containsAll(original.evidence()),"fresh campaign gift body cannot replace existing obligations or cross its observed owner");
            core().actions().withFrozen(same,lease->{StrictJson.require(lease.snapshot().actions().stream().allMatch(receipt->receipt.command().origin() instanceof CommandOrigin.Frontend&&receipt.settled()),
                    "fresh campaign gift initialization requires no previous gameplay or unresolved action chain");lease.assertCurrent();return null;});
            return Ledger.empty();
        }
    }
    private final class Begin implements Transition {
        private final RootRuntimeContext context;private final ActionCommand command;private final FinanceEvidenceArchive quotes;
        private Begin(RootRuntimeContext context,ActionCommand command,FinanceEvidenceArchive quotes) { this.context=context;this.command=command;this.quotes=quotes; }
        @Override public RawJson input() { return new RawJson(ActionCodec.encodeCommand(command)); }
        @Override public List<ExactRef> evidence() { return List.of(FinanceEvidenceArchive.reference(command.arguments())); }
        @Override public Ledger replay(Session session,Optional<Ledger> previous)throws IOException {
            requireContext(context,session);StrictJson.require(command.operation().equals(OrdinaryFinancePolicies.GIFT)&&command.before().game().equals(context.game().generation())
                    &&command.source().equals(context.source())&&command.sessionId().equals(context.game().sessionId()),"gift current source/Game/session differs");quotes.verify(session,command);
            core().actions().withFrozen(session,lease->{StrictJson.require(lease.find(command.actionId()).isEmpty(),"gift original INTENT exists; never re-create pending for retry");lease.assertCurrent();return null;});
            var original=quotes.originalRequest(session,command);context.collector().currentPlanning(session,original,command,command.deadline(),(request,lease)->null);
            var baseline=NativeFinanceEffects.giftBaseline(command.arguments());var minimum=integer(command.arguments().get("minimum_gold_reserve_raw"),"actual reserve");
            var begin=new BeginRequest(RequestIds.forActionBody(ActionCodec.bodySha256(command)),command.before().frame().episodeRunId(),
                    "R"+command.before().frame().revision(),process(context),baseline,minimum,text(command.arguments().get("checkpoint_sha256"),"actual pre-gift saved checkpoint"));
            return GiftPendingReducer.begin(previous.orElseThrow(()->new IOException("actual original gift body missing")),begin);
        }
    }
    private final class Outcome implements Transition {
        private final RootRuntimeContext context;private final ExactRef reference;
        private Outcome(RootRuntimeContext context,ExactRef reference) { this.context=context;this.reference=reference; }
        @Override public RawJson input() { return json(obj("kind",new Text("actual_original_gift_outcome"),"receipt",ref(reference))); }
        @Override public List<ExactRef> evidence() { return List.of(reference); }
        @Override public Ledger replay(Session session,Optional<Ledger> previous)throws IOException {
            requireContext(context,session);var archive=core().archive().withSession(session);ActionReceipt receipt=archive.loadReceipt(reference);
            StrictJson.require(reference.equals(archive.receiptReferenceOf(receipt))&&receipt.command().operation().equals(OrdinaryFinancePolicies.GIFT),"gift original receipt operation/identity changed");
            var canonical=core().actions().withFrozen(session,lease->{var actual=lease.find(receipt.command().actionId()).orElseThrow();lease.assertCurrent();return actual;});
            StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(receipt,archive),ActionReceiptCodec.encodeReceipt(canonical,archive)),"gift outcome is outside the original canonical action chain");
            Ledger ledger=previous.orElseThrow(()->new IOException("actual original gift body missing"));if(ledger.pending().isEmpty())return ledger;
            String id=RequestIds.forActionBody(receipt.bodySha256());GiftPendingReducer.matching(ledger,id);
            if(receipt.state() instanceof ActionState.RejectedBeforeDispatch rejected) {
                var dispatch=rejected.dispatch();var actualRef=archive.referenceOf(dispatch);
                StrictJson.require(dispatch.requestId().equals(id)&&dispatch.proof().stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                        &&dispatch.proof().requestBytesWritten()==0&&dispatch.equals(archive.load(actualRef)),"canonical gift zero-dispatch proof is unavailable or changed");
                RootGuardEvidence.loadFrame(rejected.attempt().guard(),archive,core().frameLoader());
                return GiftPendingReducer.rejectBeforeDispatch(ledger,id);
            }
            if(!CanonicalGiftColdProvider.sameProcess(ledger.pending().orElseThrow(),context.game().generation()))return GiftPendingReducer.markRestore(ledger,id);
            if(receipt.ack().isPresent()) {
                var submitted=GiftActionHistoryEvidence.decodeSubmission(receipt.ack().orElseThrow());
                ledger=GiftPendingReducer.markAck(ledger,id,submitted.ack());
            }
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Applied) {
                context.bindings().actualArchivedVerifier(receipt.command().operation()).orElseThrow().verifier().verify(session.head(),receipt,archive);
                var material=NativeEffectEvidence.load(receipt,archive,core().frameLoader());StrictJson.require(material.independentReads().size()==1,"gift material has its one original independent receipt query");
                var read=material.independentReads().getFirst();var packet=context.finance().definitions().decodeOriginal(FinanceReadContracts.Query.FACTION_GIFT_RECEIPT,read,material.frames().after().semantic());
                ledger=GiftPendingReducer.complete(ledger,id,GiftPendingCodec.decodeReceipt(encode(object(packet.result().get("receipt"),"actual independent gift receipt"))));
            }
            return ledger;
        }
    }
    private final class Replaced implements Transition {
        private final RootRuntimeContext context;private Replaced(RootRuntimeContext context) { this.context=context; }
        @Override public RawJson input() { return json(obj("kind",new Text("actual_replaced_gift_process"),"pid",new IntegerValue(process(context).pid()),"birth",new Text(process(context).creationDate()))); }
        @Override public List<ExactRef> evidence() { return List.of(context.source().sourceRef()); }
        @Override public Ledger replay(Session session,Optional<Ledger> previous)throws IOException {
            requireContext(context,session);Ledger ledger=previous.orElseThrow(()->new IOException("replaced process has no original gift body"));
            if(ledger.pending().isEmpty())return ledger;var pending=ledger.pending().orElseThrow();
            StrictJson.require(!CanonicalGiftColdProvider.sameProcess(pending,context.game().generation()),"same process cannot enter cold gift recovery");
            return GiftPendingReducer.markRestore(ledger,pending.requestId());
        }
    }
    private final class Cold implements Transition {
        private final RootRuntimeContext context;private final CanonicalGiftColdProvider provider;private final CanonicalGiftColdProvider.Ready ready;
        private Cold(RootRuntimeContext context,CanonicalGiftColdProvider provider,CanonicalGiftColdProvider.Ready ready) {
            this.context=context;this.provider=provider;this.ready=ready;
        }
        @Override public RawJson input() { return json(obj("kind",new Text("actual_canonical_gift_cold_read"),"original_read",ref(ready.originalRead()),"saved_material",ref(ready.originalSavedMaterial()))); }
        @Override public List<ExactRef> evidence() { return ready.evidence(); }
        @Override public Ledger replay(Session session,Optional<Ledger> previous)throws IOException {
            requireContext(context,session);Ledger ledger=previous.orElseThrow(()->new IOException("cold Gift has no actual previous full body"));
            var pending=ledger.pending().orElseThrow(()->new IOException("cold Gift has no original pending identity"));
            StrictJson.require(!CanonicalGiftColdProvider.sameProcess(pending,context.game().generation()),"same process cannot use cold Gift classification");
            return GiftColdRecovery.resolve(ledger,pending.requestId(),provider.verify(session,ready,pending)).ledger();
        }
    }
    private void requireContext(RootRuntimeContext context,Session session)throws IOException {
        StrictJson.require(context.core()==core()&&context.borrowedSession()==session,"gift producer requires its actual Core and original writer Session");core().writer().requireSession(session);context.game().verify();
    }
    /** Exact FILETIME to ISO UTC conversion retains all 100ns ticks; old legacy body birth spellings remain untouched. */
    private static ProcessIdentity process(RootRuntimeContext context) {
        return CanonicalGiftColdProvider.process(context.game().generation());
    }
    private static RawJson json(Obj value) { return new RawJson(encode(value)); }
    static byte[] canonicalInput(RawJson input) { return WriterContracts.canonical(input.bytes()); }
    private static Obj ref(ExactRef value) { return object(parse(StrictJson.canonical(value.toJson())),"actual original reference"); }
    private static String digest(String head,byte[] input,byte[] output) {
        byte[] prefix=head.getBytes(java.nio.charset.StandardCharsets.US_ASCII);byte[] joined=new byte[prefix.length+input.length+output.length];
        System.arraycopy(prefix,0,joined,0,prefix.length);System.arraycopy(input,0,joined,prefix.length,input.length);System.arraycopy(output,0,joined,prefix.length+input.length,output.length);return ActionCodec.sha256(joined);
    }
}
