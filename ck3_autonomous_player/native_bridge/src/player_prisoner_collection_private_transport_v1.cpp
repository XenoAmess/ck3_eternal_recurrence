#include "xar_bridge/player_prisoner_collection_private_transport_v1.hpp"
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
#include "xar_bridge/character_interaction_preview_v1_source_adapter.hpp"
#endif

#include <windows.h>

#include <atomic>
#include <charconv>
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

#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
bool CaptureReleaseFrame(
    void *opaque, CharacterInteractionPreviewFrameV1 &output) noexcept {
  auto *context = static_cast<ReadContext *>(opaque);
  xar::bridge::PlayerPrisonerFrameV1 frame{};
  if (context == nullptr || context->query == nullptr ||
      !CaptureFrame(opaque, frame)) {
    return false;
  }
  output = {};
  constexpr char prefix[] = "native:";
  std::memcpy(output.snapshot_id.data(), prefix, sizeof(prefix) - 1);
  const auto start = output.snapshot_id.data() + sizeof(prefix) - 1;
  const auto end = output.snapshot_id.data() + output.snapshot_id.size() - 1;
  const auto encoded = std::to_chars(
      start, end, context->query->expected_revision);
  if (encoded.ec != std::errc{}) return false;
  output.public_revision = frame.public_revision;
  output.native_revision = frame.native_revision;
  output.proof_epoch = frame.proof_epoch;
  output.date_raw = static_cast<std::int32_t>(frame.date_raw);
  if (static_cast<std::int64_t>(output.date_raw) != frame.date_raw)
    return false;
  output.paused = frame.paused;
  output.map_ready = frame.map_ready;
  output.has_played_character = true;
  output.played_character_alive = frame.played_character_alive;
  output.played_character_id = frame.played_character_id;
  return true;
}

bool IsReleaseMainThread(void *opaque) noexcept {
  const auto *context = static_cast<ReadContext *>(opaque);
  return context != nullptr && context->stamp != nullptr &&
         GetCurrentThreadId() == context->stamp->thread_id;
}

void ReadReleasePreviews(PlayerPrisonerCollectionMailboxContextV1 &query,
                         ReadContext &read_context) {
  if (!query.result.available || !query.result.collection_complete)
    return;
  CharacterInteractionPreviewSourceEnvironmentV1 environment{};
  environment.adapter_enabled = true;
  environment.exact_build_admitted = query.bindings.enabled;
  environment.admitted_executable_sha256 =
      kCharacterInteractionPreviewExecutableSha256V1;
  environment.module_base =
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  environment.upstream_context = &read_context;
  environment.capture_frame = CaptureReleaseFrame;
  environment.is_main_thread = IsReleaseMainThread;
  CharacterInteractionPreviewSourceStateV1 state{};
  const bool bound =
      BindCharacterInteractionPreviewSourceAdapterV1(environment, state);
  const auto snapshot_id =
      "native:" + std::to_string(query.expected_revision);
  for (std::uint32_t index = 0; index < query.result.returned_count;
       ++index) {
    auto &preview = query.release_previews[index];
    if (!bound) {
      preview.unavailable_reason =
          game::CharacterInteractionPreviewFailureV1::
              native_bindings_unavailable;
      continue;
    }
    CharacterInteractionPreviewRequestV1 request{};
    request.expected_snapshot_id = snapshot_id;
    request.expected_public_revision = query.expected_revision;
    request.expected_native_revision = query.expected_revision;
    request.expected_date_raw =
        static_cast<std::int32_t>(query.result.frame.date_raw);
    request.actor_character_id = query.result.frame.played_character_id;
    request.recipient_character_id = static_cast<std::int32_t>(
        query.result.rows[index].full_character_id);
    request.interaction_key = "release_from_prison_interaction";
    (void)ReadCharacterInteractionPreviewFromSourceAdapterV1(
        state, request, preview);
  }
  query.release_previews_complete = true;
}
#endif

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
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
    access.read_lineage = true;
#endif
    access.admitted_executable_sha256 =
        xar::bridge::kPlayerPrisonerManagementSnapshotV1ExecutableSha256;
    access.module_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    access.current_thread_id = GetCurrentThreadId();
    access.application_main_thread_id = stamp.thread_id;
    access.context = &read_context;
    access.capture_frame = CaptureFrame;
    access.read_memory = ReadMemory;
    xar::bridge::ReadPlayerPrisonerCollectionV1Private(access, query->result);
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
    ReadReleasePreviews(*query, read_context);
#endif
    query->completed = true;
    return true;
  } catch (...) {
    return false;
  }
}

std::string SerializePlayerPrisonerCollectionPrivateV1(
    const xar::bridge::PlayerPrisonerCollectionSnapshotV1 &snapshot,
    std::uint64_t snapshot_revision
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
    , const std::array<game::CharacterInteractionPreviewV1,
                       xar::bridge::kPlayerPrisonerMaximumRowsV1>
          &release_previews,
    bool release_previews_complete
#endif
) {
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
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
      "\"schema_version\":3,\"snapshot_revision\":" +
#else
      "\"schema_version\":1,\"snapshot_revision\":" +
#endif
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
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
  result += ",\"played_house_id\":";
  result += snapshot.available && snapshot.played_house_id >= 0
                ? std::to_string(snapshot.played_house_id) : "null";
  result += ",\"played_dynasty_id\":";
  result += snapshot.available && snapshot.played_dynasty_id >= 0
                ? std::to_string(snapshot.played_dynasty_id) : "null";
#endif
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
                ",\"custody_relation_verified\":true";
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1)
      if (!release_previews_complete) return {};
      result += ",\"house_id\":";
      result += snapshot.rows[index].house_id >= 0
                    ? std::to_string(snapshot.rows[index].house_id) : "null";
      result += ",\"dynasty_id\":";
      result += snapshot.rows[index].dynasty_id >= 0
                    ? std::to_string(snapshot.rows[index].dynasty_id) : "null";
      result += ",\"same_house\":";
      result += snapshot.played_house_id >= 0 &&
                        snapshot.played_house_id == snapshot.rows[index].house_id
                    ? "true" : "false";
      result += ",\"same_dynasty\":";
      result += snapshot.played_dynasty_id >= 0 &&
                        snapshot.played_dynasty_id == snapshot.rows[index].dynasty_id
                    ? "true" : "false";
      result += ",\"unconditional_release_preview\":" +
                SerializeCharacterInteractionPreviewV1(
                    release_previews[index]);
#endif
      result += '}';
    }
  }
  result += "]}";
  return result;
}

} // namespace xar::ck3_11906
