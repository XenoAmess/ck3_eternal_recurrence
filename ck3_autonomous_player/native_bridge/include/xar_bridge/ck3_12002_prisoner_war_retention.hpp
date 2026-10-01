#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_province.hpp"
#include "xar_bridge/ck3_12002_world.hpp"

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kWarRetentionPrimaryTitleRva = 0x289DA30;
inline constexpr std::uintptr_t kWarRetentionImprisonedByRva = 0x289E830;
inline constexpr std::size_t kWarRetentionCharacterExtensionOffset = 0x1B0;
inline constexpr std::size_t kWarRetentionCustodyRelationOffset = 0x288;
inline constexpr std::size_t kWarRetentionJailerIdOffset = 0x00;
inline constexpr std::size_t kWarRetentionSuccessorDataOffset = 0x150;
inline constexpr std::size_t kWarRetentionSuccessorCapacityOffset = 0x158;
inline constexpr std::size_t kWarRetentionSuccessorCountOffset = 0x15C;

using WarRetentionCharacterGetter12002 = void *(*)(void *);
struct PrisonerWarRetentionBindings {
  bool enabled = false;
  CoreBindings core;
  WorldBindings world;
  ProvinceBindings titles;
  WarRetentionCharacterGetter12002 primary_title = nullptr;
  WarRetentionCharacterGetter12002 imprisoned_by = nullptr;
};

// Address calculation only. The live caller supplies an already qualified
// image identity and executes the reader on the application's owning thread.
PrisonerWarRetentionBindings BindPrisonerWarRetentionImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Reuses the existing portable wire DTO. Names in its historical namespace
// do not select a game build. This only reads the generic effect's input graph;
// it does not execute or preview loaded effects, price retention or exit wars.
ck3_11906::ReadWarPrisonerReleasePairsResultV1 ReadWarPrisonerReleasePairsV1(
    const PrisonerWarRetentionBindings &, std::int32_t war_id,
    ck3_11906::WarPrisonerReleasePairsObservationV1 &) noexcept;

} // namespace xar::ck3_12002
