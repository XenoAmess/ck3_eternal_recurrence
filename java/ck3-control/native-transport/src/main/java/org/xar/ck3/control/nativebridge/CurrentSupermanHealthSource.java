package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** All forty actual character references and fourteen fixed signed64 values; no rendered UI claim. */
public record CurrentSupermanHealthSource(CurrentSupermanHealth.Phase phase,boolean fixtureStateAvailable,
        Optional<Long> baselineReadyRaw,Optional<Long> matrixDoneRaw,int referenceCount,List<HealthCharacter> characters,
        boolean eventCensusComplete,int namedRootCount,boolean eventFound,boolean namedRootBound,boolean windowVisible,boolean windowEnabled,
        Optional<Integer> instanceId,Optional<Integer> recipientCharacterId,Optional<String> definitionKey,Optional<String> opening,
        Optional<String> description,Optional<Integer> authoredOptionCount,List<HealthOption> options,boolean nativeChoiceAdmissible) {
    public static final List<String> CASE_KEYS=List.of("player-native-health-75","health-flat-75","health-floor-below-3_00074","health-floor-at-3_00075","health-floor-same-day-repeat","health-penalty-mitigation","health-rebuild-idempotent","health-ledger-growth","health-ledger-to-zero","health-upper-balance-block","health-upper-balance-last","health-lower-balance-block","health-lower-balance-last","six-skill-diplomacy-regression","six-skill-prowess-regression","equal-experience-health-no-transfer","only-health-eligible-dispatch","health-zero-receiver","health-negative-receiver","health-reverse-capacity-boundaries");
    public static final List<String> VALUE_NAMES=List.of("sxad_diplomacy_value","sxad_martial_value","sxad_stewardship_value","sxad_intrigue_value","sxad_learning_value","sxad_prowess_value","sxad_health_value","sxad_diplomacy_balance_value","sxad_martial_balance_value","sxad_stewardship_balance_value","sxad_intrigue_balance_value","sxad_learning_balance_value","sxad_prowess_balance_value","sxad_health_balance_value");
    public enum Role {
        RECEIVER("receiver"),DONOR("donor");private final String wire;Role(String wire){this.wire=wire;}public String wire(){return wire;}
        static Role parse(String value)throws IOException{for(var r:values())if(r.wire.equals(value))return r;throw new IOException("Unknown fixed health reference role");}
    }
    public record HealthCharacter(String caseKey,Role role,int characterId,Map<String,Long> values) {
        public HealthCharacter {
            Objects.requireNonNull(caseKey);Objects.requireNonNull(role);values=Map.copyOf(values);
            StrictJson.require(CASE_KEYS.contains(caseKey)&&characterId!=-1,"Actual fixed case and full signed32 ID required; -1 alone is invalid");
            StrictJson.require(values.keySet().equals(Set.copyOf(VALUE_NAMES)),"All fourteen actual typed values are required");
        }
        static HealthCharacter decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("case_key","role","character_id","values"));
            var raw=StrictJson.object(r.get("values"),Set.copyOf(VALUE_NAMES));var values=new LinkedHashMap<String,Long>();
            for(var key:VALUE_NAMES)values.put(key,rawLong(raw.get(key)));
            return new HealthCharacter(NativeWire.text(r.get("case_key")),Role.parse(NativeWire.text(r.get("role"))),i32(r.get("character_id")),values);
        }
        ObjectNode encode(){var r=StrictJson.object().put("case_key",caseKey).put("role",role.wire()).put("character_id",characterId);var v=r.putObject("values");for(var key:VALUE_NAMES)v.put(key,Long.toString(values.get(key)));return r;}
    }
    public record HealthOption(int authoredOptionIndex,String text,String disabledReason,boolean nativeCanSelect,Optional<String> sourceBoundOptionKey) {
        public HealthOption{StrictJson.require(authoredOptionIndex>=0,"Actual authored option index required");nativeText(text);nativeText(disabledReason);Objects.requireNonNull(sourceBoundOptionKey);sourceBoundOptionKey.ifPresent(StrictJson::text);}
        static HealthOption decode(JsonNode node)throws IOException{var r=StrictJson.object(node,Set.of("authored_option_index","text","disabled_reason","native_can_select","source_bound_option_key"));return new HealthOption(i32(r.get("authored_option_index")),CurrentSupermanHealthSource.text(r.get("text")),CurrentSupermanHealthSource.text(r.get("disabled_reason")),bool(r,"native_can_select"),nullableText(r.get("source_bound_option_key")));}
        ObjectNode encode(){var r=StrictJson.object().put("authored_option_index",authoredOptionIndex).put("text",text).put("disabled_reason",disabledReason).put("native_can_select",nativeCanSelect);if(sourceBoundOptionKey.isPresent())r.put("source_bound_option_key",sourceBoundOptionKey.orElseThrow());else r.putNull("source_bound_option_key");return r;}
    }
    public CurrentSupermanHealthSource {
        Objects.requireNonNull(phase);Objects.requireNonNull(baselineReadyRaw);Objects.requireNonNull(matrixDoneRaw);characters=List.copyOf(characters);options=List.copyOf(options);
        Objects.requireNonNull(instanceId);Objects.requireNonNull(recipientCharacterId);Objects.requireNonNull(definitionKey);Objects.requireNonNull(opening);Objects.requireNonNull(description);Objects.requireNonNull(authoredOptionCount);
        StrictJson.require(fixtureStateAvailable&&referenceCount==40&&characters.size()==40&&eventCensusComplete,"Partial fixture/values/census is Unavailable, never a fabricated Source");
        var ids=new HashSet<Integer>();
        for(int i=0;i<40;i++){var c=characters.get(i);StrictJson.require(c.caseKey().equals(CASE_KEYS.get(i/2))&&c.role()==(i%2==0?Role.RECEIVER:Role.DONOR)&&ids.add(c.characterId()),"Forty unique full-ID refs in exact reviewed case/role order required");}
        StrictJson.require(namedRootCount>=0,"Actual census count required");opening.ifPresent(CurrentSupermanHealthSource::nativeText);description.ifPresent(CurrentSupermanHealthSource::nativeText);
        if(!eventFound)StrictJson.require(!namedRootBound&&!windowVisible&&!windowEnabled&&instanceId.isEmpty()&&recipientCharacterId.isEmpty()&&definitionKey.isEmpty()&&opening.isEmpty()&&description.isEmpty()&&authoredOptionCount.isEmpty()&&options.isEmpty()&&!nativeChoiceAdmissible,"Absent fixed event cannot invent material fields or an action");
        else {
            StrictJson.require(namedRootCount>0&&instanceId.filter(i->i>0).isPresent()&&recipientCharacterId.filter(i->i!=-1).isPresent()&&definitionKey.filter(phase.eventKey()::equals).isPresent()&&opening.isPresent()&&description.isPresent()&&authoredOptionCount.filter(i->i>=0).isPresent(),"Present event requires actual fixed identity and full observation");
            var indexes=new HashSet<Integer>();for(var o:options)StrictJson.require(o.authoredOptionIndex()<authoredOptionCount.orElseThrow()&&indexes.add(o.authoredOptionIndex()),"Displayed options must bind distinct actual authored indices");
        }
        if(nativeChoiceAdmissible)StrictJson.require(eventFound&&namedRootBound&&windowVisible&&windowEnabled&&authoredOptionCount.orElseThrow()==1&&options.size()==1&&options.get(0).authoredOptionIndex()==0&&options.get(0).nativeCanSelect()&&options.get(0).sourceBoundOptionKey().filter(phase.optionKey()::equals).isPresent()&&(phase==CurrentSupermanHealth.Phase.BASELINE?baselineReadyRaw:matrixDoneRaw).filter(v->v==100000L).isPresent(),"Known choice requires actual phase marker, sole bound option and NativeCan; no reverse permission inference");
    }
    static CurrentSupermanHealthSource decode(JsonNode node)throws IOException {
        var r=StrictJson.object(node,Set.of("schema","phase","fixture_state_available","baseline_ready_raw","matrix_done_raw","reference_count","characters","event_census_complete","named_root_count","event_found","named_root_bound","window_visible","window_enabled","instance_id","recipient_character_id","definition_key","opening","description","authored_option_count","options","native_choice_admissible"));
        if(!NativeWire.text(r.get("schema")).equals(CurrentSupermanHealth.SOURCE_SCHEMA))throw new IOException("Exact health Source schema required");
        if(!r.get("characters").isArray()||!r.get("options").isArray())throw new IOException("Actual character/options arrays required");
        var chars=new ArrayList<HealthCharacter>();for(var n:r.get("characters"))chars.add(HealthCharacter.decode(n));var options=new ArrayList<HealthOption>();for(var n:r.get("options"))options.add(HealthOption.decode(n));
        return new CurrentSupermanHealthSource(CurrentSupermanHealth.Phase.parse(NativeWire.text(r.get("phase"))),bool(r,"fixture_state_available"),nullableRaw(r.get("baseline_ready_raw")),nullableRaw(r.get("matrix_done_raw")),i32(r.get("reference_count")),chars,bool(r,"event_census_complete"),i32(r.get("named_root_count")),bool(r,"event_found"),bool(r,"named_root_bound"),bool(r,"window_visible"),bool(r,"window_enabled"),nullableI32(r.get("instance_id")),nullableI32(r.get("recipient_character_id")),nullableText(r.get("definition_key")),nullableText(r.get("opening")),nullableText(r.get("description")),nullableI32(r.get("authored_option_count")),options,bool(r,"native_choice_admissible"));
    }
    ObjectNode encode(){
        var r=StrictJson.object().put("schema",CurrentSupermanHealth.SOURCE_SCHEMA).put("phase",phase.wire()).put("fixture_state_available",fixtureStateAvailable).put("reference_count",referenceCount).put("event_census_complete",eventCensusComplete).put("named_root_count",namedRootCount).put("event_found",eventFound).put("named_root_bound",namedRootBound).put("window_visible",windowVisible).put("window_enabled",windowEnabled).put("native_choice_admissible",nativeChoiceAdmissible);
        raw(r,"baseline_ready_raw",baselineReadyRaw);raw(r,"matrix_done_raw",matrixDoneRaw);var c=r.putArray("characters");characters.forEach(v->c.add(v.encode()));var o=r.putArray("options");options.forEach(v->o.add(v.encode()));
        number(r,"instance_id",instanceId);number(r,"recipient_character_id",recipientCharacterId);number(r,"authored_option_count",authoredOptionCount);putText(r,"definition_key",definitionKey);putText(r,"opening",opening);putText(r,"description",description);return r;
    }
    private static long rawLong(JsonNode n)throws IOException{String s=NativeWire.text(n);if(!s.matches("0|-?[1-9][0-9]{0,18}"))throw new IOException("Actual canonical signed64 string required");try{return Long.parseLong(s);}catch(NumberFormatException bad){throw new IOException("Native raw value outside signed64",bad);}}
    private static Optional<Long> nullableRaw(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(rawLong(n));}
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,java.math.BigInteger.valueOf(Integer.MIN_VALUE),java.math.BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static Optional<Integer> nullableI32(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(i32(n));}
    private static String text(JsonNode n)throws IOException{if(!n.isTextual())throw new IOException("Actual UTF8 string required");String s=n.textValue();if(s.getBytes(StandardCharsets.UTF_8).length>16384)throw new IOException("Native text bound exceeded");return s;}
    private static Optional<String> nullableText(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(text(n));}
    private static void nativeText(String s){Objects.requireNonNull(s);StrictJson.require(s.getBytes(StandardCharsets.UTF_8).length<=16384,"Native UTF8 text bound exceeded");}
    private static boolean bool(ObjectNode r,String k)throws IOException{var n=r.get(k);if(!n.isBoolean())throw new IOException("Actual health bool required: "+k);return n.booleanValue();}
    private static void raw(ObjectNode r,String k,Optional<Long> v){if(v.isPresent())r.put(k,Long.toString(v.orElseThrow()));else r.putNull(k);}
    private static void number(ObjectNode r,String k,Optional<Integer> v){if(v.isPresent())r.put(k,v.orElseThrow().intValue());else r.putNull(k);}
    private static void putText(ObjectNode r,String k,Optional<String> v){if(v.isPresent())r.put(k,v.orElseThrow());else r.putNull(k);}
}
