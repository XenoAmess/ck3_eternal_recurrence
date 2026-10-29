package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Closed first-map business DATA. Only the installed live authority can submit this transition. */
public final class ObservedGameplayEntry {
    public static final String KIND="JAVA_OBSERVED_GAMEPLAY_ENTRY_V1";
    public static final String SCHEMA="xar.java.observed-gameplay-entry/v1";
    public static final String SCHEMA_V2="xar.java.observed-gameplay-entry/v2";
    private ObservedGameplayEntry() { }

    public sealed interface Origin permits Origin.StartAfter,Origin.CurrentMap {
        public record StartAfter(ExactRef startAck) implements Origin {
            public StartAfter { Objects.requireNonNull(startAck); }
        }
        public record CurrentMap() implements Origin {
            public CurrentMap { }
        }
    }

    public record Details(String machineId,String sessionId,String episodeId,String snapshotId,
            GameGeneration game,long revision,long dateRaw,long actorId,BigInteger nativeRevision,
            BigInteger connectionGeneration,Origin origin,ExactRef readAck,ExactRef nativeFrame,
            ExactRef fullDriver,ExactRef driverFacts) {
        public Details {
            for(String value:List.of(machineId,sessionId,episodeId,snapshotId))StrictJson.text(value);
            Objects.requireNonNull(game);Objects.requireNonNull(origin);
            StrictJson.safe(revision,1);StrictJson.safe(actorId,1);
            StrictJson.require(dateRaw>=0&&dateRaw<=Integer.MAX_VALUE,"actual bounded native date required");
            for(BigInteger value:List.of(nativeRevision,connectionGeneration))
                StrictJson.require(value.signum()>0&&value.compareTo(StrictJson.UINT64_MAX)<=0,"positive uint64 native identity required");
            StrictJson.require(nativeRevision.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,
                    "canonical continuity native revision must remain in its exact integral JSON domain");
            for(ExactRef ref:List.of(readAck,nativeFrame,fullDriver,driverFacts))
                StrictJson.require(ref.bytes()>0&&ref.bytes()<=WriterContracts.MAX_PIN_BYTES,"bounded original entry material required");
            if(origin instanceof Origin.StartAfter) {
                var startAck=((Origin.StartAfter)origin).startAck();
                StrictJson.require(startAck.bytes()>0&&startAck.bytes()<=WriterContracts.MAX_PIN_BYTES,"bounded original entry material required");
            }
        }
        public Details(String machineId,String sessionId,String episodeId,String snapshotId,
                GameGeneration game,long revision,long dateRaw,long actorId,BigInteger nativeRevision,
                BigInteger connectionGeneration,ExactRef startAck,ExactRef readAck,ExactRef nativeFrame,
                ExactRef fullDriver,ExactRef driverFacts) {
            this(machineId,sessionId,episodeId,snapshotId,game,revision,dateRaw,actorId,nativeRevision,connectionGeneration,
                    new Origin.StartAfter(startAck),readAck,nativeFrame,fullDriver,driverFacts);
        }
        public ExactRef startAck() {
            if(origin instanceof Origin.StartAfter) return ((Origin.StartAfter)origin).startAck();
            throw new IllegalStateException("current map observation has no start ack");
        }
        public List<ExactRef> evidence() {
            return (origin instanceof Origin.StartAfter after
                    ?List.of(after.startAck(),readAck,nativeFrame,fullDriver,driverFacts)
                    :List.of(readAck,nativeFrame,fullDriver,driverFacts)).stream().distinct().toList();
        }
        public WriterContracts.Request request(){return new WriterContracts.Request(KIND,ContinuityJson.canonical(toJson()),evidence());}
        public ObjectNode toJson() {
            var row=StrictJson.object();
            if(origin instanceof Origin.CurrentMap) {
                row.put("schema",SCHEMA_V2);
                row.put("entry_origin","current_map_observation");
            } else {
                row.put("schema",SCHEMA);
            }
            row.put("evidence_id","observed-gameplay-entry:"+sessionId+":"+episodeId);
            var source=row.putObject("source");source.put("machine_id",machineId);source.put("session_id",sessionId);
            row.put("episode_id",episodeId);row.set("game",game.toJson());
            var frame=row.putObject("frame");frame.put("snapshot_id",snapshotId);frame.put("revision",revision);
            frame.put("date_raw",dateRaw);frame.put("player_character_id",actorId);
            frame.put("native_revision",nativeRevision);frame.put("connection_generation",connectionGeneration.toString());
            if(origin instanceof Origin.StartAfter) row.set("start_ack",((Origin.StartAfter)origin).startAck().toJson());
            row.set("read_ack",readAck.toJson());
            row.set("native_frame",nativeFrame.toJson());row.set("full_driver",fullDriver.toJson());row.set("driver_facts",driverFacts.toJson());
            return row;
        }
    }
    public static Details decode(JsonNode value) {
        String schema=StrictJson.text(value.get("schema"));
        boolean legacy=SCHEMA.equals(schema);
        StrictJson.require(legacy||SCHEMA_V2.equals(schema),"exact observed entry version required");
        var row=StrictJson.object(value,legacy
                ?Set.of("schema","evidence_id","source","episode_id","game","frame","start_ack","read_ack","native_frame","full_driver","driver_facts")
                :Set.of("schema","entry_origin","evidence_id","source","episode_id","game","frame","read_ack","native_frame","full_driver","driver_facts"));
        if(!legacy)StrictJson.require("current_map_observation".equals(StrictJson.text(row.get("entry_origin"))),"exact current-map origin required");
        var source=StrictJson.object(row.get("source"),Set.of("machine_id","session_id"));
        var frame=StrictJson.object(row.get("frame"),Set.of("snapshot_id","revision","date_raw","player_character_id","native_revision","connection_generation"));
        Origin origin=legacy?new Origin.StartAfter(ExactRef.fromJson(row.get("start_ack"))):new Origin.CurrentMap();
        var details=new Details(StrictJson.text(source.get("machine_id")),StrictJson.text(source.get("session_id")),StrictJson.text(row.get("episode_id")),
                StrictJson.text(frame.get("snapshot_id")),GameGeneration.fromJson(row.get("game")),
                StrictJson.integer(frame.get("revision"),1,StrictJson.MAX_SAFE_INTEGER),StrictJson.integer(frame.get("date_raw"),0,Integer.MAX_VALUE),
                StrictJson.integer(frame.get("player_character_id"),1,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(frame.get("native_revision"),BigInteger.ONE,StrictJson.UINT64_MAX),
                new BigInteger(new CrossJsDecimalUInt64(StrictJson.text(frame.get("connection_generation"))).decimal()),
                origin,ExactRef.fromJson(row.get("read_ack")),ExactRef.fromJson(row.get("native_frame")),
                ExactRef.fromJson(row.get("full_driver")),ExactRef.fromJson(row.get("driver_facts")));
        StrictJson.require(ContinuityJson.same(details.toJson(),row),"observed entry fields differ from their exact typed encoding");return details;
    }
    public static ContinuityState reduce(ContinuityState before,WriterContracts.Request request,boolean sequenced) {
        StrictJson.require(KIND.equals(request.kind())&&before.status()==ContinuityState.Status.AWAITING_INITIAL_ENTRY,"observed entry initializes only the actual empty business branch");
        var details=decode(request.detailsObject());var next=before.toJson();FreshContinuityGenesis.requirePreEntry(next);
        StrictJson.require(before.machineId().equals(details.machineId()),"observed entry belongs to another machine");
        for(String field:WriterContracts.PRESERVED_RUNTIME_FIELDS)
            if(next.has(field))StrictJson.require(next.get(field).isNull()||next.get(field).isContainerNode()&&next.get(field).isEmpty(),"initial entry cannot absorb pending/UNKNOWN/NEXT: "+field);
        next=FreshContinuityGenesis.observedEntryPredecessor(before,request.detailsObject());
        next.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD,details.fullDriver().toJson());
        next.set(WriterContracts.GAMEPLAY_ENTRY_FIELD,details.toJson());
        if(sequenced){next.put("sequence",Math.addExact(before.sequence(),1));next.put("last_event_identity",request.identity());}
        return ContinuityState.fromJson(next,before.machineId());
    }
    public static void requireReduction(ContinuityState before,ContinuityState after,WriterContracts.Request request,boolean sequenced) {
        StrictJson.require(ContinuityJson.same(reduce(before,request,sequenced).toJson(),after.toJson()),"observed entry may publish only its exact actual first-map business binding");
    }
}