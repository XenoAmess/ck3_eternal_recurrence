package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyDetachmentDataInputs.*;

/** Pure ordered 2633FF0 DATA replay. Every incoming starts from its own observed bytes; no native write is performed. */
public final class ArmyDetachmentDataProjection {
    private ArmyDetachmentDataProjection() { }
    private static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final long INVALID = 0xffff_ffffL, REGI = 0x52656769L, PROV = 0x50726f76L;
    private static final long SENTINEL = 0xffffffff029c77f8L;
    public enum Availability { UNAVAILABLE, PARTIAL, AVAILABLE }
    public enum Branch {
        INVALID_CHARACTER("invalid_character_id_return"),NULL_CHARACTER_POINTER("null_character1b8_return"),CHARACTER_INNER_PARTIAL("selected_character_inner_effects_partial"),
        NO_GROWTH("typed_no_growth"),GROWTH("typed_growth"),INVALID_REGI("invalid_selected_Regi_skip"),NULL_PHYSICAL("null_physical_pointer_skip"),PROCESSED("processed_valid_chunk"),
        BOTH_NON_PROV("both_origins_nonProv_copy_entry_qword"),CAPITAL_ORIGIN("native_computed_capital_origin"),REGI_ORIGIN("native_computed_Regi120_origin");
        private final String wire;Branch(String wire){this.wire=wire;}public String wire(){return wire;}
    }
    public record CandidateResult(int nativeIndex,Long rawFullId,String resolvedArrgIdentity,Integer incomingIndex,Boolean incomingValid,boolean ready,List<String> missingInputs) {
        public CandidateResult { missingInputs=List.copyOf(missingInputs); }
    }
    public record Suffix(boolean ready,Branch branch,Long characterFullId,String actualSelectedCharacterIdentity,List<String> missingInputs) {
        public Suffix { missingInputs=List.copyOf(missingInputs); }
    }
    public record PendingRecordResult(int nativeIndex,String recordIdentity,String vtableIdentity,String slot0TargetIdentity,long owner08,int ordinal0c) { }
    public record OldCallback(int nativeIndex,String targetIdentity,boolean sourceNoopReady) { }
    public record Growth(int newCount,int newCapacity,long allocationBytes,int allocationAlignment) { }
    public record PreparedGrowth(List<PendingRecordResult> records,int capturedOldCount,List<OldCallback> oldCallbacks) {
        public PreparedGrowth { records=List.copyOf(records);oldCallbacks=List.copyOf(oldCallbacks); }
    }
    public record PendingEvent(Integer countBefore,Integer capacityBefore,Branch branch,boolean ready,List<String> missingInputs,
            Integer countAfter,PendingRecordResult appendedRecord,Growth growth,PreparedGrowth prepared,String conditionalBufferIdentity,List<String> headerWriteOrder) {
        public PendingEvent { missingInputs=List.copyOf(missingInputs); if(headerWriteOrder!=null)headerWriteOrder=List.copyOf(headerWriteOrder); }
    }
    public sealed interface Effect permits Store,UnknownBuffer { String kind(); String addressIdentity(); int size(); BigInteger beforeRaw(); }
    public record Store(String kind,String addressIdentity,int size,BigInteger beforeRaw,BigInteger afterRaw) implements Effect { }
    public record UnknownBuffer(String kind,String addressIdentity,int size,BigInteger beforeRaw,String conditionalBufferIdentity) implements Effect { }
    public record PendingResult(String observedHeaderIdentity,String observedBufferIdentity,String conditionalBufferIdentity,Integer conditionalCount,
            Integer conditionalCapacity,List<PendingRecordResult> records,List<PendingEvent> events) {
        public PendingResult { records=List.copyOf(records);events=List.copyOf(events); }
    }
    public record ChunkResult(PhysicalChunk observed,Integer maximum00,Integer current04,Long owner08,Integer ordinal0c,Long association10,Integer flag14,Long date1cRaw64) { }
    public record Occurrence(int nativeIndex,String recordIdentity,Long rawRegiFullId,Integer dataOrdinal,String physicalChunkIdentity,
            boolean ready,Branch branch,boolean setterPairCleared,Boolean predicate,Branch dateBranch,Long outputDateRaw64,Boolean dateGreater,
            PendingEvent pendingEvent,List<String> missingInputs,boolean resolutionSelected,String selectedRegiIdentity,String heldFallbackRegiIdentity) {
        public Occurrence { missingInputs=List.copyOf(missingInputs); }
    }
    public record IncomingResult(int nativeIndex,String arrgIdentity,boolean ready,Availability status,String unavailableReason,Integer dataCount,
            String capturedCursorIdentity,String capturedEndIdentity,String terminalCursorIdentity,Long conditionalEntryDateRaw64,
            int completedOccurrences,int begunOccurrences,List<Occurrence> occurrences,List<ChunkResult> chunks,List<Effect> effects,List<String> missingInputs,
            Suffix characterSuffix,boolean wholeConditionalCallerReady,PendingResult conditionalPending) {
        public IncomingResult { occurrences=List.copyOf(occurrences);chunks=List.copyOf(chunks);effects=List.copyOf(effects);missingInputs=List.copyOf(missingInputs); }
    }
    public record Result(Availability status,boolean ready,boolean selectionReady,boolean rosterReady,List<CandidateResult> candidates,List<IncomingResult> incoming,List<String> missingInputs) {
        public Result { candidates=List.copyOf(candidates);incoming=List.copyOf(incoming);missingInputs=List.copyOf(missingInputs); }
    }
    public record ArmyResult(int armyId,Long nativeCarmyId,Result projection) { public ArmyResult { Objects.requireNonNull(projection); } }
    public record Batch(List<ArmyResult> armies) { public Batch { armies=List.copyOf(armies); } }
    public static ArmyResult build(ArmyStrengths.Row row){
        Objects.requireNonNull(row);ArmyDetachmentDataInputs inputs=ArmyStrengthsDetachment.family(row,ArmyStrengthsFamilies.Key.CURRENT_DETACHMENT_DATA_INPUTS_V1,ArmyDetachmentDataInputs.class);
        Long nativeId=row.core().nativeArmy() instanceof ArmyTypes.Present<?> present?(long)ArmyTypes.FullId.class.cast(present.value()).value():null;
        return new ArmyResult(row.core().army().value(),nativeId,project(inputs,ArmyStrengthsDetachment.monthlyDate(row)));
    }
    public static JsonNode nativeJson(ArmyResult result){return army(result,false);}
    public static JsonNode publicV2Json(ArmyResult result){return army(result,true);}
    private static ObjectNode army(ArmyResult result,boolean publicV2){ObjectNode value=encode(result.projection(),publicV2);value.put("subject_army_id",result.armyId()).put("subject_native_carmy_id",result.nativeCarmyId());return value;}
    private static RawJson batch(Batch batch,boolean publicV2){ArrayNode rows=StrictJson.object().arrayNode();for(ArmyResult row:batch.armies()){ObjectNode item=rows.addObject();item.put("army_id",row.armyId()).set("projection",army(row,publicV2));}return new RawJson(ArmyJson.bytes(rows));}
    /** The whole-service installer calls this exact source once; the other detachment stages have their own original source pins. */
    public static void install(ArmyStrengthsPipeline pipeline,ExactRef actualKernelSource){
        Objects.requireNonNull(pipeline);Objects.requireNonNull(actualKernelSource);
        pipeline.register(ArmyStrengthsPipeline.Stage.SAME_INPUT_CURRENT_DETACHMENT_DATA_PREFIX_V1,Batch.class,List.of(),
                (input,earlier)->new Batch(input.selected().stream().map(ArmyDetachmentDataProjection::build).toList()),
                value->batch(value,false),value->batch(value,true),actualKernelSource);
    }
    private enum ChunkField {
        MAXIMUM(0,4,true),CURRENT(4,4,true),OWNER(8,4,false),ORDINAL(12,4,true),ASSOCIATION(16,4,false),FLAG(20,1,false),DATE(28,8,true);
        final int offset,size;final boolean signed;ChunkField(int offset,int size,boolean signed){this.offset=offset;this.size=size;this.signed=signed;}
        BigInteger raw(PhysicalChunk chunk){return switch(this){case MAXIMUM->big(chunk.maximum00());case CURRENT->big(chunk.current04());case OWNER->big(chunk.owner08());case ORDINAL->big(chunk.ordinal0c());case ASSOCIATION->big(chunk.association10());case FLAG->big(chunk.flag14());case DATE->big(chunk.date1cRaw64());};}
    }
    private static BigInteger big(Integer value){return value==null?null:BigInteger.valueOf(value);}
    private static BigInteger big(Long value){return value==null?null:BigInteger.valueOf(value);}
    private static BigInteger address(String value){
        if(value==null||!value.startsWith("native:"))return null;String digits=value.substring(7);
        if(digits.isEmpty()||!digits.chars().allMatch(c->c>='0'&&c<='9'))return null;
        int first=0;while(first<digits.length()-1&&digits.charAt(first)=='0')first++;
        if(digits.length()-first>20)return null;BigInteger result=new BigInteger(digits.substring(first));return result.compareTo(U64)<=0?result:null;
    }
    private static String identity(BigInteger value){return "native:"+value.and(U64);}
    private static BigInteger plus(BigInteger address,long offset){return address==null?null:address.add(BigInteger.valueOf(offset));}
    private static BigInteger signed(BigInteger value,int bits){BigInteger mask=BigInteger.ONE.shiftLeft(bits).subtract(BigInteger.ONE);BigInteger result=value.and(mask);return result.testBit(bits-1)?result.subtract(BigInteger.ONE.shiftLeft(bits)):result;}
    private static Integer integer(BigInteger value){return value==null?null:value.intValueExact();}
    private static Long longValue(BigInteger value){return value==null?null:value.longValueExact();}
    private static boolean resolved(Resolution value){return value!=null&&value.state()!=null&&value.state().ready()&&address(value.objectIdentity())!=null;}
    private static final class Memory {
        final Map<BigInteger,Integer> bytes=new HashMap<>();final Set<BigInteger> unknown=new HashSet<>();final List<Effect> effects=new ArrayList<>();
        void seed(BigInteger at,int size,BigInteger value){if(at==null||value==null)return;for(int i=0;i<size;i++)bytes.putIfAbsent(at.add(BigInteger.valueOf(i)).and(U64),value.shiftRight(i*8).and(BigInteger.valueOf(255)).intValue());}
        BigInteger read(BigInteger at,int size,boolean isSigned,BigInteger fallback){
            if(at==null)return fallback;boolean missing=false;
            for(int i=0;i<size;i++){BigInteger key=at.add(BigInteger.valueOf(i)).and(U64);if(unknown.contains(key))return null;if(!bytes.containsKey(key))missing=true;}
            if(missing)return fallback;BigInteger result=BigInteger.ZERO;
            for(int i=0;i<size;i++)result=result.or(BigInteger.valueOf(bytes.get(at.add(BigInteger.valueOf(i)).and(U64))).shiftLeft(i*8));
            return isSigned?signed(result,size*8):result;
        }
        void write(BigInteger at,int size,BigInteger value,String kind){
            BigInteger mask=BigInteger.ONE.shiftLeft(size*8).subtract(BigInteger.ONE);
            effects.add(new Store(kind,identity(at),size,read(at,size,false,null),value.and(mask)));
            for(int i=0;i<size;i++){BigInteger key=at.add(BigInteger.valueOf(i)).and(U64);bytes.put(key,value.shiftRight(i*8).and(BigInteger.valueOf(255)).intValue());unknown.remove(key);}
        }
        void unknownBuffer(BigInteger at,String token){effects.add(new UnknownBuffer("pending_commit_buffer",identity(at),8,read(at,8,false,null),token));for(int i=0;i<8;i++){BigInteger key=at.add(BigInteger.valueOf(i)).and(U64);bytes.remove(key);unknown.add(key);}}
    }
    private static BigInteger field(Memory memory,PhysicalChunk chunk,ChunkField field){return memory.read(plus(address(chunk.chunkIdentity()),field.offset),field.size,field.signed,field.raw(chunk));}
    private static Memory seed(Incoming incoming,Pending pending){
        Memory memory=new Memory();for(PhysicalChunk chunk:incoming.physicalChunks())for(ChunkField field:ChunkField.values())memory.seed(plus(address(chunk.chunkIdentity()),field.offset),field.size,field.raw(chunk));
        for(DataOccurrence row:incoming.dataOccurrences()){memory.seed(plus(address(row.recordIdentity()),8),4,big(row.rawRegiFullId()));memory.seed(plus(address(row.recordIdentity()),12),4,big(row.dataOrdinal()));}
        if(pending!=null){BigInteger header=address(pending.headerIdentity());memory.seed(header,8,address(pending.bufferIdentity()));memory.seed(plus(header,8),4,big(pending.capacity08()));memory.seed(plus(header,12),4,big(pending.count0c()));memory.seed(plus(header,16),8,address(pending.allocatorIdentity()));
            for(PendingRecord row:pending.records()){BigInteger at=address(row.recordIdentity());memory.seed(at,8,address(row.vtableIdentity()));memory.seed(plus(at,8),4,big(row.owner08()));memory.seed(plus(at,12),4,big(row.ordinal0c()));}}
        return memory;
    }
    private static Owner owner(Incoming incoming,Long requested){return incoming.ownerInputs().stream().filter(value->Objects.equals(value.requestedFullId(),requested)).findFirst().orElse(null);}
    private static Association association(Incoming incoming,Long requested){return incoming.associationInputs().stream().filter(value->Objects.equals(value.requestedFullId(),requested)).findFirst().orElse(null);}
    private static Suffix suffix(Incoming incoming){
        Long character=incoming.characterFullId148();if(Objects.equals(character,INVALID))return new Suffix(true,Branch.INVALID_CHARACTER,character,null,List.of());
        if(character==null)return new Suffix(false,null,null,null,List.of("character_full_id_148_u32"));
        if(!resolved(incoming.characterResolution()))return new Suffix(false,null,character,null,List.of("actual_character_resolution"));
        String selected=incoming.characterResolution().objectIdentity();
        if(Boolean.FALSE.equals(incoming.characterPointer1b8Present()))return new Suffix(true,Branch.NULL_CHARACTER_POINTER,character,selected,List.of());
        if(Boolean.TRUE.equals(incoming.characterPointer1b8Present()))return new Suffix(false,Branch.CHARACTER_INNER_PARTIAL,character,selected,List.of("actually_selected28CBE70_inner_effects"));
        return new Suffix(false,null,character,selected,List.of("character_pointer_1b8_present"));
    }
    private static final class EventBuilder {
        final Integer countBefore,capacityBefore;Branch branch;boolean ready;final List<String> missing=new ArrayList<>();Integer countAfter;PendingRecordResult appended;Growth growth;PreparedGrowth prepared;String conditionalBuffer;List<String> writeOrder;
        EventBuilder(Integer count,Integer capacity){countBefore=count;capacityBefore=capacity;}
        PendingEvent result(){return new PendingEvent(countBefore,capacityBefore,branch,ready,missing,countAfter,appended,growth,prepared,conditionalBuffer,writeOrder);}
    }
    private record Append(boolean ready,String reason,PendingEvent event) { }
    private static final class PendingReplay {
        final Pending raw;final Memory memory;final BigInteger header;final String canonical,callback;final int incomingIndex;
        String buffer;Integer count,capacity;List<PendingRecordResult> freshRecords=List.of();final List<PendingRecord> capturedRecords;boolean fresh;int growths;final List<PendingEvent> events=new ArrayList<>();
        PendingReplay(Pending raw,Memory memory,String canonical,String callback,int incomingIndex){this.raw=raw;this.memory=memory;this.canonical=canonical;this.callback=callback;this.incomingIndex=incomingIndex;header=raw==null?null:address(raw.headerIdentity());buffer=raw==null?null:raw.bufferIdentity();count=raw==null?null:raw.count0c();capacity=raw==null?null:raw.capacity08();capturedRecords=raw==null?List.of():raw.records();}
        Integer number(boolean isCount){return integer(memory.read(plus(header,isCount?12:8),4,true,big(isCount?count:capacity)));}
        String bufferIdentity(){if(fresh)return buffer;BigInteger pointer=memory.read(header,8,false,address(buffer));return pointer==null?null:identity(pointer);}
        PendingRecordResult record(int index){
            if(fresh)return freshRecords.stream().filter(row->row.nativeIndex()==index).findFirst().orElse(null);
            BigInteger base=address(bufferIdentity()),at=base==null?null:base.add(BigInteger.valueOf((long)index*16)).and(U64);
            PendingRecord original=currentCaptured().stream().filter(row->row.nativeIndex()==index).findFirst().orElse(null);
            BigInteger vtable=memory.read(at,8,false,original==null?null:address(original.vtableIdentity()));
            Long owner=longValue(memory.read(plus(at,8),4,false,original==null?null:big(original.owner08())));
            Integer ordinal=integer(memory.read(plus(at,12),4,true,original==null?null:big(original.ordinal0c())));
            if(vtable==null||owner==null||ordinal==null)return null;String table=identity(vtable),target=null;
            if(original!=null&&Objects.equals(original.vtableIdentity(),table))target=original.slot0TargetIdentity();
            else for(PendingRecord row:currentCaptured())if(Objects.equals(row.vtableIdentity(),table)){target=row.slot0TargetIdentity();break;}
            return new PendingRecordResult(index,at==null?null:identity(at),table,target,owner,ordinal);
        }
        Append missing(EventBuilder event,String reason){event.missing.add(reason);PendingEvent result=event.result();events.add(result);return new Append(false,reason,result);}
        Append append(PhysicalChunk chunk){
            Integer beforeCount=number(true),beforeCapacity=number(false);EventBuilder event=new EventBuilder(beforeCount,beforeCapacity);
            if(beforeCount==null||beforeCapacity==null||header==null)return missing(event,"selected_pending_header_count_capacity");
            if(address(canonical)==null)return missing(event,"canonical_pending_vtable_identity");
            if(!beforeCount.equals(beforeCapacity)){
                event.branch=Branch.NO_GROWTH;BigInteger base=address(bufferIdentity());if(base==null&&!fresh)return missing(event,"selected_pending_buffer_identity");
                BigInteger destination=base==null?null:base.add(BigInteger.valueOf((long)beforeCount*16)).and(U64);
                if(destination!=null){memory.write(destination,8,address(canonical),"pending_record_init_vtable");memory.write(plus(destination,8),4,BigInteger.valueOf(INVALID),"pending_record_init_owner");memory.write(plus(destination,12),4,BigInteger.ZERO,"pending_record_init_ordinal");}
                Integer ordinal=integer(field(memory,chunk,ChunkField.ORDINAL));Long owner=longValue(field(memory,chunk,ChunkField.OWNER));
                if(owner==null||ordinal==null)return missing(event,"pending_reload_chunk_owner8_rawordinalC");
                PendingRecordResult record=new PendingRecordResult(beforeCount,destination==null?buffer+":record:"+beforeCount:identity(destination),canonical,callback,owner,ordinal);
                if(destination!=null){memory.write(plus(destination,12),4,BigInteger.valueOf(ordinal),"pending_record_raw_ordinal");memory.write(plus(destination,8),4,BigInteger.valueOf(owner),"pending_record_raw_owner");}
                Integer reload=number(true);if(reload==null)return missing(event,"pending_count_after_record_stores");count=reload+1;capacity=number(false);
                if(fresh){List<PendingRecordResult> next=new ArrayList<>(freshRecords.stream().filter(row->row.nativeIndex()!=beforeCount).toList());next.add(record);freshRecords=List.copyOf(next);}
                else {List<PendingRecord> next=new ArrayList<>(currentCaptured().stream().filter(row->row.nativeIndex()!=beforeCount).toList());next.add(new PendingRecord(null,record.nativeIndex(),record.recordIdentity(),record.vtableIdentity(),record.slot0TargetIdentity(),record.owner08(),record.ordinal0c()));capturedRecordsOverride=List.copyOf(next);}
                memory.write(plus(header,12),4,BigInteger.valueOf(count),"pending_count_increment");event.ready=true;event.countAfter=count;event.appended=record;
            }else{
                event.branch=Branch.GROWTH;BigInteger allocator=memory.read(plus(header,16),8,false,null);String selectedAllocator=allocator==null?(raw==null?null:raw.allocatorIdentity()):identity(allocator);
                if(address(selectedAllocator)==null)return missing(event,"selected_pending_allocator_identity");
                int newCount=beforeCount+1;float scaled=beforeCapacity.floatValue()*1.5f;
                int converted=Float.isFinite(scaled)&&scaled>=-2147483648.0&&scaled<2147483648.0?(int)scaled:Integer.MIN_VALUE;
                int newCapacity=Math.max(newCount,converted);event.growth=new Growth(newCount,newCapacity,Integer.toUnsignedLong(newCapacity)*16,8);
                Long owner=longValue(field(memory,chunk,ChunkField.OWNER));Integer ordinal=integer(field(memory,chunk,ChunkField.ORDINAL));
                if(owner==null||ordinal==null)return missing(event,"pending_reload_chunk_owner8_rawordinalC");
                String token="conditional:incoming:"+incomingIndex+":pending-buffer:"+(growths+1);Integer oldCount=number(true);
                if(oldCount==null)return missing(event,"growth_reloaded_old_count");List<PendingRecordResult> oldRecords=new ArrayList<>();
                for(int index=0;index<Math.max(oldCount,0);index++){PendingRecordResult row=record(index);if(row==null)return missing(event,"growth_existing_typed_record["+index+"]");oldRecords.add(row);}
                List<PendingRecordResult> prepared=new ArrayList<>();for(int index=0;index<oldRecords.size();index++){PendingRecordResult row=oldRecords.get(index);prepared.add(new PendingRecordResult(row.nativeIndex(),token+":record:"+index,canonical,callback,row.owner08(),row.ordinal0c()));}
                prepared.add(new PendingRecordResult(oldCount,token+":record:"+oldCount,canonical,callback,owner,ordinal));List<OldCallback> callbacks=new ArrayList<>();
                event.prepared=new PreparedGrowth(prepared,oldCount,callbacks);
                for(int index=0;index<oldRecords.size();index++){String target=oldRecords.get(index).slot0TargetIdentity();boolean noop=target!=null&&Objects.equals(target,callback);callbacks.add(new OldCallback(index,target,noop));event.prepared=new PreparedGrowth(prepared,oldCount,callbacks);if(!noop)return missing(event,"selected_old_pending_record_slot0["+index+"]_source");}
                growths++;count=newCount;capacity=newCapacity;buffer=token;freshRecords=List.copyOf(prepared);fresh=true;
                memory.write(plus(header,8),4,BigInteger.valueOf(newCapacity),"pending_commit_capacity");memory.unknownBuffer(header,token);memory.write(plus(header,12),4,BigInteger.valueOf(newCount),"pending_commit_count");
                event.ready=true;event.countAfter=newCount;event.conditionalBuffer=token;event.writeOrder=List.of("capacity8","buffer0","countC");
            }
            PendingEvent result=event.result();events.add(result);return new Append(true,null,result);
        }
        List<PendingRecord> capturedRecordsOverride;
        List<PendingRecord> currentCaptured(){return capturedRecordsOverride==null?capturedRecords:capturedRecordsOverride;}
        PendingResult result(){Integer actual=number(true);List<PendingRecordResult> records=new ArrayList<>();for(int index=0;index<Math.max(actual==null?0:actual,0);index++){PendingRecordResult row=record(index);if(row==null)break;records.add(row);}return new PendingResult(raw==null?null:raw.headerIdentity(),raw==null?null:raw.bufferIdentity(),buffer,actual,number(false),records,events);}
    }
    private static final class OccurrenceBuilder {
        final int index;final String identity;Long requested;Integer ordinal;String physical;boolean ready;Branch branch;boolean cleared;Boolean predicate;Branch dateBranch;Long output;Boolean greater;PendingEvent event;final List<String> missing=new ArrayList<>();boolean selected;String selectedRegi,fallback;
        OccurrenceBuilder(DataOccurrence row){index=row.nativeIndex();identity=row.recordIdentity();}
        Occurrence result(){return new Occurrence(index,identity,requested,ordinal,physical,ready,branch,cleared,predicate,dateBranch,output,greater,event,missing,selected,selectedRegi,fallback);}
    }
    private static void stop(List<String> missing,OccurrenceBuilder item,String reason){if(item!=null)item.missing.add(reason);missing.add(reason);}
    private static IncomingResult projectIncoming(Incoming incoming,ArmyDetachmentDataInputs top,Long date){
        Pending pendingRaw=incoming.pending();Memory memory=seed(incoming,pendingRaw);PendingReplay pending=new PendingReplay(pendingRaw,memory,top.canonicalPendingVtableIdentity(),top.readyPendingCallbackIdentity(),incoming.nativeIndex());
        List<OccurrenceBuilder> occurrences=new ArrayList<>();List<String> missing=new ArrayList<>();Suffix suffix=suffix(incoming);
        BigInteger cursor=address(incoming.capturedCursorIdentity()),end=address(incoming.capturedEndIdentity());
        if(cursor==null||end==null||incoming.dataCount()==null)stop(missing,null,"captured_DATA_signed_count_cursor_end");
        List<DataOccurrence> rows=incoming.dataOccurrences();String heldFallback=rows.isEmpty()?null:rows.get(0).heldFallbackRegiIdentity();int completed=0;
        if(cursor!=null&&end!=null&&missing.isEmpty())for(DataOccurrence row:rows){
            if(cursor.equals(end))break;OccurrenceBuilder item=new OccurrenceBuilder(row);occurrences.add(item);
            if(!Objects.equals(address(row.recordIdentity()),cursor)){stop(missing,item,"next_source_visited_DATA_cursor");break;}
            Long requested=longValue(memory.read(plus(cursor,8),4,false,big(row.rawRegiFullId())));Integer ordinal=integer(memory.read(plus(cursor,12),4,true,big(row.dataOrdinal())));item.requested=requested;item.ordinal=ordinal;
            DataOccurrence source=null;for(DataOccurrence candidate:rows)if(Objects.equals(candidate.rawRegiFullId(),requested)&&Objects.equals(candidate.heldFallbackRegiIdentity(),heldFallback)){source=candidate;break;}
            if(source==null||!resolved(source.resolution())||ordinal==null){stop(missing,item,"fresh_selected_Regi_resolution_for_current_DATA_request");break;}
            Resolution resolution=source.resolution();Long magic=source.magic14(),fullId=resolution.selectedFullId();item.selected=true;item.selectedRegi=resolution.objectIdentity();item.fallback=heldFallback;
            if(magic==null||fullId==null){stop(missing,item,"selected_Regi_magic14_fullID10");break;}
            if(magic!=REGI||fullId==INVALID){item.ready=true;item.branch=Branch.INVALID_REGI;cursor=plus(cursor,16).and(U64);completed++;continue;}
            BigInteger physical=address(resolution.objectIdentity()).add(BigInteger.valueOf(0x18)).add(BigInteger.valueOf(ordinal).multiply(BigInteger.valueOf(0x24))).and(U64);item.physical=identity(physical);
            if(physical.signum()==0){item.ready=true;item.branch=Branch.NULL_PHYSICAL;cursor=plus(cursor,16).and(U64);completed++;continue;}
            PhysicalChunk chunk=incoming.physicalChunks().stream().filter(value->Objects.equals(address(value.chunkIdentity()),physical)).findFirst().orElse(null);
            if(chunk==null){stop(missing,item,"selected_physical_chunk_snapshot");break;}
            Integer maximum=integer(field(memory,chunk,ChunkField.MAXIMUM)),current=integer(field(memory,chunk,ChunkField.CURRENT));
            if(maximum==null||current==null){stop(missing,item,"physical_maximum0_current4");break;}
            if(current>=maximum){
                memory.write(plus(physical,4),4,BigInteger.valueOf(maximum),"setter_exact_current_store");Long association=longValue(field(memory,chunk,ChunkField.ASSOCIATION));
                if(association==null){stop(missing,item,"setter_association10");break;}
                Integer flag=association==INVALID?integer(field(memory,chunk,ChunkField.FLAG)):null;
                if(association==INVALID&&flag==null){stop(missing,item,"setter_flag14_for_cleared_association");break;}
                if(association==INVALID&&flag==0){Owner owner=owner(incoming,longValue(field(memory,chunk,ChunkField.OWNER)));
                    if(owner==null||!resolved(owner.resolution())||owner.state138()==null){stop(missing,item,"setter_actual_owner_Regi138");break;}
                    if(owner.state138()==0){if(owner.definitionMagic38()==null){stop(missing,item,"setter_actual_owner_definition_magic38");break;}if(owner.definitionMagic38()!=0x4744624fL){memory.write(physical,8,BigInteger.ZERO,"setter_special_pair_clear");item.cleared=true;}}
                }
            }
            Long associationId=longValue(field(memory,chunk,ChunkField.ASSOCIATION));Association association=association(incoming,associationId);
            if(association==null||association.contextCount0c()==null||!resolved(association.arrgResolution())||!resolved(association.armyResolution())||!resolved(association.unitResolution())||!resolved(association.characterResolution())){
                stop(missing,item,"evolved_association2658050_chain_raw_context_count");break;
            }
            boolean predicate=association.contextCount0c()!=0;item.predicate=predicate;
            if(predicate){
                memory.write(plus(physical,28),8,BigInteger.valueOf(SENTINEL),"caller_date_sentinel");
                if(date==null){stop(missing,item,"current_date_storage_raw64_conditional_entry");break;}
                if(address(incoming.passedProvinceIdentity())==null){stop(missing,item,"actual_passed_Province_identity");break;}
                Long ownerId=longValue(field(memory,chunk,ChunkField.OWNER));Owner owner=owner(incoming,ownerId);
                if(owner==null||!resolved(owner.resolution())||owner.originMagic85c()==null){stop(missing,item,"date_actual_owner_Regi120_origin");break;}
                DateInput dateRow=incoming.dateInputs().stream().filter(value->Objects.equals(value.associationFullId(),associationId)&&Objects.equals(value.ownerFullId(),ownerId)).findFirst().orElse(null);
                Long output;
                if(owner.originMagic85c()!=PROV){
                    if(dateRow==null||dateRow.capitalOriginMagic85c()==null){stop(missing,item,"actual_native_capital_origin_tag");break;}
                    if(dateRow.capitalOriginMagic85c()!=PROV){output=date;item.dateBranch=Branch.BOTH_NON_PROV;}
                    else{output=dateRow.outputDateRaw64();item.dateBranch=Branch.CAPITAL_ORIGIN;}
                }else{output=dateRow==null?null:dateRow.outputDateRaw64();item.dateBranch=Branch.REGI_ORIGIN;}
                if(item.dateBranch!=Branch.BOTH_NON_PROV&&(output==null||dateRow==null||!Objects.equals(dateRow.unitIdentity(),association.unitResolution().objectIdentity())
                        ||!Objects.equals(date,top.currentDateStorageRaw64())||owner.originMagic85c()==PROV&&!Objects.equals(dateRow.sourceOriginIdentity(),owner.originIdentity()))){
                    stop(missing,item,"actual_selected_current_input2C54340_full_date");break;
                }
                item.output=output;boolean greater=output.intValue()>date.intValue();item.greater=greater;
                if(greater){memory.write(plus(physical,28),8,BigInteger.valueOf(output),"caller_full_computed_date_store");
                    if(address(top.primaryReceiverIdentity())==null){stop(missing,item,"actual_primary_receiver_identity");break;}
                    Append appended=pending.append(chunk);item.event=appended.event();if(!appended.ready()){stop(missing,item,appended.reason());break;}
                }
            }
            memory.write(plus(physical,16),4,BigInteger.valueOf(INVALID),"caller_association_clear");memory.write(plus(physical,20),1,BigInteger.ZERO,"caller_flag_clear");
            int nextIndex=row.nativeIndex()+1;heldFallback=nextIndex<rows.size()?rows.get(nextIndex).heldFallbackRegiIdentity():row.heldFallbackRegiIdentity();
            item.ready=true;item.branch=Branch.PROCESSED;cursor=plus(cursor,16).and(U64);completed++;
        }
        if(cursor!=null&&end!=null&&!cursor.equals(end)&&missing.isEmpty())stop(missing,null,"remaining_source_visited_DATA_occurrences");
        boolean ready=cursor!=null&&end!=null&&cursor.equals(end)&&missing.isEmpty();List<ChunkResult> chunks=new ArrayList<>();
        for(PhysicalChunk chunk:incoming.physicalChunks())chunks.add(new ChunkResult(chunk,integer(field(memory,chunk,ChunkField.MAXIMUM)),integer(field(memory,chunk,ChunkField.CURRENT)),longValue(field(memory,chunk,ChunkField.OWNER)),integer(field(memory,chunk,ChunkField.ORDINAL)),longValue(field(memory,chunk,ChunkField.ASSOCIATION)),integer(field(memory,chunk,ChunkField.FLAG)),longValue(field(memory,chunk,ChunkField.DATE))));
        return new IncomingResult(incoming.nativeIndex(),incoming.arrgIdentity(),ready,ready?Availability.AVAILABLE:Availability.PARTIAL,missing.isEmpty()?null:missing.get(0),incoming.dataCount(),incoming.capturedCursorIdentity(),incoming.capturedEndIdentity(),cursor==null?null:identity(cursor),date,completed,occurrences.size(),occurrences.stream().map(OccurrenceBuilder::result).toList(),chunks,memory.effects,missing,suffix,ready&&suffix.ready(),pending.result());
    }
    public static Result project(ArmyDetachmentDataInputs inputs,Long currentDateStorageRaw64){
        if(inputs==null)return new Result(Availability.UNAVAILABLE,false,false,false,List.of(),List.of(),List.of("current_detachment_data_inputs_v1"));
        Long date=currentDateStorageRaw64==null?inputs.currentDateStorageRaw64():currentDateStorageRaw64;
        List<IncomingResult> incoming=inputs.incoming().stream().map(row->projectIncoming(row,inputs,date)).toList();Map<Integer,IncomingResult> byIndex=new HashMap<>();for(IncomingResult row:incoming)byIndex.put(row.nativeIndex(),row);
        List<CandidateResult> candidates=new ArrayList<>();List<String> missing=new ArrayList<>();
        for(Candidate row:inputs.candidateOccurrences()){
            List<String> reasons=new ArrayList<>();boolean ready=false;
            if(Boolean.FALSE.equals(row.incomingValid())&&resolved(row.resolution()))ready=true;
            else if(Boolean.TRUE.equals(row.incomingValid())){IncomingResult seed=byIndex.get(row.incomingIndex());if(seed==null)reasons.add("independent_incoming_snapshot");else{ready=seed.ready();reasons.addAll(seed.missingInputs());}}
            else reasons.add("current_incoming_ArRg_admission");
            candidates.add(new CandidateResult(row.nativeIndex(),row.rawFullId(),row.resolution()==null?null:row.resolution().objectIdentity(),row.incomingIndex(),row.incomingValid(),ready,reasons));
            for(String reason:reasons)missing.add("candidate["+row.nativeIndex()+"]."+reason);
        }
        if(!inputs.selectionReady())missing.add("current_candidate_selection");if(!inputs.rosterReady())missing.add("whole_current_candidate_roster");
        boolean ready=inputs.selectionReady()&&inputs.rosterReady()&&candidates.stream().allMatch(CandidateResult::ready);
        return new Result(ready?Availability.AVAILABLE:Availability.PARTIAL,ready,inputs.selectionReady(),inputs.rosterReady(),candidates,incoming,missing);
    }
    public static JsonNode nativeJson(Result result){return encode(result,false);}
    /** V2 crosses JavaScript using explicitly classified 64-bit values as decimal strings. No field-name guessing. */
    public static JsonNode publicV2Json(Result result){return encode(result,true);}
    private static ObjectNode encode(Result result,boolean publicV2){
        Objects.requireNonNull(result);ObjectNode node=StrictJson.object();node.put("projection_kind","same_input_current_detachment_data_prefix").put("source_contract_game_version","1.20.0.3")
                .put("native_caller_rva","0x2633FF0").put("input_basis","standalone_current_incoming_seed_not_parent_detach_replay");
        node.put("status",wire(result.status())).put("ready",result.ready()).put("selection_ready",result.selectionReady()).put("roster_ready",result.rosterReady());
        ArrayNode candidates=node.putArray("candidate_occurrences");for(CandidateResult row:result.candidates()){
            ObjectNode item=candidates.addObject();item.put("native_index",row.nativeIndex()).put("raw_full_id_u32",row.rawFullId()).put("resolved_arrg_identity",row.resolvedArrgIdentity())
                    .put("incoming_index",row.incomingIndex()).put("incoming_valid",row.incomingValid()).put("ready",row.ready());strings(item.putArray("missing_inputs"),row.missingInputs());
        }
        ArrayNode incoming=node.putArray("incoming");for(IncomingResult row:result.incoming())incoming.add(incoming(row,publicV2));strings(node.putArray("missing_inputs"),result.missingInputs());falseFlags(node);return node;
    }
    private static ObjectNode incoming(IncomingResult row,boolean publicV2){
        ObjectNode node=StrictJson.object();node.put("native_index",row.nativeIndex()).put("arrg_identity",row.arrgIdentity()).put("input_basis","standalone_current2633FF0_seed_no_between_ArRg_replay")
                .put("ready",row.ready()).put("data_prefix_ready",row.ready()).put("status",wire(row.status())).put("unavailable_reason",row.unavailableReason()).put("data_count_raw_i32",row.dataCount())
                .put("captured_cursor_identity",row.capturedCursorIdentity()).put("captured_end_identity",row.capturedEndIdentity()).put("terminal_cursor_identity",row.terminalCursorIdentity());
        signed64(node,"conditional_entry_date_raw64",row.conditionalEntryDateRaw64(),publicV2);node.putNull("actual_caller_date_raw64");
        node.put("completed_data_occurrence_count",row.completedOccurrences()).put("begun_data_occurrence_count",row.begunOccurrences());
        ArrayNode occurrences=node.putArray("occurrences");for(Occurrence item:row.occurrences()){
            ObjectNode value=occurrences.addObject();value.put("native_index",item.nativeIndex()).put("record_identity",item.recordIdentity()).put("raw_regi_full_id_u32",item.rawRegiFullId())
                    .put("data_ordinal_raw_i32",item.dataOrdinal()).put("physical_chunk_identity",item.physicalChunkIdentity()).put("ready",item.ready()).put("branch",branch(item.branch()))
                    .put("setter_pair_cleared",item.setterPairCleared()).put("predicate",item.predicate()).put("date_branch",branch(item.dateBranch()));
            signed64(value,"output_date_raw64",item.outputDateRaw64(),publicV2);value.put("date_greater",item.dateGreater());
            value.set("pending_event",item.pendingEvent()==null?value.nullNode():event(item.pendingEvent(),publicV2));strings(value.putArray("missing_inputs"),item.missingInputs());
            if(item.resolutionSelected())value.put("selected_regi_identity",item.selectedRegiIdentity()).put("held_fallback_regi_identity",item.heldFallbackRegiIdentity());
        }
        ArrayNode chunks=node.putArray("physical_chunks");for(ChunkResult chunk:row.chunks()){
            ObjectNode value=ArmyStrengthsDetachment.encodePhysicalChunk(chunk.observed()).deepCopy();chunks.add(value);value.put("maximum_00_raw_i32",chunk.maximum00()).put("current_04_raw_i32",chunk.current04())
                    .put("owner_08_raw_u32",chunk.owner08()).put("ordinal_0c_raw_i32",chunk.ordinal0c()).put("association_10_raw_u32",chunk.association10()).put("flag_14_raw_u8",chunk.flag14());
            signed64(value,"date_1c_raw64",chunk.date1cRaw64(),publicV2);
        }
        ArrayNode effects=node.putArray("effects");for(Effect effect:row.effects()){
            ObjectNode value=effects.addObject();value.put("kind",effect.kind()).put("address_identity",effect.addressIdentity()).put("size",effect.size());
            raw(value,"before_raw",effect.beforeRaw(),publicV2&&effect.size()==8);
            if(effect instanceof Store store)raw(value,"after_raw",store.afterRaw(),publicV2&&effect.size()==8);
            else{UnknownBuffer unknown=(UnknownBuffer)effect;value.putNull("after_raw");value.put("conditional_buffer_identity",unknown.conditionalBufferIdentity()).putNull("actual_buffer_after_identity");}
        }
        strings(node.putArray("missing_inputs"),row.missingInputs());Suffix suffix=row.characterSuffix();ObjectNode character=node.putObject("Character_suffix");
        character.put("ready",suffix.ready()).put("branch",branch(suffix.branch())).put("character_full_id_148_u32",suffix.characterFullId()).put("actual_selected_character_identity",suffix.actualSelectedCharacterIdentity());
        strings(character.putArray("missing_inputs"),suffix.missingInputs());node.put("whole_conditional_caller_ready",row.wholeConditionalCallerReady());
        PendingResult pending=row.conditionalPending();ObjectNode conditional=node.putObject("conditional_pending");
        conditional.put("observed_header_identity",pending.observedHeaderIdentity()).put("observed_buffer_identity",pending.observedBufferIdentity()).put("conditional_buffer_identity",pending.conditionalBufferIdentity())
                .putNull("actual_buffer_after_identity").put("conditional_count_0c_raw_i32",pending.conditionalCount()).put("conditional_capacity_08_raw_i32",pending.conditionalCapacity());
        ArrayNode records=conditional.putArray("conditional_records");for(PendingRecordResult record:pending.records())records.add(record(record));
        ArrayNode events=conditional.putArray("events");for(PendingEvent event:pending.events())events.add(event(event,publicV2));falseFlags(node);return node;
    }
    private static ObjectNode record(PendingRecordResult row){return StrictJson.object().put("native_index",row.nativeIndex()).put("record_identity",row.recordIdentity()).put("vtable_identity",row.vtableIdentity())
            .put("slot0_target_identity",row.slot0TargetIdentity()).put("owner_08_raw_u32",row.owner08()).put("ordinal_0c_raw_i32",row.ordinal0c());}
    private static ObjectNode event(PendingEvent event,boolean publicV2){
        ObjectNode node=StrictJson.object();node.put("count_before",event.countBefore()).put("capacity_before",event.capacityBefore()).put("branch",branch(event.branch())).put("ready",event.ready());strings(node.putArray("missing_inputs"),event.missingInputs());
        if(event.countAfter()!=null)node.put("count_after",event.countAfter());if(event.appendedRecord()!=null)node.set("appended_record",record(event.appendedRecord()));
        if(event.growth()!=null){Growth growth=event.growth();node.put("new_count",growth.newCount()).put("new_capacity",growth.newCapacity());raw(node,"allocation_bytes",BigInteger.valueOf(growth.allocationBytes()),publicV2);node.put("allocation_alignment",growth.allocationAlignment());}
        if(event.prepared()!=null){PreparedGrowth prepared=event.prepared();ArrayNode records=node.putArray("prepared_records");for(PendingRecordResult row:prepared.records())records.add(record(row));
            node.put("captured_old_count",prepared.capturedOldCount());ArrayNode callbacks=node.putArray("old_record_callbacks");for(OldCallback callback:prepared.oldCallbacks())callbacks.addObject().put("native_index",callback.nativeIndex()).put("target_identity",callback.targetIdentity()).put("edx",0).put("source_noop_ready",callback.sourceNoopReady());}
        if(event.conditionalBufferIdentity()!=null)node.put("conditional_buffer_identity",event.conditionalBufferIdentity());if(event.headerWriteOrder()!=null)strings(node.putArray("header_write_order"),event.headerWriteOrder());return node;
    }
    private static void signed64(ObjectNode node,String field,Long value,boolean decimal){if(value==null)node.putNull(field);else if(decimal)node.put(field,Long.toString(value));else node.put(field,value.longValue());}
    private static void raw(ObjectNode node,String field,BigInteger value,boolean decimal){if(value==null)node.putNull(field);else if(decimal)node.put(field,value.toString());else node.put(field,value);}
    private static void strings(ArrayNode array,List<String> values){values.forEach(array::add);}
    private static String wire(Availability value){return value.name().toLowerCase(java.util.Locale.ROOT);}
    private static String branch(Branch value){return value==null?null:value.wire();}
    private static void falseFlags(ObjectNode value){for(String field:List.of("actual_effects","actual_detachment","future_drain","lifecycle","fullmonthly","future_drain_ready","full_army_lifecycle_ready","full_monthly_ready","full_calendar_ready","live"))value.put(field,false);value.putNull("actual_post_stage").put("native_writes_executed",0).put("native_mutator_invocations",0);}
}
