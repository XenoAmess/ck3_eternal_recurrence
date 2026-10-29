package org.xar.ck3.control.wave2.events.registered;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;

/** Complete original option/scope projection. No name or rendered position becomes native identity. */
final class RegisteredProjection {
    private RegisteredProjection() { }
    static final Set<String> OPTION_KEYS = Set.of("befriend_outcome.0002","death_management.1000","epidemic_events.1100","epidemic_events.5007","health.1001","health.1010","health.1015","health.3104","natural_disaster.7031","stress_threshold_special.1001");
    static final Set<String> UNIQUE_KEYS = Set.of("death_management.1007","epidemic_events.1020","fervor.1002");
    static final Set<String> SCOPE_KEYS = Set.of("feast.2001","health.1101","health.3001","health.3101","health.3103","rite_growth.0010","historical_char_creation_events.1");
    static final Set<String> RELATIONAL_KEYS = Set.of("befriend_outcome.0002","chancellor_task.1004","chancellor_task.1104","char_interaction.0232","death_management.1000","epidemic_events.5007","feast.2001","feast.7002","feast.7101","feast_default.6003","feast_default.6231","feast_events_ewan.0801","feast_main_live_fowl.0003","feast_main_live_fowl.9002","health.1001","health.1010","health.1015","health.1101","health.3001","health.3101","health.3103","health.3104","hostile_scheme_discovery.2001","historical_char_creation_events.1","physician_epidemic_events.1000","prison_notification.0001","prison_notification.2001","prison_notification.2002","rite_growth.0010","stress_threshold_special.1001","travel_completion_event.1000");
    static final Set<String> UNSUPPORTED = Set.of("boolean_scope_name_sets","boolean_scopes","character_scope_differs_from","character_scope_matches_any","character_scopes","handling_policy","max_occurrences","native_option_prefix_range","native_option_suffix","option_variants","optional_character_scope_differs_from","optional_character_scope_matches_any","optional_character_scopes","optional_scope_types","optional_unique_character_scope_excludes","scope_variants","selection_deferred","unavailable_character_scopes","unique_character_scope_excludes");
    private static final Set<String> OPTION_FIELDS = Set.of("disabled_native_option_indices","native_option_indices","option_count","selected_native_option_index","selected_option_number","snapshot_option_count","snapshot_option_counts");
    private static final Set<String> SCOPE_FIELDS = Set.of("character_scopes","character_scope_differs_from","character_scope_matches_any","saved_scope_count","saved_scope_names","scope_types","unique_character_scope_excludes");
    record Options(Map<String,Boolean> checks, ObjectValue selected) { }
    record Resolution(ObjectValue contract, Integer index, String error) { }
    static Value sourceHashes(Value analysis) {
        Value migration = get(analysis,"migration_1_20_0_2");
        return yes(get(migration,"policy_contract_compatible")) ? get(migration,"legacy_source_sha256") : get(analysis,"source_sha256");
    }
    static boolean updated(Value analysis, String field) { return obj(get(get(get(analysis,"migration_1_20_0_2"),"definition_review"),"timeline_contract_updates")).contains(field); }
    static Map<String,Boolean> scopeChecks(ObjectValue context, ObjectValue contract, BigInteger player) {
        List<Value> rows = seq(context.get("saved_scopes")); Map<String,Value> scopes = scopes(context);
        Value types = contract.get("scope_types"); Map<String,Boolean> checks = new LinkedHashMap<>();
        checks.put("root_character_id", player.equals(character(context.get("root_scope"))) && player.equals(integer(contract.get("root_character_id"))));
        checks.put("saved_scope_rows_named_unique",scopes.size() == rows.size());
        boolean namesMatch = seq(contract.get("saved_scope_name_sets")).stream().filter(RegistryJson::array)
            .anyMatch(value -> values(value).equals(scopes.keySet().stream().map(RegistryJson::v).collect(java.util.stream.Collectors.toSet())));
        checks.put("saved_scope_names_exact",namesMatch && scopes.size() == rows.size());
        checks.put("scope_types_cover_projection",object(types) && names(types).equals(scopes.keySet()));
        if (contract.contains("saved_scope_count")) checks.put("saved_scope_count",is(contract.get("saved_scope_count"),rows.size()));
        else {
            List<Value> counts = seq(contract.get("saved_scope_counts"));
            checks.put("saved_scope_count",!counts.isEmpty() && counts.stream().allMatch(value -> integer(value) != null) && counts.contains(v(rows.size())));
        }
        obj(types).fields().forEach((name,expected) -> {
            Value scope = scopes.get(name);
            checks.put("scope:"+name+":type",object(scope) && (is(get(scope,"status"),"available") && eq(get(scope,"type_key"),expected)
                || is(expected,"character-or-unavailable") && (is(get(scope,"status"),"unavailable") || is(get(scope,"status"),"available") && is(get(scope,"type_key"),"character"))));
        });
        obj(contract.get("unique_character_scope_excludes")).fields().forEach((name,raw) -> {
            List<Value> excluded = seq(raw); BigInteger id = character(scopes.get(name));
            checks.put("scope:"+name+":unique_character_excludes",array(raw) && !excluded.isEmpty() && excluded.stream().allMatch(value -> integer(value) != null) && id != null && !excluded.contains(v(id)));
        });
        obj(contract.get("character_scopes")).fields().forEach((name,expected) -> checks.put("scope:"+name+":character_id",integer(expected) != null && integer(expected).equals(character(scopes.get(name)))));
        for (String field : List.of("character_scope_matches_any","character_scope_differs_from")) obj(contract.get(field)).fields().forEach((name,raw) -> {
            List<Value> candidates = seq(raw); BigInteger id = character(scopes.get(name));
            List<BigInteger> related = !candidates.isEmpty() && candidates.stream().allMatch(value -> text(value) != null)
                ? candidates.stream().map(value -> character(scopes.get(text(value)))).toList() : List.of();
            boolean complete = id != null && !related.isEmpty() && related.stream().allMatch(Objects::nonNull);
            checks.put("scope:"+name+(field.equals("character_scope_matches_any") ? ":matches_any" : ":differs_from"),complete && (field.equals("character_scope_matches_any") ? related.contains(id) : !related.contains(id)));
        });
        return checks;
    }
    static Options options(ObjectValue context, ObjectValue contract, BigInteger snapshotCount) {
        List<Value> rows = seq(context.get("options")); Value rawNative = contract.get("native_option_indices"); List<Value> nativeIndices = seq(rawNative);
        Value rawDisabled = contract.fields().getOrDefault("disabled_native_option_indices",arr()); List<Value> disabled = seq(rawDisabled);
        BigInteger selectedNative = integer(contract.get("selected_native_option_index"));
        BigInteger selectedNumber = integer(contract.get("selected_option_number"));
        Value rawCounts = contract.get("snapshot_option_counts"); List<Value> counts;
        if (array(rawCounts)) counts = seq(rawCounts);
        else { BigInteger count = integer(contract.fields().getOrDefault("snapshot_option_count",contract.getOrNull("option_count"))); counts = count == null ? List.of() : List.of(v(count)); }
        boolean nativeTyped = array(rawNative) && nativeIndices.stream().allMatch(value -> integer(value) != null) && new HashSet<>(nativeIndices).size() == nativeIndices.size();
        boolean disabledTyped = array(rawDisabled) && disabled.stream().allMatch(value -> integer(value) != null) && new HashSet<>(disabled).size() == disabled.size();
        Map<String,Boolean> checks = new LinkedHashMap<>();
        checks.put("snapshot_option_count",counts.contains(v(snapshotCount)));
        checks.put("rendered_option_count",is(contract.get("option_count"),rows.size()));
        checks.put("native_option_indices_exact",nativeTyped && rows.stream().map(row -> get(row,"native_option_index")).toList().equals(nativeIndices));
        checks.put("disabled_option_contract",nativeTyped && disabledTyped && nativeIndices.containsAll(disabled) && !disabled.contains(v(selectedNative)));
        checks.put("selected_option_mapping",selectedNative != null && selectedNative.add(BigInteger.ONE).equals(selectedNumber));
        ObjectValue selected = null;
        for (int index=0; index<rows.size(); index++) {
            ObjectValue row = obj(rows.get(index)); BigInteger nativeIndex = integer(row.get("native_option_index"));
            boolean enabled = !disabled.contains(v(nativeIndex));
            checks.put("option:"+index+":projection",is(row.get("rendered_index"),index) && yes(row.get("shown")) && (enabled ? yes(row.get("enabled")) : no(row.get("enabled"))) && no(row.get("fallback")) && no(row.get("cancel")));
            if (nativeIndex != null && nativeIndex.equals(selectedNative)) selected = selected == null ? row : null;
        }
        checks.put("selected_native_option_unique",selected != null); checks.put("selected_native_option_enabled",selected != null && yes(selected.get("enabled")));
        return new Options(checks,selected);
    }
    static Resolution optionVariants(ObjectValue context, ObjectValue contract, BigInteger count, String key, boolean notice) {
        Value raw = contract.get("option_variants"); if (!array(raw)) return new Resolution(contract,null,null);
        Set<String> allowed = new HashSet<>(OPTION_FIELDS);
        if (Set.of("befriend_outcome.0002","health.1001","health.1010","health.1015","health.3104","stress_threshold_special.1001").contains(key) || notice) allowed.addAll(Set.of("saved_scope_count","saved_scope_name_sets","scope_types"));
        if (key.equals("death_management.1000")) allowed.addAll(Set.of("boolean_scopes","saved_scope_count","saved_scope_name_sets"));
        if (Set.of("health.1001","health.1010","health.1015","stress_threshold_special.1001").contains(key)) allowed.add("unique_character_scope_excludes");
        if (key.equals("stress_threshold_special.1001")) allowed.add("character_scope_differs_from");
        List<Resolution> candidates = new ArrayList<>(); int index=0;
        ObjectValue base = remove(contract,"option_variants");
        for (Value value : seq(raw)) {
            if (!object(value) || !allowed.containsAll(names(value))) return new Resolution(null,null,"registered_option_variant_contract_unsupported");
            ObjectValue effective = merge(base,obj(value));
            if (key.equals("death_management.1000") && object(effective.get("scope_types")) && array(effective.get("boolean_scopes"))) {
                ObjectValue types = obj(effective.get("scope_types"));
                for (Value name : seq(effective.get("boolean_scopes"))) if (text(name) != null) types = types.with(text(name),v("boolean"));
                effective = effective.with("scope_types",types);
            }
            candidates.add(new Resolution(effective,index++,null));
        }
        candidates.add(new Resolution(base,null,null)); List<Resolution> matches = new ArrayList<>();
        for (Resolution candidate : candidates) { Options projection = options(context,candidate.contract(),count); if (projection.selected()!=null && all(projection.checks())) matches.add(candidate); }
        if (matches.isEmpty()) return new Resolution(null,null,"registered_option_variant_projection_drift");
        Set<List<Value>> signatures = new HashSet<>();
        for (Resolution match : matches) {
            ObjectValue row=match.contract(); Value counts=row.get("snapshot_option_counts");
            if (!array(counts)) counts=arr(row.getOrNull("snapshot_option_count"));
            signatures.add(List.of(row.getOrNull("option_count"),arr(seq(row.get("native_option_indices"))),counts,arr(seq(row.get("disabled_native_option_indices"))),row.getOrNull("selected_option_number"),row.getOrNull("selected_native_option_index")));
        }
        return signatures.size()==1 ? matches.getFirst() : new Resolution(null,null,"registered_option_variant_projection_ambiguous");
    }
    static Resolution scopeVariants(ObjectValue context, ObjectValue contract) {
        Value raw=contract.get("scope_variants"); ObjectValue base=remove(contract,"scope_variants");
        if (!array(raw)) return new Resolution(base,null,null);
        List<Value> actual=seq(context.get("saved_scopes")).stream().map(row->get(row,"name")).toList();
        if (actual.stream().anyMatch(value->text(value)==null) || new HashSet<>(actual).size()!=actual.size()) return new Resolution(null,null,"registered_scope_variant_context_malformed");
        int index=0;
        for (Value value:seq(raw)) {
            if (!object(value)||!SCOPE_FIELDS.containsAll(names(value))) return new Resolution(null,null,"registered_scope_variant_contract_unsupported");
            List<Value> expected=seq(get(value,"saved_scope_names"));
            if (!expected.isEmpty()&&new HashSet<>(expected).equals(new HashSet<>(actual)))
                return new Resolution(remove(merge(base,obj(value)),"saved_scope_names").with("saved_scope_name_sets",arr(arr(expected))),index,null);
            index++;
        }
        return new Resolution(base,null,null);
    }
    static ObjectValue relational(ObjectValue contract) {
        ObjectValue types=obj(contract.get("scope_types")); Set<String> names=new HashSet<>();
        for (String field:List.of("character_scopes","unique_character_scope_excludes","character_scope_matches_any","character_scope_differs_from")) {
            ObjectValue rows=obj(contract.get(field)); names.addAll(rows.fields().keySet());
            if (field.equals("character_scope_matches_any")||field.equals("character_scope_differs_from"))
                rows.fields().values().forEach(value->seq(value).forEach(name->{if(text(name)!=null) names.add(text(name));}));
        }
        for(String name:names) if(!types.contains(name)) types=types.with(name,v("character"));
        return contract.with("scope_types",types);
    }
}
