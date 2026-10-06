#pragma once
#include "xar_bridge/ck3_12003_post_admission_refresh.hpp"
#include "xar_bridge/ck3_12003_army_rule24_source_pins.hpp"
#include <array>
#include <bit>
namespace xar::game {
#include "xar_bridge/army_current_flag31_inputs_v1.inc.hpp"
}
namespace xar::ck3_12003 {
using Flag31ConstructScope = void *(*)(void *, const std::int32_t *);
using Flag31DestroyScope = void (*)(void *);
using Flag31Evaluate = bool (*)(const void *, void *);
struct CurrentArmyFlag31Bindings12003 {
  CurrentDailyAssaultRosterAdmissionBindings12003 common{};
  const void *combat_registry_slot = nullptr, *combat_fallback_slot = nullptr;
  const void *rule_provider_slot = nullptr;
  Flag31ConstructScope construct_actor_scope = nullptr;
  Flag31DestroyScope destroy_scope = nullptr;
  Flag31Evaluate evaluate_condition = nullptr;
  const void *rule_source_mode_slot = nullptr;
  std::uintptr_t rule_source_module_base = 0;
  std::size_t rule_source_image_size = 0;
};
inline CurrentArmyFlag31Bindings12003 BindCurrentArmyFlag31Inputs12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentArmyFlag31Bindings12003 out{};
  out.common = BindCurrentDailyAssaultRosterAdmission12003(base, sha);
  if (!out.common.enabled) return out;
  out.combat_registry_slot = reinterpret_cast<const void *>(base + 0x5D1DE70);
  out.combat_fallback_slot = reinterpret_cast<const void *>(base + 0x5D1DE18);
  out.rule_provider_slot = reinterpret_cast<const void *>(base + 0x5D21DC8);
  out.rule_source_mode_slot = reinterpret_cast<const void *>(base + 0x5D1DADC);
  out.rule_source_module_base = base;
  out.rule_source_image_size = 102518784;
  out.construct_actor_scope = reinterpret_cast<Flag31ConstructScope>(base + 0x9F9E20);
  out.destroy_scope = reinterpret_cast<Flag31DestroyScope>(base + 0x87E0E0);
  out.evaluate_condition = reinterpret_cast<Flag31Evaluate>(base + 0x372DF30);
  return out;
}
namespace army_flag31_detail {
using namespace daily_assault_roster_detail;
using Bindings = CurrentArmyFlag31Bindings12003;
struct Rule24SourcePinCacheRow {
  const void *receiver = nullptr;
  game::ArmyCurrentRule24SourcePinsV1 pins{};
};
using Rule24SourcePinCache = std::vector<Rule24SourcePinCacheRow>;
template <class F, class R, class... A>
inline bool Returned(F f, R &out, A... args) noexcept {
  if (!f) return false;
#if defined(_MSC_VER)
  __try { out = f(args...); return true; }
  __except (1) { return false; }
#else
  out = f(args...); return true;
#endif
}
inline void Destroy(Flag31DestroyScope f, void *object) noexcept {
#if defined(_MSC_VER)
  __try { f(object); } __except (1) {}
#else
  f(object);
#endif
}
class Scope {
public:
  Scope(const Bindings &b, std::uint32_t raw) noexcept : b_(b) {
    const auto id = std::bit_cast<std::int32_t>(raw);
    constructed_ = Returned(b.construct_actor_scope, context_, bytes_.data(), &id);
  }
  ~Scope() { if (constructed_) Destroy(b_.destroy_scope, bytes_.data()); }
  void *get() const noexcept { return constructed_ ? context_ : nullptr; }
  Scope(const Scope &) = delete;
  Scope &operator=(const Scope &) = delete;
private:
  const Bindings &b_;
  alignas(8) std::array<std::byte, 0x168> bytes_{};
  void *context_ = nullptr;
  bool constructed_ = false;
};
inline const void *Select(const Bindings &b, const void *store, const void *fallback_slot,
    std::optional<std::uint32_t> requested, std::size_t full_offset, const char *role,
    game::ArmyFlag31SelectionV1 &out) {
  out.registry_loaded = store != nullptr; out.requested_full_id_u32 = requested;
  const auto fail = [&](const char *suffix) -> const void * {
    out.unavailable_reason = std::string("flag31_") + role + "_" + suffix;
    Finish(out, false); return nullptr;
  };
  if (store) {
    if (!requested) return fail("requested_full_id_unavailable");
    out.registry_capacity_u32 = Read<std::uint32_t>(b.common, store, 0x2C);
    out.registry_index_u32 = *requested & 0xFFFFFFU;
    if (!out.registry_capacity_u32) return fail("registry_capacity_unavailable");
    if (*out.registry_index_u32 < *out.registry_capacity_u32) {
      const auto rows = Read<const void *>(b.common, store, 0x20);
      if (!rows || !*rows) return fail("registry_rows_unavailable");
      const auto object = Read<const void *>(b.common, *rows,
          static_cast<std::size_t>(*out.registry_index_u32) * 16 + 8);
      if (!object) return fail("registry_object_unavailable");
      if (*object) {
        out.indexed_identity = Identity(*object);
        out.indexed_full_id_u32 = Read<std::uint32_t>(b.common, *object, full_offset);
        if (!out.indexed_full_id_u32) return fail("registry_full_id_unavailable");
        if (*out.indexed_full_id_u32 == *requested) {
          out.selection = "registry_full_id"; out.used_fallback = false;
          out.object_identity = out.indexed_identity; out.selected_object_ready = true;
          Finish(out, true); return *object;
        }
      }
    }
  }
  out.selection = "native_fallback"; out.used_fallback = true;
  const auto fallback = Read<const void *>(b.common, fallback_slot);
  if (!fallback || !*fallback) return fail("native_fallback_unavailable");
  out.object_identity = Identity(*fallback); out.selected_object_ready = true;
  // Selection itself never demands an extra fallback full-ID or magic check.
  Finish(out, true); return *fallback;
}
inline bool ActiveCombat(const Bindings &b, const void *army, game::ArmyFlag31OccurrenceV1 &out) {
  const auto store = Read<const void *>(b.common, b.combat_registry_slot);
  if (!store) {
    out.combat_resolution.unavailable_reason = "flag31_combat_registry_slot_unavailable";
    Finish(out.combat_resolution, false); out.unavailable_reason = out.combat_resolution.unavailable_reason;
    return false;
  }
  // The null-store path does not read Army128.
  if (*store) out.army_128_raw_u32 = Read<std::uint32_t>(b.common, army, 0x128);
  const auto combat = Select(b, *store, b.combat_fallback_slot, out.army_128_raw_u32, 8,
      "combat", out.combat_resolution);
  if (!combat) { out.unavailable_reason = out.combat_resolution.unavailable_reason; return false; }
  out.selected_combat_magic_0c_raw_u32 = Read<std::uint32_t>(b.common, combat, 0xC);
  if (!out.selected_combat_magic_0c_raw_u32) {
    out.unavailable_reason = "flag31_combat_magic0c_unavailable"; return false;
  }
  if (*out.selected_combat_magic_0c_raw_u32 != 0x436F6D62U) {
    out.source_active_combat = false; out.active_combat_inputs_ready = true; return true;
  }
  // 24E8360 only reads this validity input after the Comb tag matches.
  out.selected_combat_full_id_08_raw_u32 = Read<std::uint32_t>(b.common, combat, 8);
  if (!out.selected_combat_full_id_08_raw_u32) {
    out.unavailable_reason = "flag31_combat_full_id08_unavailable"; return false;
  }
  out.source_active_combat = *out.selected_combat_full_id_08_raw_u32 != 0xFFFFFFFFU;
  out.active_combat_inputs_ready = true; return true;
}
inline const void *Unit(const Bindings &b, const void *army, game::ArmyFlag31OccurrenceV1 &out) {
  const auto store = Read<const void *>(b.common, b.common.unit_registry_slot);
  if (!store) {
    out.unit_resolution.unavailable_reason = "flag31_unit_registry_slot_unavailable";
    Finish(out.unit_resolution, false); return nullptr;
  }
  if (*store) out.army_124_raw_u32 = Read<std::uint32_t>(b.common, army, 0x124);
  return Select(b, *store, b.common.unit_fallback_slot, out.army_124_raw_u32, 0x10,
      "unit", out.unit_resolution);
}
inline const void *Character(const Bindings &b, const void *unit, game::ArmyFlag31OccurrenceV1 &out) {
  const auto store = Read<const void *>(b.common, b.common.character_registry_slot);
  if (!store) {
    out.character_resolution.unavailable_reason = "flag31_character_registry_slot_unavailable";
    Finish(out.character_resolution, false); return nullptr;
  }
  // A null Character store selects the actual fallback without reading Unit174.
  if (*store) out.unit_owner_174_raw_u32 = Read<std::uint32_t>(b.common, unit, 0x174);
  return Select(b, *store, b.common.character_fallback_slot, out.unit_owner_174_raw_u32, 0x18,
      "character", out.character_resolution);
}
inline game::ArmyFlag31OccurrenceV1 Observe(const Bindings &b, const void *army,
    const game::ArmyPostAdmissionRefreshOccurrenceV1 &source,
    Rule24SourcePinCache &rule24_source_pin_cache) {
  game::ArmyFlag31OccurrenceV1 out{};
  out.native_index = source.native_index; out.raw_full_id_u32 = source.raw_full_id_u32;
  out.original_army_resolution = source.original_army_resolution; out.same_query_army_selection_matched = true;
  const auto fail = [&](const std::string &reason) {
    out.unavailable_reason = reason; Finish(out, false); return out;
  };
  const auto result = [&](std::uint8_t value) {
    out.derived_current_31_raw_u8 = value; out.current_flag31_inputs_ready = true;
    Finish(out, true); return out;
  };
  // Cached31 is provenance only and cannot decide the current branch.
  out.actual_army_31_raw_u8 = Read<std::uint8_t>(b.common, army, 0x31);
  out.army_1d4_raw_u8 = Read<std::uint8_t>(b.common, army, 0x1D4);
  if (!out.army_1d4_raw_u8) return fail("flag31_army1d4_unavailable");
  if (*out.army_1d4_raw_u8 == 0) return result(0);
  if (!ActiveCombat(b, army, out)) return fail(out.unavailable_reason);
  if (*out.source_active_combat) return result(0);
  const auto unit = Unit(b, army, out);
  if (!unit) return fail(out.unit_resolution.unavailable_reason);
  const auto character = Character(b, unit, out);
  if (!character) return fail(out.character_resolution.unavailable_reason);
  // Always use selected Character18, even when fallback differs from Unit174.
  out.selected_character_18_raw_u32 = Read<std::uint32_t>(b.common, character, 0x18);
  if (!out.selected_character_18_raw_u32) return fail("flag31_selected_character18_unavailable");
  const auto provider = Read<const void *>(b.common, b.rule_provider_slot);
  if (!provider || !*provider) return fail("flag31_rule_provider_unavailable");
  out.rule_provider_identity = Identity(*provider);
  const auto rules = Read<const void *>(b.common, *provider, 0xEF0);
  if (!rules || !*rules) return fail("flag31_rule_array_unavailable");
  out.rule_array_identity = Identity(*rules);
  const auto rule = At(*rules, 0x1380); out.inline_rule_identity = Identity(rule);
  const auto held_pin = std::find_if(
      rule24_source_pin_cache.begin(), rule24_source_pin_cache.end(),
      [rule](const auto &p) { return p.receiver == rule; });
  if (held_pin != rule24_source_pin_cache.end()) {
    out.rule24_source_pins_v1 = held_pin->pins;
  } else {
    auto pins = ReadCurrentRule24SourcePins12003(b, rule);
    rule24_source_pin_cache.push_back({rule, std::move(pins)});
    out.rule24_source_pins_v1 = rule24_source_pin_cache.back().pins;
  }
  if (!b.construct_actor_scope || !b.destroy_scope || !b.evaluate_condition)
    return fail("flag31_context_or_evaluator_unbound");
  Scope scope(b, *out.selected_character_18_raw_u32);
  if (!scope.get()) return fail("flag31_context_construction_unavailable");
  out.root_kind = 4; out.root_subtype = 0; out.root_payload_u64 = *out.selected_character_18_raw_u32;
  out.root_construction = "9F9E20_normal_return";
  bool passed = false;
  if (!Returned(b.evaluate_condition, passed, rule, scope.get()))
    return fail("flag31_native_evaluation_unavailable");
  out.native_rule_evaluation_returned = true; out.native_current_rule24_passed = passed;
  return result(static_cast<std::uint8_t>(passed ? 0 : 1));
}
}
inline game::ArmyCurrentFlag31InputsV1 ReadCurrentArmyFlag31Inputs12003(
    const CurrentArmyFlag31Bindings12003 &b,
    const game::ArmyCurrentPostAdmissionRefreshInputsV1 &same_query_refresh) noexcept {
  using namespace army_flag31_detail;
  game::ArmyCurrentFlag31InputsV1 out{};
  try {
    out.manager_loaded = same_query_refresh.manager_loaded; out.manager_identity = same_query_refresh.manager_identity;
    out.original_roster = same_query_refresh.original_roster;
    out.raw_roster_references_ready = out.original_roster.references_ready;
    CurrentPostAdmissionRefreshBindings12003 borrowed{}; borrowed.common = b.common;
    std::vector<post_admission_refresh_detail::ResolutionCacheRow> cache;
    Rule24SourcePinCache rule24_source_pin_cache;
    for (const auto &raw : out.original_roster.occurrences) {
      game::ArmyFlag31OccurrenceV1 row{};
      row.native_index = raw.native_index; row.raw_full_id_u32 = raw.raw_full_id_u32;
      const auto source = std::find_if(same_query_refresh.occurrences.begin(), same_query_refresh.occurrences.end(),
          [&](const auto &p) { return p.native_index == raw.native_index && p.raw_full_id_u32 == raw.raw_full_id_u32; });
      if (source != same_query_refresh.occurrences.end()) row.original_army_resolution = source->original_army_resolution;
      if (!b.common.enabled) {
        row.unavailable_reason = "flag31_unbound"; Finish(row, false);
      } else {
        const auto selected = post_admission_refresh_detail::Selected(borrowed, raw.raw_full_id_u32, true, cache);
        if (source == same_query_refresh.occurrences.end() ||
            !post_admission_refresh_detail::SameSelected(source->original_army_resolution, selected, raw.raw_full_id_u32)) {
          row.unavailable_reason = "flag31_same_query_army_selection_unavailable"; Finish(row, false);
        } else row = Observe(b, selected.object, *source, rule24_source_pin_cache);
      }
      out.occurrences.push_back(std::move(row));
    }
    const bool covered = b.common.enabled && post_admission_refresh_detail::Covered(out.original_roster, out.occurrences.size());
    out.original_army_selections_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
        [](const auto &p) { return p.same_query_army_selection_matched; });
    out.current_flag31_inputs_ready = out.original_army_selections_ready &&
        std::all_of(out.occurrences.begin(), out.occurrences.end(), [](const auto &p) { return p.current_flag31_inputs_ready; });
    if (!out.current_flag31_inputs_ready) out.unavailable_reason = "flag31_current_inputs_incomplete";
    Finish(out, out.current_flag31_inputs_ready);
  } catch (...) { out.unavailable_reason = "flag31_collection_unavailable"; Finish(out, false); }
  return out;
}
}
