#pragma once

#include "xar_bridge/ck3_12002_gift_opinion.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {

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
