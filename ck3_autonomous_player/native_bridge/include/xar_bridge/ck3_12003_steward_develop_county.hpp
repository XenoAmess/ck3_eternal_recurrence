#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_council_candidates.hpp"
#include "xar_bridge/ck3_12004_council_candidates.hpp"
#include "xar_bridge/steward_develop_county_candidates_v1.hpp"

namespace xar::ck3_12003 {

inline constexpr std::string_view kDevelopMaterialStage =
    "native_player_realm_develop_county_material_v1";
inline constexpr std::string_view kDevelopMaterialBackend =
    "ck3-1.20.0.3-native-steward-develop-county-material-v1";
inline constexpr std::string_view kDevelopMaterialReaderMode =
    "native_player_realm_enumerator_predicates_and_current_growth";
inline constexpr std::string_view kDevelopMaterialNextEntry =
    "native_develop_county_ai_inputs_and_proposed_task_growth";

using DevelopVector = ck3_12002::CouncilCandidatesNativeVectorV1;
using DevelopHash = std::int32_t (*)(void *, const char *, std::uint32_t);
using DevelopLookup = const void *(*)(const void *, std::int32_t);
using DevelopResolver = const void *(*)(const void *);
using DevelopHumanCheck = bool (*)(std::int32_t);
using DevelopShown = bool (*)(const void *, const void *);
using DevelopValid = bool (*)(const void *, const void *, void *);
using DevelopTargetValid = bool (*)(const void *, const void *, const void *, void *);
using DevelopGrowth = std::int64_t *(*)(std::int64_t *, const void *, void *);
using DevelopProgress = std::int64_t *(*)(const void *, std::int64_t *, const void *);
using DevelopProducer = void (*)(const void *, const void *, bool, DevelopVector *, bool);

struct StewardDevelopCountyEnvironment12003 {
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  std::uintptr_t module_base = 0;
  std::string_view admitted_executable_sha256{};
  ck3_12002::CouncilCandidatesEnvironmentV1 council{};
  void **game_state_slot = nullptr;
  void **title_storage_slot = nullptr;
  void **title_fallback_slot = nullptr;
  void **task_type_database_slot = nullptr;
  void **task_type_fallback_slot = nullptr;
  DevelopHash hash_key = nullptr;
  DevelopLookup lookup_type = nullptr;
  DevelopResolver immediate_liege = nullptr;
  DevelopResolver capital_province = nullptr;
  DevelopHumanCheck is_human = nullptr;
  DevelopShown shown = nullptr;
  DevelopValid valid = nullptr;
  DevelopTargetValid target_valid = nullptr;
  DevelopGrowth growth = nullptr;
  DevelopGrowth decay = nullptr;
  DevelopProgress current_progress = nullptr;
  DevelopProgress maximum_progress = nullptr;
  DevelopProducer produce_targets = nullptr;

  // Actual .4 role profile; appended to retain every existing aggregate prefix.
  ck3_12004::CouncilCandidatesEnvironmentV1 council12004{};
};

struct StewardDevelopCountyAccess12003 {
  void *context = nullptr;
  ck3_11906::CaptureStewardDevelopCountyCandidatesFrameV1 capture_frame = nullptr;
  ck3_11906::IsStewardDevelopCountyCandidatesMainThreadV1 is_main_thread = nullptr;
  ck3_12002::CouncilCandidatesReadMemoryV1 read_memory = nullptr;
};

// Only calculates addresses for the exact .3 image. Existing role/identity
// layouts use the reviewed .3-to-.2 ABI mapping, never a wildcard admission.
StewardDevelopCountyEnvironment12003 BindStewardDevelopCounty12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

game::ReadStewardDevelopCountyCandidatesResultV1 ReadStewardDevelopCounty12003(
    const StewardDevelopCountyEnvironment12003 &environment,
    const StewardDevelopCountyAccess12003 &access,
    const ck3_11906::StewardDevelopCountyCandidatesRequestV1 &request,
    game::StewardDevelopCountyCandidatesV1 &output) noexcept;

// The existing serializer dispatches this profile when value.material exists.
std::string SerializeStewardDevelopCountyMaterial12003(
    const game::StewardDevelopCountyCandidatesV1 &value);

} // namespace xar::ck3_12003
