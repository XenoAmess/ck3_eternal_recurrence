package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.*;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** One strict request/result codec for the seven original Driver transport tools. */
public final class ArmyTransportPublicCodec {
    private ArmyTransportPublicCodec() { }
    public static final int MAX_BYTES=8*1024*1024;
    private static final BigInteger SAFE=new BigInteger("9007199254740991");
    public enum Empty { INSTANCE }
    public enum Presence { MISSING,NULL,VALUE }
    public record Subjects(Presence presence,List<Integer> values){public Subjects{Objects.requireNonNull(presence);values=List.copyOf(values);require(presence==Presence.VALUE||values.isEmpty(),"absent subjects cannot carry values");}}
    public record Revision(BigInteger value){public Revision{positive(value);}}
    public record SamplingQuery(ArmyObserverSampling.Family family,Revision revision){public SamplingQuery{Objects.requireNonNull(family);Objects.requireNonNull(revision);}}
    public record SamplingSet(boolean enabled,ArmyObserverSampling.Family family,Revision revision,Subjects subjects){
        public SamplingSet{Objects.requireNonNull(family);Objects.requireNonNull(revision);Objects.requireNonNull(subjects);require(subjects.presence()!=Presence.VALUE||enabled&&family==ArmyObserverSampling.Family.REGULAR_CORE,"subjects only for enabling regular_core");new ArmyObserverSampling.Selection(family,subjects.presence()==Presence.VALUE?Optional.of(subjects.values()):Optional.empty());}
        public ArmyObserverSampling.Selection selection(){return new ArmyObserverSampling.Selection(family,subjects.presence()==Presence.VALUE?Optional.of(subjects.values()):Optional.empty());}
    }
    public record ScalarSet(ArmyPrivateScalarControl.Mode mode,Revision revision){public ScalarSet{Objects.requireNonNull(mode);Objects.requireNonNull(revision);}}
    public static Empty empty(RawJson input){exact(object(input),Set.of());return Empty.INSTANCE;}
    public static Revision revision(RawJson input){var row=object(input);exact(row,Set.of("expected_revision"));return revision(row);}
    public static SamplingQuery samplingQuery(RawJson input){var row=object(input);exact(row,Set.of("observer_family","expected_revision"));return new SamplingQuery(ArmyObserverSampling.Family.parse(text(row,"observer_family")),revision(row));}
    public static SamplingSet samplingSet(RawJson input){var row=object(input);Set<String> keys=keys(row);require(keys.equals(Set.of("enabled","observer_family","expected_revision"))||keys.equals(Set.of("enabled","observer_family","expected_revision","regular_core_full_carmy_ids")),"exact sampling setter fields required");
        var enabled=row.get("enabled");require(enabled!=null&&enabled.isBoolean(),"enabled must be an explicit boolean");Subjects subjects;
        JsonNode value=row.get("regular_core_full_carmy_ids");if(value==null)subjects=new Subjects(Presence.MISSING,List.of());else if(value.isNull())subjects=new Subjects(Presence.NULL,List.of());else{require(value.isArray(),"subject array required");var ids=new ArrayList<Integer>();value.forEach(v->{require(v.isIntegralNumber()&&v.canConvertToInt(),"subject must be signed32 integer");ids.add(v.intValue());});subjects=new Subjects(Presence.VALUE,ids);}
        return new SamplingSet(enabled.booleanValue(),ArmyObserverSampling.Family.parse(text(row,"observer_family")),revision(row),subjects);
    }
    public static ScalarSet scalarSet(RawJson input){var row=object(input);exact(row,Set.of("mode","expected_revision"));String mode=text(row,"mode");var selected=Arrays.stream(ArmyPrivateScalarControl.Mode.values()).filter(v->v.wire().equals(mode)).findFirst().orElseThrow(()->new IllegalArgumentException("scalar mode must be off, compare or use"));return new ScalarSet(selected,revision(row));}
    private static Revision revision(ObjectNode row){JsonNode v=row.get("expected_revision");require(v!=null,"expected_revision required");BigInteger exact;
        if(v.isTextual()){require(v.textValue().matches("[1-9][0-9]{0,19}"),"canonical positive uint64 decimal required");exact=new BigInteger(v.textValue());}
        else{require(v.isIntegralNumber()&&v.bigIntegerValue().compareTo(SAFE)<=0,"legacy revision number must be an exact safe integer");exact=v.bigIntegerValue();}return new Revision(exact);
    }
    public static RawJson scalar(ArmyPrivateScalarControl.State state){var b=state.source();for(BigInteger value:List.of(b.publicRevision(),b.nativeRevision(),b.dateRaw(),b.connectionGeneration()))require(value.signum()>=0&&value.compareTo(NativeWire.UINT64_MAX)<=0,"scalar public identity/time outside uint64");var out=ArmyJson.empty().put("status","configured").put("mode",state.mode().wire()).put("comparison_verified_for_current_identity",state.comparisonVerified()).put("native_capability_advertised",state.nativeCapabilityAdvertised()).put("source_revision",b.publicRevision().toString()).put("source_snapshot_id",b.snapshotId()).put("source_native_revision",b.nativeRevision().toString()).put("source_date_raw",b.dateRaw().toString()).put("game_pid",b.game().pid()).put("connection_generation",b.connectionGeneration().toString()).put("actor_character_id",b.actorCharacterId()).put("episode_run_id",b.episodeRunId().orElseThrow()).put("business_actions_submitted",0);return bounded(new RawJson(ArmyJson.bytes(out)));}
    public static RawJson comparison(ArmyStrengthsService.Reply rich,ArmyPrivateScalarControl.State state){require(state.mode()==ArmyPrivateScalarControl.Mode.COMPARE&&state.comparisonVerified(),"actual retained comparison certificate required");var out=ArmyJson.empty().put("status","same_frame_equal").put("business_actions_submitted",0);out.set("rich_result",ArmyJson.parse(ArmyStrengthsService.encodePublicV2(rich).bytes()));out.set("control",ArmyJson.parse(scalar(state).bytes()));return bounded(new RawJson(ArmyJson.bytes(out)));}
    public static RawJson bounded(RawJson original){require(original.bytes().length<=MAX_BYTES,"transport public result exceeds 8 MiB");var row=object(original);for(String forbidden:List.of("native_command_history","native_rollback_war_failure","native_rollback_war_failures"))require(!row.has(forbidden),"transport private result contains forbidden transcript field");return original;}
    public static RawJson encode(Revision input){return new RawJson(ArmyJson.bytes(ArmyJson.empty().put("expected_revision",input.value().toString())));}
    public static RawJson encode(SamplingQuery input){var n=ArmyJson.parse(encode(input.revision()).bytes());n.put("observer_family",input.family().wire());return new RawJson(ArmyJson.bytes(n));}
    public static RawJson encode(SamplingSet input){var n=ArmyJson.parse(encode(input.revision()).bytes());n.put("enabled",input.enabled()).put("observer_family",input.family().wire());if(input.subjects().presence()==Presence.NULL)n.putNull("regular_core_full_carmy_ids");else if(input.subjects().presence()==Presence.VALUE){var a=n.putArray("regular_core_full_carmy_ids");input.subjects().values().forEach(a::add);}return new RawJson(ArmyJson.bytes(n));}
    public static RawJson encode(ScalarSet input){var n=ArmyJson.parse(encode(input.revision()).bytes());n.put("mode",input.mode().wire());return new RawJson(ArmyJson.bytes(n));}
    private static void positive(BigInteger n){require(n!=null&&n.signum()>0&&n.compareTo(NativeWire.UINT64_MAX)<=0,"positive uint64 revision required");}
    private static ObjectNode object(RawJson input){return ArmyJson.parse(input.bytes());}
    private static Set<String> keys(ObjectNode row){Set<String> actual=new HashSet<>();row.fieldNames().forEachRemaining(actual::add);return actual;}
    private static void exact(ObjectNode row,Set<String> keys){require(keys(row).equals(keys),"exact transport request fields required");}
    private static String text(ObjectNode row,String key){var v=row.get(key);require(v!=null&&v.isTextual(),"transport text required: "+key);return v.textValue();}
}
