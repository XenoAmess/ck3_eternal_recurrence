package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Closed partial observation DATA only. No constructor or parser attests live Main, custody, a complete Council,
 * a capability, assignment, progress, an owner, a receipt, or an installation. */
public final class CouncilOwnedTaskObservation26757580 {
    public static final String SCHEMA="xar.ck3.council-owned-task-observation.26757580.v1";
    public static final String STEP="query-council-owned-task-observation-26757580-private-v1";
    public static final String ADAPTER="ck3-1.21.0-26757580-msvc-x64";
    public static final String VERSION="1.21.0",STEAM_BUILD="26757580";
    public static final String EXECUTABLE_SHA256="BB3FEF106240E95ECDB6F1532982E89E9432C92A99D33DB623521572F06E6F79";
    public static final String READER_SHA256="4738edd786b6b96c471107faa9223648689199ec75f69bbcbce7eb46f8248d3f";
    public static final String ABI_SHA256="e8177b66298cf0d72eaa4692eee1d169539661260336b11b3fcc505540094db0";
    public static final String FRAME_SHA256="e656a5aeac36b6e30902a7c4f5ff10b28595378ee949c181b00d4d2f9903b78d";
    private static final String BACKEND="ck3-1.21.0-native-headless-main-thread";
    private static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final long U32=0xffff_ffffL;
    private static final Set<String> FIELDS=Set.of("schema","step","status","reason","private_build","advertised","read_only",
            "data_ready","same_frame_ready","all_seats_enumerated","full_council_read_available","candidate_collection_complete",
            "progress_ready","action_ready","build","frame","owned_task_rows","candidates","final_gates","assignment_quote","origin","provenance");
    private CouncilOwnedTaskObservation26757580(){ }
    public sealed interface Observation permits Partial,Unavailable { Origin origin(); }
    public record Partial(Frame frame,List<OwnedTaskRow> ownedTaskRows,Origin origin) implements Observation {
        public Partial {
            Objects.requireNonNull(frame);Objects.requireNonNull(origin);ownedTaskRows=List.copyOf(ownedTaskRows);
            require(origin.kind()!=OriginKind.UNAVAILABLE,"partial data lacks its source-kind observation");
            require(ownedTaskRows.size()<=64,"owned task row bound exceeded");
            var ids=new HashSet<Integer>();var keys=new HashSet<String>();
            for(var row:ownedTaskRows)require(ids.add(row.taskId())&&keys.add(row.positionKey()),"duplicate owned task ID or position key");
        }
        /** Comparison only: independentlyExpected must come from the caller's separate Full original/receipt. */
        public void requireFrame(Frame independentlyExpected) {
            require(frame.equals(Objects.requireNonNull(independentlyExpected)),"Council partial differs from independently expected Full frame");
        }
    }
    public record Unavailable(String reason,Origin origin) implements Observation {
        public Unavailable {require(reason!=null&&!reason.isEmpty(),"unavailable reason required");Objects.requireNonNull(origin);}
    }
    public record Frame(String nativeSnapshotId,BigInteger nativeRevision,int dateRaw,int playerCharacterId,boolean paused,boolean mapReady) {
        public Frame {
            positive(nativeRevision);require(("native:"+nativeRevision).equals(nativeSnapshotId),"canonical native snapshot identity required");
            fullId(playerCharacterId);require(paused&&mapReady,"actual paused map frame required");
        }
    }
    public record OwnedTaskRow(int taskId,Optional<Integer> holderCharacterId,boolean holderAlive,String positionKey,
            String storedTaskTypeKey,boolean currentTypeSourceVerified,Optional<String> currentTaskTypeKey) {
        public OwnedTaskRow {
            fullId(taskId);Objects.requireNonNull(holderCharacterId);Objects.requireNonNull(currentTaskTypeKey);
            holderCharacterId.ifPresent(CouncilOwnedTaskObservation26757580::fullId);key(positionKey);key(storedTaskTypeKey);
            require(holderCharacterId.isPresent()||!holderAlive,"absent holder cannot be alive");
            require(currentTypeSourceVerified==currentTaskTypeKey.isPresent(),"verified/current-type null relation differs");
            if(currentTypeSourceVerified)require(holderCharacterId.isPresent()&&holderAlive
                    &&currentTaskTypeKey.orElseThrow().equals(storedTaskTypeKey),"current-type source requires live holder and matching stored key");
            currentTaskTypeKey.ifPresent(CouncilOwnedTaskObservation26757580::key);
        }
    }
    public enum OriginKind { APPLICATION_MAIN_TICKET,OFFLINE_FIXTURE,UNAVAILABLE }
    public record Origin(OriginKind kind,Optional<BigInteger> ticketSequence,Optional<BigInteger> pumpEpoch,
            OptionalLong threadId,boolean mainOwnerObserved) {
        public Origin {
            Objects.requireNonNull(kind);Objects.requireNonNull(ticketSequence);Objects.requireNonNull(pumpEpoch);Objects.requireNonNull(threadId);
            ticketSequence.ifPresent(CouncilOwnedTaskObservation26757580::positive);pumpEpoch.ifPresent(CouncilOwnedTaskObservation26757580::positive);
            if(threadId.isPresent())require(threadId.getAsLong()>0&&threadId.getAsLong()<=U32,"positive uint32 thread required");
            if(kind==OriginKind.APPLICATION_MAIN_TICKET)require(mainOwnerObserved&&ticketSequence.isPresent()&&pumpEpoch.isPresent()&&threadId.isPresent(),"Main observation metadata incomplete");
            else require(!mainOwnerObserved,"non-Main origin cannot claim Main ownership");
            if(kind==OriginKind.UNAVAILABLE)require(ticketSequence.isEmpty()&&pumpEpoch.isEmpty()&&threadId.isEmpty(),"unavailable origin retains explicit null counters");
        }
    }

    public static Observation decodeData(RawJson original) {
        ObjectNode row=RegistryJson.object(Objects.requireNonNull(original));RegistryJson.keys(row,FIELDS);
        require(SCHEMA.equals(text(row,"schema"))&&STEP.equals(text(row,"step")),"Council partial schema/step mismatch");
        require(bool(row,"private_build")&&!bool(row,"advertised")&&bool(row,"read_only"),"private read-only DATA flags differ");
        for(String field:List.of("all_seats_enumerated","full_council_read_available","candidate_collection_complete","progress_ready","action_ready"))
            require(!bool(row,field),"partial Council cannot claim "+field);
        for(String field:List.of("candidates","final_gates","assignment_quote"))nil(row,field);
        ObjectNode build=RegistryJson.object(row.get("build"));
        RegistryJson.keys(build,Set.of("adapter_id","game_version","steam_build_id","executable_sha256"));
        require(ADAPTER.equals(text(build,"adapter_id"))&&VERSION.equals(text(build,"game_version"))
                &&STEAM_BUILD.equals(text(build,"steam_build_id"))&&EXECUTABLE_SHA256.equalsIgnoreCase(text(build,"executable_sha256")),"exact Council build tuple mismatch");
        ObjectNode provenance=RegistryJson.object(row.get("provenance"));
        RegistryJson.keys(provenance,Set.of("reader_sha256","abi_sha256","frame_sha256"));
        require(READER_SHA256.equals(text(provenance,"reader_sha256"))&&ABI_SHA256.equals(text(provenance,"abi_sha256"))
                &&FRAME_SHA256.equals(text(provenance,"frame_sha256")),"exact archived Council provenance differs");
        Origin origin=origin(RegistryJson.object(row.get("origin")));
        boolean ready=bool(row,"data_ready");require(bool(row,"same_frame_ready")==ready,"same-frame/data-ready flags differ");
        String status=text(row,"status");
        if(!ready) {
            require(status.equals("unavailable"),"unavailable status required");nil(row,"frame");nil(row,"owned_task_rows");
            return new Unavailable(text(row,"reason"),origin);
        }
        require(status.equals("partial"),"partial status required");nil(row,"reason");
        ObjectNode frame=RegistryJson.object(row.get("frame"));
        RegistryJson.keys(frame,Set.of("native_snapshot_id","native_revision","date_raw","player_character_id","paused","map_ready"));
        Frame decoded=new Frame(text(frame,"native_snapshot_id"),uint64(frame.get("native_revision")),RegistryJson.int32(frame.get("date_raw")),
                RegistryJson.int32(frame.get("player_character_id")),bool(frame,"paused"),bool(frame,"map_ready"));
        var rows=RegistryJson.array(row.get("owned_task_rows"));require(rows.size()<=64,"owned task row bound exceeded");
        var decodedRows=new java.util.ArrayList<OwnedTaskRow>();for(JsonNode value:rows)decodedRows.add(task(RegistryJson.object(value)));
        return new Partial(decoded,decodedRows,origin);
    }
    /** Unavailable remains unbound and unavailable. Only Partial is compared with the independent expected Full. */
    public static Observation decodeData(RawJson original,Frame independentlyExpected) {
        Objects.requireNonNull(independentlyExpected);Observation decoded=decodeData(original);
        if(decoded instanceof Partial partial)partial.requireFrame(independentlyExpected);return decoded;
    }
    private static OwnedTaskRow task(ObjectNode row) {
        RegistryJson.keys(row,Set.of("task_id","holder_character_id","holder_alive","position_key","stored_task_type_key",
                "current_type_source_verified","current_task_type_key","target","progress","max_progress","frozen"));
        for(String field:List.of("target","progress","max_progress","frozen"))nil(row,field);
        JsonNode holder=row.get("holder_character_id"),current=row.get("current_task_type_key");
        return new OwnedTaskRow(RegistryJson.int32(row.get("task_id")),holder.isNull()?Optional.empty():Optional.of(RegistryJson.int32(holder)),
                bool(row,"holder_alive"),text(row,"position_key"),text(row,"stored_task_type_key"),bool(row,"current_type_source_verified"),
                current.isNull()?Optional.empty():Optional.of(RegistryJson.text(current)));
    }
    private static Origin origin(ObjectNode row) {
        RegistryJson.keys(row,Set.of("source_kind","ticket_sequence","pump_epoch","thread_id","main_owner_observed"));
        OriginKind kind=switch(text(row,"source_kind")) {
            case "application_main_ticket"->OriginKind.APPLICATION_MAIN_TICKET;
            case "offline_fixture"->OriginKind.OFFLINE_FIXTURE;
            case "unavailable"->OriginKind.UNAVAILABLE;
            default->throw new IllegalArgumentException("unknown Council origin kind");
        };
        JsonNode thread=row.get("thread_id");
        return new Origin(kind,nullableUint64(row.get("ticket_sequence")),nullableUint64(row.get("pump_epoch")),
                thread.isNull()?OptionalLong.empty():OptionalLong.of(RegistryJson.integer(thread,BigInteger.ONE,BigInteger.valueOf(U32)).longValueExact()),
                bool(row,"main_owner_observed"));
    }

    /** Extracts comparison DATA from an independent original Full packet; no freshness, receipt or owner is minted. */
    public static Frame frameFromFull(NativeWire.Snapshot original)throws IOException {
        Objects.requireNonNull(original);var decoded=NativeWire.decode(original.packet().value());
        require(decoded instanceof NativeWire.Snapshot,"independent Full original must remain a Snapshot");
        var held=(NativeWire.Snapshot)decoded;
        require(held.snapshotId().equals(original.snapshotId())&&held.revision().equals(original.revision())
                &&java.util.Arrays.equals(held.state().value(),original.state().value()),"independent Full original changed");
        ObjectNode state=RegistryJson.object(new RawJson(held.state().value()));fullIdentity(state,"ck3_1210_full_state_v1");
        ObjectNode actor=RegistryJson.object(state.get("played_character"));fullIdentity(actor,"ck3_1210_played_character_v1");
        require(bool(actor,"alive"),"independent Full actor must be living for this partial observation");
        return new Frame(held.snapshotId(),held.revision(),RegistryJson.int32(state.get("date_raw")),RegistryJson.int32(actor.get("character_id")),
                bool(state,"paused"),bool(state,"map_ready"));
    }
    private static void fullIdentity(ObjectNode row,String schema) {
        require(schema.equals(text(row,"schema"))&&VERSION.equals(text(row,"game_version"))
                &&EXECUTABLE_SHA256.equalsIgnoreCase(text(row,"executable_sha256"))&&ADAPTER.equals(text(row,"adapter_id"))
                &&BACKEND.equals(text(row,"backend")),"independent Full exact tuple differs");
    }
    /** Archived command-result DATA only. An ok=false original is not a typed observation or a zero-dispatch proof. */
    public static Observation decodeCommandResult(byte[] originalPacket,String expectedRequestId)throws IOException {
        Objects.requireNonNull(originalPacket);require(expectedRequestId!=null&&!expectedRequestId.isEmpty(),"expected request ID required");
        try {
            var decoded=NativeWire.decode(originalPacket);require(decoded instanceof NativeWire.CommandResult,"command_result packet required");
            var command=(NativeWire.CommandResult)decoded;
            ObjectNode envelope=RegistryJson.object(new RawJson(command.payload().value()));
            boolean ok=bool(envelope,"ok");
            RegistryJson.keys(envelope,ok?Set.of("type","protocol_version","request_id","ok","result")
                    :Set.of("type","protocol_version","request_id","ok","error"));
            require("command_result".equals(text(envelope,"type")),"command result type differs");
            RegistryJson.integer(envelope.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            require(expectedRequestId.equals(command.requestId())&&expectedRequestId.equals(text(envelope,"request_id"))
                    &&ok==command.nativeOk(),"command result correlation differs");
            if(!ok)throw new IOException("native Council command rejected: "+text(envelope,"error"));
            require(command.result().presence()==NativeWire.Presence.VALUE,"successful Council result is missing/null");
            return decodeData(new RawJson(command.result().token().orElseThrow().value()));
        }catch(IllegalArgumentException invalid){throw new IOException("invalid archived Council command result",invalid);}
    }
    public static Observation decodeCommandResult(byte[] originalPacket,String expectedRequestId,Frame independentlyExpected)throws IOException {
        Objects.requireNonNull(independentlyExpected);var decoded=decodeCommandResult(originalPacket,expectedRequestId);
        if(decoded instanceof Partial partial)partial.requireFrame(independentlyExpected);return decoded;
    }
    private static void fullId(int id){require(id!=-1,"invalid fullID sentinel -1 is not an observed identity");}
    private static void key(String value){require(value!=null&&value.matches("[A-Za-z0-9_.:-]{1,95}"),"bounded ASCII definition key required");}
    private static void positive(BigInteger value){require(value!=null&&value.signum()>0&&value.compareTo(U64)<=0,"positive uint64 required");}
    private static BigInteger uint64(JsonNode value){return RegistryJson.integer(value,BigInteger.ONE,U64);}
    private static Optional<BigInteger> nullableUint64(JsonNode value){return value.isNull()?Optional.empty():Optional.of(uint64(value));}
    private static String text(ObjectNode row,String field){return RegistryJson.text(RegistryJson.field(row,field));}
    private static boolean bool(ObjectNode row,String field){return RegistryJson.bool(RegistryJson.field(row,field));}
    private static void nil(ObjectNode row,String field){require(RegistryJson.field(row,field).isNull(),"explicit null required: "+field);}
    private static void require(boolean condition,String reason){RegistryJson.require(condition,reason);}
}
