package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.util.Set;

/** Provider192 signed upper-first thresholds and independent direct/mapped four-slot lists. */
final class BattlePersonProviderListsCodec {
    private BattlePersonProviderListsCodec() { }
    private static final String DEFAULT="inline_nested_mapped_default_5dc21b0";
    private static ObjectNode provider(JsonNode raw,String field) {
        ObjectNode out=start(raw,field,"provider_loaded","provider_identity","character_192_i16","upper_i32","lower_i32","selection","selected_identity","magic_u32","admitted","pc");
        bools(raw,out,field,"provider_loaded","admitted");texts(raw,out,field,"provider_identity","selection","selected_identity");nums(raw,out,field,16,false,"character_192_i16");nums(raw,out,field,32,false,"upper_i32","lower_i32");nums(raw,out,field,32,true,"magic_u32");out.set("pc",pc(raw.get("pc"),field+".pc"));
        BigInteger value=integer(out.get("character_192_i16")),upper=integer(out.get("upper_i32")),lower=integer(out.get("lower_i32"));String selection=null;
        if(Boolean.TRUE.equals(booleanValue(out.get("provider_loaded")))&&value!=null&&upper!=null) {
            if(value.compareTo(upper)>=0){selection="provider_16a0";require(lower==null,field,"upper success contains undemanded lower threshold");}
            else if(lower!=null)selection=value.compareTo(lower)<=0?"provider_16b0":"native_fallback_5d1e0b0";
        }
        same(out.get("selection"),selection,field,"upper-first signed provider selection differs");Boolean admitted=selection!=null&&!nil(out.get("magic_u32"))?eq(out.get("magic_u32"),0x4744624fL):null;
        same(out.get("admitted"),admitted,field,"selected Definition magic admission differs");require(Boolean.TRUE.equals(admitted)||absentPc(out.get("pc")),field,"rejected provider contains undemanded PC");
        ready(out,Boolean.TRUE.equals(booleanValue(out.get("provider_loaded")))&&!nil(out.get("provider_identity"))&&selection!=null&&!nil(out.get("selected_identity"))&&admitted!=null&&(!admitted||pcReady(out.get("pc"))),field);return out;
    }
    private static JsonNode slots(JsonNode raw,String field,boolean nested,JsonNode rite,BigInteger guard) {
        if(nil(raw))return NullNode.instance;require(raw.isArray()&&raw.size()==4,field,"resolved table requires four physical slots");ArrayNode out=list();String key=nested?"mapped_family":"pc";
        for(int i=0;i<raw.size();i++) {
            String name=field+"["+i+"]";ObjectNode row=shape(raw.get(i),name,"native_index",key),item=object();index(row,item,name,false);require(eq(item.get("native_index"),i),name,"slot native order differs");
            item.set(key,nested?BattlePersonContextPrefixCodec.mappedFamily(row.get(key),name+"."+key,rite,DEFAULT,guard):pc(row.get(key),name+".pc"));out.add(item);
        }
        return out;
    }
    private static ObjectNode occurrence(JsonNode raw,String field,int ordinal,JsonNode rite,BigInteger guard) {
        ObjectNode in=shape(raw,field,"native_index","requested_full_id_raw","resolution_selection","selected_full_id_raw","object_identity","table_identity","direct_rows","nested_rows","direct_ready","mapped_ready","ready","reason"),out=object();
        index(in,out,field,false);nums(in,out,field,32,false,"requested_full_id_raw","selected_full_id_raw");texts(in,out,field,"resolution_selection","object_identity","table_identity","reason");
        for(String key:new String[]{"direct_ready","mapped_ready","ready"})out.set(key,bool(in.get(key),field+"."+key,false));
        String selection=string(out.get("resolution_selection"));require(eq(out.get("native_index"),ordinal)&&(selection==null||selection.equals("registry_full_id_8")||selection.equals("native_fallback")),field,"occurrence order/full-ID resolution differs");
        if("registry_full_id_8".equals(selection))require(!nil(out.get("requested_full_id_raw"))&&out.get("requested_full_id_raw").equals(out.get("selected_full_id_raw")),field,"full-generation comparator differs");
        JsonNode direct=slots(in.get("direct_rows"),field+".direct_rows",false,rite,guard),mapped=slots(in.get("nested_rows"),field+".nested_rows",true,rite,guard);out.set("direct_rows",direct);out.set("nested_rows",mapped);
        boolean resolved=selection!=null&&!nil(out.get("object_identity"))&&!nil(out.get("table_identity"));boolean directReady=resolved&&!nil(direct),mappedReady=resolved&&!nil(mapped);
        for(JsonNode row:direct)directReady&=pcReady(row.get("pc"));for(JsonNode row:mapped)mappedReady&=row.get("mapped_family").get("ready").booleanValue();
        same(out.get("direct_ready"),directReady,field,"independent direct-slot readiness differs");same(out.get("mapped_ready"),mappedReady,field,"independent mapped-slot readiness differs");ready(out,directReady&&mappedReady,field);return out;
    }
    private static ObjectNode family(JsonNode raw,String field,String family,Boolean land,Boolean death,JsonNode rite,BigInteger guard) {
        ObjectNode out=start(raw,field,"direct_ready","mapped_ready","header_selection","default_init_guard_raw","count_raw","numeric_count","array_present","rows");
        out.set("direct_ready",bool(raw.get("direct_ready"),field+".direct_ready",false));out.set("mapped_ready",bool(raw.get("mapped_ready"),field+".mapped_ready",false));bools(raw,out,field,"array_present");texts(raw,out,field,"header_selection");nums(raw,out,field,32,false,"default_init_guard_raw","count_raw","numeric_count");
        String current="current_1c0_"+family.substring(family.length()-3),selection=string(out.get("header_selection"));boolean expectedCurrent=Boolean.TRUE.equals(land)&&Boolean.FALSE.equals(death);
        require(selection==null||selection.equals(current)||selection.equals("inline_default_5d67e60")||selection.equals("modeled_empty_default_5d67e60"),field,"unsupported actual list header");
        if(selection!=null)require(selection.equals(current)==expectedCurrent,field,"list header differs from current1C0/1D0 source");
        JsonNode original=raw.get("rows"),rows=NullNode.instance;if(!nil(original)){require(original.isArray(),field,"ordered occurrence list required");ArrayNode normalized=list();for(int i=0;i<original.size();i++)normalized.add(occurrence(original.get(i),field+".rows["+i+"]",i,rite,guard));rows=normalized;}out.set("rows",rows);
        JsonNode count=out.get("count_raw"),numeric=out.get("numeric_count"),defaultGuard=out.get("default_init_guard_raw");boolean complete;
        if("modeled_empty_default_5d67e60".equals(selection)) {
            require((zero(defaultGuard)||eq(defaultGuard,-1))&&nil(count)&&zero(numeric)&&nil(out.get("array_present"))&&rows.isArray()&&rows.isEmpty(),field,"modeled default contains physical operands or lacks observed guard");complete=true;
        } else {
            require(count.equals(numeric),field,"numeric count differs from actual header");complete=selection!=null&&!nil(count)&&integer(count).signum()>=0&&rows.isArray()&&integer(count).equals(BigInteger.valueOf(rows.size()));
            if(positive(count))complete&=Boolean.TRUE.equals(booleanValue(out.get("array_present")));
            if("inline_default_5d67e60".equals(selection))complete&=!nil(defaultGuard)&&!zero(defaultGuard)&&!eq(defaultGuard,-1);
            if(current.equals(selection))require(nil(defaultGuard),field,"current header contains undemanded default guard");
        }
        boolean direct=complete,mapped=complete;for(JsonNode row:rows){direct&=row.get("direct_ready").booleanValue();mapped&=row.get("mapped_ready").booleanValue();}
        same(out.get("direct_ready"),direct,field,"independent direct-list readiness differs");same(out.get("mapped_ready"),mapped,field,"independent mapped-list readiness differs");ready(out,direct&&mapped,field);return out;
    }
    static JsonNode normalize(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;ObjectNode out=start(raw,field,"character_id","current_land_present","current_death_present","rite","mapped_default_guard_raw","provider_192","list_168","list_180");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));bools(raw,out,field,"current_land_present","current_death_present");nums(raw,out,field,32,false,"mapped_default_guard_raw");
        ObjectNode rite=BattlePersonContextPrefixCodec.rite(raw.get("rite"),field+".rite");out.set("rite",rite);ObjectNode provider=provider(raw.get("provider_192"),field+".provider_192");out.set("provider_192",provider);boolean complete=provider.get("ready").booleanValue();
        for(String name:new String[]{"list_168","list_180"}) {
            ObjectNode family=family(raw.get(name),field+"."+name,name,booleanValue(out.get("current_land_present")),booleanValue(out.get("current_death_present")),rite,integer(out.get("mapped_default_guard_raw")));out.set(name,family);complete&=family.get("ready").booleanValue();
        }
        require(out.get("ready").booleanValue()==complete,field,"whole stage differs from three independent families");return out;
    }
}
