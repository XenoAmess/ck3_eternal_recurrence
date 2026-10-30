package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Concrete native governance graph. Ordinary policies and their own pending bodies remain with the ordinary installer. */
public final class GovernanceRuntimeInstaller {
    private GovernanceRuntimeInstaller() { }
    public record Sources(GovernanceActionBindings.Sources nativeProducers, ExactRef planningDecoder,
            ExactRef councilDecoder, ExactRef actionDecoder, ExactRef effectVerifier, ExactRef councilEffectVerifier,
            ExactRef finalTermsNative, ExactRef finalTermsDecoder,
            List<ExactRef> continuationClosure, Optional<ExactRef> publicCallerProducer) {
        public Sources {
            Objects.requireNonNull(nativeProducers); continuationClosure = List.copyOf(continuationClosure);
            publicCallerProducer = Objects.requireNonNull(publicCallerProducer);
            publicCallerProducer.ifPresent(source -> StrictJson.require(source.bytes() > 0 && Path.of(source.path()).isAbsolute(), "actual selected Java public caller producer source required"));
            for (ExactRef ref : List.of(planningDecoder, councilDecoder, actionDecoder, effectVerifier, councilEffectVerifier, finalTermsNative, finalTermsDecoder))
                StrictJson.require(ref != null && ref.bytes() > 0, "complete actual governance Java source closure required");
            StrictJson.require(!continuationClosure.isEmpty() && continuationClosure.size() <= 64, "actual canonical Council producer/reducer/guard/native closure required");
        }
        /** Legacy source-only definitions remain body-derived and cannot authorize explicit caller IDs. */
        public Sources(GovernanceActionBindings.Sources nativeProducers, ExactRef planningDecoder,
                ExactRef councilDecoder, ExactRef actionDecoder, ExactRef effectVerifier, ExactRef councilEffectVerifier,
                ExactRef finalTermsNative, ExactRef finalTermsDecoder, List<ExactRef> continuationClosure) {
            this(nativeProducers, planningDecoder, councilDecoder, actionDecoder, effectVerifier, councilEffectVerifier,
                    finalTermsNative, finalTermsDecoder, continuationClosure, Optional.empty());
        }
    }
    public record Config(String gameVersion, String executableSha256, String authorityId,
            Set<OperationKey> admittedActions, int maximumStatusPolls, int maximumContinuations) {
        public Config {
            org.xar.ck3.control.governance.council.CouncilCodec.requireBuild(gameVersion, executableSha256); StrictJson.text(authorityId);
            admittedActions = Set.copyOf(admittedActions);
            for (OperationKey operation : admittedActions) StrictJson.require(GovernanceActionPreparation.OPERATIONS.contains(operation.value()), "unrelated governance operation admitted");
            StrictJson.require(maximumStatusPolls >= 1 && maximumStatusPolls <= 3000 && maximumContinuations >= 3 && maximumContinuations <= 1024, "bounded native Council polling/continuation required");
        }
    }
    /** Construct before Core.open so the actual canonical continuation verifier is in the original writer registry. */
    public static Prepared prepare(Path originalWriterLock, Sources sources, Config config, Clock clock,
            CouncilContinuationPorts.SeedAuthority actualOriginalSeedAuthority) {
        return new Prepared(originalWriterLock, sources, config, clock, actualOriginalSeedAuthority);
    }
    public static Prepared prepare(Path originalWriterLock,Sources sources,Config config,Clock clock) {
        return prepare(originalWriterLock,sources,config,clock,new RootCouncilContinuationSeeds(originalWriterLock,sources.continuationClosure()));
    }
    public static final class Prepared {
        private final Path writerLock;
        private final Sources sources;
        private final Config config;
        private final Clock clock;
        private final CouncilContinuationPorts.SeedAuthority seed;
        private final CouncilContinuationCoordinator continuation;
        private final DomainBodies.Registration continuationRegistration;
        private final GovernancePlanningReads planning;
        private final GovernanceNativeReads publicReads;
        private final PrivateCouncilReads privateReads;
        private final NativeGovernanceEffects.Contracts receipts;
        private final NativeCrownFinalTermsRead finalTerms;
        private RootApplicationAssembly.Core originalCore;
        private RootRuntimeContext current;
        private CouncilContinuationPolicy policy;
        private Prepared(Path lock, Sources sources, Config config, Clock clock, CouncilContinuationPorts.SeedAuthority seed) {
            writerLock = Objects.requireNonNull(lock).toAbsolutePath().normalize(); this.sources = Objects.requireNonNull(sources);
            this.config = Objects.requireNonNull(config); this.clock = Objects.requireNonNull(clock); this.seed = Objects.requireNonNull(seed);
            continuation = new CouncilContinuationCoordinator(writerLock, sources.continuationClosure(), clock);
            continuationRegistration = continuation.registration(seed);
            planning = new GovernancePlanningReads(new GovernancePlanningReads.Sources(sources.nativeProducers().lifestyle(), sources.nativeProducers().crown()), config.gameVersion(), config.executableSha256());
            publicReads = new GovernanceNativeReads(sources.nativeProducers().council(), config.gameVersion(), config.executableSha256());
            privateReads = new PrivateCouncilReads(sources.nativeProducers().council());
            receipts = NativeGovernanceEffects.readContracts(sources.nativeProducers().lifestyle(), sources.nativeProducers().council(), sources.nativeProducers().crown());
            finalTerms = new NativeCrownFinalTermsRead(sources.finalTermsNative(), config.gameVersion(), config.executableSha256());
        }
        /** The identical actual preCore Java source passed to the native preparation producer. */
        public Optional<ExactRef> publicCallerProducer() { return sources.publicCallerProducer(); }
        public List<DomainBodies.Registration> domainRegistrations() { return List.of(continuationRegistration); }
        /** Pass these identical source-qualified permissions to the actual managed transport constructor before its first use. */
        public List<NativePrivateActionPermission> privatePermissions(NativePrivateActionPermission.QualificationVerifier actualQualification) {
            return GovernanceActionBindings.privatePermissions(sources.nativeProducers(), config.admittedActions(), actualQualification);
        }
        public synchronized Installed install(RootRuntimeContext context) throws IOException {
            Objects.requireNonNull(context); context.requireCurrent(clock.instant().plusSeconds(1));
            StrictJson.require(context.core().configuration().ledger().lock().toAbsolutePath().normalize().equals(writerLock), "governance installer belongs to another original writer lock");
            if(seed instanceof RootCouncilContinuationSeeds originals) {originals.bindCore(context.core());originals.installContext(context);}
            if (originalCore == null) {
                originalCore = context.core(); current = context;
                policy = new CouncilContinuationPolicy(privateReads, context.frameLoader(), config.gameVersion(), config.executableSha256());
                continuation.bind(originalCore.journal(), originalCore.archive(),
                        (same, head, parent, deadline) -> {
                            RootRuntimeContext actual = active();
                            return new RootCouncilContinuationGuard(actual.readiness(), actual.archive(), actual.source(), clock,
                                    config.authorityId(), actual.originals(), actual.bindings()).current(same, head, parent, deadline);
                        }, new CouncilContinuationPorts.NativePort() {
                            @Override public NativeActionPort.DispatchOutcome submit(CouncilContinuationPermit permit, NativeRequest exact, java.time.Instant deadline) throws IOException, InterruptedException {
                                return active().transport().continueCouncil(permit, exact, deadline);
                            }
                            @Override public Optional<NativeActionPort.AckReceived> collectOriginalOutcome(String requestId, java.time.Instant deadline) throws IOException, InterruptedException {
                                return active().transport().collectOriginalOutcome(requestId, deadline);
                            }
                        }, policy);
            } else {
                StrictJson.require(originalCore == context.core(), "a prepared governance graph cannot be rebound to another Core/writer");
                StrictJson.require(current != context, "actual governance runtime is installed exactly once per physical Game");
                current = context;
            }
            return new Installed(this, context);
        }
        private synchronized RootRuntimeContext active() {
            return Objects.requireNonNull(current, "actual governance Game context has not been installed");
        }
    }
    /** Shared actual constructor path; tests exercise this same source injection without a Game. */
    static GovernanceActionPreparation buildPreparation(Sources sources, Config config,
            GovernanceActionPreparation.CouncilRefreshPort refresh,
            GovernanceActionPreparation.LifestyleRefreshPort lifecycle) {
        return new GovernanceActionPreparation(config.gameVersion(), config.executableSha256(), refresh, lifecycle,
                sources.publicCallerProducer());
    }
    public static final class Installed {
        private final Prepared prepared;
        private final RootRuntimeContext context;
        private final NativeLifestyleReadPort lifecycle;
        private final GovernanceActionPreparation producer;
        private final NativeCouncilReadPort council;
        private final RootDomainInstallation installation;
        private NativeGovernanceEffects observer;
        private Installed(Prepared prepared, RootRuntimeContext context) throws IOException {
            this.prepared = prepared; this.context = context;
            lifecycle = new NativeLifestyleReadPort(context.reads(), prepared.planning, context.archive());
            var refresh = new CouncilPreparationRead(context.reads(), prepared.privateReads, context.archive(), prepared.clock,
                    prepared.config.maximumStatusPolls(), prepared.config.gameVersion(), prepared.config.executableSha256());
            producer = buildPreparation(prepared.sources, prepared.config, refresh, lifecycle);
            council = new NativeCouncilReadPort(context.reads(), prepared.publicReads, prepared.privateReads, context.transport(),
                    new NativeCouncilReadPort.SessionAccess() {
                        @Override public <T> T withSession(PlanningRequest request, NativeCouncilReadPort.SessionWork<T> work) throws IOException, InterruptedException {
                            requireCurrent(request.deadline()); var same = context.borrowedSession(); context.writer().requireSession(same);
                            try { return work.run(same); } finally { context.writer().requireSession(same); }
                        }
                    }, prepared.writerLock, context.archive(), prepared.clock, prepared.config.maximumStatusPolls(), prepared.config.gameVersion(), prepared.config.executableSha256());
            var installedReads = new ArrayList<RootReadContractCatalog.InstalledRead>();
            for (ReadContract<?> read : prepared.publicReads.registeredContracts()) installedReads.add(new RootReadContractCatalog.InstalledRead(read, prepared.sources.councilDecoder()));
            for (ReadContract<?> read : prepared.privateReads.registeredContracts()) installedReads.add(new RootReadContractCatalog.InstalledRead(read, prepared.sources.councilDecoder()));
            for (ReadContract<?> read : prepared.planning.all()) installedReads.add(new RootReadContractCatalog.InstalledRead(read, prepared.sources.planningDecoder()));
            for (ReadContract<?> read : prepared.receipts.all()) installedReads.add(new RootReadContractCatalog.InstalledRead(read, prepared.sources.effectVerifier()));
            installedReads.add(new RootReadContractCatalog.InstalledRead(prepared.finalTerms.contract(), prepared.sources.finalTermsDecoder()));
            NativeEffectRegistry.Observer callable = (command, attempt, dispatch) -> effects().observe(command, attempt, dispatch);
            var actions = GovernanceActionBindings.bindings(prepared.sources.nativeProducers(), producer, callable, prepared.config.admittedActions()).stream()
                    .map(binding -> new RootExecutableBindings.ActionBinding(binding, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                            binding.operation().value().equals(CouncilActionCodec.ASSIGN) ? Optional.of("game.action.assign-councillor-v1") : Optional.empty(), prepared.sources.actionDecoder())).toList();
            var archived = new ArrayList<NativeRecordedEvidenceVerifier.Binding>();
            for (OperationKey operation : prepared.config.admittedActions()) {
                if (operation.value().equals(CouncilActionCodec.PRIVATE_ASSIGN)) archived.add(NativeCouncilAssignmentEffects.archivedVerifier(prepared.sources.councilEffectVerifier(),
                        prepared.continuation, prepared.policy, context.frameLoader(), this::session));
                else archived.add(NativeGovernanceEffects.archivedVerifier(operation, prepared.sources.effectVerifier(), context.frameLoader(), prepared.receipts, lifecycle,
                        Optional.of(prepared.planning.focusStateReconciliation())));
            }
            var domains = actions.stream().map(binding -> new RootDomainInstallation.FixedDomain(binding,
                    binding.effect().operation().value().equals(GovernanceActionPreparation.FOCUS) || binding.effect().operation().value().equals(GovernanceActionPreparation.PERK) ? Domain.lifestyle : Domain.council)).toList();
            installation = new RootDomainInstallation("native-governance", prepared.domainRegistrations(), installedReads, List.of(), actions,
                    List.of(), archived, List.of(), List.of(), List.of(), List.of(), Set.of(), List.of(), List.of(), domains, List.of(), List.of());
        }
        public RootDomainInstallation installation() { return installation; }
        public GovernancePlanningReads planningReads() { return prepared.planning; }
        public GovernanceNativeReads publicReads() { return prepared.publicReads; }
        public PrivateCouncilReads privateReads() { return prepared.privateReads; }
        public NativeCouncilReadPort councilReads() { return council; }
        public NativeCrownFinalTermsRead crownFinalTermsRead() { return prepared.finalTerms; }
        /** Clock projection of the one complete law read; absence never suppresses the stock law material. */
        public GovernanceCollector.CrownCooldownReadPort crownCooldownReads() {
            return request->{
                try {
                    requireCurrent(request.deadline());var same=context.borrowedSession();context.writer().requireSession(same);var contract=prepared.finalTerms.contract();
                    var result=context.reads().read(same,contract,new PlanningReadRequest(request.before(),request.source(),request.sessionId(),contract.operation(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),request.deadline()));
                    if(result instanceof PlanningReadResult.Unavailable<NativeCrownFinalTermsRead.Terms> unavailable)return new GovernanceObservationSupplier.Unavailable<>(unavailable.reason());
                    var known=(PlanningReadResult.Known<NativeCrownFinalTermsRead.Terms>)result;
                    if(known.value().clock().isEmpty())return new GovernanceObservationSupplier.Unavailable<>("complete stock law material has no qualified .4 calendar observation");
                    return new GovernanceObservationSupplier.Known<>(known.value().clock().orElseThrow(),List.of(known.originalReceipt(),contract.sourceRef()));
                }catch(IOException failure) {return new GovernanceObservationSupplier.Unavailable<>("actual final-terms clock read unavailable: "+failure.getMessage());}
            };
        }
        public GovernanceActionPreparation preparation() { return producer; }
        /** Ordinary planning binds the exact currently borrowed writer, never a Session retained at startup. */
        public GovernanceCollector.LifestyleReadPort lifestyleReads() {
            return new GovernanceCollector.LifestyleReadPort() {
                @Override public GovernanceObservationSupplier.Read<org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj> formal(PlanningRequest request) {
                    try { return planning(request).formal(request); } catch (IOException missing) { return new GovernanceObservationSupplier.Unavailable<>(missing.getMessage()); }
                }
                @Override public GovernanceObservationSupplier.Read<org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj> stockFocus(PlanningRequest request, String target) {
                    try { return planning(request).stockFocus(request, target); } catch (IOException missing) { return new GovernanceObservationSupplier.Unavailable<>(missing.getMessage()); }
                }
                private NativeLifestyleReadPort planning(PlanningRequest request) throws IOException {
                    requireCurrent(request.deadline()); var same = context.borrowedSession(); context.writer().requireSession(same);
                    return new NativeLifestyleReadPort(context.reads(), prepared.planning, context.archive(), new GovernanceBorrowedSession(same, prepared.writerLock, context.writer()::requireSession));
                }
            };
        }
        /** Import only a complete original continuation manifest or an independently proven fresh seed. */
        public void adoptOriginalContinuation(ContinuityStorePort.Session same, ExactRef originalManifest) throws IOException {
            context.writer().requireSession(same); prepared.continuation.adoptOriginal(same, originalManifest, prepared.seed);
        }
        public void initializeContinuation(ContinuityStorePort.Session same,RootInitialEpisodeProof actual)throws IOException {
            context.writer().requireSession(same);StrictJson.require(prepared.seed instanceof RootCouncilContinuationSeeds,"the concrete Root original continuation producer is not installed");
            var originals=(RootCouncilContinuationSeeds)prepared.seed;adoptOriginalContinuation(same,originals.preserveFresh(same,actual));
        }
        public void initializeContinuation(ContinuityStorePort.Session same,FreshCampaignContext actual)throws IOException {
            context.writer().requireSession(same);StrictJson.require(actual.context()==context,"fresh continuation belongs to another installed Game");actual.requireCurrent(same);
            var existing=same.readDomain(DomainBodies.Slot.COUNCIL_CONTINUATION);
            if(existing instanceof DomainBodies.Available available) {CouncilContinuationCodec.decodeState(available.canonicalBody());return;}
            StrictJson.require(existing instanceof DomainBodies.Unavailable unavailable && unavailable.reason()==DomainBodies.Reason.UNIMPORTED,
                    "fresh continuation may initialize only an unimported slot");
            StrictJson.require(prepared.seed instanceof RootCouncilContinuationSeeds,"the concrete Root original continuation producer is not installed");
            var originals=(RootCouncilContinuationSeeds)prepared.seed;adoptOriginalContinuation(same,originals.preserveFresh(same,actual));
        }
        public ExactRef captureOriginalContinuation(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);StrictJson.require(prepared.seed instanceof RootCouncilContinuationSeeds,"the concrete Root original continuation producer is not installed");
            return ((RootCouncilContinuationSeeds)prepared.seed).preserveCanonical(same);
        }
        public CouncilContinuationCoordinator continuations() { return prepared.continuation; }
        public RootReconciliationAuthority.QueryPolicy reconciliationReads(){return (original,identity,current,deadline)->{
            if(!NativeGovernanceEffects.kind(original.command().operation()).filter(NativeGovernanceEffects.Kind.FOCUS::equals).isPresent())
                return List.of();
            var same=session();var contract=prepared.planning.focusStateReconciliation();
            StrictJson.require(context.readCatalog().containsIdentity(contract)&&current.identity().equals(identity.factual())
                    &&current.source().equals(identity.source())&&current.sessionId().equals(identity.sessionId()),
                    "FOCUS getter must retain its identical installed current factual source");
            var attempt=ActionTransitions.attempt(original.state()).orElseThrow();
            var request=NativeGovernanceEffects.focusStateReconciliationRequest(original.command(),attempt,identity,contract,deadline);
            NativeGovernanceEffects.requireCanonicalFocusStateReconciliation(original,attempt,identity,contract,request);
            context.archive().inSession(same,bound->{
                var retained=lifecycle.originals(original.command(),attempt,bound);
                lifecycle.verify(original.command(),attempt,retained,bound);
                var ack=(NativeActionPort.AckReceived)ActionTransitions.dispatch(original.state()).orElseThrow();
                for(var read:retained)NativeRequestChronology.requireBeforeSubmission(read,attempt,ack);
                return null;
            });
            return List.of(new RootReconciliationAuthority.AllowedRead(contract,request.arguments(),
                    RootReconciliationAuthority.QueryKind.LIFESTYLE_FOCUS_STATE));
        };}
        private ContinuityStorePort.Session session() {
            try { var same = context.borrowedSession(); context.writer().requireSession(same); return same; }
            catch (IOException failure) { throw new UncheckedIOException("actual original governance writer Session unavailable", failure); }
        }
        private void requireCurrent(java.time.Instant deadline) throws IOException {
            StrictJson.require(prepared.active() == context, "governance object belongs to a retired physical Game"); context.requireCurrent(deadline);
        }
        private synchronized NativeGovernanceEffects effects() {
            try { requireCurrent(prepared.clock.instant().plusSeconds(1)); }
            catch (IOException failure) { throw new UncheckedIOException(failure); }
            if (observer == null) {
                var snapshots = new NativeEffectSnapshots(context.adopted().observations(), context.archive(), context.frameLoader());
                var privateCouncil = new NativeCouncilAssignmentEffects(prepared.continuation, prepared.policy, snapshots, context.archive(), context.frameLoader(), this::session,
                        prepared.clock, prepared.config.maximumContinuations());
                observer = new NativeGovernanceEffects(snapshots, context.reads(), prepared.receipts, new NativeGovernanceEffects.SessionPort() {
                    @Override public ContinuityStorePort.Session current(ActionCommand command) {
                        if(ActionReconciliationScope.activeFor(command))return session();
                        var same = GovernanceActionScope.current(command).session(command); StrictJson.require(same == session(), "governance effect borrowed another writer Session"); return same;
                    }
                    @Override public List<PlanningReadReceipt> preflight(ActionCommand command) { return GovernanceActionScope.current(command).preflight(command); }
                }, privateCouncil, lifecycle, Optional.of(prepared.planning.focusStateReconciliation()));
            }
            return observer;
        }
    }
}

