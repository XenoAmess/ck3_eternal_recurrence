#pragma once

#include "xar_bridge/faction_gift_mitigation_action_v1.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::string_view kFactionGiftColdRecoveryPrivateStepV1 =
    "private-query-faction-gift-cold-recovery-v1";

// Persisted before a one-shot submit. The old native ACK is process-local and
// cannot be required by a different CK3 process.
struct FactionGiftColdRecoveryRequestV1 {
  std::string request_id;
  std::string episode_run_id;
  std::string source_round_id;
  std::uint32_t source_bridge_pid = 0;
  std::string source_bridge_creation_date;
  std::string checkpoint_sha256_before_submit;
  std::uint64_t pre_snapshot_revision = 0;
  std::uint64_t pre_native_snapshot_revision = 0;
  std::int32_t pre_date_raw = 0;
  std::uint32_t player_character_id = 0;
  std::uint32_t source_faction_id = 0;
  std::uint32_t recipient_character_id = 0;
  std::int64_t pre_player_gold_raw = 0;
  std::int64_t expected_gold_cost_raw = 0;
  std::int32_t expected_opinion_delta = 0;
  std::int32_t pre_recipient_opinion_of_player = 0;
  std::int64_t pre_source_faction_power_raw = 0;
  std::int64_t pre_source_faction_discontent_raw = 0;
  std::vector<std::uint32_t> pre_source_faction_member_character_ids;
};

// Only the exact paused native recovery receiver may set these facts. The
// faction entity lookup must be independent of the player's current targeting
// vector, including when that vector is now empty.
struct FactionGiftColdRecoveryPostV1 {
  std::string new_round_id;
  std::uint32_t new_bridge_pid = 0;
  std::string new_bridge_creation_date;
  std::string episode_run_id;
  bool new_process_confirmed = false;
  bool independent_faction_storage_lookup_complete = false;
  bool independent_recipient_lookup_complete = false;
  bool selected_from_current_targeting_vector = false;
  bool save_is_pre_action_checkpoint = false;
  std::string selected_save_sha256;
  game::FactionGiftMitigationObservationV1 observation{};
};

enum class FactionGiftColdRecoveryTerminalV1 : std::uint8_t {
  unresolved = 0,
  applied = 1,
  unchanged = 2,
};

struct FactionGiftColdRecoveryResultV1 {
  FactionGiftColdRecoveryTerminalV1 terminal =
      FactionGiftColdRecoveryTerminalV1::unresolved;
  std::string reason;
  game::FactionGiftMitigationReceiptV1 receipt{};
  bool action_retry_allowed = false;
};

FactionGiftColdRecoveryTerminalV1 EvaluateFactionGiftColdRecoveryV1(
    const FactionGiftColdRecoveryRequestV1 &request,
    const FactionGiftColdRecoveryPostV1 &post,
    FactionGiftColdRecoveryResultV1 &result) noexcept;

} // namespace xar::ck3_11906
