#include "xar_bridge/route_contact_horizon_v1_mailbox.hpp"

#include <windows.h>

#include <algorithm>
#include <atomic>
#include <charconv>
#include <string>

namespace xar::ck3_11906 {
namespace {

bool ParseCanonicalPositiveInt32(std::string_view text,
                                 std::int32_t &output) noexcept {
  if (text.empty() || text.front() == '0') {
    return false;
  }
  std::int32_t value = -1;
  const auto parsed =
      std::from_chars(text.data(), text.data() + text.size(), value);
  if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size() ||
      value <= 0) {
    return false;
  }
  char canonical[16]{};
  const auto rendered =
      std::to_chars(canonical, canonical + sizeof(canonical), value);
  if (rendered.ec != std::errc{} ||
      std::string_view(canonical, rendered.ptr) != text) {
    return false;
  }
  output = value;
  return true;
}

bool TakeToken(std::string_view &input, std::string_view delimiter,
               std::string_view &token) noexcept {
  const auto at = input.find(delimiter);
  if (at == std::string_view::npos) {
    return false;
  }
  token = input.substr(0, at);
  input.remove_prefix(at + delimiter.size());
  return true;
}

bool IsExecutingExactMailboxSlot(
    const RouteContactHorizonMailboxContextV1 &query,
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
         mailbox.executor == &ExecuteRouteContactHorizonMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<RouteContactHorizonMailboxContextV1 *>(&query);
}

} // namespace

bool ParseRouteContactHorizonV1Step(
    std::string_view step,
    game::RouteContactHorizonRequest &output) noexcept {
  output = {};
  if (!step.starts_with(kRouteContactHorizonV1StepPrefix)) {
    return false;
  }
  auto body = step.substr(kRouteContactHorizonV1StepPrefix.size());
  std::string_view subject_text;
  std::string_view target_text;
  std::string_view count_text;
  if (!TakeToken(body, "-to-", subject_text) ||
      !TakeToken(body, "-h-", target_text) ||
      !TakeToken(body, "-", count_text) ||
      !ParseCanonicalPositiveInt32(subject_text, output.subject_army_id) ||
      !ParseCanonicalPositiveInt32(target_text, output.target_province_id)) {
    output = {};
    return false;
  }
  std::int32_t hostile_count = 0;
  if (!ParseCanonicalPositiveInt32(count_text, hostile_count) ||
      hostile_count < 1 ||
      hostile_count >
          static_cast<std::int32_t>(kRouteContactHorizonV1MaximumHostiles)) {
    output = {};
    return false;
  }
  output.hostile_army_ids.reserve(static_cast<std::size_t>(hostile_count));
  std::int32_t prior_hostile_id = 0;
  for (std::int32_t index = 0; index < hostile_count; ++index) {
    const auto separator = body.find('-');
    const bool final = index + 1 == hostile_count;
    if ((!final && separator == std::string_view::npos) ||
        (final && separator != std::string_view::npos)) {
      output = {};
      return false;
    }
    const auto token = final ? body : body.substr(0, separator);
    std::int32_t hostile_id = -1;
    if (!ParseCanonicalPositiveInt32(token, hostile_id) ||
        hostile_id == output.subject_army_id ||
        hostile_id <= prior_hostile_id) {
      output = {};
      return false;
    }
    output.hostile_army_ids.push_back(hostile_id);
    prior_hostile_id = hostile_id;
    if (!final) {
      body.remove_prefix(separator + 1U);
    }
  }
  return output.hostile_army_ids.size() ==
         static_cast<std::size_t>(hostile_count);
}

bool ParseRouteContactExpectedRevisionV1(
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

bool RouteContactHostileScopeMatchesSnapshotV1(
    const game::Snapshot &snapshot,
    const game::RouteContactHorizonRequest &request) {
  const bool subject_is_controllable = std::any_of(
      snapshot.player_armies.begin(), snapshot.player_armies.end(),
      [&request](const game::ArmySnapshot &army) {
        return army.army_id == request.subject_army_id && army.controllable;
      });
  if (!snapshot.paused || !subject_is_controllable ||
      request.hostile_army_ids.empty() ||
      request.hostile_army_ids.size() >
          kRouteContactHorizonV1MaximumHostiles ||
      !std::is_sorted(request.hostile_army_ids.begin(),
                      request.hostile_army_ids.end()) ||
      std::adjacent_find(request.hostile_army_ids.begin(),
                         request.hostile_army_ids.end()) !=
          request.hostile_army_ids.end()) {
    return false;
  }

  std::vector<std::int32_t> expected;
  for (const auto &war : snapshot.active_wars) {
    for (const auto &enemy : war.enemy_armies) {
      if (!enemy.retreating && enemy.army_id > 0 &&
          std::find(expected.begin(), expected.end(), enemy.army_id) ==
              expected.end()) {
        expected.push_back(enemy.army_id);
      }
    }
  }
  if (expected.empty() ||
      expected.size() > kRouteContactHorizonV1MaximumHostiles) {
    return false;
  }
  std::sort(expected.begin(), expected.end());
  return expected == request.hostile_army_ids;
}

bool ExecuteRouteContactHorizonMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<RouteContactHorizonMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          RouteContactHorizonMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          RouteContactHorizonMailboxCompletionV1::infrastructure_rejected;
    }
    return false;
  }

  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    const auto status = ReadRouteContactHorizon(
        query->bindings, query->request, query->result);
    if (status == game::RouteContactHorizonStatus::available &&
        query->result.status == status &&
        query->result.date_raw == stamp.date_raw &&
        query->result.subject_route.timeline_observable &&
        query->result.subject_route.route_province_ids.size() ==
            query->result.subject_route.arrival_date_raws.size() &&
        std::all_of(
            query->result.hostile_routes.begin(),
            query->result.hostile_routes.end(),
            [](const game::RouteTimelineSnapshot &route) {
              return route.timeline_observable &&
                     route.route_province_ids.size() ==
                         route.arrival_date_raws.size();
            })) {
      query->completion = RouteContactHorizonMailboxCompletionV1::available;
      return true;
    }
    const auto timeline_failure = query->result.timeline_failure;
    query->result = {};
    query->result.status = status;
    query->result.timeline_failure = timeline_failure;
    query->completion =
        RouteContactHorizonMailboxCompletionV1::query_unavailable;
    return true;
  } catch (...) {
    query->result = {};
    query->completion =
        RouteContactHorizonMailboxCompletionV1::query_unavailable;
    return true;
  }
}

std::string_view RouteContactHorizonFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    RouteContactHorizonMailboxCompletionV1 completion,
    game::RouteContactHorizonStatus status,
    bool completion_snapshot_stable) noexcept {
  switch (wait) {
  case MainThreadQueryWaitResultV1::executor_failed:
    if (completion ==
        RouteContactHorizonMailboxCompletionV1::infrastructure_rejected) {
      return "application-main route-contact executor gate rejected execution";
    }
    if (completion ==
        RouteContactHorizonMailboxCompletionV1::not_executed) {
      return "application-main route-contact executor failed before recording completion";
    }
    return "application-main route-contact executor failed after recording completion";
  case MainThreadQueryWaitResultV1::infrastructure_failed:
    if (completion == RouteContactHorizonMailboxCompletionV1::available ||
        completion ==
            RouteContactHorizonMailboxCompletionV1::query_unavailable) {
      return "application-main route-contact boundary drifted after execution";
    }
    return "application-main route-contact mailbox infrastructure failed before execution";
  case MainThreadQueryWaitResultV1::cancelled:
    return "application-main route-contact query was cancelled";
  case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
    return "application-main route-contact query timed out before execution";
  case MainThreadQueryWaitResultV1::timeout_executor_already_running:
    return "application-main route-contact executor is still running";
  case MainThreadQueryWaitResultV1::ticket_mismatch:
    return "application-main route-contact query ticket mismatch";
  case MainThreadQueryWaitResultV1::completed:
    break;
  }

  switch (completion) {
  case RouteContactHorizonMailboxCompletionV1::not_executed:
    return "application-main route-contact executor completed without a query completion";
  case RouteContactHorizonMailboxCompletionV1::infrastructure_rejected:
    return "application-main route-contact executor gate rejected execution";
  case RouteContactHorizonMailboxCompletionV1::query_unavailable:
    break;
  case RouteContactHorizonMailboxCompletionV1::available:
    if (status == game::RouteContactHorizonStatus::available) {
      return completion_snapshot_stable
                 ? "application-main route-contact result is inconsistent"
                 : "route-contact completion snapshot changed";
    }
    break;
  }

  switch (status) {
  case game::RouteContactHorizonStatus::available:
    return "application-main route-contact completion is inconsistent";
  case game::RouteContactHorizonStatus::requires_paused:
    return "route-contact query observed an unpaused map";
  case game::RouteContactHorizonStatus::subject_army_not_found:
    return "route-contact subject army was not found";
  case game::RouteContactHorizonStatus::subject_army_not_controllable:
    return "route-contact subject army is not player-controllable";
  case game::RouteContactHorizonStatus::target_province_not_found:
    return "route-contact target province was not found";
  case game::RouteContactHorizonStatus::hostile_scope_mismatch:
    return "route-contact hostile scope changed";
  case game::RouteContactHorizonStatus::route_unavailable:
    return "CK3 could not build a complete contact route";
  case game::RouteContactHorizonStatus::timeline_unavailable:
    return "CK3 route arrival timeline is unavailable";
  case game::RouteContactHorizonStatus::state_changed:
    return "CK3 route-contact state changed during query";
  case game::RouteContactHorizonStatus::unavailable:
    return "CK3 route-contact reader is unavailable";
  }
  return "application-main route-contact failure state is unknown";
}

std::string RouteContactHorizonFailureDetailV1(
    MainThreadQueryWaitResultV1 wait,
    RouteContactHorizonMailboxCompletionV1 completion,
    const game::RouteContactHorizonSnapshot &result,
    bool completion_snapshot_stable) {
  std::string detail(RouteContactHorizonFailureMessageV1(
      wait, completion, result.status, completion_snapshot_stable));
  const auto &failure = result.timeline_failure;
  if (wait != MainThreadQueryWaitResultV1::completed ||
      completion != RouteContactHorizonMailboxCompletionV1::query_unavailable ||
      result.status != game::RouteContactHorizonStatus::timeline_unavailable ||
      failure.army_id <= 0 ||
      failure.role == game::RouteContactTimelineFailureRole::none ||
      failure.path_kind == game::RouteContactTimelinePathKind::none ||
      failure.stage == game::RouteContactTimelineFailureStage::none) {
    return detail;
  }

  std::string_view role = "unknown";
  switch (failure.role) {
  case game::RouteContactTimelineFailureRole::none:
    break;
  case game::RouteContactTimelineFailureRole::subject:
    role = "subject";
    break;
  case game::RouteContactTimelineFailureRole::hostile:
    role = "hostile";
    break;
  }

  std::string_view path_kind = "unknown";
  switch (failure.path_kind) {
  case game::RouteContactTimelinePathKind::none:
    break;
  case game::RouteContactTimelinePathKind::stationary_active:
    path_kind = "stationary_active";
    break;
  case game::RouteContactTimelinePathKind::committed_active:
    path_kind = "committed_active";
    break;
  case game::RouteContactTimelinePathKind::constructed:
    path_kind = "constructed";
    break;
  case game::RouteContactTimelinePathKind::hostile_active:
    path_kind = "hostile_active";
    break;
  }

  std::string_view stage = "unknown";
  switch (failure.stage) {
  case game::RouteContactTimelineFailureStage::none:
    break;
  case game::RouteContactTimelineFailureStage::invalid_input:
    stage = "invalid_input";
    break;
  case game::RouteContactTimelineFailureStage::active_identity:
    stage = "active_identity";
    break;
  case game::RouteContactTimelineFailureStage::path_header:
    stage = "path_header";
    break;
  case game::RouteContactTimelineFailureStage::route_speed_read:
    stage = "route_speed_read";
    break;
  case game::RouteContactTimelineFailureStage::route_origin:
    stage = "route_origin";
    break;
  case game::RouteContactTimelineFailureStage::route_entry:
    stage = "route_entry";
    break;
  case game::RouteContactTimelineFailureStage::route_adjacency:
    stage = "route_adjacency";
    break;
  case game::RouteContactTimelineFailureStage::land_speed:
    stage = "land_speed";
    break;
  case game::RouteContactTimelineFailureStage::naval_speed:
    stage = "naval_speed";
    break;
  case game::RouteContactTimelineFailureStage::current_edge_speed:
    stage = "current_edge_speed";
    break;
  case game::RouteContactTimelineFailureStage::zero_progress_boundary:
    stage = "zero_progress_boundary";
    break;
  case game::RouteContactTimelineFailureStage::edge_duration_read:
    stage = "edge_duration_read";
    break;
  case game::RouteContactTimelineFailureStage::route_duration_read:
    stage = "route_duration_read";
    break;
  case game::RouteContactTimelineFailureStage::route_duration_value:
    stage = "route_duration_value";
    break;
  case game::RouteContactTimelineFailureStage::route_duration_order:
    stage = "route_duration_order";
    break;
  case game::RouteContactTimelineFailureStage::arrival_date:
    stage = "arrival_date";
    break;
  case game::RouteContactTimelineFailureStage::route_mismatch:
    stage = "route_mismatch";
    break;
  case game::RouteContactTimelineFailureStage::timeline_shape:
    stage = "timeline_shape";
    break;
  }

  std::string suffix = " (role=";
  suffix += role;
  suffix += ", army_id=";
  suffix += std::to_string(failure.army_id);
  suffix += ", path=";
  suffix += path_kind;
  suffix += ", stage=";
  suffix += stage;
  suffix += ')';
  if (detail.size() > kRouteContactHorizonV1FailureDetailMaximumBytes) {
    detail.resize(kRouteContactHorizonV1FailureDetailMaximumBytes);
  } else if (suffix.size() <=
             kRouteContactHorizonV1FailureDetailMaximumBytes -
                 detail.size()) {
    detail += suffix;
  }
  return detail;
}

} // namespace xar::ck3_11906
