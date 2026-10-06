#pragma once

#include "xar_bridge/ck3_12003_daily_assault_roster_admission.hpp"

#include <map>

namespace xar::ck3_12003 {
struct CurrentPreDatePendingUpdateBindings12003 {
  CurrentDailyAssaultRosterAdmissionBindings12003 common{};
  const void *combat_registry_slot = nullptr, *combat_fallback_slot = nullptr;
  const void *arrg_registry_slot = nullptr, *arrg_fallback_slot = nullptr;
  const void *contract_registry_slot = nullptr, *contract_fallback_slot = nullptr;
  const void *persistent_registry_slot = nullptr, *persistent_fallback_slot = nullptr;
  const void *native_empty_pending_buffer = nullptr;
  const void *expected_pending_vector_allocator = nullptr;
};
inline CurrentPreDatePendingUpdateBindings12003 BindCurrentPreDatePendingUpdate12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentPreDatePendingUpdateBindings12003 out{};
  out.common = BindCurrentDailyAssaultRosterAdmission12003(base, sha);
  if (!out.common.enabled) return out;
  const auto at = [base](std::uintptr_t rva) { return reinterpret_cast<const void *>(base + rva); };
  out.combat_registry_slot = at(0x5D1DE70); out.combat_fallback_slot = at(0x5D1DE18);
  out.arrg_registry_slot = at(0x5D1F340); out.arrg_fallback_slot = at(0x5D1F338);
  out.contract_registry_slot = at(0x5D1EB88); out.contract_fallback_slot = at(0x5D1EB40);
  out.persistent_registry_slot = at(0x5D1EB68); out.persistent_fallback_slot = at(0x5D1EB58);
  out.native_empty_pending_buffer = at(0x5D68BA0);
  out.expected_pending_vector_allocator = at(0x54DEB68);
  return out;
}
namespace pre_date_pending_update_detail {
using namespace daily_assault_roster_detail;
struct PendingPhysicalReadState {
  bool control_read = false, key_read = false, references_read = false, values_read = false;
};
struct PendingTableCapture {
  const CurrentPreDatePendingUpdateBindings12003 *bindings = nullptr;
  const game::ArmyCurrentDailyAssaultRosterAdmissionV1 *same_query_roster = nullptr;
  std::optional<const void *> entries;
  game::ArmyPreDatePendingTableFrameV1 frame{};
  std::map<std::int64_t, std::size_t> record_indices;
  std::vector<PendingPhysicalReadState> read_states;
};
inline std::size_t PhysicalRecordIndex(PendingTableCapture &capture, std::int64_t slot) {
  if (const auto found = capture.record_indices.find(slot); found != capture.record_indices.end())
    return found->second;
  const std::size_t index = capture.frame.records.size();
  game::ArmyPreDatePendingPhysicalRecordV1 out{};
  out.native_index = static_cast<std::int32_t>(index); out.physical_slot_i64 = slot;
  PendingPhysicalReadState state{};
  // Reuse actual same-query reads, including a failed demanded read; do not retry it.
  for (const auto &occurrence : capture.same_query_roster->occurrences) {
    const auto &pending = occurrence.pending_selection;
    if (pending.entries_identity != capture.frame.entries_identity ||
        pending.mask_raw_i32 != capture.frame.mask_raw_i32) continue;
    for (const auto &probe : pending.probes) {
      if (probe.physical_slot_i64 != slot) continue;
      if (!state.control_read) { out.control_raw_u8 = probe.control_raw_u8; state.control_read = true; }
      if (!state.key_read && probe.control_raw_u8 && *probe.control_raw_u8 >= probe.distance_raw_u8) {
        out.key_raw_full_id_u32 = probe.key_raw_full_id_u32; state.key_read = true;
      }
    }
    if (pending.selected_physical_slot_i64 == slot) {
      if (!state.control_read) { out.control_raw_u8 = pending.selected_control_raw_u8; state.control_read = true; }
      const auto &refs = pending.suppression_references;
      if (!state.references_read && (refs.status != "unavailable" || refs.unavailable_reason != "not_demanded")) {
        out.references = refs; state.references_read = true;
      }
    }
  }
  if (!state.control_read) {
    out.control_raw_u8 = Read<std::uint8_t>(capture.bindings->common,
        Record(*capture.entries, slot, 0x28), 4);
    state.control_read = true;
  }
  Finish(out, out.control_raw_u8.has_value());
  if (!out.control_raw_u8) out.unavailable_reason = "pre_date_pending_physical_control_unavailable";
  capture.record_indices.emplace(slot, index);
  capture.frame.records.push_back(std::move(out)); capture.read_states.push_back(state);
  return index;
}
inline void PhysicalRecordKey(PendingTableCapture &capture, std::size_t index) {
  auto &state = capture.read_states[index]; auto &out = capture.frame.records[index];
  if (!state.key_read) {
    out.key_raw_full_id_u32 = Read<std::uint32_t>(capture.bindings->common,
        Record(*capture.entries, out.physical_slot_i64, 0x28), 8);
    state.key_read = true;
  }
}
inline void PhysicalRecordValues(PendingTableCapture &capture, std::size_t index) {
  auto &state = capture.read_states[index]; auto &out = capture.frame.records[index];
  if (state.values_read) return;
  state.values_read = true;
  const auto &b = *capture.bindings;
  const auto record = Record(*capture.entries, out.physical_slot_i64, 0x28);
  out.stored_hash_raw_u32 = Read<std::uint32_t>(b.common, record);
  PhysicalRecordKey(capture, index);
  out.vector_capacity_raw_i32 = Read<std::int32_t>(b.common, record, 0x18);
  const auto allocator = Read<const void *>(b.common, record, 0x20);
  if (allocator) {
    out.vector_allocator_identity = Identity(*allocator);
    out.vector_allocator_matches_expected = *allocator == b.expected_pending_vector_allocator;
  }
  if (!state.references_read) {
    out.references = References(b.common, At(record, 0x10)); state.references_read = true;
  }
  // References deliberately needs no data read for count0. The physical header still has a real pointer.
  if (out.references.count_raw_i32 == 0 && !out.references.data_present) {
    const auto data = Read<const void *>(b.common, record, 0x10);
    if (data) { out.references.data_present = *data != nullptr; out.references.data_identity = Identity(*data); }
  }
  const bool complete = out.control_raw_u8 && out.stored_hash_raw_u32 && out.key_raw_full_id_u32 &&
      out.vector_capacity_raw_i32 && out.vector_allocator_identity && out.vector_allocator_matches_expected &&
      out.references.references_ready;
  if (!complete) out.unavailable_reason = "pre_date_pending_physical_record_values_incomplete";
  Finish(out, complete);
}
inline PendingTableCapture CapturePendingTable(const CurrentPreDatePendingUpdateBindings12003 &b,
    const void *manager, const game::ArmyCurrentDailyAssaultRosterAdmissionV1 &same_query_roster) {
  PendingTableCapture capture{}; capture.bindings = &b; capture.same_query_roster = &same_query_roster;
  auto &out = capture.frame;
  capture.entries = Read<const void *>(b.common, manager, 0x138);
  if (capture.entries) {
    out.entries_present = *capture.entries != nullptr; out.entries_identity = Identity(*capture.entries);
    out.data_is_native_empty_buffer = *capture.entries == b.native_empty_pending_buffer;
  }
  out.map_count_raw_i32 = Read<std::int32_t>(b.common, manager, 0x140);
  out.mask_raw_i32 = Read<std::int32_t>(b.common, manager, 0x144);
  out.tail_raw_u8 = Read<std::uint8_t>(b.common, manager, 0x148);
  out.threshold_bits_u32 = Read<std::uint32_t>(b.common, manager, 0x14C);
  if (!capture.entries || !*capture.entries) {
    out.unavailable_reason = "pre_date_pending_physical_entries_unavailable"; Finish(out, false); return capture;
  }
  if (out.mask_raw_i32 && out.tail_raw_u8) {
    out.physical_control_extent_last_slot_i64 = Signed(static_cast<std::uint32_t>(*out.mask_raw_i32) +
        static_cast<std::uint32_t>(*out.tail_raw_u8) + 1U);
    if (*out.physical_control_extent_last_slot_i64 >= 0) {
      out.physical_controls_complete = true;
      for (std::int64_t slot = 0; slot <= *out.physical_control_extent_last_slot_i64; ++slot) {
        const auto index = PhysicalRecordIndex(capture, slot);
        const auto control = out.records[index].control_raw_u8;
        if (!control) out.physical_controls_complete = false;
        // The allocator initializes only the terminal FF control, leaving its payload unused.
        if (control && *control != 0 &&
            (slot != *out.physical_control_extent_last_slot_i64 || *control != 0xFF))
          PhysicalRecordValues(capture, index);
      }
    }
  }
  // This is independent of the current allocated-image extent: actual rebuild starts at slot0
  // and stops after oldcount nonzero records, without consulting mask or terminal FF.
  if (out.data_is_native_empty_buffer == true || (out.map_count_raw_i32 && *out.map_count_raw_i32 <= 0))
    out.rehash_prefix_complete = true;
  else if (out.map_count_raw_i32) {
    for (std::int64_t slot = 0; out.rehash_nonzero_records_observed_i32 < *out.map_count_raw_i32; ++slot) {
      const auto index = PhysicalRecordIndex(capture, slot);
      const auto control = out.records[index].control_raw_u8;
      if (!control) break;
      if (*control != 0) {
        PhysicalRecordValues(capture, index); ++out.rehash_nonzero_records_observed_i32;
      }
    }
    out.rehash_prefix_complete = out.rehash_nonzero_records_observed_i32 == *out.map_count_raw_i32;
  }
  return capture;
}
inline void FinishPendingTableCapture(PendingTableCapture &capture) {
  auto &out = capture.frame;
  const bool complete = out.entries_present == true && out.data_is_native_empty_buffer.has_value() &&
      out.map_count_raw_i32 && out.mask_raw_i32 && out.tail_raw_u8 && out.threshold_bits_u32 &&
      out.physical_controls_complete && out.rehash_prefix_complete &&
      std::all_of(out.records.begin(), out.records.end(), [](const auto &row) { return row.ready; });
  if (!complete && out.unavailable_reason == "not_demanded")
    out.unavailable_reason = "pre_date_pending_physical_frame_incomplete";
  Finish(out, complete);
}
inline game::ArmyPreDatePendingSetupV1 Setup(const CurrentPreDatePendingUpdateBindings12003 &b,
    const void *manager, std::uint32_t target, const game::ArmyDailyAssaultPendingSelectionV1 *existing,
    PendingTableCapture *capture = nullptr) {
  game::ArmyPreDatePendingSetupV1 out{}; out.target_army_full_id_u32 = target; out.hash_raw_u32 = Hash(target);
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  const auto entries = capture ? capture->entries : Read<const void *>(b.common, manager, 0x138);
  if (entries) { out.entries_present = *entries != nullptr; out.entries_identity = Identity(*entries); }
  out.mask_raw_i32 = capture ? capture->frame.mask_raw_i32 : Read<std::int32_t>(b.common, manager, 0x144);
  if (!entries || !*entries || !out.mask_raw_i32) return fail("pre_date_pending_map_header_unavailable");
  const bool reuse = existing && existing->target_army_full_id_u32 == target &&
      existing->entries_identity == out.entries_identity && existing->mask_raw_i32 == out.mask_raw_i32;
  std::int64_t slot = static_cast<std::int64_t>(Signed(*out.hash_raw_u32)) & static_cast<std::int64_t>(*out.mask_raw_i32);
  out.home_slot_i64 = slot; std::uint8_t distance = 1;
  for (;;) {
    game::ArmyDailyAssaultPendingProbeV1 probe{}; probe.native_index = static_cast<std::int32_t>(out.probes.size());
    probe.physical_slot_i64 = slot; probe.distance_raw_u8 = distance;
    const auto record = Record(*entries, slot, 0x28);
    if (capture) {
      const auto index = PhysicalRecordIndex(*capture, slot);
      probe.control_raw_u8 = capture->frame.records[index].control_raw_u8;
      if (probe.control_raw_u8 && *probe.control_raw_u8 >= distance) {
        PhysicalRecordKey(*capture, index); probe.key_raw_full_id_u32 = capture->frame.records[index].key_raw_full_id_u32;
      }
    } else if (reuse && out.probes.size() < existing->probes.size()) probe = existing->probes[out.probes.size()];
    else {
      probe.control_raw_u8 = Read<std::uint8_t>(b.common, record, 4);
      if (probe.control_raw_u8 && *probe.control_raw_u8 >= distance)
        probe.key_raw_full_id_u32 = Read<std::uint32_t>(b.common, record, 8);
    }
    out.probes.push_back(probe);
    if (!probe.control_raw_u8) return fail("pre_date_pending_map_probe_control_unavailable");
    if (*probe.control_raw_u8 < distance) {
      out.existing_key = false; out.terminal_physical_slot_i64 = slot;
      out.map_count_raw_i32 = capture ? capture->frame.map_count_raw_i32 : Read<std::int32_t>(b.common, manager, 0x140);
      out.insertion_tail_raw_u8 = capture ? capture->frame.tail_raw_u8 : Read<std::uint8_t>(b.common, manager, 0x148);
      out.insertion_threshold_bits_u32 = capture ? capture->frame.threshold_bits_u32 : Read<std::uint32_t>(b.common, manager, 0x14C);
      const bool complete = out.map_count_raw_i32 && out.insertion_tail_raw_u8 && out.insertion_threshold_bits_u32;
      if (!complete) out.unavailable_reason = "pre_date_pending_insertion_header_unavailable";
      Finish(out, complete); return out;
    }
    if (!probe.key_raw_full_id_u32) return fail("pre_date_pending_map_probe_key_unavailable");
    if (*probe.key_raw_full_id_u32 == target) {
      out.existing_key = true; out.terminal_physical_slot_i64 = slot;
      if (capture) {
        const auto index = PhysicalRecordIndex(*capture, slot);
        PhysicalRecordValues(*capture, index); out.existing_references = capture->frame.records[index].references;
      } else if (reuse && existing->suppression_references.references_ready)
        out.existing_references = existing->suppression_references;
      else out.existing_references = References(b.common, At(record, 0x10));
      if (!out.existing_references.references_ready) out.unavailable_reason = "pre_date_pending_existing_list_incomplete";
      Finish(out, out.existing_references.references_ready); return out;
    }
    ++slot; distance = static_cast<std::uint8_t>(distance + 1U);
  }
}
inline game::ArmyPreDatePendingArRgV1 ArRg(const CurrentPreDatePendingUpdateBindings12003 &b,
    const game::ArmyDailyAssaultRawReferenceOccurrenceV1 &raw) {
  game::ArmyPreDatePendingArRgV1 out{}; out.native_index = raw.native_index; out.raw_full_id_u32 = raw.raw_full_id_u32;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  const auto finish = [&](bool append, const Resolved &arrg) {
    out.append_to_pending = append;
    if (append) {
      out.append_full_id_u32 = Read<std::uint32_t>(b.common, arrg.object, 0x10);
      if (!out.append_full_id_u32) return fail("pre_date_pending_selected_arrg_id_unavailable");
    }
    Finish(out, true); return out;
  };
  auto arrg = Resolve(b.common, b.arrg_registry_slot, b.arrg_fallback_slot, raw.raw_full_id_u32, 0x10);
  out.arrg_resolution = arrg.observation;
  if (!arrg.observation.selected_object_ready) return fail("pre_date_pending_arrg_selection_unavailable");
  out.current_38_raw_i32 = Read<std::int32_t>(b.common, arrg.object, 0x38);
  if (!out.current_38_raw_i32) return fail("pre_date_pending_arrg_current_unavailable");
  if (*out.current_38_raw_i32 == 0) return finish(true, arrg);
  out.contract_id_144_raw_u32 = Read<std::uint32_t>(b.common, arrg.object, 0x144);
  auto contract = Resolve(b.common, b.contract_registry_slot, b.contract_fallback_slot, out.contract_id_144_raw_u32, 8);
  out.contract_resolution = contract.observation;
  if (!contract.observation.selected_object_ready) return fail("pre_date_pending_contract_selection_unavailable");
  out.contract_flag_b9_raw_u8 = Read<std::uint8_t>(b.common, contract.object, 0xB9);
  if (!out.contract_flag_b9_raw_u8) return fail("pre_date_pending_contract_flag_unavailable");
  if (*out.contract_flag_b9_raw_u8 != 0) return finish(true, arrg);
  out.state_14c_raw_i32 = Read<std::int32_t>(b.common, arrg.object, 0x14C);
  if (!out.state_14c_raw_i32) return fail("pre_date_pending_arrg_state_unavailable");
  if (*out.state_14c_raw_i32 != 1) return finish(false, arrg);
  const auto data = Read<const void *>(b.common, arrg.object, 0x20);
  if (data) { out.original_data_present = *data != nullptr; out.original_data_identity = Identity(*data); }
  if (!data || !*data) return fail("pre_date_pending_original_data_pointer_unavailable");
  // Actual2A92320 reads pointer+8 without consulting ArRg+2C.
  out.first_persistent_id_raw_u32 = Read<std::uint32_t>(b.common, *data, 8);
  auto persistent = Resolve(b.common, b.persistent_registry_slot, b.persistent_fallback_slot,
      out.first_persistent_id_raw_u32, 0x10);
  out.persistent_resolution = persistent.observation;
  if (!persistent.observation.selected_object_ready) return fail("pre_date_pending_persistent_selection_unavailable");
  out.persistent_war_id_13c_raw_u32 = Read<std::uint32_t>(b.common, persistent.object, 0x13C);
  if (!out.persistent_war_id_13c_raw_u32) return fail("pre_date_pending_persistent_war_id_unavailable");
  if (*out.persistent_war_id_13c_raw_u32 == 0xFFFFFFFFU) return finish(false, arrg);
  auto war = Resolve(b.common, b.common.war_registry_slot, b.common.war_fallback_slot,
      out.persistent_war_id_13c_raw_u32, 8);
  out.war_resolution = war.observation;
  if (!war.observation.selected_object_ready) return fail("pre_date_pending_war_selection_unavailable");
  out.war_magic_0c_raw_u32 = Read<std::uint32_t>(b.common, war.object, 0xC);
  if (!out.war_magic_0c_raw_u32) return fail("pre_date_pending_war_magic_unavailable");
  if (*out.war_magic_0c_raw_u32 != 0x5761725FU) return finish(true, arrg);
  const auto id = Read<std::uint32_t>(b.common, war.object, 8);
  out.war_resolution.selected_full_id_u32 = id;
  out.war_resolution.selected_full_id_read_ready = id.has_value();
  if (!id) return fail("pre_date_pending_war_full_id_unavailable");
  return finish(*id == 0xFFFFFFFFU, arrg);
}
inline game::ArmyPreDatePendingOccurrenceV1 Occurrence(const CurrentPreDatePendingUpdateBindings12003 &b,
    const void *manager, const game::ArmyDailyAssaultRawReferenceOccurrenceV1 &raw,
    const game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 *existing, PendingTableCapture *capture = nullptr) {
  game::ArmyPreDatePendingOccurrenceV1 out{}; out.native_index = raw.native_index; out.raw_full_id_u32 = raw.raw_full_id_u32;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  auto army = Resolve(b.common, b.common.army_registry_slot, b.common.army_fallback_slot, raw.raw_full_id_u32, 0x10);
  out.original_army_resolution = army.observation;
  if (!army.observation.selected_object_ready) return fail("pre_date_pending_army_selection_unavailable");
  out.combat_id_128_raw_u32 = Read<std::uint32_t>(b.common, army.object, 0x128);
  auto combat = Resolve(b.common, b.combat_registry_slot, b.combat_fallback_slot, out.combat_id_128_raw_u32, 8);
  out.combat_resolution = combat.observation;
  if (!combat.observation.selected_object_ready) return fail("pre_date_pending_combat_selection_unavailable");
  out.combat_magic_0c_raw_u32 = Read<std::uint32_t>(b.common, combat.object, 0xC);
  if (!out.combat_magic_0c_raw_u32) return fail("pre_date_pending_combat_magic_unavailable");
  if (*out.combat_magic_0c_raw_u32 == 0x436F6D62U) {
    const auto id = Read<std::uint32_t>(b.common, combat.object, 8);
    out.combat_resolution.selected_full_id_u32 = id;
    out.combat_resolution.selected_full_id_read_ready = id.has_value();
    if (!id) return fail("pre_date_pending_combat_full_id_unavailable");
    if (*id != 0xFFFFFFFFU) { out.pending_mutator_selected = false; Finish(out, true); return out; }
  }
  out.army_counter_5c_raw_i32 = Read<std::int32_t>(b.common, army.object, 0x5C);
  if (!out.army_counter_5c_raw_i32) return fail("pre_date_pending_army_counter_unavailable");
  if (*out.army_counter_5c_raw_i32 != 0) { out.pending_mutator_selected = false; Finish(out, true); return out; }
  out.pending_mutator_selected = true;
  const auto target = Read<std::uint32_t>(b.common, army.object, 0x10);
  if (!target) return fail("pre_date_pending_selected_army_id_unavailable");
  // Same130 probes/list are reused, but the mutator's miss does not demand the standalone end marker.
  out.pending_setup = Setup(b, manager, *target, existing ? &existing->pending_selection : nullptr, capture);
  if (existing && existing->original_arrg_references.references_ready)
    out.original_arrg_references = existing->original_arrg_references;
  else out.original_arrg_references = References(b.common, At(army.object, 0x38));
  for (const auto &reference : out.original_arrg_references.occurrences)
    out.arrg_occurrences.push_back(ArRg(b, reference));
  const bool complete = out.pending_setup.ready && out.original_arrg_references.references_ready &&
      std::all_of(out.arrg_occurrences.begin(), out.arrg_occurrences.end(), [](const auto &row) { return row.ready; });
  if (!complete) out.unavailable_reason = "pre_date_pending_arrg_operands_incomplete";
  Finish(out, complete); return out;
}
} // namespace pre_date_pending_update_detail
inline game::ArmyCurrentPreDatePendingUpdateInputsV1 ReadCurrentPreDatePendingUpdateInputs12003(
    const CurrentPreDatePendingUpdateBindings12003 &bindings,
    const game::ArmyCurrentDailyAssaultRosterAdmissionV1 &same_query_roster,
    const game::ArmyDailyQueueInputsV1 *existing_queue = nullptr) noexcept {
  using namespace daily_assault_roster_detail;
  game::ArmyCurrentPreDatePendingUpdateInputsV1 out{};
  const auto unavailable = [&](const char *reason) { out.unavailable_reason = reason; return out; };
  if (!bindings.common.enabled) return unavailable("pre_date_pending_unbound");
  const auto state = Read<const void *>(bindings.common, bindings.common.game_state_slot);
  if (!state || !*state) return unavailable("pre_date_pending_game_state_unavailable");
  const auto data = Read<const void *>(bindings.common, *state, 0xA0);
  if (!data || !*data) return unavailable("pre_date_pending_game_data_unavailable");
  const auto manager = At(*data, 0x2A540); out.manager_loaded = true; out.manager_identity = Identity(manager);
  out.original_roster = same_query_roster.original_roster;
  out.removal_queue = same_query_roster.removal_queue.references_ready ? same_query_roster.removal_queue :
      ReadDailyAssaultRemovalReferences12003(bindings.common, manager, existing_queue);
  out.raw_roster_references_ready = out.original_roster.references_ready;
  std::optional<pre_date_pending_update_detail::PendingTableCapture> capture;
  if (bindings.native_empty_pending_buffer && bindings.expected_pending_vector_allocator)
    capture = pre_date_pending_update_detail::CapturePendingTable(bindings, manager, same_query_roster);
  for (const auto &raw : out.original_roster.occurrences) {
    const auto found = std::find_if(same_query_roster.occurrences.begin(), same_query_roster.occurrences.end(),
        [&](const auto &row) { return row.native_index == raw.native_index && row.raw_full_id_u32 == raw.raw_full_id_u32; });
    const auto *existing = found == same_query_roster.occurrences.end() ? nullptr : &*found;
    out.occurrences.push_back(pre_date_pending_update_detail::Occurrence(bindings, manager, raw, existing,
        capture ? &*capture : nullptr));
  }
  if (capture) {
    pre_date_pending_update_detail::FinishPendingTableCapture(*capture);
    out.pending_table_frame_v1 = std::move(capture->frame);
  }
  const bool covered = out.raw_roster_references_ready && out.original_roster.count_raw_i32 &&
      out.occurrences.size() == static_cast<std::size_t>(*out.original_roster.count_raw_i32);
  out.source_operands_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
      [](const auto &row) { return row.ready; });
  if (!out.source_operands_ready) out.unavailable_reason = "pre_date_pending_source_operands_incomplete";
  Finish(out, out.source_operands_ready); return out;
}
} // namespace xar::ck3_12003
