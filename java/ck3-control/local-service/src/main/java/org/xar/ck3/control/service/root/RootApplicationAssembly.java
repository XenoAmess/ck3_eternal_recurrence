package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Collections;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.OrdinaryPlanningPipeline;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.OriginalLegacyResume;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeFrontendAuthority;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.platform.ManagedGameSession;

/** The actual retained graph. Construction links reject all use until their identical producer is bound. */
public final class RootApplicationAssembly {
    private RootApplicationAssembly() { }
    public record FreshSessionConfiguration(String authorityId,NativeReadiness.Policy policy,Duration freshness,RootStartupConfiguration.CheckpointPaths checkpoints,OriginalWindowReducer.Policy cyclePolicy,Instant deadline){
        public FreshSessionConfiguration(String authorityId,NativeReadiness.Policy policy,Duration freshness,RootStartupConfiguration.CheckpointPaths checkpoints,OriginalWindowReducer.Policy cyclePolicy,Instant deadline){
            this.authorityId=Objects.requireNonNull(authorityId);
            this.policy=Objects.requireNonNull(policy);
            this.freshness=Objects.requireNonNull(freshness);
            this.checkpoints=Objects.requireNonNull(checkpoints);
            this.cyclePolicy=Objects.requireNonNull(cyclePolicy);
            this.deadline=Objects.requireNonNull(deadline);
        }
    }

    public record FreshSessionServices(CheckpointFiles files,RootOfflineAnalysisWorker.Prepared offline,SessionClock sessionClock,SessionPorts.EpisodeContinuation episodes,RootCheckpointVerifier.SavedCaptureFactory savedCapture,RootRestoreMaterialFactory restoreMaterials,RootRestoreAdapters.PostAdoptionPort restorePublication){
        public FreshSessionServices(CheckpointFiles files,RootOfflineAnalysisWorker.Prepared offline,SessionClock sessionClock,SessionPorts.EpisodeContinuation episodes,RootCheckpointVerifier.SavedCaptureFactory savedCapture,RootRestoreMaterialFactory restoreMaterials,RootRestoreAdapters.PostAdoptionPort restorePublication){
            this.files=Objects.requireNonNull(files);
            this.offline=Objects.requireNonNull(offline);
            this.sessionClock=Objects.requireNonNull(sessionClock);
            this.episodes=Objects.requireNonNull(episodes);
            this.savedCapture=Objects.requireNonNull(savedCapture);
            this.restoreMaterials=Objects.requireNonNull(restoreMaterials);
            this.restorePublication=Objects.requireNonNull(restorePublication);
        }
    }

    private static SessionIdentity sessionIdentity(DriverBootstrap.Adopted actual) {
        var transport=Objects.requireNonNull(actual).session();
        return new SessionIdentity(transport.machineId(),transport.game(),transport.sessionId());
    }
    public static Core open(RootApplicationConfiguration configuration, Clock clock,
            List<DomainBodies.Registration> domains, Optional<RollbackPair.Authority> rollback,StorageWriteGuard storage) throws IOException {
        Objects.requireNonNull(configuration);Objects.requireNonNull(storage);
        try {
            return new Core(configuration,clock,List.copyOf(domains),Objects.requireNonNull(rollback),storage);
        }catch(IOException|RuntimeException|Error failure){
            try{storage.close();}catch(IOException|RuntimeException|Error closeFailure){if(closeFailure!=failure)failure.addSuppressed(closeFailure);}
            throw failure;
        }
    }

    /** Private minting keeps all later stages on this exact writer, archive, Driver and native owner. */
    public static final class Core implements AutoCloseable {
        private final RootApplicationConfiguration configuration;
        private final Clock clock;
        private final RootAuthorityRouter router = new RootAuthorityRouter();
        private RootInstalledCatalog fixtureCatalog;
        private InitialDriverBootstrap.Staged fixtureInitial;
        private RootInstalledCatalog.FixtureProducts fixtureProducts;
        private final RootDeferredAuthorities.Transition entryAuthority = new RootDeferredAuthorities.Transition();
        private final ImmutableArtifactStore artifacts;
        private final ContinuityWriter writer;
        private final NativeOutcomeArchive archive;
        private final ArchiveOriginalEvidencePort originals;
        private final ContinuityActionJournal journal;
        private final FreshGameplayEntryAuthority observedEntry;
        private final ActionSnapshotReader actions;
        private org.xar.ck3.control.application.driver.FreshGameplayEntryAuthority.RecoveryAdmission initialRecoveryAdmission;
        private final DriverObservationAssembler assembler = new DriverObservationAssembler();
        private final DriverFrameEvidenceLoader frames = new DriverFrameEvidenceLoader(assembler);
        private final NativeSemanticEvidenceVerifier semanticVerifier;
        private final RootPlanningReads reads;
        private final RootKnownReadObserver knownReads;
        private final RootSessionSwitchboard submissions;
        private final RootSavedAttachmentLoader savedLoader;
        private final RootReadHistoryAuthority readHistory;
        private final ActionHistoryLink actionHistory;
        private final RootSessionAccess sessionAccess;
        private final List<DomainBodies.Registration> originalDomainRegistrations;
        private final RootNextEpisodeWindowRuntime nextWindows;
        private final RootCheckpointVerifierRouter checkpointVerifiers;
        private RootLifecycleRuntimeFactory.Prepared lifecycleTransitions;
        private RootLegacyResumeRuntime originalResume;
        private RootPrivateBootstrap.Original coldOriginal;
        private Instant coldBootstrapDeadline;
        private final ReconciliationLink initialReconciliation = new ReconciliationLink();
        private final ThreadLocal<ContinuityStorePort.Session> planningSession = new ThreadLocal<>();
        private org.xar.ck3.control.application.planning.OrdinaryDecisionSelector decisionSelector;
        private boolean m5JointPeacetimeEnabled = true;
        private final Set<DriverBootstrap.Adopted> adopted = Collections.newSetFromMap(new IdentityHashMap<>());
        private boolean staged;
        private boolean finished;
        private RootMenuSession menu;
        private volatile RootApplicationSession activeSession;
        private Staged pendingRestore;
        private RestoredFirstEpisodeDomainProof restoredFirstDomains;
        private RootApplicationSession restoreCandidate;
        private String rootAuthorityId;
        private OriginalWindowReducer.Policy originalCyclePolicy;
        private RootCheckpointVerifier.SavedCapture savedCapture;
        private RootCheckpointVerifier.SavedCaptureFactory savedCaptureFactory;
        private OrdinaryCycleTransitions cleanRestartCycles;
        private ContinuityBatchJournal cleanRestartBatches;
        private org.xar.ck3.control.application.session.ContinuityBatchJournal.CleanRestartAdmission cleanRestartAdmission;
        private OriginalWindowReducer.Policy cleanRestartPolicy;
        private OrdinaryCycleTransitions unresolvedSameGameCycles;
        private ContinuityBatchJournal unresolvedSameGameBatches;
        private ContinuityBatchJournal.UnresolvedSameGameData unresolvedSameGameData;
        private OriginalWindowReducer.Policy unresolvedSameGamePolicy;
        private OrdinaryCycleTransitions settledSameGameCycles;
        private ContinuityBatchJournal settledSameGameBatches;
        private ContinuityBatchJournal.SettledSameGameData settledSameGameData;
        private SessionPorts.SemanticEvidence settledSameGameSemantic;
        private OriginalWindowReducer.Policy settledSameGamePolicy;
        private ContinuityBatchJournal.InitialNoDispatchRecovery initialNoDispatchProof;
        private OrdinaryCycleTransitions initialNoDispatchCycles;
        private ContinuityBatchJournal initialNoDispatchBatches;
        private OriginalWindowReducer.Policy initialNoDispatchPolicy;
        private SessionPorts.SemanticEvidence initialNoDispatchSemantic;
        private volatile org.xar.ck3.control.application.lifecycle.LifecycleComposites activeLifecycle;
        private volatile NextEpisodeStage pendingNext;
        private volatile NextEpisodeAttempt nextAttempt;
        private boolean nextStageEntered;
        private NextEpisodeStage lastPublishedNext;
        private RootStartupNextResources.Prepared nextResources;
        private RootOfflineAnalysisWorker.Prepared ordinaryOffline;
        private RootRuntimeStorageGuard ordinaryStorage;
        private RootPublicRestoreRuntime publicRestore;
        private PhysicalActionRegistry physicalActions;
        private final Set<RootInstalledCatalog> resourceCatalogs=Collections.newSetFromMap(new IdentityHashMap<>());
        private boolean resourcesClosed;
        private boolean requestsClosed;
        private java.util.concurrent.CompletionStage<Void> closeCompletion;
        private Throwable closeFailure;
        private final RootDecisionDisplay decisionDisplay;
        private Core(RootApplicationConfiguration configuration, Clock clock, List<DomainBodies.Registration> domains,
                Optional<RollbackPair.Authority> rollback,StorageWriteGuard storage) throws IOException {
            this.configuration = configuration; this.clock = Objects.requireNonNull(clock);
            decisionDisplay = new RootDecisionDisplay(clock);
            originalDomainRegistrations = List.copyOf(domains);
            artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(configuration.artifactRoot(),
                    configuration.ledger().lock(), configuration.maximumArtifactBytes()),storage);
            writer = new ContinuityWriter(configuration.ledger(), configuration.writerSources(), router, clock,
                    new ContinuityWriter.Extensions(domains, Optional.of(artifacts), rollback),storage);
            StrictJson.require(writer.storageGuard()==storage&&artifacts.storageGuard()==storage,
                    "Core ledger and immutable artifact store must retain the identical required storage guard");
            archive = new NativeOutcomeArchive(artifacts, writer); originals = new ArchiveOriginalEvidencePort(archive);
            journal = new ContinuityActionJournal(writer, archive); actions = new ActionSnapshotReader(journal);
            observedEntry=new FreshGameplayEntryAuthority(writer,archive);
            semanticVerifier = new NativeSemanticEvidenceVerifier(archive::readArtifact); reads = new RootPlanningReads(writer);
            knownReads = new RootKnownReadObserver(writer);
            submissions = new RootSessionSwitchboard(writer);
            savedLoader = new RootSavedAttachmentLoader(writer);
            readHistory = new RootReadHistoryAuthority(writer);
            actionHistory=new ActionHistoryLink(writer,journal,archive);
            sessionAccess = new RootSessionAccess(this);
            nextWindows = new RootNextEpisodeWindowRuntime(this);
            checkpointVerifiers=new RootCheckpointVerifierRouter(writer);
        }
        public StorageWriteGuard storageGuard(){return writer.storageGuard();}
        public synchronized void bindDecisionSelector(org.xar.ck3.control.application.planning.OrdinaryDecisionSelector actual) {
            StrictJson.require(decisionSelector == null, "per-Game ordinary selector already bound");
            decisionSelector = Objects.requireNonNull(actual);
        }
        public synchronized void bindM5JointPeacetimeEnabled(boolean actual) {
            m5JointPeacetimeEnabled = actual;
        }
        public synchronized boolean m5JointPeacetimeEnabled() {
            return m5JointPeacetimeEnabled;
        }
        public synchronized Optional<org.xar.ck3.control.application.planning.OrdinaryDecisionSelector> decisionSelector() {
            return Optional.ofNullable(decisionSelector);
        }
        public ContinuityWriter writer() { return writer; }
        public NativeOutcomeArchive archive() { return archive; }
        public ArchiveOriginalEvidencePort originals() { return originals; }
        public ActionSnapshotReader actions() { return actions; }
        public ActionJournal journal() { return journal; }
        public RootPlanningReads planningReads() { return reads; }
        public DriverFrameEvidenceLoader frameLoader() { return frames; }
        public DriverObservationAssembler observationAssembler() { return assembler; }
        public NativeSemanticEvidenceVerifier semanticVerifier() { return semanticVerifier; }
        public RootApplicationConfiguration configuration() { return configuration; }
        public RootSessionAccess sessionAccess() { return sessionAccess; }
        public RootNextEpisodeWindowRuntime nextEpisodeWindows() { return nextWindows; }
        /** Validates either the private post-BASELINE candidate or this exact privately published successor. */
        public void requireAdmittedNext(ContinuityStorePort.Session same,NextEpisodeStage stage,
                RootNextEpisodeWindowRuntime.Baselined baseline,RootInstalledCatalog catalog,DriverCapabilityRuntime candidate)throws IOException {
            writer.requireSession(same);Objects.requireNonNull(stage);Objects.requireNonNull(baseline);
            synchronized(this) {
                StrictJson.require(stage.owner==this&&stage.catalog==catalog&&stage.candidate==candidate
                        &&stage.baselined==baseline&&baseline.begun().stage()==stage,
                        "next admission belongs to another private stage, baseline or runtime");
                if(stage.publishedSuccessor==null) {
                    StrictJson.require(activeSession==stage.previous&&pendingNext==stage,"private next admission lost its original public owner");
                    nextWindows.requireBaseline(same,baseline);return;
                }
                var current=stage.publishedSuccessor;
                StrictJson.require(activeSession==current&&current.ownedBy(this)&&current.hasInstalledHost()&&!current.isRetired()
                        &&current.driver()==stage.driver&&current.capabilityRuntime()==candidate
                        &&catalog.context().core()==this&&catalog.context().adopted()==stage.driver
                        &&catalog.context().actions()==current,
                        "the actual privately published next Root is not the current admitted session");
                same.requireEpisodeWindowActive(baseline.committedBaseline());
                stage.replacement.verify();
            }
        }
        Clock clock() { return clock; }
        org.xar.ck3.control.application.presentation.DecisionDisplay audienceDisplay() { return decisionDisplay.feed(); }
        public RootDecisionDisplay.UiStatus decisionDisplayStatus() { return decisionDisplay.status(); }
        String authorityId(){return Objects.requireNonNull(rootAuthorityId,"the actual Root action authority has not been installed");}
        RootSessionSwitchboard submissionSwitchboard() { return submissions; }
        RootKnownReadObserver knownReadObserver() { return knownReads; }
        Supplier<ContinuityStorePort.Session> borrowedSessions() { return borrowed(); }
        ActionCoordinatorPort scopedCoordinator(ActionCoordinator actual, NativeGameTransport transport) {
            return scoped(Objects.requireNonNull(actual), Objects.requireNonNull(transport));
        }
        /** The actual concrete lifecycle producer is linked before the original immutable writer router is sealed. */
        public synchronized void bindLifecycleTransitions(RootLifecycleRuntimeFactory.Prepared actual) {
            Objects.requireNonNull(actual);
            StrictJson.require(lifecycleTransitions == null && menu == null && !staged && !finished && !router.isSealed(),
                    "the original lifecycle transition authority binds once before Root startup");
            StrictJson.require(actual.transitionKind().equals(org.xar.ck3.control.application.lifecycle.LifecycleChild.KIND)
                    && actual.domainRegistrations().stream().allMatch(registration ->
                            originalDomainRegistrations.stream().anyMatch(original -> original == registration)),
                    "lifecycle transitions must retain the same pre-Core registered domain producers");
            lifecycleTransitions = actual;
        }
        /** The original journal migration authority is retained before the sole writer router is sealed. */
        public synchronized void bindOriginalResume(RootLegacyResumeRuntime actual)throws IOException {
            Objects.requireNonNull(actual);actual.requireOwner(this);
            StrictJson.require(originalResume==null&&menu==null&&!staged&&!finished&&!router.isSealed(),
                    "the actual original journal migration producer binds once before Root startup");
            originalResume=actual;
        }
        private RootOperatorCharacterAuthority.Prepared operatorAuthority;
        /** The finite operator source binds before this Core seals its one canonical writer router. */
        public synchronized void bindOperatorAuthority(RootOperatorCharacterAuthority.Prepared actual)throws IOException {
            Objects.requireNonNull(actual);
            StrictJson.require(operatorAuthority==null&&menu==null&&!staged&&!finished&&!router.isSealed(),
                    "actual operator authority binds once before Root startup");operatorAuthority=actual;
        }
        public synchronized RootOperatorCharacterAuthority.Prepared operatorAuthority(){
            StrictJson.require(operatorAuthority!=null,"INCOMPLETE_ROOT_RUNTIME: actual operator authority is not installed");return operatorAuthority;
        }
        private void sealAuthorities(List<RootAuthorityRouter.Binding> builtins) {
            StrictJson.require(lifecycleTransitions != null, "INCOMPLETE_ROOT_RUNTIME: the actual lifecycle transition producer is missing");
            StrictJson.require(operatorAuthority!=null,"INCOMPLETE_ROOT_RUNTIME: actual operator authority is missing");
            List<RootAuthorityRouter.Binding> actual = new ArrayList<>(builtins);
            if(originalResume!=null)actual.add(new RootAuthorityRouter.Binding(Set.of(OriginalLegacyResume.KIND),originalResume.authority()));
            actual.add(new RootAuthorityRouter.Binding(Set.of(org.xar.ck3.control.continuity.ObservedGameplayEntry.KIND),observedEntry));
            actual.add(new RootAuthorityRouter.Binding(Set.of(org.xar.ck3.control.continuity.EpisodeWindow.OPERATOR_REBIND_KIND),operatorAuthority));
            actual.add(new RootAuthorityRouter.Binding(Set.of(WriterContracts.DRIVER_ACTION_HISTORY_KIND),actionHistory));
            actual.add(new RootAuthorityRouter.Binding(Set.of(lifecycleTransitions.transitionKind()), lifecycleTransitions.transitionAuthority()));
            actual.add(new RootAuthorityRouter.Binding(Set.of(org.xar.ck3.control.continuity.EpisodeWindow.BEGIN_KIND,
                    org.xar.ck3.control.continuity.EpisodeWindow.BASELINE_KIND), nextWindows.authority()));
            Set<String> required = actual.stream().flatMap(binding -> binding.kinds().stream()).collect(java.util.stream.Collectors.toUnmodifiableSet());
            router.seal(actual, required);
        }
        RootReadHistoryAuthority readHistoryAuthority() { return readHistory; }
        /** The sole journal, archive and writer retain the same lease until capture, planning and publication have all left their freezes. */
        public <T> T withBorrowed(OrdinaryPlanCompletion.ScopeWork<T> work) throws IOException, InterruptedException {
            Objects.requireNonNull(work);
            try {
                return journal.locked(locked -> {
                    var same = locked.writerSession();
                    try {
                        writer.requireSession(same);
                        var inherited = planningSession.get();
                        StrictJson.require(inherited == null || inherited == same, "cannot replace the active Root planning writer Session");
                        if (inherited != null) return work.run();
                        planningSession.set(same);
                        try { return work.run(); } finally { planningSession.remove(); }
                    } catch (IOException failure) { throw new UncheckedIOException(failure); }
                    catch (InterruptedException interrupted) { throw new InterruptedAssembly(interrupted); }
                });
            } catch (UncheckedIOException failure) { throw failure.getCause(); }
            catch (InterruptedAssembly interrupted) { Thread.currentThread().interrupt(); throw interrupted.interruption; }
        }
        ContinuityStorePort.Session activeBorrowedSession() throws IOException {
            var same = planningSession.get();
            if (same == null) throw new IOException("no actual Root journal planning scope is active");
            writer.requireSession(same); return same;
        }
        synchronized RootApplicationSession currentForAccess() throws IOException {
            if (resourcesClosed || requestsClosed || activeSession == null || !activeSession.hasInstalledHost()) throw new IOException("actual current Root session is not admitted or is awaiting restored publication");
            return activeSession;
        }

        /** Same pre-Core actual product registry survives every menu, NEXT and restore coordinator. */
        public synchronized void bindPhysicalActions(PhysicalActionRegistry actual)throws IOException {
            Objects.requireNonNull(actual);
            StrictJson.require(!resourcesClosed&&!requestsClosed&&(physicalActions==actual||(physicalActions==null&&!router.isSealed())),
                    "physical products cannot replace the original Core registry or bind after authority sealing");
            physicalActions=actual;
        }
        public synchronized PhysicalActionRegistry physicalActions()throws IOException {
            if(physicalActions==null)throw new IOException("actual source-bound physical action products are not installed");
            return physicalActions;
        }
        /** Public restore alone may query an already entered replacement after retiring its original Root. */
        public RootCheckpointPublicCalls.RestoreCall restoreCheckpointPublic(RootCheckpointPublicCalls.Request request,Instant deadline)
                throws IOException,InterruptedException {
            Objects.requireNonNull(request);Objects.requireNonNull(deadline);
            RootApplicationSession original;RootPublicRestoreRuntime runtime;
            synchronized(this){
                original=activeSession;runtime=publicRestore;
                if(original==null||runtime==null)throw new IOException("actual public restore runtime or current Root is not installed");
                requirePublicRestoreCall(original,runtime);
            }
            // Root publication acquires this monitor while holding its call lock; never acquire calls under the monitor.
            return original.restoreCheckpointPublic(request,deadline);
        }
        synchronized RootPublicRestoreRuntime publicRestoreRuntime(RootApplicationSession original)throws IOException {
            var runtime=publicRestore;
            if(runtime==null)throw new IOException("actual source-bound public restore runtime is not installed");
            requirePublicRestoreCall(original,runtime);return runtime;
        }
        synchronized void requirePublicRestoreCall(RootApplicationSession original,RootPublicRestoreRuntime runtime)throws IOException {
            if(resourcesClosed||requestsClosed||runtime==null||runtime!=publicRestore||activeSession!=original||!original.ownedBy(this)
                    ||(original.isRetired()?!runtime.ownsPending(original):!original.hasInstalledHost()))
                throw new IOException("public restore must retain its exact current Root or its privately entered pending replacement");
        }
        /** Binds the concrete runtime carrying the identical original startup resources, never a replacement factory. */
        public synchronized void bindPublicRestoreRuntime(RootPublicRestoreRuntime actual)throws IOException {
            Objects.requireNonNull(actual);actual.requireCore(this);
            StrictJson.require(!resourcesClosed&&!requestsClosed&&(publicRestore==null||publicRestore==actual),
                    "public restoration cannot replace the original Core-owned runtime or reopen a closed lifetime");
            publicRestore=actual;
        }
        synchronized void requirePublicHost(org.xar.ck3.control.service.OrdinarySessionHost actual)throws IOException {
            if(resourcesClosed||requestsClosed||activeSession==null||!activeSession.ownedBy(this)||!activeSession.hasInstalledHost()
                    ||activeSession.hostForPublication()!=actual)
                throw new IOException("public Host must retain this exact admitted current Root and sole Core");
        }
        synchronized void requirePublicWork(RootApplicationSession actual){
            StrictJson.require(!resourcesClosed&&!requestsClosed&&activeSession==actual&&actual.ownedBy(this),
                    "public work cannot enter a stopped, closed or replaced actual Root");
        }
        synchronized void requireRetiredStageAccess(RootApplicationSession actual){
            StrictJson.require(!resourcesClosed&&!requestsClosed&&activeSession==actual&&actual.ownedBy(this)&&actual.isRetired(),
                    "retired transfer cannot reopen a stopped, closed or replaced actual Root");
        }
        /** Returns only the already constructed same-Game menu; its original frontend guards retain all permission checks. */
        public synchronized RootMenuSession requireFrontendMenu(RootRuntimeContext actual)throws IOException {
            Objects.requireNonNull(actual);
            StrictJson.require(!resourcesClosed&&!requestsClosed&&actual.core()==this&&actual.writer()==writer&&actual.archive()==archive
                    &&menu!=null&&menu.game==actual.game()&&menu.source.equals(actual.source())
                    &&(activeSession==null||activeSession.identity().game().equals(actual.game().generation())),
                    "the actual pre-game frontend menu does not belong to this current managed Game/source/Core");
            actual.game().verify();return menu;
        }
        /** Menus can be acted on before an initial complete Driver exists, through this same sole coordinator. */
        public synchronized RootMenuSession menu(String authorityId, ManagedGameSession game, G2Source source,
                RootExecutableBindings bindings, NativeFrontendAuthority frontend) throws IOException {
            StrictJson.require(menu == null && !staged && !finished && !router.isSealed(), "one original frontend startup graph required");
            rootAuthorityId = StrictJson.text(authorityId);
            game.verify(); bindings.requireCompleteArchiveCoverage(); Supplier<ContinuityStorePort.Session> borrowed = borrowed();
            var gameplay = new RootDeferredAuthorities.ActionGuard(); var gameplayReads = new RootDeferredAuthorities.ReadGuard();
            knownReads.initial(gameplayReads);
            var intents = new RootDeferredAuthorities.Intent(); var cycles = new RootDeferredAuthorities.Transition(); var saved = new RootDeferredAuthorities.Transition();
            var attempts = new RootDeferredAuthorities.Attempts(writer);
            var terminalActions = new RootDeferredAuthorities.TerminalActions(); var terminalReads = new RootDeferredAuthorities.TerminalReads();
            var derivedReplay = new RootDeferredAuthorities.DerivedReplay(writer);
            var readBarrier = new RootDeferredAuthorities.ReadBarrier();
            RootFrontendActionGuard menus = new RootFrontendActionGuard(frontend, borrowed, archive, source, clock, authorityId, originals, bindings);
            ActionPorts.GuardPort guard = new OriginActions(gameplay, menus, terminalActions);
            RootFrontendReadGuard menuReads = new RootFrontendReadGuard(frontend, borrowed, archive, source, clock, authorityId, originals, bindings.readCatalog());
            PlanningReadCoordinator queries = new PlanningReadCoordinator(bindings.readCatalog(), journal,
                    submissions, game.nativeTransport(), archive, clock, knownReads);
            NativeRecordedEvidenceVerifier evidence = new NativeRecordedEvidenceVerifier(archive, borrowed, originals, frames, bindings,
                    RootLifecycleGuardEvidence::verify, derivedReplay, initialReconciliation,
                    (command,originalGuard,originalArchive,same,originalsPort)->RootOperatorGuardEvidence.requireHistorical(same,command,originalGuard,originalArchive));
            submissions.installInitial(new RootSessionSwitchboard.View(new SessionIdentity(game.machineId(), game.generation(), game.sessionId()), guard,
                    new OriginReads(gameplayReads, menuReads, terminalReads, initialReconciliation,
                            new RootMenuPhysicalStatusReads(bindings,source,borrowed)), evidence));
            RootDecisionDisplay.requireSources(game.launchPlan());
            ActionCoordinator sole = new ActionCoordinator(authorityId, journal, submissions, bindings, game.nativeTransport(),
                    bindings.effects(), clock, bindings.composites(), intents, attempts, readBarrier);
            sole.bindDecisionDisplay(audienceDisplay());
            sole.bindPhysicalActions(physicalActions());
            sole.bindReconciliationObservation(initialReconciliation);
            ActionCoordinatorPort coordinator = scoped(sole, game.nativeTransport());
            ActionContinuityAuthority action = new ActionContinuityAuthority(authorityId, archive, submissions, submissions, clock,bindings);
            action.bindPhysicalActions(physicalActions());
            sealAuthorities(List.of(new RootAuthorityRouter.Binding(Set.of(ContinuityActionJournal.KIND), action),
                    new RootAuthorityRouter.Binding(Set.of(OrdinaryCycleTransitions.CYCLE_KIND, OrdinaryCycleTransitions.BATCH_KIND,
                            OrdinaryCycleTransitions.NEXT_BASELINE_KIND), cycles),
                    new RootAuthorityRouter.Binding(SavedAttachmentAuthority.kinds(), saved),
                    new RootAuthorityRouter.Binding(Set.of(WriterContracts.GAMEPLAY_ENTRY_KIND), entryAuthority),
                    new RootAuthorityRouter.Binding(Set.of(WriterContracts.DRIVER_READ_HISTORY_KIND), readHistory)));
            reads.bind(queries);
            menu = new RootMenuSession(authorityId, writer, game, source, bindings, frontend, coordinator, queries, gameplay, gameplayReads,
                    intents, attempts, terminalActions, terminalReads, derivedReplay, readBarrier, cycles, saved, entryAuthority);
            return menu;
        }

        /** Installs the actual provisional history owners only inside this registered fixture callback. */
        void bindFixtureHistory(RootRuntimeContext context,InitialDriverBootstrap.Staged initial,
                RootInstalledCatalog.FixtureProducts products)throws IOException {
            var same=writer.borrowedSession();writer.requireSession(same);
            var scope=RootFixtureQualifiedScope.required();scope.requireContext(context);
            StrictJson.require(scope.context()==context&&scope.staged(same)==initial&&context.core()==this
                    &&requireFrontendMenu(context)==menu&&!staged&&!finished,"fixture history crossed its actual private startup scope");
            initial.requireFixtureOwner(same,context.game(),context.source());
            products.capabilities().requireOwner(initial.fixtureAuthority(same),archive,menu.bindings);
            products.readHistory().requireOwner(initial.fixtureAuthority(same),archive,menu.bindings.readCatalog());
            products.actionHistory().requireOwner(initial.fixtureAuthority(same),journal,archive);
            StrictJson.require(products.capabilities().readHistoryPublisher()==products.readHistory(),
                    "fixture caches and history must retain the identical original READ publisher");
            synchronized(this){
                StrictJson.require(fixtureProducts==null||fixtureProducts==products&&fixtureInitial==initial,
                        "fixture cannot replace its actual provisional Driver/history products");
                fixtureInitial=initial;fixtureProducts=products;fixtureCatalog=scope.catalog();
                readHistory.initial(products.readHistory());actionHistory.initial(products.actionHistory());
            }
        }

        /** The privately resolved original journal is committed and adopted within this exact writer Session. */
        public synchronized DriverBootstrap.Adopted adoptOriginal(ManagedGameSession game,G2Source source,
                int retainedFrames,Instant deadline,
                RootLegacyResumeRuntime actualOriginalResume)throws IOException,InterruptedException {
            return adoptOriginalBound(game,source,retainedFrames,deadline,actualOriginalResume,null).driver();
        }
        /** A fresh physical private issuer consumes the existing canonical cold reducer exactly once. */
        public synchronized RootPrivateBootstrap.Original adoptColdOriginal(RootPrivateBootstrap.Prepared bootstrap,
                int retainedFrames)throws IOException,InterruptedException {
            Objects.requireNonNull(bootstrap);
            StrictJson.require(bootstrap.context().core()==this&&bootstrap.actualResume()==originalResume,
                    "cold bootstrap crossed its actual Core or original resume authority");
            StrictJson.require(coldOriginal==null,"this Core already retained its one actual cold bootstrap");
            var actual=adoptOriginalBound(bootstrap.game(),bootstrap.context().source(),retainedFrames,bootstrap.deadline(),
                    bootstrap.actualResume(),bootstrap).cold().orElseThrow();
            coldOriginal=actual;coldBootstrapDeadline=bootstrap.deadline();return actual;
        }
        private record OriginalAdoption(DriverBootstrap.Adopted driver,Optional<RootPrivateBootstrap.Original> cold){ }
        private OriginalAdoption adoptOriginalBound(ManagedGameSession game,G2Source source,int retainedFrames,
                Instant deadline,RootLegacyResumeRuntime actualOriginalResume,RootPrivateBootstrap.Prepared cold)
                throws IOException,InterruptedException {
            Objects.requireNonNull(actualOriginalResume);actualOriginalResume.requireOwner(this,game,source);
            StrictJson.require(actualOriginalResume==originalResume&&!staged&&!finished&&router.isSealed(),
                    "original Driver adoption requires the same bound migration authority before native staging");
            game.verify();NativeGameTransport transport=game.nativeTransport();
            try {
                return writer.locked(same->{
                    try {
                        var result=actualOriginalResume.prepare(same,deadline);
                        if(result instanceof RootLegacyResumeRuntime.Awaiting waiting)
                            throw new IOException("ORIGINAL_RESUME_AWAITING: "+waiting.reason());
                        var prepared=(RootLegacyResumeRuntime.Prepared)result;prepared.requireCurrent(same);
                        if(cold!=null)cold.requireBeforeCommit(same,prepared);
                        var receipt=prepared.commit(same);
                        if(cold!=null)cold.recordCommitted(same,prepared,receipt);
                        var actual=DriverBootstrap.adoptResolvedOriginal(prepared,receipt,same,actions,transport,source,archive,
                                (ref,maximum)->RootOriginalArtifacts.read(writer,archive,same,ref,maximum,source.sourceRef()),
                                prepared.coverage(same,receipt),retainedFrames,deadline);
                        adopted.add(actual);
                        return new OriginalAdoption(actual,cold==null?Optional.empty():Optional.of(cold.acceptCommitted(same,prepared,receipt,actual)));
                    }catch(InterruptedException interrupted){throw new InterruptedAssembly(interrupted);}
                });
            }catch(InterruptedAssembly interrupted){
                if(cold!=null)recordColdFailure(cold,interrupted.interruption);
                Thread.currentThread().interrupt();throw interrupted.interruption;
            }catch(IOException|RuntimeException|Error failure){
                if(cold!=null)recordColdFailure(cold,failure);throw failure;
            }
        }
        private static void recordColdFailure(RootPrivateBootstrap.Prepared cold,Throwable original){
            try{cold.recordFailure(original);}catch(IOException|RuntimeException proofFailure){if(proofFailure!=original)original.addSuppressed(proofFailure);}
        }
        synchronized void requireColdOriginalAdopted(RootPrivateBootstrap.Prepared bootstrap,DriverBootstrap.Adopted actual)throws IOException {
            StrictJson.require(bootstrap.context().core()==this&&bootstrap.actualResume()==originalResume
                    &&!staged&&!finished&&router.isSealed()&&adopted.contains(actual)
                    &&actual.session().game().equals(bootstrap.game().generation())
                    &&actual.session().sessionId().equals(bootstrap.game().sessionId()),
                    "cold private issuer requires this exact Core's actual recorded Driver adoption");
        }
        /** Registers the genuine first-map Driver on this Core without a legacy import or manufactured entry receipt. */
        public synchronized DriverBootstrap.Adopted adoptFresh(ManagedGameSession game,
                org.xar.ck3.control.application.action.NativeActionPort.AckReceived originalStartAck,
                org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received received,
                InitialDriverState.Produced initial,G2Source source,int retainedFrames,Instant deadline)throws IOException {
            StrictJson.require(menu==null&&!staged&&!finished&&adopted.isEmpty(),"fresh Driver binds once to the unused Core");
            var result=DriverBootstrap.fresh(received,initial,game,writer,archive,actions,source,retainedFrames,deadline);
            observedEntry.retain(game,originalStartAck,received,initial,result);
            adopted.add(result);return result;
        }

        public synchronized DriverBootstrap.Adopted adoptObservedMap(ManagedGameSession game,
                org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received received,
                InitialDriverState.Produced initial,G2Source source,int retainedFrames,Instant deadline)throws IOException {
            StrictJson.require(menu==null&&!staged&&!finished&&adopted.isEmpty(),"fresh Driver binds once to the unused Core");
            writer.locked(same->{
                StrictJson.require(same.head().state().status()==org.xar.ck3.control.continuity.ContinuityState.Status.AWAITING_INITIAL_ENTRY,
                        "current-map initialization requires the actual pre-entry writer branch");return null;
            });
            var result=DriverBootstrap.fresh(received,initial,game,writer,archive,actions,source,retainedFrames,deadline);
            observedEntry.retainCurrentMap(game,received,initial,result);
            adopted.add(result);return result;
        }

        public synchronized boolean hasCanonicalGameplayEntry() throws IOException {
            return writer.locked(same -> {
                var state = same.head().state();
                return state.toJson().hasNonNull(WriterContracts.GAMEPLAY_ENTRY_FIELD);
            });
        }

        /** Routing hint only; actual clean admission still validates its canonical capture and originals. */
        public synchronized boolean matchesCleanRestartHead(ContinuityBatchJournal.CleanRestartTicket ticket) throws IOException {
            Objects.requireNonNull(ticket);
            return writer.locked(same -> same.head().state().sequence() == ticket.sequence()
                    && same.head().digest().equals(ticket.headDigest()) && same.persistedHead().equals(ticket.persistedHead()));
        }

        public synchronized DriverBootstrap.Adopted adoptInitialRecovery(ManagedGameSession game, int retainedFrames,
                OriginalWindowReducer.Policy cyclePolicy, Instant deadline) throws IOException {
            Objects.requireNonNull(deadline);
            return adoptInitialRecovery(game,retainedFrames,cyclePolicy,()->deadline);
        }

        public synchronized DriverBootstrap.Adopted adoptInitialRecovery(ManagedGameSession game, int retainedFrames,
                OriginalWindowReducer.Policy cyclePolicy, java.util.function.Supplier<Instant> deadlineSupplier) throws IOException {
            StrictJson.require(menu == null && !staged && !finished && adopted.isEmpty(), "recovery Driver binds once to the unused Core");
            Objects.requireNonNull(game);Objects.requireNonNull(cyclePolicy);Objects.requireNonNull(deadlineSupplier);
            return writer.locked(same -> {
                OrdinaryCycleTransitions recoveryCycles = null;
                ContinuityBatchJournal recoveryBatches = null;
                ContinuityBatchJournal.InitialNoDispatchRecovery recoveryProof = null;
                FreshGameplayEntryAuthority.RecoveryAdmission admission;
                var predecessor = same.head().state();
                if (predecessor.status() == org.xar.ck3.control.continuity.ContinuityState.Status.REPAIR_REQUIRED
                        || predecessor.status() == org.xar.ck3.control.continuity.ContinuityState.Status.RUNNING
                        && predecessor.toJson().hasNonNull(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)) {
                    recoveryCycles = new OrdinaryCycleTransitions(archive, semanticVerifier, checkpointVerifiers, cyclePolicy, writer::requireSession);
                    recoveryCycles.bindTerminalFrameLoader(frames);
                    recoveryBatches = new ContinuityBatchJournal(writer, recoveryCycles);
                    recoveryProof = recoveryBatches.admitInitialNoDispatchRecovery(same,
                            new SessionIdentity(game.machineId(), game.generation(), game.sessionId()));
                    admission = observedEntry.admitRecovery(same, game, recoveryProof);
                } else {
                    admission = observedEntry.admitRecovery(same, game);
                }
                var source = recoveryProof != null && recoveryProof.capturedManifest().isPresent()
                        ? recoveryProof.capturedManifest().orElseThrow().source()
                        : admission.facts().observation().orElseThrow(()->new IOException("entry recovery lost its actual original observation")).source();
                DriverBootstrap.Adopted result;
                try {
                    result = DriverBootstrap.adoptInitialRecovery(admission, same, actions, game.nativeTransport(), source, archive, retainedFrames, deadlineSupplier);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    var failure = new java.io.InterruptedIOException("same-Game recovery adoption interrupted");
                    failure.initCause(interrupted);
                    throw failure;
                }
                SessionPorts.SemanticEvidence current = null;
                if (recoveryProof != null) {
                    result.requireInitialNoDispatchRecovery(recoveryProof);
                    current = initialRecoverySemantic(same, result, recoveryProof.owner());
                }
                adopted.add(result);
                initialRecoveryAdmission = admission;
                initialNoDispatchProof = recoveryProof;
                initialNoDispatchCycles = recoveryCycles;
                initialNoDispatchBatches = recoveryBatches;
                initialNoDispatchPolicy = recoveryProof == null ? null : cyclePolicy;
                initialNoDispatchSemantic = current;
                return result;
            });
        }

        private SessionPorts.SemanticEvidence initialRecoverySemantic(ContinuityStorePort.Session same,
                DriverBootstrap.Adopted driver, SessionIdentity owner) throws IOException {
            writer.requireSession(same);
            return driver.authority().withFrozenFacts(same, frozen -> {
                if (!(frozen.state() instanceof org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known))
                    throw new IOException("initial recovery requires actual observed complete Driver facts");
                var frame = driver.first();
                var scoped = archive.withSession(same);
                var semantic = scoped.preserveMaterial(RawJson.fullMaterial(
                        org.xar.ck3.control.application.driver.DriverJson.encode(frame.semantic())));
                var stamp = scoped.preserveMaterial(RawJson.fullMaterial(
                        org.xar.ck3.control.application.readiness.NativeDriverStamp.encode(frame, known)));
                var fullDriver = scoped.preserveMaterial(RawJson.fullMaterial(known.driver().encode()));
                var current = new SessionPorts.SemanticEvidence(frame.identity(), semantic, frame.originalEvidence(),
                        stamp, fullDriver, frame.observedAt());
                semanticVerifier.verify(same, owner, current);
                return current;
            });
        }

        public synchronized Optional<ContinuityBatchJournal.InitialNoDispatchRecovery> initialNoDispatchRecovery(DriverBootstrap.Adopted expected) {
            if (initialNoDispatchProof == null) return Optional.empty();
            expected.requireInitialRecovery(initialRecoveryAdmission);
            expected.requireInitialNoDispatchRecovery(initialNoDispatchProof);
            return Optional.of(initialNoDispatchProof);
        }

        public synchronized Optional<org.xar.ck3.control.application.driver.FreshGameplayEntryAuthority.RecoveryAdmission> initialRecoveryAdmission(DriverBootstrap.Adopted expected) {
            if (initialRecoveryAdmission == null) return Optional.empty();
            expected.requireInitialRecovery(initialRecoveryAdmission);
            return Optional.of(initialRecoveryAdmission);
        }

        public RootApplicationSession finishInitialRecovery(RootInstalledCatalog installed, DriverBootstrap.Adopted driver, FreshSessionConfiguration configuration, FreshSessionServices services) throws IOException, InterruptedException {
            StrictJson.require(initialRecoveryAdmission != null, "initial recovery admission required");
            driver.requireInitialRecovery(initialRecoveryAdmission);
            if(initialNoDispatchProof!=null)StrictJson.require(initialNoDispatchPolicy.equals(configuration.cyclePolicy()),
                    "initial no-dispatch recovery retains its actual cycle policy");
            return finishObserved(installed, driver, configuration, services, Optional.empty());
        }

        public synchronized DriverBootstrap.Adopted adoptCleanRestart(ManagedGameSession game, ContinuityBatchJournal.CleanRestartTicket ticket, int retainedFrames, OriginalWindowReducer.Policy cyclePolicy, Instant deadline) throws IOException, InterruptedException {
            StrictJson.require(menu == null && !staged && !finished && adopted.isEmpty(), "clean restart binds once to the unused Core");
            StrictJson.require(game != null && ticket != null && cyclePolicy != null && deadline != null, "clean restart requires non-null arguments");
            return writer.locked(same -> {
            var cycles = new OrdinaryCycleTransitions(archive, semanticVerifier, checkpointVerifiers, cyclePolicy, writer::requireSession);
            cycles.bindTerminalFrameLoader(frames);
            var batches = new ContinuityBatchJournal(writer, cycles);
            var admission = batches.admitCleanRestart(same, ticket);
            var source=admission.manifest().source();
            DriverBootstrap.Adopted result;
            try { result = DriverBootstrap.adoptCleanRestart(admission, same, actions, game.nativeTransport(), source, archive, (ref, max) -> archive.readArtifact(same, ref, Math.min(max, ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES)), retainedFrames, deadline); }
            catch(InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                var failure=new java.io.InterruptedIOException("same-Game Driver adoption interrupted");
                failure.initCause(interrupted);throw failure;
            }
            adopted.add(result);
            cleanRestartCycles = cycles;
            cleanRestartBatches = batches;
            cleanRestartAdmission = admission;
            cleanRestartPolicy = cyclePolicy;
            return result;
            });
        }

        /** Reads a closed dirty batch directly from its real Driver/WAL without a clean capture. */
        public synchronized Optional<ContinuityBatchJournal.SettledSameGameData> readSettledSameGame(
                ManagedGameSession game,OriginalWindowReducer.Policy cyclePolicy)throws IOException {
            StrictJson.require(menu==null&&!staged&&!finished&&adopted.isEmpty(),
                    "settled continuation reads the unused actual Core");
            Objects.requireNonNull(game);Objects.requireNonNull(cyclePolicy);
            return writer.locked(same->{
                var cycle=same.head().state().toJson().get(OrdinaryCycleTransitions.STATE_FIELD);
                var status=same.head().state().status();
                if((status!=org.xar.ck3.control.continuity.ContinuityState.Status.REPAIR_REQUIRED
                        &&status!=org.xar.ck3.control.continuity.ContinuityState.Status.RUNNING)
                        ||cycle==null||cycle.get("head")==null||cycle.get("head").isNull()
                        ||cycle.get("pending_receipt")==null||!cycle.get("pending_receipt").isNull())
                    return Optional.empty();
                boolean settled=actions.withFrozen(same,lease->{
                    boolean result=!lease.snapshot().actions().isEmpty()
                            &&lease.snapshot().actions().stream().allMatch(ActionReceipt::settled);
                    lease.assertCurrent();return result;
                });
                if(!settled)return Optional.empty();
                var cycles=new OrdinaryCycleTransitions(archive,semanticVerifier,checkpointVerifiers,cyclePolicy,writer::requireSession);
                cycles.bindTerminalFrameLoader(frames);
                var batches=new ContinuityBatchJournal(writer,cycles);
                // The Journal decides whether READY is a retained settled recovery. A catalog
                // failure after repair must return through this path without a clean capture.
                var data=batches.readSettledSameGame(same,new SessionIdentity(game.machineId(),game.generation(),game.sessionId()));
                settledSameGameCycles=cycles;settledSameGameBatches=batches;
                settledSameGameData=data;settledSameGamePolicy=cyclePolicy;
                return Optional.of(data);
            });
        }

        public synchronized DriverBootstrap.Adopted adoptSettledSameGame(ManagedGameSession game,
                ContinuityBatchJournal.SettledSameGameData data,int retainedFrames,
                OriginalWindowReducer.Policy cyclePolicy,Instant deadline)throws IOException,InterruptedException {
            StrictJson.require(menu==null&&!staged&&!finished&&adopted.isEmpty(),
                    "settled continuation Driver binds once to the unused Core");
            StrictJson.require(data==settledSameGameData&&settledSameGameCycles!=null&&settledSameGameBatches!=null
                    &&settledSameGamePolicy.equals(cyclePolicy),
                    "settled continuation retains its actual history reader and cycle policy");
            return writer.locked(same->{
                final DriverBootstrap.Adopted result;
                try {
                    result=DriverBootstrap.adoptSettledSameGame(data,same,actions,game.nativeTransport(),archive,
                            writer::borrowedSession,retainedFrames,deadline);
                }catch(InterruptedException interrupted){
                    Thread.currentThread().interrupt();
                    var failure=new java.io.InterruptedIOException("settled same-Game Driver adoption interrupted");
                    failure.initCause(interrupted);throw failure;
                }
                settledSameGameSemantic=initialRecoverySemantic(same,result,data.controller().owner());
                adopted.add(result);return result;
            });
        }

        public synchronized Optional<ContinuityBatchJournal.UnresolvedSameGameData> readUnresolvedSameGame(
                ManagedGameSession game, OriginalWindowReducer.Policy cyclePolicy) throws IOException {
            StrictJson.require(menu == null && !staged && !finished && adopted.isEmpty(), "unresolved reconstruction reads the unused actual Core");
            Objects.requireNonNull(game);Objects.requireNonNull(cyclePolicy);
            return writer.locked(same -> {
                boolean pending=actions.withFrozen(same,lease->{
                    boolean found=lease.snapshot().actions().stream().anyMatch(action->!action.settled()
                            || action.command().operation().value().equals("private-select-player-lifestyle-stock-focus-v1")
                            && action.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED);
                    lease.assertCurrent();return found;
                });
                if(!pending||same.head().state().status()!=org.xar.ck3.control.continuity.ContinuityState.Status.REPAIR_REQUIRED)
                    return Optional.empty();
                var cycles=new OrdinaryCycleTransitions(archive,semanticVerifier,checkpointVerifiers,cyclePolicy,writer::requireSession);
                cycles.bindTerminalFrameLoader(frames);
                var batches=new ContinuityBatchJournal(writer,cycles);
                var data=batches.readUnresolvedSameGame(same,new SessionIdentity(game.machineId(),game.generation(),game.sessionId()));
                unresolvedSameGameCycles=cycles;unresolvedSameGameBatches=batches;
                unresolvedSameGameData=data;unresolvedSameGamePolicy=cyclePolicy;
                return Optional.of(data);
            });
        }

        public synchronized DriverBootstrap.Adopted adoptUnresolvedSameGame(ManagedGameSession game,
                ContinuityBatchJournal.UnresolvedSameGameData data,int retainedFrames,
                OriginalWindowReducer.Policy cyclePolicy,Instant deadline)throws IOException,InterruptedException {
            StrictJson.require(menu==null&&!staged&&!finished&&adopted.isEmpty(),"unresolved same-Game Driver binds once to the unused Core");
            StrictJson.require(data==unresolvedSameGameData&&unresolvedSameGameCycles!=null&&unresolvedSameGameBatches!=null
                    &&unresolvedSameGamePolicy.equals(cyclePolicy),"unresolved adoption retains the actual DATA reader and cycle policy");
            var owner=data.capturedController().owner();
            StrictJson.require(owner.machineId().equals(game.machineId())&&owner.game().equals(game.generation())
                    &&owner.sessionId().equals(game.sessionId()),"unresolved Controller belongs to another actual Game");
            return writer.locked(same->{
                final DriverBootstrap.Adopted result;
                try{result=DriverBootstrap.adoptUnresolvedSameGame(data.capturedManifest(),data.retainedFacts(),
                        data.retainedFullDriver(),same,actions,game.nativeTransport(),archive,retainedFrames,deadline);}
                catch(InterruptedException interrupted){
                    Thread.currentThread().interrupt();var failure=new java.io.InterruptedIOException("same-Game unresolved Driver adoption interrupted");
                    failure.initCause(interrupted);throw failure;
                }
                adopted.add(result);return result;
            });
        }

        public synchronized DriverBootstrap.Adopted adoptInitial(InitialDriverBootstrap.Staged original,
                WriterContracts.Prepared prepared, WriterContracts.Receipt receipt) throws IOException {
            StrictJson.require(menu != null && !staged && !finished, "initial Driver promotion requires this Core's actual startup graph");
            var held=writer.activeSession();
            DriverBootstrap.Adopted result = held.isPresent()?original.promote(held.orElseThrow(),prepared,receipt)
                    :writer.locked(borrowed -> original.promote(borrowed, prepared, receipt));
            StrictJson.require(result.session().game().equals(menu.game.generation()) && result.session().sessionId().equals(menu.game.sessionId()),
                    "initial promoted Driver belongs to another physical startup owner");
            if(!adopted.contains(result))adopted.add(result);
            if(fixtureInitial==original){
                StrictJson.require(fixtureCatalog!=null,"fixture promotion lost its actual staged catalog");
                fixtureCatalog.context().bindPhysicalDriver(result);
            }
            return result;
        }

        synchronized void requireCurrentForAccess(ContinuityStorePort.Session same,RootApplicationSession actual)throws IOException {
            writer.requireSession(same);Objects.requireNonNull(actual);
            if(resourcesClosed||requestsClosed||activeSession!=actual||!actual.ownedBy(this)||actual.isRetired()||!actual.hasInstalledHost())
                throw new IOException("the previously resolved Root is not this exact current admitted session");
        }
        /** Only checkpoint DATA resolvers may join a privately staged current Driver before Host publication. */
        public Optional<RootRuntimeContext> privateCheckpointRuntime(SessionIdentity expected)throws IOException {
            var same=writer.borrowedSession();writer.requireSession(same);Objects.requireNonNull(expected);
            synchronized(this) {
                if(pendingNext!=null&&sessionIdentity(pendingNext.driver).equals(expected)) {
                    requireRetainedNextStage(same,pendingNext);var context=pendingNext.catalog.context();
                    StrictJson.require(context.core()==this&&context.adopted()==pendingNext.driver&&context.source().equals(pendingNext.source),
                            "private NEXT checkpoint resolver crossed its actual Driver/source/catalog");
                    return Optional.of(context);
                }
                if(pendingRestore!=null&&restoreCandidate!=null&&pendingRestore.identity.equals(expected)) {
                    var stage=pendingRestore;var binding=stage.restoration.binding();stage.restoration.service().requireRetainedOriginal(same,binding);
                    var context=stage.restoration.runtime().catalog().context();context.requireRestorationOriginal(same,binding);stage.game.verify();
                    StrictJson.require(activeSession==stage.restoration.previous()&&stage.restoration.previous().isRetired()
                            &&restoreCandidate.ownedBy(this)&&context.actions()==restoreCandidate&&context.adopted()==stage.driver
                            &&binding.session().equals(expected)&&context.source().equals(binding.source()),
                            "private restored checkpoint resolver crossed its actually staged current owner");
                    return Optional.of(context);
                }
                return Optional.empty();
            }
        }
        /** Startup binds the concrete source-bound replacement-resource producer once for this original Core. */
        public synchronized void bindNextResources(RootStartupNextResources.Prepared actual)throws IOException {
            Objects.requireNonNull(actual);actual.requireCore(this);
            StrictJson.require(!resourcesClosed&&(nextResources==null||nextResources==actual),"NEXT resources cannot replace the original Core-owned producer or reopen its closed lifetime");
            nextResources=actual;
        }
        public synchronized void bindOrdinaryOfflineWorker(RootOfflineAnalysisWorker.Prepared actual,RootRuntimeStorageGuard storage) {
            Objects.requireNonNull(actual);Objects.requireNonNull(storage);
            StrictJson.require(!resourcesClosed&&nextResources==null&&ordinaryOffline==null,
                    "ordinary worker lifetime binds once before resource close");
            StrictJson.require(storageGuard()==storage,"ordinary worker must retain this actual Core storage guard");
            ordinaryOffline=actual;ordinaryStorage=storage;
        }
        public synchronized ContinuityBatchJournal.CleanRestartAdmission cleanRestartAdmission(DriverBootstrap.Adopted expected) {
            StrictJson.require(cleanRestartAdmission!=null&&adopted.contains(Objects.requireNonNull(expected)),
                    "this Core has no actual clean restart adoption");
            expected.requireCleanRestart(cleanRestartAdmission);return cleanRestartAdmission;
        }
        /** Retains only actual source-bound products for cleanup, including a before-Game or partial staged catalog. */
        public synchronized void retainCatalogResources(RootInstalledCatalog actual)throws IOException {
            Objects.requireNonNull(actual);var context=actual.context();
            StrictJson.require(!resourcesClosed&&context.core()==this&&context.writer()==writer&&context.archive()==archive,
                    "resource cleanup registration crossed its original Core/writer/archive or closed lifetime");
            if(!resourceCatalogs.contains(actual)&&resourceCatalogs.size()>=1024)
                throw new IOException("bounded actual Game resources require disposal before another catalog installation");
            resourceCatalogs.add(actual);
        }
        void releaseCatalogResources(RootInstalledCatalog actual)throws IOException {
            synchronized(this){if(!resourceCatalogs.contains(actual))return;}
            actual.closeResources();
            synchronized(this){resourceCatalogs.remove(actual);}
        }
        private IOException closeRetainedCatalogResources(){
            List<RootInstalledCatalog> actual;synchronized(this){actual=List.copyOf(resourceCatalogs);}
            IOException failure=null;
            for(var catalog:actual)try{releaseCatalogResources(catalog);}
            catch(IOException|RuntimeException cause){
                var current=cause instanceof IOException io?io:new IOException("actual per-Game cleanup failed",cause);
                if(failure==null)failure=current;else failure.addSuppressed(current);
            }
            return failure;
        }
        /** Retire the actual current public controller before Game cleanup while the original ledger remains open for cleanup evidence. */
        public void stopPublicRequests(){
            RootApplicationSession current;
            synchronized(this){requestsClosed=true;current=activeSession;}
            if(current!=null){
                if(current.hasInstalledHost()&&!current.isRetired())current.retire();
                else try{current.closeResourcesForRetirement();}catch(IOException failure){throw new UncheckedIOException(failure);}
            }
        }
        /** Stop new calls, then retain the actual accepted worker drain; each per-Game retirement leaves the pool open. */
        @Override public void close() {
            RootStartupNextResources.Prepared actual;
            synchronized(this){
                if(resourcesClosed){propagateCloseFailure(closeFailure);return;}
                resourcesClosed=true;actual=nextResources;
            }
            Throwable failure=null;
            try {stopPublicRequests();}catch(RuntimeException|Error cause){failure=cause;}
            try {failure=mergeCloseFailure(failure,closeRetainedCatalogResources());}
            catch(RuntimeException|Error cause){failure=mergeCloseFailure(failure,cause);}
            try {decisionDisplay.close();}
            catch(IOException|RuntimeException|Error cause){failure=mergeCloseFailure(failure,cause);}
            java.util.concurrent.CompletionStage<Void> drained;
            try {
                if(actual!=null){actual.close();drained=actual.closeCompletion();}
                else if(ordinaryOffline!=null){drained=ordinaryOffline.closeStorageAfterDrain(ordinaryStorage);}
                else {storageGuard().close();drained=java.util.concurrent.CompletableFuture.completedFuture(null);}
            }catch(IOException|RuntimeException|Error cause){
                failure=mergeCloseFailure(failure,cause);drained=java.util.concurrent.CompletableFuture.failedFuture(cause);
            }
            final Throwable recorded=failure;
            synchronized(this){closeFailure=recorded;}
            drained=drained.handle((ignored,drainFailure)->{
                Throwable retained;
                synchronized(this){
                    closeFailure=mergeCloseFailure(closeFailure,originalCloseFailure(drainFailure));
                    retained=closeFailure;
                }
                if(retained!=null)throw new java.util.concurrent.CompletionException(retained);
                return null;
            });
            synchronized(this){closeCompletion=drained;}
            propagateCloseFailure(recorded);
        }
        private static Throwable originalCloseFailure(Throwable failure){
            while((failure instanceof java.util.concurrent.CompletionException
                    ||failure instanceof java.util.concurrent.ExecutionException)&&failure.getCause()!=null)
                failure=failure.getCause();
            return failure;
        }
        private static void propagateCloseFailure(Throwable failure){
            if(failure instanceof Error error)throw error;
            if(failure instanceof RuntimeException runtime)throw runtime;
            if(failure instanceof IOException io)throw new UncheckedIOException("actual Core resource/storage release failed",io);
            if(failure!=null)throw new IllegalStateException("actual Core resource/storage release failed",failure);
        }
        private static Throwable mergeCloseFailure(Throwable original,Throwable next){
            if(original==null)return next;if(next!=null&&next!=original)original.addSuppressed(next);return original;
        }
        public synchronized java.util.concurrent.CompletionStage<Void> closeCompletion(){
            return Objects.requireNonNull(closeCompletion,"Core has not yet initiated its real resource close");
        }
        /** Validate the real lifecycle-created Game before installing any replacement catalog. No Game is created here. */
        public void requireCreatedNextGame(ContinuityStorePort.Session same,RootApplicationSession previous,
                ActionReceipt parent,ManagedGameSession actual,G2Source source,Instant deadline)throws IOException {
            writer.requireSession(same);Objects.requireNonNull(previous);Objects.requireNonNull(parent);
            Objects.requireNonNull(actual);Objects.requireNonNull(source);Objects.requireNonNull(deadline);
            synchronized(this) {
                StrictJson.require(activeSession==previous&&previous.ownedBy(this)&&previous.isRetired()
                        &&activeLifecycle!=null&&pendingRestore==null&&restoreCandidate==null&&clock.instant().isBefore(deadline),
                        "replacement resources require the exact retired current NEXT owner and bounded deadline");
                var original=pendingNext!=null?pendingNext.original:nextAttempt!=null?nextAttempt.original:
                        activeLifecycle.requireNextEpisodeAdoption(same,parent);
                if(pendingNext!=null||nextAttempt!=null) {
                    StrictJson.require(original.parent().equals(parent),"retained replacement resources crossed their canonical NEXT parent");
                    var proof=activeLifecycle.requireRetainedEpisode(same,original.parent(),original.proof());
                    StrictJson.require(proof==original.proof(),"retained resource custody lost its original private lifecycle proof");
                }
                var nativeOwner=original.replacement();actual.verify();
                StrictJson.require(previous.identity().game().equals(nativeOwner.oldGame())
                        &&actual.generation().equals(nativeOwner.newGame())&&actual.sessionId().equals(nativeOwner.sessionId())
                        &&actual.machineId().equals(previous.identity().machineId())&&actual.machineId().equals(source.machineId())
                        &&actual.nativeTransport().pipeName().equals(nativeOwner.pipeName()),
                        "catalog preparation crossed the actual lifecycle-created Game birth/session/source/pipe");
                if(pendingNext!=null)StrictJson.require(pendingNext.previous==previous&&pendingNext.replacement==actual
                        &&pendingNext.original.parent().equals(parent)&&pendingNext.source.equals(source),
                        "replacement resources conflict with the retained original NEXT stage");
            }
        }
        /** Consume the actual returned report before presenting it or allowing a later batch. It never runs another turn. */
        RootApplicationSession afterTurn(RootApplicationSession previous,BatchReport report,Instant deadline)
                throws IOException,InterruptedException {
            Objects.requireNonNull(previous);Objects.requireNonNull(report);Objects.requireNonNull(deadline);
            StrictJson.require(report.session().equals(previous.identity()),"post-turn report crossed its original Root session");
            if(report.terminal()!=BatchReport.Terminal.EPISODE_HANDOFF)return previous;
            var parents=report.lifecycleTurns().stream().map(turn->turn.receipt()).filter(receipt->
                    receipt.state() instanceof ActionState.CompositeSettled settled
                    &&settled.settlement() instanceof ActionState.LifecycleApplied applied
                    &&applied.proof().kind()==org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind.NEXT_EPISODE).toList();
            if(parents.isEmpty())return previous;
            StrictJson.require(parents.size()==1,"one old Game cannot hand off multiple actual NEXT parents");
            RootStartupNextResources.Prepared producer;
            synchronized(this){producer=nextResources;}
            if(producer==null)throw new IOException("INCOMPLETE_ROOT_RUNTIME: actual startup NEXT resources producer is not bound; original report/parent retained without replay");
            producer.requireCore(this);
            var resources=producer.prepare(previous,parents.getFirst(),deadline);
            return completeNextEpisode(previous,parents.getFirst(),resources,deadline);
        }
        /** Transfers the real published next episode's existing owner; this stage grants no ordinary or host admission. */
        public NextEpisodeStage nextEpisodeStage(RootApplicationSession previous, ActionReceipt canonicalParent,
                ManagedGameSession replacement, G2Source source, RootInstalledCatalog replacementCatalog,
                int retainedFrames, Instant deadline)
                throws IOException, InterruptedException {
            Objects.requireNonNull(previous); Objects.requireNonNull(canonicalParent); Objects.requireNonNull(replacement);
            Objects.requireNonNull(source); Objects.requireNonNull(deadline);
            Objects.requireNonNull(replacementCatalog);
            StrictJson.require(retainedFrames >= 2 && retainedFrames <= 4096, "bounded next episode retained frames required");
            return previous.withRetiredRootStage(this, () -> {
                try {
                    return writer.locked(same -> {
                        writer.requireSession(same);
                        synchronized (this) {
                            if (pendingNext != null) {
                                StrictJson.require(pendingNext.previous == previous && pendingNext.replacement == replacement
                                        && pendingNext.original.parent().equals(canonicalParent) && pendingNext.source.equals(source)
                                        && pendingNext.catalog == replacementCatalog
                                        && pendingNext.retainedFrames == retainedFrames && pendingNext.deadline.equals(deadline),
                                        "a retained next episode transfer cannot be renamed or rebound to another original");
                                if(pendingNext.begun==null)requireNextStage(same,pendingNext);else requireRetainedNextStage(same,pendingNext); return pendingNext;
                            }
                            StrictJson.require(activeSession == previous && pendingRestore == null && restoreCandidate == null
                                    && activeLifecycle != null && pendingNext == null,
                                    "only the actual retired current Root can enter its unique next episode transfer");
                            StrictJson.require(clock.instant().isBefore(deadline), "next episode Root transfer deadline expired");
                            replacement.verify();
                            var context = replacementCatalog.context();
                            StrictJson.require(context.core() == this && context.game() == replacement
                                    && context.source().equals(source) && context.archive() == archive && context.writer() == writer,
                                    "next episode requires the actual replacement catalog under the sole original Core");
                            if (nextAttempt == null) {
                                StrictJson.require(!nextStageEntered, "a partial NEXT candidate construction cannot be replayed");
                                var original = activeLifecycle.requireNextEpisodeAdoption(same, canonicalParent);
                                var nativeOwner = original.replacement();
                                StrictJson.require(previous.identity().game().equals(nativeOwner.oldGame())
                                        && replacement.generation().equals(nativeOwner.newGame())
                                        && replacement.sessionId().equals(nativeOwner.sessionId())
                                        && replacement.machineId().equals(previous.identity().machineId())
                                        && replacement.machineId().equals(source.machineId())
                                        && replacement.nativeTransport().pipeName().equals(nativeOwner.pipeName()),
                                        "actual next episode replacement differs in full Game birth, session, source machine or pipe");
                                if (previous.capabilityRuntime().readHistoryPublisher().hasPending(same))
                                    throw new IOException("unpublished original READ history prevents next episode owner transfer");
                                previous.retainNextAutoPresentation(same, canonicalParent, original.originalParentFacts());
                                nextStageEntered = true;
                                DriverCapabilityRuntime candidate = previous.capabilityRuntime().nextCandidate(same, original, archive,
                                        () -> { try { return writer.borrowedSession(); } catch (IOException failure) { throw new UncheckedIOException(failure); } },
                                        replacementCatalog.bindings(), replacementCatalog.capabilityFiles(),
                                        replacementCatalog.retreatDomain());
                                candidate.bindCurrentOptions(replacementCatalog.remainingDomains().events()::issueCurrentOptions);
                                nextAttempt = new NextEpisodeAttempt(previous, canonicalParent, replacement, source, replacementCatalog,
                                        retainedFrames, deadline, original, candidate);
                            }
                            NextEpisodeAttempt attempt = nextAttempt;
                            StrictJson.require(attempt.previous == previous && attempt.parent.equals(canonicalParent)
                                    && attempt.replacement == replacement && attempt.source.equals(source) && attempt.catalog == replacementCatalog
                                    && attempt.retainedFrames == retainedFrames && attempt.deadline.equals(deadline),
                                    "an entered NEXT transfer retains its exact original adoption and candidate inputs");
                            var original = attempt.original;
                            var nativeOwner = original.replacement();
                            attempt.candidate.requireNextCandidate(same, original, previous.driver().authority());
                            StrictJson.require(previous.identity().game().equals(nativeOwner.oldGame())
                                    && replacement.generation().equals(nativeOwner.newGame())
                                    && replacement.sessionId().equals(nativeOwner.sessionId())
                                    && replacement.machineId().equals(previous.identity().machineId())
                                    && replacement.machineId().equals(source.machineId())
                                    && replacement.nativeTransport().pipeName().equals(nativeOwner.pipeName()),
                                    "actual next episode replacement differs in full Game birth, session, source machine or pipe");
                            DriverBootstrap.Adopted transferred = archive.inSession(same, bound -> {
                                try {
                                    return DriverBootstrap.adoptNextEpisode(previous.driver(), original, same, replacement.nativeTransport(), source, attempt.candidate,
                                            archive, writer::borrowedSession,
                                            (ref, maximum) -> RootOriginalArtifacts.readNext(writer, archive, same, ref, maximum, source.sourceRef(), original,
                                                    attempt.candidate, previous.driver().authority()),
                                            retainedFrames, deadline);
                                } catch (IOException failure) { throw new UncheckedIOException(failure); }
                                catch (InterruptedException interrupted) { throw new InterruptedAssembly(interrupted); }
                            });
                            StrictJson.require(transferred.repository() == previous.driver().repository()
                                    && transferred.authority() == previous.driver().authority()
                                    && transferred.producer() == previous.driver().producer()
                                    && transferred.status() == DriverBootstrap.AdoptionStatus.QUALIFICATION_REQUIRED
                                    && transferred.session().game().equals(nativeOwner.newGame())
                                    && transferred.session().sessionId().equals(nativeOwner.sessionId()),
                                    "next episode transfer must retain the sole repository, authority and public-revision producer");
                            attempt.candidate.requireNextCandidate(same, original, previous.driver().authority());
                            NextEpisodeStage stage = new NextEpisodeStage(this, previous, replacement, original, transferred, source,
                                    replacementCatalog, attempt.candidate, retainedFrames, deadline);
                            adopted.add(transferred); pendingNext = stage; return stage;
                        }
                    });
                } catch (UncheckedIOException failure) { throw failure.getCause(); }
                catch (InterruptedAssembly interrupted) { Thread.currentThread().interrupt(); throw interrupted.interruption; }
            });
        }

        private void requireNextStage(ContinuityStorePort.Session same, NextEpisodeStage stage) throws IOException {
            writer.requireSession(same);
            synchronized (this) {
                StrictJson.require(stage != null && stage.owner == this && pendingNext == stage && activeSession == stage.previous
                        && stage.previous.isRetired() && adopted.contains(stage.driver), "actual next episode Root transfer custody is not current");
                StrictJson.require(clock.instant().isBefore(stage.deadline), "original next episode transfer deadline expired");
                stage.candidate.requireNextCandidate(same, stage.original, stage.previous.driver().authority()); stage.replacement.verify();
            }
        }
        private void requireRetainedNextStage(ContinuityStorePort.Session same, NextEpisodeStage stage) throws IOException {
            writer.requireSession(same);
            synchronized (this) {
                StrictJson.require(stage != null && stage.owner == this && pendingNext == stage && activeSession == stage.previous
                        && stage.previous.isRetired() && stage.previous.ownedBy(this) && adopted.contains(stage.driver)
                        && stage.catalog.context().core() == this && stage.catalog.context().game() == stage.replacement
                        && stage.catalog.context().source().equals(stage.source),
                        "retained NEXT originals belong to another actual Root transfer");
                StrictJson.require(clock.instant().isBefore(stage.deadline), "original NEXT qualification deadline expired");
                var actual = activeLifecycle.requireRetainedEpisode(same, stage.original.parent(), stage.original.proof());
                StrictJson.require(actual == stage.original.proof(), "the original lifecycle issuer did not retain this exact NEXT proof");
                stage.replacement.verify();
            }
        }

        /** The checkpoint service is built before its real SAVE effect is registered in the live executable catalog. */
        public RootApplicationSession finishFresh(RootInstalledCatalog installed,DriverBootstrap.Adopted driver,FreshSessionConfiguration configuration,FreshSessionServices services)throws IOException,InterruptedException{
            StrictJson.require(driver.status()==DriverBootstrap.AdoptionStatus.FRESH_OBSERVED,"fresh finish requires the actual first-map Driver");
            return finishObserved(installed, driver, configuration, services, Optional.empty());
        }

        public RootApplicationSession finishCleanRestart(RootInstalledCatalog installed,DriverBootstrap.Adopted driver,FreshSessionConfiguration configuration,FreshSessionServices services)throws IOException,InterruptedException{
            StrictJson.require(cleanRestartAdmission != null, "clean restart admission required");
            StrictJson.require(cleanRestartPolicy.equals(configuration.cyclePolicy()), "clean restart policy mismatch");
            driver.requireCleanRestart(cleanRestartAdmission);
            return finishObserved(installed, driver, configuration, services, Optional.of(cleanRestartAdmission));
        }

        public RootApplicationSession finishSettledSameGame(RootInstalledCatalog installed,DriverBootstrap.Adopted driver,
                FreshSessionConfiguration configuration,FreshSessionServices services)throws IOException,InterruptedException {
            StrictJson.require(settledSameGameData!=null&&settledSameGamePolicy.equals(configuration.cyclePolicy()),
                    "settled continuation retains its actual data and cycle policy");
            driver.requireSettledSameGame(settledSameGameData);
            return finishObserved(installed,driver,configuration,services,Optional.empty());
        }

        public RootApplicationSession finishUnresolvedSameGame(RootInstalledCatalog installed,DriverBootstrap.Adopted driver,FreshSessionConfiguration configuration,FreshSessionServices services)throws IOException,InterruptedException{
            StrictJson.require(unresolvedSameGameData != null, "unresolved same-game data required");
            StrictJson.require(unresolvedSameGamePolicy.equals(configuration.cyclePolicy()), "unresolved same-game policy mismatch");
            return finishObserved(installed, driver, configuration, services, Optional.empty());
        }

        private RootApplicationSession finishObserved(RootInstalledCatalog installed,DriverBootstrap.Adopted driver,FreshSessionConfiguration configuration,FreshSessionServices services,Optional<org.xar.ck3.control.application.session.ContinuityBatchJournal.CleanRestartAdmission> admissionOpt)throws IOException,InterruptedException{
            var context=installed.context();
            var game=context.game();
            var source=context.source();
            var sources=context.sources();
            var originals=context.originals();
            var frameLoader=context.frameLoader();
            var remaining=installed.remainingDomains();
            var policy=configuration.policy();
            var freshness=configuration.freshness();
            var files=services.files();
            var checkpoints=configuration.checkpoints();
            var cyclePolicy=configuration.cyclePolicy();
            var deadline=configuration.deadline();
            var offline=services.offline();
            var sessionClock=services.sessionClock();
            var episodes=services.episodes();
            var savedCapture=services.savedCapture();
            var restoreMaterials=services.restoreMaterials();
            var restorePublication=services.restorePublication();
            var authorityId=configuration.authorityId();

            installed.bindPhysicalDriver(driver);
            var staged=unresolvedSameGameData==null
                    ?stage(driver,game,sources,policy,freshness,files,checkpoints.driverCheckpoint(),checkpoints.checkpointEvidence(),checkpoints.attachmentEvidence(),remaining.lifecycle().seedAdoption(),checkpoints.lineageId(),checkpoints.save())
                    :stageReadonly(driver,game,sources,policy,freshness,files,checkpoints.driverCheckpoint(),checkpoints.checkpointEvidence(),checkpoints.attachmentEvidence(),remaining.lifecycle().seedAdoption(),checkpoints.lineageId(),checkpoints.save());
            installed.bindSave(staged);

            var readiness=new RootRuntimeReadiness(this,policy,freshness,clock);

            return writer.locked(same->{
                writer.requireSession(same);
                var runtime=readiness.initial(same,installed,staged,deadline);
                var life=remaining.life();life.requireContext(context);
                var physical=remaining.lifecycle().physical();
                var derived=RootDerivedChildAuthority.install(context,installed.bindings(),life.infrastructure());
                var historyQualification=new RootUnresolvedHistoryQualification(writer,archive,driver.authority(),installed.readHistory(),installed.bindings().readCatalog());
                var pendingBinding=new ReconciliationPendingBinding(writer,archive,originals,historyQualification);
                var historyEpoch=historyQualification.captureEpoch(same);
                archive.bindReconciliationHistory(same,pendingBinding,historyEpoch);
                if(archive.reconciliationHistoryBinding(historyEpoch)!=pendingBinding)
                    throw new IOException("initial reconciliation archive lost the identical qualified history binding");
                var reconciliation=new RootReconciliationAuthority(writer,archive,physical,pendingBinding,originals,frameLoader,installed.bindings().readCatalog(),remaining.reconciliationReads(),clock);
                derived.requireOwner(context,installed.bindings());
                staged.prepareDispatcher(authorityId,installed.bindings(),installed.frontend().authority(),physical,reconciliation,remaining.lifecycle().closeAdmission(),derived.admission(),derived.replay(),runtime.capabilities(),installed.readHistory(),installed.pendingBindings(),installed.requiredPending(),remaining.lifeReplay());
                var actualOffline=offline.install(installed,remaining.events().eventSources());actualOffline.requireContext(installed);
                var root=staged.finish(authorityId,installed.bindings(),installed.frontend().authority(),physical,reconciliation,remaining.lifecycle().closeAdmission(),remaining.lifecycle().terminalDecisions(),remaining.lifecycle(),derived.admission(),derived.replay(),runtime.capabilities(),installed.readHistory(),remaining.lifeReplay(),runtime.planningInputs(),installed.pipeline(),installed.pendingBindings(),installed.requiredPending(),cyclePolicy,actualOffline.port(),sessionClock,Optional.empty(),0,installed.completion(),episodes,savedCapture,restoreMaterials,restorePublication);
                if(admissionOpt.isPresent()){
                    try { root.restoreCleanRestart(same,admissionOpt.orElseThrow()); }
                    catch(InterruptedException interrupted) {
                        Thread.currentThread().interrupt();
                        var failure=new java.io.InterruptedIOException("same-Game Controller restoration interrupted");
                        failure.initCause(interrupted);throw failure;
                    }
                    runtime.capabilities().initializePlanning(same,driver.first());
                } else if(settledSameGameData!=null) {
                    // Staged.finish has now sealed this Core's real cycle authority router.
                    settledSameGameBatches.recoverSettledSameGame(same,settledSameGameData,
                            Objects.requireNonNull(settledSameGameSemantic,"actual settled adoption SEM is missing"));
                    try {root.restoreSettledSameGame(same,settledSameGameData);}
                    catch(InterruptedException interrupted){
                        Thread.currentThread().interrupt();
                        var failure=new java.io.InterruptedIOException("settled same-Game Controller restoration interrupted");
                        failure.initCause(interrupted);throw failure;
                    }
                    runtime.capabilities().restoreRetainedPlanning(same);
                } else if (unresolvedSameGameData != null) {
                    // Restore the existing per-graph reader without capture/publication or canonical head changes.
                    runtime.capabilities().restoreRetainedPlanning(same);
                } else {
                    if (initialRecoveryAdmission != null) {
                        initialRecoveryAdmission.requireCurrent(same);
                        driver.requireInitialRecovery(initialRecoveryAdmission);
                        if(initialNoDispatchProof!=null){
                            initialNoDispatchBatches.finishInitialNoDispatchRecovery(same,initialNoDispatchProof,
                                    Objects.requireNonNull(initialNoDispatchSemantic));
                        }
                        installed.initializeFresh(same, driver.first(), deadline);
                        if(initialNoDispatchProof!=null&&initialNoDispatchProof.capturedManifest().isPresent())
                            runtime.capabilities().initializePlanning(same,driver.first());
                        else installed.initializePersistentPlanning(same, driver.first());
                        if(initialNoDispatchProof!=null){
                            try { root.restoreInitialNoDispatchRecovery(same,initialNoDispatchProof); }
                            catch(InterruptedException interrupted){
                                Thread.currentThread().interrupt();
                                var failure=new java.io.InterruptedIOException("initial no-dispatch Controller restoration interrupted");
                                failure.initCause(interrupted);throw failure;
                            }
                        }
                    } else {
                        observedEntry.commitInitial(same);
                        installed.initializeFresh(same, driver.first(), deadline);
                        installed.initializePersistentPlanning(same, driver.first());
                    }
                }
                return root;
            });
        }

        public synchronized Staged stage(DriverBootstrap.Adopted driver, ManagedGameSession game,
                RootNativeSourceAuthority sources, NativeReadiness.Policy policy, Duration freshness,
                CheckpointFiles files, Path driverCheckpointPath, Path checkpointEvidence,
                Path attachmentEvidence, CheckpointService.SeedAdoptionPort seeds, String lineageId, Path savePath) throws IOException {
            StrictJson.require(!staged&&!finished&&adopted.contains(driver),"stage requires this Core's original adopted Driver once");
            StrictJson.require(driver.status()==DriverBootstrap.AdoptionStatus.FRESH_OBSERVED
                    ||driver.status()==DriverBootstrap.AdoptionStatus.QUALIFICATION_REQUIRED,
                    "unresolved or incomplete action history cannot stage gameplay authority");
            return stagePhysical(driver,game,sources,policy,freshness,files,driverCheckpointPath,checkpointEvidence,attachmentEvidence,seeds,lineageId,savePath);
        }

        private synchronized Staged stageReadonly(DriverBootstrap.Adopted driver, ManagedGameSession game,
                RootNativeSourceAuthority sources, NativeReadiness.Policy policy, Duration freshness,
                CheckpointFiles files, Path driverCheckpointPath, Path checkpointEvidence,
                Path attachmentEvidence, CheckpointService.SeedAdoptionPort seeds, String lineageId, Path savePath) throws IOException {
            StrictJson.require(!staged&&!finished&&adopted.contains(driver)&&unresolvedSameGameData!=null
                    &&driver.status()==DriverBootstrap.AdoptionStatus.READ_ONLY_UNRESOLVED,
                    "readonly reconstruction requires this Core's actual unresolved Driver");
            return stagePhysical(driver,game,sources,policy,freshness,files,driverCheckpointPath,checkpointEvidence,attachmentEvidence,seeds,lineageId,savePath);
        }

        private Staged stagePhysical(DriverBootstrap.Adopted driver, ManagedGameSession game,
                RootNativeSourceAuthority sources, NativeReadiness.Policy policy, Duration freshness,
                CheckpointFiles files, Path driverCheckpointPath, Path checkpointEvidence,
                Path attachmentEvidence, CheckpointService.SeedAdoptionPort seeds, String lineageId, Path savePath) throws IOException {
            game.verify(); NativeGameTransport transport = game.nativeTransport();
            SessionIdentity identity = new SessionIdentity(game.machineId(), game.generation(), game.sessionId());
            StrictJson.require(driver.session().game().equals(identity.game()) && driver.session().sessionId().equals(identity.sessionId())
                    && driver.source().machineId().equals(identity.machineId()), "adopted Driver and managed native owner differ");
            InputLink inputs = new InputLink(writer);
            DriverCheckpointStore checkpoints = new DriverCheckpointStore(files, driverCheckpointPath, transport.pipeName(), new FrozenDriverSnapshotSupplier(driver.authority()));
            NativeReadinessCollector collector = new NativeReadinessCollector(identity, writer, transport, driver.authority(), assembler,
                    game, (borrowed, role, bytes) -> archive.preserveArtifact(borrowed, bytes, role.maximumBytes()),
                    semanticVerifier, sources, inputs::capabilities, inputs::planning, policy, freshness, clock);
            collector.bindObservationSession(writer::requireSession);
            collector.bindActiveObservationSession(writer::activeSession);
            CheckpointService service = new CheckpointService(files, checkpoints, collector.checkpoint(lineageId), checkpointEvidence, clock, seeds);
            service.bindEvidence(archive, writer::borrowedSession, writer::requireSession);
            CheckpointRequestFactory requests = new CheckpointRequestFactory(savePath, collector.checkpoint(lineageId));
            staged = true;
            return new Staged(this, identity, driver, game, inputs, collector, service, requests, files, checkpoints, attachmentEvidence,
                    null, reads, knownReads);
        }
        /** One actual post-turn NEXT handoff. Every input is retained from the real installed replacement catalog.
         * This method is called only after the original Controller has returned and retired; it never executes another turn.
         */
        public RootApplicationSession completeNextEpisode(RootApplicationSession previous,ActionReceipt canonicalParent,
                RootNextEpisodeAssemblyInputs.SessionResources resources,Instant deadline)throws IOException,InterruptedException {
            Objects.requireNonNull(resources);Objects.requireNonNull(previous);Objects.requireNonNull(canonicalParent);
            synchronized(this) {
                if(lastPublishedNext!=null&&lastPublishedNext.previous==previous&&lastPublishedNext.original.parent().equals(canonicalParent)) {
                    StrictJson.require(lastPublishedNext.assemblyResources==resources&&activeSession==lastPublishedNext.publishedSuccessor
                            &&lastPublishedNext.publishedSuccessor.hasInstalledHost(),"completed NEXT retry changed its actual resources or current published owner");
                    return lastPublishedNext.publishedSuccessor;
                }
            }
            StrictJson.require(resources.core()==this,"NEXT assembly resources belong to another original Core");
            var catalog=resources.catalog();
            var next=nextEpisodeStage(previous,canonicalParent,catalog.context().game(),catalog.context().source(),catalog,resources.retainedFrames(),deadline);
            return previous.withRetiredRootStage(this,()->withBorrowed(()->{
                var same=activeBorrowedSession();
                synchronized(this) {
                    if(next.assemblyResources==null)next.assemblyResources=resources;
                    else StrictJson.require(next.assemblyResources==resources,"NEXT retry cannot replace the actual retained resource products");
                    if(next.assemblyInputs==null) {
                        StrictJson.require(!next.assemblyInputsEntered,"partial actual NEXT input construction cannot be replayed");
                        next.assemblyInputsEntered=true;next.assemblyInputs=RootNextEpisodeAssemblyInputs.create(same,next,resources);
                    }
                }
                var values=next.assemblyInputs;var paths=values.checkpoints();
                if(next.checkpointStage==null) {
                    values.prepareDirectories(same);
                    nextCheckpointStage(next,values.policy(same),paths.freshness(),paths.files(),paths.driverCheckpointPath(),
                            paths.checkpointEvidence(),paths.attachmentEvidence(),paths.seeds(),paths.lineageId(),paths.savePath());
                }
                var staged=next.checkpointStage;var dispatch=values.dispatcher(same,staged);
                staged.prepareDispatcher(dispatch.authorityId(),dispatch.bindings(),dispatch.frontend(),dispatch.lifecycle(),dispatch.reconciliation(),
                        dispatch.closeAdmission(),dispatch.derivedChildren(),dispatch.derivedReplay(),dispatch.capabilities(),dispatch.readHistory(),
                        dispatch.pending(),dispatch.requiredPending(),dispatch.actualLifeFrames());
                var begun=beginNextEpisode(same,next,deadline);firstNextCheckpoint(same,begun,staged,deadline);
                var baseline=baselineNextEpisode(same,next);captureNextBaseline(same,next,deadline);
                initializeNextDomains(same,next);rebindNextBaseline(same,next);
                RootApplicationSession successor=next.hostCandidate;
                if(successor==null) {
                    var finish=values.finish(same,staged,baseline);
                    successor=staged.finish(finish.authorityId(),finish.bindings(),finish.frontend(),finish.lifecycle(),finish.reconciliation(),
                            finish.closeAdmission(),finish.terminalDecisions(),finish.actualLifecycleRuntime(),finish.derivedChildren(),finish.derivedReplay(),
                            finish.capabilities(),finish.readHistory(),finish.actualLifeFrames(),finish.planningInputs(),finish.pipeline(),finish.pending(),
                            finish.requiredPending(),finish.cyclePolicy(),finish.offline(),finish.sessionClock(),finish.baseline(),finish.admittedSavedDays(),
                            finish.completion(),finish.episodes(),finish.savedCaptureFactory(),finish.restoreMaterials(),finish.restorePublication());
                }
                publishNextSession(same,next,successor,deadline);return successor;
            }));
        }
        /** Candidate-only checkpoint resources; constructing them never replaces the public Root or its action View. */
        public synchronized Staged nextCheckpointStage(NextEpisodeStage original,NativeReadiness.Policy policy,Duration freshness,
                CheckpointFiles files,Path driverCheckpointPath,Path checkpointEvidence,Path attachmentEvidence,
                CheckpointService.SeedAdoptionPort seeds,String lineageId,Path savePath)throws IOException {
            StrictJson.require(pendingNext==Objects.requireNonNull(original)&&activeSession==original.previous&&finished,
                    "checkpoint staging requires the exact privately transferred NEXT owner");
            if(original.checkpointStageEntered)throw new IOException("actual NEXT checkpoint resource construction already entered; retain its original stage or failure");
            original.checkpointStageEntered=true;
            var same=writer.borrowedSession();original.requireCurrent(same);
            var runtime=original.catalog;var game=original.replacement;var driver=original.driver;
            runtime.bindPhysicalDriver(driver);
            var planning=runtime.planningInputs(driver,original.candidate);
            var inputs=new InputLink(writer);inputs.bind(original.candidate,planning);
            var checkpoints=new DriverCheckpointStore(files,driverCheckpointPath,game.nativeTransport().pipeName(),new FrozenDriverSnapshotSupplier(driver.authority()));
            var collector=new NativeReadinessCollector(sessionIdentity(driver),writer,game.nativeTransport(),driver.authority(),assembler,game,
                    (lease,role,bytes)->archive.preserveArtifact(lease,bytes,role.maximumBytes()),semanticVerifier,runtime.context().sources(),
                    inputs::capabilities,inputs::planning,policy,freshness,clock);
            collector.bindObservationSession(writer::requireSession);collector.bindActiveObservationSession(writer::activeSession);
            var checkpointObservations=collector.checkpointFirst(lineageId,new NativeReadinessCollector.FirstCheckpointAdmission(){
                @Override public void requireStage(ContinuityStorePort.Session same,SessionIdentity expected,Instant actualDeadline)throws IOException {
                    writer.requireSession(same);
                    StrictJson.require(sessionIdentity(original.driver).equals(expected)&&original.checkpointStage!=null
                            &&original.checkpointStage.collector==collector&&clock.instant().isBefore(actualDeadline)
                            &&!actualDeadline.isAfter(original.deadline),"first checkpoint observation crossed its actual private stage/collector/deadline");
                    if(original.begun==null)original.requireCurrent(same);
                    else {original.requireRetainedOriginal(same);nextWindows.requireBegun(same,original.begun);}
                }
                @Override public java.math.BigInteger requirePhysical(ContinuityStorePort.Session same,SessionIdentity expected,
                        DriverObservationAssembler.Complete frame,DriverSnapshotFacts.Known known,
                        SessionPorts.SemanticEvidence semantic,NativeReadinessCollector.SourceQualification sources,Instant actualDeadline)throws IOException {
                    requireStage(same,expected,actualDeadline);
                    var first=original.driver.first().identity();
                    StrictJson.require(frame.source().equals(original.source)&&frame.sessionId().equals(expected.sessionId())
                            &&frame.identity().machineId().equals(expected.machineId())&&frame.identity().game().equals(expected.game())
                            &&frame.identity().frame().episodeRunId().equals(first.frame().episodeRunId())
                            &&frame.identity().frame().identity().player().equals(first.frame().identity().player())
                            &&known.stamp().game().equals(expected.game())&&semantic.frame().equals(frame.identity()),
                            "first checkpoint physical material differs from the true privately adopted actor/episode/source");
                    sources.assertCurrent(same);return first.frame().identity().player();
                }
            });
            var ordinaryObservations=collector.checkpoint(lineageId);
            CheckpointRequest.ObservationPort routedObservations=new CheckpointRequest.ObservationPort(){
                @Override public CheckpointRequest.Readiness observe(Instant until)throws InterruptedException {
                    if(original.publishedSuccessor==null)return checkpointObservations.observe(until);
                    try {
                        var borrowed=writer.borrowedSession();requireAdmittedNext(borrowed,original,original.baselined,runtime,original.candidate);
                        return ordinaryObservations.observe(until);
                    }catch(IOException unavailable){throw new UncheckedIOException("actual published NEXT checkpoint owner unavailable",unavailable);}
                }
                @Override public CheckpointRequest.Readiness observeForPreparation(
                        org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity expected,Instant until)throws InterruptedException {
                    if(original.publishedSuccessor==null)return checkpointObservations.observeForPreparation(expected,until);
                    try {
                        var borrowed=writer.borrowedSession();requireAdmittedNext(borrowed,original,original.baselined,runtime,original.candidate);
                        return ordinaryObservations.observeForPreparation(expected,until);
                    }catch(IOException unavailable){throw new UncheckedIOException("actual published NEXT checkpoint owner unavailable",unavailable);}
                }
            };
            var checkpointService=new CheckpointService(files,checkpoints,routedObservations,checkpointEvidence,clock,seeds);
            checkpointService.bindEvidence(archive,writer::borrowedSession,writer::requireSession);
            var requests=new CheckpointRequestFactory(savePath,routedObservations);
            var staged=new Staged(this,sessionIdentity(driver),driver,game,inputs,collector,checkpointService,requests,files,checkpoints,
                    attachmentEvidence,null,runtime.context().reads(),new RootKnownReadObserver(writer));
            staged.nextEpisode=original;staged.firstObservations=checkpointObservations;staged.ordinaryObservations=ordinaryObservations;runtime.bindReadiness(driver,collector);
            staged.bindReadyPublication(runtime.readyPublication());staged.bindPlanningEvidence(runtime.planningEvidence());
            var actualLifecycle=runtime.remainingDomains().lifecycle();
            staged.bindPhysicalLifecycle(actualLifecycle.physical(),actualLifecycle.composite());
            actualLifecycle.bindStage(staged);runtime.bindSave(staged);
            staged.prepareCheckpointStores(original.previous.cycles(),savedCaptureFactory);
            original.checkpointStage=staged;return staged;
        }
        /** Exactly one source-owned request is retained across canonical reconciliation; no second first SAVE is manufactured. */
        public FirstCheckpointVerifier.VerifiedFirstCheckpoint firstNextCheckpoint(ContinuityStorePort.Session same,
                RootNextEpisodeWindowRuntime.Begun begun,Staged actual,Instant deadline)throws IOException,InterruptedException {
            writer.requireSession(same);Objects.requireNonNull(actual);Objects.requireNonNull(deadline);
            synchronized(this) {
                nextWindows.requireBegun(same,begun);
                StrictJson.require(actual.core==this&&actual.nextEpisode==begun.stage()&&begun.stage().checkpointStage==actual
                        &&actual.dispatcher!=null&&actual.game==begun.stage().replacement
                        &&clock.instant().isBefore(deadline)&&!deadline.isAfter(begun.stage().deadline),
                        "first SAVE requires the same actual staged dispatcher and original bounded NEXT deadline");
                if(actual.firstBegin!=null)StrictJson.require(actual.firstBegin==begun,"first SAVE cannot switch its private BEGIN");
                else actual.firstBegin=begun;
                if(actual.firstProof!=null){actual.firstVerifier.requireIssued(same,actual.firstProof);
                    if(actual.firstMaterial==null)actual.firstMaterial=actual.firstStore.capture(actual.firstProof);
                    captureFirstKernel(same,begun.stage(),actual);return actual.firstProof;}
            }
            try {
                return begun.stage().candidate.withCandidateScope(same,()->{
                    try {
                        if(actual.firstRequest==null)actual.firstRequest=actual.requests.prepare(begun.opening().frame(),begun.stage().source(),
                                actual.identity.sessionId(),Optional.empty(),deadline);
                        StrictJson.require(actual.firstRequest.baseline().isEmpty(),"the actual first SAVE cannot use a foreign or old episode baseline");
                        if(actual.firstGuard==null)actual.firstGuard=new RootFirstCheckpointGuard(writer,archive,
                                begun.stage().catalog.remainingDomains().lifecycle().physical(),begun.stage().catalog.bindings(),actual.identity,
                                begun.stage().source,actual.firstObservations,actual.firstRequest.saveCommand(),(borrowed,head,retained)->{
                                    writer.requireSession(borrowed);nextWindows.requireBegun(borrowed,begun);
                                    StrictJson.require(actual==begun.stage().checkpointStage&&actual.firstBegin==begun
                                            &&retained==actual.firstRequest.saveCommand()&&head.digest().equals(borrowed.head().digest()),
                                            "first SAVE guard lost its same private BEGIN/checkpoint request/writer point");
                                    begun.stage().requireRetainedOriginal(borrowed);
                                },clock,authorityId());

                        boolean resumeConfirmedMaterial=actual.firstResult instanceof CheckpointResult.Unknown unknown
                                &&unknown.action().filter(action->action.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                                        &&action.command().actionId().equals(actual.firstRequest.saveCommand().actionId())).isPresent();
                        if(actual.firstResult==null||resumeConfirmedMaterial)actual.firstResult=submissions.withFirstSave(same,this,currentSubmissionView(begun.stage().previous),
                                actual.dispatcher.view(),begun,actual.firstRequest.saveCommand(),actual.firstGuard,()->actual.checkpoints.checkpoint(actual.firstRequest));
                        if(!(actual.firstResult instanceof CheckpointResult.Confirmed confirmed))
                            throw new IOException("actual first SAVE remains unresolved or rejected; retain its original request and canonical receipt: "+actual.firstResult);
                        StrictJson.require(confirmed.advancedDays().signum()==0,"the first actual episode SAVE grants zero saved-day credit");
                        actual.firstProof=actual.firstVerifier.verifyCheckpoint(same,actual.identity,confirmed.pair(),begun.opening(),begun.committedBegin());
                        actual.firstMaterial=actual.firstStore.capture(actual.firstProof);
                        captureFirstKernel(same,begun.stage(),actual);return actual.firstProof;
                    }catch(InterruptedException interrupted){throw new InterruptedAssembly(interrupted);}
                });
            }catch(InterruptedAssembly interrupted){Thread.currentThread().interrupt();throw interrupted.interruption;}
        }
        /** The saved M7 inputs belong to the same actual per-Game store triplet; readiness kernel inputs are not a substitute. */
        private void captureFirstKernel(ContinuityStorePort.Session same,NextEpisodeStage next,Staged actual)throws IOException {
            writer.requireSession(same);StrictJson.require(next.checkpointStage==actual&&actual.firstProof!=null&&actual.firstMaterial!=null,
                    "first M7 projection requires the original verified SAVE and captured first material");
            if(actual.firstSavedKernel!=null) {
                StrictJson.require(actual.firstSavedKernel.pair().equals(actual.firstProof.pair())
                        &&actual.firstSavedKernel.materialWitness().equals(actual.firstMaterial.witness()),
                        "retained first M7 data crossed its original pair/material witness");return;
            }
            if(!(savedCaptureFactory instanceof RootM7CheckpointCaptureFactory factory))
                throw new IOException("first M7 data requires the concrete same-Core checkpoint capture factory");
            String head=same.head().digest();actual.firstStore.requireRetained(same,actual.firstMaterial);
            StrictJson.require(actual.firstMaterial.checkpoint().pair().equals(actual.firstProof.pair())
                    &&actual.firstMaterial.checkpoint().digest().equals(actual.firstProof.digest()),
                    "actual first material differs from its same private verified checkpoint");
            var context=next.catalog.context();var diagnostics=context.transport().diagnostics();
            var transport=diagnostics.session().orElseThrow(()->new IOException("actual first SAVE transport source is unavailable"));
            var qualification=context.sources().verifyPhysicalOrigin(same,transport,next.source,actual.firstProof.semantic().originalNativePacket(),
                    diagnostics,actual.firstRequest.saveCommand().deadline());
            var metadata=context.sources().optionalMetadata(same,qualification);
            var inputs=factory.requireInputs(actual.checkpointPairs(),actual.driverCheckpoints(),actual.savedSources());
            actual.firstSavedKernel=inputs.savedFirst(same,actual.firstVerifier,actual.firstProof,actual.firstMaterial.witness(),
                    next.source,metadata.map(RootNativeSourceAuthority.QualifiedMetadata::ownerSourceEpoch),
                    metadata.map(RootNativeSourceAuthority.QualifiedMetadata::gameExecutable),Optional.empty());
            if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);
            actual.firstStore.requireRetained(same,actual.firstMaterial);
            StrictJson.require(head.equals(same.head().digest()),"actual first M7 data capture changed the canonical writer head");
        }
        private RootSessionSwitchboard.View currentSubmissionView(RootApplicationSession expected) {
            StrictJson.require(activeSession==expected&&expected.isRetired(),"original retired Root authority changed before first SAVE");
            var current=submissions.current();StrictJson.require(current.identity().equals(expected.identity()),"original public action View changed before first SAVE");return current;
        }
        /** A genuinely later candidate SEM precedes BEGIN; immutable Bootstrap first material is never substituted for it. */
        public RootNextEpisodeWindowRuntime.Begun beginNextEpisode(ContinuityStorePort.Session same,NextEpisodeStage stage,
                Instant deadline)throws IOException {
            writer.requireSession(same);Objects.requireNonNull(stage);
            if(stage.begun!=null){stage.requireRetainedOriginal(same);nextWindows.requireBegun(same,stage.begun);return stage.begun;}
            requireNextStage(same,stage);
            StrictJson.require(stage.checkpointStage!=null&&stage.checkpointStage.dispatcher!=null
                    &&!deadline.isAfter(stage.deadline)&&clock.instant().isBefore(deadline),
                    "actual candidate checkpoint dispatcher must precede the private episode BEGIN");
            warmFirstCheckpoint(same,stage,deadline);
            if(stage.episodeInputs==null)stage.episodeInputs=new org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs(
                    writer,writer::requireSession,activeLifecycle,stage.driver.authority(),archive,semanticVerifier);
            if(stage.opening==null)stage.opening=stage.candidate.withCandidateScope(same,()->
                    stage.catalog.remainingDomains().lifecycle().physical().semantic(same,sessionIdentity(stage.driver),deadline));
            stage.begun=nextWindows.begin(same,stage,stage.episodeInputs,stage.opening);return stage.begun;
        }
        private void warmFirstCheckpoint(ContinuityStorePort.Session same,NextEpisodeStage stage,Instant deadline)throws IOException {
            StrictJson.require(stage.checkpointStage!=null&&stage.checkpointStage.firstObservations!=null,"actual first checkpoint observation port is missing");
            try {
                stage.candidate.withCandidateScope(same,()->{
                    try {
                        for(;;) {
                            StrictJson.require(clock.instant().isBefore(deadline),"the actual first checkpoint never reached bounded physical stability");
                            var observed=stage.checkpointStage.firstObservations.observe(deadline);
                            if(observed.mapReady()&&observed.paused()&&observed.saveEligible())return null;
                            long remaining=Duration.between(clock.instant(),deadline).toMillis();
                            if(remaining<=0)throw new IOException("actual first checkpoint physical stability deadline expired: "+observed.reason());
                            Thread.sleep(Math.min(100,remaining));
                        }
                    }catch(InterruptedException interrupted){throw new InterruptedAssembly(interrupted);}
                });
            }catch(InterruptedAssembly interrupted){Thread.currentThread().interrupt();var failure=new java.io.InterruptedIOException("actual first checkpoint physical stabilization interrupted");failure.initCause(interrupted.interruption);throw failure;}
            catch(UncheckedIOException failure){throw failure.getCause();}
        }
        /** Commits only the same verified first physical pair; this method never requests another SAVE. */
        public RootNextEpisodeWindowRuntime.Baselined baselineNextEpisode(ContinuityStorePort.Session same,NextEpisodeStage stage)
                throws IOException {
            writer.requireSession(same);stage.requireRetainedOriginal(same);
            StrictJson.require(stage.begun!=null&&stage.checkpointStage!=null&&stage.checkpointStage.firstProof!=null,
                    "BASELINE requires this actual BEGIN and its privately verified first SAVE");
            if(stage.baselined==null)stage.baselined=nextWindows.baseline(same,stage.begun,stage.checkpointStage.firstVerifier,stage.checkpointStage.firstProof);
            nextWindows.requireBaseline(same,stage.baselined);return stage.baselined;
        }
        /** The post-SAVE observation is new physical material, captured exclusively through the candidate callback. */
        public org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.NextBaselineBinding captureNextBaseline(
                ContinuityStorePort.Session same,NextEpisodeStage stage,Instant deadline)throws IOException {
            writer.requireSession(same);stage.requireRetainedOriginal(same);baselineNextEpisode(same,stage);
            StrictJson.require(clock.instant().isBefore(deadline)&&!deadline.isAfter(stage.deadline),"actual next baseline observation deadline expired");
            if(stage.baselineBinding!=null){stage.episodeInputs.requireCurrentBaseline(same,stage.baselineBinding);
                if(stage.firstBaselineMaterial==null)stage.firstBaselineMaterial=stage.checkpointStage.firstStore.captureBaseline(same,
                        stage.checkpointStage.firstMaterial,stage.baselined.committedBaseline(),stage.baselineBinding.semantic());
                checkpointVerifiers.registerNext(same,stage.baselineBinding,stage.checkpointStage.savedVerifier);
                return stage.baselineBinding;}
            return stage.candidate.withCandidateScope(same,()->{
                var fresh=stage.catalog.remainingDomains().lifecycle().physical().semantic(same,sessionIdentity(stage.driver),deadline);
                stage.baselineBinding=stage.episodeInputs.bindAfterBaseline(same,stage.begun.openingBinding(),stage.checkpointStage.firstVerifier,
                        stage.checkpointStage.firstProof,stage.baselined.committedBaseline(),fresh);
                stage.firstBaselineMaterial=stage.checkpointStage.firstStore.captureBaseline(same,stage.checkpointStage.firstMaterial,
                        stage.baselined.committedBaseline(),fresh);
                checkpointVerifiers.registerNext(same,stage.baselineBinding,stage.checkpointStage.savedVerifier);
                return stage.baselineBinding;
            });
        }
        /** The sole mint for domain initialization after the actual first physical SAVE and BASELINE. */
        public NextEpisodeDomainProof nextEpisodeDomainProof(ContinuityStorePort.Session same,NextEpisodeStage stage)throws IOException {
            writer.requireSession(same);Objects.requireNonNull(stage);stage.requireRetainedOriginal(same);
            StrictJson.require(stage.baselineBinding!=null&&stage.firstBaselineMaterial!=null&&stage.baselined!=null
                    &&stage.rebound==null,"new-episode domain initialization requires the actual first BASELINE before cycle publication");
            if(stage.domainReads==null)stage.domainReads=episodeDomainReads(stage.catalog);
            if(stage.domainProof==null)stage.domainProof=new NextEpisodeDomainProof(this,stage);
            stage.domainProof.requireCurrent(same,stage.catalog.context());return stage.domainProof;
        }
        private RootNextEpisodeDomainReads.Installed episodeDomainReads(RootInstalledCatalog catalog)throws IOException {
            return RootNextEpisodeDomainReads.install(catalog.context(),catalog.remainingDomains().lifecycle().physical(),List.of(
                    catalog.context().finance().definitions().contract(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.Query.CASH),
                    catalog.context().finance().definitions().contract(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.Query.CONSTRUCTION),
                    catalog.prisoners().collectionContract(),
                    catalog.activity().definitions().contract(org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts.Query.HOSTED)));
        }
        /** The sole restored-FIRST mint. A saved manifest alone cannot enter without its actual admitted replacement Root. */
        public RestoredFirstEpisodeDomainProof restoredFirstDomainProof(ContinuityStorePort.Session same,
                RootApplicationSession successor,Instant deadline)throws IOException {
            writer.requireSession(same);Objects.requireNonNull(successor);Objects.requireNonNull(deadline);
            Staged stage;
            synchronized(this) {
                stage=pendingRestore;
                StrictJson.require(stage!=null&&restoreCandidate==successor&&stage.restoration!=null
                        &&activeSession==stage.restoration.previous()&&stage.restoration.previous().isRetired()
                        &&successor.ownedBy(this)&&!successor.isRetired()&&!successor.hasInstalledHost()&&clock.instant().isBefore(deadline),
                        "restored FIRST domains require the private actually staged replacement before Host publication");
                if(restoredFirstDomains!=null) {
                    StrictJson.require(restoredFirstDomains.stage==stage&&restoredFirstDomains.successor==successor
                            &&restoredFirstDomains.deadline.equals(deadline),"restored FIRST initialization cannot switch its original scope or deadline");
                    restoredFirstDomains.requireCurrent(same,restoredFirstDomains.catalog.context());return restoredFirstDomains;
                }
            }
            var binding=stage.restoration.binding();stage.restoration.service().requireRetainedOriginal(same,binding);
            StrictJson.require(binding.savedMaterial() instanceof SavedFirstCheckpointMaterialStore.BaselinedMaterial,
                    "ordinary saved cycles cannot enter the FIRST episode initialization branch");
            var material=(SavedFirstCheckpointMaterialStore.BaselinedMaterial)binding.savedMaterial();material.requireRetained(same);
            var catalog=stage.restoration.runtime().catalog();var context=catalog.context();
            StrictJson.require(context.adopted()==stage.driver&&context.actions()==successor&&context.game()==stage.game
                    &&context.source().equals(binding.source())&&context.savedMaterials()==successor.savedMaterials(),
                    "restored FIRST initializer crossed its actually bound replacement catalog/Driver/material store");
            context.requireRestorationOriginal(same,binding);
            same.requireHistoricalEpisodeWindowBaseline(material.baseline());
            same.requireDomainImportContinuation(binding.attachment().head().sequence(),
                    org.xar.ck3.control.continuity.ContinuityJson.digest(binding.attachment().head().toJson()));
            var begin=material.firstMaterial().checkpoint().begin().begin();
            var parent=actions.withFrozen(same,lease->lease.find(begin.parentActionId()).orElse(null));
            StrictJson.require(parent!=null,"saved FIRST has no actual canonical original NEXT parent");
            var originals=activeLifecycle.archivedNextOrigins(same,material,parent);
            var proof=new RestoredFirstEpisodeDomainProof(this,stage,successor,catalog,material,originals,episodeDomainReads(catalog),deadline);
            synchronized(this){StrictJson.require(restoredFirstDomains==null&&pendingRestore==stage&&restoreCandidate==successor,
                    "restored FIRST private mint was displaced during original verification");restoredFirstDomains=proof;}
            proof.requireCurrent(same,context);return proof;
        }
        /** Captures and imports each actual new-player domain before a cycle or public owner can be published. */
        public List<DomainBodies.BodyRef> initializeNextDomains(ContinuityStorePort.Session same,NextEpisodeStage stage)throws IOException {
            writer.requireSession(same);stage.requireRetainedOriginal(same);
            if(stage.initializedDomains!=null&&stage.rebound!=null) {
                stage.batches.requireCurrent(same,stage.rebound);stage.firstBaselineMaterial.requireRetained(same);
                for(var ref:stage.initializedDomains) {
                    var current=same.readDomain(ref.slot());
                    StrictJson.require(current instanceof DomainBodies.Available known&&known.reference().equals(ref),
                            "retained NEXT domain initialization no longer names the actual canonical body");
                }
                return stage.initializedDomains;
            }
            var proof=nextEpisodeDomainProof(same,stage);
            if(stage.initializedDomains==null) {
                var actual=List.copyOf(stage.catalog.initializeNext(same,proof));
                StrictJson.require(actual.size()==EPISODE_DOMAIN_SLOTS.size()&&actual.stream().map(DomainBodies.BodyRef::slot)
                        .collect(java.util.stream.Collectors.toSet()).equals(EPISODE_DOMAIN_SLOTS),
                        "actual new-episode domain initialization must return exactly its thirteen unique real body references");
                proof.requireCurrent(same,stage.catalog.context());stage.initializedDomains=actual;
            }
            proof.requireCurrent(same,stage.catalog.context());return stage.initializedDomains;
        }
        private static final Set<DomainBodies.Slot> EPISODE_DOMAIN_SLOTS=Set.of(DomainBodies.Slot.FAMILY,
                DomainBodies.Slot.CHILD_MATRILINEAL,DomainBodies.Slot.DEFAULT_MARRIAGE,DomainBodies.Slot.SWAY,
                DomainBodies.Slot.CONSTRUCTION,DomainBodies.Slot.MERCENARY,DomainBodies.Slot.FACTION,
                DomainBodies.Slot.PRISONER_RELEASE,DomainBodies.Slot.PRISONER_RANSOM,
                DomainBodies.Slot.OPENING_GATE,DomainBodies.Slot.FEAST,DomainBodies.Slot.OPTIONAL_CADENCE,DomainBodies.Slot.RITE_CREATION);
        private void requireEpisodeImportSuffix(ContinuityStorePort.Session same,long sequence,String digest)throws IOException {
            writer.requireSession(same);same.requireDomainImportContinuation(sequence,digest);
            var original=same.requireHistoricalState(sequence,digest);var current=same.head().state();
            for(var slot:DomainBodies.Slot.values())if(!EPISODE_DOMAIN_SLOTS.contains(slot))
                StrictJson.require(DomainBodies.reference(original,slot).equals(DomainBodies.reference(current,slot)),
                        "episode initialization changed an unadmitted domain: "+slot);
        }
        private record RestoredSourceMetadata(Optional<String> epoch,Optional<org.xar.ck3.control.contracts.ExactRef> executable) { }
        /** Read the original FIRST material through its real store, then compare the actual newly published Driver before imports. */
        void captureRestoredFirstKernel(RootApplicationSession successor,Instant deadline)throws IOException,InterruptedException {
            StrictJson.require(writer.activeSession().isEmpty(),"restore kernel comparison must precede the held domain-import writer scope");
            Staged stage;
            synchronized(this){stage=pendingRestore;StrictJson.require(stage!=null&&restoreCandidate==successor&&stage.restoration!=null,
                    "restore kernel comparison requires its actual private staged successor");}
            var binding=stage.restoration.binding();
            if(!(binding.savedMaterial() instanceof SavedFirstCheckpointMaterialStore.BaselinedMaterial material))return;
            if(stage.restoredKernel!=null)return;
            if(!(savedCaptureFactory instanceof RootM7CheckpointCaptureFactory factory))throw new IOException("FIRST restore requires the original concrete M7 factory");
            var actualSources=stage.restoration.previous().savedMaterials();actualSources.requireOwn(material);
            var inputs=factory.requireInputs(stage.checkpointPairs(),stage.driverCheckpoints(),stage.savedSources());
            var reader=new RootM7HistoricalFirstCheckpointInputs(writer,writer::requireSession,archive,actualSources.firstStore(),inputs);
            var saved=reader.recover(material.pair(),material.firstMaterial().witness());
            StrictJson.require(saved.pair().equals(binding.pair())&&saved.materialWitness().equals(material.firstMaterial().witness()),
                    "recovered FIRST kernel data crossed its original pair or first-material FileWitness");
            var context=stage.restoration.runtime().catalog().context();
            RestoredSourceMetadata metadata=writer.locked(same->{
                stage.restoration.service().requireRetainedOriginal(same,binding);var diagnostics=context.transport().diagnostics();
                var transport=diagnostics.session().orElseThrow(()->new IOException("actual restored Native transport is unavailable"));
                var qualification=context.sources().verifyPhysicalOrigin(same,transport,context.source(),binding.semantic().originalNativePacket(),diagnostics,deadline);
                var qualified=context.sources().optionalMetadata(same,qualification);
                if(qualified.isPresent())qualified.orElseThrow().requireCurrent(same);
                return new RestoredSourceMetadata(qualified.map(RootNativeSourceAuthority.QualifiedMetadata::ownerSourceEpoch),
                        qualified.map(RootNativeSourceAuthority.QualifiedMetadata::gameExecutable));
            });
            var compared=inputs.restored(saved,stage.restoration.service(),binding,metadata.epoch(),metadata.executable(),Optional.empty(),deadline);
            synchronized(this){StrictJson.require(pendingRestore==stage&&restoreCandidate==successor,"restore kernel result lost its original private successor");
                stage.firstSavedKernel=saved;stage.restoredKernel=compared;}
        }
        /** One actual restored domain initialization after finish bound the true replacement session, before rebind/Host. */
        public List<DomainBodies.BodyRef> initializeRestoredDomains(ContinuityStorePort.Session same,
                RootApplicationSession successor,Instant deadline)throws IOException {
            writer.requireSession(same);Staged stage;
            synchronized(this){stage=pendingRestore;StrictJson.require(stage!=null&&restoreCandidate==successor
                    &&stage.restoration!=null&&activeSession==stage.restoration.previous(),
                    "restored initialization requires this exact original private successor");}
            var catalog=stage.restoration.runtime().catalog();var context=catalog.context();var binding=stage.restoration.binding();
            stage.restoration.service().requireRetainedOriginal(same,binding);context.requireRestorationOriginal(same,binding);
            if(binding.savedMaterial() instanceof SavedFirstCheckpointMaterialStore.BaselinedMaterial){
                if(stage.reopenedFirst==null)stage.reopenedFirst=RootSavedFirstReopen.reopen(context,same,stage.restoration.service(),binding);
                stage.reopenedFirst.requireCurrent(same);
            }
            if(binding.savedMaterial() instanceof SavedAttachmentSourceStore.SavedMaterial){
                if(stage.reopenedOrdinary==null)stage.reopenedOrdinary=RootSavedOrdinaryReopen.reopen(context,same,stage.restoration.service(),binding);
                stage.reopenedOrdinary.requireCurrent(same);
            }
            requireEpisodeImportSuffix(same,binding.attachment().head().sequence(),
                    org.xar.ck3.control.continuity.ContinuityJson.digest(binding.attachment().head().toJson()));
            if(stage.restoredDomainRefs==null) {
                if(binding.savedMaterial() instanceof SavedFirstCheckpointMaterialStore.BaselinedMaterial) {
                    var proof=restoredFirstDomainProof(same,successor,deadline);var actual=List.copyOf(catalog.initializeNext(same,proof));
                    StrictJson.require(actual.stream().map(DomainBodies.BodyRef::slot).collect(java.util.stream.Collectors.toSet()).equals(EPISODE_DOMAIN_SLOTS)
                            &&actual.size()==EPISODE_DOMAIN_SLOTS.size(),"restored FIRST must initialize exactly the thirteen actual episode domain slots");
                    proof.requireCurrent(same,context);stage.restoredDomainRefs=actual;
                }else stage.restoredDomainRefs=List.of();
            }
            for(var ref:stage.restoredDomainRefs) {
                var body=same.readDomain(ref.slot());StrictJson.require(body instanceof DomainBodies.Available known&&known.reference().equals(ref),
                        "restored initialization no longer names its actual registered canonical body: "+ref.slot());
            }
            if(!stage.restoredOriginalsAdopted) {
                catalog.adoptRestored(same,stage.restoration.service(),binding,successor.savedSources(),deadline);
                stage.restoredOriginalsAdopted=true;
            }
            requireEpisodeImportSuffix(same,binding.attachment().head().sequence(),
                    org.xar.ck3.control.continuity.ContinuityJson.digest(binding.attachment().head().toJson()));
            if(!stage.restoredPlanningInitialized) {
                var current=catalog.remainingDomains().lifecycle().physical().withSnapshot(same,deadline,lease->{
                    lease.assertCurrent(same);var frame=lease.ordinary().orElseThrow(()->new IOException("restored planning requires its genuine current physical living frame"));
                    lease.assertCurrent(same);return frame;
                });
                catalog.initializePersistentPlanning(same,current);stage.restoredPlanningInitialized=true;
            }
            return stage.restoredDomainRefs;
        }
        void warmRestoredCheckpoint(ContinuityStorePort.Session same,RootApplicationSession successor,Instant deadline)throws IOException {
            writer.requireSession(same);Staged stage;
            synchronized(this){stage=pendingRestore;StrictJson.require(stage!=null&&restoreCandidate==successor&&stage.restoredPlanningInitialized,
                    "restored checkpoint warming requires its actual initialized domain/planning owner");}
            var observations=stage.collector.checkpoint(stage.restoration.binding().pair().lineageId());
            try {
                for(;;) {
                    if(!clock.instant().isBefore(deadline))throw new IOException("restored physical stability deadline expired before Host publication");
                    var observed=observations.observe(deadline);
                    if(observed.mapReady()&&observed.paused()&&observed.saveEligible())return;
                    long remaining=Duration.between(clock.instant(),deadline).toMillis();
                    if(remaining<=0)throw new IOException("actual restored checkpoint readiness is unavailable: "+observed.reason());
                    Thread.sleep(Math.min(100,remaining));
                }
            }catch(InterruptedException interrupted){Thread.currentThread().interrupt();var failure=new java.io.InterruptedIOException("actual restored physical stabilization interrupted");failure.initCause(interrupted);throw failure;}
        }
        /** A source-owner admission may borrow only the helper's currently active private physical read. */
        public <T> Optional<T> withEpisodeDomainRead(ContinuityStorePort.Session same,RootRuntimeContext context,
                PlanningReadRequest request,ReadContract<?> contract,RootNextEpisodeDomainReads.PhysicalWork<T> work)throws IOException {
            writer.requireSession(same);Objects.requireNonNull(context);Objects.requireNonNull(work);
            NextEpisodeStage next;RestoredFirstEpisodeDomainProof restored;
            synchronized(this){next=pendingNext;restored=restoredFirstDomains;}
            if(next!=null&&next.domainReads!=null) {
                var actual=next.domainReads.withCurrent(same,context,request,contract,work);
                if(actual.isPresent())return actual;
            }
            if(restored==null)return Optional.empty();
            return restored.domainReads.withCurrent(same,context,request,contract,work);
        }
        /** Rebinds only the cycle origin after the actual physical first SAVE and persisted BASELINE material exist. */
        public ContinuityBatchJournal.ReboundNextBaseline rebindNextBaseline(ContinuityStorePort.Session same,NextEpisodeStage stage)throws IOException {
            writer.requireSession(same);stage.requireRetainedOriginal(same);
            StrictJson.require(stage.baselineBinding!=null&&stage.firstBaselineMaterial!=null&&stage.initializedDomains!=null,
                    "next cycle requires the actual saved SEM and persisted private first BASELINE material");
            stage.firstBaselineMaterial.requireRetained(same);
            if(stage.batches==null)stage.batches=new ContinuityBatchJournal(writer,stage.previous.cycles());
            if(stage.rebound==null)stage.rebound=stage.batches.rebindNextBaseline(same,stage.episodeInputs,stage.baselineBinding);
            stage.batches.requireCurrent(same,stage.rebound);return stage.rebound;
        }
        NextHostCommit prepareNextHost(ContinuityStorePort.Session same,NextEpisodeStage stage,RootApplicationSession successor,
                org.xar.ck3.control.service.OrdinarySessionHost host)throws IOException {
            writer.requireSession(same);stage.requireRetainedOriginal(same);
            StrictJson.require(stage.hostCandidate==successor&&stage.rebound!=null&&stage.baselineBinding!=null
                    &&stage.firstBaselineMaterial!=null&&activeSession==stage.previous&&successor.ownedBy(this)
                    &&!successor.isRetired()&&successor.driver()==stage.driver&&successor.capabilityRuntime()==stage.candidate,
                    "next host publication requires its privately constructed complete successor");
            stage.batches.requireCurrent(same,stage.rebound);stage.firstBaselineMaterial.requireRetained(same);
            return new NextHostCommit(this,stage,successor,Objects.requireNonNull(host),
                    actionHistory.preparePublication(same,stage.previous.driver().authority(),stage.checkpointStage.actionHistory()));
        }
        void publishNextSession(ContinuityStorePort.Session same,NextEpisodeStage stage,RootApplicationSession successor,
                Instant deadline)throws IOException {
            writer.requireSession(same);stage.requireRetainedOriginal(same);
            StrictJson.require(stage.hostCandidate==successor&&clock.instant().isBefore(deadline)&&!deadline.isAfter(stage.deadline),
                    "the original next host candidate or deadline changed before publication");
            if(!stage.planningInitialized) {
                var current=stage.candidate.withCandidateScope(same,()->stage.catalog.remainingDomains().lifecycle().physical()
                        .withSnapshot(same,deadline,physical->physical.ordinary().orElseThrow(()->new IOException("actual next living physical frame is unavailable"))));
                stage.candidate.withCandidateScope(same,()->{stage.catalog.initializePersistentPlanning(same,current);return null;});
                stage.planningInitialized=true;
            }
            warmPublishedCheckpoint(same,stage,deadline);
            stage.candidate.withCandidateScope(same,()->successor.readiness().currentOwned(same,successor.identity(),deadline,lease->lease.frame()));
            var host=Objects.requireNonNull(stage.previous.hostForPublication());
            var publication=prepareNextHost(same,stage,successor,host);
            submissions.publishNext(same,stage.previous.viewForPublication(),successor.viewForPublication(),stage.baselineBinding,
                    stage.batches,stage.rebound,host,stage.previous.controllerForPublication(),successor.controllerForPublication(),
                    savedLoader,stage.previous.loaderForPublication(),successor.loaderForPublication(),readHistory,
                    stage.previous.readsForPublication(),successor.readsForPublication(),stage.previous.capabilityRuntime(),stage.candidate,publication);
        }
        private void warmPublishedCheckpoint(ContinuityStorePort.Session same,NextEpisodeStage stage,Instant deadline)throws IOException {
            StrictJson.require(stage.planningInitialized&&stage.checkpointStage.ordinaryObservations!=null,
                    "next publication requires its actual initialized ordinary observation port");
            try {
                stage.candidate.withCandidateScope(same,()->{
                    try {
                        for(;;) {
                            if(!clock.instant().isBefore(deadline))throw new IOException("next ordinary physical stability deadline expired before host publication");
                            var observed=stage.checkpointStage.ordinaryObservations.observe(deadline);
                            if(observed.mapReady()&&observed.paused()&&observed.saveEligible())return null;
                            long remaining=Duration.between(clock.instant(),deadline).toMillis();
                            if(remaining<=0)throw new IOException("next ordinary checkpoint stability unavailable: "+observed.reason());
                            Thread.sleep(Math.min(100,remaining));
                        }
                    }catch(InterruptedException interrupted){throw new InterruptedAssembly(interrupted);}
                });
            }catch(InterruptedAssembly interrupted){Thread.currentThread().interrupt();var failure=new java.io.InterruptedIOException("actual next ordinary physical stabilization interrupted");failure.initCause(interrupted.interruption);throw failure;}
            catch(UncheckedIOException failure){throw failure.getCause();}
        }
        /** Builds a successor only from this owner's private actual restored Driver, without a new writer or a new native launch. */
        public synchronized Staged restoredStage(RootApplicationSession previous, RestoreCheckpointService service,
                RestoreCheckpointService.RestoreBinding binding, ManagedGameSession replacement, CheckpointFiles files, Path driverCheckpointPath,
                Path checkpointEvidence, Path attachmentEvidence, CheckpointService.SeedAdoptionPort seeds, String lineageId, Path savePath,
                Instant deadline)
                throws IOException, InterruptedException {
            StrictJson.require(finished && activeSession == previous && previous.isRetired() && previous.ownedBy(this)
                    && pendingRestore == null && restoreCandidate == null, "one actual retired original session must own restored staging");
            StrictJson.require(clock.instant().isBefore(Objects.requireNonNull(deadline)), "restored staging deadline expired");
            DriverBootstrap.Adopted driver = previous.restoreAdapters().adopted(binding);
            replacement.verify(); NativeGameTransport transport = replacement.nativeTransport();
            SessionIdentity identity = new SessionIdentity(replacement.machineId(), replacement.generation(), replacement.sessionId());
            StrictJson.require(identity.equals(binding.session()) && driver.session().game().equals(identity.game())
                    && driver.session().sessionId().equals(identity.sessionId()) && driver.status() == DriverBootstrap.AdoptionStatus.QUALIFICATION_REQUIRED,
                    "restore binding, privately adopted Driver and actual replacement owner differ");
            RootRestoreAdapters.RestoredRuntime runtime = writer.locked(borrowed -> {
                service.requireRetainedOriginal(borrowed, binding);
                return previous.restoreAdapters().runtime(borrowed, service, binding);
            });
            DriverCheckpointStore checkpoints = new DriverCheckpointStore(files, driverCheckpointPath, transport.pipeName(), new FrozenDriverSnapshotSupplier(driver.authority()));
            NativeReadinessCollector collector = runtime.collector();
            StrictJson.require(collector.identity().equals(identity), "restored stage must reuse the exact fresh publication collector");
            CheckpointService checkpointService = new CheckpointService(files, checkpoints, collector.checkpoint(lineageId), checkpointEvidence, clock, seeds);
            checkpointService.bindEvidence(archive, writer::borrowedSession, writer::requireSession);
            CheckpointRequestFactory requests = new CheckpointRequestFactory(savePath, collector.checkpoint(lineageId));
            Staged candidate = new Staged(this, identity, driver, replacement, null, collector, checkpointService, requests, files, checkpoints,
                    attachmentEvidence, new Restoration(previous, service, binding, runtime), runtime.reads(), new RootKnownReadObserver(writer));
            pendingRestore=candidate;runtime.catalog().bindSave(candidate);return candidate;
        }
        synchronized void requireRestorePublication(RootApplicationSession previous, RootApplicationSession successor)throws IOException {
            StrictJson.require(activeSession == previous && restoreCandidate == successor, "actual restored Root candidate changed before publication");
            StrictJson.require(pendingRestore!=null&&pendingRestore.lifecycleDomain!=null,
                    "actual restored lifecycle must be bound before Host publication");
            var held=writer.activeSession();
            if(held.isPresent())pendingRestore.restoredActionHistory=actionHistory.preparePublication(held.orElseThrow(),
                    previous.driver().authority(),pendingRestore.actionHistory());
        }
        synchronized void publishRestored(RootApplicationSession previous, RootApplicationSession successor) {
            // The same Core monitor and original writer already validated this private stage before the Host CAS.
            pendingRestore.restoredActionHistory.commit();
            activeLifecycle=pendingRestore.lifecycleDomain;
            activeSession=successor;restoreCandidate=null;pendingRestore=null;restoredFirstDomains=null;
        }
        private Supplier<ContinuityStorePort.Session> borrowed() {
            return () -> { try { return writer.borrowedSession(); } catch (IOException failure) { throw new UncheckedIOException(failure); } };
        }
        private ActionCoordinatorPort scoped(ActionCoordinator sole, NativeGameTransport transport) {
            return new org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionScope(sole, journal, transport,
                    new RootGovernanceSessions(writer), writer.originalLockPath());
        }
    }
    /** Private actual first-baseline custody shared by every domain initializer. It grants no action permission.
     * Its lineage permits only canonical registered DOMAIN_IMPORT edges, preserving all earlier action history,
     * including UNKNOWN originals. A READ, SAVE, cycle event or action ends this initialization scope.
     */
    /** Only Core's two private constructors may issue domain initialization authority. Saved originals are never current Game facts. */
    public sealed interface EpisodeDomainInitializationProof permits NextEpisodeDomainProof,RestoredFirstEpisodeDomainProof {
        enum Kind { NEXT, RESTORED_FIRST }
        Kind kind();
        SessionIdentity beforeSession();
        SessionIdentity afterSession();
        G2Source source();
        Instant deadline();
        SavedFirstCheckpointMaterialStore.BaselinedMaterial baselineMaterial();
        DriverStateSnapshot.Complete predecessorDriver();
        ActionReceipt parent();
        org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof lifecycleProof();
        DriverStateSnapshot.Complete firstSavedDriver();
        SessionPorts.SemanticEvidence savedSemantic();
        DriverStateSnapshot.Complete currentDriver();
        SessionPorts.SemanticEvidence currentSemantic();
        long initializationHeadSequence();
        String initializationHeadDigest();
        DomainBodies.BodyRef oldDomain(DomainBodies.Slot slot)throws IOException;
        <T> RootNextEpisodeDomainReads.Captured<T> read(ContinuityStorePort.Session same,RootRuntimeContext context,
                ReadContract<T> contract,org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj arguments,Instant deadline)throws IOException;
        void requireCurrent(ContinuityStorePort.Session same,RootRuntimeContext context)throws IOException;
    }
    public static final class NextEpisodeDomainProof implements EpisodeDomainInitializationProof {
        private final Core owner;private final NextEpisodeStage stage;
        private final SavedFirstCheckpointMaterialStore.BaselinedMaterial material;
        private NextEpisodeDomainProof(Core owner,NextEpisodeStage stage){
            this.owner=owner;this.stage=stage;material=Objects.requireNonNull(stage.firstBaselineMaterial);
        }
        public Kind kind(){return Kind.NEXT;}
        public DriverStateSnapshot.Complete predecessorDriver(){return stage.baselineBinding.predecessorDriver();}
        public ActionReceipt parent(){return stage.baselineBinding.parent();}
        public org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof lifecycleProof(){return stage.baselineBinding.proof();}
        public DriverStateSnapshot.Complete currentDriver(){return material.savedDriver();}
        public SessionPorts.SemanticEvidence currentSemantic(){return material.sourceSemantic();}
        public long initializationHeadSequence(){return material.originalHeadSequence();}
        public String initializationHeadDigest(){return material.originalHeadDigest();}
        public DomainBodies.BodyRef oldDomain(DomainBodies.Slot slot)throws IOException {
            return DomainBodies.reference(material.originalHead(),Objects.requireNonNull(slot))
                    .orElseThrow(()->new IOException("actual FIRST BASELINE lacks the original domain: "+slot));
        }
        public SessionIdentity beforeSession(){return stage.previous.identity();}
        public SessionIdentity afterSession(){return sessionIdentity(stage.driver);}
        public G2Source source(){return stage.source;}
        public Instant deadline(){return stage.deadline;}
        public <T> RootNextEpisodeDomainReads.Captured<T> read(ContinuityStorePort.Session same,RootRuntimeContext context,
                ReadContract<T> contract,org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj arguments,Instant deadline)throws IOException {
            requireCurrent(same,context);Objects.requireNonNull(deadline);
            StrictJson.require(owner.clock.instant().isBefore(deadline)&&!deadline.isAfter(stage.deadline),"domain read crossed the original bounded NEXT deadline");
            var result=stage.candidate.withCandidateScope(same,()->stage.domainReads.read(same,this,contract,arguments,deadline));
            requireCurrent(same,context);return result;
        }
        public SavedFirstCheckpointMaterialStore.BaselinedMaterial baselineMaterial(){return material;}
        public org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.NextBaselineBinding baseline(){return stage.baselineBinding;}
        public DriverStateSnapshot.Complete firstSavedDriver(){return material.savedDriver();}
        public SessionPorts.SemanticEvidence savedSemantic(){return material.sourceSemantic();}
        public void requireCurrent(ContinuityStorePort.Session same,RootRuntimeContext context)throws IOException {
            owner.writer.requireSession(same);Objects.requireNonNull(context);
            StrictJson.require(context==stage.catalog.context()&&context.core()==owner&&context.writer()==owner.writer
                    &&context.archive()==owner.archive&&context.adopted()==stage.driver&&context.source().equals(stage.source)
                    &&material==stage.firstBaselineMaterial&&stage.rebound==null,
                    "new-episode domain proof crossed its original private Core, physical Game or initialization scope");
            owner.requireAdmittedNext(same,stage,stage.baselined,stage.catalog,stage.candidate);
            material.requireRetained(same);
            owner.requireEpisodeImportSuffix(same,material.originalHeadSequence(),material.originalHeadDigest());
        }
    }
    /** A restore of an original FIRST baseline may initialize that episode on its genuinely new physical owner. */
    public static final class RestoredFirstEpisodeDomainProof implements EpisodeDomainInitializationProof {
        private final Core owner;private final Staged stage;private final RootApplicationSession successor;
        private final RootInstalledCatalog catalog;private final SavedFirstCheckpointMaterialStore.BaselinedMaterial material;
        private final org.xar.ck3.control.application.lifecycle.LifecycleComposites.ArchivedNextOrigins originals;
        private final Instant deadline;private final RootNextEpisodeDomainReads.Installed domainReads;
        private RestoredFirstEpisodeDomainProof(Core owner,Staged stage,RootApplicationSession successor,
                RootInstalledCatalog catalog,SavedFirstCheckpointMaterialStore.BaselinedMaterial material,
                org.xar.ck3.control.application.lifecycle.LifecycleComposites.ArchivedNextOrigins originals,
                RootNextEpisodeDomainReads.Installed domainReads,Instant deadline) {
            this.owner=owner;this.stage=stage;this.successor=successor;this.catalog=catalog;this.material=material;
            this.originals=originals;this.domainReads=domainReads;this.deadline=deadline;
        }
        public Kind kind(){return Kind.RESTORED_FIRST;}
        public SessionIdentity beforeSession(){return originals.beforeSession();}
        public SessionIdentity afterSession(){return stage.restoration.binding().session();}
        public G2Source source(){return stage.restoration.binding().source();}
        public Instant deadline(){return deadline;}
        public SavedFirstCheckpointMaterialStore.BaselinedMaterial baselineMaterial(){return material;}
        public DriverStateSnapshot.Complete predecessorDriver(){return originals.predecessorDriver();}
        public ActionReceipt parent(){return originals.parent();}
        public org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof lifecycleProof(){return originals.proof();}
        public DriverStateSnapshot.Complete firstSavedDriver(){return material.savedDriver();}
        public SessionPorts.SemanticEvidence savedSemantic(){return material.sourceSemantic();}
        public DriverStateSnapshot.Complete currentDriver(){return stage.restoration.binding().driver();}
        public SessionPorts.SemanticEvidence currentSemantic(){return stage.restoration.binding().semantic();}
        public long initializationHeadSequence(){return stage.restoration.binding().attachment().head().sequence();}
        public String initializationHeadDigest(){return org.xar.ck3.control.continuity.ContinuityJson.digest(stage.restoration.binding().attachment().head().toJson());}
        public DomainBodies.BodyRef oldDomain(DomainBodies.Slot slot)throws IOException {
            return DomainBodies.reference(material.originalHead(),Objects.requireNonNull(slot))
                    .orElseThrow(()->new IOException("actual saved FIRST BASELINE lacks its original domain: "+slot));
        }
        public <T> RootNextEpisodeDomainReads.Captured<T> read(ContinuityStorePort.Session same,RootRuntimeContext context,
                ReadContract<T> contract,org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj arguments,Instant limit)throws IOException {
            requireCurrent(same,context);Objects.requireNonNull(limit);
            StrictJson.require(owner.clock.instant().isBefore(limit)&&!limit.isAfter(deadline),"restored FIRST domain read crossed its actual bounded deadline");
            var result=domainReads.read(same,this,contract,arguments,limit);requireCurrent(same,context);return result;
        }
        public void requireCurrent(ContinuityStorePort.Session same,RootRuntimeContext context)throws IOException {
            owner.writer.requireSession(same);Objects.requireNonNull(context);
            synchronized(owner) {
                StrictJson.require(owner.restoredFirstDomains==this&&owner.pendingRestore==stage&&owner.restoreCandidate==successor
                        &&owner.activeSession==stage.restoration.previous()&&stage.restoration.previous().isRetired()
                        &&successor.ownedBy(owner)&&!successor.isRetired()&&!successor.hasInstalledHost()
                        &&context==catalog.context()&&context.core()==owner&&context.archive()==owner.archive&&context.writer()==owner.writer
                        &&context.adopted()==stage.driver&&context.actions()==successor&&context.source().equals(source())
                        &&stage.restoration.binding().savedMaterial()==material&&owner.clock.instant().isBefore(deadline),
                        "restored FIRST initialization lost its original private Root/binding/catalog/current physical scope");
            }
            var binding=stage.restoration.binding();stage.restoration.service().requireRetainedOriginal(same,binding);
            context.requireRestorationOriginal(same,binding);material.requireRetained(same);stage.game.verify();
            StrictJson.require(binding.session().equals(stage.identity)&&binding.session().game().equals(context.game().generation())
                    &&binding.driver().session().actorId().equals(material.savedDriver().session().actorId())
                    &&binding.driver().session().episodeRunId().equals(material.savedDriver().session().episodeRunId())
                    &&binding.semantic().frame().frame().identity().dateRaw().equals(material.sourceSemantic().frame().frame().identity().dateRaw())
                    &&!binding.session().game().equals(material.session().game()),
                    "restored FIRST current Game must be a distinct physical owner of the original saved episode/actor/date");
            owner.semanticVerifier.verify(same,binding.session(),binding.semantic());
            owner.requireEpisodeImportSuffix(same,initializationHeadSequence(),initializationHeadDigest());
        }
    }
    /** Minted after every original writer/physical/source proof has passed; commit performs no further I/O or validation. */
    static final class NextHostCommit {
        private final Core core;private final NextEpisodeStage stage;private final RootApplicationSession successor;
        private final org.xar.ck3.control.service.OrdinarySessionHost host;
        private final ActionHistoryLink.PreparedPublication history;
        private NextHostCommit(Core core,NextEpisodeStage stage,RootApplicationSession successor,
                org.xar.ck3.control.service.OrdinarySessionHost host,ActionHistoryLink.PreparedPublication history){
            this.core=core;this.stage=stage;this.successor=successor;this.host=host;this.history=Objects.requireNonNull(history);}
        void commit(){
            history.commit();successor.commitInstalledHost(host);stage.publishedSuccessor=successor;
            core.activeSession=successor;core.activeLifecycle=stage.checkpointStage.lifecycleDomain;
            core.lastPublishedNext=stage;core.pendingNext=null;core.nextAttempt=null;core.nextStageEntered=false;
        }
    }

    private static final class ActionHistoryLink implements WriterContracts.TransitionAuthority {
        private final ContinuityWriter writer;private final ActionJournal journal;private final NativeOutcomeArchive archive;
        private volatile DriverActionHistoryPublisher current;
        ActionHistoryLink(ContinuityWriter writer,ActionJournal journal,NativeOutcomeArchive archive){this.writer=writer;this.journal=journal;this.archive=archive;}
        synchronized void initial(DriverActionHistoryPublisher actual){
            StrictJson.require(current==null||current==actual,"initial action history cannot replace its actual producer");current=Objects.requireNonNull(actual);
        }
        synchronized PreparedPublication preparePublication(ContinuityStorePort.Session same,DriverStateAssembler previous,
                DriverActionHistoryPublisher replacement)throws IOException {
            writer.requireSession(same);var original=required();original.requireOwner(previous,journal,archive);
            StrictJson.require(original!=replacement&&!original.hasPending(same),
                    "pending original action history cannot be replaced before its true commit/CAS outcome is resolved");
            return new PreparedPublication(this,replacement);
        }
        private DriverActionHistoryPublisher required()throws IOException {
            var actual=current;if(actual==null)throw new IOException("actual action history producer has not been installed");return actual;
        }
        @Override public String revalidate(org.xar.ck3.control.continuity.ContinuityState before,WriterContracts.Request request)throws IOException {
            throw new IOException("action history requires the exact original writer Head and private material capture");
        }
        @Override public String revalidate(WriterContracts.Head head,WriterContracts.Request request)throws IOException {
            writer.requireSession(writer.borrowedSession());return required().revalidate(head,request);
        }
        @Override public org.xar.ck3.control.continuity.ContinuityState reduce(org.xar.ck3.control.continuity.ContinuityState before,
                WriterContracts.Request request)throws IOException {
            writer.requireSession(writer.borrowedSession());return required().reduce(before,request);
        }
        static final class PreparedPublication {
            private final ActionHistoryLink owner;private final DriverActionHistoryPublisher replacement;
            private PreparedPublication(ActionHistoryLink owner,DriverActionHistoryPublisher replacement){this.owner=owner;this.replacement=Objects.requireNonNull(replacement);}
            void commit(){owner.current=replacement;}
        }
    }

    public static final class Staged {
        private final Core core;
        private final SessionIdentity identity;
        private final DriverBootstrap.Adopted driver;
        private final ManagedGameSession game;
        private final InputLink inputs;
        private final NativeReadinessCollector collector;
        private final CheckpointService checkpoints;
        private final CheckpointRequestFactory requests;
        private final CheckpointFiles files;
        private final DriverCheckpointStore drivers;
        private final CanonicalSaveReceiptVerifier saveReceiptVerifier;
        private final Path attachmentEvidence;
        private final Restoration restoration;
        private final RootPlanningReads reads;
        private final RootKnownReadObserver knownReads;
        private org.xar.ck3.control.application.lifecycle.LifecycleComposites lifecycleDomain;
        private RootLifecycleAuthority physicalLifecycle;
        private RootRuntimeDispatcherFactory.Inputs dispatcherInputs;
        private RootRuntimeDispatcherFactory.Installed dispatcher;
        private boolean dispatcherEntered;
        private RootInstalledCatalog historyCatalog;
        private DriverActionHistoryPublisher actionHistory;
        private ActionHistoryLink.PreparedPublication restoredActionHistory;
        private NextEpisodeStage nextEpisode;
        private RootNextEpisodeWindowRuntime.Begun firstBegin;
        private CheckpointRequest firstRequest;
        private CheckpointRequest.ObservationPort firstObservations;
        private CheckpointRequest.ObservationPort ordinaryObservations;
        private RootFirstCheckpointGuard firstGuard;
        private CheckpointResult firstResult;
        private final FirstCheckpointVerifier firstVerifier;
        private final SavedFirstCheckpointMaterialStore firstStore;
        private SavedFirstCheckpointMaterialStore.Material firstMaterial;
        private SavedAttachmentSourceStore ordinarySourceStore;
        private SavedCheckpointMaterialStore savedMaterials;
        private CheckpointCommitVerifier pairVerifier;
        private RootCheckpointVerifier savedVerifier;
        private boolean storesEntered;
        private FirstCheckpointVerifier.VerifiedFirstCheckpoint firstProof;
        private org.xar.ck3.control.application.planning.campaign.M7CheckpointInputs.Saved firstSavedKernel;
        private org.xar.ck3.control.application.planning.campaign.M7CheckpointInputs.Restored restoredKernel;
        private boolean finishAttempted;
        private List<DomainBodies.BodyRef> restoredDomainRefs;
        private RootSavedFirstReopen.Reopened reopenedFirst;
        private RootSavedOrdinaryReopen.Reopened reopenedOrdinary;
        private boolean restoredOriginalsAdopted,restoredPlanningInitialized;
        private Staged(Core core, SessionIdentity identity, DriverBootstrap.Adopted driver, ManagedGameSession game,
                InputLink inputs, NativeReadinessCollector collector, CheckpointService checkpoints,
                CheckpointRequestFactory requests, CheckpointFiles files, DriverCheckpointStore drivers, Path attachmentEvidence,
                Restoration restoration, RootPlanningReads reads, RootKnownReadObserver knownReads) {
            this.core = core; this.identity = identity; this.driver = driver; this.game = game; this.inputs = inputs;
            this.collector = collector; this.checkpoints = checkpoints; this.requests = requests; this.files = files; this.drivers = drivers;
            this.attachmentEvidence = attachmentEvidence;
            this.saveReceiptVerifier = new CanonicalSaveReceiptVerifier(core.writer, core.actions, core.archive, files, drivers);
            firstVerifier=new FirstCheckpointVerifier(files,drivers,
                    (same,owner,semantic)->core.semanticVerifier.verify(same,owner,semantic).materialDigest(),
                    core.writer.originalLockPath(),core.writer::requireSession,saveReceiptVerifier);
            firstStore=new SavedFirstCheckpointMaterialStore(files,firstVerifier,core.writer::borrowedSession,attachmentEvidence.resolve("first"));
            this.restoration = restoration; this.reads = reads; this.knownReads = knownReads;
        }
        public NativeReadinessCollector readiness() { return collector; }
        public CheckpointService checkpoints() { return checkpoints; }
        public DriverBootstrap.Adopted driver() { return driver; }
        public DriverCheckpointStore driverCheckpoints() { return drivers; }
        public CanonicalSaveReceiptVerifier saveReceiptVerifier() { return saveReceiptVerifier; }
        public CheckpointCommitVerifier checkpointPairs(){StrictJson.require(pairVerifier!=null,"actual paired verifier has not been bound");return pairVerifier;}
        public SavedAttachmentSourceStore savedSources(){StrictJson.require(ordinarySourceStore!=null,"actual ordinary saved-source store has not been bound");return ordinarySourceStore;}
        public SavedFirstCheckpointMaterialStore firstSources(){return firstStore;}
        public FirstCheckpointVerifier firstCheckpointVerifier(){return firstVerifier;}
        /** Read-only saved kernel DATA, not planning or restore admission. */
        public org.xar.ck3.control.application.planning.campaign.M7CheckpointInputs.Saved firstSavedKernel(){
            StrictJson.require(firstSavedKernel!=null,"actual first saved kernel inputs have not been captured");return firstSavedKernel;
        }

        public org.xar.ck3.control.application.planning.campaign.M7CheckpointInputs.Restored restoredFirstKernel(){
            StrictJson.require(restoredKernel!=null,"actual FIRST restored kernel comparison has not been captured");return restoredKernel;
        }
        public void requireCheckpointFiles(CheckpointFiles actual) {
            StrictJson.require(files == Objects.requireNonNull(actual), "the actual Staged checkpoint files cannot be substituted");
        }
        public RootPlanningReads planningReads() { return reads; }
        private void prepareCheckpointStores(OrdinaryCycleTransitions cycles,RootCheckpointVerifier.SavedCaptureFactory actualFactory)throws IOException {
            synchronized(core) {
                if(savedMaterials!=null)return;
                StrictJson.require(!storesEntered,"partial actual checkpoint material construction cannot be replayed");storesEntered=true;
                pairVerifier=new CheckpointCommitVerifier(files,drivers,
                        (same,owner,semantic)->core.semanticVerifier.verify(same,owner,semantic).materialDigest(),
                        core.writer.originalLockPath(),core.writer::requireSession,saveReceiptVerifier);
                savedVerifier=new RootCheckpointVerifier(core.writer,pairVerifier);
                ordinarySourceStore=new SavedAttachmentSourceStore(files,drivers,pairVerifier,core.writer::borrowedSession,attachmentEvidence,
                        cycles::verifyCompletedCycleProof,cycles::verifyHistoricalCompletedCycleProof);
                savedVerifier.bind(ordinarySourceStore);
                savedVerifier.bindCapture(Objects.requireNonNull(actualFactory.create(pairVerifier,drivers,ordinarySourceStore)));
                savedMaterials=new SavedCheckpointMaterialStore(ordinarySourceStore,firstStore);
            }
        }
        public SavedCheckpointMaterialStore savedMaterials() {
            StrictJson.require(savedMaterials!=null,"the actual ordinary and first-checkpoint stores are not bound");return savedMaterials;
        }
        private void bindPhysicalLifecycle(RootLifecycleAuthority actual,
                org.xar.ck3.control.application.lifecycle.LifecycleComposites domain) {
            Objects.requireNonNull(actual);Objects.requireNonNull(domain);
            if(lifecycleDomain!=null){StrictJson.require(lifecycleDomain==domain&&physicalLifecycle==actual,
                    "a staged collector cannot replace its original physical lifecycle producers");return;}
            collector.bindLifecycleParentAuthority(domain::requireCommittedEpisode);
            collector.bindPhysicalSemanticCapture(actual::semantic);lifecycleDomain=domain;physicalLifecycle=actual;
        }
        /** Installs the identical catalog's archived-material producer before preparing this sole dispatcher. */
        public void installActionHistory(RootInstalledCatalog actual)throws IOException {
            Objects.requireNonNull(actual);var context=actual.context();
            StrictJson.require(context.core()==core&&context.game()==game&&context.adopted()==driver
                    &&context.writer()==core.writer&&context.archive()==core.archive,
                    "action history must retain this staged Driver, Game, writer and archive");
            synchronized(core) {
                if(actionHistory!=null){StrictJson.require(historyCatalog==actual,"action history cannot replace its actual catalog");return;}
                DriverActionHistoryPublisher created;
                if(core.fixtureProducts!=null){
                    StrictJson.require(core.fixtureCatalog==actual&&core.fixtureInitial.fixtureRetired(),
                            "fixture adoption must reuse its same actual catalog after initial promotion");
                    created=core.fixtureProducts.actionHistory();
                }else{
                    var products=actual.remainingDomains().actionHistory(context,actual);
                    created=new DriverActionHistoryPublisher(driver.authority(),core.journal,core.archive,
                            products.materials(),products.publisherSources());
                }
                created.requireOwner(driver.authority(),core.journal,core.archive);core.retainCatalogResources(actual);historyCatalog=actual;actionHistory=created;
            }
        }
        public DriverActionHistoryPublisher actionHistory(){
            return Objects.requireNonNull(actionHistory,"the actual per-Game action history publisher has not been installed");
        }
        /** Constructs the actual dispatcher once, before any Controller or first checkpoint is required. */
        public RootRuntimeDispatcherFactory.Installed prepareDispatcher(String authorityId,RootExecutableBindings bindings,
                NativeFrontendAuthority frontend,RootLifecycleAuthority lifecycle,RootReconciliationAuthority reconciliation,
                RootLifecycleActionGuard.CloseAdmission closeAdmission,RootActionGuard.DerivedChildAdmission derivedChildren,
                NativeRecordedEvidenceVerifier.DerivedGuardVerifier derivedReplay,DriverCapabilityRuntime capabilities,
                DriverReadHistoryPublisher readHistory,List<RootDomainIntentPreparation.Binding> pending,Set<OperationKey> requiredPending,
                org.xar.ck3.control.application.advance.LifeAdvanceEvidence.BoundFrameVerifier actualLifeFrames)throws IOException {
            synchronized(core) {
                var actualLifecycle=Objects.requireNonNull(historyCatalog,"actual lifecycle catalog is not installed").remainingDomains().lifecycle();
                actualLifecycle.requireContext(historyCatalog.context());
                var actual=new RootRuntimeDispatcherFactory.Inputs(core,identity,driver,game,collector,bindings,frontend,lifecycle,actualLifecycle,
                        reconciliation,closeAdmission,derivedChildren,derivedReplay,capabilities,readHistory,actionHistory(),pending,requiredPending,knownReads,
                        Optional.ofNullable(restoration==null&&core.menu!=null&&core.menu.game==game?core.menu:null));
                if(dispatcher!=null){StrictJson.require(dispatcherInputs.equals(actual),"actual dispatcher cannot replace original producer inputs");return dispatcher;}
                StrictJson.require(!dispatcherEntered,"partial actual dispatcher construction cannot be replayed");dispatcherEntered=true;
                dispatcherInputs=actual;var created=RootRuntimeDispatcherFactory.create(authorityId,actual);
                capabilities.bindPlanningPorts(files,created.evidence(),Objects.requireNonNull(actualLifeFrames));
                checkpoints.bindActions(created.coordinator());dispatcher=created;return created;
            }
        }

        /** Installs the real same-frame kernel capture before this collector may publish an ordinary ready request. */
        public void bindReadyPublication(NativeReadinessCollector.ReadyPublication actual) {
            collector.bindReadyPublication(Objects.requireNonNull(actual));
        }
        public void bindPlanningEvidence(NativeReadinessCollector.PlanningEvidenceVerifier actual) {
            collector.bindPlanningEvidence(Objects.requireNonNull(actual));
        }

        /** Every argument is an actual policy or installed callable, never a capability-name descriptor. */
        public RootApplicationSession finish(String authorityId, RootExecutableBindings bindings, NativeFrontendAuthority frontend,
                RootLifecycleAuthority lifecycle, RootReconciliationAuthority reconciliation, RootLifecycleActionGuard.CloseAdmission closeAdmission,
                TerminalLifecycleDecisionProducer terminalDecisions,
                RootLifecycleRuntimeFactory.Installed actualLifecycleRuntime,
                RootActionGuard.DerivedChildAdmission derivedChildren,
                NativeRecordedEvidenceVerifier.DerivedGuardVerifier derivedReplay,
                DriverCapabilityRuntime capabilities,DriverReadHistoryPublisher readHistory,
                org.xar.ck3.control.application.advance.LifeAdvanceEvidence.BoundFrameVerifier actualLifeFrames,
                NativeReadinessCollector.PlanningInputsPort planningInputs,
                OrdinaryPlanningPipeline pipeline, List<RootDomainIntentPreparation.Binding> pending,
                Set<OperationKey> requiredPending, OriginalWindowReducer.Policy cyclePolicy,
                SessionPorts.OfflineAnalysisPort offline, SessionClock sessionClock,
                Optional<CheckpointPair> baseline, long admittedSavedDays, OrdinaryPlanCompletion completion,
                SessionPorts.EpisodeContinuation episodes,
                RootCheckpointVerifier.SavedCaptureFactory savedCaptureFactory,
                RootRestoreMaterialFactory restoreMaterials, RootRestoreAdapters.PostAdoptionPort restorePublication) throws IOException {
            synchronized (core) {
                StrictJson.require(!finishAttempted, "this Root graph's original assembly attempt cannot be replayed after partial binding");
                finishAttempted = true;
                boolean restoring = restoration != null;
                boolean next=nextEpisode!=null;
                StrictJson.require(restoring ? core.finished && core.pendingRestore == this && core.restoreCandidate == null
                        && core.activeSession == restoration.previous() && restoration.previous().isRetired()
                        :next?core.finished&&core.pendingNext==nextEpisode&&core.activeSession==nextEpisode.previous
                            &&nextEpisode.previous.isRetired()&&nextEpisode.hostCandidate==null&&nextEpisode.rebound!=null
                        :!core.finished,
                        "only the current original Root stage or its privately qualified restored successor may finish");
                StrictJson.require(core.configuration.mode() == HostMode.COMPLETE_MIGRATION, "full ordinary session requires complete-migration host mode");
                core.finished = true; // An interrupted/partial assembly must never be silently attempted again.
                if (restoring) StrictJson.require(authorityId.equals(core.rootAuthorityId) && cyclePolicy.equals(core.originalCyclePolicy)
                        && baseline.filter(restoration.binding().pair()::equals).isPresent()
                        && admittedSavedDays == restoration.binding().committedSavedDays() && savedCaptureFactory == core.savedCaptureFactory,
                        "restored graph changed frozen policy, actual saved frontier or session-aware SAVE capture");
                else if(next) {
                    StrictJson.require(authorityId.equals(core.rootAuthorityId)&&cyclePolicy.equals(core.originalCyclePolicy)
                            &&savedCaptureFactory==core.savedCaptureFactory&&admittedSavedDays==0
                            &&baseline.filter(nextEpisode.baselineBinding.firstCheckpoint().pair()::equals).isPresent()
                            &&capabilities==nextEpisode.candidate&&bindings==nextEpisode.catalog.bindings(),
                            "new episode must retain its original first physical SAVE pair, policy and zero credit");
                    nextEpisode.batches.requireCurrent(core.writer.borrowedSession(),nextEpisode.rebound);
                    nextEpisode.firstBaselineMaterial.requireRetained(core.writer.borrowedSession());
                } else { core.rootAuthorityId = StrictJson.text(authorityId); core.originalCyclePolicy = cyclePolicy; core.savedCaptureFactory=Objects.requireNonNull(savedCaptureFactory); }
                Objects.requireNonNull(frontend); Objects.requireNonNull(pipeline); bindings.requireCompleteArchiveCoverage();
                StrictJson.require(Objects.requireNonNull(actualLifecycleRuntime)==Objects.requireNonNull(historyCatalog).remainingDomains().lifecycle(),
                        "the Root dispatcher and observation probe must retain the identical actual lifecycle/pending-UI source");
                Objects.requireNonNull(reconciliation).requireOwner(core.writer, core.archive, bindings.readCatalog(), lifecycle);
                Supplier<ContinuityStorePort.Session> borrowed = core.borrowed(); G2Source source = driver.source();
                Objects.requireNonNull(capabilities); capabilities.requireOwner(driver.authority(), core.archive, bindings);
                Objects.requireNonNull(readHistory).requireOwner(driver.authority(),core.archive,bindings.readCatalog());
                StrictJson.require(capabilities.readHistoryPublisher()==readHistory,"Root must retain the capability runtime's identical read-history publisher");
                RootReadPublicationCompletion readCompletion=new RootReadPublicationCompletion(core,readHistory,completion,collector);
                var lifecycleHandler=bindings.composites().find(new OperationKey("continue-as-reconciled-successor")).orElseThrow();
                if(!(lifecycleHandler instanceof org.xar.ck3.control.application.lifecycle.LifecycleComposites domainLifecycle))
                    throw new IllegalStateException("actual lifecycle domain service is required for canonical episode verification");
                StrictJson.require(bindings.composites().find(new OperationKey("death-terminal")).orElseThrow()==domainLifecycle
                        &&bindings.composites().find(new OperationKey("start-next-episode")).orElseThrow()==domainLifecycle,
                        "all lifecycle operations must retain the identical actual composite service");
                bindPhysicalLifecycle(lifecycle,domainLifecycle);
                if (restoring) {
                    StrictJson.require(bindings == restoration.runtime().bindings(), "restored ordinary graph must reuse its exact published executable catalog");
                    StrictJson.require(planningInputs == restoration.runtime().planningInputs(), "restored ordinary graph must retain its actual collector planning producer");
                    StrictJson.require(capabilities == restoration.runtime().capabilities(), "restored ordinary graph cannot bind a second capability runtime");
                }
                RootMenuSession menu = restoring||next ? null : core.menu;
                if (menu != null) StrictJson.require(menu.authorityId.equals(authorityId) && menu.game == game && menu.source.equals(source) && menu.bindings == bindings
                        && menu.frontend == frontend, "ordinary graph must retain its actual frontend startup objects");
                var actualDispatcher=prepareDispatcher(authorityId,bindings,frontend,lifecycle,reconciliation,closeAdmission,derivedChildren,
                        derivedReplay,capabilities,readHistory,pending,requiredPending,actualLifeFrames);
                var gameplay=actualDispatcher.gameplay();var gameplayReads=actualDispatcher.gameplayReads();
                var terminalActions=actualDispatcher.terminalActions();var terminalReads=actualDispatcher.terminalReads();
                var reconciliationReads=actualDispatcher.reconciliationReads();var intents=actualDispatcher.intents();
                PlanningReadCoordinator queries=actualDispatcher.queries();RootSessionSwitchboard.View view=actualDispatcher.view();
                if (menu == null && !restoring&&!next) core.submissions.installInitial(view);
                ActionCoordinatorPort coordinator=actualDispatcher.coordinator();
                OrdinaryCycleTransitions cycles; SavedAttachmentSourceStore sourceStore;
                if (restoring) { cycles = restoration.previous().cycles(); }
                else if(next){cycles=nextEpisode.previous.cycles();}
                else if(core.cleanRestartCycles!=null){
                    StrictJson.require(core.cleanRestartPolicy.equals(cyclePolicy),"clean restart retains its actual cycle policy");
                    cycles=core.cleanRestartCycles;
                }
                else if(core.settledSameGameCycles!=null){
                    StrictJson.require(core.settledSameGamePolicy.equals(cyclePolicy),"settled continuation retains its actual cycle policy");
                    cycles=core.settledSameGameCycles;
                }
                else if(core.unresolvedSameGameCycles!=null){
                    StrictJson.require(core.unresolvedSameGamePolicy.equals(cyclePolicy),"unresolved reconstruction retains its actual cycle policy");
                    cycles=core.unresolvedSameGameCycles;
                }
                else if(core.initialNoDispatchCycles!=null){
                    StrictJson.require(core.initialNoDispatchPolicy.equals(cyclePolicy),"initial no-dispatch recovery retains its actual cycle policy");
                    cycles=core.initialNoDispatchCycles;
                }
                else {
                    cycles = new OrdinaryCycleTransitions(core.archive, core.semanticVerifier, core.checkpointVerifiers, cyclePolicy, core.writer::requireSession);
                    cycles.bindTerminalFrameLoader(core.frames);
                }
                prepareCheckpointStores(cycles,savedCaptureFactory);sourceStore=ordinarySourceStore;
                if(!restoring&&!next) {
                    var active=core.writer.activeSession();
                    if(active.isPresent())core.checkpointVerifiers.registerInitial(active.orElseThrow(),identity,savedVerifier);
                    else core.writer.locked(same->{core.checkpointVerifiers.registerInitial(same,identity,savedVerifier);return null;});
                } else if(restoring) {
                    var active=core.writer.activeSession();
                    if(active.isPresent())core.checkpointVerifiers.registerRestored(active.orElseThrow(),restoration.service(),restoration.binding(),savedVerifier);
                    else core.writer.locked(same->{core.checkpointVerifiers.registerRestored(same,restoration.service(),restoration.binding(),savedVerifier);return null;});
                }
                RootRestoreAdapters restores = new RootRestoreAdapters(core.writer, core.archive, core.actions, driver, sourceStore,savedMaterials,
                        Objects.requireNonNull(restoreMaterials).create(core.writer,core.archive,files,drivers,savedMaterials,driver),restorePublication);
                SavedAttachmentAuthority.SourceLoader actualLoader = (predecessor, event) -> {
                    SavedAttachmentAuthority.Loaded loaded = savedMaterials.load(predecessor, event);
                    restores.verifyAttachmentSource(core.writer.borrowedSession(), predecessor, event); return loaded;
                };
                if (!restoring&&!next) core.savedLoader.initial(actualLoader);
                SavedAttachmentAuthority attachment = new SavedAttachmentAuthority(drivers, core.savedLoader);
                ActionContinuityAuthority actionAuthority = new ActionContinuityAuthority(authorityId, core.archive, core.submissions, core.submissions, core.clock,bindings);
                actionAuthority.bindPhysicalActions(core.physicalActions());
                if (menu == null && !restoring&&!next) {
                    core.sealAuthorities(List.of(new RootAuthorityRouter.Binding(Set.of(ContinuityActionJournal.KIND), actionAuthority),
                            new RootAuthorityRouter.Binding(cycles.kinds(), cycles),
                            new RootAuthorityRouter.Binding(SavedAttachmentAuthority.kinds(), attachment),
                            new RootAuthorityRouter.Binding(Set.of(WriterContracts.GAMEPLAY_ENTRY_KIND), core.entryAuthority),
                            new RootAuthorityRouter.Binding(Set.of(WriterContracts.DRIVER_READ_HISTORY_KIND),core.readHistory)));
                    reads.bind(queries);
                } else if (menu != null) {
                    core.initialReconciliation.bind(reconciliationReads, reconciliation);
                    menu.cycles.bind(cycles); menu.saved.bind(attachment); menu.intents.bind(intents); menu.attempts.bind(capabilities,actionHistory());
                    menu.terminalActions.bind(terminalActions); menu.terminalReads.bind(terminalReads);
                    menu.derivedReplay.bind(derivedReplay);
                    menu.readBarrier.bind(readHistory);
                    menu.gameplayReads.bind(gameplayReads); menu.gameplay.bind(gameplay); menu.admitted();
                }
                if (restoring||next) reads.bind(queries);
                else {core.readHistory.initial(readHistory);core.actionHistory.initial(actionHistory());}
                knownReads.bind(capabilities); if (!restoring) inputs.bind(capabilities, planningInputs);
                if(!restoring&&!next)cycles.bindOperatorAuthority(core.operatorAuthority());
                ContinuityBatchJournal batches = next?nextEpisode.batches:(core.cleanRestartBatches != null ? core.cleanRestartBatches :
                        (core.settledSameGameBatches != null ? core.settledSameGameBatches :
                        (core.unresolvedSameGameBatches != null ? core.unresolvedSameGameBatches :
                        (core.initialNoDispatchBatches != null ? core.initialNoDispatchBatches : new ContinuityBatchJournal(core.writer, cycles)))));
                SessionPorts.ObservationPort observations = new RootSessionObservationPort(core,collector,lifecycle,terminalDecisions,driver.authority(),game.nativeTransport(),
                        Objects.requireNonNull(actualLifecycleRuntime));
                RootControllerActions controllerActions = new RootControllerActions(core, identity, coordinator);
                var ordinaryPlanner = pipeline.create(core.clock);
                core.decisionSelector().ifPresent(ordinaryPlanner::bindSelector);
                ordinaryPlanner.setM5JointPeacetimeEnabled(core.m5JointPeacetimeEnabled());
                SessionController controller = new SessionController(identity, (owned, until) -> game.inspect(owned.game(), until), observations,
                        ordinaryPlanner, controllerActions, checkpoints, requests, batches, offline, sessionClock, baseline, admittedSavedDays, readCompletion, episodes);
                controller.bindDecisionDisplay(core.audienceDisplay());
                core.finished = true;
                RootApplicationSession result = new RootApplicationSession(core, core.submissions, view, batches, core.savedLoader, actualLoader, restoration,nextEpisode,
                        core.writer, core.archive, game, driver, collector,lifecycle, coordinator, queries, cycles,
                        checkpoints,requests,drivers,sourceStore,savedMaterials,restores, capabilities,readHistory,readCompletion, controller,Objects.requireNonNull(historyCatalog), core.clock);
                controllerActions.bind(result);
                if(restoring){restoration.runtime().catalog().bindSession(result);core.restoreCandidate=result;}
                else if(next){nextEpisode.catalog.bindSession(result);nextEpisode.hostCandidate=result;}
                else { core.activeSession = result; core.activeLifecycle = domainLifecycle; }
                if(!restoring&&!next&&core.coldOriginal!=null){
                    StrictJson.require(historyCatalog.context()==core.coldOriginal.context()&&driver==core.coldOriginal.adopted(),
                            "cold postbind must consume the exact privately committed and adopted Root");
                    try{RootColdReboundRuntime.complete(core.coldOriginal,historyCatalog.context(),core.coldBootstrapDeadline);}
                    catch(InterruptedException interrupted){
                        Thread.currentThread().interrupt();var failure=new java.io.InterruptedIOException("actual cold Root postbind observations interrupted");
                        failure.initCause(interrupted);throw failure;
                    }
                }
                return result;
            }
        }
    }
    private static final class NextEpisodeAttempt {
        private final RootApplicationSession previous;
        private final ActionReceipt parent;
        private final ManagedGameSession replacement;
        private final G2Source source;
        private final RootInstalledCatalog catalog;
        private final int retainedFrames;
        private final Instant deadline;
        private final org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption original;
        private final DriverCapabilityRuntime candidate;
        private NextEpisodeAttempt(RootApplicationSession previous, ActionReceipt parent, ManagedGameSession replacement,
                G2Source source, RootInstalledCatalog catalog, int retainedFrames, Instant deadline,
                org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption original, DriverCapabilityRuntime candidate) {
            this.previous = previous; this.parent = parent; this.replacement = replacement; this.source = source; this.catalog = catalog;
            this.retainedFrames = retainedFrames; this.deadline = deadline; this.original = original; this.candidate = candidate;
        }
    }
    /** A private factory token proves owner transfer only. It cannot install a host or stand in for new paired SAVE/window admission. */
    public static final class NextEpisodeStage {
        private final Core owner;
        private final RootApplicationSession previous;
        private final ManagedGameSession replacement;
        private final org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption original;
        private final DriverBootstrap.Adopted driver;
        private final G2Source source;
        private final RootInstalledCatalog catalog;
        private final DriverCapabilityRuntime candidate;
        private final int retainedFrames;
        private final Instant deadline;
        private Staged checkpointStage;
        private boolean checkpointStageEntered;
        private org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs episodeInputs;
        private SessionPorts.SemanticEvidence opening;
        private RootNextEpisodeWindowRuntime.Begun begun;
        private RootNextEpisodeWindowRuntime.Baselined baselined;
        private org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.NextBaselineBinding baselineBinding;
        private SavedFirstCheckpointMaterialStore.BaselinedMaterial firstBaselineMaterial;
        private volatile RootApplicationSession publishedSuccessor;
        private ContinuityBatchJournal batches;
        private ContinuityBatchJournal.ReboundNextBaseline rebound;
        private RootApplicationSession hostCandidate;
        private NextEpisodeDomainProof domainProof;
        private RootNextEpisodeDomainReads.Installed domainReads;
        private List<DomainBodies.BodyRef> initializedDomains;
        private RootNextEpisodeAssemblyInputs.SessionResources assemblyResources;
        private RootNextEpisodeAssemblyInputs.StageInputs assemblyInputs;
        private boolean assemblyInputsEntered;
        private boolean planningInitialized;
        private NextEpisodeStage(Core owner, RootApplicationSession previous, ManagedGameSession replacement,
                org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption original,
                DriverBootstrap.Adopted driver, G2Source source, RootInstalledCatalog catalog,
                DriverCapabilityRuntime candidate, int retainedFrames, Instant deadline) {
            this.owner = owner; this.previous = previous; this.replacement = replacement; this.original = original;
            this.driver = driver; this.source = source; this.catalog = catalog; this.candidate = candidate;
            this.retainedFrames = retainedFrames; this.deadline = deadline;
        }
        public DriverBootstrap.Adopted driver() { return driver; }
        public ManagedGameSession replacement() { return replacement; }
        public G2Source source() { return source; }
        public Instant deadline(){return deadline;}
        public RootApplicationSession previous() { return previous; }
        public RootInstalledCatalog catalog() { return catalog; }
        public DriverCapabilityRuntime candidate() { return candidate; }
        public org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption original() { return original; }
        /** Valid only before capability activation changes the original published auxiliary facts. */
        public void requireCurrent(ContinuityStorePort.Session same) throws IOException { owner.requireNextStage(same, this); }
        /** Private original custody after the actual first SAVE; this grants neither a current observation nor activation. */
        public void requireRetainedOriginal(ContinuityStorePort.Session same) throws IOException { owner.requireRetainedNextStage(same, this); }
    }
    record Restoration(RootApplicationSession previous, RestoreCheckpointService service, RestoreCheckpointService.RestoreBinding binding,
            RootRestoreAdapters.RestoredRuntime runtime) { }

    private static final class InputLink {
        private final ContinuityWriter writer;
        private volatile NativeReadinessCollector.CapabilitiesPort capabilities;
        private volatile NativeReadinessCollector.PlanningInputsPort planning;
        private InputLink(ContinuityWriter writer) { this.writer = writer; }
        synchronized void bind(NativeReadinessCollector.CapabilitiesPort actualCapabilities, NativeReadinessCollector.PlanningInputsPort actualPlanning) {
            if(capabilities!=null||planning!=null){StrictJson.require(capabilities==actualCapabilities&&planning==actualPlanning,
                    "native input producers cannot replace the same privately staged capability/planning objects");return;}
            StrictJson.require(capabilities == null && planning == null, "native input producers already installed");
            capabilities = Objects.requireNonNull(actualCapabilities); planning = Objects.requireNonNull(actualPlanning);
        }
        public NativeReadinessCollector.ExecutableCapabilities capabilities(ContinuityStorePort.Session borrowed,
                DriverObservationAssembler.Complete frame, DriverSnapshotFacts.Known driver,
                org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj received, Instant deadline) throws IOException {
            writer.requireSession(borrowed); NativeReadinessCollector.CapabilitiesPort actual = capabilities;
            if (actual == null) throw new IOException("actual pure capability producer is not installed");
            return actual.collect(borrowed, frame, driver, received, deadline);
        }
        public NativeReadinessCollector.PlanningInputs planning(ContinuityStorePort.Session borrowed,
                DriverObservationAssembler.Complete frame, DriverSnapshotFacts.Known driver,
                org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj received, Instant deadline) throws IOException {
            writer.requireSession(borrowed); NativeReadinessCollector.PlanningInputsPort actual = planning;
            if (actual == null) throw new IOException("actual full planning input producers are not installed");
            return actual.collect(borrowed, frame, driver, received, deadline);
        }
    }
    private static final class OriginActions implements ActionPorts.GuardPort {
        private final ActionPorts.GuardPort gameplay; private final RootFrontendActionGuard frontend; private final ActionPorts.GuardPort terminal;
        private OriginActions(ActionPorts.GuardPort gameplay, RootFrontendActionGuard frontend, ActionPorts.GuardPort terminal) {
            this.gameplay = gameplay; this.frontend = frontend; this.terminal = terminal;
        }
        @Override public GuardEvidence verify(WriterContracts.Head head, ActionCommand command) {
            if (command.origin() instanceof CommandOrigin.Gameplay) return gameplay.verify(head, command);
            if (command.origin() instanceof CommandOrigin.LifecycleTerminal) return terminal.verify(head, command);
            if(command.origin() instanceof CommandOrigin.Frontend)return frontend.verify(head, command);
            throw new IllegalArgumentException("a read-only reconciliation origin cannot submit any primitive or composite action");
        }
    }
    static final class OriginReads implements PlanningReadCoordinator.ReadGuardPort {
        private final PlanningReadCoordinator.ReadGuardPort gameplay; private final RootFrontendReadGuard frontend;
        private final PlanningReadCoordinator.ReadGuardPort terminal; private final PlanningReadCoordinator.ReadGuardPort reconciliation;
        private final PlanningReadCoordinator.ReadGuardPort physical;
        OriginReads(PlanningReadCoordinator.ReadGuardPort gameplay, RootFrontendReadGuard frontend,
                PlanningReadCoordinator.ReadGuardPort terminal, PlanningReadCoordinator.ReadGuardPort reconciliation,
                PlanningReadCoordinator.ReadGuardPort physical) {
            this.gameplay = gameplay; this.frontend = frontend; this.terminal = terminal; this.reconciliation = Objects.requireNonNull(reconciliation);
            this.physical = Objects.requireNonNull(physical);
        }
        @Override public void verifyFrontendReadContinuation(WriterContracts.Head head,PlanningReadRequest request,
                ReadContract<?> contract,PlanningReadGuard before,PlanningReadGuard after){
            if(!(request.origin() instanceof CommandOrigin.Frontend))
                throw new IllegalArgumentException("only the actual frontend source-bound scope can continue a frontend read");
            frontend.verifyFrontendReadContinuation(head,request,contract,before,after);
        }
        @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract) {
            if(!(request.origin() instanceof CommandOrigin.Gameplay))throw new IllegalArgumentException("current original read requires the actual admitted gameplay origin");
            return gameplay.verifyOriginalCurrent(head,request,contract);
        }
        @Override public <T> T withOriginalReadSource(WriterContracts.Head head,PlanningReadRequest request,
                ReadContract<?> contract,java.util.function.Supplier<T> work) {
            Objects.requireNonNull(work);
            PlanningReadCoordinator.ReadGuardPort retained=authorityFor(request);
            try { return retained.withOriginalReadSource(head,request,contract,work); }
            finally { StrictJson.require(retained==authorityFor(request),"original read source changed its origin authority"); }
        }
        @Override public PlanningReadGuard verify(WriterContracts.Head head, PlanningReadRequest request, ReadContract<?> contract) {
            return authorityFor(request).verify(head,request,contract);
        }
        private PlanningReadCoordinator.ReadGuardPort authorityFor(PlanningReadRequest request) {
            if (request.origin() instanceof CommandOrigin.PhysicalStatusOnly) return physical;
            if (request.origin() instanceof CommandOrigin.Gameplay) return gameplay;
            if (request.origin() instanceof CommandOrigin.LifecycleTerminal) return terminal;
            if (request.origin() instanceof CommandOrigin.Reconciliation) return reconciliation;
            if (request.origin() instanceof CommandOrigin.Frontend) return frontend;
            throw new IllegalArgumentException("the actual read-only reconciliation guard has not been installed in this Root view");
        }
    }
    /** The menu graph retains its original verifier object; only its actual same-Root readonly authority may be installed once. */
    private static final class ReconciliationLink implements PlanningReadCoordinator.ReadGuardPort,
            NativeRecordedEvidenceVerifier.ReconciliationGuardVerifier, ActionPorts.ReconciliationObservationPort {
        private RootReconciliationReadGuard reads;
        private RootReconciliationAuthority authority;
        synchronized void bind(RootReconciliationReadGuard actualReads, RootReconciliationAuthority actualAuthority) {
            StrictJson.require(reads == null && authority == null, "the original Root reconciliation authority is already installed");
            reads = Objects.requireNonNull(actualReads); authority = Objects.requireNonNull(actualAuthority);
        }
        @Override public synchronized PlanningReadGuard verify(WriterContracts.Head head, PlanningReadRequest request, ReadContract<?> contract) {
            if (reads == null) throw new IllegalStateException("actual Root reconciliation read authority is not admitted");
            return reads.verify(head, request, contract);
        }
        @Override public synchronized DriverObservationAssembler.Complete verify(GuardEvidence guard, ActionPorts.OutcomeArchive archive,
                ContinuityStorePort.Session same, OriginalEvidencePort originals) throws IOException {
            if (authority == null) throw new IOException("actual Root reconciliation archive authority is not admitted");
            return authority.verifyArchived(guard, archive, same, originals);
        }
        @Override public synchronized ActionPorts.PostconditionResult observe(ContinuityStorePort.Session same, ActionReceipt pending,
                Instant deadline, ActionPorts.ReconciliationWork work) throws IOException, InterruptedException {
            if (authority == null) throw new IOException("actual Root reconciliation observation authority is not admitted");
            return authority.observe(same, pending, deadline,
                    lease -> work.apply(lease.complete(), lease.identity(), lease.observationGuard()));
        }
    }
    private static final class InterruptedAssembly extends RuntimeException {
        private static final long serialVersionUID = 1L; private final InterruptedException interruption;
        private InterruptedAssembly(InterruptedException interruption) { super(interruption); this.interruption = interruption; }
    }
}

