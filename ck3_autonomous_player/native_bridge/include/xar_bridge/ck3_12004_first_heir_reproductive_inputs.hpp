#pragma once

#include "xar_bridge/ck3_12004_first_heir_descendants.hpp"
#include "xar_bridge/current_first_heir_reproductive_inputs_v1.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <algorithm>

namespace xar::ck3_12004 {

// Reuses the independently bound actual4 CharacterValue reader. Current
// relationships own the receivers; neither an arbitrary pair nor a prospective
// marriage context is needed for an already married household.
inline ck3_11906::CurrentFirstHeirReproductiveInputsV1
ReadCurrentFirstHeirReproductiveInputsV1(
    const ck3_12002::FamilyBindings &bindings,
    const ck3_11906::CurrentFirstHeirRelationshipReadV1 &relationship) noexcept {
  using namespace first_heir_descendants_detail;
  ck3_11906::CurrentFirstHeirReproductiveInputsV1 result{};
  result.heir_character_id = relationship.heir_character_id;
  CoreSnapshotPrefix before{}, after{};
  if (!Frame(bindings, before) || relationship.failure !=
          ck3_11906::CurrentFirstHeirRelationshipFailureV1::none) {
    result.unavailable_reason = "current_household_relation_unavailable";
    return result;
  }
  result.played_character_id = before.played_character_id;
  result.date_raw = before.clock.date_raw;
  const auto add = [&](std::int32_t id, std::string_view role) {
    if (id <= 0) return;
    auto found = std::find_if(result.rows.begin(), result.rows.end(),
        [id](const auto &row) { return row.character_id == id; });
    if (found == result.rows.end()) {
      ck3_11906::CurrentFirstHeirReproductiveRowV1 row{};
      row.character_id = id;
      row.roles.push_back(role);
      result.rows.push_back(std::move(row));
    } else if (std::find(found->roles.begin(), found->roles.end(), role) ==
                   found->roles.end()) {
      found->roles.push_back(role);
    }
  };
  add(relationship.heir_character_id, "heir");
  add(relationship.relationship.primary_spouse_character_id, "primary_spouse");
  for (const auto id : relationship.relationship.spouse_character_ids)
    add(id, "spouse");
  add(relationship.relationship.betrothed_character_id, "betrothed");
  result.status = "available";
  result.unavailable_reason = {};
  for (auto &row : result.rows) {
    ck3_12002::family_value::CharacterValue first{}, second{};
    if (!ck3_12002::family_value::ReadCharacterValue(
            bindings.values, row.character_id, first, true,
            &row.unavailable_reason) ||
        !ck3_12002::family_value::ReadCharacterValue(
            bindings.values, row.character_id, second, true,
            &row.unavailable_reason)) {
      result.status = "partial";
      result.unavailable_reason = "current_household_value_partial";
      continue;
    }
    if (first != second) {
      row.unavailable_reason = "current_household_value_changed";
      result.status = "partial";
      result.unavailable_reason = "current_household_value_partial";
      continue;
    }
    row.available = true;
    row.unavailable_reason = {};
    row.age_measure_raw = second.age_raw;
    row.sex_selector_raw = second.sex_selector_raw;
    const auto &fertility = second.fertility;
    row.fertility = {fertility.available, fertility.extension_present,
        fertility.native_gate_evaluated, fertility.native_gate_allows,
        fertility.effective_raw};
  }
  const auto checked = ck3_12002::ReadCurrentFirstHeirRelationshipV1(
      bindings, relationship.heir_character_id);
  if (!Frame(bindings, after) || !SameFrame(before, after) ||
      checked.failure != ck3_11906::CurrentFirstHeirRelationshipFailureV1::none ||
      checked.relationship != relationship.relationship) {
    result.status = "unavailable";
    result.unavailable_reason = "current_household_frame_changed";
    result.rows.clear();
  }
  return result;
}

} // namespace xar::ck3_12004
#endif
