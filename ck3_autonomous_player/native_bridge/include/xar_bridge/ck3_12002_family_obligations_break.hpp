#pragma once

#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_family_obligations_break_penalty.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kFamilyBreakDatabaseGetterRvaV1 = 0x89DA60;
inline constexpr std::uintptr_t kFamilyBreakStableHashRvaV1 = 0x3F7E240;
inline constexpr std::uintptr_t kFamilyBreakLookupDefinitionRvaV1 = 0xA055E0;
inline constexpr std::uintptr_t kFamilyBreakMissingDefinitionSlotRvaV1 = 0x5D1DD28;
inline constexpr std::size_t kFamilyBreakDefinitionOrdinalOffsetV1 = 0x10;
inline constexpr std::size_t kFamilyBreakDefinitionHashOffsetV1 = 0x14;
inline constexpr std::size_t kFamilyBreakDefinitionKeyOffsetV1 = 0x18;
inline constexpr std::size_t kFamilyBreakDefinitionKindOffsetV1 = 0x38;
inline constexpr std::uint32_t kFamilyBreakDefinitionKindV1 = 0x4744624F;
inline constexpr std::string_view kFamilyBreakDefinitionKeyV1 = "break_betrothal_interaction";

using FamilyBreakDatabaseGetterV1 = void *(*)();
using FamilyBreakStableHashV1 = std::int32_t (*)(void *, const char *, std::uint32_t);
using FamilyBreakLookupDefinitionV1 = void *(*)(void *, std::int32_t);

struct FamilyObligationsBreakBindingsV1 {
  bool enabled = false;
  ContextBindings interaction{};
  family_break_penalty::Bindings penalty{};
  FamilyBreakDatabaseGetterV1 get_database = nullptr;
  FamilyBreakStableHashV1 stable_hash = nullptr;
  FamilyBreakLookupDefinitionV1 lookup_definition = nullptr;
  void **missing_definition_slot = nullptr;
};

enum class FamilyObligationsBreakStatusV1 { unavailable, no_betrothal, available };

struct FamilyObligationsBreakTermsV1 {
  FamilyObligationsBreakStatusV1 status = FamilyObligationsBreakStatusV1::unavailable;
  std::int32_t actor_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t betrothed_character_id = -1;
  std::int32_t requested_recipient_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::int32_t secondary_actor_character_id = -1;
  std::int32_t secondary_recipient_character_id = -1;
  std::int32_t intermediary_character_id = -1;
  std::int32_t definition_ordinal = -1;
  std::uint32_t definition_stable_hash = 0;
  bool final_legality_sampled = false;
  bool complete_can_send = false;
  bool native_send_costs_available = false;
  // Native charge-vector order: gold, prestige, piety, renown, influence,
  // herd, treasury, treasury_or_gold, merit, barter_goods; scale 100000.
  // These are send charges. Conditional on_accept prestige/opinion loss and
  // Grand Wedding prestige-level loss are separate outcome effects.
  std::array<std::int64_t, 10> native_send_costs_raw{};
  family_break_penalty::Penalty outcome_resource_penalty{};
  std::string_view unavailable_reason = "break_betrothal_source_unavailable";
};

FamilyObligationsBreakBindingsV1 BindFamilyObligationsBreakImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Runs on the already established owner thread. Native redirection receives
// the explicit interaction recipient and the independently observed subject /
// current partner. It never selects a different person or sends a command.
FamilyObligationsBreakTermsV1 ReadFamilyObligationsBreakTermsV1(
    const FamilyObligationsBreakBindingsV1 &, std::int32_t subject_character_id,
    std::int32_t interaction_recipient_character_id) noexcept;

} // namespace xar::ck3_12002
