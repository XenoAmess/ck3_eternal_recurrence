#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr char kPlayerEpidemicRecoveryStepV1[] =
    "query-player-epidemic-recovery-v1";
inline constexpr char kPlayerEpidemicRecoveryTitleStepPrefixV1[] =
    "query-player-epidemic-recovery-v1-title-";
inline constexpr char kPlayerEpidemicRecoveryListKeyV1[] =
    "formerly_infected_counties";
inline constexpr char kPlayerEpidemicRecoveryMinorKeyV1[] =
    "county_epidemic_recovered_minor_modifier";
inline constexpr char kPlayerEpidemicRecoveryTinyKeyV1[] =
    "county_epidemic_recovered_tiny_modifier";

struct PlayerEpidemicRecoveryCountyV1 {
  std::int32_t landed_title_id = -1;
  bool minor_present = false;
  bool tiny_present = false;
};

struct PlayerEpidemicRecoveryV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::int32_t requested_title_id = 0;
  bool available = false;
  std::vector<PlayerEpidemicRecoveryCountyV1> counties;
  std::string unavailable_reason;
};

// Exact-build list row extractor. An absent list key is a known empty list;
// malformed spans and non-title targets are unknown, never known absence.
bool ReadEpidemicRecoveryListRowsV1(const void *context,
                                    std::int32_t list_identifier,
                                    std::vector<std::int32_t> &titles);

PlayerEpidemicRecoveryV1 ReadPlayerEpidemicRecoveryNativeV1(
    const Bindings &bindings,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    std::uint64_t revision, std::int32_t date_raw,
    std::int32_t played_character_id,
    std::int32_t requested_title_id) noexcept;

bool ParsePlayerEpidemicRecoveryStepV1(std::string_view step,
                                       std::int32_t &requested_title_id) noexcept;

std::string SerializePlayerEpidemicRecoveryV1(
    const PlayerEpidemicRecoveryV1 &value);

struct PlayerEpidemicRecoveryMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  std::int32_t requested_title_id = 0;
  PlayerEpidemicRecoveryV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
};

bool ExecutePlayerEpidemicRecoveryMailboxV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;

} // namespace xar::ck3_11906
