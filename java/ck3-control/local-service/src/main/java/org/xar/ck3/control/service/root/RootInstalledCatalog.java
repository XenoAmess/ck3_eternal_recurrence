package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.CapabilityFileProbe;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission;

/** Exact products from a successful actual catalog installation; no public constructor can forge ownership. */
public final class RootInstalledCatalog {
    private final RootRuntimeCatalogFactory factory;
    private final RootRuntimeContext context;
    private final RootExecutableBindings bindings;
    private final List<RootDomainInstallation> domains;
    private final CapabilityFileProbe files;
    private final ArmyRuntimeInstaller army;
    private final PrisonersRuntimeInstaller prisoners;
    private final GovernanceRuntimeInstaller.Installed nativeGovernance;
    private final GovernanceOrdinaryRuntimeInstaller.Installed governance;
    private final GovernanceActivityRuntime activity;
    private final RootFrontendRuntime frontend;
    private final KnownInteractionsRuntimeInstaller interactions;
    private final RootIncidentRuntime offline;
    private final ConstructionRuntimeInstaller construction;
    private final OrdinaryMilitaryInstaller military;
    private final ArmyAdditionalReadInstaller.Installed additionalArmy;
    private final RootSaveRuntime save;
    private final RootAubRuntimeFactory.Runtime aub;
    private final RootContactRuntime contactScopes;
    private final RootCoreFrameRuntime coreFrame;
    private final RootArmyDeclarationDiagnostics declarationDiagnostics;
    private final RootRuntimeDomainAssembly.Installed remaining;
    private final RootAdditionalDomains.Installed additionalDomains;
    private final RootMilitaryControlStepRuntime.Installed militaryControls;
    private final RootArmyStructuralStepRuntime armyStructural;
    private final RootPublicPauseRuntime.Installed publicPause;
    private final RootPublicPauseArchiveClassifier publicPauseClassifier;
    private boolean resourcesClosed;
    private final CrossRunPlanningDomain crossRun;
    private final RootPlanningDomainCatalog domainCatalog;
    private final NativeReadinessCollector.PlanningEvidenceVerifier planningEvidence;
    private DriverBootstrap.Adopted adopted;
    private DriverCapabilityRuntime capabilities;
    private NativeReadinessCollector.PlanningInputsPort planning;
    private M7KernelInputs kernelInputs;
    private RootM7ReadyPublication readyPublication;
    private DriverReadHistoryPublisher readHistory;
    private InitialDriverBootstrap.Staged fixtureStage;
    private FixtureProducts fixtureProducts;
    private OrdinaryPlanningPipeline fullPipeline;
    private NativeCampaignCapabilitySource nativeCampaignCapabilitySource;
    private org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.ReboundOrigin restoredNativeCampaignOrigin;
    private RootFrozenRunProfile.FrozenRunProfile restoredNativeCampaignFrozen;
    private RootPublicStepExecution.Catalog publicSteps;
    private RestoredFeastOriginal restoredFeastOriginal;
    private FirstRestoredInitialization firstRestoredInitialization;
    private record FirstRestoredInitialization(RootApplicationAssembly.EpisodeDomainInitializationProof proof,
            List<DomainBodies.BodyRef> bodies) {
        private FirstRestoredInitialization {Objects.requireNonNull(proof);bodies=List.copyOf(bodies);}
    }
    RootInstalledCatalog(RootRuntimeCatalogFactory factory,RootRuntimeContext context,RootExecutableBindings bindings,
            List<RootDomainInstallation> domains,CapabilityFileProbe files,ArmyRuntimeInstaller army,
            PrisonersRuntimeInstaller prisoners,GovernanceRuntimeInstaller.Installed nativeGovernance,
            GovernanceOrdinaryRuntimeInstaller.Installed governance,GovernanceActivityRuntime activity,RootFrontendRuntime frontend,
            KnownInteractionsRuntimeInstaller interactions,
            RootIncidentRuntime offline,CrossRunPlanningDomain crossRun,ConstructionRuntimeInstaller construction,
            OrdinaryMilitaryInstaller military,ArmyAdditionalReadInstaller.Installed additionalArmy,RootSaveRuntime save,RootAubRuntimeFactory.Runtime aub,RootContactRuntime contactScopes,
            RootRuntimeDomainAssembly.Installed remaining,RootAdditionalDomains.Installed additionalDomains,
            RootMilitaryControlStepRuntime.Installed militaryControls,RootArmyStructuralStepRuntime armyStructural,
            RootPublicPauseRuntime.Installed publicPause)throws IOException {
        this.factory=Objects.requireNonNull(factory);this.context=Objects.requireNonNull(context);this.bindings=Objects.requireNonNull(bindings);
        this.domains=List.copyOf(domains);this.files=Objects.requireNonNull(files);this.army=Objects.requireNonNull(army);
        this.prisoners=Objects.requireNonNull(prisoners);this.nativeGovernance=Objects.requireNonNull(nativeGovernance);
        this.governance=Objects.requireNonNull(governance);this.activity=Objects.requireNonNull(activity);
        this.frontend=Objects.requireNonNull(frontend);
        this.interactions=Objects.requireNonNull(interactions);
        this.offline=Objects.requireNonNull(offline);this.crossRun=Objects.requireNonNull(crossRun);
        this.construction=Objects.requireNonNull(construction);this.military=Objects.requireNonNull(military);this.additionalArmy=Objects.requireNonNull(additionalArmy);
        this.save=Objects.requireNonNull(save);this.aub=Objects.requireNonNull(aub);this.contactScopes=Objects.requireNonNull(contactScopes);
        StrictJson.require(this.contactScopes.context()==context,
                "Contact READ runtime must retain this identical actual per-Game context");
        this.remaining=Objects.requireNonNull(remaining);
        this.additionalDomains=Objects.requireNonNull(additionalDomains);this.additionalDomains.requireContext(context);
        this.militaryControls=Objects.requireNonNull(militaryControls);this.militaryControls.requireContext(context);
        if(this.domains.stream().noneMatch(actual->actual==this.militaryControls.installation()))
            throw new IOException("military controls are absent from this identical installed Root catalog");
        this.armyStructural=Objects.requireNonNull(armyStructural);this.armyStructural.requireContext(context);
        if(this.domains.stream().noneMatch(actual->actual==this.armyStructural.installation()))
            throw new IOException("army structural actions are absent from this identical installed Root catalog");
        this.publicPause=Objects.requireNonNull(publicPause);this.publicPause.requireContext(context);
        if(this.domains.stream().filter(actual->actual==this.publicPause.installation()).count()!=1)
            throw new IOException("public pause must retain exactly one identical installed Root inventory entry");
        for(var installation:additionalDomains.installations())
            if(this.domains.stream().noneMatch(actual->actual==installation))
                throw new IOException("additional business installation is absent from the identical frozen Root inventory");
        coreFrame=new RootCoreFrameRuntime(context);
        declarationDiagnostics=RootArmyDeclarationDiagnostics.install(factory.sources().military().declarationDiagnostics(),context,military);
        factory.publicStepSource(context,RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootPublicPauseArchiveClassifier.class);
        publicPauseClassifier=RootPublicPauseArchiveClassifier.install(context,bindings,this.domains,this.publicPause);
        publicPauseClassifier.requireContext(context);
        if(publicPauseClassifier.publicPause()!=this.publicPause)
            throw new IOException("public pause classifier must retain the identical installed Root runtime");
        domainCatalog=new RootPlanningDomainCatalog(context,bindings,this.domains,save,this.aub,this.remaining.riteCreation(),
                this.additionalDomains.driverRegistry().product(RootDriverRegistryPublicProducts.Kind.TRANSPORT,RootDriverTransportRuntimeFactory.Runtime.class),
                this.additionalDomains.gui(),this.additionalDomains.religion(),this.militaryControls,this.publicPauseClassifier);
        planningEvidence=(same,original,lease)->DriverPlanningEvidence.requireEquivalent(same,original,lease,context.originals());
    }
    public RootRuntimeContext context() { return context; }
    /** The exact pre-Core definitions already used for this installed catalog; this creates no producer. */
    public RootRuntimeCatalogFactory.Sources definitions(){return factory.sources();}
    public org.xar.ck3.control.contracts.ExactRef publicStepSource(RootRuntimeSelectedSources.Module module,
            Class<?> type)throws IOException{return factory.publicStepSource(context,module,type);}
    public org.xar.ck3.control.contracts.ExactRef publicStepSourceAt(String actualTarget,Class<?> type)throws IOException{
        return factory.publicStepSourceAt(context,actualTarget,type);
    }
    synchronized void bindPublicSteps(RootPublicStepExecution.Catalog actual)throws IOException{
        Objects.requireNonNull(actual);
        if(actual.context()!=context)throw new IOException("public step roster belongs to another actual runtime context");
        if(publicSteps!=null&&publicSteps!=actual)throw new IOException("public step roster is already bound to its original catalog");
        publicSteps=actual;
    }
    public synchronized RootPublicStepExecution.Catalog publicSteps()throws IOException{
        if(publicSteps==null)throw new IOException("actual source-owned public step products have not been installed");
        return publicSteps;
    }
    public PhysicalActionRegistry physicalActions() { return factory.physicalActions(); }
    public void bindPhysicalDriver(DriverBootstrap.Adopted actual)throws IOException { context.bindPhysicalDriver(actual); }
    public RootExecutableBindings bindings() { return bindings; }
    public List<RootDomainInstallation> domains() { return domains; }
    public CapabilityFileProbe capabilityFiles() { return files; }
    public ArmyRuntimeInstaller army() { return army; }
    public PrisonersRuntimeInstaller prisoners() { return prisoners; }
    public GovernanceRuntimeInstaller.Installed nativeGovernance() { return nativeGovernance; }
    public GovernanceOrdinaryRuntimeInstaller.Installed governance() { return governance; }
    public GovernanceActivityRuntime activity() { return activity; }
    public RootFrontendRuntime frontend() { return frontend; }
    public KnownInteractionsRuntimeInstaller interactions() { return interactions; }
    public RootIncidentRuntime offline() { return offline; }
    public ConstructionRuntimeInstaller construction() { return construction; }
    public OrdinaryMilitaryInstaller military() { return military; }
    public ArmyAdditionalReadInstaller.Installed additionalArmy() { return additionalArmy; }
    public RootSaveRuntime save() { return save; }
    public RootAubRuntimeFactory.Runtime aub() { return aub; }
    public RootContactRuntime contactScopes() { return contactScopes; }
    public RootRiteCreationRuntimeFactory.Runtime riteCreation() { return remaining.riteCreation(); }
    public RootCoreFrameRuntime coreFrame() { return coreFrame; }
    public RootArmyDeclarationDiagnostics declarationDiagnostics() { return declarationDiagnostics; }
    /** Captured historical source status only; absence means no restored capture, never no active FEAST. */
    public synchronized Optional<RestoredFeastOriginal> restoredFeastOriginal() { return Optional.ofNullable(restoredFeastOriginal); }
    public void bindSave(RootApplicationAssembly.Staged actual)throws IOException {
        var actualSeed=remaining.lifecycle().bindStage(actual);
        files.bindSeeds(actualSeed);
        save.bind(actual);
        actual.installActionHistory(this);
    }
    public RootRuntimeDomainAssembly.Installed remainingDomains() { return remaining; }
    public RootAdditionalDomains.Installed additionalDomains() { return additionalDomains; }
    public RootMilitaryControlStepRuntime.Installed militaryControls(){return militaryControls;}
    public RootArmyStructuralStepRuntime armyStructural(){return armyStructural;}
    public RootPublicPauseRuntime.Installed publicPause(){return publicPause;}
    public RootPublicPauseArchiveClassifier publicPauseClassifier(){return publicPauseClassifier;}
    /** Exact central catalog used by this installed runtime, including its sole public pause classifier. */
    public RootPlanningDomainCatalog planningDomainCatalog(){return domainCatalog;}
    /** Call while the original Root and writer can record actual handle disposal. This never terminates the Game. */
    public synchronized void closeResources()throws IOException {
        if(resourcesClosed)return;
        IOException failure=null;
        try{additionalDomains.close();}catch(IOException|RuntimeException disposal){
            if(disposal instanceof java.io.InterruptedIOException)Thread.currentThread().interrupt();
            failure=disposal instanceof IOException io?io:new IOException("original additional resources failed to close",disposal);
        }
        try{army.close();}catch(IOException|RuntimeException disposal){
            if(disposal instanceof java.io.InterruptedIOException)Thread.currentThread().interrupt();
            if(failure==null)failure=disposal instanceof IOException io?io:new IOException("original Army resources failed to close",disposal);
            else if(disposal!=failure)failure.addSuppressed(disposal);
        }
        if(failure!=null)throw failure;
        resourcesClosed=true;
    }
    public DriverCapabilityRuntime.RetreatDomainSource retreatDomain() {
        return same->{
            context.writer().requireSession(same);
            return army.currentRetreatDomain(same).original().reference().payload();
        };
    }
    /** Returned DATA is accepted only by exact instance together with its private actual staged owner. */
    public record FixtureProducts(DriverCapabilityRuntime capabilities,DriverReadHistoryPublisher readHistory,DriverActionHistoryPublisher actionHistory) {
        public FixtureProducts {Objects.requireNonNull(capabilities);Objects.requireNonNull(readHistory);Objects.requireNonNull(actionHistory);}
    }
    /** Pre-entry history custody only, under the already-held original writer session. No M7/planning/Ready is issued. */
    public synchronized FixtureProducts stageFixture(InitialDriverBootstrap.Staged actual)throws IOException {
        var same=context.writer().borrowedSession();context.writer().requireSession(same);Objects.requireNonNull(actual);
        if(fixtureStage!=null) {
            if(fixtureProducts==null)throw new IOException("partial fixture history installation cannot be replayed");
            requireFixtureProducts(actual,fixtureProducts);return fixtureProducts;
        }
        StrictJson.require(adopted==null&&capabilities==null&&readHistory==null&&frontend.fixture().isPresent(),"only an explicit original pre-entry fixture may stage its history products");
        actual.requireFixtureOwner(same,context.game(),context.source());actual.requireFixtureBootstrap(same,frontend.initialDriver());
        var authority=actual.fixtureAuthority(same);fixtureStage=actual;context.bindFixtureHistory(actual,authority);
        var created=new DriverCapabilityRuntime(authority,context.archive(),context.core().borrowedSessions(),bindings,files,retreatDomain());
        bindNativeCampaignCapabilitySource(created,authority,Optional.of(actual));
        var history=new DriverReadHistoryPublisher(authority,context.archive(),bindings.readCatalog(),factory.sources().readHistoryProducers());
        created.bindReadHistoryPublisher(history);created.bindWindowAttempts(army.products().windowAttempts());
        context.bindFixtureCapabilities(actual,created);
        var materials=remaining.actionHistory(context,this);
        var actions=new DriverActionHistoryPublisher(authority,context.core().journal(),context.archive(),materials.materials(),materials.publisherSources());
        capabilities=created;readHistory=history;fixtureProducts=new FixtureProducts(created,history,actions);
        requireFixtureProducts(actual,fixtureProducts);return fixtureProducts;
    }
    public synchronized void requireFixtureProducts(InitialDriverBootstrap.Staged same,FixtureProducts actual)throws IOException {
        var borrowed=context.writer().borrowedSession();context.writer().requireSession(borrowed);
        StrictJson.require(fixtureStage==Objects.requireNonNull(same)&&fixtureProducts==Objects.requireNonNull(actual),"fixture products cannot cross their exact catalog/staged instance");
        var authority=context.historyAuthority(borrowed);
        actual.capabilities().requireOwner(authority,context.archive(),bindings);
        actual.readHistory().requireOwner(authority,context.archive(),bindings.readCatalog());
        actual.actionHistory().requireOwner(authority,context.core().journal(),context.archive());
        StrictJson.require(capabilities==actual.capabilities()&&readHistory==actual.readHistory(),"fixture history products were replaced");
    }
    public synchronized NativeReadinessCollector.PlanningInputsPort planningInputs(DriverBootstrap.Adopted actual,
            DriverCapabilityRuntime actualCapabilities) {
        Objects.requireNonNull(actual);Objects.requireNonNull(actualCapabilities);
        actualCapabilities.requireOwner(actual.authority(),context.archive(),bindings);
        StrictJson.require(actual.source().equals(context.source()) && actual.session().game().equals(context.game().generation())
                && actual.session().sessionId().equals(context.game().sessionId()),"planning products crossed their actual adopted physical Game");
        if(planning!=null) {
            StrictJson.require(adopted==actual && capabilities==actualCapabilities,"catalog cannot replace its exact Driver/capability runtime");
            return planning;
        }
        if(fixtureProducts!=null)StrictJson.require(capabilities==actualCapabilities&&readHistory==fixtureProducts.readHistory(),"actual fixture adoption must retain its sole staged capability/history runtime");
        adopted=actual;capabilities=actualCapabilities;
        if(fixtureProducts==null) {
            readHistory=new DriverReadHistoryPublisher(actual.authority(),context.archive(),bindings.readCatalog(),factory.sources().readHistoryProducers());
            actualCapabilities.bindReadHistoryPublisher(readHistory);actualCapabilities.bindWindowAttempts(army.products().windowAttempts());
        }
        context.bindCapabilities(actual,actualCapabilities);
        if(restoredNativeCampaignOrigin!=null||frontend.initialPolicy().kind()==InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED) {
            try{context.withSession(same->{bindNativeCampaignCapabilitySource(actualCapabilities,actual.authority(),Optional.empty());return null;});}
            catch(IOException failed){throw new UncheckedIOException(failed);}
        }
        kernelInputs=new M7KernelInputs(context.writer(),context.writer()::requireSession,actual.authority());
        readyPublication=new RootM7ReadyPublication(context.sources(),kernelInputs);
        planning=RootPlanningInputsFactory.create(context,actual,actualCapabilities,
                new RootPlanningInputsFactory.Products(bindings,crossRun,domainCatalog,governance.openingInputs(),offline.offlineInputs()));
        return planning;
    }
    /** Called only after genuine warm publication and before this catalog installs its planning products. */
    public synchronized void bindRestoredNativeCampaignPlanning(ContinuityStorePort.Session same,
            RootFrozenRunProfile.FrozenRunProfile original,
            org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.ReboundOrigin actual)throws IOException {
        context.writer().requireSession(same);Objects.requireNonNull(original);Objects.requireNonNull(actual);
        boolean repeated=restoredNativeCampaignOrigin!=null;
        if(repeated)StrictJson.require(restoredNativeCampaignOrigin==actual&&restoredNativeCampaignFrozen==original,
                "warm constructor provenance cannot replace its original private objects");
        else StrictJson.require(planning==null&&fixtureStage==null&&fixtureProducts==null,
                "warm constructor provenance must precede planning and cannot borrow a fresh staged owner");
        StrictJson.require(context.requireRestoredOrigin(same)==actual,"warm constructor provenance crossed the actual private context origin");
        original.requireExplicitNativeCampaign();
        context.adopted().producer().requireNativeCampaignProjectionOrigin(original);
        context.adopted().producer().requireNativeCampaignRestoredProjection(same,actual);
        actual.requireOriginal(same);
        if(repeated) {
            if(nativeCampaignCapabilitySource!=null)nativeCampaignCapabilitySource.requireOwner(same,context.adopted().authority(),context.archive(),bindings);
        } else {restoredNativeCampaignOrigin=actual;restoredNativeCampaignFrozen=original;}
    }
    private void bindNativeCampaignCapabilitySource(DriverCapabilityRuntime runtime,DriverStateAssembler authority,
            Optional<InitialDriverBootstrap.Staged> actualStage)throws IOException {
        var same=context.writer().borrowedSession();context.writer().requireSession(same);
        if(nativeCampaignCapabilitySource==null)nativeCampaignCapabilitySource=new NativeCampaignCapabilitySource(authority,actualStage);
        else StrictJson.require(nativeCampaignCapabilitySource.authority==authority&&nativeCampaignCapabilitySource.stage.equals(actualStage),"native constructor source cannot replace its original custody");
        runtime.bindPublicPlanningLifecycleSource(nativeCampaignCapabilitySource);
    }
    /** Private actual installed producer; public null projection is never used as a default binding. */
    private final class NativeCampaignCapabilitySource implements DriverCapabilityRuntime.PublicPlanningLifecycleSource {
        private final DriverStateAssembler authority;
        private final Optional<InitialDriverBootstrap.Staged> stage;
        private final RootFrozenRunProfile.FrozenRunProfile frozen;
        private final org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.ReboundOrigin warmOrigin;
        private final List<org.xar.ck3.control.build.SharedSourceFiles.Witness> originalWitnesses;
        private final List<org.xar.ck3.control.contracts.ExactRef> originals;
        private ContinuityStorePort.Session capturedSession;
        private DriverObservationAssembler.FullSnapshot capturedFull;
        private DriverSnapshotFacts.Known capturedDriver;
        private DriverCapabilityRuntime.NativeCampaignConstructorFacts captured;
        private NativeCampaignCapabilitySource(DriverStateAssembler authority,Optional<InitialDriverBootstrap.Staged> stage)throws IOException {
            this.authority=Objects.requireNonNull(authority);this.stage=Objects.requireNonNull(stage);
            warmOrigin=restoredNativeCampaignOrigin;
            frozen=warmOrigin==null?factory.sources().frontend().originalDriverImport().frozenProfile():restoredNativeCampaignFrozen;
            if(warmOrigin==null)frozen.requireCurrent(context.game().launchPlan(),context.clock());
            frozen.requireExplicitNativeCampaign();
            var all=new java.util.LinkedHashSet<org.xar.ck3.control.contracts.ExactRef>();
            for(Class<?> type:List.of(RootInstalledCatalog.class,RootFrozenRunProfile.class,InitialEpisodePolicy.class)) {
                context.game().launchPlan().sources().requireLoadedClass(type);
                all.add(publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,type));
            }
            context.game().launchPlan().sources().requireLoadedClass(NativeCampaignCapabilitySource.class);
            all.addAll(frozen.originalReferences());all.addAll(frozen.initialPolicy().evidenceClosure());all.add(context.source().sourceRef());
            if(warmOrigin!=null) {
                var current=context.game().launchPlan().preparedProfile().environmentManifest();
                all.add(new org.xar.ck3.control.contracts.ExactRef(current.path(),current.bytes(),current.sha256()));
                var origin=warmOrigin.evidence();all.add(origin.originalHistoryBasis());
                all.add(origin.pair().save().reference());all.add(origin.pair().driver().reference());all.add(origin.pair().nativeAckRef());
                all.add(origin.materialWitness().reference());all.add(origin.lifecycleEvidence().reference());all.add(origin.restoredNativeEvidence().reference());
            }
            originals=List.copyOf(all);var witnesses=new java.util.ArrayList<org.xar.ck3.control.build.SharedSourceFiles.Witness>();
            for(var original:originals)witnesses.add(RootFrozenRunProfile.retainOriginalEvidence(original));
            originalWitnesses=List.copyOf(witnesses);requireOwner(context.writer().borrowedSession(),authority,context.archive(),bindings);
        }
        @Override public List<org.xar.ck3.control.contracts.ExactRef> sources(){return originals;}
        @Override public void requireOwner(ContinuityStorePort.Session same,DriverStateAssembler identical,
                ActionPorts.OutcomeArchive archive,ExecutableStepBindings executable)throws IOException {
            context.writer().requireSession(same);context.game().verify();
            StrictJson.require(identical==authority&&archive==context.archive()&&executable==bindings&&context.historyAuthority(same)==authority,
                    "native constructor capability data crossed its actual installed writer/Driver/archive/bindings");
            frozen.requireExplicitNativeCampaign();
            if(warmOrigin!=null) {
                StrictJson.require(restoredNativeCampaignOrigin==warmOrigin&&restoredNativeCampaignFrozen==frozen
                        &&context.requireRestoredOrigin(same)==warmOrigin,"warm constructor lost its identical private origin");
                context.adopted().producer().requireNativeCampaignProjectionOrigin(frozen);
                context.adopted().producer().requireNativeCampaignRestoredProjection(same,warmOrigin);warmOrigin.requireOriginal(same);
            } else {
                frozen.requireCurrent(context.game().launchPlan(),context.clock());
                if(stage.isPresent())stage.orElseThrow().requireNativeCampaignObservationOwner(same,context.game(),context.source());
                else {frozen.initialPolicy().requireSavedProjection(context.game().launchPlan());
                    StrictJson.require(context.adopted().authority()==authority,"Saved private constructor lost its actual adopted Driver");}
            }
            for(Class<?> type:List.of(RootInstalledCatalog.class,RootFrozenRunProfile.class,InitialEpisodePolicy.class,NativeCampaignCapabilitySource.class))
                context.game().launchPlan().sources().requireLoadedClass(type);
            for(var original:originalWitnesses)org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(original);
            context.writer().requireSession(same);
        }
        @Override public DriverCapabilityRuntime.NativeCampaignConstructorFacts capture(ContinuityStorePort.Session same,
                DriverObservationAssembler.FullSnapshot full,DriverSnapshotFacts.Known driver)throws IOException {
            requireOwner(same,authority,context.archive(),bindings);
            StrictJson.require(driver.observation().filter(full.facts()::equals).isPresent()&&full.facts().source().equals(context.source())
                    &&full.facts().driver().equals(driver.driver())
                    &&full.actual().session().game().equals(context.game().generation())
                    &&full.actual().session().sessionId().equals(context.game().sessionId()),"native constructor capture crossed the actual joined frame");
            if(captured!=null&&capturedSession==same&&capturedFull==full&&capturedDriver==driver&&captured.headDigest().equals(same.head().digest())) {
                requireCurrent(same,full,driver,captured);return captured;
            }
            var mode=frozen.importMode() instanceof RootFrozenRunProfile.DisabledFreshFixture
                    ?DriverCapabilityRuntime.NativeCampaignConstructor.FRESH_FIXTURE:DriverCapabilityRuntime.NativeCampaignConstructor.SAVED;
            var environment=frozen.initialPolicy().environment();
            if(warmOrigin!=null) {var actual=context.game().launchPlan().preparedProfile().environmentManifest();
                environment=new org.xar.ck3.control.contracts.ExactRef(actual.path(),actual.bytes(),actual.sha256());}
            captured=new DriverCapabilityRuntime.NativeCampaignConstructorFacts(mode,context.game().generation(),context.game().sessionId(),context.source(),
                    frozen.initialPolicy().source(),environment,originals,same.head().digest());
            capturedSession=same;capturedFull=full;capturedDriver=driver;return captured;
        }
        @Override public void requireCurrent(ContinuityStorePort.Session same,DriverObservationAssembler.FullSnapshot full,
                DriverSnapshotFacts.Known driver,DriverCapabilityRuntime.NativeCampaignConstructorFacts identical)throws IOException {
            StrictJson.require(captured!=null&&identical==captured&&same==capturedSession&&full==capturedFull&&driver==capturedDriver
                    &&captured.headDigest().equals(same.head().digest()),"private constructor DATA cannot be reconstructed or moved to another frame/head/scope");
            requireOwner(same,authority,context.archive(),bindings);
        }
    }
    /** Called once by initial stage or the actual PostAdoption producer. Callback binding remains with that caller. */
    public synchronized void bindReadiness(DriverBootstrap.Adopted actual,NativeReadinessCollector collector)throws IOException {
        StrictJson.require(planning!=null && adopted==actual,"actual planning inputs and sole capability runtime must precede collector binding");
        collector.bindPublicSourceAuthority((same,owner,full,driver,received,process,deadline)->{
            StrictJson.require(full.facts().source().equals(context.source()),"public raw frame crossed the installed Root source");
            return context.sources().verifyPhysicalOrigin(same,full.actual().session(),context.source(),full.originalEvidence(),received,deadline);
        });
        context.bindReadiness(actual,collector);
    }
    public synchronized NativeReadinessCollector.ReadyPublication readyPublication() {
        StrictJson.require(readyPublication!=null,"same actual M7 input capture has not been constructed");return readyPublication;
    }
    public NativeReadinessCollector.PlanningEvidenceVerifier planningEvidence() { return planningEvidence; }
    public synchronized DriverReadHistoryPublisher readHistory() {
        StrictJson.require(readHistory!=null,"actual read-history publisher is unavailable before Driver binding");return readHistory;
    }
    public synchronized M7KernelInputs kernelInputs() {
        StrictJson.require(kernelInputs!=null,"actual M7 kernel inputs are unavailable before Driver binding");return kernelInputs;
    }
    public List<RootDomainIntentPreparation.Binding> pendingBindings() {
        return domains.stream().flatMap(domain->domain.pending().stream()).toList();
    }
    public Set<OperationKey> requiredPending() {
        return domains.stream().flatMap(domain->domain.requiredPending().stream()).collect(java.util.stream.Collectors.toUnmodifiableSet());
    }
    public List<FrontendRouteAdmission> frontendAdmissions() {
        return domains.stream().flatMap(domain->domain.frontendAdmissions().stream()).toList();
    }
    /** Missing real producers remain explicit. No missing stage is filled with a preserve/no-op policy. */
    public Set<PlanningStage> missingStages() { return RootRuntimePipeline.missing(domains); }
    public synchronized OrdinaryPlanningPipeline pipeline() {
        if(fullPipeline==null) {
            var actual=RootRuntimePipeline.assemble(domains);
            remaining.bindFullPipeline(actual);fullPipeline=actual;
        }
        return fullPipeline;
    }
    public OrdinaryPlanCompletion completion() {
        return new RootRuntimePipeline.Completion(domains.stream().flatMap(domain->domain.completions().stream()).toList());
    }
    /** Only the genuine committed entry may create fresh domain bodies. Restore never calls this path. */
    public void afterInitialEntry(ContinuityStorePort.Session same,RootInitialEpisodeProof actual)throws IOException {
        context.writer().requireSession(same);actual.requireCurrent(same);
        StrictJson.require(actual.adopted()==context.adopted(),"fresh domain initialization crossed its actual current Driver");
        nativeGovernance.initializeContinuation(same,actual);
        construction.initializeFresh(same,actual);
        factory.sources().finance().initializeFresh(context,same,actual);
        factory.sources().prisonerConfiguration().definitions().initialize(same,actual);
        factory.sources().governance().afterInitialEntry(same,actual);
        factory.sources().governanceDomains().initialize(same,actual);
        factory.sources().crossRun().initializeFresh(context,same,actual);
        offline.afterInitialEntry(same,actual);
        army.initialize(same,actual);
        remaining.afterInitialEntry(same,actual);
    }
    /** Initialize real fresh business state from the already observed day-zero Driver. */
    public FreshCampaignContext initializeFresh(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,java.time.Instant deadline)throws IOException {
        var actual=FreshCampaignContext.create(context,same,frame,deadline);
        afterInitialEntry(same,actual);return actual;
    }
    public void afterInitialEntry(ContinuityStorePort.Session same,FreshCampaignContext actual)throws IOException {
        context.writer().requireSession(same);actual.requireCurrent(same);
        if(actual.adopted()!=context.adopted())throw new IOException("Fresh domains crossed the real Driver");
        nativeGovernance.initializeContinuation(same,actual);
        if (requiresFreshImport(same, DomainBodies.Slot.CONSTRUCTION)) construction.initializeFresh(same,actual);
        factory.sources().finance().initializeFresh(context,same,actual);
        factory.sources().prisonerConfiguration().definitions().initialize(same,actual);
        factory.sources().governance().afterInitialEntry(same,actual);
        factory.sources().governanceDomains().initialize(same,actual);
        factory.sources().crossRun().initializeFresh(context,same,actual);
        offline.afterInitialEntry(same,actual);
        if (requiresFreshImport(same, DomainBodies.Slot.ACTIVE_RETREAT)) army.initialize(same,actual);
        remaining.afterInitialEntry(same,actual);
    }

    static boolean requiresFreshImport(ContinuityStorePort.Session same,DomainBodies.Slot slot)throws IOException {
        var current=same.readDomain(slot);
        if(current instanceof DomainBodies.Available)return false;
        if(current instanceof DomainBodies.Unavailable missing&&missing.reason()==DomainBodies.Reason.UNIMPORTED)return true;
        throw new IOException("fresh domain initialization cannot replace an unavailable body: "+slot);
    }
    /** Real cold adoption retains canonical domain bodies; it must never execute Fresh initializers. */
    public void afterColdEntry(ContinuityStorePort.Session same,RootPrivateBootstrap.Original actual)throws IOException {
        context.writer().requireSession(same);Objects.requireNonNull(actual).requireCurrent(same,context);
        StrictJson.require(actual.context()==context&&actual.adopted()==context.adopted(),"cold domain continuation crossed its original canonical adopter");
        requireBaseDomainBodies(same);
        StrictJson.require(factory.sources().crossRun().domain().read(same) instanceof CrossRunPlanningDomain.KnownState,
                "cold continuation requires its actually retained cross-run strategy body");
        factory.sources().crossRun().attachContext(context);actual.requireOriginal(same);
    }
    /** Only Core's actual NEXT or FIRST-restored private proof may run this one initialization transform. */
    public List<DomainBodies.BodyRef> initializeNext(ContinuityStorePort.Session same,
            RootApplicationAssembly.EpisodeDomainInitializationProof actual)throws IOException {
        context.writer().requireSession(same);Objects.requireNonNull(actual).requireCurrent(same,context);
        var required=EnumSet.of(DomainBodies.Slot.FAMILY,DomainBodies.Slot.CHILD_MATRILINEAL,
                DomainBodies.Slot.DEFAULT_MARRIAGE,DomainBodies.Slot.SWAY,DomainBodies.Slot.CONSTRUCTION,
                DomainBodies.Slot.MERCENARY,DomainBodies.Slot.FACTION,DomainBodies.Slot.OPENING_GATE,
                DomainBodies.Slot.FEAST,DomainBodies.Slot.OPTIONAL_CADENCE,DomainBodies.Slot.RITE_CREATION);
        var prisonerRegistrations=factory.sources().prisonerConfiguration().definitions().registrations();
        StrictJson.require(prisonerRegistrations.stream().map(DomainBodies.Registration::slot)
                .collect(java.util.stream.Collectors.toUnmodifiableSet())
                .equals(Set.of(DomainBodies.Slot.PRISONER_RELEASE,DomainBodies.Slot.PRISONER_RANSOM)),
                "NEXT requires the actual separate registered prisoner RELEASE and RANSOM slots");
        for(var registration:prisonerRegistrations)
            StrictJson.require(required.add(registration.slot()),"NEXT prisoner slot duplicates another actual domain producer");
        if(actual.kind()==RootApplicationAssembly.EpisodeDomainInitializationProof.Kind.RESTORED_FIRST) {
            FirstRestoredInitialization retained;
            synchronized(this){retained=firstRestoredInitialization;}
            if(retained!=null) {
                if(retained.proof()!=actual)throw new IOException("another private FIRST-restored proof already owns this catalog initialization");
                requireNextBodyReferences(same,retained.bodies(),required);actual.requireCurrent(same,context);return retained.bodies();
            }
        }
        var installed=new ArrayList<DomainBodies.BodyRef>();
        installed.addAll(remaining.initializeNextFamilyAndSway(same,actual));actual.requireCurrent(same,context);
        installed.add(construction.initializeNext(same,actual).body());actual.requireCurrent(same,context);
        installed.addAll(factory.sources().finance().initializeNext(context,same,actual));actual.requireCurrent(same,context);
        installed.addAll(prisoners.initializeNext(same,actual));actual.requireCurrent(same,context);
        installed.addAll(factory.sources().governance().initializeNext(context,same,actual));actual.requireCurrent(same,context);
        requireNextBodyReferences(same,installed,required);
        actual.requireCurrent(same,context);
        List<DomainBodies.BodyRef> retained=List.copyOf(installed);
        if(actual.kind()==RootApplicationAssembly.EpisodeDomainInitializationProof.Kind.RESTORED_FIRST) {
            synchronized(this) {
                if(firstRestoredInitialization!=null&&firstRestoredInitialization.proof()!=actual)
                    throw new IOException("another private FIRST-restored proof already initialized this actual catalog");
                firstRestoredInitialization=new FirstRestoredInitialization(actual,retained);
            }
        }
        return retained;
    }
    private static void requireNextBodyReferences(ContinuityStorePort.Session same,List<DomainBodies.BodyRef> originals,
            Set<DomainBodies.Slot> required)throws IOException {
        var slots=EnumSet.noneOf(DomainBodies.Slot.class);
        for(var original:originals) {
            if(!slots.add(original.slot()))throw new IOException("NEXT domain initialization returned duplicate actual slot: "+original.slot());
            var current=same.readDomain(original.slot());
            if(!(current instanceof DomainBodies.Available known)||!known.reference().equals(original))
                throw new IOException("NEXT initializer did not retain its actual canonical body: "+original.slot());
            var pin=same.capturePin(original.payload(),WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);
        }
        if(!slots.equals(required))throw new IOException("NEXT initialization must return every actual family, Sway, Rite, construction, finance, prisoner and governance slot");
    }
    public void bindSession(RootApplicationSession actual)throws IOException { context.bindSession(actual); }
    /** After every actual domain import and Staged.finish's real planning-port binding, before ordinary Ready. */
    public void initializePersistentPlanning(ContinuityStorePort.Session same,DriverObservationAssembler.Complete actual)throws IOException {
        context.writer().requireSession(same);Objects.requireNonNull(actual);
        DriverCapabilityRuntime current;
        synchronized(this) {
            StrictJson.require(capabilities!=null&&adopted==context.adopted(),"persistent planning requires this actual installed Driver/capability runtime");
            current=capabilities;
        }
        current.requireOwner(context.adopted().authority(),context.archive(),bindings);
        requireBaseDomainBodies(same);
        StrictJson.require(factory.sources().crossRun().domain().read(same) instanceof CrossRunPlanningDomain.KnownState,
                "persistent planning requires the actual retained cross-run strategy after domain imports");
        initializeCapabilityState(same,actual);
        current.initializePlanning(same,actual);
    }

    private void initializeCapabilityState(ContinuityStorePort.Session same, DriverObservationAssembler.Complete actual) throws IOException {
        var authority = context.adopted().authority();
        ActionPorts.OutcomeArchive archive = context.archive().withSession(same);
        authority.withFrozenFacts(same, frozen -> {
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known, "persistent planning requires the actual complete Driver");
            var known = (DriverSnapshotFacts.Known) frozen.state();

            if (known.auxiliary().members().containsKey(DriverCapabilityStateProducer.STATE_SOURCE)) {
                var ref = DriverObservationEvidenceReader.reference(known.auxiliary().get(DriverCapabilityStateProducer.STATE_SOURCE));
                var replay = DriverCapabilityStateProducer.replay(actual, known, ref, archive);
                for (var entry : replay.members().entrySet()) {
                    StrictJson.require(entry.getValue().equals(known.auxiliary().get(entry.getKey())), "replay mismatch");
                }
                return null;
            }

            var sources = factory.sources().frontend();
            var configured = sources.capabilitySession();
            var presentation = configured;

            if (configured.bindingState() == CapabilitySessionPresentation.BindingState.UNBOUND && configured.restoreKind().isEmpty()) {
                presentation = new CapabilitySessionPresentation(
                    configured.driverStateRestored(),
                    configured.driverStateError(),
                    java.util.Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,
                    configured.coldCandidateRejection(),
                    configured.episodeTransitionError(),
                    configured.queueDirectory(),
                    configured.driverStatePath()
                );
            }

            var archivedPolicy = archive.preserveMaterial(sources.initialPolicy().lifecycle());
            var initial = DriverCapabilityStateProducer.initializeNewEpisode(
                actual,
                known,
                sources.capabilityConfiguration(),
                presentation,
                archivedPolicy,
                archive
            );
            authority.publishCapabilityInputs(same, initial.expectedStamp(), initial.expectedAuxiliarySha256(), initial);
            return null;
        });
    }
    /** Actual private attachment, then domain originals; no capability observation or cycle rebind runs in this scope. */
    public void adoptRestored(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.checkpoint.RestoreCheckpointService actualIssuer,
            org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.RestoreBinding actual,
            org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore sameSources,Instant deadline)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(deadline);Objects.requireNonNull(actualIssuer);Objects.requireNonNull(actual);
        StrictJson.require(context.savedSources()==Objects.requireNonNull(sameSources),"restored domain originals require the actual sole saved source store");
        actualIssuer.requireRetainedOriginal(same,actual);context.requireRestorationOriginal(same,actual);
        RootRestorationOriginalProof proof=RootRestorationOriginalProof.requireRetained(context,same,actual);
        var material=actual.savedMaterial();material.requireRetained(same);
        boolean first=switch(material.kind()){case ORDINARY->false;case FIRST_BASELINE->true;};
        if(first)requireFirstRestoredInitialization(same,material);
        // Both material kinds admit the private restored source before any remaining domain transform.
        remaining.adoptRestored(same,proof,actual,deadline);
        // FIRST already consumed the common transform. Ordinary restoration retains its existing import path.
        requireBaseDomainBodies(same);
        if(!first)construction.restore(same,proof);
        factory.sources().crossRun().attachContext(context);
        StrictJson.require(factory.sources().crossRun().domain().read(same) instanceof CrossRunPlanningDomain.KnownState,
                "restoration requires the actual complete retained cross-run strategy, not missing state");
        factory.sources().crossRun().requireRestoredFirst(context,same);
        var beforeFeast=same.head().digest();
        var actualOriginal=context.restorationOriginal(same);
        var feastOriginal=factory.sources().governance().captureRestoredFeastOriginal(same,actualOriginal);
        StrictJson.require(same.head().digest().equals(beforeFeast),"restored FEAST original capture must not mutate the original writer");
        synchronized(this) {restoredFeastOriginal=feastOriginal;}
        requireBaseDomainBodies(same);
    }
    private void requireFirstRestoredInitialization(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial actualMaterial)throws IOException {
        FirstRestoredInitialization initialized;
        synchronized(this){initialized=firstRestoredInitialization;}
        if(initialized==null||initialized.proof().kind()!=RootApplicationAssembly.EpisodeDomainInitializationProof.Kind.RESTORED_FIRST
                ||initialized.proof().baselineMaterial()!=actualMaterial)
            throw new IOException("FIRST restoration requires this catalog's completed initialization from the identical private material proof");
        initialized.proof().requireCurrent(same,context);
        var required=EnumSet.of(DomainBodies.Slot.FAMILY,DomainBodies.Slot.CHILD_MATRILINEAL,DomainBodies.Slot.DEFAULT_MARRIAGE,
                DomainBodies.Slot.SWAY,DomainBodies.Slot.CONSTRUCTION,DomainBodies.Slot.MERCENARY,DomainBodies.Slot.FACTION,
                DomainBodies.Slot.PRISONER_RELEASE,DomainBodies.Slot.PRISONER_RANSOM,DomainBodies.Slot.OPENING_GATE,
                DomainBodies.Slot.FEAST,DomainBodies.Slot.OPTIONAL_CADENCE,DomainBodies.Slot.RITE_CREATION);
        requireNextBodyReferences(same,initialized.bodies(),required);
        initialized.proof().requireCurrent(same,context);
    }
    private void requireBaseDomainBodies(ContinuityStorePort.Session same)throws IOException {
        var registrations=new java.util.LinkedHashSet<DomainBodies.Registration>();
        registrations.addAll(factory.sources().nativeGovernance().domainRegistrations());
        registrations.addAll(factory.sources().finance().registrations());registrations.addAll(factory.sources().army().domainRegistrations());
        registrations.addAll(factory.sources().prisonerConfiguration().definitions().registrations());
        registrations.addAll(factory.sources().governance().domainRegistrations());registrations.addAll(factory.sources().governanceDomains().domainRegistrations());
        registrations.addAll(factory.sources().crossRun().registrations());
        var rite=remaining.riteCreation().registration();
        StrictJson.require(rite.slot()==DomainBodies.Slot.RITE_CREATION
                &&factory.sources().remainingDomains().domainRegistrations().stream().anyMatch(original->original==rite),
                "Rite requires the identical pre-Core registered canonical domain producer");
        registrations.add(rite);
        for(var registration:registrations) {
            var retained=same.readDomain(registration.slot());
            if(!(retained instanceof DomainBodies.Available known))throw new IOException("restoration lacks an actual retained domain body: "+registration.slot());
            var pin=same.capturePin(known.reference().payload(),WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);
        }
    }
}


