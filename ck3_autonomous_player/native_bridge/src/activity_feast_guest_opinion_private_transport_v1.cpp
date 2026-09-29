#include "activity_feast_guest_opinion_private_transport_v1.hpp"

#include "xar_bridge/faction_gift_receivers_v1.hpp"

#include <windows.h>

namespace xar::ck3_11906 {
namespace {

struct OpinionContext {
  ActivityFeastGuestOpinionPrivateQueryV1 *query = nullptr;
  std::uintptr_t module_base = 0;
  DWORD owner_thread_id = 0;
};

bool ReadFrame(void *opaque,
               bridge::ActivityFeastGuestOpinionFrameV1 &output) noexcept {
  auto &context = *static_cast<OpinionContext *>(opaque);
  game::Snapshot snapshot{};
  if (GetCurrentThreadId() != context.owner_thread_id ||
      !ReadSnapshot(context.query->bindings, snapshot))
    return false;
  output = {context.query->expected_revision,
            snapshot.date_raw,
            snapshot.played_character_id,
            snapshot.paused,
            snapshot.map_ready,
            snapshot.has_played_character && snapshot.played_character_alive};
  return true;
}

bool ReadOpinion(void *opaque, std::uint32_t recipient_character_id,
                 std::uint32_t actor_character_id,
                 std::int32_t &output) noexcept {
  auto &context = *static_cast<OpinionContext *>(opaque);
  if (GetCurrentThreadId() != context.owner_thread_id ||
      context.module_base == 0)
    return false;
  GiftOpinionReceiverResultV1 value{};
  bool succeeded = false;
  __try {
    succeeded = ReadGiftOpinionExact11906V1(
        context.module_base, context.query->bindings, recipient_character_id,
        actor_character_id, value);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    succeeded = false;
  }
  if (!succeeded || !value.query_complete) return false;
  output = value.recipient_opinion_of_player;
  return true;
}

} // namespace

bool ExecuteActivityFeastGuestOpinionPrivateV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ActivityFeastGuestOpinionPrivateQueryV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->expected_revision == 0 ||
      query->invocations != 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id)
    return false;
  auto &mailbox = *query->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          query->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) != stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != &ExecuteActivityFeastGuestOpinionPrivateV1 ||
      mailbox.executor_context != query)
    return false;
  try {
    ++query->invocations;
    game::Snapshot current{};
    if (!ReadSnapshot(query->bindings, current) ||
        current != query->expected_snapshot || !current.paused ||
        !current.map_ready || !current.has_played_character ||
        !current.played_character_alive || current.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->failure = "published_frame_changed";
      query->completed = true;
      return true;
    }
    const auto base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (!query->bindings.enabled || base == 0) {
      query->failure = "exact_activity_feast_guest_opinion_build_unavailable";
      query->completed = true;
      return true;
    }
    OpinionContext context{query, base, stamp.thread_id};
    const bridge::ActivityFeastGuestOpinionFrameV1 expected{
        query->expected_revision, current.date_raw,
        current.played_character_id, true, true, true};
    const bridge::ActivityFeastGuestOpinionEnvironmentV1 environment{
        &context, &ReadFrame, &ReadOpinion};
    query->opinion = bridge::ReadActivityFeastGuestOpinionV1(
        environment, expected, query->guest_character_id);
    query->completed = true;
    return true;
  } catch (...) {
    query->failure = "native_activity_feast_guest_opinion_exception";
    query->completed = true;
    return true;
  }
}

std::string SerializeActivityFeastGuestOpinionPrivateV1(
    const ActivityFeastGuestOpinionPrivateQueryV1 &query) {
  if (!query.completed || !query.failure.empty() || query.frame_changed)
    return {};
  const auto observed = query.opinion.status ==
                        bridge::ActivityFeastGuestOpinionStatusV1::observed;
  std::string result =
      "{\"schema\":\"activity-feast-guest-opinion-private-read-v1\","
      "\"snapshot_revision\":" + std::to_string(query.expected_revision) +
      ",\"date_raw\":" +
      std::to_string(query.expected_snapshot.date_raw) +
      ",\"actor_character_id\":" +
      std::to_string(query.expected_snapshot.played_character_id) +
      ",\"guest_character_id\":" +
      std::to_string(query.guest_character_id) +
      ",\"status\":\"" +
      std::string(bridge::ActivityFeastGuestOpinionStatusKeyV1(
          query.opinion.status)) +
      "\",\"guest_opinion_of_actor\":";
  result += observed ? std::to_string(query.opinion.guest_opinion_of_actor)
                     : "null";
  result += ",\"read_only\":true,\"raw_pointer_fields_persisted\":false}";
  return result;
}

} // namespace xar::ck3_11906
