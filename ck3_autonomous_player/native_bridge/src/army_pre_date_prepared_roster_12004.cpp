#include "army_pre_date_prepared_roster_12004.hpp"

#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12004 {
namespace {
const void *At(const void *p, std::size_t offset = 0) noexcept {
  return p ? static_cast<const std::byte *>(p) + offset : nullptr;
}
template<class T> std::optional<T> Read(
    const ArmyPreDatePreparedRosterBindings12004 &b,
    const void *p, std::size_t offset = 0) noexcept {
  if (!p) return std::nullopt;
  T value{};
  if (b.read_memory) {
    if (!b.read_memory(b.read_context, At(p, offset), &value, sizeof value))
      return std::nullopt;
  } else std::memcpy(&value, At(p, offset), sizeof value);
  return value;
}
const void *Resolve(const ArmyPreDatePreparedRosterBindings12004 &b,
    ArmyPreDatePreparedOccurrence12004 &row) noexcept {
  const auto store = Read<const void *>(b, b.persistent_registry_slot);
  if (!store) { row.resolution_reason = "persistent_registry_slot_unread"; return nullptr; }
  if (*store) {
    row.registry_capacity = Read<std::uint32_t>(b, *store, 0x2C);
    row.registry_index = *row.raw_full_id & 0xFFFFFFU;
    if (!row.registry_capacity) {
      row.resolution_reason = "persistent_registry_capacity_unread"; return nullptr;
    }
    if (*row.registry_index < *row.registry_capacity) {
      const auto table = Read<const void *>(b, *store, 0x20);
      if (!table || !*table) {
        row.resolution_reason = "persistent_registry_table_unread"; return nullptr;
      }
      const auto candidate = Read<const void *>(b, *table,
          static_cast<std::size_t>(*row.registry_index) * 16 + 8);
      if (!candidate) {
        row.resolution_reason = "persistent_registry_candidate_unread"; return nullptr;
      }
      if (*candidate) {
        row.candidate_full_id = Read<std::uint32_t>(b, *candidate, 0x10);
        if (!row.candidate_full_id) {
          row.resolution_reason = "persistent_candidate_full_id_unread"; return nullptr;
        }
        if (*row.candidate_full_id == *row.raw_full_id) {
          row.resolved_full_id = row.candidate_full_id;
          row.resolution_ready = true;
          return *candidate;
        }
        row.resolution_reason = "full_generation_mismatch";
      } else row.resolution_reason = "native_null_candidate";
    } else row.resolution_reason = "native_index_out_of_bounds";
  } else row.resolution_reason = "native_registry_not_loaded";
  // Actual2A9A315 uses the native fallback without an extra Regi magic gate.
  row.used_fallback = true;
  const auto fallback = Read<const void *>(b, b.persistent_fallback_slot);
  if (!fallback || !*fallback) return nullptr;
  row.resolved_full_id = Read<std::uint32_t>(b, *fallback, 0x10);
  row.resolution_ready = row.resolved_full_id.has_value();
  return row.resolution_ready ? *fallback : nullptr;
}
void PrepareAtCurrentEntry(const ArmyPreDatePreparedRosterBindings12004 &b,
    const void *receiver, ArmyPreDatePreparedOccurrence12004 &row) noexcept {
  // Actual4 complete93B262C680, frozen before implementing this projection.
  row.guard138 = Read<std::int32_t>(b, receiver, 0x138);
  if (!row.guard138) { row.unavailable_reason = "preparation_guard138_unread"; return; }
  if (*row.guard138 != 0) row.permission_required = true;
  else {
    const auto definition = Read<const void *>(b, receiver, 0x118);
    if (definition && *definition)
      row.definition_magic38 = Read<std::uint32_t>(b, *definition, 0x38);
    if (!row.definition_magic38) {
      row.unavailable_reason = "preparation_definition_magic38_unread"; return;
    }
    row.permission_required = *row.definition_magic38 == 0x4744624FU;
  }
  if (*row.permission_required) {
    if (!b.can_fixed_chunk0_replenish) {
      row.unavailable_reason = "preparation_fixed_chunk0_getter_unbound"; return;
    }
    auto *regiment = const_cast<void *>(receiver);
    // Native262C6A2 always passes physical+18; raw chunk+C is irrelevant here.
    row.fixed_chunk0_permission = b.can_fixed_chunk0_replenish(
        regiment, static_cast<std::byte *>(regiment) + 0x18);
    if (!*row.fixed_chunk0_permission) {
      row.conditional_branch_cache148 = 0;
      row.conditional_preparation_ready = true;
      return;
    }
  }
  if (!b.get_fresh_fraction) {
    row.unavailable_reason = "preparation_fresh_fraction_getter_unbound"; return;
  }
  std::int64_t local{};
  auto *value = b.get_fresh_fraction(const_cast<void *>(receiver), &local);
  // Actual262C6CD consumes [returned RAX], rather than assuming an out ACK.
  if (value) row.fresh_fraction = Read<std::int64_t>(b, value);
  if (!row.fresh_fraction) {
    row.unavailable_reason = "preparation_fresh_fraction_unread"; return;
  }
  row.conditional_branch_cache148 = row.fresh_fraction;
  row.conditional_preparation_ready = true;
}
} // namespace

ArmyPreDatePreparedRosterBindings12004 BindArmyPreDatePreparedRoster12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ArmyPreDatePreparedRosterBindings12004 out{};
  if (!base || sha != "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
    return out;
  out.enabled = true;
  out.game_state_slot = reinterpret_cast<const void *>(base + 0x5C68C50);
  out.persistent_registry_slot = reinterpret_cast<const void *>(base + 0x5D1EB68);
  out.persistent_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1EB58);
  out.can_fixed_chunk0_replenish = reinterpret_cast<decltype(out.can_fixed_chunk0_replenish)>(base + 0x262C6E0);
  out.get_fresh_fraction = reinterpret_cast<decltype(out.get_fresh_fraction)>(base + 0x262CAB0);
  // The mutating262C680 preparation method is deliberately absent from bindings.
  return out;
}

ArmyPreDatePreparedRoster12004 ReadArmyPreDatePreparedRoster12004(
    const ArmyPreDatePreparedRosterBindings12004 &b,
    ArmyPreparedRosterFrame12004 frame) noexcept {
  ArmyPreDatePreparedRoster12004 out{};
  out.observed_frame = frame;
  if (!b.enabled) { out.unavailable_reason = "pre_date_prepared_roster_unbound"; return out; }
  const auto state = Read<const void *>(b, b.game_state_slot);
  if (!state || !*state) { out.unavailable_reason = "pre_date_game_state_unread"; return out; }
  out.observed_frame.date_raw = Read<std::uint64_t>(b, *state, 8);
  out.observed_frame.absolute_day_raw = Read<std::uint32_t>(b, *state, 0x9C);
  out.current_c0_raw = Read<std::uint8_t>(b, *state, 0xC0);
  if (out.current_c0_raw) out.current_mask02_admitted = (*out.current_c0_raw & 2U) != 0;
  const auto data = Read<const void *>(b, *state, 0xA0);
  if (!data || !*data) { out.unavailable_reason = "pre_date_game_data_unread"; return out; }
  const auto *primary = At(*data, 0x2A540);
  // Caller holds secondary=primary+8; its+28/+34 are primary+30/+3C.
  const auto ids = Read<const void *>(b, primary, 0x30);
  out.native_persistent_occurrence_count = Read<std::int32_t>(b, primary, 0x3C);
  if (!out.native_persistent_occurrence_count || *out.native_persistent_occurrence_count < 0 ||
      *out.native_persistent_occurrence_count > 1'000'000 || !ids ||
      (*out.native_persistent_occurrence_count > 0 && !*ids)) {
    out.unavailable_reason = "pre_date_persistent_roster_unread"; return out;
  }
  out.raw_roster_ready = true;
  out.occurrences.reserve(static_cast<std::size_t>(*out.native_persistent_occurrence_count));
  for (std::int32_t index = 0; index < *out.native_persistent_occurrence_count; ++index) {
    ArmyPreDatePreparedOccurrence12004 row{};
    row.stored_index = index;
    row.raw_full_id = Read<std::uint32_t>(b, *ids, static_cast<std::size_t>(index) * 4);
    if (!row.raw_full_id) {
      out.raw_roster_ready = false; row.unavailable_reason = "pre_date_raw_full_id_unread";
    } else if (const auto *receiver = Resolve(b, row)) {
      row.current_cache148 = Read<std::int64_t>(b, receiver, 0x148);
      if (out.current_mask02_admitted == false) {
        row.conditional_branch_cache148 = row.current_cache148;
        row.conditional_preparation_ready = row.current_cache148.has_value();
      } else if (out.current_mask02_admitted == true) {
        PrepareAtCurrentEntry(b, receiver, row);
      } else row.unavailable_reason = "pre_date_c0_unread";
    } else row.unavailable_reason = "pre_date_persistent_resolution_unread";
    out.occurrences.push_back(std::move(row));
  }
  const auto all = [&](const auto &predicate) {
    return out.raw_roster_ready && std::all_of(out.occurrences.begin(), out.occurrences.end(), predicate);
  };
  out.current_resolution_ready = all([](const auto &row) { return row.resolution_ready; });
  out.current_cache_ready = all([](const auto &row) { return row.current_cache148.has_value(); });
  out.conditional_preparation_ready = out.current_mask02_admitted.has_value() &&
      all([](const auto &row) { return row.conditional_preparation_ready; });
  if (!out.conditional_preparation_ready) out.unavailable_reason = "pre_date_conditional_preparation_incomplete";
  return out;
}
} // namespace xar::ck3_12004
