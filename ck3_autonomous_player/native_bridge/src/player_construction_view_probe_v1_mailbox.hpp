#pragma once

#include "player_construction_view_probe_v1.hpp"
#include "player_held_construction_model_enumerator_v1.hpp"
#include "player_world_building_definition_source_v1.hpp"
#include "player_world_building_action_candidate_v1.hpp"
#include "domain_construction_application_main_runtime_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <cstddef>
#include <optional>
#include <string>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr const char* kPlayerConstructionViewProbePrivateStepV1 =
    "g2_player_construction_view_probe_v1";
inline constexpr const char* kPlayerWorldBuildingActionPrivateStepV1 =
    "g2_player_world_building_action_private_v1";

enum class PlayerConstructionViewProbeMailboxCompletionV1 : std::uint8_t {
  not_executed = 0,
  completed,
  infrastructure_rejected,
};

struct PlayerConstructionViewProbeMailboxContextV1 final {
  MainThreadQueryMailboxV1* mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0U;
  std::uintptr_t module_base = 0U;
  xar::ck3::shared::PlayerConstructionViewProbeResultV1 result{};
  PlayerHeldConstructionModelResultV1 player_model_sources{};
  // Additive private same-frame world source and sampled stock player final
  // eligibility. It carries only copied scalar IDs, never borrowed addresses.
  PlayerWorldBuildingSourceResultV1 player_world_building_sources{};
  bool player_world_building_source_executed = false;
  bool request_private_action = false;
  std::int64_t minimum_gold_reserve_raw = 20'000'000;
  PlayerWorldBuildingActionCandidateV1 private_action_candidate{};
  xar::ck3::shared::PlayerWorldBuildingDirectActionStateV1
      private_action_state{};
  std::size_t player_model_definition_source_count = 0;
  // Null before an active view/model comparison, false on a failed binding,
  // true only when the already identity-checked view+0x108 equals the exact
  // global model source in this executing paused frame.
  std::optional<bool> player_model_view_binding_verified;
  PlayerConstructionViewProbeMailboxCompletionV1 completion =
      PlayerConstructionViewProbeMailboxCompletionV1::not_executed;
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0U;
};

[[nodiscard]] bool ExecutePlayerConstructionViewProbeMailboxV1(
    void* context, const MainThreadExecutionStampV1& stamp) noexcept;

[[nodiscard]] std::string SerializePlayerConstructionViewProbePrivateV1(
    const PlayerConstructionViewProbeMailboxContextV1& query);

static_assert(std::is_same_v<
              decltype(&ExecutePlayerConstructionViewProbeMailboxV1),
              MainThreadQueryExecutorV1>);

}  // namespace xar::ck3_11906
