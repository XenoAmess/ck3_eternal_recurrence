#include "xar_bridge/ck3_12004_faction_alerts.hpp"

namespace xar::ck3_12004 {

PlayerFactionAlertsNativeEnvironmentV1 BindPlayerFactionAlertsImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  PlayerFactionAlertsNativeEnvironmentV1 environment{};
  const auto core = ck3_12004::BindCoreImage(base, sha);
  if (!core.enabled) return environment;
  environment.module_base = base;
  environment.exact_build_admitted = true;
  environment.character_storage_slot = core.character_storage_slot;
  environment.character_fallback_slot = reinterpret_cast<void **>(base + 0x5C67570);
  environment.faction_storage_slot = reinterpret_cast<void **>(base + 0x5D1DE90);
  environment.faction_fallback_slot = reinterpret_cast<void **>(base + 0x5D1DE10);
  environment.landed_title_storage_slot = reinterpret_cast<void **>(base + 0x5D1DAF8);
  environment.landed_title_fallback_slot = reinterpret_cast<void **>(base + 0x5D1DAE0);
  environment.war_storage_slot = reinterpret_cast<void **>(base + 0x5D1DE58);
  environment.war_fallback_slot = reinterpret_cast<void **>(base + 0x5D1DE40);
  environment.vassal_contract_storage_slot = reinterpret_cast<void **>(base + 0x5D1EB88);
  environment.vassal_contract_fallback_slot = reinterpret_cast<void **>(base + 0x5D1EB40);
  environment.expected_faction_vtable = base + 0x4743530;
  environment.immediate_liege = reinterpret_cast<
      ck3_12002::NativeCampaignRootCharacterResolverV1>(base + 0x28BFC50);
  environment.title_province = reinterpret_cast<
      ck3_12002::NativeCampaignRootCharacterResolverV1>(base + 0x230F8E0);
  environment.character_is_human = reinterpret_cast<
      ck3_12002::NativeFactionCharacterBool12002>(base + 0x2BAA6F0);
  environment.power = reinterpret_cast<ck3_12002::NativeFactionFixedPoint12002>(base + 0x2601ED0);
  environment.power_threshold = reinterpret_cast<ck3_12002::NativeFactionFixedPoint12002>(base + 0x2602180);
  environment.discontent_per_month = reinterpret_cast<ck3_12002::NativeFactionFixedPoint12002>(base + 0x2601B30);
  environment.months_until_max_discontent = reinterpret_cast<ck3_12002::NativeFactionInt32_12002>(base + 0x2601C40);
  environment.at_war = reinterpret_cast<ck3_12002::NativeFactionBool12002>(base + 0x2603A90);
  environment.dangerous = reinterpret_cast<ck3_12002::NativeFactionDanger12002>(base + 0x1D65BD0);
  environment.county_observations_12003 = true;
  environment.county_opinion = reinterpret_cast<ck3_12002::NativeCountyOpinionInt32_12003>(base + 0x24D4C90);
  environment.county_faction_finals.join_score = reinterpret_cast<
      ck3_12002::NativeCountyFactionJoinScore12003>(base + 0x2602550);
  environment.county_faction_finals.can_add = reinterpret_cast<
      ck3_12002::NativeCountyFactionCanAdd12003>(base + 0x26028C0);
  environment.county_faction_finals.leave_score_threshold = reinterpret_cast<const std::int32_t *>(base + 0x5C694C0);
  environment.culture_storage_slot = reinterpret_cast<void **>(base + 0x5D1E2F0);
  environment.culture_fallback_slot = reinterpret_cast<void **>(base + 0x5D1E2E8);
  environment.surrender_observations_12003 = true;
  environment.government = reinterpret_cast<
      ck3_12002::NativeCampaignRootCharacterResolverV1>(base + 0x28C2DF0);
  environment.pair_relation = reinterpret_cast<ck3_12002::NativeFactionRelation12003>(base + 0x28BC250);
  environment.government_allows_mask = reinterpret_cast<
      ck3_12002::NativeGovernmentAllowsMask12003>(base + 0x22CA040);
  environment.state_faith_identifier = reinterpret_cast<const std::int32_t *>(base + 0x5C78AC0);
  return environment;
}

game::ReadPlayerFactionAlertsResultV1 ReadPlayerFactionAlerts12004(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access,
    const ck3_12002::PlayerFactionAlertsRequestV1 &request,
    game::PlayerFactionAlertsV1 &output) noexcept {
  return ck3_12002::ReadPlayerFactionAlertsV1(environment, access, request, output);
}

ReadFactionEntityResult12004 ReadFactionEntity12004(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access, std::int32_t id,
    game::PlayerTargetingFactionV1 &output) noexcept {
  return ck3_12002::ReadFactionEntityV1(environment, access, id, output);
}

std::string SerializePlayerFactionAlerts12004(
    const game::PlayerFactionAlertsV1 &snapshot) {
  return ck3_11906::SerializePlayerFactionAlertsWithProvenanceV1(
      snapshot, kGameVersion, kExecutableSha256,
      kPlayerFactionAlertsBackendId12004);
}
} // namespace xar::ck3_12004
