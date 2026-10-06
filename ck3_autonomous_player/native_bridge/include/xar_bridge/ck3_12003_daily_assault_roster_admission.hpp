#pragma once

#include "xar_bridge/army_daily_assault_active_table_collector_v1.inc.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xar::ck3_12003 {
struct CurrentDailyAssaultRosterAdmissionBindings12003 {
  bool enabled = false;
  const void *game_state_slot = nullptr;
  const void *army_registry_slot = nullptr, *army_fallback_slot = nullptr;
  const void *unit_registry_slot = nullptr, *unit_fallback_slot = nullptr;
  const void *character_registry_slot = nullptr, *character_fallback_slot = nullptr;
  const void *war_registry_slot = nullptr, *war_fallback_slot = nullptr;
  const void *siege_registry_slot = nullptr, *siege_fallback_slot = nullptr;
  const void *province_fallback_slot = nullptr, *relationship_fallback_slot = nullptr;
  bool (*read_memory)(void *, const void *, void *, std::size_t) noexcept = nullptr;
  void *read_context = nullptr;
};
inline CurrentDailyAssaultRosterAdmissionBindings12003 BindCurrentDailyAssaultRosterAdmission12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentDailyAssaultRosterAdmissionBindings12003 out{};
  if (!base || sha != kExecutableSha256) return out;
  const auto address = [base](std::uintptr_t rva) { return reinterpret_cast<const void *>(base + rva); };
  out.enabled = true; out.game_state_slot = address(0x5C68C50);
  out.army_registry_slot = address(0x5D1DE48); out.army_fallback_slot = address(0x5D1DE50);
  out.unit_registry_slot = address(0x5D1E380); out.unit_fallback_slot = address(0x5D1E378);
  out.character_registry_slot = address(0x5C67568); out.character_fallback_slot = address(0x5C67570);
  out.war_registry_slot = address(0x5D1DE58); out.war_fallback_slot = address(0x5D1DE40);
  out.siege_registry_slot = address(0x5D1EC88); out.siege_fallback_slot = address(0x5D1EC60);
  out.province_fallback_slot = address(0x5D1E390); out.relationship_fallback_slot = address(0x5D27B70);
  return out;
}
namespace daily_assault_roster_detail {
using Bindings = CurrentDailyAssaultRosterAdmissionBindings12003;
inline const void *At(const void *object, std::size_t offset = 0) {
  return object ? reinterpret_cast<const void *>(reinterpret_cast<std::uintptr_t>(object) + offset) : nullptr;
}
inline const void *Record(const void *data, std::int64_t index, std::size_t stride) {
  return At(data, static_cast<std::uintptr_t>(index) * stride);
}
template <typename T> inline std::optional<T> Read(const Bindings &b, const void *object, std::size_t offset = 0) {
  CurrentDailyAssaultTableBindings12003 common{};
  common.read_memory = b.read_memory; common.read_context = b.read_context;
  return daily_assault_table_detail::Read<T>(common, object, offset);
}
inline std::string Identity(const void *object) { return daily_assault_table_detail::Identity(object); }
template <typename T> inline void Finish(T &out, bool complete) {
  out.ready = complete; out.status = complete ? "available" : "partial";
  if (complete) out.unavailable_reason.clear();
  else if (out.unavailable_reason.empty() || out.unavailable_reason == "not_demanded")
    out.unavailable_reason = "daily_assault_roster_source_inputs_incomplete";
}
struct Resolved {
  const void *object = nullptr;
  game::ArmyDailyAssaultOperandResolutionV1 observation{};
};
inline Resolved Resolve(const Bindings &b, const void *registry, const void *fallback,
    const std::optional<std::uint32_t> &requested, std::size_t full_offset) {
  Resolved result{}; auto &out = result.observation; out.requested_full_id_u32 = requested;
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason; Finish(out, false); return result;
  };
  if (!requested) return fail("daily_assault_roster_reference_full_id_unavailable");
  const auto store = Read<const void *>(b, registry);
  if (!store) return fail("daily_assault_roster_registry_slot_unavailable");
  out.registry_loaded = *store != nullptr;
  if (*store) {
    out.registry_capacity_u32 = Read<std::uint32_t>(b, *store, 0x2C);
    out.registry_index_u32 = *requested & 0xFFFFFFU;
    if (!out.registry_capacity_u32) return fail("daily_assault_roster_registry_capacity_unavailable");
    if (*out.registry_index_u32 < *out.registry_capacity_u32) {
      const auto table = Read<const void *>(b, *store, 0x20);
      if (!table || !*table) return fail("daily_assault_roster_registry_table_unavailable");
      const auto candidate = Read<const void *>(b, *table, static_cast<std::size_t>(*out.registry_index_u32) * 16 + 8);
      if (!candidate) return fail("daily_assault_roster_registry_object_unavailable");
      if (*candidate) {
        out.indexed_identity = Identity(*candidate);
        out.indexed_full_id_u32 = Read<std::uint32_t>(b, *candidate, full_offset);
        if (!out.indexed_full_id_u32) return fail("daily_assault_roster_registry_full_id_unavailable");
        if (*out.indexed_full_id_u32 == *requested) {
          out.selection = "registry_full_id"; out.used_fallback = false;
          out.object_identity = out.indexed_identity; out.selected_full_id_u32 = out.indexed_full_id_u32;
          out.selected_object_ready = true; out.selected_full_id_read_ready = true;
          result.object = *candidate; Finish(out, true); return result;
        }
      }
    }
  }
  const auto selected = Read<const void *>(b, fallback);
  if (!selected) return fail("daily_assault_roster_fallback_slot_unavailable");
  out.selection = "native_fallback"; out.used_fallback = true;
  if (!*selected) return fail("daily_assault_roster_fallback_null");
  result.object = *selected; out.object_identity = Identity(*selected); out.selected_object_ready = true;
  out.selected_full_id_u32 = Read<std::uint32_t>(b, *selected, full_offset);
  out.selected_full_id_read_ready = out.selected_full_id_u32.has_value();
  if (!out.selected_full_id_u32) return fail("daily_assault_roster_fallback_full_id_metadata_unavailable");
  Finish(out, true); return result;
}
inline game::ArmyDailyAssaultRawReferencesV1 References(const Bindings &b, const void *header) {
  game::ArmyDailyAssaultRawReferencesV1 out{};
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  out.count_raw_i32 = Read<std::int32_t>(b, header, 0xC);
  if (!out.count_raw_i32) return fail("daily_assault_roster_vector_count_unavailable");
  if (*out.count_raw_i32 < 0) return fail("daily_assault_roster_vector_negative_count");
  if (*out.count_raw_i32 == 0) { out.references_ready = true; Finish(out, true); return out; }
  const auto data = Read<const void *>(b, header);
  if (data) { out.data_present = *data != nullptr; out.data_identity = Identity(*data); }
  if (!data || !*data) return fail("daily_assault_roster_vector_data_unavailable");
  bool complete = true;
  for (std::int32_t i = 0; i < *out.count_raw_i32; ++i) {
    game::ArmyDailyAssaultRawReferenceOccurrenceV1 row{}; row.native_index = i;
    row.raw_full_id_u32 = Read<std::uint32_t>(b, *data, static_cast<std::size_t>(i) * 4);
    if (!row.raw_full_id_u32) {
      row.unavailable_reason = "daily_assault_roster_reference_full_id_unavailable"; complete = false;
      out.unavailable_reason = row.unavailable_reason;
    }
    Finish(row, row.raw_full_id_u32.has_value()); out.occurrences.push_back(std::move(row));
  }
  out.observed_occurrence_count = static_cast<std::int32_t>(out.occurrences.size());
  out.references_ready = complete; Finish(out, complete); return out;
}
inline std::optional<bool> Contains(const game::ArmyDailyAssaultRawReferencesV1 &refs, std::uint32_t target) {
  for (const auto &row : refs.occurrences) {
    if (!row.raw_full_id_u32) return std::nullopt;
    if (*row.raw_full_id_u32 == target) return true;
  }
  return refs.references_ready ? std::optional<bool>{false} : std::nullopt;
}
inline game::ArmyDailyAssaultRawReferencesV1 RemovalReferences(const Bindings &b, const void *manager,
    const game::ArmyDailyQueueInputsV1 *existing_queue) {
  game::ArmyDailyAssaultRawReferencesV1 out{};
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  out.count_raw_i32 = Read<std::int32_t>(b, manager, 0x74);
  if (!out.count_raw_i32) return fail("daily_assault_roster_removal_count_unavailable");
  if (*out.count_raw_i32 < 0) return fail("daily_assault_roster_removal_negative_count");
  if (*out.count_raw_i32 == 0) { out.references_ready = true; Finish(out, true); return out; }
  const auto data = Read<const void *>(b, manager, 0x68);
  if (data) { out.data_identity = Identity(*data); out.data_present = *data != nullptr; }
  if (existing_queue && existing_queue->manager_army_id_list_2a5a8 &&
      existing_queue->manager_army_id_list_2a5a8->size() == static_cast<std::size_t>(*out.count_raw_i32)) {
    const auto &ids = *existing_queue->manager_army_id_list_2a5a8;
    for (std::size_t i = 0; i < ids.size(); ++i) {
      game::ArmyDailyAssaultRawReferenceOccurrenceV1 row{};
      row.native_index = static_cast<std::int32_t>(i); row.raw_full_id_u32 = static_cast<std::uint32_t>(ids[i]);
      Finish(row, true); out.occurrences.push_back(std::move(row));
    }
    out.observed_occurrence_count = static_cast<std::int32_t>(out.occurrences.size());
    out.references_ready = true; Finish(out, true); return out;
  }
  if (!data || !*data) return fail("daily_assault_roster_removal_data_unavailable");
  bool complete = true;
  for (std::int32_t i = 0; i < *out.count_raw_i32; ++i) {
    game::ArmyDailyAssaultRawReferenceOccurrenceV1 row{}; row.native_index = i;
    row.raw_full_id_u32 = Read<std::uint32_t>(b, *data, static_cast<std::size_t>(i) * 4);
    if (!row.raw_full_id_u32) {
      row.unavailable_reason = "daily_assault_roster_reference_full_id_unavailable"; complete = false;
      out.unavailable_reason = row.unavailable_reason;
    }
    Finish(row, row.raw_full_id_u32.has_value()); out.occurrences.push_back(std::move(row));
  }
  out.observed_occurrence_count = static_cast<std::int32_t>(out.occurrences.size());
  out.references_ready = complete; Finish(out, complete); return out;
}
inline game::ArmyDailyAssaultRelationLookupV1 Relation(const Bindings &b, const void *first,
    const std::optional<std::uint32_t> &target) {
  game::ArmyDailyAssaultRelationLookupV1 out{}; out.target_character_full_id_raw_u32 = target;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  const auto component = Read<const void *>(b, first, 0x1B0);
  if (component) { out.component_present = *component != nullptr; out.component_identity = Identity(*component); }
  if (!component) return fail("daily_assault_roster_relation_component_unavailable");
  const void *selected = nullptr;
  const auto use_default = [&]() -> bool {
    out.selection = "native_fallback";
    const auto value = Read<const void *>(b, b.relationship_fallback_slot);
    if (!value) { out.unavailable_reason = "daily_assault_roster_default_relationship_unavailable"; return false; }
    out.default_relationship_identity = Identity(*value); out.default_relationship_present = *value != nullptr;
    selected = *value; return true;
  };
  if (!*component) {
    if (!use_default()) { Finish(out, false); return out; }
  } else {
    out.table_count_raw_i32 = Read<std::int32_t>(b, *component, 0x2C);
    if (!out.table_count_raw_i32) return fail("daily_assault_roster_relation_count_unavailable");
    if (*out.table_count_raw_i32 < 0) return fail("daily_assault_roster_relation_negative_count_precondition_unclosed");
    if (*out.table_count_raw_i32 == 0) {
      out.candidate_slot_index_i64 = 0;
      if (!use_default()) { Finish(out, false); return out; }
    } else {
      const auto data = Read<const void *>(b, *component, 0x20);
      if (data) { out.table_data_present = *data != nullptr; out.table_data_identity = Identity(*data); }
      if (!data || !*data) return fail("daily_assault_roster_relation_data_unavailable");
      if (!target) return fail("daily_assault_roster_relation_target_full_id_unavailable");
      std::int64_t base = 0, candidate = 0, count = *out.table_count_raw_i32;
      const auto probe = [&](std::int64_t slot, const char *kind) {
        game::ArmyDailyAssaultRelationProbeV1 row{};
        row.native_index = static_cast<std::int32_t>(out.probes.size()); row.kind = kind; row.slot_index_i64 = slot;
        row.key_character_id_raw_u32 = Read<std::uint32_t>(b, Record(*data, slot, 16));
        const auto key = row.key_character_id_raw_u32; out.probes.push_back(std::move(row)); return key;
      };
      while (count > 0) {
        const std::int64_t half = count >> 1, remaining = count - half;
        const auto key = probe(base + half, "pivot");
        if (!key) return fail("daily_assault_roster_relation_probe_key_unavailable");
        if (*key < *target) base += remaining;
        candidate = base; count = half;
        if (half == 0) break;
      }
      out.candidate_slot_index_i64 = candidate;
      if (candidate == *out.table_count_raw_i32) {
        if (!use_default()) { Finish(out, false); return out; }
      } else {
        const auto key = probe(candidate, "candidate");
        if (!key) return fail("daily_assault_roster_relation_candidate_key_unavailable");
        if (*target < *key) {
          if (!use_default()) { Finish(out, false); return out; }
        } else {
          out.selection = "pair_map";
          const auto pointer = Read<const void *>(b, Record(*data, candidate, 16), 8);
          if (!pointer) return fail("daily_assault_roster_relationship_pointer_unavailable");
          selected = *pointer;
        }
      }
    }
  }
  out.selected_relationship_identity = Identity(selected); out.selected_relationship_present = selected != nullptr;
  if (!selected) return fail("daily_assault_roster_selected_relationship_native_read_precondition_unclosed");
  out.selected_relationship_war_id_raw_u32 = Read<std::uint32_t>(b, selected, 0x20);
  if (!out.selected_relationship_war_id_raw_u32) return fail("daily_assault_roster_relationship_war_id_unavailable");
  Finish(out, true); return out;
}
inline game::ArmyDailyAssaultAdmissionGateV1 Gate(const Bindings &b, const void *army) {
  game::ArmyDailyAssaultAdmissionGateV1 out{};
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  const auto verdict = [&](bool value) { out.verdict = value; Finish(out, true); return out; };
  out.original_army_unit_id_raw_u32 = Read<std::uint32_t>(b, army, 0x124);
  if (!out.original_army_unit_id_raw_u32) return fail("daily_assault_roster_original_unit_id_unavailable");
  auto unit = Resolve(b, b.unit_registry_slot, b.unit_fallback_slot, out.original_army_unit_id_raw_u32, 0x10);
  out.original_unit_resolution = unit.observation;
  if (!unit.observation.selected_object_ready) return fail("daily_assault_roster_original_unit_operand_unavailable");
  out.original_unit_kind_raw_u32 = Read<std::uint32_t>(b, unit.object, 0x18);
  if (!out.original_unit_kind_raw_u32) return fail("daily_assault_roster_original_unit_kind_unavailable");
  if (*out.original_unit_kind_raw_u32 != 0) return verdict(false);
  const auto province = Read<const void *>(b, unit.object, 0x20);
  if (province) { out.original_unit_province_identity = Identity(*province); out.original_unit_province_present = *province != nullptr; }
  if (!province) return fail("daily_assault_roster_original_province_pointer_unavailable");
  if (!*province) {
    const auto comparison = Read<const void *>(b, b.province_fallback_slot);
    if (comparison) out.selected_province_comparison_identity = Identity(*comparison);
    return fail("original_province_pointer_native_read_precondition_unclosed");
  }
  out.selected_province_comparison_identity = Identity(*province);
  out.original_province_identity_raw_u32 = Read<std::uint32_t>(b, *province, 0x10);
  out.selected_province_comparison_identity_raw_u32 = Read<std::uint32_t>(b, *province, 0x10);
  if (!out.original_province_identity_raw_u32 || !out.selected_province_comparison_identity_raw_u32)
    return fail("daily_assault_roster_province_identity_unavailable");
  if (*out.original_province_identity_raw_u32 != *out.selected_province_comparison_identity_raw_u32) return verdict(false);
  out.original_unit_counter_170_raw_i32 = Read<std::int32_t>(b, unit.object, 0x170);
  if (!out.original_unit_counter_170_raw_i32) return fail("daily_assault_roster_original_unit_counter_unavailable");
  if (*out.original_unit_counter_170_raw_i32 > 0) return verdict(false);
  out.associated_army_id_raw_u32 = Read<std::uint32_t>(b, unit.object, 0x178);
  if (!out.associated_army_id_raw_u32) return fail("daily_assault_roster_associated_army_id_unavailable");
  auto associated = Resolve(b, b.army_registry_slot, b.army_fallback_slot, out.associated_army_id_raw_u32, 0x10);
  out.associated_army_resolution = associated.observation;
  if (!associated.observation.selected_object_ready) return fail("daily_assault_roster_associated_army_operand_unavailable");
  out.province_siege_id_raw_u32 = Read<std::uint32_t>(b, *province, 0x788);
  if (!out.province_siege_id_raw_u32) return fail("daily_assault_roster_province_siege_id_unavailable");
  if (*out.province_siege_id_raw_u32 == 0xFFFFFFFFU) return verdict(false);
  out.province_counter_850_raw_i32 = Read<std::int32_t>(b, *province, 0x850);
  if (!out.province_counter_850_raw_i32) return fail("daily_assault_roster_province_counter_unavailable");
  if (*out.province_counter_850_raw_i32 <= 0) return verdict(false);
  out.associated_army_flag_1d4_raw_u8 = Read<std::uint8_t>(b, associated.object, 0x1D4);
  if (!out.associated_army_flag_1d4_raw_u8) return fail("daily_assault_roster_associated_army_flag_1d4_unavailable");
  if (*out.associated_army_flag_1d4_raw_u8 != 0) return verdict(false);
  out.associated_army_flag_1ec_raw_u8 = Read<std::uint8_t>(b, associated.object, 0x1EC);
  if (!out.associated_army_flag_1ec_raw_u8) return fail("daily_assault_roster_associated_army_flag_1ec_unavailable");
  if (*out.associated_army_flag_1ec_raw_u8 != 0) return verdict(false);
  out.associated_army_unit_id_raw_u32 = Read<std::uint32_t>(b, associated.object, 0x124);
  if (!out.associated_army_unit_id_raw_u32) return fail("daily_assault_roster_associated_unit_id_unavailable");
  auto second = Resolve(b, b.unit_registry_slot, b.unit_fallback_slot, out.associated_army_unit_id_raw_u32, 0x10);
  out.associated_unit_resolution = second.observation;
  if (!second.observation.selected_object_ready) return fail("daily_assault_roster_associated_unit_operand_unavailable");
  out.associated_unit_character_id_raw_u32 = Read<std::uint32_t>(b, second.object, 0x174);
  if (!out.associated_unit_character_id_raw_u32) return fail("daily_assault_roster_associated_character_id_unavailable");
  auto first_character = Resolve(b, b.character_registry_slot, b.character_fallback_slot, out.associated_unit_character_id_raw_u32, 0x18);
  out.associated_character_resolution = first_character.observation;
  if (!first_character.observation.selected_object_ready) return fail("daily_assault_roster_associated_character_operand_unavailable");
  out.province_character_id_73c_raw_u32 = Read<std::uint32_t>(b, *province, 0x73C);
  if (!out.province_character_id_73c_raw_u32) return fail("daily_assault_roster_province_character_id_unavailable");
  if (*out.province_character_id_73c_raw_u32 == 0xFFFFFFFFU) return fail("province_73c_requires_2c099f0_inputs");
  auto second_character = Resolve(b, b.character_registry_slot, b.character_fallback_slot, out.province_character_id_73c_raw_u32, 0x18);
  out.province_character_resolution = second_character.observation;
  if (!second_character.observation.selected_object_ready) return fail("daily_assault_roster_province_character_operand_unavailable");
  out.associated_character_full_id_raw_u32 = Read<std::uint32_t>(b, first_character.object, 0x18);
  out.province_character_full_id_raw_u32 = Read<std::uint32_t>(b, second_character.object, 0x18);
  if (!out.associated_character_full_id_raw_u32 || !out.province_character_full_id_raw_u32)
    return fail("daily_assault_roster_character_full_ids_unavailable");
  if (*out.associated_character_full_id_raw_u32 == *out.province_character_full_id_raw_u32) return verdict(false);
  out.relation_lookup = Relation(b, first_character.object, out.province_character_full_id_raw_u32);
  if (!out.relation_lookup.ready) return fail("daily_assault_roster_relation_lookup_incomplete");
  if (*out.relation_lookup.selected_relationship_war_id_raw_u32 == 0xFFFFFFFFU)
    return fail("2c09640_remaining_relation_predicates_unclosed");
  auto war = Resolve(b, b.war_registry_slot, b.war_fallback_slot, out.relation_lookup.selected_relationship_war_id_raw_u32, 8);
  out.selected_war_resolution = war.observation;
  if (!war.observation.selected_object_ready) return fail("daily_assault_roster_war_operand_unavailable");
  out.selected_war_ended_358_raw_u8 = Read<std::uint8_t>(b, war.object, 0x358);
  if (!out.selected_war_ended_358_raw_u8) return fail("daily_assault_roster_war_ended_byte_unavailable");
  if (*out.selected_war_ended_358_raw_u8 != 0) return fail("2c09640_remaining_relation_predicates_unclosed");
  return verdict(true);
}
inline std::uint32_t Hash(std::uint32_t full) {
  std::uint32_t hash = 0x811C9DC5U;
  for (std::uint32_t shift = 0; shift != 32; shift += 8) hash = (hash ^ ((full >> shift) & 0xFFU)) * 0x1000193U;
  return hash;
}
inline std::int32_t Signed(std::uint32_t raw) {
  std::int32_t value{}; std::memcpy(&value, &raw, sizeof(value)); return value;
}
struct SelectedPending { const void *record = nullptr; game::ArmyDailyAssaultPendingSelectionV1 observation{}; };
inline SelectedPending Pending(const Bindings &b, const void *manager, std::uint32_t target) {
  SelectedPending result{}; auto &out = result.observation; out.target_army_full_id_u32 = target; out.hash_raw_u32 = Hash(target);
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return result; };
  const auto entries = Read<const void *>(b, manager, 0x138);
  if (entries) { out.entries_present = *entries != nullptr; out.entries_identity = Identity(*entries); }
  out.mask_raw_i32 = Read<std::int32_t>(b, manager, 0x144);
  if (!entries || !*entries) return fail("daily_assault_roster_pending_entries_unavailable");
  if (!out.mask_raw_i32) return fail("daily_assault_roster_pending_mask_unavailable");
  std::int64_t slot = static_cast<std::int64_t>(Signed(*out.hash_raw_u32)) & static_cast<std::int64_t>(*out.mask_raw_i32);
  out.home_slot_i64 = slot; std::uint8_t distance = 1;
  for (;;) {
    game::ArmyDailyAssaultPendingProbeV1 probe{}; probe.native_index = static_cast<std::int32_t>(out.probes.size());
    probe.physical_slot_i64 = slot; probe.distance_raw_u8 = distance;
    const auto record = Record(*entries, slot, 0x28);
    probe.control_raw_u8 = Read<std::uint8_t>(b, record, 4);
    if (!probe.control_raw_u8) { out.probes.push_back(std::move(probe)); return fail("daily_assault_roster_pending_probe_control_unavailable"); }
    if (*probe.control_raw_u8 < distance) {
      out.probes.push_back(std::move(probe)); out.tail_distance_raw_u8 = Read<std::uint8_t>(b, manager, 0x148);
      if (!out.tail_distance_raw_u8) return fail("daily_assault_roster_pending_tail_unavailable");
      out.end_slot_raw_i32 = Signed(static_cast<std::uint32_t>(*out.mask_raw_i32) + *out.tail_distance_raw_u8 + 1U);
      out.selected_physical_slot_i64 = *out.end_slot_raw_i32; out.selected_is_end_marker = true;
      result.record = Record(*entries, *out.end_slot_raw_i32, 0x28); break;
    }
    probe.key_raw_full_id_u32 = Read<std::uint32_t>(b, record, 8);
    if (!probe.key_raw_full_id_u32) { out.probes.push_back(std::move(probe)); return fail("daily_assault_roster_pending_probe_key_unavailable"); }
    const bool equal = *probe.key_raw_full_id_u32 == target; out.probes.push_back(std::move(probe));
    if (equal) { out.selected_physical_slot_i64 = slot; out.selected_is_end_marker = false; result.record = record; break; }
    ++slot; distance = static_cast<std::uint8_t>(distance + 1U);
  }
  out.selected_control_raw_u8 = Read<std::uint8_t>(b, result.record, 4);
  if (!out.selected_control_raw_u8) return fail("daily_assault_roster_pending_selected_control_unavailable");
  Finish(out, true); return result;
}
inline game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 Occurrence(const Bindings &b, const void *manager,
    const game::ArmyDailyAssaultRawReferenceOccurrenceV1 &raw, const game::ArmyDailyAssaultRawReferencesV1 &removal) {
  game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 out{}; out.native_index = raw.native_index; out.raw_full_id_u32 = raw.raw_full_id_u32;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  const auto skip = [&]() {
    out.army_append_ready = true; out.army_append = false; out.arrg_append_ready = true;
    out.arrg_append_full_ids_u32 = std::vector<std::uint32_t>{}; Finish(out, true); return out;
  };
  auto army = Resolve(b, b.army_registry_slot, b.army_fallback_slot, raw.raw_full_id_u32, 0x10);
  out.original_army_resolution = army.observation;
  if (!army.observation.selected_object_ready) return fail("daily_assault_roster_original_army_operand_unavailable");
  out.gate = Gate(b, army.object);
  if (!out.gate.ready) return fail(out.gate.unavailable_reason.c_str());
  if (out.gate.verdict == false) return skip();
  out.caller_army_unit_id_raw_u32 = Read<std::uint32_t>(b, army.object, 0x124);
  if (!out.caller_army_unit_id_raw_u32) return fail("daily_assault_roster_caller_unit_id_unavailable");
  auto unit = Resolve(b, b.unit_registry_slot, b.unit_fallback_slot, out.caller_army_unit_id_raw_u32, 0x10);
  out.caller_unit_resolution = unit.observation;
  if (!unit.observation.selected_object_ready) return fail("daily_assault_roster_caller_unit_operand_unavailable");
  const auto original = Read<const void *>(b, unit.object, 0x20);
  if (!original) return fail("daily_assault_roster_caller_province_pointer_unavailable");
  const void *province = *original; out.caller_used_province_fallback = province == nullptr;
  if (!province) {
    const auto fallback = Read<const void *>(b, b.province_fallback_slot);
    if (!fallback) return fail("daily_assault_roster_caller_province_fallback_unavailable");
    province = *fallback;
  }
  out.caller_province_identity = Identity(province); out.caller_province_present = province != nullptr;
  if (!province) return fail("daily_assault_roster_caller_province_null");
  out.caller_province_siege_id_raw_u32 = Read<std::uint32_t>(b, province, 0x788);
  if (!out.caller_province_siege_id_raw_u32) return fail("daily_assault_roster_caller_siege_id_unavailable");
  auto siege = Resolve(b, b.siege_registry_slot, b.siege_fallback_slot, out.caller_province_siege_id_raw_u32, 8);
  out.siege_resolution = siege.observation;
  if (!siege.observation.selected_object_ready) return fail("daily_assault_roster_siege_operand_unavailable");
  out.siege_flag_44c_raw_u8 = Read<std::uint8_t>(b, siege.object, 0x44C);
  if (!out.siege_flag_44c_raw_u8) return fail("daily_assault_roster_siege_flag_unavailable");
  if (*out.siege_flag_44c_raw_u8 == 0) return skip();
  out.selected_army_full_id_raw_u32 = Read<std::uint32_t>(b, army.object, 0x10);
  if (!out.selected_army_full_id_raw_u32) return fail("daily_assault_roster_append_army_full_id_unavailable");
  out.removal_contains_selected_army = Contains(removal, *out.selected_army_full_id_raw_u32);
  if (!out.removal_contains_selected_army) return fail("daily_assault_roster_removal_membership_unavailable");
  if (*out.removal_contains_selected_army) return skip();
  out.army_append_siege_full_id_u32 = Read<std::uint32_t>(b, siege.object, 8);
  if (!out.army_append_siege_full_id_u32) return fail("daily_assault_roster_append_siege_full_id_unavailable");
  out.army_append_ready = true; out.army_append = true; out.army_append_full_id_u32 = out.selected_army_full_id_raw_u32;
  auto pending = Pending(b, manager, *out.selected_army_full_id_raw_u32); out.pending_selection = pending.observation;
  if (!out.pending_selection.ready) return fail("daily_assault_roster_pending_selection_incomplete");
  if (*out.pending_selection.selected_control_raw_u8 == 0xFF) {
    out.arrg_append_ready = true; out.arrg_append_full_ids_u32 = std::vector<std::uint32_t>{}; Finish(out, true); return out;
  }
  out.original_arrg_references = References(b, At(army.object, 0x38));
  if (out.original_arrg_references.count_raw_i32 && *out.original_arrg_references.count_raw_i32 > 0)
    out.pending_selection.suppression_references = References(b, At(pending.record, 0x10));
  std::vector<std::uint32_t> appended; bool complete = out.original_arrg_references.references_ready;
  for (const auto &reference : out.original_arrg_references.occurrences) {
    game::ArmyDailyAssaultArRgAdmissionOccurrenceV1 row{};
    row.native_index = reference.native_index; row.raw_full_id_u32 = reference.raw_full_id_u32;
    if (row.raw_full_id_u32) row.pending_contains = Contains(out.pending_selection.suppression_references, *row.raw_full_id_u32);
    if (row.pending_contains) {
      row.append = !*row.pending_contains;
      if (*row.append) appended.push_back(*row.raw_full_id_u32);
      Finish(row, true);
    } else {
      row.unavailable_reason = row.raw_full_id_u32 ? "daily_assault_roster_pending_membership_unavailable" : "daily_assault_roster_arrg_full_id_unavailable";
      Finish(row, false); complete = false;
    }
    out.arrg_occurrences.push_back(std::move(row));
  }
  out.arrg_append_ready = complete;
  if (complete) out.arrg_append_full_ids_u32 = std::move(appended);
  else out.unavailable_reason = "daily_assault_roster_arrg_admission_incomplete";
  Finish(out, complete); return out;
}
} // namespace daily_assault_roster_detail

inline game::ArmyDailyAssaultRawReferencesV1 ReadDailyAssaultRemovalReferences12003(
    const CurrentDailyAssaultRosterAdmissionBindings12003 &bindings, const void *manager,
    const game::ArmyDailyQueueInputsV1 *existing_queue = nullptr) {
  return daily_assault_roster_detail::RemovalReferences(bindings, manager, existing_queue);
}
inline game::ArmyCurrentDailyAssaultRosterAdmissionV1 ReadCurrentDailyAssaultRosterAdmission12003(
    const CurrentDailyAssaultRosterAdmissionBindings12003 &bindings,
    const game::ArmyDailyQueueInputsV1 *existing_queue = nullptr) noexcept {
  using namespace daily_assault_roster_detail;
  game::ArmyCurrentDailyAssaultRosterAdmissionV1 out{};
  const auto unavailable = [&](const char *reason) { out.unavailable_reason = reason; return out; };
  if (!bindings.enabled) return unavailable("daily_assault_roster_unbound");
  const auto state = Read<const void *>(bindings, bindings.game_state_slot);
  if (!state || !*state) return unavailable("daily_assault_roster_game_state_unavailable");
  const auto data = Read<const void *>(bindings, *state, 0xA0);
  if (!data || !*data) return unavailable("daily_assault_roster_game_data_unavailable");
  const auto manager = At(*data, 0x2A540); out.manager_loaded = true; out.manager_identity = Identity(manager);
  out.removal_queue = ReadDailyAssaultRemovalReferences12003(bindings, manager, existing_queue);
  out.original_roster = References(bindings, At(manager, 0x50)); out.raw_roster_references_ready = out.original_roster.references_ready;
  for (const auto &raw : out.original_roster.occurrences)
    out.occurrences.push_back(Occurrence(bindings, manager, raw, out.removal_queue));
  const bool covered = out.raw_roster_references_ready &&
      out.occurrences.size() == static_cast<std::size_t>(*out.original_roster.count_raw_i32);
  out.original_army_selections_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
      [](const auto &row) { return row.original_army_resolution.selected_object_ready; });
  out.army_appends_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
      [](const auto &row) { return row.army_append_ready; });
  out.arrg_appends_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
      [](const auto &row) { return row.arrg_append_ready; });
  out.conditional_admission_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
      [](const auto &row) { return row.ready; });
  if (!out.conditional_admission_ready) {
    out.unavailable_reason = !out.raw_roster_references_ready ? out.original_roster.unavailable_reason : "daily_assault_roster_conditional_admission_incomplete";
  }
  Finish(out, out.conditional_admission_ready); return out;
}
} // namespace xar::ck3_12003
