#include "xar_bridge/loaded_feature_manifest_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>
#include <charconv>
#include <string>

namespace xar::ck3_11906 {
namespace {

struct MailboxAccessProxyV1 {
  LoadedFeatureManifestMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const LoadedFeatureManifestMailboxContextV1 &query,
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
             &ExecuteLoadedFeatureManifestMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<LoadedFeatureManifestMailboxContextV1 *>(&query);
}

bool ProxyIsMainThread(void *opaque) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp);
}

bool ProxyCaptureFrame(
    void *opaque, game::LoadedFeatureManifestFrameV1 &output) noexcept {
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
  return true;
}

bool ProxyReadMemory(void *opaque, const void *address, void *output,
                     std::size_t size) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.read_memory != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.read_memory(proxy->query->access.context,
                                          address, output, size);
}

bool ProxyReadString(void *opaque, const void *native_string,
                     std::string &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.read_string != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.read_string(proxy->query->access.context,
                                          native_string, output);
}

void MakeInternalUnavailable(
    LoadedFeatureManifestMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) {
  query.result = {};
  query.result.status = game::LoadedFeatureManifestStatusV1::unavailable;
  query.result.snapshot_revision =
      query.request.expected_snapshot_revision;
  query.result.date_raw = stamp.date_raw;
  query.result.unavailable_reason = "internal_error";
  query.result.effective_feature_flags.unavailable_reason =
      "internal_error";
  query.result.script_dlc_keys.unavailable_reason = "internal_error";
  query.read_result = game::ReadLoadedFeatureManifestResultV1::unavailable;
  query.completion =
      LoadedFeatureManifestMailboxCompletionV1::completed;
}

} // namespace

bool ParseLoadedFeatureManifestV1Step(std::string_view step) noexcept {
  return step == kLoadedFeatureManifestV1Step;
}

bool ParseLoadedFeatureManifestExpectedRevisionV1(
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

bool ExecuteLoadedFeatureManifestMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query =
      static_cast<LoadedFeatureManifestMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          LoadedFeatureManifestMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          LoadedFeatureManifestMailboxCompletionV1::infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    MailboxAccessProxyV1 proxy{query, &stamp};
    LoadedFeatureManifestAccessV1 access{};
    access.context = &proxy;
    access.capture_frame = &ProxyCaptureFrame;
    access.is_main_thread = &ProxyIsMainThread;
    access.read_memory = query->access.read_memory == nullptr
                             ? nullptr
                             : &ProxyReadMemory;
    access.read_string = query->access.read_string == nullptr
                             ? nullptr
                             : &ProxyReadString;
    query->read_result = ReadLoadedFeatureManifestV1(
        query->environment, access, query->request, query->result);
    const bool typed_available =
        query->read_result ==
            game::ReadLoadedFeatureManifestResultV1::available &&
        query->result.status ==
            game::LoadedFeatureManifestStatusV1::available &&
        query->result.readiness.actionable_ready;
    const bool typed_unavailable =
        query->read_result ==
            game::ReadLoadedFeatureManifestResultV1::unavailable &&
        query->result.status ==
            game::LoadedFeatureManifestStatusV1::unavailable &&
        !query->result.unavailable_reason.empty() &&
        !query->result.readiness.actionable_ready;
    if ((typed_available || typed_unavailable) &&
        query->result.snapshot_revision ==
            query->request.expected_snapshot_revision &&
        query->result.date_raw == stamp.date_raw) {
      query->completion =
          LoadedFeatureManifestMailboxCompletionV1::completed;
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
          LoadedFeatureManifestMailboxCompletionV1::infrastructure_rejected;
      return false;
    }
  }
}

std::string_view LoadedFeatureManifestFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    LoadedFeatureManifestMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main loaded-feature executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main loaded-feature boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main loaded-feature query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main loaded-feature query timed out";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main loaded-feature executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main loaded-feature ticket mismatch";
    case MainThreadQueryWaitResultV1::completed:
      break;
    }
  }
  if (completion == LoadedFeatureManifestMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main loaded-feature result is inconsistent"
               : "loaded-feature completion snapshot changed";
  }
  if (completion ==
      LoadedFeatureManifestMailboxCompletionV1::frame_changed) {
    return "loaded-feature application-main frame changed";
  }
  return "application-main loaded-feature executor was rejected";
}

} // namespace xar::ck3_11906
