#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_pending_context.hpp"

namespace xar::ck3_12004 {

// Actual4 source joins and exact named RTTI chains: see the pending context
// migration topic. Environment/Access/Request and result are software DTOs.
inline constexpr std::uintptr_t kPendingStorageRva12004 = 0x5D1EC80;
inline constexpr std::uintptr_t kPendingCharacterStorageRva12004 = 0x5C67568;
inline constexpr std::uintptr_t kPendingExpirationDaysRva12004 = 0x5C68CFC;
inline constexpr std::uintptr_t kPendingLocalRoutingRva12004 = 0x136D190;
inline constexpr std::uintptr_t kPendingReplyValidatorRva12004 = 0x2968470;
inline constexpr std::uintptr_t kPendingTriggerEvaluatorRva12004 = 0x372DF10;
inline constexpr std::uintptr_t kPendingCostEvaluatorRva12004 = 0x310CEC0;
inline constexpr std::uintptr_t kPendingCommonWarRelationRva12004 = 0x28BC250;
inline constexpr std::uintptr_t kPendingTargetRegistryGetterRva12004 = 0x3795A60;
inline constexpr std::uintptr_t kPendingTargetRegistryRva12004 = 0x54F2AF0;
inline constexpr std::uintptr_t kPendingIdentifierNameRva12004 = 0x3F4F8E0;
inline constexpr std::uintptr_t kPendingReplyPrimaryVtableRva12004 = 0x448BC28;
inline constexpr std::uintptr_t kPendingReplySecondaryVtableRva12004 = 0x448BBF8;
inline constexpr std::uintptr_t kPendingWarVictoryVtableRva12004 = 0x46C3AB0;
inline constexpr std::uintptr_t kPendingWarWhitePeaceVtableRva12004 = 0x46C3B20;
inline constexpr std::uintptr_t kPendingWarDefeatVtableRva12004 = 0x46C3B90;

// Inline preserves the old standalone reader's link dependencies. Actual4
// production admission does not use the fixture function-override flag.
inline bool MatchesPendingCharacterInteractionEnvironment12004(
    const ck3_12002::PendingCharacterInteractionNativeEnvironmentV1 &env) noexcept {
  if (!env.exact_build_admitted || env.module_base == 0 ||
      env.offline_fixture_function_overrides) return false;
  const auto base = env.module_base;
  return reinterpret_cast<std::uintptr_t>(env.pending_storage_slot) ==
             base + kPendingStorageRva12004 &&
         reinterpret_cast<std::uintptr_t>(env.character_storage_slot) ==
             base + kPendingCharacterStorageRva12004 &&
         reinterpret_cast<std::uintptr_t>(env.expiration_days) ==
             base + kPendingExpirationDaysRva12004 &&
         reinterpret_cast<std::uintptr_t>(env.local_routing) ==
             base + kPendingLocalRoutingRva12004 &&
         reinterpret_cast<std::uintptr_t>(env.reply_validator) ==
             base + kPendingReplyValidatorRva12004 &&
         reinterpret_cast<std::uintptr_t>(env.trigger_evaluator) ==
             base + kPendingTriggerEvaluatorRva12004 &&
         reinterpret_cast<std::uintptr_t>(env.cost_evaluator) ==
             base + kPendingCostEvaluatorRva12004 &&
         reinterpret_cast<std::uintptr_t>(env.common_war_relation) ==
             base + kPendingCommonWarRelationRva12004 &&
         reinterpret_cast<std::uintptr_t>(env.target_type_registry) ==
             base + kPendingTargetRegistryGetterRva12004 &&
         reinterpret_cast<std::uintptr_t>(env.script_identifier_name) ==
             base + kPendingIdentifierNameRva12004 &&
         env.reply_primary_vtable == base + kPendingReplyPrimaryVtableRva12004 &&
         env.reply_secondary_vtable == base + kPendingReplySecondaryVtableRva12004 &&
         env.war_victory_special_vtable == base + kPendingWarVictoryVtableRva12004 &&
         env.war_white_peace_special_vtable ==
             base + kPendingWarWhitePeaceVtableRva12004 &&
         env.war_defeat_special_vtable == base + kPendingWarDefeatVtableRva12004;
}

ck3_12002::PendingCharacterInteractionNativeEnvironmentV1
BindPendingCharacterInteractionNativeEnvironment12004(
    std::uintptr_t module_base,
    std::string_view actual_executable_sha256) noexcept;

// Owning-thread caller supplies its existing frame and guarded native
// invokers. The wrapper installs actual4 received-ransom helpers.
game::ReadPendingCharacterInteractionContextResultV1
ReadPendingCharacterInteractionContext12004(
    const ck3_12002::PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const ck3_12002::PendingCharacterInteractionAccessV1 &access,
    const ck3_12002::PendingCharacterInteractionContextRequestV1 &request,
    game::PendingCharacterInteractionContextV1 &output) noexcept;

std::string SerializePendingCharacterInteractionContext12004(
    const game::PendingCharacterInteractionContextV1 &context);

} // namespace xar::ck3_12004
