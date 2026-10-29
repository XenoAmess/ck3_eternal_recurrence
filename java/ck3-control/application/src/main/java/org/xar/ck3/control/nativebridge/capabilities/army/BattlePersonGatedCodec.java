package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.util.Set;

/** Literal tree/flag precedence, fresh temporary rank and exact CC/C8/current/related demand. */
final class BattlePersonGatedCodec {
    private BattlePersonGatedCodec() { }
    static ObjectNode named(JsonNode raw,String field,int slot) {
        ObjectNode out=start(raw,field,"slot_offset","entry_identity","tree_present","tree_identity","fixed_flag_u8","raw_fixed_q64","value_q64","kind");
        out.set("slot_offset",number(raw.get("slot_offset"),field+".slot_offset",32,false,false));texts(raw,out,field,"entry_identity","tree_identity");bools(raw,out,field,"tree_present");nums(raw,out,field,8,true,"fixed_flag_u8");nums(raw,out,field,64,false,"raw_fixed_q64","value_q64");out.set("kind",text(raw.get("kind"),field+".kind",false,true));
        String kind=string(out.get("kind"));require(eq(out.get("slot_offset"),slot)&&Set.of("unconsumed","missing","dynamic_tree_requires_current_result","known_zero","literal").contains(kind),field,"named source slot/kind differs");
        Boolean tree=booleanValue(out.get("tree_present"));BigInteger flag=integer(out.get("fixed_flag_u8"));
        require(Boolean.FALSE.equals(tree)||allNull(out,"fixed_flag_u8","raw_fixed_q64"),field,"tree takes precedence over fixed flag/value");require(flag!=null&&flag.signum()!=0||nil(out.get("raw_fixed_q64")),field,"raw68 was not demanded");
        BigInteger value=!Boolean.FALSE.equals(tree)||flag==null?null:flag.signum()==0?BigInteger.ZERO:integer(out.get("raw_fixed_q64"));same(out.get("value_q64"),value,field,"literal named value differs from actual tree/flag/raw68");
        if(Boolean.TRUE.equals(tree))require(kind.equals("dynamic_tree_requires_current_result")&&!nil(out.get("entry_identity"))&&!nil(out.get("tree_identity")),field,"dynamic source provenance differs");
        else if(value!=null)require(kind.equals(flag.signum()==0?"known_zero":"literal"),field,"literal source kind differs");
        else require(kind.equals("missing")||kind.equals("unconsumed"),field,"incomplete source claimed a value kind");
        if(kind.equals("unconsumed"))require(allNull(out,"entry_identity","tree_present","tree_identity","fixed_flag_u8","raw_fixed_q64","value_q64"),field,"unconsumed source contains operands");
        ready(out,value!=null&&!nil(out.get("entry_identity")),field);return out;
    }
    private static ObjectNode refresh(JsonNode raw,String field,Boolean gate) {
        ObjectNode out=start(raw,field,"source","minimum_q64","maximum_q64","clamped_q64","threshold_count","threshold_array_present","thresholds_consumed_q64","fresh_rank_raw");
        ObjectNode source=named(raw.get("source"),field+".source",0x168);out.set("source",source);nums(raw,out,field,64,false,"minimum_q64","maximum_q64","clamped_q64");nums(raw,out,field,32,false,"threshold_count","fresh_rank_raw");bools(raw,out,field,"threshold_array_present");
        JsonNode thresholds=numbers(raw.get("thresholds_consumed_q64"),field+".thresholds_consumed_q64",64,false,true,false);out.set("thresholds_consumed_q64",thresholds);
        BigInteger value=integer(source.get("value_q64")),minimum=integer(out.get("minimum_q64")),maximum=integer(out.get("maximum_q64")),count=integer(out.get("threshold_count")),clamp=null,rank=null;
        if(value!=null&&minimum!=null) {
            if(value.compareTo(minimum)<0)clamp=minimum;else if(maximum!=null)clamp=value.min(maximum);
            if(clamp!=null&&count!=null) {
                if(count.signum()<=0)rank=count;
                else if(thresholds.isArray()){for(int i=0;i<thresholds.size();i++)if(clamp.compareTo(integer(thresholds.get(i)))<=0){rank=BigInteger.valueOf(i);break;}if(rank==null&&count.equals(BigInteger.valueOf(thresholds.size())))rank=count;}
            }
        }
        same(out.get("clamped_q64"),clamp,field,"fresh clamp differs from literal source");same(out.get("fresh_rank_raw"),rank,field,"fresh rank differs from consumed threshold prefix");
        if(count!=null&&thresholds.isArray()) {
            if(count.signum()<=0)require(thresholds.isEmpty()&&nil(out.get("threshold_array_present")),field,"nonpositive count contains undemanded thresholds");
            else {require(BigInteger.valueOf(thresholds.size()).compareTo(count)<=0,field,"threshold prefix exceeds count");if(clamp!=null)for(int i=0;i<thresholds.size();i++)if(clamp.compareTo(integer(thresholds.get(i)))<=0){require(i==thresholds.size()-1,field,"threshold reads continue after first signed rank");break;}}
        }
        boolean complete;
        if(Boolean.FALSE.equals(gate)){require(allNull(out,"minimum_q64","maximum_q64","clamped_q64","threshold_count","threshold_array_present","thresholds_consumed_q64","fresh_rank_raw")&&is(source.get("kind"),"unconsumed"),field,"skipped refresh contains operands");complete=true;}
        else complete=Boolean.TRUE.equals(gate)&&source.get("ready").booleanValue()&&clamp!=null&&rank!=null&&count!=null&&(count.signum()<=0||Boolean.TRUE.equals(booleanValue(out.get("threshold_array_present"))))&&thresholds.isArray()&&nil(out.get("reason"));
        same(out.get("ready"),complete,field,"refresh availability differs");return out;
    }
    private static JsonNode prefixRow(JsonNode raw,String field) {
        ObjectNode in=shape(raw,field,"native_index","definition_identity","magic_raw","admitted","property_identity","property_block","reason"),out=object();index(in,out,field,false);nums(in,out,field,32,true,"magic_raw");texts(in,out,field,"definition_identity","property_identity","reason");bools(in,out,field,"admitted");out.set("property_block",properties(in.get("property_block"),field+".property_block"));
        Boolean admitted=nil(out.get("magic_raw"))?null:eq(out.get("magic_raw"),0x4744624fL);same(out.get("admitted"),admitted,field,"prefix Definition magic admission differs");require(Boolean.TRUE.equals(admitted)||allNull(out,"property_identity","property_block"),field,"unadmitted Definition contains PC");return out;
    }
    private static ObjectNode prefix(JsonNode raw,String field,BigInteger selector,Boolean gate) {
        ObjectNode out=start(raw,field,"selector_raw","native_prefix_count","header_count","array_present","rows");nums(raw,out,field,32,false,"selector_raw","native_prefix_count","header_count");bools(raw,out,field,"array_present");JsonNode rows=array(raw.get("rows"),field+".rows",true,BattlePersonGatedCodec::prefixRow);order(rows,field);out.set("rows",rows);
        BigInteger selected=Boolean.TRUE.equals(gate)?selector:null,count=selected==null?null:wrap(selected.add(BigInteger.ONE),32),header=integer(out.get("header_count"));same(out.get("selector_raw"),selected,field,"actual selector differs");same(out.get("native_prefix_count"),count,field,"wrapped native prefix count differs");boolean complete;
        if(Boolean.FALSE.equals(gate)){require(header==null&&nil(out.get("array_present"))&&rows.isArray()&&rows.isEmpty(),field,"skipped prefix contains operands");complete=true;}
        else if(!Boolean.TRUE.equals(gate)||count==null)complete=false;
        else if(count.signum()<=0){require(header==null&&nil(out.get("array_present"))&&rows.isArray()&&rows.isEmpty(),field,"nonpositive prefix demanded header/rows");complete=nil(out.get("reason"));}
        else if(header==null)complete=false;
        else if(count.compareTo(header)>0){require(rows.isArray()&&rows.isEmpty()&&nil(out.get("array_present")),field,"rejected prefix contains rows");complete=nil(out.get("reason"));}
        else {
            if(rows.isArray())require(BigInteger.valueOf(rows.size()).compareTo(count)<=0,field,"rows exceed admitted prefix");complete=Boolean.TRUE.equals(booleanValue(out.get("array_present")))&&rows.isArray()&&count.equals(BigInteger.valueOf(rows.size()))&&nil(out.get("reason"));
            for(JsonNode row:rows)complete&=!nil(row.get("definition_identity"))&&!nil(row.get("admitted"))&&nil(row.get("reason"))&&(!row.get("admitted").booleanValue()||(!nil(row.get("property_identity"))&&propertiesReady(row.get("property_block"))&&nil(row.get("property_block").get("reason"))));
        }
        same(out.get("ready"),complete,field,"independent prefix readiness differs");return out;
    }
    private static ObjectNode delta(JsonNode raw,String field,ObjectNode leaf,BigInteger selected) {
        ObjectNode out=start(raw,field,"delta_raw","absolute_delta_raw","header_selection","weight_source","prefix");nums(raw,out,field,32,false,"delta_raw","absolute_delta_raw");texts(raw,out,field,"header_selection");ObjectNode weight=named(raw.get("weight_source"),field+".weight_source",0x170);out.set("weight_source",weight);
        Boolean gate=booleanValue(leaf.get("temporary_admitted"));BigInteger rank=integer(leaf.get("refresh_168").get("fresh_rank_raw")),delta=null,absolute=null;
        if(Boolean.TRUE.equals(gate)&&selected!=null&&rank!=null){delta=wrap(selected.subtract(rank),32);if(delta.signum()!=0)absolute=wrap(delta.abs(),32);}
        same(out.get("delta_raw"),delta,field,"delta must consume fresh rank, not cached FC");same(out.get("absolute_delta_raw"),absolute,field,"wrapped absolute delta differs");String header=delta==null?null:delta.signum()==0?"zero_delta":delta.signum()>0?"provider_1420":"provider_14a8";same(out.get("header_selection"),header,field,"delta header differs");
        Boolean prefixGate=Boolean.FALSE.equals(gate)||BigInteger.ZERO.equals(delta)?false:delta!=null?true:null;ObjectNode prefix=prefix(raw.get("prefix"),field+".prefix",absolute,prefixGate);out.set("prefix",prefix);
        boolean needsWeight=false;if(prefix.get("ready").booleanValue())for(JsonNode row:prefix.get("rows"))if(Boolean.TRUE.equals(booleanValue(row.get("admitted")))&&positive(row.get("property_block").get("keys_count")))needsWeight=true;
        ready(out,Boolean.FALSE.equals(gate)||(Boolean.TRUE.equals(gate)&&leaf.get("refresh_168").get("ready").booleanValue()&&delta!=null&&prefix.get("ready").booleanValue()&&(!needsWeight||weight.get("ready").booleanValue())),field);return out;
    }
    static ObjectNode resolution(JsonNode raw,String field,int ordinal,boolean helper) {
        ObjectNode in=shape(raw,field,"native_index","requested_full_id_raw","registry_present","capacity_u32","indexed_pointer_present","indexed_full_id_raw","selection","object_identity","magic_raw","full_id_raw","admitted","reason"),out=object();index(in,out,field,false);nums(in,out,field,32,false,"requested_full_id_raw","indexed_full_id_raw","full_id_raw");nums(in,out,field,32,true,"capacity_u32","magic_raw");bools(in,out,field,"registry_present","indexed_pointer_present","admitted");texts(in,out,field,"selection","object_identity","reason");
        String selection=string(out.get("selection"));require(eq(out.get("native_index"),ordinal)&&(selection==null||Set.of("registry_absent","out_of_capacity","indexed_full_id","native_fallback").contains(selection)),field,"resolver order/selection differs");String expected=null;Boolean store=booleanValue(out.get("registry_present"));BigInteger key=integer(out.get("requested_full_id_raw")),capacity=integer(out.get("capacity_u32"));
        if(Boolean.FALSE.equals(store))expected=helper?"registry_absent":"native_fallback";
        else if(Boolean.TRUE.equals(store)&&key!=null&&capacity!=null) {
            if(key.and(BigInteger.valueOf(0xffffff)).compareTo(capacity)>=0)expected=helper?"out_of_capacity":"native_fallback";
            else if(Boolean.FALSE.equals(booleanValue(out.get("indexed_pointer_present"))))expected="native_fallback";
            else if(Boolean.TRUE.equals(booleanValue(out.get("indexed_pointer_present")))&&!nil(out.get("indexed_full_id_raw")))expected=key.equals(integer(out.get("indexed_full_id_raw")))?"indexed_full_id":"native_fallback";
        }
        require(selection==null||selection.equals(expected),field,"resolver differs from actual full-generation lookup");Boolean admitted="registry_absent".equals(selection)||"out_of_capacity".equals(selection)?false:nil(out.get("magic_raw"))?null:!eq(out.get("magic_raw"),0x43686172L)?false:nil(out.get("full_id_raw"))?null:!eq(out.get("full_id_raw"),-1);same(out.get("admitted"),admitted,field,"Character magic/full-ID admission differs");
        if("registry_absent".equals(selection)||"out_of_capacity".equals(selection))require(allNull(out,"object_identity","magic_raw","full_id_raw"),field,"helper miss contains undemanded fallback/gates");return out;
    }
    private static ObjectNode related(JsonNode raw,String field,Boolean currentLand) {
        ObjectNode in=shape(raw,field,"carrier_present","attempts","self_full_id_raw","helper_return_full_id_raw","caller","land_present","selected_present","reason"),out=object();bools(in,out,field,"carrier_present","land_present","selected_present");nums(in,out,field,32,false,"self_full_id_raw","helper_return_full_id_raw");texts(in,out,field,"reason");JsonNode original=in.get("attempts");require(original.isArray()&&original.size()<=2,field,"attempts must be CC then C8 prefix");ArrayNode attempts=list();for(int i=0;i<original.size();i++)attempts.add(resolution(original.get(i),field+".attempts["+i+"]",i,true));out.set("attempts",attempts);
        BigInteger returned=null;Boolean carrier=booleanValue(out.get("carrier_present"));
        if(Boolean.FALSE.equals(carrier)){require(attempts.isEmpty()&&nil(out.get("self_full_id_raw")),field,"absent carrier contains candidate/self demand");returned=BigInteger.ONE.negate();}
        else if(Boolean.TRUE.equals(carrier)) {boolean exhausted=true;for(int i=0;i<attempts.size();i++){JsonNode row=attempts.get(i);if(Boolean.TRUE.equals(booleanValue(row.get("admitted")))){require(i==attempts.size()-1,field,"continued after admitted candidate");returned=integer(row.get("requested_full_id_raw"));exhausted=false;break;}if(nil(row.get("admitted"))||!nil(row.get("reason"))){exhausted=false;break;}}if(exhausted&&attempts.size()==2)returned=Boolean.TRUE.equals(currentLand)?integer(out.get("self_full_id_raw")):Boolean.FALSE.equals(currentLand)?BigInteger.ONE.negate():null;}
        same(out.get("helper_return_full_id_raw"),returned,field,"CC/C8/self helper return differs");ObjectNode caller=resolution(in.get("caller"),field+".caller",0,false);out.set("caller",caller);same(caller.get("requested_full_id_raw"),returned,field,"caller did not resolve actual helper full ID");
        require(Boolean.TRUE.equals(booleanValue(caller.get("admitted")))||allNull(out,"land_present","selected_present"),field,"inadmissible related Character contains selected operands");require(!Boolean.FALSE.equals(booleanValue(out.get("land_present")))||nil(out.get("selected_present"))||Boolean.FALSE.equals(booleanValue(out.get("selected_present"))),field,"absent related land has selected458");return out;
    }
    private static ObjectNode listFamily(JsonNode raw,String field,ObjectNode leaf) {
        ObjectNode out=start(raw,field,"selection","related","count_raw","array_present","rows");texts(raw,out,field,"selection");nums(raw,out,field,32,false,"count_raw");bools(raw,out,field,"array_present");ObjectNode related=related(raw.get("related"),field+".related",booleanValue(leaf.get("current_land_present")));out.set("related",related);
        JsonNode rows=array(raw.get("rows"),field+".rows",true,(item,name)->{ObjectNode in=shape(item,name,"native_index","property_identity","property_block","reason"),row=object();index(in,row,name,false);texts(in,row,name,"property_identity","reason");row.set("property_block",properties(in.get("property_block"),name+".property_block"));return row;});order(rows,field);out.set("rows",rows);
        Boolean bit=booleanValue(leaf.get("global_bit20")),current=booleanValue(leaf.get("current_selected_present"));String selection=null;
        if(Boolean.FALSE.equals(bit))selection="skipped_bit20";else if(Boolean.TRUE.equals(bit)&&Boolean.TRUE.equals(current))selection="current_A20";
        else if(Boolean.TRUE.equals(bit)&&Boolean.FALSE.equals(current)) {
            Boolean admitted=booleanValue(related.get("caller").get("admitted")),land=booleanValue(related.get("land_present")),selected=booleanValue(related.get("selected_present"));
            if(Boolean.FALSE.equals(admitted)||Boolean.FALSE.equals(land)||Boolean.FALSE.equals(selected))selection="related_skip";
            else if(Boolean.TRUE.equals(admitted)&&Boolean.TRUE.equals(land)&&Boolean.TRUE.equals(selected))selection="related_BE0";
        }
        same(out.get("selection"),selection,field,"list source differs from bit/current/related gates");BigInteger count=integer(out.get("count_raw"));boolean complete;
        if("skipped_bit20".equals(selection)||"related_skip".equals(selection)){require(count==null&&nil(out.get("array_present"))&&rows.isArray()&&rows.isEmpty(),field,"skipped list contains rows");complete=true;}
        else if(selection==null||count==null)complete=false;
        else if(count.signum()==0||selection.equals("related_BE0")&&count.signum()<0){require(rows.isArray()&&rows.isEmpty(),field,"empty list contains rows");complete=true;}
        else if(count.signum()<0)complete=false;
        else {if(rows.isArray())require(BigInteger.valueOf(rows.size()).compareTo(count)<=0,field,"list rows exceed actual count");complete=Boolean.TRUE.equals(booleanValue(out.get("array_present")))&&rows.isArray()&&count.equals(BigInteger.valueOf(rows.size()));for(JsonNode row:rows)complete&=!nil(row.get("property_identity"))&&propertiesReady(row.get("property_block"))&&nil(row.get("property_block").get("reason"))&&nil(row.get("reason"));}
        ready(out,complete,field);return out;
    }
    static JsonNode normalize(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;ObjectNode out=start(raw,field,"character_id","global_flag_u8","global_bit20","current_land_present","current_selected_present","temporary_admitted","selected_ec_raw","selector_global_raw","selected_e8_raw","selected_f8_raw","refresh_168","prefix_1398","delta_prefix_1420_14a8","list");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));nums(raw,out,field,32,false,"selected_ec_raw","selector_global_raw","selected_e8_raw","selected_f8_raw");nums(raw,out,field,8,true,"global_flag_u8");bools(raw,out,field,"global_bit20","current_land_present","current_selected_present","temporary_admitted");
        Boolean bit=nil(out.get("global_flag_u8"))?null:integer(out.get("global_flag_u8")).testBit(5),land=booleanValue(out.get("current_land_present")),selected=booleanValue(out.get("current_selected_present"));same(out.get("global_bit20"),bit,field,"global bit20 differs from actual flag byte");
        if(Boolean.FALSE.equals(bit))require(land==null&&selected==null,field,"disabled bit demanded current selection");require(!Boolean.FALSE.equals(land)||selected==null||!selected,field,"absent current land has selected458");
        Boolean gate=Boolean.FALSE.equals(bit)||Boolean.FALSE.equals(land)||Boolean.FALSE.equals(selected)?false:Boolean.TRUE.equals(bit)&&Boolean.TRUE.equals(land)&&Boolean.TRUE.equals(selected)?true:null;same(out.get("temporary_admitted"),gate,field,"temporary admission differs");
        BigInteger ec=integer(out.get("selected_ec_raw")),reference=integer(out.get("selector_global_raw")),operand=ec==null||reference==null?null:integer(out.get(ec.equals(reference)?"selected_f8_raw":"selected_e8_raw"));
        if(!Boolean.TRUE.equals(gate))require(allNull(out,"selected_ec_raw","selector_global_raw","selected_e8_raw","selected_f8_raw"),field,"skipped temporary gate contains selected operands");
        if(ec!=null&&reference!=null)require(nil(out.get(ec.equals(reference)?"selected_e8_raw":"selected_f8_raw")),field,"undemanded alternate selection operand present");
        ObjectNode refresh=refresh(raw.get("refresh_168"),field+".refresh_168",gate);out.set("refresh_168",refresh);ObjectNode prefix=prefix(raw.get("prefix_1398"),field+".prefix_1398",operand,gate);out.set("prefix_1398",prefix);ObjectNode delta=delta(raw.get("delta_prefix_1420_14a8"),field+".delta_prefix_1420_14a8",out,operand);out.set("delta_prefix_1420_14a8",delta);ObjectNode list=listFamily(raw.get("list"),field+".list",out);out.set("list",list);
        same(out.get("ready"),prefix.get("ready").booleanValue()&&delta.get("ready").booleanValue()&&list.get("ready").booleanValue(),field,"whole stage differs from three independent families");return out;
    }
}
