package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.util.Set;

/** Entire-vector Definition preflight precedes every 2920B50 rank/PC demand. */
final class BattlePersonRankedCodec {
    private BattlePersonRankedCodec() { }
    private static final String[] NUMBERS={"rank_raw_i32","index_raw_i32","ranked_count_raw","ranked_default_init_guard_raw"};
    private static final String[] STRINGS={"ranked_header_identity","selection","selected_row_identity"};
    private static ObjectNode attributeShape(JsonNode raw,String field) {
        return shape(raw,field,"native_index","definition_present","definition_identity","definition_magic_u32","preflight_valid","rank_raw_i32","index_raw_i32","ranked_count_raw","ranked_default_init_guard_raw","ranked_header_identity","selection","selected_row_identity","ranked_array_present","pc","ready","reason");
    }
    private static Boolean preflight(JsonNode raw,String field) {
        Boolean present=booleanValue(bool(raw.get("definition_present"),field+".definition_present",true));
        JsonNode magic=number(raw.get("definition_magic_u32"),field+".definition_magic_u32",32,true,true);
        return Boolean.FALSE.equals(present)?false:present==null||nil(magic)?null:eq(magic,0x4744624fL);
    }
    private static ObjectNode attribute(JsonNode raw,String field,int ordinal,boolean numeric) {
        ObjectNode in=attributeShape(raw,field),out=object();index(in,out,field,false);nums(in,out,field,32,false,NUMBERS);nums(in,out,field,32,true,"definition_magic_u32");
        texts(in,out,field,STRINGS);texts(in,out,field,"definition_identity","reason");bools(in,out,field,"definition_present","preflight_valid","ranked_array_present");out.set("ready",bool(in.get("ready"),field+".ready",false));out.set("pc",pc(in.get("pc"),field+".pc"));
        require(eq(out.get("native_index"),ordinal),field,"attribute physical order differs");same(out.get("preflight_valid"),preflight(in,field),field,"Definition preflight differs");
        if(!Boolean.TRUE.equals(booleanValue(out.get("definition_present"))))require(nil(out.get("definition_identity"))&&nil(out.get("definition_magic_u32")),field,"absent Definition contains undemanded identity/magic");
        if(!numeric) {
            for(String key:NUMBERS)require(nil(out.get(key)),field,"entire-vector preflight blocks every rank operand");
            for(String key:STRINGS)require(nil(out.get(key)),field,"entire-vector preflight blocks every rank selection");
            require(nil(out.get("ranked_array_present"))&&absentPc(out.get("pc"))&&!out.get("ready").booleanValue(),field,"blocked preflight contains ranked header/PC");return out;
        }
        BigInteger rank=integer(out.get("rank_raw_i32")),index=rank==null?null:wrap(rank.subtract(BigInteger.ONE),32),count=integer(out.get("ranked_count_raw"));String selection=null;
        if(index!=null&&(index.signum()<0||count!=null)) {
            if(index.signum()<0||index.compareTo(count)>=0) {
                JsonNode guard=out.get("ranked_default_init_guard_raw");if(!nil(guard))selection=zero(guard)||eq(guard,-1)?"uninitialized_default_5d68fb0":"initialized_default_5d68fb0";
            } else selection="indexed_ranked_row";
        }
        same(out.get("index_raw_i32"),index,field,"native wrapped rank index differs");same(out.get("selection"),selection,field,"native rank/default selection differs");
        if(index!=null&&index.signum()<0)require(nil(out.get("ranked_count_raw"))&&nil(out.get("ranked_array_present")),field,"negative index contains undemanded ranked header");
        boolean selected;
        if("indexed_ranked_row".equals(selection)) {
            require(nil(out.get("ranked_default_init_guard_raw")),field,"indexed row contains undemanded default guard");
            selected=!nil(out.get("ranked_header_identity"))&&Boolean.TRUE.equals(booleanValue(out.get("ranked_array_present")));
        } else {
            selected="initialized_default_5d68fb0".equals(selection);require(nil(out.get("ranked_array_present")),field,"default row contains undemanded ranked data");
        }
        if("uninitialized_default_5d68fb0".equals(selection))require(is(out.get("reason"),"ranked_default_initialization_result")&&absentPc(out.get("pc")),field,"cold default must preserve actual initialization gap without PC bytes");
        ready(out,!nil(out.get("definition_identity"))&&selected&&!nil(out.get("selected_row_identity"))&&pcReady(out.get("pc")),field);return out;
    }
    private static ObjectNode occurrence(JsonNode raw,String field,int ordinal,boolean own) {
        ObjectNode out=start(raw,field,"native_index","requested_full_id_raw","resolution_selection","selected_full_id_raw","object_identity","accolade_magic_u32","accolade_full_id_raw","admitted","attribute_count_raw","attribute_array_present","preflight_ready","preflight_all_valid","attributes");
        index(raw,out,field,false);nums(raw,out,field,32,false,"requested_full_id_raw","selected_full_id_raw","accolade_full_id_raw","attribute_count_raw");nums(raw,out,field,32,true,"accolade_magic_u32");
        texts(raw,out,field,"resolution_selection","object_identity");bools(raw,out,field,"admitted","attribute_array_present","preflight_all_valid");out.set("preflight_ready",bool(raw.get("preflight_ready"),field+".preflight_ready",false));
        String selection=string(out.get("resolution_selection"));require(eq(out.get("native_index"),ordinal)&&(selection==null||selection.equals("registry_full_id_8")||selection.equals("native_fallback")),field,"occurrence order/resolution differs");
        if("registry_full_id_8".equals(selection))require(!nil(out.get("requested_full_id_raw"))&&out.get("requested_full_id_raw").equals(out.get("selected_full_id_raw")),field,"full-generation selection differs");
        boolean resolved=selection!=null&&!nil(out.get("object_identity"));Boolean admitted;
        if(own)admitted=!resolved||nil(out.get("accolade_magic_u32"))?null:!eq(out.get("accolade_magic_u32"),0x4163636fL)?false:nil(out.get("accolade_full_id_raw"))?null:!eq(out.get("accolade_full_id_raw"),-1);
        else {admitted=resolved?true:null;require(nil(out.get("accolade_magic_u32"))&&nil(out.get("accolade_full_id_raw")),field,"list occurrence has no Acco magic/full-ID gate");}
        same(out.get("admitted"),admitted,field,"actual Accolade admission differs");JsonNode attrs=raw.get("attributes");require(nil(attrs)||attrs.isArray(),field,"attributes must be original-order list or null");
        BigInteger count=integer(out.get("attribute_count_raw"));boolean preflight=false;Boolean all=null;
        if(Boolean.FALSE.equals(admitted)) {
            require(count==null&&nil(out.get("attribute_array_present"))&&attrs.isArray()&&attrs.isEmpty(),field,"rejected own Accolade contains attribute operands");preflight=true;all=false;
        } else if(Boolean.TRUE.equals(admitted)&&BigInteger.ZERO.equals(count)) {
            require(attrs.isArray()&&attrs.isEmpty(),field,"zero vector contains attribute rows");preflight=true;all=true;
        } else if(Boolean.TRUE.equals(admitted)&&count!=null&&count.signum()>0&&attrs.isArray()&&Boolean.TRUE.equals(booleanValue(out.get("attribute_array_present")))) {
            require(BigInteger.valueOf(attrs.size()).compareTo(count)<=0,field,"attribute prefix exceeds actual count");boolean allSeen=true;
            for(int i=0;i<attrs.size();i++) {
                ObjectNode row=attributeShape(attrs.get(i),field+".attributes["+i+"]");Boolean valid=preflight(row,field);
                if(!Boolean.TRUE.equals(valid)) {require(i==attrs.size()-1,field,"preflight prefix continues after invalid/unknown Definition");preflight=Boolean.FALSE.equals(valid);all=preflight?Boolean.FALSE:null;allSeen=false;break;}
            }
            if(allSeen&&BigInteger.valueOf(attrs.size()).equals(count)){preflight=true;all=true;}
        }
        same(out.get("preflight_ready"),preflight,field,"entire-vector preflight availability differs");same(out.get("preflight_all_valid"),all,field,"entire-vector preflight validity differs");
        JsonNode normalized=NullNode.instance;
        if(attrs.isArray()){ArrayNode result=list();for(int i=0;i<attrs.size();i++)result.add(attribute(attrs.get(i),field+".attributes["+i+"]",i,preflight&&Boolean.TRUE.equals(all)));normalized=result;}
        out.set("attributes",normalized);boolean every=true;for(JsonNode row:normalized)every&=row.get("ready").booleanValue();
        ready(out,resolved&&preflight&&(Boolean.FALSE.equals(all)||every),field);return out;
    }
    private static ObjectNode listFamily(JsonNode raw,String field) {
        ObjectNode out=start(raw,field,"component_present","header_selection","default_init_guard_raw","count_raw","numeric_count","array_present","rows");
        bools(raw,out,field,"component_present","array_present");texts(raw,out,field,"header_selection");nums(raw,out,field,32,false,"default_init_guard_raw","count_raw","numeric_count");
        JsonNode original=raw.get("rows"),rows=NullNode.instance;if(!nil(original)){require(original.isArray(),field,"physical list rows required");ArrayNode items=list();for(int i=0;i<original.size();i++)items.add(occurrence(original.get(i),field+".rows["+i+"]",i,false));rows=items;}out.set("rows",rows);
        String selection=string(out.get("header_selection"));require(selection==null||Set.of("current_1c8_50","inline_default_5d67e80","modeled_empty_default_5d67e80").contains(selection),field,"unsupported list header");
        if(selection!=null)require(selection.equals("current_1c8_50")==Boolean.TRUE.equals(booleanValue(out.get("component_present"))),field,"header selection differs from component1C8");
        JsonNode guard=out.get("default_init_guard_raw"),count=out.get("count_raw");boolean complete;
        if("modeled_empty_default_5d67e80".equals(selection)) {
            require((zero(guard)||eq(guard,-1))&&nil(count)&&zero(out.get("numeric_count"))&&nil(out.get("array_present"))&&rows.isArray()&&rows.isEmpty(),field,"modeled default contains physical operands or lacks native guard");complete=true;
        } else {
            require(count.equals(out.get("numeric_count")),field,"numeric count differs from actual header");complete=selection!=null&&!nil(count)&&integer(count).signum()>=0&&rows.isArray()&&integer(count).equals(BigInteger.valueOf(rows.size()));
            if(positive(count)){complete&=Boolean.TRUE.equals(booleanValue(out.get("array_present")));for(JsonNode row:rows)complete&=row.get("ready").booleanValue();}
            if("inline_default_5d67e80".equals(selection))complete&=!nil(guard)&&!zero(guard)&&!eq(guard,-1);
            if("current_1c8_50".equals(selection))require(nil(guard),field,"current header contains undemanded default guard");
        }
        ready(out,complete,field);return out;
    }
    static JsonNode normalize(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;ObjectNode out=start(raw,field,"character_id","list_1c8_50","own_1b0_570");
        out.set("character_id",number(raw.get("character_id"),field+".character_id",32,false,false));ObjectNode list=listFamily(raw.get("list_1c8_50"),field+".list_1c8_50");out.set("list_1c8_50",list);
        JsonNode ownRaw=raw.get("own_1b0_570");ObjectNode own=start(ownRaw,field+".own_1b0_570","component_present","occurrence");bools(ownRaw,own,field,"component_present");ObjectNode occurrence=occurrence(ownRaw.get("occurrence"),field+".own_1b0_570.occurrence",0,true);own.set("occurrence",occurrence);ready(own,occurrence.get("ready").booleanValue(),field);out.set("own_1b0_570",own);
        require(out.get("ready").booleanValue()==(list.get("ready").booleanValue()&&own.get("ready").booleanValue()),field,"whole stage differs from two independent families");return out;
    }
}
