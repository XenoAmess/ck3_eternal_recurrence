#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/m5_war_primary_readback_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/war_entry_assessments_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

// Private diagnostic only: one native-final-legal target, no action or public
// capability. The exact-build sources are read together on application-main.
inline constexpr std::string_view kM5WarPrimaryPrivateStepPrefixV1 =
    "query-m5-war-primary-current-v1-";
inline constexpr std::string_view kPrewarPlayerClaimPrivateStepPrefixV1 =
    "query-prewar-player-claim-current-v1-";

bool ParseM5WarPrimaryPrivateStepV1(std::string_view step,
                                   std::int32_t &target_character_id) noexcept;
bool ParsePrewarPlayerClaimPrivateStepV1(
    std::string_view step, std::int32_t &target_character_id) noexcept;

struct M5WarPrimaryPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  const game::GameAdapter *game = nullptr;
  std::uintptr_t module_base = 0;
  WarEntryNativeEnvironmentV1 war_environment{};
  std::uint64_t expected_revision = 0;
  game::Snapshot expected_snapshot{};
  std::vector<game::DeclarableWarSnapshot> expected_declarations;
  game::DeclarableWarSnapshot chosen_declaration{};
  std::int32_t target_character_id = -1;
  bool require_unique_player_claim = false;

  M5WarPrimaryReadbackV1 result{};
  std::int32_t claim_county_objective_province_id = -1;
  std::int32_t claim_actor_default_raise_province_id = -1;
  std::int32_t claim_defender_default_raise_province_id = -1;
  std::vector<PrewarRaisedArmyV1> claim_primary_current_raised_armies;
  std::string failure_stage;
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
  bool available = false;
};

bool ExecuteM5WarPrimaryPrivateQueryV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept;

// Empty unless the complete current-primary join was available. This payload
// never claims future supply, voluntary allies, campaign cost or win chance.
std::string SerializeM5WarPrimaryPrivateResultV1(
    const M5WarPrimaryReadbackV1 &result);
std::string SerializePrewarPlayerClaimPrivateResultV1(
    const M5WarPrimaryPrivateQueryV1 &query);

} // namespace xar::ck3_11906
