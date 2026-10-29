package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** One source-pinned original MCP registration capture. No Game query and no Java admission.
 * Run only within the actual Root SharedOwnedCommand execution/capacity window.
 * Five DATA documents are returned to the existing finite bootstrap CREATE_NEW port; this class is not a DATA writer. */
public final class OriginalMcpCapture {
    public static final String PLAN_SCHEMA="xar.original-mcp-java-capture-plan/v1";
    public static final String RESULT_SCHEMA="xar.original-mcp-java-capture-actual/v1";
    public static final String REQUEST_SHA="19af91b87007676d9a4d2eb85cfb3046732f81c4ba07586026e9da8128d04a41";
    public static final long REQUEST_BYTES=53413;
    public static final int DOCUMENT_MAX=16<<20,CONTROL_MAX=1<<20,WIRE_MAX=64<<20;
    /** Current mechanical Java outer reservation; a larger dataset needs a newly qualified memory profile. */
    public static final int CAPTURE_LOGICAL_MAX=8<<20;
    private static final String REQUEST_SCHEMA="xar.original-mcp-root-memory-measurement-request/v2";
    private static final ObjectMapper JSON=JsonMapper.builder(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
        .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(32<<20).maxNestingDepth(128).maxNumberLength(1000).build()).build())
        .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS,DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES,
                DeserializationFeature.FAIL_ON_MISSING_CREATOR_PROPERTIES,DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
        .disable(DeserializationFeature.ACCEPT_FLOAT_AS_INT)
        .disable(com.fasterxml.jackson.databind.MapperFeature.ALLOW_COERCION_OF_SCALARS).build();
    static {
        for(var shape:List.of(com.fasterxml.jackson.databind.cfg.CoercionInputShape.Integer,
                com.fasterxml.jackson.databind.cfg.CoercionInputShape.Float,com.fasterxml.jackson.databind.cfg.CoercionInputShape.Boolean))
            JSON.coercionConfigFor(com.fasterxml.jackson.databind.type.LogicalType.Textual)
                    .setCoercion(shape,com.fasterxml.jackson.databind.cfg.CoercionAction.Fail);
    }
    private OriginalMcpCapture(){ }

    /** Current capture request is data only. Historical Request02 remains the immutable inventory authority. */
    public static final String CURRENT_REQUEST_SCHEMA="xar.original-mcp-java-capture-request/v3";
    public static final String CONFIGURATION_SCHEMA="xar.original-mcp-current-configuration/v4";
    public record RequestBinding(String machineId,FileRef inventoryRequestRef,FileRef selectedConfigurationProducerRef,
            FileRef selectedConfigurationSourceMapRef,FileRef originalFixtureProducerRef) {
        public RequestBinding {
            machine(machineId);
            require(inventoryRequestRef!=null&&inventoryRequestRef.bytes()==REQUEST_BYTES&&inventoryRequestRef.sha256().equals(REQUEST_SHA),"exact historical Request02 inventory required");
            for(var input:List.of(inventoryRequestRef,selectedConfigurationProducerRef,selectedConfigurationSourceMapRef,originalFixtureProducerRef)){
                absolute(input.path());require(input.bytes()>0&&input.bytes()<=CONTROL_MAX,"bounded exact current request source required");
            }
            require(Path.of(selectedConfigurationProducerRef.path()).getFileName().toString().equals("RootSelectedRegistrationConfiguration.java"),"sole selected configuration producer required");
            require(originalFixtureProducerRef.bytes()==322681&&originalFixtureProducerRef.sha256().equals("f25af27d0221260a95b45fc5dcf417d25d733c8dbbdba7be866146643b75f1ee")
                    &&Path.of(originalFixtureProducerRef.path()).getFileName().toString().equals("run_ck3_12002_mcp_live.py"),"exact original fixture parameter producer required");
        }
    }
    public static byte[] encodeRequest(RequestBinding value)throws IOException {
        Objects.requireNonNull(value);var n=JSON.createObjectNode().put("schema",CURRENT_REQUEST_SCHEMA).put("machine_id",value.machineId());
        n.set("inventory_request_ref",refJson(value.inventoryRequestRef()));n.set("selected_configuration_producer_ref",refJson(value.selectedConfigurationProducerRef()));
        n.set("selected_configuration_source_map_ref",refJson(value.selectedConfigurationSourceMapRef()));n.set("original_fixture_producer_ref",refJson(value.originalFixtureProducerRef()));
        return JSON.writeValueAsBytes(n);
    }
    public static RequestBinding decodeRequest(byte[] bytes)throws IOException {
        JsonNode n=parse(bytes,65536);keys(n,Set.of("schema","machine_id","inventory_request_ref","selected_configuration_producer_ref","selected_configuration_source_map_ref","original_fixture_producer_ref"));
        require(text(n,"schema").equals(CURRENT_REQUEST_SCHEMA),"explicit capture request v3 required; no historical configuration alias");
        return new RequestBinding(text(n,"machine_id"),ref(field(n,"inventory_request_ref")),ref(field(n,"selected_configuration_producer_ref")),
                ref(field(n,"selected_configuration_source_map_ref")),ref(field(n,"original_fixture_producer_ref")));
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode refJson(FileRef ref) {
        return JSON.createObjectNode().put("path",ref.path()).put("bytes",ref.bytes()).put("sha256",ref.sha256());
    }
    public enum SelectedIntent {
        FRESH_ROBERT_1066_ALL_ORDINARY,EXPLICIT_ROBERT_FIXTURE,EXPLICIT_SCENARIO_FIXTURE,SAVED_GAME_ALL_ORDINARY,SAVED_NATIVE_CAMPAIGN;
        public boolean fixture(){return this==EXPLICIT_ROBERT_FIXTURE||this==EXPLICIT_SCENARIO_FIXTURE;}
        public boolean saved(){return this==SAVED_GAME_ALL_ORDINARY||this==SAVED_NATIVE_CAMPAIGN;}
        public boolean nativeCampaign(){return fixture()||this==SAVED_NATIVE_CAMPAIGN;}
        public String selectedFixtureTool(){return switch(this){
            case FRESH_ROBERT_1066_ALL_ORDINARY,SAVED_GAME_ALL_ORDINARY,SAVED_NATIVE_CAMPAIGN->"";
            case EXPLICIT_ROBERT_FIXTURE->"ck3_submit_frontend_fixture_robert_start_v1";
            case EXPLICIT_SCENARIO_FIXTURE->"ck3_submit_frontend_fixture_scenario_start_v1";};}
    }
    public enum ConfigurationSourceRole { ROOT_INTENT,DOMAIN_SETTINGS,CAPABILITY_CONFIGURATION,LIFE_SETTINGS,RUN_PROFILE,
        ORIGINAL_MCP_SERVER,ORIGINAL_NATIVE_DRIVER,ORIGINAL_SERVICE,ORIGINAL_FIXTURE }
    public record ConfigurationSource(ConfigurationSourceRole role,FileRef original) {
        public ConfigurationSource {Objects.requireNonNull(role);Objects.requireNonNull(original);absolute(original.path());
            require(original.bytes()>0&&original.bytes()<=4<<20,"bounded exact selected configuration source required");}
    }
    public enum Projection { ONE_LIFE("one_life"),NATIVE_CAMPAIGN("native_campaign");
        private final String wire;Projection(String wire){this.wire=wire;}public String wire(){return wire;}
        private static Projection parse(String wire){for(var value:values())if(value.wire.equals(wire))return value;throw new IllegalArgumentException("closed actual episode projection required");}
    }
    /** Opaque transport for the sole SuccessionLifecycleCodec. This supplies neither lifecycle nor Game permission. */
    public record LifecycleArgument(String canonicalJson) {
        public LifecycleArgument {
            require(canonicalJson!=null,"explicit same lifecycle argument required");
            try{JsonNode value=parse(canonicalJson.getBytes(StandardCharsets.UTF_8),65536);
                require((value.isNull()||value.isObject()&&value.size()>0)&&JSON.writeValueAsString(value).equals(canonicalJson),"bounded canonical lifecycle object or explicit null transport required");
            }catch(IOException invalid){throw new IllegalArgumentException("invalid lifecycle argument transport",invalid);}
        }
    }
    public record ConstructorArguments(int routeContactTimelineSpeed,boolean allowRouteContactHighSpeedAb,
            boolean stationaryObjectiveHoldCanaryRequested,boolean warDailyWatchEnabled,Projection projection,LifecycleArgument lifecycle) {
        public ConstructorArguments {
            require(routeContactTimelineSpeed>=1&&routeContactTimelineSpeed<=5,"exact route speed 1..5 required");
            require(routeContactTimelineSpeed<=3||allowRouteContactHighSpeedAb,"speed 4..5 requires the explicit existing A/B request");
            Objects.requireNonNull(projection);Objects.requireNonNull(lifecycle);
            require(lifecycle.canonicalJson().equals("null")==(projection==Projection.NATIVE_CAMPAIGN),"native_campaign requires explicit null lifecycle; one_life requires the existing nonnull binding");
        }
    }
    public record FixtureTarget(String bookmarkKey,String characterNameKey,String governmentKey,int startDateRaw,String bookmarkGroupKey) {
        public FixtureTarget {
            require("bm_xar_faith_h01_867".equals(bookmarkKey)&&"bookmark_xar_faith_h01_abbasid".equals(characterNameKey)
                    &&"clan_government".equals(governmentKey)&&startDateRaw==51394920&&"bm_group_867".equals(bookmarkGroupKey),"exact original scenario target required");
        }
    }
    public record FixtureBinding(String policySha256,String preparationSha256,java.util.Optional<FixtureTarget> scenarioTarget) {
        public FixtureBinding {require(policySha256!=null&&policySha256.matches("[0-9a-f]{64}")&&preparationSha256!=null&&preparationSha256.matches("[0-9a-f]{64}"),"canonical exact policy/preparation SHA required");
            Objects.requireNonNull(scenarioTarget);}
    }
    public record FixtureSelection(FixtureBinding binding,Path profileDirectory) {
        public FixtureSelection {Objects.requireNonNull(binding);Objects.requireNonNull(profileDirectory);absolute(profileDirectory.toString());}
    }
    /** Consumer DTO only. Root's one producer still rederives Bound against its actual PreparedFixture and frozen inputs. */
    public record SelectedConfiguration(String machineId,String observedAtUtc,String reviewAtUtc,SelectedIntent intent,FileRef producer,
            List<ConfigurationSource> sources,ConstructorArguments constructorArguments,java.util.Optional<FixtureSelection> fixture,java.util.Optional<Path> profileDirectory) {
        /** Original fresh call shape remains explicit; Saved requires the canonical profile argument. */
        public SelectedConfiguration(String machineId,String observedAtUtc,String reviewAtUtc,SelectedIntent intent,FileRef producer,
                List<ConfigurationSource> sources,ConstructorArguments constructorArguments,java.util.Optional<FixtureSelection> fixture) {
            this(machineId,observedAtUtc,reviewAtUtc,intent,producer,sources,constructorArguments,fixture,fixture.map(FixtureSelection::profileDirectory));
        }
        public SelectedConfiguration {
            machine(machineId);Instant first=Instant.parse(observedAtUtc),last=Instant.parse(reviewAtUtc);
            require(first.isBefore(last)&&java.time.Duration.between(first,last).compareTo(java.time.Duration.ofDays(7))<=0
                    &&first.toString().equals(observedAtUtc)&&last.toString().equals(reviewAtUtc),"finite canonical selected configuration UTC interval required");
            Objects.requireNonNull(intent);Objects.requireNonNull(producer);Objects.requireNonNull(constructorArguments);Objects.requireNonNull(fixture);Objects.requireNonNull(profileDirectory);
            sources=List.copyOf(sources);require(sources.size()==ConfigurationSourceRole.values().length
                    &&sources.stream().map(ConfigurationSource::role).distinct().count()==ConfigurationSourceRole.values().length
                    &&sources.stream().map(row->Path.of(row.original().path()).toAbsolutePath().normalize()).distinct().count()==sources.size(),"nine distinct exact selected configuration sources required");
            require(fixture.isPresent()==intent.fixture(),"only the two explicit fixture intents carry a fixture binding");
            require(profileDirectory.isPresent()==(intent.fixture()||intent.saved()),"explicit fixture/Saved profile required; fresh ordinary requires null");
            profileDirectory.ifPresent(value->absolute(value.toString()));
            require(constructorArguments.projection()==(intent.nativeCampaign()?Projection.NATIVE_CAMPAIGN:Projection.ONE_LIFE),"selected projection differs from explicit intent");
            if(fixture.isPresent()){
                var value=fixture.orElseThrow();require(profileDirectory.equals(java.util.Optional.of(value.profileDirectory())),"fixture/common profile directories differ");
                require(value.binding().scenarioTarget().isPresent()==(intent==SelectedIntent.EXPLICIT_SCENARIO_FIXTURE),"fixture policy binding kind differs from selected intent");
            }
        }
    }

    public enum RegistrationAttribute {
        GRANT_TITLE_PICKER("_grant_title_picker_private_enabled_v1"),
        ACTIVE_SCHEME_SWAY_ACTION("allow_private_active_scheme_sway_action"),
        ACTIVE_SCHEME_SWAY_COMPLETION_EXECUTION_QUERY("allow_private_active_scheme_sway_completion_execution_query"),
        ACTIVE_SCHEME_SWAY_COMPLETION_INVALIDATION_REASON_QUERY("allow_private_active_scheme_sway_completion_invalidation_reason_query"),
        ACTIVE_SCHEME_SWAY_COMPLETION_QUERY("allow_private_active_scheme_sway_completion_query"),
        ACTIVE_SCHEME_SWAY_COMPLETION_TERMINATION_QUERY("allow_private_active_scheme_sway_completion_termination_query"),
        ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_QUERY("allow_private_active_scheme_sway_outcome_opinion_query"),
        ACTIVE_SCHEME_SWAY_QUERY("allow_private_active_scheme_sway_query"),
        ACTIVITY_FEAST_GUEST_CANDIDATE_QUERY("allow_private_activity_feast_guest_candidate_query"),
        ACTIVITY_FEAST_GUEST_OPINION_QUERY("allow_private_activity_feast_guest_opinion_query"),
        ACTIVITY_FEAST_GUEST_ROUTE_PROOF_QUERY("allow_private_activity_feast_guest_route_proof_query"),
        ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_QUERY("allow_private_activity_feast_guest_rule_provenance_query"),
        ACTIVITY_FEAST_GUEST_TARGET_QUERY("allow_private_activity_feast_guest_target_query"),
        ACTIVITY_FEAST_STAGE5_START_QUERY("allow_private_activity_feast_stage5_start_query"),
        ACTIVITY_STAGE5_FEAST_FULL_COST_QUERY("allow_private_activity_stage5_feast_full_cost_query"),
        ACTOR_CACHED_SUCCESSION_QUERIES("allow_private_actor_cached_succession_queries"),
        CHARACTER_KNIGHT_EFFECTIVENESS_QUERY("allow_private_character_knight_effectiveness_query"),
        CHARACTER_SKILL_EFFECTS_QUERY("allow_private_character_skill_effects_query"),
        CONFUCIAN_CHALLENGER_QUERIES("allow_private_confucian_challenger_queries"),
        CONFUCIAN_READONLY_QUERIES("allow_private_confucian_readonly_queries"),
        CONSTRUCTION_FORMAL_TRIAL("allow_private_construction_formal_trial"),
        COUNCIL_ACTION("allow_private_council_action"),COUNCIL_QUERY("allow_private_council_query"),
        CURRENT_FIRST_HEIR_RELATIONSHIP_QUERY("allow_private_current_first_heir_relationship_query"),
        DEATH_SUCCESSION_MODAL_CONTINUE("allow_private_death_succession_modal_continue"),
        EPIDEMIC_RECOVERY_QUERY("allow_private_epidemic_recovery_query"),
        EPIDEMIC_TREATMENT_PRESENCE_QUERY("allow_private_epidemic_treatment_presence_query"),
        FACTION_GIFT_ACTION("allow_private_faction_gift_action"),FACTION_GIFT_QUERY("allow_private_faction_gift_query"),
        FAMILY_OBLIGATIONS_QUERY("allow_private_family_obligations_query"),
        GOVERNMENT_RUNTIME_ADAPTER_QUERY("allow_private_government_runtime_adapter_query"),
        HOLY_SITE_ADOPTION_DETAIL_QUERY("allow_private_holy_site_adoption_detail_query"),
        HOLY_SITE_RELIC_ACTIONS("allow_private_holy_site_relic_actions"),
        PLAYER_ARTIFACT_PERSONAL_USE_ACTIONS("allow_private_player_artifact_personal_use_actions"),
        PLAYER_ARTIFACT_PERSONAL_USE_QUERY("allow_private_player_artifact_personal_use_query"),
        PLAYER_CHILD_MARRIAGE_SUBJECT_QUERY("allow_private_player_child_marriage_subject_query"),
        PLAYER_CLERGY_APPOINTMENT_QUERY("allow_private_player_clergy_appointment_query"),
        PLAYER_GHW_PERMISSIONS_QUERY("allow_private_player_ghw_permissions_query"),
        PLAYER_HOLY_SITE_CREATION_CONTEXT_QUERY("allow_private_player_holy_site_creation_context_query"),
        PLAYER_HOLY_SITE_CREATION_CREATE_ONCE("allow_private_player_holy_site_creation_create_once"),
        PLAYER_HOLY_SITE_CREATION_UI("allow_private_player_holy_site_creation_ui"),
        PLAYER_HOLY_SITE_QUERY("allow_private_player_holy_site_query"),
        PLAYER_HOLY_SITE_RELIC_ACTION_CONTEXT_QUERY("allow_private_player_holy_site_relic_action_context_query"),
        PLAYER_HOLY_SITE_RELIC_CONTEXT_QUERY("allow_private_player_holy_site_relic_context_query"),
        PLAYER_HOLY_SITE_RELIC_PERMISSIONS_QUERY("allow_private_player_holy_site_relic_permissions_query"),
        PLAYER_INVENTORY_WINDOW_CLOSE("allow_private_player_inventory_window_close"),
        PLAYER_INVENTORY_WINDOW_OPEN("allow_private_player_inventory_window_open"),
        PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_QUERY("allow_private_player_ordinary_holy_war_declaration_context_query"),
        PLAYER_PILGRIMAGE_ACTIVITIES_QUERY("allow_private_player_pilgrimage_activities_query"),
        PLAYER_PILGRIMAGE_EXECUTION("allow_private_player_pilgrimage_execution"),
        PLAYER_RELIGION_AI_REFORM_INPUTS_QUERY("allow_private_player_religion_ai_reform_inputs_query"),
        PLAYER_RELIGION_CONTEXT_QUERY("allow_private_player_religion_context_query"),
        PLAYER_RELIGION_CONVERSION_CHOICES_QUERY("allow_private_player_religion_conversion_choices_query"),
        PLAYER_RELIGION_CONVERSION_INPUTS_QUERY("allow_private_player_religion_conversion_inputs_query"),
        PLAYER_RELIGION_CONVERSION_OUTCOME_QUERY("allow_private_player_religion_conversion_outcome_query"),
        PLAYER_RELIGION_CONVERSION_REASONS_QUERY("allow_private_player_religion_conversion_reasons_query"),
        PLAYER_RELIGION_CONVERSION_TERMS_QUERY("allow_private_player_religion_conversion_terms_query"),
        PLAYER_RELIGION_DOCTRINE_CATALOGUE_QUERY("allow_private_player_religion_doctrine_catalogue_query"),
        PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_QUERY("allow_private_player_religion_doctrine_knowledge_query"),
        PLAYER_RELIGION_DOCTRINES_QUERY("allow_private_player_religion_doctrines_query"),
        PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_QUERY("allow_private_player_religion_draft_doctrine_choices_query"),
        PLAYER_RELIGION_DRAFT_GROUPS_QUERY("allow_private_player_religion_draft_groups_query"),
        PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_QUERY("allow_private_player_religion_draft_resource_costs_query"),
        PLAYER_RELIGION_DRAFT_TENET_CHOICES_QUERY("allow_private_player_religion_draft_tenet_choices_query"),
        PLAYER_RELIGION_HOSTILITY_QUERY("allow_private_player_religion_hostility_query"),
        PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_QUERY("allow_private_player_religion_numeric_special_parameters_query"),
        PLAYER_RELIGION_PERSONAL_PARAMETERS_QUERY("allow_private_player_religion_personal_parameters_query"),
        PLAYER_RELIGION_REFORM_CONTEXT_QUERY("allow_private_player_religion_reform_context_query"),
        PLAYER_RELIGION_TENETS_QUERY("allow_private_player_religion_tenets_query"),
        PLAYER_RITE_CREATION_ACTIONS("allow_private_player_rite_creation_actions"),
        PLAYER_RITE_GOVERNANCE_QUERY("allow_private_player_rite_governance_query"),
        PLAYER_RITE_MEMBERS_QUERY("allow_private_player_rite_members_query"),
        PREWAR_FORCE_COALITION_QUERY("allow_private_prewar_force_coalition_query"),
        PRISONER_COLLECTION_QUERY("allow_private_prisoner_collection_query"),
        PRISONER_RANSOM_ACTION("allow_private_prisoner_ransom_action"),
        REALM_LAW_ACTION("allow_private_realm_law_action"),REALM_LAW_PAUSED_QUERY("allow_private_realm_law_paused_query"),
        SEMANTIC_SNAPSHOT_READONLY("allow_private_semantic_snapshot_readonly"),WAR_CASH_QUERY("allow_private_war_cash_query");
        private final String wire;RegistrationAttribute(String wire){this.wire=wire;}public String wire(){return wire;}
    }

    public enum Role {
        CATALOG("catalog","xar.original-mcp-declarations/v2"),
        TOOLS("tools","xar.java-public-mcp-tools/v1"),
        RESOURCES("resources","xar.java-public-mcp-resources/v1"),
        REGISTRATION_FACTS("registration_facts","xar.original-mcp-registration-facts/v1"),
        INVENTORY_PROOF("inventory_proof","xar.original-mcp-registration-callgraph/v1");
        private final String wire,schema;
        Role(String wire,String schema){this.wire=wire;this.schema=schema;}
        public String wire(){return wire;}public String schema(){return schema;}
        public static Role parse(String value)throws IOException{for(var role:values())if(role.wire.equals(value))return role;throw new IOException("unknown original MCP document role");}
    }
    public enum Phase { MEASURE,CAPTURE }
    public enum OriginalModule {
        MCP_SERVER("xar_autoplayer.bridge.mcp_server"),RITE_CREATION_ACTION_MCP_V1("xar_autoplayer.bridge.rite_creation_action_mcp_v1"),
        ARMY_OBSERVER_RESEARCH_SAMPLING_CONTROL("xar_autoplayer.bridge.army_observer_research_sampling_control"),PRIVATE_AUTO_SCALAR_AB_CONTROL_V1("xar_autoplayer.bridge.private_auto_scalar_ab_control_v1");
        private final String pythonModule;OriginalModule(String pythonModule){this.pythonModule=pythonModule;}public String pythonModule(){return pythonModule;}
        public static OriginalModule parse(String module)throws IOException{for(var value:values())if(value.pythonModule.equals(module))return value;throw new IOException("unknown exact original MCP registration module");}
    }
    public record OriginalSource(OriginalModule module,FileRef original,SharedSourceFiles.NativeFile nativeFile){
        public OriginalSource{Objects.requireNonNull(module);Objects.requireNonNull(original);Objects.requireNonNull(nativeFile);require(original.bytes()>0&&original.bytes()<=4<<20
            &&nativeFile.logicalBytes()==original.bytes(),"actual explicit original registration source required");}
    }
    public record OriginalMcpSourceSet(OriginalSource mcpServer,OriginalSource riteCreationActionMcpV1,
            OriginalSource armyObserverResearchSamplingControl,OriginalSource privateAutoScalarAbControlV1){
        public OriginalMcpSourceSet{var paths=new HashSet<Path>();var nativeIds=new HashSet<String>();for(var module:OriginalModule.values()){
            var source=switch(module){case MCP_SERVER->mcpServer;case RITE_CREATION_ACTION_MCP_V1->riteCreationActionMcpV1;case ARMY_OBSERVER_RESEARCH_SAMPLING_CONTROL->armyObserverResearchSamplingControl;case PRIVATE_AUTO_SCALAR_AB_CONTROL_V1->privateAutoScalarAbControlV1;};
            require(source!=null&&source.module()==module&&paths.add(Path.of(source.original().path()).toAbsolutePath().normalize())&&nativeIds.add(source.nativeFile().identityKey()),"four distinct explicit source roles/identities required");}}
        public OriginalSource get(OriginalModule module){return switch(module){case MCP_SERVER->mcpServer;case RITE_CREATION_ACTION_MCP_V1->riteCreationActionMcpV1;case ARMY_OBSERVER_RESEARCH_SAMPLING_CONTROL->armyObserverResearchSamplingControl;case PRIVATE_AUTO_SCALAR_AB_CONTROL_V1->privateAutoScalarAbControlV1;};}
        public java.util.Optional<OriginalSource> lookup(FileRef exact){Objects.requireNonNull(exact);for(var module:OriginalModule.values())if(sameRef(get(module).original(),exact))return java.util.Optional.of(get(module));return java.util.Optional.empty();}
        public OriginalSource requireOriginal(FileRef exact)throws IOException{return lookup(exact).orElseThrow(()->new IOException("original Python source is outside the actual captured four-module table"));}
        public void verify()throws IOException{for(var module:OriginalModule.values()){var source=get(module);var actual=SharedSourceFiles.observe(Path.of(source.original().path()));
            require(sameRef(source.original(),actual.source())&&source.nativeFile().equals(actual.nativeFile()),"original MCP source bytes/native identity drifted");}}
    }
    public record Extent(long bytes,String sha256){
        public Extent{require(bytes>0&&bytes<=DOCUMENT_MAX&&sha256!=null&&sha256.matches("[0-9a-f]{64}"),"bounded exact original document extent required");}
    }
    public record FiveExtents(Extent catalog,Extent tools,Extent resources,Extent registrationFacts,Extent inventoryProof){
        public FiveExtents{for(var role:Role.values())Objects.requireNonNull(switch(role){case CATALOG->catalog;case TOOLS->tools;case RESOURCES->resources;case REGISTRATION_FACTS->registrationFacts;case INVENTORY_PROOF->inventoryProof;});}
        public Extent get(Role role){return switch(role){case CATALOG->catalog;case TOOLS->tools;case RESOURCES->resources;case REGISTRATION_FACTS->registrationFacts;case INVENTORY_PROOF->inventoryProof;};}
        public long logicalBytes(){long bytes=0;for(Role role:Role.values())bytes=Math.addExact(bytes,get(role).bytes());return bytes;}
        /** All base64 payload plus finite framing and final transport line, including the temporary audit copy. */
        public long maximumWireBytes(){long total=65536;for(var role:Role.values())total=Math.addExact(total,Math.addExact(512,Math.multiplyExact(4,Math.floorDiv(Math.addExact(get(role).bytes(),2),3))));return total;}
    }
    public record Counts(int declarations,int unconditional,int conditional,int registeredTools,int resources,
            List<String> registeredIdentities,List<String> unregisteredConditionalIdentities,int sdkSerdeCount,int sdkRejections){
        public Counts{
            registeredIdentities=List.copyOf(registeredIdentities);unregisteredConditionalIdentities=List.copyOf(unregisteredConditionalIdentities);
            require(declarations>0&&declarations<=4096&&unconditional>=0&&unconditional<=declarations&&conditional>=0&&conditional<=declarations&&unconditional+conditional==declarations
                &&registeredTools==registeredIdentities.size()&&registeredTools>=unconditional&&registeredTools<=declarations&&resources==2
                &&unregisteredConditionalIdentities.size()+registeredTools==declarations&&sdkSerdeCount==registeredTools+resources&&sdkRejections==6,"actual original counts/sets/serde differ");
            var all=new HashSet<String>();for(var name:registeredIdentities)require(name!=null&&!name.isEmpty()&&all.add(name),"unique actual registered identities required");
            for(var name:unregisteredConditionalIdentities)require(name!=null&&!name.isEmpty()&&all.add(name),"unique excluded original identities required");
        }
    }
    public record Versions(String pythonExecutable,String pythonVersion,String mcp,String mcpTypes,String pydantic){
        public Versions{for(var value:List.of(pythonExecutable,pythonVersion,mcp,mcpTypes,pydantic))require(value!=null&&!value.isBlank(),"actual interpreter/SDK versions required");require(mcp.equals("2.0.0"),"exact original MCP2 distribution required");}
    }
    public record Transport(String actualPipe,String actualUncreatedState,boolean listenerClosed){
        public Transport{
            require(actualPipe!=null&&actualPipe.startsWith("\\\\.\\pipe\\xar_original_mcp_capture_")&&actualPipe.substring(actualPipe.lastIndexOf('_')+1).matches("[0-9a-f]{32}"),"actual fresh production capture pipe required");
            require(actualUncreatedState!=null&&Path.of(actualUncreatedState).isAbsolute()&&listenerClosed,"actual uncreated isolated state and closed listener required");
        }
    }
    public record Summary(String machineId,String observedAtUtc,FileRef configurationRef,FiveExtents documents,Counts counts,Versions versions,Transport transport){
        public Summary{
            machine(machineId);Instant.parse(observedAtUtc);Objects.requireNonNull(configurationRef);Objects.requireNonNull(documents);Objects.requireNonNull(counts);Objects.requireNonNull(versions);Objects.requireNonNull(transport);
        }
    }
    /** Finite process/control scope, data-only record. Actual SharedOwnedCommand/issuer release is still required before invocation. */
    public record Plan(String schema,String machineId,String observedAtUtc,String reviewAtUtc,FileRef originalRequestRef,
            FileRef selectedConfigurationRef,FileRef pythonExecutableRef,String cwd,String sessionParent,
            SharedSourceFiles.DirectoryIdentity sessionParentIdentity,FileRef executionReleaseRef,
            long timeoutSeconds,long memoryLimitBytes,long maximumSessionNativeBytes,long maximumStderrBytes){
        public Plan{
            require(PLAN_SCHEMA.equals(schema),"unknown original MCP capture plan");machine(machineId);
            require(Instant.parse(observedAtUtc).isBefore(Instant.parse(reviewAtUtc)),"finite original capture period required");
            for(var ref:List.of(originalRequestRef,selectedConfigurationRef,pythonExecutableRef,executionReleaseRef))Objects.requireNonNull(ref);
            require(originalRequestRef.bytes()>0&&originalRequestRef.bytes()<=CONTROL_MAX,"bounded exact capture request required; execution resolves its explicit version");
            require(selectedConfigurationRef.bytes()>0&&selectedConfigurationRef.bytes()<=65536,"bounded actual selected configuration original required");
            absolute(cwd);absolute(sessionParent);Objects.requireNonNull(sessionParentIdentity);
            require(timeoutSeconds>0&&timeoutSeconds<=60&&memoryLimitBytes>0&&memoryLimitBytes<=512L<<20
                &&maximumSessionNativeBytes>=131072&&maximumSessionNativeBytes<=96L<<20
                &&maximumStderrBytes>0&&maximumStderrBytes<=131072,"finite capture process/IO limits required");
        }
    }
    public record ProcessEvidence(WindowsJobProcess.CommandResult result,SharedSourceFiles.Witness wire,
            SharedSourceFiles.Witness stderr,SharedSourceFiles.DirectoryIdentity sessionDirectory,String sessionRoot){
        public ProcessEvidence{
            Objects.requireNonNull(result);Objects.requireNonNull(wire);Objects.requireNonNull(stderr);Objects.requireNonNull(sessionDirectory);absolute(sessionRoot);
            require(result.passed(),"actual hard-Job terminal success required; ACK is insufficient");
        }
    }
    public record Measured(Plan plan,Summary summary,ProcessEvidence evidence){
        public Measured{Objects.requireNonNull(plan);Objects.requireNonNull(summary);Objects.requireNonNull(evidence);
            require(plan.machineId().equals(summary.machineId())&&sameRef(plan.selectedConfigurationRef(),summary.configurationRef()),"actual measured configuration/machine differs");}
    }
    /** Bytes are immutable private originals; a constructed record does not grant storage or Java service admission. */
    public static final class Documents {
        private final EnumMap<Role,byte[]> values;
        private Documents(EnumMap<Role,byte[]> values){this.values=new EnumMap<>(Role.class);for(var role:Role.values()){byte[] raw=Objects.requireNonNull(values.get(role));this.values.put(role,raw.clone());}}
        public byte[] get(Role role){return values.get(Objects.requireNonNull(role)).clone();}
        public FiveExtents extents(){return new FiveExtents(extent(values.get(Role.CATALOG)),extent(values.get(Role.TOOLS)),extent(values.get(Role.RESOURCES)),extent(values.get(Role.REGISTRATION_FACTS)),extent(values.get(Role.INVENTORY_PROOF)));}
    }
    public static final class Captured {
        private final Measured measured;private final Documents documents;private final ProcessEvidence evidence;private final Transport transport;
        private final List<SharedSourceFiles.Witness> sourceOriginals;
        private Captured(Measured measured,Documents documents,ProcessEvidence evidence,Transport transport,List<SharedSourceFiles.Witness> sourceOriginals){this.measured=measured;this.documents=documents;this.evidence=evidence;this.transport=transport;this.sourceOriginals=List.copyOf(sourceOriginals);}
        public Measured measured(){return measured;}public Documents documents(){return documents;}public ProcessEvidence evidence(){return evidence;}public Transport transport(){return transport;}
    }
    public record DataFile(Role role,FileRef original,SharedSourceFiles.NativeFile nativeFile){
        public DataFile{Objects.requireNonNull(role);Objects.requireNonNull(original);Objects.requireNonNull(nativeFile);require(original.bytes()>0&&original.bytes()<=DOCUMENT_MAX
            &&nativeFile.logicalBytes()==original.bytes()&&nativeFile.linkCount()==1,"exact private captured DATA file required");}
    }
    public record FiveFiles(DataFile catalog,DataFile tools,DataFile resources,DataFile registrationFacts,DataFile inventoryProof){
        public FiveFiles{var paths=new HashSet<Path>();var identities=new HashSet<String>();for(Role role:Role.values()){
            DataFile file=switch(role){case CATALOG->catalog;case TOOLS->tools;case RESOURCES->resources;case REGISTRATION_FACTS->registrationFacts;case INVENTORY_PROOF->inventoryProof;};
            require(file!=null&&file.role()==role&&paths.add(Path.of(file.original().path()).toAbsolutePath().normalize())&&identities.add(file.nativeFile().identityKey()),"five distinct exact captured roles/paths/native IDs required");}}
        public DataFile get(Role role){return switch(role){case CATALOG->catalog;case TOOLS->tools;case RESOURCES->resources;case REGISTRATION_FACTS->registrationFacts;case INVENTORY_PROOF->inventoryProof;};}
    }
    public static void verify(FiveFiles files)throws IOException{for(Role role:Role.values()){var file=files.get(role);var actual=SharedSourceFiles.observe(Path.of(file.original().path()));
        require(sameRef(file.original(),actual.source())&&file.nativeFile().equals(actual.nativeFile()),"captured original DATA bytes/native identity changed");}}
    public static Measured measure(Plan actualPlan)throws IOException,InterruptedException{
        Run result=run(actualPlan,Phase.MEASURE,null);Summary summary=parseSummary(result.summary);verifySelectedTools(result.selected(),summary.counts().registeredIdentities());return new Measured(actualPlan,summary,result.evidence);
    }
    public static byte[] encodePlan(Plan value)throws IOException{return JSON.writeValueAsBytes(Objects.requireNonNull(value));}
    public static Plan decodePlan(byte[] raw)throws IOException{parse(raw,CONTROL_MAX);return JSON.readValue(raw,Plan.class);}
    public static byte[] encodeMeasured(Measured value)throws IOException{return JSON.writeValueAsBytes(Objects.requireNonNull(value));}
    public static Measured readMeasured(FileRef original)throws IOException{
        original.verify();require(original.bytes()>0&&original.bytes()<=CONTROL_MAX,"bounded original measured receipt required");
        byte[] raw=Files.readAllBytes(Path.of(original.path()));parse(raw,CONTROL_MAX);var measured=JSON.readValue(raw,Measured.class);original.verify();
        SharedSourceFiles.assertUnchanged(measured.evidence().wire());SharedSourceFiles.assertUnchanged(measured.evidence().stderr());
        byte[] wire=Files.readAllBytes(Path.of(measured.evidence().wire().source().path()));
        require(parseSummary(parse(wire,131072)).equals(measured.summary()),"original measured wire/typed receipt differs");
        return measured;
    }
    /** C24 can run this bounded measurement entry without booting Quarkus or the Game. */
    public static void main(String[] args)throws Exception{
        require(args.length==4&&args[0].equals("measure"),"measure PLAN_PATH EXACT_BYTES SHA256 required");
        long count=Long.parseLong(args[2]);require(Long.toString(count).equals(args[2]),"canonical exact plan byte count required");
        FileRef original=new FileRef(absolute(args[1]).toString(),count,args[3]);var input=SharedSourceFiles.observe(Path.of(original.path()));
        require(sameRef(input.source(),original)&&count<=CONTROL_MAX,"actual bounded plan original required");
        Plan plan=decodePlan(Files.readAllBytes(Path.of(original.path())));var measured=measure(plan);
        var saved=writeSessionReceipt(plan,measured.evidence(),encodeMeasured(measured));SharedSourceFiles.assertUnchanged(input);
        System.out.println(JSON.writeValueAsString(saved.source()));
    }
    /** One random control receipt after an actual successful Job. No DATA path or arbitrary output is accepted. */
    public static SharedSourceFiles.Witness writeSessionReceipt(Plan plan,ProcessEvidence evidence,byte[] complete)throws IOException{
        require(complete!=null&&complete.length>0&&complete.length<=CONTROL_MAX,"bounded complete control receipt required");
        var originals=new ArrayList<SharedSourceFiles.Witness>();admitExecution(plan,originals);current(plan);
        Path parent=Path.of(plan.sessionParent()),session=Path.of(evidence.sessionRoot());
        require(session.getParent().equals(parent)&&session.getFileName().toString().matches("mcp-[0-9a-f]{32}")
            &&SharedSourceFiles.nativeDirectory(parent).equals(plan.sessionParentIdentity())&&SharedSourceFiles.nativeDirectory(session).equals(evidence.sessionDirectory()),"actual original random session directory required");
        require(Path.of(evidence.wire().source().path()).equals(session.resolve("temporary-wire.jsonl"))&&Path.of(evidence.stderr().source().path()).equals(session.resolve("stderr.log")),"session receipt crossed its original Job outputs");
        SharedSourceFiles.assertUnchanged(evidence.wire());SharedSourceFiles.assertUnchanged(evidence.stderr());
        try(var entries=Files.newDirectoryStream(session)){var names=new HashSet<String>();for(Path entry:entries)names.add(entry.getFileName().toString());
            require(names.equals(Set.of("temporary-wire.jsonl","stderr.log")),"one original receipt only; unknown or prior session outputs cannot be adopted");}
        require(allocation(session,session.resolve("temporary-wire.jsonl"),session.resolve("stderr.log"))+CONTROL_MAX+8192<=plan.maximumSessionNativeBytes(),"control receipt exceeds its released complete session peak");
        Path target=session.resolve("receipt-"+UUID.randomUUID().toString().replace("-","")+".json");SharedSourceFiles.plainAncestors(target);
        try(var output=java.nio.channels.FileChannel.open(target,java.nio.file.StandardOpenOption.CREATE_NEW,java.nio.file.StandardOpenOption.WRITE)){
            var buffer=java.nio.ByteBuffer.wrap(complete);while(buffer.hasRemaining())output.write(buffer);output.force(true);
        }
        var actual=SharedSourceFiles.observe(target);require(actual.source().bytes()==complete.length&&actual.source().sha256().equals(sha256(complete))&&actual.nativeFile().linkCount()==1,"actual new control receipt readback differs");
        SharedSourceFiles.assertUnchanged(actual);for(var original:originals)SharedSourceFiles.assertUnchanged(original);return actual;
    }
    /** Invoke only after the exact measurement has received actual finite output admission.
     * This reuses the identical frozen capture function, then requires all five stable byte/hash pairs to match. */
    public static Captured capture(Measured original,Plan actualCapturePlan)throws IOException,InterruptedException{
        Objects.requireNonNull(original);require(sameInputs(original.plan(),actualCapturePlan),"final capture changed original Request02/config/interpreter");
        require(original.summary().documents().logicalBytes()<=CAPTURE_LOGICAL_MAX,"actual measured documents exceed this qualified Java outer memory profile");
        require(original.summary().documents().maximumWireBytes()<=WIRE_MAX,"actual measured wire exceeds this existing owned-stdio lane");
        Run result=run(actualCapturePlan,Phase.CAPTURE,original.summary().documents());
        var docs=new Documents(result.documents);require(docs.extents().equals(original.summary().documents()),"actual final capture changed stable original documents");
        verifyDocuments(docs,original.summary(),actualCapturePlan.selectedConfigurationRef());verifySelectedTools(result.selected(),original.summary().counts().registeredIdentities());return new Captured(original,docs,result.evidence,result.transport,result.sourceOriginals);
    }
    /** Sole source table producer: explicit reviewed module/ref pairs from Request02 joined to actual catalog sources. */
    public static OriginalMcpSourceSet sourceSet(Captured actual)throws IOException{
        Objects.requireNonNull(actual);return joinSources(actual.measured().plan().originalRequestRef(),actual.documents().get(Role.CATALOG),actual.sourceOriginals);
    }
    /** Reopen/replay the same explicit join for an untrusted durable receipt. No process or directory inference. */
    public static void verifySourceSet(OriginalMcpSourceSet original,FileRef originalRequest,byte[] catalog)throws IOException{
        Objects.requireNonNull(original);original.verify();var basis=new ArrayList<SharedSourceFiles.Witness>();
        for(var module:OriginalModule.values()){var row=original.get(module);basis.add(new SharedSourceFiles.Witness(row.original(),row.nativeFile()));}
        require(joinSources(originalRequest,catalog,basis).equals(original),"durable original source set differs from the same explicit request/catalog join");
    }
    private static OriginalMcpSourceSet joinSources(FileRef originalRequest,byte[] catalogBytes,List<SharedSourceFiles.Witness> basis)throws IOException{
        JsonNode request=requestInputs(originalRequest).inventory();
        List<JsonNode> modules=array(request,"reviewed_registration_modules"),refs=array(request,"registration_source_refs");
        require(modules.size()==4&&refs.size()==4,"complete explicit four-module registration source table required");
        JsonNode catalog=parse(catalogBytes,DOCUMENT_MAX);var catalogRefs=new ArrayList<FileRef>();for(JsonNode row:array(catalog,"sources"))catalogRefs.add(ref(row));
        require(catalogRefs.size()==4,"actual captured catalog source universe differs");var sources=new EnumMap<OriginalModule,OriginalSource>(OriginalModule.class);
        for(int i=0;i<4;i++){
            require(modules.get(i).isTextual(),"explicit original module text required");var module=OriginalModule.parse(modules.get(i).textValue());FileRef expected=ref(refs.get(i));
            require(catalogRefs.stream().filter(value->sameRef(value,expected)).count()==1,"reviewed module/ref is absent or duplicated in actual catalog");
            var witness=basis.stream().filter(value->sameRef(value.source(),expected)).findFirst().orElseThrow(()->new IOException("actual owned-process source witness missing"));
            SharedSourceFiles.assertUnchanged(witness);require(sameRef(witness.source(),expected),"actual original source differs from explicit reviewed ref");
            require(sources.put(module,new OriginalSource(module,witness.source(),witness.nativeFile()))==null,"duplicate actual original source role");
        }
        var selected=new OriginalMcpSourceSet(sources.get(OriginalModule.MCP_SERVER),sources.get(OriginalModule.RITE_CREATION_ACTION_MCP_V1),sources.get(OriginalModule.ARMY_OBSERVER_RESEARCH_SAMPLING_CONTROL),sources.get(OriginalModule.PRIVATE_AUTO_SCALAR_AB_CONTROL_V1));selected.verify();return selected;
    }
    private record Run(JsonNode summary,EnumMap<Role,byte[]> documents,Transport transport,ProcessEvidence evidence,List<SharedSourceFiles.Witness> sourceOriginals,SelectedConfiguration selected){ }
    private static Run run(Plan plan,Phase phase,FiveExtents expected)throws IOException,InterruptedException{
        current(plan);var originals=new ArrayList<SharedSourceFiles.Witness>();
        retain(plan.originalRequestRef(),originals,1<<20);retain(plan.selectedConfigurationRef(),originals,65536);retain(plan.pythonExecutableRef(),originals,64<<20);retain(plan.executionReleaseRef(),originals,1<<20);
        admitExecution(plan,originals);
        RequestInputs inputs=requestInputs(plan.originalRequestRef());
        RequestBinding binding=inputs.current().orElseThrow(()->new IOException("live capture requires explicit request v3; historical Request02 is inventory only"));
        require(binding.machineId().equals(plan.machineId())&&text(inputs.inventory(),"machine_id").equals(plan.machineId()),"current capture request machine drift");
        SelectedConfiguration selected=decodeSelectedConfiguration(readBytes(plan.selectedConfigurationRef(),65536),plan.machineId(),binding.selectedConfigurationProducerRef());
        require(!Instant.now().isBefore(Instant.parse(selected.observedAtUtc()))&&Instant.now().isBefore(Instant.parse(selected.reviewAtUtc()))
                &&!Instant.parse(plan.reviewAtUtc()).isAfter(Instant.parse(selected.reviewAtUtc())),"selected configuration is future/expired/shorter than actual capture plan");
        JsonNode request=inputs.inventory();
        var all=new ArrayList<FileRef>();all.add(plan.originalRequestRef());all.add(plan.selectedConfigurationRef());all.add(plan.executionReleaseRef());
        for(var current:List.of(inputs.inventoryOriginal(),binding.selectedConfigurationProducerRef(),binding.selectedConfigurationSourceMapRef(),binding.originalFixtureProducerRef()))addPin(current,all,originals);
        String adaptation=boundaryEditWire(inputs.inventoryBytes());
        for(String key:List.of("producer_refs","registration_source_refs"))for(JsonNode row:array(request,key))addPin(ref(row),all,originals);
        for(String key:List.of("historical_catalog_ref","independent_callgraph_audit_ref"))addPin(ref(field(request,key)),all,originals);
        for(ConfigurationSource source:selected.sources())addPin(source.original(),all,originals);
        var parent=Path.of(plan.sessionParent());require(SharedSourceFiles.nativeDirectory(parent).equals(plan.sessionParentIdentity()),"actual capture parent native identity changed");
        Path session=parent.resolve("mcp-"+UUID.randomUUID().toString().replace("-",""));Files.createDirectory(session);
        var directory=SharedSourceFiles.nativeDirectory(session);Path wire=session.resolve("temporary-wire.jsonl"),stderr=session.resolve("stderr.log");
        var env=new java.util.TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);
        // WJP receives the complete environment; it does not merge overrides itself.
        env.putAll(System.getenv());
        env.put("PYTHONDONTWRITEBYTECODE","1");env.put("PYTHONIOENCODING","utf-8");env.put("PYTHONHASHSEED","0");
        env.put("PYTHONPYCACHEPREFIX",session.resolve("never-created-pycache").toString());
        var args=List.of("-X","utf8","-c",RUNNER,plan.originalRequestRef().path(),plan.selectedConfigurationRef().path(),
            Long.toString(plan.selectedConfigurationRef().bytes()),plan.selectedConfigurationRef().sha256(),phase.name(),adaptation);
        var command=new WindowsJobProcess.CommandSpec(Path.of(plan.pythonExecutableRef().path()),args,Path.of(plan.cwd()),env,wire,stderr,plan.memoryLimitBytes());
        long wireLimit=phase==Phase.MEASURE?131072:expected.maximumWireBytes();require(wireLimit<=WIRE_MAX&&wireLimit+plan.maximumStderrBytes()+CONTROL_MAX+24576<=plan.maximumSessionNativeBytes(),"exact session TEMP peak exceeds finite released scope");
        Instant until=Instant.now().plusSeconds(plan.timeoutSeconds());if(until.isAfter(Instant.parse(plan.reviewAtUtc())))until=Instant.parse(plan.reviewAtUtc());
        final Instant deadline=until;
        WindowsJobProcess.StdioGuard guard=()->{current(plan);for(var original:originals)SharedSourceFiles.assertUnchanged(original);
            require(SharedSourceFiles.nativeDirectory(parent).equals(plan.sessionParentIdentity())&&SharedSourceFiles.nativeDirectory(session).equals(directory),"original capture directory identity drift");
            require(size(stderr)<=plan.maximumStderrBytes()&&size(wire)<=wireLimit,"capture control bytes exceed finite IO scope");
            require(allocation(session,wire,stderr)<=plan.maximumSessionNativeBytes(),"actual capture TEMP native allocation exceeds its released peak");
        };
        var spec=new WindowsJobProcess.OwnedStdioSpec(command,WindowsJobProcess.ConsoleMode.NO_WINDOW,plan.pythonExecutableRef(),List.copyOf(all),
            deadline,phase==Phase.MEASURE?131072:32<<20,1,wireLimit,guard);
        JsonNode summary=null;Transport transport=null;var data=new EnumMap<Role,byte[]>(Role.class);WindowsJobProcess.CommandResult terminal;
        try(var child=WindowsJobProcess.startOwnedStdio(spec)){
            child.closeInput();
            if(phase==Phase.MEASURE)summary=parse(child.readLine(deadline).rawBytes(),131072);
            else{
                for(Role role:Role.values()){
                    byte[] frame=child.readLine(deadline).rawBytes();data.put(role,decodeDocument(frame,role,expected.get(role)));
                }
                JsonNode end=parse(child.readLine(deadline).rawBytes(),65536);keys(end,Set.of("kind","actual_pipe","actual_uncreated_state","actual_listener_closed"));
                require(text(end,"kind").equals("end"),"original capture lacks exact final transport receipt");
                transport=new Transport(text(end,"actual_pipe"),text(end,"actual_uncreated_state"),yes(end,"actual_listener_closed"));
            }
            terminal=child.awaitExit(null).commandResult();require(terminal.passed(),"original capture child failed/timeout/unknown; no DATA may be published");
        }
        guard.verify();for(var original:originals)SharedSourceFiles.assertUnchanged(original);
        var evidence=new ProcessEvidence(terminal,SharedSourceFiles.observe(wire),SharedSourceFiles.observe(stderr),directory,session.toString());
        return new Run(summary,data,transport,evidence,List.copyOf(originals),selected);
    }
    static byte[] decodeDocument(byte[] frame,Role expected,Extent extent)throws IOException{
        JsonNode n=parse(frame,32<<20);keys(n,Set.of("kind","role","bytes","sha256","base64"));require(text(n,"kind").equals("document")&&Role.parse(text(n,"role"))==expected,"original document order/role mismatch");
        require(number(n,"bytes",DOCUMENT_MAX)==extent.bytes()&&text(n,"sha256").equals(extent.sha256()),"final original document extent differs from measured");
        byte[] raw;try{raw=Base64.getDecoder().decode(text(n,"base64"));}catch(IllegalArgumentException invalid){throw new IOException("invalid exact document base64",invalid);}
        require(Base64.getEncoder().encodeToString(raw).equals(text(n,"base64"))&&extent(raw).equals(extent),"actual original document bytes/hash differ");
        return raw;
    }
    static Summary parseSummary(JsonNode n)throws IOException{
        keys(n,Set.of("schema","machine_id","observed_at_utc","python_executable","python_version","distribution_versions","configuration_ref","capture_transport_observation","documents",
            "declaration_count","unconditional_declarations","conditional_declarations","actual_registered_tools","actual_resources","actual_registered_identities","unregistered_conditional_identities",
            "sdk_descriptor_serde_count","sdk_wrong_type_missing_field_rejections","source_prepost_match","python_writes","native_peer_observed","java_admission","status"));
        require(text(n,"schema").equals("xar.original-mcp-memory-measurement/v1")&&text(n,"status").equals("MEASURED_ORIGINAL_REGISTRATION_ONLY_NOT_JAVA_OR_GAME")
            &&yes(n,"source_prepost_match")&&!bool(n,"native_peer_observed")&&number(n,"python_writes",0)==0&&text(n,"java_admission").equals("NOT_PRODUCED"),"original measurement granted unsupported qualification");
        JsonNode ext=field(n,"documents");keys(ext,Set.of("catalog","tools","resources","registration_facts","inventory_proof"));
        var five=new FiveExtents(extent(field(ext,"catalog")),extent(field(ext,"tools")),extent(field(ext,"resources")),extent(field(ext,"registration_facts")),extent(field(ext,"inventory_proof")));
        var counts=new Counts(count(n,"declaration_count"),count(n,"unconditional_declarations"),count(n,"conditional_declarations"),count(n,"actual_registered_tools"),count(n,"actual_resources"),
            strings(n,"actual_registered_identities"),strings(n,"unregistered_conditional_identities"),count(n,"sdk_descriptor_serde_count"),count(n,"sdk_wrong_type_missing_field_rejections"));
        JsonNode versions=field(n,"distribution_versions");keys(versions,Set.of("mcp","mcp-types","pydantic"));
        JsonNode transport=field(n,"capture_transport_observation");keys(transport,Set.of("actual_pipe","actual_uncreated_state","actual_listener_closed"));
        return new Summary(text(n,"machine_id"),text(n,"observed_at_utc"),ref(field(n,"configuration_ref")),five,counts,
            new Versions(text(n,"python_executable"),text(n,"python_version"),text(versions,"mcp"),text(versions,"mcp-types"),text(versions,"pydantic")),
            new Transport(text(transport,"actual_pipe"),text(transport,"actual_uncreated_state"),yes(transport,"actual_listener_closed")));
    }
    static void verifyDocuments(Documents docs,Summary summary,FileRef configuration)throws IOException{
        for(var role:Role.values()){JsonNode n=parse(docs.get(role),DOCUMENT_MAX);require(text(n,"schema").equals(role.schema()),"wrong original document schema");}
        JsonNode catalog=parse(docs.get(Role.CATALOG),DOCUMENT_MAX),tools=parse(docs.get(Role.TOOLS),DOCUMENT_MAX),resources=parse(docs.get(Role.RESOURCES),DOCUMENT_MAX);
        require(array(catalog,"declarations").size()==summary.counts().declarations()&&array(tools,"tools").size()==summary.counts().registeredTools()&&array(resources,"resources").size()==2,"actual original document denominators differ");
        var toolNames=new HashSet<String>();for(JsonNode tool:array(tools,"tools"))require(toolNames.add(text(tool,"name")),"duplicate original tool identity");
        require(toolNames.equals(new HashSet<>(summary.counts().registeredIdentities())),"actual original registered names differ from measurement");
        JsonNode facts=parse(docs.get(Role.REGISTRATION_FACTS),DOCUMENT_MAX);require(sameRef(ref(field(facts,"configuration_ref")),configuration)
            &&text(facts,"semantic_scope").equals("ORIGINAL_REGISTRATION_FACTS_ONLY_NO_JAVA_ADMISSION")
            &&text(facts,"selected_configuration_qualification").equals("ROOT_TYPED_PRODUCER_REQUIRED_NOT_GRANTED_BY_THIS_CAPTURE"),"original facts must not manufacture Java admission");
        require(array(facts,"declarations").size()==summary.counts().declarations(),"registration facts lack complete declaration universe");
        JsonNode proof=parse(docs.get(Role.INVENTORY_PROOF),DOCUMENT_MAX);
        require(count(proof,"declarations")==summary.counts().declarations()&&yes(proof,"source_prepost_match"),"recursive original inventory proof differs");
        // Descriptor structures/SDK metadata are decoded only by the shared RootPublicCatalogCodec consumer.
    }

    /** Strict v4 consumer for the actual Root encoder; this is data mapping, never a Bound issuer. */
    public static SelectedConfiguration decodeSelectedConfiguration(byte[] bytes,String expectedMachine,FileRef expectedProducer)throws IOException {
        JsonNode cfg=parse(bytes,65536);
        keys(cfg,Set.of("schema","machine_id","observed_at_utc","review_at_utc","intent","configuration_producer","source_inputs","constructor_keywords","registration_attributes","fixture_policy","profile_directory"));
        require(text(cfg,"schema").equals(CONFIGURATION_SCHEMA)&&text(cfg,"machine_id").equals(expectedMachine),"actual selected configuration v4/machine required");
        FileRef producer=ref(field(cfg,"configuration_producer"));require(sameRef(producer,Objects.requireNonNull(expectedProducer))
                &&Path.of(producer.path()).getFileName().toString().equals("RootSelectedRegistrationConfiguration.java"),"actual current configuration producer differs");
        SelectedIntent intent=SelectedIntent.valueOf(text(cfg,"intent"));var sources=new ArrayList<ConfigurationSource>();
        for(JsonNode row:array(cfg,"source_inputs")){keys(row,Set.of("role","original_ref"));sources.add(new ConfigurationSource(ConfigurationSourceRole.valueOf(text(row,"role")),ref(field(row,"original_ref"))));}
        JsonNode ctor=field(cfg,"constructor_keywords");keys(ctor,Set.of("route_contact_timeline_speed","allow_route_contact_high_speed_ab",
                "allow_stationary_objective_hold_sentinel_canary","allow_war_daily_watch_v1","episode_projection","succession_lifecycle_binding"));
        var constructor=new ConstructorArguments(Math.toIntExact(number(ctor,"route_contact_timeline_speed",5)),bool(ctor,"allow_route_contact_high_speed_ab"),
                bool(ctor,"allow_stationary_objective_hold_sentinel_canary"),bool(ctor,"allow_war_daily_watch_v1"),Projection.parse(text(ctor,"episode_projection")),
                new LifecycleArgument(JSON.writeValueAsString(field(ctor,"succession_lifecycle_binding"))));
        var flagNames=new HashSet<String>();for(var flag:RegistrationAttribute.values())flagNames.add(flag.wire());
        JsonNode flags=field(cfg,"registration_attributes");keys(flags,Set.copyOf(flagNames));
        require(flagNames.size()==79,"complete original registration attribute contract required");for(var flag:RegistrationAttribute.values())yes(flags,flag.wire());
        java.util.Optional<FixtureSelection> fixture;
        java.util.Optional<Path> profile=field(cfg,"profile_directory").isNull()?java.util.Optional.empty():java.util.Optional.of(absolute(text(cfg,"profile_directory")));
        if(intent.fixture()){
            JsonNode raw=field(cfg,"fixture_policy");boolean scenario=intent==SelectedIntent.EXPLICIT_SCENARIO_FIXTURE;
            keys(raw,scenario?Set.of("policy_sha256","preparation_sha256","profile_id","frontend_target"):Set.of("policy_sha256","preparation_sha256"));
            java.util.Optional<FixtureTarget> target=java.util.Optional.empty();
            if(scenario){
                require(text(raw,"profile_id").equals("faith-and-power-e01-abbasid-867"),"exact original scenario profile required");
                JsonNode value=field(raw,"frontend_target");keys(value,Set.of("bookmark_key","character_name_key","government_key","start_date_raw","bookmark_group_key"));
                target=java.util.Optional.of(new FixtureTarget(text(value,"bookmark_key"),text(value,"character_name_key"),text(value,"government_key"),
                        Math.toIntExact(number(value,"start_date_raw",Integer.MAX_VALUE)),text(value,"bookmark_group_key")));
            }
            fixture=java.util.Optional.of(new FixtureSelection(new FixtureBinding(text(raw,"policy_sha256"),text(raw,"preparation_sha256"),target),profile.orElseThrow(()->new IllegalArgumentException("explicit fixture profile required"))));
        }else{
            require(field(cfg,"fixture_policy").isNull(),"ordinary/Saved capture cannot invent a fixture binding");
            require(profile.isPresent()==intent.saved(),"Saved requires its explicit current profile; fresh ordinary requires null");
            fixture=java.util.Optional.empty();
        }
        return new SelectedConfiguration(text(cfg,"machine_id"),text(cfg,"observed_at_utc"),text(cfg,"review_at_utc"),intent,producer,sources,constructor,fixture,profile);
    }
    public static void verifySelectedTools(SelectedConfiguration selected,List<String> registeredNames) {
        Objects.requireNonNull(selected);var names=List.copyOf(registeredNames);
        require(new HashSet<>(names).size()==names.size(),"actual original registered identities must be unique");
        for(var variant:List.of(SelectedIntent.EXPLICIT_ROBERT_FIXTURE,SelectedIntent.EXPLICIT_SCENARIO_FIXTURE))
            require(names.contains(variant.selectedFixtureTool())==(selected.intent()==variant),"actual original fixture tool differs from the explicit selected policy");
    }
    private record RequestInputs(JsonNode inventory,byte[] inventoryBytes,FileRef inventoryOriginal,java.util.Optional<RequestBinding> current){ }
    private static RequestInputs requestInputs(FileRef original)throws IOException {
        byte[] raw=readBytes(original,CONTROL_MAX);JsonNode inventory;FileRef inventoryOriginal;java.util.Optional<RequestBinding> current;
        if(original.bytes()==REQUEST_BYTES&&original.sha256().equals(REQUEST_SHA)){
            inventory=read(original,CONTROL_MAX);inventoryOriginal=original;current=java.util.Optional.empty();
        }else{
            var binding=decodeRequest(raw);inventoryOriginal=binding.inventoryRequestRef();raw=readBytes(inventoryOriginal,CONTROL_MAX);
            inventory=parse(raw,CONTROL_MAX);require(binding.machineId().equals(text(inventory,"machine_id")),"current request changed historical inventory machine");
            current=java.util.Optional.of(binding);
        }
        require(text(inventory,"schema").equals(REQUEST_SCHEMA),"exact original inventory request schema required");
        return new RequestInputs(inventory,raw,inventoryOriginal,current);
    }
    private static byte[] readBytes(FileRef ref,int maximum)throws IOException {
        ref.verify();require(ref.bytes()>0&&ref.bytes()<=maximum,"bounded exact source bytes required");byte[] raw=Files.readAllBytes(Path.of(ref.path()));
        require(raw.length==ref.bytes()&&sha256(raw).equals(ref.sha256()),"exact source changed while reading");ref.verify();return raw;
    }

    private record BoundaryEdit(String before,String after){ }
    /** Fixed compatibility edits only: variant/policy decisions stay in the Java consumer above.
     * Source inventory, SDK serde, six constructor checks, all79 source-derived flags and real listener
     * remain the exact historical producer. The Python boundary performs only these closed byte edits. */
    private static List<BoundaryEdit> boundaryEdits() {
        return List.of(new BoundaryEdit(
                "    if cfg[\"schema\"] != \"xar.original-mcp-current-configuration/v1\" or cfg[\"intent\"] != \"FRESH_ROBERT_1066_ALL_ORDINARY\":\n",
                "    if cfg[\"schema\"] != \"xar.original-mcp-current-configuration/v4\":\n"),
            new BoundaryEdit(
                "    if keywords[\"episode_projection\"] != \"one_life\" or type(keywords[\"succession_lifecycle_binding\"]) is not dict:\n",
                "    if not ((keywords[\"episode_projection\"] == \"one_life\" and type(keywords[\"succession_lifecycle_binding\"]) is dict)"
                +" or (keywords[\"episode_projection\"] == \"native_campaign\" and keywords[\"succession_lifecycle_binding\"] is None)):\n"),
            new BoundaryEdit(
                "        if cfg[\"fixture_policy\"] is not None or cfg[\"profile_directory\"] is not None:\n"
                +"            raise ValueError(\"Root target has no business fixture/profile; no fixture policy may be invented\")\n"
                +"        server = mcp_server.create_server(driver, profile_dir=None)\n",
                "        driver.frontend_fixture_start_policy_binding = cfg[\"fixture_policy\"]\n"
                +"        server = mcp_server.create_server(driver, profile_dir=cfg[\"profile_directory\"])\n"),
            new BoundaryEdit(
                "                if isinstance(node,(ast.For,ast.AsyncFor,ast.While,ast.With,ast.AsyncWith,ast.Match)):\n"
                +"                    # No registration loop/factory exists in the reviewed original callgraph.\n"
                +"                    # Refuse a future delegated registration construct instead of guessing paths.\n"
                +"                    registration = any(isinstance(child,ast.Call) and ((isinstance(child.func,ast.Attribute) and child.func.attr in {\"tool\",\"resource\",\"add_tool\"}) or any(isinstance(arg,ast.Name) and arg.id in servers for arg in child.args)) for child in ast.walk(node))\n"
                +"                    if registration:\n"
                +"                        raise ValueError(\"new registration loop/context/match requires source research\")\n"
                +"                    continue\n",
                "                if isinstance(node,(ast.For,ast.AsyncFor,ast.While,ast.With,ast.AsyncWith,ast.Match)):\n"
                +"                    # No registration loop/factory exists in the reviewed original callgraph.\n"
                +"                    # Refuse a future delegated registration construct instead of guessing paths.\n"
                +"                    registration = any(isinstance(child,ast.Call) and ((isinstance(child.func,ast.Attribute) and child.func.attr in {\"tool\",\"resource\",\"add_tool\"}) or any(isinstance(arg,ast.Name) and arg.id in servers for arg in child.args)) for child in ast.walk(node))\n"
                +"                    if registration:\n"
                +"                        if isinstance(node,ast.For) and isinstance(node.target,ast.Name) and isinstance(node.iter,ast.Tuple) and all(isinstance(e,ast.Constant) and isinstance(e.value,str) for e in node.iter.elts) and not node.orelse and len(node.body)==1 and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Call) and isinstance(node.body[0].value.func,ast.Name) and node.body[0].value.func.id=='_forbid_unknown_tool_arguments_v1' and len(node.body[0].value.args)==2 and isinstance(node.body[0].value.args[0],ast.Name) and node.body[0].value.args[0].id in servers and isinstance(node.body[0].value.args[1],ast.Name) and node.body[0].value.args[1].id==node.target.id and not node.body[0].value.keywords:\n"
                +"                            calls(node.body[0].value,current)\n"
                +"                            continue\n"
                +"                        raise ValueError(\"new registration loop/context/match requires source research\")\n"
                +"                    continue\n"));
    }
    /** Initialize only asyncio's own Windows plumbing before the original mutation hook.
     * Runner owns shutdown on every source/import/SDK failure; the original hook stays unchanged. */
    private static List<BoundaryEdit> completeBoundaryEdits() {
        var edits=new ArrayList<>(boundaryEdits());
        edits.add(new BoundaryEdit(
            "def capture(request: dict[str, object], configuration_ref: dict[str, object]) -> OriginalDocuments:\n",
            """
            def capture(request: dict[str, object], configuration_ref: dict[str, object]) -> OriginalDocuments:
                with asyncio.Runner() as capture_runner:
                    capture_runner.get_loop()
                    return _capture_original_with_loop(request, configuration_ref, capture_runner)
            def _capture_original_with_loop(request: dict[str, object], configuration_ref: dict[str, object], capture_runner: asyncio.Runner) -> OriginalDocuments:
            """));
        edits.add(new BoundaryEdit(
            "        tool_models, resource_models = asyncio.run(actual_lists(server))\n",
            "        tool_models, resource_models = capture_runner.run(actual_lists(server))\n"));
        return List.copyOf(edits);
    }
    /** Read-only replay permits a regression to verify the actual source-pinned boundary without a process. */
    static String originalCaptureProgram(byte[] inventoryBytes)throws IOException {
        require(inventoryBytes!=null&&inventoryBytes.length==REQUEST_BYTES&&sha256(inventoryBytes).equals(REQUEST_SHA),"only exact historical capture producer may be adapted");
        JsonNode request=parse(inventoryBytes,CONTROL_MAX);String source=String.join("\n",strings(request,"code_lines"));
        String marker="if __name__ == \"__main__\":";int end=source.lastIndexOf(marker);require(end>0&&source.indexOf(marker)==end,"single frozen original main marker required");source=source.substring(0,end);
        for(var edit:completeBoundaryEdits())source=replaceOriginal(source,edit.before(),edit.after());return source;
    }
    private static String boundaryEditWire(byte[] inventoryBytes)throws IOException {
        originalCaptureProgram(inventoryBytes);return Base64.getEncoder().encodeToString(JSON.writeValueAsBytes(completeBoundaryEdits()));
    }
    private static String replaceOriginal(String source,String exact,String replacement) {
        int start=source.indexOf(exact);require(start>=0&&source.lastIndexOf(exact)==start,"exact historical capture boundary changed");
        return source.substring(0,start)+replacement+source.substring(start+exact.length());
    }

    /** Current finite execution release; historical build/source refs remain typed metadata. */
    private static void admitExecution(Plan plan,List<SharedSourceFiles.Witness> originals)throws IOException{
        JsonNode release=read(plan.executionReleaseRef(),CONTROL_MAX);
        keys(release,Set.of("schema","status","machine_id","issuer","owner","observed_at_utc","review_at_utc",
            "original_request_ref","selected_configuration_ref","python_executable_ref","producer_source_ref","whole_build_receipt_ref",
            "own_archive_actual_ref","policy_ref","standing_ref","session_parent","session_parent_identity","timeout_seconds","memory_limit_bytes",
            "maximum_session_native_bytes","maximum_stderr_bytes"));
        require(text(release,"schema").equals("xar.original-mcp-capture-execution-release/v1")
            &&text(release,"status").equals("RELEASED_ROOT_ORIGINAL_MCP_CAPTURE_NO_GAME")&&text(release,"issuer").equals("/root/budget_fast_lane")
            &&text(release,"owner").equals("/root")&&text(release,"machine_id").equals(plan.machineId()),"actual finite original capture execution release required");
        Instant first=Instant.parse(text(release,"observed_at_utc")),last=Instant.parse(text(release,"review_at_utc"));
        require(!Instant.now().isBefore(first)&&Instant.now().isBefore(last)&&!Instant.parse(plan.reviewAtUtc()).isAfter(last),"actual capture release expired/future/shorter than plan");
        require(sameRef(ref(field(release,"original_request_ref")),plan.originalRequestRef())
            &&sameRef(ref(field(release,"selected_configuration_ref")),plan.selectedConfigurationRef())
            &&sameRef(ref(field(release,"python_executable_ref")),plan.pythonExecutableRef()),"actual capture release selected other originals");
        require(Path.of(text(release,"session_parent")).equals(Path.of(plan.sessionParent()))
            &&JSON.treeToValue(field(release,"session_parent_identity"),SharedSourceFiles.DirectoryIdentity.class).equals(plan.sessionParentIdentity())
            &&number(release,"timeout_seconds",60)==plan.timeoutSeconds()&&number(release,"memory_limit_bytes",512L<<20)==plan.memoryLimitBytes()
            &&number(release,"maximum_session_native_bytes",96L<<20)==plan.maximumSessionNativeBytes()
            &&number(release,"maximum_stderr_bytes",131072)==plan.maximumStderrBytes(),"actual capture process/IO/directory release differs");
        for(String key:List.of("producer_source_ref","whole_build_receipt_ref"))ref(field(release,key));
        for(String key:List.of("own_archive_actual_ref","policy_ref","standing_ref"))retain(ref(field(release,key)),originals,4<<20);
    }
    private static void addPin(FileRef ref,List<FileRef> all,List<SharedSourceFiles.Witness> originals)throws IOException{
        if(all.stream().noneMatch(v->v.path().equals(ref.path()))){retain(ref,originals,4<<20);all.add(ref);}
    }
    private static void retain(FileRef ref,List<SharedSourceFiles.Witness> all,int maximum)throws IOException{
        require(ref.bytes()>0&&ref.bytes()<=maximum,"bounded explicit original input required");var witness=SharedSourceFiles.observe(Path.of(ref.path()));
        require(sameRef(witness.source(),ref),"actual source/input bytes/SHA differ");all.add(witness);
    }
    private static void current(Plan plan)throws IOException{
        Instant now=Instant.now();require(plan.machineId().equals(WindowsJobProcess.currentMachineId())&&!now.isBefore(Instant.parse(plan.observedAtUtc()))&&now.isBefore(Instant.parse(plan.reviewAtUtc())),"capture machine/time scope unavailable");
    }
    private static boolean sameInputs(Plan a,Plan b){return a.machineId().equals(b.machineId())&&sameRef(a.originalRequestRef(),b.originalRequestRef())&&sameRef(a.selectedConfigurationRef(),b.selectedConfigurationRef())&&sameRef(a.pythonExecutableRef(),b.pythonExecutableRef());}
    private static boolean sameRef(FileRef a,FileRef b){return Path.of(a.path()).toAbsolutePath().normalize().equals(Path.of(b.path()).toAbsolutePath().normalize())&&a.bytes()==b.bytes()&&a.sha256().equals(b.sha256());}
    static JsonNode parse(byte[] raw,int maximum)throws IOException{require(raw!=null&&raw.length>0&&raw.length<=maximum,"bounded original capture JSON required");return JSON.readTree(raw);}
    static FileRef ref(JsonNode n)throws IOException{keys(n,Set.of("path","bytes","sha256"));return new FileRef(absolute(text(n,"path")).toString(),number(n,"bytes",64L<<20),text(n,"sha256"));}
    static Extent extent(JsonNode n)throws IOException{keys(n,Set.of("bytes","sha256"));return new Extent(number(n,"bytes",DOCUMENT_MAX),text(n,"sha256"));}
    static Extent extent(byte[] raw){return new Extent(raw.length,sha256(raw));}
    public static String sha256(byte[] raw){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));}catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
    private static JsonNode read(FileRef ref,int maximum)throws IOException{ref.verify();require(ref.bytes()<=maximum,"bounded exact source/control input required");byte[] raw=Files.readAllBytes(Path.of(ref.path()));ref.verify();return parse(raw,maximum);}
    private static JsonNode field(JsonNode n,String key)throws IOException{require(n!=null&&n.isObject()&&n.has(key),"missing original capture field "+key);return n.get(key);}
    private static String text(JsonNode n,String key)throws IOException{JsonNode v=field(n,key);require(v.isTextual(),"exact original capture text required: "+key);return v.textValue();}
    private static boolean bool(JsonNode n,String key)throws IOException{JsonNode v=field(n,key);require(v.isBoolean(),"exact original capture boolean required: "+key);return v.booleanValue();}
    private static boolean yes(JsonNode n,String key)throws IOException{require(bool(n,key),"true original proof required: "+key);return true;}
    private static int count(JsonNode n,String key)throws IOException{return Math.toIntExact(number(n,key,4096));}
    private static long number(JsonNode n,String key,long maximum)throws IOException{JsonNode v=field(n,key);require(v.isIntegralNumber()&&v.canConvertToLong()&&v.longValue()>=0&&v.longValue()<=maximum,"exact bounded original integer required: "+key);return v.longValue();}
    private static List<JsonNode> array(JsonNode n,String key)throws IOException{JsonNode v=field(n,key);require(v.isArray()&&v.size()<=4096,"bounded original array required: "+key);var rows=new ArrayList<JsonNode>();v.forEach(rows::add);return List.copyOf(rows);}
    private static List<String> strings(JsonNode n,String key)throws IOException{var rows=new ArrayList<String>();for(JsonNode v:array(n,key)){require(v.isTextual(),"exact identity text required");rows.add(v.textValue());}return List.copyOf(rows);}
    private static void keys(JsonNode n,Set<String> keys)throws IOException{require(n!=null&&n.isObject()&&n.size()==keys.size(),"closed original capture object required");var actual=new HashSet<String>();n.fieldNames().forEachRemaining(actual::add);require(actual.equals(keys),"wrong/missing original capture fields");}
    private static Path absolute(String value){require(value!=null&&Path.of(value).isAbsolute()&&Path.of(value).normalize().equals(Path.of(value)),"absolute canonical original capture path required");return Path.of(value);}
    private static long size(Path path)throws IOException{return Files.exists(path,LinkOption.NOFOLLOW_LINKS)?Files.size(path):0;}
    private static long allocation(Path root,Path wire,Path stderr)throws IOException{long bytes=4096;for(Path p:List.of(wire,stderr))if(Files.exists(p,LinkOption.NOFOLLOW_LINKS))bytes=Math.addExact(bytes,SharedSourceFiles.nativeFile(p).allocatedBytes());return bytes;}
    private static void machine(String value){require(value!=null&&!value.equals("unknown")&&value.matches("[a-z0-9][a-z0-9-]{0,63}"),"explicit current machine required");}
    private static void require(boolean value,String why){if(!value)throw new IllegalArgumentException(why);}
    private static final String RUNNER="""
        import base64,hashlib,json,pathlib,sys
        envelope=json.loads(pathlib.Path(sys.argv[1]).read_bytes())
        if envelope['schema']!='xar.original-mcp-java-capture-request/v3':
            raise ValueError('explicit Java capture request v3 required')
        request=json.loads(pathlib.Path(envelope['inventory_request_ref']['path']).read_bytes())
        source='\\n'.join(request['code_lines'])
        prefix=source.rsplit('if __name__ == "__main__":',1)[0]
        edits=json.loads(base64.b64decode(sys.argv[6],validate=True))
        if type(edits) is not list or len(edits)!=6:
            raise ValueError('closed Java original-boundary adaptation required')
        for edit in edits:
            if type(edit) is not dict or set(edit)!={'before','after'} or prefix.count(edit['before'])!=1:
                raise ValueError('exact original-boundary anchor differs')
            prefix=prefix.replace(edit['before'],edit['after'],1)
        exec(compile(prefix,'<same-original-mcp-capture-v4-boundary>','exec'),globals())
        request['selected_configuration_producer_ref']=envelope['selected_configuration_producer_ref']
        configuration_ref={'path':sys.argv[2],'bytes':int(sys.argv[3]),'sha256':sys.argv[4]}
        if sys.argv[5]=='MEASURE':
            sys.stdout.buffer.write(encoded(measure(request,configuration_ref))+b'\\n')
        elif sys.argv[5]=='CAPTURE':
            documents=capture(request,configuration_ref)
            for role in ('catalog','tools','resources','registration_facts','inventory_proof'):
                raw=getattr(documents,role)
                row={'kind':'document','role':role,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode('ascii')}
                sys.stdout.buffer.write(encoded(row)+b'\\n')
            sys.stdout.buffer.write(encoded({'kind':'end','actual_pipe':documents.transport_pipe,'actual_uncreated_state':documents.transport_state,'actual_listener_closed':True})+b'\\n')
        else:
            raise ValueError('unknown exact original capture phase')
        sys.stdout.buffer.flush()
        """;
}
