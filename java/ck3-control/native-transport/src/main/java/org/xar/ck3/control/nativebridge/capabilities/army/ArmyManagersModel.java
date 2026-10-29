package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Closed native manager operand domain. JSON exists only at the codec boundary. */
public final class ArmyManagersModel {
    private ArmyManagersModel() { }
    public enum Field {
        STATUS, READY, UNAVAILABLE_REASON, SCHEMA_VERSION, SOURCE, STAGE, PROJECTION_STAGE, CONTEXT_BASIS,
        NATIVE_INDEX, PHYSICAL_SLOT_I64, CONTROL_RAW_U8, STORED_HASH_RAW_U32, KEY_RAW_FULL_ID_U32,
        VECTOR_CAPACITY_RAW_I32, VECTOR_ALLOCATOR_IDENTITY, VECTOR_ALLOCATOR_MATCHES_EXPECTED, REFERENCES,
        ENTRIES_IDENTITY, ENTRIES_PRESENT, DATA_IS_NATIVE_EMPTY_BUFFER, MAP_COUNT_RAW_I32, MASK_RAW_I32,
        TAIL_RAW_U8, THRESHOLD_BITS_U32, PHYSICAL_CONTROL_EXTENT_LAST_SLOT_I64, PHYSICAL_CONTROLS_COMPLETE,
        REHASH_PREFIX_COMPLETE, REHASH_NONZERO_RECORDS_OBSERVED_I32, RECORDS, RAW_FULL_ID_U32,
        ARRG_RESOLUTION, CURRENT_38_RAW_I32, CONTRACT_ID_144_RAW_U32, CONTRACT_RESOLUTION,
        CONTRACT_FLAG_B9_RAW_U8, STATE_14C_RAW_I32, ORIGINAL_DATA_IDENTITY, ORIGINAL_DATA_PRESENT,
        FIRST_PERSISTENT_ID_RAW_U32, PERSISTENT_RESOLUTION, PERSISTENT_WAR_ID_13C_RAW_U32,
        WAR_RESOLUTION, WAR_MAGIC_0C_RAW_U32, APPEND_TO_PENDING, APPEND_FULL_ID_U32,
        TARGET_ARMY_FULL_ID_U32, HASH_RAW_U32, HOME_SLOT_I64, TERMINAL_PHYSICAL_SLOT_I64, PROBES,
        EXISTING_KEY, EXISTING_REFERENCES, INSERTION_TAIL_RAW_U8, INSERTION_THRESHOLD_BITS_U32,
        ORIGINAL_ARMY_RESOLUTION, COMBAT_ID_128_RAW_U32, COMBAT_RESOLUTION, COMBAT_MAGIC_0C_RAW_U32,
        ARMY_COUNTER_5C_RAW_I32, PENDING_MUTATOR_SELECTED, PENDING_SETUP, ORIGINAL_ARRG_REFERENCES,
        ARRG_OCCURRENCES, MANAGER_LOADED, MANAGER_IDENTITY, ORIGINAL_ROSTER, REMOVAL_QUEUE, OCCURRENCES,
        RAW_ROSTER_REFERENCES_READY, SOURCE_OPERANDS_READY, ACTUAL_PRE_DATE_CALLBACK_READY,
        ACTUAL_TOMORROW_ROSTER_READY, FULL_DAILY_ASSAULT_READY, FULL_MONTHLY_READY, PENDING_TABLE_FRAME_V1,
        COUNT_RAW_I32, ORDERED_IDS_U32, POINTER_IDENTITY, POINTER_PRESENT, DATE_LOW_RAW_I32,
        ORIGINAL_REQUEST_FULL_ID_U32, ARMY_RESOLUTION, COMBAT_REQUEST_FULL_ID_U32, ARMY_DATE_COUNT_5C_RAW_I32,
        DATE_ARRAY_IDENTITY, DATE_ARRAY_PRESENT, DATE_ENTRIES, DATE_SCAN_READY, CLOCK_SOURCE, CLOCK_READY,
        CURRENT_DATE_RAW_I32, TOMORROW_DATE_LOW_I32, SOURCE_C8, INITIAL_158, DEMANDED, OBSERVABLE, VERDICT,
        EARLIER_SKIP, EARLIER_SKIP_SOURCE, ARMY_CHARACTER_120_RAW_U32, CHARACTER_RESOLUTION,
        ARMY_UNIT_124_RAW_U32, UNIT_RESOLUTION, UNIT_OWNER_174_RAW_U32, CHARACTER_MAGIC_1C_RAW_U32,
        CHARACTER_FULL_ID_18_RAW_U32, CHARACTER_DEATH_1D0_PRESENT, CHARACTER_STATE_1C8_PRESENT,
        CHARACTER_STATE_1C0_PRESENT, CHARACTER_STATE_1B8_PRESENT, MEMBERSHIP, BASIC_RULE, AVAILABILITY,
        FAILURE_APPEND_ARMY_10_RAW_U32, INITIAL_80, MAGIC_14_RAW_U32, IDENTITY_VALID, VALUE_40_RAW_I64,
        NUMERIC_24_INPUTS_READY, NUMERIC_28_INPUTS_READY, ACTUAL_ARMY_24_RAW_I32, ACTUAL_ARMY_28_RAW_I64,
        ACTUAL_ARMY_20_RAW_U8, ACTUAL_ARMY_21_RAW_U8, ACTUAL_ARMY_30_RAW_U8, ACTUAL_ARMY_31_RAW_U8,
        ARRG_ROWS_READY, ORIGINAL_ARMY_SELECTIONS_READY, ACTUAL_REFRESH_EXECUTION_READY,
        ACTUAL_NEXT_OCCURRENCE_READY, FULL_CALLBACK_READY, REQUESTED_FULL_ID_U32, REGISTRY_LOADED,
        REGISTRY_CAPACITY_U32, REGISTRY_INDEX_U32, INDEXED_IDENTITY, INDEXED_FULL_ID_U32, SELECTION,
        USED_FALLBACK, OBJECT_IDENTITY, SELECTED_OBJECT_READY, SELECTED_FULL_ID_U32, SELECTED_FULL_ID_READ_READY,
        SAME_QUERY_ARMY_SELECTION_MATCHED, ARMY_1D4_RAW_U8, ARMY_124_RAW_U32, CONDITION_OWNER_IDENTITY,
        INLINE_CONDITION_IDENTITY, ROOT_KIND, ROOT_SUBTYPE, ROOT_PAYLOAD_U64, ROOT_CONSTRUCTION,
        NATIVE_CURRENT_CONDITION_PASSED, DERIVED_CURRENT_30_RAW_U8, CURRENT_CONDITION_30_INPUTS_READY,
        NATIVE_GETTER_RETURNED, NATIVE_GETTER_20_RAW_U8, DERIVED_CURRENT_20_RAW_U8, CURRENT_FLAG20_INPUTS_READY,
        ARMY_1EC_RAW_U8, ARMY_1F0_RAW_I64, OWNER_CHARACTER_CARRIER_1C0_PRESENT, OWNER_CHARACTER_CARRIER_IDENTITY,
        HEADER_SELECTION, HEADER_IDENTITY, HEADER_0C_RAW_I32, OWNER_HEADER_INPUTS_READY, NATIVE_SHARED_TAIL_RETURNED,
        NATIVE_SHARED_TAIL_21_RAW_U8, DERIVED_CURRENT_21_RAW_U8, CURRENT_FLAG21_INPUTS_READY,
        PURPOSE, PROVINCE_USED_FALLBACK, PROVINCE_IDENTITY, PROVINCE_MAGIC_85C_RAW_U32, UNIT_SELECTIONS,
        PROVINCE_TITLE_738_RAW_U32, TITLE_HOLDER_128_RAW_U32, TITLE_RESOLUTION, PARENT_TITLE_RESOLUTION,
        TITLE_DEFINITION_64_RAW_U32, PARENT_TITLE_E8_RAW_U32, PARENT_HOLDER_128_RAW_U32,
        HOLDER_REQUESTED_FULL_ID_U32, HOLDER_CHARACTER_FULL_ID_U32, HOLDER_CHARACTER_RESOLUTION,
        SELECTED_UNIT_OWNER_174_RAW_U32, HOLDER_OWNER_EQUAL, NATIVE_RELATION_DEMANDED, NATIVE_RELATION_RETURNED,
        NATIVE_HOLDER_OWNER_RELATION, DERIVED_CURRENT_SHARED_TAIL_RAW_U8, CURRENT_SHARED_TAIL_INPUTS_READY,
        CHANGED_SELECTION_CONTEXT_READY, CHANGED_RELATIONSHIP_CONTEXT_READY, ARMY_128_RAW_U32,
        SELECTED_COMBAT_MAGIC_0C_RAW_U32, SELECTED_COMBAT_FULL_ID_08_RAW_U32, SOURCE_ACTIVE_COMBAT,
        ACTIVE_COMBAT_INPUTS_READY, SELECTED_CHARACTER_18_RAW_U32, RULE_SELECTOR_I32, RULE_INLINE_OFFSET_U32,
        RULE_PROVIDER_IDENTITY, RULE_ARRAY_IDENTITY, INLINE_RULE_IDENTITY, NATIVE_RULE_EVALUATION_RETURNED,
        NATIVE_CURRENT_RULE24_PASSED, DERIVED_CURRENT_31_RAW_U8, CURRENT_FLAG31_INPUTS_READY, RULE24_SOURCE_PINS_V1,
        PINS_CAPTURED_READY, PROVIDER_ARRAY_BORROWED, RULE_RECEIVER_IDENTITY, RULE_VTABLE_IDENTITY,
        CONDITION_MODE_RAW_U8, EXPECTED_SCOPE_FUNCTION_IDENTITY, EXPECTED_SCOPE_FUNCTION_RVA,
        SCOPE_MASK_FUNCTION_IDENTITY, SCOPE_MASK_FUNCTION_RVA, RULE_EVALUATOR_FUNCTION_IDENTITY,
        RULE_EVALUATOR_FUNCTION_RVA, VTABLE_READ_READY, MODE_READ_READY, EXPECTED_SCOPE_PIN_READ_READY,
        SCOPE_MASK_PIN_READ_READY, RULE_EVALUATOR_PIN_READ_READY, PIN_REQUESTED_BYTES_U32, PIN_CAPTURED_BYTES_U32,
        NATIVE_CALLS_EXECUTED, NATIVE_WRITES_EXECUTED, REFERENCES_READY, DATA_IDENTITY, DATA_PRESENT,
        OBSERVED_OCCURRENCE_COUNT, DISTANCE_RAW_U8;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
        static Field fromWire(String wire) {
            Field result;
            try { result = valueOf(wire.toUpperCase(Locale.ROOT)); }
            catch (IllegalArgumentException invalid) { throw new IllegalArgumentException("unknown manager field: " + wire, invalid); }
            require(result.wire().equals(wire), "noncanonical manager field"); return result;
        }
    }
    public enum Width {
        U8(8,false), U32(32,false), I32(32,true), I64(64,true), U64(64,false);
        private final int bits; private final boolean signed;
        Width(int bits,boolean signed) { this.bits=bits; this.signed=signed; }
        public boolean wide() { return bits==64; }
        void check(BigInteger value) {
            BigInteger min=signed?BigInteger.ONE.shiftLeft(bits-1).negate():BigInteger.ZERO;
            BigInteger max=BigInteger.ONE.shiftLeft(signed?bits-1:bits).subtract(BigInteger.ONE);
            require(value.compareTo(min)>=0&&value.compareTo(max)<=0,"manager native integer width");
        }
    }
    public sealed interface Value permits Nil,Flag,Text,Number,Sequence,Document { }
    public enum Nil implements Value { INSTANCE }
    public record Flag(boolean value) implements Value { }
    public record Text(String value) implements Value { public Text { Objects.requireNonNull(value); } }
    public record Number(BigInteger value,Width width) implements Value {
        public Number { Objects.requireNonNull(value); Objects.requireNonNull(width); width.check(value); }
    }
    public record Sequence(List<Value> values) implements Value { public Sequence { values=List.copyOf(values); } }
    public record Document(Shape shape,Map<Field,Value> fields) implements Value {
        public Document {
            Objects.requireNonNull(shape); EnumMap<Field,Value> copy=new EnumMap<>(Field.class); copy.putAll(fields);
            require(copy.keySet().containsAll(shape.required())&&shape.allowed().containsAll(copy.keySet()),"manager closed shape: "+shape);
            copy.forEach((field,value)->{checkValue(Objects.requireNonNull(value),shape.types.get(field));if(value instanceof Text text&&field!=Field.UNAVAILABLE_REASON)require(!text.value().isEmpty(),"manager nonempty typed text");});
            if(shape.allowed().contains(Field.STATUS))availabilityFields(copy,shape==Shape.PINS?Field.PINS_CAPTURED_READY:Field.READY,"typed "+shape);
            fields=Collections.unmodifiableMap(copy);
        }
        public Value get(Field field) { Value value=fields.get(field); require(value!=null,"manager missing required typed field: "+field); return value; }
        public boolean has(Field field) { return fields.containsKey(field); }
        public boolean nil(Field field) { return get(field)==Nil.INSTANCE; }
        public Boolean bool(Field field) { Value value=get(field); return value==Nil.INSTANCE?null:((Flag)value).value(); }
        public boolean yes(Field field) { return Boolean.TRUE.equals(bool(field)); }
        public String text(Field field) { Value value=get(field); return value==Nil.INSTANCE?null:((Text)value).value(); }
        public BigInteger integer(Field field) { Value value=get(field); return value==Nil.INSTANCE?null:((Number)value).value(); }
        public Integer i32(Field field) { BigInteger value=integer(field); return value==null?null:value.intValueExact(); }
        public Long i64(Field field) { BigInteger value=integer(field); return value==null?null:value.longValueExact(); }
        public Document object(Field field) { Value value=get(field); return value==Nil.INSTANCE?null:(Document)value; }
        public List<Value> values(Field field) { Value value=get(field); return value==Nil.INSTANCE?null:((Sequence)value).values(); }
        public List<Document> rows(Field field) { return values(field).stream().map(Document.class::cast).toList(); }
        public List<BigInteger> integers(Field field) { List<Value> value=values(field);return value==null?null:value.stream().map(item->item==Nil.INSTANCE?null:((Number)item).value()).toList(); }
    }
    private static final String STATE="status:string ready:bool unavailable_reason:string";
    private static final String SELECT="registry_loaded:bool? used_fallback:bool? requested_full_id_u32:u32? registry_capacity_u32:u32? registry_index_u32:u32? indexed_full_id_u32:u32? indexed_identity:identity? selection:string? object_identity:identity? selected_object_ready:bool";
    private static final String COMMON="manager_loaded:bool? manager_identity:identity? original_roster:REFERENCES raw_roster_references_ready:bool original_army_selections_ready:bool";
    private static final String FALSE="actual_refresh_execution_ready:bool=false actual_next_occurrence_ready:bool=false full_callback_ready:bool=false full_daily_assault_ready:bool=false full_monthly_ready:bool=false";
    private static final String ROW="native_index:i32 raw_full_id_u32:u32? original_army_resolution:RESOLUTION same_query_army_selection_matched:bool";
    public enum Shape {
        RESOLUTION(STATE+" "+SELECT+" selected_full_id_u32:u32? selected_full_id_read_ready:bool?"),
        REFERENCE(STATE+" native_index:i32 raw_full_id_u32:u32?"),
        REFERENCES(STATE+" references_ready:bool count_raw_i32:i32? data_identity:identity? data_present:bool? occurrences:REFERENCE[] observed_occurrence_count:i32"),
        PROBE("native_index:i32 physical_slot_i64:i64 distance_raw_u8:u8 control_raw_u8:u8? key_raw_full_id_u32:u32?"),
        PENDING_PHYSICAL(STATE+" native_index:i32 physical_slot_i64:i64 control_raw_u8:u8? stored_hash_raw_u32:u32? key_raw_full_id_u32:u32? vector_capacity_raw_i32:i32? vector_allocator_identity:identity? vector_allocator_matches_expected:bool? references:REFERENCES"),
        PENDING_FRAME(STATE+" schema_version:i32=1 entries_identity:identity? entries_present:bool? data_is_native_empty_buffer:bool? map_count_raw_i32:i32? mask_raw_i32:i32? tail_raw_u8:u8? threshold_bits_u32:u32? physical_control_extent_last_slot_i64:i64? physical_controls_complete:bool rehash_prefix_complete:bool rehash_nonzero_records_observed_i32:i32? records:PENDING_PHYSICAL[]"),
        PENDING_ARRG(STATE+" native_index:i32 raw_full_id_u32:u32? arrg_resolution:RESOLUTION current_38_raw_i32:i32? contract_id_144_raw_u32:u32? contract_resolution:RESOLUTION contract_flag_b9_raw_u8:u8? state_14c_raw_i32:i32? original_data_identity:identity? original_data_present:bool? first_persistent_id_raw_u32:u32? persistent_resolution:RESOLUTION persistent_war_id_13c_raw_u32:u32? war_resolution:RESOLUTION war_magic_0c_raw_u32:u32? append_to_pending:bool? append_full_id_u32:u32?"),
        PENDING_SETUP(STATE+" entries_identity:identity? entries_present:bool? mask_raw_i32:i32? target_army_full_id_u32:u32? hash_raw_u32:u32? home_slot_i64:i64? terminal_physical_slot_i64:i64? probes:PROBE[] existing_key:bool? existing_references:REFERENCES map_count_raw_i32:i32? insertion_tail_raw_u8:u8? insertion_threshold_bits_u32:u32?"),
        PENDING_ROW(STATE+" native_index:i32 raw_full_id_u32:u32? original_army_resolution:RESOLUTION combat_id_128_raw_u32:u32? combat_resolution:RESOLUTION combat_magic_0c_raw_u32:u32? army_counter_5c_raw_i32:i32? pending_mutator_selected:bool? pending_setup:PENDING_SETUP original_arrg_references:REFERENCES arrg_occurrences:PENDING_ARRG[]"),
        PENDING(STATE+" schema_version:i32=1 source:string=native_current_pre_date_pending_update_inputs stage:string=observed_current_pre_date_pending_update_inputs manager_loaded:bool? manager_identity:identity? original_roster:REFERENCES removal_queue:REFERENCES occurrences:PENDING_ROW[] raw_roster_references_ready:bool source_operands_ready:bool actual_pre_date_callback_ready:bool=false actual_tomorrow_roster_ready:bool=false full_daily_assault_ready:bool=false full_monthly_ready:bool=false pending_table_frame_v1:PENDING_FRAME?"),
        ID_LIST("ready:bool unavailable_reason:string source:string count_raw_i32:i32? ordered_ids_u32:u32?[]?"),
        DATE("native_index:i32 pointer_identity:string? pointer_present:bool? date_low_raw_i32:i32?"),
        DATED_ROW(STATE+" native_index:i32 original_request_full_id_u32:u32? army_resolution:RESOLUTION combat_request_full_id_u32:u32? combat_resolution:RESOLUTION combat_magic_0c_raw_u32:u32? army_date_count_5c_raw_i32:i32? date_array_identity:string? date_array_present:bool? date_entries:DATE[] date_scan_ready:bool"),
        DATED(STATE+" schema_version:i32=1 source:string=native_current_pre_date_dated_append_inputs stage:string=observed_current_2a9a360_tomorrow_operands manager_loaded:bool manager_identity:string? clock_source:string clock_ready:bool current_date_raw_i32:i32? tomorrow_date_low_i32:i32? source_c8:ID_LIST initial_158:ID_LIST occurrences:DATED_ROW[]"),
        PREDICATE("demanded:bool observable:bool verdict:bool? unavailable_reason:string"),
        CHARACTER_ROW(STATE+" native_index:i32 original_request_full_id_u32:u32? army_resolution:RESOLUTION earlier_skip:bool? earlier_skip_source:string army_character_120_raw_u32:u32? character_resolution:RESOLUTION army_unit_124_raw_u32:u32? unit_resolution:RESOLUTION unit_owner_174_raw_u32:u32? character_magic_1c_raw_u32:u32? character_full_id_18_raw_u32:u32? character_death_1d0_present:bool? character_state_1c8_present:bool? character_state_1c0_present:bool? character_state_1b8_present:bool? membership:PREDICATE basic_rule:PREDICATE availability:PREDICATE failure_append_army_10_raw_u32:u32?"),
        CHARACTER(STATE+" schema_version:i32=1 source:string=native_current_pre_date_character_prefix_inputs stage:string=observed_current_conditional_2a99f72_character_prefix manager_loaded:bool manager_identity:identity? original_roster:REFERENCES initial_80:ID_LIST occurrences:CHARACTER_ROW[]"),
        REFRESH_ARRG(STATE+" native_index:i32 raw_full_id_u32:u32? arrg_resolution:RESOLUTION magic_14_raw_u32:u32? identity_valid:bool? current_38_raw_i32:i32? value_40_raw_i64:i64? numeric_24_inputs_ready:bool numeric_28_inputs_ready:bool"),
        REFRESH_ROW(STATE+" native_index:i32 raw_full_id_u32:u32? original_army_resolution:RESOLUTION original_arrg_references:REFERENCES arrg_occurrences:REFRESH_ARRG[] actual_army_24_raw_i32:i32? actual_army_28_raw_i64:i64? actual_army_20_raw_u8:u8? actual_army_21_raw_u8:u8? actual_army_30_raw_u8:u8? actual_army_31_raw_u8:u8? arrg_rows_ready:bool numeric_24_inputs_ready:bool numeric_28_inputs_ready:bool"),
        REFRESH(STATE+" schema_version:i32=1 source:string=native_current_post_admission_refresh_inputs stage:string=observed_current_post_admission_refresh_inputs projection_stage:string=post24df4c3_pre24df4c7 "+COMMON+" occurrences:REFRESH_ROW[] numeric_24_inputs_ready:bool numeric_28_inputs_ready:bool source_operands_ready:bool "+FALSE),
        SELECTION(STATE+" "+SELECT),
        HOLDER_SELECTION(STATE+" "+SELECT.replace("selection:string?","selection:string")),
        CONDITION_ROW(STATE+" "+ROW+" actual_army_30_raw_u8:u8? army_1d4_raw_u8:u8? army_124_raw_u32:u32? unit_owner_174_raw_u32:u32? unit_resolution:SELECTION condition_owner_identity:identity? inline_condition_identity:identity? root_kind:u32? root_subtype:u32? root_payload_u64:u64? root_construction:string? native_current_condition_passed:bool? derived_current_30_raw_u8:u8? current_condition_30_inputs_ready:bool"),
        CONDITION(STATE+" schema_version:i32=1 source:string=native_current_army_condition30_inputs stage:string=observed_current_army_condition30_inputs "+COMMON+" occurrences:CONDITION_ROW[] current_condition_30_inputs_ready:bool "+FALSE),
        FLAG20_ROW(STATE+" "+ROW+" actual_army_20_raw_u8:u8? army_1d4_raw_u8:u8? native_getter_returned:bool native_getter_20_raw_u8:u8? derived_current_20_raw_u8:u8? current_flag20_inputs_ready:bool"),
        FLAG20(STATE+" schema_version:i32=1 source:string=native_current_army_flag20_inputs stage:string=observed_current_army_flag20_inputs "+COMMON+" occurrences:FLAG20_ROW[] current_flag20_inputs_ready:bool "+FALSE),
        FLAG21_ROW(STATE+" "+ROW+" actual_army_21_raw_u8:u8? army_1ec_raw_u8:u8? army_1f0_raw_i64:i64? army_124_raw_u32:u32? unit_resolution:SELECTION unit_owner_174_raw_u32:u32? character_resolution:SELECTION owner_character_carrier_1c0_present:bool? owner_character_carrier_identity:identity? header_selection:string? header_identity:identity? header_0c_raw_i32:i32? owner_header_inputs_ready:bool native_shared_tail_returned:bool native_shared_tail_21_raw_u8:u8? derived_current_21_raw_u8:u8? current_flag21_inputs_ready:bool"),
        FLAG21(STATE+" schema_version:i32=1 source:string=native_current_army_flag21_inputs stage:string=observed_current_army_flag21_inputs "+COMMON+" occurrences:FLAG21_ROW[] current_flag21_inputs_ready:bool "+FALSE),
        HOLDER_UNIT("native_index:i32 purpose:string army_124_raw_u32:u32? unit_resolution:HOLDER_SELECTION province_used_fallback:bool? province_identity:identity? province_magic_85c_raw_u32:u32?"),
        HOLDER_ROW(STATE+" "+ROW+" unit_selections:HOLDER_UNIT[] province_title_738_raw_u32:u32? title_holder_128_raw_u32:u32? title_resolution:HOLDER_SELECTION parent_title_resolution:HOLDER_SELECTION title_definition_64_raw_u32:u32? parent_title_e8_raw_u32:u32? parent_holder_128_raw_u32:u32? holder_requested_full_id_u32:u32? holder_character_full_id_u32:u32? holder_character_resolution:HOLDER_SELECTION selected_unit_owner_174_raw_u32:u32? holder_owner_equal:bool? native_relation_demanded:bool native_relation_returned:bool native_holder_owner_relation:bool? derived_current_shared_tail_raw_u8:u8? current_shared_tail_inputs_ready:bool"),
        HOLDER(STATE+" schema_version:i32=1 source:string=native_selected_title_holder_owner_relation_28b2820 stage:string=observed_current_selected_title_holder_owner_relation_inputs context_basis:string=same_query_selected_title_holder_and_unit_owner "+COMMON+" occurrences:HOLDER_ROW[] current_shared_tail_inputs_ready:bool changed_selection_context_ready:bool=false changed_relationship_context_ready:bool=false "+FALSE),
        FLAG31_ROW(STATE+" "+ROW+" actual_army_31_raw_u8:u8? army_1d4_raw_u8:u8? army_128_raw_u32:u32? combat_resolution:SELECTION selected_combat_magic_0c_raw_u32:u32? selected_combat_full_id_08_raw_u32:u32? source_active_combat:bool? active_combat_inputs_ready:bool army_124_raw_u32:u32? unit_owner_174_raw_u32:u32? unit_resolution:SELECTION character_resolution:SELECTION selected_character_18_raw_u32:u32? rule_selector_i32:i32=24 rule_inline_offset_u32:u32=4992 rule_provider_identity:identity? rule_array_identity:identity? inline_rule_identity:identity? root_kind:i32? root_subtype:i32? root_payload_u64:u64? root_construction:string native_rule_evaluation_returned:bool native_current_rule24_passed:bool? derived_current_31_raw_u8:u8? current_flag31_inputs_ready:bool @rule24_source_pins_v1:PINS"),
        FLAG31(STATE+" schema_version:i32=1 source:string=native_current_army_flag31_inputs stage:string=observed_current_army_flag31_inputs "+COMMON+" occurrences:FLAG31_ROW[] current_flag31_inputs_ready:bool "+FALSE),
        PINS("status:string unavailable_reason:string schema_version:i32=1 source:string=native_current_rule24_source_pins pins_captured_ready:bool provider_array_borrowed:bool=true rule_receiver_identity:identity rule_vtable_identity:identity? condition_mode_raw_u8:u8? expected_scope_function_identity:identity? expected_scope_function_rva:u32? scope_mask_function_identity:identity? scope_mask_function_rva:u32? rule_evaluator_function_identity:identity? rule_evaluator_function_rva:u32? vtable_read_ready:bool mode_read_ready:bool expected_scope_pin_read_ready:bool scope_mask_pin_read_ready:bool rule_evaluator_pin_read_ready:bool pin_requested_bytes_u32:u32 pin_captured_bytes_u32:u32 native_calls_executed:u32=0 native_writes_executed:u32=0");
        private final Map<Field,String> types; private final Set<Field> required;
        Shape(String schema) {
            EnumMap<Field,String> parsed=new EnumMap<>(Field.class); EnumSet<Field> requiredFields=EnumSet.noneOf(Field.class);
            for(String token:schema.split(" ")) { boolean optional=token.startsWith("@"); String[] pair=(optional?token.substring(1):token).split(":",2); Field field=Field.fromWire(pair[0]); require(parsed.put(field,pair[1])==null,"duplicate manager schema field"); if(!optional)requiredFields.add(field); }
            types=Collections.unmodifiableMap(parsed); required=Collections.unmodifiableSet(requiredFields);
        }
        public Set<Field> required() { return required; }
        public Set<Field> allowed() { return types.keySet(); }
    }
    public enum Kind {
        PENDING(Shape.PENDING), DATED(Shape.DATED), CHARACTER(Shape.CHARACTER), REFRESH(Shape.REFRESH),
        CONDITION30(Shape.CONDITION), FLAG20(Shape.FLAG20), FLAG21(Shape.FLAG21), HOLDER_RELATION(Shape.HOLDER), FLAG31(Shape.FLAG31);
        private final Shape shape; Kind(Shape shape){this.shape=shape;} public Shape shape(){return shape;}
    }
    public record Inputs(Kind kind,Document value) {
        public Inputs { Objects.requireNonNull(kind);Objects.requireNonNull(value);require(value.shape()==kind.shape(),"manager family/shape mismatch"); }
    }
    public static Document decodeShape(JsonNode raw,Shape shape,String path) {
        require(raw!=null&&raw.isObject(),path+" must be object"); EnumMap<Field,Value> fields=new EnumMap<>(Field.class);
        // Shared roster contract owns native shape/status checks; this conversion only changes representation.
        switch(shape) {
            case RESOLUTION -> ArmyStrengthsRosterContract.decodeOperandResolution(raw,path);
            case REFERENCES -> ArmyStrengthsRosterContract.decodeRawReferences(raw,path);
            case PROBE -> ArmyStrengthsRosterContract.decodePendingProbe(raw,path);
            default -> { }
        }
        raw.properties().forEach(entry->{Field field=Field.fromWire(entry.getKey());String type=shape.types.get(field);require(type!=null,path+" unknown field: "+field);fields.put(field,decode(entry.getValue(),type,path+"."+entry.getKey()));});
        Document result=new Document(shape,fields);
        if(shape!=Shape.DATED&&shape!=Shape.DATED_ROW&&shape!=Shape.CHARACTER&&shape!=Shape.CHARACTER_ROW&&shape!=Shape.PINS&&shape.allowed().contains(Field.STATUS)) availability(result,Field.READY,path);
        return result;
    }
    private static void checkValue(Value value,String type) {
        if(type.endsWith("?")){if(value==Nil.INSTANCE)return;checkValue(value,type.substring(0,type.length()-1));return;}
        require(value!=Nil.INSTANCE,"nonnullable typed manager value");
        if(type.endsWith("[]")){require(value instanceof Sequence,"manager typed array");((Sequence)value).values().forEach(item->checkValue(item,type.substring(0,type.length()-2)));return;}
        int literal=type.indexOf('=');if(literal>=0){String base=type.substring(0,literal),expected=type.substring(literal+1);checkValue(value,base);require(base.equals("bool")?((Flag)value).value()==Boolean.parseBoolean(expected):base.equals("string")?((Text)value).value().equals(expected):((Number)value).value().equals(new BigInteger(expected)),"manager typed literal");return;}
        if(type.equals("bool")){require(value instanceof Flag,"manager typed bool");return;}
        if(type.equals("string")||type.equals("identity")){require(value instanceof Text,"manager typed text");return;}
        if(type.matches("[iu](8|32|64)")){require(value instanceof Number&&((Number)value).width()==Width.valueOf(type.toUpperCase(Locale.ROOT)),"manager typed integer width");return;}
        require(value instanceof Document&&((Document)value).shape()==Shape.valueOf(type),"manager typed child shape");
    }
    private static Value decode(JsonNode raw,String type,String path) {
        if(type.endsWith("?")) { if(raw.isNull())return Nil.INSTANCE;return decode(raw,type.substring(0,type.length()-1),path); }
        require(!raw.isNull(),path+" must not be null");
        if(type.endsWith("[]")) { require(raw.isArray(),path+" must retain native array");List<Value> values=new ArrayList<>();for(JsonNode item:raw)values.add(decode(item,type.substring(0,type.length()-2),path));return new Sequence(values); }
        int literal=type.indexOf('=');if(literal>=0){String base=type.substring(0,literal),expected=type.substring(literal+1);Value result=decode(raw,base,path);require(base.equals("bool")?((Flag)result).value()==Boolean.parseBoolean(expected):base.equals("string")?((Text)result).value().equals(expected):((Number)result).value().equals(new BigInteger(expected)),path+" exact source literal");return result;}
        if(type.equals("bool")){require(raw.isBoolean(),path+" boolean");return new Flag(raw.booleanValue());}
        if(type.equals("string")||type.equals("identity")){require(raw.isTextual()&&(path.endsWith(".unavailable_reason")||!raw.textValue().isEmpty()),path+" nonempty text");return new Text(raw.textValue());}
        if(type.matches("[iu](8|32|64)")){require(raw.isIntegralNumber(),path+" exact native integer");Width width=Width.valueOf(type.toUpperCase(Locale.ROOT));return new Number(raw.bigIntegerValue(),width);}
        return decodeShape(raw,Shape.valueOf(type),path);
    }
    public static void availability(Document value,Field readyField,String path) {
        availabilityFields(value.fields(),readyField,path);
    }
    private static void availabilityFields(Map<Field,Value> fields,Field readyField,String path){String status=((Text)fields.get(Field.STATUS)).value();boolean ready=((Flag)fields.get(readyField)).value();String reason=((Text)fields.get(Field.UNAVAILABLE_REASON)).value();require(Set.of("available","partial","unavailable").contains(status)&&ready==status.equals("available")&&ready==reason.isEmpty(),path+" status/readiness/reason");}
    public static JsonNode encode(Value value,boolean publicV2) {
        if(value==Nil.INSTANCE)return JsonNodeFactory.instance.nullNode();if(value instanceof Flag v)return JsonNodeFactory.instance.booleanNode(v.value());if(value instanceof Text v)return JsonNodeFactory.instance.textNode(v.value());
        if(value instanceof Number v)return publicV2&&v.width().wide()?JsonNodeFactory.instance.textNode(v.value().toString()):JsonNodeFactory.instance.numberNode(v.value());
        if(value instanceof Sequence v){ArrayNode result=JsonNodeFactory.instance.arrayNode();v.values().forEach(item->result.add(encode(item,publicV2)));return result;}
        Document document=(Document)value;ObjectNode result=JsonNodeFactory.instance.objectNode();document.fields().forEach((field,item)->result.set(field.wire(),encode(item,publicV2)));return result;
    }
    static void require(boolean condition,String message){if(!condition)throw new IllegalArgumentException(message);}
}
