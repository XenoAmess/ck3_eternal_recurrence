#include "xar_bridge/player_faction_alerts_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>
#include <charconv>

namespace xar::ck3_11906 {
namespace {

struct MailboxAccessProxyV1 {
  PlayerFactionAlertsMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const PlayerFactionAlertsMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.request.expected_snapshot_revision == 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor == &ExecutePlayerFactionAlertsMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<PlayerFactionAlertsMailboxContextV1 *>(&query);
}

bool ProxyIsMainThread(void *opaque) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp);
}

bool ProxySnapshot(const MailboxAccessProxyV1 &proxy,
                   game::Snapshot &output) noexcept {
  return IsExecutingExactMailboxSlot(*proxy.query, *proxy.stamp) &&
         ReadSnapshot(proxy.query->bindings, output) &&
         output == proxy.query->expected_snapshot && output.paused &&
         output.date_raw == proxy.stamp->date_raw;
}

bool ProxyCaptureFrame(void *opaque,
                       game::PlayerFactionAlertsFrameV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr) {
    return false;
  }
  game::Snapshot snapshot{};
  if (!ProxySnapshot(*proxy, snapshot)) return false;
  output.snapshot_revision = proxy->query->request.expected_snapshot_revision;
  output.date_raw = snapshot.date_raw;
  output.paused = snapshot.paused;
  output.map_ready = snapshot.map_ready;
  output.has_played_character = snapshot.has_played_character;
  output.played_character_alive = snapshot.played_character_alive;
  output.played_character_id = snapshot.played_character_id;
  return true;
}

bool ProxyCaptureCampaignRootFrame(
    void *opaque, game::CampaignRootFrameV1 &output) noexcept {
  game::PlayerFactionAlertsFrameV1 frame{};
  if (!ProxyCaptureFrame(opaque, frame)) return false;
  output.snapshot_revision = frame.snapshot_revision;
  output.date_raw = frame.date_raw;
  output.paused = frame.paused;
  output.map_ready = frame.map_ready;
  output.has_played_character = frame.has_played_character;
  output.played_character_alive = frame.played_character_alive;
  output.played_character_id = frame.played_character_id;
  return true;
}

bool ProxyReadTargetingFactionCount(
    void *opaque, std::int32_t expected_player_character_id,
    std::int32_t &output) noexcept {
  auto *proxy = static_cast<MailboxAccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      !IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp)) {
    return false;
  }
  CampaignRootAccessV1 access{};
  access.context = proxy;
  access.capture_frame = &ProxyCaptureCampaignRootFrame;
  access.is_main_thread = &ProxyIsMainThread;
  return ReadCampaignRootTargetingFactionCountV1(
      proxy->query->campaign_root_environment, access,
      expected_player_character_id, output);
}

bool ProxyReadOfflineFixtureSource(
    void *opaque, PlayerFactionAlertsSourceSampleV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.read_offline_fixture_source != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.read_offline_fixture_source(
             proxy->query->access.context, output);
}

void MakeInternalUnavailable(PlayerFactionAlertsMailboxContextV1 &query,
                             const MainThreadExecutionStampV1 &stamp) {
  query.result = {};
  query.result.status = game::PlayerFactionAlertsStatusV1::unavailable;
  query.result.snapshot_revision = query.request.expected_snapshot_revision;
  query.result.date_raw = stamp.date_raw;
  query.result.unavailable_reason =
      game::PlayerFactionAlertsFailureReasonV1::reader_exception;
  query.read_result = game::ReadPlayerFactionAlertsResultV1::unavailable;
  query.completion = PlayerFactionAlertsMailboxCompletionV1::completed;
}

} // namespace

bool ParsePlayerFactionAlertsV1Step(std::string_view step) noexcept {
  return step == kPlayerFactionAlertsV1Step;
}

bool ParsePlayerFactionAlertsExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept {
  output = 0;
  constexpr std::string_view key = "\"expected_revision\":";
  const auto at = json.find(key);
  if (at == std::string_view::npos ||
      json.find(key, at + key.size()) != std::string_view::npos) return false;
  auto begin = at + key.size();
  while (begin < json.size() &&
         (json[begin] == ' ' || json[begin] == '\t' ||
          json[begin] == '\r' || json[begin] == '\n')) ++begin;
  auto end = begin;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') ++end;
  auto delimiter = end;
  while (delimiter < json.size() &&
         (json[delimiter] == ' ' || json[delimiter] == '\t' ||
          json[delimiter] == '\r' || json[delimiter] == '\n')) ++delimiter;
  if (end == begin || (json[begin] == '0' && end - begin != 1U) ||
      (delimiter < json.size() && json[delimiter] != ',' &&
       json[delimiter] != '}')) return false;
  const auto parsed =
      std::from_chars(json.data() + begin, json.data() + end, output);
  return parsed.ec == std::errc{} && parsed.ptr == json.data() + end &&
         output > 0;
}

bool ExecutePlayerFactionAlertsMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query =
      static_cast<PlayerFactionAlertsMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion != PlayerFactionAlertsMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          PlayerFactionAlertsMailboxCompletionV1::infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    MailboxAccessProxyV1 proxy{query, &stamp};
    PlayerFactionAlertsAccessV1 access{};
    access.context = &proxy;
    access.capture_frame = &ProxyCaptureFrame;
    access.is_main_thread = &ProxyIsMainThread;
    access.read_targeting_faction_count =
        query->environment.offline_fixture_source
            ? nullptr
            : &ProxyReadTargetingFactionCount;
    access.read_offline_fixture_source =
        query->access.read_offline_fixture_source == nullptr
            ? nullptr
            : &ProxyReadOfflineFixtureSource;
    query->read_result = ReadPlayerFactionAlertsV1(
        query->environment, access, query->request, query->result);
    const bool typed_available =
        query->read_result == game::ReadPlayerFactionAlertsResultV1::available &&
        query->result.status == game::PlayerFactionAlertsStatusV1::available &&
        query->result.readiness.same_frame_ready &&
        query->result.readiness.targeting_count_ready;
    const bool typed_unavailable =
        query->read_result ==
            game::ReadPlayerFactionAlertsResultV1::unavailable &&
        query->result.status ==
            game::PlayerFactionAlertsStatusV1::unavailable &&
        query->result.unavailable_reason !=
            game::PlayerFactionAlertsFailureReasonV1::none &&
        !query->result.readiness.alert_ready;
    const bool date_consistent =
        query->result.date_raw.has_value() &&
        query->result.date_raw.value() == stamp.date_raw;
    if ((typed_available || typed_unavailable) &&
        query->result.snapshot_revision ==
            query->request.expected_snapshot_revision &&
        date_consistent) {
      query->completion = PlayerFactionAlertsMailboxCompletionV1::completed;
      return true;
    }
    MakeInternalUnavailable(*query, stamp);
    return true;
  } catch (...) {
    try {
      MakeInternalUnavailable(*query, stamp);
      return true;
    } catch (...) {
      query->completion =
          PlayerFactionAlertsMailboxCompletionV1::infrastructure_rejected;
      return false;
    }
  }
}

std::string_view PlayerFactionAlertsFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    PlayerFactionAlertsMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main player faction-alert executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main player faction-alert boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main player faction-alert query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main player faction-alert query timed out";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main player faction-alert executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main player faction-alert ticket mismatch";
    case MainThreadQueryWaitResultV1::completed:
      break;
    }
  }
  if (completion == PlayerFactionAlertsMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main player faction-alert result is inconsistent"
               : "player faction-alert completion snapshot changed";
  }
  if (completion == PlayerFactionAlertsMailboxCompletionV1::frame_changed) {
    return "player faction-alert application-main frame changed";
  }
  return "application-main player faction-alert executor was rejected";
}

} // namespace xar::ck3_11906
