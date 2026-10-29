package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.*;
import java.math.BigInteger;
import java.util.*;
import java.util.function.Function;

/** The exact original standalone 2A99B40 observation contract and pure, source-bound admission derivation.
 * JSON is confined to strict decode/encode boundaries. No operation invokes native code or mutates a roster. */
public final class ArmyStrengthsRosterContract {
    private ArmyStrengthsRosterContract() { }
    public enum Status {
        AVAILABLE("available"), PARTIAL("partial"), UNAVAILABLE("unavailable");
        private final String wire;
        Status(String wire) { this.wire=wire; }
        public String wire() { return wire; }
        static Status parse(String wire) {
            for (Status value:values()) if(value.wire.equals(wire)) return value;
            throw bad("status", "unknown availability");
        }
    }
    public interface Indexed { int native_index(); }
    public record OperandResolution(Status status,
            boolean ready,
            String unavailable_reason,
            Long requested_full_id_u32,
            Boolean registry_loaded,
            Long registry_capacity_u32,
            Long registry_index_u32,
            String indexed_identity,
            Long indexed_full_id_u32,
            String selection,
            Boolean used_fallback,
            String object_identity,
            Long selected_full_id_u32,
            boolean selected_object_ready,
            Boolean selected_full_id_read_ready) {
        public OperandResolution {
            Objects.requireNonNull(status);
            Objects.requireNonNull(unavailable_reason);
            require(requested_full_id_u32==null || (requested_full_id_u32>=0 && requested_full_id_u32<=0xFFFFFFFFL), "requested_full_id_u32 u32 required");
            require(registry_capacity_u32==null || (registry_capacity_u32>=0 && registry_capacity_u32<=0xFFFFFFFFL), "registry_capacity_u32 u32 required");
            require(registry_index_u32==null || (registry_index_u32>=0 && registry_index_u32<=0xFFFFFFFFL), "registry_index_u32 u32 required");
            require(indexed_identity==null || !indexed_identity.isEmpty(), "indexed_identity nonempty text required");
            require(indexed_full_id_u32==null || (indexed_full_id_u32>=0 && indexed_full_id_u32<=0xFFFFFFFFL), "indexed_full_id_u32 u32 required");
            require(selection==null || !selection.isEmpty(), "selection nonempty text required");
            require(object_identity==null || !object_identity.isEmpty(), "object_identity nonempty text required");
            require(selected_full_id_u32==null || (selected_full_id_u32>=0 && selected_full_id_u32<=0xFFFFFFFFL), "selected_full_id_u32 u32 required");
            require(ready==(status==Status.AVAILABLE) && ready==unavailable_reason.isEmpty(), "availability, readiness and reason disagree");
        }
    }
    public record RawReferenceOccurrence(Status status,
            boolean ready,
            String unavailable_reason,
            int native_index,
            Long raw_full_id_u32) implements Indexed {
        public RawReferenceOccurrence {
            Objects.requireNonNull(status);
            Objects.requireNonNull(unavailable_reason);
            require(raw_full_id_u32==null || (raw_full_id_u32>=0 && raw_full_id_u32<=0xFFFFFFFFL), "raw_full_id_u32 u32 required");
            require(ready==(status==Status.AVAILABLE) && ready==unavailable_reason.isEmpty(), "availability, readiness and reason disagree");
        }
    }
    public record RawReferences(Status status,
            boolean ready,
            String unavailable_reason,
            boolean references_ready,
            Integer count_raw_i32,
            String data_identity,
            Boolean data_present,
            List<RawReferenceOccurrence> occurrences,
            int observed_occurrence_count) {
        public RawReferences {
            Objects.requireNonNull(status);
            Objects.requireNonNull(unavailable_reason);
            require(data_identity==null || !data_identity.isEmpty(), "data_identity nonempty text required");
            occurrences=List.copyOf(occurrences);
            require(ready==(status==Status.AVAILABLE) && ready==unavailable_reason.isEmpty(), "availability, readiness and reason disagree");
        }
    }
    public record RelationProbe(int native_index,
            String kind,
            long slot_index_i64,
            Long key_character_id_raw_u32) implements Indexed {
        public RelationProbe {
            require(kind!=null && !kind.isEmpty(), "kind nonempty text required");
            require(key_character_id_raw_u32==null || (key_character_id_raw_u32>=0 && key_character_id_raw_u32<=0xFFFFFFFFL), "key_character_id_raw_u32 u32 required");
        }
    }
    public record RelationLookup(Status status,
            boolean ready,
            String unavailable_reason,
            String component_identity,
            Boolean component_present,
            String table_data_identity,
            Boolean table_data_present,
            Integer table_count_raw_i32,
            Long target_character_full_id_raw_u32,
            List<RelationProbe> probes,
            Long candidate_slot_index_i64,
            String selection,
            String default_relationship_identity,
            Boolean default_relationship_present,
            String selected_relationship_identity,
            Boolean selected_relationship_present,
            Long selected_relationship_war_id_raw_u32) {
        public RelationLookup {
            Objects.requireNonNull(status);
            Objects.requireNonNull(unavailable_reason);
            require(component_identity==null || !component_identity.isEmpty(), "component_identity nonempty text required");
            require(table_data_identity==null || !table_data_identity.isEmpty(), "table_data_identity nonempty text required");
            require(target_character_full_id_raw_u32==null || (target_character_full_id_raw_u32>=0 && target_character_full_id_raw_u32<=0xFFFFFFFFL), "target_character_full_id_raw_u32 u32 required");
            probes=List.copyOf(probes);
            require(selection==null || !selection.isEmpty(), "selection nonempty text required");
            require(default_relationship_identity==null || !default_relationship_identity.isEmpty(), "default_relationship_identity nonempty text required");
            require(selected_relationship_identity==null || !selected_relationship_identity.isEmpty(), "selected_relationship_identity nonempty text required");
            require(selected_relationship_war_id_raw_u32==null || (selected_relationship_war_id_raw_u32>=0 && selected_relationship_war_id_raw_u32<=0xFFFFFFFFL), "selected_relationship_war_id_raw_u32 u32 required");
            require(ready==(status==Status.AVAILABLE) && ready==unavailable_reason.isEmpty(), "availability, readiness and reason disagree");
        }
    }
    public record AdmissionGate(Status status,
            boolean ready,
            String unavailable_reason,
            Boolean verdict,
            Long original_army_unit_id_raw_u32,
            OperandResolution original_unit_resolution,
            Long original_unit_kind_raw_u32,
            String original_unit_province_identity,
            Boolean original_unit_province_present,
            Long original_province_identity_raw_u32,
            String selected_province_comparison_identity,
            Long selected_province_comparison_identity_raw_u32,
            Integer original_unit_counter_170_raw_i32,
            Long associated_army_id_raw_u32,
            OperandResolution associated_army_resolution,
            Long province_siege_id_raw_u32,
            Integer province_counter_850_raw_i32,
            Integer associated_army_flag_1d4_raw_u8,
            Integer associated_army_flag_1ec_raw_u8,
            Long associated_army_unit_id_raw_u32,
            OperandResolution associated_unit_resolution,
            Long associated_unit_character_id_raw_u32,
            OperandResolution associated_character_resolution,
            Long province_character_id_73c_raw_u32,
            String native_2c099f0_character_identity,
            String native_2c099f0_province_identity,
            Boolean native_2c099f0_third_argument_is_null,
            boolean native_2c099f0_returned,
            Integer native_2c099f0_classification_raw_i32,
            OperandResolution province_character_resolution,
            Long associated_character_full_id_raw_u32,
            Long province_character_full_id_raw_u32,
            RelationLookup relation_lookup,
            OperandResolution selected_war_resolution,
            Integer selected_war_ended_358_raw_u8) {
        public AdmissionGate {
            Objects.requireNonNull(status);
            Objects.requireNonNull(unavailable_reason);
            require(original_army_unit_id_raw_u32==null || (original_army_unit_id_raw_u32>=0 && original_army_unit_id_raw_u32<=0xFFFFFFFFL), "original_army_unit_id_raw_u32 u32 required");
            Objects.requireNonNull(original_unit_resolution);
            require(original_unit_kind_raw_u32==null || (original_unit_kind_raw_u32>=0 && original_unit_kind_raw_u32<=0xFFFFFFFFL), "original_unit_kind_raw_u32 u32 required");
            require(original_unit_province_identity==null || !original_unit_province_identity.isEmpty(), "original_unit_province_identity nonempty text required");
            require(original_province_identity_raw_u32==null || (original_province_identity_raw_u32>=0 && original_province_identity_raw_u32<=0xFFFFFFFFL), "original_province_identity_raw_u32 u32 required");
            require(selected_province_comparison_identity==null || !selected_province_comparison_identity.isEmpty(), "selected_province_comparison_identity nonempty text required");
            require(selected_province_comparison_identity_raw_u32==null || (selected_province_comparison_identity_raw_u32>=0 && selected_province_comparison_identity_raw_u32<=0xFFFFFFFFL), "selected_province_comparison_identity_raw_u32 u32 required");
            require(associated_army_id_raw_u32==null || (associated_army_id_raw_u32>=0 && associated_army_id_raw_u32<=0xFFFFFFFFL), "associated_army_id_raw_u32 u32 required");
            Objects.requireNonNull(associated_army_resolution);
            require(province_siege_id_raw_u32==null || (province_siege_id_raw_u32>=0 && province_siege_id_raw_u32<=0xFFFFFFFFL), "province_siege_id_raw_u32 u32 required");
            require(associated_army_flag_1d4_raw_u8==null || (associated_army_flag_1d4_raw_u8>=0 && associated_army_flag_1d4_raw_u8<=255), "associated_army_flag_1d4_raw_u8 u8 required");
            require(associated_army_flag_1ec_raw_u8==null || (associated_army_flag_1ec_raw_u8>=0 && associated_army_flag_1ec_raw_u8<=255), "associated_army_flag_1ec_raw_u8 u8 required");
            require(associated_army_unit_id_raw_u32==null || (associated_army_unit_id_raw_u32>=0 && associated_army_unit_id_raw_u32<=0xFFFFFFFFL), "associated_army_unit_id_raw_u32 u32 required");
            Objects.requireNonNull(associated_unit_resolution);
            require(associated_unit_character_id_raw_u32==null || (associated_unit_character_id_raw_u32>=0 && associated_unit_character_id_raw_u32<=0xFFFFFFFFL), "associated_unit_character_id_raw_u32 u32 required");
            Objects.requireNonNull(associated_character_resolution);
            require(province_character_id_73c_raw_u32==null || (province_character_id_73c_raw_u32>=0 && province_character_id_73c_raw_u32<=0xFFFFFFFFL), "province_character_id_73c_raw_u32 u32 required");
            require(native_2c099f0_character_identity==null || !native_2c099f0_character_identity.isEmpty(), "native_2c099f0_character_identity nonempty text required");
            require(native_2c099f0_province_identity==null || !native_2c099f0_province_identity.isEmpty(), "native_2c099f0_province_identity nonempty text required");
            Objects.requireNonNull(province_character_resolution);
            require(associated_character_full_id_raw_u32==null || (associated_character_full_id_raw_u32>=0 && associated_character_full_id_raw_u32<=0xFFFFFFFFL), "associated_character_full_id_raw_u32 u32 required");
            require(province_character_full_id_raw_u32==null || (province_character_full_id_raw_u32>=0 && province_character_full_id_raw_u32<=0xFFFFFFFFL), "province_character_full_id_raw_u32 u32 required");
            Objects.requireNonNull(relation_lookup);
            Objects.requireNonNull(selected_war_resolution);
            require(selected_war_ended_358_raw_u8==null || (selected_war_ended_358_raw_u8>=0 && selected_war_ended_358_raw_u8<=255), "selected_war_ended_358_raw_u8 u8 required");
            require(ready==(status==Status.AVAILABLE) && ready==unavailable_reason.isEmpty(), "availability, readiness and reason disagree");
        }
    }
    public record PendingProbe(int native_index,
            long physical_slot_i64,
            int distance_raw_u8,
            Integer control_raw_u8,
            Long key_raw_full_id_u32) implements Indexed {
        public PendingProbe {
            require((distance_raw_u8>=0 && distance_raw_u8<=255), "distance_raw_u8 u8 required");
            require(control_raw_u8==null || (control_raw_u8>=0 && control_raw_u8<=255), "control_raw_u8 u8 required");
            require(key_raw_full_id_u32==null || (key_raw_full_id_u32>=0 && key_raw_full_id_u32<=0xFFFFFFFFL), "key_raw_full_id_u32 u32 required");
        }
    }
    public record PendingSelection(Status status,
            boolean ready,
            String unavailable_reason,
            String entries_identity,
            Boolean entries_present,
            Integer mask_raw_i32,
            Integer tail_distance_raw_u8,
            Integer end_slot_raw_i32,
            Long target_army_full_id_u32,
            Long hash_raw_u32,
            Long home_slot_i64,
            List<PendingProbe> probes,
            Long selected_physical_slot_i64,
            Boolean selected_is_end_marker,
            Integer selected_control_raw_u8,
            RawReferences suppression_references) {
        public PendingSelection {
            Objects.requireNonNull(status);
            Objects.requireNonNull(unavailable_reason);
            require(entries_identity==null || !entries_identity.isEmpty(), "entries_identity nonempty text required");
            require(tail_distance_raw_u8==null || (tail_distance_raw_u8>=0 && tail_distance_raw_u8<=255), "tail_distance_raw_u8 u8 required");
            require(target_army_full_id_u32==null || (target_army_full_id_u32>=0 && target_army_full_id_u32<=0xFFFFFFFFL), "target_army_full_id_u32 u32 required");
            require(hash_raw_u32==null || (hash_raw_u32>=0 && hash_raw_u32<=0xFFFFFFFFL), "hash_raw_u32 u32 required");
            probes=List.copyOf(probes);
            require(selected_control_raw_u8==null || (selected_control_raw_u8>=0 && selected_control_raw_u8<=255), "selected_control_raw_u8 u8 required");
            Objects.requireNonNull(suppression_references);
            require(ready==(status==Status.AVAILABLE) && ready==unavailable_reason.isEmpty(), "availability, readiness and reason disagree");
        }
    }
    public record ArRgAdmissionOccurrence(Status status,
            boolean ready,
            String unavailable_reason,
            int native_index,
            Long raw_full_id_u32,
            Boolean pending_contains,
            Boolean append) implements Indexed {
        public ArRgAdmissionOccurrence {
            Objects.requireNonNull(status);
            Objects.requireNonNull(unavailable_reason);
            require(raw_full_id_u32==null || (raw_full_id_u32>=0 && raw_full_id_u32<=0xFFFFFFFFL), "raw_full_id_u32 u32 required");
            require(ready==(status==Status.AVAILABLE) && ready==unavailable_reason.isEmpty(), "availability, readiness and reason disagree");
        }
    }
    public record RosterAdmissionOccurrence(Status status,
            boolean ready,
            String unavailable_reason,
            int native_index,
            Long raw_full_id_u32,
            OperandResolution original_army_resolution,
            AdmissionGate gate,
            Long caller_army_unit_id_raw_u32,
            OperandResolution caller_unit_resolution,
            String caller_province_identity,
            Boolean caller_province_present,
            Boolean caller_used_province_fallback,
            Long caller_province_siege_id_raw_u32,
            OperandResolution siege_resolution,
            Integer siege_flag_44c_raw_u8,
            Long selected_army_full_id_raw_u32,
            Boolean removal_contains_selected_army,
            boolean army_append_ready,
            Boolean army_append,
            Long army_append_siege_full_id_u32,
            Long army_append_full_id_u32,
            PendingSelection pending_selection,
            RawReferences original_arrg_references,
            List<ArRgAdmissionOccurrence> arrg_occurrences,
            boolean arrg_append_ready,
            List<Long> arrg_append_full_ids_u32) implements Indexed {
        public RosterAdmissionOccurrence {
            Objects.requireNonNull(status);
            Objects.requireNonNull(unavailable_reason);
            require(raw_full_id_u32==null || (raw_full_id_u32>=0 && raw_full_id_u32<=0xFFFFFFFFL), "raw_full_id_u32 u32 required");
            Objects.requireNonNull(original_army_resolution);
            Objects.requireNonNull(gate);
            require(caller_army_unit_id_raw_u32==null || (caller_army_unit_id_raw_u32>=0 && caller_army_unit_id_raw_u32<=0xFFFFFFFFL), "caller_army_unit_id_raw_u32 u32 required");
            Objects.requireNonNull(caller_unit_resolution);
            require(caller_province_identity==null || !caller_province_identity.isEmpty(), "caller_province_identity nonempty text required");
            require(caller_province_siege_id_raw_u32==null || (caller_province_siege_id_raw_u32>=0 && caller_province_siege_id_raw_u32<=0xFFFFFFFFL), "caller_province_siege_id_raw_u32 u32 required");
            Objects.requireNonNull(siege_resolution);
            require(siege_flag_44c_raw_u8==null || (siege_flag_44c_raw_u8>=0 && siege_flag_44c_raw_u8<=255), "siege_flag_44c_raw_u8 u8 required");
            require(selected_army_full_id_raw_u32==null || (selected_army_full_id_raw_u32>=0 && selected_army_full_id_raw_u32<=0xFFFFFFFFL), "selected_army_full_id_raw_u32 u32 required");
            require(army_append_siege_full_id_u32==null || (army_append_siege_full_id_u32>=0 && army_append_siege_full_id_u32<=0xFFFFFFFFL), "army_append_siege_full_id_u32 u32 required");
            require(army_append_full_id_u32==null || (army_append_full_id_u32>=0 && army_append_full_id_u32<=0xFFFFFFFFL), "army_append_full_id_u32 u32 required");
            Objects.requireNonNull(pending_selection);
            Objects.requireNonNull(original_arrg_references);
            arrg_occurrences=List.copyOf(arrg_occurrences);
            if (arrg_append_full_ids_u32 != null) arrg_append_full_ids_u32=List.copyOf(arrg_append_full_ids_u32);
            if (arrg_append_full_ids_u32 != null) for(Long value:arrg_append_full_ids_u32) require(value!=null && value>=0 && value<=0xFFFFFFFFL, "arrg_append_full_ids_u32 uint32 required");
            require(ready==(status==Status.AVAILABLE) && ready==unavailable_reason.isEmpty(), "availability, readiness and reason disagree");
        }
    }
    public record Root(Status status,
            boolean ready,
            String unavailable_reason,
            int schema_version,
            String source,
            String stage,
            Boolean manager_loaded,
            String manager_identity,
            RawReferences original_roster,
            RawReferences removal_queue,
            List<RosterAdmissionOccurrence> occurrences,
            boolean raw_roster_references_ready,
            boolean original_army_selections_ready,
            boolean army_appends_ready,
            boolean arrg_appends_ready,
            boolean conditional_admission_ready,
            boolean actual_next_callback_ready,
            boolean actual_tomorrow_roster_ready,
            boolean full_future_table_placement_ready,
            boolean full_daily_assault_ready) {
        public Root {
            Objects.requireNonNull(status);
            Objects.requireNonNull(unavailable_reason);
            require(schema_version==1, "schema_version exact original literal required");
            require(source!=null && !source.isEmpty(), "source nonempty text required");
            require("native_current_daily_assault_roster_admission".equals(source), "source exact original literal required");
            require(stage!=null && !stage.isEmpty(), "stage nonempty text required");
            require("observed_current_standalone_2a99b40_admission".equals(stage), "stage exact original literal required");
            require(manager_identity==null || !manager_identity.isEmpty(), "manager_identity nonempty text required");
            Objects.requireNonNull(original_roster);
            Objects.requireNonNull(removal_queue);
            occurrences=List.copyOf(occurrences);
            require(actual_next_callback_ready==false, "actual_next_callback_ready exact original literal required");
            require(actual_tomorrow_roster_ready==false, "actual_tomorrow_roster_ready exact original literal required");
            require(full_future_table_placement_ready==false, "full_future_table_placement_ready exact original literal required");
            require(full_daily_assault_ready==false, "full_daily_assault_ready exact original literal required");
            require(ready==(status==Status.AVAILABLE) && ready==unavailable_reason.isEmpty(), "availability, readiness and reason disagree");
        }
    }
    private record Spec(String name,String kind) { }
    private static final Map<String,List<Spec>> SHAPES=Map.ofEntries(
            Map.entry("OperandResolution",List.of(new Spec("status","string"),new Spec("ready","bool"),new Spec("unavailable_reason","string"),new Spec("requested_full_id_u32","u32?"),new Spec("registry_loaded","bool?"),new Spec("registry_capacity_u32","u32?"),new Spec("registry_index_u32","u32?"),new Spec("indexed_identity","identity?"),new Spec("indexed_full_id_u32","u32?"),new Spec("selection","string?"),new Spec("used_fallback","bool?"),new Spec("object_identity","identity?"),new Spec("selected_full_id_u32","u32?"),new Spec("selected_object_ready","bool"),new Spec("selected_full_id_read_ready","bool?"))),
            Map.entry("RawReferenceOccurrence",List.of(new Spec("status","string"),new Spec("ready","bool"),new Spec("unavailable_reason","string"),new Spec("native_index","i32"),new Spec("raw_full_id_u32","u32?"))),
            Map.entry("RawReferences",List.of(new Spec("status","string"),new Spec("ready","bool"),new Spec("unavailable_reason","string"),new Spec("references_ready","bool"),new Spec("count_raw_i32","i32?"),new Spec("data_identity","identity?"),new Spec("data_present","bool?"),new Spec("occurrences","RawReferenceOccurrence[]"),new Spec("observed_occurrence_count","i32"))),
            Map.entry("RelationProbe",List.of(new Spec("native_index","i32"),new Spec("kind","string"),new Spec("slot_index_i64","i64"),new Spec("key_character_id_raw_u32","u32?"))),
            Map.entry("RelationLookup",List.of(new Spec("status","string"),new Spec("ready","bool"),new Spec("unavailable_reason","string"),new Spec("component_identity","identity?"),new Spec("component_present","bool?"),new Spec("table_data_identity","identity?"),new Spec("table_data_present","bool?"),new Spec("table_count_raw_i32","i32?"),new Spec("target_character_full_id_raw_u32","u32?"),new Spec("probes","RelationProbe[]"),new Spec("candidate_slot_index_i64","i64?"),new Spec("selection","string?"),new Spec("default_relationship_identity","identity?"),new Spec("default_relationship_present","bool?"),new Spec("selected_relationship_identity","identity?"),new Spec("selected_relationship_present","bool?"),new Spec("selected_relationship_war_id_raw_u32","u32?"))),
            Map.entry("AdmissionGate",List.of(new Spec("status","string"),new Spec("ready","bool"),new Spec("unavailable_reason","string"),new Spec("verdict","bool?"),new Spec("original_army_unit_id_raw_u32","u32?"),new Spec("original_unit_resolution","OperandResolution"),new Spec("original_unit_kind_raw_u32","u32?"),new Spec("original_unit_province_identity","identity?"),new Spec("original_unit_province_present","bool?"),new Spec("original_province_identity_raw_u32","u32?"),new Spec("selected_province_comparison_identity","identity?"),new Spec("selected_province_comparison_identity_raw_u32","u32?"),new Spec("original_unit_counter_170_raw_i32","i32?"),new Spec("associated_army_id_raw_u32","u32?"),new Spec("associated_army_resolution","OperandResolution"),new Spec("province_siege_id_raw_u32","u32?"),new Spec("province_counter_850_raw_i32","i32?"),new Spec("associated_army_flag_1d4_raw_u8","u8?"),new Spec("associated_army_flag_1ec_raw_u8","u8?"),new Spec("associated_army_unit_id_raw_u32","u32?"),new Spec("associated_unit_resolution","OperandResolution"),new Spec("associated_unit_character_id_raw_u32","u32?"),new Spec("associated_character_resolution","OperandResolution"),new Spec("province_character_id_73c_raw_u32","u32?"),new Spec("native_2c099f0_character_identity","identity?"),new Spec("native_2c099f0_province_identity","identity?"),new Spec("native_2c099f0_third_argument_is_null","bool?"),new Spec("native_2c099f0_returned","bool"),new Spec("native_2c099f0_classification_raw_i32","i32?"),new Spec("province_character_resolution","OperandResolution"),new Spec("associated_character_full_id_raw_u32","u32?"),new Spec("province_character_full_id_raw_u32","u32?"),new Spec("relation_lookup","RelationLookup"),new Spec("selected_war_resolution","OperandResolution"),new Spec("selected_war_ended_358_raw_u8","u8?"))),
            Map.entry("PendingProbe",List.of(new Spec("native_index","i32"),new Spec("physical_slot_i64","i64"),new Spec("distance_raw_u8","u8"),new Spec("control_raw_u8","u8?"),new Spec("key_raw_full_id_u32","u32?"))),
            Map.entry("PendingSelection",List.of(new Spec("status","string"),new Spec("ready","bool"),new Spec("unavailable_reason","string"),new Spec("entries_identity","identity?"),new Spec("entries_present","bool?"),new Spec("mask_raw_i32","i32?"),new Spec("tail_distance_raw_u8","u8?"),new Spec("end_slot_raw_i32","i32?"),new Spec("target_army_full_id_u32","u32?"),new Spec("hash_raw_u32","u32?"),new Spec("home_slot_i64","i64?"),new Spec("probes","PendingProbe[]"),new Spec("selected_physical_slot_i64","i64?"),new Spec("selected_is_end_marker","bool?"),new Spec("selected_control_raw_u8","u8?"),new Spec("suppression_references","RawReferences"))),
            Map.entry("ArRgAdmissionOccurrence",List.of(new Spec("status","string"),new Spec("ready","bool"),new Spec("unavailable_reason","string"),new Spec("native_index","i32"),new Spec("raw_full_id_u32","u32?"),new Spec("pending_contains","bool?"),new Spec("append","bool?"))),
            Map.entry("RosterAdmissionOccurrence",List.of(new Spec("status","string"),new Spec("ready","bool"),new Spec("unavailable_reason","string"),new Spec("native_index","i32"),new Spec("raw_full_id_u32","u32?"),new Spec("original_army_resolution","OperandResolution"),new Spec("gate","AdmissionGate"),new Spec("caller_army_unit_id_raw_u32","u32?"),new Spec("caller_unit_resolution","OperandResolution"),new Spec("caller_province_identity","identity?"),new Spec("caller_province_present","bool?"),new Spec("caller_used_province_fallback","bool?"),new Spec("caller_province_siege_id_raw_u32","u32?"),new Spec("siege_resolution","OperandResolution"),new Spec("siege_flag_44c_raw_u8","u8?"),new Spec("selected_army_full_id_raw_u32","u32?"),new Spec("removal_contains_selected_army","bool?"),new Spec("army_append_ready","bool"),new Spec("army_append","bool?"),new Spec("army_append_siege_full_id_u32","u32?"),new Spec("army_append_full_id_u32","u32?"),new Spec("pending_selection","PendingSelection"),new Spec("original_arrg_references","RawReferences"),new Spec("arrg_occurrences","ArRgAdmissionOccurrence[]"),new Spec("arrg_append_ready","bool"),new Spec("arrg_append_full_ids_u32","u32[]?"))),
            Map.entry("ArmyCurrentDailyAssaultRosterAdmissionV1",List.of(new Spec("status","string"),new Spec("ready","bool"),new Spec("unavailable_reason","string"),new Spec("schema_version","i32=1"),new Spec("source","string=native_current_daily_assault_roster_admission"),new Spec("stage","string=observed_current_standalone_2a99b40_admission"),new Spec("manager_loaded","bool?"),new Spec("manager_identity","identity?"),new Spec("original_roster","RawReferences"),new Spec("removal_queue","RawReferences"),new Spec("occurrences","RosterAdmissionOccurrence[]"),new Spec("raw_roster_references_ready","bool"),new Spec("original_army_selections_ready","bool"),new Spec("army_appends_ready","bool"),new Spec("arrg_appends_ready","bool"),new Spec("conditional_admission_ready","bool"),new Spec("actual_next_callback_ready","bool=false"),new Spec("actual_tomorrow_roster_ready","bool=false"),new Spec("full_future_table_placement_ready","bool=false"),new Spec("full_daily_assault_ready","bool=false")))
    );
    private static final Set<String> CLASSIFIER=Set.of("native_2c099f0_character_identity","native_2c099f0_province_identity","native_2c099f0_third_argument_is_null","native_2c099f0_returned","native_2c099f0_classification_raw_i32");
    private static final JsonNodeFactory J=JsonNodeFactory.instance;
    static IllegalArgumentException bad(String name,String why) { return new IllegalArgumentException(name+": "+why); }
    static void require(boolean condition,String why) { if(!condition) throw new IllegalArgumentException(why); }
    /** Shape, exact JSON type, range, literal and availability only; this grants no derived readiness. */
    public static void validateType(JsonNode value,String kind) { validateType(value,kind,kind); }
    public static void validateType(JsonNode value,String kind,String name) {
        if(kind.endsWith("?")) { if(value!=null && value.isNull()) return; kind=kind.substring(0,kind.length()-1); }
        if(value==null) throw bad(name,"missing field");
        if(kind.endsWith("[]")) {
            if(!value.isArray()) throw bad(name,"native array required");
            String item=kind.substring(0,kind.length()-2);
            for(int i=0;i<value.size();i++) validateType(value.get(i),item,name+"["+i+"]");
            return;
        }
        int eq=kind.indexOf('=');
        if(eq>=0) {
            String base=kind.substring(0,eq), literal=kind.substring(eq+1);
            validateType(value,base,name);
            boolean same=switch(base) {case "string" -> value.textValue().equals(literal); case "bool" -> value.booleanValue()==Boolean.parseBoolean(literal); default -> value.bigIntegerValue().equals(new BigInteger(literal));};
            if(!same) throw bad(name,"exact source literal required");
            return;
        }
        List<Spec> schema=SHAPES.get(kind);
        if(schema!=null) {
            if(!value.isObject() || value.size()!=schema.size()) throw bad(name,"closed schema required");
            Set<String> keys=new HashSet<>(); value.fieldNames().forEachRemaining(keys::add);
            for(Spec spec:schema) {
                if(!keys.remove(spec.name())) throw bad(name+"."+spec.name(),"missing required field");
                validateType(value.get(spec.name()),spec.kind(),name+"."+spec.name());
            }
            if(!keys.isEmpty()) throw bad(name,"unexpected field");
            if(value.has("status")) {
                Status status=Status.parse(value.get("status").textValue());
                boolean ready=value.get("ready").booleanValue();
                if(ready!=(status==Status.AVAILABLE) || ready!=value.get("unavailable_reason").textValue().isEmpty())
                    throw bad(name,"availability, readiness and reason disagree");
            }
            return;
        }
        switch(kind) {
            case "bool" -> { if(!value.isBoolean()) throw bad(name,"bool required"); }
            case "string","identity" -> { if(!value.isTextual() || value.textValue().isEmpty() && !name.endsWith(".unavailable_reason")) throw bad(name,"nonempty text required"); }
            case "u8","u32","i32","i64" -> {
                int bits=kind.equals("u8")?8:kind.equals("i64")?64:32;
                boolean unsigned=kind.startsWith("u");
                BigInteger low=unsigned?BigInteger.ZERO:BigInteger.ONE.shiftLeft(bits-1).negate();
                BigInteger high=BigInteger.ONE.shiftLeft(unsigned?bits:bits-1);
                if(!value.isIntegralNumber() || value.bigIntegerValue().compareTo(low)<0 || value.bigIntegerValue().compareTo(high)>=0) throw bad(name,"exact "+kind+" integer required");
            }
            default -> throw bad(name,"unsupported contract kind "+kind);
        }
    }
    public static OperandResolution decodeOperandResolution(JsonNode raw,String name) {
        validateType(raw,"OperandResolution",name);
        ObjectNode o=(ObjectNode)raw;
        return new OperandResolution(Status.parse(o.get("status").textValue()),
                o.get("ready").booleanValue(),
                o.get("unavailable_reason").textValue(),
                o.get("requested_full_id_u32").isNull()?null:o.get("requested_full_id_u32").longValue(),
                o.get("registry_loaded").isNull()?null:o.get("registry_loaded").booleanValue(),
                o.get("registry_capacity_u32").isNull()?null:o.get("registry_capacity_u32").longValue(),
                o.get("registry_index_u32").isNull()?null:o.get("registry_index_u32").longValue(),
                o.get("indexed_identity").isNull()?null:o.get("indexed_identity").textValue(),
                o.get("indexed_full_id_u32").isNull()?null:o.get("indexed_full_id_u32").longValue(),
                o.get("selection").isNull()?null:o.get("selection").textValue(),
                o.get("used_fallback").isNull()?null:o.get("used_fallback").booleanValue(),
                o.get("object_identity").isNull()?null:o.get("object_identity").textValue(),
                o.get("selected_full_id_u32").isNull()?null:o.get("selected_full_id_u32").longValue(),
                o.get("selected_object_ready").booleanValue(),
                o.get("selected_full_id_read_ready").isNull()?null:o.get("selected_full_id_read_ready").booleanValue());
    }
    public static ObjectNode encodeOperandResolution(OperandResolution value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("status",node(value.status().wire()));
        o.set("ready",node(value.ready()));
        o.set("unavailable_reason",node(value.unavailable_reason()));
        o.set("requested_full_id_u32",node(value.requested_full_id_u32()));
        o.set("registry_loaded",node(value.registry_loaded()));
        o.set("registry_capacity_u32",node(value.registry_capacity_u32()));
        o.set("registry_index_u32",node(value.registry_index_u32()));
        o.set("indexed_identity",node(value.indexed_identity()));
        o.set("indexed_full_id_u32",node(value.indexed_full_id_u32()));
        o.set("selection",node(value.selection()));
        o.set("used_fallback",node(value.used_fallback()));
        o.set("object_identity",node(value.object_identity()));
        o.set("selected_full_id_u32",node(value.selected_full_id_u32()));
        o.set("selected_object_ready",node(value.selected_object_ready()));
        o.set("selected_full_id_read_ready",node(value.selected_full_id_read_ready()));
        validateType(o,"OperandResolution","OperandResolution"); return o;
    }
    public static RawReferenceOccurrence decodeRawReferenceOccurrence(JsonNode raw,String name) {
        validateType(raw,"RawReferenceOccurrence",name);
        ObjectNode o=(ObjectNode)raw;
        return new RawReferenceOccurrence(Status.parse(o.get("status").textValue()),
                o.get("ready").booleanValue(),
                o.get("unavailable_reason").textValue(),
                o.get("native_index").intValue(),
                o.get("raw_full_id_u32").isNull()?null:o.get("raw_full_id_u32").longValue());
    }
    public static ObjectNode encodeRawReferenceOccurrence(RawReferenceOccurrence value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("status",node(value.status().wire()));
        o.set("ready",node(value.ready()));
        o.set("unavailable_reason",node(value.unavailable_reason()));
        o.set("native_index",node(value.native_index()));
        o.set("raw_full_id_u32",node(value.raw_full_id_u32()));
        validateType(o,"RawReferenceOccurrence","RawReferenceOccurrence"); return o;
    }
    public static RawReferences decodeRawReferences(JsonNode raw,String name) {
        validateType(raw,"RawReferences",name);
        ObjectNode o=(ObjectNode)raw;
        return new RawReferences(Status.parse(o.get("status").textValue()),
                o.get("ready").booleanValue(),
                o.get("unavailable_reason").textValue(),
                o.get("references_ready").booleanValue(),
                o.get("count_raw_i32").isNull()?null:o.get("count_raw_i32").intValue(),
                o.get("data_identity").isNull()?null:o.get("data_identity").textValue(),
                o.get("data_present").isNull()?null:o.get("data_present").booleanValue(),
                readList(o.get("occurrences"), n -> decodeRawReferenceOccurrence(n,name+".occurrences[]")),
                o.get("observed_occurrence_count").intValue());
    }
    public static ObjectNode encodeRawReferences(RawReferences value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("status",node(value.status().wire()));
        o.set("ready",node(value.ready()));
        o.set("unavailable_reason",node(value.unavailable_reason()));
        o.set("references_ready",node(value.references_ready()));
        o.set("count_raw_i32",node(value.count_raw_i32()));
        o.set("data_identity",node(value.data_identity()));
        o.set("data_present",node(value.data_present()));
        o.set("occurrences",list(value.occurrences(), ArmyStrengthsRosterContract::encodeRawReferenceOccurrence));
        o.set("observed_occurrence_count",node(value.observed_occurrence_count()));
        validateType(o,"RawReferences","RawReferences"); return o;
    }
    public static RelationProbe decodeRelationProbe(JsonNode raw,String name) {
        validateType(raw,"RelationProbe",name);
        ObjectNode o=(ObjectNode)raw;
        return new RelationProbe(o.get("native_index").intValue(),
                o.get("kind").textValue(),
                o.get("slot_index_i64").longValue(),
                o.get("key_character_id_raw_u32").isNull()?null:o.get("key_character_id_raw_u32").longValue());
    }
    public static ObjectNode encodeRelationProbe(RelationProbe value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("native_index",node(value.native_index()));
        o.set("kind",node(value.kind()));
        o.set("slot_index_i64",node(value.slot_index_i64()));
        o.set("key_character_id_raw_u32",node(value.key_character_id_raw_u32()));
        validateType(o,"RelationProbe","RelationProbe"); return o;
    }
    public static RelationLookup decodeRelationLookup(JsonNode raw,String name) {
        validateType(raw,"RelationLookup",name);
        ObjectNode o=(ObjectNode)raw;
        return new RelationLookup(Status.parse(o.get("status").textValue()),
                o.get("ready").booleanValue(),
                o.get("unavailable_reason").textValue(),
                o.get("component_identity").isNull()?null:o.get("component_identity").textValue(),
                o.get("component_present").isNull()?null:o.get("component_present").booleanValue(),
                o.get("table_data_identity").isNull()?null:o.get("table_data_identity").textValue(),
                o.get("table_data_present").isNull()?null:o.get("table_data_present").booleanValue(),
                o.get("table_count_raw_i32").isNull()?null:o.get("table_count_raw_i32").intValue(),
                o.get("target_character_full_id_raw_u32").isNull()?null:o.get("target_character_full_id_raw_u32").longValue(),
                readList(o.get("probes"), n -> decodeRelationProbe(n,name+".probes[]")),
                o.get("candidate_slot_index_i64").isNull()?null:o.get("candidate_slot_index_i64").longValue(),
                o.get("selection").isNull()?null:o.get("selection").textValue(),
                o.get("default_relationship_identity").isNull()?null:o.get("default_relationship_identity").textValue(),
                o.get("default_relationship_present").isNull()?null:o.get("default_relationship_present").booleanValue(),
                o.get("selected_relationship_identity").isNull()?null:o.get("selected_relationship_identity").textValue(),
                o.get("selected_relationship_present").isNull()?null:o.get("selected_relationship_present").booleanValue(),
                o.get("selected_relationship_war_id_raw_u32").isNull()?null:o.get("selected_relationship_war_id_raw_u32").longValue());
    }
    public static ObjectNode encodeRelationLookup(RelationLookup value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("status",node(value.status().wire()));
        o.set("ready",node(value.ready()));
        o.set("unavailable_reason",node(value.unavailable_reason()));
        o.set("component_identity",node(value.component_identity()));
        o.set("component_present",node(value.component_present()));
        o.set("table_data_identity",node(value.table_data_identity()));
        o.set("table_data_present",node(value.table_data_present()));
        o.set("table_count_raw_i32",node(value.table_count_raw_i32()));
        o.set("target_character_full_id_raw_u32",node(value.target_character_full_id_raw_u32()));
        o.set("probes",list(value.probes(), ArmyStrengthsRosterContract::encodeRelationProbe));
        o.set("candidate_slot_index_i64",node(value.candidate_slot_index_i64()));
        o.set("selection",node(value.selection()));
        o.set("default_relationship_identity",node(value.default_relationship_identity()));
        o.set("default_relationship_present",node(value.default_relationship_present()));
        o.set("selected_relationship_identity",node(value.selected_relationship_identity()));
        o.set("selected_relationship_present",node(value.selected_relationship_present()));
        o.set("selected_relationship_war_id_raw_u32",node(value.selected_relationship_war_id_raw_u32()));
        validateType(o,"RelationLookup","RelationLookup"); return o;
    }
    public static AdmissionGate decodeAdmissionGate(JsonNode raw,String name) {
        validateType(raw,"AdmissionGate",name);
        ObjectNode o=(ObjectNode)raw;
        return new AdmissionGate(Status.parse(o.get("status").textValue()),
                o.get("ready").booleanValue(),
                o.get("unavailable_reason").textValue(),
                o.get("verdict").isNull()?null:o.get("verdict").booleanValue(),
                o.get("original_army_unit_id_raw_u32").isNull()?null:o.get("original_army_unit_id_raw_u32").longValue(),
                decodeOperandResolution(o.get("original_unit_resolution"),name+".original_unit_resolution"),
                o.get("original_unit_kind_raw_u32").isNull()?null:o.get("original_unit_kind_raw_u32").longValue(),
                o.get("original_unit_province_identity").isNull()?null:o.get("original_unit_province_identity").textValue(),
                o.get("original_unit_province_present").isNull()?null:o.get("original_unit_province_present").booleanValue(),
                o.get("original_province_identity_raw_u32").isNull()?null:o.get("original_province_identity_raw_u32").longValue(),
                o.get("selected_province_comparison_identity").isNull()?null:o.get("selected_province_comparison_identity").textValue(),
                o.get("selected_province_comparison_identity_raw_u32").isNull()?null:o.get("selected_province_comparison_identity_raw_u32").longValue(),
                o.get("original_unit_counter_170_raw_i32").isNull()?null:o.get("original_unit_counter_170_raw_i32").intValue(),
                o.get("associated_army_id_raw_u32").isNull()?null:o.get("associated_army_id_raw_u32").longValue(),
                decodeOperandResolution(o.get("associated_army_resolution"),name+".associated_army_resolution"),
                o.get("province_siege_id_raw_u32").isNull()?null:o.get("province_siege_id_raw_u32").longValue(),
                o.get("province_counter_850_raw_i32").isNull()?null:o.get("province_counter_850_raw_i32").intValue(),
                o.get("associated_army_flag_1d4_raw_u8").isNull()?null:o.get("associated_army_flag_1d4_raw_u8").intValue(),
                o.get("associated_army_flag_1ec_raw_u8").isNull()?null:o.get("associated_army_flag_1ec_raw_u8").intValue(),
                o.get("associated_army_unit_id_raw_u32").isNull()?null:o.get("associated_army_unit_id_raw_u32").longValue(),
                decodeOperandResolution(o.get("associated_unit_resolution"),name+".associated_unit_resolution"),
                o.get("associated_unit_character_id_raw_u32").isNull()?null:o.get("associated_unit_character_id_raw_u32").longValue(),
                decodeOperandResolution(o.get("associated_character_resolution"),name+".associated_character_resolution"),
                o.get("province_character_id_73c_raw_u32").isNull()?null:o.get("province_character_id_73c_raw_u32").longValue(),
                o.get("native_2c099f0_character_identity").isNull()?null:o.get("native_2c099f0_character_identity").textValue(),
                o.get("native_2c099f0_province_identity").isNull()?null:o.get("native_2c099f0_province_identity").textValue(),
                o.get("native_2c099f0_third_argument_is_null").isNull()?null:o.get("native_2c099f0_third_argument_is_null").booleanValue(),
                o.get("native_2c099f0_returned").booleanValue(),
                o.get("native_2c099f0_classification_raw_i32").isNull()?null:o.get("native_2c099f0_classification_raw_i32").intValue(),
                decodeOperandResolution(o.get("province_character_resolution"),name+".province_character_resolution"),
                o.get("associated_character_full_id_raw_u32").isNull()?null:o.get("associated_character_full_id_raw_u32").longValue(),
                o.get("province_character_full_id_raw_u32").isNull()?null:o.get("province_character_full_id_raw_u32").longValue(),
                decodeRelationLookup(o.get("relation_lookup"),name+".relation_lookup"),
                decodeOperandResolution(o.get("selected_war_resolution"),name+".selected_war_resolution"),
                o.get("selected_war_ended_358_raw_u8").isNull()?null:o.get("selected_war_ended_358_raw_u8").intValue());
    }
    public static ObjectNode encodeAdmissionGate(AdmissionGate value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("status",node(value.status().wire()));
        o.set("ready",node(value.ready()));
        o.set("unavailable_reason",node(value.unavailable_reason()));
        o.set("verdict",node(value.verdict()));
        o.set("original_army_unit_id_raw_u32",node(value.original_army_unit_id_raw_u32()));
        o.set("original_unit_resolution",encodeOperandResolution(value.original_unit_resolution()));
        o.set("original_unit_kind_raw_u32",node(value.original_unit_kind_raw_u32()));
        o.set("original_unit_province_identity",node(value.original_unit_province_identity()));
        o.set("original_unit_province_present",node(value.original_unit_province_present()));
        o.set("original_province_identity_raw_u32",node(value.original_province_identity_raw_u32()));
        o.set("selected_province_comparison_identity",node(value.selected_province_comparison_identity()));
        o.set("selected_province_comparison_identity_raw_u32",node(value.selected_province_comparison_identity_raw_u32()));
        o.set("original_unit_counter_170_raw_i32",node(value.original_unit_counter_170_raw_i32()));
        o.set("associated_army_id_raw_u32",node(value.associated_army_id_raw_u32()));
        o.set("associated_army_resolution",encodeOperandResolution(value.associated_army_resolution()));
        o.set("province_siege_id_raw_u32",node(value.province_siege_id_raw_u32()));
        o.set("province_counter_850_raw_i32",node(value.province_counter_850_raw_i32()));
        o.set("associated_army_flag_1d4_raw_u8",node(value.associated_army_flag_1d4_raw_u8()));
        o.set("associated_army_flag_1ec_raw_u8",node(value.associated_army_flag_1ec_raw_u8()));
        o.set("associated_army_unit_id_raw_u32",node(value.associated_army_unit_id_raw_u32()));
        o.set("associated_unit_resolution",encodeOperandResolution(value.associated_unit_resolution()));
        o.set("associated_unit_character_id_raw_u32",node(value.associated_unit_character_id_raw_u32()));
        o.set("associated_character_resolution",encodeOperandResolution(value.associated_character_resolution()));
        o.set("province_character_id_73c_raw_u32",node(value.province_character_id_73c_raw_u32()));
        o.set("native_2c099f0_character_identity",node(value.native_2c099f0_character_identity()));
        o.set("native_2c099f0_province_identity",node(value.native_2c099f0_province_identity()));
        o.set("native_2c099f0_third_argument_is_null",node(value.native_2c099f0_third_argument_is_null()));
        o.set("native_2c099f0_returned",node(value.native_2c099f0_returned()));
        o.set("native_2c099f0_classification_raw_i32",node(value.native_2c099f0_classification_raw_i32()));
        o.set("province_character_resolution",encodeOperandResolution(value.province_character_resolution()));
        o.set("associated_character_full_id_raw_u32",node(value.associated_character_full_id_raw_u32()));
        o.set("province_character_full_id_raw_u32",node(value.province_character_full_id_raw_u32()));
        o.set("relation_lookup",encodeRelationLookup(value.relation_lookup()));
        o.set("selected_war_resolution",encodeOperandResolution(value.selected_war_resolution()));
        o.set("selected_war_ended_358_raw_u8",node(value.selected_war_ended_358_raw_u8()));
        validateType(o,"AdmissionGate","AdmissionGate"); return o;
    }
    public static PendingProbe decodePendingProbe(JsonNode raw,String name) {
        validateType(raw,"PendingProbe",name);
        ObjectNode o=(ObjectNode)raw;
        return new PendingProbe(o.get("native_index").intValue(),
                o.get("physical_slot_i64").longValue(),
                o.get("distance_raw_u8").intValue(),
                o.get("control_raw_u8").isNull()?null:o.get("control_raw_u8").intValue(),
                o.get("key_raw_full_id_u32").isNull()?null:o.get("key_raw_full_id_u32").longValue());
    }
    public static ObjectNode encodePendingProbe(PendingProbe value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("native_index",node(value.native_index()));
        o.set("physical_slot_i64",node(value.physical_slot_i64()));
        o.set("distance_raw_u8",node(value.distance_raw_u8()));
        o.set("control_raw_u8",node(value.control_raw_u8()));
        o.set("key_raw_full_id_u32",node(value.key_raw_full_id_u32()));
        validateType(o,"PendingProbe","PendingProbe"); return o;
    }
    public static PendingSelection decodePendingSelection(JsonNode raw,String name) {
        validateType(raw,"PendingSelection",name);
        ObjectNode o=(ObjectNode)raw;
        return new PendingSelection(Status.parse(o.get("status").textValue()),
                o.get("ready").booleanValue(),
                o.get("unavailable_reason").textValue(),
                o.get("entries_identity").isNull()?null:o.get("entries_identity").textValue(),
                o.get("entries_present").isNull()?null:o.get("entries_present").booleanValue(),
                o.get("mask_raw_i32").isNull()?null:o.get("mask_raw_i32").intValue(),
                o.get("tail_distance_raw_u8").isNull()?null:o.get("tail_distance_raw_u8").intValue(),
                o.get("end_slot_raw_i32").isNull()?null:o.get("end_slot_raw_i32").intValue(),
                o.get("target_army_full_id_u32").isNull()?null:o.get("target_army_full_id_u32").longValue(),
                o.get("hash_raw_u32").isNull()?null:o.get("hash_raw_u32").longValue(),
                o.get("home_slot_i64").isNull()?null:o.get("home_slot_i64").longValue(),
                readList(o.get("probes"), n -> decodePendingProbe(n,name+".probes[]")),
                o.get("selected_physical_slot_i64").isNull()?null:o.get("selected_physical_slot_i64").longValue(),
                o.get("selected_is_end_marker").isNull()?null:o.get("selected_is_end_marker").booleanValue(),
                o.get("selected_control_raw_u8").isNull()?null:o.get("selected_control_raw_u8").intValue(),
                decodeRawReferences(o.get("suppression_references"),name+".suppression_references"));
    }
    public static ObjectNode encodePendingSelection(PendingSelection value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("status",node(value.status().wire()));
        o.set("ready",node(value.ready()));
        o.set("unavailable_reason",node(value.unavailable_reason()));
        o.set("entries_identity",node(value.entries_identity()));
        o.set("entries_present",node(value.entries_present()));
        o.set("mask_raw_i32",node(value.mask_raw_i32()));
        o.set("tail_distance_raw_u8",node(value.tail_distance_raw_u8()));
        o.set("end_slot_raw_i32",node(value.end_slot_raw_i32()));
        o.set("target_army_full_id_u32",node(value.target_army_full_id_u32()));
        o.set("hash_raw_u32",node(value.hash_raw_u32()));
        o.set("home_slot_i64",node(value.home_slot_i64()));
        o.set("probes",list(value.probes(), ArmyStrengthsRosterContract::encodePendingProbe));
        o.set("selected_physical_slot_i64",node(value.selected_physical_slot_i64()));
        o.set("selected_is_end_marker",node(value.selected_is_end_marker()));
        o.set("selected_control_raw_u8",node(value.selected_control_raw_u8()));
        o.set("suppression_references",encodeRawReferences(value.suppression_references()));
        validateType(o,"PendingSelection","PendingSelection"); return o;
    }
    public static ArRgAdmissionOccurrence decodeArRgAdmissionOccurrence(JsonNode raw,String name) {
        validateType(raw,"ArRgAdmissionOccurrence",name);
        ObjectNode o=(ObjectNode)raw;
        return new ArRgAdmissionOccurrence(Status.parse(o.get("status").textValue()),
                o.get("ready").booleanValue(),
                o.get("unavailable_reason").textValue(),
                o.get("native_index").intValue(),
                o.get("raw_full_id_u32").isNull()?null:o.get("raw_full_id_u32").longValue(),
                o.get("pending_contains").isNull()?null:o.get("pending_contains").booleanValue(),
                o.get("append").isNull()?null:o.get("append").booleanValue());
    }
    public static ObjectNode encodeArRgAdmissionOccurrence(ArRgAdmissionOccurrence value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("status",node(value.status().wire()));
        o.set("ready",node(value.ready()));
        o.set("unavailable_reason",node(value.unavailable_reason()));
        o.set("native_index",node(value.native_index()));
        o.set("raw_full_id_u32",node(value.raw_full_id_u32()));
        o.set("pending_contains",node(value.pending_contains()));
        o.set("append",node(value.append()));
        validateType(o,"ArRgAdmissionOccurrence","ArRgAdmissionOccurrence"); return o;
    }
    public static RosterAdmissionOccurrence decodeRosterAdmissionOccurrence(JsonNode raw,String name) {
        validateType(raw,"RosterAdmissionOccurrence",name);
        ObjectNode o=(ObjectNode)raw;
        return new RosterAdmissionOccurrence(Status.parse(o.get("status").textValue()),
                o.get("ready").booleanValue(),
                o.get("unavailable_reason").textValue(),
                o.get("native_index").intValue(),
                o.get("raw_full_id_u32").isNull()?null:o.get("raw_full_id_u32").longValue(),
                decodeOperandResolution(o.get("original_army_resolution"),name+".original_army_resolution"),
                decodeAdmissionGate(o.get("gate"),name+".gate"),
                o.get("caller_army_unit_id_raw_u32").isNull()?null:o.get("caller_army_unit_id_raw_u32").longValue(),
                decodeOperandResolution(o.get("caller_unit_resolution"),name+".caller_unit_resolution"),
                o.get("caller_province_identity").isNull()?null:o.get("caller_province_identity").textValue(),
                o.get("caller_province_present").isNull()?null:o.get("caller_province_present").booleanValue(),
                o.get("caller_used_province_fallback").isNull()?null:o.get("caller_used_province_fallback").booleanValue(),
                o.get("caller_province_siege_id_raw_u32").isNull()?null:o.get("caller_province_siege_id_raw_u32").longValue(),
                decodeOperandResolution(o.get("siege_resolution"),name+".siege_resolution"),
                o.get("siege_flag_44c_raw_u8").isNull()?null:o.get("siege_flag_44c_raw_u8").intValue(),
                o.get("selected_army_full_id_raw_u32").isNull()?null:o.get("selected_army_full_id_raw_u32").longValue(),
                o.get("removal_contains_selected_army").isNull()?null:o.get("removal_contains_selected_army").booleanValue(),
                o.get("army_append_ready").booleanValue(),
                o.get("army_append").isNull()?null:o.get("army_append").booleanValue(),
                o.get("army_append_siege_full_id_u32").isNull()?null:o.get("army_append_siege_full_id_u32").longValue(),
                o.get("army_append_full_id_u32").isNull()?null:o.get("army_append_full_id_u32").longValue(),
                decodePendingSelection(o.get("pending_selection"),name+".pending_selection"),
                decodeRawReferences(o.get("original_arrg_references"),name+".original_arrg_references"),
                readList(o.get("arrg_occurrences"), n -> decodeArRgAdmissionOccurrence(n,name+".arrg_occurrences[]")),
                o.get("arrg_append_ready").booleanValue(),
                o.get("arrg_append_full_ids_u32").isNull()?null:readList(o.get("arrg_append_full_ids_u32"), n -> n.longValue()));
    }
    public static ObjectNode encodeRosterAdmissionOccurrence(RosterAdmissionOccurrence value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("status",node(value.status().wire()));
        o.set("ready",node(value.ready()));
        o.set("unavailable_reason",node(value.unavailable_reason()));
        o.set("native_index",node(value.native_index()));
        o.set("raw_full_id_u32",node(value.raw_full_id_u32()));
        o.set("original_army_resolution",encodeOperandResolution(value.original_army_resolution()));
        o.set("gate",encodeAdmissionGate(value.gate()));
        o.set("caller_army_unit_id_raw_u32",node(value.caller_army_unit_id_raw_u32()));
        o.set("caller_unit_resolution",encodeOperandResolution(value.caller_unit_resolution()));
        o.set("caller_province_identity",node(value.caller_province_identity()));
        o.set("caller_province_present",node(value.caller_province_present()));
        o.set("caller_used_province_fallback",node(value.caller_used_province_fallback()));
        o.set("caller_province_siege_id_raw_u32",node(value.caller_province_siege_id_raw_u32()));
        o.set("siege_resolution",encodeOperandResolution(value.siege_resolution()));
        o.set("siege_flag_44c_raw_u8",node(value.siege_flag_44c_raw_u8()));
        o.set("selected_army_full_id_raw_u32",node(value.selected_army_full_id_raw_u32()));
        o.set("removal_contains_selected_army",node(value.removal_contains_selected_army()));
        o.set("army_append_ready",node(value.army_append_ready()));
        o.set("army_append",node(value.army_append()));
        o.set("army_append_siege_full_id_u32",node(value.army_append_siege_full_id_u32()));
        o.set("army_append_full_id_u32",node(value.army_append_full_id_u32()));
        o.set("pending_selection",encodePendingSelection(value.pending_selection()));
        o.set("original_arrg_references",encodeRawReferences(value.original_arrg_references()));
        o.set("arrg_occurrences",list(value.arrg_occurrences(), ArmyStrengthsRosterContract::encodeArRgAdmissionOccurrence));
        o.set("arrg_append_ready",node(value.arrg_append_ready()));
        o.set("arrg_append_full_ids_u32",value.arrg_append_full_ids_u32()==null?NullNode.instance:list(value.arrg_append_full_ids_u32(), ArmyStrengthsRosterContract::node));
        validateType(o,"RosterAdmissionOccurrence","RosterAdmissionOccurrence"); return o;
    }
    public static Root decodeRoot(JsonNode raw,String name) {
        validateType(raw,"ArmyCurrentDailyAssaultRosterAdmissionV1",name);
        ObjectNode o=(ObjectNode)raw;
        return new Root(Status.parse(o.get("status").textValue()),
                o.get("ready").booleanValue(),
                o.get("unavailable_reason").textValue(),
                o.get("schema_version").intValue(),
                o.get("source").textValue(),
                o.get("stage").textValue(),
                o.get("manager_loaded").isNull()?null:o.get("manager_loaded").booleanValue(),
                o.get("manager_identity").isNull()?null:o.get("manager_identity").textValue(),
                decodeRawReferences(o.get("original_roster"),name+".original_roster"),
                decodeRawReferences(o.get("removal_queue"),name+".removal_queue"),
                readList(o.get("occurrences"), n -> decodeRosterAdmissionOccurrence(n,name+".occurrences[]")),
                o.get("raw_roster_references_ready").booleanValue(),
                o.get("original_army_selections_ready").booleanValue(),
                o.get("army_appends_ready").booleanValue(),
                o.get("arrg_appends_ready").booleanValue(),
                o.get("conditional_admission_ready").booleanValue(),
                o.get("actual_next_callback_ready").booleanValue(),
                o.get("actual_tomorrow_roster_ready").booleanValue(),
                o.get("full_future_table_placement_ready").booleanValue(),
                o.get("full_daily_assault_ready").booleanValue());
    }
    public static ObjectNode encodeRoot(Root value) {
        Objects.requireNonNull(value); ObjectNode o=J.objectNode();
        o.set("status",node(value.status().wire()));
        o.set("ready",node(value.ready()));
        o.set("unavailable_reason",node(value.unavailable_reason()));
        o.set("schema_version",node(value.schema_version()));
        o.set("source",node(value.source()));
        o.set("stage",node(value.stage()));
        o.set("manager_loaded",node(value.manager_loaded()));
        o.set("manager_identity",node(value.manager_identity()));
        o.set("original_roster",encodeRawReferences(value.original_roster()));
        o.set("removal_queue",encodeRawReferences(value.removal_queue()));
        o.set("occurrences",list(value.occurrences(), ArmyStrengthsRosterContract::encodeRosterAdmissionOccurrence));
        o.set("raw_roster_references_ready",node(value.raw_roster_references_ready()));
        o.set("original_army_selections_ready",node(value.original_army_selections_ready()));
        o.set("army_appends_ready",node(value.army_appends_ready()));
        o.set("arrg_appends_ready",node(value.arrg_appends_ready()));
        o.set("conditional_admission_ready",node(value.conditional_admission_ready()));
        o.set("actual_next_callback_ready",node(value.actual_next_callback_ready()));
        o.set("actual_tomorrow_roster_ready",node(value.actual_tomorrow_roster_ready()));
        o.set("full_future_table_placement_ready",node(value.full_future_table_placement_ready()));
        o.set("full_daily_assault_ready",node(value.full_daily_assault_ready()));
        validateType(o,"ArmyCurrentDailyAssaultRosterAdmissionV1","Root"); return o;
    }
    private static <T> List<T> readList(JsonNode raw,Function<JsonNode,T> decoder) { List<T> values=new ArrayList<>(); for(JsonNode row:raw) values.add(decoder.apply(row)); return List.copyOf(values); }
    static <T> JsonNode list(List<T> values,Function<T,? extends JsonNode> encoder) { if(values==null)return NullNode.instance; ArrayNode result=J.arrayNode(); for(T value:values)result.add(encoder.apply(value)); return result; }
    static JsonNode node(String value) { return value==null?NullNode.instance:TextNode.valueOf(value); }
    static JsonNode node(Boolean value) { return value==null?NullNode.instance:BooleanNode.valueOf(value); }
    static JsonNode node(Number value) { return value==null?NullNode.instance:LongNode.valueOf(value.longValue()); }

    public static void validateOrdered(List<? extends Indexed> rows,String name,Integer count) {
        int previous=-1;
        for(Indexed row:rows) {
            int index=row.native_index();
            if(index<0 || index<=previous || count!=null && count>=0 && index>=count)
                throw bad(name,"native occurrence order is malformed");
            previous=index;
        }
    }
    public static void validateReferences(RawReferences value,String name) {
        if(value.occurrences().size()!=value.observed_occurrence_count()) throw bad(name,"observed count is malformed");
        validateOrdered(value.occurrences(),name,value.count_raw_i32());
        for(RawReferenceOccurrence row:value.occurrences()) if(row.ready()!=(row.raw_full_id_u32()!=null)) throw bad(name,"raw occurrence readiness is malformed");
        boolean complete=ArmyRosterDerivation.referencesReady(value);
        if(value.references_ready()!=complete || value.ready()!=complete) throw bad(name,"raw references readiness is malformed");
    }
    public static void validateResolution(OperandResolution value,Long requested,String name) {
        boolean demanded=value.requested_full_id_u32()!=null || value.selection()!=null || value.selected_object_ready();
        if(demanded && !Objects.equals(value.requested_full_id_u32(),requested)) throw bad(name,"lost raw requested full ID");
        if(value.selection()!=null && !Set.of("registry_full_id","native_fallback").contains(value.selection())) throw bad(name,"invalid selection");
        if(value.selection()!=null && !Objects.equals(value.used_fallback(),value.selection().equals("native_fallback"))) throw bad(name,"fallback provenance is malformed");
        if(value.registry_index_u32()!=null && (requested==null || value.registry_index_u32()!=(requested & 0xFFFFFFL))) throw bad(name,"raw full-ID index is malformed");
        if(value.selected_object_ready() && (value.object_identity()==null || value.selection()==null)) throw bad(name,"selected native operand is unobserved");
        if("registry_full_id".equals(value.selection()) && value.selected_object_ready() &&
                (!Objects.equals(value.indexed_full_id_u32(),requested) || !Objects.equals(value.selected_full_id_u32(),requested))) throw bad(name,"indexed full generation does not match");
        if(Boolean.TRUE.equals(value.selected_full_id_read_ready()) && value.selected_full_id_u32()==null) throw bad(name,"claimed full-ID read has no value");
        if(value.ready() && !(value.selected_object_ready() && Boolean.TRUE.equals(value.selected_full_id_read_ready()))) throw bad(name,"complete generic metadata is missing");
    }
    public static Root decodeRoot(JsonNode raw) { return decodeRoot(raw,"current_daily_assault_roster_admission_v1"); }
    /** Strict family entry; the entire five-field classifier extension alone may be absent in an old producer. */
    public static ObjectNode normalizeRoster(JsonNode raw) {
        if(raw==null || raw.isNull()) return null;
        JsonNode adjusted=legacyClassifierDefaults(raw);
        Root root=decodeRoot(adjusted);
        validateRoot(root);
        return encodeRoot(root);
    }
    private static JsonNode legacyClassifierDefaults(JsonNode raw) {
        if(!raw.isObject() || !raw.path("occurrences").isArray()) return raw;
        ObjectNode result=(ObjectNode)raw.deepCopy();
        for(JsonNode row:result.withArray("occurrences")) {
            JsonNode gate=row.get("gate");
            if(gate instanceof ObjectNode object && CLASSIFIER.stream().noneMatch(object::has)) {
                for(String key:CLASSIFIER) object.set(key,key.equals("native_2c099f0_returned")?BooleanNode.FALSE:NullNode.instance);
            }
        }
        return result;
    }
    public static Projection validateRoot(Root root) {
        Objects.requireNonNull(root);
        // A constructed internal value is checked against the same boundary contract.
        encodeRoot(root);
        validateReferences(root.original_roster(),"original_roster");
        validateReferences(root.removal_queue(),"removal_queue");
        if(root.occurrences().size()!=root.original_roster().occurrences().size()) throw bad("admission","original roster coverage changed");
        for(int i=0;i<root.occurrences().size();i++) {
            RosterAdmissionOccurrence row=root.occurrences().get(i);
            RawReferenceOccurrence original=root.original_roster().occurrences().get(i);
            if(row.native_index()!=original.native_index() || !Objects.equals(row.raw_full_id_u32(),original.raw_full_id_u32())) throw bad("admission","original roster filtered or relabeled");
            String prefix="occurrences["+row.native_index()+"]";
            validateResolution(row.original_army_resolution(),row.raw_full_id_u32(),prefix+".original_army_resolution");
            AdmissionGate g=row.gate();
            validateResolution(g.original_unit_resolution(),g.original_army_unit_id_raw_u32(),prefix+".gate.original_unit_resolution");
            validateResolution(g.associated_army_resolution(),g.associated_army_id_raw_u32(),prefix+".gate.associated_army_resolution");
            validateResolution(g.associated_unit_resolution(),g.associated_army_unit_id_raw_u32(),prefix+".gate.associated_unit_resolution");
            validateResolution(g.associated_character_resolution(),g.associated_unit_character_id_raw_u32(),prefix+".gate.associated_character_resolution");
            validateResolution(g.province_character_resolution(),g.province_character_id_73c_raw_u32(),prefix+".gate.province_character_resolution");
            validateResolution(g.selected_war_resolution(),g.relation_lookup().selected_relationship_war_id_raw_u32(),prefix+".gate.selected_war_resolution");
            validateOrdered(g.relation_lookup().probes(),prefix+".gate.relation_lookup.probes",null);
            for(RelationProbe probe:g.relation_lookup().probes()) if(!Set.of("pivot","candidate").contains(probe.kind())) throw bad(prefix,"invalid relation probe kind");
            String relationSelection=g.relation_lookup().selection();
            if(relationSelection!=null && !Set.of("pair_map","native_fallback").contains(relationSelection)) throw bad(prefix,"invalid relation selection");
            validateResolution(row.caller_unit_resolution(),row.caller_army_unit_id_raw_u32(),prefix+".caller_unit_resolution");
            validateResolution(row.siege_resolution(),row.caller_province_siege_id_raw_u32(),prefix+".siege_resolution");
            validateOrdered(row.pending_selection().probes(),prefix+".pending_selection.probes",null);
            validateReferences(row.pending_selection().suppression_references(),prefix+".pending_selection.suppression_references");
            validateReferences(row.original_arrg_references(),prefix+".original_arrg_references");
            validateOrdered(row.arrg_occurrences(),prefix+".arrg_occurrences",row.original_arrg_references().count_raw_i32());
        }
        Projection projection=project(root,0);
        validateDeclared(root,projection);
        return projection;
    }
    public sealed interface SourceValue permits NumberValue,FlagValue,TextValue { }
    public record NumberValue(long value) implements SourceValue { }
    public record FlagValue(boolean value) implements SourceValue { }
    public record TextValue(String value) implements SourceValue { public TextValue { Objects.requireNonNull(value); } }
    public enum GateField {
        READY("ready"),
        VERDICT("verdict"),
        ORIGINAL_ARMY_UNIT_ID_RAW_U32("original_army_unit_id_raw_u32"),
        ORIGINAL_UNIT_KIND_RAW_U32("original_unit_kind_raw_u32"),
        ORIGINAL_UNIT_PROVINCE_IDENTITY("original_unit_province_identity"),
        ORIGINAL_UNIT_PROVINCE_PRESENT("original_unit_province_present"),
        ORIGINAL_PROVINCE_IDENTITY_RAW_U32("original_province_identity_raw_u32"),
        SELECTED_PROVINCE_COMPARISON_IDENTITY("selected_province_comparison_identity"),
        SELECTED_PROVINCE_COMPARISON_IDENTITY_RAW_U32("selected_province_comparison_identity_raw_u32"),
        ORIGINAL_UNIT_COUNTER_170_RAW_I32("original_unit_counter_170_raw_i32"),
        ASSOCIATED_ARMY_ID_RAW_U32("associated_army_id_raw_u32"),
        PROVINCE_SIEGE_ID_RAW_U32("province_siege_id_raw_u32"),
        PROVINCE_COUNTER_850_RAW_I32("province_counter_850_raw_i32"),
        ASSOCIATED_ARMY_FLAG_1D4_RAW_U8("associated_army_flag_1d4_raw_u8"),
        ASSOCIATED_ARMY_FLAG_1EC_RAW_U8("associated_army_flag_1ec_raw_u8"),
        ASSOCIATED_ARMY_UNIT_ID_RAW_U32("associated_army_unit_id_raw_u32"),
        ASSOCIATED_UNIT_CHARACTER_ID_RAW_U32("associated_unit_character_id_raw_u32"),
        PROVINCE_CHARACTER_ID_73C_RAW_U32("province_character_id_73c_raw_u32"),
        NATIVE_2C099F0_CHARACTER_IDENTITY("native_2c099f0_character_identity"),
        NATIVE_2C099F0_PROVINCE_IDENTITY("native_2c099f0_province_identity"),
        NATIVE_2C099F0_THIRD_ARGUMENT_IS_NULL("native_2c099f0_third_argument_is_null"),
        NATIVE_2C099F0_RETURNED("native_2c099f0_returned"),
        NATIVE_2C099F0_CLASSIFICATION_RAW_I32("native_2c099f0_classification_raw_i32"),
        ASSOCIATED_CHARACTER_FULL_ID_RAW_U32("associated_character_full_id_raw_u32"),
        PROVINCE_CHARACTER_FULL_ID_RAW_U32("province_character_full_id_raw_u32"),
        SELECTED_WAR_ENDED_358_RAW_U8("selected_war_ended_358_raw_u8");
        private final String wire; GateField(String wire) {this.wire=wire;} public String wire(){return wire;}
    }
    public record GateSource(GateField field,SourceValue value) { public GateSource {Objects.requireNonNull(field);Objects.requireNonNull(value);} }
    public record DerivedRelation(boolean ready,String unavailable_reason,Long candidate_slot_index_i64,String selection,
            String selected_relationship_identity,Long selected_relationship_war_id_raw_u32,List<RelationProbe> probe_ledger) {
        public DerivedRelation {probe_ledger=List.copyOf(probe_ledger);}
    }
    public record DerivedGate(boolean ready,Boolean verdict,String unavailable_reason,DerivedRelation relation_lookup,List<GateSource> source_ledger) {
        public DerivedGate {Objects.requireNonNull(relation_lookup);source_ledger=List.copyOf(source_ledger);}
    }
    public record DerivedPending(boolean ready,String unavailable_reason,Long target_army_full_id_u32,Long hash_raw_u32,
            Long home_slot_i64,Long selected_physical_slot_i64,Boolean selected_is_end_marker,Integer selected_control_raw_u8,
            List<PendingProbe> probe_ledger) {
        public DerivedPending {probe_ledger=List.copyOf(probe_ledger);}
    }
    public record DerivedArRg(int native_index,Long raw_full_id_u32,boolean ready,Boolean pending_contains,Boolean append,String unavailable_reason) implements Indexed { }
    public sealed interface OccurrenceSource permits SourceBoundSkip,VerifiedConditionalArmyAppend { }
    public record SourceBoundSkip(String reason) implements OccurrenceSource {public SourceBoundSkip {Objects.requireNonNull(reason);}}
    public record VerifiedConditionalArmyAppend(long siege_full_id_u32,long army_full_id_u32) implements OccurrenceSource { }
    public record DerivedOccurrence(int native_index,Long raw_full_id_u32,boolean ready,String unavailable_reason,
            boolean original_army_selection_ready,DerivedGate gate,Boolean removal_contains_selected_army,
            boolean army_append_ready,Boolean army_append,Long army_append_siege_full_id_u32,Long army_append_full_id_u32,
            DerivedPending pending_selection,List<DerivedArRg> arrg_occurrences,boolean arrg_append_ready,
            List<Long> arrg_append_full_ids_u32,List<OccurrenceSource> source_ledger) implements Indexed {
        public DerivedOccurrence {Objects.requireNonNull(gate);Objects.requireNonNull(pending_selection);arrg_occurrences=List.copyOf(arrg_occurrences);if(arrg_append_full_ids_u32!=null)arrg_append_full_ids_u32=List.copyOf(arrg_append_full_ids_u32);source_ledger=List.copyOf(source_ledger);}
    }
    public record RequestProvenance(int original_roster_native_index,Long requested_army_full_id_u32,
            OperandResolution original_army_resolution,OperandResolution siege_resolution,List<GateSource> gate_source_ledger,
            DerivedRelation relation_lookup,DerivedPending pending_selection,List<Integer> admitted_original_arrg_native_indices) {
        public RequestProvenance {Objects.requireNonNull(original_army_resolution);Objects.requireNonNull(siege_resolution);gate_source_ledger=List.copyOf(gate_source_ledger);Objects.requireNonNull(relation_lookup);Objects.requireNonNull(pending_selection);admitted_original_arrg_native_indices=List.copyOf(admitted_original_arrg_native_indices);}
    }
    public record PlacementRequest(long siege_full_id_u32,long army_full_id_u32,List<Long> arrg_full_ids_u32,RequestProvenance source_provenance) {
        public PlacementRequest {require(siege_full_id_u32>=0 && siege_full_id_u32<=0xFFFFFFFFL && army_full_id_u32>=0 && army_full_id_u32<=0xFFFFFFFFL,"full uint32 request IDs required");arrg_full_ids_u32=List.copyOf(arrg_full_ids_u32);for(Long id:arrg_full_ids_u32)require(id!=null && id>=0 && id<=0xFFFFFFFFL,"full uint32 ArRg required");Objects.requireNonNull(source_provenance);}
    }
    public record VerifiedArmyAppend(int native_index,Long siege_full_id_u32,Long army_full_id_u32,boolean arrg_append_ready) { }
    public sealed interface MissingInput permits MissingField,OccurrenceMissing { }
    public record MissingField(String field) implements MissingInput {public MissingField {Objects.requireNonNull(field);}}
    public record OccurrenceMissing(int native_index,String reason) implements MissingInput {public OccurrenceMissing {Objects.requireNonNull(reason);}}
    public record Projection(Status status,boolean ready,String unavailable_reason,boolean raw_roster_references_ready,
            boolean removal_queue_references_ready,boolean original_army_selections_ready,boolean army_appends_ready,boolean arrg_appends_ready,
            Root observed_current_roster_admission,RawReferences original_roster,RawReferences removal_queue,List<DerivedOccurrence> occurrences,
            List<RawReferenceOccurrence> raw_roster_occurrences,Integer raw_roster_reference_count,List<PlacementRequest> request_prefix,
            List<PlacementRequest> independently_derived_requests,List<VerifiedArmyAppend> verified_army_append_facts,
            Integer first_partial_native_index,List<MissingInput> missing_inputs) {
        public Projection {Objects.requireNonNull(status);occurrences=List.copyOf(occurrences);raw_roster_occurrences=List.copyOf(raw_roster_occurrences);request_prefix=List.copyOf(request_prefix);independently_derived_requests=List.copyOf(independently_derived_requests);verified_army_append_facts=List.copyOf(verified_army_append_facts);missing_inputs=List.copyOf(missing_inputs);}
        public boolean conditional_admission_ready(){return ready;}
        public boolean current_conditional_admission_ready(){return ready;}
        public boolean raw_roster_ready(){return raw_roster_references_ready;}
    }
    /** Whole original roster is deliberately independent of the queried ArmyStrength scope. */
    public static Projection project(Root root,int queriedArmy) {return ArmyRosterDerivation.project(root);}
    public static List<PlacementRequest> requests(Projection projection,boolean prefixOnly) {
        if(!projection.conditional_admission_ready() && !prefixOnly) throw bad("admission","incomplete input requires explicit prefixOnly");
        return projection.request_prefix();
    }
    private static void same(boolean actual,boolean expected,String field) {if(actual!=expected)throw bad(field,"disagrees with actual source inputs");}
    private static void same(Object actual,Object expected,String field) {if(!Objects.equals(actual,expected))throw bad(field,"disagrees with actual source inputs");}
    public static void validateDeclared(Root raw,Projection p) {
        same(raw.ready(),p.ready(),"admission.ready");
        same(raw.raw_roster_references_ready(),p.raw_roster_references_ready(),"admission.raw_roster_references_ready");
        same(raw.original_army_selections_ready(),p.original_army_selections_ready(),"admission.original_army_selections_ready");
        same(raw.army_appends_ready(),p.army_appends_ready(),"admission.army_appends_ready");
        same(raw.arrg_appends_ready(),p.arrg_appends_ready(),"admission.arrg_appends_ready");
        same(raw.conditional_admission_ready(),p.ready(),"admission.conditional_admission_ready");
        same(raw.original_roster().ready(),p.raw_roster_references_ready(),"original_roster.ready");
        same(raw.original_roster().references_ready(),p.raw_roster_references_ready(),"original_roster.references_ready");
        require(raw.occurrences().size()==p.occurrences().size(),"derived occurrence coverage changed");
        for(int i=0;i<raw.occurrences().size();i++) {
            RosterAdmissionOccurrence a=raw.occurrences().get(i); DerivedOccurrence b=p.occurrences().get(i);
            same(a.ready(),b.ready(),"occurrence.ready");same(a.removal_contains_selected_army(),b.removal_contains_selected_army(),"occurrence.removal_contains_selected_army");
            same(a.army_append_ready(),b.army_append_ready(),"occurrence.army_append_ready");same(a.army_append(),b.army_append(),"occurrence.army_append");
            same(a.army_append_siege_full_id_u32(),b.army_append_siege_full_id_u32(),"occurrence.army_append_siege_full_id_u32");same(a.army_append_full_id_u32(),b.army_append_full_id_u32(),"occurrence.army_append_full_id_u32");
            same(a.arrg_append_ready(),b.arrg_append_ready(),"occurrence.arrg_append_ready");same(a.arrg_append_full_ids_u32(),b.arrg_append_full_ids_u32(),"occurrence.arrg_append_full_ids_u32");
            same(a.gate().ready(),b.gate().ready(),"gate.ready");same(a.gate().verdict(),b.gate().verdict(),"gate.verdict");
            same(a.gate().relation_lookup().ready(),b.gate().relation_lookup().ready(),"relation.ready");same(a.gate().relation_lookup().candidate_slot_index_i64(),b.gate().relation_lookup().candidate_slot_index_i64(),"relation.candidate_slot_index_i64");same(a.gate().relation_lookup().selection(),b.gate().relation_lookup().selection(),"relation.selection");
            same(a.pending_selection().ready(),b.pending_selection().ready(),"pending.ready");same(a.pending_selection().selected_physical_slot_i64(),b.pending_selection().selected_physical_slot_i64(),"pending.selected_physical_slot_i64");same(a.pending_selection().selected_is_end_marker(),b.pending_selection().selected_is_end_marker(),"pending.selected_is_end_marker");same(a.pending_selection().selected_control_raw_u8(),b.pending_selection().selected_control_raw_u8(),"pending.selected_control_raw_u8");
            require(a.arrg_occurrences().size()==b.arrg_occurrences().size(),"ArRg occurrence demand coverage disagrees");
            for(int j=0;j<a.arrg_occurrences().size();j++){
                ArRgAdmissionOccurrence x=a.arrg_occurrences().get(j);DerivedArRg y=b.arrg_occurrences().get(j);
                same(x.native_index(),y.native_index(),"arrg.native_index");same(x.raw_full_id_u32(),y.raw_full_id_u32(),"arrg.raw_full_id_u32");same(x.ready(),y.ready(),"arrg.ready");same(x.pending_contains(),y.pending_contains(),"arrg.pending_contains");same(x.append(),y.append(),"arrg.append");
            }
        }
    }

    private static ObjectNode object(){return J.objectNode();}
    private static ObjectNode encodeRelation(DerivedRelation v){
        ObjectNode o=object();o.put("ready",v.ready());o.set("unavailable_reason",node(v.unavailable_reason()));o.set("candidate_slot_index_i64",node(v.candidate_slot_index_i64()));o.set("selection",node(v.selection()));o.set("selected_relationship_identity",node(v.selected_relationship_identity()));o.set("selected_relationship_war_id_raw_u32",node(v.selected_relationship_war_id_raw_u32()));o.set("probe_ledger",list(v.probe_ledger(),ArmyStrengthsRosterContract::encodeRelationProbe));return o;
    }
    private static ObjectNode encodeGateSource(GateSource value){
        ObjectNode o=object();o.put("field",value.field().wire());
        JsonNode raw=switch(value.value()){
            case NumberValue n -> node(n.value());
            case FlagValue b -> node(b.value());
            case TextValue t -> node(t.value());
        };
        o.set("value",raw);return o;
    }
    private static ObjectNode encodeGate(DerivedGate v){
        ObjectNode o=object();o.put("ready",v.ready());o.set("verdict",node(v.verdict()));o.set("unavailable_reason",node(v.unavailable_reason()));o.set("relation_lookup",encodeRelation(v.relation_lookup()));o.set("source_ledger",list(v.source_ledger(),ArmyStrengthsRosterContract::encodeGateSource));return o;
    }
    private static ObjectNode encodePending(DerivedPending v){
        ObjectNode o=object();o.put("ready",v.ready());o.set("unavailable_reason",node(v.unavailable_reason()));o.set("target_army_full_id_u32",node(v.target_army_full_id_u32()));o.set("hash_raw_u32",node(v.hash_raw_u32()));o.set("home_slot_i64",node(v.home_slot_i64()));o.set("selected_physical_slot_i64",node(v.selected_physical_slot_i64()));o.set("selected_is_end_marker",node(v.selected_is_end_marker()));o.set("selected_control_raw_u8",node(v.selected_control_raw_u8()));o.set("probe_ledger",list(v.probe_ledger(),ArmyStrengthsRosterContract::encodePendingProbe));return o;
    }
    private static ObjectNode encodeDerivedArRg(DerivedArRg v){
        ObjectNode o=object();o.put("native_index",v.native_index());o.set("raw_full_id_u32",node(v.raw_full_id_u32()));o.put("ready",v.ready());o.set("pending_contains",node(v.pending_contains()));o.set("append",node(v.append()));o.set("unavailable_reason",node(v.unavailable_reason()));return o;
    }
    private static ObjectNode encodeOccurrenceSource(OccurrenceSource value){
        ObjectNode o=object();
        switch(value){
            case SourceBoundSkip skip -> {o.put("stage","source_bound_skip");o.put("reason",skip.reason());}
            case VerifiedConditionalArmyAppend append -> {o.put("stage","verified_conditional_army_append");o.put("siege_full_id_u32",append.siege_full_id_u32());o.put("army_full_id_u32",append.army_full_id_u32());o.put("native_append_executed",false);}
        }return o;
    }
    private static ObjectNode encodeOccurrence(DerivedOccurrence v){
        ObjectNode o=object();o.put("native_index",v.native_index());o.set("raw_full_id_u32",node(v.raw_full_id_u32()));o.put("ready",v.ready());o.set("unavailable_reason",node(v.unavailable_reason()));o.put("original_army_selection_ready",v.original_army_selection_ready());o.set("gate",encodeGate(v.gate()));o.set("removal_contains_selected_army",node(v.removal_contains_selected_army()));o.put("army_append_ready",v.army_append_ready());o.set("army_append",node(v.army_append()));o.set("army_append_siege_full_id_u32",node(v.army_append_siege_full_id_u32()));o.set("army_append_full_id_u32",node(v.army_append_full_id_u32()));o.set("pending_selection",encodePending(v.pending_selection()));o.set("arrg_occurrences",list(v.arrg_occurrences(),ArmyStrengthsRosterContract::encodeDerivedArRg));o.put("arrg_append_ready",v.arrg_append_ready());o.set("arrg_append_full_ids_u32",list(v.arrg_append_full_ids_u32(),ArmyStrengthsRosterContract::node));o.set("source_ledger",list(v.source_ledger(),ArmyStrengthsRosterContract::encodeOccurrenceSource));return o;
    }
    public static ObjectNode encodeRequest(PlacementRequest value){
        ObjectNode o=object();o.put("siege_full_id_u32",value.siege_full_id_u32());o.put("army_full_id_u32",value.army_full_id_u32());o.set("arrg_full_ids_u32",list(value.arrg_full_ids_u32(),ArmyStrengthsRosterContract::node));
        RequestProvenance v=value.source_provenance();ObjectNode p=object();p.put("source","observed_current_standalone_2a99b40_admission");p.put("original_roster_native_index",v.original_roster_native_index());p.set("requested_army_full_id_u32",node(v.requested_army_full_id_u32()));p.set("original_army_resolution",encodeOperandResolution(v.original_army_resolution()));p.set("siege_resolution",encodeOperandResolution(v.siege_resolution()));p.set("gate_source_ledger",list(v.gate_source_ledger(),ArmyStrengthsRosterContract::encodeGateSource));p.set("relation_lookup",encodeRelation(v.relation_lookup()));p.set("pending_selection",encodePending(v.pending_selection()));p.set("admitted_original_arrg_native_indices",list(v.admitted_original_arrg_native_indices(),ArmyStrengthsRosterContract::node));p.put("earlier_callbacks_replayed",false);p.put("actual_next_callback_ready",false);o.set("source_provenance",p);return o;
    }
    private static ObjectNode encodeFact(VerifiedArmyAppend v){
        ObjectNode o=object();o.put("native_index",v.native_index());o.set("siege_full_id_u32",node(v.siege_full_id_u32()));o.set("army_full_id_u32",node(v.army_full_id_u32()));o.put("arrg_append_ready",v.arrg_append_ready());o.put("native_append_executed",false);return o;
    }
    private static JsonNode encodeMissing(MissingInput v){
        return switch(v){
            case MissingField field -> node(field.field());
            case OccurrenceMissing missing -> {ObjectNode o=object();o.put("native_index",missing.native_index());o.put("reason",missing.reason());yield o;}
        };
    }
    public static ObjectNode encodeProjection(Projection p){
        Objects.requireNonNull(p);ObjectNode o=object();
        o.put("schema_version",1);o.put("source","source_bound_current_standalone_2a99b40_admission");o.put("stage","observed_current_standalone_2a99b40_admission");o.put("source_contract_game_version","1.20.0.3");
        o.put("status",p.status().wire());o.put("ready",p.ready());o.set("unavailable_reason",node(p.unavailable_reason()));o.put("raw_roster_references_ready",p.raw_roster_references_ready());o.put("raw_roster_ready",p.raw_roster_references_ready());o.put("removal_queue_references_ready",p.removal_queue_references_ready());o.put("original_army_selections_ready",p.original_army_selections_ready());o.put("army_appends_ready",p.army_appends_ready());o.put("arrg_appends_ready",p.arrg_appends_ready());o.put("conditional_admission_ready",p.ready());o.put("current_conditional_admission_ready",p.ready());
        o.put("actual_next_callback_ready",false);o.put("actual_tomorrow_roster_ready",false);o.put("full_future_table_placement_ready",false);o.put("full_daily_assault_ready",false);o.put("full_daily",false);o.put("full_monthly",false);o.put("native_calls_executed",0);o.put("native_writes_executed",0);o.put("earlier_dispatch_replayed",false);o.put("earlier_callbacks_replayed",false);
        o.set("observed_current_roster_admission",p.observed_current_roster_admission()==null?NullNode.instance:encodeRoot(p.observed_current_roster_admission()));o.set("original_roster",p.original_roster()==null?NullNode.instance:encodeRawReferences(p.original_roster()));o.set("removal_queue",p.removal_queue()==null?NullNode.instance:encodeRawReferences(p.removal_queue()));o.set("occurrences",list(p.occurrences(),ArmyStrengthsRosterContract::encodeOccurrence));o.set("raw_roster_occurrences",list(p.raw_roster_occurrences(),ArmyStrengthsRosterContract::encodeRawReferenceOccurrence));o.set("raw_roster_reference_count",node(p.raw_roster_reference_count()));o.set("request_prefix",list(p.request_prefix(),ArmyStrengthsRosterContract::encodeRequest));o.set("independently_derived_requests",list(p.independently_derived_requests(),ArmyStrengthsRosterContract::encodeRequest));o.set("verified_army_append_facts",list(p.verified_army_append_facts(),ArmyStrengthsRosterContract::encodeFact));o.set("first_partial_native_index",node(p.first_partial_native_index()));o.set("missing_inputs",list(p.missing_inputs(),ArmyStrengthsRosterContract::encodeMissing));return o;
    }
}

