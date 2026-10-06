#pragma once
#include "xar_bridge/ck3_12003_post_admission_refresh.hpp"
#include <array>
#include <bit>
namespace xar::game {
#include "xar_bridge/army_current_condition30_inputs_v1.inc.hpp"
}
namespace xar::ck3_12003 {
using Condition30ConstructScope = void *(*)(void *, const std::int32_t *);
using Condition30DestroyScope = void (*)(void *);
using Condition30Evaluate = bool (*)(const void *, void *);
struct CurrentArmyCondition30Bindings12003 {
  CurrentDailyAssaultRosterAdmissionBindings12003 common{};
  Condition30ConstructScope construct_actor_scope = nullptr;
  Condition30DestroyScope destroy_scope = nullptr;
  Condition30Evaluate evaluate_condition = nullptr;
};
inline CurrentArmyCondition30Bindings12003 BindCurrentArmyCondition30Inputs12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentArmyCondition30Bindings12003 out{};
  out.common = BindCurrentDailyAssaultRosterAdmission12003(base, sha);
  if (!out.common.enabled) return out;
  out.construct_actor_scope = reinterpret_cast<Condition30ConstructScope>(base + 0x9F9E20);
  out.destroy_scope = reinterpret_cast<Condition30DestroyScope>(base + 0x87E0E0);
  out.evaluate_condition = reinterpret_cast<Condition30Evaluate>(base + 0x372DF30);
  return out;
}
namespace army_condition30_detail {
using namespace daily_assault_roster_detail;
using Bindings = CurrentArmyCondition30Bindings12003;
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
inline void Destroy(Condition30DestroyScope f, void *object) noexcept {
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
inline const void *Unit(const Bindings &b, const void *army, game::ArmyCondition30OccurrenceV1 &row) {
  auto &out = row.unit_resolution;
  const auto fail = [&](const char *reason) -> const void * {
    out.unavailable_reason = reason; Finish(out, false); return nullptr;
  };
  const auto store = Read<const void *>(b.common, b.common.unit_registry_slot);
  if (!store) return fail("condition30_unit_registry_slot_unavailable");
  out.registry_loaded = *store != nullptr;
  if (*store) {
    row.army_124_raw_u32 = Read<std::uint32_t>(b.common, army, 0x124);
    out.requested_full_id_u32 = row.army_124_raw_u32;
    if (!row.army_124_raw_u32) return fail("condition30_army124_unavailable");
    out.registry_index_u32 = *row.army_124_raw_u32 & 0xFFFFFFU;
    out.registry_capacity_u32 = Read<std::uint32_t>(b.common, *store, 0x2C);
    if (!out.registry_capacity_u32) return fail("condition30_unit_capacity_unavailable");
    if (*out.registry_index_u32 < *out.registry_capacity_u32) {
      const auto table = Read<const void *>(b.common, *store, 0x20);
      if (!table || !*table) return fail("condition30_unit_table_unavailable");
      const auto candidate = Read<const void *>(b.common, *table, static_cast<std::size_t>(*out.registry_index_u32) * 16 + 8);
      if (!candidate) return fail("condition30_unit_slot_unavailable");
      if (*candidate) {
        out.indexed_identity = Identity(*candidate);
        out.indexed_full_id_u32 = Read<std::uint32_t>(b.common, *candidate, 0x10);
        if (!out.indexed_full_id_u32) return fail("condition30_unit_generation_unavailable");
        if (*out.indexed_full_id_u32 == *row.army_124_raw_u32) {
          out.selection = "registry_full_id"; out.used_fallback = false;
          out.object_identity = out.indexed_identity; out.selected_object_ready = true;
          Finish(out, true); return *candidate;
        }
      }
    }
  }
  const auto fallback = Read<const void *>(b.common, b.common.unit_fallback_slot);
  out.selection = "native_fallback"; out.used_fallback = true;
  if (!fallback || !*fallback) return fail("condition30_unit_fallback_unavailable");
  out.object_identity = Identity(*fallback); out.selected_object_ready = true;
  Finish(out, true); return *fallback;
}
inline game::ArmyCondition30OccurrenceV1 Observe(const Bindings &b, const void *army,
    const game::ArmyPostAdmissionRefreshOccurrenceV1 &source) {
  game::ArmyCondition30OccurrenceV1 out{};
  out.native_index = source.native_index; out.raw_full_id_u32 = source.raw_full_id_u32;
  out.original_army_resolution = source.original_army_resolution;
  out.same_query_army_selection_matched = true;
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason; Finish(out, false); return out;
  };
  out.actual_army_30_raw_u8 = Read<std::uint8_t>(b.common, army, 0x30);
  out.army_1d4_raw_u8 = Read<std::uint8_t>(b.common, army, 0x1D4);
  if (!out.army_1d4_raw_u8) return fail("condition30_army1d4_unavailable");
  if (*out.army_1d4_raw_u8 == 0) {
    out.derived_current_30_raw_u8 = std::uint8_t{0}; out.current_condition_30_inputs_ready = true;
    Finish(out, true); return out;
  }
  const auto *unit = Unit(b, army, out);
  if (!unit) return fail(out.unit_resolution.unavailable_reason.c_str());
  out.unit_owner_174_raw_u32 = Read<std::uint32_t>(b.common, unit, 0x174);
  if (!out.unit_owner_174_raw_u32) return fail("condition30_unit_owner174_unavailable");
  const auto condition_owner = Read<const void *>(b.common, army, 0x1D8);
  if (!condition_owner || !*condition_owner) return fail("condition30_condition_owner_unavailable");
  out.condition_owner_identity = Identity(*condition_owner);
  const auto *condition = At(*condition_owner, 0x160);
  out.inline_condition_identity = Identity(condition);
  if (!b.construct_actor_scope || !b.destroy_scope || !b.evaluate_condition)
    return fail("condition30_context_or_evaluator_unbound");
  Scope scope(b, *out.unit_owner_174_raw_u32);
  if (!scope.get()) return fail("condition30_context_construction_unavailable");
  out.root_kind = 4; out.root_subtype = 0; out.root_payload_u64 = *out.unit_owner_174_raw_u32;
  out.root_construction = "9F9E20_normal_return";
  bool passed = false;
  if (!Returned(b.evaluate_condition, passed, condition, scope.get()))
    return fail("condition30_native_evaluation_unavailable");
  out.native_current_condition_passed = passed;
  out.derived_current_30_raw_u8 = static_cast<std::uint8_t>(passed ? 0 : 1);
  out.current_condition_30_inputs_ready = true; Finish(out, true); return out;
}
}
inline game::ArmyCurrentCondition30InputsV1 ReadCurrentArmyCondition30Inputs12003(
    const CurrentArmyCondition30Bindings12003 &b,
    const game::ArmyCurrentPostAdmissionRefreshInputsV1 &same_query_refresh) noexcept {
  using namespace army_condition30_detail;
  game::ArmyCurrentCondition30InputsV1 out{};
  out.manager_loaded = same_query_refresh.manager_loaded; out.manager_identity = same_query_refresh.manager_identity;
  out.original_roster = same_query_refresh.original_roster;
  out.raw_roster_references_ready = out.original_roster.references_ready;
  if (!b.common.enabled) { out.unavailable_reason = "condition30_unbound"; return out; }
  try {
    CurrentPostAdmissionRefreshBindings12003 borrowed{}; borrowed.common = b.common;
    std::vector<post_admission_refresh_detail::ResolutionCacheRow> cache;
    for (const auto &raw : out.original_roster.occurrences) {
      game::ArmyCondition30OccurrenceV1 row{};
      row.native_index = raw.native_index; row.raw_full_id_u32 = raw.raw_full_id_u32;
      const auto source = std::find_if(same_query_refresh.occurrences.begin(), same_query_refresh.occurrences.end(),
          [&](const auto &p) { return p.native_index == raw.native_index && p.raw_full_id_u32 == raw.raw_full_id_u32; });
      if (source != same_query_refresh.occurrences.end()) row.original_army_resolution = source->original_army_resolution;
      const auto selected = post_admission_refresh_detail::Selected(borrowed, raw.raw_full_id_u32, true, cache);
      if (source == same_query_refresh.occurrences.end() ||
          !post_admission_refresh_detail::SameSelected(source->original_army_resolution, selected, raw.raw_full_id_u32)) {
        row.unavailable_reason = "condition30_same_query_army_selection_unavailable"; Finish(row, false);
      } else row = Observe(b, selected.object, *source);
      out.occurrences.push_back(std::move(row));
    }
    const bool covered = post_admission_refresh_detail::Covered(out.original_roster, out.occurrences.size());
    out.original_army_selections_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
        [](const auto &p) { return p.same_query_army_selection_matched; });
    out.current_condition_30_inputs_ready = out.original_army_selections_ready &&
        std::all_of(out.occurrences.begin(), out.occurrences.end(), [](const auto &p) { return p.current_condition_30_inputs_ready; });
    if (!out.current_condition_30_inputs_ready) out.unavailable_reason = "condition30_current_inputs_incomplete";
    Finish(out, out.current_condition_30_inputs_ready);
  } catch (...) { out.unavailable_reason = "condition30_collection_unavailable"; Finish(out, false); }
  return out;
}
}
