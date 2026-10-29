package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.session.AutoFailureDiagnostic;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.evidence.PortableEvidenceJson;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts.Query;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.evidence.PortableEvidenceReader;
import org.xar.ck3.control.service.events.PortableEvidenceMethods;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

/** Concrete current-Root public assembly. Missing original callables stop before host installation. */
public final class RootRuntimePublicCatalog {
    private static final Set<String> OFFLINE_NAMES=Set.of("ck3_query_vanilla_event_knowledge_v1","ck3_list_vanilla_event_knowledge_v1",
            "ck3_query_vanilla_event_source_provenance_v1","ck3_list_vanilla_event_evidence_v1","ck3_read_vanilla_event_evidence_v1");
    private static final Set<String> AUB_NAMES=Set.of("ck3_query_aub_business_state_v1","ck3_query_aub_policy_options_v1",
            "ck3_select_aub_policy_option_v1","ck3_confirm_aub_policy_v1");
    public record OfflineImplementationSources(ExactRef knowledge, ExactRef discovery, ExactRef provenance, ExactRef evidence) {
        public OfflineImplementationSources { for (var source : List.of(knowledge, discovery, provenance, evidence)) exact(source); }
    }
    public static final class OfflineEvents {
        private final RootPublicCatalogCodec.PublicCatalog originals;
        private final PortableEvidenceReader reader;
        private final VanillaEventKnowledgeMethods knowledge;
        private final EventDiscoveryPublicService discovery;
        private final EventSourceProvenanceService provenance;
        private final PortableEvidenceMethods evidence;
        private final OfflineImplementationSources sources;
        private OfflineEvents(RootPublicCatalogCodec.PublicCatalog originals, VanillaEventCatalog fullCatalog,
                RegisteredEventKnowledge policy, PortableEvidenceReader reader, OfflineImplementationSources sources) {
            this.originals=Objects.requireNonNull(originals); this.reader=Objects.requireNonNull(reader); this.sources=Objects.requireNonNull(sources);
            reader.requireManifestSource();
            knowledge=new VanillaEventKnowledgeMethods(Objects.requireNonNull(fullCatalog),tool(originals,VanillaEventKnowledgeMethods.NAME));
            discovery=EventDiscoveryPublicService.fromOriginalDescriptor(fullCatalog,reader::portableEventKeys,tool(originals,"ck3_list_vanilla_event_knowledge_v1"));
            provenance=new EventSourceProvenanceService(Objects.requireNonNull(policy)); evidence=new PortableEvidenceMethods(reader);
            StrictJson.require(knowledge.catalog()==discovery.catalog(),"one actual complete catalog instance required");
        }
        public VanillaEventKnowledgeMethods knowledge(){return knowledge;}
        public EventDiscoveryPublicService discovery(){return discovery;}
        public PortableEvidenceReader reader(){return reader;}
        public List<McpExecutableDirectory.DirectBinding<?, ?>> actualMethods() {
            var methods = new ArrayList<McpExecutableDirectory.DirectBinding<?, ?>>();
            methods.addAll(knowledge.actualMethods(sources.knowledge())); methods.addAll(discovery.actualMethods(sources.discovery()));
            methods.add(provenance.actualMethod(sources.provenance())); methods.addAll(evidence.actualMethods(sources.evidence()));
            return List.copyOf(methods);
        }
    }
    /** The concrete startup helper constructs all five offline tools from the same complete provider and pinned reader. */
    public static OfflineEvents offlineEvents(RootPublicCatalogCodec.PublicCatalog originals,
            VanillaEventCatalog fullCatalog, RegisteredEventKnowledge policyKnowledge, PortableEvidenceReader actualPinnedReader,
            OfflineImplementationSources actualImplementations) {
        Objects.requireNonNull(originals); Objects.requireNonNull(fullCatalog); Objects.requireNonNull(policyKnowledge);
        Objects.requireNonNull(actualPinnedReader); actualPinnedReader.requireManifestSource();
        return new OfflineEvents(originals,fullCatalog,policyKnowledge,actualPinnedReader,actualImplementations);
    }
    public static OfflineImplementationSources offlineSources(RootRuntimeDefinitions.Inputs inputs) throws IOException {
        return new OfflineImplementationSources(
                selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/VanillaEventKnowledgeMethods.java"),
                selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/EventDiscoveryPublicService.java"),
                selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/EventSourceProvenanceService.java"),
                selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/events/PortableEvidenceMethods.java"));
    }
    public record Diagnostic(AutoFailureDiagnostic.Port actual, ExactRef implementation) {
        public Diagnostic { Objects.requireNonNull(actual); exact(implementation); }
    }
    /** Already constructed typed methods, never configuration callbacks or inventory-only declarations. */
    public record HandlerProducts(PublicBindings actualServices,
            List<McpExecutableDirectory.DirectBinding<?, ?>> direct, List<Diagnostic> diagnostics, Optional<OfflineEvents> offline,
            Optional<RootSelectedRegistrationConfiguration.Bound> configuration) {
        public HandlerProducts {
            Objects.requireNonNull(actualServices); direct = List.copyOf(direct); diagnostics = List.copyOf(diagnostics);
            Objects.requireNonNull(offline);Objects.requireNonNull(configuration);
            StrictJson.require(direct.stream().noneMatch(value -> OFFLINE_NAMES.contains(value.name())),"offline methods require the actual shared catalog/reader product, not an unrelated direct handler");
            StrictJson.require(!actualServices.frozen(), "actual service registry must still accept the concrete Root adapters");
        }
        public List<McpExecutableDirectory.DirectBinding<?,?>> actualDirect(){
            var result=new ArrayList<>(direct); offline.ifPresent(value->result.addAll(value.actualMethods())); return List.copyOf(result);
        }
    }
    public record ImplementationSources(ExactRef autoTurn, ExactRef capabilities, ExactRef snapshot,
            ExactRef activity, ExactRef currentArmy, ExactRef eventOption, ExactRef sway, ExactRef coreFrame, ExactRef marriage,
            ExactRef interactions,ExactRef lifecycle,ExactRef aub,ExactRef checkpoint,ExactRef bridgeDiagnostics,ExactRef diagnosticSupplements) {
        public ImplementationSources { for (ExactRef source : List.of(autoTurn, capabilities, snapshot, activity, currentArmy, eventOption, sway, coreFrame, marriage,interactions,lifecycle,aub,checkpoint,bridgeDiagnostics,diagnosticSupplements)) exact(source); }
    }
    public record OriginalFiles(FileRef catalog, FileRef admission, FileRef tools, FileRef resources) {
        public OriginalFiles {
            originalFile(catalog,DataRole.MCP_CATALOG);originalFile(admission,DataRole.MCP_ADMISSION);
            originalFile(tools,DataRole.MCP_TOOLS);originalFile(resources,DataRole.MCP_RESOURCES);
        }
        public void verify() throws IOException { for (FileRef file : List.of(catalog, admission, tools, resources)) file.verify(); }
    }
    public record Sources(RootApplicationConfiguration application, RootPublicCatalogCodec.PublicCatalog original,
            OriginalFiles originalFiles, FileRef portableManifest, ImplementationSources implementations, PublicInputs policy,
            HandlerProducts handlers, List<SelectedSource> actualSourceIndex,RootRuntimeDefinitions.Inputs actualInputs) {
        public Sources {
            Objects.requireNonNull(application); Objects.requireNonNull(original); Objects.requireNonNull(originalFiles);
            Objects.requireNonNull(implementations); Objects.requireNonNull(policy); Objects.requireNonNull(handlers);
            Objects.requireNonNull(actualInputs);StrictJson.require(application==actualInputs.application(),"public configuration must retain its actual shared Inputs application");
            requireManifest(portableManifest);
            handlers.offline().ifPresent(value->{
                StrictJson.require(RootPublicCatalogCodec.equivalent(value.originals,original),"offline helpers use another original public catalog");
                StrictJson.require(value.reader().requireManifestSource().equals(exactFile(portableManifest)),"offline reader manifest differs from the actual mandatory SDK input");
            });
            actualSourceIndex = List.copyOf(actualSourceIndex);
            RootPublicCatalogCodec.executableTools(original); // Schema drift must fail before Native or registry mutation.
            StrictJson.require(application.mode() == HostMode.COMPLETE_MIGRATION, "only the actual complete-migration manifest can install public Root authority");
            StrictJson.require(policy.observationTimeoutMs() <= 120000 && policy.autoTimeoutMs() <= 1800000,
                    "configured public deadlines exceed the actual adapter bounds");
            Set<ExactRef> selected = actualSourceIndex.stream().map(SelectedSource::sourceRef)
                    .collect(java.util.stream.Collectors.toUnmodifiableSet());
            for (ExactRef source : List.of(implementations.autoTurn(), implementations.capabilities(), implementations.snapshot(),
                    implementations.activity(), implementations.currentArmy(), implementations.eventOption(), implementations.sway(), implementations.coreFrame(), implementations.marriage(),implementations.interactions(),implementations.lifecycle(),implementations.aub(),implementations.checkpoint(),implementations.bridgeDiagnostics(),implementations.diagnosticSupplements()))
                StrictJson.require(selected.contains(source), "Root public implementation is outside the actual single-winner source graph");
            for (var binding : handlers.actualDirect()) StrictJson.require(selected.contains(binding.target().implementationSource()),
                    "actual direct public method source is outside the selected graph");
            for (var diagnostic : handlers.diagnostics()) StrictJson.require(selected.contains(diagnostic.implementation()),
                    "actual public diagnostic source is outside the selected graph");
            for (var info : handlers.actualServices().inventory()) if (info.target().isPresent())
                StrictJson.require(selected.contains(info.target().orElseThrow().implementationSource()), "actual service method source is outside the selected graph");
        }

        public static Sources read(RootRuntimeDefinitions.Inputs inputs, HandlerProducts actualTypedHandlers) throws IOException {
            Objects.requireNonNull(inputs); Objects.requireNonNull(actualTypedHandlers);
            var files = new OriginalFiles(inputs.data(DataRole.MCP_CATALOG), inputs.data(DataRole.MCP_ADMISSION),
                    inputs.data(DataRole.MCP_TOOLS), inputs.data(DataRole.MCP_RESOURCES));
            var original = RootPublicCatalogCodec.decode(new RootPublicCatalogCodec.Documents(readExact(files.catalog()),
                    readExact(files.admission()), readExact(files.tools()), readExact(files.resources())));
            var implementations = new ImplementationSources(inputs.source(SourceRole.PUBLIC_AUTO_TURN),
                    inputs.source(SourceRole.PUBLIC_CAPABILITIES), inputs.source(SourceRole.PUBLIC_SNAPSHOT),
                    inputs.source(SourceRole.PUBLIC_ACTIVITY), inputs.source(SourceRole.PUBLIC_CURRENT_ARMY),
                    selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/root/EventOptionPublicDispatcher.java"),
                    selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/RootMcpSway.java"),
                    selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/RootMcpCoreFrame.java"),
                    selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/RootMcpMarriage.java"),
                    selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/RootMcpInteractions.java"),
                    selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/RootMcpLifecycle.java"),
                    selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/RootMcpAubOperations.java"),
                    selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/RootMcpCheckpoint.java"),
                    selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/mcp/RootMcpBridgeDiagnostics.java"),
                    selected(inputs, "local-service/src/main/java/org/xar/ck3/control/service/root/RootPublicDiagnosticSupplements.java"));
            return new Sources(inputs.application(), original, files, inputs.data(DataRole.PORTABLE_EVENT_EVIDENCE_MANIFEST),implementations, inputs.configuration().publicCatalog(),
                    actualTypedHandlers, inputs.sourceIndex(),inputs);
        }
        public static RootPublicCatalogCodec.PublicCatalog readOriginals(RootRuntimeDefinitions.Inputs inputs) throws IOException {
            return RootPublicCatalogCodec.decode(new RootPublicCatalogCodec.Documents(readExact(inputs.data(DataRole.MCP_CATALOG)),
                    readExact(inputs.data(DataRole.MCP_ADMISSION)), readExact(inputs.data(DataRole.MCP_TOOLS)), readExact(inputs.data(DataRole.MCP_RESOURCES))));
        }
    }
    public static PortableEvidenceReader evidenceReader(RootRuntimeDefinitions.Inputs inputs)throws IOException {
        FileRef manifest=inputs.data(DataRole.PORTABLE_EVENT_EVIDENCE_MANIFEST);requireManifest(manifest);manifest.verify();
        return new PortableEvidenceReader(exactFile(manifest));
    }
    public record DefinitionGap(String identity, String reason) {
        public DefinitionGap { StrictJson.text(identity); StrictJson.text(reason); }
    }
    public static final class Incomplete extends IOException {
        private static final long serialVersionUID = 1L;
        private final List<DefinitionGap> missing;
        public Incomplete(List<DefinitionGap> missing) {
            super("INCOMPLETE_ROOT_PUBLIC_CATALOG: " + List.copyOf(missing)); this.missing = List.copyOf(missing);
            StrictJson.require(!this.missing.isEmpty(), "public incompleteness requires exact missing identities");
        }
        public List<DefinitionGap> missing() { return missing; }
    }
    private static final Set<PublicMethod> FACTORY_SERVICES = Set.of(PublicMethod.AUTO_TURN, PublicMethod.CAPABILITIES,
            PublicMethod.SNAPSHOT, PublicMethod.SELECT_EVENT_OPTION, PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1,
            PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1, PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1,
            PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, PublicMethod.QUERY_BATTLE_TRANSITION_V1,
            PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1, PublicMethod.PREVIEW_ACTIVE_COMBAT_RETREAT_V1,
            PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1, PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1,
            PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1, PublicMethod.QUERY_PLAYER_MERCENARY_CONTEXT_V1,
            PublicMethod.QUERY_ARMY_COMMANDER_CANDIDATES_V1, PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1,
            PublicMethod.FINISH_ACTIVE_SCHEME_SWAY_PRIVATE_V1,
            PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_COMPLETION_EXECUTION_PRIVATE_V1,
            PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_COMPLETION_TERMINATION_PRIVATE_V1,
            PublicMethod.QUERY_CORE_FRAME_V1, PublicMethod.QUERY_ARRANGE_MARRIAGE_CHOICES,
            PublicMethod.REPLY_PENDING_CHARACTER_INTERACTION,PublicMethod.ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION,
            PublicMethod.ONE_LIFE_SETTLEMENT,PublicMethod.SETTLE_ONE_LIFE,PublicMethod.SAVE_CHECKPOINT,PublicMethod.BRIDGE_DIAGNOSTICS,
            PublicMethod.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1,PublicMethod.QUERY_CHARACTER_INTERACTION_ORDINARY_V1,
            PublicMethod.INITIATE_CHARACTER_INTERACTION_ORDINARY_V1);
    private static final List<Query> ACTIVITY = List.of(Query.START_INPUTS, Query.HOSTED, Query.FULL_COST,
            Query.GUEST_CANDIDATE, Query.GUEST_OPINION, Query.GUEST_TARGET, Query.GUEST_ROUTE_PROOF, Query.GUEST_RULE_PROVENANCE);
    private final Sources sources;
    private final Clock clock;
    private boolean attempted;
    public RootRuntimePublicCatalog(Sources sources, Clock clock) { this.sources = Objects.requireNonNull(sources); this.clock = Objects.requireNonNull(clock); }

    /** Called by the named startup before Native launch. This examines real typed method products. */
    public List<DefinitionGap> missingDefinitions() {
        Set<String> exclusions=Set.of();var configurationGaps=new ArrayList<DefinitionGap>();
        if(sources.handlers().configuration().isPresent())try {
            exclusions=configurationExclusions(sources.actualInputs(),sources.original(),sources.handlers().configuration().orElseThrow());
        }catch(IOException|IllegalArgumentException invalid){configurationGaps.add(new DefinitionGap("selected_registration_configuration",invalid.getMessage()==null?invalid.getClass().getName():invalid.getMessage()));}
        var missing = new ArrayList<>(definitionGaps(sources.original(), sources.handlers(),exclusions));missing.addAll(configurationGaps);
        if(sources.handlers().offline().isPresent()) {
            try {sources.handlers().offline().orElseThrow().reader().manifest();}
            catch(IOException unavailable){
                for(String name:List.of("ck3_list_vanilla_event_evidence_v1","ck3_read_vanilla_event_evidence_v1"))
                    missing.add(new DefinitionGap(name,"actual pinned portable manifest/blob closure unavailable: "+unavailable.getMessage()));
            }
        }
        for (PublicMethod method : sources.policy().requiredServices())
            if (sources.handlers().actualServices().lookup(method).isEmpty()
                    && missing.stream().noneMatch(value -> value.identity().equals(method.pythonName())))
                missing.add(new DefinitionGap(method.pythonName(), "configured required actual service handler is missing"));
        return List.copyOf(missing);
    }
    public static List<DefinitionGap> definitionGaps(RootPublicCatalogCodec.PublicCatalog original, HandlerProducts handlers) {
        return definitionGaps(original,handlers,Set.of());
    }
    /** A source-only label cannot use this path; the private-issued product retains the same actual Inputs and selection. */
    public static Set<String> configurationExclusions(RootRuntimeDefinitions.Inputs actualInputs,
            RootPublicCatalogCodec.PublicCatalog original,RootSelectedRegistrationConfiguration.Bound configuration)throws IOException {
        Objects.requireNonNull(actualInputs);Objects.requireNonNull(original);Objects.requireNonNull(configuration);
        configuration.requireInputs(actualInputs);
        List<String> registered=original.tools().stream().map(PublicMcpDirectory.ToolDescriptor::name).toList();
        var accepted=new HashSet<String>();
        for(var decision:original.admission())if(decision.admission()==McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION) {
            var declaration=original.catalog().declarations().stream().filter(value->value.name().equals(decision.name())).findFirst().orElseThrow();
            StrictJson.require(!declaration.conditions().isEmpty(),"unconditional original method cannot be excluded");
            var evidence=configuration.exclusion(declaration,registered);
            if(evidence.isEmpty())continue;
            evidence.orElseThrow().require(configuration,declaration,registered);
            StrictJson.require(configuration.original().equals(decision.actualAdmissionProducer()),"configuration exclusion producer differs from the actual qualified input");
            accepted.add(decision.name());
        }
        configuration.requireInputs(actualInputs);return Set.copyOf(accepted);
    }
    private static List<DefinitionGap> definitionGaps(RootPublicCatalogCodec.PublicCatalog original, HandlerProducts handlers,Set<String> configurationExclusions) {
        Objects.requireNonNull(original); Objects.requireNonNull(handlers);
        var missing = new ArrayList<DefinitionGap>();
        Set<String> direct = new HashSet<>();
        for (var binding : handlers.actualDirect()) StrictJson.require(direct.add(binding.name()), "duplicate actual direct public method");
        Set<String> names = original.catalog().declarations().stream().map(McpCoverage.Declaration::name)
                .collect(java.util.stream.Collectors.toUnmodifiableSet());
        StrictJson.require(names.containsAll(direct), "actual public direct method is outside the original declaration catalog");
        Set<String> descriptors = original.tools().stream().map(PublicMcpDirectory.ToolDescriptor::name)
                .collect(java.util.stream.Collectors.toUnmodifiableSet());
        for (var decision : original.admission()) {
            if (decision.admission() == McpCoverage.Admission.UNMIGRATED) {
                missing.add(new DefinitionGap(decision.name(), "original operation has no complete migration admission")); continue;
            }
            if (decision.admission() == McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION) {
                if(!configurationExclusions.contains(decision.name()))missing.add(new DefinitionGap(decision.name(), "conditional exclusion requires its actual Java configuration producer; source metadata alone is insufficient"));
                continue;
            }
            if (decision.admission() == McpCoverage.Admission.RETIRED) {
                try {
                    if (!PublicMcpNativeAdapter.expectedServiceMethod(decision.name()).retired())
                        missing.add(new DefinitionGap(decision.name(), "original method has no source-owned retirement"));
                } catch (IllegalArgumentException notService) {
                    missing.add(new DefinitionGap(decision.name(), "direct method has no source-owned retirement producer"));
                }
                continue;
            }
            if (decision.admission() != McpCoverage.Admission.ADMITTED) continue;
            if (!descriptors.contains(decision.name())) missing.add(new DefinitionGap(decision.name(), "actual original descriptor is missing"));
            PublicMethod method;
            try { method = PublicMcpNativeAdapter.expectedServiceMethod(decision.name()); }
            catch (IllegalArgumentException notService) {
                if (!direct.contains(decision.name())) missing.add(new DefinitionGap(decision.name(), "actual typed direct method is missing"));
                continue;
            }
            boolean installed = handlers.actualServices().lookup(method).isPresent();
            if (installed && direct.contains(decision.name())) missing.add(new DefinitionGap(decision.name(), "same original identity has service and direct handlers"));
            // The executable directory permits an actual driver-direct method even when a vocabulary enum also exists.
            if (handlers.actualServices().lookup(method).isEmpty() && !direct.contains(decision.name()))
                missing.add(new DefinitionGap(decision.name(), "actual typed service handler is missing"));
        }
        return List.copyOf(missing);
    }
    public void requireCompleteDefinitions() throws Incomplete { var missing = missingDefinitions(); if (!missing.isEmpty()) throw new Incomplete(missing); }

    public synchronized McpExecutableDirectory.Complete install(RootApplicationAssembly.Core core,
            RootRuntimeCatalogFactory catalogs, PublicMcpHost host) throws IOException, InterruptedException {
        requireInstallInputs(core,catalogs,host);
        var current=core.sessionAccess().current();catalogs.requireCurrentCatalog(current.identity());
        return installDirectory(core,catalogs,host);
    }
    /** Same once-only executable directory before a gameplay Root exists; the real menu keeps its guards. */
    public synchronized McpExecutableDirectory.Complete installFrontend(RootApplicationAssembly.Core core,
            RootRuntimeCatalogFactory catalogs,RootInstalledCatalog actualBeforeGame,PublicMcpHost host)
            throws IOException,InterruptedException {
        requireInstallInputs(core,catalogs,host);Objects.requireNonNull(actualBeforeGame);
        actualBeforeGame.context().withSession(same->{
            requireSameFrontend(core,catalogs,actualBeforeGame);return actualBeforeGame;
        });
        var installed=installDirectory(core,catalogs,host);
        actualBeforeGame.context().withSession(same->{
            requireSameFrontend(core,catalogs,actualBeforeGame);return actualBeforeGame;
        });
        return installed;
    }
    private static void requireSameFrontend(RootApplicationAssembly.Core core,RootRuntimeCatalogFactory catalogs,
            RootInstalledCatalog actual)throws IOException {
        StrictJson.require(actual.context().core()==core&&catalogs.requireFrontendCatalog(core)==actual,
                "frontend public assembly lost its identical retained catalog/Core");
        core.requireFrontendMenu(actual.context());
    }
    private void requireInstallInputs(RootApplicationAssembly.Core core,RootRuntimeCatalogFactory catalogs,PublicMcpHost host)throws IOException {
        Objects.requireNonNull(core);Objects.requireNonNull(catalogs);Objects.requireNonNull(host);
        StrictJson.require(!attempted,"public assembly is entered once; an uncertain attempt cannot reinstall or replace authority");
        requireCompleteDefinitions();
        StrictJson.require(core.configuration().equals(sources.application()),"public catalog belongs to another actual Core configuration");
        sources.application().requireCurrent(clock);sources.originalFiles().verify();sources.portableManifest().verify();
    }
    private McpExecutableDirectory.Complete installDirectory(RootApplicationAssembly.Core core,
            RootRuntimeCatalogFactory catalogs,PublicMcpHost host)throws IOException,InterruptedException {
        attempted = true;
        PublicBindings registry = sources.handlers().actualServices();
        var direct = sources.handlers().actualDirect();
        var required = new HashSet<>(sources.policy().requiredServices()); required.addAll(FACTORY_SERVICES);
        registry.freeze(Set.copyOf(required));
        var result = McpExecutableDirectory.assemble(sources.original().catalog(), sources.original().admission(),
                RootPublicCatalogCodec.executableTools(sources.original()), sources.original().resources(), registry, direct);
        if (result instanceof McpExecutableDirectory.Partial partial)
            throw new Incomplete(partial.missing().stream().map(value -> new DefinitionGap(value.identity(), value.reason().name())).toList());
        var assembled = (McpExecutableDirectory.Complete) result;
        if(sources.handlers().configuration().isPresent())sources.handlers().configuration().orElseThrow().requireInputs(sources.actualInputs());
        var complete = RootOriginalMcpInvocationDirectory.bind(assembled);
        host.install(core.configuration().mode(), complete.directory()); return complete;
    }
    /** Construct actual typed adapters before Core exists. No handler is invoked or host installed. */
    static HandlerProducts bindFactoryHandlers(RootRuntimeDefinitions.Inputs inputs,HandlerProducts handlers,
            RootSessionAccess sessions,RootRuntimeCatalogFactory catalogs,Clock clock)throws IOException {
        Sources sources=Sources.read(inputs,handlers);
        PublicBindings registry = handlers.actualServices();
        StrictJson.require(!registry.frozen(), "actual public registry was frozen by another assembly");
        Duration observationTimeout = Duration.ofMillis(sources.policy().observationTimeoutMs());
        Duration autoTimeout = Duration.ofMillis(sources.policy().autoTimeoutMs());
        var implementation = sources.implementations();
        new RootMcpAutoTurn(sessions, clock, autoTimeout,
                handlers.diagnostics().stream().map(Diagnostic::actual).toList()).register(registry, implementation.autoTurn());
        new RootMcpCapabilities(sessions, clock, observationTimeout).register(registry, implementation.capabilities());
        new RootMcpSnapshot(sessions, clock, observationTimeout).register(registry, implementation.snapshot());
        new RootCurrentArmyPublicServices(sessions, catalogs).install(registry, implementation.currentArmy());
        new EventOptionPublicDispatcher(sessions, root -> catalogs.requireCurrentCatalog(root.identity())
                .remainingDomains().events(), clock, autoTimeout).register(registry, implementation.eventOption());
        new RootMcpSway(sessions, root -> catalogs.requireCurrentCatalog(root.identity())
                .remainingDomains().sway(), clock, autoTimeout).register(registry, implementation.sway());
        new RootMcpCoreFrame(sessions, root -> catalogs.requireCurrentCatalog(root.identity())
                .coreFrame(), clock, observationTimeout).register(registry, implementation.coreFrame());
        new RootMcpMarriage(sessions, root -> catalogs.requireCurrentCatalog(root.identity())
                .remainingDomains().family(), clock, observationTimeout).register(registry, implementation.marriage());
        new RootMcpInteractions(sessions,root->catalogs.requireCurrentCatalog(root.identity()).interactions(),clock,autoTimeout)
                .register(registry,implementation.interactions());
        // The source-qualified lifecycle adapter supplies inspection and actual settlement; NEXT has its separate supplied owner.
        new RootMcpLifecycle(sessions,root->catalogs.requireCurrentCatalog(root.identity()).remainingDomains().lifecycle(),clock,autoTimeout)
                .register(registry,implementation.lifecycle());
        new RootMcpCheckpoint(sessions,root->catalogs.requireCurrentCatalog(root.identity()).save(),clock,autoTimeout)
                .registerSaveOnly(registry,implementation.checkpoint());
        new RootMcpBridgeDiagnostics(sessions,root->catalogs.requireCurrentCatalog(root.identity()).context(),
                new RootPublicDiagnosticSupplements(catalogs,implementation.diagnosticSupplements()),clock,observationTimeout)
                .register(registry,implementation.bridgeDiagnostics());
        var direct = new ArrayList<>(handlers.direct());
        direct.addAll(new RootMcpActivityReads(sessions, catalogs.sources().activityDefinitions(), clock,
                observationTimeout).actualMethods(implementation.activity()));
        direct.addAll(new RootMcpAubOperations(sessions,root->catalogs.requireCurrentCatalog(root.identity()).aub(),clock,observationTimeout)
                .actualMethods(implementation.aub()));
        return new HandlerProducts(registry,direct,handlers.diagnostics(),handlers.offline(),handlers.configuration());
    }
    private static ExactRef selected(RootRuntimeDefinitions.Inputs inputs, String target) throws IOException {
        var matches = inputs.sourceIndex().stream().filter(value -> value.targetRelative().equals(target)).toList();
        if (matches.size() != 1) throw new IOException("INCOMPLETE_ROOT_PUBLIC_CATALOG: exact selected public producer missing: " + target);
        return matches.getFirst().sourceRef();
    }
    private static PublicMcpDirectory.ToolDescriptor tool(RootPublicCatalogCodec.PublicCatalog originals, String name) {
        return originals.tools().stream().filter(value -> value.name().equals(name)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("INCOMPLETE_ROOT_PUBLIC_CATALOG: actual original descriptor is missing: " + name));
    }
    private static RawJson readExact(FileRef ref) throws IOException {
        requireFile(ref); ref.verify(); var witness = SharedSourceFiles.observe(Path.of(ref.path())); byte[] bytes;
        try (var input = Files.newInputStream(Path.of(ref.path()))) { bytes = input.readNBytes(Math.toIntExact(ref.bytes()) + 1); }
        if (bytes.length != ref.bytes()) throw new IOException("actual public runtime document changed while reading");
        SharedSourceFiles.assertUnchanged(witness); ref.verify(); return new RawJson(bytes);
    }
    private static void requireFile(FileRef ref) {
        Objects.requireNonNull(ref); StrictJson.require(ref.bytes() > 0 && ref.bytes() <= RawJson.MAXIMUM_BYTES
                && Path.of(ref.path()).isAbsolute(), "bounded exact actual public runtime file required");
    }
    private static void requireManifest(FileRef file){
        requireFile(file);StrictJson.require(file.bytes()<=PortableEvidenceJson.MANIFEST_LIMIT
                &&Path.of(file.path()).getFileName().toString().equals("manifest_v1.json"),"actual bounded portable manifest input required");
    }
    private static void originalFile(FileRef file,DataRole role){requireFile(file);StrictJson.require(file.bytes()<=RootRuntimeDefinitionModel.maximumDataBytes(role),"public original exceeds its actual SDK role bound");}
    private static ExactRef exactFile(FileRef file){return new ExactRef(file.path(),file.bytes(),file.sha256());}
    private static void exact(ExactRef source) { Objects.requireNonNull(source); StrictJson.require(source.bytes() > 0, "actual public implementation source required"); }
}
