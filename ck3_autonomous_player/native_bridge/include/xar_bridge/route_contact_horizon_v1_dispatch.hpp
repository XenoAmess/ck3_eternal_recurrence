#pragma once

#include "xar_bridge/route_contact_horizon_v1_mailbox.hpp"

#include <string>

namespace xar::ck3_11906 {

// The bridge and the focused fixture use the same typed producer. The retry
// wakes the existing queued ticket; it neither resubmits nor extends its budget.
inline constexpr std::uint32_t kRouteContactHorizonV1QueuedWakeIntervalMs = 250;

inline MainThreadQuerySubmitResultV1 SubmitRouteContactHorizonQueryV1(
    RouteContactHorizonMailboxContextV1 &query,
    MainThreadQueryQueuedWakeTraceV1 &trace) noexcept {
  if (query.mailbox == nullptr) {
    return MainThreadQuerySubmitResultV1::invalid_request;
  }
  return TrySubmitMainThreadQueryV1(
      *query.mailbox, &ExecuteRouteContactHorizonMailboxQueryV1,
      &query, query.ticket, &trace);
}

inline MainThreadQueryWaitResultV1 WaitForRouteContactHorizonQueryV1(
    RouteContactHorizonMailboxContextV1 &query,
    MainThreadQueryQueuedWakeTraceV1 &trace) noexcept {
  if (query.mailbox == nullptr) {
    return MainThreadQueryWaitResultV1::ticket_mismatch;
  }
  return WaitForMainThreadQueryV1(
      *query.mailbox, query.ticket,
      kRouteContactHorizonV1QueuedWaitBudgetMilliseconds,
      &trace, kRouteContactHorizonV1QueuedWakeIntervalMs);
}

inline std::string RouteContactHorizonDispatchDiagnosticsV1(
    MainThreadQueryWaitResultV1 wait,
    const RouteContactHorizonMailboxContextV1 &query,
    const MainThreadQueryQueuedWakeTraceV1 &trace,
    const MainThreadQueryQueuedWakeTraceV1 &initial_trace,
    const MainThreadQueryMailboxDiagnosticsV1 &before,
    const MainThreadQueryMailboxDiagnosticsV1 &after) {
  std::string result = "{\"schema\":\"xar.route-contact-dispatch.v1\"";
  const auto number = [&](const char *key, auto value) {
    result += ",\"";
    result += key;
    result += "\":";
    result += std::to_string(value);
  };
  const auto boolean = [&](const char *key, bool value) {
    result += ",\"";
    result += key;
    result += "\":";
    result += value ? "true" : "false";
  };
  number("ticket_sequence", query.ticket.sequence);
  number("wait", static_cast<std::uint32_t>(wait));
  number("completion", static_cast<std::uint32_t>(query.completion));
  number("executor_invocations", query.executor_invocations);
  number("queued_wait_budget_ms", kRouteContactHorizonV1QueuedWaitBudgetMilliseconds);
  number("executing_wait_slice_ms", kRouteContactHorizonV1ExecutingWaitSliceMilliseconds);
  number("queued_wake_interval_ms", kRouteContactHorizonV1QueuedWakeIntervalMs);
  number("wake_owner_thread_id", trace.owner_thread_id);
  number("initial_wake_attempts", initial_trace.wake_attempts);
  number("initial_wake_succeeded", initial_trace.wake_succeeded);
  number("initial_wake_failed", initial_trace.wake_failed);
  number("queued_wake_attempts", trace.wake_attempts - initial_trace.wake_attempts);
  number("queued_wake_succeeded", trace.wake_succeeded - initial_trace.wake_succeeded);
  number("queued_wake_failed", trace.wake_failed - initial_trace.wake_failed);
  number("total_wake_attempts", trace.wake_attempts);
  number("total_wake_succeeded", trace.wake_succeeded);
  number("total_wake_failed", trace.wake_failed);
  number("pump_epoch_at_start", trace.pump_epoch_at_start);
  number("pump_epoch_at_end", trace.pump_epoch_at_end);
  number("wake_attempts", trace.wake_attempts);
  number("wake_succeeded", trace.wake_succeeded);
  number("wake_failed", trace.wake_failed);
  number("last_wake_error", trace.last_wake_error);
  const auto mailbox = [&](const char *key,
                           const MainThreadQueryMailboxDiagnosticsV1 &value) {
    result += ",\"";
    result += key;
    result += "\":{\"state\":";
    result += std::to_string(static_cast<std::uint32_t>(value.state));
    number("failure_flags", value.failure_flags);
    number("pump_epochs", value.pump_epochs);
    number("owner_verified_pump_epochs", value.owner_verified_pump_epochs);
    number("paused_owner_verified_pump_epochs", value.paused_owner_verified_pump_epochs);
    number("published_sequence", value.published_sequence);
    number("completed_sequence", value.completed_sequence);
    number("executor_started_requests", value.executor_started_requests);
    number("executor_started_sequence", value.executor_started_sequence);
    number("executor_started_pump_epoch", value.executor_started_pump_epoch);
    number("executed_requests", value.executed_requests);
    number("owner_thread_id", value.owner_thread_id);
    number("current_thread_id", value.observed_current_thread_id);
    number("tls_initialized", value.observed_tls_initialized);
    number("tls_context", value.observed_tls_context);
    number("tls_main_thread_marker", value.observed_tls_main_thread_marker);
    number("jomini_state", value.observed_jomini_state);
    number("game_state", value.observed_game_state);
    number("date_raw", value.observed_date_raw);
    boolean("paused", value.observed_paused);
    boolean("stamp_read_success", value.observed_stamp_read_success);
    boolean("iat_installed", value.iat_installed);
    boolean("sdl_poll_event_hook_installed", value.sdl_poll_event_hook_installed);
    boolean("stop_requested", value.stop_requested);
    boolean("executor_submission_enabled", value.executor_submission_enabled);
    boolean("ready", value.ready);
    result += '}';
  };
  mailbox("before_submit", before);
  mailbox("after_wait_before_reclaim", after);
  result += '}';
  return result;
}

// Called only for a negative route-contact command frame. The diagnostic is a
// sibling of error, so the successful semantic result schema is unchanged.
inline std::string RouteContactHorizonNegativeFrameWithDispatchV1(
    std::string frame, MainThreadQueryWaitResultV1 wait,
    const RouteContactHorizonMailboxContextV1 &query,
    const MainThreadQueryQueuedWakeTraceV1 &trace,
    const MainThreadQueryQueuedWakeTraceV1 &initial_trace,
    const MainThreadQueryMailboxDiagnosticsV1 &before,
    const MainThreadQueryMailboxDiagnosticsV1 &after) {
  if (frame.empty() || frame.back() != '}' ||
      frame.find("\"ok\":false") == std::string::npos) {
    return frame;
  }
  frame.pop_back();
  frame += ",\"route_contact_dispatch_v1\":";
  frame += RouteContactHorizonDispatchDiagnosticsV1(
      wait, query, trace, initial_trace, before, after);
  frame += '}';
  return frame;
}

} // namespace xar::ck3_11906
