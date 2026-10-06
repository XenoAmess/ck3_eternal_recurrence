#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_gift_opinion.hpp"

#include <cstdint>
#include <optional>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kGiftReadCharacterOpinionRva12004 = 0x28BC470;
inline constexpr std::uintptr_t kGiftOpinionModifierDatabaseSlotRva12004 = 0x5D207E0;
inline constexpr std::uintptr_t kGiftOpinionModifierLookupRva12004 = 0x25A2EE0;
inline constexpr std::uintptr_t kGiftFindActiveOpinionGroupRva12004 = 0x2949A80;
inline constexpr std::uintptr_t kGiftSumOpinionModifierRva12004 = 0x2596290;
inline constexpr std::uintptr_t kGiftOpinionModifierVtableRva12004 = 0x48C5380;
inline constexpr std::uintptr_t kGiftOpinionModifierSecondaryVtableRva12004 = 0x48C5348;
inline constexpr std::uintptr_t kGiftActiveOpinionVtableRva12004 = 0x473DE18;
inline constexpr std::uintptr_t kGiftTemporaryOpinionVtableRva12004 = 0x473DDE0;

using GiftOpinionResult = ck3_12002::GiftOpinionResult;

using GiftReadCharacterOpinion12004 = std::int32_t (*)(void *, void *);
using GiftLookupOpinionModifier12004 = void *(*)(void *, std::uint32_t);
using GiftFindOpinionGroup12004 = void *(*)(void *, std::uint32_t);
using GiftSumOpinionModifier12004 = std::int32_t (*)(void *, void *);

// Production binds these functions to the reviewed image. The same reader
// runs against fixture-owned stores and callbacks in the offline C++ test.
struct GiftOpinionBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  CoreBindings core;
  void **modifier_database_slot = nullptr;
  GiftReadCharacterOpinion12004 read_opinion = nullptr;
  GiftLookupOpinionModifier12004 lookup_modifier = nullptr;
  GiftFindOpinionGroup12004 find_group = nullptr;
  GiftSumOpinionModifier12004 sum_modifier = nullptr;
  std::uintptr_t modifier_primary_vtable = 0;
  std::uintptr_t modifier_secondary_vtable = 0;
  std::uintptr_t active_opinion_vtable = 0;
  std::uintptr_t temporary_opinion_vtable = 0;
};

GiftOpinionBindings12004 BindGiftOpinionImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

bool ReadGiftOpinion12004(const GiftOpinionBindings12004 &bindings,
                         std::uint32_t recipient_character_id,
                         std::uint32_t player_character_id,
                         GiftOpinionResult &output) noexcept;

bool ReadGiftOpinionExact12004(std::uintptr_t module_base,
                              const CoreBindings &core,
                              std::uint32_t recipient_character_id,
                              std::uint32_t player_character_id,
                              GiftOpinionResult &output) noexcept;

// Independent total-opinion query for Sway and gift receipts. No gift
// definition is required. The owner is the recipient, toward is the actor.
bool ReadCharacterOpinion12004(std::uintptr_t module_base,
                              const CoreBindings &core,
                              std::uint32_t recipient_character_id,
                              std::uint32_t player_character_id,
                              std::int32_t &output) noexcept;

using GiftNamedDatabase12004 = void *(*)();
using GiftLookupNamed12004 = const void *(*)(void *, std::uint32_t);
using GiftCloneScope12004 = void *(*)(void *, const void *);
using GiftConstructSupport12004 = void *(*)(void *);
using GiftInternString12004 = const void *(*)(void *, const void *);
using GiftEvaluateNamedFixed12004 = std::int64_t *(*)(
    const void *, std::int64_t *, void *, void *, const void *);
using GiftDestroyScopePart12004 = void (*)(void *);

struct GiftNamedOpinionBindings12004 {
  bool enabled = false;
  CoreBindings core;
  GiftNamedDatabase12004 named_database = nullptr;
  GiftLookupNamed12004 lookup_named = nullptr;
  GiftCloneScope12004 clone_scope = nullptr;
  GiftConstructSupport12004 construct_support_118 = nullptr;
  GiftConstructSupport12004 construct_support_2a8 = nullptr;
  GiftNamedDatabase12004 intern_database = nullptr;
  GiftInternString12004 intern_string = nullptr;
  GiftEvaluateNamedFixed12004 evaluate_fixed = nullptr;
  GiftDestroyScopePart12004 destroy_scope_tail = nullptr;
  GiftDestroyScopePart12004 destroy_scope_rows = nullptr;
  GiftDestroyScopePart12004 destroy_support_rows = nullptr;
  const std::uint8_t *evaluation_flag = nullptr;
  std::uintptr_t named_primary_vtable = 0;
  std::uintptr_t named_secondary_vtable = 0;
};

GiftNamedOpinionBindings12004 BindGiftNamedOpinionImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

bool ReadGiftOpinionDelta12004(const GiftNamedOpinionBindings12004 &bindings,
                             const void *character_interaction_scope,
                             std::uint32_t recipient_character_id,
                             std::uint32_t player_character_id,
                             std::int32_t &opinion_delta) noexcept;

// Shared with gift/ransom: evaluates one native named value in a borrowed
// prepared interaction scope, with the stock caller's character as root.
// Keeping the native Q100000 result avoids inventing or rounding gold costs.
bool ReadNamedInteractionFixed12004(
    const GiftNamedOpinionBindings12004 &bindings,
    const void *character_interaction_scope, std::uint32_t root_character_id,
    std::uint32_t actor_character_id, std::uint32_t recipient_character_id,
    std::string_view canonical_key, std::uint32_t stable_hash,
    std::int64_t &output) noexcept;
bool ReadNamedInteractionFixedExact12004(
    std::uintptr_t module_base, const void *character_interaction_scope,
    std::uint32_t root_character_id, std::uint32_t actor_character_id,
    std::uint32_t recipient_character_id, std::string_view canonical_key,
    std::uint32_t stable_hash, std::int64_t &output) noexcept;
bool ReadGiftValueExact12004(std::uintptr_t module_base,
                           const void *character_interaction_scope,
                           std::uint32_t recipient_character_id,
                           std::uint32_t actor_character_id,
                           std::int64_t &gold_raw) noexcept;

// Borrows the already prepared interaction scope for this synchronous call.
// It clones actor/recipient aliases, changes only root to the recipient and
// evaluates the native named value; it never sends an interaction.
bool ReadGiftOpinionDeltaExact12004(std::uintptr_t module_base,
                                   const void *character_interaction_scope,
                                   std::uint32_t recipient_character_id,
                                   std::uint32_t player_character_id,
                                   std::int32_t &opinion_delta) noexcept;

bool ConvertGiftOpinionFixed12004(std::int64_t raw,
                                 std::int32_t &output) noexcept;

// Retain the already adopted Activity binding API.
// Actual .4 opinion entry/operand proof: activity/guest-cost-native/gift-opinion.
// Only total opinion and the existing Feast modifier surface are migrated.
inline constexpr std::uintptr_t kReadCharacterOpinionRva = 0x28BC470;
inline constexpr std::uintptr_t kOpinionModifierDatabaseSlotRva = 0x5D207E0;
inline constexpr std::uintptr_t kOpinionModifierLookupRva = 0x25A2EE0;
inline constexpr std::uintptr_t kFindActiveOpinionGroupRva = 0x2949A80;
inline constexpr std::uintptr_t kSumOpinionModifierRva = 0x2596290;
inline constexpr std::uintptr_t kOpinionModifierVtableRva = 0x48C5380;
inline constexpr std::uintptr_t kOpinionModifierSecondaryVtableRva = 0x48C5348;
inline constexpr std::uintptr_t kActiveOpinionVtableRva = 0x473DE18;
inline constexpr std::uintptr_t kTemporaryOpinionVtableRva = 0x473DDE0;
inline constexpr std::uintptr_t kOpinionStableKeyHashRva = 0x3F7E220;

ck3_12002::GiftOpinionBindings12002 BindGiftOpinionImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Owner is the recipient; toward is the player actor. Caller-owned bindings
// also permit an offline fixture to exercise this same repeated native read.
bool ReadCharacterOpinion(
    const ck3_12002::GiftOpinionBindings12002 &bindings,
    std::uint32_t recipient_character_id, std::uint32_t player_character_id,
    std::int32_t &output) noexcept;

} // namespace xar::ck3_12004
