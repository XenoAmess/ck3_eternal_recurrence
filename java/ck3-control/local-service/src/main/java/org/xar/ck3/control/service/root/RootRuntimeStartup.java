package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ReconciliationPendingBinding;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageCodec;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.RollbackPair;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.mcp.McpCoverage;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpHost;

/** One startup composition, one Core, one managed lifecycle and the real per-Game products.
 * Historical source references are metadata; actual products retain their execution ownership. */
public final class RootRuntimeStartup {
    private final RootRuntimeDefinitions.Inputs inputs;
    private final Clock clock;
    private final RootCoreBoundPorts ports;
    private final RootRuntimeSelectedSources selected;
    private final NativeLaunchPlan plan;
    private final RootRuntimeStorageGuard storage;
    private final CheckpointFiles files;
    private final RootStartupReceiptFiles receipts;
    private final RootRuntimePreparedSources.Rollback rollback;
    private final RootRuntimeSourceProducts.Prepared products;
    private final RootSelectedRegistrationConfiguration.Bound registration;
    private final RootPublicHandlerProductsFactory.Prepared publicProducts;
    private final RootRuntimePublicCatalog publicCatalog;
    private RootApplicationAssembly.Core owner;
    private RootManagedLifecycleFactory managedFactory;
    private JavaGameLifecycle lifecycle;
    private RootRuntimeReadiness readiness;
    private RootOfflineAnalysisWorker.Prepared offline;
    private RootEpisodeContinuationRuntime episodes;
    private RootM7CheckpointCaptureFactory savedCapture;
    private RootRestoreMaterialFactory restoreMaterials;
    private RootPostAdoptionCollector postAdoption;
    private RootStartupNextResources.Prepared nextResources;
    private RootStartupNextResources.Shared sharedNext;
    private McpExecutableDirectory.Complete frontendDirectory;
    private RootInstalledCatalog frontendDirectoryOwner;
    private PublicMcpHost frontendHost;
    private boolean frontendInstallEntered;
    private IOException frontendInstallFailure;
    private RootApplicationSession initial;
    private boolean lifecycleEntered,initialEntered;
    private RootInstalledCatalog originalResumeCatalog;
    private RootLegacyResumeRuntime originalResume;
    private final SessionClock sessionClock=new SessionClock.SystemClock();
    private final OriginalWindowReducer.Policy cyclePolicy=new OriginalWindowReducer.Policy(OriginalWindowReducer.TARGET_DAYS);

    public RootRuntimeStartup(RootRuntimeDefinitions.Inputs inputs,Clock clock)throws IOException {
        this.inputs=Objects.requireNonNull(inputs);this.clock=Objects.requireNonNull(clock);
        ports=new RootCoreBoundPorts(inputs.application());selected=new RootRuntimeSelectedSources(inputs);
        plan=NativeLaunchPlan.readExact(inputs.application().nativeLaunchPlan(),new NativeBridgeLaunchEvidence());
        storage=RootRuntimeStorageGuard.readExact(inputs,ports::requireWriter,clock);
        files=storage.checkpointFiles(new NativeCheckpointFiles());
        var frontend=RootRuntimePreparedSources.frontend(inputs,selected,storage,files,plan,clock);
        receipts=new RootStartupReceiptFiles(inputs,ports,storage,files,clock);
        rollback=RootRuntimePreparedSources.rollback(inputs,ports,files,clock);
        var settings=RootRuntimeDomainSettings.readExact(inputs.data(RootRuntimeDefinitionModel.DataRole.REMAINING_DOMAIN_SETTINGS),clock);
        var originals=RootRuntimeNativeOriginals.readExact(inputs.data(RootRuntimeDefinitionModel.DataRole.NATIVE_DOMAIN_ORIGINALS),clock);
        // Both fixture declarations are absent in the actual fresh ordinary registration. Their real decisions retain
        // the same selected-configuration original, avoiding a definitions -> configuration -> definitions hash cycle.
        var declarations=RootRuntimePublicCatalog.Sources.readOriginals(inputs);
        List<ExactRef> configured=declarations.admission().stream()
                .filter(value->value.admission()==McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION)
                .map(McpCoverage.Decision::actualAdmissionProducer).distinct().toList();
        if(configured.size()!=1)throw new IOException("INCOMPLETE_SELECTED_REGISTRATION: actual admission must bind one real current-configuration original for its fixture exclusions");
        registration=RootSelectedRegistrationConfiguration.readExact(configured.getFirst(),inputs,
                frontend.originalDriverImport().frozenProfile(),plan,clock);
        if(!registration.configuration().source(RootSelectedRegistrationConfiguration.SourceRole.ORIGINAL_NATIVE_DRIVER)
                .equals(inputs.source(RootRuntimeDefinitionModel.SourceRole.FRONTEND_ORIGINAL_DRIVER)))
            throw new IOException("frontend and actual registration must retain the identical original native_driver.py producer");
        var packageRequest=JavaRuntimePackageCodec.readRequest(inputs.configuration().runtimePackageRequestRef());
        products=RootRuntimeSourceProducts.prepare(inputs,selected,settings,originals,registration,frontend,ports,storage,files,packageRequest,plan,clock);
        publicProducts=RootPublicHandlerProductsFactory.prepare(inputs,ports,products.catalogs(),Optional.of(registration),settings,clock);
        publicCatalog=new RootRuntimePublicCatalog(RootRuntimePublicCatalog.Sources.read(inputs,publicProducts.handlers()),clock);
        requireCurrent();
    }
    /** Actual pre-Core typed bindings mint final admission DATA; this never installs a host or launches a Game. */
    RootBootstrapOutputContract.Output quotePublicAdmission(Path target)throws IOException {
        requireCurrent();var result=RootPublicMcpAdmission.quote(inputs,publicProducts.handlers(),registration,target,clock);
        requireCurrent();return result;
    }
    FileRef publishPublicAdmission(RootBootstrapInputFiles authority,Path target)throws IOException {
        requireCurrent();
        var result=RootPublicMcpAdmission.publish(inputs,publicProducts.handlers(),registration,authority,target,clock);
        requireCurrent();return result;
    }
    public void bindStartup(FileRef actual)throws IOException {requireCurrent();receipts.bindStartup(actual);}
    public void writeRuntimeReceipt(Path target,byte[] canonicalBytes)throws IOException {requireCurrent();receipts.writeRuntimeReceipt(target,canonicalBytes);}
    /** The same required object enters both Core's writer and immutable archive constructors before their first IO. */
    public StorageWriteGuard storageWriteGuard()throws IOException {requireCurrent();receipts.requireCurrent();return storage;}
    public synchronized void bindOriginalResume(RootApplicationAssembly.Core actual,RootInstalledCatalog installed)throws IOException {
        requireOwner(actual);Objects.requireNonNull(installed);
        if(installed.context().core()!=actual)throw new IOException("original resume producer crossed the actual Core/catalog");
        if(originalResume!=null){if(originalResumeCatalog!=installed)throw new IOException("actual original resume producer is already bound to another physical catalog");return;}
        var created=new RootLegacyResumeRuntime(installed.context(),products.frontend().originalDriverImport(),
                selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootLegacyResumeRuntime.class));
        created.requireOwner(actual);actual.bindOriginalResume(created);originalResume=created;originalResumeCatalog=installed;
    }
    public RootRuntimeCatalogFactory catalogFactory(){return products.catalogs();}
    /** Returns the identical source-bound handler Context already retained by the installed public products. */
    public RootPublicHandlerProductsFactory.Context publicHandlerContext()throws IOException {
        requireCurrent();return publicProducts.currentContext();
    }
    /** Same actual pre-Core factory used by the total composition; no second input/factory/Finance binding. */
    public RootDriverProductSourcesFactory driverProductSources()throws IOException {
        requireCurrent();return products.driverProductSources();
    }
    public Optional<RollbackPair.Authority> rollbackAuthority(){return rollback.writerAuthority();}
    public NativeLaunchPlan nativeLaunchPlan()throws IOException {requireCurrent();return plan;}
    public void requireCompleteMigration()throws IOException {
        requireCurrent();var start=receipts.requireCurrent();
        if(!start.authorityId().equals(inputs.configuration().startup().authorityId())
                ||!start.authorityId().equals(inputs.configuration().frontend().authorityId())
                ||!start.freshness().equals(java.time.Duration.ofMillis(inputs.configuration().startup().ordinaryFreshnessMs())))
            throw new IOException("actual startup authority/freshness must agree with the single retained source configuration");
        publicProducts.requireComplete();publicCatalog.requireCompleteDefinitions();
    }
    public synchronized JavaGameLifecycle gameLifecycle(RootApplicationAssembly.Core actual)throws IOException {
        requireOwner(actual);
        if(lifecycle!=null&&nextResources!=null)return lifecycle;
        if(lifecycleEntered)throw new IOException("partial managed/source construction is retained and cannot replay");
        lifecycleEntered=true;ports.bindCore(actual);owner=actual;
        if(actual.writer().storageGuard()!=storage||actual.writer().artifactStore().orElseThrow().storageGuard()!=storage)
            throw new IOException("the original Core writer/archive did not retain this identical whole runtime storage authority");
        RootRuntimePreparedSources.preflightRollback(rollback,ports,actual);
        managedFactory=new RootManagedLifecycleFactory(actual,products.catalogs(),plan,clock);
        ports.bindManagedLifecycleFactory(managedFactory);lifecycle=managedFactory.create();
        var start=receipts.requireCurrent();
        readiness=new RootRuntimeReadiness(actual,start.ordinaryPolicy(),start.freshness(),clock);
        episodes=new RootEpisodeContinuationRuntime(actual,products.catalogs());episodes.requireCore(actual,products.catalogs());
        savedCapture=new RootM7CheckpointCaptureFactory(actual.writer(),actual.writer()::requireSession,actual.journal(),actual.archive(),
                new RootCheckpointRuntimeAuthority(actual,products.catalogs()));
        var originalFrozen=products.frontend().originalDriverImport().frozenProfile();
        restoreMaterials=new RootRestoreMaterialFactory(lifecycle,selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootRestoreMaterials.class),
                inputs.configuration().frontend().retainedFrames(),originalFrozen);
        postAdoption=new RootPostAdoptionCollector(actual,ports,products.catalogs(),readiness,start.freshness(),clock,originalFrozen);
        RootOfflineAnalysisWorker.Prepared unowned=new RootOfflineAnalysisWorker.Prepared(products.settings().configuration().offline().configuration(),storage,files);
        boolean transferred=false;
        try {
            var actualShared=new RootStartupNextResources.Shared(actual,lifecycle,products.catalogs(),start.source(),start,
                    products.settings(),storage,files,readiness,inputs.configuration().frontend().retainedFrames(),cyclePolicy,unowned,sessionClock,
                    episodes,savedCapture,restoreMaterials,postAdoption,clock);
            var created=new RootStartupNextResources.Prepared(actualShared);
            created.requireCore(actual);actual.bindNextResources(created);nextResources=created;sharedNext=actualShared;offline=unowned;transferred=true;
            var publicRestore=new RootPublicRestoreRuntime(actualShared);publicRestore.requireCore(actual);actual.bindPublicRestoreRuntime(publicRestore);
        }finally{if(!transferred)unowned.close();}
        requireCurrent();return lifecycle;
    }
    public RootApplicationSession finishInitial(RootApplicationAssembly.Core actual,RootInstalledCatalog installed,
            GameplayEntryService.Admitted admitted,JavaGameLifecycle actualLifecycle,RootStartupConfiguration start,Clock actualClock)
            throws IOException,InterruptedException {
        requireOwner(actual);receipts.requireStartup(start);Objects.requireNonNull(installed);Objects.requireNonNull(admitted);
        synchronized(this){
            if(initial!=null)throw new IOException("initial finish cannot replay a committed entry or return a different publication state");
            if(initialEntered)throw new IOException("partial actual initial assembly is retained and cannot be replayed");
            if(actualLifecycle!=lifecycle||actualClock!=clock||owner!=actual||installed.context().core()!=actual||nextResources==null||offline==null)
                throw new IOException("initial finish crossed the retained Core/lifecycle/clock/source resources");
            initialEntered=true;
        }
        return finishBound(actual,installed,new FreshAdmission(admitted),start);
    }
    /** Called only by the actual explicit Saved Quarkus route after this same lifecycle returned Started. */
    public RootApplicationSession finishSaved(RootApplicationAssembly.Core actual,RootInstalledCatalog installed,
            RootSavedNativeCoordinator coordinator,JavaGameLifecycle actualLifecycle,RootStartupConfiguration start,Clock actualClock)
            throws IOException,InterruptedException {
        requireOwner(actual);receipts.requireStartup(start);Objects.requireNonNull(installed);Objects.requireNonNull(coordinator);
        coordinator.requireOwner(actualLifecycle,plan);
        synchronized(this) {
            if(initial!=null||initialEntered)throw new IOException("actual Saved initial assembly is consumed and cannot be replayed");
            if(actualLifecycle!=lifecycle||actualClock!=clock||owner!=actual||installed.context().core()!=actual
                    ||originalResume==null||originalResumeCatalog!=installed||nextResources==null||offline==null
                    ||!(plan.load() instanceof NativeLaunchPlan.SavedGame))
                throw new IOException("Saved finish crossed the original Core/catalog/lifecycle/resume or exact Saved plan");
            initialEntered=true;
        }
        var original=coordinator.adopt(installed.context(),originalResume,inputs.configuration().frontend().retainedFrames());
        return finishBound(actual,installed,new ColdAdmission(original,coordinator.deadline()),start);
    }
    private sealed interface InitialAdmission permits FreshAdmission,ColdAdmission {
        DriverBootstrap.Adopted driver();Instant deadline();
    }
    private record FreshAdmission(GameplayEntryService.Admitted actual) implements InitialAdmission {
        private FreshAdmission {Objects.requireNonNull(actual);}
        @Override public DriverBootstrap.Adopted driver(){return actual.driver();}
        @Override public Instant deadline(){return actual.actual().command().deadline();}
    }
    private record ColdAdmission(RootPrivateBootstrap.Original original,Instant deadline) implements InitialAdmission {
        private ColdAdmission {Objects.requireNonNull(original);Objects.requireNonNull(deadline);}
        @Override public DriverBootstrap.Adopted driver(){return original.adopted();}
    }
    private RootApplicationSession finishBound(RootApplicationAssembly.Core actual,RootInstalledCatalog installed,
            InitialAdmission admission,RootStartupConfiguration start)throws IOException,InterruptedException {
        var context=installed.context();var remaining=installed.remainingDomains();
        if(context.game().launchPlan()!=plan||!context.source().equals(start.source()))
            throw new IOException("actual initial catalog did not retain the identical frozen native plan and startup source");
        var checkpoints=start.checkpoints();
        for(Path directory:List.of(checkpoints.driverCheckpoint().getParent(),checkpoints.checkpointEvidence(),
                checkpoints.attachmentEvidence(),checkpoints.save().getParent()))storage.createManagedDirectories(directory);
        installed.bindPhysicalDriver(admission.driver());
        var ordinaryPolicy=admission instanceof ColdAdmission cold
                ?actual.writer().locked(same->readiness.coldPolicy(same,installed,cold.original(),admission.deadline())):start.ordinaryPolicy();
        var staged=actual.stage(admission.driver(),context.game(),context.sources(),ordinaryPolicy,start.freshness(),files,
                checkpoints.driverCheckpoint(),checkpoints.checkpointEvidence(),checkpoints.attachmentEvidence(),remaining.lifecycle().seedAdoption(),
                checkpoints.lineageId(),checkpoints.save());
        installed.bindSave(staged);
        RootApplicationSession assembled=actual.writer().locked(same->{
            actual.writer().requireSession(same);
            var runtime=admission instanceof ColdAdmission cold
                    ?readiness.cold(same,installed,staged,cold.original(),admission.deadline())
                    :readiness.initial(same,installed,staged,admission.deadline());
            var life=remaining.life();life.requireContext(context);
            var physical=remaining.lifecycle().physical();
            var derived=RootDerivedChildAuthority.install(context,installed.bindings(),life.infrastructure());
            var historyQualification=new RootUnresolvedHistoryQualification(actual.writer(),actual.archive(),admission.driver().authority(),
                    installed.readHistory(),installed.bindings().readCatalog());
            var pendingBinding=new ReconciliationPendingBinding(actual.writer(),actual.archive(),context.originals(),historyQualification);
            var historyEpoch=historyQualification.captureEpoch(same);
            actual.archive().bindReconciliationHistory(same,pendingBinding,historyEpoch);
            if(actual.archive().reconciliationHistoryBinding(historyEpoch)!=pendingBinding)
                throw new IOException("initial reconciliation archive lost the identical qualified history binding");
            var reconciliation=new RootReconciliationAuthority(actual.writer(),actual.archive(),physical,
                    pendingBinding,context.originals(),
                    context.frameLoader(),installed.bindings().readCatalog(),remaining.reconciliationReads(),clock);
            derived.requireOwner(context,installed.bindings());
            staged.prepareDispatcher(start.authorityId(),installed.bindings(),installed.frontend().authority(),physical,reconciliation,
                    remaining.lifecycle().closeAdmission(),derived.admission(),derived.replay(),runtime.capabilities(),installed.readHistory(),
                    installed.pendingBindings(),installed.requiredPending(),remaining.lifeReplay());
            var actualOffline=offline.install(installed,remaining.events().eventSources());actualOffline.requireContext(installed);
            var root=staged.finish(start.authorityId(),installed.bindings(),installed.frontend().authority(),physical,reconciliation,
                    remaining.lifecycle().closeAdmission(),remaining.lifecycle().terminalDecisions(),remaining.lifecycle(),derived.admission(),derived.replay(),
                    runtime.capabilities(),installed.readHistory(),remaining.lifeReplay(),runtime.planningInputs(),installed.pipeline(),
                    installed.pendingBindings(),installed.requiredPending(),cyclePolicy,actualOffline.port(),sessionClock,Optional.empty(),0,
                    installed.completion(),episodes,savedCapture,restoreMaterials,postAdoption);
            if(admission instanceof FreshAdmission fresh)installed.afterInitialEntry(same,RootInitialEpisodeProof.require(context,same,fresh.actual()));
            else installed.afterColdEntry(same,((ColdAdmission)admission).original());
            var current=physical.withSnapshot(same,admission.deadline(),lease->{
                lease.assertCurrent(same);var frame=lease.ordinary().orElseThrow(()->new IOException("initial planning requires its actual living physical frame"));
                lease.assertCurrent(same);return frame;
            });
            installed.initializePersistentPlanning(same,current);
            actual.writer().requireSession(same);return root;
        });
        synchronized(this){initial=assembled;}requireCurrent();return assembled;
    }
    /** Publish the one actual directory before START, using the same Menu, catalog and offline worker. */
    public synchronized McpExecutableDirectory.Complete installFrontendPublic(RootApplicationAssembly.Core actual,RootInstalledCatalog installed,
            PublicMcpHost host,Clock actualClock)throws IOException,InterruptedException {
        requireOwner(actual);Objects.requireNonNull(installed);Objects.requireNonNull(host);
        if(actualClock!=clock||installed.context().core()!=actual||offline==null||nextResources==null)
            throw new IOException("actual frontend directory requires its retained Core/catalog/clock/worker lifetime");
        if(frontendDirectory==null&&initial!=null)throw new IOException("first frontend directory installation cannot follow gameplay admission");
        if(frontendDirectory!=null){
            requireFrontendDirectory(installed,host);return frontendDirectory;
        }
        if(frontendInstallEntered)throw new IOException("original partial frontend host installation is retained and cannot be replayed",frontendInstallFailure);
        publicProducts.requireComplete();publicCatalog.requireCompleteDefinitions();frontendInstallEntered=true;
        try{
            var sameOffline=offline.install(installed,installed.remainingDomains().events().eventSources());sameOffline.requireContext(installed);
            var complete=RootFrontendPublicHostFactory.install(actual,installed,publicCatalog,products.catalogs(),host,clock);
            if(host.current().filter(value->value==complete.directory()).isEmpty())
                throw new IOException("actual frontend host did not retain its original complete directory");
            frontendDirectory=complete;frontendDirectoryOwner=installed;frontendHost=host;return complete;
        }catch(IOException failure){frontendInstallFailure=failure;throw failure;}
        catch(InterruptedException failure){frontendInstallFailure=new IOException("actual frontend host installation was interrupted",failure);throw failure;}
        catch(RuntimeException failure){frontendInstallFailure=new IOException("actual frontend host installation failed",failure);throw frontendInstallFailure;}
    }
    public synchronized McpExecutableDirectory.Complete installPublic(RootApplicationAssembly.Core actual,RootInstalledCatalog installed,
            PublicMcpHost host,Clock actualClock)throws IOException,InterruptedException {
        requireOwner(actual);Objects.requireNonNull(installed);Objects.requireNonNull(host);
        if(actualClock!=clock||installed.context().core()!=actual||initial==null||initial.isRetired())
            throw new IOException("actual public admission requires the same complete admitted initial Root");
        publicProducts.requireComplete();publicCatalog.requireCompleteDefinitions();requireFrontendDirectory(installed,host);
        return frontendDirectory;
    }
    private void requireFrontendDirectory(RootInstalledCatalog installed,PublicMcpHost host)throws IOException {
        if(frontendDirectory==null||frontendDirectoryOwner!=installed||frontendHost!=host
                ||host.current().filter(value->value==frontendDirectory.directory()).isEmpty())
            throw new IOException("the original frontend directory/catalog/host is absent or has changed");
    }
    /** The actual managed integration test retains this original object; creating another supplier would violate its identity. */
    public synchronized RootStartupNextResources.Prepared nextResources(RootApplicationAssembly.Core actual)throws IOException {
        requireOwner(actual);if(nextResources==null)throw new IOException("actual Core next resources have not been constructed");
        nextResources.requireCore(actual);return nextResources;
    }
    /** Exact original lifetime resources for the separate concrete public RESTORE factory; no replacement pool or store. */
    public synchronized RootStartupNextResources.Shared requireNextShared(RootApplicationAssembly.Core actual)throws IOException {
        nextResources(actual);if(sharedNext==null)throw new IOException("original shared runtime resources are not retained");return sharedNext;
    }
    private void requireOwner(RootApplicationAssembly.Core actual)throws IOException {
        requireCurrent();Objects.requireNonNull(actual);
        if(!actual.configuration().equals(inputs.application())||actual.archive().writer()!=actual.writer()||owner!=null&&owner!=actual)
            throw new IOException("startup belongs to another actual Core/writer/configuration");
        products.catalogs().requireBoundCore(actual);
    }
    /** Repeated access retains the captured Inputs without reopening historical source files. */
    private void requireCurrent()throws IOException {
        selected.requireInputs(inputs);
    }
}
