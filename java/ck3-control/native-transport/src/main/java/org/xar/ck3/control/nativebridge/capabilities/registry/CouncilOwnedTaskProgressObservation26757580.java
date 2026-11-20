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
import org.xar.ck3.control.nativebridge.capabilities.registry.CouncilOwnedTaskObservation26757580.Frame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CouncilOwnedTaskObservation26757580.Origin;
import org.xar.ck3.control.nativebridge.capabilities.registry.CouncilOwnedTaskObservation26757580.OriginKind;
import org.xar.ck3.control.nativebridge.capabilities.registry.CouncilOwnedTaskObservation26757580.OwnedTaskRow;

/** Independent private v2 observation DATA. No live/Main/owner/custody, complete Council, evaluator, float or action grant. */
public final class CouncilOwnedTaskProgressObservation26757580 {
    public static final String SCHEMA="xar.ck3.council-owned-task-progress-observation.26757580.v2";
    public static final String STEP="query-council-owned-task-progress-observation-26757580-private-v2";
    public static final String READER_SHA256="dd79375f0cc20d9a889d87023a9fa5872d226791a019102a6298955d2aa07991";
    public static final String ABI_SHA256="93aead4e20de67eab5b4b898a900473daa2eda330724187ec14be1d07a4415ab";
    public static final String FRAME_SHA256="fe0375c0351ac0921ec996fe43782cc5d7d8b4fae06b1221dd8acfbb871dd934";
    private static final String FROZEN_REASON="council70_noncanonical_frozen_byte";
    private static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final Set<String> FIELDS=Set.of("schema","step","status","reason","private_build","advertised","read_only","data_ready","same_frame_ready",
            "all_seats_enumerated","full_council_read_available","candidate_collection_complete","progress_ready","action_ready","build","frame","owned_task_rows","candidates","final_gates","assignment_quote","origin","provenance");
    private CouncilOwnedTaskProgressObservation26757580(){ }
    public sealed interface Observation permits Partial,Unavailable { Origin origin(); }
    public record Partial(Frame frame,List<Row> ownedTaskRows,Origin origin) implements Observation {
        public Partial {
            Objects.requireNonNull(frame);Objects.requireNonNull(origin);ownedTaskRows=List.copyOf(ownedTaskRows);
            require(origin.kind()!=OriginKind.UNAVAILABLE&&ownedTaskRows.size()<=64,"partial source/owned rows unavailable");
            var ids=new HashSet<Integer>();var keys=new HashSet<String>();
            for(var row:ownedTaskRows)require(ids.add(row.identity().taskId())&&keys.add(row.identity().positionKey()),"duplicate owned task ID/position key");
        }
        /** Comparison DATA only: expected must come from an independent actual Full original/receipt. */
        public void requireFrame(Frame independentlyExpected){require(frame.equals(Objects.requireNonNull(independentlyExpected)),"v2 Council differs from independent Full frame");}
    }
    public record Unavailable(String reason,Origin origin) implements Observation {
        public Unavailable {require(reason!=null&&!reason.isEmpty(),"unavailable reason required");Objects.requireNonNull(origin);}
    }
    public enum Kind {
        INFINITE("infinite"),PERCENTAGE("percentage"),VALUE("value"),UNKNOWN("unknown");
        private final String wire;Kind(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Kind fromRaw(int raw){return switch(raw){case 0->INFINITE;case 1->PERCENTAGE;case 2->VALUE;default->UNKNOWN;};}
    }
    public enum CurrentReason {
        HOLDER_UNVERIFIED("council70_current_holder_unverified"),VALUE_EVALUATOR_UNOBSERVED("council70_value_evaluator_unobserved"),KIND_UNRECOGNIZED("council70_progress_kind_unrecognized");
        private final String wire;CurrentReason(String wire){this.wire=wire;}public String wire(){return wire;}
    }
    public record ProgressObservation(int kindRaw,Kind kind,long backingRaw,int scale,boolean currentSourceVerified,
            OptionalLong currentRaw,OptionalLong maximumRaw,Optional<CurrentReason> currentReason,boolean nativeFloatObserved,
            int frozenRaw,boolean frozenKnown,Optional<Boolean> frozenValue,Optional<String> frozenReason) {
        public ProgressObservation {
            Objects.requireNonNull(kind);Objects.requireNonNull(currentRaw);Objects.requireNonNull(maximumRaw);Objects.requireNonNull(currentReason);
            Objects.requireNonNull(frozenValue);Objects.requireNonNull(frozenReason);
            require(kind==Kind.fromRaw(kindRaw)&&scale==100000&&!nativeFloatObserved,"progress kind/scale/float contract differs");
            if(currentSourceVerified)require((kind==Kind.INFINITE||kind==Kind.PERCENTAGE)&&currentRaw.isPresent()&&maximumRaw.isPresent()
                    &&currentRaw.getAsLong()==backingRaw&&maximumRaw.getAsLong()==(kind==Kind.INFINITE?0L:10000000L)&&currentReason.isEmpty(),"known current raw/maximum/reason differs");
            else require(currentRaw.isEmpty()&&maximumRaw.isEmpty()&&currentReason.isPresent(),"unknown current requires explicit null raw/maximum and reason");
            require(frozenRaw>=0&&frozenRaw<=255&&frozenKnown==(frozenRaw<=1),"frozen byte/known contract differs");
            if(frozenKnown)require(frozenValue.isPresent()&&frozenValue.orElseThrow()==(frozenRaw==1)&&frozenReason.isEmpty(),"known frozen value/reason differs");
            else require(frozenValue.isEmpty()&&frozenReason.filter(FROZEN_REASON::equals).isPresent(),"unknown frozen byte requires null value and exact reason");
        }
    }
    public record Row(OwnedTaskRow identity,ProgressObservation progressObservation) {
        public Row {
            Objects.requireNonNull(identity);Objects.requireNonNull(progressObservation);var p=progressObservation;
            boolean current=identity.currentTypeSourceVerified()&&(p.kind()==Kind.INFINITE||p.kind()==Kind.PERCENTAGE);
            require(p.currentSourceVerified()==current,"progress current-source flag differs from identity/kind");
            if(!current){var reason=!identity.currentTypeSourceVerified()?CurrentReason.HOLDER_UNVERIFIED
                    :p.kind()==Kind.VALUE?CurrentReason.VALUE_EVALUATOR_UNOBSERVED:CurrentReason.KIND_UNRECOGNIZED;
                require(p.currentReason().equals(Optional.of(reason)),"progress unknown-current reason precedence differs");}
        }
    }

    public static Observation decodeData(RawJson original){
        ObjectNode row=RegistryJson.object(Objects.requireNonNull(original));RegistryJson.keys(row,FIELDS);
        require(SCHEMA.equals(text(row,"schema"))&&STEP.equals(text(row,"step")),"independent Council70 schema/step required");
        require(bool(row,"private_build")&&!bool(row,"advertised")&&bool(row,"read_only"),"private read-only flags differ");
        for(String field:List.of("all_seats_enumerated","full_council_read_available","candidate_collection_complete","progress_ready","action_ready"))require(!bool(row,field),"partial cannot claim "+field);
        for(String field:List.of("candidates","final_gates","assignment_quote"))nil(row,field);
        ObjectNode build=RegistryJson.object(row.get("build"));RegistryJson.keys(build,Set.of("adapter_id","game_version","steam_build_id","executable_sha256"));
        require(CouncilOwnedTaskObservation26757580.ADAPTER.equals(text(build,"adapter_id"))&&CouncilOwnedTaskObservation26757580.VERSION.equals(text(build,"game_version"))
                &&CouncilOwnedTaskObservation26757580.STEAM_BUILD.equals(text(build,"steam_build_id"))&&CouncilOwnedTaskObservation26757580.EXECUTABLE_SHA256.equalsIgnoreCase(text(build,"executable_sha256")),"Council70 exact build tuple differs");
        ObjectNode provenance=RegistryJson.object(row.get("provenance"));RegistryJson.keys(provenance,Set.of("reader_sha256","abi_sha256","frame_sha256"));
        require(READER_SHA256.equals(text(provenance,"reader_sha256"))&&ABI_SHA256.equals(text(provenance,"abi_sha256"))&&FRAME_SHA256.equals(text(provenance,"frame_sha256")),"Council70 provenance differs");
        Origin origin=origin(RegistryJson.object(row.get("origin")));boolean ready=bool(row,"data_ready");require(bool(row,"same_frame_ready")==ready,"same-frame/data-ready flags differ");
        if(!ready){require(text(row,"status").equals("unavailable"),"unavailable status required");nil(row,"frame");nil(row,"owned_task_rows");return new Unavailable(text(row,"reason"),origin);}
        require(text(row,"status").equals("partial"),"partial status required");nil(row,"reason");
        ObjectNode frame=RegistryJson.object(row.get("frame"));RegistryJson.keys(frame,Set.of("native_snapshot_id","native_revision","date_raw","player_character_id","paused","map_ready"));
        Frame actual=new Frame(text(frame,"native_snapshot_id"),uint64(frame.get("native_revision")),RegistryJson.int32(frame.get("date_raw")),RegistryJson.int32(frame.get("player_character_id")),bool(frame,"paused"),bool(frame,"map_ready"));
        var rows=RegistryJson.array(row.get("owned_task_rows"));require(rows.size()<=64,"owned task row bound exceeded");
        var decoded=new java.util.ArrayList<Row>();for(JsonNode value:rows)decoded.add(task(RegistryJson.object(value)));return new Partial(actual,decoded,origin);
    }
    /** Unavailable remains unbound; comparison never upgrades it or creates a live role. */
    public static Observation decodeData(RawJson original,Frame independentlyExpected){
        Objects.requireNonNull(independentlyExpected);var decoded=decodeData(original);if(decoded instanceof Partial p)p.requireFrame(independentlyExpected);return decoded;
    }
    private static Row task(ObjectNode row){
        RegistryJson.keys(row,Set.of("task_id","holder_character_id","holder_alive","position_key","stored_task_type_key","current_type_source_verified","current_task_type_key","target","progress","max_progress","frozen","progress_observation"));
        for(String field:List.of("target","progress","max_progress","frozen"))nil(row,field);
        JsonNode holder=row.get("holder_character_id"),current=row.get("current_task_type_key");
        var identity=new OwnedTaskRow(RegistryJson.int32(row.get("task_id")),holder.isNull()?Optional.empty():Optional.of(RegistryJson.int32(holder)),bool(row,"holder_alive"),text(row,"position_key"),text(row,"stored_task_type_key"),bool(row,"current_type_source_verified"),current.isNull()?Optional.empty():Optional.of(RegistryJson.text(current)));
        return new Row(identity,progress(RegistryJson.object(row.get("progress_observation"))));
    }
    private static ProgressObservation progress(ObjectNode p){
        RegistryJson.keys(p,Set.of("kind_raw","kind","backing_raw","scale","current_source_verified","current_raw","maximum_raw","current_reason","native_float_observed","frozen_raw","frozen_known","frozen_value","frozen_reason"));
        int raw=RegistryJson.int32(p.get("kind_raw"));Kind kind=Kind.fromRaw(raw);require(kind.wire().equals(text(p,"kind")),"kind raw/name mismatch");
        Optional<CurrentReason> reason=Optional.empty();if(!p.get("current_reason").isNull()){
            String value=text(p,"current_reason");for(var candidate:CurrentReason.values())if(candidate.wire().equals(value))reason=Optional.of(candidate);
            require(reason.isPresent(),"unknown current reason literal");
        }
        JsonNode frozen=p.get("frozen_value"),frozenReason=p.get("frozen_reason");
        return new ProgressObservation(raw,kind,signed64(p.get("backing_raw")),RegistryJson.int32(p.get("scale")),bool(p,"current_source_verified"),nullableSigned64(p.get("current_raw")),nullableSigned64(p.get("maximum_raw")),reason,bool(p,"native_float_observed"),
                RegistryJson.integer(p.get("frozen_raw"),BigInteger.ZERO,BigInteger.valueOf(255)).intValueExact(),bool(p,"frozen_known"),frozen.isNull()?Optional.empty():Optional.of(RegistryJson.bool(frozen)),frozenReason.isNull()?Optional.empty():Optional.of(text(p,"frozen_reason")));
    }
    private static Origin origin(ObjectNode row){
        RegistryJson.keys(row,Set.of("source_kind","ticket_sequence","pump_epoch","thread_id","main_owner_observed"));
        OriginKind kind=switch(text(row,"source_kind")){case "application_main_ticket"->OriginKind.APPLICATION_MAIN_TICKET;case "offline_fixture"->OriginKind.OFFLINE_FIXTURE;case "unavailable"->OriginKind.UNAVAILABLE;default->throw new IllegalArgumentException("unknown origin kind");};
        JsonNode thread=row.get("thread_id");return new Origin(kind,nullableUint64(row.get("ticket_sequence")),nullableUint64(row.get("pump_epoch")),thread.isNull()?OptionalLong.empty():OptionalLong.of(RegistryJson.integer(thread,BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()),bool(row,"main_owner_observed"));
    }

    /** Reuses only the already separate Full comparison DATA helper, never the old67 result parser. */
    public static Frame frameFromFull(NativeWire.Snapshot original)throws IOException{return CouncilOwnedTaskObservation26757580.frameFromFull(original);}
    /** Original archived packet DATA; a native error is neither a typed observation nor a zero-dispatch proof. */
    public static Observation decodeCommandResult(byte[] originalPacket,String expectedRequestId)throws IOException{
        Objects.requireNonNull(originalPacket);require(expectedRequestId!=null&&!expectedRequestId.isEmpty(),"expected request ID required");
        try{
            var decoded=NativeWire.decode(originalPacket);require(decoded instanceof NativeWire.CommandResult,"command_result required");var command=(NativeWire.CommandResult)decoded;
            ObjectNode envelope=RegistryJson.object(new RawJson(command.payload().value()));boolean ok=bool(envelope,"ok");
            RegistryJson.keys(envelope,ok?Set.of("type","protocol_version","request_id","ok","result"):Set.of("type","protocol_version","request_id","ok","error"));
            require("command_result".equals(text(envelope,"type")),"command result type differs");RegistryJson.integer(envelope.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            require(expectedRequestId.equals(command.requestId())&&expectedRequestId.equals(text(envelope,"request_id"))&&ok==command.nativeOk(),"command correlation differs");
            if(!ok)throw new IOException("native Council70 command rejected: "+text(envelope,"error"));
            require(command.result().presence()==NativeWire.Presence.VALUE,"successful v2 result is missing/null");
            return decodeData(new RawJson(command.result().token().orElseThrow().value()));
        }catch(IllegalArgumentException invalid){throw new IOException("invalid archived Council70 result",invalid);}
    }
    public static Observation decodeCommandResult(byte[] originalPacket,String expectedRequestId,Frame independentlyExpected)throws IOException{
        Objects.requireNonNull(independentlyExpected);var decoded=decodeCommandResult(originalPacket,expectedRequestId);if(decoded instanceof Partial p)p.requireFrame(independentlyExpected);return decoded;
    }
    private static long signed64(JsonNode value){return RegistryJson.integer(value,BigInteger.valueOf(Long.MIN_VALUE),BigInteger.valueOf(Long.MAX_VALUE)).longValueExact();}
    private static OptionalLong nullableSigned64(JsonNode value){return value.isNull()?OptionalLong.empty():OptionalLong.of(signed64(value));}
    private static BigInteger uint64(JsonNode value){return RegistryJson.integer(value,BigInteger.ONE,U64);}
    private static Optional<BigInteger> nullableUint64(JsonNode value){return value.isNull()?Optional.empty():Optional.of(uint64(value));}
    private static String text(ObjectNode row,String field){return RegistryJson.text(RegistryJson.field(row,field));}
    private static boolean bool(ObjectNode row,String field){return RegistryJson.bool(RegistryJson.field(row,field));}
    private static void nil(ObjectNode row,String field){require(RegistryJson.field(row,field).isNull(),"explicit null required: "+field);}
    private static void require(boolean condition,String reason){RegistryJson.require(condition,reason);}
}
