package org.xar.ck3.control.wave2.events.registered;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrenceCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegisteredProjection.*;

/** Complete Java producer for recommend_registered_vanilla_event_option_v1.
 * Knowledge, raw context and selections remain source/identity bound. This pure
 * producer recommends one bounded route; it does not submit or certify effects.
 */
public final class RegisteredVanillaEventPolicy {
    public enum Status { RECOMMENDED, BLOCKED, NOT_REGISTERED }
    public record Input(ObjectValue eventContext, Value playedCharacterId, Value snapshotOptionCount,
                        Optional<String> ck3Build, Value playedCharacter, Value opinionObservations, Value eventHistory) {
        public Input {
            Objects.requireNonNull(eventContext); Objects.requireNonNull(playedCharacterId); Objects.requireNonNull(snapshotOptionCount);
            Objects.requireNonNull(ck3Build); Objects.requireNonNull(playedCharacter); Objects.requireNonNull(opinionObservations); Objects.requireNonNull(eventHistory);
        }
    }
    public record Selection(BigInteger optionNumber,BigInteger nativeIndex,BigInteger renderedIndex) {
        public Selection {
            Objects.requireNonNull(optionNumber); Objects.requireNonNull(nativeIndex); Objects.requireNonNull(renderedIndex);
            StrictJson.require(nativeIndex.signum()>=0&&renderedIndex.signum()>=0&&optionNumber.equals(nativeIndex.add(BigInteger.ONE)),"exact native/API/rendered option mapping required");
        }
    }
    public record Recommendation(Status status,Optional<Selection> selection,ObjectValue wire) {
        public Recommendation {
            Objects.requireNonNull(status); Objects.requireNonNull(selection); Objects.requireNonNull(wire);
            StrictJson.require(selection.isPresent()==(status==Status.RECOMMENDED),"only recommended result can carry an option");
            StrictJson.require(is(wire.get("status"),status.name().toLowerCase(java.util.Locale.ROOT)),"typed recommendation/wire status differs");
            selection.ifPresent(value->StrictJson.require(eq(wire.get("selected_option_number"),v(value.optionNumber()))&&eq(wire.get("selected_native_option_index"),v(value.nativeIndex()))&&eq(wire.get("selected_rendered_index"),v(value.renderedIndex())),"typed recommendation/wire option differs"));
        }
    }
    private final RegisteredEventKnowledge registry;
    public RegisteredVanillaEventPolicy(RegisteredEventKnowledge registry) { this.registry=Objects.requireNonNull(registry); }
    public Recommendation recommend(Input input) {
        Objects.requireNonNull(input); ObjectValue context=input.eventContext();
        String build=input.ck3Build().orElseGet(()->RegisteredEventKnowledge.contextBuild(context)); Value eventKey=context.getOrNull("event_definition_key");
        String key=str(eventKey); ObjectValue knowledge=registry.query(build,key);
        if(!is(knowledge.get("status"),"available")) return response(Status.NOT_REGISTERED,eventKey,build,str(knowledge.get("unavailable_reason")),Map.of(),null,null,null,null,null);
        if(Set.of("1.20.0.3","1.20.0.4").contains(build)&&key.equals("faction_demand.1001")) {
            ObjectValue recognition=faction(context,input.playedCharacterId(),input.snapshotOptionCount());
            Map<String,Boolean> checks=decodeChecks(obj(recognition.get("checks")));
            Recommendation result=response(Status.BLOCKED,eventKey,build,is(recognition.get("status"),"recognized")?"populist_ultimatum_readonly_review_required":"current_populist_projection_does_not_match",checks,null,null,null,null,null);
            return extra(result,"readonly_projection",recognition,"decision_context_builder",v("build_faction_demand1001_decision_context_v1"));
        }
        BigInteger player=integer(input.playedCharacterId()),count=integer(input.snapshotOptionCount());
        if(!object(knowledge.get("contract"))||player==null||player.signum()<=0||count==null) return response(Status.BLOCKED,eventKey,build,"played_character_or_contract_projection_unavailable",Map.of(),null,null,null,null,null);
        ObjectValue contract=obj(materialize(knowledge.get("contract"),player)); Value analysis=knowledge.get("analysis");
        boolean noticePresent=obj(analysis).contains("source_reviewed_effectless_notice");
        ObjectValue notice=noticePresent?RegisteredSourceRules.notice(registry,knowledge,key,count):null;
        if(noticePresent&&notice==null) return blocked(eventKey,build,"registered_effectless_notice_source_review_invalid","effectless_notice_source_review");
        Integer variantIndex=null;
        if((OPTION_KEYS.contains(key)||notice!=null||updated(analysis,"option_variants"))&&active(contract.get("option_variants"))) {
            Resolution resolved=optionVariants(context,contract,count,key,notice!=null);variantIndex=resolved.index();
            if(resolved.contract()==null) return blocked(eventKey,build,resolved.error(),"option_variant_projection");contract=resolved.contract();
        }
        if((SCOPE_KEYS.contains(key)||updated(analysis,"scope_variants"))&&active(contract.get("scope_variants"))) {
            Resolution resolved=scopeVariants(context,contract);
            if(resolved.contract()==null) return blocked(eventKey,build,resolved.error(),"scope_variant_projection");contract=resolved.contract();
        }
        boolean currentRelational=RegisteredEventKnowledge.migrated(build)&&List.of("scope_variants","character_scopes","character_scope_matches_any","character_scope_differs_from").stream().anyMatch(field->updated(analysis,field));
        if(RELATIONAL_KEYS.contains(key)||notice!=null||currentRelational) contract=relational(contract);
        Set<String> allowed=new HashSet<>();Boolean witchBooleanNames=null;
        if(build.equals("1.20.0.4")&&key.equals("historical_char_creation_events.1")&&!RegisteredSourceRules.historical(registry,knowledge,build,key)) return blocked(eventKey,build,"historical_character_exact_source_or_index_drift","historical_character_exact_source");
        if(key.equals("trait_specific.4001")) {
            var projected=RegisteredSourceRules.witch(context,contract,analysis,player);
            if(projected==null) return blocked(eventKey,build,"registered_witch_exact_source_or_contract_drift","witch_exact_source_and_contract");
            contract=projected.contract();witchBooleanNames=projected.booleanNamesMatch();
            allowed.addAll(Set.of("boolean_scope_name_sets","character_scope_matches_any","optional_character_scope_matches_any","optional_scope_types","optional_unique_character_scope_excludes","unique_character_scope_excludes"));
        }
        if(key.equals("lifestyle_nicknames.1000")) {
            ObjectValue projected=RegisteredSourceRules.nickname(context,contract,analysis,player);
            if(projected==null) return blocked(eventKey,build,"registered_nickname_exact_source_or_contract_drift","nickname_exact_source_and_contract");
            contract=projected;allowed.addAll(Set.of("boolean_scopes","character_scopes","max_occurrences","unique_character_scope_excludes"));
        }
        if(key.equals("epidemic_events.0110")&&is(get(sourceHashes(analysis),"events/dlc/ce1/epidemic_events.txt"),"FEF2972BD4F778818CD3A414C337D036F5132C1598FEBAB0E2623E0252DB7A1E")
            &&eq(contract.get("scope_types"),json("{\"epidemic\":\"epidemic\"}"))&&eq(contract.get("optional_scope_types"),json("{\"new_preferred_capital\":\"landed_title\"}"))&&array(context.get("saved_scopes"))) {
            contract=contract.with("scope_types",merge(obj(contract.get("scope_types")),onlyPresent(obj(contract.get("optional_scope_types")),scopes(context).keySet())));allowed.add("optional_scope_types");
        }
        if(UNIQUE_KEYS.contains(key)||currentRelational) allowed.add("unique_character_scope_excludes");
        if(RELATIONAL_KEYS.contains(key)||currentRelational) allowed.addAll(Set.of("character_scopes","unique_character_scope_excludes","character_scope_matches_any","character_scope_differs_from"));
        if(notice!=null) allowed.addAll(Set.of("character_scope_matches_any","unique_character_scope_excludes"));
        if(key.equals("death_management.1000")) allowed.add("boolean_scopes");
        if(Set.of("health.3001","hostile_scheme_discovery.2001").contains(key)) allowed.add("max_occurrences");
        Map<String,Boolean> checks=new LinkedHashMap<>();
        if(key.equals("health.1015")&&build.equals("1.20.0.4")) {
            Value hashes=get(analysis,"source_sha256");boolean sourceReady=is(get(hashes,"events/health_events.txt"),"74073E049A416C744B36A2A996FA467610705E38D53C836B050F1AC6F66E1212")&&is(get(hashes,"common/scripted_effects/20_health_effects.txt"),"ABEFA738C913C660A52FA747BCC92FCA2F57D77A0F47D903BEDC2882F3D5A9DB");
            ObjectValue occurrence=occurrences(input.eventHistory(),key,player);BigInteger maximum=integer(contract.get("max_occurrences")),seen=integer(occurrence.get("count"));
            checks.put("health1015_exact_source",sourceReady);checks.put("occurrence_history_ready",is(occurrence.get("status"),"available"));
            checks.put("max_occurrences",maximum!=null&&maximum.signum()>0&&is(occurrence.get("status"),"available")&&seen!=null&&seen.compareTo(maximum)<0);
            if(!all(checks)) return extra(response(Status.BLOCKED,eventKey,build,"registered_event_source_or_occurrence_bound_unavailable",checks,null,null,null,null,null),"event_occurrence_observation",occurrence);
            allowed.add("max_occurrences");
        }
        Map<String,Boolean> unsupported=new LinkedHashMap<>();
        for(String field:UNSUPPORTED.stream().sorted().toList()) if(!allowed.contains(field)&&active(contract.get(field))) unsupported.put("direct_projection_support:"+field,false);
        if(!unsupported.isEmpty()) return response(Status.BLOCKED,eventKey,build,"registered_contract_requires_extended_consumer",unsupported,null,null,null,null,null);
        checks.put("context_schema",is(context.get("schema"),"current-event-window-context-v1"));checks.put("context_schema_version",is(context.get("schema_version"),1));checks.put("context_available",is(context.get("status"),"available"));
        checks.put("unique_window",is(context.get("window_match_count"),1));checks.put("event_definition_key",eq(eventKey,knowledge.get("event_definition_key")));
        ObjectValue scopeContext=context,scopeContract=contract;
        if(Set.of("prison_notification.0001","prison_notification.2001").contains(key)) {
            Value hashes=sourceHashes(analysis);
            checks.put("r0109_exact_prison_notification_source",is(get(hashes,"events/prison_events/prison_notification_events.txt"),"56023FBADC5F56C98293B1FB4AB7D846AD957F115B2E329422A0DCAD283B6C7F")&&is(get(hashes,"common/on_action/prison_on_actions.txt"),"D9CEBF10ED0E2E5ECC33E18BC71768F634E5F5504B690C5EDE6B095ACC1A2ECD"));
            Set<String> required=Set.of("prisoner","imprisoner","bg_override_char","this_player");List<Value> rows=seq(context.get("saved_scopes"));List<Value> names=rows.stream().map(row->get(row,"name")).toList();
            checks.put("r0109_all_scope_rows_named_unique",array(context.get("saved_scopes"))&&names.stream().allMatch(value->text(value)!=null)&&new HashSet<>(names).size()==names.size());
            checks.put("r0109_authored_roles_present",array(context.get("saved_scopes"))&&names.containsAll(required.stream().map(RegistryJson::v).toList()));
            if(array(context.get("saved_scopes"))) scopeContext=context.with("saved_scopes",arr(rows.stream().filter(row->object(row)&&required.contains(str(get(row,"name")))).toList()));
        }
        boolean bookmark=build.equals("1.20.0.4")&&key.equals("bookmark.1070");
        if(bookmark) {var projection=RegisteredSourceRules.bookmark(context,contract,knowledge);scopeContext=projection.context();scopeContract=projection.contract();checks.putAll(projection.checks());}
        checks.putAll(scopeChecks(scopeContext,scopeContract,player));if(witchBooleanNames!=null) checks.put("trait_specific_4001_boolean_scope_names_exact",witchBooleanNames);
        Options options=options(context,contract,count);checks.putAll(options.checks());ObjectValue selected=options.selected();
        if(notice!=null) checks.putAll(RegisteredSourceRules.noticeFrame(context,contract,selected));
        if(key.equals("tgp_japan_yearly_events.1190")) {
            checks.put("r0100_exact_source",is(get(sourceHashes(analysis),"events/dlc/tgp/tgp_japan_yearly_events_ariana.txt"),"B9F5799465E9B83B16C97086BC74F43ECD3949680AE1A78C081ED44ECD9B5FD6"));
            checks.put("r0100_selected_stress_decrease_indicator",RegisteredProfiles.japanIndicator(selected,build));
        }
        if(key.equals("stress_threshold_special.1001")) {
            checks.put("r0065_exact_source_and_definition",is(get(sourceHashes(analysis),"events/stress_events/stress_threshold_special_events.txt"),"768CBA7DB6270BB2FE25D9EEE37D2F24483EE309A2496DD9A539673EF094F709")&&(RegisteredEventKnowledge.migrated(build)||is(context.get("calculated_event_id"),3_121_001)&&is(context.get("runtime_stats_ordinal"),4_333)));
            checks.put("r0065_single_paused_event_frame",positive(context.get("current_event_instance_id"))&&positive(context.get("snapshot_revision"))&&integer(context.get("date_raw"))!=null);
            checks.put("r0065_exact_grief_variant_only",Integer.valueOf(3).equals(variantIndex)&&is(contract.get("selected_native_option_index"),7)&&eq(arr(seq(contract.get("native_option_indices"))),json("[0,4,7]")));
        }
        if(!all(checks)||selected==null) return response(Status.BLOCKED,eventKey,build,"registered_contract_projection_drift",checks,null,null,null,null,null);
        BigInteger nativeIndex=integer(contract.get("selected_native_option_index")),optionNumber=integer(contract.get("selected_option_number")),rendered=integer(selected.get("rendered_index"));
        RegisteredComparisons.Comparison feast=Set.of("1.20.0.3","1.20.0.4").contains(build)&&key.equals("feast_default.6003")?RegisteredComparisons.feast(context,knowledge,input.opinionObservations()):null;
        RegisteredComparisons.Comparison poet=build.equals("1.20.0.4")&&key.equals("trait_specific.9001")?RegisteredComparisons.poet(context,knowledge,input.playedCharacter()):null;
        ObjectValue effect,utility;
        if(feast!=null||poet!=null) {
            var comparison=feast!=null?feast:poet;nativeIndex=comparison.nativeIndex();optionNumber=nativeIndex.add(BigInteger.ONE);selected=comparison.option();rendered=integer(selected.get("rendered_index"));effect=comparison.effect();utility=comparison.utility();
        } else {
            effect=notice!=null?RegisteredSourceRules.noticeProfile(notice,nativeIndex):key.equals("epidemic_events.5007")?RegisteredProfiles.epidemic(knowledge,selected,nativeIndex):RegisteredProfiles.selectedEffect(knowledge,nativeIndex);
            effect=RegisteredProfiles.stressObservable(knowledge,selected,nativeIndex,effect);utility=RegisteredProfiles.selectedUtility(knowledge,nativeIndex);
        }
        Recommendation result=response(Status.RECOMMENDED,eventKey,build,null,checks,new Selection(optionNumber,nativeIndex,rendered),variantIndex,effect,utility,null);
        if(feast!=null) result=extra(result,"feast_brawl_decision_context",feast.context());
        if(poet!=null) result=extra(result,"poet_long_term_decision_context",poet.context());
        if(bookmark) result=extra(result,"scope_projection_source",v("source-reviewed-selected-option-dependencies"),"selected_scope_dependencies",json("{\"root\":\"root.capital_province\",\"saved_scope_names\":[],\"raw_inherited_scope_rows_preserved\":true,\"inherited_scope_identity_qualified\":false}"));
        return result;
    }
    private static Recommendation blocked(Value key,String build,String reason,String check) {return response(Status.BLOCKED,key,build,reason,Map.of(check,false),null,null,null,null,null);}
    private static Recommendation response(Status status,Value key,String build,String reason,Map<String,Boolean> checks,Selection selection,Integer variant,ObjectValue effect,ObjectValue utility,Void unused) {
        ObjectValue wire=b().set("schema","xar.ck3.vanilla-event-registry-choice").set("schema_version",1).set("status",status.name().toLowerCase(java.util.Locale.ROOT))
            .set("policy","exact-build-vanilla-event-registry-direct-projection-v1").set("source","shared_vanilla_event_registry").set("ck3_build",build).set("ck3_exe_sha256",RegisteredEventKnowledge.EXE.get(build)).set("event_definition_key",text(key))
            .set("recommendation_scope","bounded_timeline_continuation").set("native_ai_equivalent",false).set("semantic_optimal",false).set("semantic_decision_ready",false)
            .set("selected_option_number",selection==null?RetainedJson.NULL:v(selection.optionNumber())).set("selected_native_option_index",selection==null?RetainedJson.NULL:v(selection.nativeIndex())).set("selected_rendered_index",selection==null?RetainedJson.NULL:v(selection.renderedIndex()))
            .set("matched_option_variant_index",variant==null?RetainedJson.NULL:v(variant)).set("option_projection_source",variant!=null?"registered_option_variant":status==Status.RECOMMENDED?"base_contract":null)
            .set("choice_effect_profile",effect).set("campaign_utility_ready",utility!=null).set("campaign_utility_profile",utility).set("checks",checks(checks)).set("failed_checks",failed(checks)).set("unavailable_reason",reason).build();
        return new Recommendation(status,Optional.ofNullable(selection),wire);
    }
    private static Recommendation extra(Recommendation result,String key,Value value) {return new Recommendation(result.status(),result.selection(),result.wire().with(key,value));}
    private static Recommendation extra(Recommendation result,String first,Value value,String second,Value other) {return extra(extra(result,first,value),second,other);}
    private static Map<String,Boolean> decodeChecks(ObjectValue raw) {Map<String,Boolean> result=new LinkedHashMap<>();raw.fields().forEach((key,value)->{StrictJson.require(value instanceof BooleanValue,"boolean policy check required");result.put(key,yes(value));});return result;}
    private static ObjectValue occurrences(Value history,String key,BigInteger player) {
        if(!array(history)) return b().set("status","unavailable").set("count",RetainedJson.NULL).set("reason","event_history_unavailable").build();
        ObjectValue input=b().set("schema",EventOccurrenceCodec.SCHEMA).set("event_definition_key",key).set("played_character_id",player).set("commands",history).build();
        return RetainedJson.object(RetainedJson.parse(EventOccurrenceCodec.encode(EventOccurrence.count(EventOccurrenceCodec.decodeRetained(input)))));
    }
    private static BigInteger factionIdentity(Value scope) {
        Value identity=get(scope,"typed_identity"),id=get(identity,"character_id");
        return is(get(scope,"status"),"available")&&is(get(identity,"status"),"available")&&is(get(identity,"kind"),"character")?integer(id):null;
    }
    private static ObjectValue faction(ObjectValue context,Value player,Value optionCount) {
        Map<String,Value> scopes=scopes(context);List<Value> options=seq(context.get("options")).stream().filter(RegistryJson::object).toList();
        BigInteger root=factionIdentity(context.get("root_scope")),leader=factionIdentity(scopes.get("peasant_leader")),target=factionIdentity(scopes.get("faction_target")),named=factionIdentity(scopes.get("faction_leader"));
        ObjectValue types=jsonObject("{\"faction\":\"faction\",\"peasant_county\":\"landed_title\",\"faction_target\":\"character\",\"target_title\":\"landed_title\",\"peasant_leader\":\"character\",\"new_title\":\"landed_title\",\"faction_leader\":\"character\"}");
        Map<String,Boolean> checks=new LinkedHashMap<>();checks.put("exact_build",Set.of("1.20.0.3","1.20.0.4").contains(RegisteredEventKnowledge.contextBuild(context)));
        checks.put("event_definition",is(context.get("status"),"available")&&is(context.get("event_definition_key"),"faction_demand.1001"));
        checks.put("player_root_target",positive(player)&&integer(player).equals(root)&&integer(player).equals(target));checks.put("leader_roles",leader!=null&&leader.signum()>0&&leader.equals(named)&&!leader.equals(root));
        checks.put("saved_role_names",scopes.size()==7&&scopes.keySet().equals(types.fields().keySet()));checks.put("saved_role_types",types.fields().entrySet().stream().allMatch(row->object(scopes.get(row.getKey()))&&eq(get(scopes.get(row.getKey()),"type_key"),row.getValue())));
        checks.put("authored_option_count",is(optionCount,4));checks.put("visible_native_options",options.size()==2&&options.stream().map(row->get(row,"native_option_index")).collect(java.util.stream.Collectors.toSet()).equals(Set.of(v(2),v(3)))&&options.stream().allMatch(row->yes(get(row,"shown"))&&yes(get(row,"enabled"))));
        List<Value> mapping=new ArrayList<>();for(Value row:options) {BigInteger index=integer(get(row,"native_option_index"));if(BigInteger.TWO.equals(index)||BigInteger.valueOf(3).equals(index)) mapping.add(b().set("native_option_index",index).set("api_option_number",index.add(BigInteger.ONE)).set("rendered_index",get(row,"rendered_index")).set("resolved_name",get(row,"resolved_name")).build());}
        return b().set("status",all(checks)?"recognized":"blocked").set("checks",checks(checks)).set("failed_checks",failed(checks)).set("native_option_mapping",arr(mapping)).set("selected_option_number",RetainedJson.NULL).set("selected_native_option_index",RetainedJson.NULL).set("automatic_selection",false).build();
    }
}
