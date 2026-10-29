package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.FrontendAuthority;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.FrontendObservationSequence;
import org.xar.ck3.control.nativebridge.NativeFrontendAuthority;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.*;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.continuity.writer.WriterTransactionCodec;

/** Installs real native frontend rules; ordinary gameplay may omit unavailable original menu Start custody. */
public final class RootFrontendRuntime {
    /** Native menu Start custody is optional for an already-running ordinary campaign. */
    public record MenuStartSources(ExactRef startEffects,ExactRef startDecoder,ExactRef entryGuard,ExactRef entryAuthority,
            RootFrontendStartQueryDiagnostics.Prepared frontendStartDiagnostics,RootOriginalDriverJournal.Prepared originalDriverImport,
            Optional<FixtureSources> fixtureSources) {
        public MenuStartSources {
            Objects.requireNonNull(frontendStartDiagnostics);Objects.requireNonNull(originalDriverImport);Objects.requireNonNull(fixtureSources);
            for(var ref:List.of(startEffects,startDecoder,entryGuard,entryAuthority))
                StrictJson.require(ref.bytes()>0,"actual menu Start and entry source closure required");
            StrictJson.require(fixtureSources.isPresent()==originalDriverImport.frozenProfile().fixture().isPresent(),"only an explicit frozen fixture can select its actual Java source closure");
        }
    }
    public record Sources(FrontendRulesData.Build exactBuild,ExactRef originalNativeDriver,ExactRef rulesEffects,
            ExactRef rulesDecoder,Optional<MenuStartSources> menuStart,
            InitialEpisodePolicy initialPolicy,DynamicCapabilities.Configuration capabilityConfiguration,
            CapabilitySessionPresentation capabilitySession,Duration freshness,Duration heartbeatMaximumAge,
            int retainedFrames,int retainedOrigins,String authorityId) {
        public Sources(FrontendRulesData.Build exactBuild,ExactRef originalNativeDriver,ExactRef rulesEffects,
                ExactRef rulesDecoder,ExactRef startEffects,ExactRef startDecoder,ExactRef entryGuard,ExactRef entryAuthority,
                RootFrontendStartQueryDiagnostics.Prepared frontendStartDiagnostics,RootOriginalDriverJournal.Prepared originalDriverImport,
                InitialEpisodePolicy initialPolicy,DynamicCapabilities.Configuration capabilityConfiguration,
                CapabilitySessionPresentation capabilitySession,Duration freshness,Duration heartbeatMaximumAge,
                int retainedFrames,int retainedOrigins,String authorityId,Optional<FixtureSources> fixtureSources) {
            this(exactBuild,originalNativeDriver,rulesEffects,rulesDecoder,Optional.of(new MenuStartSources(startEffects,startDecoder,
                    entryGuard,entryAuthority,frontendStartDiagnostics,originalDriverImport,fixtureSources)),initialPolicy,
                    capabilityConfiguration,capabilitySession,freshness,heartbeatMaximumAge,retainedFrames,retainedOrigins,authorityId);
        }
        public Sources(FrontendRulesData.Build exactBuild,ExactRef originalNativeDriver,ExactRef rulesEffects,
                ExactRef rulesDecoder,ExactRef startEffects,ExactRef startDecoder,ExactRef entryGuard,ExactRef entryAuthority,
                RootFrontendStartQueryDiagnostics.Prepared frontendStartDiagnostics,RootOriginalDriverJournal.Prepared originalDriverImport,
                InitialEpisodePolicy initialPolicy,DynamicCapabilities.Configuration capabilityConfiguration,
                CapabilitySessionPresentation capabilitySession,Duration freshness,Duration heartbeatMaximumAge,
                int retainedFrames,int retainedOrigins,String authorityId) {
            this(exactBuild,originalNativeDriver,rulesEffects,rulesDecoder,startEffects,startDecoder,entryGuard,entryAuthority,
                    frontendStartDiagnostics,originalDriverImport,initialPolicy,capabilityConfiguration,capabilitySession,freshness,
                    heartbeatMaximumAge,retainedFrames,retainedOrigins,authorityId,Optional.empty());
        }
        /** Uses the real ordinary policy and native GUI sources without manufacturing an original Start import. */
        public static Sources ordinary(FrontendRulesData.Build exactBuild,ExactRef originalNativeDriver,ExactRef rulesEffects,
                ExactRef rulesDecoder,InitialEpisodePolicy initialPolicy,DynamicCapabilities.Configuration capabilityConfiguration,
                CapabilitySessionPresentation capabilitySession,Duration freshness,Duration heartbeatMaximumAge,
                int retainedFrames,int retainedOrigins,String authorityId) {
            Objects.requireNonNull(initialPolicy);
            StrictJson.require(initialPolicy.kind()==InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE
                    ||initialPolicy.kind()==InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,"ordinary frontend requires an explicit business lifecycle");
            return new Sources(exactBuild,originalNativeDriver,rulesEffects,rulesDecoder,Optional.empty(),initialPolicy,
                    capabilityConfiguration,capabilitySession,freshness,heartbeatMaximumAge,retainedFrames,retainedOrigins,authorityId);
        }
        public Sources {
            Objects.requireNonNull(exactBuild);Objects.requireNonNull(initialPolicy);Objects.requireNonNull(capabilityConfiguration);
            Objects.requireNonNull(capabilitySession);Objects.requireNonNull(freshness);Objects.requireNonNull(heartbeatMaximumAge);
            Objects.requireNonNull(menuStart);
            menuStart.ifPresent(start->StrictJson.require(start.originalDriverImport().frozenProfile().initialPolicy()==initialPolicy,
                    "frontend and Driver import must consume the identical actual frozen episode policy producer"));
            for(var ref:List.of(originalNativeDriver,rulesEffects,rulesDecoder))
                StrictJson.require(ref.bytes()>0,"actual native frontend rules source closure required");
            StrictJson.text(authorityId);StrictJson.require(retainedFrames>=1 && retainedFrames<=4096 && retainedOrigins>=1 && retainedOrigins<=65536,
                    "finite original frame and frontend sequence custody required");
        }
        private MenuStartSources requireMenuStart() {
            return menuStart.orElseThrow(()->new IllegalStateException("ordinary frontend has no original menu Start inputs; unsupported until genuine Start custody is supplied"));
        }
        public ExactRef startEffects(){return requireMenuStart().startEffects();}
        public ExactRef startDecoder(){return requireMenuStart().startDecoder();}
        public ExactRef entryGuard(){return requireMenuStart().entryGuard();}
        public ExactRef entryAuthority(){return requireMenuStart().entryAuthority();}
        public RootFrontendStartQueryDiagnostics.Prepared frontendStartDiagnostics(){return requireMenuStart().frontendStartDiagnostics();}
        public RootOriginalDriverJournal.Prepared originalDriverImport(){return requireMenuStart().originalDriverImport();}
        public Optional<RootOriginalDriverJournal.Prepared> optionalOriginalDriverImport(){return menuStart.map(MenuStartSources::originalDriverImport);}
        public Optional<FixtureSources> fixtureSources(){return menuStart.flatMap(MenuStartSources::fixtureSources);}
    }
    /** One source-target contract shared by the actual configuration producer and the strict runtime consumer. */
    public record RequiredFixtureSource(String targetRelative,Class<?> type) {
        public RequiredFixtureSource {
            Objects.requireNonNull(targetRelative);Objects.requireNonNull(type);
            StrictJson.require(targetRelative.endsWith("/src/main/java/"+type.getName().replace('.','/')+".java"),"exact top-level fixture source target required");
        }
    }
    public static List<RequiredFixtureSource> requiredFixtureSources()throws IOException {
        var result=new ArrayList<RequiredFixtureSource>();
        for(Class<?> type:List.of(FrontendFixturePolicy.class,PreparedFixture.class,FixtureStartSubmission.class,
                FixtureFrontendProducer.class,FixtureQualificationLogs.class,RootFixtureFrontendPort.class,
                RootFixtureFrontendPublicProducts.class,RootFixtureWorkflow.class,FixtureQualificationTrace.class,QualifiedFixtureScope.class,
                FixtureStartupHandler.class,FixtureStartupCase.class,FixtureStartupObservation.class,FixtureBusinessQualification.class,
                FixtureGameplayRoot.class,FixtureFrontendEffects.class,FixtureModelContract.class,
                RootFrontendRuntime.class,RootInstalledCatalog.class,RootRuntimeCatalogFactory.class,RootRuntimeContext.class,
                RootFrozenRunProfile.class,RootSelectedRegistrationConfiguration.class,RootFrontendRulesPublicProducts.class,RootFixtureQualifiedScope.class,
                InitialEpisodePolicy.class,InitialDriverBootstrap.class,InitialDriverState.class,GameplayEntryService.class,GameplayEntryAuthority.class))
            result.add(new RequiredFixtureSource("local-service/src/main/java/"+type.getName().replace('.','/')+".java",type));
        for(Class<?> type:List.of(FixturePlan.class,FixtureCompositeActionPort.class,FixtureStartObservation.class,FixtureBusinessEvidence.class,
                FixtureBusinessObservation.class,FixtureProofCodec.class,ActionCoordinator.class,ActionPorts.class,ActionState.class,
                ActionEffects.class,ActionReceipt.class,ActionReceiptCodec.class,ActionChildPlanningScope.class,CompositeContinuationToken.class,
                NativeCampaignProjection.class,org.xar.ck3.control.application.planning.campaign.PublicTerminalDataContext.class))
            result.add(new RequiredFixtureSource("application/src/main/java/"+type.getName().replace('.','/')+".java",type));
        for(String name:List.of("org.xar.ck3.control.application.action.CompositeCoordinatorSupport","org.xar.ck3.control.application.action.CompositeContinuationSupport")) {
            try {Class<?> type=Class.forName(name,false,RootFrontendRuntime.class.getClassLoader());
                result.add(new RequiredFixtureSource("application/src/main/java/"+name.replace('.','/')+".java",type));}
            catch(ClassNotFoundException missing){throw new IOException("actual private fixture composite implementation missing: "+name,missing);}
        }
        String guard="org.xar.ck3.control.service.root.RootFixtureGuardEvidence";
        try {result.add(new RequiredFixtureSource("local-service/src/main/java/"+guard.replace('.','/')+".java",Class.forName(guard,false,RootFrontendRuntime.class.getClassLoader())));}
        catch(ClassNotFoundException missing){throw new IOException("actual private Root fixture guard evidence missing",missing);}
        result.add(new RequiredFixtureSource("continuity-core/src/main/java/org/xar/ck3/control/continuity/writer/WriterTransactionCodec.java",WriterTransactionCodec.class));
        return List.copyOf(result);
    }
    /** Captures the real selector used by the pre-Core producer; no public DTO can issue this custody. */
    public static final class FixtureSources {
        private final RootRuntimeSelectedSources selected;
        private final ExactRef effects;
        private final ExactRef workflow;
        private final ExactRef model;
        private FixtureSources(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected)throws IOException {
            this.selected=Objects.requireNonNull(selected);selected.requireInputs(Objects.requireNonNull(inputs));
            for(RequiredFixtureSource required:requiredFixtureSources())requireConfigured(inputs,selected.javaSourceAt(required.targetRelative(),required.type()));
            effects=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,FixtureFrontendEffects.class);requireConfigured(inputs,effects);
            workflow=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootFixtureWorkflow.class);requireConfigured(inputs,workflow);
            model=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,FixtureModelContract.class);requireConfigured(inputs,model);
            selected.requireInputs(inputs);
        }
        private void requireCurrent(NativeLaunchPlan samePlan)throws IOException {selected.requireCurrent();selected.requireLoadedClasses(samePlan);}
    }
    public static FixtureSources fixtureSources(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected)throws IOException {return new FixtureSources(inputs,selected);}
    private static void requireConfigured(RootRuntimeDefinitions.Inputs inputs,ExactRef ref)throws IOException {
        requireConfiguredFixtureSource(inputs.configuration(),ref);
    }
    /** The production consumer and producer-to-codec tests use this same exact original membership boundary. */
    static void requireConfiguredFixtureSource(RootRuntimeDefinitionModel.Configuration configuration,ExactRef ref)throws IOException {
        Objects.requireNonNull(configuration);Objects.requireNonNull(ref);
        if(RootRuntimeDefinitions.configuredSources(configuration).stream().noneMatch(row->row.sourceRef().equals(ref)))
            throw new IOException("explicit fixture Java source is absent from the original configured closure: "+ref.path());
    }
    private final RootRuntimeContext context;
    private final Sources sources;
    private final FrontendRulesDefinitions definitions;
    private final FrontendRulesInstaller rules;
    private final Optional<InitialDriverBootstrap> bootstrap;
    private final Optional<GameplayStartEffects> effects;
    private final Optional<RootFrontendStartQueryDiagnostics> frontendStartDiagnostics;
    private final Optional<GameplayStartInstaller> start;
    private final Optional<FixtureFrontendEffects> fixtureEffects;
    private final Optional<RootFixtureWorkflow> workflow;
    private RootInstalledCatalog fixtureCatalog;
    private final Optional<GameplayEntryAuthority> entryAuthority;
    private final ReadContract<?> root;
    private final RootDomainInstallation installation;
    private FrontendObservationSequence sequence;
    private NativeFrontendAuthority authority;
    private RootMenuSession menu;
    private GameplayEntryService service;
    public RootFrontendRuntime(RootRuntimeContext context,Sources sources)throws IOException {
        this.context=Objects.requireNonNull(context);this.sources=Objects.requireNonNull(sources);
        definitions=new FrontendRulesDefinitions(sources.exactBuild(),sources.originalNativeDriver());
        rules=new FrontendRulesInstaller(definitions,context.reads(),context.archive(),sources.rulesEffects(),sources.rulesDecoder());
        root=context.finance().definitions().contract(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.Query.ROOT);
        if(sources.menuStart().isPresent()) {
            var actualBootstrap=new InitialDriverBootstrap(context.writer(),context.archive(),context.core().actions(),context.game(),context.source(),
                    context.sources(),context.semanticVerifier(),sources.initialPolicy(),context.clock(),sources.freshness(),sources.retainedFrames(),
                    sources.capabilityConfiguration(),sources.capabilitySession(),sources.originalDriverImport());
            bootstrap=Optional.of(actualBootstrap);
            var actualEffects=new GameplayStartEffects(definitions,root,actualBootstrap,context.writer(),context.archive(),context.semanticVerifier());
            effects=Optional.of(actualEffects);
            frontendStartDiagnostics=Optional.of(sources.frontendStartDiagnostics().install(context,actualEffects));
            if(sources.originalDriverImport().frozenProfile().fixture().isPresent()) {
                FixtureSources actual=sources.fixtureSources().orElseThrow();actual.requireCurrent(context.game().launchPlan());
                fixtureEffects=Optional.of(new FixtureFrontendEffects(sources.originalDriverImport().frozenProfile().fixture().orElseThrow(),definitions,context.reads(),context.archive(),context.writer(),actualBootstrap,context.semanticVerifier(),context.clock()));
                workflow=Optional.of(new RootFixtureWorkflow(context,this,sources.originalDriverImport().frozenProfile().fixture().orElseThrow(),fixtureEffects.orElseThrow(),actual.workflow));
                start=Optional.empty();
            } else {fixtureEffects=Optional.empty();workflow=Optional.empty();start=Optional.of(new GameplayStartInstaller(actualEffects,sources.startEffects(),sources.startDecoder()));}
            entryAuthority=Optional.of(new GameplayEntryAuthority(context.writer(),context.archive(),actualBootstrap,actualEffects,sources.entryAuthority()));
        } else {
            bootstrap=Optional.empty();effects=Optional.empty();frontendStartDiagnostics=Optional.empty();entryAuthority=Optional.empty();
            fixtureEffects=Optional.empty();workflow=Optional.empty();start=Optional.empty();
        }
        var actions=new ArrayList<>(rules.actions());var archived=new ArrayList<>(rules.archivedVerifiers());var admissions=new ArrayList<>(rules.routeAdmissions());
        var reads=new ArrayList<RootReadContractCatalog.InstalledRead>();
        for(var read:rules.reads())reads.add(new RootReadContractCatalog.InstalledRead(read,sources.rulesDecoder()));
        var composites=new ArrayList<RootExecutableBindings.CompositeBinding>();
        if(fixtureEffects.isPresent()) {
            var actual=fixtureEffects.orElseThrow();var originalSources=sources.fixtureSources().orElseThrow();var source=originalSources.effects;
            var model=actual.models().model();reads.removeIf(read->read.contract().operation().equals(model.operation()));
            reads.add(new RootReadContractCatalog.InstalledRead(model,originalSources.model));
            if(actual.fixture().policy().kind()==FrontendFixturePolicy.Kind.ROBERT) {
                var selector=FrontendRulesRequests.Primitive.SELECT_1066.operation();
                actions.removeIf(binding->binding.effect().operation().equals(selector));
                archived.removeIf(binding->binding.operation().equals(selector));
                admissions.removeIf(binding->binding.operation().equals(selector));
            }
            actions.addAll(actual.actions(source,source));archived.addAll(actual.archivedVerifiers(source));admissions.addAll(actual.routeAdmissions(source));
            var originalWorkflow=workflow.orElseThrow();composites.addAll(originalWorkflow.composites());archived.addAll(originalWorkflow.archivedVerifiers());admissions.addAll(originalWorkflow.routeAdmissions());
        } else start.ifPresent(ordinary->{actions.addAll(ordinary.actions());archived.addAll(ordinary.archivedVerifiers());admissions.addAll(ordinary.routeAdmissions());});
        installation=new RootDomainInstallation("frontend-menu-and-initial-gameplay",List.of(),
                List.copyOf(reads),
                List.of(),actions,composites,archived,List.of(),List.of(),admissions,List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
    }
    public RootDomainInstallation installation() { return installation; }
    void requireContext(RootRuntimeContext identical)throws IOException {
        if(context!=Objects.requireNonNull(identical))throw new IOException("frontend runtime belongs to another actual Root context");
    }
    public FrontendRulesInstaller rules() { return rules; }
    public Optional<RootFrontendStartQueryDiagnostics> optionalFrontendStartDiagnostics() { return frontendStartDiagnostics; }
    public RootFrontendStartQueryDiagnostics frontendStartDiagnostics() { return frontendStartDiagnostics.orElseThrow(()->new IllegalStateException("ordinary frontend has no original Start query journal")); }
    public InitialDriverBootstrap initialDriver() { return bootstrap.orElseThrow(()->new IllegalStateException("ordinary frontend menu Start is unsupported without original bootstrap inputs")); }
    public boolean menuStartSupported() { return sources.menuStart().isPresent(); }
    public InitialEpisodePolicy initialPolicy() { return sources.initialPolicy(); }
    public Optional<PreparedFixture> fixture() { return sources.optionalOriginalDriverImport().flatMap(actual->actual.frozenProfile().fixture()); }
    public Optional<FixtureFrontendEffects> fixtureEffects() { return fixtureEffects; }
    public Optional<FixtureStartupCase> startupCase() { return sources.optionalOriginalDriverImport().flatMap(actual->actual.frozenProfile().startupCase()); }
    public Optional<RootFixtureWorkflow> workflow() { return workflow; }
    public GameplayEntryAuthority entryAuthority() { return entryAuthority.orElseThrow(()->new IllegalStateException("ordinary frontend entry is unsupported without original menu Start authority")); }
    synchronized void bindFixtureCatalog(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);context.game().verify();
        StrictJson.require(fixture().isPresent()&&actual.context()==context&&actual.frontend()==this
                &&actual.context().core()==context.core()&&actual.bindings()==context.bindings(),"fixture catalog must be the sole fully installed same-context inventory");
        StrictJson.require(fixtureCatalog==null||fixtureCatalog==actual,"fixture catalog cannot be replaced");fixtureCatalog=actual;
    }
    public synchronized RootInstalledCatalog fixtureCatalog() {
        StrictJson.require(fixture().isPresent()&&fixtureCatalog!=null,"actual fixture catalog has not completed installation");return fixtureCatalog;
    }
    public FixtureFrontendProducer.Submitted submitFixture(RootMenuSession sameMenu,FrontendAuthority.LeaseSnapshot actual,Instant deadline)throws IOException,InterruptedException {
        fixture().orElseThrow(()->new IOException("ordinary runtime has no explicit fixture policy"));
        sources.fixtureSources().orElseThrow().requireCurrent(context.game().launchPlan());fixtureCatalog();
        return workflow.orElseThrow().submit(sameMenu,actual,deadline);
    }
    synchronized void bindInventory(List<FrontendRouteAdmission> allOriginalAdmissions)throws IOException {
        StrictJson.require(sequence==null,"one frontend observation sequence owns the entire menu and adopted runtime");
        sequence=new FrontendObservationSequence(context.transport(),context.archive(),context.source(),context.bindings(),
                List.copyOf(allOriginalAdmissions),context::optionalDriverProducer,context.sources()::verifyFrontend,context.clock(),
                sources.freshness(),sources.heartbeatMaximumAge(),sources.retainedOrigins());
        authority=new NativeFrontendAuthority(sequence);
    }
    public synchronized NativeFrontendAuthority authority() {
        StrictJson.require(authority!=null,"actual inventory has not bound its frontend sequence");return authority;
    }
    public FrontendAuthority.LeaseSnapshot observeMenu(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Instant deadline)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(deadline);return sequence.observeMenu(same,deadline);
    }
    /** One original source-bound observation covers the entire frontend read callback. MENU needs no adopted Driver. */
    public <T> T withSourceBoundFrontendRead(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            FrontendRouteAdmission.FrameMode mode,Instant deadline,FrontendAuthority.CheckedWork<T> work)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(deadline);
        T result=authority().withSourceBoundFrontendRead(same,mode,deadline,work);
        context.writer().requireSession(same);context.requireCurrent(deadline);return result;
    }
    public synchronized GameplayEntryService entry(RootMenuSession actualMenu)throws IOException {
        if(fixture().isPresent())throw new IOException("explicit fixture must use its original once-only submission and typed continuation");
        return entryService(actualMenu);
    }
    public synchronized GameplayEntryService fixtureEntry(RootMenuSession actualMenu)throws IOException {
        if(fixture().isEmpty())throw new IOException("ordinary runtime cannot obtain the explicit fixture entry consumer");
        StrictJson.require(fixtureCatalog().context()==context&&context.core().requireFrontendMenu(context)==actualMenu,"fixture entry crossed the actual installed catalog/menu");
        return entryService(actualMenu);
    }
    private GameplayEntryService entryService(RootMenuSession actualMenu)throws IOException {
        if(service!=null) {StrictJson.require(menu==actualMenu,"entry service cannot bind another menu/dispatcher");return service;}
        if(bootstrap.isEmpty()||effects.isEmpty()||entryAuthority.isEmpty())
            throw new IOException("unsupported ordinary frontend menu Start: original bootstrap/Start/entry inputs are unavailable; defer rather than fabricate an adopted episode");
        var actualBootstrap=bootstrap.orElseThrow();var actualEffects=effects.orElseThrow();var actualEntryAuthority=entryAuthority.orElseThrow();
        var guard=new GameplayEntryReadGuard(actualBootstrap,root,context.writer(),context.archive(),context.originals(),context.readCatalog(),
                context.source(),context.clock(),sources.authorityId());
        service=fixture().isPresent()?GameplayEntryService.fixture(context.core(),actualMenu,definitions,actualEffects,actualBootstrap,guard,actualEntryAuthority,
                sources.entryGuard(),sources.entryAuthority()):new GameplayEntryService(context.core(),actualMenu,definitions,actualEffects,actualBootstrap,guard,actualEntryAuthority,
                sources.entryGuard(),sources.entryAuthority());menu=actualMenu;return service;
    }
}
