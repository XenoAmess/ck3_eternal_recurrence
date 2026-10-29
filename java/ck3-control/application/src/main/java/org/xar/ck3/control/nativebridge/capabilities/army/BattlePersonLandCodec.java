package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.util.Set;

/** Raw government bit29, living-first Land source and the source-qualified mode3 gap. */
final class BattlePersonLandCodec {
    private BattlePersonLandCodec() { }
    private static ObjectNode government(JsonNode raw,String field) {
        ObjectNode out=start(raw,field,"selection","selected_character_identity","selection_native_index","government_identity","flags_raw_u32");
        texts(raw,out,field,"selection","selected_character_identity","government_identity");nums(raw,out,field,32,false,"selection_native_index");nums(raw,out,field,32,true,"flags_raw_u32");
        String selection=string(out.get("selection"));require(selection==null||Set.of("death_1d0_88","living_1c0_3f8","global_fallback_5d1e2a8").contains(selection),field,"unsupported government source selection");
        require(nil(out.get("selection_native_index"))||integer(out.get("selection_native_index")).signum()>=0,field,"government source ordinal is negative");
        ready(out,selection!=null&&!nil(out.get("government_identity"))&&!nil(out.get("flags_raw_u32")),field);return out;
    }
    private static ObjectNode first(JsonNode raw,String field) {
        ObjectNode out=start(raw,field,"selection","living_present","death_present","count_raw","array_present","full_id_raw");
        texts(raw,out,field,"selection");bools(raw,out,field,"living_present","death_present","array_present");nums(raw,out,field,32,false,"count_raw","full_id_raw");
        Boolean living=booleanValue(out.get("living_present")),death=booleanValue(out.get("death_present"));
        String selection=Boolean.TRUE.equals(living)?"living_1c0":Boolean.FALSE.equals(living)?Boolean.TRUE.equals(death)?"death_1d0":Boolean.FALSE.equals(death)?"none":null:null;
        same(out.get("selection"),selection,field,"living-first Land source selection differs");
        require(!Boolean.TRUE.equals(living)||death==null,field,"living branch contains undemanded death source");
        boolean complete=false;
        if("none".equals(selection)) {
            require(nil(out.get("count_raw"))&&nil(out.get("array_present"))&&eq(out.get("full_id_raw"),-1),field,"absent first Land must preserve ID -1 without header demand");complete=true;
        } else if(selection!=null&&zero(out.get("count_raw"))) {
            require(nil(out.get("array_present"))&&eq(out.get("full_id_raw"),-1),field,"zero count must preserve ID -1 without array demand");complete=true;
        } else complete=selection!=null&&!nil(out.get("count_raw"))&&!zero(out.get("count_raw"))&&Boolean.TRUE.equals(booleanValue(out.get("array_present")))&&!nil(out.get("full_id_raw"));
        ready(out,complete,field);return out;
    }
    private static ObjectNode land(JsonNode raw,String field,JsonNode first) {
        ObjectNode out=start(raw,field,"selection","requested_full_id_raw","selected_full_id_raw","object_identity","magic_u32","full_id_raw","admitted","balance_raw_q64");
        texts(raw,out,field,"selection","object_identity");nums(raw,out,field,32,false,"requested_full_id_raw","selected_full_id_raw","full_id_raw");nums(raw,out,field,32,true,"magic_u32");nums(raw,out,field,64,false,"balance_raw_q64");bools(raw,out,field,"admitted");
        String selection=string(out.get("selection"));require(selection==null||selection.equals("registry_full_id_10")||selection.equals("native_fallback"),field,"unsupported Land resolution");
        require(first==null||nil(out.get("requested_full_id_raw"))||out.get("requested_full_id_raw").equals(first.get("full_id_raw")),field,"Land resolver requested a different full generation");
        if("registry_full_id_10".equals(selection))require(!nil(out.get("requested_full_id_raw"))&&out.get("requested_full_id_raw").equals(out.get("selected_full_id_raw")),field,"Land full-generation comparator differs");
        Boolean admitted=nil(out.get("magic_u32"))?null:!eq(out.get("magic_u32"),0x4c616e64L)?false:nil(out.get("full_id_raw"))?null:!eq(out.get("full_id_raw"),-1);
        same(out.get("admitted"),admitted,field,"Land magic/full-ID admission differs");
        require(eq(out.get("magic_u32"),0x4c616e64L)||nil(out.get("full_id_raw")),field,"rejected magic contains undemanded full ID");
        require(Boolean.TRUE.equals(admitted)||nil(out.get("balance_raw_q64")),field,"invalid Land contains undemanded balance");
        if(Boolean.TRUE.equals(admitted)&&"registry_full_id_10".equals(selection))require(out.get("full_id_raw").equals(out.get("selected_full_id_raw")),field,"caller Land full ID differs from selected object");
        ready(out,selection!=null&&!nil(out.get("object_identity"))&&admitted!=null&&(!admitted||!nil(out.get("balance_raw_q64"))),field);return out;
    }
    private static ObjectNode mode(JsonNode raw,String field) {
        ObjectNode out=start(raw,field,"income_q64","index_raw_i32");nums(raw,out,field,64,false,"income_q64");nums(raw,out,field,32,false,"index_raw_i32");
        require(!out.get("ready").booleanValue()&&nil(out.get("income_q64"))&&nil(out.get("index_raw_i32"))&&is(out.get("reason"),"mode3_income_2bca580"),field,"minimum source must retain precise unobserved mode3 income");return out;
    }
    private static ObjectNode provider(JsonNode raw,String field) {
        ObjectNode out=start(raw,field,"provider_loaded","count_raw","selection","definition_identity","definition_magic_u32","admitted","pc");
        bools(raw,out,field,"provider_loaded","admitted");nums(raw,out,field,32,false,"count_raw");nums(raw,out,field,32,true,"definition_magic_u32");texts(raw,out,field,"selection","definition_identity");out.set("pc",pc(raw.get("pc"),field+".pc"));
        require(!out.get("ready").booleanValue()&&absentPc(out.get("pc")),field,"missing mode3 classifier cannot publish provider PC");
        for(String key:new String[]{"count_raw","selection","definition_identity","definition_magic_u32","admitted"})require(nil(out.get(key)),field,"missing mode3 classifier contains downstream provider operands");return out;
    }
    static JsonNode normalize(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;
        ObjectNode out=start(raw,field,"character_id","government_source","character_state_present","first_land_source","land_resolution","mode3_classifier","provider_selection","stage_selection");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));bools(raw,out,field,"character_state_present");texts(raw,out,field,"stage_selection");
        ObjectNode government=government(raw.get("government_source"),field+".government_source");out.set("government_source",government);
        JsonNode first=nil(raw.get("first_land_source"))?NullNode.instance:first(raw.get("first_land_source"),field+".first_land_source");out.set("first_land_source",first);
        JsonNode land=nil(raw.get("land_resolution"))?NullNode.instance:land(raw.get("land_resolution"),field+".land_resolution",nil(first)?null:first);out.set("land_resolution",land);
        out.set("mode3_classifier",nil(raw.get("mode3_classifier"))?NullNode.instance:mode(raw.get("mode3_classifier"),field+".mode3_classifier"));
        out.set("provider_selection",nil(raw.get("provider_selection"))?NullNode.instance:provider(raw.get("provider_selection"),field+".provider_selection"));
        String selection=null;
        if(government.get("ready").booleanValue()) {
            if(!integer(government.get("flags_raw_u32")).testBit(29))selection="government_bit29_false";
            else if(Boolean.FALSE.equals(booleanValue(out.get("character_state_present"))))selection="character_1b0_absent";
            else if(Boolean.TRUE.equals(booleanValue(out.get("character_state_present")))&&!nil(first)&&first.get("ready").booleanValue()&&!nil(land)&&land.get("ready").booleanValue()) {
                if(Boolean.FALSE.equals(booleanValue(land.get("admitted"))))selection="first_land_invalid";
                else if(Boolean.TRUE.equals(booleanValue(land.get("admitted")))&&!nil(land.get("balance_raw_q64")))selection=integer(land.get("balance_raw_q64")).signum()>=0?"first_land_nonnegative":"negative_land_mode3_income_unobserved";
            }
        }
        same(out.get("stage_selection"),selection,field,"ordered native stage selection differs");
        if("government_bit29_false".equals(selection)||"character_1b0_absent".equals(selection)) {
            for(String key:new String[]{"first_land_source","land_resolution","mode3_classifier","provider_selection"})require(nil(out.get(key)),field,"early known-zero contains undemanded later groups");
            require(!"government_bit29_false".equals(selection)||nil(out.get("character_state_present")),field,"false bit29 contains undemanded Character1B0");
        }
        if("first_land_invalid".equals(selection)||"first_land_nonnegative".equals(selection))require(nil(out.get("mode3_classifier"))&&nil(out.get("provider_selection")),field,"known-zero Land contains undemanded mode3/provider");
        if("negative_land_mode3_income_unobserved".equals(selection))require(!nil(out.get("mode3_classifier"))&&!nil(out.get("provider_selection")),field,"negative Land must retain actual classifier/provider gap");
        ready(out,selection!=null&&Set.of("government_bit29_false","character_1b0_absent","first_land_invalid","first_land_nonnegative").contains(selection),field);return out;
    }
}
