package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Objects;

/** Exact Lege owner/tier demand, preserving independent weighted-owner and two-PC readiness. */
final class BattlePersonLegacyCodec {
    private BattlePersonLegacyCodec() { }
    private static JsonNode span(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;ObjectNode in=shape(raw,field,"selected_source","count","rows","reason"),out=object();
        out.set("selected_source",text(in.get("selected_source"),field+".selected_source",false,true));nums(in,out,field,32,false,"count");texts(in,out,field,"reason");
        JsonNode rows=array(in.get("rows"),field+".rows",true,(item,name)->{
            ObjectNode row=shape(item,name,"native_index","definition_identity","weight_q64"),normalized=object();index(row,normalized,name,false);texts(row,normalized,name,"definition_identity");nums(row,normalized,name,64,false,"weight_q64");return normalized;
        });order(rows,field);out.set("rows",rows);return out;
    }
    private static boolean ownerReady(JsonNode header,JsonNode blocks) {
        if(nil(header)||nil(header.get("count"))||!nil(header.get("reason")))return false;BigInteger count=integer(header.get("count"));JsonNode rows=header.get("rows");
        if(count.signum()<=0)return rows.isArray()&&rows.isEmpty();if(!rows.isArray()||!count.equals(BigInteger.valueOf(rows.size())))return false;
        for(JsonNode row:rows) {
            if(nil(row.get("definition_identity"))||nil(row.get("weight_q64")))return false;JsonNode selected=null;
            for(JsonNode block:blocks)if(block.get("definition_identity").equals(row.get("definition_identity"))){selected=block.get("properties");break;}
            if(selected==null||!propertiesReady(selected)||!nil(selected.get("reason")))return false;
        }
        return true;
    }
    static JsonNode normalize(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;
        ObjectNode out=start(raw,field,"character_id","requested_full_id_raw","selected_full_id_raw","full_id_raw","character_full_id_raw","owner_full_id_raw","resolution_selection","object_identity","table_identity","definition_identity","tier_selection","selected_row_identity","component_present","admitted","owner_matches","owner_header_ready","magic_u32","rank_raw_i8","owner_weighted_header","owner_definition_blocks","base_pc","tier_pc","composite_ready");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));nums(raw,out,field,32,false,"requested_full_id_raw","selected_full_id_raw","full_id_raw","character_full_id_raw","owner_full_id_raw");
        texts(raw,out,field,"resolution_selection","object_identity","table_identity","definition_identity","tier_selection","selected_row_identity");bools(raw,out,field,"component_present","admitted","owner_matches","owner_header_ready");nums(raw,out,field,32,true,"magic_u32");nums(raw,out,field,8,false,"rank_raw_i8");out.set("composite_ready",bool(raw.get("composite_ready"),field+".composite_ready",false));
        JsonNode header=span(raw.get("owner_weighted_header"),field+".owner_weighted_header");out.set("owner_weighted_header",header);
        var identities=new HashSet<String>();JsonNode blocks=array(raw.get("owner_definition_blocks"),field+".owner_definition_blocks",false,(item,name)->{
            ObjectNode row=shape(item,name,"definition_identity","properties"),normalized=object();JsonNode identity=text(row.get("definition_identity"),name+".definition_identity",false,true);require(identities.add(identity.textValue()),name,"physical Definition identity repeated");normalized.set("definition_identity",identity);normalized.set("properties",properties(row.get("properties"),name+".properties"));return normalized;
        });out.set("owner_definition_blocks",blocks);out.set("base_pc",pc(raw.get("base_pc"),field+".base_pc"));out.set("tier_pc",pc(raw.get("tier_pc"),field+".tier_pc"));
        String selection=string(out.get("resolution_selection"));require(selection==null||selection.equals("registry_full_id_8")||selection.equals("native_fallback"),field,"unsupported Lege resolver");
        JsonNode requested=out.get("requested_full_id_raw");if(Boolean.FALSE.equals(booleanValue(out.get("component_present"))))require(nil(requested)||eq(requested,-1),field,"absent carrier requests full FFFFFFFF");
        if("registry_full_id_8".equals(selection))require(!nil(requested)&&requested.equals(out.get("selected_full_id_raw")),field,"full-generation registry selection differs");
        else require(nil(out.get("selected_full_id_raw")),field,"nonindexed resolver published selected generation");
        boolean resolved=selection!=null&&!nil(out.get("object_identity"));JsonNode magic=out.get("magic_u32"),full=out.get("full_id_raw");
        Boolean admitted=!resolved||nil(magic)?null:!eq(magic,0x4c656765L)?false:nil(full)?null:!eq(full,-1);same(out.get("admitted"),admitted,field,"Lege magic/full-ID admission differs");
        require(nil(magic)||eq(magic,0x4c656765L)||nil(full),field,"rejected magic contains undemanded full-ID gate");boolean complete;
        if(!Boolean.TRUE.equals(admitted)) {
            for(String key:new String[]{"character_full_id_raw","owner_full_id_raw","owner_matches","table_identity","definition_identity","rank_raw_i8","tier_selection","selected_row_identity","owner_weighted_header","owner_header_ready"})require(nil(out.get(key)),field,"unadmitted object contains downstream operands");
            require(blocks.isEmpty()&&!out.get("composite_ready").booleanValue()&&absentPc(out.get("base_pc"))&&absentPc(out.get("tier_pc")),field,"unadmitted object contains owner/composite PC");complete=Boolean.FALSE.equals(admitted);
        } else {
            JsonNode actor=out.get("character_full_id_raw"),owner=out.get("owner_full_id_raw");require(nil(actor)||actor.equals(out.get("character_id")),field,"actual Character18 differs from actor");Boolean match=compare(actor,owner);same(out.get("owner_matches"),match,field,"owner DWORD comparison differs");
            BigInteger rank=integer(out.get("rank_raw_i8"));String tier=rank==null?null:rank.signum()>=0&&rank.compareTo(BigInteger.valueOf(3))<0?"direct_rank_0_2":"diagnostic_3f7ab90_outcome_unobserved";same(out.get("tier_selection"),tier,field,"signed-byte tier/diagnostic selection differs");
            boolean direct="direct_rank_0_2".equals(tier)&&!nil(out.get("table_identity"))&&!nil(out.get("selected_row_identity"));
            require("direct_rank_0_2".equals(tier)||nil(out.get("selected_row_identity")),field,"diagnostic rank fabricated returned row");
            require(!"diagnostic_3f7ab90_outcome_unobserved".equals(tier)||is(out.get("reason"),"rank_diagnostic_3f7ab90_result"),field,"diagnostic rank lost actual missing result");
            if(!(direct&&Boolean.TRUE.equals(match)))require(nil(header)&&blocks.isEmpty()&&nil(out.get("owner_header_ready")),field,"undemanded owner header contains physical operands");
            else {require(nil(header)||is(header.get("selected_source"),"selected_28"),field,"owner header source differs");same(out.get("owner_header_ready"),ownerReady(header,blocks),field,"owner header readiness differs");}
            boolean compositeDemand=direct&&match!=null&&!nil(out.get("definition_identity"));if(!compositeDemand)require(absentPc(out.get("base_pc"))&&absentPc(out.get("tier_pc")),field,"unavailable getter/owner contains undemanded composite PCs");
            boolean composite=compositeDemand&&pcReady(out.get("base_pc"))&&pcReady(out.get("tier_pc"));same(out.get("composite_ready"),composite,field,"composite readiness differs from actual PCs");complete=composite&&(Boolean.FALSE.equals(match)||Boolean.TRUE.equals(booleanValue(out.get("owner_header_ready"))));
        }
        ready(out,complete,field);return out;
    }
}
