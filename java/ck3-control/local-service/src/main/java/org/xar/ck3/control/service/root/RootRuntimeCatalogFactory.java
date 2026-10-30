package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.time.Duration;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.CapabilityFileProbe;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.activity.*;
import org.xar.ck3.control.platform.ManagedGameSession;

/**
 * Core-lifetime definitions, then concrete per-physical-Game native installation.
 * Construction installs actual callable products. It never grants source/readiness/restore admission.
 */
public final class RootRuntimeCatalogFactory {
    public record MilitarySources(OrdinaryMilitaryInstaller.Sources ordinary,ArmyAdditionalReadInstaller.Sources additional,
            CombatSimulationInputsCodec simulation,CombatPhaseInputsCodec phases,
            RootArmyDeclarationDiagnostics.Sources declarationDiagnostics,Duration publicReadTimeout,
            RootMilitaryControlStepRuntime.Prepared controls,RootArmyStructuralStepRuntime.Prepared structural,
            RootPublicPauseRuntime.Prepared publicPause) {
        public MilitarySources {
            Objects.requireNonNull(ordinary);Objects.requireNonNull(additional);Objects.requireNonNull(simulation);Objects.requireNonNull(phases);
            Objects.requireNonNull(declarationDiagnostics);
            Objects.requireNonNull(controls);
            Objects.requireNonNull(structural);
            Objects.requireNonNull(publicPause);
            Objects.requireNonNull(publicReadTimeout);StrictJson.require(!publicReadTimeout.isZero()&&!publicReadTimeout.isNegative()
                    &&publicReadTimeout.compareTo(Duration.ofMinutes(1))<=0,"bounded actual Army public read timeout required");
        }
    }
    public record HistoricalPackage(Request request,FileRef hostConfiguration) {
        public HistoricalPackage {Objects.requireNonNull(request);Objects.requireNonNull(hostConfiguration);}
    }
    public record Sources(
            GovernanceRuntimeInstaller.Prepared nativeGovernance,
            FinanceRuntimeInstaller.Prepared finance,
            ArmyRuntimeInstaller.Prepared army,
            MilitarySources military,
            RootSaveRuntime.Sources save,
            RootAubRuntimeFactory.Prepared aub,
            RootContactRuntime.Prepared contactScopes,
            RootRuntimeDomainAssembly.Prepared remainingDomains,
            RootAdditionalDomains.Prepared additionalDomains,
            ConstructionRuntimeInstaller.Sources construction,
            PrisonersRuntimeInstaller.Sources prisoners,
            PrisonersRuntimeInstaller.Configuration prisonerConfiguration,
            GovernanceOrdinaryRuntimeInstaller.Prepared governance,
            RootCrownRetryRuntime.Prepared retryRuntime,
            GovernanceOrdinaryRuntimeInstaller.StateDomains governanceState,
            RootGovernanceDomains governanceDomains,
            ActivityNativeContracts.Installation activityDefinitions,
            ActivityActionRoutes activityActions,
            ExactRef activityCodec,
            RootFrontendRuntime.Sources frontend,
            KnownInteractionsRuntimeInstaller.Sources interactions,
            List<ExactRef> readHistoryProducers,
            RootCrossRunPlanning.Prepared crossRun,
            RootIncidentRuntime.Prepared incidents,
            CheckpointFiles checkpointFiles,
            java.util.Optional<HistoricalPackage> historicalPackage,
            List<DomainBodies.Registration> additionalRegistrations,
            int retainedEffects) {
        public Sources {
            Objects.requireNonNull(nativeGovernance);Objects.requireNonNull(finance);Objects.requireNonNull(army);Objects.requireNonNull(military);
            Objects.requireNonNull(construction);Objects.requireNonNull(prisoners);Objects.requireNonNull(prisonerConfiguration);
            Objects.requireNonNull(save);Objects.requireNonNull(aub);Objects.requireNonNull(contactScopes);Objects.requireNonNull(remainingDomains);
            Objects.requireNonNull(additionalDomains);
            Objects.requireNonNull(governance);Objects.requireNonNull(governanceState);Objects.requireNonNull(activityDefinitions);
            Objects.requireNonNull(governanceDomains);
            Objects.requireNonNull(retryRuntime);
            StrictJson.require(governanceState.retryPublication()==governanceDomains.retryPublication(),"one actual Crown retry and ordinary domain authority required");
            StrictJson.require(governanceState.retryPublication()==retryRuntime.pub()&&governanceState.retryDue()==retryRuntime.due(),
                    "ordinary governance and shared advance must retain the actual sole Crown runtime products");
            Objects.requireNonNull(activityActions);Objects.requireNonNull(activityCodec);Objects.requireNonNull(crossRun);
            Objects.requireNonNull(frontend);Objects.requireNonNull(interactions);readHistoryProducers=List.copyOf(readHistoryProducers);
            Objects.requireNonNull(incidents);
            Objects.requireNonNull(checkpointFiles);Objects.requireNonNull(historicalPackage);
            additionalRegistrations=List.copyOf(additionalRegistrations);
            StrictJson.require(activityCodec.bytes()>0 && !readHistoryProducers.isEmpty() && retainedEffects>=1 && retainedEffects<=4096,
                    "actual bounded source, archive and Core definitions required");
        }
        /** Legacy metadata remains explicit; ordinary products do not manufacture it. */
        public Request packageRequest() {
            return historicalPackage.orElseThrow(()->new IllegalStateException("Ordinary products have no historical package request")).request();
        }
        public FileRef hostConfiguration() {
            return historicalPackage.orElseThrow(()->new IllegalStateException("Ordinary products have no historical host configuration")).hostConfiguration();
        }
        /** Historical callers keep their original explicit package metadata. Ordinary products use Optional.empty(). */
        public Sources(GovernanceRuntimeInstaller.Prepared nativeGovernance,
                FinanceRuntimeInstaller.Prepared finance,
                ArmyRuntimeInstaller.Prepared army,
                MilitarySources military,
                RootSaveRuntime.Sources save,
                RootAubRuntimeFactory.Prepared aub,
                RootContactRuntime.Prepared contactScopes,
                RootRuntimeDomainAssembly.Prepared remainingDomains,
                RootAdditionalDomains.Prepared additionalDomains,
                ConstructionRuntimeInstaller.Sources construction,
                PrisonersRuntimeInstaller.Sources prisoners,
                PrisonersRuntimeInstaller.Configuration prisonerConfiguration,
                GovernanceOrdinaryRuntimeInstaller.Prepared governance,
                RootCrownRetryRuntime.Prepared retryRuntime,
                GovernanceOrdinaryRuntimeInstaller.StateDomains governanceState,
                RootGovernanceDomains governanceDomains,
                ActivityNativeContracts.Installation activityDefinitions,
                ActivityActionRoutes activityActions,
                ExactRef activityCodec,
                RootFrontendRuntime.Sources frontend,
                KnownInteractionsRuntimeInstaller.Sources interactions,
                List<ExactRef> readHistoryProducers,
                RootCrossRunPlanning.Prepared crossRun,
                RootIncidentRuntime.Prepared incidents,
                CheckpointFiles checkpointFiles,
                Request packageRequest,
                FileRef hostConfiguration,
                List<DomainBodies.Registration> additionalRegistrations,
                int retainedEffects) {
            this(nativeGovernance,finance,army,military,save,aub,contactScopes,remainingDomains,additionalDomains,construction,prisoners,prisonerConfiguration,governance,retryRuntime,governanceState,governanceDomains,activityDefinitions,activityActions,activityCodec,frontend,interactions,readHistoryProducers,crossRun,incidents,checkpointFiles,java.util.Optional.of(new HistoricalPackage(packageRequest,hostConfiguration)),additionalRegistrations,retainedEffects);
        }
    }
    private static final class Attempt {
        final RootRuntimeContext context;
        RootInstalledCatalog installed;
        IOException failure;
        boolean entered;
        Attempt(RootRuntimeContext context) { this.context=context; }
    }
    private final Sources sources;
    private final List<DomainBodies.Registration> registrations;
    private final PhysicalActionRegistry physicalActions;
    private RootRuntimeDefinitions.Inputs publicStepInputs;
    private RootRuntimeSelectedSources publicStepSources;
    private final IdentityHashMap<ManagedGameSession,Attempt> attempts=new IdentityHashMap<>();
    private RootApplicationAssembly.Core core;
    private org.xar.ck3.control.application.battleadvance.TacticalClockFailureRuntime.Installed tactical;
    /** The public facade supplies its one existing actual selector before any physical installation. */
    public synchronized void bindPublicStepSources(RootRuntimeDefinitions.Inputs identicalInputs,
            RootRuntimeSelectedSources identicalSelected)throws IOException {
        Objects.requireNonNull(identicalInputs);Objects.requireNonNull(identicalSelected);
        identicalSelected.requireInputs(identicalInputs);
        if(publicStepSources!=null) {
            if(publicStepSources!=identicalSelected||publicStepInputs!=identicalInputs)
                throw new IOException("public step source custody cannot be replaced by another selector or Inputs");
            return;
        }
        if(!attempts.isEmpty())throw new IOException("public step source custody must precede actual runtime installation");
        publicStepInputs=identicalInputs;publicStepSources=identicalSelected;
    }
    synchronized ExactRef publicStepSource(RootRuntimeContext actual,RootRuntimeSelectedSources.Module module,
            Class<?> type)throws IOException {
        if(sources.historicalPackage().isEmpty())return ordinaryCallerSource(actual);
        requirePublicStepSourceOwner(actual);ExactRef original=publicStepSources.javaSource(module,type);
        publicStepSources.requireLoadedClasses(actual.game().launchPlan());
        requirePublicStepSourceOwner(actual);return original;
    }
    synchronized ExactRef publicStepSourceAt(RootRuntimeContext actual,String target,Class<?> type)throws IOException {
        if(sources.historicalPackage().isEmpty())return ordinaryCallerSource(actual);
        requirePublicStepSourceOwner(actual);ExactRef original=publicStepSources.javaSourceAt(target,type);
        publicStepSources.requireLoadedClasses(actual.game().launchPlan());
        requirePublicStepSourceOwner(actual);return original;
    }
    /** Ordinary products record their actual application caller; this is no source or class qualification. */
    private ExactRef ordinaryCallerSource(RootRuntimeContext actual)throws IOException {
        if(core==null||Objects.requireNonNull(actual).core()!=core)
            throw new IOException("Ordinary product belongs to another actual Core");
        return actual.source().sourceRef();
    }
    private void requirePublicStepSourceOwner(RootRuntimeContext actual)throws IOException {
        Objects.requireNonNull(actual);
        if(core==null||actual.core()!=core||publicStepSources==null||publicStepInputs==null)
            throw new IOException("actual same-Core public step source custody has not been bound");
        publicStepSources.requireInputs(publicStepInputs);actual.game().verify();
    }
    public RootRuntimeCatalogFactory(Sources actualSources) {
        sources=Objects.requireNonNull(actualSources);
        List<DomainBodies.Registration> all=new ArrayList<>();
        all.addAll(sources.nativeGovernance().domainRegistrations());
        all.addAll(sources.finance().registrations());all.addAll(sources.army().domainRegistrations());
        all.add(sources.construction().registration());all.addAll(sources.prisonerConfiguration().definitions().registrations());
        all.addAll(sources.governance().domainRegistrations());
        all.addAll(sources.governanceDomains().domainRegistrations());
        all.addAll(sources.crossRun().registrations());all.addAll(sources.additionalRegistrations());
        all.addAll(sources.remainingDomains().domainRegistrations());
        all.addAll(sources.additionalDomains().domainRegistrations());
        all.addAll(sources.contactScopes().domainRegistrations());
        all.addAll(sources.military().controls().domainRegistrations());
        all.addAll(sources.military().structural().domainRegistrations());
        all.addAll(sources.military().publicPause().domainRegistrations());
        Map<DomainBodies.Slot,DomainBodies.Registration> unique=new LinkedHashMap<>();
        for(var registration:all) {
            var old=unique.putIfAbsent(registration.slot(),registration);
            StrictJson.require(old==null || old==registration,"distinct Core producers claim one canonical domain slot");
        }
        registrations=List.copyOf(unique.values());
        List<PhysicalActionRegistry.Binding> physical=new ArrayList<>();
        physical.addAll(sources.additionalDomains().frontendCoa().physicalBindings());
        physical.addAll(sources.additionalDomains().gui().physicalBindings());
        physicalActions=new PhysicalActionRegistry(List.copyOf(physical));
    }
    /** Pass these identical registrations to Core.open, before a writer is constructed. */
    public List<DomainBodies.Registration> domainRegistrations() { return registrations; }
    public Sources sources() { return sources; }
    public PhysicalActionRegistry physicalActions() { return physicalActions; }
    /** Transport construction must consume these real source-qualified permissions before Native is first used. */
    public List<NativePrivateActionPermission> privatePermissions(NativePrivateActionPermission.QualificationVerifier actual) {
        Objects.requireNonNull(actual);List<NativePrivateActionPermission> result=new ArrayList<>();
        result.addAll(sources.nativeGovernance().privatePermissions(actual));
        result.addAll(PrisonersRuntimeInstaller.privatePermissions(sources.prisoners(),actual));
        result.addAll(sources.activityActions().privatePermissions().stream()
                .map(permission->permission.withAdditionalQualification(actual)).toList());
        result.addAll(sources.remainingDomains().privatePermissions(actual));
        result.addAll(sources.additionalDomains().privatePermissions(actual));
        result.addAll(sources.military().controls().privatePermissions().stream()
                .map(permission->permission.withAdditionalQualification(actual)).toList());
        result.addAll(sources.military().structural().privatePermissions().stream()
                .map(permission->permission.withAdditionalQualification(actual)).toList());
        result.addAll(sources.military().publicPause().privatePermissions().stream()
                .map(permission->permission.withAdditionalQualification(actual)).toList());
        return List.copyOf(result);
    }
    public synchronized void requireBoundCore(RootApplicationAssembly.Core actual)throws IOException {
        if(core==null||core!=Objects.requireNonNull(actual)||actual.archive().writer()!=actual.writer())
            throw new IOException("managed lifecycle requires the identical once-bound runtime Core/writer/archive");
    }
    public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
        StrictJson.require(core==null,"runtime definitions bind the sole original Core exactly once");
        Objects.requireNonNull(actual);StrictJson.require(actual.archive().writer()==actual.writer(),"Core writer/archive identity differs");
        sources.finance().bindCore(actual);sources.governance().bindCore(actual);
        sources.prisonerConfiguration().definitions().bindCore(actual);core=actual;
        sources.governanceDomains().bindCore(actual);
        sources.crossRun().bindCore(actual);
        sources.retryRuntime().bindCore(actual);
        sources.remainingDomains().bindCore(actual);
        sources.additionalDomains().bindCore(actual);
        sources.military().controls().bindCore(actual);
        sources.military().structural().bindCore(actual);
        sources.military().publicPause().bindCore(actual);
        actual.bindPhysicalActions(physicalActions);
        sources.governanceDomains().bindActionCadencePublisher(sources.governance().actionCadencePublisher());
        tactical=org.xar.ck3.control.application.battleadvance.TacticalClockFailureRuntime.install(actual.frameLoader(),actual.archive());
    }
    public synchronized org.xar.ck3.control.application.battleadvance.TacticalClockFailureRuntime.Installed tactical() {
        StrictJson.require(tactical!=null,"actual Core tactical evidence runtime is unbound");return tactical;
    }
    public synchronized RootInstalledCatalog install(RootApplicationAssembly.Core actual,ManagedGameSession game,
            G2Source source,RootPlanningReads reads,Clock clock,Instant deadline)throws IOException {
        StrictJson.require(core==actual && core!=null,"runtime catalog requires its exact once-bound Core");
        Objects.requireNonNull(game);Objects.requireNonNull(source);Objects.requireNonNull(reads);Objects.requireNonNull(clock);
        Attempt attempt=attempts.get(game);
        if(attempt==null) {
            StrictJson.require(attempts.size()<64,"bounded actual Game installation attempts; reconcile before further construction");
            attempt=new Attempt(new RootRuntimeContext(actual,game,source,reads,clock));attempts.put(game,attempt);
        }
        RootRuntimeContext context=attempt.context;
        StrictJson.require(context.core()==actual && context.game()==game && context.source().equals(source)
                && context.reads()==reads && context.clock()==clock,"same physical Game cannot acquire another runtime context");
        context.requireActiveGame();
        if(attempt.installed!=null)return attempt.installed;
        if(attempt.entered)throw new IOException("actual runtime installation already entered; failed partial bindings are not replayed",attempt.failure);
        attempt.entered=true;
        RootAdditionalDomains.Installed installedAdditional=null;
        ArmyRuntimeInstaller installedArmy=null;
        try {
            RootNativeSourceAuthority sourceAuthority;
            if(sources.historicalPackage().isPresent()) {
                var historical=sources.historicalPackage().orElseThrow();
                sourceAuthority=new RootNativeSourceAuthority(actual.writer(),actual.archive(),game,
                        new RootPackageNativeVerifier(),historical.request(),historical.hostConfiguration(),clock);
            } else sourceAuthority=new RootNativeSourceAuthority(actual.writer(),actual.archive(),game,clock);
            context.bindSources(sourceAuthority);
            var activity=new GovernanceActivityRuntime(context,sources.activityDefinitions());
            var nativeGovernance=sources.nativeGovernance().install(context);
            var retry=sources.retryRuntime().install(context,nativeGovernance);
            var nativeGovernanceDomains=sources.governanceDomains().install(context,nativeGovernance);
            var prisoners=new PrisonersRuntimeInstaller(context,sources.prisoners(),sources.prisonerConfiguration());
            var finance=sources.finance().install(context,activity,List.of(prisoners.pendingContributor()));
            var governance=sources.governance().install(context,nativeGovernance,activity,sources.activityActions(),sources.governanceState(),retry);
            var army=sources.army().install(context);
            installedArmy=army;
            var construction=new ConstructionRuntimeInstaller(context,sources.construction());
            var constructionInstallation=construction.install();
            var combat=new CombatObservationCache(sources.military().simulation(),sources.military().phases());
            var armyProducts=army.products();
            var military=new OrdinaryMilitaryInstaller(context,sources.military().ordinary(),
                    new OrdinaryMilitaryInstaller.Army(armyProducts.frames(),armyProducts.retreatDomain(),armyProducts.retreatReads(),armyProducts.battleContracts()),
                    combat,context::readHistoryPublisher);
            var additionalArmy=new ArmyAdditionalReadInstaller(context,armyProducts,context.finance().definitions(),military.commander(),
                    sources.military().additional(),sources.military().publicReadTimeout()).install();
            var interactions=new KnownInteractionsRuntimeInstaller(context,sources.interactions(),prisoners);
            prisoners.bindKnown(interactions);
            context.bindInteractions(interactions);
            var frontend=new RootFrontendRuntime(context,sources.frontend());
            context.bindFrontend(frontend);
            var offline=sources.incidents().install(context);
            var save=new RootSaveRuntime(context,sources.save());
            var aub=sources.aub().install(context);
            var contactScopes=sources.contactScopes().install(context);
            var remaining=sources.remainingDomains().install(context,new RootRuntimeDomainAssembly.Shared(nativeGovernance,governance,activity,
                    prisoners,army,construction,military,additionalArmy,interactions,offline,frontend));
            context.bindRemainingDomains(remaining);
            installedAdditional=sources.additionalDomains().install(context);
            var additionalDomains=installedAdditional;
            var militaryControls=sources.military().controls().install(context,additionalDomains.gui(),remaining.life());
            var armyStructural=sources.military().structural().install(context);
            var publicPause=sources.military().publicPause().install(context,remaining.life().infrastructure());
            List<RootDomainInstallation> domainList=new ArrayList<>(List.of(nativeGovernance.installation(),nativeGovernanceDomains,finance,prisoners.install(),governance.installation(),
                    army.products().installation(),constructionInstallation,military.readInstallation(),additionalArmy.installation(),
                    activityInstallation(activity,sources.activityCodec()),frontend.installation(),remaining.knownInteractions(),save.installation(),aub.installation(),contactScopes.readInstallation()));
            domainList.addAll(remaining.installations());domainList.addAll(additionalDomains.installations());
            domainList.add(militaryControls.installation());domainList.add(armyStructural.installation());
            domainList.add(publicPause.installation());var domains=List.copyOf(domainList);
            var readsInstalled=new ArrayList<RootReadContractCatalog.InstalledRead>(
                    domains.stream().flatMap(domain->domain.reads().stream()).toList());
            ExactRef crownDecoder=publicStepSource(context,RootRuntimeSelectedSources.Module.LOCAL_SERVICE,CrownAuthorityNativeRead.class);
            ExactRef crownDefinition=sources.historicalPackage().isPresent()
                    ?crownDefinition(game.launchPlan().sources().nativeProof().expected().completeSources()):crownDecoder;
            readsInstalled.add(new RootReadContractCatalog.InstalledRead(
                    CrownAuthorityNativeRead.contract(crownDefinition,true,context.archive(),actual.frameLoader()),crownDecoder));
            var families=domains.stream().flatMap(domain->domain.readFamilies().stream()).toList();
            var readCatalog=new RootReadContractCatalog(readsInstalled,families);
            var bindings=RootExecutableBindings.freeze(domains.stream().flatMap(domain->domain.actions().stream()).toList(),readCatalog,
                    domains.stream().flatMap(domain->domain.composites().stream()).toList(),
                    domains.stream().flatMap(domain->domain.archived().stream()).toList(),
                    domains.stream().flatMap(domain->domain.actionFamilies().stream()).toList(),
                    domains.stream().flatMap(domain->domain.compositeFamilies().stream()).toList(),sources.retainedEffects());
            bindings.requireCompleteArchiveCoverage();context.bindInventory(bindings);
            actual.operatorAuthority().bindInventory(context,bindings);
            publicPause.postInventoryBind(bindings);
            frontend.bindInventory(domains.stream().flatMap(domain->domain.frontendAdmissions().stream()).toList());
            // The immutable seed store is constructed only from this Game's actual Staged DriverCheckpointStore.
            // The pre-stage file probe is explicitly unbound; it cannot report a seed as available.
            var files=new CapabilityFileProbe(sources.checkpointFiles(),java.util.Optional.empty());
            var completed=new RootInstalledCatalog(this,context,bindings,domains,files,army,prisoners,nativeGovernance,
                    governance,activity,frontend,interactions,offline,sources.crossRun().domain(),construction,military,additionalArmy,save,aub.runtime(),contactScopes,remaining,additionalDomains,militaryControls,armyStructural,publicPause);
            if(frontend.fixture().isPresent())frontend.bindFixtureCatalog(completed);
            publicStepSource(context,RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootPhysicalStatusReadAuthority.class);
            var physicalStatus=new RootPhysicalStatusReadAuthority(context,sources.frontend().freshness());
            physicalStatus.requireContext(context);
            bindings.bindPhysicalStatusAuthority(game.generation(),game.sessionId(),context.source(),physicalStatus);
            context.bindPhysicalStatusReads(physicalStatus);
            context.withSession(same->{context.archive().bindPhysicalStatusOriginals(same,game.generation(),bindings,context.originals());return null;});
            RootDirectFixedWindowQueryAuthority.install(completed);
            var publicProducts=new ArrayList<RootPublicStepExecution.Product>();
            publicProducts.addAll(RootChinaCasesPublicStepProducts.install(completed));
            publicProducts.addAll(RootChinaCareerPublicStepProducts.install(completed));
            publicProducts.addAll(RootWarPublicStepProducts.install(completed));
            publicProducts.addAll(RootCombatPublicStepProducts.install(completed));
            publicProducts.addAll(RootGovernancePublicStepProducts.install(completed));
            publicProducts.addAll(RootInteractionPublicStepProducts.install(completed));
            publicProducts.addAll(RootEventPublicStepProducts.install(completed));
            publicProducts.addAll(RootLifecyclePublicStepProducts.install(completed));
            publicProducts.addAll(RootMilitaryControlPublicStepProducts.install(completed));
            publicProducts.addAll(RootMarriagePublicStepProducts.install(completed));
            publicProducts.addAll(RootLifePublicStepProducts.install(completed));
            publicProducts.addAll(RootArmyPublicStepProducts.install(completed));
            publicProducts.addAll(RootRouteContactAdvancePublicProducts.install(completed));
            publicProducts.addAll(RootPublicPauseStepProducts.install(completed));
            completed.bindPublicSteps(new RootPublicStepExecution.Catalog(context,publicProducts));
            context.requireActiveGame();actual.retainCatalogResources(completed);attempt.installed=completed;return completed;
        } catch(IOException failure) {attempt.failure=closeFailedResources(installedAdditional,installedArmy,failure);throw attempt.failure;}
        catch(RuntimeException failure) {attempt.failure=closeFailedResources(installedAdditional,installedArmy,new IOException("actual per-Game runtime installation failed",failure));throw attempt.failure;}
    }
    /** Source selection only. The caller first verifies the same actual Game/package through publicStepSource.
     * No historical wire, Java decoder source or unrelated basename can become the native definition. */
    static ExactRef crownDefinition(List<FileRef> qualifiedNative)throws IOException {
        var originals=List.copyOf(qualifiedNative).stream().filter(ref->java.nio.file.Path.of(ref.path()).getFileName().toString()
                .equals("ck3_12004_realm_law_action_mailbox.cpp")).toList();
        if(originals.size()!=1)throw new IOException("actual qualified native cut lacks one unambiguous Crown query definition");
        var actual=originals.getFirst();actual.verify();
        return new ExactRef(actual.path(),actual.bytes(),actual.sha256());
    }
    private static IOException closeFailedResources(RootAdditionalDomains.Installed actual,
            ArmyRuntimeInstaller actualArmy,IOException failure) {
        if(actual!=null)try{actual.close();}catch(IOException|RuntimeException disposal){
            if(disposal instanceof java.io.InterruptedIOException)Thread.currentThread().interrupt();
            if(disposal!=failure)failure.addSuppressed(disposal);
        }
        if(actualArmy!=null)try{actualArmy.close();}catch(IOException|RuntimeException disposal){
            if(disposal instanceof java.io.InterruptedIOException)Thread.currentThread().interrupt();
            if(disposal!=failure)failure.addSuppressed(disposal);
        }
        return failure;
    }
    /** Lookup is through Core's actual current Root session, never the last constructed candidate. */
    public RootRuntimeContext requireCurrent(org.xar.ck3.control.application.session.SessionPorts.SessionIdentity owner)throws IOException {
        return requireCurrentCatalog(owner).context();
    }
    public RootInstalledCatalog requireCurrentCatalog(org.xar.ck3.control.application.session.SessionPorts.SessionIdentity owner)throws IOException {
        RootApplicationAssembly.Core actual;
        synchronized(this) { actual=core; }
        if(actual==null)throw new IOException("actual Core is unbound");
        var root=actual.sessionAccess().current();
        StrictJson.require(root.identity().equals(owner) && !root.isRetired(),"runtime owner is not the actual admitted Root session");
        return retainedCatalog(actual,root);
    }
    /** Consume the identical Root already resolved by its caller, inside the original held writer scope. */
    public RootInstalledCatalog requireCurrentCatalog(RootApplicationSession identicalCurrent)throws IOException {
        Objects.requireNonNull(identicalCurrent);RootApplicationAssembly.Core actual;
        synchronized(this) {actual=core;}
        if(actual==null)throw new IOException("actual Core is unbound");
        var same=actual.writer().borrowedSession();
        actual.requireCurrentForAccess(same,identicalCurrent);
        if(identicalCurrent.writer()!=actual.writer()||identicalCurrent.archive()!=actual.archive())
            throw new IOException("resolved current Root crossed its original Core writer/archive");
        var retained=retainedCatalog(actual,identicalCurrent);
        actual.requireCurrentForAccess(same,identicalCurrent);return retained;
    }
    /** Resolves the already owned menu catalog inside the original borrowed writer scope, before a Driver may exist. */
    public RootInstalledCatalog requireFrontendCatalog(RootApplicationAssembly.Core identicalCore)throws IOException {
        Objects.requireNonNull(identicalCore);List<RootInstalledCatalog> retained;
        synchronized(this) {
            if(core==null||core!=identicalCore)throw new IOException("frontend lookup requires the identical once-bound runtime Core");
            retained=attempts.values().stream().map(attempt->attempt.installed).filter(Objects::nonNull).toList();
        }
        var same=identicalCore.writer().borrowedSession();identicalCore.writer().requireSession(same);
        RootInstalledCatalog selected=null;IOException rejected=new IOException("the original Core has no uniquely retained current frontend catalog");
        for(var candidate:retained) {
            if(candidate.context().core()!=identicalCore)continue;
            try {
                var menu=identicalCore.requireFrontendMenu(candidate.context());
                if(menu.bindings!=candidate.bindings()||menu.frontend!=candidate.frontend().authority())
                    throw new IOException("retained frontend menu lost its identical actual inventory or observation authority");
            } catch(IOException|IllegalArgumentException failure) {rejected.addSuppressed(failure);continue;}
            if(selected!=null)throw new IOException("multiple actual runtime catalogs claim the identical current frontend menu");
            selected=candidate;
        }
        if(selected==null)throw rejected;
        var menu=identicalCore.requireFrontendMenu(selected.context());
        if(menu.bindings!=selected.bindings()||menu.frontend!=selected.frontend().authority())
            throw new IOException("original frontend inventory or authority changed during retained lookup");
        identicalCore.writer().requireSession(same);requireBoundCore(identicalCore);return selected;
    }
    private RootInstalledCatalog retainedCatalog(RootApplicationAssembly.Core actual,RootApplicationSession root)throws IOException {
        var owner=root.identity();
        synchronized(this) {
            if(core!=actual)throw new IOException("original bound Core changed during retained catalog lookup");
            for(Attempt attempt:attempts.values())if(attempt.installed!=null
                    && attempt.context.core()==actual&&attempt.context.game().machineId().equals(owner.machineId())
                    && attempt.context.game().generation().equals(owner.game()) && attempt.context.game().sessionId().equals(owner.sessionId())
                    && attempt.context.adopted()==root.driver())
                return attempt.installed;
        }
        throw new IOException("actual admitted Root has no retained runtime catalog");
    }
    private static RootDomainInstallation activityInstallation(GovernanceActivityRuntime actual,ExactRef codec) {
        return new RootDomainInstallation("shared-activity-native-contracts",List.of(),actual.installedReads(codec),List.of(),
                List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
    }
}


