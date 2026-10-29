package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.RootMcpRiteCreation;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;

/** Concrete pre-Core supplied public products. Registration never borrows an invented Root session. */
public final class RootPublicHandlerProductsFactory {
    private RootPublicHandlerProductsFactory() {}

    /** Source-bound ports retained before Core exists; every invocation resolves the committed same Core. */
    public static final class Context {
        private final RootRuntimeDefinitions.Inputs inputs;
        private final RootCoreBoundPorts ports;
        private final RootRuntimeCatalogFactory catalogs;
        private final Clock clock;
        private final RootRuntimeSelectedSources sources;
        private final Optional<RootSelectedRegistrationConfiguration.Bound> selectedConfiguration;
        private final RootRuntimeDomainSettings.Bound planSettings;
        private final Duration observationTimeout;
        private final Duration actionTimeout;

        private Context(RootRuntimeDefinitions.Inputs inputs, RootCoreBoundPorts ports,
                RootRuntimeCatalogFactory catalogs,
                Optional<RootSelectedRegistrationConfiguration.Bound> selectedConfiguration,
                RootRuntimeDomainSettings.Bound samePlanSettings, Clock clock) throws IOException {
            this.inputs = Objects.requireNonNull(inputs);
            this.ports = Objects.requireNonNull(ports);
            this.catalogs = Objects.requireNonNull(catalogs);
            this.clock = Objects.requireNonNull(clock);
            this.selectedConfiguration = Objects.requireNonNull(selectedConfiguration);
            this.planSettings = Objects.requireNonNull(samePlanSettings);
            requirePlanSettings();
            sources = new RootRuntimeSelectedSources(inputs);
            catalogs.bindPublicStepSources(inputs, sources);
            observationTimeout = Duration.ofMillis(inputs.configuration().publicCatalog().observationTimeoutMs());
            actionTimeout = Duration.ofMillis(inputs.configuration().publicCatalog().autoTimeoutMs());
            StrictJson.require(!observationTimeout.isZero() && !observationTimeout.isNegative()
                    && observationTimeout.compareTo(Duration.ofMinutes(2)) <= 0,
                    "finite actual public observation timeout required");
            StrictJson.require(!actionTimeout.isZero() && !actionTimeout.isNegative()
                    && actionTimeout.compareTo(Duration.ofMinutes(30)) <= 0,
                    "finite actual public action timeout required");
        }
        public RootRuntimeDefinitions.Inputs inputs() { return inputs; }
        /** The original typed pre-Core definitions, without constructing replacement domain contracts. */
        public RootRuntimeCatalogFactory.Sources definitions() { return catalogs.sources(); }
        public org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService.Contracts factionContracts() {
            return definitions().finance().factionContracts();
        }
        public Clock clock() { return clock; }
        public Duration observationTimeout() { return observationTimeout; }
        public Duration actionTimeout() { return actionTimeout; }
        /** The same decoded mandatory configuration; these DATA flags confer no private action permission. */
        public RootRuntimeDomainSettings.PlanFlags planningFlags(
                org.xar.ck3.control.application.planning.PlanningRequest actual) throws IOException {
            Objects.requireNonNull(actual);
            var configured = planSettings.configuration().planFlags();
            boolean currentInitial = actual.observations().initialLifestyleFocusRequired();
            if (!configured.initialLifestyleFocusRequired() && currentInitial)
                throw new IOException("current initial-focus requirement contradicts its actual configured original");
            // The immutable profile requests initial focus; its already-existing collector owns consumption.
            return new RootRuntimeDomainSettings.PlanFlags(configured.lifestyleFormalTrial(),
                    configured.factionGiftFormalTrial(), configured.constructionFormalTrial(),
                    configured.familyMarriageFormalTrial(), configured.councilAction(),
                    configured.m5JointCollector(), currentInitial);
        }
        public ExactRef source(Class<?> type) throws IOException {
            return source(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, type);
        }
        public ExactRef source(RootRuntimeSelectedSources.Module module, Class<?> type) throws IOException {
            return sources.javaSource(module, type);
        }
        public ExactRef sourceAt(String actualTarget, Class<?> type) throws IOException {
            return sources.javaSourceAt(actualTarget, type);
        }
        /** Exact original provenance custody only; this does not confer dispatch or Game qualification. */
        public ExactRef original(org.xar.ck3.control.build.ControlBuild.FileRef original,
                RootRuntimeSelectedSources.OriginalKind kind) throws IOException {
            return sources.original(original, kind);
        }
        /** A historical source-DATA role from the same captured original registration closure. */
        public ExactRef originalMcp(org.xar.ck3.control.build.OriginalMcpCapture.OriginalModule module) throws IOException {
            var captured = inputs.originalMcpCapture().sourceSet();
            var selected = captured.get(Objects.requireNonNull(module)).original();
            return original(selected, RootRuntimeSelectedSources.OriginalKind.ORIGINAL_PYTHON);
        }
        @FunctionalInterface
        public interface FrontendWork<T> {
            T run(RootInstalledCatalog installed, RootMenuSession menu,
                    org.xar.ck3.control.application.effects.FrontendAuthority.LeaseSnapshot initial)
                    throws IOException, InterruptedException;
        }
        private record FrontendView(RootInstalledCatalog installed, RootMenuSession menu,
                org.xar.ck3.control.application.effects.FrontendAuthority.LeaseSnapshot initial) { }
        public <T> T withFrontend(FrontendWork<T> work) throws IOException, InterruptedException {
            return withFrontend(clock.instant().plus(observationTimeout), work);
        }
        /** Capture only initial menu DATA under the original read/writer scope. Each subsequent read or action
         * invokes its original independently guarded executor after this read scope and writer lease close. */
        public <T> T withFrontend(Instant deadline, FrontendWork<T> work) throws IOException, InterruptedException {
            Objects.requireNonNull(work); Objects.requireNonNull(deadline);
            var core = ports.requireCore();
            if (!core.configuration().equals(inputs.application()) || core.archive().writer() != core.writer()
                    || !deadline.isAfter(clock.instant()) || deadline.isAfter(inputs.application().reviewAt()))
                throw new IOException("frontend public invocation lost its actual Core/writer or finite deadline");
            FrontendView view = core.writer().locked(same -> {
                var installed = catalogs.requireFrontendCatalog(core);
                var menu = core.requireFrontendMenu(installed.context());
                if (installed.context().core() != core || installed.context().writer() != core.writer()
                        || installed.frontend() != installed.context().frontend()
                        || menu.bindings != installed.bindings() || menu.frontend != installed.frontend().authority())
                    throw new IOException("frontend public invocation crossed its identical installed menu/context");
                var initial = installed.frontend().withSourceBoundFrontendRead(same,
                        org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission.FrameMode.MENU,
                        deadline, actual -> actual);
                if (!initial.source().equals(installed.context().source())
                        || !initial.identity().game().equals(installed.context().game().generation())
                        || !initial.identity().machineId().equals(installed.context().game().machineId()))
                    throw new IOException("initial frontend DATA differs from the retained actual physical menu");
                return new FrontendView(installed, menu, initial);
            });
            view.installed().frontend().authority().requireOutsideSourceBoundFrontendRead();
            return work.run(view.installed(), view.menu(), view.initial());
        }
        /** Actual admitted/menu phase; no exception-based fallback, Native probe, or invented Root. */
        public <T> T withActualView(RootSessionAccess.Work<T> gameplay, FrontendWork<T> frontend)
                throws IOException, InterruptedException {
            Objects.requireNonNull(gameplay); Objects.requireNonNull(frontend);
            return switch (actualPublicPhase()) {
                case FRONTEND -> withFrontend(frontend);
                case GAMEPLAY -> withCurrent(gameplay);
            };
        }
        private RootMenuSession.PublicPhase actualPublicPhase() throws IOException {
            var core = ports.requireCore();
            if (!core.configuration().equals(inputs.application()) || core.archive().writer() != core.writer())
                throw new IOException("public phase belongs to another actual Core/writer");
            return core.writer().locked(same -> {
                var installed = catalogs.requireFrontendCatalog(core);
                return core.requireFrontendMenu(installed.context()).publicPhase();
            });
        }
        @FunctionalInterface
        public interface FrontendReadWork<T> {
            T run(RootInstalledCatalog installed, RootMenuSession menu,
                    org.xar.ck3.control.application.effects.FrontendAuthority.LeaseSnapshot actual)
                    throws IOException;
        }
        public <T> T withActualReadView(Instant deadline, RootSessionAccess.Work<T> gameplay,
                FrontendReadWork<T> frontend) throws IOException, InterruptedException {
            Objects.requireNonNull(deadline); Objects.requireNonNull(gameplay); Objects.requireNonNull(frontend);
            return switch (actualPublicPhase()) {
                case FRONTEND -> withFrontendRead(deadline, frontend);
                case GAMEPLAY -> withCurrent(gameplay);
            };
        }
        /** Pure reads retain one actual outer source-bound capture. Original Menu.read re-enters this same scope.
         * The authority rejects mutation while it is held; SET/START must use withFrontend instead. */
        public <T> T withFrontendRead(Instant deadline, FrontendReadWork<T> work) throws IOException {
            Objects.requireNonNull(work); Objects.requireNonNull(deadline);
            var core = ports.requireCore();
            if (!core.configuration().equals(inputs.application()) || core.archive().writer() != core.writer()
                    || !deadline.isAfter(clock.instant()) || deadline.isAfter(inputs.application().reviewAt()))
                throw new IOException("frontend read lost its actual Core/writer or finite deadline");
            return core.writer().locked(same -> {
                var installed = catalogs.requireFrontendCatalog(core);
                var menu = core.requireFrontendMenu(installed.context());
                if (menu.publicPhase() != RootMenuSession.PublicPhase.FRONTEND)
                    throw new IOException("frontend read cannot reuse an admitted gameplay menu");
                return installed.frontend().withSourceBoundFrontendRead(same,
                        org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission.FrameMode.MENU,
                        deadline, actual -> work.run(installed, menu, actual));
            });
        }
        public RootSaveArtifactPublicProducts.Prepared saveArtifacts() {
            return definitions().additionalDomains().driverRegistry().saveArtifacts();
        }
        @FunctionalInterface
        public interface InstalledDataWork<T> {
            T run(RootInstalledCatalog installed,
                    org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) throws IOException;
        }
        /** Passive installed DATA under the original writer and physical ownership, with no fresh Native frame. */
        public <T> T withInstalledData(Instant deadline, InstalledDataWork<T> work) throws IOException {
            Objects.requireNonNull(deadline); Objects.requireNonNull(work);
            var core = ports.requireCore();
            if (!core.configuration().equals(inputs.application()) || core.archive().writer() != core.writer()
                    || !deadline.isAfter(clock.instant()) || deadline.isAfter(inputs.application().reviewAt()))
                throw new IOException("installed public DATA lost its actual Core/writer or finite deadline");
            return core.writer().locked(same -> {
                var installed = catalogs.requireFrontendCatalog(core);
                core.requireFrontendMenu(installed.context());
                installed.context().requireCurrent(deadline);
                try { return work.run(installed, same); }
                finally { installed.context().requireCurrent(deadline); }
            });
        }
        public RootEngineDiagnosticsPublicProducts.Prepared engineDiagnostics() {
            return definitions().additionalDomains().driverRegistry().engineDiagnostics();
        }
        /** Same complete pre-Core catalog also supplies the original Unicode TextRules for FS products. */
        public VanillaEventCatalog eventCatalog() throws IOException {
            sourceAt("wave2-events/src/main/java/org/xar/ck3/control/wave2/events/catalog/VanillaEventCatalog.java",
                    VanillaEventCatalog.class);
            return definitions().additionalDomains().driverRegistry().eventCatalog();
        }
        public RootInstalledCatalog installed(RootApplicationSession root) throws IOException {
            Objects.requireNonNull(root);
            var core = ports.requireCore();
            var installed = catalogs.requireCurrentCatalog(root.identity());
            if (installed.context().core() != core || installed.context().actions() != root
                    || !core.configuration().equals(inputs.application()))
                throw new IOException("supplied public product lost its identical current Core/catalog/Root owner");
            return installed;
        }
        /** Called only by a supplied method invocation, after the real Core has been committed. */
        public RootMcpRiteCreation ritePublicServices() throws IOException {
            var core=ports.requireCore();
            if(!core.configuration().equals(inputs.application())||core.archive().writer()!=core.writer())
                throw new IOException("Rite public adapter belongs to another actual Core/writer");
            return new RootMcpRiteCreation(core.sessionAccess(),root->{
                return installed(root).riteCreation();
            },clock,observationTimeout);
        }
        public <T> T withCurrent(RootSessionAccess.Work<T> work) throws IOException, InterruptedException {
            Objects.requireNonNull(work);
            var core = ports.requireCore();
            if (!core.configuration().equals(inputs.application()) || core.archive().writer() != core.writer())
                throw new IOException("supplied public product belongs to another actual Core/writer");
            return core.sessionAccess().withCurrent(root -> {
                installed(root);
                return work.run(root);
            });
        }
        /** Restore remains reachable through the exact private attempt after the old current Root is retired. */
        public RootCheckpointPublicCalls.RestoreCall restoreCheckpointPublic(
                RootCheckpointPublicCalls.Request request, Instant deadline) throws IOException, InterruptedException {
            Objects.requireNonNull(request); Objects.requireNonNull(deadline);
            if (!clock.instant().isBefore(deadline)) throw new IOException("public restore deadline expired before dispatch");
            var core = ports.requireCore();
            if (!core.configuration().equals(inputs.application()) || core.archive().writer() != core.writer())
                throw new IOException("public restore belongs to another actual bound Core/writer");
            var result = core.sessionAccess().restoreCheckpointPublic(request, deadline);
            return result;
        }

        private void requirePlanSettings() throws IOException {
            var actual = inputs.data(RootRuntimeDefinitionModel.DataRole.REMAINING_DOMAIN_SETTINGS);
            var bound = planSettings.original();
            if (!java.nio.file.Path.of(actual.path()).equals(java.nio.file.Path.of(bound.path()))
                    || actual.bytes() != bound.bytes() || !actual.sha256().equals(bound.sha256()))
                throw new IOException("public PLAN settings differ from the identical original SDK DATA role");
        }
        private void requireCurrent() throws IOException {
            requirePlanSettings();
        }
    }

    /** The common registry already holds each contributed service; direct handlers remain strongly typed. */
    public record Contribution(List<McpExecutableDirectory.DirectBinding<?, ?>> direct,
            List<RootRuntimePublicCatalog.Diagnostic> diagnostics,
            List<RootRuntimePublicCatalog.DefinitionGap> gaps) {
        public Contribution {
            direct = List.copyOf(direct);
            diagnostics = List.copyOf(diagnostics);
            gaps = List.copyOf(gaps);
        }
    }

    public static final class Prepared {
        private final Context context;
        private final RootRuntimePublicCatalog.HandlerProducts handlers;
        private final List<RootRuntimePublicCatalog.DefinitionGap> missing;
        private Prepared(Context context, RootRuntimePublicCatalog.HandlerProducts handlers,
                List<RootRuntimePublicCatalog.DefinitionGap> missing) {
            this.context = context;
            this.handlers = handlers;
            this.missing = List.copyOf(missing);
        }
        public RootRuntimePublicCatalog.HandlerProducts handlers() { return handlers; }
        /** The identical Context already prepared for these installed handlers; never a second preparation. */
        public Context currentContext() throws IOException { requireComplete(); return context; }
        public List<RootRuntimePublicCatalog.DefinitionGap> missingDefinitions() { return missing; }
        public void requireComplete() throws IOException {
            context.requireCurrent();
            if (!missing.isEmpty()) throw new RootRuntimePublicCatalog.Incomplete(missing);
        }
        /** Custody check only; neither source selection nor class loading grants Native or Game authority. */
        public void requireLoadedClasses(NativeLaunchPlan sameActualPlan) throws IOException {
            context.sources.requireLoadedClasses(sameActualPlan);
        }
    }

    public static Prepared prepare(RootRuntimeDefinitions.Inputs sameInputs, RootCoreBoundPorts samePorts,
            RootRuntimeCatalogFactory sameCatalogs,
            Optional<RootSelectedRegistrationConfiguration.Bound> selectedConfiguration,
            RootRuntimeDomainSettings.Bound samePlanSettings, Clock clock) throws IOException {
        Objects.requireNonNull(selectedConfiguration);
        Context context = new Context(sameInputs, samePorts, sameCatalogs, selectedConfiguration, samePlanSettings, clock);
        context.source(RootPublicHandlerProductsFactory.class);
        var original = RootRuntimePublicCatalog.Sources.readOriginals(sameInputs);
        PublicBindings registry = new PublicBindings();
        var direct = new ArrayList<McpExecutableDirectory.DirectBinding<?, ?>>();
        var diagnostics = new ArrayList<RootRuntimePublicCatalog.Diagnostic>();
        var gaps = new ArrayList<RootRuntimePublicCatalog.DefinitionGap>();
        List<Contribution> contributions = List.of(
                RootArmySuppliedPublicProducts.install(context, registry),
                RootPrisonerPublicProducts.install(context, registry),
                RootSwaySuppliedPublicProducts.install(context, registry),
                RootContactPublicProducts.install(context, registry),
                RootGovernancePublicProducts.install(context, registry),
                RootCampaignPublicProducts.install(context, registry),
                RootNextEpisodePublicProducts.install(context, registry),
                RootEventWindowPublicProducts.install(context, registry),
                RootFactionAlertPublicProducts.install(context, registry),
                RootRegistryReadPublicProducts.install(context, registry),
                RootWaitForChangePublicProducts.install(context, registry),
                RootRiteCreationPublicProducts.install(context, registry),
                RootMarriageArrangePublicProducts.install(context, registry),
                RootReligionPublicProducts.install(context, registry),
                RootFrontendRulesPublicProducts.install(context, registry),
                RootFrontendCoaPublicProducts.install(context, registry),
                RootChinaCasesPublicProducts.install(context, registry),
                RootChinaCareerPublicProducts.install(context, registry),
                RootGuiPublicProducts.install(context, registry),
                RootDriverRegistryPublicProducts.install(context, registry),
                RootArtifactsPublicProducts.install(context, registry),
                RootRestoreCheckpointPublicProducts.install(context, registry),
                org.xar.ck3.control.service.mcp.RootMcpPlanning.install(context, registry));
        for (Contribution contribution : contributions) {
            direct.addAll(contribution.direct());
            diagnostics.addAll(contribution.diagnostics());
            gaps.addAll(contribution.gaps());
        }
        Optional<RootRuntimePublicCatalog.OfflineEvents> offline;
        try {
            context.sourceAt("wave2-events/src/main/java/org/xar/ck3/control/wave2/events/catalog/VanillaEventCatalog.java",
                    VanillaEventCatalog.class);
            context.sourceAt("wave2-events/src/main/java/org/xar/ck3/control/wave2/events/registered/RegisteredEventKnowledge.java",
                    RegisteredEventKnowledge.class);
            var fullCatalog = context.eventCatalog();
            var policyKnowledge = RegisteredEventKnowledge.load();
            var reader = RootRuntimePublicCatalog.evidenceReader(sameInputs);
            offline = Optional.of(RootRuntimePublicCatalog.offlineEvents(original, fullCatalog, policyKnowledge,
                    reader, RootRuntimePublicCatalog.offlineSources(sameInputs)));
        } catch (IOException unavailable) {
            offline = Optional.empty();
            for (String name : List.of("ck3_query_vanilla_event_knowledge_v1", "ck3_list_vanilla_event_knowledge_v1",
                    "ck3_query_vanilla_event_source_provenance_v1", "ck3_list_vanilla_event_evidence_v1",
                    "ck3_read_vanilla_event_evidence_v1"))
                gaps.add(new RootRuntimePublicCatalog.DefinitionGap(name,
                        "actual complete catalog/policy/pinned evidence product unavailable: " + unavailable.getMessage()));
        }
        var handlers = new RootRuntimePublicCatalog.HandlerProducts(registry, direct, diagnostics, offline,
                selectedConfiguration);
        handlers = RootRuntimePublicCatalog.bindFactoryHandlers(sameInputs,handlers,new RootSessionAccess(samePorts),sameCatalogs,clock);
        var catalog = new RootRuntimePublicCatalog(RootRuntimePublicCatalog.Sources.read(sameInputs, handlers), clock);
        gaps.addAll(catalog.missingDefinitions());
        var unique = new LinkedHashMap<String, RootRuntimePublicCatalog.DefinitionGap>();
        for (var gap : gaps) unique.putIfAbsent(gap.identity() + "\n" + gap.reason(), gap);
        context.requireCurrent();
        return new Prepared(context, handlers, List.copyOf(unique.values()));
    }
}