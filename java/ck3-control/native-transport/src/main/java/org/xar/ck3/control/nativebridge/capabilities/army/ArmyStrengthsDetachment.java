package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.military.monthlycaller.ArmyMonthlyCaller;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyDetachmentDataInputs.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyDetachmentInputsCodec.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsFamilies.Key.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPipeline.Stage.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPublicNumbers.Domain.SIGNED_64;

/** Original independent current-seed producers. Conditional previews never grant native execution or future-state evidence. */
public final class ArmyStrengthsDetachment {
    private ArmyStrengthsDetachment() { }
    private static final long INVALID=4294967295L,REGI=0x52656769L;
    public static ArmyDetachmentDataInputs decodeData(JsonNode raw) { return ArmyDetachmentInputsCodec.decodeData(raw); }
    public static JsonNode encodeData(ArmyDetachmentDataInputs value) { return ArmyDetachmentInputsCodec.encodeData(value); }
    public static JsonNode encodePhysicalChunk(PhysicalChunk value) { return ArmyDetachmentInputsCodec.encodePhysicalChunk(value); }
    public static <T> T family(ArmyStrengths.Row row,ArmyStrengthsFamilies.Key key,Class<T> type) {
        var found=row.families().stream().filter(v->v.key()==key).toList();require(found.size()<=1,"duplicate detachment family");
        if(found.isEmpty())return null;var value=found.getFirst();require(value.valueType().equals(type),"detachment family exact type differs");
        return value.value() instanceof Present<?> p?type.cast(p.value()):null;
    }
    public static Long monthlyDate(ArmyStrengths.Row row) { ArmyMonthlyCaller.Input input=family(row,MONTHLY_CALLER_EFFECT_INPUTS_V1,ArmyMonthlyCaller.Input.class);return input==null?null:input.currentDateStorageRaw64(); }
    private static <T> Field<T> decode(Field<RawJson> field,Function<JsonNode,T> decoder) {
        if(field instanceof Missing<?>)return new Missing<>();if(field instanceof NullValue<?>)return new NullValue<>();
        if(field instanceof Present<RawJson> present) { T result=decoder.apply(ArmyStrengthsCodec.parseValue(present.value()));return result==null?new NullValue<>():new Present<>(result); }throw new IllegalArgumentException("unknown detachment field state");
    }
    private static <T> RawJson encode(Field<T> field,Function<T,JsonNode> encoder) { return raw(field instanceof Present<T> p?encoder.apply(p.value()):JsonNodeFactory.instance.nullNode()); }
    private static RawJson wide(RawJson nativeJson,String... paths) { return ArmyStrengthsPublicNumbers.encode(nativeJson,java.util.Arrays.stream(paths).map(p->new ArmyStrengthsPublicNumbers.Rule(p,SIGNED_64)).toList()); }
    public static void install(ArmyStrengthsFamilies.Registry families,ArmyStrengthsPipeline pipeline,ExactRef actualJavaBundleSource) {
        Objects.requireNonNull(actualJavaBundleSource);
        families.register(CURRENT_CANDIDATE_DETACHMENT_MAPPER_INPUTS_V1,MapperInputs.class,(f,row)->decode(f,ArmyDetachmentInputsCodec::decodeMapper),f->encode(f,ArmyDetachmentInputsCodec::encodeMapper),f->encode(f,ArmyDetachmentInputsCodec::encodeMapper),actualJavaBundleSource);
        families.register(CURRENT_DETACHMENT_DATA_INPUTS_V1,ArmyDetachmentDataInputs.class,(f,row)->decode(f,ArmyStrengthsDetachment::decodeData),f->encode(f,ArmyStrengthsDetachment::encodeData),f->wide(encode(f,ArmyStrengthsDetachment::encodeData),"/current_date_storage_raw64","/incoming/*/physical_chunks/*/date_1c_raw64","/incoming/*/date_inputs/*/output_date_raw64"),actualJavaBundleSource);
        families.register(CURRENT_DETACHMENT_CALLBACK_INPUTS_V1,CallbackInputs.class,(f,row)->decode(f,ArmyDetachmentInputsCodec::decodeCallback),f->encode(f,ArmyDetachmentInputsCodec::encodeCallback),f->wide(encode(f,ArmyDetachmentInputsCodec::encodeCallback),"/current_date_storage_raw64"),actualJavaBundleSource);
        families.register(CURRENT_DETACHMENT_STORE_INPUTS_V1,StoreInputs.class,(f,row)->decode(f,ArmyDetachmentInputsCodec::decodeStore),f->encode(f,ArmyDetachmentInputsCodec::encodeStore),f->wide(encode(f,ArmyDetachmentInputsCodec::encodeStore),"/current_date_storage_raw64"),actualJavaBundleSource);
        families.register(CURRENT_CHARACTER_DETACHMENT_INPUTS_V1,CharacterInputs.class,(f,row)->decode(f,ArmyDetachmentInputsCodec::decodeCharacter),f->encode(f,ArmyDetachmentInputsCodec::encodeCharacter),f->wide(encode(f,ArmyDetachmentInputsCodec::encodeCharacter),"/current_date_storage_raw64","/requests/*/extension_100_raw64"),actualJavaBundleSource);
        pipeline.register(SAME_INPUT_CURRENT_CANDIDATE_DETACHMENT_MAPPER_V1,MapperBatch.class,List.of(),(input,earlier)->new MapperBatch(input.selected().stream().map(ArmyStrengthsDetachment::buildMapper).toList()),ArmyStrengthsDetachment::mapperBatchJson,ArmyStrengthsDetachment::mapperBatchJson,actualJavaBundleSource);
        pipeline.register(CONDITIONAL_CURRENT_DETACHMENT_CALLBACK_V1,CallbackBatch.class,List.of(),(input,earlier)->new CallbackBatch(input.selected().stream().map(row->new CallbackArmy(row.core().army(),projectCallback(family(row,CURRENT_DETACHMENT_CALLBACK_INPUTS_V1,CallbackInputs.class)))).toList()),b->raw(array(b.rows(),r->entry(r.army(),callbackJson(r.projection())))),b->wide(raw(array(b.rows(),r->entry(r.army(),callbackJson(r.projection())))),"/*/projection/current_date_storage_raw64"),actualJavaBundleSource);
        pipeline.register(CURRENT_DETACHMENT_STORE_ADMISSION_V1,StoreBatch.class,List.of(),(input,earlier)->new StoreBatch(input.selected().stream().map(row->new StoreArmy(row.core().army(),projectStore(family(row,CURRENT_DETACHMENT_STORE_INPUTS_V1,StoreInputs.class)))).toList()),b->raw(array(b.rows(),r->entry(r.army(),storeJson(r.projection())))),b->wide(raw(array(b.rows(),r->entry(r.army(),storeJson(r.projection())))),"/*/projection/current_date_storage_raw64"),actualJavaBundleSource);
        pipeline.register(CURRENT_CHARACTER_DETACHMENT_SUFFIX_V1,CharacterBatch.class,List.of(),(input,earlier)->new CharacterBatch(input.selected().stream().map(row->new CharacterArmy(row.core().army(),projectCharacter(family(row,CURRENT_CHARACTER_DETACHMENT_INPUTS_V1,CharacterInputs.class)))).toList()),b->raw(array(b.rows(),r->entry(r.army(),characterJson(r.projection())))),b->wide(raw(array(b.rows(),r->entry(r.army(),characterJson(r.projection())))),"/*/projection/current_date_storage_raw64","/*/projection/requests/*/observed_current_extension/storage_100_raw64","/*/projection/requests/*/source_defined_reset_descriptors/1/source_defined_after_raw64"),actualJavaBundleSource);
        // DATA stage is installed once by ArmyDetachmentDataProjection with its actual separate kernel source.
    }
    public record MapperArmy(PublicUnitId army,Field<FullId> nativeArmy,MapperResult projection) { }
    public record CallbackArmy(PublicUnitId army,CallbackResult projection) { }
    public record StoreArmy(PublicUnitId army,StoreResult projection) { }
    public record CharacterArmy(PublicUnitId army,CharacterResult projection) { }
    public record MapperBatch(List<MapperArmy> rows) { public MapperBatch { rows=List.copyOf(rows); } }
    public record CallbackBatch(List<CallbackArmy> rows) { public CallbackBatch { rows=List.copyOf(rows); } }
    public record StoreBatch(List<StoreArmy> rows) { public StoreBatch { rows=List.copyOf(rows); } }
    public record CharacterBatch(List<CharacterArmy> rows) { public CharacterBatch { rows=List.copyOf(rows); } }
    public static MapperArmy buildMapper(ArmyStrengths.Row row) { return new MapperArmy(row.core().army(),row.core().nativeArmy(),projectMapper(family(row,CURRENT_CANDIDATE_DETACHMENT_MAPPER_INPUTS_V1,MapperInputs.class))); }
    private static RawJson mapperBatchJson(MapperBatch batch) { return raw(array(batch.rows(),r->{ObjectNode projection=(ObjectNode)mapperJson(r.projection());projection.put("subject_army_id",r.army().value());if(r.nativeArmy() instanceof Present<FullId> p)projection.put("subject_native_carmy_id",p.value().value());else projection.putNull("subject_native_carmy_id");return entry(r.army(),projection);})); }

    public enum CountBranch { MAXIMUM_ZERO_SKIP,NONZERO_CURRENT_DIFFERENCE,STATE3_ZERO_CURRENT_SKIP,ZERO_CURRENT_DIFFERENCE }
    public enum ReturnChoice { SELECTED_REGI,NATIVE_FALLBACK }
    public record ChunkResult(int physicalIndex,boolean ready,Integer delta,CountBranch branch,List<String> missing) { public ChunkResult { missing=List.copyOf(missing); } }
    public record CountResult(CountInput input,boolean ready,Integer signedCount,List<ChunkResult> chunks,List<String> missing) { public CountResult { chunks=List.copyOf(chunks);missing=List.copyOf(missing); } }
    public record MapperItem(MapperInput input,Long requested,Boolean selectedValid,boolean returnBranchReady,boolean returnSelectionReady,ReturnChoice choice,String returnedIdentity,
            boolean countDemanded,Integer countIndex,CountResult count,boolean callerStateReady,Integer returnedState,Boolean state4,boolean ready,List<String> missing) { public MapperItem { missing=List.copyOf(missing); } }
    public record OccurrenceResult(int index,MapperOccurrence input,String resolvedIdentity,MapperItem mapper,boolean ready,List<String> missing) { public OccurrenceResult { missing=List.copyOf(missing); } }
    public record MapperResult(MapperInputs input,Status status,boolean initialSeedReady,boolean rosterReady,List<OccurrenceResult> occurrences,List<MapperItem> mappers,List<CountResult> counts,List<String> missing) {
        public MapperResult { occurrences=List.copyOf(occurrences);mappers=List.copyOf(mappers);counts=List.copyOf(counts);missing=List.copyOf(missing); }
    }
    public static CountResult count(CountInput row) {
        List<String> missing=new ArrayList<>();if(row.base128()==null)missing.add("count_base_128_raw_i32");Integer total=row.base128();List<ChunkResult> chunks=new ArrayList<>();
        for(int index=0;index<7;index++) { final int ordinal=index;CountChunk c=row.chunks().stream().filter(v->v.physicalIndex()==ordinal).findFirst().orElse(null);List<String> errors=new ArrayList<>();Integer delta=null;CountBranch branch=null;
            if(c==null)errors.add("physical_chunk");else if(c.maximum()==null)errors.add("maximum_00_raw_i32");else if(c.maximum()==0) { delta=0;branch=CountBranch.MAXIMUM_ZERO_SKIP; }
            else if(c.current()==null)errors.add("current_04_raw_i32");else if(c.current()!=0) { delta=c.current()-c.maximum();branch=CountBranch.NONZERO_CURRENT_DIFFERENCE; }
            else if(c.state18()==null)errors.add("state_18_raw_i32_for_zero_current");else if(c.state18()==3) { delta=0;branch=CountBranch.STATE3_ZERO_CURRENT_SKIP; }else { delta=-c.maximum();branch=CountBranch.ZERO_CURRENT_DIFFERENCE; }
            if(total!=null&&delta!=null)total=total+delta;else if(delta==null)total=null;chunks.add(new ChunkResult(index,delta!=null,delta,branch,errors));prefix(missing,"chunks["+index+"].",errors);
        }return new CountResult(row,total!=null,total,chunks,missing);
    }
    private static final class MapperWork {
        final MapperInput row;Long requested;Boolean valid;boolean branchReady,selectionReady,countDemanded,callerReady,ready;ReturnChoice choice;String returned;Integer countIndex,state;CountResult count;Boolean state4;final List<String> missing=new ArrayList<>();
        MapperWork(MapperInput row) { this.row=row; }
        MapperItem result() { return new MapperItem(row,requested,valid,branchReady,selectionReady,choice,returned,countDemanded,countIndex,count,callerReady,state,state4,ready,missing); }
        MapperItem missing(String field) { missing.add(field);return result(); }
    }
    private static MapperItem mapper(MapperInput row,List<CountInput> counts,LinkedHashMap<Integer,CountResult> cache) {
        MapperWork w=new MapperWork(row);Integer kind=row.kind14c();if(kind==null)return w.missing("kind_14c_raw_i32");String selected=null;ReturnChoice choice=ReturnChoice.NATIVE_FALLBACK;
        if(kind==1||kind==4) {
            if(row.dataCount()==null)return w.missing("data_count_raw_i32");w.requested=row.dataCount()==0?INVALID:row.firstRegiId();if(w.requested==null)return w.missing("first_data_record_regi_id_8_for_nonzero_count");
            Resolution resolution=row.selectedResolution();if(resolution==null)return w.missing("selected_regi_resolution");if(!Objects.equals(resolution.requestedFullId(),w.requested))return w.missing("selected_regi_resolution_actual_requested_full_id");
            Long selectedId=resolution.selectedFullId(),magic=row.selectedMagic();selected=resolution.objectIdentity();
            if((magic!=null&&magic!=REGI)||Objects.equals(selectedId,INVALID))w.valid=false;else if(Objects.equals(magic,REGI)&&selectedId!=null)w.valid=true;else return w.missing("selected_regi_magic_14_and_full_id_10");
            if(w.valid) {
                if(!textok(selected))return w.missing("selected_regi_physical_identity");choice=ReturnChoice.SELECTED_REGI;
                if(kind==1) { w.countDemanded=true;w.countIndex=row.countInputIndex();CountInput source=w.countIndex==null?null:counts.stream().filter(c->c.nativeIndex()==w.countIndex).findFirst().orElse(null);
                    if(source==null)return w.missing("selected_kind1_count_input");if(!Objects.equals(source.regiIdentity(),selected))return w.missing("count_input_selected_physical_Regi_identity");
                    w.count=cache.computeIfAbsent(w.countIndex,k->count(source));if(!w.count.ready()) { prefix(w.missing,"count.",w.count.missing());return w.result(); }if(w.count.signedCount()>0)choice=ReturnChoice.NATIVE_FALLBACK;
                }
            }
        }
        w.branchReady=true;w.choice=choice;String returned=choice==ReturnChoice.SELECTED_REGI?selected:row.fallbackRegiIdentity();if(!textok(returned))return w.missing(choice==ReturnChoice.NATIVE_FALLBACK?"fallback_regi_identity":"selected_regi_physical_identity");
        w.selectionReady=true;w.returned=returned;if(!Objects.equals(row.returnedRegiIdentity(),returned))return w.missing("returned_state_capture_matches_source_selected_pointer");if(row.returnedState138()==null)return w.missing("returned_state_138_raw_i32");
        w.callerReady=true;w.state=row.returnedState138();w.state4=w.state==4;w.ready=true;return w.result();
    }
    public static MapperResult projectMapper(MapperInputs input) {
        List<String> missing=new ArrayList<>();List<OccurrenceResult> occurrences=new ArrayList<>();LinkedHashMap<Integer,MapperItem> mappers=new LinkedHashMap<>();LinkedHashMap<Integer,CountResult> counts=new LinkedHashMap<>();
        if(input==null) { missing.add("current_candidate_detachment_mapper_inputs_v1");return mapperResult(null,Status.UNAVAILABLE,false,false,occurrences,mappers,counts,missing); }
        if(!input.selectionReady()) { missing.add("initial_current_candidate_selection");return mapperResult(input,Status.UNAVAILABLE,false,false,occurrences,mappers,counts,missing); }
        if(input.selectionBranch()==SeedSelection.NOT_CALLED)return mapperResult(input,Status.AVAILABLE,true,true,occurrences,mappers,counts,missing);
        if(input.selectionBranch()!=SeedSelection.FIRST_VALID_CURRENT_RECEIVER) { missing.add("initial_current_candidate_selection_branch");return mapperResult(input,Status.UNAVAILABLE,false,false,occurrences,mappers,counts,missing); }
        if(input.rosterCount()==null) { missing.add("roster_count_raw_i32");return mapperResult(input,Status.UNAVAILABLE,false,false,occurrences,mappers,counts,missing); }
        if(input.rosterCount()<=0)return mapperResult(input,Status.AVAILABLE,true,true,occurrences,mappers,counts,missing);
        boolean roster=Boolean.TRUE.equals(input.rosterDataPresent())&&input.occurrences().size()==input.rosterCount();if(!Boolean.TRUE.equals(input.rosterDataPresent()))missing.add("current_candidate_roster_data_pointer");
        for(int index=0;index<input.rosterCount();index++) { MapperOccurrence row=index<input.occurrences().size()?input.occurrences().get(index):null;List<String> errors=new ArrayList<>();String identity=row==null?null:row.resolution().objectIdentity();MapperItem projection=null;
            if(row==null)errors.add("observed_raw_ArRg_occurrence");else if(row.rawFullId()==null) { errors.add("raw_full_id_u32");roster=false; }
            else if(!row.resolution().state().ready()||!textok(identity))errors.add("current_ArRg_registry_or_fallback_resolution");else {
                MapperInput source=row.mapperIndex()==null?null:input.mappers().stream().filter(m->m.nativeIndex()==row.mapperIndex()).findFirst().orElse(null);
                if(source==null)errors.add("physical_ArRg_mapper_snapshot");else if(!Objects.equals(source.arrgIdentity(),identity))errors.add("mapper_resolved_physical_ArRg_identity");else { projection=mappers.computeIfAbsent(row.mapperIndex(),k->mapper(source,input.counts(),counts));errors.addAll(projection.missing()); }
            }
            occurrences.add(new OccurrenceResult(index,row,identity,projection,projection!=null&&projection.ready(),errors));prefix(missing,"occurrences["+index+"].",errors);
        }
        boolean ready=roster&&occurrences.stream().allMatch(OccurrenceResult::ready);return mapperResult(input,ready?Status.AVAILABLE:Status.PARTIAL,ready,roster,occurrences,mappers,counts,missing);
    }
    private static MapperResult mapperResult(MapperInputs input,Status status,boolean ready,boolean roster,List<OccurrenceResult> occurrences,LinkedHashMap<Integer,MapperItem> mappers,LinkedHashMap<Integer,CountResult> counts,List<String> missing) { return new MapperResult(input,status,ready,roster,occurrences,new ArrayList<>(mappers.values()),new ArrayList<>(counts.values()),missing); }
    public static JsonNode mapperJson(MapperResult r) {
        MapperInputs v=r.input();ObjectNode n=object();n.put("projection_kind","current_candidate_detachment_mapper_preview");n.put("source_contract_game_version","1.20.0.3");n.put("native_mapper_rva","0x2A977A0");n.put("native_count_rva","0x262BBC0");n.put("input_basis","initial_current_first_candidate_seed_only");n.put("status",wire(r.status()));n.put("initial_current_seed_ready",r.initialSeedReady());n.put("selection_ready",v!=null&&v.selectionReady());n.put("selection_branch",v==null?null:wire(v.selectionBranch()));n.put("roster_ready",r.rosterReady());n.put("roster_count_raw_i32",v==null?null:v.rosterCount());n.put("roster_data_present",v==null?null:v.rosterDataPresent());n.put("roster_data_identity",v==null?null:v.rosterDataIdentity());n.put("candidate_reference_native_index",v==null?null:v.candidateReferenceIndex());n.put("candidate_pending_native_index",v==null?null:v.candidatePendingIndex());n.put("candidate_raw_full_id_u32",v==null?null:v.candidateRawId());n.put("candidate_actual_full_id_u32",v==null?null:v.candidateActualId());n.put("candidate_army_identity",v==null?null:v.candidateArmyIdentity());
        n.set("occurrences",array(r.occurrences(),a->{ObjectNode o=object();o.put("native_index",a.index());o.put("raw_full_id_u32",a.input()==null?null:a.input().rawFullId());o.put("resolved_arrg_identity",a.resolvedIdentity());o.put("mapper_index",a.input()==null?null:a.input().mapperIndex());o.put("preview_ready",a.ready());o.set("mapper_projection",a.mapper()==null?JsonNodeFactory.instance.nullNode():mapperItemJson(a.mapper()));o.set("missing_inputs",strings(a.missing()));return o;}));
        n.set("mapper_results",array(r.mappers(),ArmyStrengthsDetachment::mapperItemJson));n.set("count_results",array(r.counts(),ArmyStrengthsDetachment::countJson));n.set("missing_inputs",strings(r.missing()));falseFields(n,"actual_effects","actual_detachment","future_drain_ready","full_army_lifecycle_ready","full_monthly_ready","full_calendar_ready","live");n.putNull("actual_post_stage");n.put("native_writes_executed",0);return n;
    }
    private static JsonNode countJson(CountResult r) { ObjectNode n=object();n.put("native_index",r.input().nativeIndex());n.put("regi_identity",r.input().regiIdentity());n.put("observed_count_base_128_raw_i32",r.input().base128());n.put("count_ready",r.ready());n.put("signed_count_i32",r.signedCount());n.set("chunk_projections",array(r.chunks(),c->{ObjectNode o=object();o.put("physical_index",c.physicalIndex());o.put("delta_ready",c.ready());o.put("delta_i32",c.delta());o.put("branch",wire(c.branch()));o.set("missing_inputs",strings(c.missing()));return o;}));n.set("missing_inputs",strings(r.missing()));n.put("input_basis","current_physical_Regi128_and_seven_chunks");return n; }
    private static JsonNode mapperItemJson(MapperItem r) { MapperInput v=r.input();ObjectNode n=object();n.put("native_index",v.nativeIndex());n.put("arrg_identity",v.arrgIdentity());n.put("kind_14c_raw_i32",v.kind14c());n.put("data_count_raw_i32",v.dataCount());n.put("source_requested_regi_full_id_u32",r.requested());n.put("selected_regi_identity_valid",r.selectedValid());n.put("return_branch_ready",r.returnBranchReady());n.put("return_selection_ready",r.returnSelectionReady());n.put("return_selection",wire(r.choice()));n.put("returned_regi_identity",r.returnedIdentity());n.put("count_demanded",r.countDemanded());n.put("count_input_index",r.countIndex());n.set("count_projection",r.count()==null?JsonNodeFactory.instance.nullNode():countJson(r.count()));n.put("caller_state_ready",r.callerStateReady());n.put("returned_state_138_raw_i32",r.returnedState());n.put("state4_branch_admitted",r.state4());n.put("preview_ready",r.ready());n.set("missing_inputs",strings(r.missing()));n.put("observed_return_selection",wire(v.returnSelection()));n.put("observed_returned_regi_identity",v.returnedRegiIdentity());n.put("observed_returned_regi_full_id_u32",v.returnedRegiId());n.put("observed_returned_regi_magic_14_raw_u32",v.returnedMagic());n.put("input_basis","source2A977A0_from_same_capture_raw_operands");return n; }

    public enum CallbackBranch { NULL_DATA_SKIPS_CLEANUP_AND_RESOURCE,NONNULL_DATA_CLEANUP_THEN_CONDITIONAL_RESOURCE_RETURN }
    public enum CleanupBranch { CAPTURED_NONPOSITIVE_COUNT_SKIP_THEN_ZERO,CAPTURED_POSITIVE_COUNT_ORDERED_MODE0_RECORDS }
    public record RecordCleanupItem(int index,CallbackRecord observed,boolean ready,List<String> missing) { public RecordCleanupItem { missing=List.copyOf(missing); } }
    public record Cleanup(boolean ready,CleanupBranch branch,Integer count,int completed,List<RecordCleanupItem> records,Integer afterCount,List<String> missing) { public Cleanup { records=List.copyOf(records);missing=List.copyOf(missing); } }
    public record ResourceCall(String allocator,String vtable,String target,String buffer) { }
    public record AfterHeader(String primaryVtable,String secondaryVtable,boolean dataPresent,String dataBuffer,Integer count,Integer capacity,List<String> knownFields,List<String> preservedMissing) { public AfterHeader { knownFields=List.copyOf(knownFields);preservedMissing=List.copyOf(preservedMissing); } }
    public record CallbackItem(int index,CallbackIncoming input,Integer mode,boolean inputReady,boolean selectedTargetReady,boolean coreEntryReady,
            Boolean cleanupRequired,boolean cleanupReady,Cleanup cleanup,Boolean resourceRequired,boolean resourceReady,ResourceCall resource,
            boolean mode0Ready,boolean afterReady,AfterHeader after,List<String> completed,CallbackBranch branch,boolean ready,List<String> missing) {
        public CallbackItem { completed=List.copyOf(completed);missing=List.copyOf(missing); }
    }
    public record CallbackResult(CallbackInputs input,Status status,boolean ready,List<CallbackItem> incoming,List<Integer> independentlyReady,List<Integer> mode0Ready,List<Integer> cleanupReady,List<String> missing,String reason) {
        public CallbackResult { incoming=List.copyOf(incoming);independentlyReady=List.copyOf(independentlyReady);mode0Ready=List.copyOf(mode0Ready);cleanupReady=List.copyOf(cleanupReady);missing=List.copyOf(missing); }
    }
    private static final class CallbackWork {
        final int index;final CallbackIncoming row;final Integer mode;boolean inputReady,targetReady,coreReady,cleanupReady,resourceReady,mode0Ready,afterReady,ready;Boolean cleanupRequired,resourceRequired;Cleanup cleanup;ResourceCall resource;AfterHeader after;CallbackBranch branch;final List<String> completed=new ArrayList<>(),missing=new ArrayList<>();
        CallbackWork(int index,CallbackIncoming row,Integer mode) { this.index=index;this.row=row;this.mode=mode; }
        CallbackItem result() { return new CallbackItem(index,row,mode,inputReady,targetReady,coreReady,cleanupRequired,cleanupReady,cleanup,resourceRequired,resourceReady,resource,mode0Ready,afterReady,after,completed,branch,ready,missing); }
        CallbackItem missing(String name) { missing.add(name);return result(); }
    }
    private static Cleanup cleanup(CallbackIncoming row,String known) {
        Integer count=row.dataCount();List<RecordCleanupItem> records=new ArrayList<>();List<String> missing=new ArrayList<>();if(count==null)return new Cleanup(false,null,null,0,records,null,List.of("data_count_2c_raw_i32"));
        if(count<=0)return new Cleanup(true,CleanupBranch.CAPTURED_NONPOSITIVE_COUNT_SKIP_THEN_ZERO,count,0,records,0,missing);
        for(int index=0;index<count;index++) { CallbackRecord record=index<row.records().size()?row.records().get(index):null;List<String> errors=new ArrayList<>();String target=record==null?null:record.slot0TargetIdentity();
            if(record==null||!nativeok(record.recordIdentity()))errors.add("record_identity");if(!nativeok(known))errors.add("known_mode0_record_callback_identity");if(!nativeok(target))errors.add("actual_record_slot0_target_identity");else if(nativeok(known)&&!target.equals(known))errors.add("selected_record_callback_effects_not_source_closed");
            records.add(new RecordCleanupItem(index,record,errors.isEmpty(),errors));if(!errors.isEmpty()) { prefix(missing,"records["+index+"].",errors);return new Cleanup(false,CleanupBranch.CAPTURED_POSITIVE_COUNT_ORDERED_MODE0_RECORDS,count,index,records,null,missing); }
        }return new Cleanup(true,CleanupBranch.CAPTURED_POSITIVE_COUNT_ORDERED_MODE0_RECORDS,count,count,records,0,missing);
    }
    private static CallbackItem callback(CallbackIncoming row,CallbackInputs inputs,int index) {
        CallbackWork w=new CallbackWork(index,row,inputs.mode());KnownCallbacks known=inputs.known();
        if(!nativeok(row.arrgIdentity()))w.missing.add("arrg_identity");if(!nativeok(known.primarySlot0()))w.missing.add("known_primary_slot0_target_identity");if(!nativeok(known.core()))w.missing.add("known_core_identity");
        if(!nativeok(row.primarySlot0()))w.missing.add("arrg_primary_slot0_target_identity");else if(nativeok(known.primarySlot0())&&!row.primarySlot0().equals(known.primarySlot0()))w.missing.add("selected_primary_callback_core_not_source_closed");if(!w.missing.isEmpty())return w.result();
        w.targetReady=true;w.coreReady=true;w.completed.add("known_selected_wrapper_enters_core");if(row.dataPresent()==null)return w.missing("data_pointer_present");w.inputReady=true;
        List<String> fields=new ArrayList<>(List.of("tag_14_raw_u32")),preserved=new ArrayList<>();if(nativeok(known.primaryVtable()))fields.add("primary_vtable_identity");else w.missing.add("known_primary_vtable_identity");if(nativeok(known.secondaryVtable()))fields.add("secondary_vtable_identity");else w.missing.add("known_secondary_vtable_identity");
        Integer afterCount=row.dataCount(),afterCapacity=row.dataCapacity();
        if(!row.dataPresent()) {
            w.branch=CallbackBranch.NULL_DATA_SKIPS_CLEANUP_AND_RESOURCE;w.cleanupRequired=false;w.cleanupReady=true;w.resourceRequired=false;w.resourceReady=true;fields.addAll(List.of("data_pointer_present","data_buffer_identity"));
            if(afterCount!=null)fields.add("data_count_2c_raw_i32");else preserved.add("data_count_2c_raw_i32");if(afterCapacity!=null)fields.add("data_capacity_28_raw_i32");else preserved.add("data_capacity_28_raw_i32");w.completed.add("null_DATA20_skips_EBA050_and_allocator");
        }else {
            w.branch=CallbackBranch.NONNULL_DATA_CLEANUP_THEN_CONDITIONAL_RESOURCE_RETURN;w.cleanupRequired=true;w.resourceRequired=true;if(!nativeok(row.dataBuffer()))return w.missing("data_buffer_identity");
            w.cleanup=cleanup(row,known.mode0Record());w.cleanupReady=w.cleanup.ready();for(int position=0;position<w.cleanup.completed();position++)w.completed.add("record["+position+"]_mode0_noop");if(!w.cleanupReady) { w.missing.addAll(w.cleanup.missing());return w.result(); }
            w.completed.add("EBA050_stores_count2C_zero");w.resource=new ResourceCall(row.allocator(),row.allocatorVtable(),row.allocatorSlot10(),row.dataBuffer());w.resourceReady=nativeok(row.allocator())&&nativeok(row.allocatorVtable())&&nativeok(row.allocatorSlot10());
            if(!nativeok(row.allocator()))w.missing.add("data_allocator_identity");if(!nativeok(row.allocatorVtable()))w.missing.add("data_allocator_vtable_identity");if(!nativeok(row.allocatorSlot10()))w.missing.add("data_allocator_slot10_target_identity");afterCount=0;afterCapacity=0;fields.addAll(List.of("data_pointer_present","data_buffer_identity","data_count_2c_raw_i32","data_capacity_28_raw_i32"));w.completed.add("assumed_normal_allocator_return_then_clear20_and28");
        }
        w.completed.add("write_Dltd_tag_and_secondary_base_vtable");w.after=new AfterHeader(known.primaryVtable(),known.secondaryVtable(),false,null,afterCount,afterCapacity,fields,preserved);w.afterReady=nativeok(known.primaryVtable())&&nativeok(known.secondaryVtable());w.ready=w.afterReady&&(!row.dataPresent()||w.resourceReady);w.mode0Ready=w.ready&&Integer.valueOf(0).equals(inputs.mode());return w.result();
    }
    public static CallbackResult projectCallback(CallbackInputs input) {
        List<CallbackItem> rows=new ArrayList<>();List<Integer> ready=new ArrayList<>(),mode0=new ArrayList<>(),cleanup=new ArrayList<>();List<String> missing=new ArrayList<>();if(input==null)return new CallbackResult(null,Status.UNAVAILABLE,false,rows,ready,mode0,cleanup,missing,"native_current_detachment_callback_family_absent");
        for(int index=0;index<input.incoming().size();index++) { CallbackItem item=callback(input.incoming().get(index),input,index);rows.add(item);if(item.ready())ready.add(index);if(item.mode0Ready())mode0.add(index);if(item.cleanupReady())cleanup.add(index);prefix(missing,"incoming["+index+"].",item.missing()); }
        if(!input.seedSelectionReady())missing.add("seed_selection_ready");if(!input.seedRosterReady())missing.add("seed_roster_ready");boolean complete=input.seedSelectionReady()&&input.seedRosterReady()&&rows.stream().allMatch(CallbackItem::ready);Status status=complete?Status.AVAILABLE:input.state().status()==Status.UNAVAILABLE&&rows.isEmpty()?Status.UNAVAILABLE:Status.PARTIAL;
        return new CallbackResult(input,status,complete,rows,ready,mode0,cleanup,missing,complete?null:"current_detachment_callback_inputs_partial");
    }
    public static JsonNode callbackJson(CallbackResult r) {
        CallbackInputs v=r.input();ObjectNode n=object();n.put("projection_kind","conditional_current_detachment_callback_v1");n.put("status",wire(r.status()));n.put("ready",r.ready());n.put("seed_selection_ready",v!=null&&v.seedSelectionReady());n.put("seed_roster_ready",v!=null&&v.seedRosterReady());n.put("current_date_storage_raw64",v==null?null:v.date());n.put("source_parent_wrapper_mode_i32",v==null?null:v.mode());n.put("input_basis","independent_observed_current_detachment_callback_seeds_12004");n.put("source_core_rva","0x2632DD0");n.put("source_record_cleanup_rva","0xEBA050");n.put("normal_resource_return_assumed",true);n.put("resource_internal_effects_modeled",false);n.putNull("outer_wrapper_mode");n.set("incoming",array(r.incoming(),ArmyStrengthsDetachment::callbackItemJson));n.set("independently_ready_incoming_indices",ints(r.independentlyReady()));n.set("conditional_mode0_wrapper_ready_incoming_indices",ints(r.mode0Ready()));n.set("record_cleanup_ready_incoming_indices",ints(r.cleanupReady()));n.set("missing_inputs",strings(r.missing()));n.put("unavailable_reason",r.reason());callbackLimits(n);return n;
    }
    private static JsonNode callbackItemJson(CallbackItem r) {
        CallbackIncoming v=r.input();ObjectNode n=object();n.put("incoming_index",r.index());n.set("seed_incoming_native_indices",ints(v.seedIndices()));n.put("arrg_identity",v.arrgIdentity());n.put("arrg_full_id_u32",v.arrgFullId());ObjectNode observed=object();observed.put("arrg_primary_vtable_identity",v.primaryVtable());observed.put("arrg_primary_slot0_target_identity",v.primarySlot0());observed.put("data_pointer_present",v.dataPresent());observed.put("data_buffer_identity",v.dataBuffer());observed.put("data_count_2c_raw_i32",v.dataCount());observed.put("data_capacity_28_raw_i32",v.dataCapacity());observed.put("data_allocator_identity",v.allocator());observed.put("data_allocator_vtable_identity",v.allocatorVtable());observed.put("data_allocator_slot10_target_identity",v.allocatorSlot10());n.set("observed_current_header",observed);n.set("observed_ordered_records",array(v.records(),ArmyDetachmentInputsCodec::encodeCallbackRecord));
        n.put("independent_current_seed",true);n.put("input_ready",r.inputReady());n.put("selected_callback_target_ready",r.selectedTargetReady());n.put("conditional_core_entry_ready",r.coreEntryReady());n.put("record_cleanup_required",r.cleanupRequired());n.put("record_cleanup_ready",r.cleanupReady());n.set("record_cleanup",r.cleanup()==null?JsonNodeFactory.instance.nullNode():cleanupJson(r.cleanup()));n.put("resource_call_required",r.resourceRequired());n.put("resource_call_descriptor_ready",r.resourceReady());n.set("conditional_resource_call",r.resource()==null?JsonNodeFactory.instance.nullNode():resourceJson(r.resource()));n.put("normal_resource_return_assumed",true);n.put("source_parent_wrapper_mode_i32",r.mode());n.put("conditional_selected_parent_mode0_wrapper_ready",r.mode0Ready());n.put("conditional_outer_sized_free_selected",Integer.valueOf(0).equals(r.mode())?Boolean.FALSE:null);n.put("conditional_direct_after_header_ready",r.afterReady());n.set("conditional_direct_after_header",r.after()==null?JsonNodeFactory.instance.nullNode():afterJson(r.after()));n.set("completed_source_prefix",strings(r.completed()));n.put("branch",wire(r.branch()));n.put("ready",r.ready());n.set("missing_inputs",strings(r.missing()));callbackLimits(n);return n;
    }
    private static JsonNode cleanupJson(Cleanup r) { ObjectNode n=object();n.put("ready",r.ready());n.put("branch",wire(r.branch()));n.put("captured_count_i32",r.count());n.put("completed_record_prefix_count",r.completed());n.set("record_results",array(r.records(),a->{CallbackRecord v=a.observed();ObjectNode o=object();o.put("native_index",a.index());o.put("record_identity",v==null?null:v.recordIdentity());o.put("observed_vtable_identity",v==null?null:v.vtableIdentity());o.put("selected_slot0_target_identity",v==null?null:v.slot0TargetIdentity());o.put("call_mode_edx",0);o.put("ready",a.ready());o.put("normal_return_noop",a.ready());o.put("game_reads",a.ready()?Integer.valueOf(0):null);o.put("game_writes",a.ready()?Integer.valueOf(0):null);o.put("selected_resource_calls",a.ready()?Integer.valueOf(0):null);o.set("missing_inputs",strings(a.missing()));return o;}));n.put("conditional_count_after_i32",r.afterCount());n.set("missing_inputs",strings(r.missing()));n.put("record_call_mode_edx",0);n.put("native_calls_executed",0);n.put("native_writes_executed",0);return n; }
    private static JsonNode resourceJson(ResourceCall r) { ObjectNode n=object();n.put("allocator_identity",r.allocator());n.put("allocator_vtable_identity",r.vtable());n.put("selected_slot10_target_identity",r.target());n.put("buffer_identity",r.buffer());n.put("r8d_size",8);n.put("normal_return_assumed",true);n.put("executed",false);n.put("internal_effects_modeled",false);return n; }
    private static JsonNode afterJson(AfterHeader r) { ObjectNode n=object();n.put("primary_vtable_identity",r.primaryVtable());n.put("secondary_vtable_identity",r.secondaryVtable());n.put("tag_14_raw_u32",0x446C7464L);n.put("data_pointer_present",r.dataPresent());n.put("data_buffer_identity",r.dataBuffer());n.put("data_count_2c_raw_i32",r.count());n.put("data_capacity_28_raw_i32",r.capacity());n.set("known_field_names",strings(r.knownFields()));n.set("preserved_context_missing",strings(r.preservedMissing()));return n; }
    private static void callbackLimits(ObjectNode n) { commonLimits(n);falseFields(n,"actual_outer_wrapper_mode_observed","outer_wrapper_complete","outer_store_or_registry_invalidation_ready","actual_next_occurrence_ready"); }

    public enum StoreBranch { NONZERO_STORE48_FALSE_RETURN,UNSIGNED_INDEX_OUT_OF_RANGE_FALSE_RETURN,NULL_SELECTED_SLOT_POINTER_FALSE_RETURN,SELECTED_FULL_ID_MISMATCH_FALSE_RETURN,MATCHING_SELECTED_FULL_ID_ADMITTED }
    public enum StoreField { ACTIVE_COUNT_3C_RAW_U32,REGISTRY_MARK_4A_RAW_U8 }
    public record StoreUpdate(StoreField field,Long before,long after) { }
    public record SelectedCallback(String objectIdentity,String vtable,String target,Integer mode) { }
    public record StoreItem(int index,StoreRequest input,Long sourceIndex,boolean admissionReady,Boolean admitted,StoreBranch branch,Boolean skipReturn,Boolean updatesRequired,
            boolean updatesReady,List<StoreUpdate> updates,Boolean callbackSelected,boolean descriptorReady,SelectedCallback descriptor,List<String> completed,
            List<String> missingAdmission,List<String> missingUpdates,List<String> missingDescriptor) {
        public StoreItem { updates=List.copyOf(updates);completed=List.copyOf(completed);missingAdmission=List.copyOf(missingAdmission);missingUpdates=List.copyOf(missingUpdates);missingDescriptor=List.copyOf(missingDescriptor); }
    }
    public record StoreResult(StoreInputs input,Status status,boolean ready,List<StoreItem> requests,int prefix,List<Integer> independentlyReady,List<Integer> admitted,List<Integer> skipped,List<Integer> updatesReady,List<String> missing,List<String> remaining,String reason) {
        public StoreResult { requests=List.copyOf(requests);independentlyReady=List.copyOf(independentlyReady);admitted=List.copyOf(admitted);skipped=List.copyOf(skipped);updatesReady=List.copyOf(updatesReady);missing=List.copyOf(missing);remaining=List.copyOf(remaining); }
    }
    private static final class StoreWork {
        final int index;final StoreRequest row;Long sourceIndex;boolean ready,updatesReady,descriptorReady;Boolean admitted,skipReturn,updatesRequired,callbackSelected;StoreBranch branch;SelectedCallback descriptor;final List<StoreUpdate> updates=new ArrayList<>();final List<String> completed=new ArrayList<>(),missing=new ArrayList<>(),missingUpdates=new ArrayList<>(),missingDescriptor=new ArrayList<>();
        StoreWork(int index,StoreRequest row) { this.index=index;this.row=row; }
        StoreItem result() { return new StoreItem(index,row,sourceIndex,ready,admitted,branch,skipReturn,updatesRequired,updatesReady,updates,callbackSelected,descriptorReady,descriptor,completed,missing,missingUpdates,missingDescriptor); }
        StoreItem missing(String field) { missing.add(field);return result(); }
        StoreItem skip(StoreBranch branch) { ready=true;admitted=false;this.branch=branch;skipReturn=false;updatesRequired=false;updatesReady=true;callbackSelected=false;return result(); }
    }
    private static StoreItem store(StoreRequest row,StoreInputs input,int index) {
        StoreWork w=new StoreWork(index,row);if(input.flag48()==null)return w.missing("store_48_raw_u8");w.completed.add("read_store48");if(input.flag48()!=0)return w.skip(StoreBranch.NONZERO_STORE48_FALSE_RETURN);
        if(row.requestedId()==null)return w.missing("requested_full_id_u32");w.sourceIndex=row.requestedId()&0xFFFFFFL;if(input.slotCount()==null)return w.missing("slot_count_2c_raw_u32");w.completed.add("unsigned_low24_below_slot_count_comparison");if(w.sourceIndex>=input.slotCount())return w.skip(StoreBranch.UNSIGNED_INDEX_OUT_OF_RANGE_FALSE_RETURN);
        if(row.pointerPresent()==null)return w.missing("selected_slot_object_pointer_present");w.completed.add("read_actual_selected_slot_pointer");if(!row.pointerPresent())return w.skip(StoreBranch.NULL_SELECTED_SLOT_POINTER_FALSE_RETURN);
        if(row.selectedId()==null)return w.missing("selected_full_id_10_raw_u32");w.completed.add("compare_selected_object10_with_complete_requested_id");if(!row.selectedId().equals(row.requestedId()))return w.skip(StoreBranch.SELECTED_FULL_ID_MISMATCH_FALSE_RETURN);
        w.ready=true;w.admitted=true;w.branch=StoreBranch.MATCHING_SELECTED_FULL_ID_ADMITTED;w.updatesRequired=true;w.callbackSelected=true;w.updates.add(new StoreUpdate(StoreField.REGISTRY_MARK_4A_RAW_U8,input.registryMark()==null?null:input.registryMark().longValue(),1));
        if(input.activeCount()!=null) { w.updates.addFirst(new StoreUpdate(StoreField.ACTIVE_COUNT_3C_RAW_U32,input.activeCount(),(input.activeCount()-1)&INVALID));w.updatesReady=true; }else w.missingUpdates.add("active_count_3c_raw_u32");
        w.descriptor=new SelectedCallback(row.selectedIdentity(),row.selectedVtable(),row.selectedSlot0(),input.mode());if(!nativeok(row.selectedIdentity()))w.missingDescriptor.add("selected_object_identity");if(!nativeok(row.selectedVtable()))w.missingDescriptor.add("selected_primary_vtable_identity");if(!nativeok(row.selectedSlot0()))w.missingDescriptor.add("selected_slot0_target_identity");if(!Integer.valueOf(0).equals(input.mode()))w.missingDescriptor.add("source_parent_wrapper_mode_i32");w.descriptorReady=w.missingDescriptor.isEmpty();return w.result();
    }
    public static StoreResult projectStore(StoreInputs input) {
        List<StoreItem> rows=new ArrayList<>();List<Integer> independently=new ArrayList<>(),admitted=new ArrayList<>(),skipped=new ArrayList<>(),updates=new ArrayList<>();List<String> missing=new ArrayList<>();int completed=0;boolean prefixOpen=true;
        if(input==null)return new StoreResult(null,Status.UNAVAILABLE,false,rows,0,independently,admitted,skipped,updates,missing,List.of(),"native_current_detachment_store_family_absent");
        for(int index=0;index<input.requests().size();index++) { StoreItem row=store(input.requests().get(index),input,index);rows.add(row);if(row.admissionReady()) { independently.add(index);if(prefixOpen)completed++;(Boolean.TRUE.equals(row.admitted())?admitted:skipped).add(index); }else prefixOpen=false;
            if(Boolean.TRUE.equals(row.admitted())&&row.updatesReady())updates.add(index);prefix(missing,"requests["+index+"].",row.missingAdmission());
        }
        if(!input.seedSelectionReady())missing.add("seed_selection_ready");if(!input.seedRosterReady())missing.add("seed_roster_ready");boolean unavailable=rows.isEmpty()&&input.state().status()==Status.UNAVAILABLE;if(unavailable)missing.add("current_request_capture_unavailable");boolean ready=input.seedSelectionReady()&&input.seedRosterReady()&&rows.stream().allMatch(StoreItem::admissionReady)&&!unavailable;
        List<String> remaining=admitted.isEmpty()?List.of():List.of("actual_selected_callback_effects_and_postcallback_object10","reached4226F10_effects","actual_postcall_table20_and_registry_fields");return new StoreResult(input,ready?Status.AVAILABLE:unavailable?Status.UNAVAILABLE:Status.PARTIAL,ready,rows,completed,independently,admitted,skipped,updates,missing,remaining,ready?null:"current_detachment_store_admission_inputs_partial");
    }
    public static JsonNode storeJson(StoreResult r) {
        StoreInputs v=r.input();ObjectNode n=object();n.put("projection_kind","current_detachment_store_admission_v1");n.put("source_parent_rva","0x2A9E620");n.put("source_parent_identity",v==null?null:v.parentIdentity());n.put("source_parent_wrapper_mode_i32",v==null?null:v.mode());n.put("current_date_storage_raw64",v==null?null:v.date());n.put("input_basis","independent_same_query_current_arrg_registry_requests");n.put("seed_selection_ready",v!=null&&v.seedSelectionReady());n.put("seed_roster_ready",v!=null&&v.seedRosterReady());n.put("status",wire(r.status()));n.put("ready",r.ready());n.put("admission_ready",r.ready());
        ObjectNode registry=v==null?null:object();if(registry!=null) { registry.put("registry_identity",v.registryIdentity());registry.put("store_48_raw_u8",v.flag48());registry.put("slot_count_2c_raw_u32",v.slotCount());registry.put("slot_table_identity",v.slotTable());registry.put("active_count_3c_raw_u32",v.activeCount());registry.put("registry_mark_4a_raw_u8",v.registryMark());registry.put("high_water_38_raw_u32",v.highWater());registry.put("free_head_40_raw_u32",v.freeHead()); }n.set("observed_current_registry",registry);
        n.set("requests",array(r.requests(),ArmyStrengthsDetachment::storeItemJson));n.put("completed_admission_prefix_count",r.prefix());n.set("independently_ready_request_indices",ints(r.independentlyReady()));n.set("admitted_request_indices",ints(r.admitted()));n.set("skipped_request_indices",ints(r.skipped()));n.set("pre_callback_updates_ready_request_indices",ints(r.updatesReady()));n.set("missing_admission_inputs",strings(r.missing()));n.putNull("post_callback_full_id_u32");n.putNull("actual_store_method_return");n.set("remaining_stage_inputs",strings(r.remaining()));n.put("unavailable_reason",r.reason());storeLimits(n);return n;
    }
    private static JsonNode storeItemJson(StoreItem r) {
        StoreRequest v=r.input();ObjectNode n=object();n.put("request_index",r.index());n.set("seed_incoming_native_indices",ints(v.seedIndices()));n.put("incoming_arrg_identity",v.incomingIdentity());n.put("requested_full_id_u32",v.requestedId());n.put("observed_index_low24_u32",v.observedIndex());n.put("source_index_low24_u32",r.sourceIndex());n.put("independent_current_request",true);n.put("observed_slot_identity",v.slotIdentity());n.put("observed_selected_pointer_present",v.pointerPresent());n.put("observed_selected_object_identity",v.selectedIdentity());n.put("observed_selected_full_id_10_raw_u32",v.selectedId());n.set("observed_trailing_slot_scan",array(v.trailingScan(),ArmyDetachmentInputsCodec::encodeSlotScan));
        n.put("admission_ready",r.admissionReady());n.put("admitted",r.admitted());n.put("branch",wire(r.branch()));n.put("conditional_skip_return",r.skipReturn());n.put("pre_callback_updates_required",r.updatesRequired());n.put("pre_callback_updates_ready",r.updatesReady());n.set("pre_callback_updates",array(r.updates(),a->{ObjectNode o=object();o.put("field",wire(a.field()));o.put("before",a.before());o.put("after",a.after());o.put("source_defined_write_ready",true);o.put("executed",false);return o;}));n.put("callback_selected",r.callbackSelected());n.put("selected_callback_descriptor_ready",r.descriptorReady());
        SelectedCallback d=r.descriptor();ObjectNode descriptor=d==null?null:object();if(descriptor!=null) { descriptor.put("selected_object_identity",d.objectIdentity());descriptor.put("selected_primary_vtable_identity",d.vtable());descriptor.put("selected_slot0_target_identity",d.target());descriptor.put("source_parent_wrapper_mode_i32",d.mode());descriptor.put("mode_is_source_constant",true);descriptor.put("execution_observed",false);descriptor.put("effects_replayed",false); }n.set("selected_callback_descriptor",descriptor);n.set("source_completed_prefix",strings(r.completed()));n.set("missing_admission_inputs",strings(r.missingAdmission()));n.set("missing_pre_callback_inputs",strings(r.missingUpdates()));n.set("missing_callback_descriptor_inputs",strings(r.missingDescriptor()));storeLimits(n);return n;
    }
    private static void storeLimits(ObjectNode n) { commonLimits(n);falseFields(n,"actual_store_method_return_observed","actual_registry_after_state_observed","callback_effects_replayed","zeroing_effects_replayed","registry_invalidation_ready","actual_next_occurrence_ready"); }

    public enum CharacterBranch { INVALID_CHARACTER_FULL_ID_NO_SUFFIX,NULL_CURRENT_CHARACTER1B8_NO_SUFFIX,NONNULL_CURRENT_CHARACTER1B8_CONDITIONAL_RESET_DESCRIPTORS }
    public sealed interface ResetDescriptor permits InitialReset,ReloadReset { }
    public record InitialReset(String target,Long before) implements ResetDescriptor { }
    public record ReloadReset(long sourceAfter) implements ResetDescriptor { }
    public record CharacterItem(int index,CharacterRequest input,boolean branchReady,CharacterBranch branch,Boolean noSuffix,Boolean resetRequired,boolean resetReady,boolean descriptorsReady,List<ResetDescriptor> descriptors,List<String> missing,List<String> optionalMissing,List<String> remaining) {
        public CharacterItem { descriptors=List.copyOf(descriptors);missing=List.copyOf(missing);optionalMissing=List.copyOf(optionalMissing);remaining=List.copyOf(remaining); }
    }
    public record CharacterResult(CharacterInputs input,Status status,boolean ready,List<CharacterItem> requests,int prefix,List<Integer> independentlyReady,List<Integer> noSuffix,List<Integer> descriptorsReady,List<Integer> sourceChainReady,List<String> missing,List<String> remaining,String reason) {
        public CharacterResult { requests=List.copyOf(requests);independentlyReady=List.copyOf(independentlyReady);noSuffix=List.copyOf(noSuffix);descriptorsReady=List.copyOf(descriptorsReady);sourceChainReady=List.copyOf(sourceChainReady);missing=List.copyOf(missing);remaining=List.copyOf(remaining); }
    }
    private static CharacterItem character(CharacterRequest row,int index) {
        if(Objects.equals(row.characterId(),INVALID))return noSuffix(row,index,CharacterBranch.INVALID_CHARACTER_FULL_ID_NO_SUFFIX);
        if(Boolean.FALSE.equals(row.extensionPresent()))return noSuffix(row,index,CharacterBranch.NULL_CURRENT_CHARACTER1B8_NO_SUFFIX);
        if(row.extensionPresent()==null)return new CharacterItem(index,row,false,null,null,null,false,false,List.of(),List.of("current_extension_1b8_present"),List.of(),List.of());
        CharacterBranch branch=CharacterBranch.NONNULL_CURRENT_CHARACTER1B8_CONDITIONAL_RESET_DESCRIPTORS;if(!nativeok(row.extensionIdentity()))return new CharacterItem(index,row,false,branch,false,true,false,false,List.of(),List.of("current_extension_1b8_identity"),List.of(),List.of());
        List<String> optional=new ArrayList<>();if(row.extensionF8()==null)optional.add("extension_f8_raw_u32");if(row.extension100()==null)optional.add("extension_100_raw64");
        List<ResetDescriptor> descriptors=List.of(new InitialReset(row.extensionIdentity(),row.extensionF8()),new ReloadReset(0xFFFFFFFF029C77F8L));
        return new CharacterItem(index,row,true,branch,false,true,true,true,descriptors,List.of(),optional,List.of("actual_reset_reached_and_fresh_character1b8_reload","actual_post_reset_origin_selected_inputs_and_callee_effects","reached28B2710_mutator_effects_and_actual_post_mutator_owner_context_date"));
    }
    private static CharacterItem noSuffix(CharacterRequest row,int index,CharacterBranch branch) { return new CharacterItem(index,row,true,branch,true,false,true,true,List.of(),List.of(),List.of(),List.of()); }
    public static CharacterResult projectCharacter(CharacterInputs input) {
        List<CharacterItem> rows=new ArrayList<>();List<Integer> independently=new ArrayList<>(),noSuffix=new ArrayList<>(),descriptors=new ArrayList<>(),sourceChain=new ArrayList<>();List<String> missing=new ArrayList<>(),remaining=new ArrayList<>();int completed=0;boolean prefixOpen=true;
        if(input==null)return new CharacterResult(null,Status.UNAVAILABLE,false,rows,0,independently,noSuffix,descriptors,sourceChain,missing,remaining,"native_current_character_detachment_family_absent");
        for(int index=0;index<input.requests().size();index++) { CharacterItem row=character(input.requests().get(index),index);rows.add(row);if(row.branchReady()) { independently.add(index);if(prefixOpen)completed++;(Boolean.TRUE.equals(row.noSuffix())?noSuffix:descriptors).add(index); }else prefixOpen=false;
            if(row.input().chainReady())sourceChain.add(index);prefix(missing,"requests["+index+"].",row.missing());for(String field:row.remaining())if(!remaining.contains(field))remaining.add(field);
        }
        if(!input.seedSelectionReady())missing.add("seed_selection_ready");if(!input.seedRosterReady())missing.add("seed_roster_ready");boolean unavailable=rows.isEmpty()&&input.state().status()==Status.UNAVAILABLE;if(unavailable)missing.add("current_request_capture_unavailable");boolean ready=input.seedSelectionReady()&&input.seedRosterReady()&&rows.stream().allMatch(CharacterItem::branchReady)&&!unavailable;
        return new CharacterResult(input,ready?Status.AVAILABLE:unavailable?Status.UNAVAILABLE:Status.PARTIAL,ready,rows,completed,independently,noSuffix,descriptors,sourceChain,missing,remaining,ready?null:"current_character_detachment_extension_inputs_partial");
    }
    public static JsonNode characterJson(CharacterResult r) {
        CharacterInputs v=r.input();ObjectNode n=object();n.put("projection_kind","current_character_detachment_suffix_v1");n.put("source_parent_rva","0x28CBE50");n.put("source_parent_identity",v==null?null:v.parentIdentity());n.put("current_date_storage_raw64",v==null?null:v.date());n.put("input_basis","ordered_same_query_current_character_suffix_seeds");n.put("seed_selection_ready",v!=null&&v.seedSelectionReady());n.put("seed_roster_ready",v!=null&&v.seedRosterReady());n.put("status",wire(r.status()));n.put("ready",r.ready());n.put("current_extension_inputs_ready",r.ready());n.set("requests",array(r.requests(),ArmyStrengthsDetachment::characterItemJson));n.put("known_current_input_prefix_count",r.prefix());n.set("independently_ready_request_indices",ints(r.independentlyReady()));n.set("no_suffix_request_indices",ints(r.noSuffix()));n.set("conditional_reset_descriptor_request_indices",ints(r.descriptorsReady()));n.set("current_source_chain_ready_request_indices",ints(r.sourceChainReady()));n.set("missing_current_extension_inputs",strings(r.missing()));n.set("remaining_stage_inputs",strings(r.remaining()));n.put("unavailable_reason",r.reason());characterLimits(n);return n;
    }
    private static JsonNode characterItemJson(CharacterItem r) {
        CharacterRequest v=r.input();ObjectNode n=object();n.put("request_index",r.index());n.put("seed_incoming_native_index",v.seedIndex());n.put("arrg_identity",v.arrgIdentity());n.put("character_full_id_148_u32",v.characterId());n.set("observed_character_resolution",encodeResolution(v.characterResolution()));n.put("observed_current_character_identity",v.characterResolution().objectIdentity());n.put("passed_province_identity",v.passedProvince());n.put("independent_same_query_current_seed",true);
        ObjectNode extension=object();extension.put("present",v.extensionPresent());extension.put("identity",v.extensionIdentity());extension.put("f8_raw_u32",v.extensionF8());extension.put("storage_100_raw64",v.extension100());n.set("observed_current_extension",extension);n.put("observed_extension_reset_inputs_ready",v.resetInputsReady());ObjectNode chain=object();chain.set("arrg_resolution",encodeResolution(v.arrgResolution()));chain.put("army_full_id_140_u32",v.armyId());chain.set("army_resolution",encodeResolution(v.armyResolution()));chain.put("unit_full_id_124_u32",v.unitId());chain.set("unit_resolution",encodeResolution(v.unitResolution()));n.set("observed_current_source_chain",chain);n.put("current_source_chain_ready",v.chainReady());n.put("observed_current_saved_unit_identity",v.unitResolution().objectIdentity());n.put("current_extension_branch_ready",r.branchReady());n.put("branch",characterBranch(r.branch()));n.put("no_suffix",r.noSuffix());n.put("reset_inputs_required",r.resetRequired());n.put("reset_inputs_ready",r.resetReady());n.put("source_defined_reset_descriptors_ready",r.descriptorsReady());n.set("source_defined_reset_descriptors",array(r.descriptors(),ArmyStrengthsDetachment::resetJson));n.set("missing_current_extension_inputs",strings(r.missing()));n.set("missing_optional_before_context",strings(r.optionalMissing()));n.set("remaining_stage_inputs",strings(r.remaining()));characterLimits(n);return n;
    }
    private static String characterBranch(CharacterBranch branch) { if(branch==null)return null;return switch(branch) { case INVALID_CHARACTER_FULL_ID_NO_SUFFIX->"invalid_character_full_id_no_suffix";case NULL_CURRENT_CHARACTER1B8_NO_SUFFIX->"null_current_character1b8_no_suffix";case NONNULL_CURRENT_CHARACTER1B8_CONDITIONAL_RESET_DESCRIPTORS->"nonnull_current_character1b8_conditional_reset_descriptors"; }; }
    private static JsonNode resetJson(ResetDescriptor value) {
        ObjectNode n=object();if(value instanceof InitialReset r) { n.put("target_role","captured_initial_extension");n.put("target_identity",r.target());n.put("field_offset","0xF8");n.put("before_current_raw_u32",r.before());n.put("source_defined_after_raw_u32",INVALID); }
        else if(value instanceof ReloadReset r) { n.put("target_role","fresh_character1B8_reload_if_nonnull");n.putNull("target_identity");n.put("field_offset","0x100");n.put("conditional_on","fresh_character1b8_reload_is_nonnull");n.put("source_defined_after_raw_u64_hex","0xFFFFFFFF029C77F8");n.put("source_defined_after_raw64",r.sourceAfter());n.put("fresh_target_observed",false); }else throw new IllegalArgumentException("unknown typed reset descriptor");
        n.put("source_defined_value_ready",true);n.put("descriptor_ready",true);n.put("source_reached",false);n.put("actual_write_observed",false);return n;
    }
    private static void characterLimits(ObjectNode n) { commonLimits(n);falseFields(n,"full_character_detachment_suffix_ready","future_date_ready","actual_reset_observed","source_reset_reached","post_reset_origin_ready","post_mutator_date_inputs_ready","actual_next_occurrence_ready"); }

    private static ObjectNode object() { return JsonNodeFactory.instance.objectNode(); }
    private static RawJson raw(JsonNode value) { return new RawJson(value.toString().getBytes(StandardCharsets.UTF_8)); }
    private static <T> ArrayNode array(List<T> values,Function<T,JsonNode> encoder) { ArrayNode a=JsonNodeFactory.instance.arrayNode();values.forEach(v->a.add(encoder.apply(v)));return a; }
    private static ArrayNode strings(List<String> values) { ArrayNode a=JsonNodeFactory.instance.arrayNode();values.forEach(a::add);return a; }
    private static ArrayNode ints(List<Integer> values) { ArrayNode a=JsonNodeFactory.instance.arrayNode();values.forEach(a::add);return a; }
    private static ObjectNode entry(PublicUnitId army,JsonNode projection) { ObjectNode n=object();n.put("army_id",army.value());n.set("projection",projection);return n; }
    private static String wire(Enum<?> value) { return value==null?null:value.name().toLowerCase(java.util.Locale.ROOT); }
    private static void prefix(List<String> target,String prefix,List<String> values) { values.forEach(value->target.add(prefix+value)); }
    private static boolean textok(String value) { return value!=null&&!value.isEmpty(); }
    private static boolean nativeok(String value) { return value!=null&&value.matches("native:[0-9]+")&&new BigInteger(value.substring(7)).bitLength()<=64; }
    private static void falseFields(ObjectNode n,String... keys) { for(String key:keys)n.put(key,false); }
    private static void commonLimits(ObjectNode n) { falseFields(n,"actual_callback_observed","actual_resource_return_observed","actual_after_state_observed","full_detachment_transition_ready","full_daily_ready","full_monthly_ready");n.put("native_calls_executed",0);n.put("native_writes_executed",0); }
}
