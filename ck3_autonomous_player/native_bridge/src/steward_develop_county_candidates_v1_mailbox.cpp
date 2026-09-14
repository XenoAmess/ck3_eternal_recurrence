#include "xar_bridge/steward_develop_county_candidates_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>
#include <charconv>

namespace xar::ck3_11906 {
namespace {

struct MailboxAccessProxyV1 {
  StewardDevelopCountyCandidatesMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const StewardDevelopCountyCandidatesMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.request.expected_snapshot_revision == 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id) {
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
         mailbox.executor ==
             &ExecuteStewardDevelopCountyCandidatesMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<StewardDevelopCountyCandidatesMailboxContextV1 *>(
                 &query);
}

bool ProxyIsMainThread(void *opaque) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp);
}

bool ProxyCaptureFrame(void *opaque,
                       game::StewardDevelopCountyCandidatesFrameV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      !IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp)) {
    return false;
  }
  game::Snapshot snapshot{};
  if (!ReadSnapshot(proxy->query->bindings, snapshot) ||
      snapshot != proxy->query->expected_snapshot || !snapshot.paused ||
      snapshot.date_raw != proxy->stamp->date_raw) {
    return false;
  }
  output.snapshot_revision =
      proxy->query->request.expected_snapshot_revision;
  output.date_raw = snapshot.date_raw;
  output.paused = snapshot.paused;
  output.map_ready = snapshot.map_ready;
  output.has_played_character = snapshot.has_played_character;
  output.played_character_alive = snapshot.played_character_alive;
  output.played_character_id = snapshot.played_character_id;
  return true;
}

bool ProxyReadOfflineFixtureSource(
    void *opaque,
    StewardDevelopCountyCandidatesSourceSampleV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.read_offline_fixture_source != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.read_offline_fixture_source(
             proxy->query->access.context, output);
}

void MakeInternalUnavailable(
    StewardDevelopCountyCandidatesMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) {
  query.result = {};
  query.result.status =
      game::StewardDevelopCountyCandidatesStatusV1::unavailable;
  query.result.snapshot_revision = query.request.expected_snapshot_revision;
  query.result.observed_date_raw = stamp.date_raw;
  query.result.unavailable_reason =
      game::StewardDevelopCountyFailureReasonV1::reader_exception;
  query.read_result =
      game::ReadStewardDevelopCountyCandidatesResultV1::unavailable;
  query.completion =
      StewardDevelopCountyCandidatesMailboxCompletionV1::completed;
}

} // namespace

bool ParseStewardDevelopCountyCandidatesV1Step(
    std::string_view step) noexcept {
  return step == kStewardDevelopCountyCandidatesV1Step;
}

bool ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept {
  output = 0;
  constexpr std::string_view key = "\"expected_revision\":";
  const auto at = json.find(key);
  if (at == std::string_view::npos ||
      json.find(key, at + key.size()) != std::string_view::npos) {
    return false;
  }
  auto begin = at + key.size();
  while (begin < json.size() &&
         (json[begin] == ' ' || json[begin] == '\t' ||
          json[begin] == '\r' || json[begin] == '\n')) {
    ++begin;
  }
  auto end = begin;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') {
    ++end;
  }
  auto delimiter = end;
  while (delimiter < json.size() &&
         (json[delimiter] == ' ' || json[delimiter] == '\t' ||
          json[delimiter] == '\r' || json[delimiter] == '\n')) {
    ++delimiter;
  }
  if (end == begin || (json[begin] == '0' && end - begin != 1U) ||
      (delimiter < json.size() && json[delimiter] != ',' &&
       json[delimiter] != '}')) {
    return false;
  }
  const auto parsed =
      std::from_chars(json.data() + begin, json.data() + end, output);
  return parsed.ec == std::errc{} && parsed.ptr == json.data() + end &&
         output > 0;
}

bool ExecuteStewardDevelopCountyCandidatesMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<
      StewardDevelopCountyCandidatesMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          StewardDevelopCountyCandidatesMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          StewardDevelopCountyCandidatesMailboxCompletionV1::
              infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    MailboxAccessProxyV1 proxy{query, &stamp};
    StewardDevelopCountyCandidatesAccessV1 access{};
    access.context = &proxy;
    access.capture_frame = &ProxyCaptureFrame;
    access.is_main_thread = &ProxyIsMainThread;
    access.read_offline_fixture_source =
        query->access.read_offline_fixture_source == nullptr
            ? nullptr
            : &ProxyReadOfflineFixtureSource;
    query->read_result = ReadStewardDevelopCountyCandidatesV1(
        query->environment, access, query->request, query->result);
    const bool typed_available =
        query->read_result ==
            game::ReadStewardDevelopCountyCandidatesResultV1::available &&
        query->result.status ==
            game::StewardDevelopCountyCandidatesStatusV1::available &&
        query->result.readiness.ready;
    const bool typed_unavailable =
        query->read_result ==
            game::ReadStewardDevelopCountyCandidatesResultV1::unavailable &&
        query->result.status ==
            game::StewardDevelopCountyCandidatesStatusV1::unavailable &&
        query->result.unavailable_reason !=
            game::StewardDevelopCountyFailureReasonV1::none &&
        !query->result.readiness.ready;
    const bool observed_date_consistent =
        typed_available
            ? query->result.observed_date_raw.has_value() &&
                  query->result.observed_date_raw.value() == stamp.date_raw
            : !query->result.observed_date_raw.has_value() ||
                  query->result.observed_date_raw.value() == stamp.date_raw;
    if ((typed_available || typed_unavailable) &&
        query->result.snapshot_revision ==
            query->request.expected_snapshot_revision &&
        observed_date_consistent) {
      query->completion =
          StewardDevelopCountyCandidatesMailboxCompletionV1::completed;
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
          StewardDevelopCountyCandidatesMailboxCompletionV1::
              infrastructure_rejected;
      return false;
    }
  }
}

std::string_view StewardDevelopCountyCandidatesFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    StewardDevelopCountyCandidatesMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main steward develop-county executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main steward develop-county boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main steward develop-county query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main steward develop-county query timed out";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main steward develop-county executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main steward develop-county ticket mismatch";
    case MainThreadQueryWaitResultV1::completed:
      break;
    }
  }
  if (completion ==
      StewardDevelopCountyCandidatesMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main steward develop-county result is inconsistent"
               : "steward develop-county completion snapshot changed";
  }
  if (completion ==
      StewardDevelopCountyCandidatesMailboxCompletionV1::frame_changed) {
    return "steward develop-county application-main frame changed";
  }
  return "application-main steward develop-county executor was rejected";
}

} // namespace xar::ck3_11906
