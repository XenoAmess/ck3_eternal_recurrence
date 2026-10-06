#include "xar_bridge/ck3_12004_war.hpp"

namespace xar::ck3_12004 {

ck3_12002::WarEntryNativeEnvironmentV1 BindWarEntryNativeEnvironment12004(
    std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  ck3_12002::WarEntryNativeEnvironmentV1 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256)
    return result;
  result.module_base = image_base;
  result.game_state_slot = reinterpret_cast<void **>(
      image_base + kGameStateSlotRva);
  result.character_storage_slot = reinterpret_cast<void **>(
      image_base + kCharacterStorageSlotRva);
  result.character_fallback_slot = reinterpret_cast<void **>(
      image_base + kWarEntryCharacterFallbackSlotRva12004);
  result.actor_state_dependency_slot = reinterpret_cast<void **>(
      image_base + kWarEntryActorStateDependencySlotRva12004);
  result.actor_state_builder =
      reinterpret_cast<ck3_12002::NativeWarEntryActorStateBuilderFunctionV1>(
          image_base + kWarEntryActorStateBuilderRva12004);
  result.assessment =
      reinterpret_cast<ck3_12002::NativeWarEntryAssessmentFunctionV1>(
          image_base + kWarEntryAssessmentRva12004);
  result.network_collector =
      reinterpret_cast<ck3_12002::NativeWarEntryNetworkCollectorFunctionV1>(
          image_base + kWarEntryNetworkCollectorRva12004);
  result.effective_target_resolver =
      reinterpret_cast<ck3_12002::NativeWarEntryEffectiveTargetResolverFunctionV1>(
          image_base + kWarEntryEffectiveTargetResolverRva12004);
  return result;
}

bool IsWarEntryNativeEnvironment12004(
    const ck3_12002::WarEntryNativeEnvironmentV1 &environment) noexcept {
  if (environment.module_base == 0 ||
      environment.offline_fixture_function_overrides)
    return false;
  const auto expected = BindWarEntryNativeEnvironment12004(
      environment.module_base, kExecutableSha256);
  return environment.game_state_slot == expected.game_state_slot &&
      environment.character_storage_slot == expected.character_storage_slot &&
      environment.character_fallback_slot == expected.character_fallback_slot &&
      environment.actor_state_dependency_slot == expected.actor_state_dependency_slot &&
      environment.actor_state_builder == expected.actor_state_builder &&
      environment.assessment == expected.assessment &&
      environment.network_collector == expected.network_collector &&
      environment.effective_target_resolver == expected.effective_target_resolver;
}

std::string SerializeWarEntryAssessments12004(
    const game::WarEntryAssessmentsV1 &result) {
  auto wire = ck3_12002::SerializeWarEntryAssessmentsV1(result);
  const auto replace = [&wire](std::string_view from, std::string_view to) {
    const auto at = wire.find(from);
    if (at != std::string::npos)
      wire.replace(at, from.size(), to);
  };
  replace("\"assessment_rva\":\"0x1A23240\"",
          "\"assessment_rva\":\"0x1A23220\"");
  replace("\"network_collector_rva\":\"0x1A24010\"",
          "\"network_collector_rva\":\"0x1A23FF0\"");
  return wire;
}

ck3_12003::WarOccupationTargetsBindingsV1 BindWarOccupationTargets12004(
    std::uintptr_t image_base,
    std::string_view executable_sha256,
    const ck3_12002::WorldBindings &actual_world,
    const ck3_12002::ProvinceBindings &actual_provinces) noexcept {
  ck3_12003::WarOccupationTargetsBindingsV1 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      !actual_world.enabled || !actual_provinces.enabled)
    return result;
  result.world = actual_world;
  result.provinces = actual_provinces;
  result.character_storage_slot = reinterpret_cast<void **>(
      image_base + kCharacterStorageSlotRva);
  result.vector_allocator = reinterpret_cast<void *>(
      image_base + kWarOccupationVectorAllocatorRva12004);
  result.war_occupation_context_fallback_slot = reinterpret_cast<void **>(
      image_base + kWarOccupationContextFallbackSlotRva12004);
  result.get_war_occupation_context =
      reinterpret_cast<decltype(result.get_war_occupation_context)>(
          image_base + kWarOccupationContextRva12004);
  result.collect_territory_participants =
      reinterpret_cast<decltype(result.collect_territory_participants)>(
          image_base + kWarOccupationCollectParticipantsRva12004);
  result.collect_holding_titles =
      reinterpret_cast<decltype(result.collect_holding_titles)>(
          image_base + kWarOccupationCollectTitlesRva12004);
  result.count_holding = reinterpret_cast<decltype(result.count_holding)>(
          image_base + kWarOccupationCountHoldingRva12004);
  result.war_participants_are_liege_related =
      reinterpret_cast<decltype(result.war_participants_are_liege_related)>(
          image_base + kWarOccupationLiegeRelatedRva12004);
  result.enabled = true;
  return result;
}

ck3_12002::BattleCurrentWarscoreCapsBindings12003
BindBattleCurrentWarscoreCaps12004(
    std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256)
    return {};
  return {
      reinterpret_cast<const std::int64_t *>(
          image_base + kWarAttackerWinnerCapRva12004),
      reinterpret_cast<const std::int64_t *>(
          image_base + kWarDefenderWinnerCapRva12004)};
}

} // namespace xar::ck3_12004
