package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleLeafRecord.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleLeafRecord.Kind.*;

/** Exact current conference gates, backward pack probes and four independent native PC families. */
final class BattleConferenceCodec {
    private BattleConferenceCodec() { }
    private static ObjectNode objectRecord(JsonNode raw,String field,int offset) {
        ObjectNode out=parseRecord(raw,field,f(I32,true,"requested_full_id_raw","full_id_raw"),f(TEXT,true,"selection","identity","reason"));
        String selected=s(out,"selection"),registry="registry_full_id_"+Integer.toHexString(offset);
        require(selected==null||selected.equals("native_fallback")||selected.equals(registry),field,"invalid object selection");
        if(selected!=null)require(present(out,"identity"),field,"selected object lacks actual identity");
        if(registry.equals(selected))require(n(out,"requested_full_id_raw")!=null&&Objects.equals(n(out,"full_id_raw"),n(out,"requested_full_id_raw")),field,"registry full ID differs");return out;
    }
    private static void absent(JsonNode out,String field,String... keys) {for(String key:keys)require(nil(out.get(key)),field,"undemanded operand: "+key);}
    private static ObjectNode pack(JsonNode raw,String field) {
        ObjectNode out=parseRecord(raw,field,f(TEXT,false,"status"),f(BOOL,false,"ready"),f(TEXT,true,"configuration_identity","selection","pack_identity","reason"),f(I32,true,"count_raw","selected_native_index","default_guard_raw"),f(I64,true,"target_q64"),f(U8,true,"enabled_u8"),f(BOOL,true,"array_present"),f(RAW,false,"probes"));
        Availability availability=availability(out,field);
        out.set("probes",array(out.get("probes"),field+".probes",true,(value,path)->parseRecord(value,path,f(I32,false,"native_index"),f(I64,false,"timestamp_q64"))));
        BigInteger flag=n(out,"enabled_u8"),count=n(out,"count_raw"),target=n(out,"target_q64"),selected=n(out,"selected_native_index");JsonNode probes=out.get("probes");
        String selection=s(out,"selection");require(selection==null||Set.of("last_native_row_at_or_before_target","inline_default_54ebab0").contains(selection),field,"invalid pack selection");String known=null;
        if(BigInteger.ZERO.equals(flag)){absent(out,field,"count_raw","array_present","probes","selected_native_index");known="inline_default_54ebab0";}
        else if(flag!=null&&count!=null&&count.signum()>=0&&!nil(probes)&&target!=null) {
            require(BigInteger.valueOf(probes.size()).compareTo(count)<=0,field,"probe count exceeds native row count");BigInteger match=null;
            for(int index=0;index<probes.size();index++) {
                JsonNode probe=probes.get(index);require(n(probe,"native_index").equals(count.subtract(BigInteger.valueOf(1L+index))),field,"backward native probe order differs");
                if(n(probe,"timestamp_q64").compareTo(target)<=0){require(index==probes.size()-1,field,"probes continued after last qualifying native row");match=n(probe,"native_index");}
            }
            if(match!=null){known="last_native_row_at_or_before_target";require(Objects.equals(selected,match),field,"selected row is not last qualifying native row");}
            else if(BigInteger.valueOf(probes.size()).equals(count))known="inline_default_54ebab0";
        }
        if(selection!=null)require(selection.equals(known),field,"selected pack differs from consumed probes");
        if(!"last_native_row_at_or_before_target".equals(selection))require(selected==null,field,"default or unavailable pack has a selected index");
        else require(n(out,"default_guard_raw")==null,field,"mapped pack contains unused inline guard");
        BigInteger guard=n(out,"default_guard_raw");boolean initialized=guard!=null&&guard.signum()!=0&&!guard.equals(BigInteger.valueOf(-1));
        boolean complete=present(out,"configuration_identity","target_q64","enabled_u8","selection","pack_identity")
                &&(!"last_native_row_at_or_before_target".equals(selection)||Boolean.TRUE.equals(b(out,"array_present")))
                &&(!"inline_default_54ebab0".equals(selection)||initialized)&&availability.reason()==null;
        require(availability.ready()==complete,field,"selected pack readiness differs");return out;
    }
    private static Boolean gate(BigInteger magic,BigInteger id,long expected) {return magic==null?null:!magic.equals(BigInteger.valueOf(expected))?false:id==null?null:!id.equals(BigInteger.valueOf(-1));}
    private static ObjectNode family(JsonNode raw,String field,int index,ObjectNode helper,Integer offset) {
        ObjectNode out=parseRecord(raw,field,f(TEXT,false,"status"),f(BOOL,false,"ready"),f(I32,false,"native_index"),f(BOOL,true,"admitted"),f(U32,true,"pc_offset"),f(TEXT,true,"property_identity","reason"),f(RAW,false,"property_block"));
        Availability availability=availability(out,field);out.set("property_block",properties(out.get("property_block"),field+".property_block"));
        Boolean admitted=b(helper,"admitted");require(eq(out,"native_index",index)&&Objects.equals(b(out,"admitted"),admitted),field,"family native order or admission differs");boolean complete;
        if(!Boolean.TRUE.equals(admitted)){absent(out,field,"pc_offset","property_identity","property_block");complete=Boolean.FALSE.equals(admitted);}
        else {require(Objects.equals(n(out,"pc_offset"),offset==null?null:BigInteger.valueOf(offset)),field,"family PC offset differs from predicates");complete=Boolean.TRUE.equals(b(helper.get("pack"),"ready"))&&offset!=null&&present(out,"property_identity")&&pcReady(out.get("property_block"))&&availability.reason()==null;}
        require(availability.ready()==complete,field,"independent family readiness differs");return out;
    }
    static JsonNode normalize(JsonNode input,String field) {
        if(nil(input))return NullNode.instance;
        ObjectNode out=parseRecord(input,field,f(TEXT,false,"status"),f(BOOL,false,"ready"),f(I32,false,"character_id"),f(BOOL,true,"carrier_present","conference_admitted","character_admitted","admitted","relation_registry_present","owner_matches"),f(TEXT,true,"first_group_identity","second_group_identity","category","reason"),f(U32,true,"conference_magic_raw","character_magic_raw"),f(I32,true,"character_full_id_raw","owner_full_id_raw"),f(RAW,false,"conference","first","second","pack","families"));
        Availability availability=availability(out,field);out.set("conference",objectRecord(out.get("conference"),field+".conference",8));out.set("first",objectRecord(out.get("first"),field+".first",0x10));out.set("second",objectRecord(out.get("second"),field+".second",0x10));out.set("pack",pack(out.get("pack"),field+".pack"));
        Boolean conference=gate(n(out,"conference_magic_raw"),n(out.get("conference"),"full_id_raw"),0x436f6e66L),character=gate(n(out,"character_magic_raw"),n(out,"character_full_id_raw"),0x43686172L);
        require(Objects.equals(b(out,"conference_admitted"),conference)&&Objects.equals(b(out,"character_admitted"),character),field,"magic/full ID admission differs");
        if(!Boolean.TRUE.equals(conference))absent(out,field,"character_magic_raw","character_full_id_raw","character_admitted");
        BigInteger characterMagic=n(out,"character_magic_raw");if(characterMagic!=null&&!characterMagic.equals(BigInteger.valueOf(0x43686172L)))absent(out,field,"character_full_id_raw");
        Boolean admitted=Boolean.FALSE.equals(conference)?false:Boolean.TRUE.equals(conference)?character:null;require(Objects.equals(b(out,"admitted"),admitted),field,"helper admission differs");
        BigInteger first=n(out.get("first"),"full_id_raw"),second=n(out.get("second"),"full_id_raw");String category=null;
        if(first!=null&&second!=null) {
            if(first.equals(second)){category="same_id";absent(out,field,"first_group_identity","second_group_identity");}
            else if(present(out,"first_group_identity","second_group_identity"))category=s(out,"first_group_identity").equals(s(out,"second_group_identity"))?"same_identity":"different";
        }
        require(Objects.equals(s(out,"category"),category),field,"full ID/QWORD category differs");BigInteger owner=n(out,"owner_full_id_raw"),characterId=n(out,"character_full_id_raw");Boolean ownerMatches=owner!=null&&characterId!=null?owner.equals(characterId):null;
        require(Objects.equals(b(out,"owner_matches"),ownerMatches),field,"owner full DWORD comparison differs");
        if(!Boolean.TRUE.equals(admitted))require(category==null&&owner==null&&nil(out.get("pack").get("selection")),field,"unadmitted helper contains consumed relation/pack operands");
        if(Boolean.FALSE.equals(b(out,"relation_registry_present")))for(String key:List.of("first","second"))require(nil(out.get(key).get("requested_full_id_raw")),field,"null relation registry contains undemanded key");
        Integer[] offsets=new Integer[4];
        if(Boolean.TRUE.equals(admitted)) {
            offsets[3]=0x8f0;if(ownerMatches!=null)offsets[2]=ownerMatches?0x570:0x730;
            if(category!=null){int[] choices=switch(category){case "same_id"->new int[]{0x30,0x1f0,0x3b0};case "same_identity"->new int[]{0xab0,0xc70,0xe30};case "different"->new int[]{0xff0,0x11b0,0x1370};default->throw bad(field,"invalid computed category");};offsets[1]=choices[2];if(ownerMatches!=null)offsets[0]=choices[ownerMatches?0:1];}
        }
        JsonNode families=out.get("families");require(families.isArray()&&families.size()==4,field,"four native families required");ArrayNode normalized=list();boolean all=true;
        for(int index=0;index<4;index++){ObjectNode family=family(families.get(index),field+".families["+index+"]",index,out,offsets[index]);normalized.add(family);all=all&&Boolean.TRUE.equals(b(family,"ready"));}
        out.set("families",normalized);require(availability.ready()==all,field,"four independent family readiness differs");return out;
    }
}
