#pragma once

#include "xar_bridge/ck3_12002_world.hpp"
#include "xar_bridge/ck3_12002_province.hpp"
#include "xar_bridge/war_occupation_targets_v1.hpp"

#include <cstddef>

namespace xar::ck3_12003 {

// Exact .3 CArray<T*> ABI. Inputs are borrowed CWar participant arrays;
// outputs own a native-allocator allocation and release it through vtable +0x10.
struct WarOccupationPointerVector {
  void **data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *allocator = nullptr;
};
static_assert(sizeof(WarOccupationPointerVector) == 0x18);
static_assert(offsetof(WarOccupationPointerVector, count) == 0x0C);

struct WarOccupationNativeCounts {
  std::int32_t occupied = 0;
  std::int32_t eligible = 0;
};
static_assert(sizeof(WarOccupationNativeCounts) == 8);

struct WarOccupationTargetsBindingsV1 {
  bool enabled = false;
  ck3_12002::WorldBindings world;
  ck3_12002::ProvinceBindings provinces;
  void **character_storage_slot = nullptr;
  void *vector_allocator = nullptr;
  void *(*get_war_occupation_context)(std::int32_t war_id) = nullptr;
  void (*collect_territory_participants)(
      void *context, std::int32_t primary_territory_character_id,
      const WarOccupationPointerVector *territory_participants,
      const WarOccupationPointerVector *opposing_participants,
      WarOccupationPointerVector *output) = nullptr;
  void (*collect_holding_titles)(void *character,
                                WarOccupationPointerVector *output) = nullptr;
  void (*count_holding)(
      void *holding_title, const WarOccupationPointerVector *opposing_participants,
      const WarOccupationPointerVector *territory_participants,
      bool skip_holder_filter, WarOccupationNativeCounts *output) = nullptr;
  bool (*war_participants_are_liege_related)(void *war) = nullptr;
};

using WarOccupationTargetsReadResultV1 = game::ReadWarOccupationTargetsV1Result;

WarOccupationTargetsBindingsV1 BindWarOccupationTargetsImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
WarOccupationTargetsReadResultV1 ReadWarOccupationTargetsV1(
    const WarOccupationTargetsBindingsV1 &bindings,
    const game::Snapshot &paused_scope, std::int32_t war_id,
    game::WarOccupationTargetsV1 &output) noexcept;

} // namespace xar::ck3_12003
