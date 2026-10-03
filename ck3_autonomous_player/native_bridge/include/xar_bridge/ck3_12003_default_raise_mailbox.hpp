#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_prewar_muster.hpp"

namespace xar::ck3_12003 {
inline constexpr std::string_view kPlayerDefaultRaiseStepV1 =
    "query-player-default-raise-v1";
inline constexpr std::string_view kPlayerDefaultRaiseCapabilityV1 =
    "game.command.query-player-default-raise-v1";

struct PlayerDefaultRaiseMailboxContextV1 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  ck3_12002::PlayerDefaultRaiseObservationV1 observation{};
  bool completed = false;
};
bool ExecutePlayerDefaultRaiseMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
inline void RegisterPlayerDefaultRaiseMailboxExecutorV1(
    ck3_11906::MainThreadQueryInstallEnvironmentV1 &environment) noexcept {
  // Slot 17 is unused by the exact .3 Crozier installer. The old 1.19
  // installer registers its historical callback on its separate path.
  environment.permitted_executor_septendenary =
      &ExecutePlayerDefaultRaiseMailboxV1;
}
std::string SerializePlayerDefaultRaiseV1(
    const ck3_12002::PlayerDefaultRaiseObservationV1 &observation,
    std::uint64_t query_sequence, std::uint64_t snapshot_revision,
    std::int32_t date_raw);
} // namespace xar::ck3_12003
