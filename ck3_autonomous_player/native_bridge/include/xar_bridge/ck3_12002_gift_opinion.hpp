#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <cstdint>
#include <optional>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kGiftReadCharacterOpinionRva12002 = 0x28BC490;
inline constexpr std::uintptr_t kGiftOpinionModifierDatabaseSlotRva12002 = 0x5D207E0;
inline constexpr std::uintptr_t kGiftOpinionModifierLookupRva12002 = 0x25A2F00;
inline constexpr std::uintptr_t kGiftFindActiveOpinionGroupRva12002 = 0x2949AA0;
inline constexpr std::uintptr_t kGiftSumOpinionModifierRva12002 = 0x25962B0;
inline constexpr std::uintptr_t kGiftOpinionModifierVtableRva12002 = 0x48C5370;
inline constexpr std::uintptr_t kGiftOpinionModifierSecondaryVtableRva12002 = 0x48C5338;
inline constexpr std::uintptr_t kGiftActiveOpinionVtableRva12002 = 0x473DE08;
inline constexpr std::uintptr_t kGiftTemporaryOpinionVtableRva12002 = 0x473DDD0;

struct GiftOpinionResult {
  bool query_complete = false;
  std::int32_t recipient_opinion_of_player = 0;
  bool gift_opinion_present = false;
  std::optional<std::int32_t> gift_opinion_modifier_value;
};

using GiftReadCharacterOpinion12002 = std::int32_t (*)(void *, void *);
using GiftLookupOpinionModifier12002 = void *(*)(void *, std::uint32_t);
using GiftFindOpinionGroup12002 = void *(*)(void *, std::uint32_t);
using GiftSumOpinionModifier12002 = std::int32_t (*)(void *, void *);

// Production binds these functions to the reviewed image. The same reader
// runs against fixture-owned stores and callbacks in the offline C++ test.
struct GiftOpinionBindings12002 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  CoreBindings core;
  void **modifier_database_slot = nullptr;
  GiftReadCharacterOpinion12002 read_opinion = nullptr;
  GiftLookupOpinionModifier12002 lookup_modifier = nullptr;
  GiftFindOpinionGroup12002 find_group = nullptr;
  GiftSumOpinionModifier12002 sum_modifier = nullptr;
  std::uintptr_t modifier_primary_vtable = 0;
  std::uintptr_t modifier_secondary_vtable = 0;
  std::uintptr_t active_opinion_vtable = 0;
  std::uintptr_t temporary_opinion_vtable = 0;
};

GiftOpinionBindings12002 BindGiftOpinionImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

bool ReadGiftOpinion12002(const GiftOpinionBindings12002 &bindings,
                         std::uint32_t recipient_character_id,
                         std::uint32_t player_character_id,
                         GiftOpinionResult &output) noexcept;

bool ReadGiftOpinionExact12002(std::uintptr_t module_base,
                              const CoreBindings &core,
                              std::uint32_t recipient_character_id,
                              std::uint32_t player_character_id,
                              GiftOpinionResult &output) noexcept;

// Independent total-opinion query for Sway and gift receipts. No gift
// definition is required. The owner is the recipient, toward is the actor.
bool ReadCharacterOpinion12002(std::uintptr_t module_base,
                              const CoreBindings &core,
                              std::uint32_t recipient_character_id,
                              std::uint32_t player_character_id,
                              std::int32_t &output) noexcept;

using GiftNamedDatabase12002 = void *(*)();
using GiftLookupNamed12002 = const void *(*)(void *, std::uint32_t);
using GiftCloneScope12002 = void *(*)(void *, const void *);
using GiftConstructSupport12002 = void *(*)(void *);
using GiftInternString12002 = const void *(*)(void *, const void *);
using GiftEvaluateNamedFixed12002 = std::int64_t *(*)(
    const void *, std::int64_t *, void *, void *, const void *);
using GiftDestroyScopePart12002 = void (*)(void *);

struct GiftNamedOpinionBindings12002 {
  bool enabled = false;
  CoreBindings core;
  GiftNamedDatabase12002 named_database = nullptr;
  GiftLookupNamed12002 lookup_named = nullptr;
  GiftCloneScope12002 clone_scope = nullptr;
  GiftConstructSupport12002 construct_support_118 = nullptr;
  GiftConstructSupport12002 construct_support_2a8 = nullptr;
  GiftNamedDatabase12002 intern_database = nullptr;
  GiftInternString12002 intern_string = nullptr;
  GiftEvaluateNamedFixed12002 evaluate_fixed = nullptr;
  GiftDestroyScopePart12002 destroy_scope_tail = nullptr;
  GiftDestroyScopePart12002 destroy_scope_rows = nullptr;
  GiftDestroyScopePart12002 destroy_support_rows = nullptr;
  const std::uint8_t *evaluation_flag = nullptr;
  std::uintptr_t named_primary_vtable = 0;
  std::uintptr_t named_secondary_vtable = 0;
};

GiftNamedOpinionBindings12002 BindGiftNamedOpinionImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

bool ReadGiftOpinionDelta12002(const GiftNamedOpinionBindings12002 &bindings,
                             const void *character_interaction_scope,
                             std::uint32_t recipient_character_id,
                             std::uint32_t player_character_id,
                             std::int32_t &opinion_delta) noexcept;

// Shared with gift/ransom: evaluates one native named value in a borrowed
// prepared interaction scope, with the stock caller's character as root.
// Keeping the native Q100000 result avoids inventing or rounding gold costs.
bool ReadNamedInteractionFixed12002(
    const GiftNamedOpinionBindings12002 &bindings,
    const void *character_interaction_scope, std::uint32_t root_character_id,
    std::uint32_t actor_character_id, std::uint32_t recipient_character_id,
    std::string_view canonical_key, std::uint32_t stable_hash,
    std::int64_t &output) noexcept;
bool ReadNamedInteractionFixedExact12002(
    std::uintptr_t module_base, const void *character_interaction_scope,
    std::uint32_t root_character_id, std::uint32_t actor_character_id,
    std::uint32_t recipient_character_id, std::string_view canonical_key,
    std::uint32_t stable_hash, std::int64_t &output) noexcept;
bool ReadGiftValueExact12002(std::uintptr_t module_base,
                           const void *character_interaction_scope,
                           std::uint32_t recipient_character_id,
                           std::uint32_t actor_character_id,
                           std::int64_t &gold_raw) noexcept;

// Borrows the already prepared interaction scope for this synchronous call.
// It clones actor/recipient aliases, changes only root to the recipient and
// evaluates the native named value; it never sends an interaction.
bool ReadGiftOpinionDeltaExact12002(std::uintptr_t module_base,
                                   const void *character_interaction_scope,
                                   std::uint32_t recipient_character_id,
                                   std::uint32_t player_character_id,
                                   std::int32_t &opinion_delta) noexcept;

bool ConvertGiftOpinionFixed12002(std::int64_t raw,
                                 std::int32_t &output) noexcept;

} // namespace xar::ck3_12002
