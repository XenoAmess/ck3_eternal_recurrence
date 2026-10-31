package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.time.Clock;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.lifecycle.*;
import org.xar.ck3.control.application.lifecycle.NaturalSuccessionPreparation.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.platform.GameSeedAdapter;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier.Originals;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One original writer transition service and actual per-Game terminal products. Constructors grant no live qualification. */
public final class RootLifecycleRuntimeFactory {
    private RootLifecycleRuntimeFactory() { }
    public static final List<OperationKey> OPERATIONS=List.of(new OperationKey("death-terminal"),
            new OperationKey("continue-as-reconciled-successor"),new OperationKey("start-next-episode"));
    public record Sources(List<ExactRef> naturalProducers,ExactRef timelineDefinition,ExactRef closeDefinition,
            ExactRef retainedPrisonerDefinition,ExactRef naturalDecoder,ExactRef timelineDecoder,
            ExactRef prisonerDecoder,ExactRef compositeImplementation,ExactRef compositeReplay) {
        public Sources {
            naturalProducers=List.copyOf(naturalProducers);
            require(!naturalProducers.isEmpty()&&naturalProducers.size()<=64&&naturalProducers.stream().distinct().count()==naturalProducers.size(),"finite unique original natural producer closure required");
            for(ExactRef ref:naturalProducers)require(ref.bytes()>0&&Path.of(ref.path()).isAbsolute(),"actual nonempty absolute original natural producer source required");
            for(ExactRef ref:List.of(timelineDefinition,closeDefinition,retainedPrisonerDefinition,naturalDecoder,
                    timelineDecoder,prisonerDecoder,compositeImplementation,compositeReplay))
                require(ref.bytes()>0&&Path.of(ref.path()).isAbsolute(),"complete exact absolute lifecycle implementation/decoder sources required");
        }
    }
    public record Configuration(Path stateRoot,Path saveGames,Path tutorial,Path evidenceRoot,
            Set<String> actualClockHandlers,Duration actionBudget) {
        public Configuration {
            for(Path path:List.of(stateRoot,saveGames,tutorial,evidenceRoot))
                require(path.isAbsolute()&&path.normalize().equals(path),"absolute normalized actual lifecycle storage/profile paths required");
            actualClockHandlers=Set.copyOf(actualClockHandlers);
            require(!actualClockHandlers.isEmpty()&&actualClockHandlers.size()<=32&&actualClockHandlers.stream().noneMatch(String::isBlank),"explicit installed clock handler identities required");
            Objects.requireNonNull(actionBudget);require(!actionBudget.isZero()&&!actionBudget.isNegative()&&actionBudget.compareTo(Duration.ofMinutes(5))<=0,"finite original lifecycle action budget required");
        }
    }
    private static final class Attempt {
        final RootRuntimeContext context;final RootLifecycleAuthority physical;final PrisonersRuntimeInstaller prisoners;
        final RootCrossRunPlanning.Prepared crossRun;final ReadContract<?> campaignRoot;
        final RootLifeRuntimeFactory.Installed life;
        Installed installed;IOException failure;boolean entered;
        Attempt(RootRuntimeContext context,RootLifecycleAuthority physical,PrisonersRuntimeInstaller prisoners,
                RootCrossRunPlanning.Prepared crossRun,ReadContract<?> campaignRoot,RootLifeRuntimeFactory.Installed life) {
            this.context=context;this.physical=physical;this.prisoners=prisoners;this.crossRun=crossRun;this.campaignRoot=campaignRoot;this.life=life;
        }
    }
    /** Register the original domain and transition authority before Core.open. Bind the one actual creator before CREATE. */
    public static final class Prepared {
        private ExactRef changedPreflightSource;
        private final Sources sources;private final Configuration configuration;private final CheckpointFiles files;
        private final Clock clock;
        private final RootRuntimeStorageGuard storage;
        private final RootNaturalSuccessionOriginals.Prepared natural;
        private final LifecycleContinuityAuthority transition=new LifecycleContinuityAuthority();
        private final Map<SessionIdentity,Attempt> attempts=new LinkedHashMap<>();
        private final RootOriginalNaturalSuccessionVerifier verifier;
        private RootApplicationAssembly.Core core;private JavaGameLifecycle managed;private NativeLaunchPlan plan;
        private GameSeedAdapter seedGames;private LifecycleComposites composite;
        private RootExecutableBindings.CompositeBinding binding;
        private List<NativeRecordedEvidenceVerifier.Binding> replays;
        private NativePrivateActionPermission.QualificationVerifier qualifier;
        private List<NativePrivateActionPermission> permissions;
        public Prepared(Sources sources,Configuration configuration,CheckpointFiles actualFiles,RootRuntimeStorageGuard actualStorage,Clock actualClock) {
            this.sources=Objects.requireNonNull(sources);this.configuration=Objects.requireNonNull(configuration);
            files=Objects.requireNonNull(actualFiles);storage=Objects.requireNonNull(actualStorage);clock=Objects.requireNonNull(actualClock);
            natural=new RootNaturalSuccessionOriginals.Prepared(sources.naturalProducers(),sources.timelineDefinition(),sources.closeDefinition());
            verifier=new RootOriginalNaturalSuccessionVerifier(new OriginalRouter(this));
        }
        public Sources sources(){return sources;}
        void bindChangedPreflightSource(ExactRef actual)throws IOException {
            require(core==null&&changedPreflightSource==null&&actual!=null&&actual.bytes()>0,"changed preflight source must be bound exactly once before Core installation");changedPreflightSource=actual;
        }
        public Configuration configuration(){return configuration;}
        public synchronized void requireBoundCore(RootApplicationAssembly.Core identical)throws IOException {
            require(core!=null&&core==identical&&identical.archive().writer()==identical.writer(),"PendingUI must retain the same bound lifecycle Core/writer");
        }
        public synchronized Installed installedFor(RootRuntimeContext actual)throws IOException {
            Objects.requireNonNull(actual);requireBoundCore(actual.core());var installed=installed(identity(actual));installed.requireContext(actual);return installed;
        }
        public List<DomainBodies.Registration> domainRegistrations() {return List.of(natural.registration());}
        public LifecycleContinuityAuthority transitionAuthority() {return transition;}
        public String transitionKind() {return LifecycleChild.KIND;}
        public void requireCompleteAdmission()throws IOException {
            storage.requireFilePort(files);
            storage.requireManagedRoots(List.of(configuration.stateRoot(),configuration.saveGames(),configuration.evidenceRoot()));
            storage.requireCompleteAdmission();
        }
        public synchronized void bindCore(RootApplicationAssembly.Core actual) {
            Objects.requireNonNull(actual);require(core==null&&actual.archive().writer()==actual.writer(),"lifecycle definitions bind their sole original Core exactly once");
            natural.linkCore(actual);core=actual;actual.bindLifecycleTransitions(this);
        }
        public synchronized List<NativePrivateActionPermission> privatePermissions(NativePrivateActionPermission.QualificationVerifier actual) {
            Objects.requireNonNull(actual);
            if(permissions!=null){require(qualifier==actual,"actual prelaunch lifecycle source qualifier cannot be replaced");return permissions;}
            require(managed==null,"Close permission must be frozen before the actual managed creator is bound");qualifier=actual;
            var template=new RootNaturalSuccessionOriginals(sources.naturalProducers(),sources.timelineDefinition(),sources.closeDefinition(),actual);
            permissions=List.of(template.timeline().privatePermission());return permissions;
        }
        public synchronized void bindManagedLifecycle(JavaGameLifecycle actual,NativeLaunchPlan retainedPlan)throws IOException {
            Objects.requireNonNull(actual);Objects.requireNonNull(retainedPlan);var root=requireCore();
            require(managed==null&&permissions!=null,"one actual managed creator follows the original prelaunch permissions");
            require(retainedPlan.sources().review().machineId().equals(root.configuration().machineId()),"managed lifecycle plan belongs to another Core machine");
            retainedPlan.sources().verify();managed=actual;plan=retainedPlan;seedGames=new GameSeedAdapter(actual,retainedPlan);
        }
        public synchronized Installed install(RootRuntimeContext context,RootLifecycleAuthority samePhysical,
                PrisonersRuntimeInstaller samePrisoners,RootCrossRunPlanning.Prepared actualCrossRun,ReadContract<?> originalCampaignRoot,
                RootLifeRuntimeFactory.Installed sameLife)throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(samePhysical);Objects.requireNonNull(samePrisoners);Objects.requireNonNull(actualCrossRun);Objects.requireNonNull(originalCampaignRoot);Objects.requireNonNull(sameLife);
            var root=requireCore();require(context.core()==root&&context.writer()==root.writer()&&context.archive()==root.archive(),"lifecycle installation crossed the original Core/writer/archive");
            requireCompleteAdmission();
            require(context.clock()==clock,"lifecycle installation must retain the actual original Root clock");
            require(managed!=null&&seedGames!=null&&managed.currentSession().filter(game->game==context.game()).isPresent(),"lifecycle installation requires the actual same managed Game");

            require(originalCampaignRoot.operation().value().equals("query-campaign-root-context-v1")&&originalCampaignRoot.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,"actual installed ordinary campaign-root contract required");

            Set<String> actualClockHandlers=requireActualClockHandlers(context,sameLife);
            SessionIdentity identity=identity(context);Attempt attempt=attempts.get(identity);
            if(attempt==null){require(attempts.size()<64,"bounded actual lifecycle Game installations required");attempt=new Attempt(context,samePhysical,samePrisoners,actualCrossRun,originalCampaignRoot,sameLife);attempts.put(identity,attempt);}
            require(attempt.context==context&&attempt.physical==samePhysical&&attempt.prisoners==samePrisoners&&attempt.crossRun==actualCrossRun&&attempt.campaignRoot==originalCampaignRoot&&attempt.life==sameLife,"same Game cannot replace its original lifecycle installation inputs");
            if(attempt.installed!=null)return attempt.installed;
            if(attempt.entered)throw new IOException("actual lifecycle installation already entered; no partial replay",attempt.failure);
            attempt.entered=true;
            try {
                context.game().verify();actualCrossRun.attachContext(context);createComposite();
                var originals=natural.install(context,samePhysical,context.sources(),originalCampaignRoot,sources.retainedPrisonerDefinition(),
                        actualClockHandlers,qualifier,Optional.of(permissions.getFirst()));
                var seed=new SeedBinding(context,files,storage);
                var decisions=new TerminalLifecycleDecisionProducer(root.writer(),samePhysical,root.actions(),composite,seed::requireActual,files,originals,
                        context.clock(),configuration.actionBudget());
                // The terminal decision service consumes an actual SeedStore. A missing staged store is never an empty seed.
                var installed=new Installed(this,context,samePhysical,originals,decisions,seed);
                installed.crossRun=actualCrossRun.install(context,samePhysical,composite,decisions);
                attempt.installed=installed;
                return installed;
            }catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure){attempt.failure=new IOException("actual lifecycle construction failed",failure);throw attempt.failure;}
        }
        private Set<String> requireActualClockHandlers(RootRuntimeContext context,RootLifeRuntimeFactory.Installed actual)throws IOException {
            actual.requireContext(context);
            var lifeBindings=actual.installation().composites();
            require(lifeBindings.size()==1&&lifeBindings.getFirst().handler()==actual.composite(),"natural preclock must retain the actual installed Life composite object");
            var infrastructure=actual.infrastructure();
            require(infrastructure.installation().composites().isEmpty(),"a new infrastructure composite needs an explicit clock-parent contract");
            var resume=infrastructure.installation().actions().stream().filter(binding->binding.effect().operation().value().equals("resume-map")).toList();
            require(resume.size()==1&&resume.getFirst().effect().preparation()==infrastructure.primitives()
                    &&resume.getFirst().effect().producerSource().equals(infrastructure.sources().primitiveProducer()),
                    "natural preclock must retain the same actual shared resume primitive and source");
            Set<String> handlers=Set.of(actual.composite().handlerId());
            require(configuration.actualClockHandlers().equals(handlers),"configured clock parent identities differ from actual installed Life; missing Battle cannot be declared by text");
            return handlers;
        }
        private void createComposite()throws IOException {
            if(composite!=null)return;var root=requireCore();
            LifecycleObservationPort observations=new LifecycleObservationPort(){
                @Override public Snapshot current(ActionCommand parent,Instant deadline){return selected(parent).observations.current(parent,deadline);}
                @Override public Snapshot next(ActionCommand parent,Snapshot previous,Instant deadline){return selected(parent).observations.next(parent,previous,deadline);}
            };
            composite=new LifecycleComposites(this::actualDriver,observations,files,this::actualSeeds,seedGames,transition,
                    configuration.tutorial(),configuration.evidenceRoot(),clock,storage.seedGuard(),pin->root.writer().borrowedSession().verifyPin(pin),
                    verifier,new org.xar.ck3.control.application.lifecycle.NaturalSuccessionContinuationSource(){
                         @Override public Preparation prepareOutcome(ActionCommand parent,LifecycleObservationPort.Snapshot original,CompositeActionPort.Children children)throws IOException,InterruptedException{return selected(parent).natural.prepareOutcome(parent,original,children);}
                         @Override public void requireCurrent(ActionCommand parent,ContinuityStorePort.Session same,PendingToken token)throws IOException{selected(parent).natural.requireCurrent(parent,same,token);}
                         @Override public LifecycleObservationPort.Snapshot requireRetainedOriginalFrame(ActionCommand parent,ContinuityStorePort.Session same,PendingToken token)throws IOException{return selected(parent).natural.requireRetainedOriginalFrame(parent,same,token);}
                         @Override public void requireCommittedPendingEpisode(ActionReceipt parent,ContinuityStorePort.Session same,LifecycleComposites.RecordedPendingEpisode identical)throws IOException{selected(parent.command()).natural.requireCommittedPendingEpisode(parent,same,identical);}
                         @Override public void requireFinalized(ActionCommand parent,ContinuityStorePort.Session same,FinalToken token)throws IOException{selected(parent).natural.requireFinalized(parent,same,token);}
                         @Override public Preparation resumeOutcome(ActionCommand parent,PendingToken token,CompositeActionPort.Children children)throws IOException,InterruptedException{return selected(parent).natural.resumeOutcome(parent,token,children);}
                         @Override public void requireChild(ActionCommand parent,ContinuityStorePort.Session same,PendingToken token,ActionCommand child)throws IOException{selected(parent).natural.requireChild(parent,same,token,child);}
                     },root.writer()::borrowedSession);
            composite.bindTerminalPlanningArchive(root.archive());
            binding=new RootExecutableBindings.CompositeBinding(composite,ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,Optional.empty(),sources.compositeImplementation(),sources.compositeReplay());
            var values=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();
            for(OperationKey operation:OPERATIONS)values.add(new NativeRecordedEvidenceVerifier.Binding(operation,sources.compositeReplay(),(head,receipt,archive)->{
                try {
                    var same=root.writer().borrowedSession();root.writer().requireSession(same);require(same.head().digest().equals(head.digest())&&receipt.command().operation().equals(operation),"lifecycle replay crossed original writer head or operation");
                    require(receipt.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied,"actual settled lifecycle proof required");
                    var proof=((ActionState.LifecycleApplied)((ActionState.CompositeSettled)receipt.state()).settlement()).proof();composite.verifyRecorded(receipt.command(),proof,head);
                }catch(IOException failure){throw new UncheckedIOException("actual lifecycle recorded proof unavailable",failure);}
            }));replays=List.copyOf(values);
        }
        private synchronized RootApplicationAssembly.Core requireCore()throws IOException {if(core==null)throw new IOException("actual lifecycle Core is not bound");return core;}
        private synchronized Installed selected(ActionCommand parent) {
            try {var actual=installed(new SessionIdentity(parent.origin().machineId(),parent.origin().game(),parent.sessionId()));
                require(actual.context.source().equals(parent.source()),"lifecycle parent source differs from original per-Game producer");return actual;
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private synchronized Installed installed(SessionIdentity identity)throws IOException {
            Attempt attempt=attempts.get(identity);if(attempt==null||attempt.installed==null)throw new IOException("actual per-Game lifecycle producer is unavailable");return attempt.installed;
        }
        private DriverStateAssembler actualDriver()throws IOException {
            var root=requireCore();root.writer().requireSession(root.writer().borrowedSession());var current=root.sessionAccess().current();
            var owner=installed(current.identity());require(owner.context.adopted()==current.driver(),"lifecycle Driver resolver crossed the actual admitted per-Game Driver");return current.driver().authority();
        }
        private SeedStore actualSeeds()throws IOException {var root=requireCore();root.writer().requireSession(root.writer().borrowedSession());var current=root.sessionAccess().current();return installed(current.identity()).seed.requireActual();}
    }
    /** Strict deferred binding to this actual Staged checkpoint store; absence never becomes an empty seed. */
    private static final class SeedBinding implements CheckpointService.SeedAdoptionPort {
        private final RootRuntimeContext context;private final CheckpointFiles files;
        private final RootRuntimeStorageGuard storage;
        private record Bound(SeedStore actual,RootApplicationAssembly.Staged stage) { }
        private Optional<Bound> bound=Optional.empty();
        SeedBinding(RootRuntimeContext context,CheckpointFiles files,RootRuntimeStorageGuard storage) {this.context=context;this.files=files;this.storage=storage;}
        synchronized void bind(SeedStore value,RootApplicationAssembly.Staged stage) {require(bound.isEmpty(),"per-Game immutable seed producer is once bound");bound=Optional.of(new Bound(Objects.requireNonNull(value),Objects.requireNonNull(stage)));}
        SeedStore requireActual()throws IOException {
            Bound value;synchronized(this){value=bound.orElseThrow(()->new IOException("actual Staged immutable seed producer is not bound"));}
            storage.requireCompleteAdmission();storage.requireFilePort(files);
            context.game().verify();require(context.adopted()==value.stage().driver()&&value.stage().readiness().identity().equals(identity(context)),"immutable seed reader crossed its actual Staged Game/Driver");
            value.stage().requireCheckpointFiles(files);value.stage().checkpoints().requireSeedStore(this,value.actual());return value.actual();
        }
        @Override public SeedAdoption freezeFirst(CheckpointPair pair,ActionReceipt save)throws IOException {return requireActual().freezeFirst(pair,save);}
    }
    /** Real objects retained by the catalog, Staged finish, original INTENT hook and terminal observation consumer. */
    public static final class Installed {
        private RootChangedSuccessionPreflight changedPreflight;
        private final Prepared owner;private final RootRuntimeContext context;private final RootLifecycleAuthority physical;
        private final RootNaturalSuccessionOriginals natural;private final TerminalLifecycleDecisionProducer decisions;
        private final RootLifecycleObservationPort observations;private final SeedBinding seed;
        private final RootLifecycleActionGuard.CloseAdmission closeAdmission;
        private final RootDomainInstallation installation;
        private RootCrossRunPlanning.Installed crossRun;private RootApplicationAssembly.Staged stage;
        private Installed(Prepared owner,RootRuntimeContext context,RootLifecycleAuthority physical,
                RootNaturalSuccessionOriginals natural,TerminalLifecycleDecisionProducer decisions,SeedBinding seed) {
            this.owner=owner;this.context=context;this.physical=physical;this.natural=natural;this.decisions=decisions;this.seed=seed;
            closeAdmission=natural.timeline()::verifyClose;
            observations=new RootLifecycleObservationPort(physical,()->{
                try{return context.borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            var reads=new ArrayList<RootReadContractCatalog.InstalledRead>();
            for(ReadContract<?> read:natural.terminalContracts()) {
                ExactRef decoder=read==natural.timeline().contract()?owner.sources.timelineDecoder():
                        read==natural.prisonerContract()?owner.sources.prisonerDecoder():owner.sources.naturalDecoder();
                reads.add(new RootReadContractCatalog.InstalledRead(read,decoder));
            }
            var replay=new ArrayList<>(owner.replays);replay.add(natural.timeline().replayBinding());
            installation=new RootDomainInstallation("canonical-lifecycle-and-natural-originals",owner.domainRegistrations(),reads,List.of(),
                    List.of(natural.timeline().actionBinding()),List.of(owner.binding),replay,List.of(),List.of(),List.of(),List.of(),Set.of(),
                    List.of(),List.of(),List.of(),List.of(),List.of());
        }
        public RootDomainInstallation installation() {return installation;}
        /** Identity check for actual installer consumers. It grants no current observation, source, planning or submit qualification. */
        public void requireContext(RootRuntimeContext actual)throws IOException {
            Objects.requireNonNull(actual);var original=owner.requireCore();
            require(context==actual&&context.core()==original&&context.writer()==original.writer()&&context.archive()==original.archive()
                    &&context.clock()==owner.clock&&owner.installed(identity(context))==this,
                    "lifecycle consumer must retain this identical installed per-Game Root context and original Core/writer/archive");
        }
        public LifecycleComposites composite() {return owner.composite;}
        /** One handler instance implements all three exact operations, so the registry retains one binding. */
        public List<RootExecutableBindings.CompositeBinding> composites() {return List.of(owner.binding);}
        public List<NativeRecordedEvidenceVerifier.Binding> replays() {return installation.archived();}
        public List<NativePrivateActionPermission> privatePermissions() {return owner.permissions;}
        public RootLifecycleAuthority physical() {return physical;}
        public RootNaturalSuccessionOriginals natural() {return natural;}
        public RootLifeRuntimeFactory.Installed life()throws IOException {requireContext(context);return owner.attempts.get(identity(context)).life;}
        public Optional<SessionPorts.PendingSuccessorUi> pendingSuccessorUi(ContinuityStorePort.Session same,SessionIdentity expected,Instant deadline)throws IOException{return natural.pendingRuntime().pendingSuccessorUi(same,expected,deadline);}
        public void installTransportContinuity(ContinuityStorePort.Session same)throws IOException{natural.pendingRuntime().installTransportContinuity(same);}
        public Optional<org.xar.ck3.control.application.session.ContinuityBatchJournal.ReboundTransport> rebindPendingTransport(ContinuityStorePort.Session same,SessionIdentity owner,Instant deadline)throws IOException,InterruptedException{return natural.pendingRuntime().rebindPendingTransport(same,owner,deadline);}
        public Optional<SessionPorts.PendingSuccessorUi> pendingTransportedSuccessorUi(ContinuityStorePort.Session same,SessionIdentity owner,org.xar.ck3.control.application.session.ContinuityBatchJournal.ReboundTransport transport,Instant deadline)throws IOException{return natural.pendingRuntime().pendingTransportedSuccessorUi(same,owner,transport,deadline);}
        public Optional<org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.CurrentAdoptionBinding> admittedCurrent(ContinuityStorePort.Session same,ActionReceipt exactParent,Instant deadline)throws IOException{return natural.pendingRuntime().admittedCurrent(same,exactParent,deadline);}
        public Optional<org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.CurrentAdoptionBinding> admittedTransportedCurrent(ContinuityStorePort.Session same,ActionReceipt exactParent,org.xar.ck3.control.application.session.ContinuityBatchJournal.ReboundTransport transport,Instant deadline)throws IOException{return natural.pendingRuntime().admittedTransportedCurrent(same,exactParent,transport,deadline);}
        public org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs requireAdmittedCurrentProducer(ContinuityStorePort.Session same,org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.CurrentAdoptionBinding identical)throws IOException{return natural.pendingRuntime().requireAdmittedCurrentProducer(same,identical);}
        public ActionPorts.GuardPort wrapActions(ActionPorts.GuardPort ordinary){Objects.requireNonNull(ordinary);return (head,command)->{try{return natural.pendingRuntime().wrapActions(ordinary).verify(head,command);}catch(IOException failure){throw new UncheckedIOException(failure);}};}
        public PlanningReadCoordinator.ReadGuardPort wrapReads(PlanningReadCoordinator.ReadGuardPort ordinary){
            Objects.requireNonNull(ordinary);return new PlanningReadCoordinator.ReadGuardPort(){
                private PlanningReadCoordinator.ReadGuardPort actual(){try{return natural.pendingRuntime().wrapReads(ordinary);}catch(IOException failure){throw new UncheckedIOException(failure);}}
                @Override public PlanningReadGuard verify(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract){return actual().verify(head,request,contract);}
                @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract){return actual().verifyOriginalCurrent(head,request,contract);}
                @Override public void verifyFrontendReadContinuation(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract,PlanningReadGuard before,PlanningReadGuard after){actual().verifyFrontendReadContinuation(head,request,contract,before,after);}
                @Override public <T> T withOriginalReadSource(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract,java.util.function.Supplier<T> work){return actual().withOriginalReadSource(head,request,contract,Objects.requireNonNull(work));}
            };
        }

        public TerminalLifecycleDecisionProducer terminalDecisions() {return decisions;}
        public Optional<RootChangedSuccessionPreflight.Prepared> changedPreflight(ContinuityStorePort.Session same,
                org.xar.ck3.control.application.readiness.NativeReadinessCollector.PublicPlanningObservation actual,Instant deadline)throws IOException {
            requireContext(context);require(owner.changedPreflightSource!=null,"actual changed preflight helper source was not selected by the installed Root");
            if(changedPreflight==null)changedPreflight=new RootChangedSuccessionPreflight(context,physical,natural,owner.changedPreflightSource);
            return changedPreflight.capture(same,actual,deadline);
        }
        public RootLifecycleActionGuard.CloseAdmission closeAdmission() {return closeAdmission;}
        public ActionPorts.IntentPreparationPort intentPreparation() {return natural;}
        public RootCrossRunPlanning.Installed crossRun() {return Objects.requireNonNull(crossRun,"actual cross-run terminal join not installed");}
        public CheckpointService.SeedAdoptionPort seedAdoption() {return seed;}
        /** The stage was privately minted from this adopted Driver and creates the one real seed producer using its same checkpoint store. */
        public synchronized SeedStore bindStage(RootApplicationAssembly.Staged actual)throws IOException {
            Objects.requireNonNull(actual);require(context.adopted()==actual.driver()&&actual.readiness().identity().equals(identity(context)),"lifecycle seed binding crossed the actual Staged Game/Driver");
            owner.requireCompleteAdmission();
            actual.requireCheckpointFiles(owner.files);actual.checkpoints().requireSeedAdoptionPort(seed);
            if(stage!=null){require(stage==actual,"per-Game seed producer cannot move to another Staged owner");return seed.requireActual();}
            SeedStore value=new SeedStore(owner.files,actual.driverCheckpoints(),owner.configuration.stateRoot(),owner.configuration.saveGames(),owner.storage.seedGuard());
            actual.checkpoints().requireSeedStore(seed,value);
            actual.driver().authority().bindPreclockExpectationSource(natural.preclockExpectationSource());
            actual.driver().authority().bindPendingEpisodeSource(natural.pendingEpisodeSource());
            seed.bind(value,actual);stage=actual;return value;
        }
        public Optional<SessionPorts.TerminalReady> pending(ContinuityStorePort.Session same,SessionIdentity expected)throws IOException {
            context.writer().requireSession(same);require(expected.equals(identity(context)),"terminal pending source belongs to another actual Game");return decisions.pending(same,expected);
        }
        private record CapturedTerminal(SessionPorts.TerminalReady decision,boolean scored) { }
        /** Root calls outside a physical lease; scored publication ends its own read scope before changing the domain head. */
        public SessionPorts.TerminalReady observeTerminal(ContinuityStorePort.Session same,SessionIdentity expected,Instant deadline)throws IOException {
            context.writer().requireSession(same);require(expected.equals(identity(context)),"terminal observation belongs to another actual Game");
            physical.requireOutsideObservationScope(same);context.requireCurrent(deadline);
            var pending=pending(same,expected);if(pending.isPresent())return pending.orElseThrow();
            CapturedTerminal captured=physical.withObserved(same,deadline,lease->{
                var decision=decisions.decide(same,lease,deadline);
                boolean scored=decisions.canonicalTerminal(same,lease,deadline).filter(value->
                        new OpportunityJson.Text("complete").equals(value.resultObj().get("settlement_status"))).isPresent();
                lease.assertCurrent(same);return new CapturedTerminal(decision,scored);
            });
            if(!captured.scored())return captured.decision();
            physical.requireOutsideObservationScope(same);crossRun().recordScored(same,captured.decision().identity(),deadline);
            var root=context.core().sessionAccess().current();require(root.identity().equals(expected)&&root.driver()==context.adopted(),"terminal strategy refresh crossed the actual admitted Root/Driver");
            root.capabilityRuntime().refreshTerminalCanonicalStrategy(same,physical,expected,deadline);
            // A returned command carries the fresh post-publication source/Driver frame rather than the old lease.
            return physical.withObserved(same,deadline,lease->decisions.decide(same,lease,deadline));
        }
    }
    /** Private routing preserves each genuine per-Game original provider. It never reconstructs a natural proof from JSON. */
    private static final class OriginalRouter implements RootOriginalNaturalSuccessionVerifier.RootOriginals {
        private final Prepared owner;OriginalRouter(Prepared owner){this.owner=owner;}
        @Override public Originals openQualified(ActionCommand parent,LifecycleObservationPort.Snapshot actual,WriterContracts.Head head)throws IOException {return owner.selected(parent).natural.openQualified(parent,actual,head);}
        @Override public void requireCurrent(Originals originals,ActionCommand parent,LifecycleObservationPort.Snapshot actual,WriterContracts.Head head)throws IOException {owner.selected(parent).natural.requireCurrent(originals,parent,actual,head);}
        @Override public byte[] readExact(ExactRef original)throws IOException {var core=owner.requireCore();return core.archive().readArtifact(core.writer().borrowedSession(),original,WriterContracts.MAX_PIN_BYTES);}
    }
    private static SessionIdentity identity(RootRuntimeContext context) {return new SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());}
}
