package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling;
import org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccessionService;
import org.xar.ck3.control.nativebridge.capabilities.interactions.GrantPickerControlEffects;
import org.xar.ck3.control.nativebridge.capabilities.interactions.GrantTitleCodec;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionReads;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionTitleSelectorReads;
import org.xar.ck3.control.nativebridge.capabilities.interactions.TitleClaimsPublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry.DriverRegistryService;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.NativePrelaunchInputs;
import org.xar.ck3.control.platform.NormalExitSourceInventory;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;
import org.xar.ck3.control.service.root.RootDriverRegistryPublicProducts.ProductSource;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;

/** The sole pre-Core constructor for the twelve Driver products. Source custody is not Game admission. */
public final class RootDriverProductSourcesFactory {
    /** These are the identical objects already retained by the one total startup composition. */
    public record Input(RootRuntimeDefinitions.Inputs inputs, RootRuntimeSelectedSources selected,
            RootRuntimeNativeOriginals.Bound originals, RootRuntimeDomainSettings.Bound settings,
            RootSelectedRegistrationConfiguration.Bound registration, NativeLaunchPlan plan,
            RootRuntimeStorageGuard storage, RootFrontendRuntime.Sources frontend,
            FinanceRuntimeInstaller.Prepared finance, ConstructionRuntimeInstaller.Sources construction,
            RootFamilyRuntimeFactory.Prepared family, GovernanceOrdinaryRuntimeInstaller.Prepared governance,
            RootCrownRetryRuntime.Prepared retry, RootLifecycleRuntimeFactory.Prepared lifecycle,
            RootCoreBoundPorts ports, GovernanceRuntimeInstaller.Prepared nativeGovernance,
            OriginalRuntimeHandoffProof.Provider grantStore, Clock clock,
            OriginalDriverQueryHistorySettings.Bound queryHistory,RootOperatorCharacterAuthority.Prepared operatorAuthority) {
        public Input {
            for (Object value : List.of(inputs, selected, originals, settings, registration, plan, storage,
                    frontend, finance, construction, family, governance, retry, lifecycle, ports,
                    nativeGovernance, grantStore, clock,queryHistory,operatorAuthority)) Objects.requireNonNull(value);
        }
    }
    /** Exact Java sources only. This record contains no deserializable service or permission authority. */
    public record JavaProducts(ExactRef governance, ExactRef faction, ExactRef heir, ExactRef lifecycle,
            ExactRef transport, ExactRef family, ExactRef grant, ExactRef titleClaims, ExactRef cash,
            ExactRef saveArtifacts, ExactRef engineDiagnostics, ExactRef platform) {
        public JavaProducts {
            for (var source : List.of(governance, faction, heir, lifecycle, transport, family, grant,
                    titleClaims, cash, saveArtifacts, engineDiagnostics, platform)) needSource(source);
        }
    }
    public record TitleSources(ExactRef selectors, ExactRef decoder, ExactRef publicCodec, ExactRef runtime) {
        public TitleSources { for (var source : List.of(selectors, decoder, publicCodec, runtime)) needSource(source); }
    }
    /** A closed data description of the actual source joins. Constructing it cannot install its products. */
    public record Sources(JavaProducts javaProducts, ExactRef cachedNative, ExactRef cachedDecoder,
            DriverGovernanceReadDefinitions.Sources governanceReads, ExactRef governancePublicService,
            RootDriverLifecycleRuntimeInstaller.Sources lifecycle,
            RootDriverTransportRuntimeFactory.Sources transport, TitleSources titleClaims,
            CashObservationReads.Sources cash, NormalExitSourceInventory.Input normalExit,
            ExactRef grantEffects, ExactRef grantDecoder) {
        public Sources {
            for (Object value : List.of(javaProducts, governanceReads, lifecycle, transport, titleClaims,
                    cash, normalExit)) Objects.requireNonNull(value);
            for (var source : List.of(cachedNative, cachedDecoder, governancePublicService, grantEffects,
                    grantDecoder)) needSource(source);
        }
    }

    public record NativeSources(ExactRef cachedSuccession, ExactRef councilDefinition, ExactRef governmentBinder, ExactRef dispatcher, List<ExactRef> observerProducerClosure) {
        public NativeSources {
            for (Object value : List.of(cachedSuccession, councilDefinition, governmentBinder, dispatcher, observerProducerClosure)) Objects.requireNonNull(value);
            observerProducerClosure=List.copyOf(observerProducerClosure);
            for (var source : observerProducerClosure) needSource(source);
        }
    }

    public record PlainConfig(NativeLaunchPlan plan, RootRuntimeDefinitionModel.GovInputs governance, boolean privateSemanticReadonly, NativeSources nativeSources, java.util.Optional<NormalExitSourceInventory.Input> normalExit) {
        public PlainConfig {
            Objects.requireNonNull(plan);
            Objects.requireNonNull(governance);
            Objects.requireNonNull(nativeSources);
            Objects.requireNonNull(normalExit);
        }
    }

    public record SharedServices(FinanceRuntimeInstaller.Prepared finance, ConstructionRuntimeInstaller.Sources construction, RootFamilyRuntimeFactory.Prepared family, RootLifecycleRuntimeFactory.Prepared lifecycle, GovernanceRuntimeInstaller.Prepared nativeGovernance, OriginalRuntimeHandoffProof.Provider grantStore, RootSetPlayedCharacterRuntime.SourceFactory operatorSource) {
        public SharedServices {
            for (Object value : List.of(finance, construction, family, lifecycle, nativeGovernance, grantStore, operatorSource)) Objects.requireNonNull(value);
        }
    }

    public static RootDriverRegistryPublicProducts.Prepared prepareOrdinary(PlainConfig config, SharedServices shared, RootCoreBoundPorts ports, RootAdditionalDomains.ImplementationMetadata metadata, Clock clock) throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(shared);Objects.requireNonNull(ports);Objects.requireNonNull(metadata);Objects.requireNonNull(clock);
        var catalog = VanillaEventCatalog.load();
        var java = new JavaProducts(
                metadata.implementation(RootDriverGovernancePublicSupplier.class),
                metadata.implementation(RootDriverFactionPublicSupplier.class),
                metadata.implementation(RootDriverHeirPublicSupplier.class),
                metadata.implementation(RootDriverLifecycleRuntimeInstaller.class),
                metadata.implementation(RootDriverTransportRuntimeFactory.class),
                metadata.implementation(RootDriverFamilyPublicProduct.class),
                metadata.implementation(RootGrantTitlePublicProducts.class),
                metadata.implementation(RootTitleClaimsRuntime.class),
                metadata.implementation(RootCashObservationPublicProducts.class),
                metadata.implementation(RootSaveArtifactPublicProducts.class),
                metadata.implementation(RootEngineDiagnosticsPublicProducts.class),
                metadata.implementation(RootNormalExitRuntime.class));
        var governanceReads = new DriverGovernanceReadDefinitions.Sources(config.nativeSources().councilDefinition(), config.nativeSources().governmentBinder(), metadata.implementation(DriverGovernanceReadDefinitions.class));
        var governance = shared.nativeGovernance().publicCallerProducer().isPresent() ?
                RootDriverGovernancePublicSupplier.prepare(
                        product(RootDriverGovernancePublicSupplier.class, java.governance()),
                        governanceReads,
                        config.governance(),
                        shared.nativeGovernance().publicCallerProducer().get()) :
                RootDriverGovernancePublicSupplier.prepare(
                        product(RootDriverGovernancePublicSupplier.class, java.governance()),
                        governanceReads,
                        config.governance());
        var faction = new RootDriverFactionPublicSupplier.Prepared(new RootDriverFactionPublicSupplier.Sources(
                shared.finance(), product(RootDriverFactionPublicSupplier.class, java.faction())));
        var heir = new RootDriverHeirPublicSupplier.Prepared(java.heir());
        var lifecycle = new RootDriverLifecycleRuntimeInstaller.Prepared(
                product(RootDriverLifecycleRuntimeInstaller.class, java.lifecycle()),
                lifecycleSourcesOrdinary(metadata, shared.lifecycle()),
                shared.lifecycle(), clock);
        var transport = new RootDriverTransportRuntimeFactory.Prepared(new RootDriverTransportRuntimeFactory.Sources(
                config.nativeSources().dispatcher(),
                metadata.implementation(ArmyObserverSampling.class), java.transport(),
                List.copyOf(config.nativeSources().observerProducerClosure()),
                metadata.implementation(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.class)), config.privateSemanticReadonly());
        var family = new RootDriverFamilyPublicProduct.Prepared(shared.family(),
                product(RootDriverFamilyPublicProduct.class, java.family()));
        var grant = new RootGrantTitlePublicProducts.Prepared(new RootGrantTitlePublicProducts.Sources(
                java.grant(), metadata.implementation(GrantPickerControlEffects.class), metadata.implementation(GrantTitleCodec.class), shared.grantStore()));
        var title = new TitleSources(metadata.implementation(InteractionTitleSelectorReads.class), metadata.implementation(InteractionReads.class), metadata.implementation(TitleClaimsPublicCodec.class), java.titleClaims());
        var actualOperator = RootSetPlayedCharacterRuntime.prepareOrdinary(shared.operatorSource(), metadata);
        var titleClaims = new RootTitleClaimsRuntime.Prepared(title.selectors(), title.decoder(), title.publicCodec(), title.runtime(), actualOperator);
        var cashSources = new CashObservationReads.Sources(metadata.implementation(CashObservationReads.class), metadata.implementation(CashObservationCodec.class));
        shared.finance().bindCashObservationSources(cashSources);
        var cash = new RootCashObservationPublicProducts.Prepared(new RootCashObservationPublicProducts.Sources(
                product(RootCashObservationPublicProducts.class, java.cash()),
                cashSources,
                shared.finance(), shared.construction()));
        var save = RootSaveArtifactPublicProducts.prepare(config.plan(), clock, catalog.textRules(), java.saveArtifacts());
        var engine = RootEngineDiagnosticsPublicProducts.prepareOrdinary(config.plan(), catalog.textRules(), java.engineDiagnostics(), clock);
        var platform = RootNormalExitRuntime.ordinary(product(RootNormalExitRuntime.class, java.platform()), config.normalExit());
        var cached = DriverRegistryService.definitions(config.nativeSources().cachedSuccession(), metadata.implementation(CachedSuccessionService.class), request -> {
            try { ports.verifyCachedRead(request); }
            catch (IOException unavailable) { throw new UncheckedIOException("actual cached-succession read admission unavailable", unavailable); }
        });
        var children = new RootDriverRegistryPublicProducts.Products(governance, faction, heir, lifecycle, transport, family, grant, titleClaims, cash, save, engine, platform);
        return new RootDriverRegistryPublicProducts.Prepared(cached, children, catalog);
    }

    private static RootDriverLifecycleRuntimeInstaller.Sources lifecycleSourcesOrdinary(RootAdditionalDomains.ImplementationMetadata metadata, RootLifecycleRuntimeFactory.Prepared lifecycle) throws IOException {
        final Class<?> pendingEpisodeClass;
        try { pendingEpisodeClass=Class.forName("org.xar.ck3.control.application.driver.DriverPendingEpisodeProducer",false,org.xar.ck3.control.application.driver.DriverPendingEpisodeSource.class.getClassLoader()); }
        catch(ClassNotFoundException missing) { throw new IOException("actual pending episode producer is not deployed",missing); }
        return new RootDriverLifecycleRuntimeInstaller.Sources(
                metadata.implementation(RootPendingUiRuntime.class),
                metadata.implementation(RootDriverLifecyclePublicSupplier.class),
                metadata.implementation(RootDriverLifecyclePublicCodec.class),
                metadata.implementation(org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.class),
                metadata.implementation(org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec.class),
                metadata.implementation(org.xar.ck3.control.application.lifecycle.SuccessorUiObligationReducer.class),
                metadata.implementation(org.xar.ck3.control.application.driver.DriverPendingEpisodeSource.class),
                metadata.implementation(org.xar.ck3.control.application.driver.DriverPendingEpisodeProjection.class),
                metadata.implementation(pendingEpisodeClass),
                metadata.implementation(org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.class),
                lifecycle.sources().timelineDefinition(), lifecycle.sources().closeDefinition());
    }

    private final Input input;
    private Sources sources;
    private RootDriverRegistryPublicProducts.Prepared products;
    private IOException failure;
    private boolean entered;

    public RootDriverProductSourcesFactory(Input identical) { input = Objects.requireNonNull(identical); }
    /** Retained concrete inputs for other same-package source compositions; never a serialized admission. */
    Input retainedInput() { return input; }

    /** One actual attempt. A failed partial constructor is retained and never binds Finance a second time. */
    public synchronized RootDriverRegistryPublicProducts.Prepared prepare() throws IOException {
        if (products != null) { requireCurrent(); return products; }
        if (entered) throw new IOException("Driver source composition previously failed or is reentrant", failure);
        entered = true;
        try {
            requireCurrent();
            NativePrelaunchInputs.requireCurrent(input.plan(), input.clock());
            sources = captureSources();
            var catalog = VanillaEventCatalog.load();
            requireCurrent();
            var java = sources.javaProducts();
            var governance = RootDriverGovernancePublicSupplier.prepare(
                    product(RootDriverGovernancePublicSupplier.class, java.governance()),
                    sources.governanceReads(), input.inputs().configuration().governance(),
                    sources.governancePublicService());
            var faction = new RootDriverFactionPublicSupplier.Prepared(new RootDriverFactionPublicSupplier.Sources(
                    input.finance(), product(RootDriverFactionPublicSupplier.class, java.faction())));
            var heir = new RootDriverHeirPublicSupplier.Prepared(java.heir());
            var lifecycle = new RootDriverLifecycleRuntimeInstaller.Prepared(
                    product(RootDriverLifecycleRuntimeInstaller.class, java.lifecycle()), sources.lifecycle(),
                    input.lifecycle(), input.clock());
            var transport = new RootDriverTransportRuntimeFactory.Prepared(sources.transport(), semanticReadSelected());
            var family = new RootDriverFamilyPublicProduct.Prepared(input.family(),
                    product(RootDriverFamilyPublicProduct.class, java.family()));
            var grant = new RootGrantTitlePublicProducts.Prepared(new RootGrantTitlePublicProducts.Sources(
                    java.grant(), sources.grantEffects(), sources.grantDecoder(), input.grantStore()));
            var title = sources.titleClaims();
            var actualOperator=RootSetPlayedCharacterRuntime.prepare(input.inputs(),input.selected(),input.operatorAuthority());
            var titleClaims = new RootTitleClaimsRuntime.Prepared(title.selectors(), title.decoder(),
                    title.publicCodec(), title.runtime(),actualOperator);
            // Finance owns this exact family. Its once-binding occurs here, before any Core or second adapter.
            input.finance().bindCashObservationSources(sources.cash());
            var cash = new RootCashObservationPublicProducts.Prepared(new RootCashObservationPublicProducts.Sources(
                    product(RootCashObservationPublicProducts.class, java.cash()), sources.cash(),
                    input.finance(), input.construction()));
            var save = RootSaveArtifactPublicProducts.prepare(input.plan(), input.clock(), catalog.textRules(), java.saveArtifacts());
            var engine = RootEngineDiagnosticsPublicProducts.prepare(input.plan(), input.storage(), catalog.textRules(),
                    input.inputs(), input.clock());
            var platform = new RootNormalExitRuntime.Prepared(product(RootNormalExitRuntime.class, java.platform()), sources.normalExit());
            var cached = DriverRegistryService.definitions(sources.cachedNative(), sources.cachedDecoder(), request -> {
                try { input.ports().verifyCachedRead(request); }
                catch (IOException unavailable) { throw new UncheckedIOException("actual cached-succession read admission unavailable", unavailable); }
            });
            var children = new RootDriverRegistryPublicProducts.Products(governance, faction, heir, lifecycle,
                    transport, family, grant, titleClaims, cash, save, engine, platform);
            var result = new RootDriverRegistryPublicProducts.Prepared(cached, children, catalog);
            requireCurrent();
            products = result;
            return result;
        } catch (IOException invalid) { failure = invalid; throw invalid; }
        catch (RuntimeException invalid) { failure = new IOException("actual Driver source composition failed", invalid); throw failure; }
    }

    public synchronized Sources sources() throws IOException {
        if (products == null || sources == null) throw new IOException("Driver source composition has not completed");
        requireCurrent(); return sources;
    }

    /** The total caller checks its completed Sources before constructing the sole catalog factory. */
    public synchronized void requireDefinitions(RootRuntimeCatalogFactory.Sources actual) throws IOException {
        Objects.requireNonNull(actual); var same = prepare();
        if (actual.additionalDomains().driverRegistry() != same || actual.finance() != input.finance()
                || actual.construction() != input.construction() || actual.nativeGovernance() != input.nativeGovernance()
                || actual.frontend() != input.frontend() || actual.governance() != input.governance()
                || actual.retryRuntime() != input.retry())
            throw new IOException("total runtime Sources replaced a retained Driver dependency or Prepared");
        actual.remainingDomains().requireDriverDependencies(input.family(),input.lifecycle());
        if(actual.remainingDomains().strengths().queryHistorySettings()!=input.queryHistory())
            throw new IOException("Driver and actual Army strengths installation use different query-history settings custody");
        input.storage().requireFilePort(actual.checkpointFiles());
        requireCurrent();
    }

    public synchronized void requireCurrent() throws IOException {
        input.inputs().originalRef().verify();
        input.selected().requireInputs(input.inputs());
        input.registration().requireCurrent(input.inputs(), input.clock());
        input.queryHistory().requireSame(input.plan(),input.clock());
        if(!input.queryHistory().original().equals(input.settings().configuration().queryHistorySettings()))
            throw new IOException("Driver query history does not retain the actual configured settings document");
        input.operatorAuthority().requireInputs(input.inputs(),input.selected());
        input.frontend().originalDriverImport().frozenProfile().requireCurrent(input.plan(),input.clock());
        if(!input.settings().original().equals(input.inputs().data(RootRuntimeDefinitionModel.DataRole.REMAINING_DOMAIN_SETTINGS))
                ||!input.originals().original().equals(input.inputs().data(RootRuntimeDefinitionModel.DataRole.NATIVE_DOMAIN_ORIGINALS)))
            throw new IOException("Driver source/settings custody differs from the actual configured data originals");
        input.originals().requireCurrent(input.clock());
        input.settings().requireCurrent(input.clock());
        input.storage().requireReadAuthorityCurrent();
        input.originals().requireQualifiedCut(input.plan());
        // This later check retains immutable inputs; launch-time mutable prepared files were checked before construction.
        input.plan().sources().verify();
        var expectedPlan = input.inputs().configuration().nativeLaunchPlanRef();
        var configured = NativeLaunchPlanCodec.fromJson(StrictJson.parse(
                RootRuntimeDefinitions.read(expectedPlan, NativeLaunchPlanCodec.MAXIMUM_BYTES), NativeLaunchPlanCodec.MAXIMUM_BYTES));
        if (!configured.equals(NativeLaunchPlanCodec.describe(input.plan())))
            throw new IOException("Driver products require the identical retained launch configuration");
        input.selected().requireCurrent();
        input.selected().requireLoadedClasses(input.plan());
    }

    private Sources captureSources() throws IOException {
        var selected = input.selected();
        selected.javaSource(LOCAL_SERVICE, RootDriverProductSourcesFactory.class);
        selected.javaSource(LOCAL_SERVICE, RootDriverRegistryPublicProducts.class);
        selected.javaSource(NATIVE_TRANSPORT, DriverRegistryService.class);
        selected.javaSource(NATIVE_TRANSPORT, NativePrelaunchInputs.class);
        selected.javaSource(NATIVE_TRANSPORT, OriginalDriverQueryHistorySettings.class);
        selected.javaSource(LOCAL_SERVICE, RootOperatorCharacterAuthority.class);
        selected.javaSource(LOCAL_SERVICE, RootSetPlayedCharacterRuntime.class);
        selected.javaSourceAt("wave2-events/src/main/java/org/xar/ck3/control/wave2/events/catalog/VanillaEventCatalog.java", VanillaEventCatalog.class);
        selected.javaTarget("wave2-events/src/main/java/org/xar/ck3/control/wave2/events/catalog/VanillaEventCatalogCodec.java");
        selected.javaTarget("wave2-events/src/main/java/org/xar/ck3/control/wave2/events/catalog/VanillaEventCatalogSourceFacts.java");
        var java = new JavaProducts(selected.javaSource(LOCAL_SERVICE, RootDriverGovernancePublicSupplier.class),
                selected.javaSource(LOCAL_SERVICE, RootDriverFactionPublicSupplier.class),
                selected.javaSource(LOCAL_SERVICE, RootDriverHeirPublicSupplier.class),
                selected.javaSource(LOCAL_SERVICE, RootDriverLifecycleRuntimeInstaller.class),
                selected.javaSource(LOCAL_SERVICE, RootDriverTransportRuntimeFactory.class),
                selected.javaSource(LOCAL_SERVICE, RootDriverFamilyPublicProduct.class),
                selected.javaSource(LOCAL_SERVICE, RootGrantTitlePublicProducts.class),
                selected.javaSource(LOCAL_SERVICE, RootTitleClaimsRuntime.class),
                selected.javaSource(LOCAL_SERVICE, RootCashObservationPublicProducts.class),
                selected.javaSource(LOCAL_SERVICE, RootSaveArtifactPublicProducts.class),
                selected.javaSource(LOCAL_SERVICE, RootEngineDiagnosticsPublicProducts.class),
                selected.javaSource(LOCAL_SERVICE, RootNormalExitRuntime.class));
        var publicGov = selected.javaSource(LOCAL_SERVICE, RootDriverGovernancePublicService.class);
        if (!input.nativeGovernance().publicCallerProducer().orElseThrow(() ->
                new IOException("actual native governance has no source-bound public caller producer")).equals(publicGov))
            throw new IOException("public Council and native preparation use different actual caller sources");
        var govReads = new DriverGovernanceReadDefinitions.Sources(
                input.inputs().source(RootRuntimeDefinitionModel.SourceRole.NATIVE_GOV_COUNCIL),
                input.originals().source(RootRuntimeNativeOriginals.Role.GOVERNMENT_BINDER),
                selected.javaSource(LOCAL_SERVICE, DriverGovernanceReadDefinitions.class));
        var transport = new RootDriverTransportRuntimeFactory.Sources(
                input.originals().source(RootRuntimeNativeOriginals.Role.NATIVE_DISPATCHER),
                selected.javaSource(NATIVE_TRANSPORT, ArmyObserverSampling.class), java.transport(),
                List.of(nativeCut("ck3_autonomous_player/native_bridge/include/xar_bridge/army_observer_research_control_12004.hpp")),
                selected.javaSource(APPLICATION, DriverReadHistoryRichMaterial.class));
        var title = new TitleSources(selected.javaSource(NATIVE_TRANSPORT, InteractionTitleSelectorReads.class),
                selected.javaSource(NATIVE_TRANSPORT, InteractionReads.class),
                selected.javaSource(NATIVE_TRANSPORT, TitleClaimsPublicCodec.class), java.titleClaims());
        if (!title.decoder().equals(input.inputs().source(RootRuntimeDefinitionModel.SourceRole.INTERACTION_READ_DECODER)))
            throw new IOException("title selectors replaced the actual Known Interaction decoder source");
        selected.javaSource(LOCAL_SERVICE, CashObservationPublicCodec.class);
        var cash = new CashObservationReads.Sources(selected.javaSource(LOCAL_SERVICE, CashObservationReads.class),
                selected.javaSource(LOCAL_SERVICE, CashObservationCodec.class));
        var normalExit = input.settings().configuration().normalExit().input();
        NormalExitSourceInventory.inspect(normalExit);
        var lifecycle = lifecycleSources();
        return new Sources(java,
                input.originals().source(RootRuntimeNativeOriginals.Role.CACHED_SUCCESSION_MAILBOX),
                selected.javaSource(NATIVE_TRANSPORT, CachedSuccessionService.class), govReads, publicGov,
                lifecycle, transport, title, cash, normalExit,
                selected.javaSource(NATIVE_TRANSPORT, GrantPickerControlEffects.class),
                selected.javaSource(NATIVE_TRANSPORT, GrantTitleCodec.class));
    }

    private RootDriverLifecycleRuntimeInstaller.Sources lifecycleSources() throws IOException {
        var selected = input.selected();
        return new RootDriverLifecycleRuntimeInstaller.Sources(
                selected.javaSource(LOCAL_SERVICE, RootPendingUiRuntime.class),
                selected.javaSource(LOCAL_SERVICE, org.xar.ck3.control.service.root.RootDriverLifecyclePublicSupplier.class),
                selected.javaSource(LOCAL_SERVICE, org.xar.ck3.control.service.root.RootDriverLifecyclePublicCodec.class),
                selected.javaSource(APPLICATION, org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.class),
                selected.javaSource(APPLICATION, org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec.class),
                selected.javaSource(APPLICATION, org.xar.ck3.control.application.lifecycle.SuccessorUiObligationReducer.class),
                selected.javaSource(APPLICATION, org.xar.ck3.control.application.driver.DriverPendingEpisodeSource.class),
                selected.javaSource(APPLICATION, org.xar.ck3.control.application.driver.DriverPendingEpisodeProjection.class),
                selected.javaTarget("application/src/main/java/org/xar/ck3/control/application/driver/DriverPendingEpisodeProducer.java"),
                selected.javaSource(LOCAL_SERVICE, org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.class),
                input.lifecycle().sources().timelineDefinition(), input.lifecycle().sources().closeDefinition());
    }

    private boolean semanticReadSelected() throws IOException {
        var original = input.registration().original();
        var raw = RootRuntimeDefinitions.read(new FileRef(original.path(), original.bytes(), original.sha256()),
                RootSelectedRegistrationConfiguration.MAXIMUM_BYTES);
        if (!RootSelectedRegistrationConfiguration.decode(raw).equals(input.registration().configuration()))
            throw new IOException("selected registration differs from its actual bound original");
        var row = StrictJson.parse(raw, RootSelectedRegistrationConfiguration.MAXIMUM_BYTES);
        var flag = row.path("registration_attributes").get(
                RootSelectedRegistrationConfiguration.RegistrationFlag.SEMANTIC_SNAPSHOT_READONLY.wire());
        if (flag == null || !flag.isBoolean()) throw new IOException("explicit actual semantic read registration boolean required");
        return flag.booleanValue();
    }

    /** A fixed repository role is selected only from the identical qualified complete native review. */
    private ExactRef nativeCut(String repositoryRelative) throws IOException {
        String suffix = "/" + repositoryRelative;
        var matches = input.plan().sources().nativeProof().expected().completeSources().stream()
                .filter(ref -> ref.path().replace('\\', '/').endsWith(suffix)).toList();
        if (matches.size() != 1) throw new IOException("actual native review lacks one unambiguous source role: " + repositoryRelative);
        var actual = matches.get(0);
        return input.selected().original(actual, RootRuntimeSelectedSources.OriginalKind.NATIVE_HEADER);
    }

    private static ProductSource product(Class<?> implementation, ExactRef source) {
        return new ProductSource(implementation, "local-service/src/main/java/" + implementation.getName().replace('.', '/') + ".java", source);
    }
    private static void needSource(ExactRef source) {
        Objects.requireNonNull(source);
        StrictJson.require(source.bytes() > 0 && Path.of(source.path()).isAbsolute(), "actual exact source required");
    }
}
