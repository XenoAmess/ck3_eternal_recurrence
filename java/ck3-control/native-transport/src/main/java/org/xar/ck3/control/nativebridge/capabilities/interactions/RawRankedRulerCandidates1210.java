package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Strict DATA boundary for the new raw native-ranked source; no legacy choice, AI acceptance or send qualification. */
public final class RawRankedRulerCandidates1210 {
    public static final String SCHEMA="ck3_1210_ruler_raw_ranked_candidates_v1";
    public static final String STEP="query-ruler-raw-ranked-candidates-v1";
    public static final int MAXIMUM_BYTES=32768,MAXIMUM_ROWS=8,MAXIMUM_WORK_ROWS=4096;
    private static final long U32=4294967295L;
    private static final BigInteger U64=new BigInteger("18446744073709551615");
    private RawRankedRulerCandidates1210() { }
    public record Counter(String decimal) {
        public Counter {
            StrictJson.require(decimal!=null&&decimal.matches("[1-9][0-9]{0,19}")&&new BigInteger(decimal).compareTo(U64)<=0,
                    "positive canonical uint64 decimal string required");
        }
    }
    public record Request(Counter expectedRevision,Counter expectedConnectionGeneration,NativeCharacterId actor,
            long ownedGamePid,int limit) {
        public Request {
            Objects.requireNonNull(expectedRevision);Objects.requireNonNull(expectedConnectionGeneration);Objects.requireNonNull(actor);
            StrictJson.require(ownedGamePid>0&&ownedGamePid<=U32&&limit>=1&&limit<=MAXIMUM_ROWS,"bounded actual PID and native row limit required");
        }
    }
    public record Frame(Counter nativeRevision,Counter connectionGeneration,Counter pumpEpoch,long ownerThreadId,int dateRaw,
            NativeCharacterId actor,NativeCharacterId subject,int localPlayerId,boolean paused,boolean mapReady,boolean actorAlive) {
        public Frame {
            Objects.requireNonNull(nativeRevision);Objects.requireNonNull(connectionGeneration);Objects.requireNonNull(pumpEpoch);
            Objects.requireNonNull(actor);Objects.requireNonNull(subject);
            StrictJson.require(ownerThreadId>0&&ownerThreadId<=U32&&dateRaw>0&&localPlayerId>=0
                    &&actor.equals(subject)&&paused&&mapReady&&actorAlive,"raw source requires its exact paused living actor-as-subject frame");
        }
    }
    public record Row(NativeCharacterId candidate,int nativeCandidateScore) {
        public Row {Objects.requireNonNull(candidate);}
    }
    public record Sample(int nativeTierIndex,int nativeEnumerationCap,int nativeScoringCap,int nativePoolCount,
            int nativeScoredCount,List<Row> rows) {
        public Sample {
            rows=List.copyOf(rows);StrictJson.require(nativeTierIndex>=-1&&nativeTierIndex<=64
                    &&nativeEnumerationCap>=0&&nativeEnumerationCap<=MAXIMUM_WORK_ROWS&&nativeScoringCap>=0&&nativeScoringCap<=MAXIMUM_WORK_ROWS
                    &&nativePoolCount>=0&&nativePoolCount<=MAXIMUM_WORK_ROWS&&nativeScoredCount>=0&&nativeScoredCount<=MAXIMUM_WORK_ROWS
                    &&rows.size()<=MAXIMUM_ROWS&&rows.size()<=nativeScoredCount,"raw adapter work counts outside their actual bounds");
            var unique=new HashSet<NativeCharacterId>();Row prior=null;
            for(var row:rows) {
                StrictJson.require(unique.add(row.candidate()),"duplicate full native candidate identity");
                if(prior!=null)StrictJson.require(prior.nativeCandidateScore()>row.nativeCandidateScore()
                        ||prior.nativeCandidateScore()==row.nativeCandidateScore()
                        &&Integer.compareUnsigned(prior.candidate().value(),row.candidate().value())>0,"raw native ranking order changed");
                prior=row;
            }
        }
    }
    public sealed interface Result permits Partial,Unavailable {
        Counter querySequence();
        default boolean completeContextQualified(){return false;}
        default boolean publicCapabilityReady(){return false;}
    }
    public record Partial(Counter querySequence,Frame frame,Sample sample) implements Result {
        public Partial {
            Objects.requireNonNull(querySequence);Objects.requireNonNull(frame);Objects.requireNonNull(sample);
            for(var row:sample.rows())StrictJson.require(!row.candidate().equals(frame.actor()),"raw source cannot rank the actor as its own spouse");
        }
    }
    public record Unavailable(Counter querySequence,String reason) implements Result {
        public Unavailable {Objects.requireNonNull(querySequence);StrictJson.text(reason);StrictJson.require(reason.length()<=256,"bounded actual native reason required");}
    }
    public static RawJson arguments(Request actual) {
        Objects.requireNonNull(actual);var n=StrictJson.object().put("expected_revision",actual.expectedRevision().decimal())
                .put("expected_connection_generation",actual.expectedConnectionGeneration().decimal()).put("actor_full_id",actual.actor().value())
                .put("owned_game_pid",actual.ownedGamePid()).put("limit",actual.limit());
        return new RawJson(StrictJson.canonical(n));
    }
    /** Fixed new request envelope only. The existing generic transport route is not an installation of this proposal. */
    public static byte[] wireRequest(String requestId,Request actual) throws IOException {
        StrictJson.text(requestId);
        StrictJson.require(requestId.getBytes(StandardCharsets.UTF_8).length<=128
                &&requestId.chars().allMatch(c->c>=0x21&&c<=0x7e&&c!='"'&&c!=0x5c),"bounded unescaped native request ID required");
        var n=StrictJson.object(StrictJson.parse(arguments(actual).bytes()),Set.of("expected_revision","expected_connection_generation","actor_full_id","owned_game_pid","limit"));
        n.put("type","execute_step").put("protocol_version",1).put("request_id",requestId).put("step",STEP);
        return NativeWire.packet(StrictJson.canonical(n));
    }
    public static Result decode(RawJson original,Request actual) {
        Objects.requireNonNull(original);Objects.requireNonNull(actual);
        var n=StrictJson.object(StrictJson.parse(original.bytes(),MAXIMUM_BYTES),Set.of("schema","step","status","read_only","scope","frame","sample",
                "query_sequence","raw_source_available","application_main_observed","same_frame_verified","complete_context_qualified","public_capability_ready","unavailable_reason",
                "game_version","executable_sha256","adapter_id"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(n.get("schema")))&&STEP.equals(StrictJson.text(n.get("step"))),"wrong raw-ranked schema or actual step");
        StrictJson.require(ExactCk3Build.CK3_1210.matches(StrictJson.text(n.get("game_version")),StrictJson.text(n.get("executable_sha256")))
                &&"ck3-1.21.0-msvc-x64".equals(StrictJson.text(n.get("adapter_id"))),"raw source changed its exact configured producer tuple");
        flag(n,"read_only",true);flag(n,"complete_context_qualified",false);flag(n,"public_capability_ready",false);
        var scope=StrictJson.object(n.get("scope"),Set.of("actor_equals_subject","candidate_source"));flag(scope,"actor_equals_subject",true);
        StrictJson.require("current_actor_strategy".equals(StrictJson.text(scope.get("candidate_source"))),"different native candidate source scope");
        var sequence=counter(n.get("query_sequence"));String status=StrictJson.text(n.get("status"));
        if(status.equals("unavailable")) {
            flag(n,"raw_source_available",false);flag(n,"application_main_observed",false);flag(n,"same_frame_verified",false);
            StrictJson.require(n.get("frame").isNull()&&n.get("sample").isNull(),"unavailable raw source cannot retain a stale frame/sample");
            return new Unavailable(sequence,StrictJson.text(n.get("unavailable_reason")));
        }
        StrictJson.require(status.equals("partial"),"only raw partial/unavailable status is defined");
        flag(n,"raw_source_available",true);flag(n,"application_main_observed",true);flag(n,"same_frame_verified",true);
        StrictJson.require(n.get("unavailable_reason").isNull(),"partial raw source reason must be explicit null");
        var f=StrictJson.object(n.get("frame"),Set.of("native_revision","connection_generation","pump_epoch","owner_thread_id","date_raw","actor_full_id",
                "subject_full_id","local_player_id","paused","map_ready","actor_alive"));
        var frame=new Frame(counter(f.get("native_revision")),counter(f.get("connection_generation")),counter(f.get("pump_epoch")),
                StrictJson.integer(f.get("owner_thread_id"),1,U32),(int)StrictJson.integer(f.get("date_raw"),1,Integer.MAX_VALUE),
                NativeCharacterId.fromJson(f.get("actor_full_id")),NativeCharacterId.fromJson(f.get("subject_full_id")),
                (int)StrictJson.integer(f.get("local_player_id"),0,Integer.MAX_VALUE),bool(f,"paused"),bool(f,"map_ready"),bool(f,"actor_alive"));
        StrictJson.require(frame.nativeRevision().equals(actual.expectedRevision())&&frame.connectionGeneration().equals(actual.expectedConnectionGeneration())
                &&frame.actor().equals(actual.actor()),"raw-ranked source crossed requested actor/revision/connection");
        var s=StrictJson.object(n.get("sample"),Set.of("native_tier_index","native_enumeration_cap","native_scoring_cap","native_pool_count","native_scored_count","returned_count","rows"));
        JsonNode values=s.get("rows");StrictJson.require(values.isArray()&&values.size()<=MAXIMUM_ROWS,"bounded native ranked rows required");var rows=new ArrayList<Row>();
        for(var value:values) {var row=StrictJson.object(value,Set.of("candidate_full_id","native_candidate_score"));
            rows.add(new Row(NativeCharacterId.fromJson(row.get("candidate_full_id")),(int)StrictJson.integer(row.get("native_candidate_score"),Integer.MIN_VALUE,Integer.MAX_VALUE)));}
        var sample=new Sample((int)StrictJson.integer(s.get("native_tier_index"),-1,64),work(s,"native_enumeration_cap"),work(s,"native_scoring_cap"),
                work(s,"native_pool_count"),work(s,"native_scored_count"),rows);
        StrictJson.require(StrictJson.integer(s.get("returned_count"),0,MAXIMUM_ROWS)==rows.size()
                &&rows.size()==Math.min(sample.nativeScoredCount(),actual.limit()),"raw source returned count differs from its requested native prefix");
        return new Partial(sequence,frame,sample);
    }
    private static Counter counter(JsonNode value){return new Counter(StrictJson.text(value));}
    private static int work(JsonNode n,String key){return (int)StrictJson.integer(n.get(key),0,MAXIMUM_WORK_ROWS);}
    private static boolean bool(JsonNode n,String key){var v=n.get(key);StrictJson.require(v!=null&&v.isBoolean(),"exact boolean required");return v.booleanValue();}
    private static void flag(JsonNode n,String key,boolean expected){StrictJson.require(bool(n,key)==expected,"raw capability/readiness flag changed: "+key);}
}
