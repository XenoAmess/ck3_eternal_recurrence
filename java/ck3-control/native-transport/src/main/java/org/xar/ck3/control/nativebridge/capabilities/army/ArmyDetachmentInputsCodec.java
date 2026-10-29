package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyDetachmentDataInputs.*;

/** Exact original five input contracts. JSON is confined to this boundary; kernels consume immutable records. */
public final class ArmyDetachmentInputsCodec {
    private ArmyDetachmentInputsCodec() { }
    private static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private enum Profile { LOOSE_TEXT,NATIVE_TEXT,STRONG_RESOLUTION,CHARACTER }
    public enum SeedSelection { FIRST_VALID_CURRENT_RECEIVER,NOT_CALLED }
    public enum ObservedReturn { SELECTED_REGI,NATIVE_FALLBACK }
    public record MapperInputs(State state,boolean selectionReady,SeedSelection selectionBranch,Integer candidateReferenceIndex,Integer candidatePendingIndex,
            Long candidateRawId,Long candidateActualId,String candidateArmyIdentity,Integer rosterCount,Boolean rosterDataPresent,String rosterDataIdentity,
            boolean rosterReady,List<MapperOccurrence> occurrences,List<MapperInput> mappers,List<CountInput> counts) {
        public MapperInputs { occurrences=List.copyOf(occurrences);mappers=List.copyOf(mappers);counts=List.copyOf(counts); }
    }
    public record MapperOccurrence(State state,int nativeIndex,Long rawFullId,Resolution resolution,Integer mapperIndex) { }
    public record MapperInput(State state,int nativeIndex,String arrgIdentity,Integer kind14c,Integer dataCount,String firstDataRecordIdentity,
            Long firstRegiId,Resolution selectedResolution,Long selectedMagic,Boolean selectedValid,Integer countInputIndex,
            boolean returnSelectionReady,ObservedReturn returnSelection,String fallbackRegiIdentity,String returnedRegiIdentity,Long returnedRegiId,
            Long returnedMagic,Integer returnedState138) { }
    public record CountInput(State state,int nativeIndex,String regiIdentity,Integer base128,List<CountChunk> chunks) { public CountInput { chunks=List.copyOf(chunks); } }
    public record CountChunk(int physicalIndex,Integer maximum,Integer current,Integer state18) { }
    public record KnownCallbacks(String primaryVtable,String primarySlot0,String core,String mode0Record,String secondaryVtable) { }
    public record CallbackInputs(State state,boolean seedSelectionReady,boolean seedRosterReady,Long date,Integer mode,KnownCallbacks known,List<CallbackIncoming> incoming) {
        public CallbackInputs { incoming=List.copyOf(incoming); }
    }
    public record CallbackIncoming(State state,List<Integer> seedIndices,String arrgIdentity,Long arrgFullId,String primaryVtable,String primarySlot0,
            Boolean dataPresent,String dataBuffer,Integer dataCount,Integer dataCapacity,String allocator,String allocatorVtable,String allocatorSlot10,List<CallbackRecord> records) {
        public CallbackIncoming { seedIndices=List.copyOf(seedIndices);records=List.copyOf(records); }
    }
    public record CallbackRecord(State state,int nativeIndex,String recordIdentity,String vtableIdentity,String slot0TargetIdentity) { }
    public record StoreInputs(State state,boolean seedSelectionReady,boolean seedRosterReady,Long date,String parentIdentity,Integer mode,String registryIdentity,
            Integer flag48,Long slotCount,String slotTable,Long activeCount,Integer registryMark,Long highWater,Long freeHead,List<StoreRequest> requests) {
        public StoreInputs { requests=List.copyOf(requests); }
    }
    public record StoreRequest(State state,List<Integer> seedIndices,String incomingIdentity,Long requestedId,Long observedIndex,String slotIdentity,
            Boolean pointerPresent,String selectedIdentity,Long selectedId,String selectedVtable,String selectedSlot0,List<SlotScan> trailingScan) {
        public StoreRequest { seedIndices=List.copyOf(seedIndices);trailingScan=List.copyOf(trailingScan); }
    }
    public record SlotScan(State state,long slotIndex,String slotIdentity,Boolean pointerPresent,String objectIdentity) { }
    public record CharacterInputs(State state,boolean seedSelectionReady,boolean seedRosterReady,Long date,String parentIdentity,List<CharacterRequest> requests) {
        public CharacterInputs { requests=List.copyOf(requests); }
    }
    public record CharacterRequest(State state,int seedIndex,String arrgIdentity,Long characterId,Resolution characterResolution,String passedProvince,
            Boolean extensionPresent,String extensionIdentity,Long extensionF8,Long extension100,boolean resetInputsReady,boolean chainReady,
            Resolution arrgResolution,Long armyId,Resolution armyResolution,Long unitId,Resolution unitResolution) { }
    private static final Set<String> LIMITS=Set.of("actual_callback_observed","actual_resource_return_observed","actual_after_state_observed","full_detachment_transition_ready","full_daily_ready","full_monthly_ready");
    private static final Set<String> STATE=Set.of("status","ready","unavailable_reason");
    private static Set<String> fields(String... extra) { Set<String> result=new HashSet<>(STATE);result.addAll(List.of(extra));return Set.copyOf(result); }
    private static Set<String> limits(String... extra) { Set<String> result=new HashSet<>(fields(extra));result.addAll(LIMITS);return Set.copyOf(result); }
    private static final Set<String> RESOLUTION=fields("requested_full_id_u32","registry_loaded","registry_capacity_u32","registry_index_u32","indexed_identity","indexed_full_id_u32","selection","used_fallback","object_identity","selected_full_id_u32");
    private static State state(JsonNode n,Profile profile,boolean coherent) {
        Status status=switch(text(n,"status",false,false)) { case "available"->Status.AVAILABLE;case "partial"->Status.PARTIAL;case "unavailable"->Status.UNAVAILABLE;default->throw new IllegalArgumentException("detachment state status invalid"); };
        boolean ready=bool(n,"ready");String reason=text(n,"unavailable_reason",true,coherent||profile==Profile.CHARACTER||profile==Profile.STRONG_RESOLUTION);
        if(coherent)need(ready==(status==Status.AVAILABLE)&&(ready?reason==null:reason!=null),"detachment state readiness/reason differ");
        return new State(status,ready,reason);
    }
    private static Resolution resolution(JsonNode n,Long requested,Profile profile) {
        closed(n,RESOLUTION);State state=state(n,profile,profile==Profile.STRONG_RESOLUTION);
        Long raw=u32(n,"requested_full_id_u32"),capacity=u32(n,"registry_capacity_u32"),index=u32(n,"registry_index_u32"),indexed=u32(n,"indexed_full_id_u32"),selected=u32(n,"selected_full_id_u32");
        Boolean loaded=nullableBool(n,"registry_loaded"),fallback=nullableBool(n,"used_fallback");
        String indexedIdentity=identity(n,"indexed_identity",profile),objectIdentity=identity(n,"object_identity",profile),selection=text(n,"selection",true,false);
        Selection route=selection==null?null:switch(selection) { case "registry_full_id"->Selection.REGISTRY_FULL_ID;case "native_fallback"->Selection.NATIVE_FALLBACK;default->throw new IllegalArgumentException("detachment resolution selection invalid"); };
        if(profile==Profile.STRONG_RESOLUTION) {
            need(Objects.equals(raw,requested),"mapper resolution changed actual requested full ID");
            if(state.ready()) {
                need(objectIdentity!=null&&selected!=null&&route!=null&&fallback!=null&&fallback==(route==Selection.NATIVE_FALLBACK),"ready mapper resolution selected route incomplete");
                if(route==Selection.REGISTRY_FULL_ID)need(Objects.equals(selected,requested),"mapper registry generation differs");
            }
        }
        return new Resolution(state,raw,loaded,capacity,index,indexedIdentity,indexed,route,fallback,objectIdentity,selected);
    }
    public static MapperInputs decodeMapper(JsonNode n) {
        if(n==null||n.isNull())return null;
        closed(n,fields("schema_version","source","stage","selection_ready","selection_branch","candidate_reference_native_index","candidate_pending_native_index","candidate_raw_full_id_u32",
                "candidate_actual_full_id_u32","candidate_army_identity","roster_count_raw_i32","roster_data_present","roster_data_identity","roster_ready","occurrences","mappers","count_inputs"));
        top(n,"native_current_candidate_detachment_mapper_inputs","observed_current_first_candidate_mapper_seed");State state=state(n,Profile.LOOSE_TEXT,false);
        String selection=text(n,"selection_branch",true,false);need(selection==null||Set.of("first_valid_current_receiver","not_called").contains(selection),"candidate selection branch invalid");
        List<MapperOccurrence> occurrences=new ArrayList<>();int index=0;for(JsonNode item:array(n,"occurrences")) {
            closed(item,fields("native_index","raw_full_id_u32","resolution","mapper_index"));ordinal(item,index++);Long raw=u32(item,"raw_full_id_u32");
            occurrences.add(new MapperOccurrence(state(item,Profile.LOOSE_TEXT,false),index-1,raw,resolution(field(item,"resolution"),raw,Profile.STRONG_RESOLUTION),i32(item,"mapper_index")));
        }
        List<MapperInput> mappers=new ArrayList<>();index=0;for(JsonNode item:array(n,"mappers")) {
            closed(item,fields("native_index","arrg_identity","kind_14c_raw_i32","data_count_raw_i32","first_data_record_identity","first_regi_full_id_u32","selected_regi_resolution",
                    "selected_regi_magic_14_raw_u32","selected_regi_identity_valid","count_input_index","return_selection_ready","return_selection","fallback_regi_identity","returned_regi_identity",
                    "returned_regi_full_id_u32","returned_regi_magic_14_raw_u32","returned_state_138_raw_i32","return_basis"));ordinal(item,index++);
            Integer count=i32(item,"data_count_raw_i32");Long first=u32(item,"first_regi_full_id_u32");JsonNode rawResolution=field(item,"selected_regi_resolution");
            Resolution selected=rawResolution.isNull()?null:resolution(rawResolution,Integer.valueOf(0).equals(count)?4294967295L:first,Profile.STRONG_RESOLUTION);
            String returned=text(item,"return_selection",true,false);need(returned==null||Set.of("selected_regi","native_fallback").contains(returned),"mapper return selection invalid");
            eq(item,"return_basis","source2A977A0_from_same_capture_raw_operands");
            mappers.add(new MapperInput(state(item,Profile.LOOSE_TEXT,false),index-1,text(item,"arrg_identity",false,false),i32(item,"kind_14c_raw_i32"),count,
                    text(item,"first_data_record_identity",true,false),first,selected,u32(item,"selected_regi_magic_14_raw_u32"),nullableBool(item,"selected_regi_identity_valid"),
                    i32(item,"count_input_index"),bool(item,"return_selection_ready"),returned==null?null:ObservedReturn.valueOf(returned.toUpperCase(Locale.ROOT)),text(item,"fallback_regi_identity",true,false),text(item,"returned_regi_identity",true,false),
                    u32(item,"returned_regi_full_id_u32"),u32(item,"returned_regi_magic_14_raw_u32"),i32(item,"returned_state_138_raw_i32")));
        }
        List<CountInput> counts=new ArrayList<>();index=0;for(JsonNode item:array(n,"count_inputs")) {
            closed(item,fields("native_index","regi_identity","count_base_128_raw_i32","chunks"));ordinal(item,index++);List<CountChunk> chunks=new ArrayList<>();Set<Integer> seen=new HashSet<>();
            for(JsonNode chunk:array(item,"chunks")) {
                closed(chunk,Set.of("physical_index","maximum_00_raw_i32","current_04_raw_i32","state_18_raw_i32"));int physical=requiredI32(chunk,"physical_index");
                need(physical>=0&&physical<7&&seen.add(physical),"mapper count chunk physical index invalid/repeated");
                chunks.add(new CountChunk(physical,i32(chunk,"maximum_00_raw_i32"),i32(chunk,"current_04_raw_i32"),i32(chunk,"state_18_raw_i32")));
            }
            counts.add(new CountInput(state(item,Profile.LOOSE_TEXT,false),index-1,text(item,"regi_identity",false,false),i32(item,"count_base_128_raw_i32"),chunks));
        }
        return new MapperInputs(state,bool(n,"selection_ready"),selection==null?null:SeedSelection.valueOf(selection.toUpperCase(Locale.ROOT)),i32(n,"candidate_reference_native_index"),i32(n,"candidate_pending_native_index"),
                u32(n,"candidate_raw_full_id_u32"),u32(n,"candidate_actual_full_id_u32"),text(n,"candidate_army_identity",true,false),i32(n,"roster_count_raw_i32"),
                nullableBool(n,"roster_data_present"),text(n,"roster_data_identity",true,false),bool(n,"roster_ready"),occurrences,mappers,counts);
    }
    public static CallbackInputs decodeCallback(JsonNode n) {
        if(n==null||n.isNull())return null;
        closed(n,limits("schema_version","source","stage","seed_selection_ready","seed_roster_ready","current_date_storage_raw64","source_parent_wrapper_mode_i32","incoming",
                "known_primary_vtable_identity","known_primary_slot0_target_identity","known_core_identity","known_mode0_record_callback_identity","known_secondary_base_vtable_identity"));
        top(n,"native_current_detachment_callback_inputs_12004","observed_current_detachment_callback_seed");limits(n);State state=state(n,Profile.NATIVE_TEXT,true);Integer mode=mode(n);
        KnownCallbacks known=new KnownCallbacks(identity(n,"known_primary_vtable_identity",Profile.NATIVE_TEXT),identity(n,"known_primary_slot0_target_identity",Profile.NATIVE_TEXT),
                identity(n,"known_core_identity",Profile.NATIVE_TEXT),identity(n,"known_mode0_record_callback_identity",Profile.NATIVE_TEXT),identity(n,"known_secondary_base_vtable_identity",Profile.NATIVE_TEXT));
        List<CallbackIncoming> incoming=new ArrayList<>();for(JsonNode item:array(n,"incoming")) {
            closed(item,fields("seed_incoming_native_indices","arrg_identity","arrg_full_id_u32","arrg_primary_vtable_identity","arrg_primary_slot0_target_identity","data_pointer_present",
                    "data_buffer_identity","data_count_2c_raw_i32","data_capacity_28_raw_i32","data_allocator_identity","data_allocator_vtable_identity","data_allocator_slot10_target_identity","records"));
            List<CallbackRecord> records=new ArrayList<>();int index=0;for(JsonNode record:array(item,"records")) {
                closed(record,fields("native_index","record_identity","vtable_identity","slot0_target_identity"));ordinal(record,index++);
                records.add(new CallbackRecord(state(record,Profile.NATIVE_TEXT,true),index-1,identity(record,"record_identity",Profile.NATIVE_TEXT),identity(record,"vtable_identity",Profile.NATIVE_TEXT),identity(record,"slot0_target_identity",Profile.NATIVE_TEXT)));
            }
            incoming.add(new CallbackIncoming(state(item,Profile.NATIVE_TEXT,true),indices(item,"seed_incoming_native_indices"),identity(item,"arrg_identity",Profile.NATIVE_TEXT),u32(item,"arrg_full_id_u32"),
                    identity(item,"arrg_primary_vtable_identity",Profile.NATIVE_TEXT),identity(item,"arrg_primary_slot0_target_identity",Profile.NATIVE_TEXT),nullableBool(item,"data_pointer_present"),
                    identity(item,"data_buffer_identity",Profile.NATIVE_TEXT),i32(item,"data_count_2c_raw_i32"),i32(item,"data_capacity_28_raw_i32"),identity(item,"data_allocator_identity",Profile.NATIVE_TEXT),
                    identity(item,"data_allocator_vtable_identity",Profile.NATIVE_TEXT),identity(item,"data_allocator_slot10_target_identity",Profile.NATIVE_TEXT),records));
        }
        return new CallbackInputs(state,bool(n,"seed_selection_ready"),bool(n,"seed_roster_ready"),i64(n,"current_date_storage_raw64"),mode,known,incoming);
    }
    public static StoreInputs decodeStore(JsonNode n) {
        if(n==null||n.isNull())return null;
        closed(n,limits("schema_version","source","stage","seed_selection_ready","seed_roster_ready","current_date_storage_raw64","source_parent_identity","source_parent_wrapper_mode_i32",
                "registry_identity","store_48_raw_u8","slot_count_2c_raw_u32","slot_table_identity","active_count_3c_raw_u32","registry_mark_4a_raw_u8","high_water_38_raw_u32","free_head_40_raw_u32","requests"));
        top(n,"native_current_detachment_store_inputs_12004","observed_current_detachment_store_seed");limits(n);List<StoreRequest> requests=new ArrayList<>();
        for(JsonNode item:array(n,"requests")) {
            closed(item,fields("seed_incoming_native_indices","incoming_arrg_identity","requested_full_id_u32","index_low24_u32","slot_identity","selected_pointer_present","selected_object_identity",
                    "selected_full_id_10_raw_u32","selected_primary_vtable_identity","selected_slot0_target_identity","trailing_slot_scan"));List<SlotScan> scans=new ArrayList<>();
            for(JsonNode scan:array(item,"trailing_slot_scan")) {
                closed(scan,fields("slot_index_u32","slot_identity","object_pointer_present","object_identity"));
                scans.add(new SlotScan(state(scan,Profile.NATIVE_TEXT,true),requiredU32(scan,"slot_index_u32"),identity(scan,"slot_identity",Profile.NATIVE_TEXT),nullableBool(scan,"object_pointer_present"),identity(scan,"object_identity",Profile.NATIVE_TEXT)));
            }
            requests.add(new StoreRequest(state(item,Profile.NATIVE_TEXT,true),indices(item,"seed_incoming_native_indices"),identity(item,"incoming_arrg_identity",Profile.NATIVE_TEXT),
                    u32(item,"requested_full_id_u32"),u32(item,"index_low24_u32"),identity(item,"slot_identity",Profile.NATIVE_TEXT),nullableBool(item,"selected_pointer_present"),
                    identity(item,"selected_object_identity",Profile.NATIVE_TEXT),u32(item,"selected_full_id_10_raw_u32"),identity(item,"selected_primary_vtable_identity",Profile.NATIVE_TEXT),identity(item,"selected_slot0_target_identity",Profile.NATIVE_TEXT),scans));
        }
        return new StoreInputs(state(n,Profile.NATIVE_TEXT,true),bool(n,"seed_selection_ready"),bool(n,"seed_roster_ready"),i64(n,"current_date_storage_raw64"),identity(n,"source_parent_identity",Profile.NATIVE_TEXT),mode(n),
                identity(n,"registry_identity",Profile.NATIVE_TEXT),u8(n,"store_48_raw_u8"),u32(n,"slot_count_2c_raw_u32"),identity(n,"slot_table_identity",Profile.NATIVE_TEXT),u32(n,"active_count_3c_raw_u32"),
                u8(n,"registry_mark_4a_raw_u8"),u32(n,"high_water_38_raw_u32"),u32(n,"free_head_40_raw_u32"),requests);
    }
    public static CharacterInputs decodeCharacter(JsonNode n) {
        if(n==null||n.isNull())return null;Set<String> expected=new HashSet<>(limits("schema_version","source","stage","seed_selection_ready","seed_roster_ready","current_date_storage_raw64","source_parent_identity","requests"));
        expected.addAll(Set.of("full_character_detachment_suffix_ready","future_date_ready"));closed(n,expected);
        top(n,"native_current_character_detachment_inputs_12004","observed_current_character_detachment_seed");limits(n);need(!bool(n,"full_character_detachment_suffix_ready")&&!bool(n,"future_date_ready"),"character suffix/future date must remain unknown");
        List<CharacterRequest> requests=new ArrayList<>();for(JsonNode item:array(n,"requests")) {
            closed(item,fields("seed_incoming_native_index","arrg_identity","character_full_id_148_u32","character_resolution","passed_province_identity","current_extension_1b8_present","current_extension_1b8_identity",
                    "extension_f8_raw_u32","extension_100_raw64","extension_reset_inputs_ready","source_chain_ready","arrg_resolution","army_full_id_140_u32","army_resolution","unit_full_id_124_u32","unit_resolution"));
            int index=requiredI32(item,"seed_incoming_native_index");need(index>=0,"character seed occurrence must be nonnegative");
            requests.add(new CharacterRequest(state(item,Profile.CHARACTER,false),index,identity(item,"arrg_identity",Profile.CHARACTER),u32(item,"character_full_id_148_u32"),resolution(field(item,"character_resolution"),null,Profile.CHARACTER),
                    identity(item,"passed_province_identity",Profile.CHARACTER),nullableBool(item,"current_extension_1b8_present"),identity(item,"current_extension_1b8_identity",Profile.CHARACTER),u32(item,"extension_f8_raw_u32"),i64(item,"extension_100_raw64"),
                    bool(item,"extension_reset_inputs_ready"),bool(item,"source_chain_ready"),resolution(field(item,"arrg_resolution"),null,Profile.CHARACTER),u32(item,"army_full_id_140_u32"),resolution(field(item,"army_resolution"),null,Profile.CHARACTER),
                    u32(item,"unit_full_id_124_u32"),resolution(field(item,"unit_resolution"),null,Profile.CHARACTER)));
        }
        return new CharacterInputs(state(n,Profile.CHARACTER,false),bool(n,"seed_selection_ready"),bool(n,"seed_roster_ready"),i64(n,"current_date_storage_raw64"),identity(n,"source_parent_identity",Profile.CHARACTER),requests);
    }
    public static ArmyDetachmentDataInputs decodeData(JsonNode n) {
        if(n==null||n.isNull())return null;
        closed(n,fields("schema_version","source","stage","selection_ready","roster_ready","current_date_storage_raw64","primary_receiver_identity","canonical_pending_vtable_identity","ready_pending_callback_identity","candidate_occurrences","incoming"));
        top(n,"native_current_detachment_data_inputs","observed_current_incoming_2633ff0_seed");List<Candidate> candidates=new ArrayList<>();int index=0;
        for(JsonNode item:array(n,"candidate_occurrences")) {
            closed(item,fields("native_index","raw_full_id_u32","resolution","magic_14_raw_u32","incoming_valid","incoming_index"));ordinal(item,index++);
            candidates.add(new Candidate(state(item,Profile.NATIVE_TEXT,false),index-1,u32(item,"raw_full_id_u32"),resolution(field(item,"resolution"),null,Profile.NATIVE_TEXT),u32(item,"magic_14_raw_u32"),nullableBool(item,"incoming_valid"),i32(item,"incoming_index")));
        }
        List<Incoming> incoming=new ArrayList<>();index=0;for(JsonNode item:array(n,"incoming")) {
            closed(item,fields("native_index","arrg_identity","arrg_full_id_u32","army_full_id_140_u32","unit_full_id_124_u32","army_resolution","unit_resolution","passed_province_identity","data_pointer_identity","data_count_raw_i32",
                    "captured_cursor_identity","captured_end_identity","data_ready","character_full_id_148_u32","character_resolution","character_pointer_1b8_present","character_pointer_1b8_identity","data_occurrences","physical_chunks","association_inputs","owner_inputs","date_inputs","pending"));ordinal(item,index++);
            List<DataOccurrence> data=new ArrayList<>();int position=0;for(JsonNode row:array(item,"data_occurrences")) {
                closed(row,fields("native_index","record_identity","raw_regi_full_id_u32","data_ordinal_raw_i32","held_fallback_regi_identity","resolution","magic_14_raw_u32","identity_valid","physical_chunk_present","physical_chunk_index"));ordinal(row,position++);
                data.add(new DataOccurrence(state(row,Profile.NATIVE_TEXT,false),position-1,identity(row,"record_identity",Profile.NATIVE_TEXT),u32(row,"raw_regi_full_id_u32"),i32(row,"data_ordinal_raw_i32"),identity(row,"held_fallback_regi_identity",Profile.NATIVE_TEXT),resolution(field(row,"resolution"),null,Profile.NATIVE_TEXT),u32(row,"magic_14_raw_u32"),nullableBool(row,"identity_valid"),nullableBool(row,"physical_chunk_present"),i32(row,"physical_chunk_index")));
            }
            List<PhysicalChunk> chunks=new ArrayList<>();position=0;for(JsonNode row:array(item,"physical_chunks")) {
                closed(row,fields("native_index","chunk_identity","maximum_00_raw_i32","current_04_raw_i32","owner_08_raw_u32","ordinal_0c_raw_i32","association_10_raw_u32","flag_14_raw_u8","date_1c_raw64"));ordinal(row,position++);
                chunks.add(new PhysicalChunk(state(row,Profile.NATIVE_TEXT,false),position-1,identity(row,"chunk_identity",Profile.NATIVE_TEXT),i32(row,"maximum_00_raw_i32"),i32(row,"current_04_raw_i32"),u32(row,"owner_08_raw_u32"),i32(row,"ordinal_0c_raw_i32"),u32(row,"association_10_raw_u32"),u8(row,"flag_14_raw_u8"),i64(row,"date_1c_raw64")));
            }
            List<Association> associations=new ArrayList<>();for(JsonNode row:array(item,"association_inputs")) {
                closed(row,fields("requested_full_id_u32","arrg_resolution","army_full_id_140_u32","army_resolution","unit_full_id_124_u32","unit_resolution","character_full_id_174_u32","character_resolution","context_pointer_identity","context_count_0c_raw_u32"));
                associations.add(new Association(state(row,Profile.NATIVE_TEXT,false),u32(row,"requested_full_id_u32"),resolution(field(row,"arrg_resolution"),null,Profile.NATIVE_TEXT),u32(row,"army_full_id_140_u32"),resolution(field(row,"army_resolution"),null,Profile.NATIVE_TEXT),u32(row,"unit_full_id_124_u32"),resolution(field(row,"unit_resolution"),null,Profile.NATIVE_TEXT),u32(row,"character_full_id_174_u32"),resolution(field(row,"character_resolution"),null,Profile.NATIVE_TEXT),identity(row,"context_pointer_identity",Profile.NATIVE_TEXT),u32(row,"context_count_0c_raw_u32")));
            }
            List<Owner> owners=new ArrayList<>();for(JsonNode row:array(item,"owner_inputs")) {
                closed(row,fields("requested_full_id_u32","resolution","state_138_raw_i32","definition_identity","definition_magic_38_raw_u32","origin_identity","origin_magic_85c_raw_u32"));
                owners.add(new Owner(state(row,Profile.NATIVE_TEXT,false),u32(row,"requested_full_id_u32"),resolution(field(row,"resolution"),null,Profile.NATIVE_TEXT),i32(row,"state_138_raw_i32"),identity(row,"definition_identity",Profile.NATIVE_TEXT),u32(row,"definition_magic_38_raw_u32"),identity(row,"origin_identity",Profile.NATIVE_TEXT),u32(row,"origin_magic_85c_raw_u32")));
            }
            List<DateInput> dates=new ArrayList<>();for(JsonNode row:array(item,"date_inputs")) {
                closed(row,fields("association_full_id_u32","owner_full_id_u32","unit_identity","source_origin_identity","source_origin_magic_85c_raw_u32","capital_origin_identity","capital_origin_magic_85c_raw_u32","output_date_raw64","basis"));
                dates.add(new DateInput(state(row,Profile.NATIVE_TEXT,false),u32(row,"association_full_id_u32"),u32(row,"owner_full_id_u32"),identity(row,"unit_identity",Profile.NATIVE_TEXT),identity(row,"source_origin_identity",Profile.NATIVE_TEXT),u32(row,"source_origin_magic_85c_raw_u32"),identity(row,"capital_origin_identity",Profile.NATIVE_TEXT),u32(row,"capital_origin_magic_85c_raw_u32"),i64(row,"output_date_raw64"),text(row,"basis",true,false)));
            }
            JsonNode raw=field(item,"pending");closed(raw,fields("header_identity","buffer_identity","capacity_08_raw_i32","count_0c_raw_i32","allocator_identity","records"));
            List<PendingRecord> records=new ArrayList<>();position=0;for(JsonNode row:array(raw,"records")) {
                closed(row,fields("native_index","record_identity","vtable_identity","slot0_target_identity","owner_08_raw_u32","ordinal_0c_raw_i32"));ordinal(row,position++);
                records.add(new PendingRecord(state(row,Profile.NATIVE_TEXT,false),position-1,identity(row,"record_identity",Profile.NATIVE_TEXT),identity(row,"vtable_identity",Profile.NATIVE_TEXT),identity(row,"slot0_target_identity",Profile.NATIVE_TEXT),u32(row,"owner_08_raw_u32"),i32(row,"ordinal_0c_raw_i32")));
            }
            Pending pending=new Pending(state(raw,Profile.NATIVE_TEXT,false),identity(raw,"header_identity",Profile.NATIVE_TEXT),identity(raw,"buffer_identity",Profile.NATIVE_TEXT),i32(raw,"capacity_08_raw_i32"),i32(raw,"count_0c_raw_i32"),identity(raw,"allocator_identity",Profile.NATIVE_TEXT),records);
            JsonNode character=field(item,"character_resolution");incoming.add(new Incoming(state(item,Profile.NATIVE_TEXT,false),index-1,identity(item,"arrg_identity",Profile.NATIVE_TEXT),u32(item,"arrg_full_id_u32"),u32(item,"army_full_id_140_u32"),u32(item,"unit_full_id_124_u32"),
                    resolution(field(item,"army_resolution"),null,Profile.NATIVE_TEXT),resolution(field(item,"unit_resolution"),null,Profile.NATIVE_TEXT),identity(item,"passed_province_identity",Profile.NATIVE_TEXT),identity(item,"data_pointer_identity",Profile.NATIVE_TEXT),i32(item,"data_count_raw_i32"),
                    identity(item,"captured_cursor_identity",Profile.NATIVE_TEXT),identity(item,"captured_end_identity",Profile.NATIVE_TEXT),bool(item,"data_ready"),u32(item,"character_full_id_148_u32"),character.isNull()?null:resolution(character,null,Profile.NATIVE_TEXT),nullableBool(item,"character_pointer_1b8_present"),identity(item,"character_pointer_1b8_identity",Profile.NATIVE_TEXT),data,chunks,associations,owners,dates,pending));
        }
        return new ArmyDetachmentDataInputs(state(n,Profile.NATIVE_TEXT,false),bool(n,"selection_ready"),bool(n,"roster_ready"),i64(n,"current_date_storage_raw64"),identity(n,"primary_receiver_identity",Profile.NATIVE_TEXT),identity(n,"canonical_pending_vtable_identity",Profile.NATIVE_TEXT),identity(n,"ready_pending_callback_identity",Profile.NATIVE_TEXT),candidates,incoming);
    }
    public static JsonNode encodeMapper(MapperInputs v) {
        if(v==null)return NullNode.instance;ObjectNode n=header(v.state(),"native_current_candidate_detachment_mapper_inputs","observed_current_first_candidate_mapper_seed");
        n.put("selection_ready",v.selectionReady());n.put("selection_branch",v.selectionBranch()==null?null:v.selectionBranch().name().toLowerCase(Locale.ROOT));n.put("candidate_reference_native_index",v.candidateReferenceIndex());n.put("candidate_pending_native_index",v.candidatePendingIndex());
        n.put("candidate_raw_full_id_u32",v.candidateRawId());n.put("candidate_actual_full_id_u32",v.candidateActualId());n.put("candidate_army_identity",v.candidateArmyIdentity());n.put("roster_count_raw_i32",v.rosterCount());n.put("roster_data_present",v.rosterDataPresent());n.put("roster_data_identity",v.rosterDataIdentity());n.put("roster_ready",v.rosterReady());
        n.set("occurrences",encodeRows(v.occurrences(),r->{ObjectNode o=encodeState(r.state());o.put("native_index",r.nativeIndex());o.put("raw_full_id_u32",r.rawFullId());o.set("resolution",encodeResolution(r.resolution()));o.put("mapper_index",r.mapperIndex());return o;}));
        n.set("mappers",encodeRows(v.mappers(),r->{ObjectNode o=encodeState(r.state());o.put("native_index",r.nativeIndex());o.put("arrg_identity",r.arrgIdentity());o.put("kind_14c_raw_i32",r.kind14c());o.put("data_count_raw_i32",r.dataCount());o.put("first_data_record_identity",r.firstDataRecordIdentity());o.put("first_regi_full_id_u32",r.firstRegiId());o.set("selected_regi_resolution",encodeResolution(r.selectedResolution()));o.put("selected_regi_magic_14_raw_u32",r.selectedMagic());o.put("selected_regi_identity_valid",r.selectedValid());o.put("count_input_index",r.countInputIndex());o.put("return_selection_ready",r.returnSelectionReady());o.put("return_selection",r.returnSelection()==null?null:r.returnSelection().name().toLowerCase(Locale.ROOT));o.put("fallback_regi_identity",r.fallbackRegiIdentity());o.put("returned_regi_identity",r.returnedRegiIdentity());o.put("returned_regi_full_id_u32",r.returnedRegiId());o.put("returned_regi_magic_14_raw_u32",r.returnedMagic());o.put("returned_state_138_raw_i32",r.returnedState138());o.put("return_basis","source2A977A0_from_same_capture_raw_operands");return o;}));
        n.set("count_inputs",encodeRows(v.counts(),r->{ObjectNode o=encodeState(r.state());o.put("native_index",r.nativeIndex());o.put("regi_identity",r.regiIdentity());o.put("count_base_128_raw_i32",r.base128());o.set("chunks",encodeRows(r.chunks(),c->{ObjectNode a=object();a.put("physical_index",c.physicalIndex());a.put("maximum_00_raw_i32",c.maximum());a.put("current_04_raw_i32",c.current());a.put("state_18_raw_i32",c.state18());return a;}));return o;}));
        decodeMapper(n);return n;
    }
    public static JsonNode encodeCallback(CallbackInputs v) {
        if(v==null)return NullNode.instance;ObjectNode n=header(v.state(),"native_current_detachment_callback_inputs_12004","observed_current_detachment_callback_seed");encodeLimits(n);
        n.put("seed_selection_ready",v.seedSelectionReady());n.put("seed_roster_ready",v.seedRosterReady());n.put("current_date_storage_raw64",v.date());n.put("source_parent_wrapper_mode_i32",v.mode());
        n.put("known_primary_vtable_identity",v.known().primaryVtable());n.put("known_primary_slot0_target_identity",v.known().primarySlot0());n.put("known_core_identity",v.known().core());n.put("known_mode0_record_callback_identity",v.known().mode0Record());n.put("known_secondary_base_vtable_identity",v.known().secondaryVtable());
        n.set("incoming",encodeRows(v.incoming(),r->{ObjectNode o=encodeState(r.state());o.set("seed_incoming_native_indices",encodeInts(r.seedIndices()));o.put("arrg_identity",r.arrgIdentity());o.put("arrg_full_id_u32",r.arrgFullId());o.put("arrg_primary_vtable_identity",r.primaryVtable());o.put("arrg_primary_slot0_target_identity",r.primarySlot0());o.put("data_pointer_present",r.dataPresent());o.put("data_buffer_identity",r.dataBuffer());o.put("data_count_2c_raw_i32",r.dataCount());o.put("data_capacity_28_raw_i32",r.dataCapacity());o.put("data_allocator_identity",r.allocator());o.put("data_allocator_vtable_identity",r.allocatorVtable());o.put("data_allocator_slot10_target_identity",r.allocatorSlot10());o.set("records",encodeRows(r.records(),ArmyDetachmentInputsCodec::encodeCallbackRecord));return o;}));
        decodeCallback(n);return n;
    }
    public static JsonNode encodeCallbackRecord(CallbackRecord r) {
        ObjectNode o=encodeState(r.state());o.put("native_index",r.nativeIndex());o.put("record_identity",r.recordIdentity());o.put("vtable_identity",r.vtableIdentity());o.put("slot0_target_identity",r.slot0TargetIdentity());return o;
    }
    public static JsonNode encodeStore(StoreInputs v) {
        if(v==null)return NullNode.instance;ObjectNode n=header(v.state(),"native_current_detachment_store_inputs_12004","observed_current_detachment_store_seed");encodeLimits(n);
        n.put("seed_selection_ready",v.seedSelectionReady());n.put("seed_roster_ready",v.seedRosterReady());n.put("current_date_storage_raw64",v.date());n.put("source_parent_identity",v.parentIdentity());n.put("source_parent_wrapper_mode_i32",v.mode());
        n.put("registry_identity",v.registryIdentity());n.put("store_48_raw_u8",v.flag48());n.put("slot_count_2c_raw_u32",v.slotCount());n.put("slot_table_identity",v.slotTable());n.put("active_count_3c_raw_u32",v.activeCount());n.put("registry_mark_4a_raw_u8",v.registryMark());n.put("high_water_38_raw_u32",v.highWater());n.put("free_head_40_raw_u32",v.freeHead());
        n.set("requests",encodeRows(v.requests(),r->{ObjectNode o=encodeState(r.state());o.set("seed_incoming_native_indices",encodeInts(r.seedIndices()));o.put("incoming_arrg_identity",r.incomingIdentity());o.put("requested_full_id_u32",r.requestedId());o.put("index_low24_u32",r.observedIndex());o.put("slot_identity",r.slotIdentity());o.put("selected_pointer_present",r.pointerPresent());o.put("selected_object_identity",r.selectedIdentity());o.put("selected_full_id_10_raw_u32",r.selectedId());o.put("selected_primary_vtable_identity",r.selectedVtable());o.put("selected_slot0_target_identity",r.selectedSlot0());o.set("trailing_slot_scan",encodeRows(r.trailingScan(),ArmyDetachmentInputsCodec::encodeSlotScan));return o;}));
        decodeStore(n);return n;
    }
    public static JsonNode encodeSlotScan(SlotScan r) { ObjectNode o=encodeState(r.state());o.put("slot_index_u32",r.slotIndex());o.put("slot_identity",r.slotIdentity());o.put("object_pointer_present",r.pointerPresent());o.put("object_identity",r.objectIdentity());return o; }
    public static JsonNode encodeCharacter(CharacterInputs v) {
        if(v==null)return NullNode.instance;ObjectNode n=header(v.state(),"native_current_character_detachment_inputs_12004","observed_current_character_detachment_seed");encodeLimits(n);n.put("full_character_detachment_suffix_ready",false);n.put("future_date_ready",false);
        n.put("seed_selection_ready",v.seedSelectionReady());n.put("seed_roster_ready",v.seedRosterReady());n.put("current_date_storage_raw64",v.date());n.put("source_parent_identity",v.parentIdentity());
        n.set("requests",encodeRows(v.requests(),r->{ObjectNode o=encodeState(r.state());o.put("seed_incoming_native_index",r.seedIndex());o.put("arrg_identity",r.arrgIdentity());o.put("character_full_id_148_u32",r.characterId());o.set("character_resolution",encodeResolution(r.characterResolution()));o.put("passed_province_identity",r.passedProvince());o.put("current_extension_1b8_present",r.extensionPresent());o.put("current_extension_1b8_identity",r.extensionIdentity());o.put("extension_f8_raw_u32",r.extensionF8());o.put("extension_100_raw64",r.extension100());o.put("extension_reset_inputs_ready",r.resetInputsReady());o.put("source_chain_ready",r.chainReady());o.set("arrg_resolution",encodeResolution(r.arrgResolution()));o.put("army_full_id_140_u32",r.armyId());o.set("army_resolution",encodeResolution(r.armyResolution()));o.put("unit_full_id_124_u32",r.unitId());o.set("unit_resolution",encodeResolution(r.unitResolution()));return o;}));
        decodeCharacter(n);return n;
    }
    public static JsonNode encodeData(ArmyDetachmentDataInputs v) {
        if(v==null)return NullNode.instance;ObjectNode n=header(v.state(),"native_current_detachment_data_inputs","observed_current_incoming_2633ff0_seed");n.put("selection_ready",v.selectionReady());n.put("roster_ready",v.rosterReady());n.put("current_date_storage_raw64",v.currentDateStorageRaw64());n.put("primary_receiver_identity",v.primaryReceiverIdentity());n.put("canonical_pending_vtable_identity",v.canonicalPendingVtableIdentity());n.put("ready_pending_callback_identity",v.readyPendingCallbackIdentity());
        n.set("candidate_occurrences",encodeRows(v.candidateOccurrences(),r->{ObjectNode o=encodeState(r.state());o.put("native_index",r.nativeIndex());o.put("raw_full_id_u32",r.rawFullId());o.set("resolution",encodeResolution(r.resolution()));o.put("magic_14_raw_u32",r.magic14());o.put("incoming_valid",r.incomingValid());o.put("incoming_index",r.incomingIndex());return o;}));
        n.set("incoming",encodeRows(v.incoming(),r->{ObjectNode o=encodeState(r.state());o.put("native_index",r.nativeIndex());o.put("arrg_identity",r.arrgIdentity());o.put("arrg_full_id_u32",r.arrgFullId());o.put("army_full_id_140_u32",r.armyFullId140());o.put("unit_full_id_124_u32",r.unitFullId124());o.set("army_resolution",encodeResolution(r.armyResolution()));o.set("unit_resolution",encodeResolution(r.unitResolution()));o.put("passed_province_identity",r.passedProvinceIdentity());o.put("data_pointer_identity",r.dataPointerIdentity());o.put("data_count_raw_i32",r.dataCount());o.put("captured_cursor_identity",r.capturedCursorIdentity());o.put("captured_end_identity",r.capturedEndIdentity());o.put("data_ready",r.dataReady());o.put("character_full_id_148_u32",r.characterFullId148());o.set("character_resolution",encodeResolution(r.characterResolution()));o.put("character_pointer_1b8_present",r.characterPointer1b8Present());o.put("character_pointer_1b8_identity",r.characterPointer1b8Identity());
            o.set("data_occurrences",encodeRows(r.dataOccurrences(),a->{ObjectNode b=encodeState(a.state());b.put("native_index",a.nativeIndex());b.put("record_identity",a.recordIdentity());b.put("raw_regi_full_id_u32",a.rawRegiFullId());b.put("data_ordinal_raw_i32",a.dataOrdinal());b.put("held_fallback_regi_identity",a.heldFallbackRegiIdentity());b.set("resolution",encodeResolution(a.resolution()));b.put("magic_14_raw_u32",a.magic14());b.put("identity_valid",a.identityValid());b.put("physical_chunk_present",a.physicalChunkPresent());b.put("physical_chunk_index",a.physicalChunkIndex());return b;}));
            o.set("physical_chunks",encodeRows(r.physicalChunks(),ArmyDetachmentInputsCodec::encodePhysicalChunk));
            o.set("association_inputs",encodeRows(r.associationInputs(),a->{ObjectNode b=encodeState(a.state());b.put("requested_full_id_u32",a.requestedFullId());b.set("arrg_resolution",encodeResolution(a.arrgResolution()));b.put("army_full_id_140_u32",a.armyFullId140());b.set("army_resolution",encodeResolution(a.armyResolution()));b.put("unit_full_id_124_u32",a.unitFullId124());b.set("unit_resolution",encodeResolution(a.unitResolution()));b.put("character_full_id_174_u32",a.characterFullId174());b.set("character_resolution",encodeResolution(a.characterResolution()));b.put("context_pointer_identity",a.contextPointerIdentity());b.put("context_count_0c_raw_u32",a.contextCount0c());return b;}));
            o.set("owner_inputs",encodeRows(r.ownerInputs(),a->{ObjectNode b=encodeState(a.state());b.put("requested_full_id_u32",a.requestedFullId());b.set("resolution",encodeResolution(a.resolution()));b.put("state_138_raw_i32",a.state138());b.put("definition_identity",a.definitionIdentity());b.put("definition_magic_38_raw_u32",a.definitionMagic38());b.put("origin_identity",a.originIdentity());b.put("origin_magic_85c_raw_u32",a.originMagic85c());return b;}));
            o.set("date_inputs",encodeRows(r.dateInputs(),a->{ObjectNode b=encodeState(a.state());b.put("association_full_id_u32",a.associationFullId());b.put("owner_full_id_u32",a.ownerFullId());b.put("unit_identity",a.unitIdentity());b.put("source_origin_identity",a.sourceOriginIdentity());b.put("source_origin_magic_85c_raw_u32",a.sourceOriginMagic85c());b.put("capital_origin_identity",a.capitalOriginIdentity());b.put("capital_origin_magic_85c_raw_u32",a.capitalOriginMagic85c());b.put("output_date_raw64",a.outputDateRaw64());b.put("basis",a.basis());return b;}));
            Pending a=r.pending();ObjectNode b=encodeState(a.state());b.put("header_identity",a.headerIdentity());b.put("buffer_identity",a.bufferIdentity());b.put("capacity_08_raw_i32",a.capacity08());b.put("count_0c_raw_i32",a.count0c());b.put("allocator_identity",a.allocatorIdentity());b.set("records",encodeRows(a.records(),c->{ObjectNode d=encodeState(c.state());d.put("native_index",c.nativeIndex());d.put("record_identity",c.recordIdentity());d.put("vtable_identity",c.vtableIdentity());d.put("slot0_target_identity",c.slot0TargetIdentity());d.put("owner_08_raw_u32",c.owner08());d.put("ordinal_0c_raw_i32",c.ordinal0c());return d;}));o.set("pending",b);return o;}));
        decodeData(n);return n;
    }
    public static JsonNode encodePhysicalChunk(PhysicalChunk r) { ObjectNode o=encodeState(r.state());o.put("native_index",r.nativeIndex());o.put("chunk_identity",r.chunkIdentity());o.put("maximum_00_raw_i32",r.maximum00());o.put("current_04_raw_i32",r.current04());o.put("owner_08_raw_u32",r.owner08());o.put("ordinal_0c_raw_i32",r.ordinal0c());o.put("association_10_raw_u32",r.association10());o.put("flag_14_raw_u8",r.flag14());o.put("date_1c_raw64",r.date1cRaw64());return o; }
    public static JsonNode encodeResolution(Resolution v) {
        if(v==null)return NullNode.instance;ObjectNode n=encodeState(v.state());n.put("requested_full_id_u32",v.requestedFullId());n.put("registry_loaded",v.registryLoaded());n.put("registry_capacity_u32",v.registryCapacity());n.put("registry_index_u32",v.registryIndex());n.put("indexed_identity",v.indexedIdentity());n.put("indexed_full_id_u32",v.indexedFullId());n.put("selection",v.selection()==null?null:v.selection().name().toLowerCase(Locale.ROOT));n.put("used_fallback",v.usedFallback());n.put("object_identity",v.objectIdentity());n.put("selected_full_id_u32",v.selectedFullId());return n;
    }
    private static ObjectNode object() { return com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode(); }
    private static ObjectNode encodeState(State v) { ObjectNode n=object();n.put("status",v.status().name().toLowerCase(Locale.ROOT));n.put("ready",v.ready());n.put("unavailable_reason",v.unavailableReason());return n; }
    private static ObjectNode header(State state,String source,String stage) { ObjectNode n=encodeState(state);n.put("schema_version",1);n.put("source",source);n.put("stage",stage);return n; }
    private static void encodeLimits(ObjectNode n) { for(String key:LIMITS)n.put(key,false); }
    private static <T> JsonNode encodeRows(List<T> values,Function<T,JsonNode> encoder) { var a=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();values.forEach(v->a.add(encoder.apply(v)));return a; }
    private static JsonNode encodeInts(List<Integer> values) { var a=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();values.forEach(a::add);return a; }
    private static void top(JsonNode n,String source,String stage) { need(requiredI32(n,"schema_version")==1,"detachment schema version must equal one");eq(n,"source",source);eq(n,"stage",stage); }
    private static void limits(JsonNode n) { for(String key:LIMITS)need(!bool(n,key),"observed detachment effects must stay false: "+key); }
    private static Integer mode(JsonNode n) { Integer result=i32(n,"source_parent_wrapper_mode_i32");need(result==null||result==0,"detachment wrapper mode lacks actual4 source witness");return result; }
    private static void ordinal(JsonNode n,int index) { need(requiredI32(n,"native_index")==index,"detachment original occurrence order changed"); }
    private static List<Integer> indices(JsonNode n,String key) { List<Integer> result=new ArrayList<>();for(JsonNode v:array(n,key)) { int index=number(v,Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact();need(index>=0,"seed alias index must be nonnegative");result.add(index); }return List.copyOf(result); }
    private static JsonNode field(JsonNode n,String key) { need(n!=null&&n.isObject()&&n.has(key),"missing detachment field "+key);return n.get(key); }
    private static void closed(JsonNode n,Set<String> expected) { need(n!=null&&n.isObject(),"detachment object required");Set<String> actual=new HashSet<>();n.fieldNames().forEachRemaining(actual::add);need(expected.equals(actual),"detachment fields differ from strict source contract"); }
    private static List<JsonNode> array(JsonNode n,String key) { JsonNode v=field(n,key);need(v.isArray(),"ordered detachment array required: "+key);List<JsonNode> result=new ArrayList<>();v.forEach(result::add);return result; }
    private static String text(JsonNode n,String key,boolean nullable,boolean nonempty) { JsonNode v=field(n,key);if(v.isNull()&&nullable)return null;need(v.isTextual()&&(!nonempty||!v.textValue().isEmpty()),"detachment text required: "+key);return v.textValue(); }
    private static String identity(JsonNode n,String key,Profile profile) {
        String value=text(n,key,true,profile!=Profile.LOOSE_TEXT);if(value==null)return null;
        if(profile==Profile.NATIVE_TEXT||profile==Profile.CHARACTER)need(value.matches("native:[0-9]+")&&new BigInteger(value.substring(7)).compareTo(U64)<=0,"detachment opaque native identity invalid");return value;
    }
    private static boolean bool(JsonNode n,String key) { JsonNode v=field(n,key);need(v.isBoolean(),"detachment boolean required: "+key);return v.booleanValue(); }
    private static Boolean nullableBool(JsonNode n,String key) { return field(n,key).isNull()?null:bool(n,key); }
    private static BigInteger number(JsonNode v,long low,long high) { need(v.isIntegralNumber(),"exact detachment integer required");BigInteger value=v.bigIntegerValue();need(value.compareTo(BigInteger.valueOf(low))>=0&&value.compareTo(BigInteger.valueOf(high))<=0,"detachment integer width differs");return value; }
    private static Integer i32(JsonNode n,String key) { JsonNode v=field(n,key);return v.isNull()?null:number(v,Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact(); }
    private static int requiredI32(JsonNode n,String key) { return number(field(n,key),Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact(); }
    private static Long u32(JsonNode n,String key) { JsonNode v=field(n,key);return v.isNull()?null:number(v,0,4294967295L).longValueExact(); }
    private static long requiredU32(JsonNode n,String key) { return number(field(n,key),0,4294967295L).longValueExact(); }
    private static Integer u8(JsonNode n,String key) { JsonNode v=field(n,key);return v.isNull()?null:number(v,0,255).intValueExact(); }
    private static Long i64(JsonNode n,String key) { JsonNode v=field(n,key);return v.isNull()?null:number(v,Long.MIN_VALUE,Long.MAX_VALUE).longValueExact(); }
    private static void eq(JsonNode n,String key,String expected) { need(expected.equals(text(n,key,false,false)),"detachment source/stage differs: "+key); }
    private static void need(boolean condition,String message) { StrictJson.require(condition,message); }
}
