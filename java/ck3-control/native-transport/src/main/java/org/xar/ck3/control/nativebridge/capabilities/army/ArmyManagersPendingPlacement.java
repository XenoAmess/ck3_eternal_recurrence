package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyManagersModel.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyManagersModel.Field.*;

/** Literal record28 placement on a private sparse same-capture image. No native allocation is performed. */
final class ArmyManagersPendingPlacement {
    private ArmyManagersPendingPlacement() { }
    static final class Unavailable extends RuntimeException {
        private static final long serialVersionUID=1L;
        Unavailable(String reason){super(reason);}
    }
    static final class Vector {
        Integer count;List<BigInteger> values;final Boolean allocatorMatches;
        Vector(Integer count,List<BigInteger> values,Boolean allocatorMatches){this.count=count;this.values=copyValues(values);this.allocatorMatches=allocatorMatches;}
        Vector copy(){return new Vector(count,values,allocatorMatches);}
    }
    static final class PhysicalRecord {
        Integer control;final BigInteger hash,key;final Vector vector;
        PhysicalRecord(Integer control,BigInteger hash,BigInteger key,Vector vector){this.control=control;this.hash=hash;this.key=key;this.vector=vector;}
        PhysicalRecord copy(){return new PhysicalRecord(control,hash,key,vector.copy());}
    }
    sealed interface Event permits Growth,DirectEmpty,FastShift,CarryStart,CarryEmpty,LowerDistanceSwap,CarriedOverflow { }
    record Rehash(long physicalSlot,BigInteger storedHash,BigInteger key,long selectedSlot,boolean inserted) { }
    static final class Growth implements Event {
        final String trigger;final int index,maskBefore,countBefore,capacity,maskAfter,tailAfter;final long allocatedRecords,terminalSlot;
        final List<Rehash> oldRehashOccurrences=new ArrayList<>();
        Growth(String trigger,int index,int maskBefore,int countBefore,int capacity,int tailAfter){this.trigger=trigger;this.index=index;this.maskBefore=maskBefore;this.countBefore=countBefore;this.capacity=capacity;this.maskAfter=capacity-1;this.tailAfter=tailAfter;allocatedRecords=(long)capacity+tailAfter+1;terminalSlot=(long)capacity+tailAfter;}
        Growth copy(){Growth result=new Growth(trigger,index,maskBefore,countBefore,capacity,tailAfter);result.oldRehashOccurrences.addAll(oldRehashOccurrences);return result;}
    }
    record DirectEmpty(long slot,BigInteger key) implements Event { }
    record FastShift(long slot,long movedTo,BigInteger key) implements Event { }
    record CarryStart(long slot,BigInteger key) implements Event { }
    record CarryEmpty(long slot,long selectedSlot) implements Event { }
    record LowerDistanceSwap(long slot,int reloadedControl,int carriedControlAfter) implements Event { }
    record CarriedOverflow(long slot) implements Event { }
    static final class State {
        final Boolean entriesPresent;final String initialEntriesIdentity;Boolean dataIsEmpty;Integer mask,count,tail;final BigInteger threshold;
        Map<Long,PhysicalRecord> records;boolean generated;Long terminal;final List<Event> events;int placementInvocations;final Set<BigInteger> changedKeys;
        State(Boolean entriesPresent,String initialEntriesIdentity,Boolean dataIsEmpty,Integer mask,Integer count,Integer tail,BigInteger threshold,Map<Long,PhysicalRecord> records,boolean generated,Long terminal,List<Event> events,int placementInvocations,Set<BigInteger> changedKeys){this.entriesPresent=entriesPresent;this.initialEntriesIdentity=initialEntriesIdentity;this.dataIsEmpty=dataIsEmpty;this.mask=mask;this.count=count;this.tail=tail;this.threshold=threshold;this.records=records;this.generated=generated;this.terminal=terminal;this.events=events;this.placementInvocations=placementInvocations;this.changedKeys=changedKeys;}
        State copy(){Map<Long,PhysicalRecord> copied=new LinkedHashMap<>();records.forEach((slot,row)->copied.put(slot,row.copy()));List<Event> copiedEvents=new ArrayList<>();for(Event event:events)copiedEvents.add(event instanceof Growth growth?growth.copy():event);return new State(entriesPresent,initialEntriesIdentity,dataIsEmpty,mask,count,tail,threshold,copied,generated,terminal,copiedEvents,placementInvocations,new HashSet<>(changedKeys));}
    }
    record Selected(long slot,PhysicalRecord record,boolean inserted,String branch) { Selected branch(String next){return new Selected(slot,record,inserted,next);} }
    static State create(Document frame){Map<Long,PhysicalRecord> records=new LinkedHashMap<>();for(Document row:frame.rows(RECORDS)){Document refs=row.object(REFERENCES);records.put(row.i64(PHYSICAL_SLOT_I64),new PhysicalRecord(row.i32(CONTROL_RAW_U8),row.integer(STORED_HASH_RAW_U32),row.integer(KEY_RAW_FULL_ID_U32),new Vector(refs.i32(COUNT_RAW_I32),referenceValues(refs),row.bool(VECTOR_ALLOCATOR_MATCHES_EXPECTED))));}return new State(frame.bool(ENTRIES_PRESENT),frame.text(ENTRIES_IDENTITY),frame.bool(DATA_IS_NATIVE_EMPTY_BUFFER),frame.i32(MASK_RAW_I32),frame.i32(MAP_COUNT_RAW_I32),frame.i32(TAIL_RAW_U8),frame.integer(THRESHOLD_BITS_U32),records,false,frame.i64(PHYSICAL_CONTROL_EXTENT_LAST_SLOT_I64),new ArrayList<>(),0,new HashSet<>());}
    private static PhysicalRecord at(State state,long slot){PhysicalRecord row=state.records.get(slot);if(row==null){if(state.generated&&state.terminal!=null&&slot>=0&&slot<=state.terminal){row=new PhysicalRecord(slot==state.terminal?255:0,null,null,new Vector(null,null,null));state.records.put(slot,row);}else throw new Unavailable("pending_physical_control_unobserved");}need(row.control,"pending_physical_control_unavailable");return row;}
    private static PhysicalRecord movable(PhysicalRecord row){need(row.hash,"pending_carried_stored_hash_unavailable");need(row.key,"pending_carried_key_unavailable");if(!Boolean.TRUE.equals(row.vector.allocatorMatches))throw new Unavailable("pending_required_vector_transfer_unmatched_or_unread");return row.copy();}
    private static PhysicalRecord incoming(BigInteger hash,BigInteger key,Vector vector,int control){if(!Boolean.TRUE.equals(vector.allocatorMatches))throw new Unavailable("pending_required_vector_transfer_unmatched_or_unread");return new PhysicalRecord(control,hash,key,vector.copy());}
    private static int growthIndex(int mask){int size=mask+1;return size<=1?3:Math.max(3,32-Integer.numberOfLeadingZeros(size-1)+1);}
    private static void grow(State state,String trigger){int mask=need(state.mask,"pending_insertion_mask_unavailable"),count=need(state.count,"pending_insertion_count_unavailable"),index=growthIndex(mask);if(index>=31)throw new Unavailable("pending_native_growth_index_nonreturn_boundary");boolean oldEmpty=count>0?need(state.dataIsEmpty,"pending_old_data_sentinel_equality_unavailable"):true;State old=state.copy();int capacity=1<<index,tail=(index+2)&255;Growth event=new Growth(trigger,index,mask,count,capacity,tail);state.mask=capacity-1;state.count=0;state.tail=tail;state.records=new LinkedHashMap<>();state.generated=true;state.terminal=(long)capacity+tail;state.dataIsEmpty=false;state.events.add(event);if(count<=0||oldEmpty)return;int remaining=count;long slot=0;while(remaining>0){PhysicalRecord record=at(old,slot);if(record.control!=0){BigInteger hash=need(record.hash,"pending_rehash_stored_hash_unavailable"),key=need(record.key,"pending_rehash_key_unavailable");Selected selected=insert(state,hash,key,record.vector);state.changedKeys.add(key);event.oldRehashOccurrences.add(new Rehash(slot,hash,key,selected.slot(),selected.inserted()));remaining--;}slot++;}}
    private static Selected insert(State state,BigInteger hash,BigInteger key,Vector vector){int mask=need(state.mask,"pending_insertion_mask_unavailable");long slot=(int)(hash.longValue()&(mask&0xffffffffL));int distance=1;PhysicalRecord record;int control;
        while(true){record=at(state,slot);control=record.control;if(control<distance)break;if(need(record.key,"pending_probe_key_unavailable").equals(key))return new Selected(slot,record,false,"existing_key");slot++;distance=(distance+1)&255;}
        int tail=need(state.tail,"pending_insertion_tail_unavailable"),count=need(state.count,"pending_insertion_count_unavailable");BigInteger threshold=need(state.threshold,"pending_insertion_threshold_unavailable");
        if(distance>tail||densityExceeds(count,mask,threshold)){grow(state,"initial_growth");return insert(state,hash,key,vector).branch("initial_growth");}
        if(control==0){state.records.put(slot,incoming(hash,key,vector,distance));state.changedKeys.add(key);state.count=count+1;state.events.add(new DirectEmpty(slot,key));return new Selected(slot,state.records.get(slot),true,"direct_empty");}
        int carriedControl=(control+1)&255;PhysicalRecord next=at(state,slot+1),resident=movable(record);state.changedKeys.add(key);state.changedKeys.add(resident.key);resident.control=carriedControl;
        if(next.control==0){state.records.put(slot+1,resident);state.records.put(slot,incoming(hash,key,vector,distance));state.count=count+1;state.events.add(new FastShift(slot,slot+1,key));return new Selected(slot,state.records.get(slot),true,"fast_shift");}
        long first=slot;state.records.put(slot,incoming(hash,key,vector,distance));PhysicalRecord carried=resident;state.events.add(new CarryStart(slot,key));
        while(true){slot++;record=at(state,slot);control=record.control;if(control==0){state.records.put(slot,carried);state.count=state.count+1;state.events.add(new CarryEmpty(slot,first));return new Selected(first,state.records.get(first),true,"general_carried_collision");}
            if(control<carried.control){PhysicalRecord displaced=movable(record);state.changedKeys.add(displaced.key);state.records.put(slot,carried);carried=displaced;carried.control=(control+1)&255;state.events.add(new LowerDistanceSwap(slot,control,carried.control));continue;}
            carried.control=(carried.control+1)&255;if(carried.control<=state.tail)continue;PhysicalRecord original=movable(state.records.get(first));state.records.put(first,carried);carried=original;state.events.add(new CarriedOverflow(first));grow(state,"carried_overflow");return insert(state,carried.hash,carried.key,carried.vector).branch("carried_growth");}
    }
    static Selected select(State state,BigInteger key,BigInteger hash){if(!Boolean.TRUE.equals(state.entriesPresent))throw new Unavailable("pending_map_header_unavailable");state.placementInvocations++;return insert(state,hash,key,new Vector(0,List.of(),true));}
    static boolean densityExceeds(int count,int mask,BigInteger thresholdBits){float numerator=(float)(count+1),denominator=(float)mask;float density=numerator/denominator,threshold=Float.intBitsToFloat(thresholdBits.intValue());return !Float.isNaN(density)&&!Float.isNaN(threshold)&&density>threshold;}
    static BigInteger hash(BigInteger value){int result=0x811c9dc5;long full=value.longValue();for(int shift:new int[]{0,8,16,24})result=(result^(int)((full>>>shift)&255))*0x01000193;return BigInteger.valueOf(Integer.toUnsignedLong(result));}
    static List<BigInteger> referenceValues(Document refs){return refs.yes(REFERENCES_READY)?new ArrayList<>(refs.rows(OCCURRENCES).stream().map(row->row.integer(RAW_FULL_ID_U32)).toList()):null;}
    static List<BigInteger> copyValues(List<BigInteger> values){return values==null?null:new ArrayList<>(values);}
    static <T> T need(T value,String reason){if(value==null)throw new Unavailable(reason);return value;}
    static ObjectNode encode(State state,boolean publicV2){ObjectNode out=JsonNodeFactory.instance.objectNode();out.put("source","same_input_conditional_pending_record28_placement_v1");nullable(out,"mask_raw_i32",state.mask);nullable(out,"conditional_map_count_raw_i32",state.count);nullable(out,"tail_raw_u8",state.tail);integer(out,"threshold_bits_u32",state.threshold,false);out.put("sparse_generated_image",state.generated);if(state.generated)out.put("default_control_raw_u8",0);else out.putNull("default_control_raw_u8");integer(out,"terminal_slot_i64",state.terminal==null?null:BigInteger.valueOf(state.terminal),publicV2);if(state.generated)out.put("terminal_control_raw_u8",255);else out.putNull("terminal_control_raw_u8");ArrayNode rows=out.putArray("physical_records");for(var entry:new TreeMap<>(state.records).entrySet()){PhysicalRecord row=entry.getValue();ObjectNode item=rows.addObject();integer(item,"physical_slot_i64",BigInteger.valueOf(entry.getKey()),publicV2);nullable(item,"control_raw_u8",row.control);integer(item,"stored_hash_raw_u32",row.hash,false);integer(item,"key_raw_full_id_u32",row.key,false);nullable(item,"conditional_count_raw_i32",row.control!=null&&row.control!=0?row.vector.count:null);ids(item,"conditional_full_ids_u32",row.control!=null&&row.control!=0?row.vector.values:null);item.put("physically_changed",state.changedKeys.contains(row.key));}ArrayNode events=out.putArray("events");for(Event event:state.events)events.add(encodeEvent(event,publicV2));out.put("placement_invocations",state.placementInvocations).put("native_writes",0).put("native_mutator_invocations",0).put("actual_native_after_ready",false);return out;}
    private static ObjectNode encodeEvent(Event event,boolean publicV2){ObjectNode out=JsonNodeFactory.instance.objectNode();if(event instanceof Growth v){out.put("kind","growth").put("trigger",v.trigger).put("index",v.index).put("mask_before",v.maskBefore).put("count_before",v.countBefore).put("capacity",v.capacity).put("mask_after",v.maskAfter).put("tail_after",v.tailAfter).put("allocated_records",v.allocatedRecords).put("terminal_slot",v.terminalSlot);ArrayNode rows=out.putArray("old_rehash_occurrences");for(Rehash row:v.oldRehashOccurrences){ObjectNode item=rows.addObject();integer(item,"physical_slot_i64",BigInteger.valueOf(row.physicalSlot()),publicV2);integer(item,"stored_hash_raw_u32",row.storedHash(),false);integer(item,"key_raw_full_id_u32",row.key(),false);item.put("selected_slot_i64",row.selectedSlot()).put("inserted",row.inserted());if(publicV2)item.put("selected_slot_i64",Long.toString(row.selectedSlot()));}}
        else if(event instanceof DirectEmpty v){out.put("kind","direct_empty").put("slot",v.slot());integer(out,"key",v.key(),false);}else if(event instanceof FastShift v){out.put("kind","fast_shift").put("slot",v.slot()).put("moved_to",v.movedTo());integer(out,"key",v.key(),false);}else if(event instanceof CarryStart v){out.put("kind","carry_start").put("slot",v.slot());integer(out,"key",v.key(),false);}else if(event instanceof CarryEmpty v)out.put("kind","carry_empty").put("slot",v.slot()).put("selected_slot",v.selectedSlot());else if(event instanceof LowerDistanceSwap v)out.put("kind","lower_distance_swap").put("slot",v.slot()).put("reloaded_control",v.reloadedControl()).put("carried_control_after",v.carriedControlAfter()).put("tail_test",false);else if(event instanceof CarriedOverflow v)out.put("kind","carried_overflow_first_slot_exchange").put("slot",v.slot());if(publicV2)for(String field:List.of("slot","moved_to","selected_slot"))if(out.has(field))out.put(field,out.get(field).bigIntegerValue().toString());return out;}
    static void nullable(ObjectNode out,String field,Integer value){if(value==null)out.putNull(field);else out.put(field,value);}
    static void integer(ObjectNode out,String field,BigInteger value,boolean decimal){if(value==null)out.putNull(field);else if(decimal)out.put(field,value.toString());else out.put(field,value);}
    static void ids(ObjectNode out,String field,List<BigInteger> values){if(values==null){out.putNull(field);return;}ArrayNode list=out.putArray(field);for(BigInteger value:values)if(value==null)list.addNull();else list.add(value);}
}
