package org.xar.ck3.control.nativebridge.capabilities.activity;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.activity.ActivityJson.*;

/** Copied cut observations. A disappearing activity and a counter delta are never terminal proof. */
public final class ActivityTerminalJournal {
    private ActivityTerminalJournal() { }
    public record NativeFields(Optional<Integer> completed,Optional<Integer> invalidated,Optional<BigInteger> stamp) { }
    public record CaptureFrame(BigInteger dateRaw,int actorId,long ownerThreadId,boolean paused) { }
    public record Row(BigInteger sequence,long captureThreadId,BigInteger managerIdentity,BigInteger activityIdentity,
            BigInteger typeIdentity,long fullActivityId,int generation,int hostId,NativeFields fields,CaptureFrame frame,Obj original) { }
    public record Journal(boolean available,Optional<String> unavailableReason,long queryThreadId,long actorId,
            BigInteger earliest,BigInteger latest,BigInteger overflow,List<Row> records,Obj original) {
        public Journal { records=List.copyOf(records); }
    }
    public sealed interface Observation permits Known,Rejected,ExplicitNull { }
    public record Known(Journal journal) implements Observation { }
    public record Rejected(String reason,org.xar.ck3.control.application.action.RawJson raw) implements Observation { }
    public record ExplicitNull() implements Observation { }
    public static Journal decode(byte[] raw,long actorId) {
        JsonNode root=parse(raw); exact(root,"schema available unavailable_reason observer_attached process_lifetime read_only query_thread_id_u32 query_actor_full_id_u32 record_capacity earliest_retained_sequence_u64 latest_capture_sequence_u64 overflow_dropped_count_u64 record_count records"); eq(root,"schema","activity_terminal_observations_12004_v1"); yes(root,"process_lifetime"); yes(root,"read_only"); boolean available=bool(root,"available"),attached=bool(root,"observer_attached"); long thread=number(root,"query_thread_id_u32",BigInteger.ZERO,U32).longValueExact(),actor=number(root,"query_actor_full_id_u32",BigInteger.ZERO,U32).longValueExact(); integer(root,"record_capacity",64,64); int count=integer(root,"record_count",0,64); JsonNode entries=root.get("records"); need(entries.isArray() && entries.size()==count,"terminal journal count"); BigInteger earliest=u64(root,"earliest_retained_sequence_u64"),latest=u64(root,"latest_capture_sequence_u64"),overflow=u64(root,"overflow_dropped_count_u64"); need((earliest.signum()==0)==(latest.signum()==0) && earliest.compareTo(latest)<=0,"terminal journal sequence coverage"); Optional<String> reason;
        if(available) { nil(root,"unavailable_reason"); need(attached && thread!=0 && actor==actorId,"terminal journal actual query actor/thread"); reason=Optional.empty(); } else { String value=text(root,"unavailable_reason"); need(!value.isEmpty() && entries.isEmpty(),"terminal unavailable shape"); reason=Optional.of(value); }
        List<Row> rows=new ArrayList<>(); BigInteger previous=BigInteger.ZERO;
        for(JsonNode row:entries) {
            exact(row,"capture_sequence_u64 capture_thread_id_u32 source_cut_rva_u64 manager_identity_u64 activity_identity_u64 type_identity_u64 activity_full_id_u32 activity_instance_generation_u8 host_character_id_i32 type_key completed_observed completed_raw_u8 invalidated_observed invalidated_raw_u8 native_completion_stamp_observed native_completion_stamp_raw_u64 capture_frame"); BigInteger sequence=positive(row,"capture_sequence_u64"); need(sequence.compareTo(previous)>0 && sequence.compareTo(earliest)>=0 && sequence.compareTo(latest)<=0,"terminal capture ordering"); long captureThread=number(row,"capture_thread_id_u32",BigInteger.ONE,U32).longValueExact(); need(u64(row,"source_cut_rva_u64").equals(BigInteger.valueOf(0x29BF68CL)),"terminal original cut differs"); long activity=number(row,"activity_full_id_u32",BigInteger.ZERO,U32.subtract(BigInteger.ONE)).longValueExact(); int generation=integer(row,"activity_instance_generation_u8",0,255),host=integer(row,"host_character_id_i32",Integer.MIN_VALUE,Integer.MAX_VALUE); need(generation==activity>>>24 && Integer.toUnsignedLong(host)==actor,"terminal full activity generation/host"); eq(row,"type_key","activity_feast");
            NativeFields fields=new NativeFields(observedByte(row,"completed_observed","completed_raw_u8"),observedByte(row,"invalidated_observed","invalidated_raw_u8"),observedStamp(row)); JsonNode frame=row.get("capture_frame"); exact(frame,"date_raw_i64 actor_character_id_i32 owner_thread_id_u32 paused map_ready has_played_character played_character_alive"); int frameActor=integer(frame,"actor_character_id_i32",Integer.MIN_VALUE,Integer.MAX_VALUE); long owner=number(frame,"owner_thread_id_u32",BigInteger.ONE,U32).longValueExact(); need(frameActor==host && owner==captureThread,"terminal capture frame identity/thread"); yes(frame,"map_ready"); yes(frame,"has_played_character"); yes(frame,"played_character_alive"); CaptureFrame captured=new CaptureFrame(signed(frame,"date_raw_i64"),frameActor,owner,bool(frame,"paused")); rows.add(new Row(sequence,captureThread,u64(row,"manager_identity_u64"),u64(row,"activity_identity_u64"),u64(row,"type_identity_u64"),activity,generation,host,fields,captured,app(row))); previous=sequence;
        }
        return new Journal(available,reason,thread,actor,earliest,latest,overflow,rows,app(root));
    }
    private static Optional<Integer> observedByte(JsonNode row,String flag,String field) { if(bool(row,flag))return Optional.of(integer(row,field,0,255)); nil(row,field); return Optional.empty(); }
    private static Optional<BigInteger> observedStamp(JsonNode row) { if(bool(row,"native_completion_stamp_observed"))return Optional.of(u64(row,"native_completion_stamp_raw_u64")); nil(row,"native_completion_stamp_raw_u64"); return Optional.empty(); }
}
