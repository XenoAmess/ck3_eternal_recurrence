#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/ck3_121003_full_profile111.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_opening_readonly56.hpp"
#include "xar_bridge/ck3_1210_military_production58.hpp"
#include <array>
#include <optional>
#include <string_view>

namespace xar::ck3_1210 {
struct ReadWireBuildIdentityV1 {
  std::string_view adapter_id, game_version, executable_sha256;
};
enum class ReadWireStepLocationV1 { result_field, original_outbound };
struct ReadWireContractV1 {
  std::string_view step, capability, schema, schema_member;
  ReadWireStepLocationV1 step_location = ReadWireStepLocationV1::result_field;
};
// Contract identity DATA only. A table entry grants no compiled producer,
// enabled feature, main custody, successful observation or public available.
// Public capability remains solely in the exact adapter's compiled span.
inline constexpr std::array<ReadWireContractV1, 7> kReadWireContractsV1{{
    {"query-war-cash-current-resources-v2", "game.query.war-cash-current-resources.v2",
     "xar.ck3.war-cash-current-resources.v2", "war_cash_current_resources"},
    {"query-active-wars-identity-v1", "game.query.active-wars-identity.v1",
     "ck3_1210_active_wars_identity_v1", ""},
    {"query-decision-candidates-readonly-1210-v1", "game.query.decision-candidates-readonly.1210.v1",
     "ck3_1210_decision_candidates_data_v1", "", ReadWireStepLocationV1::original_outbound},
    {"query-character-manager-roster-v1", "game.query.character-manager-roster.v1",
     "ck3_1210_character_roster_readonly_v1", ""},
    {"query-siege-target-partial-v1", "game.query.siege-target-partial.v1",
     "ck3_1210_siege_target_query_v1", ""},
    {"query-council-holder-frame-v1", "game.query.council-holder-frame.v1",
     "ck3_1210_council_holder_frame_v1", ""},
    {"query-actor-resource-leaf-v2", "game.query.actor-resource-leaf.v2",
     "ck3_1210_actor_resource_leaf_v2", ""},
}};
constexpr std::optional<ReadWireContractV1> FindOpeningReadWireContract56(
    ImageBuildV1 build,std::string_view step) noexcept {
  const auto *profile=FindOpeningReadWireProfile56(step);
  if(!profile || profile->build!=build)return std::nullopt;
  return ReadWireContractV1{profile->step,profile->capability,profile->schema,"",ReadWireStepLocationV1::original_outbound};
}
inline constexpr ReadWireContractV1 kMilitaryReadWireContract58{
 kActiveWarsHotfixStep58,kActiveWarsHotfixCapability58,kActiveWarsHotfixSchema58,""};
constexpr std::optional<ReadWireContractV1> FindReadWireContractV1(
    ReadWireBuildIdentityV1 build, std::string_view step) noexcept {
  if(build.adapter_id==hotfix26757580::kAdapterId && build.game_version==kGameVersion &&
     build.executable_sha256==hotfix26757580::kExecutableSha256){
    if(step==kMilitaryReadWireContract58.step)return kMilitaryReadWireContract58;
    if(step=="query-war-cash-current-resources-v2")
      for(const auto &contract:kReadWireContractsV1)if(contract.step==step)return contract;
    return FindOpeningReadWireContract56(ImageBuildV1::hotfix26757580,step);
  }
  if(build.adapter_id==ck3_121003::full111::kAdapterId && build.game_version==ck3_121003::full111::kGameVersion &&
     build.executable_sha256==ck3_121003::full111::kExecutableSha256)
    return FindOpeningReadWireContract56(ImageBuildV1::full11126785313,step);
  if (build.adapter_id != kAdapterId || build.game_version != kGameVersion ||
      build.executable_sha256 != kExecutableSha256) return std::nullopt;
  for (const auto &contract : kReadWireContractsV1)
    if (contract.step == step) return contract;
  return std::nullopt;
}
enum class ReadWireIdentityMatchV1 { exact_contract, wrong_schema, unknown_command };
// Caller extracts the schema at schema_member from the original result.
// For original_outbound, retain the real outbound step; the DATA result has
// no step member. Never synthesize or insert one while decoding.
// Matching identity never promotes result status or internal available=true.
constexpr ReadWireIdentityMatchV1 MatchReadWireResultIdentityV1(
    ReadWireBuildIdentityV1 build, std::string_view original_step,
    std::string_view original_schema) noexcept {
  const auto contract = FindReadWireContractV1(build, original_step);
  if (!contract) return ReadWireIdentityMatchV1::unknown_command;
  return original_schema == contract->schema ? ReadWireIdentityMatchV1::exact_contract
                                           : ReadWireIdentityMatchV1::wrong_schema;
}
} // namespace xar::ck3_1210
