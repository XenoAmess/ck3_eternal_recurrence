package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.planning.finance.FinanceRuntimeServices;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.platform.ManagedGameSession;

/** Per-physical-Game dependencies. This link is not a source, restore, readiness or dispatch qualification. */
public final class RootRuntimeContext {
    private RootFrontendRuntime frontend;
    private RootRuntimeDomainAssembly.Installed remainingDomains;
    private KnownInteractionsRuntimeInstaller interactions;
    private final RootApplicationAssembly.Core core;
    private final ManagedGameSession game;
    private final G2Source source;
    private final RootPlanningReads reads;
    private final Clock clock;
    private final ReadinessAuthority readiness=new OwnedReadiness();
    private RootPhysicalStatusReadAuthority physicalStatusReads;
    private RootExecutableBindings bindings;
    private DriverBootstrap.Adopted adopted;
    private NativeReadinessCollector collector;
    private RootApplicationSession session;
    private Restoration restoration;
    private RootColdReboundRuntime.ColdReboundOrigin coldReboundOrigin;
    private org.xar.ck3.control.contracts.ExactRef restorationBasis;
    private FinanceRuntimeServices finance;
    private SavedAttachmentSourceStore savedSources;
    private SavedCheckpointMaterialStore savedMaterials;
    private RootNativeSourceAuthority sources;
    private DriverCapabilityRuntime capabilities;
    private FixtureHistory fixtureHistory;
    private RootReconciliationAuthority reconciliation;
    public RootRuntimeContext(RootApplicationAssembly.Core core,ManagedGameSession actualGame,G2Source actualSource,
            RootPlanningReads sameReads,Clock clock)throws IOException {
        this.core=Objects.requireNonNull(core);game=Objects.requireNonNull(actualGame);source=Objects.requireNonNull(actualSource);
        reads=Objects.requireNonNull(sameReads);this.clock=Objects.requireNonNull(clock);
        StrictJson.require(source.machineId().equals(game.machineId()) && core.archive().writer()==core.writer(),
                "runtime must retain its exact current physical Game and original writer/archive");
        game.verify();
    }
    public RootApplicationAssembly.Core core() { return core; }
    public ManagedGameSession game() { return game; }
    public G2Source source() { return source; }
    public RootPlanningReads reads() { return reads; }
    public Clock clock() { return clock; }
    public ContinuityWriter writer() { return core.writer(); }
    /** Never retain an archive bound to a particular borrowed Session in a long-lived installer. */
    public NativeOutcomeArchive archive() { return core.archive(); }
    public ArchiveOriginalEvidencePort originals() { return core.originals(); }
    public DriverFrameEvidenceLoader frameLoader() { return core.frameLoader(); }
    public NativeSemanticEvidenceVerifier semanticVerifier() { return core.semanticVerifier(); }
    public NativeGameTransport transport()throws IOException { game.verify();return game.nativeTransport(); }
    public ContinuityStorePort.Session borrowedSession()throws IOException { return writer().borrowedSession(); }
    @FunctionalInterface public interface SessionWork<T> { T run(ContinuityStorePort.Session same)throws IOException; }
    /** Borrow a verified active scope, or acquire the original writer once when no scope exists on this thread. */
    public <T> T withSession(SessionWork<T> work)throws IOException {
        Objects.requireNonNull(work);var active=writer().activeSession();
        if(active.isPresent()) {
            var same=active.orElseThrow();writer().requireSession(same);
            try { return work.run(same); } finally { writer().requireSession(same); }
        }
        return writer().locked(same->work.run(same));
    }
    public ReadinessAuthority readiness() { return readiness; }
    synchronized void bindPhysicalStatusReads(RootPhysicalStatusReadAuthority actual)throws IOException {
        Objects.requireNonNull(actual).requireContext(this);
        if(physicalStatusReads!=null&&physicalStatusReads!=actual)
            throw new IOException("physical Status reads are already bound to their identical actual runtime issuer");
        physicalStatusReads=actual;
    }
    public synchronized RootPhysicalStatusReadAuthority physicalStatusReads()throws IOException {
        if(physicalStatusReads==null)throw new IOException("actual physical Status read issuer has not been installed");
        return physicalStatusReads;
    }
    public <T> T currentPlanning(ContinuityStorePort.Session borrowed,
            org.xar.ck3.control.application.planning.PlanningRequest original,ActionCommand actual,
            Instant deadline,NativeReadinessCollector.PlanningWork<T> work)throws IOException {
        writer().requireSession(borrowed);
        return collector().currentPlanning(borrowed,original,actual,deadline,work);
    }
    public synchronized RootNativeSourceAuthority sources() {
        StrictJson.require(sources!=null,"actual physical Game source authority has not been installed");return sources;
    }
    synchronized void bindSources(RootNativeSourceAuthority actual) {
        StrictJson.require(sources==null,"physical Game source authority is once bound");sources=Objects.requireNonNull(actual);
    }
    public synchronized RootExecutableBindings bindings() {
        StrictJson.require(bindings!=null,"actual runtime inventory has not been installed");return bindings;
    }
    public RootReadContractCatalog readCatalog() { return bindings().readCatalog(); }
    public synchronized RootReconciliationAuthority reconciliation() {
        StrictJson.require(reconciliation!=null,"actual same-runtime reconciliation authority has not been installed");return reconciliation;
    }
    synchronized void bindReconciliation(RootReconciliationAuthority actual,RootLifecycleAuthority samePhysical) {
        StrictJson.require(reconciliation==null,"reconciliation authority is once bound for this physical Game");
        Objects.requireNonNull(actual).requireOwner(writer(),archive(),readCatalog(),Objects.requireNonNull(samePhysical));
        reconciliation=actual;
    }
    synchronized void bindCapabilities(DriverBootstrap.Adopted actual,DriverCapabilityRuntime capabilityRuntime) {
        StrictJson.require(capabilities==null||(fixtureHistory!=null&&capabilities==capabilityRuntime&&fixtureHistory.authority()==actual.authority()),"one actual capability runtime per physical Game context required");
        Objects.requireNonNull(capabilityRuntime).requireOwner(actual.authority(),archive(),bindings());
        StrictJson.require(actual.source().equals(source) && actual.session().game().equals(game.generation())
                && actual.session().sessionId().equals(game.sessionId()),"capability runtime crossed this actual physical Game");
        capabilities=capabilityRuntime;
    }
    /** Binds the genuine source-owned terminal ROOT reader to this already installed capability runtime. */
    public synchronized void bindPublicPlanningTerminalRootReadSource(DriverCapabilityRuntime.PublicPlanningTerminalRootReadSource actual)throws IOException {
        if(capabilities==null)throw new IOException("actual same-context capability runtime must precede terminal ROOT source binding");
        capabilities.bindPublicPlanningTerminalRootReadSource(Objects.requireNonNull(actual));
    }
    /** Actual private Staged custody; this publishes no Adopted, current collector or readiness. */
    synchronized void bindFixtureHistory(InitialDriverBootstrap.Staged stage,DriverStateAssembler authority)throws IOException {
        var same=writer().borrowedSession();Objects.requireNonNull(stage);Objects.requireNonNull(authority);writer().requireSession(same);game.verify();
        StrictJson.require(adopted==null&&frontend().fixture().isPresent(),"only explicit pre-entry fixture can bind staged history custody");
        stage.requireFixtureOwner(same,game,source);stage.requireFixtureBootstrap(same,frontend().initialDriver());
        StrictJson.require(stage.fixtureAuthority(same)==authority,"fixture history authority differs from the actual retained staged Driver");
        if(fixtureHistory!=null)StrictJson.require(fixtureHistory.stage()==stage&&fixtureHistory.authority()==authority,"fixture history custody cannot be rebound");
        else fixtureHistory=new FixtureHistory(stage,authority);
    }
    /** Same history authority across the explicit pre-entry stage and its actual subsequent adoption. */
    public synchronized DriverStateAssembler historyAuthority(ContinuityStorePort.Session same)throws IOException {
        writer().requireSession(same);game.verify();
        if(adopted!=null) {
            StrictJson.require(adopted.source().equals(source)&&adopted.session().game().equals(game.generation())
                    &&adopted.session().sessionId().equals(game.sessionId()),"adopted history authority crossed the physical context");
            if(fixtureHistory!=null)StrictJson.require(fixtureHistory.authority()==adopted.authority(),"fixture adoption lost its sole staged history authority");
            return adopted.authority();
        }
        FixtureHistory retained=fixtureHistory;
        if(retained==null)throw new IOException("actual adopted or explicit private staged history authority is unavailable");
        retained.stage().requireFixtureOwner(same,game,source);retained.stage().requireFixtureBootstrap(same,frontend().initialDriver());
        StrictJson.require(retained.stage().fixtureAuthority(same)==retained.authority(),"actual fixture staged authority changed");
        game.verify();writer().requireSession(same);return retained.authority();
    }
    synchronized void bindFixtureCapabilities(InitialDriverBootstrap.Staged stage,DriverCapabilityRuntime actual)throws IOException {
        var same=writer().borrowedSession();
        StrictJson.require(fixtureHistory!=null&&fixtureHistory.stage()==Objects.requireNonNull(stage),"fixture capability binding requires its actual staged history custody");
        Objects.requireNonNull(actual).requireOwner(historyAuthority(same),archive(),bindings());
        StrictJson.require(capabilities==null||capabilities==actual,"fixture cannot replace its sole capability runtime");capabilities=actual;
    }
    public synchronized DriverReadHistoryPublisher readHistoryPublisher() {
        StrictJson.require(capabilities!=null,"actual read-history publisher is unavailable before capability binding");
        return capabilities.readHistoryPublisher();
    }
    public synchronized DriverBootstrap.Adopted adopted() {
        StrictJson.require(adopted!=null,"actual current Driver has not been bound");return adopted;
    }
    /** Phase-one raw Native/Driver publication only; no capability hooks, planning or ready qualification. */
    synchronized void bindPhysicalDriver(DriverBootstrap.Adopted actual)throws IOException {
        Objects.requireNonNull(actual);game.verify();
        StrictJson.require((adopted==null||adopted==actual)&&actual.source().equals(source)
                &&actual.session().game().equals(game.generation())&&actual.session().sessionId().equals(game.sessionId())
                &&actual.session().machineId().equals(game.machineId()),"physical Driver must retain this exact replacement source/session");
        if(fixtureHistory!=null)StrictJson.require(fixtureHistory.authority()==actual.authority(),"fixture adoption cannot replace its actual staged history authority");
        actual.producer().requireSameTransport(game.nativeTransport(),source);adopted=actual;
    }
    public synchronized java.util.Optional<NativeDriverObservationProducer> optionalDriverProducer() {
        return adopted==null?java.util.Optional.empty():java.util.Optional.of(adopted.producer());
    }
    public synchronized NativeReadinessCollector collector() {
        StrictJson.require(collector!=null,"actual current collector has not been bound");return collector;
    }
    public synchronized ActionCoordinatorPort actions() {
        StrictJson.require(session!=null,"actual Root session dispatcher has not been bound");return session;
    }
    public synchronized FinanceRuntimeServices finance() {
        StrictJson.require(finance!=null,"actual same-Game finance services have not been installed");return finance;
    }
    public synchronized RootFrontendRuntime frontend() {
        StrictJson.require(frontend!=null,"actual same-Game frontend runtime has not been installed");return frontend;
    }
    public synchronized KnownInteractionsRuntimeInstaller interactions() {
        StrictJson.require(interactions!=null,"actual same-Game known interactions have not been installed");return interactions;
    }
    synchronized void bindInteractions(KnownInteractionsRuntimeInstaller actual)throws IOException {
        Objects.requireNonNull(actual);actual.requireContext(this);
        if(interactions!=null)throw new IOException("known interactions can be installed only once for this identical context");
        interactions=actual;
    }
    synchronized void bindFrontend(RootFrontendRuntime actual)throws IOException {
        Objects.requireNonNull(actual);actual.requireContext(this);
        if(frontend!=null)throw new IOException("actual frontend runtime can be installed only once for this identical context");
        frontend=actual;
    }
    public synchronized RootRuntimeDomainAssembly.Installed remainingDomains() {
        StrictJson.require(remainingDomains!=null,"actual remaining business domains have not been installed");return remainingDomains;
    }
    synchronized void bindRemainingDomains(RootRuntimeDomainAssembly.Installed actual)throws IOException {
        Objects.requireNonNull(actual);actual.requireContext(this);
        if(remainingDomains!=null)throw new IOException("remaining business domains can be installed only once for this identical context");
        remainingDomains=actual;
    }
    public synchronized void bindFinance(FinanceRuntimeServices actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(finance==null && actual.game().equals(game.generation()) && actual.sessionId().equals(game.sessionId())
                && actual.source().equals(source),"finance services must be installed once for this actual physical Game");
        finance=actual;
    }
    public synchronized SavedAttachmentSourceStore savedSources() {
        StrictJson.require(savedSources!=null,"actual Root saved source store has not been bound");return savedSources;
    }
    synchronized void bindSavedSources(SavedAttachmentSourceStore actual) {
        Objects.requireNonNull(actual);StrictJson.require(savedSources==null || savedSources==actual,"cannot replace the original saved source store");
        savedSources=actual;
    }
    public synchronized SavedCheckpointMaterialStore savedMaterials() {
        StrictJson.require(savedMaterials!=null,"actual typed ordinary/FIRST checkpoint material store is not bound");return savedMaterials;
    }
    synchronized void bindSavedMaterials(SavedCheckpointMaterialStore actual) {
        Objects.requireNonNull(actual);StrictJson.require(savedMaterials==null||savedMaterials==actual,
                "cannot replace the actual typed checkpoint material aggregate");savedMaterials=actual;
    }
    synchronized void bindInventory(RootExecutableBindings actual) {
        StrictJson.require(bindings==null,"runtime inventory is once bound");bindings=Objects.requireNonNull(actual);
    }
    synchronized void bindReadiness(DriverBootstrap.Adopted actual,NativeReadinessCollector actualCollector)throws IOException {
        StrictJson.require((adopted==null||adopted==actual) && collector==null,"runtime Driver/readiness is once bound");
        Objects.requireNonNull(actual);Objects.requireNonNull(actualCollector);game.verify();
        var identity=actualCollector.identity();
        StrictJson.require(actual.source().equals(source) && actual.session().game().equals(game.generation())
                && actual.session().sessionId().equals(game.sessionId()) && actual.session().machineId().equals(game.machineId())
                && identity.game().equals(game.generation()) && identity.sessionId().equals(game.sessionId())
                && identity.machineId().equals(game.machineId()),"runtime Driver/collector crossed the physical Game");
        actual.producer().requireSameTransport(game.nativeTransport(),source);
        adopted=actual;collector=actualCollector;
    }
    public synchronized void bindSession(RootApplicationSession actual)throws IOException {
        Objects.requireNonNull(actual);game.verify();
        StrictJson.require(session==null && collector!=null && actual.ownedBy(core)&&actual.writer()==writer() && actual.archive()==archive()
                && actual.driver()==adopted && actual.readiness()==collector && actual.identity().equals(collector.identity())
                && !actual.isRetired(),"runtime dispatcher must be its actual once-created Root session");
        session=actual;
        bindSavedSources(actual.savedSources());
        bindSavedMaterials(actual.savedMaterials());
    }
    public synchronized void bindRestoration(RestoreCheckpointService actualService,RestoreCheckpointService.RestoreBinding actual,
            Instant deadline)throws IOException,InterruptedException {
        StrictJson.require(restoration==null&&coldReboundOrigin==null,"actual warm restoration is once bound and cannot replace a cold origin");
        Objects.requireNonNull(actualService).requireCurrent(Objects.requireNonNull(actual),deadline);
        StrictJson.require(actual.session().game().equals(game.generation()) && actual.session().sessionId().equals(game.sessionId())
                && actual.session().machineId().equals(game.machineId()),"restoration belongs to another physical Game");
        restoration=new Restoration(actualService,actual);
        withSession(same->{captureRestorationOriginal(same,actual);return null;});
    }
    /** The actual restore service already minted this binding before post-adoption domain imports. */
    public synchronized void bindRetainedRestoration(ContinuityStorePort.Session same,RestoreCheckpointService actualService,
            RestoreCheckpointService.RestoreBinding actual)throws IOException {
        writer().requireSession(same);Objects.requireNonNull(actualService);Objects.requireNonNull(actual);game.verify();
        StrictJson.require(restoration==null&&coldReboundOrigin==null&&actual.session().game().equals(game.generation())
                &&actual.session().sessionId().equals(game.sessionId())&&actual.session().machineId().equals(game.machineId())
                &&actual.source().equals(source),"retained restoration must be this exact private replacement source");
        actualService.requireRetainedOriginal(same,actual);restoration=new Restoration(actualService,actual);
        captureRestorationOriginal(same,actual);
    }
    private void captureRestorationOriginal(ContinuityStorePort.Session same,RestoreCheckpointService.RestoreBinding actual)throws IOException {
        StrictJson.require(restorationBasis==null,"restoration original custody is captured once before ordinary mutations");
        restorationBasis=RootRestorationOriginalProof.require(this,same,actual).preserveOriginal(same);
    }
    /** Historical material of this privately admitted replacement; normal later SAVE/READ/domain writes do not reload its old pair. */
    public RootRestorationOriginalProof.Original restorationOriginal(ContinuityStorePort.Session same)throws IOException {
        Restoration retained;org.xar.ck3.control.contracts.ExactRef basis;
        synchronized(this){retained=restoration;basis=restorationBasis;}
        writer().requireSession(same);
        if(retained==null||basis==null)throw new IOException("actual immutable restoration originals have not been captured");
        requireRestorationOriginal(same,retained.binding());
        var original=RootRestorationOriginalProof.replayOriginal(this,same,basis);
        StrictJson.require(original.game().equals(game.generation())&&original.sessionId().equals(game.sessionId())
                &&original.source().equals(source)&&original.pair().equals(retained.binding().pair()),
                "retained original does not belong to this privately admitted replacement");
        return original;
    }
    /** Retained private origin only; this does not grant a current read, reload or new restore. */
    public void requireRestorationOriginal(ContinuityStorePort.Session same,RestoreCheckpointService.RestoreBinding binding)throws IOException {
        Restoration original;
        synchronized(this){original=restoration;}
        writer().requireSession(same);game.verify();
        StrictJson.require(original!=null&&original.binding()==binding
                &&binding.session().game().equals(game.generation())&&binding.session().sessionId().equals(game.sessionId())
                &&binding.source().equals(source),"actual private restoration belongs to another context");
        original.service().requireRetainedOriginal(same,binding);
    }
    /** Only the real cold producer can issue this retained token; DATA decoding cannot bind it. */
    public synchronized void bindColdReboundOrigin(ContinuityStorePort.Session same,RootColdReboundRuntime.ColdReboundOrigin actual)throws IOException {
        Objects.requireNonNull(actual);writer().requireSession(same);game.verify();
        StrictJson.require(restoration==null&&actual.context()==this&&(coldReboundOrigin==null||coldReboundOrigin==actual),
                "cold rebound must retain its sole original context and cannot replace a warm restoration");
        for(Class<?> type:RootColdReboundRuntime.requiredSourceTypes())game.launchPlan().sources().requireLoadedClass(type);
        actual.requireOriginal(same);game.verify();writer().requireSession(same);
        coldReboundOrigin=actual;
    }
    /** Retained canonical cold originals only. It grants no current SnapshotLease, Native action or SAVE permission. */
    public RootColdReboundRuntime.ColdReboundOrigin requireColdReboundOrigin(ContinuityStorePort.Session same)throws IOException {
        RootColdReboundRuntime.ColdReboundOrigin actual;
        synchronized(this){actual=coldReboundOrigin;}
        writer().requireSession(same);game.verify();
        if(actual==null)throw new IOException("actual privately retained cold rebound issuer is unavailable");
        StrictJson.require(actual.context()==this&&restoration==null,"cold rebound crossed the actual physical runtime context");
        for(Class<?> type:RootColdReboundRuntime.requiredSourceTypes())game.launchPlan().sources().requireLoadedClass(type);
        actual.requireOriginal(same);game.verify();writer().requireSession(same);
        for(Class<?> type:RootColdReboundRuntime.requiredSourceTypes())game.launchPlan().sources().requireLoadedClass(type);
        return actual;
    }
    /** Private actual restore origin only. This grants no current SnapshotLease, Native or SAVE qualification. */
    public RestoreCheckpointService.ReboundOrigin requireRestoredOrigin(ContinuityStorePort.Session same)throws IOException {
        Restoration retained;
        synchronized(this){retained=restoration;}
        writer().requireSession(same);game.verify();
        if(retained==null)throw new IOException("actual privately retained restoration issuer is unavailable");
        requireRestorationOriginal(same,retained.binding());
        game.launchPlan().sources().requireLoadedClass(RestoreCheckpointService.class);
        game.launchPlan().sources().requireLoadedClass(org.xar.ck3.control.application.checkpoint.RestoredEpisodeOriginData.class);
        RestoreCheckpointService.ReboundOrigin origin=retained.binding().requireReboundOrigin(same);
        origin.requireOriginal(same);
        requireRestorationOriginal(same,retained.binding());game.verify();writer().requireSession(same);
        game.launchPlan().sources().requireLoadedClass(RestoreCheckpointService.class);
        game.launchPlan().sources().requireLoadedClass(org.xar.ck3.control.application.checkpoint.RestoredEpisodeOriginData.class);
        return origin;
    }
    /** Historical material is loaded only through the genuinely retained restore issuer and its typed aggregate store. */
    public SavedCheckpointMaterial loadRestorationMaterialOriginal(ContinuityStorePort.Session same,
            SavedCheckpointMaterial.Kind kind,CheckpointPair.FileWitness originalWitness,CheckpointPair pair)throws IOException {
        Restoration retained;
        synchronized(this){retained=restoration;}
        writer().requireSession(same);
        if(retained==null)throw new IOException("actual private restoration issuer is unavailable");
        requireRestorationOriginal(same,retained.binding());
        var admitted=retained.binding().savedMaterial();
        StrictJson.require(admitted.kind()==Objects.requireNonNull(kind)&&admitted.witness().equals(Objects.requireNonNull(originalWitness))
                &&admitted.pair().equals(Objects.requireNonNull(pair)),"retained material kind, original identity and pair crossed the actual private restore");
        return retained.service().loadRetainedMaterialOriginal(same,kind,originalWitness,pair);
    }
    public RestoreCheckpointService.RestoreBinding requireRestoration(Instant deadline)throws IOException,InterruptedException {
        Restoration actual;
        synchronized(this) { actual=restoration; }
        if(actual==null)throw new IOException("actual committed restoration binding is not available");
        requireCurrent(deadline);
        withSession(same->{actual.service().requireRetainedOriginal(same,actual.binding());return null;});
        game.verify();return actual.binding();
    }
    public void requireCurrent(Instant deadline)throws IOException {
        StrictJson.require(clock.instant().isBefore(Objects.requireNonNull(deadline)),"runtime context deadline expired");game.verify();
        synchronized(this) {
            StrictJson.require(session==null || !session.isRetired(),"runtime belongs to a retired physical Game");
        }
    }
    private final class OwnedReadiness implements ReadinessAuthority {
        @Override public <T> T currentDerivedCleanup(ContinuityStorePort.Session borrowed,ObservationIdentity expected,
                Instant deadline,PhysicalReadWork<T> work)throws IOException {
            writer().requireSession(borrowed);Objects.requireNonNull(expected);Objects.requireNonNull(work);
            requireCurrent(deadline);NativeReadinessCollector actual=collector();
            StrictJson.require(expected.game().equals(game.generation()) && expected.machineId().equals(game.machineId()),
                    "runtime cleanup source crossed its physical Game");
            return actual.currentDerivedCleanup(borrowed,expected,deadline,physical->{
                writer().requireSession(borrowed);requireCurrent(deadline);
                T result=work.apply(physical);
                writer().requireSession(borrowed);requireCurrent(deadline);return result;
            });
        }
        @Override public <T> T current(ContinuityStorePort.Session borrowed,ObservationIdentity expected,Instant callerDeadline,CheckedWork<T> work)throws IOException {
            writer().requireSession(borrowed);NativeReadinessCollector actual=collector();
            StrictJson.require(expected.game().equals(game.generation()) && expected.machineId().equals(game.machineId()),
                    "runtime read scope crossed its physical Game");
            return actual.current(borrowed,expected,callerDeadline,work);
        }
    }
    private record FixtureHistory(InitialDriverBootstrap.Staged stage,DriverStateAssembler authority) { }
    private record Restoration(RestoreCheckpointService service,RestoreCheckpointService.RestoreBinding binding) { }
}

