package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.*;

/** Lossless decision artifact around immutable domain selections; source metadata never grants native eligibility. */
public final class KnownPendingInteractionPlans {
    private KnownPendingInteractionPlans() { }
    private record Source(String path,String sha256,List<String> decline,List<String> costs) {
        private Source { decline=List.copyOf(decline);costs=List.copyOf(costs); }
    }
    public static OpportunityJson.Obj encode(PlanningRequest request,Context held,Plan plan,Optional<OpportunityJson.Obj> original) {
        ObjectNode root=F.objectNode().put("policy","one-life-turn-v1").put("phase",plan.phase())
                .put("reason","exact known player reply policy with independent postconditions")
                .put("known_policy_handled",plan.classification().dedicated());
        root.set("java_policy_plan",KnownPendingInteractionPlanCodec.encode(plan));
        put(root,"selected_step",plan.selected().map(Action::step));
        plan.requiredStep().ifPresent(value->root.put("required_step",value));
        plan.requiredTool().ifPresent(value->root.put("required_mcp_tool",value));
        ObjectNode summary=root.putObject("pending_character_interaction");
        summary.put("instance_id",held.controls().pending().instance().value())
                .put("sender_character_id",held.controls().pending().sender().value())
                .put("auto_accept_notification",held.controls().pending().autoAcceptNotification());
        ObjectNode binding=summary.putObject("frame_binding").put("snapshot_id",request.before().frame().snapshotId())
                .put("public_revision",request.before().frame().revision()).put("native_revision",held.revision())
                .put("date_raw",held.date()).put("pending_interaction_id",held.controls().pending().instance().value());
        ObjectNode context=null;
        if(original.isPresent()) {
            ObjectNode wrapper=InteractionArguments.parseApp(original.orElseThrow());
            context=object(field(wrapper,"pending_character_interaction_context"));
            root.set("original_context_wrapper",wrapper.deepCopy());
            summary.set("context_status",field(context,"status").deepCopy());summary.set("context_reason",field(context,"reason").deepCopy());
            for(String field:List.of("definition","roles","routing","deadline","send_options"))
                summary.set(field,field(context,field).deepCopy());
            summary.set("reply_legality",field(context,"legality").deepCopy());
            JsonNode definition=field(context,"definition");
            if(definition.isObject())summary.set("interaction_key",field(definition,"canonical_key").deepCopy());else summary.putNull("interaction_key");
            JsonNode terms=field(context,"terms");
            if(terms.isObject()) {
                summary.set("special_data_present",field(terms,"special_data_present").deepCopy());
                summary.set("special_war_binding",field(terms,"special_war_binding").deepCopy());
                if(terms.has("ransom_quote"))summary.set("ransom_quote",terms.get("ransom_quote").deepCopy());
            }
            JsonNode readiness=field(context,"readiness");
            summary.set("context_semantic_decision_ready",field(readiness,"interaction_semantic_decision_ready").deepCopy());
            summary.set("not_ready_reasons",field(readiness,"not_ready_reasons").deepCopy());
        }
        ObjectNode decision=root.putObject("decision").put("rule_id",plan.ruleId())
                .put("classification",plan.classification().key())
                .put("mode",plan.classification()==Classification.KNOWN_RECEIVED_RANSOM?"source_backed_ordinary_gold":"degraded_blocker_removal")
                .put("native_ai_equivalent",false).put("semantic_optimal",false).put("semantic_decision_ready",false)
                .put("interaction_semantic_decision_ready",false).put("ordinary_gold_decision_ready",plan.ordinaryGoldReady())
                .put("pending_interaction_id",held.controls().pending().instance().value());
        decision.set("frame_binding",binding.deepCopy());decision.set("pending_character_interaction",summary.deepCopy());
        put(decision,"selected_action",plan.selected().map(Action::key));put(decision,"selected_step",plan.selected().map(Action::step));
        put(decision,"recommended_action",plan.selected().map(Action::key));
        var blocked=decision.putArray("blocked_reasons");plan.blockedReasons().forEach(blocked::add);
        if(context!=null) {
            decision.set("reply_legality",field(context,"legality").deepCopy());
            decision.set("roles",field(context,"roles").deepCopy());decision.set("deadline",field(context,"deadline").deepCopy());
            JsonNode definition=field(context,"definition");
            if(definition.isObject()) {
                String key=text(definition,"canonical_key");decision.put("interaction_key",key);
                if(java.util.Set.of("arrange_marriage_interaction","grant_vassal_interaction","negotiate_alliance_interaction",
                        "perk_alliance_interaction","call_ally_interaction","pay_ransom_interaction","ransom_me_interaction",
                        "end_war_attacker_victory_interaction","end_war_attacker_white_peace_interaction","end_war_attacker_defeat_interaction").contains(key))
                    root.put("known_policy_handled",true);
                boolean reviewedMarriage=held.build()==Build.CROZIER4
                        &&number(definition,"deterministic_key_hash",java.math.BigInteger.ZERO,U32).longValueExact()==1_298_930_137L;
                Source source=source(plan,held,key,reviewedMarriage);
                ObjectNode metadata=decision.putObject("definition_classification").put("definition_key",key)
                        .put("allowlisted",plan.classification().dedicated());
                if(source!=null) {
                    ObjectNode evidence=metadata.putObject("evidence").put("source",source.path()).put("source_sha256",source.sha256())
                            .put("loaded_definition_bytes_verified",false).put("material_effects_verified",false);
                    var declines=evidence.putArray("known_decline_effects");source.decline().forEach(declines::add);
                    var costs=evidence.putArray("known_selected_option_costs");source.costs().forEach(costs::add);
                    if(plan.classification()==Classification.KNOWN_MARRIAGE && held.build()==Build.CROZIER4
                            &&number(definition,"deterministic_key_hash",java.math.BigInteger.ZERO,U32).longValueExact()==1_298_930_137L) {
                        evidence.put("source_policy","ck3-1.20.0.4-explicit-marriage-special-reject-only-v1")
                                .put("definition_sha256","5927c5d4e719bb04a645d47c4e79544bf3e72f76be5c60e8bd6ad5ad59b0301a")
                                .put("on_decline_sha256","8390846f7a5c14848079abcd079d2fca1d801214011e80da44786d4788c1ace1")
                                .put("send_option_catalogue_sha256","c462de92849c534ab85391b020e288470de75a1b65693a313051493827ae5731")
                                .put("accept_outcome_qualified",false);
                    }
                } else metadata.putNull("evidence");
            }
        }
        var candidate=decision.putArray("candidate_replies");
        if(context!=null&&field(context,"legality").isObject()) {
            for(String action:List.of("accept","reject","block","acknowledge")) {
                JsonNode legal=field(field(context,"legality"),action);String step=action+"-pending-character-interaction";
                candidate.addObject().put("action",action).put("step",step)
                        .put("native_legal","available".equals(text(legal,"status"))&&bool(legal,"allowed"))
                        .put("action_reachable",request.observations().actionSteps().contains(new org.xar.ck3.control.application.action.OperationKey(step)))
                        .set("native_legality",legal.deepCopy());
            }
        }
        ObjectNode post=decision.putObject("postconditions").put("old_pending_full_id_absent_in_paused_frame",true)
                .put("reply_ack_verifies_payment_or_release",false).put("alliance_semantic_postcondition_ready",false);
        plan.warId().ifPresent(value->post.put("bound_war_id_must_disappear",value));
        plan.prisonerId().ifPresent(value->post.put("prisoner_character_id",value));
        plan.quotedGoldRaw().ifPresent(value->post.put("quoted_gold_raw",value));
        post.put("amount_re_evaluated_on_accept",plan.classification()==Classification.KNOWN_RECEIVED_RANSOM);
        post.put("independent_player_gold_and_custody_required",plan.classification()==Classification.KNOWN_RECEIVED_RANSOM);
        plan.originalWarSignature().ifPresent(values-> {
            var array=decision.putArray("active_war_signature_before_reply");
            for(WarSignature value:values) {
                var war=array.addObject().put("war_id",value.warId())
                        .put("player_side",value.side().name().toLowerCase(java.util.Locale.ROOT))
                        .put("player_relative_war_score",value.score());
                if(value.primaryLeader()==null)war.putNull("player_is_primary_war_leader");else war.put("player_is_primary_war_leader",value.primaryLeader());
                if(value.opponent()==null)war.putNull("primary_opponent_character_id");else war.put("primary_opponent_character_id",value.opponent());
                var titles=war.putArray("targeted_title_ids");value.targetedTitleIds().forEach(titles::add);
            }
        });
        if(plan.classification()==Classification.KNOWN_CALL_ALLY)
            decision.put("target_raw_token_consumed",false).put("target_typed_identity_consumed",false).put("target_war_id_resolved",false);
        if(plan.classification()==Classification.KNOWN_RECEIVED_RANSOM) {
            decision.putArray("quality_gaps").add("prisoner_title_tier_political_value_not_scored")
                    .add("native_greed_rivalry_feud_and_other_acceptance_inputs_not_scored");
        }
        return InteractionArguments.app(root);
    }
    private static void put(ObjectNode object,String key,Optional<String> value) {
        if(value.isPresent())object.put(key,value.orElseThrow());else object.putNull(key);
    }
    private static Source source(Plan plan,Context held,String key,boolean reviewedMarriage) {
        String alliance="919ED408EC735F64ED972E23A376CD618A2E207A0EA273F973C5B1F89440E39D";
        return switch(plan.classification()) {
            case KNOWN_MARRIAGE -> new Source("common/character_interactions/00_marriage_interactions.txt",
                    reviewedMarriage?"9481FD44A078F2D06034DD4A2107FE183F231D2B49D8B90F106C1D54F7A501F0"
                    :"681A9B669E5A16642A197B6FE16085193DFBB99A398D0E20E86173F5AC6DE219",
                    List.of("marriage_interaction.0011","secondary_actor:player_declined_marriage:5y"),List.of());
            case KNOWN_GRANT_VASSAL -> new Source("common/character_interactions/00_vassal_interactions.txt",
                    held.build()==Build.CROZIER3?"B0F81CF740B6DBF42952D9A08703BA75E23D6918DD44F4D8E9999F11695B3A20"
                    :"1249CAC40138D48210A07245746C4A6683C5F58F3141C04A20DB2C00B6375BF8",
                    List.of("actor:char_interaction.0211:letter_only","conditional_clan_unity_loss"),List.of());
            case KNOWN_NEGOTIATE_ALLIANCE,KNOWN_PERK_ALLIANCE -> new Source("common/character_interactions/00_alliance.txt",alliance,
                    List.of("actor:refused_alliance_opinion:toward_recipient","minor_clan_unity_loss"),List.of("actor_hook","actor_influence"));
            case KNOWN_CALL_ALLY -> new Source("common/character_interactions/00_alliance.txt",alliance,
                    List.of("actor:rejected_call_to_offensive_war_opinion:-20","actor:rejected_call_to_defensive_war_opinion:-50",
                            "recipient:prestige_experience_or_mandala_penalty","target_war:set_called_to",
                            "conditional_contract_house_blood_brother_penalties"),List.of());
            case KNOWN_RECEIVED_RANSOM -> new Source("common/character_interactions/00_prison_interactions.txt",
                    "1bb43b3c2061212af8d41b11314ff4e569af2a3506319f820d05877a7762abc5",List.of(),List.of());
            case KNOWN_WAR_EXIT -> new Source("common/casus_belli_types/00_event_war.txt",
                    "BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707",List.of(),List.of());
            case ORDINARY -> switch(key) {
                case "demand_hostage_interaction" -> new Source("common/character_interactions/05_bp2_interactions.txt",
                        "78526C7BBC520B4F8D8713DC80BF8C089655A3000B661FC104FA1AF139AD7E94",
                        List.of("secondary_recipient:remove_under_offer_as_hostage_flag","actor:char_interaction.0301",
                                "conditional_actor_tyranny_and_opinion_if_player_vassal"),List.of());
                case "spar_with_knight_interaction" -> new Source("common/character_interactions/00_tradition_interactions.txt",
                        "E3B7330D8DFD9C82522D65629B6DD991D319B76B41C388CE483E351D829391E3",List.of(),List.of());
                case "pay_ransom_interaction","ransom_interaction" -> new Source("common/character_interactions/00_prison_interactions.txt",
                        "3E05C94CDCE4D42CCE8256D2D79CD78FEB1C9D5B79DAA64AA8243AA0C658F22B",
                        List.of("secondary_recipient:character_ransom_refused_by_player:10y","actor:char_interaction.0131"),List.of());
                default -> null;
            };
            case EXPLICIT_NATIVE_REPLY -> null;
            default -> null;
        };
    }
}

