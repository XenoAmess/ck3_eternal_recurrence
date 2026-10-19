#include "ck3_12004_player_pilgrimage_activities_private_v1.hpp"
#include "xar_bridge/ck3_12004_activity_migration_v1.hpp"
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
struct Context {
  PlayerPilgrimageActivitiesPrivateQuery12004V1 *query;
  DWORD owner_thread_id;
};
bool ReadMemory(void *, std::uintptr_t address, void *output, std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && size != 0 &&
      ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void *>(address),
                        output, size, &read) != 0 && read == size;
}
bool ReadHostedFrame(void *opaque, bridge::ActivityHostedIdentityFrameV1 &output) noexcept {
  auto &context = *static_cast<Context *>(opaque);
  game::Snapshot current{};
  if (GetCurrentThreadId() != context.owner_thread_id ||
      context.query->read_snapshot == nullptr ||
      !context.query->read_snapshot(context.query->native_context, current) ||
      current != context.query->expected_snapshot || !current.paused ||
      !current.map_ready || !current.has_played_character ||
      !current.played_character_alive || current.played_character_id <= 0)
    return false;
  output = {context.query->expected_revision, current.date_raw,
            current.played_character_id, true, true, true, true};
  return true;
}
} // namespace

bool ExecutePlayerPilgrimageActivitiesPrivate12004V1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  using namespace ck3_11906;
  auto *query = static_cast<PlayerPilgrimageActivitiesPrivateQuery12004V1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->expected_revision == 0 ||
      query->invocations != 0 || stamp.pump_epoch == 0 || stamp.thread_id == 0 ||
      !stamp.paused || stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id)
    return false;
  auto &mailbox = *query->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) != MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) != query->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) != stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != &ExecutePlayerPilgrimageActivitiesPrivate12004V1 ||
      mailbox.executor_context != query)
    return false;
  try {
    ++query->invocations;
    game::Snapshot current{};
    if (query->read_snapshot == nullptr ||
        !query->read_snapshot(query->native_context, current) ||
        current != query->expected_snapshot || !current.paused || !current.map_ready ||
        !current.has_played_character || !current.played_character_alive ||
        current.played_character_id <= 0 || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
    } else if (!query->enabled || query->module_base == 0 ||
               !bridge::IsActivity12004BuildV1(query->executable_sha256)) {
      query->failure = "exact_player_pilgrimage_identities_build_unavailable";
    } else {
      Context context{query, stamp.thread_id};
      const bridge::ActivityHostedIdentityFrameV1 frame{
          query->expected_revision, current.date_raw, current.played_character_id,
          true, true, true, true};
      const bridge::ActivityHostedIdentityEnvironmentV1 environment{
          true, query->executable_sha256, query->module_base, &context,
          &ReadMemory, &ReadHostedFrame};
      query->pilgrimage_identities = bridge::ReadActivityHostedIdentityV1(environment, frame);
      if (query->pilgrimage_identities.status != bridge::ActivityHostedIdentityStatusV1::observed)
        query->failure = "native_player_pilgrimage_identities_unavailable";
    }
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_player_pilgrimage_identities_exception";
    query->completed = true;
    return true;
  }
}

// The wire serializer is moved verbatim except for its dedicated query type
// and removal of the now-unnecessary World-query mode flag check.
std::string SerializePlayerPilgrimageActivitiesPrivate12004V1(
    const PlayerPilgrimageActivitiesPrivateQuery12004V1 &query) {
  const auto &identities = query.pilgrimage_identities;
  if (!query.completed || !query.failure.empty() ||
      !bridge::IsActivity12004BuildV1(query.executable_sha256) ||
      identities.status != bridge::ActivityHostedIdentityStatusV1::observed ||
      identities.hosted_count > identities.hosted.size())
    return {};
  std::string rows = "[";
  std::uint32_t count = 0;
  const auto boolean = [](bool value) { return value ? "true" : "false"; };
  for (std::size_t index = 0; index < identities.hosted_count; ++index) {
    const auto &row = identities.hosted[index];
    if (row.type_key_size > row.type_key.size()) return {};
    if (std::string_view(row.type_key.data(), row.type_key_size) != "activity_pilgrimage") continue;
    if (row.host_character_id != query.expected_snapshot.played_character_id) return {};
    if (count++ != 0) rows += ',';
    rows += "{\"activity_id\":" + std::to_string(row.activity_id) +
        ",\"host_character_id\":" + std::to_string(row.host_character_id) +
        ",\"type_key\":\"activity_pilgrimage\",\"terminal_flags_observed\":" +
        boolean(row.terminal_flags_observed) + ",\"native_completed\":";
    rows += row.terminal_flags_observed ? boolean(row.native_completed) : "null";
    rows += ",\"native_invalidated\":";
    rows += row.terminal_flags_observed ? boolean(row.native_invalidated) : "null";
    rows += ",\"native_completion_stamp_observed\":";
    rows += boolean(row.native_completion_stamp_observed);
    rows += ",\"native_completion_stamp_raw\":";
    rows += row.native_completion_stamp_observed ? std::to_string(row.native_completion_stamp_raw) : "null";
    rows += '}';
  }
  rows += ']';
  return "{\"schema\":\"ck3_12004_player_pilgrimage_activities_v1\",\"read_only\":true,"
      "\"snapshot_revision\":" + std::to_string(query.expected_revision) +
      ",\"date_raw\":" + std::to_string(query.expected_snapshot.date_raw) +
      ",\"played_character_id\":" + std::to_string(query.expected_snapshot.played_character_id) +
      ",\"scope\":\"currently-hosted-by-current-player\","
      "\"activity_type_key\":\"activity_pilgrimage\",\"activity_count\":" + std::to_string(count) +
      ",\"activities\":" + rows + ",\"absence_is_completion\":false,\"raw_pointer_fields_persisted\":false}";
}
} // namespace xar::ck3_12002
