package org.xar.ck3.control.wave2.events.eventmaterial;

import static org.xar.ck3.control.wave2.events.eventmaterial.MaterialJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Independent current religion fulfillment; the authored +5 is never substituted for an actual delta. */
public final class RiteGrowthMaterial {
    public static final String EVENT="rite_growth.0010", METRIC="player_religion.spiritual_fulfillment_raw", RELATION="non_decreasing";
    public static final String OBSERVATION_SCHEMA="xar.ck3.rite-growth-fulfillment-observation/v1";
    public static final String GAME_VERSION="1.20.0.4", EXE="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    public static final String SNAPSHOT_FIELD="rite_growth_fulfillment_observation", STARTING_FIELD="starting_rite_growth_fulfillment", ENDING_FIELD="ending_rite_growth_fulfillment";
    private RiteGrowthMaterial() { }
    public enum Status { AVAILABLE, UNAVAILABLE, READY, FAILED, VERIFIED_CHANGE, VERIFIED_NO_CHANGE }
    public record Frame(String snapshotId,BigInteger revision,BigInteger nativeRevision,BigInteger dateRaw,BigInteger characterId) { }
    public record Observation(Status status,Frame frame,BigInteger riteId,BigInteger faithId,BigInteger fulfillmentRaw,BigInteger rawScale,BigInteger captureEpoch,String reason) {
        public Observation { Objects.requireNonNull(status);Objects.requireNonNull(frame);StrictJson.require(status==Status.AVAILABLE||status==Status.UNAVAILABLE,"religion observation status");
            if(status==Status.AVAILABLE)StrictJson.require(availableFrame(frame)&&range(riteId,BigInteger.ZERO,U32)&&range(faithId,BigInteger.ZERO,U32)
                &&range(fulfillmentRaw,I64_MIN,I64_MAX)&&BigInteger.valueOf(100000).equals(rawScale)&&range(captureEpoch,BigInteger.ONE,U64)&&reason==null,"available religion observation requires exact signed raw/full IDs/frame");
            else StrictJson.require(nonempty(reason),"unavailable religion reason"); }
    }
    public record Expectation(Status status,Frame frame,BigInteger startingValue,Observation before,String reason) {
        public Expectation { Objects.requireNonNull(frame);StrictJson.require(status==Status.READY||status==Status.UNAVAILABLE,"material plan status");
            if(status==Status.READY)StrictJson.require(before!=null&&before.status()==Status.AVAILABLE&&frame.equals(before.frame())&&equal(startingValue,before.fulfillmentRaw())&&reason==null,"ready religion expectation must retain actual matching frame"); }
    }
    public record Evaluation(Expectation expectation,Status status,Boolean relationSatisfied,Boolean materialChangeObserved,
                             BigInteger endingValue,BigInteger delta,Observation after,String reason) {
        public Evaluation { Objects.requireNonNull(expectation);Objects.requireNonNull(status); }
    }
    @FunctionalInterface public interface ReligionRead { JsonNode read(BigInteger expectedRevision); }

    /** Exactly one existing religion read for the supplied frame. No mutation API is available. */
    public static Observation capture(ReligionRead reader,JsonNode snapshot) {
        Objects.requireNonNull(reader);BigInteger revision=integer(snapshot,"revision");
        return observe(positive(revision)?reader.read(revision):null,snapshot);
    }
    /** Full base context and query provenance are validated before constructing compact internal values. */
    public static Observation observe(JsonNode query,JsonNode snapshot) {
        JsonNode source=nullableObject(snapshot),actor=nullableObject(get(source,"played_character"));
        Frame frame=new Frame(text(source,"snapshot_id"),integer(source,"revision"),integer(source,"native_revision"),integer(source,"date_raw"),integer(actor,"character_id"));
        Observation unavailable=new Observation(Status.UNAVAILABLE,new Frame(frame.snapshotId(),frame.revision(),frame.nativeRevision(),frame.dateRaw(),null),null,null,null,null,null,"same_frame_rite_growth_religion_unavailable");
        if(query==null||!query.isObject())return unavailable;
        try {
            JsonNode hello=nullableObject(get(nullableObject(get(source,"diagnostics")),"hello"));
            String identitySha=text(hello,"executable_sha256"),querySha=text(query,"executable_sha256");
            boolean base="ck3_12004_religion_context_v1".equals(text(query,"schema"))&&GAME_VERSION.equals(text(query,"game_version"))&&EXE.equals(querySha)
                &&GAME_VERSION.equals(text(hello,"game_version"))&&identitySha!=null&&EXE.equalsIgnoreCase(identitySha)
                &&Boolean.TRUE.equals(bool(query,"available"))&&get(query,"unavailable_reason")!=null&&get(query,"unavailable_reason").isNull()
                &&range(integer(query,"capture_epoch"),BigInteger.ONE,U64)&&equal(integer(query,"date_raw"),frame.dateRaw())&&equal(integer(query,"played_character_id"),frame.characterId())
                &&BigInteger.valueOf(100000).equals(integer(query,"raw_scale"))&&range(integer(query,"spiritual_fulfillment_raw"),I64_MIN,I64_MAX);
            for(String field:java.util.List.of("rite_id","faith_id","religion_id","faith_main_rite_id")) {
                StrictJson.require(query.has(field),"religion context reference field missing: "+field);BigInteger id=integer(query,field);if(id!=null)base&=range(id,BigInteger.ZERO,U32);
            }
            for(String field:java.util.List.of("faith_key","religion_key")){StrictJson.require(query.has(field),"religion context tag missing: "+field);text(query,field);}
            StrictJson.require(query.has("faith_fervor_raw"),"religion context resource missing");BigInteger fervor=integer(query,"faith_fervor_raw");if(fervor!=null)base&=range(fervor,I64_MIN,I64_MAX);
            boolean bound=base&&"ck3-1.20.0.4-native-player-religion-context-v1".equals(text(query,"backend_id"))&&"player_religion_context_v1".equals(text(query,"domain_key"))
                &&Boolean.TRUE.equals(bool(query,"read_only"))&&"observed".equals(text(query,"status"))&&Boolean.TRUE.equals(bool(source,"paused"))&&Boolean.TRUE.equals(bool(source,"map_ready"))
                &&Boolean.TRUE.equals(bool(actor,"alive"))&&availableFrame(frame)&&equal(text(query,"queried_snapshot_id"),frame.snapshotId())&&equal(integer(query,"queried_revision"),frame.revision())
                &&equal(integer(query,"queried_native_revision"),frame.nativeRevision())&&equal(integer(query,"snapshot_revision"),frame.nativeRevision())&&equal(integer(query,"query_date_raw"),frame.dateRaw())
                &&integer(query,"rite_id")!=null&&integer(query,"faith_id")!=null;
            if(!bound)return unavailable;
            return new Observation(Status.AVAILABLE,frame,integer(query,"rite_id"),integer(query,"faith_id"),integer(query,"spiritual_fulfillment_raw"),integer(query,"raw_scale"),integer(query,"capture_epoch"),null);
        } catch(IllegalArgumentException invalid) { return unavailable; }
    }
    /** The composition root adds this detached observation after its real same-frame typed religion read. */
    public static Optional<Expectation> plan(JsonNode decision,JsonNode snapshot) {
        JsonNode raw=get(snapshot,SNAPSHOT_FIELD);Observation before=raw==null||raw.isNull()?null:decodeObservation(raw);
        return plan(decision,snapshot,before);
    }
    public static Optional<Expectation> plan(JsonNode decision,JsonNode snapshot,Observation before) {
        if(!"recommended".equals(text(decision,"status"))||!EVENT.equals(text(decision,"event_definition_key"))||!GAME_VERSION.equals(text(decision,"ck3_build"))
            ||!BigInteger.ZERO.equals(integer(decision,"selected_native_option_index"))||!BigInteger.ONE.equals(integer(decision,"selected_option_number")))return Optional.empty();
        JsonNode actor=nullableObject(get(snapshot,"played_character"));Frame frame=new Frame(text(snapshot,"snapshot_id"),integer(snapshot,"revision"),integer(snapshot,"native_revision"),integer(snapshot,"date_raw"),integer(actor,"character_id"));
        boolean ready=before!=null&&before.status()==Status.AVAILABLE&&frame.equals(before.frame());
        return Optional.of(new Expectation(ready?Status.READY:Status.UNAVAILABLE,frame,ready?before.fulfillmentRaw():null,ready?before:null,ready?null:"same_frame_rite_growth_religion_unavailable"));
    }
    public static Evaluation evaluate(Expectation expected,JsonNode selection) {
        Objects.requireNonNull(expected);
        if(expected.status()!=Status.READY)return new Evaluation(expected,Status.UNAVAILABLE,null,null,null,null,null,expected.reason());
        JsonNode selected=nullableObject(selection),beforeRaw=get(selected,STARTING_FIELD),afterRaw=get(selected,ENDING_FIELD);
        if(beforeRaw==null||beforeRaw.isNull()||afterRaw==null||afterRaw.isNull())return unavailable(expected);
        Observation before=decodeObservation(beforeRaw),after=decodeObservation(afterRaw);
        if(before.status()!=Status.AVAILABLE||after.status()!=Status.AVAILABLE)return unavailable(expected);
        Frame a=before.frame(),b=after.frame();BigInteger old=integer(selected,"old_event_instance_id"),next=integer(selected,"new_event_instance_id");
        boolean bound=BigInteger.ZERO.equals(integer(selected,"selected_native_option_index"))&&BigInteger.ONE.equals(integer(selected,"selected_option_number"))
            &&Boolean.TRUE.equals(bool(selected,"postcondition_verified"))&&positive(old)&&(next==null||positive(next))&&!equal(old,next)
            &&before.equals(expected.before())&&equal(before.fulfillmentRaw(),expected.startingValue())&&equal(a.characterId(),b.characterId())&&equal(a.characterId(),expected.frame().characterId())
            &&equal(a.dateRaw(),b.dateRaw())&&equal(a.dateRaw(),expected.frame().dateRaw())&&equal(before.riteId(),after.riteId())&&equal(before.faithId(),after.faithId())
            &&equal(a.snapshotId(),text(selected,"starting_snapshot_id"))&&equal(a.snapshotId(),expected.frame().snapshotId())&&equal(a.revision(),integer(selected,"starting_revision"))&&equal(a.revision(),expected.frame().revision())
            &&equal(a.nativeRevision(),expected.frame().nativeRevision())&&equal(b.snapshotId(),text(selected,"ending_snapshot_id"))&&!equal(a.snapshotId(),b.snapshotId())
            &&equal(b.revision(),integer(selected,"ending_revision"))&&newer(b.revision(),a.revision())&&newer(b.nativeRevision(),a.nativeRevision())&&newer(after.captureEpoch(),before.captureEpoch());
        if(!bound)return new Evaluation(expected,Status.FAILED,false,false,null,null,null,"rite_growth_material_frame_or_identity_mismatch");
        BigInteger delta=after.fulfillmentRaw().subtract(before.fulfillmentRaw());int sign=delta.signum();
        return new Evaluation(expected,sign>0?Status.VERIFIED_CHANGE:sign==0?Status.VERIFIED_NO_CHANGE:Status.FAILED,sign>=0,sign!=0,after.fulfillmentRaw(),delta,after,sign<0?"spiritual_fulfillment_decreased":null);
    }
    private static boolean availableFrame(Frame f) { return nonempty(f.snapshotId())&&positive(f.revision())&&positive(f.nativeRevision())&&f.dateRaw()!=null&&positive(f.characterId()); }
    private static Evaluation unavailable(Expectation e) { return new Evaluation(e,Status.UNAVAILABLE,null,null,null,null,null,"native_rite_growth_fulfillment_observation_unavailable"); }
    public static byte[] encode(Observation o) { return StrictJson.canonical(observationTree(o)); }
    private static ObjectNode observationTree(Observation o) {
        Frame f=o.frame();return StrictJson.object().put("schema",OBSERVATION_SCHEMA).put("status",o.status()==Status.AVAILABLE?"available":"unavailable")
            .put("game_version",GAME_VERSION).put("executable_sha256",EXE).put("snapshot_id",f.snapshotId()).put("revision",f.revision()).put("native_revision",f.nativeRevision())
            .put("date_raw",f.dateRaw()).put("character_id",f.characterId()).put("rite_id",o.riteId()).put("faith_id",o.faithId()).put("fulfillment_raw",o.fulfillmentRaw())
            .put("raw_scale",o.rawScale()).put("capture_epoch",o.captureEpoch()).put("unavailable_reason",o.reason());
    }
    public static Observation decodeObservation(JsonNode raw) {
        exact(raw,Set.of("schema","status","game_version","executable_sha256","snapshot_id","revision","native_revision","date_raw","character_id","rite_id","faith_id","fulfillment_raw","raw_scale","capture_epoch","unavailable_reason"));
        StrictJson.require(OBSERVATION_SCHEMA.equals(text(raw,"schema"))&&GAME_VERSION.equals(text(raw,"game_version"))&&EXE.equals(text(raw,"executable_sha256")),"exact religion observation/build identity required");
        String status=text(raw,"status");StrictJson.require("available".equals(status)||"unavailable".equals(status),"religion observation status");
        Frame f=new Frame(text(raw,"snapshot_id"),integer(raw,"revision"),integer(raw,"native_revision"),integer(raw,"date_raw"),integer(raw,"character_id"));
        Observation result=new Observation("available".equals(status)?Status.AVAILABLE:Status.UNAVAILABLE,f,integer(raw,"rite_id"),integer(raw,"faith_id"),integer(raw,"fulfillment_raw"),integer(raw,"raw_scale"),integer(raw,"capture_epoch"),text(raw,"unavailable_reason"));sameJson(raw,encode(result));return result;
    }
    public static byte[] encode(Expectation expected) { return StrictJson.canonical(expectationTree(expected)); }
    private static ObjectNode expectationTree(Expectation e) {
        Frame f=e.frame();ObjectNode n=base(EVENT,0,METRIC,RELATION).put("ck3_build",GAME_VERSION).put("status",e.status()==Status.READY?"ready":"unavailable")
            .put("starting_snapshot_id",f.snapshotId()).put("starting_revision",f.revision()).put("starting_native_revision",f.nativeRevision()).put("date_raw",f.dateRaw()).put("character_id",f.characterId())
            .put("starting_value",e.startingValue()).put("unavailable_reason",e.reason());
        if(e.before()==null)n.putNull("starting_religion_observation");else n.set("starting_religion_observation",observationTree(e.before()));return n;
    }
    public static Expectation decodeExpectation(byte[] raw) {
        JsonNode n=StrictJson.parse(raw);validateBase(n,EVENT,0,METRIC,RELATION);StrictJson.require(GAME_VERSION.equals(text(n,"ck3_build")),"exact Rite material build required");
        String status=text(n,"status");StrictJson.require("ready".equals(status)||"unavailable".equals(status),"Rite expectation status");JsonNode before=get(n,"starting_religion_observation");
        Expectation e=new Expectation("ready".equals(status)?Status.READY:Status.UNAVAILABLE,new Frame(text(n,"starting_snapshot_id"),integer(n,"starting_revision"),integer(n,"starting_native_revision"),integer(n,"date_raw"),integer(n,"character_id")),integer(n,"starting_value"),before==null||before.isNull()?null:decodeObservation(before),text(n,"unavailable_reason"));sameJson(n,encode(e));return e;
    }
    public static byte[] encode(Evaluation e) {
        ObjectNode n=expectationTree(e.expectation()).put("status",e.status().name().toLowerCase(java.util.Locale.ROOT)).put("ending_value",e.endingValue()).put("delta",e.delta()).put("unavailable_reason",e.reason());
        nullable(n,"relation_satisfied",e.relationSatisfied());nullable(n,"material_change_observed",e.materialChangeObserved());if(e.after()!=null)n.set("ending_religion_observation",observationTree(e.after()));return StrictJson.canonical(n);
    }
}
