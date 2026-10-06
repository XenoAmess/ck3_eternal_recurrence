#pragma once
#include "xar_bridge/ck3_12003_post_admission_refresh.hpp"
namespace xar::game {
#include "xar_bridge/army_current_flag21_inputs_v1.inc.hpp"
}
namespace xar::ck3_12003 {
using Flag21GetSharedTail = std::uint8_t (*)(const void *);
struct CurrentArmyFlag21Bindings12003 {
  CurrentDailyAssaultRosterAdmissionBindings12003 common{};
  const void *default_header = nullptr;
  Flag21GetSharedTail get_current_shared_tail = nullptr;
};
inline CurrentArmyFlag21Bindings12003 BindCurrentArmyFlag21Inputs12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentArmyFlag21Bindings12003 out{};
  out.common = BindCurrentDailyAssaultRosterAdmission12003(base, sha);
  if (out.common.enabled) {
    out.default_header = reinterpret_cast<const void *>(base + 0x5459D38);
    out.get_current_shared_tail = reinterpret_cast<Flag21GetSharedTail>(base + 0x24E3FE0);
  }
  return out;
}
namespace army_flag21_detail {
using namespace daily_assault_roster_detail;
using Bindings = CurrentArmyFlag21Bindings12003;
inline bool Returned(Flag21GetSharedTail f, std::uint8_t &out, const void *army) noexcept {
  if (!f) return false;
#if defined(_MSC_VER)
  __try { out = f(army); return true; }
  __except (1) { return false; }
#else
  out = f(army); return true;
#endif
}
inline const void *Select(const Bindings &b, const void *store, const void *fallback_slot,
    std::optional<std::uint32_t> requested, std::size_t full_offset, game::ArmyFlag21SelectionV1 &out) {
  out.registry_loaded = store != nullptr; out.requested_full_id_u32 = requested;
  const auto fail = [&](const char *reason) -> const void * {
    out.unavailable_reason = reason; Finish(out, false); return nullptr;
  };
  if (store) {
    if (!requested) return fail("flag21_requested_full_id_unavailable");
    out.registry_capacity_u32 = Read<std::uint32_t>(b.common, store, 0x2C);
    out.registry_index_u32 = *requested & 0xFFFFFFU;
    if (!out.registry_capacity_u32) return fail("flag21_registry_capacity_unavailable");
    if (*out.registry_index_u32 < *out.registry_capacity_u32) {
      const auto rows = Read<const void *>(b.common, store, 0x20);
      if (!rows || !*rows) return fail("flag21_registry_rows_unavailable");
      const auto object = Read<const void *>(b.common, *rows, static_cast<std::size_t>(*out.registry_index_u32) * 16 + 8);
      if (!object) return fail("flag21_registry_object_unavailable");
      if (*object) {
        out.indexed_identity = Identity(*object);
        out.indexed_full_id_u32 = Read<std::uint32_t>(b.common, *object, full_offset);
        if (!out.indexed_full_id_u32) return fail("flag21_registry_full_id_unavailable");
        if (*out.indexed_full_id_u32 == *requested) {
          out.selection = "registry_full_id"; out.used_fallback = false;
          out.object_identity = out.indexed_identity; out.selected_object_ready = true;
          Finish(out, true); return *object;
        }
      }
    }
  }
  const auto fallback = Read<const void *>(b.common, fallback_slot);
  out.selection = "native_fallback"; out.used_fallback = true;
  if (!fallback || !*fallback) return fail("flag21_native_fallback_unavailable");
  out.object_identity = Identity(*fallback); out.selected_object_ready = true;
  // The inline source needs the fallback object, not an additional full-ID metadata read.
  Finish(out, true); return *fallback;
}
inline const void *Unit(const Bindings &b, const void *army, game::ArmyFlag21OccurrenceV1 &out) {
  const auto store = Read<const void *>(b.common, b.common.unit_registry_slot);
  if (!store) {
    out.unit_resolution.unavailable_reason = "flag21_unit_registry_slot_unavailable";
    Finish(out.unit_resolution, false); return nullptr;
  }
  if (*store) out.army_124_raw_u32 = Read<std::uint32_t>(b.common, army, 0x124);
  return Select(b, *store, b.common.unit_fallback_slot, out.army_124_raw_u32, 0x10, out.unit_resolution);
}
inline const void *Character(const Bindings &b, const void *unit, game::ArmyFlag21OccurrenceV1 &out) {
  const auto store = Read<const void *>(b.common, b.common.character_registry_slot);
  if (!store) {
    out.character_resolution.unavailable_reason = "flag21_character_registry_slot_unavailable";
    Finish(out.character_resolution, false); return nullptr;
  }
  out.character_resolution.registry_loaded = *store != nullptr;
  if (*store) {
    if (!unit) {
      out.character_resolution.unavailable_reason = "flag21_owner_unit_selection_unavailable";
      Finish(out.character_resolution, false); return nullptr;
    }
    out.unit_owner_174_raw_u32 = Read<std::uint32_t>(b.common, unit, 0x174);
  }
  // Null Character store goes to real fallback without demanding Unit174.
  return Select(b, *store, b.common.character_fallback_slot, out.unit_owner_174_raw_u32, 0x18, out.character_resolution);
}
inline bool Header(const Bindings &b, const void *army, game::ArmyFlag21OccurrenceV1 &out) {
  const auto unit = Unit(b, army, out);
  const auto character = Character(b, unit, out);
  if (!character) return false;
  const auto carrier = Read<const void *>(b.common, character, 0x1C0);
  if (!carrier) return false;
  out.owner_character_carrier_1c0_present = *carrier != nullptr;
  const void *header = nullptr;
  if (*carrier) {
    out.owner_character_carrier_identity = Identity(*carrier);
    out.header_selection = "carrier_inline"; header = At(*carrier, 0x318);
  } else {
    out.header_selection = "native_static"; header = b.default_header;
  }
  if (!header) return false;
  out.header_identity = Identity(header);
  out.header_0c_raw_i32 = Read<std::int32_t>(b.common, header, 0xC);
  out.owner_header_inputs_ready = out.header_0c_raw_i32.has_value();
  return out.owner_header_inputs_ready;
}
inline game::ArmyFlag21OccurrenceV1 Observe(const Bindings &b, const void *army,
    const game::ArmyPostAdmissionRefreshOccurrenceV1 &source) {
  game::ArmyFlag21OccurrenceV1 out{};
  out.native_index = source.native_index; out.raw_full_id_u32 = source.raw_full_id_u32;
  out.original_army_resolution = source.original_army_resolution; out.same_query_army_selection_matched = true;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  const auto zero = [&]() {
    out.derived_current_21_raw_u8 = std::uint8_t{0}; out.current_flag21_inputs_ready = true;
    Finish(out, true); return out;
  };
  out.actual_army_21_raw_u8 = Read<std::uint8_t>(b.common, army, 0x21);
  out.army_1ec_raw_u8 = Read<std::uint8_t>(b.common, army, 0x1EC);
  if (!out.army_1ec_raw_u8) return fail("flag21_army1ec_unavailable");
  if (*out.army_1ec_raw_u8 == 0) return zero();
  out.army_1f0_raw_i64 = Read<std::int64_t>(b.common, army, 0x1F0);
  if (!out.army_1f0_raw_i64) return fail("flag21_army1f0_unavailable");
  if (*out.army_1f0_raw_i64 <= 0) {
    if (!Header(b, army, out)) return fail("flag21_owner_header_inputs_unavailable");
    if (*out.header_0c_raw_i32 == 0) return zero();
  }
  if (!b.get_current_shared_tail) return fail("flag21_shared_tail_unbound");
  std::uint8_t value = 0;
  if (!Returned(b.get_current_shared_tail, value, army)) return fail("flag21_native_shared_tail_unavailable");
  out.native_shared_tail_returned = true; out.native_shared_tail_21_raw_u8 = value;
  out.derived_current_21_raw_u8 = value; out.current_flag21_inputs_ready = true;
  Finish(out, true); return out;
}
}
inline game::ArmyCurrentFlag21InputsV1 ReadCurrentArmyFlag21Inputs12003(
    const CurrentArmyFlag21Bindings12003 &b,
    const game::ArmyCurrentPostAdmissionRefreshInputsV1 &same_query_refresh) noexcept {
  using namespace army_flag21_detail;
  game::ArmyCurrentFlag21InputsV1 out{};
  out.manager_loaded = same_query_refresh.manager_loaded; out.manager_identity = same_query_refresh.manager_identity;
  out.original_roster = same_query_refresh.original_roster; out.raw_roster_references_ready = out.original_roster.references_ready;
  try {
    CurrentPostAdmissionRefreshBindings12003 borrowed{}; borrowed.common = b.common;
    std::vector<post_admission_refresh_detail::ResolutionCacheRow> cache;
    for (const auto &raw : out.original_roster.occurrences) {
      game::ArmyFlag21OccurrenceV1 row{};
      row.native_index = raw.native_index; row.raw_full_id_u32 = raw.raw_full_id_u32;
      const auto source = std::find_if(same_query_refresh.occurrences.begin(), same_query_refresh.occurrences.end(),
          [&](const auto &p) { return p.native_index == raw.native_index && p.raw_full_id_u32 == raw.raw_full_id_u32; });
      if (source != same_query_refresh.occurrences.end()) row.original_army_resolution = source->original_army_resolution;
      if (!b.common.enabled) {
        row.unavailable_reason = "flag21_unbound"; Finish(row, false);
      } else {
        const auto selected = post_admission_refresh_detail::Selected(borrowed, raw.raw_full_id_u32, true, cache);
        if (source == same_query_refresh.occurrences.end() ||
            !post_admission_refresh_detail::SameSelected(source->original_army_resolution, selected, raw.raw_full_id_u32)) {
          row.unavailable_reason = "flag21_same_query_army_selection_unavailable"; Finish(row, false);
        } else row = Observe(b, selected.object, *source);
      }
      out.occurrences.push_back(std::move(row));
    }
    const bool covered = post_admission_refresh_detail::Covered(out.original_roster, out.occurrences.size());
    out.original_army_selections_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
        [](const auto &p) { return p.same_query_army_selection_matched; });
    out.current_flag21_inputs_ready = out.original_army_selections_ready &&
        std::all_of(out.occurrences.begin(), out.occurrences.end(), [](const auto &p) { return p.current_flag21_inputs_ready; });
    if (!out.current_flag21_inputs_ready) out.unavailable_reason = "flag21_current_inputs_incomplete";
    Finish(out, out.current_flag21_inputs_ready);
  } catch (...) { out.unavailable_reason = "flag21_collection_unavailable"; Finish(out, false); }
  return out;
}
}
