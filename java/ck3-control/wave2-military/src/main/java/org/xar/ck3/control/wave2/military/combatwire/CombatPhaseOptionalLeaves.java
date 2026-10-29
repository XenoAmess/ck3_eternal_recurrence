package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatLeafWire.*;
import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;

/** Actual phase optional normalizers. Diagnostics never grant base combat readiness. */
public final class CombatPhaseOptionalLeaves implements CombatOptionalLeaves {
    private static final List<String> CHANCE_TRAITS=List.of("wrathful","giant","impatient","sadistic","brave","ambitious","content","compassionate","temperate","lazy","patient","wounded_1","wounded_2","wounded_3","one_legged","disfigured","one_eyed","maimed");
    @Override public JsonNode normalize(Leaf leaf,JsonNode value,Context context){
        if(nil(value))return NullNode.instance;
        return switch(leaf){
            case PHASE_RITE_PARAMETERS -> rite(value,context.expectedCharacterId());
            case PHASE_WARMONGER_CORE -> warmonger(value,context.expectedCharacterId());
            case PHASE_BERSERKER_VALIDITY -> validity(value,context.expectedCharacterId());
            case PHASE_BERSERKER_CHANCE -> chance(value,context.expectedCharacterId());
            case PHASE_EVENT_CALENDAR,PHASE_EVENT_ROLE_COMPATIBILITY,PHASE_EVENT_COMMANDER_SIDE_IDENTITY,PHASE_EVENT_COMMANDER_TRIGGER,PHASE_EVENT_COMMANDER_CHANCE -> CombatRosterLeaves.normalize(leaf,value,context);
            default -> throw new IllegalArgumentException("physical combat leaf routed to phase owner: "+leaf);
        };
    }
    public static ObjectNode rite(JsonNode value,Integer expected){
        ObjectNode n=obj(value,"status source_character_id raw_adopted_rite_id rite_id faith_id boolean_parameters_complete boolean_parameter_keys unavailable_reason");sourceCharacter(n,expected);
        String s=token(n.get("status"),"status","available","absent","unavailable");long raw=u32(n.get("raw_adopted_rite_id"),"raw_adopted_rite_id");Long rite=ref(n.get("rite_id"),"rite_id"),faith=ref(n.get("faith_id"),"faith_id");boolean complete=bool(n.get("boolean_parameters_complete"),"boolean_parameters_complete");List<String> keys=strings(n.get("boolean_parameter_keys"),"boolean_parameter_keys");require(new HashSet<>(keys).size()==keys.size(),"Rite Boolean keys contain duplicates");String reason=nullableText(n.get("unavailable_reason"),"unavailable_reason");require(rite==null||rite==raw,"resolved Rite differs from raw reference");
        if(s.equals("available"))require(raw!=U32&&rite!=null&&complete&&reason==null,"available Rite incomplete");
        else if(s.equals("absent"))require(raw==U32&&rite==null&&faith==null&&!complete&&keys.isEmpty()&&reason==null,"absent Rite inconsistent");
        else require(!complete&&keys.isEmpty()&&reason!=null,"unavailable Rite requires incomplete empty keys and reason");return n.deepCopy();
    }
    public static ObjectNode warmonger(JsonNode value,Integer expected){
        ObjectNode n=obj(value,"status source_character_id raw_adopted_rite_id rite_id rite_resolution requested_tenet_key target_tenet_key warmonger_core_membership unavailable_reason");sourceCharacter(n,expected);long raw=u32(n.get("raw_adopted_rite_id"),"raw_adopted_rite_id");Long rite=ref(n.get("rite_id"),"rite_id");require(rite==null||rite==raw,"resolved Rite differs");String resolution=token(n.get("rite_resolution"),"rite_resolution","unresolved","adopted","native_fallback");require(resolution.equals("adopted")== (rite!=null),"Rite resolution differs");eq(n.get("requested_tenet_key"),"tenet_warmonger","requested Tenet differs");require(nil(n.get("target_tenet_key"))||n.get("target_tenet_key").isTextual()&&n.get("target_tenet_key").textValue().equals("tenet_warmonger"),"resolved Tenet differs");Boolean member=nb(n.get("warmonger_core_membership"),"warmonger_core_membership");String s=state(n,"available","unavailable");require(!s.equals("available")||resolution.equals("adopted")&&!nil(n.get("target_tenet_key"))&&member!=null,"available warmonger incomplete");require(!s.equals("unavailable")||member==null,"unavailable warmonger requires null membership");return n.deepCopy();
    }
    public static ObjectNode validity(JsonNode value,Integer expected){
        ObjectNode n=obj(value,"source_character_id culture religion traits");sourceCharacter(n,expected);
        ObjectNode culture=obj(n.get("culture"),"status raw_culture_id culture_id resolution selected_pillar_keys heritage_north_germanic unavailable_reason");long raw=u32(culture.get("raw_culture_id"),"raw_culture_id");Long resolved=ref(culture.get("culture_id"),"culture_id");resolution(token(culture.get("resolution"),"resolution","resolved","native_fallback","unresolved"),raw,resolved,false);String cs=state(culture,"available","unavailable");Boolean heritage=nb(culture.get("heritage_north_germanic"),"heritage_north_germanic");require(cs.equals("available")== (heritage!=null),"culture Boolean/status differs");
        if(cs.equals("available")){List<String> keys=boundedStrings(culture.get("selected_pillar_keys"),5,false);require(resolved!=null&&heritage==keys.contains("heritage_north_germanic"),"culture actual heritage differs");}else require(nil(culture.get("selected_pillar_keys")),"unavailable culture must null selected keys");
        ObjectNode religion=obj(n.get("religion"),"status raw_adopted_rite_id rite_id raw_faith_id faith_id raw_religion_id religion_id resolution religion_key germanic unavailable_reason");
        for(String[] pair:List.of(new String[]{"raw_adopted_rite_id","rite_id"},new String[]{"raw_faith_id","faith_id"},new String[]{"raw_religion_id","religion_id"})){Long r=pair[0].equals("raw_adopted_rite_id")?Long.valueOf(u32(religion.get(pair[0]),pair[0])):nr(religion.get(pair[0]),0,U32,pair[0]);Long id=ref(religion.get(pair[1]),pair[1]);require(id==null||id.equals(r),"religion chain differs from raw reference");}
        String rr=token(religion.get("resolution"),"resolution","resolved","native_fallback","unresolved");require(rr.equals("resolved")== !nil(religion.get("religion_id")),"religion resolution differs");require(nil(religion.get("faith_id"))||!nil(religion.get("rite_id")),"Faith requires Rite");require(nil(religion.get("religion_id"))||!nil(religion.get("faith_id")),"Religion requires Faith");String rs=state(religion,"available","unavailable");Boolean germanic=nb(religion.get("germanic"),"germanic");require(rs.equals("available")== (germanic!=null),"religion Boolean/status differs");
        if(rs.equals("available")){require(religion.get("religion_key").isTextual(),"available Religion requires actual key");String key=religion.get("religion_key").textValue();require(key.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=4096&&rr.equals("resolved")&&germanic==key.equals("germanic_religion"),"Religion key/germanic differs");}else require(nil(religion.get("religion_key")),"unavailable Religion cannot invent key");
        ObjectNode traits=obj(n.get("traits"),"craven berserker calm");for(String k:List.of("craven","berserker","calm"))boolObservation(traits.get(k));return n.deepCopy();
    }
    public static ObjectNode chance(JsonNode value,Integer expected){
        ObjectNode n=obj(value,"source_character_id is_ai stalwart dynasty acclaimed traits");sourceCharacter(n,expected);boolObservation(n.get("is_ai"));perk(n.get("stalwart"),"stalwart_leader_perk");
        ObjectNode d=obj(n.get("dynasty"),"raw_house_id house_id raw_dynasty_id dynasty_id house_resolution dynasty_resolution warfare_legacy_3");
        for(String kind:List.of("house","dynasty")){Long raw=kind.equals("house")?Long.valueOf(u32(d.get("raw_"+kind+"_id"),"raw house")):nr(d.get("raw_"+kind+"_id"),0,U32,"raw dynasty");Long resolved=ref(d.get(kind+"_id"),kind+"_id");resolution(token(d.get(kind+"_resolution"),kind+"_resolution","resolved","unresolved","absent","native_fallback"),raw,resolved,true);}
        require(nil(d.get("dynasty_id"))||!nil(d.get("house_id")),"Dynasty requires House");ObjectNode warfare=perk(d.get("warfare_legacy_3"),"warfare_legacy_3");Boolean owned=nb(warfare.path("presence").get("value"),"warfare presence");String dr=d.get("dynasty_resolution").textValue();require(owned==null||List.of("resolved","absent").contains(dr),"warfare requires resolved/absent Dynasty");require(!Boolean.TRUE.equals(owned)||dr.equals("resolved"),"absent Dynasty cannot own warfare");
        ObjectNode a=obj(n.get("acclaimed"),"raw_accolade_id accolade_id resolution is_acclaimed");Long raw=nr(a.get("raw_accolade_id"),0,U32,"raw_accolade_id"),id=ref(a.get("accolade_id"),"accolade_id");String ar=token(a.get("resolution"),"resolution","resolved","unresolved","absent","native_fallback");resolution(ar,raw,id,true);ObjectNode acclaim=boolObservation(a.get("is_acclaimed"));Boolean observed=nb(acclaim.get("value"),"is_acclaimed");require(observed==null||ar.equals(observed?"resolved":"absent"),"acclaimed differs from actual identity");ObjectNode t=obj(n.get("traits"),String.join(" ",CHANCE_TRAITS));for(String key:CHANCE_TRAITS)boolObservation(t.get(key));return n.deepCopy();
    }
}
