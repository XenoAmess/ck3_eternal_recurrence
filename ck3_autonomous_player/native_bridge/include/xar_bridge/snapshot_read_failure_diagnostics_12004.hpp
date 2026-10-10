#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::bridge::ck3_12004 {
enum class SnapshotReadFailureStage12004 : std::uint8_t {
  none, core_reader_missing, core_prefix, foundation_missing, actor_resources,
  played_relationships, events, world, settlement
};

// Owned facts from one actual4 read attempt. A failed prefix has no qualified
// prefix values. Request/state revisions belong to the caller's existing guard.
struct SnapshotReadFailure12004 {
  std::uint64_t read_sequence{};
  SnapshotReadFailureStage12004 stage{SnapshotReadFailureStage12004::none};
  bool prefix_ready{};
  std::int32_t date_raw{}, speed{}, local_player_id{}, played_character_id{};
  bool paused{}, map_ready{}, has_played_character{}, played_character_alive{};
  std::optional<std::uint32_t> world_read_result, settlement_read_result;
};

namespace detail {
inline thread_local SnapshotReadFailure12004 snapshot_read_attempt12004{};
}

inline std::uint64_t CaptureSnapshotReadSequence12004() noexcept {
  return detail::snapshot_read_attempt12004.read_sequence;
}

inline void BeginSnapshotReadAttempt12004() noexcept {
  const auto next = CaptureSnapshotReadSequence12004() + std::uint64_t{1};
  detail::snapshot_read_attempt12004 = {};
  detail::snapshot_read_attempt12004.read_sequence = next;
}

inline void CopySnapshotReadPrefix12004(
    std::int32_t date_raw, std::int32_t speed, std::int32_t local_player_id,
    bool paused, bool map_ready, bool has_played_character,
    std::int32_t played_character_id, bool played_character_alive) noexcept {
  auto &receipt = detail::snapshot_read_attempt12004;
  receipt.prefix_ready = true;
  receipt.date_raw = date_raw;
  receipt.speed = speed;
  receipt.local_player_id = local_player_id;
  receipt.paused = paused;
  receipt.map_ready = map_ready;
  receipt.has_played_character = has_played_character;
  receipt.played_character_id = played_character_id;
  receipt.played_character_alive = played_character_alive;
}

inline void RecordSnapshotReadFailure12004(
    SnapshotReadFailureStage12004 stage,
    std::optional<std::uint32_t> world_result = {},
    std::optional<std::uint32_t> settlement_result = {}) noexcept {
  auto &receipt = detail::snapshot_read_attempt12004;
  receipt.stage = stage;
  receipt.world_read_result = world_result;
  receipt.settlement_read_result = settlement_result;
}

inline std::optional<SnapshotReadFailure12004> FreshSnapshotReadFailure12004(
    std::uint64_t before_sequence) noexcept {
  const auto &receipt = detail::snapshot_read_attempt12004;
  if (receipt.read_sequence != before_sequence + std::uint64_t{1} ||
      receipt.stage == SnapshotReadFailureStage12004::none) return {};
  return receipt;
}

inline std::string_view SnapshotReadFailureStageName12004(
    SnapshotReadFailureStage12004 stage) noexcept {
  switch (stage) {
    case SnapshotReadFailureStage12004::core_reader_missing: return "core_reader_missing";
    case SnapshotReadFailureStage12004::core_prefix: return "core_prefix";
    case SnapshotReadFailureStage12004::foundation_missing: return "foundation_missing";
    case SnapshotReadFailureStage12004::actor_resources: return "actor_resources";
    case SnapshotReadFailureStage12004::played_relationships: return "played_relationships";
    case SnapshotReadFailureStage12004::events: return "events";
    case SnapshotReadFailureStage12004::world: return "world";
    case SnapshotReadFailureStage12004::settlement: return "settlement";
    case SnapshotReadFailureStage12004::none: return "none";
  }
  return "unknown";
}

inline std::string FormatSnapshotReadFailure12004(
    const SnapshotReadFailure12004 &receipt) {
  auto text = std::string(" read_stage=") +
      std::string(SnapshotReadFailureStageName12004(receipt.stage)) +
      " prefix_ready=" + (receipt.prefix_ready ? "true" : "false");
  if (receipt.prefix_ready) {
    text += " date_raw=" + std::to_string(receipt.date_raw) +
        " speed=" + std::to_string(receipt.speed) +
        " local_player_id=" + std::to_string(receipt.local_player_id) +
        " paused=" + (receipt.paused ? "true" : "false") +
        " map_ready=" + (receipt.map_ready ? "true" : "false") +
        " has_played_character=" + (receipt.has_played_character ? "true" : "false") +
        " played_character_id=" + std::to_string(receipt.played_character_id) +
        " played_character_alive=" + (receipt.played_character_alive ? "true" : "false");
  }
  if (receipt.world_read_result)
    text += " world_read_result=" + std::to_string(*receipt.world_read_result);
  if (receipt.settlement_read_result)
    text += " settlement_read_result=" + std::to_string(*receipt.settlement_read_result);
  return text;
}
} // namespace xar::bridge::ck3_12004
