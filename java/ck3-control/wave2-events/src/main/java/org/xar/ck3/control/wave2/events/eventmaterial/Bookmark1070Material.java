package org.xar.ck3.control.wave2.events.eventmaterial;

import static org.xar.ck3.control.wave2.events.eventmaterial.MaterialJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** The existing .1070.c roster/core observation path. A net manpower gain is never spawn proof. */
public final class Bookmark1070Material {
    public static final String EVENT="bookmark.1070", METRIC="player_armies.bookmark1070_spawn", RELATION="new_army_source_shape";
    public static final String OBSERVATION_SCHEMA="xar.ck3.bookmark1070-army-observation/v1";
    private Bookmark1070Material() { }
    public enum Status { AVAILABLE, UNAVAILABLE, READY, FAILED, VERIFIED_CHANGE }
    public record Frame(BigInteger characterId, BigInteger dateRaw, String snapshotId, BigInteger revision,
                        BigInteger nativeRevision, String episodeRunId, BigInteger bridgePid, BigInteger connectionGeneration) {
        public boolean valid() { return i32(characterId,1)&&i32(dateRaw,0)&&i32(revision,0)&&i32(nativeRevision,0)
            &&i32(bridgePid,1)&&i32(connectionGeneration,0)&&nonempty(snapshotId)&&nonempty(episodeRunId); }
    }
    public record Army(BigInteger armyId, BigInteger ownerCharacterId, BigInteger currentProvinceId) { }
    public record Regiment(BigInteger armyRegimentId, BigInteger currentSoldiers, BigInteger maximumSoldiers,
                           BigInteger scale, String maaTypeStatus, String maaTypeKey, String compositionUnavailableReason) { }
    public record Strength(String status, BigInteger armyId, BigInteger nativeCarmyId, BigInteger regimentCount,
                           BigInteger currentSoldiers, BigInteger maximumSoldiers, String unavailableReason, List<Regiment> regiments) {
        public Strength { if(regiments!=null)regiments=List.copyOf(regiments); }
    }
    public record Observation(Status status, Frame frame, List<Army> armies, List<Strength> strengths, String reason) {
        public Observation {
            Objects.requireNonNull(status); Objects.requireNonNull(frame);
            StrictJson.require(status==Status.AVAILABLE||status==Status.UNAVAILABLE,"observation status");
            if(armies!=null)armies=List.copyOf(armies); if(strengths!=null)strengths=List.copyOf(strengths);
            if(status==Status.AVAILABLE) StrictJson.require(frame.valid()&&armies!=null&&reason==null,"available army observation binding");
            else StrictJson.require(nonempty(reason),"unavailable observation diagnosis");
        }
    }
    public record Expectation(Status status, Observation before, BigInteger oldEventInstanceId, String reason) {
        public Expectation {
            Objects.requireNonNull(before); StrictJson.require(status==Status.READY||status==Status.UNAVAILABLE,"expectation status");
            StrictJson.require(status!=Status.READY||(before.status()==Status.AVAILABLE&&i32(oldEventInstanceId,1)&&reason==null),"ready spawn before frame");
        }
    }
    public record Composition(String key, BigInteger soldiers) { }
    public record Evaluation(Expectation expectation, Status status, Boolean relationSatisfied, Boolean materialChangeObserved,
                             BigInteger newArmyId, BigInteger nativeCarmyId, List<Composition> composition,
                             BigInteger currentSoldiers, BigInteger maximumSoldiers, String reason) {
        public Evaluation { Objects.requireNonNull(expectation); Objects.requireNonNull(status); if(composition!=null)composition=List.copyOf(composition); }
    }

    /** Supplied strengths come from the existing read-only core query; this leaf never queries or submits. */
    public static Observation observe(JsonNode snapshot, JsonNode armyStrengths, List<BigInteger> beforeArmyIds) {
        JsonNode source=nullableObject(snapshot), player=nullableObject(get(source,"played_character")), diagnostics=nullableObject(get(source,"diagnostics"));
        Frame frame=new Frame(integer(player,"character_id"),integer(source,"date_raw"),text(source,"snapshot_id"),integer(source,"revision"),
            integer(source,"native_revision"),text(source,"episode_run_id"),integer(diagnostics,"bridge_pid"),integer(diagnostics,"connection_generation"));
        String missing="bookmark1070_player_army_frame_unavailable";
        if(!Boolean.TRUE.equals(bool(source,"paused"))||!Boolean.TRUE.equals(bool(source,"map_ready"))
            ||!Boolean.TRUE.equals(bool(player,"alive"))||!frame.valid()) return new Observation(Status.UNAVAILABLE,frame,null,null,missing);
        List<JsonNode> raw=rows(get(source,"player_armies")); if(raw==null)return new Observation(Status.UNAVAILABLE,frame,null,null,missing);
        List<Army> armies=new ArrayList<>(); Set<BigInteger> seen=new HashSet<>();
        for(JsonNode row:raw) {
            if(row==null||!row.isObject())return new Observation(Status.UNAVAILABLE,frame,null,null,missing);
            BigInteger id=integer(row,"army_id"),owner=integer(row,"owner_character_id");
            if(!i32(id,0)||!i32(owner,1)||!seen.add(id))return new Observation(Status.UNAVAILABLE,frame,null,null,missing);
            armies.add(new Army(id,owner,integer(row,"current_province_id")));
        }
        JsonNode rawStrengths=armyStrengths!=null&&armyStrengths.isObject()?armyStrengths.get("army_strengths"):armyStrengths;
        List<JsonNode> strengthRows=rows(rawStrengths); List<Strength> strengths=null;
        if(strengthRows!=null) {
            Set<BigInteger> prior=beforeArmyIds==null?Set.of():Set.copyOf(beforeArmyIds); Set<BigInteger> wanted=new HashSet<>();
            for(Army army:armies)if(army.ownerCharacterId().equals(frame.characterId())&&!prior.contains(army.armyId()))wanted.add(army.armyId());
            strengths=new ArrayList<>(); for(JsonNode row:strengthRows)
                if(row.isObject()&&wanted.contains(integer(row,"army_id")))strengths.add(strength(row));
        }
        return new Observation(Status.AVAILABLE,frame,armies,strengths,null);
    }
    public static Optional<Expectation> plan(JsonNode decision, JsonNode snapshot) {
        if(!"recommended".equals(text(decision,"status"))||!EVENT.equals(text(decision,"event_definition_key"))
            ||!"1.20.0.4".equals(text(decision,"ck3_build"))||!BigInteger.TWO.equals(integer(decision,"selected_native_option_index")))return Optional.empty();
        JsonNode profile=nullableObject(get(decision,"choice_effect_profile")),spec=nullableObject(get(profile,"observable_postcondition"));
        ObjectNode actual=StrictJson.object().put("metric",METRIC).put("expected_relation",RELATION).put("material_change_required_for_evidence",true);
        if(!actual.equals(spec))return Optional.empty();
        Observation before=observe(snapshot,null,null); JsonNode event=nullableObject(get(snapshot,"active_event")); BigInteger instance=integer(event,"instance_id");
        boolean ready=before.status()==Status.AVAILABLE&&i32(instance,1);
        return Optional.of(new Expectation(ready?Status.READY:Status.UNAVAILABLE,before,instance,ready?null:"bookmark1070_before_armies_unavailable"));
    }
    public static Evaluation evaluate(Expectation expected, JsonNode selection) {
        Objects.requireNonNull(expected);
        if(expected.status()!=Status.READY)return reject(expected,expected.reason()==null?"bookmark1070_expectation_not_ready":expected.reason(),false);
        JsonNode selected=nullableObject(selection),beforeRaw=get(selected,"starting_bookmark1070_armies"),afterRaw=get(selected,"ending_bookmark1070_armies");
        if(beforeRaw==null||beforeRaw.isNull()||afterRaw==null||afterRaw.isNull())return unavailable(expected);
        Observation before=decodeObservation(beforeRaw),after=decodeObservation(afterRaw);
        if(before.status()!=Status.AVAILABLE||after.status()!=Status.AVAILABLE||!before.frame().valid()||!after.frame().valid())return unavailable(expected);
        Frame a=before.frame(),b=after.frame();
        boolean bound=before.equals(expected.before())&&"event_instance_advanced".equals(text(selected,"status"))&&Boolean.TRUE.equals(bool(selected,"postcondition_verified"))
            &&BigInteger.TWO.equals(integer(selected,"selected_native_option_index"))&&equal(integer(selected,"old_event_instance_id"),expected.oldEventInstanceId())
            &&!equal(integer(selected,"new_event_instance_id"),expected.oldEventInstanceId())
            &&equal(a.episodeRunId(),b.episodeRunId())&&equal(a.episodeRunId(),text(selected,"episode_run_id"))
            &&equal(a.bridgePid(),b.bridgePid())&&equal(a.bridgePid(),integer(selected,"bridge_pid"))
            &&equal(a.connectionGeneration(),b.connectionGeneration())&&equal(a.connectionGeneration(),integer(selected,"connection_generation"))
            &&equal(a.characterId(),b.characterId())&&equal(a.characterId(),expected.before().frame().characterId())&&equal(a.dateRaw(),b.dateRaw())
            &&equal(a.snapshotId(),text(selected,"starting_snapshot_id"))&&equal(b.snapshotId(),text(selected,"ending_snapshot_id"))&&!equal(a.snapshotId(),b.snapshotId())
            &&equal(a.revision(),integer(selected,"starting_revision"))&&equal(b.revision(),integer(selected,"ending_revision"))&&newer(b.revision(),a.revision())&&newer(b.nativeRevision(),a.nativeRevision());
        if(!bound)return reject(expected,"bookmark1070_army_frame_binding_mismatch",true);
        if(before.armies()==null||after.armies()==null)return unavailable(expected);
        Set<BigInteger> prior=new HashSet<>();before.armies().forEach(row->prior.add(row.armyId()));
        List<Army> candidates=after.armies().stream().filter(row->!prior.contains(row.armyId())&&equal(row.ownerCharacterId(),a.characterId())).toList();
        if(candidates.size()!=1)return reject(expected,"bookmark1070_unique_new_player_army_not_observed",true);
        BigInteger id=candidates.getFirst().armyId(); List<Strength> matches=after.strengths()==null?List.of():after.strengths().stream().filter(row->equal(row.armyId(),id)).toList();
        if(matches.size()!=1||!"available".equals(matches.getFirst().status()))return unavailable(expected);
        Strength strength=matches.getFirst();BigInteger nativeId=strength.nativeCarmyId();
        if(!range(nativeId,BigInteger.valueOf(Integer.MIN_VALUE),I32)||BigInteger.valueOf(-1).equals(nativeId))return reject(expected,"bookmark1070_new_army_identity_unavailable",false);
        CompositionResult composition=composition(strength);if(composition.values()==null)return reject(expected,composition.reason(),false);
        Map<String,BigInteger> wanted=Map.of("non_maa",BigInteger.valueOf(125),"bowmen",BigInteger.valueOf(50),"light_horsemen",BigInteger.valueOf(50),"armored_horsemen",BigInteger.valueOf(25));
        boolean matched=wanted.equals(composition.values())&&BigInteger.valueOf(250).equals(strength.currentSoldiers())&&BigInteger.valueOf(250).equals(strength.maximumSoldiers());
        return new Evaluation(expected,matched?Status.VERIFIED_CHANGE:Status.FAILED,matched,matched,id,nativeId,
            composition.values().entrySet().stream().map(row->new Composition(row.getKey(),row.getValue())).toList(),strength.currentSoldiers(),strength.maximumSoldiers(),matched?null:"bookmark1070_new_army_source_shape_mismatch");
    }
    private record CompositionResult(Map<String,BigInteger> values,String reason) { }
    private static CompositionResult composition(Strength strength) {
        if(!"available".equals(strength.status())||strength.regiments()==null||!i32(strength.regimentCount(),0)
            ||!BigInteger.valueOf(strength.regiments().size()).equals(strength.regimentCount()))return new CompositionResult(null,"bookmark1070_new_army_regiments_unavailable");
        Map<String,BigInteger> result=new LinkedHashMap<>();Set<BigInteger> seen=new HashSet<>();BigInteger current=BigInteger.ZERO,maximum=BigInteger.ZERO;
        for(Regiment row:strength.regiments()) {
            if(!i32(row.armyRegimentId(),0)||!seen.add(row.armyRegimentId())||!i32(row.currentSoldiers(),0)||!i32(row.maximumSoldiers(),0)||!BigInteger.ONE.equals(row.scale()))
                return new CompositionResult(null,"bookmark1070_new_army_regiments_unavailable");
            String key=row.maaTypeKey();if("absent".equals(row.maaTypeStatus())&&key==null)key="non_maa";
            else if(!"available".equals(row.maaTypeStatus())||!nonempty(key))return new CompositionResult(null,"bookmark1070_new_army_type_unavailable");
            if(row.compositionUnavailableReason()!=null)return new CompositionResult(null,"bookmark1070_new_army_type_unavailable");
            result.merge(key,row.currentSoldiers(),BigInteger::add);current=current.add(row.currentSoldiers());maximum=maximum.add(row.maximumSoldiers());
        }
        if(!equal(current,strength.currentSoldiers())||!equal(maximum,strength.maximumSoldiers()))return new CompositionResult(null,"bookmark1070_new_army_regiment_aggregate_mismatch");
        return new CompositionResult(Map.copyOf(result),null);
    }
    private static Evaluation unavailable(Expectation e) { return reject(e,"bookmark1070_army_observation_unavailable",false); }
    private static Evaluation reject(Expectation e,String reason,boolean failed) { return new Evaluation(e,failed?Status.FAILED:Status.UNAVAILABLE,failed?false:null,failed?false:null,null,null,null,null,null,reason); }
    private static Strength strength(JsonNode node) {
        List<JsonNode> raw=rows(get(node,"regiment_strengths"));List<Regiment> regiments=null;
        if(raw!=null){regiments=new ArrayList<>();for(JsonNode row:raw){
            if(row==null||!row.isObject())return new Strength(text(node,"status"),integer(node,"army_id"),integer(node,"native_carmy_id"),integer(node,"regiment_count"),integer(node,"current_soldiers"),integer(node,"maximum_soldiers"),text(node,"unavailable_reason"),null);
            regiments.add(new Regiment(integer(row,"army_regiment_id"),integer(row,"current_soldiers"),integer(row,"maximum_soldiers"),integer(row,"scale"),text(row,"maa_type_status"),text(row,"maa_type_key"),text(row,"composition_unavailable_reason")));}}
        return new Strength(text(node,"status"),integer(node,"army_id"),integer(node,"native_carmy_id"),integer(node,"regiment_count"),integer(node,"current_soldiers"),integer(node,"maximum_soldiers"),text(node,"unavailable_reason"),regiments);
    }
    public static byte[] encode(Observation observation) { return StrictJson.canonical(observationTree(observation)); }
    public static Observation decodeObservation(JsonNode raw) {
        exact(raw,Set.of("schema","status","character_id","date_raw","snapshot_id","revision","native_revision","episode_run_id","bridge_pid","connection_generation","player_armies","army_strengths","unavailable_reason"));
        StrictJson.require(OBSERVATION_SCHEMA.equals(text(raw,"schema")),"exact army observation schema");
        Frame frame=new Frame(integer(raw,"character_id"),integer(raw,"date_raw"),text(raw,"snapshot_id"),integer(raw,"revision"),integer(raw,"native_revision"),text(raw,"episode_run_id"),integer(raw,"bridge_pid"),integer(raw,"connection_generation"));
        List<JsonNode> armyRows=rows(get(raw,"player_armies"));List<Army> armies=null;
        if(armyRows!=null){armies=new ArrayList<>();Set<BigInteger> ids=new HashSet<>();for(JsonNode row:armyRows){exact(row,Set.of("army_id","owner_character_id","current_province_id"));BigInteger id=integer(row,"army_id"),owner=integer(row,"owner_character_id");StrictJson.require(i32(id,0)&&i32(owner,1)&&ids.add(id),"full distinct army ids required");armies.add(new Army(id,owner,integer(row,"current_province_id")));}}
        List<JsonNode> strengthRows=rows(get(raw,"army_strengths"));List<Strength> strengths=null;if(strengthRows!=null){strengths=new ArrayList<>();for(JsonNode row:strengthRows)strengths.add(strength(row));}
        String status=text(raw,"status");StrictJson.require("available".equals(status)||"unavailable".equals(status),"observation status");
        Observation result=new Observation("available".equals(status)?Status.AVAILABLE:Status.UNAVAILABLE,frame,armies,strengths,text(raw,"unavailable_reason"));sameJson(raw,encode(result));return result;
    }
    public static Expectation decodeExpectation(byte[] raw) {
        JsonNode node=StrictJson.parse(raw);validateBase(node,EVENT,2,METRIC,RELATION);
        Observation before=decodeObservation(get(node,"before_army_observation"));String status=text(node,"status");
        StrictJson.require("ready".equals(status)||"unavailable".equals(status),"expectation status");
        Expectation result=new Expectation("ready".equals(status)?Status.READY:Status.UNAVAILABLE,before,integer(node,"old_event_instance_id"),text(node,"unavailable_reason"));sameJson(node,encode(result));return result;
    }
    public static byte[] encode(Expectation e) {
        Frame f=e.before().frame();ObjectNode node=base(EVENT,2,METRIC,RELATION).put("status",e.status()==Status.READY?"ready":"unavailable")
            .put("character_id",f.characterId()).put("starting_snapshot_id",f.snapshotId()).put("starting_revision",f.revision()).put("old_event_instance_id",e.oldEventInstanceId())
            .put("source_expected_levies",125).put("expected_current_soldiers",250).put("unavailable_reason",e.reason());node.set("before_army_observation",observationTree(e.before()));return StrictJson.canonical(node);
    }
    public static byte[] encode(Evaluation e) {
        Frame f=e.expectation().before().frame();ObjectNode n=base(EVENT,2,METRIC,RELATION).put("starting_snapshot_id",f.snapshotId()).put("starting_revision",f.revision()).put("character_id",f.characterId())
            .put("status",e.status().name().toLowerCase(java.util.Locale.ROOT)).put("new_army_id",e.newArmyId()).put("native_carmy_id",e.nativeCarmyId())
            .put("source_expected_levies",125).put("levy_type_identity_observed",false).put("total_army_net_gain_used",false).put("unavailable_reason",e.reason());
        nullable(n,"relation_satisfied",e.relationSatisfied());nullable(n,"material_change_observed",e.materialChangeObserved());
        if(e.composition()==null)n.putNull("observed_composition");else {ObjectNode composition=n.putObject("observed_composition");e.composition().forEach(row->composition.put(row.key(),row.soldiers()));n.put("observed_current_soldiers",e.currentSoldiers()).put("observed_maximum_soldiers",e.maximumSoldiers());}
        return StrictJson.canonical(n);
    }
    private static ObjectNode observationTree(Observation o) {
        Frame f=o.frame();ObjectNode n=StrictJson.object().put("schema",OBSERVATION_SCHEMA).put("status",o.status()==Status.AVAILABLE?"available":"unavailable")
            .put("character_id",f.characterId()).put("date_raw",f.dateRaw()).put("snapshot_id",f.snapshotId()).put("revision",f.revision()).put("native_revision",f.nativeRevision())
            .put("episode_run_id",f.episodeRunId()).put("bridge_pid",f.bridgePid()).put("connection_generation",f.connectionGeneration()).put("unavailable_reason",o.reason());
        if(o.armies()==null)n.putNull("player_armies");else{ArrayNode a=n.putArray("player_armies");o.armies().forEach(row->a.addObject().put("army_id",row.armyId()).put("owner_character_id",row.ownerCharacterId()).put("current_province_id",row.currentProvinceId()));}
        if(o.strengths()==null)n.putNull("army_strengths");else{ArrayNode a=n.putArray("army_strengths");for(Strength s:o.strengths()){
            ObjectNode r=a.addObject().put("status",s.status()).put("army_id",s.armyId()).put("native_carmy_id",s.nativeCarmyId()).put("regiment_count",s.regimentCount()).put("current_soldiers",s.currentSoldiers()).put("maximum_soldiers",s.maximumSoldiers()).put("unavailable_reason",s.unavailableReason());
            if(s.regiments()==null)r.putNull("regiment_strengths");else{ArrayNode regs=r.putArray("regiment_strengths");s.regiments().forEach(reg->regs.addObject().put("army_regiment_id",reg.armyRegimentId()).put("current_soldiers",reg.currentSoldiers()).put("maximum_soldiers",reg.maximumSoldiers()).put("scale",reg.scale()).put("maa_type_status",reg.maaTypeStatus()).put("maa_type_key",reg.maaTypeKey()).put("composition_unavailable_reason",reg.compositionUnavailableReason()));}
        }}return n;
    }
}
