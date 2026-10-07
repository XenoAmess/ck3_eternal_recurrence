#include "xar_bridge/ck3_12004_steward_develop_county.hpp"

namespace xar::ck3_12004 {

StewardDevelopCountyEnvironment12004 BindStewardDevelopCounty12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  StewardDevelopCountyEnvironment12004 out{};
  if (module_base == 0 || executable_sha256 != kExecutableSha256) return out;
  out.council12004 = BindCouncilCandidates12004(module_base, executable_sha256);
  if (!out.council12004.exact_build_admitted) return out;
  out.exact_build_admitted = true;
  out.module_base = module_base;
  out.admitted_executable_sha256 = kExecutableSha256;
  // This retained software carrier is used only by Initialize/Release. Role
  // capture and character identity resolve through council12004 independently.
  out.council.allocator_vtable = out.council12004.allocator_vtable;
  out.council.fallback_allocator = out.council12004.fallback_allocator;
  out.council.initialize_vector = out.council12004.initialize_vector;
  out.council.release_allocation = out.council12004.release_allocation;
  out.game_state_slot = reinterpret_cast<void **>(module_base + kGameStateSlotRva);
  out.title_storage_slot = reinterpret_cast<void **>(module_base + kStewardTitleStorageSlotRva12004);
  out.title_fallback_slot = reinterpret_cast<void **>(module_base + kStewardTitleFallbackSlotRva12004);
  out.task_type_database_slot = reinterpret_cast<void **>(module_base + kStewardTaskTypeDatabaseSlotRva12004);
  out.task_type_fallback_slot = reinterpret_cast<void **>(module_base + kStewardTaskTypeFallbackSlotRva12004);
  out.hash_key = reinterpret_cast<ck3_12003::DevelopHash>(module_base + kStewardHashRva12004);
  out.lookup_type = reinterpret_cast<ck3_12003::DevelopLookup>(module_base + kStewardTaskTypeLookupRva12004);
  out.immediate_liege = reinterpret_cast<ck3_12003::DevelopResolver>(module_base + kStewardImmediateLiegeRva12004);
  out.capital_province = reinterpret_cast<ck3_12003::DevelopResolver>(module_base + kStewardCapitalProvinceRva12004);
  out.is_human = reinterpret_cast<ck3_12003::DevelopHumanCheck>(module_base + kStewardIsHumanRva12004);
  out.shown = reinterpret_cast<ck3_12003::DevelopShown>(module_base + kStewardShownRva12004);
  out.valid = reinterpret_cast<ck3_12003::DevelopValid>(module_base + kStewardValidRva12004);
  out.target_valid = reinterpret_cast<ck3_12003::DevelopTargetValid>(module_base + kStewardTargetValidRva12004);
  out.growth = reinterpret_cast<ck3_12003::DevelopGrowth>(module_base + kStewardGrowthRva12004);
  out.decay = reinterpret_cast<ck3_12003::DevelopGrowth>(module_base + kStewardDecayRva12004);
  out.current_progress = reinterpret_cast<ck3_12003::DevelopProgress>(module_base + kStewardCurrentProgressRva12004);
  out.maximum_progress = reinterpret_cast<ck3_12003::DevelopProgress>(module_base + kStewardMaximumProgressRva12004);
  out.produce_targets = reinterpret_cast<ck3_12003::DevelopProducer>(module_base + kStewardProduceTargetsRva12004);
  return out;
}

bool IsStewardDevelopCountyEnvironment12004(
    const StewardDevelopCountyEnvironment12004 &env) noexcept {
  if (!env.exact_build_admitted || env.offline_fixture_function_overrides ||
      env.module_base == 0 || env.admitted_executable_sha256 != kExecutableSha256)
    return false;
  const auto base = env.module_base;
  const auto &council = env.council12004;
  if (!council.exact_build_admitted || council.offline_fixture_function_overrides ||
      council.module_base != base ||
      council.admitted_executable_sha256 != kExecutableSha256 ||
      env.council.offline_fixture_function_overrides ||
      env.council.allocator_vtable != council.allocator_vtable ||
      env.council.fallback_allocator != council.fallback_allocator ||
      env.council.initialize_vector != council.initialize_vector ||
      env.council.release_allocation != council.release_allocation)
    return false;
  return reinterpret_cast<std::uintptr_t>(council.character_storage_slot) ==
             base + kCharacterStorageSlotRva &&
      reinterpret_cast<std::uintptr_t>(council.character_fallback_slot) ==
             base + kCouncilCandidatesCharacterFallbackSlotRva12004 &&
      reinterpret_cast<std::uintptr_t>(council.active_task_storage_slot) ==
             base + kCouncilCandidatesTaskStorageSlotRva12004 &&
      reinterpret_cast<std::uintptr_t>(council.active_task_fallback_slot) ==
             base + kCouncilCandidatesTaskFallbackSlotRva12004 &&
      council.allocator_vtable == base + kCouncilCandidatesAllocatorVtableRva12004 &&
      council.fallback_allocator == base + kCouncilCandidatesFallbackAllocatorRva12004 &&
      reinterpret_cast<std::uintptr_t>(council.initialize_vector) ==
             base + kCouncilCandidatesInitializeRva12004 &&
      reinterpret_cast<std::uintptr_t>(council.release_allocation) ==
             base + kCouncilCandidatesReleaseRva12004 &&
      reinterpret_cast<std::uintptr_t>(council.position_lookup) ==
             base + kCouncilCandidatesPositionLookupRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.game_state_slot) == base + kGameStateSlotRva &&
      reinterpret_cast<std::uintptr_t>(env.title_storage_slot) == base + kStewardTitleStorageSlotRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.title_fallback_slot) == base + kStewardTitleFallbackSlotRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.task_type_database_slot) == base + kStewardTaskTypeDatabaseSlotRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.task_type_fallback_slot) == base + kStewardTaskTypeFallbackSlotRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.hash_key) == base + kStewardHashRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.lookup_type) == base + kStewardTaskTypeLookupRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.immediate_liege) == base + kStewardImmediateLiegeRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.capital_province) == base + kStewardCapitalProvinceRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.is_human) == base + kStewardIsHumanRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.shown) == base + kStewardShownRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.valid) == base + kStewardValidRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.target_valid) == base + kStewardTargetValidRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.growth) == base + kStewardGrowthRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.decay) == base + kStewardDecayRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.current_progress) == base + kStewardCurrentProgressRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.maximum_progress) == base + kStewardMaximumProgressRva12004 &&
      reinterpret_cast<std::uintptr_t>(env.produce_targets) == base + kStewardProduceTargetsRva12004;
}

game::ReadStewardDevelopCountyCandidatesResultV1 ReadStewardDevelopCounty12004(
    const StewardDevelopCountyEnvironment12004 &env,
    const StewardDevelopCountyAccess12004 &access,
    const ck3_11906::StewardDevelopCountyCandidatesRequestV1 &request,
    game::StewardDevelopCountyCandidatesV1 &output) noexcept {
  if (!IsStewardDevelopCountyEnvironment12004(env)) {
    output = {};
    output.material.emplace();
    output.snapshot_revision = request.expected_snapshot_revision;
    output.unavailable_reason =
        game::StewardDevelopCountyFailureReasonV1::exact_build_not_admitted;
    return game::ReadStewardDevelopCountyCandidatesResultV1::unavailable;
  }
  return ck3_12003::ReadStewardDevelopCounty12003(env, access, request, output);
}

} // namespace xar::ck3_12004
