package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleLeafRecord.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleLeafRecord.Kind.*;

/** Actual current 2922070 walk/filter/membership/order validation, without native writes. */
final class Battle2922070Codec {
    private static final BigInteger MASK=new BigInteger("1000000400",16), MAGIC=BigInteger.valueOf(0x4744624fL);
    private Battle2922070Codec() { }
    private static ObjectNode edge(JsonNode raw,String field) {return parseRecord(raw,field,f(I32,true,"requested_id_raw","holder_id_18_raw"),f(TEXT,true,"selection","object_identity","holder_identity","reason"),f(I32,false,"native_index"));}
    private static ObjectNode walk(JsonNode raw,String field) {
        ObjectNode row=parseRecord(raw,field,f(I32,true,"count_c_raw"),f(TEXT,true,"header_selection","reason"),f(BOOL,true,"array_present"),f(I32,false,"native_index"),f(TEXT,false,"character_identity"),f(RAW,false,"edges"));
        row.set("edges",ordered(row.get("edges"),field+".edges",false,Battle2922070Codec::edge));return row;
    }
    private static ObjectNode character(JsonNode raw,String field) {
        ObjectNode row=parseRecord(raw,field,f(I32,true,"input_id_raw","character_id_18_raw","first_key_158_raw","owner_id_160_raw"),
                f(TEXT,true,"selection","character_identity","first_selection","first_identity","owner_selection","owner_identity","government_selection","government_identity","top_character_identity","top_government_selection","top_government_identity","reason"),
                f(BOOL,true,"admitted"),f(I32,false,"native_index"),f(BOOL,false,"include_self"),f(U64,true,"government_mask_40_raw","top_government_mask_40_raw"));
        Boolean expected=null;
        if(row.get("include_self").booleanValue())expected=true;
        else if(eq(row,"first_key_158_raw",-1))expected=false;
        else if(present(row,"owner_id_160_raw","character_id_18_raw")) {
            expected=n(row,"owner_id_160_raw").equals(n(row,"character_id_18_raw"));
            if(expected){BigInteger first=n(row,"government_mask_40_raw"),top=n(row,"top_government_mask_40_raw");expected=first==null?null:!first.and(MASK).equals(MASK)?false:top==null?null:top.and(MASK).equals(MASK);}
        }
        require(Objects.equals(b(row,"admitted"),expected),field,"actual character filter admission differs");return row;
    }
    private static ObjectNode key(JsonNode raw,String field) {return parseRecord(raw,field,f(I32,true,"requested_id_raw"),f(U8,true,"gate_32_raw"),f(TEXT,true,"selection","object_identity","reason"),f(I32,false,"native_index"));}
    private static boolean nonzero(JsonNode raw,String key) {BigInteger value=n(raw,key);return value!=null&&value.signum()!=0;}
    private static ObjectNode member(JsonNode raw,String field) {
        ObjectNode row=parseRecord(raw,field,f(I32,true,"first_key_158_raw","count_c_raw","first_id_10_raw"),f(TEXT,true,"first_selection","first_identity","header_selection","reason"),f(BOOL,true,"array_present","admitted","appended"),f(I32,false,"native_index","character_index"),f(RAW,false,"scans"));
        row.set("scans",ordered(row.get("scans"),field+".scans",false,Battle2922070Codec::key));JsonNode scans=row.get("scans");
        for(int index=0;index<scans.size()-1;index++)require(!nonzero(scans.get(index),"gate_32_raw"),field,"scan continued after first native membership match");
        if(Boolean.TRUE.equals(b(row,"admitted")))require(!scans.isEmpty()&&nonzero(scans.get(scans.size()-1),"gate_32_raw"),field,"admission lacks first nonzero BYTE32");
        if(Boolean.FALSE.equals(b(row,"admitted")))for(JsonNode scan:scans)require(!nonzero(scan,"gate_32_raw"),field,"actual membership match was rejected");return row;
    }
    private static void absent(ObjectNode row,String field,String... keys) {for(String key:keys)require(nil(row.get(key)),field,"undemanded operand: "+key);}
    private static ObjectNode sourceRow(JsonNode raw,String field) {
        ObjectNode row=parseRecord(raw,field,f(I32,true,"selected_id_10_raw","count_214_raw","requested_index_228_raw","selected_index_raw"),f(TEXT,true,"selection","source_identity","definition_identity","table_identity","property_identity","reason"),f(BOOL,true,"admitted"),f(I32,false,"native_index","input_index","requested_id_raw"),f(U8,true,"type_280_raw"),f(U32,true,"definition_magic_38_raw"),f(RAW,false,"property_block"));
        row.set("property_block",properties(row.get("property_block"),field+".property_block"));BigInteger type=n(row,"type_280_raw"),magic=n(row,"definition_magic_38_raw");
        Boolean admitted=type==null?null:!type.equals(BigInteger.TWO)?false:magic==null?null:magic.equals(MAGIC);require(Objects.equals(b(row,"admitted"),admitted),field,"BYTE280/magic38 admission differs");
        BigInteger count=n(row,"count_214_raw"),requested=n(row,"requested_index_228_raw");if(count!=null&&requested!=null){int last=count.intValue()-1;int expected=requested.signum()<0?0:Math.min(requested.intValue(),last);require(eq(row,"selected_index_raw",expected),field,"signed native clamp differs");}
        if(type!=null&&!type.equals(BigInteger.TWO))absent(row,field,"definition_identity","definition_magic_38_raw","count_214_raw","requested_index_228_raw","selected_index_raw","table_identity","property_identity","property_block");
        if(!Boolean.TRUE.equals(admitted))absent(row,field,"count_214_raw","requested_index_228_raw","selected_index_raw","table_identity","property_identity","property_block");return row;
    }
    private static boolean rowReady(JsonNode row) {
        Boolean admitted=b(row,"admitted");return zeroReason(row)&&admitted!=null&&(!admitted||(present(row,"definition_identity","definition_magic_38_raw","count_214_raw","requested_index_228_raw","selected_index_raw","table_identity","property_identity")&&pcReady(row.get("property_block"))));
    }
    private static List<BigInteger> integers(JsonNode rows) {List<BigInteger> result=new ArrayList<>();for(JsonNode row:rows)result.add(integer(row));return result;}
    private static boolean collectionReady(ObjectNode branch) {
        for(String key:List.of("walk_nodes","characters","character_order","membership_rows","output_ids","rows"))if(nil(branch.get(key)))return false;
        JsonNode walks=branch.get("walk_nodes"),characters=branch.get("characters"),members=branch.get("membership_rows"),sourceRows=branch.get("rows");
        List<BigInteger> order=integers(branch.get("character_order")),ids=integers(branch.get("output_ids"));
        if(walks.isEmpty()||characters.isEmpty()||!Boolean.TRUE.equals(b(characters.get(characters.size()-1),"include_self")))return false;
        for(JsonNode walk:walks) {
            BigInteger count=n(walk,"count_c_raw");if(!zeroReason(walk)||count==null||count.signum()<0||b(walk,"array_present")==null||!BigInteger.valueOf(walk.get("edges").size()).equals(count))return false;
            for(JsonNode edge:walk.get("edges"))if(!zeroReason(edge)||!present(edge,"selection","object_identity","holder_identity","holder_id_18_raw"))return false;
        }
        List<Integer> retained=new ArrayList<>();
        for(int index=0;index<characters.size();index++){JsonNode row=characters.get(index);if(!zeroReason(row)||!present(row,"character_identity")||b(row,"admitted")==null)return false;if(Boolean.TRUE.equals(b(row,"admitted")))retained.add(index);}
        if(retained.size()>1) {
            for(int index:retained)if(n(characters.get(index),"character_id_18_raw")==null)return false;
            retained.sort(Comparator.<Integer>comparingLong(index->n(characters.get(index),"character_id_18_raw").longValue()&0xffffffffL));
            List<Integer> unique=new ArrayList<>();String previous=null;for(int index:retained){String identity=s(characters.get(index),"character_identity");if(unique.isEmpty()||!Objects.equals(previous,identity))unique.add(index);previous=identity;}retained=unique;
        }
        List<BigInteger> expectedOrder=new ArrayList<>();for(int index:retained)expectedOrder.add(BigInteger.valueOf(index));
        if(!order.equals(expectedOrder)||members.size()!=order.size())return false;List<BigInteger> appended=new ArrayList<>();
        for(int index=0;index<members.size();index++) {
            JsonNode member=members.get(index);BigInteger count=n(member,"count_c_raw");
            if(!zeroReason(member)||!Objects.equals(n(member,"character_index"),order.get(index))||!present(member,"first_key_158_raw","first_selection","first_identity","header_selection","count_c_raw","array_present","admitted")||count.signum()<0)return false;
            JsonNode scans=member.get("scans");for(JsonNode scan:scans)if(!zeroReason(scan)||!present(scan,"requested_id_raw","selection","object_identity","gate_32_raw"))return false;
            if(Boolean.TRUE.equals(b(member,"admitted"))) {
                BigInteger id=n(member,"first_id_10_raw");if(id==null||BigInteger.valueOf(scans.size()).compareTo(count)>0)return false;boolean actual=!appended.contains(id);
                if(!Objects.equals(b(member,"appended"),actual))return false;if(actual)appended.add(id);
            } else if(!BigInteger.valueOf(scans.size()).equals(count))return false;
        }
        if(!ids.equals(appended)||sourceRows.size()!=ids.size())return false;List<BigInteger> inputIndices=new ArrayList<>();for(JsonNode row:sourceRows)inputIndices.add(n(row,"input_index"));inputIndices.sort(Comparator.naturalOrder());
        for(int index=0;index<inputIndices.size();index++)if(!inputIndices.get(index).equals(BigInteger.valueOf(index)))return false;
        for(JsonNode row:sourceRows)if(!n(row,"requested_id_raw").equals(ids.get(n(row,"input_index").intValueExact()))||!present(row,"selection","source_identity"))return false;
        if(sourceRows.size()>1) {
            for(JsonNode row:sourceRows)if(n(row,"selected_id_10_raw")==null)return false;List<JsonNode> expected=rows(sourceRows);
            expected.sort(Comparator.<JsonNode>comparingLong(row->n(row,"selected_id_10_raw").longValue()&0xffffffffL).thenComparing(row->n(row,"input_index")));
            if(!rows(sourceRows).equals(expected))return false;
        }return true;
    }
    static JsonNode normalize(JsonNode input,String field) {
        if(nil(input))return NullNode.instance;
        ObjectNode out=parseRecord(input,field,f(I32,true,"subject_id_8_raw"),f(TEXT,true,"government_selection","government_identity","subject_identity","reason"),f(BOOL,true,"character_land_present","admitted"),f(U8,true,"government_mode_4d6_raw"),f(U32,true,"subject_magic_c_raw"),f(I32,false,"character_id"),f(BOOL,false,"ready","gate_ready","collection_ready","rows_ready"),f(TEXT,false,"status"),f(RAW,false,"walk_nodes","characters","character_order","membership_rows","output_ids","rows"));
        Availability availability=availability(out,field);
        out.set("walk_nodes",ordered(out.get("walk_nodes"),field+".walk_nodes",true,Battle2922070Codec::walk));
        out.set("characters",ordered(out.get("characters"),field+".characters",true,Battle2922070Codec::character));
        out.set("membership_rows",ordered(out.get("membership_rows"),field+".membership_rows",true,Battle2922070Codec::member));
        out.set("rows",ordered(out.get("rows"),field+".rows",true,Battle2922070Codec::sourceRow));
        for(String key:List.of("character_order","output_ids"))out.set(key,numbers(out.get(key),field+"."+key,32,false,true,false));
        BigInteger mode=n(out,"government_mode_4d6_raw"),magic=n(out,"subject_magic_c_raw"),word=n(out,"subject_id_8_raw");Boolean land=b(out,"character_land_present");
        Boolean admitted=mode==null?null:!mode.equals(BigInteger.valueOf(5))?false:Boolean.FALSE.equals(land)?false:land==null||magic==null?null:!magic.equals(BigInteger.valueOf(0x5362436fL))?true:word==null?null:word.equals(BigInteger.valueOf(-1));
        require(Objects.equals(b(out,"admitted"),admitted)&&out.get("gate_ready").booleanValue()==(admitted!=null),field,"whole-helper admission differs");
        if(magic!=null&&!magic.equals(BigInteger.valueOf(0x5362436fL)))require(word==null,field,"undemanded subject ID8");
        boolean collection=Boolean.TRUE.equals(admitted)&&collectionReady(out),readyRows=collection;
        if(collection)for(JsonNode row:out.get("rows"))readyRows=readyRows&&rowReady(row);
        require(out.get("collection_ready").booleanValue()==collection&&out.get("rows_ready").booleanValue()==readyRows,field,"collection/rows readiness differs");
        boolean complete=admitted!=null&&(!admitted||collection&&readyRows)&&availability.reason()==null;require(availability.ready()==complete,field,"demanded2922070 readiness differs");return out;
    }
}
