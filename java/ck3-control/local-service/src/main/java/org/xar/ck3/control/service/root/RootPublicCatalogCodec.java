package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.McpCoverage;
import org.xar.ck3.control.service.mcp.PublicMcpNativeAdapter;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ResourceDescriptor;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolDescriptor;

/** One typed representation for the four original public-catalog runtime input documents. */
public final class RootPublicCatalogCodec {
    public static final String ADMISSION_SCHEMA = "xar.java-public-mcp-admission/v1";
    public static final String TOOLS_SCHEMA = "xar.java-public-mcp-tools/v1";
    public static final String RESOURCES_SCHEMA = "xar.java-public-mcp-resources/v1";
    // Exact source-owned Activity query revisions; all other fields retain their original schema.
    private static final Set<String> ACTIVITY_PRIVATE_READS = Set.of(
            "ck3_query_activity_feast_stage5_start_inputs_private_v1",
            "ck3_query_activity_feast_hosted_post_private_v1",
            "ck3_query_activity_stage5_feast_full_cost_private_v1",
            "ck3_query_activity_feast_guest_candidate_private_v1",
            "ck3_query_activity_feast_guest_opinion_private_v1",
            "ck3_query_activity_feast_guest_target_private_v1",
            "ck3_query_activity_feast_guest_route_proof_private_v1",
            "ck3_query_activity_feast_guest_rule_provenance_private_v1");
    private static final Set<String> COA_SOURCE_UPLOAD = Set.of(
            "ck3_begin_coat_of_arms_source_upload_v2","ck3_append_coat_of_arms_source_chunk_v2",
            "ck3_commit_coat_of_arms_source_upload_v2","ck3_abort_coat_of_arms_source_upload_v2",
            "ck3_probe_coat_of_arms_source_v1","ck3_export_coat_of_arms_source_v1");
    private static final Set<String> ADDITIONAL_POSITIVE = Set.of(
            "ck3_query_council_composition_candidates_private_v1",
            "ck3_query_council_final_gates_private_v1",
            "ck3_assign_councillor_private_v1",
            "ck3_query_council_assign_receipt_private_v1",
            "ck3_query_realm_law_final_terms_private_v1",
            "ck3_query_realm_law_crown_action_private_v1",
            "ck3_query_realm_law_crown_receipt_private_v1",
            "ck3_query_government_runtime_adapter_private_v1",
            "ck3_confirm_holy_site_adoption_decision_v1",
            "ck3_confirm_holy_site_decision_v1",
            "ck3_convert_player_religion_private_v1",
            "ck3_create_holy_site_once_v1",
            "ck3_open_holy_site_adoption_decision_v1",
            "ck3_open_holy_site_creation_window_v1",
            "ck3_open_holy_site_decision_v1",
            "ck3_open_holy_site_window_v1",
            "ck3_query_confucian_assembly_predicates_v1",
            "ck3_query_confucian_challenger_graph_v1",
            "ck3_query_confucian_religious_title_v1",
            "ck3_query_county_conversion_task_result",
            "ck3_query_current_actor_stress_adjustment_v1",
            "ck3_query_player_clergy_appointment_v1",
            "ck3_query_player_epidemic_recovery_private_v1",
            "ck3_query_player_ghw_permissions_v1",
            "ck3_query_player_head_of_faith_gold_context_v1",
            "ck3_query_player_holy_order_context_v1",
            "ck3_query_player_holy_order_loan_context_v1",
            "ck3_query_player_holy_order_selected_title_terms_v1",
            "ck3_query_player_holy_site_adoption_detail_v1",
            "ck3_query_player_holy_site_creation_context_v1",
            "ck3_query_player_holy_site_decision_cooldown_v1",
            "ck3_query_player_holy_site_decision_detail_v1",
            "ck3_query_player_holy_site_v1",
            "ck3_query_player_pilgrimage_activities_v1",
            "ck3_query_player_pilgrimage_planner_v1",
            "ck3_query_player_religion_ai_reform_inputs_v1",
            "ck3_query_player_religion_context_v1",
            "ck3_query_player_religion_conversion_choices_v1",
            "ck3_query_player_religion_conversion_inputs_v1",
            "ck3_query_player_religion_conversion_outcome_v1",
            "ck3_query_player_religion_conversion_reasons_v1",
            "ck3_query_player_religion_conversion_result_private_v1",
            "ck3_query_player_religion_conversion_terms_v1",
            "ck3_query_player_religion_doctrine_catalogue_v1",
            "ck3_query_player_religion_doctrine_knowledge_v1",
            "ck3_query_player_religion_doctrines_v1",
            "ck3_query_player_religion_draft_doctrine_choices_v1",
            "ck3_query_player_religion_draft_groups_v1",
            "ck3_query_player_religion_draft_resource_costs_v1",
            "ck3_query_player_religion_draft_tenet_choices_v1",
            "ck3_query_player_religion_hostility_v1",
            "ck3_query_player_religion_numeric_special_parameters_v1",
            "ck3_query_player_religion_personal_parameters_v1",
            "ck3_query_player_religion_reform_context_v1",
            "ck3_query_player_religion_tenets_v1",
            "ck3_query_player_repentance_context_v1",
            "ck3_query_player_rite_governance_v1",
            "ck3_query_player_rite_members_v1",
            "ck3_query_player_seek_indulgences_terms_v1",
            "ck3_select_holy_site_creation_barony_v1",
            "ck3_select_holy_site_creation_type_v1",
            "ck3_submit_county_conversion_task",
            "ck3_submit_player_pilgrimage_planner_v1",
            "ck3_set_army_observer_research_sampling_v1",
            "ck3_query_army_observer_research_sampling_v1",
            "ck3_set_army_private_auto_scalar_ab_v1",
            "ck3_query_army_private_auto_scalar_ab_v1",
            "ck3_compare_army_private_auto_scalar_ab_v1");
    private static final Set<String> ADDITIONAL_ZERO = Set.of(
            "ck3_query_player_faction_alerts_v1",
            "ck3_query_zhongguo_career_hc_workforce_postcondition_v1",
            "ck3_query_zhongguo_manager_governance_snapshot_v1",
            "ck3_query_zhongguo_manager_subordinate_selector_v1",
            "ck3_query_zhongguo_workforce_collective_snapshot_v1",
            "ck3_query_zhongguo_workforce_normal_exit_snapshot_v1",
            "ck3_query_zhongguo_workforce_owner_snapshot_v1",
            "ck3_query_zhongguo_b1_cycle_snapshot_v1",
            "ck3_query_zhongguo_b2_pip_snapshot_v1",
            "ck3_query_zhongguo_case_snapshot_v1",
            "ck3_query_zhongguo_compensation_af5_snapshot_v1",
            "ck3_query_zhongguo_incident_snapshot_v1",
            "ck3_query_zhongguo_projects_metrics_postcondition_v1",
            "ck3_query_zhongguo_promotion_compensation_postcondition_v1",
            "ck3_query_zhongguo_result_case_snapshot_v1",
            "ck3_query_zhongguo_scoreboard_state_v1",
            "ck3_query_faction_gift_candidate_private_v1",
            "ck3_query_resolved_faction_gift_outcome_v1",
            "ck3_send_faction_gift_private_v1",
            "ck3_query_faction_gift_receipt_private_v1",
            "ck3_query_faction_gift_cold_recovery_private_v1",
            "ck3_query_title_own_laws_v1",
            "ck3_query_player_claims_v1",
            "ck3_query_title_holder_v1",
            "ck3_query_current_title_appointment_v1",
            "ck3_set_played_character_v1");
    private static final Set<String> ARMY13 = Set.of("ck3_query_player_default_raise_v1", "ck3_query_player_truce_expiry_v1",
            "ck3_query_army_gathering_research_sampling_v1", "ck3_query_battle_control_snapshot_v1", "ck3_query_battle_transition_v1",
            "ck3_query_battle_terminal_transition_v1", "ck3_preview_active_combat_retreat_v1", "ck3_order_active_combat_retreat_v1",
            "ck3_query_war_declared_overview_v1", "ck3_query_war_results_window_v1", "ck3_query_player_mercenary_context_v1",
            "ck3_query_army_commander_candidates_v1", "ck3_query_battle_reinforcement_assignment_v1");
    private static Set<PublicMethod> names(PublicMethod... methods) {
        return Arrays.stream(methods).collect(java.util.stream.Collectors.toUnmodifiableSet());
    }
    // Exact newly supplied Army methods, not the full vocabulary or disabled/retired operations.
    private static final Set<PublicMethod> ARMY_OPTIONAL=names(PublicMethod.QUERY_DECLARABLE_WARS,
            PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1,PublicMethod.QUERY_WAR_TERMINATION_OPTIONS,
            PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS,PublicMethod.QUERY_WAR_TERMINATION_TERMS,
            PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS,PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3,
            PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS,PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1,
            PublicMethod.QUERY_ARMY_STRENGTHS,PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1,
            PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1,PublicMethod.DECLARE_WAR,PublicMethod.RAISE_TROOPS_DEFAULT,
            PublicMethod.MOVE_ARMY,PublicMethod.START_ASSAULT,PublicMethod.STOP_ASSAULT,PublicMethod.DISBAND_ARMY,
            PublicMethod.ENFORCE_DEMANDS,PublicMethod.SURRENDER_WAR,PublicMethod.OFFER_WHITE_PEACE,PublicMethod.QUERY_WAR_TERMINATION_EXIT_TERMS);
    private static final Set<PublicMethod> ARMY_REQUIRED_ZERO=names(PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1,
            PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1,PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2,
            PublicMethod.SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1,PublicMethod.HIRE_MERCENARY_V1,PublicMethod.HIRE_HOLY_ORDER_V1,
            PublicMethod.ASSIGN_ARMY_COMMANDER_V1,PublicMethod.SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1,PublicMethod.COLLECT_DECLARABLE_WARS_RESULT_V1);
    private static final Set<PublicMethod> ARMY_REQUIRED_POSITIVE=names(PublicMethod.QUERY_CURRENT_BATTLE_KNIGHT_V1,
            PublicMethod.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1);
    private static boolean originalService(Set<PublicMethod> methods,String actualName) {
        try{return methods.contains(PublicMcpNativeAdapter.expectedServiceMethod(actualName));}
        catch(IllegalArgumentException nonService){return false;}
    }
    public record PublicCatalog(McpCoverage.Catalog catalog, List<McpCoverage.Decision> admission,
            List<ToolDescriptor> tools, List<ResourceDescriptor> resources) {
        public PublicCatalog {
            Objects.requireNonNull(catalog); admission = List.copyOf(admission);
            tools = List.copyOf(tools); resources = List.copyOf(resources);
            Set<String> names = catalog.declarations().stream().map(McpCoverage.Declaration::name)
                    .collect(java.util.stream.Collectors.toUnmodifiableSet());
            require(admission.size() == names.size() && admission.stream().map(McpCoverage.Decision::name)
                    .collect(java.util.stream.Collectors.toSet()).equals(names), "one actual admission per original declaration required");
            require(tools.stream().map(ToolDescriptor::name).distinct().count() == tools.size()
                    && names.containsAll(tools.stream().map(ToolDescriptor::name).toList()), "unique original tool descriptors required");
            require(resources.size() == 2 && resources.stream().map(ResourceDescriptor::uri)
                    .collect(java.util.stream.Collectors.toSet()).equals(Set.of("ck3://capabilities", "ck3://state/current")),
                    "both exact original public resources required");
            for (McpCoverage.Decision decision : admission) {
                McpCoverage.Declaration declaration = catalog.declarations().stream()
                        .filter(value -> value.name().equals(decision.name())).findFirst().orElseThrow();
                require(decision.admission() != McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION
                        || !declaration.conditions().isEmpty(), "an unconditional original tool cannot disappear by configured exclusion");
            }
        }
    }
    public record Documents(RawJson catalog, RawJson admission, RawJson tools, RawJson resources) {
        public Documents {
            Objects.requireNonNull(catalog); Objects.requireNonNull(admission); Objects.requireNonNull(tools); Objects.requireNonNull(resources);
            documentSize(catalog,RootRuntimeDefinitionModel.DataRole.MCP_CATALOG);documentSize(admission,RootRuntimeDefinitionModel.DataRole.MCP_ADMISSION);
            documentSize(tools,RootRuntimeDefinitionModel.DataRole.MCP_TOOLS);documentSize(resources,RootRuntimeDefinitionModel.DataRole.MCP_RESOURCES);
        }
    }
    public record DocumentTargets(Path catalog,Path admission,Path tools,Path resources) {
        public DocumentTargets {
            var all=List.of(catalog,admission,tools,resources);
            require(all.stream().allMatch(path->path.isAbsolute()&&path.normalize().equals(path)),"absolute normalized public document targets required");
            require(all.stream().distinct().count()==4,"four distinct immutable public document targets required");
        }
    }
    public record ProducedDocuments(RootRuntimePublicCatalog.OriginalFiles files,PublicCatalog value) {
        public ProducedDocuments {Objects.requireNonNull(files);Objects.requireNonNull(value);}
    }

    /** Actual guarded immutable producer. The caller supplies its existing writer-bound guard and identical file port.
     * A partial/unknown write returns no successful document set and is never retried or overwritten here. */
    public static ProducedDocuments writeActualDocuments(RootRuntimeStorageGuard guard,CheckpointFiles files,
            DocumentTargets targets,PublicCatalog actual)throws IOException {
        Objects.requireNonNull(guard);Objects.requireNonNull(files);Objects.requireNonNull(targets);Objects.requireNonNull(actual);
        return writeActualDocuments(new RootRuntimeBootstrapInputFiles(guard,files),targets,actual);
    }
    /** Same sole producer on a separately issued pre-Core immutable output port; grants no writer or Game authority. */
    public static ProducedDocuments writeActualDocuments(RootBootstrapInputFiles authority,DocumentTargets targets,PublicCatalog actual)throws IOException {
        Objects.requireNonNull(authority);Objects.requireNonNull(targets);Objects.requireNonNull(actual);
        var actualTargets=List.of(targets.catalog(),targets.admission(),targets.tools(),targets.resources());
        authority.requireTargets(actualTargets);CheckpointFiles files=Objects.requireNonNull(authority.files());
        Documents encoded=encode(actual);
        FileWitness catalog=write(files,targets.catalog(),encoded.catalog()),admission=write(files,targets.admission(),encoded.admission());
        FileWitness tools=write(files,targets.tools(),encoded.tools()),resources=write(files,targets.resources(),encoded.resources());
        Documents reopened=new Documents(read(files,catalog),read(files,admission),read(files,tools),read(files,resources));
        PublicCatalog decoded=decode(reopened);require(equivalent(actual,decoded),"actual written public documents changed their original JSON domain");
        var originals=new RootRuntimePublicCatalog.OriginalFiles(file(catalog),file(admission),file(tools),file(resources));
        originals.verify();authority.requireTargets(actualTargets);require(authority.files()==files,"bootstrap public writer file port changed");return new ProducedDocuments(originals,decoded);
    }
    private static FileWitness write(CheckpointFiles files,Path target,RawJson actual)throws IOException {
        FileWitness saved=files.createNew(target,actual.bytes());files.verify(saved);
        require(Path.of(saved.reference().path()).equals(target)&&Arrays.equals(actual.bytes(),files.read(saved,RawJson.MAXIMUM_BYTES)),"actual immutable public document witness differs from its producer");
        return saved;
    }
    private static RawJson read(CheckpointFiles files,FileWitness actual)throws IOException {files.verify(actual);return new RawJson(files.read(actual,RawJson.MAXIMUM_BYTES));}
    private static FileRef file(FileWitness actual){var ref=actual.reference();return new FileRef(ref.path(),ref.bytes(),ref.sha256());}
    private RootPublicCatalogCodec() { }
    private static void documentSize(RawJson document,RootRuntimeDefinitionModel.DataRole role){
        require(document.bytes().length<=RootRuntimeDefinitionModel.maximumDataBytes(role),"public document exceeds its actual mandatory SDK input lane: "+role);
    }

    /** Exact public width migrations; the four pinned original documents remain untouched. */
    public static List<ToolDescriptor> executableTools(PublicCatalog original) {
        return original.tools().stream().map(RootPublicCatalogCodec::executableTool).toList();
    }
    public static ToolDescriptor executableTool(ToolDescriptor original) {
        if(Set.of("ck3_search_entities_v1","ck3_query_turn_bundle_v1","ck3_query_campaign_root_context_v1").contains(original.name()))return registryRevision(original);
        if(ACTIVITY_PRIVATE_READS.contains(original.name()))return activityRevision(original);
        if(original.name().equals("ck3_execute_step"))return executeStep(original);
        if(COA_SOURCE_UPLOAD.contains(original.name()))return coaSourceUpload(original);
        if(Set.of("ck3_convert_player_religion_private_v1","ck3_submit_player_pilgrimage_planner_v1").contains(original.name()))return religionResources(original);
        if(original.name().equals("ck3_query_player_child_marriage_subject_private_v1"))return familySubject(original);
        if(Set.of("ck3_query_family_obligations_private_v1","ck3_query_player_epidemic_treatment_presence_private_v1").contains(original.name()))return additionalRevision(original,1);
        if(original.name().equals("ck3_activate_zhongguo_scoreboard_v1"))return scoreboard(original);
        if(original.name().equals("ck3_query_zhongguo_ai_owned_case_snapshot_v1"))return optionalChinaRevision(original);
        if(original.name().equals("ck3_query_faction_gift_candidate_private_v1"))return factionReserve(original);
        if(ADDITIONAL_POSITIVE.contains(original.name()))return additionalRevision(original,1);
        if(ADDITIONAL_ZERO.contains(original.name()))return additionalRevision(original,0);
        if(original.name().equals("ck3_enact_realm_law_crown_private_v1"))return currencyBudgets(original);
        if(original.name().equals("ck3_wait_for_change")) {
            ObjectNode descriptor=(ObjectNode)tree(original.original()).deepCopy();
            ObjectNode schema=object(descriptor.get("inputSchema"));
            ObjectNode properties=object(schema.get("properties"));
            migrateInteger(properties,"after_revision",false,false,0);
            // Public snapshot revision is bounded decimal BigInteger, not the native uint64 domain.
            ObjectNode decimal=object(properties.get("after_revision").get("anyOf").get(0));
        decimal.put("maxLength",org.xar.ck3.control.contracts.PublicRevision.MAX_DECIMAL_CHARACTERS)
                .put("pattern",org.xar.ck3.control.contracts.PublicRevision.DECIMAL_PATTERN);
            require(required(schema,"after_revision"),"original after_revision must remain required");
            return new ToolDescriptor(original.name(),raw(descriptor));
        }
        if(original.name().equals("ck3_query_council_composition_candidates_v1")) {
            ObjectNode descriptor=(ObjectNode)tree(original.original()).deepCopy();ObjectNode schema=object(descriptor.get("inputSchema"));
            ObjectNode properties=object(schema.get("properties"));
            for(String field:List.of("public_revision","native_revision")) {
                migrateInteger(properties,field,false,true,1);require(required(schema,field),"original council revision must remain required");
            }
            return new ToolDescriptor(original.name(),raw(descriptor));
        }
        boolean rite=Set.of("ck3_query_player_rite_creation_action_context_v1","ck3_execute_player_rite_creation_action_v1").contains(original.name());
        boolean development=original.name().equals("ck3_query_steward_develop_county_candidates_v1");
        boolean change=original.name().equals("ck3_change_steward_develop_county_task_v1");
        boolean option = original.name().equals("ck3_select_event_option");
        boolean interaction=Set.of("ck3_reply_pending_character_interaction","ck3_acknowledge_pending_character_interaction").contains(original.name());
        boolean save=original.name().equals("ck3_save_checkpoint");
        boolean aub=Set.of("ck3_query_aub_business_state_v1","ck3_query_aub_policy_options_v1",
                "ck3_select_aub_policy_option_v1","ck3_confirm_aub_policy_v1").contains(original.name());
        boolean marriage = original.name().equals("ck3_query_arrange_marriage_choices");
        boolean campaignRoot=original.name().equals("ck3_query_campaign_root_context_v1");
        boolean projectedContact=original.name().equals("ck3_query_projected_contact_scope_v1");
        boolean actualContact=original.name().equals("ck3_query_actual_contact_scope");
        boolean swayRead=Set.of("ck3_query_active_scheme_sway_completion_private_v1",
                "ck3_query_active_scheme_sway_outcome_opinion_private_v1").contains(original.name());
        boolean army = ARMY13.contains(original.name());
        boolean armyOptional=originalService(ARMY_OPTIONAL,original.name());
        boolean armyRequiredZero=originalService(ARMY_REQUIRED_ZERO,original.name());
        boolean armyRequiredPositive=originalService(ARMY_REQUIRED_POSITIVE,original.name());
        boolean nextEpisode=original.name().equals("ck3_start_next_episode");
        boolean settlement=original.name().equals("ck3_settle_one_life");
        boolean resolveEvent=original.name().equals("ck3_resolve_active_event");
        boolean arrange=original.name().equals("ck3_arrange_marriage");
        boolean interactionDirect=originalService(Set.of(PublicMethod.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1,
                PublicMethod.QUERY_CHARACTER_INTERACTION_ORDINARY_V1,PublicMethod.INITIATE_CHARACTER_INTERACTION_ORDINARY_V1),original.name());
        boolean successorResume=original.name().equals("ck3_resume_successor_ui_v1");
        boolean successorTimeline=original.name().equals("ck3_query_current_timeline_blocker_context_v1");
        boolean successorClose=original.name().equals("ck3_continue_death_succession_modal_v1");
        boolean swayTarget=original.name().equals("ck3_query_active_scheme_sway_target_private_v1");
        boolean swayReceipt=original.name().equals("ck3_query_active_scheme_sway_receipt_private_v1");
        boolean finish = original.name().equals("ck3_finish_active_scheme_sway_private_v1");
        boolean journal = Set.of("ck3_query_active_scheme_sway_completion_execution_private_v1",
                "ck3_query_active_scheme_sway_completion_termination_private_v1",
                "ck3_query_active_scheme_sway_completion_invalidation_reason_private_v1").contains(original.name());
        if (!option && !interaction && !save && !aub && !marriage && !army && !finish && !journal && !campaignRoot && !projectedContact && !actualContact && !swayRead && !armyOptional && !armyRequiredZero && !armyRequiredPositive && !nextEpisode && !rite && !development && !change && !settlement && !resolveEvent && !arrange && !interactionDirect && !swayTarget && !swayReceipt && !successorResume && !successorTimeline && !successorClose) return original;
        ObjectNode descriptor = (ObjectNode) tree(original.original()).deepCopy();
        ObjectNode schema = object(descriptor.get("inputSchema"));
        ObjectNode properties = object(schema.get("properties"));
        boolean nullable = successorResume || option || interaction || save || aub || marriage || actualContact || armyOptional || nextEpisode || settlement || resolveEvent || arrange || Set.of("ck3_query_player_default_raise_v1", "ck3_query_army_commander_candidates_v1").contains(original.name());
        migrateInteger(properties, "expected_revision", nullable, !(option||interaction||interactionDirect||projectedContact||actualContact||nextEpisode||settlement||resolveEvent||successorResume||successorTimeline||successorClose), nullable || successorTimeline || successorClose || army || armyRequiredZero || campaignRoot || projectedContact || development || interactionDirect ? 0 : 1);
        require(required(schema, "expected_revision") == !nullable, "original expected_revision presence contract changed");
        if(originalService(Set.of(PublicMethod.QUERY_CURRENT_BATTLE_KNIGHT_V1),original.name())) {
            migrateInteger(properties,"expected_native_revision",false,true,1);
            require(required(schema,"expected_native_revision"),"original knight native revision must remain required");
        }
        if(swayReceipt) {
            migrateInteger(properties,"pre_capture_epoch",false,true,1);
            require(required(schema,"pre_capture_epoch"),"original Sway pre-capture epoch must remain required");
        }
        if (journal) {
            migrateInteger(properties, "after_sequence", false, true, 0);
            require(!required(schema, "after_sequence"), "original after_sequence must remain optional");
        }
        if (original.name().equals("ck3_query_battle_terminal_transition_v1")) {
            migrateInteger(properties, "after_terminal_sequence", true, true, 1);
            require(!required(schema, "after_terminal_sequence"), "original terminal sequence must remain optional");
        }
        return new ToolDescriptor(original.name(), raw(descriptor));
    }
    /** This original provenance query reuses its uint32 positive validator for the public revision. */
    private static ToolDescriptor activityRevision(ToolDescriptor original) {
        var revised=additionalRevision(original,1);
        if(!original.name().equals("ck3_query_activity_feast_guest_rule_provenance_private_v1"))return revised;
        ObjectNode descriptor=(ObjectNode)tree(revised.original()).deepCopy();
        ObjectNode properties=object(object(descriptor.get("inputSchema")).get("properties"));
        ObjectNode revision=object(properties.get("expected_revision"));
        object(revision.get("anyOf").get(0)).put("maximum",4294967295L);
        object(revision.get("anyOf").get(1)).put("maxLength",10).put("pattern",boundedDecimalPattern("4294967295",false));
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    private static ToolDescriptor additionalRevision(ToolDescriptor original,int minimum) {
        ObjectNode descriptor=(ObjectNode)tree(original.original()).deepCopy();
        ObjectNode schema=object(descriptor.get("inputSchema"));
        migrateInteger(object(schema.get("properties")),"expected_revision",false,true,minimum);
        require(required(schema,"expected_revision"),"original additional revision must remain required");
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    /** Same actual public planning codec: optional revision and the one fixed H2743 DATA frame. */
    private static ToolDescriptor executeStep(ToolDescriptor original) {
        ObjectNode descriptor=(ObjectNode)tree(original.original()).deepCopy();ObjectNode schema=object(descriptor.get("inputSchema"));ObjectNode properties=object(schema.get("properties"));
        migrateInteger(properties,"expected_revision",true,true,0);require(!required(schema,"expected_revision"),"original execute revision remains optional");
        ObjectNode previous=object(properties.get("expected_h2743_frame"));require(!required(schema,"expected_h2743_frame")&&previous.get("anyOf").isArray()&&previous.get("anyOf").size()==2,"original optional H2743 object/null required");
        ObjectNode objectBranch=null;boolean nullable=false;for(JsonNode value:previous.get("anyOf")){ObjectNode branch=object(value);String type=StrictJson.text(branch.get("type"));if(type.equals("object")){require(objectBranch==null&&!branch.has("properties")&&!branch.has("required"),"original generic H2743 object required");branch.fieldNames().forEachRemaining(name->require(Set.of("type","additionalProperties").contains(name),"unreviewed H2743 schema constraint"));if(branch.has("additionalProperties"))require(branch.get("additionalProperties").isBoolean()&&branch.get("additionalProperties").booleanValue(),"original H2743 object must retain its generic field carrier");objectBranch=branch;}else{require(type.equals("null")&&branch.size()==1,"original H2743 null branch required");nullable=true;}}
        require(objectBranch!=null&&nullable,"original H2743 object/null pair required");
        ObjectNode frame=StrictJson.object().put("type","object").put("additionalProperties",false);ObjectNode fields=frame.putObject("properties");
        for(String name:List.of("snapshot_id","episode_run_id"))fields.putObject(name).put("type","string");
        for(String name:List.of("revision","native_revision","connection_generation")){fields.putObject(name).put("type","integer");migrateInteger(fields,name,false,true,1);}
        fields.putObject("date_raw").put("type","integer").put("minimum",0).put("maximum",Integer.MAX_VALUE);
        for(String name:List.of("actor_character_id","war_id"))fields.putObject(name).put("type","integer").put("minimum",0).put("maximum",4294967294L);
        var mandatory=frame.putArray("required");for(String name:List.of("snapshot_id","revision","native_revision","date_raw","actor_character_id","episode_run_id","war_id","connection_generation"))mandatory.add(name);
        ObjectNode replacement=previous.deepCopy();var alternatives=replacement.putArray("anyOf");alternatives.add(frame);alternatives.addObject().put("type","null");properties.set("expected_h2743_frame",replacement);
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    private static ToolDescriptor scoreboard(ToolDescriptor original) {
        ToolDescriptor revised=additionalRevision(original,0);
        ObjectNode descriptor=(ObjectNode)tree(revised.original()).deepCopy();ObjectNode schema=object(descriptor.get("inputSchema"));
        ObjectNode properties=object(schema.get("properties"));
        for(String field:List.of("expected_native_revision","expected_connection_generation","expected_observation_sequence","expected_observed_state_revision")) {
            migrateInteger(properties,field,false,true,1);require(required(schema,field),"original scoreboard identity must remain required");
        }
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    /** The same upload response generation can be fed into the original next tool, without Number. */
    private static ToolDescriptor coaSourceUpload(ToolDescriptor original) {
        ObjectNode descriptor=(ObjectNode)tree(original.original()).deepCopy();ObjectNode schema=object(descriptor.get("inputSchema"));
        ObjectNode properties=object(schema.get("properties"));
        if(!original.name().equals("ck3_abort_coat_of_arms_source_upload_v2")) {
            migrateInteger(properties,"expected_revision",false,true,0);
            require(required(schema,"expected_revision"),"original CoA source revision must remain required");
        }
        if(Set.of("ck3_append_coat_of_arms_source_chunk_v2","ck3_commit_coat_of_arms_source_upload_v2","ck3_abort_coat_of_arms_source_upload_v2").contains(original.name())) {
            migrateInteger(properties,"generation",false,true,1);
            require(required(schema,"generation"),"original CoA upload generation must remain required");
        }
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    /** Only the five source-owned nonnegative signed64 resource carriers are extended. */
    private static ToolDescriptor religionResources(ToolDescriptor original) {
        var revised=additionalRevision(original,1);
        ObjectNode descriptor=(ObjectNode)tree(revised.original()).deepCopy();ObjectNode schema=object(descriptor.get("inputSchema"));
        ObjectNode properties=object(schema.get("properties"));
        boolean conversion=original.name().equals("ck3_convert_player_religion_private_v1");
        var fields=conversion?List.of("max_piety_cost_raw"):List.of("reserve_gold_raw","reserve_treasury_raw","reserve_piety_raw","reserve_barter_goods_raw");
        for(String field:fields) {
            migrateInteger(properties,field,false,true,0);
            object(properties.get(field).get("anyOf").get(1)).put("maxLength",19)
                    .put("pattern",boundedDecimalPattern("9223372036854775807",true));
            require(required(schema,field)==conversion,"original Religion resource presence changed: "+field);
        }
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    private static ToolDescriptor familySubject(ToolDescriptor original) {
        ObjectNode descriptor=(ObjectNode)tree(original.original()).deepCopy();ObjectNode schema=object(descriptor.get("inputSchema"));
        migrateInteger(object(schema.get("properties")),"expected_native_revision",false,true,1);
        require(required(schema,"expected_native_revision"),"original child subject native revision must remain required");
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    private static ToolDescriptor optionalChinaRevision(ToolDescriptor original) {
        ObjectNode descriptor=(ObjectNode)tree(original.original()).deepCopy();ObjectNode schema=object(descriptor.get("inputSchema"));
        migrateInteger(object(schema.get("properties")),"expected_revision",true,true,0);
        require(!required(schema,"expected_revision"),"original AI-owned revision must remain optional");
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    private static ToolDescriptor factionReserve(ToolDescriptor original) {
        ToolDescriptor revised=additionalRevision(original,0);
        ObjectNode descriptor=(ObjectNode)tree(revised.original()).deepCopy();ObjectNode schema=object(descriptor.get("inputSchema"));
        migrateSignedCarrier(object(schema.get("properties")),"minimum_gold_reserve_raw","^(?:0|-?[1-9][0-9]{0,4299})(?![\\s\\S])",4301);
        require(!required(schema,"minimum_gold_reserve_raw"),"original reserve policy remains optional with its actual default");
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    private static void migrateSignedCarrier(ObjectNode properties,String field,String pattern,int maximumCharacters) {
        migrateInteger(properties,field,false,true,0);ObjectNode schema=object(properties.get(field));
        object(schema.get("anyOf").get(0)).put("minimum",-9007199254740991L);
        object(schema.get("anyOf").get(1)).put("maxLength",maximumCharacters).put("pattern",pattern);
    }
    private static String signed64Pattern() {
        return "^(?:(?:"+decimalAlternatives("9223372036854775807",true)+")|-(?:"+decimalAlternatives("9223372036854775808",false)+"))(?![\\s\\S])";
    }
    private static ToolDescriptor currencyBudgets(ToolDescriptor original) {
        ObjectNode descriptor=(ObjectNode)tree(original.original()).deepCopy();
        ObjectNode schema=object(descriptor.get("inputSchema"));ObjectNode properties=object(schema.get("properties"));
        require(required(schema,"budgets"),"original crown budgets must remain required");
        ObjectNode budgets=object(properties.get("budgets"));
        require("object".equals(StrictJson.text(budgets.get("type")))&&!budgets.has("properties")&&!budgets.has("required"),"original typed budget dictionary required");
        ObjectNode holder=StrictJson.object();holder.set("budget",budgets.get("additionalProperties"));
        migrateSignedCarrier(holder,"budget",signed64Pattern(),20);
        budgets.set("additionalProperties",holder.get("budget"));
        // Preserve the original container contract and error priority: law-key validation precedes
        // unknown/negative currency rejection in the owner codec. Do not pre-filter currency keys here.
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    /** Registry queries consume the same unbounded public revision returned by the public snapshot.
     * Native uint64 revisions and the ordinary bounded CharacterID arguments keep their own roles. */
    private static ToolDescriptor registryRevision(ToolDescriptor original) {
        ObjectNode descriptor=(ObjectNode)tree(original.original()).deepCopy();
        ObjectNode schema=object(descriptor.get("inputSchema"));
        ObjectNode properties=object(schema.get("properties"));
        migrateInteger(properties,"expected_revision",false,true,0);
        require(required(schema,"expected_revision"),"original registry revision must remain required");
        ObjectNode decimal=object(properties.get("expected_revision").get("anyOf").get(1));
        decimal.put("maxLength",4300).put("pattern","^(?:0|[1-9][0-9]*)(?![\\s\\S])");
        return new ToolDescriptor(original.name(),raw(descriptor));
    }
    private static boolean required(ObjectNode schema, String field) {
        if (!schema.has("required")) return false;
        require(schema.get("required").isArray(), "original required array expected");
        for (JsonNode value : schema.get("required")) if (field.equals(StrictJson.text(value))) return true;
        return false;
    }
    private static void migrateInteger(ObjectNode properties, String field, boolean nullable, boolean safeNumber, int minimum) {
        ObjectNode previous = object(properties.get(field));
        Set<String> annotations = Set.of("title", "description", "default", "examples", "deprecated", "readOnly", "writeOnly");
        previous.fieldNames().forEachRemaining(name -> require(annotations.contains(name)
                || Set.of("type", "anyOf", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum").contains(name),
                "original width field contains an unreviewed schema constraint: " + field + "/" + name));
        if (nullable) {
            require(!previous.has("type") && previous.has("anyOf") && previous.get("anyOf").isArray()
                    && previous.get("anyOf").size() == 2, "original optional integer|null schema required");
            boolean integer = false, nil = false;
            for (JsonNode choice : previous.get("anyOf")) {
                ObjectNode branch = StrictJson.object(choice, Set.of("type"));
                String type = StrictJson.text(branch.get("type")); integer |= type.equals("integer"); nil |= type.equals("null");
            }
            require(integer && nil, "original integer|null alternatives required");
        } else require("integer".equals(StrictJson.text(previous.get("type"))) && !previous.has("anyOf"), "original integer schema required");
        ObjectNode replacement = StrictJson.object();
        previous.properties().forEach(entry -> { if (annotations.contains(entry.getKey())) replacement.set(entry.getKey(), entry.getValue()); });
        var alternatives = replacement.putArray("anyOf");
        if (safeNumber) alternatives.addObject().put("type", "integer").put("minimum", minimum).put("maximum", 9007199254740991L);
        alternatives.addObject().put("type", "string").put("minLength", 1).put("maxLength", 20)
                .put("pattern", uint64Pattern(minimum == 0));
        if (nullable) alternatives.addObject().put("type", "null");
        properties.set(field, replacement);
    }
    /** Canonical decimal strings bounded at uint64 MAX, including a lexical check at length 20. */
    private static String uint64Pattern(boolean zero) {
        return boundedDecimalPattern("18446744073709551615",zero);
    }
    private static String boundedDecimalPattern(String maximum,boolean zero) {
        return "^(?:"+decimalAlternatives(maximum,zero)+")(?![\\s\\S])";
    }
    private static String decimalAlternatives(String maximum,boolean zero) {
        var choices = new ArrayList<String>();
        if (zero) choices.add("0");
        if(maximum.length()>1)choices.add("[1-9][0-9]{0,"+(maximum.length()-2)+"}");
        for (int index = 0; index < maximum.length(); index++) {
            int digit = maximum.charAt(index) - '0'; int lower = index == 0 ? 1 : 0;
            if (digit > lower) {
                String range = digit - lower == 1 ? Integer.toString(lower) : "[" + lower + "-" + (digit - 1) + "]";
                int suffix = maximum.length() - index - 1;
                choices.add(maximum.substring(0, index) + range + (suffix == 0 ? "" : "[0-9]{" + suffix + "}"));
            }
        }
        choices.add(maximum); return String.join("|", choices);
    }

    public static PublicCatalog decode(Documents documents) {
        List<McpCoverage.Decision> decisions = decodeAdmission(documents.admission());
        List<ToolDescriptor> tools = decodeTools(documents.tools());
        List<ResourceDescriptor> resources = new ArrayList<>();
        for (JsonNode value : wrapper(documents.resources(), RESOURCES_SCHEMA, "resources").get("resources")) {
            require(value.isObject(), "original resource descriptor object required");
            resources.add(new ResourceDescriptor(StrictJson.text(value.get("uri")), raw(value)));
        }
        return new PublicCatalog(McpCoverage.readCatalog(documents.catalog()), decisions, tools, resources);
    }

    /** Sole strict admission document decoder, shared by bootstrap and final production. */
    public static List<McpCoverage.Decision> decodeAdmission(RawJson document) {
        Objects.requireNonNull(document);documentSize(document,RootRuntimeDefinitionModel.DataRole.MCP_ADMISSION);
        ObjectNode admission = wrapper(document, ADMISSION_SCHEMA, "decisions");
        List<McpCoverage.Decision> decisions = new ArrayList<>();
        for (JsonNode value : admission.get("decisions")) {
            ObjectNode row = StrictJson.object(value, Set.of("name", "admission", "actual_admission_producer", "condition_and_scope"));
            decisions.add(new McpCoverage.Decision(StrictJson.text(row.get("name")),
                    McpCoverage.Admission.valueOf(StrictJson.text(row.get("admission"))),
                    ExactRef.fromJson(row.get("actual_admission_producer")), StrictJson.text(row.get("condition_and_scope"))));
        }
        require(!decisions.isEmpty()&&decisions.stream().map(McpCoverage.Decision::name).distinct().count()==decisions.size(),"one unique admission decision per original identity required");
        return List.copyOf(decisions);
    }

    /** Strict shared decoder for the actual captured tool document; it grants no admission. */
    public static List<ToolDescriptor> decodeTools(RawJson document) {
        Objects.requireNonNull(document);documentSize(document,RootRuntimeDefinitionModel.DataRole.MCP_TOOLS);
        var tools=new ArrayList<ToolDescriptor>();var names=new java.util.HashSet<String>();
        for(JsonNode value:wrapper(document,TOOLS_SCHEMA,"tools").get("tools")) {
            require(value.isObject(),"original tool descriptor object required");
            String name=StrictJson.text(value.get("name"));require(names.add(name),"duplicate original tool descriptor");
            tools.add(new ToolDescriptor(name,raw(value)));
        }
        return List.copyOf(tools);
    }

    /** Admission has one field contract; writers must not duplicate its JSON shape. */
    public static RawJson encodeAdmission(List<McpCoverage.Decision> actual) {
        actual=List.copyOf(actual);
        require(!actual.isEmpty()&&actual.stream().map(McpCoverage.Decision::name).distinct().count()==actual.size(),"one unique admission decision per original identity required");
        ObjectNode admission = StrictJson.object().put("schema", ADMISSION_SCHEMA); var decisions = admission.putArray("decisions");
        for (var decision : actual) {
            var row = decisions.addObject().put("name", decision.name()).put("admission", decision.admission().name())
                    .put("condition_and_scope", decision.conditionAndScope());
            row.set("actual_admission_producer", decision.actualAdmissionProducer().toJson());
        }
        RawJson encoded=raw(admission);documentSize(encoded,RootRuntimeDefinitionModel.DataRole.MCP_ADMISSION);return encoded;
    }

    /** Runtime-data producers use this same codec; test oracle documents are not a production source. */
    public static Documents encode(PublicCatalog value) {
        Objects.requireNonNull(value);
        var sourceIndexes = new LinkedHashMap<ExactRef, Integer>();
        for (var declaration : value.catalog().declarations()) sourceIndexes.computeIfAbsent(declaration.source(), ignored -> sourceIndexes.size());
        ObjectNode catalog = StrictJson.object().put("schema", "xar.original-mcp-declarations/v2");
        var sourceRows = catalog.putArray("sources"); sourceIndexes.keySet().forEach(source -> sourceRows.add(source.toJson()));
        var declarations = catalog.putArray("declarations");
        for (var declaration : value.catalog().declarations()) {
            var row = declarations.addObject().put("name", declaration.name()).put("source", sourceIndexes.get(declaration.source()))
                    .put("line", declaration.firstLine()).put("end_line", declaration.lastLine()).put("scope", declaration.scope());
            var conditions = row.putArray("conditions"); declaration.conditions().forEach(conditions::add);
        }
        RawJson admission = encodeAdmission(value.admission());
        ObjectNode tools = StrictJson.object().put("schema", TOOLS_SCHEMA); var toolRows = tools.putArray("tools");
        value.tools().forEach(descriptor -> toolRows.add(PublicDataJson.object(descriptor.original())));
        ObjectNode resources = StrictJson.object().put("schema", RESOURCES_SCHEMA); var resourceRows = resources.putArray("resources");
        value.resources().forEach(descriptor -> resourceRows.add(PublicDataJson.object(descriptor.original())));
        Documents encoded = new Documents(raw(catalog), admission, raw(tools), raw(resources));
        require(equivalent(value, decode(encoded)), "public catalog serialization changed its typed original documents");
        return encoded;
    }

    public static boolean equivalent(PublicCatalog left, PublicCatalog right) {
        if (!left.catalog().equals(right.catalog()) || !left.admission().equals(right.admission())
                || left.tools().size() != right.tools().size() || left.resources().size() != right.resources().size()) return false;
        for (int index = 0; index < left.tools().size(); index++) {
            var first = left.tools().get(index); var second = right.tools().get(index);
            if (!first.name().equals(second.name()) || !tree(first.original()).equals(tree(second.original()))) return false;
        }
        for (int index = 0; index < left.resources().size(); index++) {
            var first = left.resources().get(index); var second = right.resources().get(index);
            if (!first.uri().equals(second.uri()) || !tree(first.original()).equals(tree(second.original()))) return false;
        }
        return true;
    }

    private static ObjectNode wrapper(RawJson original, String schema, String array) {
        ObjectNode value = StrictJson.object(PublicDataJson.object(original), Set.of("schema", array));
        require(schema.equals(StrictJson.text(value.get("schema"))) && value.get(array).isArray(), "exact public runtime document schema and array required");
        return value;
    }
    private static RawJson raw(JsonNode value) { return PublicDataJson.encode(value); }
    private static JsonNode tree(RawJson value) { return PublicDataJson.object(value); }
    private static ObjectNode object(JsonNode value) {
        require(value instanceof ObjectNode, "original descriptor JSON object required"); return (ObjectNode) value;
    }
    private static void require(boolean condition, String message) { StrictJson.require(condition, message); }
}
