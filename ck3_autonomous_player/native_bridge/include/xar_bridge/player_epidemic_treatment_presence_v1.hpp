#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kPlayerEpidemicTreatmentPresenceStepV1 =
    "query-player-epidemic-treatment-presence-v1";
inline constexpr std::string_view kPlayerEpidemicTreatmentModifierKeyV1 =
    "ce1_unorthodox_epidemic_treatment";
inline constexpr std::uint32_t kPlayerEpidemicTreatmentQueuedWaitMsV1 = 8'000;
inline constexpr std::uint32_t kPlayerEpidemicTreatmentExecutingWaitMsV1 = 2'000;

struct PlayerEpidemicTreatmentPresenceV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  bool available = false;
  bool present = false;
  std::string unavailable_reason;
};

// Exact-build native DB definition and CCharacter extension reader. Never
// treats a failed definition/row read as a known absence.
PlayerEpidemicTreatmentPresenceV1 ReadPlayerEpidemicTreatmentPresenceNativeV1(
    const Bindings &bindings,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    std::uint64_t revision, std::int32_t date_raw,
    std::int32_t played_character_id) noexcept;

// Separately fixture-testable, pointer-identity row scan. Null extension is a
// legal empty set; non-null malformed spans are unavailable.
bool ScanPlayerModifierRowsV1(const void *extension, const void *definition,
                              bool &present) noexcept;

std::string SerializePlayerEpidemicTreatmentPresenceV1(
    const PlayerEpidemicTreatmentPresenceV1 &result);

struct PlayerEpidemicTreatmentMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  PlayerEpidemicTreatmentPresenceV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
};

bool ExecutePlayerEpidemicTreatmentPresenceMailboxV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;

} // namespace xar::ck3_11906
