package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaselineAdapter;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads.*;

/** Original native result normalizers. Parsing DATA cannot create a permit, Known or stock admission. */
public final class ArmyWarSupplementalReadCodec {
    public static final int MAX_BYTES=1_048_576;
    public static final String PUBLIC_PROFILE="xar.army-supplemental-read-public64/v1";
    private static final BigInteger I32=BigInteger.valueOf(Integer.MAX_VALUE),I64=BigInteger.valueOf(Long.MAX_VALUE);
    private ArmyWarSupplementalReadCodec(){ }

    public static LocalSiege normalizeLocalSiege(Selection selected,RawJson original){
        StrictJson.require(kind(selected.operation())==Kind.LOCAL_SIEGE,"province siege selection required");
        ObjectNode raw=object(original);StrictJson.object(raw,Set.of("step","accepted","status","query_sequence","snapshot_revision","date_raw","province_state","backend_id"));
        literal(raw.get("step"),selected.operation().value());yes(raw.get("accepted"));literal(raw.get("backend_id"),"native-headless");
        positive64(raw.get("query_sequence"));
        StrictJson.require(integer(raw.get("snapshot_revision"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(selected.context().nativeRevision())
                &&raw.path("date_raw").isIntegralNumber()&&raw.get("date_raw").bigIntegerValue().equals(selected.context().dateRaw()),"province siege original native frame changed");
        ObjectNode state=province(raw.get("province_state"));
        StrictJson.require(integer(state.get("province_id"),BigInteger.ONE,I32).intValueExact()==id(selected.operation()),"province siege ProvinceID changed");
        boolean complete=state.get("occupation_observable").booleanValue()&&!state.get("fort_level").isNull()
                &&!state.get("garrison_size").isNull()&&!state.get("besieging_strength").isNull()&&state.get("siege_observable").booleanValue();
        literal(raw.get("status"),complete?"available":"partial");
        ObjectNode normalized=raw.deepCopy();normalized.set("province_state",state);
        return new LocalSiege(selected,original,json(normalized));
    }
    /** The existing sole Adapter validates actual before AND independently retained after snapshots. */
    public static DefenderBaseline normalizeBaseline(Selection selected,RawJson original,RawJson before,RawJson after){
        StrictJson.require(kind(selected.operation())==Kind.DEFENDER_BASELINE,"defender baseline selection required");
        ObjectNode raw=object(original);
        StrictJson.require(!raw.path("defender_de_jure_exit_terms_v1").has("h2743_stock_predicate_evidence_v1"),
                "source-admitted stock wire cannot enter the historical unadmitted baseline normalizer");
        var bound=DeJureExitBaselineAdapter.bindReturnedBaseline(original.bytes(),before.bytes(),after.bytes(),id(selected.operation()));
        return new DefenderBaseline(selected,original,before,after,bound,new RawJson(DeJureExitBaselineAdapter.encodeDriverResult(bound)));
    }
    /** Explicit typed public64 projection. Original numeric native/archive/normalized DATA is unchanged. */
    public static RawJson fullDriverResult(Observation actual){
        Objects.requireNonNull(actual);RawJson normalized;
        if(actual instanceof LocalSiege local){var replay=normalizeLocalSiege(local.selection(),local.nativeResult());StrictJson.require(replay.equals(local),"local siege observation differs from its sole original normalizer");normalized=replay.normalizedResult();}
        else if(actual instanceof DefenderBaseline baseline){var replay=normalizeBaseline(baseline.selection(),baseline.nativeResult(),baseline.before(),baseline.after());StrictJson.require(replay.equals(baseline),"defender baseline differs from its original before/after Adapter");normalized=replay.normalizedResult();}
        else if(actual instanceof DefenderStock stock)return ArmyWarSupplementalStockCodec.fullDriverResult(stock);
        else throw new IllegalArgumentException("unknown typed supplemental observation");
        ObjectNode result=object(normalized);decimal(result,"query_sequence",true);
        if(actual instanceof LocalSiege){
            integer(result.get("date_raw"),BigInteger.valueOf(Integer.MIN_VALUE),I32);decimal(result,"snapshot_revision",true);ObjectNode state=(ObjectNode)result.get("province_state");
            if(state.get("active_siege") instanceof ObjectNode siege){
                for(String key:List.of("progress_fraction","current_work","total_work","remaining_work","ordinary_daily_progress","current_phase_length","prepared_phase_length","assault_daily_progress","eligible_regiment_siege_work"))
                    if(siege.get(key) instanceof ObjectNode fixed)decimal(fixed,"raw",false);
            }
        }else{
            decimal(result,"queried_revision",false);decimal(result,"queried_native_revision",true);
            ObjectNode baseline=(ObjectNode)result.get("defender_de_jure_exit_terms_v1");decimal(baseline,"native_revision",true);
            // game_contract.hpp DefenderDeJureExitTermsV1 and its holder/resource rows declare
            // these as int32, despite the reusable historical Java model storing them in long.
            integer(baseline.get("date_raw"),BigInteger.valueOf(Integer.MIN_VALUE),I32);
            for(String key:List.of("primary_attacker_character_id","primary_defender_character_id"))integer(baseline.get(key),BigInteger.ONE,I32);
            for(JsonNode title:baseline.get("target_title_ids"))integer(title,BigInteger.ONE,I32);
            for(JsonNode holder:baseline.get("target_title_holder_prestate")){var row=(ObjectNode)holder;for(String key:List.of("title_id","holder_character_id"))integer(row.get(key),BigInteger.ONE,I32);if(!row.get("holder_immediate_liege_character_id").isNull())integer(row.get("holder_immediate_liege_character_id"),BigInteger.ONE,I32);}
            for(String key:List.of("primary_resource_balances","primary_monthly_gold_income"))for(JsonNode value:baseline.get(key)){var row=(ObjectNode)value;integer(row.get("character_id"),BigInteger.ONE,I32);signedDecimal((ObjectNode)row.get("value"),"raw");}
        }
        safeNumbers(result);return json(result);
    }

    private static ObjectNode province(JsonNode value){
        ObjectNode raw=object(value),out=StrictJson.object();putInt(out,"province_id",raw.get("province_id"),1,Integer.MAX_VALUE);
        boolean occupation=bool(raw.get("occupation_observable"));out.put("occupation_observable",occupation);
        JsonNode occupied=get(raw,"is_occupied"),occupant=get(raw,"occupying_character_id");
        if(!occupation){nil(occupied);nil(occupant);out.putNull("is_occupied");out.putNull("occupying_character_id");}
        else{boolean isOccupied=bool(occupied);out.put("is_occupied",isOccupied);if(isOccupied)putInt(out,"occupying_character_id",occupant,1,Integer.MAX_VALUE);else{nil(occupant);out.putNull("occupying_character_id");}}
        for(String key:List.of("fort_level","garrison_size","besieging_strength"))optionalInt(out,key,get(raw,key),0,Integer.MAX_VALUE);
        boolean visible=bool(raw.get("siege_observable"));out.put("siege_observable",visible);JsonNode siege=get(raw,"active_siege");
        if(!visible){nil(siege);out.putNull("active_siege");}else out.set("active_siege",siege.isNull()?siege:siege(siege));
        if(raw.has("current_besieging_army_selection"))out.set("current_besieging_army_selection",selection(raw.get("current_besieging_army_selection")));
        return out;
    }
    private static ObjectNode siege(JsonNode value){
        ObjectNode raw=object(value),out=StrictJson.object();putInt(out,"siege_id",raw.get("siege_id"),0,Integer.MAX_VALUE);
        optionalInt(out,"besieging_army_id",get(raw,"besieging_army_id"),0,Integer.MAX_VALUE);out.put("player_army_besieging",bool(raw.get("player_army_besieging")));
        ObjectNode progress=fixed(raw.get("progress_fraction"),true),current=fixed(raw.get("current_work"),false),total=fixed(raw.get("total_work"),false);
        out.set("progress_fraction",progress);out.set("current_work",current);out.set("total_work",total);
        out.set("remaining_work",fixedValue(total.get("raw").bigIntegerValue().subtract(current.get("raw").bigIntegerValue()).max(BigInteger.ZERO)));
        for(String key:List.of("days_left","phase_counter"))optionalInt(out,key,get(raw,key),0,Integer.MAX_VALUE);
        for(String key:List.of("ordinary_daily_progress","current_phase_length","prepared_phase_length"))out.set(key,get(raw,key).isNull()?get(raw,key):fixed(raw.get(key),false));
        JsonNode advance=get(raw,"can_advance");if(!advance.isNull())bool(advance);out.set("can_advance",advance.deepCopy());
        JsonNode phase=get(raw,"phase_event_state");if(phase.isNull())out.putNull("phase_event_state");else{ObjectNode p=object(phase),n=StrictJson.object();for(String key:List.of("breach_level","starvation_level","disease_level","desertion_count","stalemate_count"))optionalInt(n,key,get(p,key),0,Integer.MAX_VALUE);out.set("phase_event_state",n);}
        optionalInt(out,"prepared_selected_phase_event_enum",get(raw,"prepared_selected_phase_event_enum"),0,5);
        boolean assault=raw.has("assault_observable")?bool(raw.get("assault_observable")):false;out.put("assault_observable",assault);
        var assaultFields=List.of("breach_level","assault_in_progress","can_start_assault","can_stop_assault","assault_daily_progress","assault_daily_casualties");
        if(!assault){for(String key:assaultFields){nil(get(raw,key));out.putNull(key);}out.putNull("walls_breached");}
        else{int breach=integer(raw.get("breach_level"),BigInteger.ZERO,BigInteger.TWO).intValueExact();out.put("breach_level",breach).put("walls_breached",breach>0);
            for(String key:List.of("assault_in_progress","can_start_assault","can_stop_assault"))out.put(key,bool(raw.get(key)));
            out.set("assault_daily_progress",fixed(raw.get("assault_daily_progress"),false));putInt(out,"assault_daily_casualties",raw.get("assault_daily_casualties"),0,Integer.MAX_VALUE);}
        if(raw.has("eligible_regiment_siege_work"))out.set("eligible_regiment_siege_work",raw.get("eligible_regiment_siege_work").isNull()?raw.get("eligible_regiment_siege_work"):fixed(raw.get("eligible_regiment_siege_work"),false));
        if(raw.has("highest_eligible_siege_tier"))optionalInt(out,"highest_eligible_siege_tier",raw.get("highest_eligible_siege_tier"),0,Integer.MAX_VALUE);
        if(raw.has("province_unit_occurrences"))out.set("province_unit_occurrences",occurrences(raw.get("province_unit_occurrences")));
        return out;
    }
    private static JsonNode selection(JsonNode value){
        if(value.isNull())return value;ObjectNode raw=object(value),out=StrictJson.object();
        for(String key:List.of("native_carmy_id","public_unit_id"))optionalInt(out,key,get(raw,key),0,Integer.MAX_VALUE);
        JsonNode controlled=get(raw,"controllable");if(!controlled.isNull())bool(controlled);out.set("controllable",controlled.deepCopy());return out;
    }
    private static JsonNode occurrences(JsonNode value){
        if(value.isNull())return value;StrictJson.require(value.isArray(),"native province occurrence array required");ArrayNode out=StrictJson.object().arrayNode();int index=0;
        for(JsonNode v:value){ObjectNode raw=object(v),row=StrictJson.object();int ordinal=integer(raw.get("occurrence_index"),BigInteger.ZERO,I32).intValueExact();StrictJson.require(ordinal==index++,"native occurrence order changed");row.put("occurrence_index",ordinal);
            for(String key:List.of("public_unit_id","native_carmy_id"))optionalInt(row,key,get(raw,key),0,Integer.MAX_VALUE);
            JsonNode eligible=get(raw,"eligible"),regiments=get(raw,"qualified_regiment_ids");if(!eligible.isNull())bool(eligible);row.set("eligible",eligible.deepCopy());
            if(regiments.isNull())row.putNull("qualified_regiment_ids");else{StrictJson.require(regiments.isArray(),"qualified native regiment IDs must be array/null");ArrayNode ids=row.putArray("qualified_regiment_ids");for(JsonNode id:regiments)ids.add(integer(id,BigInteger.ZERO,I32));}
            if(eligible.isBoolean()&&eligible.booleanValue())StrictJson.require(!row.get("public_unit_id").isNull()&&!row.get("native_carmy_id").isNull(),"eligible occurrence lacks resolved identities");
            if(eligible.isBoolean()&&!eligible.booleanValue())StrictJson.require(regiments.isArray()&&regiments.isEmpty(),"excluded occurrence cannot consume regiments");
            if(eligible.isNull())nil(regiments);out.add(row);
        }return out;
    }
    private static ObjectNode fixed(JsonNode node,boolean fraction){ObjectNode value=StrictJson.object(node,Set.of("raw","scale"));BigInteger raw=integer(value.get("raw"),BigInteger.ZERO,fraction?BigInteger.valueOf(100_000):I64);integer(value.get("scale"),BigInteger.valueOf(100_000),BigInteger.valueOf(100_000));return fixedValue(raw);}
    private static ObjectNode fixedValue(BigInteger raw){return StrictJson.object().put("raw",raw).put("scale",100_000);}
    private static void optionalInt(ObjectNode out,String key,JsonNode value,int low,int high){if(value.isNull())out.putNull(key);else putInt(out,key,value,low,high);}
    private static void putInt(ObjectNode out,String key,JsonNode value,int low,int high){out.put(key,integer(value,BigInteger.valueOf(low),BigInteger.valueOf(high)));}
    private static JsonNode get(ObjectNode value,String key){return value.path(key).isMissingNode()?com.fasterxml.jackson.databind.node.NullNode.instance:value.get(key);}
    private static boolean bool(JsonNode value){StrictJson.require(value!=null&&value.isBoolean(),"strict native boolean required");return value.booleanValue();}
    private static void yes(JsonNode value){StrictJson.require(bool(value),"native acceptance required");}
    private static void nil(JsonNode value){StrictJson.require(value!=null&&value.isNull(),"explicit or normalized absent null required");}
    private static void literal(JsonNode value,String expected){StrictJson.require(value!=null&&value.isTextual()&&expected.equals(value.textValue()),"native literal differs: "+expected);}
    private static BigInteger integer(JsonNode value,BigInteger low,BigInteger high){return StrictJson.integer(value,low,high);}
    private static BigInteger positive64(JsonNode value){return integer(value,BigInteger.ONE,StrictJson.UINT64_MAX);}
    private static void decimal(ObjectNode value,String key,boolean positive){value.put(key,PublicUnsigned64.canonical(integer(value.get(key),positive?BigInteger.ONE:BigInteger.ZERO,StrictJson.UINT64_MAX),positive?PublicUnsigned64.Minimum.ONE:PublicUnsigned64.Minimum.ZERO));}
    private static void signedDecimal(ObjectNode value,String key){value.put(key,integer(value.get(key),BigInteger.valueOf(Long.MIN_VALUE),I64).toString());}
    private static void safeNumbers(JsonNode value){if(value.isIntegralNumber())StrictJson.require(value.bigIntegerValue().abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER)<=0,"undeclared unsafe public supplemental integer");else if(value.isContainerNode())value.forEach(ArmyWarSupplementalReadCodec::safeNumbers);}
    static ObjectNode object(RawJson value){return object(DriverJson.toNode(DriverJson.object(value.bytes(),MAX_BYTES)));}
    private static ObjectNode object(JsonNode value){StrictJson.require(value instanceof ObjectNode,"native object required");return (ObjectNode)value;}
    static RawJson json(JsonNode value){return new RawJson(DriverJson.encode(DriverJson.fromNode(value)));}
}
