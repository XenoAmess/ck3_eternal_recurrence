package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleLeafRecord.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleLeafRecord.Kind.*;

/** Strict native trait selection, signed membership, full pointer probing and growth prefix validation. */
final class BattleTraitStageCodec {
    private BattleTraitStageCodec() { }
    private static boolean keysComplete(BigInteger count,JsonNode keys) { return count!=null&&!nil(keys)&&BigInteger.valueOf(keys.size()).equals(count.max(BigInteger.ZERO)); }
    private static boolean contains(JsonNode keys,BigInteger key) {
        int low=0,high=keys.size();while(low<high){int mid=(low+high)>>>1;if(keys.get(mid).bigIntegerValue().compareTo(key)<0)low=mid+1;else high=mid;}
        return low<keys.size()&&keys.get(low).bigIntegerValue().equals(key);
    }
    private static Boolean membership(ObjectNode stage,BigInteger key,boolean first) {
        if(first){if(!keysComplete(n(stage,"selector_a_membership_count"),stage.get("selector_a_keys_i32")))return null;return contains(stage.get("selector_a_keys_i32"),key);}
        if(!keysComplete(n(stage,"selector_b_primary_count"),stage.get("selector_b_primary_keys_i32")))return null;
        if(contains(stage.get("selector_b_primary_keys_i32"),key))return true;
        BigInteger count=n(stage,"selector_b_nested_count");JsonNode nested=stage.get("selector_b_nested_keys");if(count==null||nil(nested))return null;
        for(JsonNode keys:nested){if(!keysComplete(n(keys,"count"),keys.get("keys_i32"))||!zeroReason(keys))return null;if(contains(keys.get("keys_i32"),key))return true;}
        return BigInteger.valueOf(nested.size()).equals(count.max(BigInteger.ZERO))?false:null;
    }
    static ObjectNode keyset(JsonNode raw,String field,int index) {
        ObjectNode row=parseRecord(raw,field,f(I32,false,"native_index"),f(I32,true,"count"),f(TEXT,true,"reason"),f(RAW,false,"keys_i32"));
        row.set("keys_i32",numbers(row.get("keys_i32"),field+".keys_i32",32,false,true,false));require(eq(row,"native_index",index),field,"native keyset order differs");return row;
    }
    private static ObjectNode condition(JsonNode raw,String field,int index,ObjectNode stage,boolean first) {
        ObjectNode row=parseRecord(raw,field,f(I32,false,"native_index"),f(I32,true,"key_i32"),f(BOOL,true,"admitted"),f(TEXT,true,"property_identity","reason"),f(RAW,false,"property_block"));
        row.set("property_block",properties(row.get("property_block"),field+".property_block"));require(eq(row,"native_index",index),field,"native conditional order differs");
        Boolean expected=n(row,"key_i32")==null?null:membership(stage,n(row,"key_i32"),first);require(Objects.equals(b(row,"admitted"),expected),field,"signed membership admission differs");
        if(!Boolean.TRUE.equals(expected))require(nil(row.get("property_identity"))&&nil(row.get("property_block")),field,"undemanded conditional property container");return row;
    }
    static ObjectNode group(JsonNode raw,String field,ObjectNode stage) {
        ObjectNode row=parseRecord(raw,field,f(TEXT,false,"role"),f(I32,true,"track_index","level_index","conditional_b_count","conditional_a_count"),f(TEXT,true,"property_identity","reason"),f(BOOL,false,"ready"),f(RAW,false,"base_property_block","conditional_b_rows","conditional_a_rows"));
        row.set("base_property_block",properties(row.get("base_property_block"),field+".base_property_block"));String role=s(row,"role");
        require(role.equals("base")||role.equals("growth_level"),field,"invalid group role");require(role.equals("base")==(!present(row,"track_index")&&!present(row,"level_index")),field,"growth indices differ from role");
        boolean complete=present(row,"property_identity")&&pcReady(row.get("base_property_block"));
        for(String family:List.of("b","a")) {
            String name="conditional_"+family;int[] index={0};JsonNode entries=array(row.get(name+"_rows"),field+"."+name+"_rows",true,(value,path)->condition(value,path,index[0]++,stage,family.equals("a")));
            row.set(name+"_rows",entries);BigInteger count=n(row,name+"_count");complete=complete&&count!=null&&!nil(entries)&&BigInteger.valueOf(entries.size()).equals(count.max(BigInteger.ZERO));
            if(!nil(entries))for(JsonNode entry:entries)complete=complete&&zeroReason(entry)&&b(entry,"admitted")!=null&&(!Boolean.TRUE.equals(b(entry,"admitted"))||(present(entry,"property_identity")&&pcReady(entry.get("property_block"))));
        }
        complete=complete&&zeroReason(row);require(row.get("ready").booleanValue()==complete,field,"group readiness differs");return row;
    }
    private static ObjectNode track(JsonNode raw,String field,int index) {
        ObjectNode row=parseRecord(raw,field,f(I32,false,"native_index"),f(I32,true,"level_count","admitted_prefix_count"),f(I64,true,"current_value_raw"),f(TEXT,true,"reason"),f(RAW,false,"thresholds_read"));
        row.set("thresholds_read",numbers(row.get("thresholds_read"),field+".thresholds_read",64,false,true,false));require(eq(row,"native_index",index),field,"native track order differs");return row;
    }
    private static long fnvPointer(BigInteger pointer) {long hash=0x811c9dc5L;for(int index=0;index<8;index++)hash=((hash^pointer.shiftRight(index*8).and(BigInteger.valueOf(255)).longValue())*0x1000193L)&0xffffffffL;return hash;}
    private static ObjectNode side(JsonNode raw,String field,BigInteger pointer,ObjectNode stage) {
        ObjectNode row=parseRecord(raw,field,f(TEXT,false,"status"),f(BOOL,false,"ready"),f(I32,true,"map_mask_raw","kind_raw"),f(U8,true,"map_overflow_raw"),f(U32,true,"hash_u32"),f(I64,true,"first_row_index"),f(TEXT,true,"owner_selection","property_identity","reason"),f(RAW,false,"property_block","probes"));
        Availability availability=availability(row,field);row.set("property_block",properties(row.get("property_block"),field+".property_block"));
        BigInteger start=n(row,"first_row_index"),mask=n(row,"map_mask_raw"),overflow=n(row,"map_overflow_raw"),hash=n(row,"hash_u32");
        if(hash!=null)require(pointer!=null&&hash.equals(BigInteger.valueOf(fnvPointer(pointer)))&&mask!=null&&Objects.equals(start,BigInteger.valueOf(hash.intValue()&mask.intValue())),field,"full pointer hash/index differs");
        require(row.get("probes").isArray(),field,"probe array required");ArrayNode probes=list();boolean terminal=false,hit=false;int index=0;
        for(JsonNode input:row.get("probes")) {
            String path=field+".probes["+index+"]";ObjectNode probe=parseRecord(input,path,f(I64,false,"row_index"),f(U8,false,"distance_u8"),f(U8,true,"control_u8"),f(U64,true,"key_pointer_raw"),f(BOOL,true,"admitted"),f(TEXT,true,"reason"));
            require(!terminal&&start!=null&&n(probe,"row_index").equals(start.add(BigInteger.valueOf(index)))&&eq(probe,"distance_u8",(index+1)&255),path,"forward native probe order differs");
            Boolean admitted=n(probe,"control_u8")==null?null:n(probe,"control_u8").compareTo(n(probe,"distance_u8"))>=0;
            require(Objects.equals(b(probe,"admitted"),admitted)&&(Boolean.TRUE.equals(admitted)||nil(probe.get("key_pointer_raw"))),path,"probe admission differs");
            hit=Boolean.TRUE.equals(admitted)&&Objects.equals(n(probe,"key_pointer_raw"),pointer);terminal=Boolean.FALSE.equals(admitted)||hit;probes.add(probe);index++;
        }
        row.set("probes",probes);boolean complete=pointer!=null&&present(stage,"selector_a_identity")&&hash!=null&&mask!=null&&overflow!=null&&terminal&&!probes.isEmpty()&&n(row,"kind_raw")!=null;
        for(JsonNode probe:probes)complete=complete&&zeroReason(probe);
        Integer end=mask==null||overflow==null?null:mask.intValue()+overflow.intValue()+1;
        boolean nativeHit=hit&&!n(probes.get(probes.size()-1),"row_index").equals(end==null?null:BigInteger.valueOf(end));BigInteger kind=n(row,"kind_raw");
        if(terminal&&!nativeHit)require(kind==null||kind.signum()==0,field,"absent native probe requires kind zero");
        if(BigInteger.ZERO.equals(kind))require(nil(row.get("owner_selection"))&&nil(row.get("property_identity"))&&nil(row.get("property_block")),field,"neutral classification has undemanded owner properties");
        else if(kind!=null){String owner=kind.equals(BigInteger.ONE)?"provider_1620":"provider_1630";require(s(row,"owner_selection")==null||owner.equals(s(row,"owner_selection")),field,"signed kind owner differs");complete=complete&&owner.equals(s(row,"owner_selection"))&&present(row,"property_identity")&&pcReady(row.get("property_block"));}
        complete=complete&&availability.reason()==null;require(availability.ready()==complete,field,"classified-side readiness differs");return row;
    }
    private static boolean growthComplete(ObjectNode row,List<BigInteger> allIds) {
        BigInteger flag=n(row,"growth_flag_raw"),tracks=n(row,"track_count_raw");String selection=s(row,"growth_selection");JsonNode growth=row.get("growth_tracks");
        if(flag==null)return false;
        if(flag.signum()!=0)return selection.equals("empty_character_flag")&&eq(row,"growth_output_count_raw",0)&&growth.isEmpty();
        if(tracks==null)return false;
        if(tracks.signum()<=0)return selection.equals("empty_track_count")&&eq(row,"growth_output_count_raw",0)&&growth.isEmpty();
        BigInteger definition=n(row,"definition_id_raw");if(definition==null)return false;int match=allIds.indexOf(definition);
        if(match<0)return selection.equals("empty_trait_search")&&eq(row,"growth_output_count_raw",0)&&growth.isEmpty();
        JsonNode counts=row.get("growth_prefix_track_counts");if(!eq(row,"growth_trait_match_index",match)||nil(counts)||counts.size()!=match)return false;
        int offset=0;for(JsonNode count:counts)offset+=count.intValue();BigInteger aux=n(row,"growth_aux_count_raw");
        if(!eq(row,"growth_prefix_offset_raw",offset)||aux==null)return false;
        if(BigInteger.valueOf(offset).compareTo(aux)>=0)return selection.equals("empty_aux_range")&&eq(row,"growth_output_count_raw",0)&&growth.isEmpty();
        int output=Math.min(tracks.intValue(),aux.intValue()-offset);if(!eq(row,"growth_output_count_raw",output))return false;
        if(output==0)return selection.equals("empty_header_count")&&growth.isEmpty();
        if(!selection.equals("current_consumed_growth")||!BigInteger.valueOf(growth.size()).equals(tracks))return false;
        List<List<BigInteger>> expected=new ArrayList<>();
        for(JsonNode track:growth) {
            BigInteger value=n(track,"current_value_raw"),count=n(track,"level_count"),prefix=n(track,"admitted_prefix_count");JsonNode thresholds=track.get("thresholds_read");
            if(value==null||!zeroReason(track))return false;
            if(value.signum()<=0){if(count!=null||!nil(thresholds)||prefix!=null)return false;continue;}
            if(count==null||count.signum()<0||nil(thresholds)||prefix==null||prefix.signum()<0||prefix.compareTo(count)>0)return false;
            int admitted=prefix.intValue();boolean more=prefix.compareTo(count)<0;if(thresholds.size()!=admitted+(more?1:0))return false;
            for(int i=0;i<admitted;i++)if(thresholds.get(i).bigIntegerValue().compareTo(value)>0)return false;
            if(more&&thresholds.get(thresholds.size()-1).bigIntegerValue().compareTo(value)<=0)return false;
            for(int level=0;level<admitted;level++)expected.add(List.of(n(track,"native_index"),BigInteger.valueOf(level)));
        }
        List<List<BigInteger>> actual=new ArrayList<>();JsonNode groups=row.get("composite_groups");for(int i=1;i<groups.size();i++)actual.add(java.util.Arrays.asList(n(groups.get(i),"track_index"),n(groups.get(i),"level_index")));
        return expected.equals(actual);
    }
    private static ObjectNode row(JsonNode raw,String field,int index,ObjectNode stage,List<BigInteger> allIds) {
        ObjectNode row=parseRecord(raw,field,f(I32,false,"native_index","trait_id_raw"),f(I32,true,"definition_id_raw","track_count_raw","growth_trait_match_index","growth_prefix_offset_raw","growth_aux_count_raw","growth_output_count_raw"),f(U64,true,"definition_pointer_raw"),f(U8,true,"growth_flag_raw"),f(TEXT,true,"definition_selection","definition_identity","composite_reason","reason"),f(BOOL,false,"composite_ready"),f(RAW,false,"growth_selection","growth_prefix_track_counts","composite_groups","growth_tracks","side"));
        require(eq(row,"native_index",index),field,"native trait order differs");row.set("growth_selection",text(row.get("growth_selection"),field+".growth_selection",false,false));
        require(Set.of("","empty_character_flag","empty_track_count","empty_trait_search","empty_aux_range","empty_header_count","current_consumed_growth").contains(s(row,"growth_selection")),field,"invalid growth selection");
        require(s(row,"definition_selection")==null||Set.of("indexed_trait_database","native_trait_definition_fallback").contains(s(row,"definition_selection")),field,"invalid definition source");
        row.set("growth_prefix_track_counts",numbers(row.get("growth_prefix_track_counts"),field+".growth_prefix_track_counts",32,false,true,false));
        row.set("composite_groups",array(row.get("composite_groups"),field+".composite_groups",false,(value,path)->group(value,path,stage)));int[] trackIndex={0};
        row.set("growth_tracks",array(row.get("growth_tracks"),field+".growth_tracks",false,(value,path)->track(value,path,trackIndex[0]++)));
        row.set("side",side(row.get("side"),field+".side",n(row,"definition_pointer_raw"),stage));JsonNode groups=row.get("composite_groups");
        boolean complete=present(row,"definition_identity","definition_pointer_raw","definition_selection")&&!groups.isEmpty()&&s(groups.get(0),"role").equals("base")&&growthComplete(row,allIds)&&nil(row.get("composite_reason"));
        for(int i=0;i<groups.size();i++)complete=complete&&Boolean.TRUE.equals(b(groups.get(i),"ready"))&&(i==0||s(groups.get(i),"role").equals("growth_level"));
        require(row.get("composite_ready").booleanValue()==complete,field,"full composite readiness differs");require(zeroReason(row)==(complete&&Boolean.TRUE.equals(b(row.get("side"),"ready"))),field,"trait readiness differs");return row;
    }
    static JsonNode normalize(JsonNode input,String field) {
        if(nil(input))return NullNode.instance;
        ObjectNode out=parseRecord(input,field,f(TEXT,false,"status"),f(BOOL,false,"ready"),f(I32,false,"character_id"),f(I32,true,"trait_count","selector_a_key_raw","selector_b_key_raw","selector_a_membership_count","selector_b_primary_count","selector_b_nested_count"),f(BOOL,true,"trait_array_present"),f(TEXT,true,"selector_a_selection","selector_a_identity","selector_b_selection","selector_b_identity","reason"),f(RAW,false,"selector_a_keys_i32","selector_b_primary_keys_i32","selector_b_nested_keys","rows"));
        Availability availability=availability(out,field);
        for(String key:List.of("selector_a_keys_i32","selector_b_primary_keys_i32"))out.set(key,numbers(out.get(key),field+"."+key,32,false,true,false));
        int[] keyIndex={0};out.set("selector_b_nested_keys",array(out.get("selector_b_nested_keys"),field+".selector_b_nested_keys",true,(value,path)->keyset(value,path,keyIndex[0]++)));
        JsonNode nested=out.get("selector_b_nested_keys");BigInteger nestedCount=n(out,"selector_b_nested_count");if(!nil(nested))require(nestedCount!=null&&BigInteger.valueOf(nested.size()).compareTo(nestedCount.max(BigInteger.ZERO))<=0,field,"nested keyset count differs");
        JsonNode rawRows=out.get("rows");List<BigInteger> ids=new ArrayList<>();if(!nil(rawRows)){require(rawRows.isArray(),field,"trait rows must be array or null");for(JsonNode row:rawRows)ids.add(number(row.get("trait_id_raw"),field+".rows.trait_id_raw",32,false,false).bigIntegerValue());}
        int[] rowIndex={0};out.set("rows",array(rawRows,field+".rows",true,(value,path)->row(value,path,rowIndex[0]++,out,ids)));JsonNode rows=out.get("rows");BigInteger count=n(out,"trait_count");
        boolean complete=count!=null&&count.signum()>=0&&!nil(rows)&&BigInteger.valueOf(rows.size()).equals(count)&&(count.signum()==0||trueValue(out,"trait_array_present"))&&availability.reason()==null;
        if(!nil(rows))for(JsonNode row:rows)complete=complete&&Boolean.TRUE.equals(b(row,"composite_ready"))&&Boolean.TRUE.equals(b(row.get("side"),"ready"))&&zeroReason(row);
        require(availability.ready()==complete,field,"full D460 readiness differs");return out;
    }
}
