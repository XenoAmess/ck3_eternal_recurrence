#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12003_current_stored_context.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>
#include <string>
#include <string_view>
#include <utility>

namespace xar::ck3_12003 {
struct CurrentDailyAssaultTableBindings12003 {
  bool enabled = false;
  const void *game_state_slot = nullptr;
  const void *siege_registry_slot = nullptr, *siege_fallback_slot = nullptr;
  const void *army_registry_slot = nullptr, *army_fallback_slot = nullptr;
  const void *arrg_registry_slot = nullptr, *arrg_fallback_slot = nullptr;
  bool (*read_memory)(void *, const void *, void *, std::size_t) noexcept = nullptr;
  void *read_context = nullptr;
  const void *expected_army_allocator = nullptr;
  const void *expected_arrg_allocator = nullptr;
};
inline CurrentDailyAssaultTableBindings12003 BindCurrentDailyAssaultTable12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentDailyAssaultTableBindings12003 out{};
  if (!base || sha != kExecutableSha256) return out;
  out.enabled = true;
  out.game_state_slot = reinterpret_cast<const void *>(base + 0x5C68C50);
  out.siege_registry_slot = reinterpret_cast<const void *>(base + 0x5D1EC88);
  out.siege_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1EC60);
  out.army_registry_slot = reinterpret_cast<const void *>(base + 0x5D1DE48);
  out.army_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DE50);
  out.arrg_registry_slot = reinterpret_cast<const void *>(base + 0x5D1F340);
  out.arrg_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1F338);
  out.expected_army_allocator = reinterpret_cast<const void *>(base + 0x54E0570);
  out.expected_arrg_allocator = reinterpret_cast<const void *>(base + 0x54DEB68);
  return out;
}
namespace daily_assault_table_detail {
inline const void *At(const void *object, std::size_t offset) {
  return object ? static_cast<const std::byte *>(object) + offset : nullptr;
}
template <typename T>
inline std::optional<T> Read(const CurrentDailyAssaultTableBindings12003 &b,
    const void *object, std::size_t offset = 0) {
  const void *address = At(object, offset);
  if (!address) return std::nullopt;
  T value{};
  const bool copied = b.read_memory
      ? b.read_memory(b.read_context, address, &value, sizeof(value))
      : ck3_12002::current_stored_context_12003::CopyBytes(&value, address, sizeof(value));
  return copied ? std::optional<T>{value} : std::nullopt;
}
inline std::string Identity(const void *object) {
  return "native:" + std::to_string(reinterpret_cast<std::uintptr_t>(object));
}
inline void Reason(std::string &target, const std::string &reason) {
  if (target.empty()) target = reason;
}
template <typename T> inline void Finish(T &out, bool complete) {
  out.ready = complete;
  out.status = complete ? "available" : "partial";
}
struct Resolved {
  const void *object = nullptr;
  game::ArmyDailyAssaultResolutionV1 observation{};
};
inline Resolved Resolve(const CurrentDailyAssaultTableBindings12003 &b,
    const void *registry_slot, const void *fallback_slot,
    const std::optional<std::uint32_t> &requested, std::size_t full_offset) {
  Resolved result{};
  auto &out = result.observation;
  out.requested_full_id_u32 = requested;
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason; Finish(out, false); return result;
  };
  if (!requested) return fail("daily_assault_reference_full_id_unavailable");
  const auto store = Read<const void *>(b, registry_slot);
  if (!store) return fail("daily_assault_registry_slot_unavailable");
  out.registry_loaded = *store != nullptr;
  if (*store) {
    out.registry_capacity_u32 = Read<std::uint32_t>(b, *store, 0x2C);
    out.registry_index_u32 = *requested & 0xFFFFFFU;
    if (!out.registry_capacity_u32) return fail("daily_assault_registry_capacity_unavailable");
    if (*out.registry_index_u32 < *out.registry_capacity_u32) {
      const auto table = Read<const void *>(b, *store, 0x20);
      if (!table || !*table) return fail("daily_assault_registry_table_unavailable");
      const auto candidate = Read<const void *>(b, *table,
          static_cast<std::size_t>(*out.registry_index_u32) * 16 + 8);
      if (!candidate) return fail("daily_assault_registry_object_unavailable");
      if (*candidate) {
        out.indexed_identity = Identity(*candidate);
        out.indexed_full_id_u32 = Read<std::uint32_t>(b, *candidate, full_offset);
        if (!out.indexed_full_id_u32) return fail("daily_assault_registry_full_id_unavailable");
        if (*out.indexed_full_id_u32 == *requested) {
          out.selection = "registry_full_id"; out.used_fallback = false;
          out.object_identity = out.indexed_identity; out.selected_full_id_u32 = out.indexed_full_id_u32;
          result.object = *candidate; Finish(out, true); return result;
        }
      }
    }
  }
  const auto fallback = Read<const void *>(b, fallback_slot);
  if (!fallback) return fail("daily_assault_fallback_slot_unavailable");
  out.selection = "native_fallback"; out.used_fallback = true;
  if (!*fallback) return fail("daily_assault_fallback_null");
  out.object_identity = Identity(*fallback);
  out.selected_full_id_u32 = Read<std::uint32_t>(b, *fallback, full_offset);
  if (!out.selected_full_id_u32) return fail("daily_assault_fallback_full_id_unavailable");
  result.object = *fallback; Finish(out, true); return result;
}
inline game::ArmyDailyAssaultOccurrenceV1 ArmyOccurrence(
    const CurrentDailyAssaultTableBindings12003 &b, std::int32_t index,
    const std::optional<std::uint32_t> &requested) {
  game::ArmyDailyAssaultOccurrenceV1 out{};
  out.native_index = index; out.raw_full_id_u32 = requested;
  out.resolution = Resolve(b, b.army_registry_slot, b.army_fallback_slot, requested, 0x10).observation;
  out.unavailable_reason = out.resolution.unavailable_reason;
  Finish(out, out.resolution.ready);
  return out;
}
inline game::ArmyDailyAssaultArRgOccurrenceV1 ArRgOccurrence(
    const CurrentDailyAssaultTableBindings12003 &b, std::int32_t index,
    const std::optional<std::uint32_t> &requested) {
  game::ArmyDailyAssaultArRgOccurrenceV1 out{};
  out.native_index = index; out.raw_full_id_u32 = requested;
  auto selected = Resolve(b, b.arrg_registry_slot, b.arrg_fallback_slot, requested, 0x10);
  out.resolution = std::move(selected.observation);
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason; Finish(out, false); return out;
  };
  if (!out.resolution.ready) return fail(out.resolution.unavailable_reason.c_str());
  out.magic_raw_u32 = Read<std::uint32_t>(b, selected.object, 0x14);
  if (!out.magic_raw_u32) return fail("daily_assault_arrg_magic_unavailable");
  out.identity_valid = *out.magic_raw_u32 == 0x41725267U &&
                       *out.resolution.selected_full_id_u32 != 0xFFFFFFFFU;
  if (!*out.identity_valid) {
    out.denominator_included = false; Finish(out, true); return out;
  }
  const auto definition = Read<const void *>(b, selected.object, 0x18);
  if (!definition || !*definition) return fail("daily_assault_arrg_definition_unavailable");
  out.definition_identity = Identity(*definition);
  out.definition_type_raw_i32 = Read<std::int32_t>(b, *definition, 0x2A0);
  if (!out.definition_type_raw_i32) return fail("daily_assault_arrg_definition_type_unavailable");
  out.denominator_included = *out.definition_type_raw_i32 <= 0;
  if (*out.denominator_included) {
    out.current_raw_i32 = Read<std::int32_t>(b, selected.object, 0x38);
    if (!out.current_raw_i32) return fail("daily_assault_arrg_current_unavailable");
  }
  Finish(out, true);
  return out;
}
inline game::ArmyDailyAssaultAllocatorWitnessV1 AllocatorWitness(
    const CurrentDailyAssaultTableBindings12003 &b, const void *header,
    const void *expected, std::uint32_t expected_rva) {
  game::ArmyDailyAssaultAllocatorWitnessV1 out{};
  out.expected_rva_u32 = expected_rva;
  if (expected) out.expected_identity = Identity(expected);
  const auto actual = Read<const void *>(b, header, 0x10);
  out.actual_read_ready = actual.has_value();
  if (actual) out.actual_identity = Identity(*actual);
  if (!actual) out.unavailable_reason = "daily_assault_vector_allocator_unavailable";
  else if (!expected) out.unavailable_reason = "daily_assault_vector_expected_allocator_unbound";
  else out.matches_expected = *actual == expected;
  Finish(out, actual.has_value() && expected != nullptr);
  return out;
}
template <typename Occurrence, typename Reader>
inline game::ArmyDailyAssaultReferencesV1<Occurrence> References(
    const CurrentDailyAssaultTableBindings12003 &b, const void *header,
    Reader occurrence_reader, const void *expected_allocator, std::uint32_t expected_rva) {
  game::ArmyDailyAssaultReferencesV1<Occurrence> out{};
  const auto finish = [&]() {
    out.observed_occurrence_count = static_cast<std::int32_t>(out.occurrences.size());
    const bool complete = out.references_ready && std::all_of(out.occurrences.begin(), out.occurrences.end(),
        [](const auto &row) { return row.ready; });
    Finish(out, complete); return out;
  };
  if (b.expected_army_allocator || b.expected_arrg_allocator)
    out.allocator_witness = AllocatorWitness(b, header, expected_allocator, expected_rva);
  out.count_raw_i32 = Read<std::int32_t>(b, header, 0xC);
  const auto data = Read<const void *>(b, header);
  game::ArmyDailyAssaultReleaseHeaderV1 raw_header{};
  raw_header.count_raw_i32 = out.count_raw_i32;
  raw_header.capacity_raw_i32 = Read<std::int32_t>(b, header, 8);
  if (data) {
    raw_header.data_present = *data != nullptr;
    raw_header.data_identity = Identity(*data);
  }
  if (!data) Reason(raw_header.unavailable_reason, "daily_assault_release_data_unavailable");
  if (!out.count_raw_i32) Reason(raw_header.unavailable_reason, "daily_assault_release_count_unavailable");
  if (!raw_header.capacity_raw_i32) Reason(raw_header.unavailable_reason, "daily_assault_release_capacity_unavailable");
  Finish(raw_header, data.has_value() && out.count_raw_i32.has_value() && raw_header.capacity_raw_i32.has_value());
  out.release_header_v1 = std::move(raw_header);
  if (!out.count_raw_i32) { out.unavailable_reason = "daily_assault_vector_count_unavailable"; return finish(); }
  if (*out.count_raw_i32 < 0) { out.unavailable_reason = "daily_assault_vector_negative_count"; return finish(); }
  if (*out.count_raw_i32 == 0) { out.references_ready = true; return finish(); }
  if (data) out.data_present = *data != nullptr;
  if (!data || !*data) { out.unavailable_reason = "daily_assault_vector_data_unavailable"; return finish(); }
  out.data_identity = Identity(*data);
  out.references_ready = true;
  for (std::int32_t i = 0; i < *out.count_raw_i32; ++i) {
    const auto full = Read<std::uint32_t>(b, *data, static_cast<std::size_t>(i) * 4);
    auto row = occurrence_reader(b, i, full);
    if (!full) out.references_ready = false;
    if (!row.ready) Reason(out.unavailable_reason, row.unavailable_reason);
    out.occurrences.push_back(std::move(row));
  }
  return finish();
}
inline game::ArmyDailyAssaultGroupV1 Group(const CurrentDailyAssaultTableBindings12003 &b,
    const void *record, std::int64_t slot, std::int32_t ordinal, std::uint8_t control) {
  game::ArmyDailyAssaultGroupV1 out{};
  out.native_index = ordinal; out.physical_slot_i64 = slot; out.control_raw_u8 = control;
  out.hash_raw_u32 = Read<std::uint32_t>(b, record, 0);
  out.siege_full_id_u32 = Read<std::uint32_t>(b, record, 8);
  out.siege_resolution = Resolve(b, b.siege_registry_slot, b.siege_fallback_slot, out.siege_full_id_u32, 8).observation;
  out.armies = References<game::ArmyDailyAssaultOccurrenceV1>(b, At(record, 0x10), ArmyOccurrence,
      b.expected_army_allocator, 0x54E0570);
  out.arrgs = References<game::ArmyDailyAssaultArRgOccurrenceV1>(b, At(record, 0x28), ArRgOccurrence,
      b.expected_arrg_allocator, 0x54DEB68);
  out.denominator_ready = out.arrgs.ready;
  if (!out.hash_raw_u32) Reason(out.unavailable_reason, "daily_assault_group_hash_unavailable");
  if (!out.siege_full_id_u32) Reason(out.unavailable_reason, "daily_assault_group_siege_key_unavailable");
  if (!out.siege_resolution.ready) Reason(out.unavailable_reason, out.siege_resolution.unavailable_reason);
  if (!out.armies.ready) Reason(out.unavailable_reason, out.armies.unavailable_reason);
  if (!out.arrgs.ready) Reason(out.unavailable_reason, out.arrgs.unavailable_reason);
  Finish(out, out.hash_raw_u32.has_value() && out.siege_full_id_u32.has_value() &&
              out.siege_resolution.ready && out.armies.ready && out.arrgs.ready);
  return out;
}
} // namespace daily_assault_table_detail

inline game::ArmyCurrentDailyAssaultTableV1 ReadCurrentDailyAssaultTable12003(
    const CurrentDailyAssaultTableBindings12003 &b) noexcept {
  using namespace daily_assault_table_detail;
  game::ArmyCurrentDailyAssaultTableV1 out{};
  const auto unavailable = [&](const char *reason) {
    out.unavailable_reason = out.header.unavailable_reason = reason;
    return out;
  };
  if (!b.enabled) return unavailable("daily_assault_table_unbound");
  const auto state = Read<const void *>(b, b.game_state_slot);
  if (!state || !*state) return unavailable("daily_assault_game_state_unavailable");
  const auto data = Read<const void *>(b, *state, 0xA0);
  if (!data || !*data) return unavailable("daily_assault_game_data_unavailable");
  // The primary CArmyManager is inline in GameData, not a pointer member.
  const auto manager = At(*data, 0x2A540);
  out.manager_loaded = true;
  out.manager_identity = Identity(manager);
  auto &header = out.header;
  const auto entries = Read<const void *>(b, manager, 0x178);
  if (entries) {
    header.entries_present = *entries != nullptr;
    if (*entries) header.entries_identity = Identity(*entries);
  } else Reason(header.unavailable_reason, "daily_assault_entries_pointer_unavailable");
  header.occupied_count_raw_i32 = Read<std::int32_t>(b, manager, 0x180);
  header.mask_raw_i32 = Read<std::int32_t>(b, manager, 0x184);
  header.tail_distance_raw_u8 = Read<std::uint8_t>(b, manager, 0x188);
  header.load_factor_f32_bits_u32 = Read<std::uint32_t>(b, manager, 0x18C);
  if (!header.occupied_count_raw_i32) Reason(header.unavailable_reason, "daily_assault_occupied_count_unavailable");
  if (!header.mask_raw_i32) Reason(header.unavailable_reason, "daily_assault_mask_unavailable");
  if (!header.tail_distance_raw_u8) Reason(header.unavailable_reason, "daily_assault_tail_distance_unavailable");
  if (!header.load_factor_f32_bits_u32) Reason(header.unavailable_reason, "daily_assault_load_factor_bits_unavailable");
  const bool header_complete = entries.has_value() && header.occupied_count_raw_i32.has_value() &&
      header.mask_raw_i32.has_value() && header.tail_distance_raw_u8.has_value() &&
      header.load_factor_f32_bits_u32.has_value();
  Finish(header, header_complete);
  if (header.mask_raw_i32 && header.tail_distance_raw_u8) {
    const std::uint32_t end_bits = static_cast<std::uint32_t>(*header.mask_raw_i32) +
                                  *header.tail_distance_raw_u8 + 1U;
    std::int32_t signed_end{};
    std::memcpy(&signed_end, &end_bits, sizeof(signed_end));
    header.end_slot_raw_i32 = signed_end;
  }
  const bool scan_source = entries && *entries && header.end_slot_raw_i32 && *header.end_slot_raw_i32 >= 0;
  std::string scan_reason;
  if (scan_source) {
    header.end_marker_control_raw_u8 = Read<std::uint8_t>(b, *entries,
        static_cast<std::size_t>(*header.end_slot_raw_i32) * 0x40 + 4);
    if (!header.end_marker_control_raw_u8) scan_reason = "daily_assault_end_marker_unavailable";
    else if (*header.end_marker_control_raw_u8 == 0) scan_reason = "daily_assault_end_marker_control_zero";
    bool controls_complete = true;
    for (std::int64_t slot = 0; slot < *header.end_slot_raw_i32; ++slot) {
      game::ArmyDailyAssaultControlV1 control{};
      control.physical_slot_i64 = slot;
      const auto record = At(*entries, static_cast<std::size_t>(slot) * 0x40);
      control.control_raw_u8 = Read<std::uint8_t>(b, record, 4);
      if (!control.control_raw_u8) {
        control.unavailable_reason = "daily_assault_control_unavailable";
        Reason(scan_reason, control.unavailable_reason); controls_complete = false;
        out.physical_controls.push_back(std::move(control)); break;
      }
      if (*control.control_raw_u8 != 0)
        out.groups.push_back(Group(b, record, slot, static_cast<std::int32_t>(out.groups.size()),
                                   *control.control_raw_u8));
      out.physical_controls.push_back(std::move(control));
    }
    out.physical_scan_ready = controls_complete && scan_reason.empty();
  } else {
    scan_reason = header.end_slot_raw_i32 && *header.end_slot_raw_i32 < 0
        ? "daily_assault_signed_end_before_first_slot" : "daily_assault_scan_storage_unavailable";
  }
  out.observed_occupied_group_count = static_cast<std::int32_t>(out.groups.size());
  const bool known_empty = header.occupied_count_raw_i32 == 0 && out.groups.empty();
  const bool count_observed = header.occupied_count_raw_i32 && *header.occupied_count_raw_i32 >= 0;
  out.raw_groups_ready = known_empty || (count_observed && out.physical_scan_ready &&
      std::all_of(out.groups.begin(), out.groups.end(), [](const auto &group) {
        return group.hash_raw_u32 && group.siege_full_id_u32 &&
               group.armies.references_ready && group.arrgs.references_ready;
      }));
  const bool complete = out.raw_groups_ready && std::all_of(out.groups.begin(), out.groups.end(),
      [](const auto &group) { return group.ready; });
  if (!complete) {
    if (!count_observed) Reason(out.unavailable_reason, header.unavailable_reason.empty()
        ? "daily_assault_occupied_count_negative" : header.unavailable_reason);
    if (!out.physical_scan_ready) Reason(out.unavailable_reason, scan_reason);
    for (const auto &group : out.groups)
      if (!group.ready) Reason(out.unavailable_reason, group.unavailable_reason);
    if (out.unavailable_reason.empty()) out.unavailable_reason = "daily_assault_current_groups_partial";
  }
  Finish(out, complete);
  return out;
}
} // namespace xar::ck3_12003
