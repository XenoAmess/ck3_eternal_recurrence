package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;
import org.xar.ck3.control.wave2.military.forecast.CurrentBattleConditionCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.CombatProjectionJson.*;

/** Original Service-only combat derivations; the protocol layer merely projects these typed results. */
public final class CombatPublicProjection {
    private CombatPublicProjection() { }
    public record Input(Complete before,Complete after,PlanningReadResult.Known<ForecastReadObservation> original) {
        public Input {
            Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(original);
            StrictJson.require(before.identity().equals(after.identity())&&before.source().equals(after.source())
                    &&before.sessionId().equals(after.sessionId())&&before.connectionGeneration().equals(after.connectionGeneration()),
                    "public combat projection crossed physical frame/source/session/connection");
            var request=original.receipt().request();
            StrictJson.require(request.before().equals(before.identity())&&request.source().equals(before.source())&&request.sessionId().equals(before.sessionId()),
                    "public combat projection lost its actual original receipt binding");
            StrictJson.require(original.value() instanceof ForecastReadObservation.CombatInputs,"public combat projection requires original typed combat inputs");
            var observed=((ForecastReadObservation.CombatInputs)original.value()).observation();
            StrictJson.require(observed.frame().equals(CombatObservationCache.Frame.decode(OpportunityJson.toNode(before.semantic()))),
                    "public combat projection original decoder frame differs from actual complete source");
        }
        public CombatObservationCache.Observation observation() {return ((ForecastReadObservation.CombatInputs)original.value()).observation();}
    }
    public record V2(Optional<Obj> knightConsumption,Optional<Obj> physicalAssociation) {
        public V2 {Objects.requireNonNull(knightConsumption);Objects.requireNonNull(physicalAssociation);}
    }
    public record V3(Obj loadedPlaysetProof,Obj phaseEventManifestFidelity,List<String> missingFidelityGates,Obj specialKnightInitialValue) {
        public V3 {Objects.requireNonNull(loadedPlaysetProof);Objects.requireNonNull(phaseEventManifestFidelity);missingFidelityGates=List.copyOf(missingFidelityGates);Objects.requireNonNull(specialKnightInitialValue);}
    }
    /** A provider must return evidence minted by the actual file collector or an explicit observed unavailability. */
    @FunctionalInterface public interface LoadedPlaysetSource {CombatLoadedPlaysetProof.Evidence observe(Input input)throws IOException;}
    public static V2 v2(Input input) {
        StrictJson.require(input.observation().version()==CombatObservationCache.Version.V2,"v2 projection requires v2 observation");
        ObjectNode normalized=input.observation().normalizedJson();
        Optional<Obj> consumed=CombatKnightConsumption.project(normalized.get("knight_stat_consumption_v1"));
        JsonNode control=OpportunityJson.toNode(input.after().semantic()).get("battle_control_snapshot_v1");
        Optional<Obj> physical=control!=null&&control.isObject()&&"available".equals(control.path("status").asText())
                ?Optional.of(physical(CurrentBattleConditionCodec.adapt(control),consumed,input.observation().frame())):Optional.empty();
        return new V2(consumed,physical);
    }
    /** Serialization is pure: the Service must collect this evidence inside its actual writer/held scope first. */
    public static V3 v3(Input input,CombatLoadedPlaysetProof.Evidence actualAlreadyCollected) {
        StrictJson.require(input.observation().version()==CombatObservationCache.Version.V3,"v3 projection requires v3 observation");
        var evidence=Objects.requireNonNull(actualAlreadyCollected);evidence.requireFrame(input.after());
        Obj proof=evidence.value();ObjectNode p=node(proof),normalized=input.observation().normalizedJson();
        boolean verified="verified".equals(p.path("status").asText())&&p.path("claims").isObject()&&yes(p.path("claims").get("loaded_playset_verified"));
        ObjectNode completeness=object(normalized.get("completeness"));ObjectNode fidelity=object(completeness.get("phase_event_manifest_fidelity")).deepCopy();
        fidelity.put("loaded_playset_verified",verified).put("fidelity_gate",verified&&yes(fidelity.get("ast_evaluator_ready"))&&yes(fidelity.get("original_trace_ready")));
        List<String> gaps=new ArrayList<>();for(var key:array(completeness.get("missing_fidelity_gates")))if(!"loaded_playset_verified".equals(text(key))||!verified)gaps.add(text(key));
        return new V3(proof,immutable(fidelity),gaps,specialInitial(object(normalized.get("base_inputs")),provenance(input)));
    }
    static Obj provenance(Input input) {
        ObjectNode snapshot=object(OpportunityJson.toNode(input.before().semantic())),source=obj().put("source_method","query_combat_simulation_inputs_v3").put("query_sequence",input.observation().querySequence());
        copy(snapshot,source,"snapshot_id revision native_revision date_raw paused backend_id");
        JsonNode hello=snapshot.path("diagnostics").get("hello");
        for(String field:List.of("game_version","executable_sha256"))source.set(field,hello!=null&&hello.isObject()&&hello.has(field)?hello.get(field).deepCopy():obj().nullNode());
        return immutable(source);
    }
    /** Pure counterpart of estimate_current_special_knight_initial_stats_12003 over the existing normalized leaf. */
    public static Obj specialInitial(Obj normalizedBase,Obj provenance) {return specialInitial(node(normalizedBase),provenance);}
    private static Obj specialInitial(ObjectNode base,Obj provenance) {
        var rows=obj().arrayNode();List<String> missing=new ArrayList<>();var sums=obj();
        for(String role:List.of("attacker","defender"))sums.putObject(role).put("ready_member_count",0).put("partial_member_count",0).put("ready_member_damage_raw_sum",BigInteger.ZERO).put("ready_member_toughness_raw_sum",BigInteger.ZERO);
        JsonNode armies=base.get("armies");if(armies==null||!armies.isArray()){armies=obj().arrayNode();missing.add("armies");}
        int ai=0;for(var army:armies) {
            String key="armies["+ai+"]";JsonNode knights=army.get("knights");
            if(!"available".equals(army.path("status").asText()))missing.add(key+".available");
            if(knights==null||!knights.isObject()||!"available".equals(knights.path("status").asText())){missing.add(key+".knights.available");ai++;continue;}
            int mi=0;for(var member:array(knights.get("members"))) {
                String mk=key+".knights.members["+mi+"]";JsonNode raw=member.get("effectiveness_context");ObjectNode rawContext=raw!=null&&raw.isObject()?object(raw):obj();
                JsonNode modifiers=rawContext.get("modifier_raw");boolean valid=modifiers!=null&&modifiers.isArray()&&modifiers.size()==9;
                var keys=obj().arrayNode();for(int i=0;i<9;i++)keys.add(0xc1+i);
                var context=CombatKnightKernel.container(keys,valid?modifiers:null,valid?obj().numberNode(9):null);
                var selectedSource=obj().put("source_kind","current_effectiveness_context_observation");selectedSource.set("observation",rawContext.deepCopy());
                var calculated=CombatKnightKernel.compute(new CombatKnightKernel.Input(CombatKnightKernel.optional(member.get("character_id")),CombatKnightKernel.optional(member.get("prowess")),"frozen_current_character_values",
                        CombatKnightKernel.optional(rawContext.get("character_id")),"frozen_current_character_values",context,CombatKnightKernel.optionalList(rawContext.get("operand_raw")),
                        CombatKnightKernel.optional(knights.get("loaded_damage_multiplier")),CombatKnightKernel.optional(knights.get("loaded_toughness_multiplier")),immutable(selectedSource),provenance));
                List<String> gaps=calculated.missing().stream().map(gap->mk+"."+gap).toList();missing.addAll(gaps);
                var observed=obj();copy(member,observed,"knight_effectiveness_raw effective_damage_raw effective_toughness_raw");var comparisons=obj();
                comparisons.set("effectiveness_raw",calculated.effectiveness().isEmpty()?obj().nullNode():obj().booleanNode(eq(obj().numberNode(calculated.effectiveness().orElseThrow()),observed.get("knight_effectiveness_raw"))));
                for(String stat:List.of("effective_damage_raw","effective_toughness_raw"))comparisons.set(stat,calculated.statCache().isEmpty()?obj().nullNode():obj().booleanNode(eq(node(calculated.statCache().orElseThrow()).get(stat),observed.get(stat))));
                var row=rows.addObject().put("army_index",ai).put("member_index",mi).put("modeled_stage","caller_conditional_initial_special_knight_cache").put("ready",calculated.ready());
                row.set("encounter_role",army.get("encounter_role").deepCopy());row.set("public_cunit_id",army.has("army_id")?army.get("army_id").deepCopy():obj().nullNode());row.set("native_carmy_id",army.has("native_carmy_id")?army.get("native_carmy_id").deepCopy():obj().nullNode());row.set("regiment_id",member.get("source_regiment_id").deepCopy());
                nullable(row,"linked_character_full_id",calculated.linkedCharacter().orElse(null));nullable(row,"selected_character_full_id",calculated.selectedCharacter().orElse(null));row.put("read_stage",text(node(calculated.ledger()).get("selected_stage")));strings(row,"missing_inputs",gaps);nullable(row,"effectiveness_raw",calculated.effectiveness().orElse(null));
                row.set("initial_stat_cache",calculated.statCache().isPresent()?node(calculated.statCache().orElseThrow()):obj().nullNode());row.set("current_observation",observed);row.set("observed_matches_calculation",comparisons);row.set("calculation_ledger",node(calculated.ledger()));row.set("raw_context_status",raw!=null&&raw.isObject()&&raw.has("status")?raw.get("status").deepCopy():obj().textNode("absent"));
                String role=army.path("encounter_role").asText();if(sums.has(role)){var summary=object(sums.get(role));String count=calculated.ready()?"ready_member_count":"partial_member_count";summary.put(count,summary.get(count).intValue()+1);if(calculated.statCache().isPresent()){var s=node(calculated.statCache().orElseThrow());for(String stat:List.of("damage","toughness")){String sum="ready_member_"+stat+"_raw_sum";summary.put(sum,integer(summary.get(sum)).add(integer(s.get("effective_"+stat+"_raw"))));}}}
                mi++;
            }ai++;
        }
        var result=obj().put("schema","ck3_12003_current_special_knight_initial_value_v1").put("scope","observed_current_inputs_conditional_initial_special_knight").put("source","264E099->2657AC0->26344C0->2C06D30->28BFC70->2C06B00").put("all_observed_member_inputs_ready",missing.isEmpty()).put("observed_member_count",rows.size());
        int ready=0;for(var row:rows)if(yes(row.get("ready")))ready++;result.put("ready_member_count",ready);strings(result,"missing_inputs",missing);result.set("target_province_id",base.has("target_province_id")?base.get("target_province_id").deepCopy():obj().nullNode());result.set("members_in_query_order",rows);result.set("ready_member_contributions_by_role",sums);result.set("source_provenance",node(provenance));
        result.put("province_used_by_special_formula",false).put("current_observations_modified",false).put("admission_predicted",false).put("constructor_final_stage_inferred",false).put("full_person_preparation_ready",false).put("full_entry_ready",false).put("native_write_performed",false).put("actual_game_days_advanced",0);return immutable(result);
    }
    static Obj physical(CurrentBattleConditionCodec.Condition condition,Optional<Obj> consumed,CombatObservationCache.Frame frame) {
        var result=obj().put("snapshot_revision",condition.source().revision()).put("observed_date_raw",condition.source().dateRaw()).put("combat_id",condition.source().combatId()).put("province_id",condition.source().provinceId());
        var combatSource=obj().put("native_revision",frame.nativeRevision()).put("date_raw",frame.dateRaw());var controlSource=obj().put("native_revision",condition.source().revision()).put("date_raw",condition.source().dateRaw());
        var checks=obj().put("combat_query_native_revision_matches_control",frame.nativeRevision().equals(condition.source().revision())).put("combat_query_date_matches_control",frame.dateRaw().equals(condition.source().dateRaw())).put("control_query_native_revision_matches_control",true).put("control_query_date_matches_control",true);
        var sides=result.putArray("sides");JsonNode events=consumed.isPresent()?node(consumed.orElseThrow()).get("events"):obj().arrayNode();
        String[] fields={"effective_max_size","effective_siege_raw","effective_damage_raw","effective_toughness_raw","effective_pursuit_raw","effective_screen_raw"};
        String[] cached={"max_size","siege_value_raw","damage_raw","toughness_raw","pursuit_raw","screen_raw"};
        for(var side:condition.sides()) {var rows=sides.addObject().put("side_index",side.sideIndex()).putArray("entries_in_native_order");for(var entry:side.entries()) {
            var matches=obj().arrayNode();for(var event:events) {
                JsonNode physical=event.get("physical_entry_writeback");if(entry.physicalEntryIdentity().isEmpty()||nil(physical)||!yes(event.get("entry_association_proven"))||!entry.physicalEntryIdentity().orElseThrow().equals(integer(physical.get("entry_identity")))||nil(physical.get("regiment_id"))||!entry.state().regimentId().and(BigInteger.valueOf(0xffffffffL)).equals(integer(physical.get("regiment_id")))||!Objects.equals(entry.knightCharacterIdRaw().orElse(null),nil(event.get("linked_character_id"))?null:integer(event.get("linked_character_id"))))continue;
                var record=object(event).deepCopy();JsonNode cache=physical.get("entry_cache");var comparisons=obj();boolean equal=true;for(int i=0;i<fields.length;i++){boolean match=eq(entry.sourceEntry().get(fields[i]),cache.get(cached[i]));if(yes(cache.get("ready"))){comparisons.put(fields[i],match);equal&=match;}else comparisons.putNull(fields[i]);}
                record.set("current_cache_field_matches",comparisons);if(yes(cache.get("ready")))record.put("current_cache_matches_writeback",equal);else record.putNull("current_cache_matches_writeback");record.put("capture_date_matches_current_frame",eq(event.get("observed_date_raw"),obj().numberNode(condition.source().dateRaw()))).put("writer_province_matches_current_frame",eq(physical.get("province_id"),obj().numberNode(condition.source().provinceId()))).put("historical_record_is_current_cache",false);record.set("query_source_coordinate_checks",checks.deepCopy());matches.add(record);
            }
            var row=rows.addObject();var id=row.putObject("identity");id.put("bucket",entry.bucket()).put("bucket_index",entry.bucketIndex()).put("regiment_id",entry.state().regimentId()).put("native_carmy_id",entry.nativeArmyId()).put("public_cunit_id",entry.publicUnitId()).put("owner_character_id",entry.ownerCharacterId());nullable(id,"physical_entry_identity",entry.physicalEntryIdentity().orElse(null));
            var association=row.putObject("physical_entry_writeback_association").put("status",matches.isEmpty()?"no_matching_physical_entry_writeback":"physical_entry_writeback_observed");nullable(association,"physical_entry_identity",entry.physicalEntryIdentity().orElse(null));association.set("matching_events_in_capture_order",matches);var latest=matches.isEmpty()?null:matches.get(matches.size()-1);for(String key:List.of("current_cache_field_matches","current_cache_matches_writeback"))association.set(key,latest==null?obj().nullNode():latest.get(key).deepCopy());association.put("historical_record_is_current_cache",false).put("stored_stats_replaced",false);
        }}
        result.set("combat_query_source",combatSource);result.set("control_query_source",controlSource);result.set("query_source_coordinate_checks",checks);result.put("fresh_condition_modified",false).put("full_person_ready",false).put("full_entry_ready",false);return immutable(result);
    }
}
