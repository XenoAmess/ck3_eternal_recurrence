package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Concrete per-current-Game finance graph. The Prepared Core-level producer never retains a retired Game. */
public final class FinanceRuntimeInstaller {
    public record ReadSource(FinanceReadContracts.Query query,FinanceReadContracts.Registration registration) {
        public ReadSource { Objects.requireNonNull(query);Objects.requireNonNull(registration); }
    }
    public record GiftColdSources(FinanceReadContracts.Registration read,ExactRef readCodec,ExactRef classifier,
            ExactRef classifierCodec,ExactRef provider,ExactRef processIdentity) {
        public GiftColdSources {
            Objects.requireNonNull(read);
            for(var ref:List.of(readCodec,classifier,classifierCodec,provider,processIdentity))StrictJson.require(ref.bytes()>0,"actual selected cold Gift source required");
        }
    }
    public record Sources(OrdinaryFinanceFactory.Sources finance,ExactRef readCodec,ExactRef hireAckCodec,
            ExactRef domainSource,ExactRef domainReducer,ExactRef warPriority,
            ExactRef factionDefinition,ExactRef factionCodec,ExactRef giftDomainSource,ExactRef giftBodyCodec,ExactRef giftBodyReducer,List<ReadSource> readSources,
            List<CanonicalFinanceStateSource.Binding> externalBodyBindings,GiftColdSources giftCold) {
        public Sources {
            Objects.requireNonNull(finance);for(var ref:List.of(readCodec,hireAckCodec,domainSource,domainReducer,warPriority,factionDefinition,factionCodec,giftDomainSource,giftBodyCodec,giftBodyReducer))
                StrictJson.require(ref.bytes()>0,"selected actual finance producer/codec sources required");
            readSources=List.copyOf(readSources);externalBodyBindings=List.copyOf(externalBodyBindings);Objects.requireNonNull(giftCold);
            var queries=java.util.EnumSet.noneOf(FinanceReadContracts.Query.class);
            for(var source:readSources)StrictJson.require(queries.add(source.query()),"one selected original source per fixed finance query");
            StrictJson.require(queries.equals(java.util.EnumSet.of(FinanceReadContracts.Query.ROOT,FinanceReadContracts.Query.CASH,
                    FinanceReadContracts.Query.MERCENARIES,FinanceReadContracts.Query.CONSTRUCTION,FinanceReadContracts.Query.FACTION_GIFT,
                    FinanceReadContracts.Query.FACTION_GIFT_RECEIPT)),"exact fixed finance read inventory; M1 and Activity have their own single installed owners");
            StrictJson.require(externalBodyBindings.stream().noneMatch(binding->binding.decoder().domain()==FinanceStatePort.Domain.MERCENARY
                    ||binding.decoder().domain()==FinanceStatePort.Domain.FACTION_GIFT||binding.slot()==DomainBodies.Slot.MERCENARY||binding.slot()==DomainBodies.Slot.FACTION),"mercenary and faction-gift persistent producers are uniquely finance owned");
        }
    }
    public static final class Prepared {
        private final Sources sources;private final MercenaryDomainSource domain;private final GiftDomainSource gifts;private final FactionAlertReadService.Contracts factions;
        private RootApplicationAssembly.Core core;private CashObservationReads cashObservationReads;
        public Prepared(Sources sources) {
            this.sources=Objects.requireNonNull(sources);
            domain=new MercenaryDomainSource(List.of(sources.domainSource(),sources.domainReducer(),sources.hireAckCodec(),sources.warPriority()));
            gifts=new GiftDomainSource(List.of(sources.giftDomainSource(),sources.giftBodyCodec(),sources.giftBodyReducer(),
                    sources.giftCold().readCodec(),sources.giftCold().classifier(),sources.giftCold().classifierCodec(),sources.giftCold().provider(),sources.giftCold().processIdentity(),sources.domainReducer()));
            factions=new FactionAlertReadService.Contracts(sources.factionDefinition(),sources.factionCodec());
        }
        /** Public cash routes bind their single source-only family before the Core is minted. */
        public synchronized CashObservationReads bindCashObservationSources(CashObservationReads.Sources actual) {
            StrictJson.require(core==null&&cashObservationReads==null,"cash observation sources bind once before the actual Core");
            cashObservationReads=new CashObservationReads(Objects.requireNonNull(actual));return cashObservationReads;
        }
        public synchronized CashObservationReads cashObservationReads() {
            StrictJson.require(cashObservationReads!=null,"same prepared cash observation sources are not installed");return cashObservationReads;
        }
        public List<DomainBodies.Registration> registrations() { return List.of(domain.registration(),gifts.registration()); }
        /** The actual public PLAN callback captures an opaque Gift wait before its freeze exits; waiting happens afterwards. */
        public Optional<GiftDomainSource.PendingFrameWait> preparePendingFrame(RootRuntimeContext context,Session same,
                PlanningRequest original,org.xar.ck3.control.application.readiness.NativeReadinessCollector.PublicPlanningObservation observed)throws IOException {
            StrictJson.require(context.core()==core(),"Gift public planning capture crossed its actual installed finance Core");
            return gifts.preparePendingFrame(context,same,original,observed);
        }
        /** The public Faction route must consume this identical Contracts instance, never mint another family. */
        public FactionAlertReadService.Contracts factionContracts() { return factions; }
        public synchronized void bindCore(RootApplicationAssembly.Core actual) {
            StrictJson.require(core==null,"finance Prepared is bound once to the actual original Core");cashObservationReads();core=Objects.requireNonNull(actual);domain.bindCore(actual);gifts.bindCore(actual);
        }
        private synchronized RootApplicationAssembly.Core core() { StrictJson.require(core!=null,"finance actual Core is unbound");return core; }
        public List<MercenaryDomainSource.Publication> initializeFresh(RootRuntimeContext context,Session session,RootInitialEpisodeProof actual)throws IOException {
            StrictJson.require(context.core()==core(),"fresh finance initialization requires this actual Core");
            return List.of(domain.initializeFresh(context,session,actual),gifts.initializeFresh(context,session,actual));
        }
        /** Day-zero campaign bodies use their real observed input, without a historical startup/entry proof. */
        public List<MercenaryDomainSource.Publication> initializeFresh(RootRuntimeContext context,Session session,FreshCampaignContext actual)throws IOException {
            StrictJson.require(context.core()==core()&&Objects.requireNonNull(actual).context()==context,"fresh campaign finance initialization requires its actual Core/context");
            actual.requireCurrent(session);actual.requireInitializationPredecessor(session,session.head());
            var result=new ArrayList<MercenaryDomainSource.Publication>();
            var mercenaryRead=session.readDomain(DomainBodies.Slot.MERCENARY);
            if(mercenaryRead instanceof DomainBodies.Available) {
                domain.read(session);
            } else {
                StrictJson.require(mercenaryRead instanceof DomainBodies.Unavailable unavailable&&unavailable.reason()==DomainBodies.Reason.UNIMPORTED,"fresh campaign finance initialization cannot replace an imported or invalid mercenary body");
                var mercenary=domain.initializeFresh(context,session,actual);
                result.add(mercenary);
            }
            actual.requireCurrent(session);
            var giftRead=session.readDomain(DomainBodies.Slot.FACTION);
            if(giftRead instanceof DomainBodies.Available) {
                gifts.read(session);
            } else {
                StrictJson.require(giftRead instanceof DomainBodies.Unavailable unavailable&&unavailable.reason()==DomainBodies.Reason.UNIMPORTED,"fresh campaign finance initialization cannot replace an imported or invalid gift body");
                var gift=gifts.initializeFresh(context,session,actual);
                result.add(gift);
            }
            actual.requireCurrent(session);
            return List.copyOf(result);
        }
        /** Same frozen runtime's private NEXT or restored FIRST proof. Original pending actions keep their own identities. */
        public List<DomainBodies.BodyRef> initializeNext(RootRuntimeContext context,Session same,RootApplicationAssembly.EpisodeDomainInitializationProof actual)throws IOException {
            StrictJson.require(context.core()==core(),"next finance initialization crossed its actual Core");actual.requireCurrent(same,context);
            DomainBodies.BodyRef mercenary=domain.initializeNext(context,same,actual);actual.requireCurrent(same,context);
            DomainBodies.BodyRef gift=gifts.initializeNext(context,same,actual);actual.requireCurrent(same,context);
            StrictJson.require(DomainBodies.reference(same.head().state(),DomainBodies.Slot.MERCENARY).filter(mercenary::equals).isPresent()
                    &&DomainBodies.reference(same.head().state(),DomainBodies.Slot.FACTION).filter(gift::equals).isPresent(),"actual next finance body references drifted during same-lock initialization");
            return List.of(mercenary,gift);
        }
        /** Same actual preCore registrations and install-time read catalog; no wider leaf bound is inferred. */
        List<CanonicalFinanceStateSource.Binding> bodyBindings() {
            var bindings=new ArrayList<>(sources.externalBodyBindings());
            bindings.add(new CanonicalFinanceStateSource.Binding(new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.MERCENARY,sources.domainReducer(),
                    original->MercenaryProcurement.decode(original.bytes()).pending().isPresent()?FinanceStatePort.Pending.PENDING:FinanceStatePort.Pending.CLEAR),
                    DomainBodies.Slot.MERCENARY,MercenaryProcurement.SCHEMA,ContinuityJson.DOMAIN_MAX_BYTES,domain.producerSources()));
            bindings.add(new CanonicalFinanceStateSource.Binding(FinanceStatePort.giftReader(sources.giftBodyCodec()),DomainBodies.Slot.FACTION,
                    org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.SCHEMA,ContinuityJson.DOMAIN_MAX_BYTES,gifts.producerSources()));
            return List.copyOf(bindings);
        }
        /** Called anew for every physical Game. The exact Activity adapter is shared with governance ordinary/effects. */
        public RootDomainInstallation install(RootRuntimeContext context,GovernanceActivityRuntime activity,List<OrdinaryFinancePolicies.PendingContributor> actualPendingContributors)throws IOException {
            Objects.requireNonNull(activity);StrictJson.require(context.core()==core(),"finance installation crossed Core/writer");
            context.game().verify();
            var bodyBindings=bodyBindings();
            var originalWriter=new CanonicalFinanceStateSource(core().configuration().ledger().lock(),context.writer(),core().actions(),
                    (borrowed,request)->context.collector().current(borrowed,request.before(),request.deadline(),lease->lease.frame().identity()),
                    borrowed->checkpoint(context,borrowed),bodyBindings);
            var fixed=new EnumMap<FinanceReadContracts.Query,FinanceReadContracts.Registration>(FinanceReadContracts.Query.class);
            sources.readSources().forEach(source->fixed.put(source.query(),source.registration()));
            FinanceReadContracts.Registrations registrations=query->Objects.requireNonNull(fixed.get(query),"unselected fixed finance read");
            var alertAdapter=new FactionReads(context,factions,sources.factionDefinition());
            var quote=new AtomicReference<FinanceEvidenceArchive>();
            OrdinaryFinanceFactory.LockedCurrent current=(borrowed,command)->{
                FinanceEvidenceArchive exact=Objects.requireNonNull(quote.get(),"actual finance quote producer is not yet installed");
                PlanningRequest original=exact.originalRequest(borrowed,command);
                try { return context.collector().currentPlanning(borrowed,original,command,command.deadline(),(retained,lease)->retained); }
                catch(IOException failure) { throw new UncheckedIOException("actual quoted planning request is no longer current",failure); }
            };
            var snapshots=new NativeEffectSnapshots(()->context.adopted().observations(),context.archive(),context.frameLoader());
            var rootReads=new CanonicalRootReads(context);
            FinanceEvidenceArchive.HistoricalRootReplay historicalRoots=(same,originalRoot,targetGuard,targetFrame,archive)->{
                context.writer().requireSession(same);
                StrictJson.require(context.borrowedSession()==same,"historical finance ROOT escaped the actual held writer Session");
                org.xar.ck3.control.application.effects.RootGuardEvidence.requireHistory(targetGuard,archive,same);
                StrictJson.require(org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(targetGuard,archive,context.frameLoader()).equals(targetFrame),
                        "historical finance quote target lacks its exact original full native/Driver/SEM frame");
                var proof=context.readHistoryPublisher().requireHistoricalReadOnlyExtension(same,originalRoot,targetGuard,targetFrame).requireHistorical(same);
                StrictJson.require(proof.originalRead().equals(originalRoot)&&proof.originalReceipt().equals(archive.readReferenceOf(originalRoot))
                        &&proof.targetObserved().equals(targetFrame),"sole historical ROOT proof changed actual quote endpoints");
            };
            var installed=OrdinaryFinanceFactory.create(sources.finance(),registrations,originalWriter,context.writer(),rootReads,snapshots,context.frameLoader(),current,
                    List.copyOf(actualPendingContributors),context.archive(),()->borrowed(context),context.originals(),activity,alertAdapter,historicalRoots);
            quote.set(installed.quoteEvidence());
            var fundingPending=new CanonicalFundingPending(core().actions(),core().configuration().ledger().lock(),installed.state(),originalWriter.owningReaders(),
                    context::bindings,same->context.archive().withSession(same),context.game().generation(),context.source(),context.game().sessionId());
            var coldReads=new GiftColdReadService(sources.giftCold().read());
            var coldProvider=new CanonicalGiftColdProvider(context,coldReads);
            var publicGifts=new FactionGiftPublicService(context,installed.policies(),installed.reads(),gifts,coldReads,coldProvider);
            context.bindFinance(new FinanceRuntimeServices(context.game().generation(),context.game().sessionId(),context.source(),installed.reads(),installed.state(),installed.collector(),installed.policies(),rootReads,fundingPending,publicGifts));
            var actions=installed.effectBindings().stream().map(binding->new RootExecutableBindings.ActionBinding(binding,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,binding.operation().equals(OrdinaryFinancePolicies.MERCENARY)
                        ?Optional.of("game.command.hire-mercenary-v1"):Optional.empty(),
                    binding.operation().equals(OrdinaryFinancePolicies.MERCENARY)?sources.hireAckCodec():sources.finance().giftMaterial())).toList();
            var pending=new RootDomainIntentPreparation.Binding("ordinary-finance-before-intent-v2",sources.domainSource(),
                    command->command.operation().equals(OrdinaryFinancePolicies.MERCENARY)||command.operation().equals(OrdinaryFinancePolicies.GIFT),
                    (borrowed,command)->{
                        installed.intentPreparation().prepare(borrowed,command);
                        if(command.operation().equals(OrdinaryFinancePolicies.MERCENARY)) {
                            try { domain.begin(context,borrowed,command,installed.quoteEvidence()); }
                            catch(IOException failure) { throw new UncheckedIOException("actual unresolved mercenary pending was not durably published",failure); }
                        }
                        else {
                            try { gifts.begin(context,borrowed,command,installed.quoteEvidence()); }
                            catch(IOException failure) { throw new UncheckedIOException("actual unresolved gift pending was not durably published",failure); }
                        }
                    });
            var completion=new Completion(context,domain,gifts,coldProvider);
            var domains=actions.stream().map(binding->new RootDomainInstallation.FixedDomain(binding,
                    binding.effect().operation().equals(OrdinaryFinancePolicies.MERCENARY)?Domain.war:Domain.diplomacy)).toList();
            var allReads=new ArrayList<RootReadContractCatalog.InstalledRead>();
            installed.readContracts().forEach(contract->allReads.add(new RootReadContractCatalog.InstalledRead(contract,sources.readCodec())));
            allReads.add(new RootReadContractCatalog.InstalledRead(coldReads.contract(),sources.giftCold().readCodec()));
            var allFamilies=new ArrayList<RootReadContractCatalog.Family<?,?>>(factions.families());
            allFamilies.addAll(cashObservationReads().families());
            return new RootDomainInstallation("ordinary-finance-v3",registrations(),List.copyOf(allReads),List.copyOf(allFamilies),actions,List.of(),
                    installed.archivedVerifiers(),List.of(),List.of(),List.of(),List.of(pending),
                    Set.of(OrdinaryFinancePolicies.MERCENARY,OrdinaryFinancePolicies.GIFT),installed.stages(),List.of(completion),domains,List.of(),List.of());
        }
    }
    /** Only public ROOT opts into the publisher's actual committed originals. Other operations retain their existing read path. */
    private static final class CanonicalRootReads implements PlanningReadPort {
        private final RootRuntimeContext context;
        private CanonicalRootReads(RootRuntimeContext context){this.context=Objects.requireNonNull(context);}
        private static boolean publicRoot(ReadContract<?> contract,PlanningReadRequest request) {
            return contract.contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID)
                    &&contract.operation().equals(FinanceReadContracts.Query.ROOT.operation())
                    &&FinanceReadContracts.rootCapture(request.arguments())==FinanceReadContracts.RootCapture.PUBLIC_QUERY;
        }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            if(!publicRoot(contract,request))return context.reads().read(contract,request);
            try{return context.withSession(same->read(same,contract,request));}
            catch(IOException unavailable){return new PlanningReadResult.Unavailable<>("actual canonical ROOT originals unavailable: "+unavailable.getMessage(),Optional.empty());}
        }
        @Override public <T> PlanningReadResult<T> read(Session same,ReadContract<T> contract,PlanningReadRequest request) {
            if(!publicRoot(contract,request))return context.reads().read(same,contract,request);
            try {
                context.writer().requireSession(same);
                var canonical=context.readHistoryPublisher().canonicalReadWitness(same,contract,request);
                if(canonical.isPresent())return canonical.orElseThrow().requireCurrent(same,contract,request);
                return context.reads().read(same,contract,request);
            }catch(IOException unavailable){return new PlanningReadResult.Unavailable<>("actual canonical ROOT originals unavailable: "+unavailable.getMessage(),Optional.empty());}
        }
    }
    private static Optional<FinanceStatePort.Checkpoint> checkpoint(RootRuntimeContext context,Session session)throws IOException {
        context.writer().requireSession(session);var head=session.head();var state=head.state().toJson();
        if(!state.has(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD))return Optional.empty();
        var saved=StrictJson.object(state.get(WriterContracts.ORDINARY_SAVED_CYCLE_FIELD),Set.of("pair","state"));
        var pair=CheckpointPairCodec.decode(StrictJson.canonical(saved.get("pair")));
        var original=context.savedSources().load(pair);StrictJson.require(original.pair().equals(pair)
                &&pair.frame().machineId().equals(context.game().machineId()),"actual saved pair source belongs to another machine");
        session.requireHistoricalState(original.originalHeadSequence(),original.originalHeadDigest());
        StrictJson.require(session.head().digest().equals(head.digest()),"actual saved source verification changed the canonical finance head");
        return Optional.of(new FinanceStatePort.Checkpoint(pair.save().reference(),pair.frame().frame().episodeRunId(),pair.frame().frame().identity().dateRaw()));
    }
    private static Session borrowed(RootRuntimeContext context) {
        try { return context.borrowedSession(); }
        catch(IOException failure) { throw new UncheckedIOException("actual original finance writer Session is not held",failure); }
    }
    private static final class FactionReads implements FinanceReadContracts.ExternalFactionAlerts {
        private final RootRuntimeContext context;private final FactionAlertReadService.Contracts contracts;private final ExactRef source;
        private FactionReads(RootRuntimeContext context,FactionAlertReadService.Contracts contracts,ExactRef source) { this.context=context;this.contracts=contracts;this.source=source; }
        @Override public ExactRef definitionSource() { return source; }
        @Override public PlanningReadResult<PlanningReadReceipt> read(PlanningRequest request) {
            var selected=selection(request);return original(context.reads().read(contracts.issue(context.readCatalog(),selected),FactionAlertReadService.request(selected)));
        }
        @Override public PlanningReadResult<PlanningReadReceipt> read(Session borrowed,PlanningRequest request) {
            var selected=selection(request);return original(context.reads().read(borrowed,contracts.issue(context.readCatalog(),selected),FactionAlertReadService.request(selected)));
        }
        @Override public void verifyOriginal(PlanningReadReceipt receipt,Obj snapshot) {
            FactionAlertReadService.decodeArchivedOriginal(receipt,new FactionAlertReadService.SameFrameWars(receipt.request().before(),new RawJson(encode(snapshot.get("active_wars")))),text(snapshot.get("backend_id"),"actual original Driver backend"));
        }
        private static FactionAlertReadService.Selection selection(PlanningRequest request) {
            return new FactionAlertReadService.Selection(new FactionAlertReadService.Query(request.before().frame().revision()),
                    new FactionAlertReadService.Context(request.before(),request.source(),request.sessionId(),request.deadline(),
                        new FactionAlertReadService.SameFrameWars(request.before(),new RawJson(encode(request.observations().snapshot().get("active_wars")))),
                        text(request.observations().snapshot().get("backend_id"),"actual Driver backend")));
        }
        private static PlanningReadResult<PlanningReadReceipt> original(PlanningReadResult<FactionAlertReadService.Observation> value) {
            if(value instanceof PlanningReadResult.Known<FactionAlertReadService.Observation> known)return new PlanningReadResult.Known<>(known.receipt(),known.receipt(),known.originalReceipt());
            var unavailable=(PlanningReadResult.Unavailable<FactionAlertReadService.Observation>)value;return new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());
        }
    }
    private static final class Completion implements OrdinaryPlanCompletion {
        private final RootRuntimeContext context;private final MercenaryDomainSource producer;private final GiftDomainSource gifts;private final CanonicalGiftColdProvider cold;
        private Completion(RootRuntimeContext context,MercenaryDomainSource producer,GiftDomainSource gifts,CanonicalGiftColdProvider cold) {
            this.context=context;this.producer=producer;this.gifts=gifts;this.cold=cold;
        }
        @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned) {
            try { var session=context.borrowedSession();var publication=gifts.markReplacedProcess(context,session);
                if(publication.isEmpty()) {
                    var observed=gifts.afterPlanningCold(context,session,original,cold);
                    if(observed instanceof GiftDomainSource.ColdReadOnly waiting)return new Unchanged(waiting.reason());
                    if(observed instanceof GiftDomainSource.ColdClassified classified)publication=classified.publication();
                }
                if(publication.isEmpty())publication=producer.afterPlanning(context,session,original);
                return publication.<PlanningDisposition>map(value->new Published(value.predecessor(),value.receipt())).orElseGet(()->new Unchanged("actual finance inventory and pending bodies unchanged")); }
            catch(IOException|RuntimeException failure) { return new Blocked("actual mercenary inventory publication unavailable: "+failure.getMessage(),List.of()); }
        }
        @Override public ExecutionDisposition afterExecution(ActionReceipt actual) {
            if(!actual.command().operation().equals(OrdinaryFinancePolicies.MERCENARY)&&!actual.command().operation().equals(OrdinaryFinancePolicies.GIFT))return new Unchanged("ordinary action has no finance procurement transition");
            try { var session=context.borrowedSession();var publication=actual.command().operation().equals(OrdinaryFinancePolicies.MERCENARY)
                        ?producer.afterExecution(context,session,actual):gifts.afterExecution(context,session,actual);
                return publication.<ExecutionDisposition>map(value->new Published(value.predecessor(),value.receipt())).orElseGet(()->new Unchanged("unknown finance outcome retained without replay or new funds credit")); }
            catch(IOException|RuntimeException failure) { return new Blocked("actual mercenary original outcome publication unavailable: "+failure.getMessage(),List.of()); }
        }
    }
    private FinanceRuntimeInstaller() { }
}
