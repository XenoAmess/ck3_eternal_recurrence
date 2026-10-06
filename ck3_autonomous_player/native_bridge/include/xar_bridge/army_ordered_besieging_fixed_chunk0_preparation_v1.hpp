#pragma once
#include "xar_bridge/ck3_12003_fixed_chunk0_preparation.hpp"

namespace xar::game {
struct ArmyOrderedBesiegingFixedChunk0PreparationInputsV1 {
  FixedChunk0PreparationInputStatusV1 status = FixedChunk0PreparationInputStatusV1::unavailable;
  FixedChunk0PreparationInputStatusV1 source_scope_status = FixedChunk0PreparationInputStatusV1::unavailable;
  std::string_view unavailable_reason{};
  std::int32_t subject_army_id = -1, subject_carmy_id = -1, province_id = -1;
  bool target_persistent_ids_complete = false;
  std::vector<FixedChunk0PreparationPersistentInputV1> persistent_regiments;
  friend bool operator==(const ArmyOrderedBesiegingFixedChunk0PreparationInputsV1 &,
                         const ArmyOrderedBesiegingFixedChunk0PreparationInputsV1 &) = default;
};
} // namespace xar::game
