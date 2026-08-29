#include "xar_bridge/title_map_navigation_v1_mailbox.hpp"

#include <windows.h>

#include <algorithm>
#include <atomic>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <string>

namespace xar::ck3_11906 {
namespace {

struct MailboxAccessProxyV1 {
  TitleMapNavigationMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const TitleMapNavigationMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
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
         mailbox.executor == &ExecuteTitleMapNavigationMailboxV1 &&
         mailbox.executor_context ==
             const_cast<TitleMapNavigationMailboxContextV1 *>(&query);
}

bool ProxyOwnsThread(void *opaque) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp);
}

bool ProxyCaptureFrame(
    void *opaque, game::TitleMapNavigationFrameV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      !IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp)) {
    return false;
  }
  game::Snapshot snapshot{};
  if (!ReadSnapshot(proxy->query->bindings, snapshot) ||
      snapshot != proxy->query->expected_snapshot || !snapshot.paused ||
      !snapshot.map_ready ||
      snapshot.date_raw != proxy->stamp->date_raw) {
    return false;
  }
  output.snapshot_revision =
      proxy->query->command.request.expected_snapshot_revision;
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
         proxy->query->access.title.read_memory != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.title.read_memory(
             proxy->query->access.title.context, address, output, size);
}

bool ProxyReadString(void *opaque, const void *native_string,
                     std::string &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.title.read_string != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.title.read_string(
             proxy->query->access.title.context, native_string, output);
}

bool ProxyResolveTitleFixture(void *opaque, std::string_view key,
                              void *&output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.title.resolve_title_fixture != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.title.resolve_title_fixture(
             proxy->query->access.title.context, key, output);
}

bool ProxyResolveProvinceFixture(void *opaque, void *title,
                                 void *&output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.title.resolve_province_fixture != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.title.resolve_province_fixture(
             proxy->query->access.title.context, title, output);
}

bool ProxyResolveHandlerCameraFixture(void *opaque, void *&handler,
                                      void *&camera) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.resolve_handler_camera_fixture != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.resolve_handler_camera_fixture(
             proxy->query->access.title.context, handler, camera);
}

bool ProxyComputeBoundsFixture(
    void *opaque, void *title,
    std::array<std::int32_t, 4> &bounds) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.compute_bounds_fixture != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.compute_bounds_fixture(
             proxy->query->access.title.context, title, bounds);
}

bool ProxyQueryHandlerModeFixture(void *opaque, void *handler,
                                  std::int32_t mask,
                                  bool &enabled) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.query_handler_mode_fixture != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.query_handler_mode_fixture(
             proxy->query->access.title.context, handler, mask, enabled);
}

bool ProxyCanonicalizeFixture(
    void *opaque, void *camera,
    std::array<float, 6> &state) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.canonicalize_fixture != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.canonicalize_fixture(
             proxy->query->access.title.context, camera, state);
}

bool ProxyDispatchFixture(void *opaque, void *handler, void *title,
                          bool force_zoom) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.dispatch_fixture != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.dispatch_fixture(
             proxy->query->access.title.context, handler, title, force_zoom);
}

bool ParseUnsignedMember(std::string_view json, std::string_view key,
                         std::uint64_t &output) noexcept {
  output = 0;
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
  return parsed.ec == std::errc{} && parsed.ptr == json.data() + end;
}

bool ParseCanonicalKeyMember(std::string_view json, std::string &output) {
  output.clear();
  constexpr std::string_view key = "\"title_key\":";
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
  if (begin >= json.size() || json[begin] != '"') {
    return false;
  }
  ++begin;
  const auto end = json.find('"', begin);
  if (end == std::string_view::npos || end - begin > 1'024 ||
      json.substr(begin, end - begin).find('\\') !=
          std::string_view::npos) {
    return false;
  }
  auto delimiter = end + 1;
  while (delimiter < json.size() &&
         (json[delimiter] == ' ' || json[delimiter] == '\t' ||
          json[delimiter] == '\r' || json[delimiter] == '\n')) {
    ++delimiter;
  }
  if (delimiter < json.size() && json[delimiter] != ',' &&
      json[delimiter] != '}') {
    return false;
  }
  output.assign(json.substr(begin, end - begin));
  return IsCanonicalLandedTitleKeyV1(output);
}

std::uint32_t RemainingBudget(std::uint64_t started,
                              std::uint32_t total) noexcept {
  const auto elapsed = GetTickCount64() - started;
  if (elapsed >= total) {
    return 0;
  }
  return static_cast<std::uint32_t>(
      std::min<std::uint64_t>(total - elapsed,
                              kTitleMapNavigationV1QueuedWaitBudgetMilliseconds));
}

void SetRunFailure(TitleMapNavigationMailboxContextV1 &query,
                   game::TitleMapNavigationCommandStatusV1 status) noexcept {
  if (!IsTitleMapNavigationTerminalV1(query.command.status)) {
    query.command.status = status;
  }
}

} // namespace

bool ParseTitleMapNavigationV1Step(std::string_view step) noexcept {
  return step == kTitleMapNavigationV1Step;
}

bool ParseTitleMapNavigationRequestV1(
    std::string_view json, TitleMapNavigationRequestV1 &output) noexcept {
  output = {};
  try {
    constexpr std::string_view revision_key = "\"expected_revision\":";
    return ParseUnsignedMember(json, revision_key,
                               output.expected_snapshot_revision) &&
           ParseCanonicalKeyMember(json, output.title_key);
  } catch (...) {
    output = {};
    return false;
  }
}

bool ExecuteTitleMapNavigationMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query =
      static_cast<TitleMapNavigationMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          TitleMapNavigationMailboxCompletionV1::not_executed ||
      query->ticket.sequence <= query->last_ticket_sequence ||
      stamp.pump_epoch <= query->last_pump_epoch ||
      (query->command.dispatched &&
       (query->dispatch_pump_epoch == 0 ||
        stamp.pump_epoch <= query->dispatch_pump_epoch))) {
    if (query != nullptr) {
      query->completion =
          TitleMapNavigationMailboxCompletionV1::infrastructure_rejected;
      query->command.status =
          game::TitleMapNavigationCommandStatusV1::state_changed;
    }
    return false;
  }

  try {
    const bool was_dispatched = query->command.dispatched;
    query->execution_stamp = stamp;
    query->last_pump_epoch = stamp.pump_epoch;
    query->last_ticket_sequence = query->ticket.sequence;
    ++query->callback_count;

    MailboxAccessProxyV1 proxy{query, &stamp};
    TitleMapNavigationCameraAccessV1 access{};
    access.title.context = &proxy;
    access.title.capture_frame = &ProxyCaptureFrame;
    access.title.is_owning_thread = &ProxyOwnsThread;
    access.title.read_memory =
        query->access.title.read_memory == nullptr ? nullptr
                                                   : &ProxyReadMemory;
    access.title.read_string =
        query->access.title.read_string == nullptr ? nullptr
                                                   : &ProxyReadString;
    access.title.resolve_title_fixture =
        query->access.title.resolve_title_fixture == nullptr
            ? nullptr
            : &ProxyResolveTitleFixture;
    access.title.resolve_province_fixture =
        query->access.title.resolve_province_fixture == nullptr
            ? nullptr
            : &ProxyResolveProvinceFixture;
    access.resolve_handler_camera_fixture =
        query->access.resolve_handler_camera_fixture == nullptr
            ? nullptr
            : &ProxyResolveHandlerCameraFixture;
    access.compute_bounds_fixture =
        query->access.compute_bounds_fixture == nullptr
            ? nullptr
            : &ProxyComputeBoundsFixture;
    access.query_handler_mode_fixture =
        query->access.query_handler_mode_fixture == nullptr
            ? nullptr
            : &ProxyQueryHandlerModeFixture;
    access.canonicalize_fixture =
        query->access.canonicalize_fixture == nullptr
            ? nullptr
            : &ProxyCanonicalizeFixture;
    access.dispatch_fixture =
        query->access.dispatch_fixture == nullptr
            ? nullptr
            : &ProxyDispatchFixture;

    const auto status = AdvanceTitleMapNavigationCommandV1(
        query->title_environment, query->camera_environment, access,
        query->command);
    if (!was_dispatched && query->command.dispatched) {
      if (status != game::TitleMapNavigationCommandStatusV1::pending ||
          query->dispatch_ticket_sequence != 0 ||
          query->dispatch_pump_epoch != 0) {
        query->completion =
            TitleMapNavigationMailboxCompletionV1::infrastructure_rejected;
        query->command.status =
            game::TitleMapNavigationCommandStatusV1::internal_error;
        return false;
      }
      query->dispatch_ticket_sequence = query->ticket.sequence;
      query->dispatch_pump_epoch = stamp.pump_epoch;
    } else if (was_dispatched) {
      ++query->poll_count;
    }

    const bool valid_centered =
        status != game::TitleMapNavigationCommandStatusV1::centered ||
        (query->command.dispatched &&
         query->dispatch_ticket_sequence > 0 &&
         query->dispatch_pump_epoch > 0 &&
         stamp.pump_epoch > query->dispatch_pump_epoch);
    const bool valid_already =
        status !=
            game::TitleMapNavigationCommandStatusV1::already_centered ||
        (!query->command.dispatched &&
         query->dispatch_ticket_sequence == 0 &&
         query->dispatch_pump_epoch == 0);
    if (!valid_centered || !valid_already) {
      query->completion =
          TitleMapNavigationMailboxCompletionV1::infrastructure_rejected;
      query->command.status =
          game::TitleMapNavigationCommandStatusV1::internal_error;
      return false;
    }
    query->completion = TitleMapNavigationMailboxCompletionV1::advanced;
    return true;
  } catch (...) {
    query->completion =
        TitleMapNavigationMailboxCompletionV1::infrastructure_rejected;
    query->command.status =
        game::TitleMapNavigationCommandStatusV1::internal_error;
    return false;
  }
}

TitleMapNavigationMailboxRunResultV1 RunTitleMapNavigationMailboxV1(
    TitleMapNavigationMailboxContextV1 &query,
    std::uint32_t total_budget_milliseconds,
    std::uint32_t maximum_callbacks) noexcept {
  using Run = TitleMapNavigationMailboxRunResultV1;
  using Status = game::TitleMapNavigationCommandStatusV1;
  if (query.mailbox == nullptr || total_budget_milliseconds == 0 ||
      maximum_callbacks == 0 ||
      IsTitleMapNavigationTerminalV1(query.command.status)) {
    SetRunFailure(query, Status::submission_failed);
    return Run::submission_rejected;
  }

  const auto started = GetTickCount64();
  while (!IsTitleMapNavigationTerminalV1(query.command.status)) {
    if (query.callback_count >= maximum_callbacks ||
        RemainingBudget(started, total_budget_milliseconds) == 0) {
      query.command.status = Status::camera_state_unavailable;
      return Run::settle_budget_exhausted;
    }

    query.completion = TitleMapNavigationMailboxCompletionV1::not_executed;
    query.ticket = {};
    const auto submit = TrySubmitMainThreadQueryV1(
        *query.mailbox, &ExecuteTitleMapNavigationMailboxV1, &query,
        query.ticket);
    if (submit != MainThreadQuerySubmitResultV1::submitted) {
      SetRunFailure(query, Status::submission_failed);
      return Run::submission_rejected;
    }

    auto remaining = RemainingBudget(started, total_budget_milliseconds);
    auto wait = WaitForMainThreadQueryV1(
        *query.mailbox, query.ticket,
        std::max<std::uint32_t>(remaining, 1));
    while (wait ==
           MainThreadQueryWaitResultV1::timeout_executor_already_running) {
      // The application-main thread still owns query.  Its stack lifetime
      // cannot end until the callback becomes terminal and is reclaimed.
      wait = WaitForMainThreadQueryV1(
          *query.mailbox, query.ticket,
          kTitleMapNavigationV1ExecutingWaitSliceMilliseconds);
    }

    const auto reclaimed =
        ReclaimMainThreadQueryV1(*query.mailbox, query.ticket);
    if (reclaimed != MainThreadQueryReclaimResultV1::reclaimed) {
      SetRunFailure(query, Status::submission_failed);
      return Run::reclaim_failed;
    }
    if (wait != MainThreadQueryWaitResultV1::completed ||
        query.completion !=
            TitleMapNavigationMailboxCompletionV1::advanced) {
      SetRunFailure(query, Status::submission_failed);
      return Run::wait_failed;
    }
    if (IsTitleMapNavigationTerminalV1(query.command.status)) {
      return Run::terminal;
    }
  }
  return Run::terminal;
}

} // namespace xar::ck3_11906
