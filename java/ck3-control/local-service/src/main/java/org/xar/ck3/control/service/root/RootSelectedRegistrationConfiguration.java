package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.FrontendFixturePolicy;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture;
import org.xar.ck3.control.service.mcp.McpCoverage;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** The explicit original registration target. Registration flags select original declarations only;
 * neither a selected flag nor an excluded fixture issues Java routes, Native permission or Game Ready.
 * Its inputs precede final MCP/admission/definitions/startup files, avoiding a content-hash cycle. */
public final class RootSelectedRegistrationConfiguration {
    public static final String SCHEMA="xar.original-mcp-current-configuration/v4";
    public static final String INTENT_SCHEMA="xar.java-root-selected-intent/v3";
    public static final int MAXIMUM_BYTES=65536;
    private static final Set<String> FIELDS=Set.of("schema","machine_id","observed_at_utc","review_at_utc","intent",
            "configuration_producer","source_inputs","constructor_keywords","registration_attributes","fixture_policy","profile_directory");
    private static final String SCENARIO="ck3_submit_frontend_fixture_scenario_start_v1";
    private static final String ROBERT_FIXTURE="ck3_submit_frontend_fixture_robert_start_v1";
    private static final String FIXTURE_PRESENT="fixture_binding is not None";
    private static final String SCENARIO_PRESENT="isinstance(fixture_binding, dict) and fixture_binding.get(\"profile_id\") is not None";
    private RootSelectedRegistrationConfiguration(){ }
    public enum Intent {
        FRESH_ROBERT_1066_ALL_ORDINARY,EXPLICIT_ROBERT_FIXTURE,EXPLICIT_SCENARIO_FIXTURE,SAVED_GAME_ALL_ORDINARY,SAVED_NATIVE_CAMPAIGN;
        public boolean fixture(){return this==EXPLICIT_ROBERT_FIXTURE||this==EXPLICIT_SCENARIO_FIXTURE;}
        public boolean saved(){return this==SAVED_GAME_ALL_ORDINARY||this==SAVED_NATIVE_CAMPAIGN;}
        public boolean nativeCampaign(){return fixture()||this==SAVED_NATIVE_CAMPAIGN;}
        public String entryKind(){return saved()?(this==SAVED_NATIVE_CAMPAIGN?"SAVED_NATIVE_CAMPAIGN":"SAVED_GAME"):(this==EXPLICIT_SCENARIO_FIXTURE?"FRESH_SCENARIO_FIXTURE":"FRESH_ROBERT_1066");}
        public FrontendFixturePolicy.Kind fixtureKind(){require(fixture(),"ordinary intent has no fixture kind");return this==EXPLICIT_SCENARIO_FIXTURE?FrontendFixturePolicy.Kind.SCENARIO:FrontendFixturePolicy.Kind.ROBERT;}
    }
    public enum SourceRole { ROOT_INTENT,DOMAIN_SETTINGS,CAPABILITY_CONFIGURATION,LIFE_SETTINGS,RUN_PROFILE,
        ORIGINAL_MCP_SERVER,ORIGINAL_NATIVE_DRIVER,ORIGINAL_SERVICE,ORIGINAL_FIXTURE }
    /** A closed enumeration of actual registration boolean attributes, never arbitrary getattr/method names. */
    public enum RegistrationFlag {
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
        private final String wire;RegistrationFlag(String wire){this.wire=wire;}public String wire(){return wire;}
    }
    public record SourceInput(SourceRole role,ExactRef originalRef) {
        public SourceInput {Objects.requireNonNull(role);file(originalRef,4<<20);}
    }
    /** Root writes this explicit request before capture/admission/final definitions. No implied private=false profile. */
    public record IntentRequest(String machineId,Instant observedAt,Instant reviewAt,Intent intent,
            Optional<ExactRef> fixturePolicy,Optional<Path> profileDirectory) {
        public IntentRequest(String machineId,Instant observedAt,Instant reviewAt,Intent intent){this(machineId,observedAt,reviewAt,intent,Optional.empty(),Optional.empty());}
        public IntentRequest {period(machineId,observedAt,reviewAt);Objects.requireNonNull(intent);Objects.requireNonNull(fixturePolicy);Objects.requireNonNull(profileDirectory);
            require(fixturePolicy.isPresent()==intent.fixture()&&profileDirectory.isPresent()==(intent.fixture()||intent.saved()),"fixture intent requires both exact policy and profile; ordinary requires explicit absence");
            fixturePolicy.ifPresent(ref->file(ref,1<<20));profileDirectory.ifPresent(RootSelectedRegistrationConfiguration::absolute);}
    }
    /** Serialized registration facts, never the private prepared producer or Game permission. */
    public record FixtureSelection(FrontendFixturePolicy.Binding binding,Path profileDirectory) {
        public FixtureSelection {Objects.requireNonNull(binding);absolute(profileDirectory);}
    }
    public record ConstructorKeywords(int routeContactTimelineSpeed,boolean allowRouteContactHighSpeedAb,
            boolean stationaryObjectiveHoldCanaryRequested,boolean warDailyWatchEnabled,Optional<SuccessionLifecycleBinding> lifecycle) {
        public ConstructorKeywords(int speed,boolean ab,boolean canary,boolean watch,SuccessionLifecycleBinding lifecycle){this(speed,ab,canary,watch,Optional.of(Objects.requireNonNull(lifecycle)));}
        public ConstructorKeywords {require(routeContactTimelineSpeed>=1&&routeContactTimelineSpeed<=5,"explicit route speed 1..5 required");
            require(routeContactTimelineSpeed<=3||allowRouteContactHighSpeedAb,"speed 4..5 needs explicit existing A/B request");Objects.requireNonNull(lifecycle);
            lifecycle.ifPresent(binding->require(binding.profile()!=SuccessionLifecycleBinding.Profile.UNKNOWN,"selected lifecycle cannot be unknown"));}
    }
    public record Configuration(String machineId,Instant observedAt,Instant reviewAt,Intent intent,
            ExactRef configurationProducer,List<SourceInput> sourceInputs,ConstructorKeywords constructorKeywords,Optional<FixtureSelection> fixture,Optional<Path> savedProfileDirectory) {
        public Configuration(String machineId,Instant observedAt,Instant reviewAt,Intent intent,ExactRef configurationProducer,List<SourceInput> sourceInputs,ConstructorKeywords constructorKeywords,Optional<FixtureSelection> fixture){
            this(machineId,observedAt,reviewAt,intent,configurationProducer,sourceInputs,constructorKeywords,fixture,Optional.empty());}
        public Configuration(String machineId,Instant observedAt,Instant reviewAt,Intent intent,ExactRef configurationProducer,List<SourceInput> sourceInputs,ConstructorKeywords constructorKeywords){
            this(machineId,observedAt,reviewAt,intent,configurationProducer,sourceInputs,constructorKeywords,Optional.empty(),Optional.empty());}
        public Configuration {
            period(machineId,observedAt,reviewAt);Objects.requireNonNull(intent);file(configurationProducer,4<<20);
            sourceInputs=List.copyOf(sourceInputs);Objects.requireNonNull(constructorKeywords);Objects.requireNonNull(fixture);Objects.requireNonNull(savedProfileDirectory);
            require(savedProfileDirectory.isPresent()==intent.saved(),"Saved intent requires its explicit current profile directory");savedProfileDirectory.ifPresent(RootSelectedRegistrationConfiguration::absolute);
            require(fixture.isPresent()==intent.fixture(),"explicit fixture selection must agree with the selected intent");
            require(constructorKeywords.lifecycle().isEmpty()==intent.nativeCampaign(),"native_campaign requires null lifecycle; ordinary requires its original binding");
            fixture.ifPresent(value->require(value.binding().kind()==intent.fixtureKind(),"fixture policy kind differs from the selected tool"));
            require(sourceInputs.size()==SourceRole.values().length&&sourceInputs.stream().map(SourceInput::role).distinct().count()==SourceRole.values().length,
                    "every exact selected source role required once");
            require(sourceInputs.stream().map(row->Path.of(row.originalRef().path())).distinct().count()==sourceInputs.size(),"different selected input roles require distinct originals");
        }
        public ExactRef source(SourceRole role){return sourceInputs.stream().filter(row->row.role()==role).findFirst().orElseThrow().originalRef();}
    }
    public static byte[] encodeIntent(IntentRequest value) {
        var root=StrictJson.object().put("schema",INTENT_SCHEMA).put("machine_id",value.machineId())
                .put("observed_at_utc",value.observedAt().toString()).put("review_at_utc",value.reviewAt().toString())
                .put("intent",value.intent().name()).put("entry_kind",value.intent().entryKind()).put("ordinary_production_capabilities","ALL");
        if(value.fixturePolicy().isPresent())root.set("fixture_policy",value.fixturePolicy().orElseThrow().toJson());else root.putNull("fixture_policy");
        if(value.profileDirectory().isPresent())root.put("profile_directory",value.profileDirectory().orElseThrow().toString());else root.putNull("profile_directory");
        return StrictJson.canonical(root,MAXIMUM_BYTES);
    }
    public static IntentRequest decodeIntent(byte[] bytes) {
        var root=StrictJson.object(StrictJson.parse(bytes,MAXIMUM_BYTES),Set.of("schema","machine_id","observed_at_utc","review_at_utc","intent",
                "entry_kind","ordinary_production_capabilities","fixture_policy","profile_directory"));
        Intent intent=Intent.valueOf(text(root,"intent"));
        require(INTENT_SCHEMA.equals(text(root,"schema"))&&intent.entryKind().equals(text(root,"entry_kind"))
                &&"ALL".equals(text(root,"ordinary_production_capabilities")),"explicit entry/all ordinary request required");
        Optional<ExactRef> policy=root.get("fixture_policy").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(root.get("fixture_policy")));
        Optional<Path> profile=root.get("profile_directory").isNull()?Optional.empty():Optional.of(Path.of(text(root,"profile_directory")));
        return new IntentRequest(text(root,"machine_id"),instant(root.get("observed_at_utc")),instant(root.get("review_at_utc")),intent,policy,profile);
    }
    /** The one selected-configuration encoder also supplies the original MCP capture input. */
    public static byte[] encode(Configuration value) {
        var root=StrictJson.object().put("schema",SCHEMA).put("machine_id",value.machineId()).put("observed_at_utc",value.observedAt().toString())
                .put("review_at_utc",value.reviewAt().toString()).put("intent",value.intent().name());
        root.set("configuration_producer",value.configurationProducer().toJson());var sources=root.putArray("source_inputs");
        for(SourceRole role:SourceRole.values())sources.addObject().put("role",role.name()).set("original_ref",value.source(role).toJson());
        var constructor=root.putObject("constructor_keywords");var chosen=value.constructorKeywords();
        constructor.put("route_contact_timeline_speed",chosen.routeContactTimelineSpeed()).put("allow_route_contact_high_speed_ab",chosen.allowRouteContactHighSpeedAb())
                .put("allow_stationary_objective_hold_sentinel_canary",chosen.stationaryObjectiveHoldCanaryRequested())
                .put("allow_war_daily_watch_v1",chosen.warDailyWatchEnabled()).put("episode_projection",value.intent().nativeCampaign()?"native_campaign":"one_life");
        if(chosen.lifecycle().isPresent())constructor.set("succession_lifecycle_binding",StrictJson.parse(SuccessionLifecycleCodec.encode(chosen.lifecycle().orElseThrow()),SuccessionLifecycleCodec.MAX_BYTES));
        else constructor.putNull("succession_lifecycle_binding");
        var flags=root.putObject("registration_attributes");for(var flag:RegistrationFlag.values())flags.put(flag.wire(),true);
        if(value.fixture().isPresent()){var fixture=value.fixture().orElseThrow();root.set("fixture_policy",fixture.binding().toJson());root.put("profile_directory",fixture.profileDirectory().toString());}
        else {root.putNull("fixture_policy");if(value.savedProfileDirectory().isPresent())root.put("profile_directory",value.savedProfileDirectory().orElseThrow().toString());else root.putNull("profile_directory");}return StrictJson.canonical(root,MAXIMUM_BYTES);
    }
    public static Configuration decode(byte[] bytes) {
        var root=StrictJson.object(StrictJson.parse(bytes,MAXIMUM_BYTES),FIELDS);require(SCHEMA.equals(text(root,"schema")),"selected configuration version changed");
        Intent intent=Intent.valueOf(text(root,"intent"));Optional<FixtureSelection> fixture;
        if(intent.fixture())fixture=Optional.of(new FixtureSelection(FrontendFixturePolicy.Binding.fromJson(root.get("fixture_policy")),Path.of(text(root,"profile_directory"))));
        else {require(root.get("fixture_policy").isNull()&&(intent.saved()?!root.get("profile_directory").isNull():root.get("profile_directory").isNull()),"ordinary configuration requires explicit null fixture/profile");fixture=Optional.empty();}
        JsonNode rows=root.get("source_inputs");require(rows.isArray()&&rows.size()==SourceRole.values().length,"complete typed source input rows required");
        var originals=new ArrayList<SourceInput>();for(JsonNode value:rows){var row=StrictJson.object(value,Set.of("role","original_ref"));
            originals.add(new SourceInput(SourceRole.valueOf(text(row,"role")),ExactRef.fromJson(row.get("original_ref"))));}
        var flags=StrictJson.object(root.get("registration_attributes"),Arrays.stream(RegistrationFlag.values()).map(RegistrationFlag::wire).collect(java.util.stream.Collectors.toUnmodifiableSet()));
        for(var flag:RegistrationFlag.values())require(booleanValue(flags.get(flag.wire())),"all ordinary registration targets must be explicitly true: "+flag.wire());
        var constructor=StrictJson.object(root.get("constructor_keywords"),Set.of("route_contact_timeline_speed","allow_route_contact_high_speed_ab",
                "allow_stationary_objective_hold_sentinel_canary","allow_war_daily_watch_v1","episode_projection","succession_lifecycle_binding"));
        require((intent.nativeCampaign()?"native_campaign":"one_life").equals(text(constructor,"episode_projection")),"explicit fixture/ordinary projection differs from the selected intent");
        var chosen=new ConstructorKeywords((int)StrictJson.integer(constructor.get("route_contact_timeline_speed"),1,5),booleanValue(constructor.get("allow_route_contact_high_speed_ab")),
                booleanValue(constructor.get("allow_stationary_objective_hold_sentinel_canary")),booleanValue(constructor.get("allow_war_daily_watch_v1")),
                constructor.get("succession_lifecycle_binding").isNull()?Optional.empty():Optional.of(SuccessionLifecycleCodec.decode(StrictJson.canonical(constructor.get("succession_lifecycle_binding"),SuccessionLifecycleCodec.MAX_BYTES))));
        return new Configuration(text(root,"machine_id"),instant(root.get("observed_at_utc")),instant(root.get("review_at_utc")),Intent.valueOf(text(root,"intent")),
                ExactRef.fromJson(root.get("configuration_producer")),originals,chosen,fixture,intent.saved()?Optional.of(Path.of(text(root,"profile_directory"))):Optional.empty());
    }
    /** Actual pre-Core producer: exact source input files are decoded by their existing sole codecs.
     * Public Configuration construction/encoding alone is not the private Bound issuer. */
    public static Configuration produce(ExactRef actualProducer,List<SourceInput> actualInputs,RootFrozenRunProfile.FrozenRunProfile actualProfile,
            NativeLaunchPlan samePlan,Clock clock)throws IOException {
        Objects.requireNonNull(actualProfile);Objects.requireNonNull(samePlan);Objects.requireNonNull(clock);
        var intentRef=actualInputs.stream().filter(row->row.role()==SourceRole.ROOT_INTENT).findFirst().orElseThrow().originalRef();
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();var intent=decodeIntent(read(intentRef,MAXIMUM_BYTES,witnesses));
        Instant observed=intent.observedAt().isAfter(actualProfile.request().observedAt())?intent.observedAt():actualProfile.request().observedAt();
        Instant review=intent.reviewAt().isBefore(actualProfile.request().reviewAt())?intent.reviewAt():actualProfile.request().reviewAt();
        var provisional=new Configuration(actualProfile.request().machineId(),observed,review,
                intent.intent(),actualProducer,actualInputs,
                new ConstructorKeywords(1,false,false,false,actualProfile.lifecycleBinding()),fixtureSelection(intent,actualProfile,samePlan),intent.intent().saved()?Optional.of(samePlan.profileDirectory()):Optional.empty());
        return rederive(provisional,actualProfile,samePlan,clock,witnesses);
    }
    public static Bound readExact(ExactRef original,RootRuntimeDefinitions.Inputs actualInputs,
            RootFrozenRunProfile.FrozenRunProfile actualProfile,NativeLaunchPlan samePlan,Clock clock)throws IOException {
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();
        try {
            Configuration selected=decode(read(original,MAXIMUM_BYTES,witnesses));
            Configuration actual=rederive(selected,actualProfile,samePlan,clock,witnesses);
            require(Arrays.equals(encode(selected),encode(actual)),"selected constructor facts differ from actual original settings/lifecycle");
            var sources=new RootRuntimeSelectedSources(actualInputs);
            require(sources.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootSelectedRegistrationConfiguration.class).equals(selected.configurationProducer()),"selected configuration producer differs from the current Java winner");
            Bound bound=new Bound(original,selected,actualInputs,actualProfile,samePlan,witnesses);bound.requireInputs(actualInputs);return bound;
        }catch(IllegalArgumentException invalid){throw new IOException("selected actual registration configuration is unavailable or incompatible",invalid);}
    }
    private static Configuration rederive(Configuration selected,RootFrozenRunProfile.FrozenRunProfile actualProfile,
            NativeLaunchPlan plan,Clock clock,List<SharedSourceFiles.Witness> witnesses)throws IOException {
        actualProfile.requireCurrent(plan,clock);
        require(selected.machineId().equals(actualProfile.request().machineId()),"selected registration belongs to another actual profile machine");
        require(selected.intent().saved()?plan.load() instanceof NativeLaunchPlan.SavedGame:plan.load() instanceof NativeLaunchPlan.NewGame,"selected Saved/fresh intent differs from the identical actual load plan");
        require(selected.savedProfileDirectory().equals(selected.intent().saved()?Optional.of(plan.profileDirectory()):Optional.empty()),"selected Saved profile differs from the original plan");
        require(selected.source(SourceRole.RUN_PROFILE).equals(actualProfile.requestReference()),"selected configuration has another frozen run request");
        IntentRequest intent=decodeIntent(read(selected.source(SourceRole.ROOT_INTENT),MAXIMUM_BYTES,witnesses));
        require(intent.machineId().equals(selected.machineId())&&intent.intent()==selected.intent(),"selected target differs from the actual preceding Root request");
        Optional<FixtureSelection> fixture=fixtureSelection(intent,actualProfile,plan);
        require(fixture.equals(selected.fixture()),"selected fixture binding/profile differs from the identical frozen prepared producer");
        require(fileName(selected.configurationProducer()).equals("RootSelectedRegistrationConfiguration.java"),
                "explicit Java configuration-producer metadata role required");
        require(fileName(selected.source(SourceRole.ORIGINAL_MCP_SERVER)).equals("mcp_server.py")
                &&fileName(selected.source(SourceRole.ORIGINAL_NATIVE_DRIVER)).equals("native_driver.py")
                &&fileName(selected.source(SourceRole.ORIGINAL_SERVICE)).equals("service.py")
                &&fileName(selected.source(SourceRole.ORIGINAL_FIXTURE)).equals("frontend_fixture_start_contract.py"),"exact original producer roles required");
        var domain=RootRuntimeDomainSettings.readExact(file(selected.source(SourceRole.DOMAIN_SETTINGS)),clock);domain.requireCurrent(clock);
        // This single existing decoder enforces all six actual route configuration fields and JSON integer types.
        var capability=DynamicCapabilities.decodeConfiguration(DriverJson.object(read(selected.source(SourceRole.CAPABILITY_CONFIGURATION),MAXIMUM_BYTES,witnesses),MAXIMUM_BYTES));
        var life=RootAdvanceRuntimeFacts.Settings.decode(selected.source(SourceRole.LIFE_SETTINGS),new RawJson(read(selected.source(SourceRole.LIFE_SETTINGS),RootAdvanceRuntimeFacts.SETTINGS_MAX_BYTES,witnesses)));
        require(domain.configuration().machineId().equals(selected.machineId()),"domain settings belong to another machine");
        require(capability.stateDir().isPresent()&&capability.stateDir().orElseThrow().equals(plan.stateDirectory()),"registration route configuration differs from the actual plan state directory");
        return new Configuration(selected.machineId(),selected.observedAt(),selected.reviewAt(),selected.intent(),selected.configurationProducer(),selected.sourceInputs(),
                new ConstructorKeywords(capability.routeContactTimelineSpeed(),capability.allowRouteContactHighSpeedAb(),
                        capability.stationaryObjectiveHoldCanaryRequested(),life.warDailyWatchEnabled(),actualProfile.lifecycleBinding()),fixture,selected.savedProfileDirectory());
    }
    private static Optional<FixtureSelection> fixtureSelection(IntentRequest intent,RootFrozenRunProfile.FrozenRunProfile profile,NativeLaunchPlan plan)throws IOException {
        if(intent.intent().saved()) {
            require(intent.profileDirectory().orElseThrow().equals(plan.profileDirectory())&&plan.load() instanceof NativeLaunchPlan.SavedGame,"Saved intent requires the exact current profile/load");
            if(intent.intent()==Intent.SAVED_NATIVE_CAMPAIGN){require(profile.importMode() instanceof RootFrozenRunProfile.EnabledNativeCampaign,"Saved native intent requires its explicit native import mode");profile.requireExplicitNativeCampaign();}
            else require(profile.importMode() instanceof RootFrozenRunProfile.Enabled&&profile.lifecycleBinding().isPresent(),"Saved ordinary intent requires the original bound import mode");
            require(profile.fixture().isEmpty(),"Saved import cannot retain a fresh fixture submitter");return Optional.empty();
        }
        if(!intent.intent().fixture()) {
            require(profile.importMode() instanceof RootFrozenRunProfile.DisabledFreshRobert&&profile.fixture().isEmpty(),"ordinary request cannot select a fixture or earlier driver import");
            return Optional.empty();
        }
        require(profile.importMode() instanceof RootFrozenRunProfile.DisabledFreshFixture,"fixture request requires its distinct explicit fresh-fixture import mode");
        PreparedFixture actual=profile.fixture().orElseThrow(()->new IOException("fixture request lacks the sole private prepared producer"));
        require(actual.policySource().equals(intent.fixturePolicy().orElseThrow())&&actual.profileDirectory().equals(intent.profileDirectory().orElseThrow())
                &&actual.stateDir().equals(plan.stateDirectory())&&actual.profileDirectory().equals(plan.profileDirectory()),"fixture request crossed exact policy/state/profile inputs");
        require(actual.policy().kind()==intent.intent().fixtureKind(),"fixture policy selects another public tool");actual.verifySources();
        return Optional.of(new FixtureSelection(actual.binding(),actual.profileDirectory()));
    }
    public static final class Bound {
        private final ExactRef original;private final Configuration configuration;private final RootRuntimeDefinitions.Inputs inputs;
        private final RootFrozenRunProfile.FrozenRunProfile profile;private final NativeLaunchPlan plan;private final List<SharedSourceFiles.Witness> witnesses;
        private Bound(ExactRef original,Configuration configuration,RootRuntimeDefinitions.Inputs inputs,RootFrozenRunProfile.FrozenRunProfile profile,
                NativeLaunchPlan plan,List<SharedSourceFiles.Witness> witnesses){this.original=original;this.configuration=configuration;this.inputs=inputs;this.profile=profile;this.plan=plan;this.witnesses=List.copyOf(witnesses);}
        public ExactRef original(){return original;}
        public Configuration configuration(){return configuration;}
        /** Same actual constructor scope only; reading retained admission DATA does not renew old source periods. */
        public void requireInputs(RootRuntimeDefinitions.Inputs same)throws IOException {
            if(same!=inputs)throw new IOException("registration configuration belongs to another actual Inputs product");
            if(!same.application().machineId().equals(configuration.machineId())||!same.configuration().machineId().equals(configuration.machineId()))throw new IOException("selected registration machine differs from actual application/runtime inputs");
            for(var pair:List.of(new DataSelection(SourceRole.DOMAIN_SETTINGS,RootRuntimeDefinitionModel.DataRole.REMAINING_DOMAIN_SETTINGS),
                    new DataSelection(SourceRole.CAPABILITY_CONFIGURATION,RootRuntimeDefinitionModel.DataRole.CAPABILITY_CONFIGURATION),
                    new DataSelection(SourceRole.LIFE_SETTINGS,RootRuntimeDefinitionModel.DataRole.LIFE_SETTINGS)))
                if(!configuration.source(pair.source()).equals(exact(same.data(pair.data()))))throw new IOException("actual runtime definitions changed the selected original data: "+pair.source());
            if(!exact(same.configuration().nativeLaunchPlanRef()).equals(same.application().nativeLaunchPlan()))throw new IOException("selected application/runtime use another launch plan original");
            if(!same.configuration().family().familyEnabled()||!same.configuration().family().childFocusEnabled()||!same.configuration().family().childDefaultEnabled())throw new IOException("all ordinary selection cannot hide disabled family policies");
        }
        /** Explicit original acquisition/history boundary retained for callers which still request it. */
        public void requireCurrent(RootRuntimeDefinitions.Inputs same,Clock clock)throws IOException {
            requireInputs(same);
            current(configuration,clock);profile.requireCurrent(plan,clock);same.application().requireCurrent(clock);
            for(var witness:witnesses)SharedSourceFiles.assertUnchanged(witness);
        }
        /** No arbitrary condition evaluator: only the two explicit fixture branches can be excluded here.
         * Callable/method absence, missing providers and unimplemented ordinary routes remain gaps. */
        public Optional<Exclusion> exclusion(McpCoverage.Declaration declaration,List<String> actualRegisteredToolNames)throws IOException {
            Objects.requireNonNull(declaration);List<String> actual=List.copyOf(actualRegisteredToolNames);
            if(actual.contains(declaration.name()))return Optional.empty();
            if(!declaration.source().equals(configuration.source(SourceRole.ORIGINAL_MCP_SERVER)))return Optional.empty();
            String clause=fixtureFalseClause(configuration,declaration);if(clause==null)return Optional.empty();
            return Optional.of(new Exclusion(this,declaration.name(),declaration.source(),clause));
        }
    }
    private record DataSelection(SourceRole source,RootRuntimeDefinitionModel.DataRole data){ }
    public enum Predicate { FIXTURE_POLICY_ABSENT,FIXTURE_OTHER_PROFILE }
    public static final class Exclusion {
        private final Bound owner;private final String name;private final ExactRef declarationSource;private final String falseClause;
        private Exclusion(Bound owner,String name,ExactRef declarationSource,String falseClause){this.owner=owner;this.name=name;this.declarationSource=declarationSource;this.falseClause=falseClause;}
        public ExactRef configurationOriginal(){return owner.original();}public String name(){return name;}
        public ExactRef declarationSource(){return declarationSource;}public String falseClause(){return falseClause;}
        public Predicate predicate(){return owner.configuration.fixture().isEmpty()?Predicate.FIXTURE_POLICY_ABSENT:Predicate.FIXTURE_OTHER_PROFILE;}
        public void require(Bound same,McpCoverage.Declaration declaration,List<String> actualRegisteredToolNames)throws IOException {
            if(same!=owner||!name.equals(declaration.name())||!declarationSource.equals(declaration.source())||actualRegisteredToolNames.contains(name)
                    ||!Objects.equals(falseClause,fixtureFalseClause(owner.configuration,declaration)))throw new IOException("fixture exclusion lost the same selected configuration/actual declaration/absent registration");
        }
    }
    static String fixtureFalseClause(Configuration selected,McpCoverage.Declaration declaration) {
        if(selected.fixture().isPresent()&&selected.fixture().orElseThrow().binding().kind()==(declaration.name().equals(SCENARIO)?FrontendFixturePolicy.Kind.SCENARIO:FrontendFixturePolicy.Kind.ROBERT))return null;
        if(!Set.of(SCENARIO,ROBERT_FIXTURE).contains(declaration.name()))return null;
        String required=declaration.name().equals(SCENARIO)?SCENARIO_PRESENT:selected.fixture().isPresent()?"NOT("+SCENARIO_PRESENT+")":FIXTURE_PRESENT;
        return declaration.conditions().stream().filter(clause->normalize(clause).equals(normalize(required))).findFirst().orElse(null);
    }
    private static String normalize(String clause){return clause.replaceAll("\\s+","").replace("'","\"");}
    private static void current(Configuration value,Clock clock)throws IOException {
        Instant now=Objects.requireNonNull(clock).instant();if(!value.machineId().equals(WindowsJobProcess.currentMachineId())||now.isBefore(value.observedAt())||!now.isBefore(value.reviewAt()))
            throw new IOException("selected registration configuration is foreign/future/expired");
    }
    /** Physical custody only; the same-package Windows regression exercises this actual read without issuing Bound. */
    static byte[] read(ExactRef ref,int maximum,List<SharedSourceFiles.Witness> witnesses)throws IOException {
        file(ref,maximum);var before=SharedSourceFiles.observe(Path.of(ref.path()));
        require(Path.of(before.source().path()).equals(Path.of(ref.path()))&&before.source().bytes()==ref.bytes()
                &&before.source().sha256().equals(ref.sha256()),"original source differs from its selected exact ref");
        byte[] raw;try(var input=Files.newInputStream(Path.of(ref.path()))){raw=input.readNBytes(maximum+1);}
        require(raw.length==ref.bytes()&&DriverJson.sha256(raw).equals(ref.sha256()),"complete selected input content differs");SharedSourceFiles.assertUnchanged(before);witnesses.add(before);return raw;
    }
    private static void period(String machine,Instant observed,Instant review){require(machine!=null&&machine.matches("[a-z0-9][a-z0-9-]{0,127}")&&!machine.equals("unknown"),"actual machine required");
        require(observed!=null&&review!=null&&observed.isBefore(review)&&Duration.between(observed,review).compareTo(Duration.ofDays(7))<=0,"finite explicit selected-input period required");}
    private static void absolute(Path path){require(path!=null&&path.isAbsolute()&&path.normalize().equals(path),"absolute normalized profile directory required");}
    private static String fileName(ExactRef ref){return Path.of(ref.path()).getFileName().toString();}
    private static FileRef file(ExactRef ref){return new FileRef(ref.path(),ref.bytes(),ref.sha256());}
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static void file(ExactRef ref,int maximum){Objects.requireNonNull(ref);Path path=Path.of(ref.path());require(path.isAbsolute()&&path.normalize().equals(path)&&ref.bytes()>0&&ref.bytes()<=maximum,"absolute bounded exact selected source required");}
    private static String text(JsonNode root,String field){return StrictJson.text(root.get(field));}
    private static boolean booleanValue(JsonNode value){require(value!=null&&value.isBoolean(),"explicit JSON boolean required");return value.booleanValue();}
    private static Instant instant(JsonNode value){String raw=StrictJson.text(value);Instant result=Instant.parse(raw);require(result.toString().equals(raw),"canonical UTC instant required");return result;}
    private static void require(boolean value,String reason){if(!value)throw new IllegalArgumentException(reason);}
}
