#pragma once
#include "xar_bridge/activity_hosted_identity_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include <string>
#include <string_view>

namespace xar::ck3_12002 {
inline constexpr std::string_view kPlayerPilgrimageActivitiesPrivate12004StepV1 =
    "query-player-pilgrimage-activities-v1-private";
using PilgrimageReadSnapshot12004V1 = bool (*)(void *, game::Snapshot &) noexcept;
// Software request only. No planner, cost, guest, reserve or commit fields.
struct PlayerPilgrimageActivitiesPrivateQuery12004V1 {
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  bool enabled = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  void *native_context = nullptr;
  PilgrimageReadSnapshot12004V1 read_snapshot = nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bridge::ActivityHostedIdentityResultV1 pilgrimage_identities{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};
bool ExecutePlayerPilgrimageActivitiesPrivate12004V1(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerPilgrimageActivitiesPrivate12004V1(
    const PlayerPilgrimageActivitiesPrivateQuery12004V1 &);
} // namespace xar::ck3_12002
