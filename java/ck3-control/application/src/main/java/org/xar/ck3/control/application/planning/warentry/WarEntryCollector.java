package org.xar.ck3.control.application.planning.warentry;

import static org.xar.ck3.control.application.planning.warentry.WarEntryJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.military.declarationpriority.DeclarationObjectivePriority;
import org.xar.ck3.control.military.declarationpriority.JsonField;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsCodec;

/** Actual strategy.py 484-879 collectors. History ordering and complete native provenance are material. */
public final class WarEntryCollector {
    private WarEntryCollector() { }
    private static final BigInteger INT_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final Set<String> ASSESSMENT_KEYS = Set.of("target_character_id", "effective_target_character_id", "distance_raw",
            "actor_power_base_raw", "actor_network_contribution_raw", "actor_power_total_raw", "target_power_base_raw",
            "target_network_contribution_raw", "target_pre_adjustment_total_raw", "target_adjustment_delta_raw",
            "target_power_total_raw", "actual_power_ratio_raw", "target_ai_context_actor_entry_raw", "actor_ai_context_target_entry_raw", "native_flags_raw");
    private static final Set<String> READY = Set.of("actor_identity_ready", "targets_declarable_ready", "effective_targets_ready",
            "ai_context_ready", "native_output_ready", "network_decomposition_ready", "same_frame_ready", "ready");
    private static final List<String> ROOT_READY = List.of("player_identity_ready", "player_monthly_gold_income_ready", "player_health_ready",
            "player_domain_ready", "player_targeting_factions_ready", "primary_title_ready", "primary_title_succession_ready", "held_title_partition_ready",
            "capital_ready", "lieges_ready", "direct_landed_vassals_ready", "adjacent_external_province_holders_ready", "related_character_contexts_ready", "government_ready", "same_frame_ready");

    public record Collected(List<Obj> declarations, Map<BigInteger, Obj> assessments, Optional<Obj> campaignRoot, Optional<Obj> factionAlert) {
        public Collected { declarations = List.copyOf(declarations); assessments = java.util.Collections.unmodifiableMap(new LinkedHashMap<>(assessments)); }
    }
    public static Collected collect(Obj snapshot, List<Obj> history) {
        return new Collected(objects(snapshot.get("declarable_wars")), assessments(snapshot, history), Optional.ofNullable(root(snapshot, history)), Optional.ofNullable(faction(snapshot, history)));
    }
    public static String effectiveCommand(Obj row) {
        String command = text(row.get("command"));
        return "auto-turn".equals(command) ? text(get(child(child(row, "result"), "auto_turn"), "selected_step")) : command;
    }
    public static Obj effectiveResult(Obj row) {
        Obj result = child(row, "result");
        if (!is(row.get("command"), "auto-turn") || result == null) return result;
        for (String key : List.of("assault_action", "route_preview", "war_action", "war_progress_before", "war_progress_after")) if (child(result, key) != null) return result;
        Obj nested = child(child(result, "auto_turn"), "result");
        return nested == null ? result : nested;
    }
    public static BigInteger latest(List<Obj> rows, String command, boolean prefix, boolean successfulOnly) {
        for (int i = rows.size() - 1; i >= 0; i--) {
            Obj row = rows.get(i); String actual = effectiveCommand(row);
            if (actual != null && (prefix ? actual.startsWith(command) : actual.equals(command)) && (!successfulOnly || yes(row.get("ok")))) {
                BigInteger index = number(row, "index"); return index == null ? BigInteger.valueOf(i + 1L) : index;
            }
        }
        return BigInteger.ZERO;
    }
    public static BigInteger latestAdvance(List<Obj> rows) {
        for (int i = rows.size() - 1; i >= 0; i--) if (yes(rows.get(i).get("ok")) && WarEntryHistoryAdvance.isAdvance(effectiveCommand(rows.get(i)))) {
            BigInteger index = number(rows.get(i), "index"); return index == null ? BigInteger.valueOf(i + 1L) : index;
        }
        return BigInteger.ZERO;
    }
    public static Obj preferred(List<Obj> declarations, Map<BigInteger, Obj> assessments, BigInteger actor) {
        var input = new DeclarationObjectivePriority.SelectionInput(actor == null ? JsonField.nullValue() : JsonField.of(actor),
                declarations.stream().map(WarEntryCollector::priorityRow).toList(), JsonField.of(assessments.values().stream().map(row ->
                new DeclarationObjectivePriority.PowerAssessment(required(row,"target_character_id"), required(row,"actor_power_base_raw"),
                        required(row,"actor_network_contribution_raw"), required(row,"target_network_contribution_raw"), required(row,"target_power_total_raw"),
                        required(row,"actual_power_ratio_raw"), required(row,"distance_raw"))).toList()));
        var selected = DeclarationObjectivePriority.preferredIndex(input);
        return selected.isPresent() ? declarations.get(selected.getAsInt()) : null;
    }
    private static DeclarationObjectivePriority.Declaration priorityRow(Obj row) {
        List<BigInteger> titles = new ArrayList<>(); boolean titleReady = row.get("target_title_ids") instanceof Arr;
        for (Value value : array(row.get("target_title_ids"))) { BigInteger n = integer(value); if (n == null) { titleReady = false; break; } titles.add(n); }
        return new DeclarationObjectivePriority.Declaration(stringField(row.get("declaration_id")), integerField(row.get("target_character_id")),
                integerField(row.get("casus_belli_index")), stringField(row.get("casus_belli_key")), integerField(row.get("configuration_index")),
                integerField(row.get("claimant_character_id")), titleReady ? JsonField.of(titles) : JsonField.nullValue(), stringField(row.get("source")));
    }
    private static JsonField<String> stringField(Value value) { String s = text(value); return s == null ? JsonField.nullValue() : JsonField.of(s); }
    private static JsonField<BigInteger> integerField(Value value) { BigInteger n = integer(value); return n == null ? JsonField.nullValue() : JsonField.of(n); }

    private static Map<BigInteger, Obj> assessments(Obj snapshot, List<Obj> history) {
        Map<BigInteger, Obj> result = new LinkedHashMap<>(); List<Obj> payloads = new ArrayList<>();
        Obj direct = child(snapshot, "war_entry_assessments"); if (direct != null) payloads.add(direct);
        for (Obj row : history) {
            String command = effectiveCommand(row); if (command == null || !command.startsWith("query-war-entry-assessments-v1-") || !yes(row.get("ok"))) continue;
            Obj value = child(row, "result"); if (child(value, "result") != null) value = child(value, "result");
            Obj payload = child(value, "war_entry_assessments"); if (payload != null) payloads.add(payload);
        }
        for (Obj payload : payloads) try {
            Obj normalized = normalizeAssessments(payload, required(child(snapshot,"played_character"),"character_id"), required(snapshot,"native_revision"));
            if (!same(normalized.get("date_raw"), snapshot.get("date_raw"))) continue;
            for (Obj row : objects(normalized.get("assessments"))) result.put(required(row,"target_character_id"), row);
        } catch (IllegalArgumentException | NullPointerException ignored) { /* Original collector skips invalid/partial frames, never repairs one. */ }
        return result;
    }
    /** Full source normalizer, including exact-build RVA identity and checked int64 decomposition. */
    public static Obj normalizeAssessments(Obj payload, BigInteger actor, BigInteger revision) {
        require(payload.members().keySet().equals(Set.of("schema_version","status","snapshot_revision","date_raw","actor_character_id","requested_target_character_ids","assessments","readiness","provenance")), "assessment schema fields");
        require(eq(payload.get("schema_version"),1) && is(payload.get("status"),"available"), "assessment schema/status");
        require(range(payload.get("snapshot_revision"),BigInteger.ZERO,BigInteger.valueOf(Long.MAX_VALUE)).equals(revision), "assessment revision");
        range(payload.get("date_raw"),BigInteger.valueOf(Integer.MIN_VALUE),INT_MAX);
        require(positive32(payload.get("actor_character_id")).equals(actor), "assessment actor");
        List<Value> targets = strictArray(payload.get("requested_target_character_ids")); List<Value> rows = strictArray(payload.get("assessments"));
        require(targets.size()==1 && rows.size()==1,"assessment one-target request"); BigInteger target = positive32(targets.getFirst());
        Obj row = object(rows.getFirst()); require(row != null && row.members().keySet().equals(ASSESSMENT_KEYS), "assessment row fields");
        require(positive32(row.get("target_character_id")).equals(target),"assessment target order"); positive32(row.get("effective_target_character_id"));
        for (String key : List.of("distance_raw","actor_power_base_raw","actor_network_contribution_raw","actor_power_total_raw","target_power_base_raw","target_network_contribution_raw","target_pre_adjustment_total_raw","target_adjustment_delta_raw","target_power_total_raw","actual_power_ratio_raw")) {
            BigInteger n=range(row.get(key),BigInteger.valueOf(Long.MIN_VALUE),BigInteger.valueOf(Long.MAX_VALUE));
            if (!Set.of("actor_network_contribution_raw","target_network_contribution_raw","target_adjustment_delta_raw").contains(key)) require(n.signum()>=0,"negative power field");
        }
        sum(row,"actor_power_base_raw","actor_network_contribution_raw","actor_power_total_raw");
        sum(row,"target_power_base_raw","target_network_contribution_raw","target_pre_adjustment_total_raw");
        sum(row,"target_pre_adjustment_total_raw","target_adjustment_delta_raw","target_power_total_raw");
        range(row.get("target_ai_context_actor_entry_raw"),BigInteger.valueOf(Integer.MIN_VALUE),INT_MAX);
        range(row.get("actor_ai_context_target_entry_raw"),BigInteger.valueOf(Integer.MIN_VALUE),INT_MAX);
        range(row.get("native_flags_raw"),BigInteger.ZERO,BigInteger.valueOf(255));
        Obj ready=child(payload,"readiness"); require(ready!=null && ready.members().keySet().equals(READY) && ready.members().values().stream().allMatch(WarEntryJson::yes),"assessment readiness");
        Obj provenance=child(payload,"provenance"); require(provenance!=null && provenance.members().keySet().equals(Set.of("game_version","executable_sha256","assessment_rva","network_collector_rva","power_leaf","fixed_point_scale")),"assessment provenance fields");
        var build=FactionAlertModel.Build.exact(text(provenance.get("game_version")),text(provenance.get("executable_sha256")));
        boolean old=build==FactionAlertModel.Build.CK3_11906, fourth=build==FactionAlertModel.Build.CK3_12004;
        require(is(provenance.get("assessment_rva"),old?"0x1878A00":fourth?"0x1A23220":"0x1A23240") && is(provenance.get("network_collector_rva"),old?"0x1879850":fourth?"0x1A23FF0":"0x1A24010") && is(provenance.get("power_leaf"),old?"CCharacter+0x1B8->+0x308":"CCharacter+0x1C0->+0x308") && eq(provenance.get("fixed_point_scale"),100000),"assessment native source drift");
        return payload.with("provenance",provenance.with("executable_sha256",new Text(build.sha256())));
    }
    private static void sum(Obj row,String a,String b,String total) { BigInteger n=required(row,a).add(required(row,b)); require(n.bitLength()<=63 && n.equals(required(row,total)),"int64 power decomposition"); }
    private static List<Value> strictArray(Value value) { require(value instanceof Arr,"array required"); return array(value); }
    private static BigInteger positive32(Value value) { return range(value,BigInteger.ONE,INT_MAX); }
    private static BigInteger range(Value value,BigInteger min,BigInteger max) { BigInteger n=integer(value); require(n!=null && n.compareTo(min)>=0 && n.compareTo(max)<=0,"exact integer range"); return n; }
    private static void require(boolean condition,String reason) { if(!condition) throw new IllegalArgumentException(reason); }

    private static Obj root(Obj snapshot,List<Obj> history) {
        List<Obj> candidates=new ArrayList<>();
        for(int i=history.size()-1;i>=0;i--) { Obj row=history.get(i); if("query-campaign-root-context-v1".equals(effectiveCommand(row)) && yes(row.get("ok"))) { Obj value=child(effectiveResult(row),"campaign_root_context"); if(value!=null)candidates.add(value); } }
        Obj direct=child(snapshot,"campaign_root_context");if(direct!=null)candidates.add(direct);
        for(Obj candidate:candidates) {
            Obj ready=child(candidate,"readiness"); boolean compatible=ready!=null && (yes(ready.get("ready")) || (no(ready.get("ready")) && no(ready.get("selected_game_rule_tokens_ready")) && ROOT_READY.stream().allMatch(key->yes(ready.get(key)))));
            if(is(candidate.get("status"),"available") && same(candidate.get("snapshot_revision"),snapshot.get("native_revision")) && same(candidate.get("date_raw"),snapshot.get("date_raw")) && same(candidate.get("player_character_id"),get(child(snapshot,"played_character"),"character_id")) && compatible)return candidate;
        }
        return null;
    }
    private static Obj faction(Obj snapshot,List<Obj> history) {
        if(!yes(snapshot.get("paused")))return null; List<Obj> candidates=new ArrayList<>();
        for(int i=history.size()-1;i>=0;i--) {
            Obj row=history.get(i);if(!"query-player-faction-alerts-v1".equals(effectiveCommand(row)) || !yes(row.get("ok")))continue;
            Obj value=effectiveResult(row); if(value==null)continue; boolean bound=true;
            for(String key:List.of("snapshot_id","revision","native_revision")) {Value queried=value.get("queried_"+key);if(queried!=null && !same(queried,snapshot.get(key)))bound=false;}
            Obj payload=child(value,"player_faction_alerts");if(bound && payload!=null)candidates.add(payload);
        }
        Obj direct=child(snapshot,"player_faction_alerts");if(direct!=null)candidates.add(direct);
        for(Obj candidate:candidates)try {
            var normalized=FactionAlertsCodec.normalize(OpportunityJson.encode(candidate),new FactionAlertModel.ExpectedFrame(required(snapshot,"date_raw").intValueExact(),required(snapshot,"native_revision"),Optional.empty()));
            Obj value=parse(normalized.json());
            // A source/frame-normalized unavailable result has no actor by contract. Retain its
            // refusal DATA so the selector defers instead of issuing the same optional query again.
            if(normalized.frame() instanceof FactionAlertModel.Unavailable)return value;
            if(same(value.get("player_character_id"),get(child(snapshot,"played_character"),"character_id")))return value;
        }catch(IllegalArgumentException | ArithmeticException ignored) { }
        return null;
    }
    public static Obj factionContext(Obj root,Obj alert) {
        Value count=get(root,"player_targeting_faction_count");
        if(alert==null && eq(count,0))return obj().text("status","known_empty_targeting").bool("prior_scope_eligible",true).number("targeting_faction_count",0).text("source","same_frame_campaign_root_count").build();
        if(alert==null)return obj().text("status","unavailable").bool("prior_scope_eligible",false).value("targeting_faction_count",count).text("reason","same_frame_faction_alert_unavailable").build();
        Obj projection=child(alert,"planner_projection");
        if(!is(alert.get("status"),"available") || !same(alert.get("targeting_faction_count"),count) || !yes(get(child(alert,"readiness"),"alert_ready")) || !is(get(projection,"status"),"available"))return obj().text("status","unavailable").bool("prior_scope_eligible",false).value("targeting_faction_count",count).text("reason","faction_alert_components_unavailable").value("component_unavailable_reasons",alert.get("component_unavailable_reasons")).build();
        String status=!array(projection.get("war_handoff_faction_ids")).isEmpty()?"war_handoff":yes(projection.get("dangerous"))?"dangerous":"watch";
        List<Obj> targets=objects(alert.get("targeting_factions")).stream().map(row->project(row,"faction_id","faction_type_key","dangerous_by_stock_rule","danger_reason","faction_at_war","power","power_threshold","discontent","discontent_per_month","months_until_max_discontent")).toList();
        return obj().bool("prior_scope_eligible",status.equals("watch")).text("source","query-player-faction-alerts-v1").value("snapshot_revision",alert.get("snapshot_revision")).value("date_raw",alert.get("date_raw")).value("targeting_faction_count",count).merge(projection).text("status",status).value("factions",rows(targets)).value("county_culture_context",cultureContext(alert)).build();
    }
    private static Obj cultureContext(Obj alert) {
        List<Obj> rows=new ArrayList<>();int ready=0;
        for(Obj faction:objects(alert.get("targeting_factions"))) {
            Map<BigInteger,Obj> materials=new LinkedHashMap<>();for(Obj material:objects(faction.get("county_member_observations")))materials.put(number(material,"county_title_id"),material);
            for(Value county:array(faction.get("county_member_title_ids"))) {
                Obj material=materials.get(integer(county)); boolean fields=material!=null && material.get("culture_relation_status")!=null;
                boolean available=fields && is(material.get("culture_relation_status"),"available");if(available)ready++;
                rows.add(obj().value("faction_id",faction.get("faction_id")).value("faction_type_key",faction.get("faction_type_key")).value("target_character_id",faction.get("target_character_id")).value("county_title_id",county).value("county_culture_id",get(material,"county_culture_id")).value("target_culture_id",get(material,"target_culture_id")).value("same_culture_as_target",get(material,"same_culture_as_target")).text("culture_relation_status",fields?text(material.get("culture_relation_status")):"unavailable").bool("relation_input_ready",available).text("unavailable_reason",available?null:fields?"culture_relation_unavailable":material!=null?"culture_fields_not_published":"county_member_observation_not_published").build());
            }
        }
        return obj().text("status",rows.isEmpty()?"not_applicable":ready==rows.size()?"available":ready>0?"partial":"unavailable").bool("relation_input_ready",!rows.isEmpty() && ready==rows.size()).text("source","query-player-faction-alerts-v1").value("snapshot_revision",alert.get("snapshot_revision")).value("date_raw",alert.get("date_raw")).value("player_character_id",alert.get("player_character_id")).value("provenance",alert.get("provenance")).number("county_row_count",rows.size()).number("available_relation_count",ready).value("rows",rows(rows)).build();
    }
}
