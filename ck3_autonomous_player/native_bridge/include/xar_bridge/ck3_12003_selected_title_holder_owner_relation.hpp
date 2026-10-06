#pragma once
#include "xar_bridge/ck3_12003_post_admission_refresh.hpp"
namespace xar::game {
#include "xar_bridge/army_current_selected_title_holder_owner_relation_v1.inc.hpp"
}
namespace xar::ck3_12003 {
using SelectedHolderOwnerRelation = bool (*)(const void *, std::uint32_t);
struct CurrentSelectedTitleHolderOwnerRelationBindings12003 {
  CurrentDailyAssaultRosterAdmissionBindings12003 common{};
  const void *title_registry_slot = nullptr, *title_fallback_slot = nullptr;
  SelectedHolderOwnerRelation get_relation = nullptr;
};
inline CurrentSelectedTitleHolderOwnerRelationBindings12003 BindCurrentSelectedTitleHolderOwnerRelation12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentSelectedTitleHolderOwnerRelationBindings12003 out{};
  out.common = BindCurrentDailyAssaultRosterAdmission12003(base, sha);
  if (out.common.enabled) {
    out.title_registry_slot = reinterpret_cast<const void *>(base + 0x5D1DAF8);
    out.title_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DAE0);
    out.get_relation = reinterpret_cast<SelectedHolderOwnerRelation>(base + 0x28B2820);
  }
  return out;
}
namespace selected_holder_owner_detail {
using namespace daily_assault_roster_detail;
using Bindings = CurrentSelectedTitleHolderOwnerRelationBindings12003;
struct HeldStore {
  std::optional<const void *> registry, fallback;
  const void *fallback_slot = nullptr;
  bool fallback_preloaded = false;
};
inline HeldStore Hold(const Bindings &b, const void *registry, const void *fallback, bool preload_fallback) {
  HeldStore out{};
  out.registry = Read<const void *>(b.common, registry);
  out.fallback_slot = fallback; out.fallback_preloaded = preload_fallback;
  if (preload_fallback) out.fallback = Read<const void *>(b.common, fallback);
  return out;
}
inline const void *Select(const Bindings &b, const HeldStore &store,
    std::optional<std::uint32_t> requested, std::size_t full_offset,
    game::ArmySelectedHolderOperandSelectionV1 &out) {
  out.requested_full_id_u32 = requested;
  const auto fail = [&](const char *reason) -> const void * {
    out.unavailable_reason = reason; Finish(out, false); return nullptr;
  };
  if (!store.registry) return fail("selected_holder_registry_slot_unavailable");
  out.registry_loaded = *store.registry != nullptr;
  if (*store.registry) {
    if (!requested) return fail("selected_holder_requested_full_id_unavailable");
    out.registry_capacity_u32 = Read<std::uint32_t>(b.common, *store.registry, 0x2C);
    out.registry_index_u32 = *requested & 0xFFFFFFU;
    if (!out.registry_capacity_u32) return fail("selected_holder_registry_capacity_unavailable");
    if (*out.registry_index_u32 < *out.registry_capacity_u32) {
      const auto data = Read<const void *>(b.common, *store.registry, 0x20);
      if (!data || !*data) return fail("selected_holder_registry_rows_unavailable");
      const auto candidate = Read<const void *>(b.common, *data, static_cast<std::size_t>(*out.registry_index_u32) * 16 + 8);
      if (!candidate) return fail("selected_holder_registry_object_unavailable");
      if (*candidate) {
        out.indexed_identity = Identity(*candidate);
        out.indexed_full_id_u32 = Read<std::uint32_t>(b.common, *candidate, full_offset);
        if (!out.indexed_full_id_u32) return fail("selected_holder_registry_full_id_unavailable");
        if (*out.indexed_full_id_u32 == *requested) {
          out.selection = "registry_full_id"; out.used_fallback = false;
          out.object_identity = out.indexed_identity; out.selected_object_ready = true;
          Finish(out, true); return *candidate;
        }
      }
    }
  }
  const auto fallback = store.fallback_preloaded ? store.fallback : Read<const void *>(b.common, store.fallback_slot);
  out.selection = "native_fallback"; out.used_fallback = true;
  if (!fallback || !*fallback) return fail("selected_holder_native_fallback_unavailable");
  out.object_identity = Identity(*fallback); out.selected_object_ready = true;
  // Fallback identity metadata must not add a full-ID precondition to the native selection.
  Finish(out, true); return *fallback;
}
inline const void *Unit(const Bindings &b, const HeldStore &store, const void *army,
    std::int32_t index, const char *purpose, game::ArmySelectedTitleHolderOwnerRelationOccurrenceV1 &out) {
  game::ArmySelectedHolderUnitSelectionV1 step{};
  step.native_index = index; step.purpose = purpose;
  if (store.registry && *store.registry)
    step.army_124_raw_u32 = Read<std::uint32_t>(b.common, army, 0x124);
  const auto selected = Select(b, store, step.army_124_raw_u32, 0x10, step.unit_resolution);
  out.unit_selections.push_back(std::move(step)); return selected;
}
inline const void *Province(const std::optional<const void *> &value,
    const std::optional<const void *> &held_fallback, game::ArmySelectedHolderUnitSelectionV1 &step) {
  if (!value) return nullptr;
  step.province_used_fallback = *value == nullptr;
  const void *selected = *value;
  if (!selected) {
    if (!held_fallback || !*held_fallback) return nullptr;
    selected = *held_fallback;
  }
  step.province_identity = Identity(selected); return selected;
}
inline bool Returned(SelectedHolderOwnerRelation fn, bool &out, const void *holder, std::uint32_t owner) noexcept {
  if (!fn) return false;
#if defined(_MSC_VER)
  __try { out = fn(holder, owner); return true; }
  __except (1) { return false; }
#else
  out = fn(holder, owner); return true;
#endif
}
inline game::ArmySelectedTitleHolderOwnerRelationOccurrenceV1 Observe(const Bindings &b, const void *army,
    const game::ArmyPostAdmissionRefreshOccurrenceV1 &source) {
  game::ArmySelectedTitleHolderOwnerRelationOccurrenceV1 out{};
  out.native_index = source.native_index; out.raw_full_id_u32 = source.raw_full_id_u32;
  out.original_army_resolution = source.original_army_resolution;
  out.same_query_army_selection_matched = true;
  const auto fail = [&](const char *reason) { out.unavailable_reason = reason; Finish(out, false); return out; };
  const auto done = [&](std::uint8_t value) {
    out.derived_current_shared_tail_raw_u8 = value; out.current_shared_tail_inputs_ready = true;
    Finish(out, true); return out;
  };
  const auto units = Hold(b, b.common.unit_registry_slot, b.common.unit_fallback_slot, true);
  auto *unit = Unit(b, units, army, 0, "province_tag", out);
  if (!unit) return fail("selected_holder_first_unit_unavailable");
  // The source loads the Province fallback once and holds it for both Province selections.
  const auto first_province = Read<const void *>(b.common, unit, 0x20);
  const auto province_fallback = Read<const void *>(b.common, b.common.province_fallback_slot);
  auto *province = Province(first_province, province_fallback, out.unit_selections.back());
  if (!province) return fail("selected_holder_first_province_unavailable");
  auto &first_step = out.unit_selections.back();
  first_step.province_magic_85c_raw_u32 = Read<std::uint32_t>(b.common, province, 0x85C);
  if (!first_step.province_magic_85c_raw_u32) return fail("selected_holder_province_magic_unavailable");
  if (*first_step.province_magic_85c_raw_u32 != 0x50726F76U) return done(std::uint8_t{0});
  unit = Unit(b, units, army, 1, "title_province", out);
  if (!unit) return fail("selected_holder_second_unit_unavailable");
  const auto second_province = Read<const void *>(b.common, unit, 0x20);
  HeldStore titles{}; titles.fallback_slot = b.title_fallback_slot; titles.fallback_preloaded = true;
  titles.fallback = Read<const void *>(b.common, b.title_fallback_slot);
  province = Province(second_province, province_fallback, out.unit_selections.back());
  if (!province) return fail("selected_holder_title_province_unavailable");
  titles.registry = Read<const void *>(b.common, b.title_registry_slot);
  if (titles.registry && *titles.registry)
    out.province_title_738_raw_u32 = Read<std::uint32_t>(b.common, province, 0x738);
  const auto *title = Select(b, titles, out.province_title_738_raw_u32, 0x10, out.title_resolution);
  if (!title) return fail("selected_holder_title_selection_unavailable");
  out.title_holder_128_raw_u32 = Read<std::uint32_t>(b.common, title, 0x128);
  if (!out.title_holder_128_raw_u32) return fail("selected_holder_title_holder_unavailable");
  out.holder_requested_full_id_u32 = out.title_holder_128_raw_u32;
  if (*out.title_holder_128_raw_u32 == 0xFFFFFFFFU) {
    const auto definition = Read<const void *>(b.common, title, 0x48);
    if (!definition || !*definition) return fail("selected_holder_title_definition_unavailable");
    out.title_definition_64_raw_u32 = Read<std::uint32_t>(b.common, *definition, 0x64);
    if (!out.title_definition_64_raw_u32) return fail("selected_holder_title_tier_unavailable");
    if (*out.title_definition_64_raw_u32 == 1U) {
      if (titles.registry && *titles.registry)
        out.parent_title_e8_raw_u32 = Read<std::uint32_t>(b.common, title, 0xE8);
      const auto *parent = Select(b, titles, out.parent_title_e8_raw_u32, 0x10, out.parent_title_resolution);
      if (!parent) return fail("selected_holder_parent_title_unavailable");
      out.parent_holder_128_raw_u32 = Read<std::uint32_t>(b.common, parent, 0x128);
      if (!out.parent_holder_128_raw_u32) return fail("selected_holder_parent_holder_unavailable");
      out.holder_requested_full_id_u32 = out.parent_holder_128_raw_u32;
    }
  }
  const auto characters = Hold(b, b.common.character_registry_slot, b.common.character_fallback_slot, false);
  const auto *holder = Select(b, characters, out.holder_requested_full_id_u32, 0x18, out.holder_character_resolution);
  if (!holder) return fail("selected_holder_character_selection_unavailable");
  unit = Unit(b, units, army, 2, "unit_owner", out);
  if (!unit) return fail("selected_holder_final_unit_unavailable");
  out.selected_unit_owner_174_raw_u32 = Read<std::uint32_t>(b.common, unit, 0x174);
  out.holder_character_full_id_u32 = Read<std::uint32_t>(b.common, holder, 0x18);
  if (!out.selected_unit_owner_174_raw_u32 || !out.holder_character_full_id_u32)
    return fail("selected_holder_owner_or_holder_full_id_unavailable");
  out.holder_owner_equal = *out.selected_unit_owner_174_raw_u32 == *out.holder_character_full_id_u32;
  if (*out.holder_owner_equal) return done(std::uint8_t{1});
  out.native_relation_demanded = true;
  bool value = false;
  if (!Returned(b.get_relation, value, holder, *out.selected_unit_owner_174_raw_u32))
    return fail("selected_holder_native_relation_unavailable");
  out.native_relation_returned = true; out.native_holder_owner_relation = value;
  return done(value ? std::uint8_t{1} : std::uint8_t{0});
}
}
inline game::ArmyCurrentSelectedTitleHolderOwnerRelationV1 ReadCurrentSelectedTitleHolderOwnerRelation12003(
    const CurrentSelectedTitleHolderOwnerRelationBindings12003 &b,
    const game::ArmyCurrentPostAdmissionRefreshInputsV1 &same_query_refresh) noexcept {
  using namespace selected_holder_owner_detail;
  game::ArmyCurrentSelectedTitleHolderOwnerRelationV1 out{};
  out.manager_loaded = same_query_refresh.manager_loaded; out.manager_identity = same_query_refresh.manager_identity;
  out.original_roster = same_query_refresh.original_roster; out.raw_roster_references_ready = out.original_roster.references_ready;
  try {
    CurrentPostAdmissionRefreshBindings12003 borrowed{}; borrowed.common = b.common;
    std::vector<post_admission_refresh_detail::ResolutionCacheRow> cache;
    for (const auto &raw : out.original_roster.occurrences) {
      game::ArmySelectedTitleHolderOwnerRelationOccurrenceV1 row{};
      row.native_index = raw.native_index; row.raw_full_id_u32 = raw.raw_full_id_u32;
      const auto source = std::find_if(same_query_refresh.occurrences.begin(), same_query_refresh.occurrences.end(),
          [&](const auto &p) { return p.native_index == raw.native_index && p.raw_full_id_u32 == raw.raw_full_id_u32; });
      if (source != same_query_refresh.occurrences.end()) row.original_army_resolution = source->original_army_resolution;
      if (!b.common.enabled) { row.unavailable_reason = "selected_holder_unbound"; Finish(row, false); }
      else {
        const auto selected = post_admission_refresh_detail::Selected(borrowed, raw.raw_full_id_u32, true, cache);
        if (source == same_query_refresh.occurrences.end() ||
            !post_admission_refresh_detail::SameSelected(source->original_army_resolution, selected, raw.raw_full_id_u32)) {
          row.unavailable_reason = "selected_holder_same_query_army_selection_unavailable"; Finish(row, false);
        } else row = Observe(b, selected.object, *source);
      }
      out.occurrences.push_back(std::move(row));
    }
    const bool covered = post_admission_refresh_detail::Covered(out.original_roster, out.occurrences.size());
    out.original_army_selections_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
        [](const auto &row) { return row.same_query_army_selection_matched; });
    out.current_shared_tail_inputs_ready = out.original_army_selections_ready &&
        std::all_of(out.occurrences.begin(), out.occurrences.end(), [](const auto &row) { return row.current_shared_tail_inputs_ready; });
    if (!out.current_shared_tail_inputs_ready) out.unavailable_reason = "selected_holder_current_inputs_incomplete";
    Finish(out, out.current_shared_tail_inputs_ready);
  } catch (...) { out.unavailable_reason = "selected_holder_collection_unavailable"; Finish(out, false); }
  return out;
}
}
