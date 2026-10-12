#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::bridge::ck3_12004 {
enum class SnapshotReadFailureStage12004 : std::uint8_t {
  none, core_reader_missing, core_prefix, foundation_missing, actor_resources,
  played_relationships, events, world, settlement,
  worker_snapshot_cache_absent, worker_snapshot_stamp_unobserved,
  worker_snapshot_tls_uninitialized, worker_snapshot_tls_marker_invalid,
  worker_snapshot_epoch_unpublished, worker_snapshot_date_mismatch,
  worker_snapshot_pause_mismatch, worker_snapshot_exception
};

// Owned facts from one actual4 read attempt. A failed prefix has no qualified
// prefix values. Request/state revisions belong to the caller's existing guard.
// Cache fields below are copied under the WorkerAdapter mutex. Mailbox fields
// are an earlier group of independent atomic loads, not the same atomic frame.
enum class WorkerSnapshotObservationStage12004 : std::uint8_t {
  initial_cache_lock, before_wait, after_wait, after_diagnostics_refresh, final_guards
};
enum class WorkerMailboxSampleStage12004 : std::uint8_t {
  initial_pre_cache_lock, post_wait_cache_unlocked
};
struct WorkerSnapshotWaitTicket12004 {
  std::uint64_t generation{}, target_epoch{};
  std::uint32_t owner_thread_id{};
};
struct WorkerSnapshotObservation12004 {
  WorkerSnapshotObservationStage12004 observed_at_stage{};
  WorkerMailboxSampleStage12004 diagnostic_sample_stage{};
  bool cache_present{};
  std::uint64_t current_cache_epoch{}, cache_revision{}, raw_generation_counter{};
  std::uint64_t pending_generation{}, last_committed_raw_generation{};
  std::optional<std::uint64_t> active_raw_target_epoch;
  std::optional<std::uint32_t> active_raw_owner_thread_id;
  std::optional<std::int32_t> cache_date_raw;
  std::optional<bool> cache_paused;
  std::uint32_t created_worker_thread_id{}, reader_thread_id{};
  std::optional<WorkerSnapshotWaitTicket12004> expected_wait_ticket;
  std::optional<bool> wait_terminal;
  std::uint64_t mailbox_pump_epoch{};
  std::uint32_t mailbox_owner_thread_id{}, mailbox_observed_thread_id{};
  bool mailbox_stamp_read_success{}, mailbox_stop_requested{};
  std::uint8_t mailbox_tls_initialized{}, mailbox_tls_main_thread_marker{};
  std::optional<std::int32_t> mailbox_date_raw;
  std::optional<bool> mailbox_paused;
};

struct SnapshotReadFailure12004 {
  std::uint64_t read_sequence{};
  SnapshotReadFailureStage12004 stage{SnapshotReadFailureStage12004::none};
  bool prefix_ready{};
  std::int32_t date_raw{}, speed{}, local_player_id{}, played_character_id{};
  bool paused{}, map_ready{}, has_played_character{}, played_character_alive{};
  std::optional<std::uint32_t> world_read_result, settlement_read_result;
  std::optional<WorkerSnapshotObservation12004> worker_observation;
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

inline void RecordWorkerSnapshotObservation12004(
    const WorkerSnapshotObservation12004 &observation) noexcept {
  detail::snapshot_read_attempt12004.worker_observation = observation;
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
    case SnapshotReadFailureStage12004::worker_snapshot_cache_absent:
      return "worker_snapshot_cache_absent";
    case SnapshotReadFailureStage12004::worker_snapshot_stamp_unobserved:
      return "worker_snapshot_stamp_unobserved";
    case SnapshotReadFailureStage12004::worker_snapshot_tls_uninitialized:
      return "worker_snapshot_tls_uninitialized";
    case SnapshotReadFailureStage12004::worker_snapshot_tls_marker_invalid:
      return "worker_snapshot_tls_marker_invalid";
    case SnapshotReadFailureStage12004::worker_snapshot_epoch_unpublished:
      return "worker_snapshot_epoch_unpublished";
    case SnapshotReadFailureStage12004::worker_snapshot_date_mismatch:
      return "worker_snapshot_date_mismatch";
    case SnapshotReadFailureStage12004::worker_snapshot_pause_mismatch:
      return "worker_snapshot_pause_mismatch";
    case SnapshotReadFailureStage12004::worker_snapshot_exception:
      return "worker_snapshot_exception";
    case SnapshotReadFailureStage12004::none: return "none";
  }
  return "unknown";
}

inline std::string_view WorkerSnapshotObservationStageName12004(
    WorkerSnapshotObservationStage12004 stage) noexcept {
  switch (stage) {
    case WorkerSnapshotObservationStage12004::initial_cache_lock: return "initial_cache_lock";
    case WorkerSnapshotObservationStage12004::before_wait: return "before_wait";
    case WorkerSnapshotObservationStage12004::after_wait: return "after_wait";
    case WorkerSnapshotObservationStage12004::after_diagnostics_refresh:
      return "after_diagnostics_refresh";
    case WorkerSnapshotObservationStage12004::final_guards: return "final_guards";
  }
  return "unknown";
}
inline std::string_view WorkerMailboxSampleStageName12004(
    WorkerMailboxSampleStage12004 stage) noexcept {
  switch (stage) {
    case WorkerMailboxSampleStage12004::initial_pre_cache_lock: return "initial_pre_cache_lock";
    case WorkerMailboxSampleStage12004::post_wait_cache_unlocked: return "post_wait_cache_unlocked";
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
  text += " read_sequence=" + std::to_string(receipt.read_sequence);
  if (!receipt.worker_observation) {
    text += " worker_observed_at_stage=unknown";
  } else {
    const auto &view = *receipt.worker_observation;
    const auto number = [](const auto &value) {
      return value ? std::to_string(*value) : std::string("unknown");
    };
    const auto boolean = [](const std::optional<bool> &value) {
      return value ? std::string(*value ? "true" : "false") : std::string("unknown");
    };
    text += " worker_observed_at_stage=" +
        std::string(WorkerSnapshotObservationStageName12004(view.observed_at_stage)) +
        " mailbox_diagnostic_sample_stage=" +
        std::string(WorkerMailboxSampleStageName12004(view.diagnostic_sample_stage)) +
        " cache_present=" + (view.cache_present ? "true" : "false") +
        " current_cache_epoch=" + std::to_string(view.current_cache_epoch) +
        " cache_revision=" + std::to_string(view.cache_revision) +
        " raw_generation_counter=" + std::to_string(view.raw_generation_counter) +
        " pending_generation=" + std::to_string(view.pending_generation) +
        " active_raw_target_epoch=" + number(view.active_raw_target_epoch) +
        " active_raw_owner_thread_id=" + number(view.active_raw_owner_thread_id) +
        " last_committed_raw_generation=" + std::to_string(view.last_committed_raw_generation) +
        " raw_publish_epoch=unknown raw_publisher_thread_id=unknown" +
        " cache_date_raw=" + number(view.cache_date_raw) +
        " cache_paused=" + boolean(view.cache_paused) +
        " created_worker_thread_id=" + std::to_string(view.created_worker_thread_id) +
        " reader_thread_id=" + std::to_string(view.reader_thread_id) +
        " wait_terminal_at_stage=" + boolean(view.wait_terminal);
    if (view.expected_wait_ticket) {
      const auto &ticket = *view.expected_wait_ticket;
      text += " expected_wait_generation=" + std::to_string(ticket.generation) +
          " expected_wait_target_epoch=" + std::to_string(ticket.target_epoch) +
          " expected_wait_owner_thread_id=" + std::to_string(ticket.owner_thread_id);
    } else {
      text += " expected_wait_generation=unknown expected_wait_target_epoch=unknown"
              " expected_wait_owner_thread_id=unknown";
    }
    text += " mailbox_pump_epoch_at_sample=" + std::to_string(view.mailbox_pump_epoch) +
        " mailbox_owner_thread_id_at_sample=" + std::to_string(view.mailbox_owner_thread_id) +
        " mailbox_observed_thread_id_at_sample=" + std::to_string(view.mailbox_observed_thread_id) +
        " mailbox_stamp_read_success_at_sample=" + (view.mailbox_stamp_read_success ? "true" : "false") +
        " mailbox_tls_initialized_raw_at_sample=" + std::to_string(view.mailbox_tls_initialized) +
        " mailbox_tls_main_thread_marker_raw_at_sample=" + std::to_string(view.mailbox_tls_main_thread_marker) +
        " mailbox_stop_requested_at_sample=" + (view.mailbox_stop_requested ? "true" : "false") +
        " mailbox_date_raw_at_sample=" + number(view.mailbox_date_raw) +
        " mailbox_paused_at_sample=" + boolean(view.mailbox_paused);
  }
  return text;
}
} // namespace xar::bridge::ck3_12004
