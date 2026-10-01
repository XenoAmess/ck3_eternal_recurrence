#pragma once

#include "xar_bridge/ck3_12002_family.hpp"

namespace xar::ck3_12002 {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

// 1.20 inlines the registered is_child_of native predicate. Production binds
// its exact parent-ID comparison mirror, rather than calling a trigger wrapper
// with the legacy bool(Character*, Character*) ABI. Tests can supply a callback.
using FamilySubjectIsChildOf = bool (*)(void *child, void *parent);

struct FamilySubjectBindings {
  bool enabled = false;
  FamilyBindings family{};
  FamilySubjectIsChildOf is_character_child_of = nullptr;
  void **house_storage_slot = nullptr;
  void **house_fallback_slot = nullptr;
  void **dynasty_storage_slot = nullptr;
  void **dynasty_fallback_slot = nullptr;
};

// The retained base fields are the private serializer's existing subject ABI.
// Actual adulthood is observed independently of proposal final legality. Child
// identity never grants first-heir status or another matchmaker's permissions.
struct PlayerChildMarriageSubjectRead12002
    : ck3_11906::PlayerChildMarriageSubjectReadV1 {
  bool subject_is_player_child = false;
  bool adult_readback_available = false;
  std::uint8_t adult_selector_raw = 0;
  std::int32_t adult_threshold_raw = 0;
  bool is_adult = false;
  std::string_view unavailable_reason = "subject_unavailable";
};
using PlayerChildMarriageSubjectReadV1 = PlayerChildMarriageSubjectRead12002;
using PlayerChildMarriageSubjectFailureV1 = ck3_11906::PlayerChildMarriageSubjectFailureV1;
using PlayerFamilyArrayProbeV1 = ck3_11906::PlayerFamilyArrayProbeV1;

FamilySubjectBindings BindFamilySubjectImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

PlayerChildMarriageSubjectRead12002 ReadPlayerChildMarriageSubjectV1(
    const FamilySubjectBindings &, std::int32_t subject_character_id) noexcept;

// A bounded diagnostic of proven named native collections. No arbitrary
// memory slot becomes a child list or proposal authority from its shape.
ck3_11906::PlayerFamilyArrayProbeV1 ReadPlayerFamilyArrayProbeV1(
    const FamilySubjectBindings &, std::int32_t played_character_id) noexcept;

#endif
} // namespace xar::ck3_12002
