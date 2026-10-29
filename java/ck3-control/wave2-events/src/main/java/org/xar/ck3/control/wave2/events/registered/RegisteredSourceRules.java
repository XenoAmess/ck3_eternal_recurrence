package org.xar.ck3.control.wave2.events.registered;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegisteredProjection.*;

/** Existing source-reviewed exceptions, each bound to its exact authored contract. */
final class RegisteredSourceRules {
    private RegisteredSourceRules() { }
    static ObjectValue notice(RegisteredEventKnowledge registry, ObjectValue knowledge, String key, BigInteger count) {
        Value analysis=knowledge.get("analysis"), raw=get(analysis,"source_reviewed_effectless_notice");
        if (!object(raw)||!names(raw).equals(Set.of("schema","definition_path","definition_sha256","source_lines","authored_native_option_indices","option_effects_by_native_index","after_effects"))) return null;
        String path=text(get(raw,"definition_path")),digest=text(get(raw,"definition_sha256")),build=text(knowledge.get("ck3_build"));
        if (count.signum()<1||count.compareTo(BigInteger.valueOf(32))>0) return null;
        List<Value> authored=seq(get(raw,"authored_native_option_indices"));
        List<Value> expected=java.util.stream.IntStream.range(0,count.intValueExact()).mapToObj(RegistryJson::v).toList();
        Set<String> keys=new HashSet<>(); expected.forEach(value->keys.add(integer(value).toString()));
        Value effects=get(raw,"option_effects_by_native_index");
        if (!(is(get(raw,"schema"),"xar.ck3.source-reviewed-effectless-notice/v1")&&RegisteredEventKnowledge.EXE.containsKey(build)
            &&is(knowledge.get("ck3_exe_sha256"),RegisteredEventKnowledge.EXE.get(build))&&path!=null&&path.startsWith("events/")&&digest!=null&&digest.length()==64
            &&text(get(raw,"source_lines"))!=null&&object(get(analysis,"source_sha256"))&&is(get(get(analysis,"source_sha256"),path),digest)
            &&array(get(raw,"authored_native_option_indices"))&&authored.equals(expected)&&object(effects)&&names(effects).equals(keys)
            &&obj(effects).fields().values().stream().allMatch(value->array(value)&&seq(value).isEmpty())
            &&eq(get(raw,"after_effects"),json("[{\"kind\":\"custom_tooltip\",\"gameplay_effect\":false}]")))) return null;
        ObjectValue indexed=registry.indexed(build,key); Value definition=indexed.get("definition");
        return !indexed.fields().isEmpty()&&is(get(definition,"relative_path"),path)&&is(get(definition,"file_sha256"),digest) ? obj(raw) : null;
    }
    static Map<String,Boolean> noticeFrame(ObjectValue context, ObjectValue contract, ObjectValue selected) {
        Map<String,Boolean> checks=new LinkedHashMap<>(); Map<String,Value> scopes=scopes(context);
        List<String> characters=obj(contract.get("scope_types")).fields().entrySet().stream().filter(row->is(row.getValue(),"character")).map(Map.Entry::getKey).toList();
        checks.put("effectless_notice_same_event_frame",positive(context.get("current_event_instance_id"))&&positive(context.get("snapshot_revision"))&&integer(context.get("date_raw"))!=null);
        checks.put("effectless_notice_sole_legal_option",array(context.get("options"))&&seq(context.get("options")).size()==1&&selected!=null&&yes(selected.get("shown"))&&yes(selected.get("enabled"))&&eq(selected.get("native_option_index"),contract.get("selected_native_option_index")));
        checks.put("effectless_notice_character_scopes_typed",!characters.isEmpty()&&characters.stream().allMatch(name->character(scopes.get(name))!=null));
        return checks;
    }
    static ObjectValue noticeProfile(ObjectValue review, BigInteger nativeIndex) {
        return b().set("schema","xar.ck3.vanilla-event-choice-effect").set("schema_version",1).set("selected_native_option_index",nativeIndex)
            .set("completeness","all-authored-options-and-common-after-source-reviewed").set("selected_option_effects",arr()).set("common_after_effects",arr())
            .set("non_gameplay_after_presentation",arr(v("custom_tooltip"))).set("source_anchors",arr(v(str(review.get("definition_path"))+":"+str(review.get("source_lines")))))
            .set("source_sha256",review.getOrNull("definition_sha256")).build();
    }
    record ScopeProjection(ObjectValue context, ObjectValue contract, Map<String,Boolean> checks) { }
    static ScopeProjection bookmark(ObjectValue context, ObjectValue contract, ObjectValue knowledge) {
        String digest="5A5CE08980D8C4FDA1DCF40EC26E12D8973C01286F4DA42A6D939776CFD50E03";
        Value analysis=knowledge.get("analysis"),hashes=sourceHashes(analysis),review=get(analysis,"selected_option_scope_dependency_review");
        ObjectValue profile=RegisteredProfiles.selectedEffect(knowledge,BigInteger.TWO);
        List<Value> rows=seq(context.get("saved_scopes")); List<Value> rawNames=rows.stream().map(row->get(row,"name")).toList();
        Map<String,Boolean> checks=new LinkedHashMap<>();
        checks.put("bookmark1070_exact_current_source",is(knowledge.get("ck3_build"),"1.20.0.4")&&is(knowledge.get("ck3_exe_sha256"),RegisteredEventKnowledge.EXE.get("1.20.0.4"))&&is(get(hashes,"events/bookmark_events.txt"),digest));
        ObjectValue expectedReview=b().set("schema","xar.ck3.source-reviewed-selected-option-scopes/v1").set("ck3_build","1.20.0.4").set("selected_native_option_index",2).set("source_sha256",digest).set("root_dependencies",arr(v("root.capital_province"))).set("saved_scope_dependencies",arr()).set("common_after_effects",arr()).build();
        checks.put("bookmark1070_selected_scope_dependency_review",eq(review,expectedReview));
        checks.put("bookmark1070_native_context_backend",is(get(context.get("provenance"),"backend_id"),"ck3-1.20.0.4-native-event-window-v1"));
        checks.put("bookmark1070_root_scope_metadata",is(get(context.get("root_scope"),"raw_type_index"),4)&&is(get(context.get("root_scope"),"subtype"),0));
        checks.put("bookmark1070_all_raw_scope_rows_named_unique",array(context.get("saved_scopes"))&&rawNames.stream().allMatch(value->text(value)!=null&&!text(value).isEmpty())&&new HashSet<>(rawNames).size()==rawNames.size());
        checks.put("bookmark1070_all_raw_scope_rows_structured",array(context.get("saved_scopes"))&&rows.stream().allMatch(row->object(row)&&object(get(row,"scope"))));
        checks.put("bookmark1070_selected_effect_dependencies",is(contract.get("selected_native_option_index"),2)&&is(contract.get("selected_option_number"),3)&&profile!=null&&is(profile.get("source_sha256"),digest)
            &&eq(profile.get("selected_option_effects"),json("[{\"effect\":\"spawn_army\",\"levies\":125,\"men_at_arms\":{\"bowmen\":50,\"light_horsemen\":50,\"armored_horsemen\":25},\"location\":\"root.capital_province\"}]"))
            &&eq(profile.get("common_after_effects"),arr())&&eq(profile.get("observable_postcondition"),json("{\"metric\":\"player_armies.bookmark1070_spawn\",\"expected_relation\":\"new_army_source_shape\",\"material_change_required_for_evidence\":true}")));
        return new ScopeProjection(context.with("saved_scopes",arr()),contract.with("saved_scope_count",v(0)).with("saved_scope_name_sets",arr(arr())).with("scope_types",EMPTY),checks);
    }
    record Witch(ObjectValue contract, boolean booleanNamesMatch) { }
    static Witch witch(ObjectValue context,ObjectValue contract,Value analysis,BigInteger player) {
        Value hashes=sourceHashes(analysis); Value rawScopes=context.get("saved_scopes");
        ObjectValue excludes=b().set("witch",arr(v(player))).build(), optionalExcludes=b().set("created_witch",arr(v(player))).build();
        if (!(is(get(hashes,"events/trait_specific_events/trait_specific_events.txt"),"A4882239AB219EFB2BB082C983403E6E24B8C9DD481E5643ADFE3321ACAC43F7")
            &&is(get(hashes,"common/on_action/yearly_on_actions.txt"),"0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA")
            &&eq(contract.get("scope_types"),json("{\"witch\":\"character\"}"))&&eq(contract.get("optional_scope_types"),json("{\"created_witch\":\"character\",\"witch_secret\":\"secret\",\"old_courtier\":\"boolean\"}"))
            &&eq(contract.get("unique_character_scope_excludes"),excludes)&&eq(contract.get("optional_unique_character_scope_excludes"),optionalExcludes)
            &&eq(contract.get("optional_character_scope_matches_any"),json("{\"created_witch\":[\"witch\"]}"))
            &&eq(contract.get("boolean_scope_name_sets"),json("[[],[\"old_courtier\"]]"))
            &&eq(contract.get("saved_scope_name_sets"),json("[[\"witch\"],[\"old_courtier\",\"witch\"],[\"created_witch\",\"witch\"],[\"created_witch\",\"witch_secret\",\"witch\"]]"))
            &&eq(contract.get("saved_scope_counts"),json("[1,2,3]"))&&eq(contract.get("native_option_indices"),json("[0,1]"))
            &&is(contract.get("selected_option_number"),2)&&is(contract.get("selected_native_option_index"),1)&&array(rawScopes))) return null;
        Set<String> names=scopes(context).keySet();
        ObjectValue projected=contract.with("scope_types",merge(obj(contract.get("scope_types")),onlyPresent(obj(contract.get("optional_scope_types")),names)))
            .with("unique_character_scope_excludes",merge(excludes,onlyPresent(obj(contract.get("optional_unique_character_scope_excludes")),names)))
            .with("character_scope_matches_any",onlyPresent(obj(contract.get("optional_character_scope_matches_any")),names));
        Set<Value> booleanNames=new HashSet<>();
        for (Value row:seq(rawScopes)) if(object(row)&&object(get(row,"scope"))&&is(get(get(row,"scope"),"type_key"),"boolean")) booleanNames.add(get(row,"name"));
        return new Witch(projected,seq(contract.get("boolean_scope_name_sets")).stream().anyMatch(value->values(value).equals(booleanNames)));
    }
    static ObjectValue nickname(ObjectValue context,ObjectValue contract,Value analysis,BigInteger player) {
        Value hashes=sourceHashes(analysis); Value scopes=context.get("saved_scopes");
        ObjectValue aliases=b().set("possible_conqueror",player).set("nickname_root_scope",player).set("nickname_getter",player).build();
        if (!(is(get(hashes,"events/nickname_events/nickname_events.txt"),"C0DCEC2649DC0021C6B17E8BEECAA71BFFA4AE19ACB7C5158FD035212F848448")
            &&is(get(hashes,"common/scripted_effects/00_nickname_effects.txt"),"5E7259ED1C50C843E4C49F73842F2B11F10CDDD5C56D231FED35AF492E8D48C0")
            &&is(get(hashes,"common/on_action/yearly_on_actions.txt"),"0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA")
            &&eq(contract.get("root_character_id"),v(player))&&eq(contract.get("character_scopes"),aliases)
            &&eq(contract.get("unique_character_scope_excludes"),b().set("informer",arr(v(player))).build())
            &&eq(contract.get("scope_types"),json("{\"informer\":\"character\"}"))&&eq(contract.get("boolean_scopes"),json("[\"toggle_null_result\",\"had_nick_the_mad\"]"))
            &&eq(contract.get("saved_scope_name_sets"),json("[[\"possible_conqueror\",\"toggle_null_result\",\"nickname_root_scope\",\"had_nick_the_mad\",\"nickname_getter\",\"informer\"]]"))
            &&is(contract.get("saved_scope_count"),6)&&is(contract.get("option_count"),1)&&is(contract.get("snapshot_option_count"),6)
            &&eq(contract.get("native_option_indices"),json("[1]"))&&is(contract.get("selected_option_number"),2)&&is(contract.get("selected_native_option_index"),1)&&is(contract.get("max_occurrences"),1)
            &&array(scopes)&&seq(scopes).size()==6)) return null;
        List<Value> names=seq(scopes).stream().map(row->get(row,"name")).toList();
        if(names.stream().anyMatch(name->text(name)==null)||new HashSet<>(names).size()!=6) return null;
        Set<Value> flags=new HashSet<>(names); for(String name:List.of("possible_conqueror","nickname_root_scope","nickname_getter","toggle_null_result","informer")) flags.remove(v(name));
        if(flags.size()!=1) return null; String flag=text(flags.iterator().next()); if(flag==null||!flag.matches("had_nick_[a-z][a-z0-9_]*")) return null;
        ObjectValue types=b().set("possible_conqueror","character").set("nickname_root_scope","character").set("nickname_getter","character").set("toggle_null_result","boolean").set(flag,"boolean").set("informer","character").build();
        return contract.with("boolean_scopes",arr(v("toggle_null_result"),v(flag)))
            .with("saved_scope_name_sets",arr(arr(v("possible_conqueror"),v("toggle_null_result"),v("nickname_root_scope"),v(flag),v("nickname_getter"),v("informer"))))
            .with("scope_types",types);
    }
    static boolean historical(RegisteredEventKnowledge registry,ObjectValue knowledge,String build,String key) {
        ObjectValue expected=b().set("events/historical_character_events.txt","1E40FDB1EA99393B45743514180700D623BEFEB09F88B71F811BA09D56B43567")
            .set("common/scripted_effects/00_historical_characters_scripted_effects.txt","BB95C92120B74D80AC6C28F455ECE4E8FCD9D9D6E620EE408989B05B291840FD").build();
        ObjectValue indexed=registry.indexed(build,key); Value definition=indexed.get("definition"),callers=indexed.get("caller_candidates");
        return eq(get(knowledge.get("analysis"),"source_sha256"),expected)&&is(get(definition,"relative_path"),"events/historical_character_events.txt")&&eq(get(definition,"file_sha256"),expected.get("events/historical_character_events.txt"))
            &&array(callers)&&seq(callers).size()==4&&seq(callers).stream().allMatch(row->object(row)&&is(get(row,"relative_path"),"common/scripted_effects/00_historical_characters_scripted_effects.txt")&&eq(get(row,"file_sha256"),expected.get("common/scripted_effects/00_historical_characters_scripted_effects.txt")));
    }
}
