package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Strict dynamic boundary shared only by additive combat observations. */
final class CombatLeafWire {
    static final long U32=0xffff_ffffL;
    static final String ACTUAL4_SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private CombatLeafWire() { }
    static ObjectNode obj(JsonNode value,String fields){return object(value,fields,"combat leaf");}
    static long range(JsonNode n,long min,long max,String field){
        require(n!=null&&n.isIntegralNumber()&&n.bigIntegerValue().compareTo(BigInteger.valueOf(min))>=0&&n.bigIntegerValue().compareTo(BigInteger.valueOf(max))<=0,field+" must be an integer in "+min+".."+max);return n.longValue();
    }
    static Long nr(JsonNode n,long min,long max,String field){return nil(n)?null:range(n,min,max,field);}
    static long u32(JsonNode n,String field){return range(n,0,U32,field);}
    static Long ref(JsonNode n,String field){Long value=nr(n,0,U32,field);require(value==null||value!=U32,field+" must null the absent reference");return value;}
    static Boolean nb(JsonNode n,String field){return nil(n)?null:bool(n,field);}
    static Long ni64(JsonNode n,String field){return nil(n)?null:i64(n,field);}
    static Integer ni32(JsonNode n,String field){return nil(n)?null:i32(n,field);}
    static boolean yes(JsonNode n){return n!=null&&n.isBoolean()&&n.booleanValue();}
    static boolean no(JsonNode n){return n!=null&&n.isBoolean()&&!n.booleanValue();}
    static void falseField(ObjectNode n,String field){require(no(n.get(field)),field+" must remain false");}
    static String state(ObjectNode n,String... allowed){String status=token(n.get("status"),"status",allowed);String reason=nullableText(n.get("unavailable_reason"),"unavailable_reason");require(status.equals("available")== (reason==null),"status/reason differs");return status;}
    static String state(boolean ready,int known){return ready?"available":known>0?"partial":"unavailable";}
    static void source(ObjectNode n,String scope){require(range(n.get("schema_version"),1,1,"schema_version")==1,"schema_version");eq(n.get("scope"),scope,"scope is malformed");eq(n.get("source_ck3_sha256"),ACTUAL4_SHA,"source is not the exact actual4 executable");}
    static void sourceCharacter(ObjectNode n,Integer expected){long id=u32(n.get("source_character_id"),"source_character_id");require(id!=U32&&expected!=null&&id==Integer.toUnsignedLong(expected),"source CharacterID mismatch");}
    static List<String> boundedStrings(JsonNode n,int count,boolean nonempty){ArrayNode a=array(n,"strings");require(count<0||a.size()==count,"string list length differs");List<String> out=new ArrayList<>();for(JsonNode v:a){require(v.isTextual()&&(!nonempty||!v.textValue().isEmpty())&&v.textValue().getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=4096,"string operand malformed");out.add(v.textValue());}return List.copyOf(out);}
    static ObjectNode boolObservation(JsonNode n){ObjectNode row=obj(n,"status value unavailable_reason");String s=state(row,"available","unavailable");Boolean v=nb(row.get("value"),"value");require(s.equals("available")== (v!=null),"Boolean observation status/value differs");return row;}
    static ObjectNode perk(JsonNode n,String key){ObjectNode row=obj(n,"definition_key presence");require(nil(row.get("definition_key"))||row.get("definition_key").isTextual()&&row.get("definition_key").textValue().equals(key),"perk definition differs");ObjectNode p=boolObservation(row.get("presence"));require(!p.get("status").textValue().equals("available")||!nil(row.get("definition_key")),"available perk lacks definition");return row;}
    static void resolution(String value,Long raw,Long resolved,boolean absent){require(List.of("resolved","native_fallback","unresolved","absent").contains(value)&&(!value.equals("absent")||absent),"resolution malformed");require(value.equals("resolved")== (resolved!=null)&& (resolved==null||resolved.equals(raw)),"resolution identity differs");require(!value.equals("absent")||raw==null||raw==U32,"absence differs");}
    record Occurrence(int ordinal,long characterId,int publicId,Integer nativeId,Integer regimentId,String encounterRole,String phaseRole) {
        void verify(ObjectNode row,boolean knightFields,boolean signedNative){
            require(range(row.get("occurrence_index"),0,Integer.MAX_VALUE,"occurrence_index")==ordinal&&u32(row.get("character_id"),"character_id")==characterId&&range(row.get("source_public_cunit_id"),Integer.MIN_VALUE,Integer.MAX_VALUE,"source_public_cunit_id")==publicId,"occurrence changes V2 role provenance");
            Long nativeValue=nr(row.get("source_native_carmy_id"),signedNative?Integer.MIN_VALUE:0,Integer.MAX_VALUE,"source_native_carmy_id");require(Objects.equals(nativeValue,nativeId==null?null:nativeId.longValue()),"occurrence changes native ArmyID");
            eq(row.get("encounter_role"),encounterRole,"occurrence changes encounter role");
            if(knightFields){Long regiment=nr(row.get("source_regiment_id"),0,Integer.MAX_VALUE,"source_regiment_id");require(Objects.equals(regiment,regimentId==null?null:regimentId.longValue()),"occurrence changes source RegimentID");eq(row.get("phase_role"),phaseRole,"occurrence changes phase role");}
        }
    }
    static List<Occurrence> roster(List<CombatSimulationInputs.Army> armies,boolean commandersOnly){
        List<Occurrence> rows=new ArrayList<>();int ordinal=0;
        for(var a:armies){String role=a.encounterRole()==CombatSimulationInputs.EncounterRole.ATTACKER?"attacker":"defender";
            if(a.commander().status()==CombatSimulationInputs.Status.AVAILABLE){rows.add(new Occurrence(ordinal,Integer.toUnsignedLong(a.commander().characterId()),a.armyId(),a.nativeCarmyId(),null,role,"commander"));ordinal++;}
            if(a.knights().members()!=null)for(var k:a.knights().members()){if(!commandersOnly)rows.add(new Occurrence(ordinal,Integer.toUnsignedLong(k.characterId()),a.armyId(),a.nativeCarmyId(),k.sourceRegimentId(),role,"knight"));ordinal++;}
        }return List.copyOf(rows);
    }
    static ObjectNode occurrence(JsonNode leaf,int ordinal){if(!(leaf instanceof ObjectNode root)||!(root.get("occurrences") instanceof ArrayNode a))throw new IllegalArgumentException("same-query source occurrence unavailable");for(JsonNode n:a)if(n.isObject()&&n.path("occurrence_index").isIntegralNumber()&&n.path("occurrence_index").intValue()==ordinal)return (ObjectNode)n;throw new IllegalArgumentException("same-query source occurrence unavailable");}
    static boolean catalogObserved(JsonNode roles){if(!(roles instanceof ObjectNode r)||!(r.get("loaded_registry") instanceof ObjectNode c)||!c.path("count_raw").isIntegralNumber()||!(c.get("rows") instanceof ArrayNode rows))return false;long count=c.get("count_raw").longValue();return count>=0&&count==rows.size();}
    static JsonNode sourceLeaf(CombatOptionalLeaves.Context c,CombatOptionalLeaves.Leaf leaf){ObjectNode root=c.normalizedRoot();return root==null?null:root.get(leaf.wireName());}
    static ObjectNode unavailable(String scope,String prefix,String reason,String... flags){ObjectNode n=empty();n.put("schema_version",1);n.put("scope",scope);n.put("status","unavailable");n.put("source_ck3_sha256",ACTUAL4_SHA);for(String f:flags)n.put(f,false);n.put("complete_phase_effects_ready",false);n.put("unavailable_reason",prefix+": "+reason);n.putArray("occurrences");return n;}
}
