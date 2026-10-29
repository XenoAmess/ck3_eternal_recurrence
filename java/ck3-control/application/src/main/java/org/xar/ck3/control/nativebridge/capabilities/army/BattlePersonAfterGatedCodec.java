package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.util.Set;

/** Full source-ordered composition/calendar/CourtPosition inputs following the gated temporary stage. */
final class BattlePersonAfterGatedCodec {
    private BattlePersonAfterGatedCodec() { }
    private static final String[] FAMILIES={"composition_326a8e0","current_1b8_court_positions","current_1c0_court_positions","related_court_positions"};
    private static ObjectNode date(JsonNode raw,String field) {
        ObjectNode in=shape(raw,field,"raw_i32","day_cache_i8","month_cache_i8","year_cache_i16"),out=object();nums(in,out,field,32,false,"raw_i32");nums(in,out,field,8,false,"day_cache_i8","month_cache_i8");nums(in,out,field,16,false,"year_cache_i16");return out;
    }
    private record Calendar(int day,int month,int year) { }
    private static Calendar decodeDate(JsonNode row) {
        if(nil(row.get("day_cache_i8"))||nil(row.get("month_cache_i8"))||nil(row.get("year_cache_i16")))return null;
        int day=integer(row.get("day_cache_i8")).intValueExact(),month=integer(row.get("month_cache_i8")).intValueExact(),year=integer(row.get("year_cache_i16")).intValueExact();
        if(day<0||month<0||year<0) {
            if(nil(row.get("raw_i32")))return null;int hours=wrap(integer(row.get("raw_i32")).subtract(BigInteger.valueOf(43800000)),32).intValueExact();
            int dayIndex=Math.floorMod(hours/24,365),actualMonth=0;int[] lengths={31,28,31,30,31,30,31,31,30,31,30,31};
            while(dayIndex>=lengths[actualMonth])dayIndex-=lengths[actualMonth++];
            if(day<0)day=dayIndex;if(month<0)month=actualMonth;if(year<0)year=hours/8760;
        }
        return new Calendar(day,month,year);
    }
    private static BigInteger months(JsonNode current,JsonNode chosen) {
        Calendar a=decodeDate(current),b=decodeDate(chosen);if(a==null||b==null)return null;
        BigInteger years=wrap(BigInteger.valueOf((long)a.year()-b.year()),32);
        return wrap(wrap(years.multiply(BigInteger.valueOf(12)).add(BigInteger.valueOf((long)a.month()-b.month())),32).subtract(a.day()<b.day()?BigInteger.ONE:BigInteger.ZERO),32);
    }
    private static ObjectNode selectors(JsonNode raw,String field) {
        ObjectNode in=shape(raw,field,"selector_a_selection","selector_a_identity","selector_b_selection","selector_b_identity","selector_a_key_raw","selector_b_key_raw","selector_a_membership_count","selector_b_primary_count","selector_b_nested_count","selector_a_keys_i32","selector_b_primary_keys_i32","selector_b_nested_keys","reason"),out=object();
        texts(in,out,field,"selector_a_selection","selector_a_identity","selector_b_selection","selector_b_identity","reason");nums(in,out,field,32,false,"selector_a_key_raw","selector_b_key_raw","selector_a_membership_count","selector_b_primary_count","selector_b_nested_count");
        for(String key:new String[]{"selector_a_keys_i32","selector_b_primary_keys_i32"})out.set(key,numbers(in.get(key),field+"."+key,32,false,true,false));
        JsonNode original=in.get("selector_b_nested_keys");require(original.isArray(),field,"nested selector keysets must be ordered array");ArrayNode rows=list();for(int i=0;i<original.size();i++)rows.add(BattlePersonContextEarlyCodec.traitKeyset(original.get(i),field+".selector_b_nested_keys["+i+"]",i));out.set("selector_b_nested_keys",rows);return out;
    }
    private static ObjectNode related(JsonNode raw,String field,Boolean currentLand,boolean checkMagic) {
        ObjectNode in=shape(raw,field,"carrier_present","attempts","self_full_id_raw","helper_return_full_id_raw","caller_selection","caller_identity","caller_requested_full_id_raw","caller_full_id_raw","caller_magic_raw","caller_admitted","land_present","selected_present","reason"),out=object();
        bools(in,out,field,"carrier_present","caller_admitted","land_present","selected_present");texts(in,out,field,"caller_selection","caller_identity","reason");nums(in,out,field,32,false,"self_full_id_raw","helper_return_full_id_raw","caller_requested_full_id_raw","caller_full_id_raw");nums(in,out,field,32,true,"caller_magic_raw");
        JsonNode original=in.get("attempts");require(original.isArray()&&original.size()<=2,field,"related attempts must be CC then C8 prefix");ArrayNode attempts=list();for(int i=0;i<original.size();i++)attempts.add(BattlePersonGatedCodec.resolution(original.get(i),field+".attempts["+i+"]",i,true));out.set("attempts",attempts);
        BigInteger returned=null;Boolean carrier=booleanValue(out.get("carrier_present"));
        if(Boolean.FALSE.equals(carrier)){require(attempts.isEmpty()&&nil(out.get("self_full_id_raw")),field,"absent carrier contains undemanded candidates");returned=BigInteger.ONE.negate();}
        else if(Boolean.TRUE.equals(carrier)){boolean exhausted=true;for(int i=0;i<attempts.size();i++){JsonNode row=attempts.get(i);if(Boolean.TRUE.equals(booleanValue(row.get("admitted")))){require(i==attempts.size()-1,field,"continued after admitted candidate");returned=integer(row.get("requested_full_id_raw"));exhausted=false;break;}if(nil(row.get("admitted"))||!nil(row.get("reason"))){exhausted=false;break;}}if(exhausted&&attempts.size()==2)returned=Boolean.TRUE.equals(currentLand)?integer(out.get("self_full_id_raw")):Boolean.FALSE.equals(currentLand)?BigInteger.ONE.negate():null;}
        same(out.get("helper_return_full_id_raw"),returned,field,"related helper full ID differs");String selection=string(out.get("caller_selection"));require(selection==null||selection.equals("indexed_full_id")||selection.equals("native_fallback"),field,"unsupported caller selection");
        require(nil(out.get("caller_requested_full_id_raw"))||java.util.Objects.equals(integer(out.get("caller_requested_full_id_raw")),returned),field,"caller requested a different helper full ID");
        if("indexed_full_id".equals(selection))require(returned!=null&&returned.equals(integer(out.get("caller_full_id_raw"))),field,"indexed caller generation differs");
        if(checkMagic) {Boolean admitted=nil(out.get("caller_magic_raw"))?null:!eq(out.get("caller_magic_raw"),0x43686172L)?false:nil(out.get("caller_full_id_raw"))?null:!eq(out.get("caller_full_id_raw"),-1);same(out.get("caller_admitted"),admitted,field,"caller Character gate differs");}
        else require(nil(out.get("caller_magic_raw")),field,"composition caller has no Character magic gate");
        require(!Boolean.FALSE.equals(booleanValue(out.get("land_present")))||nil(out.get("selected_present"))||Boolean.FALSE.equals(booleanValue(out.get("selected_present"))),field,"absent land has selected458");return out;
    }
    private static ObjectNode rowset(JsonNode raw,String field,BigInteger selector,Boolean gate) {
        ObjectNode out=start(raw,field,"count_raw","array_present","rows");nums(raw,out,field,32,false,"count_raw");bools(raw,out,field,"array_present");JsonNode original=raw.get("rows"),rows=NullNode.instance;
        if(!nil(original)) {
            require(original.isArray(),field,"ordered rowset required");ArrayNode values=list();
            for(int i=0;i<original.size();i++){String name=field+".rows["+i+"]";ObjectNode in=shape(original.get(i),name,"native_index","threshold_raw","admitted","pc","reason"),row=object();index(in,row,name,false);nums(in,row,name,32,false,"threshold_raw");bools(in,row,name,"admitted");texts(in,row,name,"reason");row.set("pc",pc(in.get("pc"),name+".pc"));Boolean admitted=selector!=null&&!nil(row.get("threshold_raw"))?selector.compareTo(integer(row.get("threshold_raw")))>=0:null;require(eq(row.get("native_index"),i),name,"stored row order differs");same(row.get("admitted"),admitted,name,"threshold admission differs");require(Boolean.TRUE.equals(admitted)||absentPc(row.get("pc")),name,"rejected threshold contains undemanded PC");values.add(row);}rows=values;
        }
        out.set("rows",rows);BigInteger count=integer(out.get("count_raw"));boolean complete;
        if(Boolean.FALSE.equals(gate)){require(count==null&&nil(out.get("array_present"))&&rows.isArray()&&rows.isEmpty(),field,"skipped rowset contains operands");complete=true;}
        else if(!Boolean.TRUE.equals(gate)||count==null||count.signum()<0)complete=false;
        else if(count.signum()==0){require(rows.isArray()&&rows.isEmpty(),field,"zero rowset contains rows");complete=true;}
        else {complete=selector!=null&&Boolean.TRUE.equals(booleanValue(out.get("array_present")))&&rows.isArray()&&count.equals(BigInteger.valueOf(rows.size()));for(JsonNode row:rows)complete&=!nil(row.get("admitted"))&&nil(row.get("reason"))&&(!row.get("admitted").booleanValue()||pcReady(row.get("pc")));}
        ready(out,complete,field);return out;
    }
    private static ObjectNode composition(JsonNode raw,String field,Boolean currentLand) {
        ObjectNode out=start(raw,field,"global_flag_u8","global_bit20","current_land_present","current_selected_present","receiver_selection","admitted","related","owner_mode","definition_identity","level_raw","handle_date","fifth_date","current_date","chosen_date_selection","completed_months_raw","level_rows","month_rows");
        nums(raw,out,field,8,true,"global_flag_u8");nums(raw,out,field,32,false,"level_raw","completed_months_raw");bools(raw,out,field,"global_bit20","current_land_present","current_selected_present","admitted","owner_mode");texts(raw,out,field,"receiver_selection","definition_identity","chosen_date_selection");
        ObjectNode related=related(raw.get("related"),field+".related",currentLand,false);out.set("related",related);for(String key:new String[]{"handle_date","fifth_date","current_date"})out.set(key,date(raw.get(key),field+"."+key));
        Boolean bit=nil(out.get("global_flag_u8"))?null:integer(out.get("global_flag_u8")).testBit(5),gate=null,owner=null;String selection=null;same(out.get("global_bit20"),bit,field,"actual bit20 differs");
        if(Boolean.FALSE.equals(bit)){gate=false;selection="skipped";}
        else if(Boolean.TRUE.equals(bit)&&Boolean.TRUE.equals(booleanValue(out.get("current_land_present")))&&Boolean.TRUE.equals(booleanValue(out.get("current_selected_present")))){gate=true;selection="current_458_178";owner=true;}
        else if(Boolean.TRUE.equals(bit)&&(Boolean.FALSE.equals(booleanValue(out.get("current_land_present")))||Boolean.FALSE.equals(booleanValue(out.get("current_selected_present"))))) {
            if(eq(related.get("helper_return_full_id_raw"),-1)||Boolean.FALSE.equals(booleanValue(related.get("land_present")))||Boolean.FALSE.equals(booleanValue(related.get("selected_present")))){gate=false;selection="skipped";}
            else if(!nil(related.get("caller_selection"))&&Boolean.TRUE.equals(booleanValue(related.get("land_present")))&&Boolean.TRUE.equals(booleanValue(related.get("selected_present")))){gate=true;selection="related_458_178";owner=false;}
        }
        same(out.get("admitted"),gate,field,"composition receiver admission differs");same(out.get("receiver_selection"),selection,field,"composition receiver selection differs");same(out.get("owner_mode"),owner,field,"composition owner mode differs");
        BigInteger months=null;String choice=null;JsonNode monthCount=raw.get("month_rows").get("count_raw");
        if(Boolean.TRUE.equals(gate)&&monthCount!=null&&monthCount.isIntegralNumber()&&monthCount.bigIntegerValue().signum()>0) {
            BigInteger handle=integer(out.get("handle_date").get("raw_i32")),fifth=integer(out.get("fifth_date").get("raw_i32"));if(handle!=null&&fifth!=null){choice=fifth.compareTo(handle)>0?"fifth":"handle";months=months(out.get("current_date"),out.get(choice+"_date"));}
        }
        same(out.get("chosen_date_selection"),choice,field,"signed MAX date choice/tie differs");same(out.get("completed_months_raw"),months,field,"actual cached365 calendar difference differs");
        ObjectNode levelRows=rowset(raw.get("level_rows"),field+".level_rows",integer(out.get("level_raw")),gate),monthRows=rowset(raw.get("month_rows"),field+".month_rows",months,gate);out.set("level_rows",levelRows);out.set("month_rows",monthRows);
        ready(out,Boolean.FALSE.equals(gate)||(Boolean.TRUE.equals(gate)&&!nil(out.get("definition_identity"))&&levelRows.get("ready").booleanValue()&&monthRows.get("ready").booleanValue()),field);return out;
    }
    private static BigInteger ruleValue(JsonNode rule) {
        BigInteger mode=integer(rule.get("mode_raw"));if(mode==null)return null;if(mode.signum()==0)return integer(rule.get("raw_98_q64"));
        if(!Boolean.FALSE.equals(booleanValue(rule.get("tree_present"))))return null;
        if(Boolean.TRUE.equals(booleanValue(rule.get("named_present"))))return integer(rule.get("named").get("value_q64"));
        return Boolean.FALSE.equals(booleanValue(rule.get("named_present")))&&zero(rule.get("target_count_raw"))?integer(rule.get("raw_98_q64")):null;
    }
    private static ObjectNode rule(JsonNode raw,String field) {
        ObjectNode out=start(raw,field,"mode_raw","tree_present","tree_identity","named_present","named","target_count_raw","raw_98_q64","value_q64","selection");nums(raw,out,field,32,false,"mode_raw","target_count_raw");nums(raw,out,field,64,false,"raw_98_q64","value_q64");bools(raw,out,field,"tree_present","named_present");texts(raw,out,field,"tree_identity","selection");ObjectNode named=BattlePersonGatedCodec.named(raw.get("named"),field+".named",0);out.set("named",named);
        BigInteger mode=integer(out.get("mode_raw"));String selection=null;
        if(BigInteger.ZERO.equals(mode)){selection="mode_zero_raw98";require(allNull(out,"tree_present","tree_identity","named_present","target_count_raw")&&is(named.get("kind"),"unconsumed"),field,"mode0 literal contains tree/named/target demand");}
        else if(mode!=null) {
            if(Boolean.TRUE.equals(booleanValue(out.get("tree_present")))){selection="dynamic_tree";require(!nil(out.get("tree_identity")),field,"dynamic tree source identity missing");}
            else if(Boolean.FALSE.equals(booleanValue(out.get("tree_present")))) {
                if(Boolean.TRUE.equals(booleanValue(out.get("named_present"))))selection="nested_named";
                else if(Boolean.FALSE.equals(booleanValue(out.get("named_present")))&&!nil(out.get("target_count_raw")))selection=zero(out.get("target_count_raw"))?"zero_targets_raw98":"dynamic_targets";
            }
        }
        same(out.get("selection"),selection,field,"Definition600 rule source selection differs");BigInteger value=ruleValue(out);same(out.get("value_q64"),value,field,"Definition600 literal result differs");ready(out,value!=null&&(!"nested_named".equals(selection)||named.get("ready").booleanValue()),field);return out;
    }
    private static ObjectNode kind(JsonNode raw,String field) {
        ObjectNode out=start(raw,field,"position_120_raw","position_124_raw","owner_selection","owner_identity","owner_full_id_raw","played_count_raw","played_full_ids","owner_played","raw_a0_u8","threshold_count_raw","thresholds_i32","rule","kind_raw");
        nums(raw,out,field,32,false,"position_120_raw","position_124_raw","owner_full_id_raw","played_count_raw","threshold_count_raw","kind_raw");nums(raw,out,field,8,true,"raw_a0_u8");texts(raw,out,field,"owner_selection","owner_identity");bools(raw,out,field,"owner_played");out.set("played_full_ids",numbers(raw.get("played_full_ids"),field+".played_full_ids",32,false,true,false));out.set("thresholds_i32",numbers(raw.get("thresholds_i32"),field+".thresholds_i32",32,false,true,false));ObjectNode rule=rule(raw.get("rule"),field+".rule");out.set("rule",rule);
        BigInteger count=integer(out.get("played_count_raw")),owner=integer(out.get("owner_full_id_raw"));JsonNode ids=out.get("played_full_ids");Boolean played=null;
        if(owner!=null&&count!=null&&count.signum()>=0&&ids.isArray()&&count.equals(BigInteger.valueOf(ids.size()))){played=false;for(JsonNode id:ids)if(owner.equals(integer(id)))played=true;}
        same(out.get("owner_played"),played,field,"played membership differs from complete DWORD IDs");String selection=string(out.get("owner_selection"));require(selection==null||selection.equals("indexed_full_id")||selection.equals("native_fallback"),field,"unsupported owner selection");
        if("indexed_full_id".equals(selection))require(out.get("position_120_raw").equals(out.get("owner_full_id_raw")),field,"owner indexed full generation differs");
        if(Boolean.TRUE.equals(played))require(nil(out.get("raw_a0_u8")),field,"played branch contains undemanded raw A0");BigInteger result=null,thresholdCount=integer(out.get("threshold_count_raw"));JsonNode thresholds=out.get("thresholds_i32");
        if(played!=null) {
            boolean evaluate=played;
            if(!played){BigInteger value=integer(out.get("raw_a0_u8"));if(value!=null){if(!value.equals(BigInteger.valueOf(5)))result=value;else evaluate=true;}}
            if(evaluate&&thresholdCount!=null) {
                if(thresholdCount.compareTo(BigInteger.valueOf(4))<0)result=BigInteger.valueOf(4);
                else {BigInteger value=ruleValue(rule);if(value!=null&&thresholds.isArray()&&thresholds.size()==4){result=BigInteger.valueOf(4);for(int i=0;i<4;i++)if(value.compareTo(integer(thresholds.get(i)).multiply(BigInteger.valueOf(100000)))<0){result=BigInteger.valueOf(i);break;}}}
            }
        }
        same(out.get("kind_raw"),result,field,"raw/fixed quantized kind differs");boolean evaluate=Boolean.TRUE.equals(played)||Boolean.FALSE.equals(played)&&eq(out.get("raw_a0_u8"),5);
        if(!evaluate)require(allNull(out,"threshold_count_raw","thresholds_i32"),field,"ordinary kind contains undemanded quantizer");
        if(thresholdCount!=null&&thresholdCount.compareTo(BigInteger.valueOf(4))<0)require(nil(thresholds)&&nil(rule.get("mode_raw")),field,"short threshold count contains undemanded rule/thresholds");
        ready(out,selection!=null&&!nil(out.get("owner_identity"))&&owner!=null&&result!=null,field);return out;
    }
    private record Pair(ArrayNode rows,Boolean admitted) { }
    private static Pair pair(JsonNode raw,String field) {
        require(raw.isArray()&&raw.size()<=6,field,"at most six native count probes required");ArrayNode rows=list();Boolean admitted=null;boolean allZero=true;
        for(int i=0;i<raw.size();i++) {
            String name=field+"["+i+"]";ObjectNode in=shape(raw.get(i),name,"native_index","count_raw"),row=object();index(in,row,name,false);nums(in,row,name,32,false,"count_raw");
            require(eq(row.get("native_index"),i)&&admitted==null,name,"probe order continued after known admission");
            if(nil(row.get("count_raw"))){require(i==raw.size()-1,name,"probes continue after missing count");allZero=false;}
            else if(!zero(row.get("count_raw"))){admitted=true;allZero=false;}
            rows.add(row);
        }
        if(rows.size()==6&&allZero)admitted=false;return new Pair(rows,admitted);
    }
    private static ObjectNode position(JsonNode raw,String field,int ordinal,int family,ObjectNode selectors) {
        ObjectNode in=shape(raw,field,"native_index","requested_full_id_raw","position_selection","position_identity","position_full_id_raw","definition_identity","other_definition_identity","other_magic_raw","other_admitted","base_pc","tier_pc","composite_group","kind","other_base_pc","other_tier_pc","other_kind","definition_pair_probes","definition_pair_admitted","other_pair_probes","other_pair_admitted","ready","reason"),out=object();
        index(in,out,field,false);out.set("ready",bool(in.get("ready"),field+".ready",false));nums(in,out,field,32,false,"requested_full_id_raw","position_full_id_raw");nums(in,out,field,32,true,"other_magic_raw");texts(in,out,field,"position_selection","position_identity","definition_identity","other_definition_identity","reason");bools(in,out,field,"other_admitted","definition_pair_admitted","other_pair_admitted");
        String selection=string(out.get("position_selection"));require(eq(out.get("native_index"),ordinal)&&(selection==null||selection.equals("registry_full_id_8")||selection.equals("native_fallback")),field,"CourtPosition physical order/resolution differs");
        if("registry_full_id_8".equals(selection))require(!nil(out.get("requested_full_id_raw"))&&out.get("requested_full_id_raw").equals(out.get("position_full_id_raw")),field,"CourtPosition full-generation selection differs");
        Boolean other=nil(out.get("other_magic_raw"))?null:eq(out.get("other_magic_raw"),0x4744624fL);same(out.get("other_admitted"),other,field,"Other magic admission differs");
        for(String key:new String[]{"base_pc","tier_pc","other_base_pc","other_tier_pc"})out.set(key,pc(in.get(key),field+"."+key));
        out.set("kind",kind(in.get("kind"),field+".kind"));out.set("other_kind",kind(in.get("other_kind"),field+".other_kind"));
        JsonNode group=nil(in.get("composite_group"))?NullNode.instance:BattlePersonContextEarlyCodec.traitGroup(in.get("composite_group"),field+".composite_group",selectors);out.set("composite_group",group);
        require(nil(group)||is(group.get("role"),"base"),field,"B8D0 cannot contain growth group");
        Pair definition=pair(in.get("definition_pair_probes"),field+".definition_pair_probes"),otherPair=pair(in.get("other_pair_probes"),field+".other_pair_probes");out.set("definition_pair_probes",definition.rows());out.set("other_pair_probes",otherPair.rows());same(out.get("definition_pair_admitted"),definition.admitted(),field,"definition pair admission differs from six source counts");same(out.get("other_pair_admitted"),otherPair.admitted(),field,"other pair admission differs from six source counts");
        boolean complete=selection!=null&&!nil(out.get("position_identity"))&&!nil(out.get("definition_identity"));
        if(family==1)complete&=pcReady(out.get("base_pc"))&&!nil(group)&&group.get("ready").booleanValue()&&other!=null&&(!other||pcReady(out.get("other_base_pc")));
        else if(family==2)complete&=pcReady(out.get("base_pc"))&&out.get("kind").get("ready").booleanValue()&&pcReady(out.get("tier_pc"))&&!nil(group)&&group.get("ready").booleanValue()&&other!=null&&(!other||(pcReady(out.get("other_base_pc"))&&out.get("other_kind").get("ready").booleanValue()&&pcReady(out.get("other_tier_pc"))));
        else {
            require(nil(group),field,"related family has no B8D0 composite");
            complete&=definition.admitted()!=null&&other!=null&&(!Boolean.TRUE.equals(definition.admitted())||(pcReady(out.get("base_pc"))&&out.get("kind").get("ready").booleanValue()&&pcReady(out.get("tier_pc"))))&&(!Boolean.TRUE.equals(other)||(otherPair.admitted()!=null&&(!otherPair.admitted()||(pcReady(out.get("other_base_pc"))&&out.get("other_kind").get("ready").booleanValue()&&pcReady(out.get("other_tier_pc"))))));
        }
        ready(out,complete,field);return out;
    }
    private static ObjectNode courtList(JsonNode raw,String field,int family,Boolean currentLand,ObjectNode selectors) {
        ObjectNode out=start(raw,field,"owner_present","header_selection","count_raw","numeric_count","array_present","default_init_guard_raw","related","rows");
        nums(raw,out,field,32,false,"count_raw","numeric_count","default_init_guard_raw");bools(raw,out,field,"owner_present","array_present");texts(raw,out,field,"header_selection");out.set("related",related(raw.get("related"),field+".related",currentLand,true));
        JsonNode original=raw.get("rows"),rows=NullNode.instance;if(!nil(original)){require(original.isArray(),field,"ordered CourtPosition rows required");ArrayNode items=list();for(int i=0;i<original.size();i++)items.add(position(original.get(i),field+".rows["+i+"]",i,family,selectors));rows=items;}out.set("rows",rows);
        String selection=string(out.get("header_selection"));Set<String> allowed=family==1?Set.of("absent_owner","current_1b8_d0"):family==2?Set.of("absent_owner","current_1c0_3b8"):Set.of("related_1c0_3b8","inline_default_54e7220","modeled_empty_default_54e7220","related_invalid_skip");require(selection==null||allowed.contains(selection),field,"unsupported header selection for source family");
        JsonNode count=out.get("count_raw"),numeric=out.get("numeric_count"),guard=out.get("default_init_guard_raw");boolean complete;
        if(selection!=null&&Set.of("absent_owner","related_invalid_skip","modeled_empty_default_54e7220").contains(selection)) {
            require(zero(numeric)&&nil(count)&&nil(out.get("array_present"))&&rows.isArray()&&rows.isEmpty(),field,"known/modeled empty header contains physical operands");complete=true;
            if(selection.equals("modeled_empty_default_54e7220"))require(zero(guard)||eq(guard,-1),field,"modeled default needs actual uninitialized guard");
        } else {
            require(numeric.equals(count),field,"numeric count differs from actual observed header");complete=selection!=null&&!nil(count)&&integer(count).signum()>=0&&rows.isArray()&&integer(count).equals(BigInteger.valueOf(rows.size()));
            if(positive(count)){complete&=Boolean.TRUE.equals(booleanValue(out.get("array_present")));for(JsonNode row:rows)complete&=row.get("ready").booleanValue();}
            if("inline_default_54e7220".equals(selection))complete&=!nil(guard)&&!zero(guard)&&!eq(guard,-1);
        }
        ready(out,complete,field);return out;
    }
    static JsonNode normalize(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;ObjectNode out=start(raw,field,"character_id","current_land_present","selector_inputs","composition_326a8e0","current_1b8_court_positions","current_1c0_court_positions","related_court_positions");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));bools(raw,out,field,"current_land_present");ObjectNode selectors=selectors(raw.get("selector_inputs"),field+".selector_inputs");out.set("selector_inputs",selectors);
        ObjectNode composition=composition(raw.get(FAMILIES[0]),field+"."+FAMILIES[0],booleanValue(out.get("current_land_present")));out.set(FAMILIES[0],composition);boolean complete=composition.get("ready").booleanValue();
        for(int i=1;i<FAMILIES.length;i++){ObjectNode family=courtList(raw.get(FAMILIES[i]),field+"."+FAMILIES[i],i,booleanValue(out.get("current_land_present")),selectors);out.set(FAMILIES[i],family);complete&=family.get("ready").booleanValue();}
        same(out.get("ready"),complete,field,"whole stage differs from four independent source families");return out;
    }
}
