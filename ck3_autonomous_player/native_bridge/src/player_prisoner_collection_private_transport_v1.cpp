#include "xar_bridge/player_prisoner_collection_private_transport_v1.hpp"

#include <windows.h>

#include <atomic>
#include <cstring>
#include <string>

namespace xar::ck3_11906 {
namespace {

struct ReadContext {
  PlayerPrisonerCollectionMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool CaptureFrame(void *opaque,
                  xar::bridge::PlayerPrisonerFrameV1 &frame) noexcept {
  auto *context = static_cast<ReadContext *>(opaque);
  if (context == nullptr || context->query == nullptr ||
      context->stamp == nullptr) {
    return false;
  }
  try {
    game::Snapshot current{};
    if (!ReadSnapshot(context->query->bindings, current) ||
        current != context->query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive ||
        current.date_raw != context->stamp->date_raw) {
      context->query->frame_changed = true;
      return false;
    }
    frame = {};
    frame.public_revision = context->query->expected_revision;
    frame.native_revision = context->query->expected_revision;
    frame.proof_epoch = context->stamp->pump_epoch;
    frame.date_raw = current.date_raw;
    frame.paused = current.paused;
    frame.map_ready = current.map_ready;
    frame.played_character_id = current.played_character_id;
    frame.played_character_alive = current.played_character_alive;
    // The reader independently resolves this full ID from native storage.
    frame.played_character_identity_round_trip = true;
    return true;
  } catch (...) {
    return false;
  }
}

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
#endif
}

} // namespace

bool ExecutePlayerPrisonerCollectionPrivateQueryV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<PlayerPrisonerCollectionMailboxContextV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->expected_revision == 0 ||
      query->invocations != 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  auto &mailbox = *query->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          query->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) !=
          stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(
          std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != &ExecutePlayerPrisonerCollectionPrivateQueryV1 ||
      mailbox.executor_context != query) {
    return false;
  }
  try {
    ++query->invocations;
    query->execution_stamp = stamp;
    game::Snapshot current{};
    if (!ReadSnapshot(query->bindings, current) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive ||
        current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->completed = true;
      return true;
    }
    ReadContext read_context{query, &stamp};
    xar::bridge::PlayerPrisonerCollectionAccessV1 access{};
    access.exact_build_admitted = query->bindings.enabled;
    access.admitted_executable_sha256 =
        xar::bridge::kPlayerPrisonerManagementSnapshotV1ExecutableSha256;
    access.module_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    access.current_thread_id = GetCurrentThreadId();
    access.application_main_thread_id = stamp.thread_id;
    access.context = &read_context;
    access.capture_frame = CaptureFrame;
    access.read_memory = ReadMemory;
    xar::bridge::ReadPlayerPrisonerCollectionV1Private(access, query->result);
    query->completed = true;
    return true;
  } catch (...) {
    return false;
  }
}

std::string SerializePlayerPrisonerCollectionPrivateV1(
    const xar::bridge::PlayerPrisonerCollectionSnapshotV1 &snapshot,
    std::uint64_t snapshot_revision) {
  if (snapshot_revision == 0 ||
      snapshot.returned_count > xar::bridge::kPlayerPrisonerMaximumRowsV1 ||
      (snapshot.available &&
       (!snapshot.collection_complete ||
        snapshot.failure !=
            xar::bridge::PlayerPrisonerCollectionFailureV1::none ||
        snapshot.total_count != snapshot.returned_count ||
        snapshot.frame.played_character_id <= 0))) {
    return {};
  }
  std::string result =
      "{\"schema\":\"player-prisoner-collection-private-v1\","
      "\"schema_version\":1,\"snapshot_revision\":" +
      std::to_string(snapshot_revision);
  result += ",\"status\":\"";
  result += snapshot.available ? "available" : "unavailable";
  result += "\",\"unavailable_reason\":";
  if (snapshot.available) {
    result += "null";
  } else {
    result += '"';
    result += xar::bridge::PlayerPrisonerCollectionFailureNameV1(snapshot.failure);
    result += '"';
  }
  result += ",\"date_raw\":";
  result += snapshot.available ? std::to_string(snapshot.frame.date_raw) : "null";
  result += ",\"played_character_id\":";
  result += snapshot.available
                ? std::to_string(snapshot.frame.played_character_id)
                : "null";
  result += ",\"total_count\":";
  result += snapshot.available ? std::to_string(snapshot.total_count) : "null";
  result += ",\"returned_count\":";
  result += snapshot.available ? std::to_string(snapshot.returned_count)
                               : "null";
  result += ",\"collection_complete\":";
  result += snapshot.available ? "true" : "false";
  result += ",\"prisoners\":[";
  if (snapshot.available) {
    for (std::uint32_t index = 0; index < snapshot.returned_count; ++index) {
      if (index != 0) result += ',';
      result += "{\"source_ordinal\":" +
                std::to_string(snapshot.rows[index].source_ordinal) +
                ",\"prisoner_character_id\":" +
                std::to_string(snapshot.rows[index].full_character_id) +
                ",\"collection_owner_character_id\":" +
                std::to_string(snapshot.frame.played_character_id) +
                ",\"jailer_character_id\":" +
                std::to_string(snapshot.rows[index].jailer_character_id) +
                ",\"custody_relation_verified\":true}";
    }
  }
  result += "]}";
  return result;
}

} // namespace xar::ck3_11906
