#pragma once
#include "xar_bridge/ck3_12003_post_admission_refresh.hpp"
namespace xar::game {
#include "xar_bridge/army_current_flag20_inputs_v1.inc.hpp"
}
namespace xar::ck3_12003 {
using Flag20GetCurrent = std::uint8_t (*)(const void *);
struct CurrentArmyFlag20Bindings12003 {
  CurrentDailyAssaultRosterAdmissionBindings12003 common{};
  Flag20GetCurrent get_current_flag20 = nullptr;
};
inline CurrentArmyFlag20Bindings12003 BindCurrentArmyFlag20Inputs12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CurrentArmyFlag20Bindings12003 out{};
  out.common = BindCurrentDailyAssaultRosterAdmission12003(base, sha);
  if (out.common.enabled)
    out.get_current_flag20 = reinterpret_cast<Flag20GetCurrent>(base + 0x2C4B840);
  return out;
}
namespace army_flag20_detail {
using namespace daily_assault_roster_detail;
using Bindings = CurrentArmyFlag20Bindings12003;
inline bool Returned(Flag20GetCurrent f, std::uint8_t &out, const void *army) noexcept {
  if (!f) return false;
#if defined(_MSC_VER)
  __try { out = f(army); return true; }
  __except (1) { return false; }
#else
  out = f(army); return true;
#endif
}
inline game::ArmyFlag20OccurrenceV1 Observe(const Bindings &b, const void *army,
    const game::ArmyPostAdmissionRefreshOccurrenceV1 &source) {
  game::ArmyFlag20OccurrenceV1 out{};
  out.native_index = source.native_index; out.raw_full_id_u32 = source.raw_full_id_u32;
  out.original_army_resolution = source.original_army_resolution;
  out.same_query_army_selection_matched = true;
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason; Finish(out, false); return out;
  };
  out.actual_army_20_raw_u8 = Read<std::uint8_t>(b.common, army, 0x20);
  out.army_1d4_raw_u8 = Read<std::uint8_t>(b.common, army, 0x1D4);
  if (!out.army_1d4_raw_u8) return fail("flag20_army1d4_unavailable");
  if (*out.army_1d4_raw_u8 == 0) {
    out.derived_current_20_raw_u8 = std::uint8_t{0}; out.current_flag20_inputs_ready = true;
    Finish(out, true); return out;
  }
  if (!b.get_current_flag20) return fail("flag20_current_getter_unbound");
  std::uint8_t value = 0;
  if (!Returned(b.get_current_flag20, value, army)) return fail("flag20_native_getter_unavailable");
  out.native_getter_returned = true; out.native_getter_20_raw_u8 = value;
  out.derived_current_20_raw_u8 = value; out.current_flag20_inputs_ready = true;
  Finish(out, true); return out;
}
}
inline game::ArmyCurrentFlag20InputsV1 ReadCurrentArmyFlag20Inputs12003(
    const CurrentArmyFlag20Bindings12003 &b,
    const game::ArmyCurrentPostAdmissionRefreshInputsV1 &same_query_refresh) noexcept {
  using namespace army_flag20_detail;
  game::ArmyCurrentFlag20InputsV1 out{};
  out.manager_loaded = same_query_refresh.manager_loaded; out.manager_identity = same_query_refresh.manager_identity;
  out.original_roster = same_query_refresh.original_roster;
  out.raw_roster_references_ready = out.original_roster.references_ready;
  try {
    CurrentPostAdmissionRefreshBindings12003 borrowed{}; borrowed.common = b.common;
    std::vector<post_admission_refresh_detail::ResolutionCacheRow> cache;
    for (const auto &raw : out.original_roster.occurrences) {
      game::ArmyFlag20OccurrenceV1 row{};
      row.native_index = raw.native_index; row.raw_full_id_u32 = raw.raw_full_id_u32;
      const auto source = std::find_if(same_query_refresh.occurrences.begin(), same_query_refresh.occurrences.end(),
          [&](const auto &p) { return p.native_index == raw.native_index && p.raw_full_id_u32 == raw.raw_full_id_u32; });
      if (source != same_query_refresh.occurrences.end()) row.original_army_resolution = source->original_army_resolution;
      if (!b.common.enabled) {
        row.unavailable_reason = "flag20_unbound"; Finish(row, false);
      } else {
        const auto selected = post_admission_refresh_detail::Selected(borrowed, raw.raw_full_id_u32, true, cache);
        if (source == same_query_refresh.occurrences.end() ||
            !post_admission_refresh_detail::SameSelected(source->original_army_resolution, selected, raw.raw_full_id_u32)) {
          row.unavailable_reason = "flag20_same_query_army_selection_unavailable"; Finish(row, false);
        } else row = Observe(b, selected.object, *source);
      }
      out.occurrences.push_back(std::move(row));
    }
    const bool covered = post_admission_refresh_detail::Covered(out.original_roster, out.occurrences.size());
    out.original_army_selections_ready = covered && std::all_of(out.occurrences.begin(), out.occurrences.end(),
        [](const auto &p) { return p.same_query_army_selection_matched; });
    out.current_flag20_inputs_ready = out.original_army_selections_ready &&
        std::all_of(out.occurrences.begin(), out.occurrences.end(), [](const auto &p) { return p.current_flag20_inputs_ready; });
    if (!out.current_flag20_inputs_ready) out.unavailable_reason = "flag20_current_inputs_incomplete";
    Finish(out, out.current_flag20_inputs_ready);
  } catch (...) { out.unavailable_reason = "flag20_collection_unavailable"; Finish(out, false); }
  return out;
}
}
