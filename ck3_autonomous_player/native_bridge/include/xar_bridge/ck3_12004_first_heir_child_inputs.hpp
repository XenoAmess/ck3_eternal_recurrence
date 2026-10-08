#pragma once

#include "xar_bridge/ck3_12004_first_heir_descendants.hpp"
#include "xar_bridge/ck3_12004_lifestyle.hpp"
#include "xar_bridge/current_first_heir_child_inputs_v1.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <algorithm>
#include <array>
#include <bit>
#include <cstring>

namespace xar::ck3_12004 {
namespace first_heir_child_inputs_detail {

// App-thread reads of admitted native objects. The public LIFE key decoder is
// reused solely for Trait stable keys; no player focus/lifestyle state is read.
inline bool ReadMemory(void *, std::uintptr_t address, void *output,
                       std::size_t size) noexcept {
  if (address == 0 || output == nullptr) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

using TraitDefinitions =
    std::array<const void *, ck3_11906::kChildhoodTraitKeysV1.size()>;

inline bool ReadTraitDefinitions(
    const ck3_11906::PlayerLifestyleSnapshotEnvironmentV1 &environment,
    TraitDefinitions &definitions) noexcept {
  using namespace first_heir_descendants_detail;
  definitions = {};
  if (environment.trait_database == nullptr ||
      environment.character_has_trait == nullptr) return false;
  const void *database = environment.trait_database();
  if (database == nullptr) return false;
  const auto data = Load<const void *const *>(database, 0x50);
  const auto count = Load<std::int32_t>(database, 0x5C);
  // These are the already qualified generic Trait DB span operands and
  // bound used by the native LIFE subset reader, not a child object layout.
  if (data == nullptr || count <= 0 || count > 8192) return false;
  for (std::int32_t index = 0; index < count; ++index) {
    const void *definition = data[index];
    if (definition == nullptr) return false;
    game::PlayerLifestyleStableKeyV1 key{};
    if (!lifestyle::ReadPlayerLifestyleMsvcStableKey12004V1(
            nullptr, ReadMemory,
            reinterpret_cast<std::uintptr_t>(definition) + 0x18, key))
      return false;
    const auto view = lifestyle::PlayerLifestyleStableKeyView12004V1(key);
    const auto found = std::find(ck3_11906::kChildhoodTraitKeysV1.begin(),
                                ck3_11906::kChildhoodTraitKeysV1.end(), view);
    if (found == ck3_11906::kChildhoodTraitKeysV1.end()) continue;
    const auto slot = static_cast<std::size_t>(
        found - ck3_11906::kChildhoodTraitKeysV1.begin());
    if (definitions[slot] != nullptr) return false;
    definitions[slot] = definition;
  }
  return std::all_of(definitions.begin(), definitions.end(),
                     [](const void *value) { return value != nullptr; });
}

inline ck3_11906::CurrentFirstHeirChildTraitsV1 ReadTraits(
    const ck3_11906::PlayerLifestyleSnapshotEnvironmentV1 &environment,
    const TraitDefinitions &definitions, void *character) noexcept {
  ck3_11906::CurrentFirstHeirChildTraitsV1 result{};
  if (character == nullptr || environment.character_has_trait == nullptr ||
      std::any_of(definitions.begin(), definitions.end(),
                  [](const void *value) { return value == nullptr; }))
    return result;
  std::array<bool, ck3_11906::kChildhoodTraitKeysV1.size()> first{}, second{};
  for (std::size_t index = 0; index < definitions.size(); ++index)
    first[index] = environment.character_has_trait(character, definitions[index]);
  for (std::size_t index = 0; index < definitions.size(); ++index)
    second[index] = environment.character_has_trait(character, definitions[index]);
  if (first != second) {
    result.unavailable_reason = "child_trait_values_changed";
    return result;
  }
  result.available = true;
  result.unavailable_reason = {};
  result.present_trait_keys.emplace();
  for (std::size_t index = 0; index < second.size(); ++index)
    if (second[index])
      result.present_trait_keys->push_back(ck3_11906::kChildhoodTraitKeysV1[index]);
  return result;
}

} // namespace first_heir_child_inputs_detail

// Receivers originate in the same current-first-heir raw descendant roster.
// Childhood traits and age/sex are independent reads. A lawful zero-age child
// and a complete empty trait subset are published as values, not failures.
inline ck3_11906::CurrentFirstHeirChildInputsReadV1
ReadCurrentFirstHeirChildInputsV1(
    const ck3_12002::FamilyBindings &bindings,
    const ck3_11906::PlayerLifestyleSnapshotEnvironmentV1 &trait_environment,
    const ck3_11906::CurrentFirstHeirDescendantsReadV1 &descendants) noexcept {
  using namespace first_heir_descendants_detail;
  using namespace first_heir_child_inputs_detail;
  ck3_11906::CurrentFirstHeirChildInputsReadV1 result{};
  result.played_character_id = descendants.played_character_id;
  result.heir_character_id = descendants.heir_character_id;
  result.date_raw = descendants.date_raw;
  CoreSnapshotPrefix before{}, after{};
  if (!descendants.roster_complete || !Frame(bindings, before) ||
      before.played_character_id != descendants.played_character_id ||
      !descendants.date_raw || before.clock.date_raw != *descendants.date_raw)
    return result;
  result.status = "available";
  result.unavailable_reason = {};
  for (const auto &occurrence : descendants.rows) {
    if (!occurrence.generation_valid || occurrence.alive != true ||
        occurrence.child_of_heir != true) continue;
    const auto id = std::bit_cast<std::int32_t>(occurrence.raw_character_id);
    auto found = std::find_if(result.rows.begin(), result.rows.end(),
        [id](const auto &row) { return row.character_id == id; });
    if (found == result.rows.end()) {
      ck3_11906::CurrentFirstHeirChildInputRowV1 row{};
      row.character_id = id;
      row.occurrence_indices.push_back(occurrence.occurrence_index);
      result.rows.push_back(std::move(row));
    } else {
      found->occurrence_indices.push_back(occurrence.occurrence_index);
    }
  }
  TraitDefinitions definitions{};
  if (!result.rows.empty()) (void)ReadTraitDefinitions(trait_environment, definitions);
  for (auto &row : result.rows) {
    ck3_12002::family_value::CharacterValue first{}, second{};
    if (ck3_12002::family_value::ReadCharacterValue(
            bindings.values, row.character_id, first, false,
            &row.values.unavailable_reason) &&
        ck3_12002::family_value::ReadCharacterValue(
            bindings.values, row.character_id, second, false,
            &row.values.unavailable_reason)) {
      if (first == second) {
        row.values.available = true;
        row.values.unavailable_reason = {};
        row.values.age_measure_raw = second.age_raw;
        row.values.sex_selector_raw = second.sex_selector_raw;
      } else {
        row.values.unavailable_reason = "child_character_values_changed";
      }
    }
    void *character = xar::ck3_12004::ResolveCoreCharacter(
        bindings.context.core, row.character_id);
    if (character != nullptr &&
        Load<void *>(character, kCharacterDeathDataOffset) == nullptr)
      row.childhood_traits = ReadTraits(trait_environment, definitions, character);
    else
      row.childhood_traits.unavailable_reason = "child_full_id_or_liveness_unavailable";
    if (!row.values.available || !row.childhood_traits.available) {
      result.status = "partial";
      result.unavailable_reason = "current_heir_child_inputs_partial";
    }
  }
  if (!Frame(bindings, after) || !SameFrame(before, after)) {
    result.status = "unavailable";
    result.unavailable_reason = "current_heir_child_frame_changed";
    result.rows.clear();
  }
  return result;
}

} // namespace xar::ck3_12004
#endif
