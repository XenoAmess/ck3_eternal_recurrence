package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;

/** Exact optional V86 observations. These fields never independently infer native admission. */
public final class BattleContextAdmissionsV86Codec {
    public static final Set<String> SELECTOR_FIELDS=Set.of("selector_a_stage1","selector_a_stage2","selector_a_stage3",
            "selector_a_selected_source","selector_a_key_count","selector_a_key_identities","selector_b_resolution",
            "selector_b_primary_keys","selector_b_nested_count","selector_b_nested_keys");
    private BattleContextAdmissionsV86Codec() { }
    public enum Kind { A, B, C }
    public static ObjectNode normalizeSelectorFields(ObjectNode raw,String field) {
        ObjectNode result=object();
        for(String key:SELECTOR_FIELDS)if(raw.has(key)) {
            JsonNode value=raw.get(key);String name=field+"."+key;
            JsonNode normalized=switch(key) {
                case "selector_a_stage1","selector_a_stage2","selector_a_stage3","selector_b_resolution" -> resolution(value,name);
                case "selector_a_selected_source" -> text(value,name,false,false);
                case "selector_a_key_identities" -> array(value,name,true,(item,path)->text(item,path,false,false));
                case "selector_b_primary_keys" -> signedSet(value,name);
                case "selector_b_nested_keys" -> array(value,name,true,BattleContextAdmissionsV86Codec::signedSet);
                default -> number(value,name,32,false,true);
            };
            result.set(key,normalized);
        }
        return result;
    }
    public static ObjectNode normalizeAdmissionExtension(ObjectNode raw,String field,Kind kind) {
        ObjectNode result=object();
        Set<String> names=switch(kind) {
            case A -> Set.of("property_source","property_source_native_index");
            case B -> Set.of("admission_source","admission_nested_native_index");
            case C -> Set.of("locale_classification");
        };
        for(String key:names)if(raw.has(key)) {
            String name=field+"."+key;
            result.set(key,"locale_classification".equals(key) ? normalizeLocale(raw.get(key),name)
                    : key.endsWith("index") ? number(raw.get(key),name,32,false,true) : text(raw.get(key),name,false,false));
        }
        return result;
    }
    public static JsonNode normalizeLocale(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        ObjectNode raw=exact(value,field,Set.of("first_signed_byte","locale_max_multibyte","result_i32","crt_index","thread_locale_flags",
                "flags_mask","thread_state_present","current_locale_present","global_locale_present","selected_locale_present",
                "cached_value_api_status","thread_state_source","locale_source","status","ready","table_element_u16","reason"));
        ObjectNode result=object();result.set("status",text(raw.get("status"),field+".status",false,false));
        result.set("ready",bool(raw.get("ready"),field+".ready",true));result.set("reason",text(raw.get("reason"),field+".reason",true,false));
        for(String key:Set.of("first_signed_byte","locale_max_multibyte","result_i32"))result.set(key,number(raw.get(key),field+"."+key,32,false,true));
        for(String key:Set.of("crt_index","thread_locale_flags","flags_mask"))result.set(key,number(raw.get(key),field+"."+key,32,true,true));
        for(String key:Set.of("thread_state_present","current_locale_present","global_locale_present","selected_locale_present"))result.set(key,bool(raw.get(key),field+"."+key,true));
        for(String key:Set.of("cached_value_api_status","thread_state_source","locale_source"))result.set(key,text(raw.get(key),field+"."+key,false,false));
        result.set("table_element_u16",number(raw.get("table_element_u16"),field+".table_element_u16",16,true,true));
        Status status=Status.decode(result.get("status"),field+".status");Boolean ready=booleanValue(result,"ready");String reason=string(result.get("reason"));
        require(ready!=null && ready==(status==Status.AVAILABLE)
                && (ready ? integer(result,"result_i32")!=null && reason==null : reason!=null && !reason.isEmpty()),field,"classification availability disagrees");
        return result;
    }
    private static JsonNode resolution(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        ObjectNode raw=exact(value,field,Set.of("status","requested_full_id","selected_full_id","reason"));ObjectNode result=object();
        result.set("status",text(raw.get("status"),field+".status",false,false));
        result.set("requested_full_id",number(raw.get("requested_full_id"),field+".requested_full_id",32,true,true));
        result.set("selected_full_id",number(raw.get("selected_full_id"),field+".selected_full_id",32,true,true));
        result.set("reason",text(raw.get("reason"),field+".reason",true,false));return result;
    }
    private static JsonNode signedSet(JsonNode value,String field) {
        if(nil(value))return NullNode.instance;
        ObjectNode raw=exact(value,field,Set.of("native_index","count","keys_i32","reason"));ObjectNode result=object();
        result.set("native_index",number(raw.get("native_index"),field+".native_index",32,false,true));
        result.set("count",number(raw.get("count"),field+".count",32,false,true));
        result.set("keys_i32",numbers(raw.get("keys_i32"),field+".keys_i32",32,false,true,true));
        result.set("reason",text(raw.get("reason"),field+".reason",true,false));return result;
    }
}
