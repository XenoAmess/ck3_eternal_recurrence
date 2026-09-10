#include "xar_bridge/zhongguo_b1_cycle_snapshot_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>
#include <charconv>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

struct ProxyV1 {
  ZhongguoB1CycleSnapshotMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool Exact(const ZhongguoB1CycleSnapshotMailboxContextV1 &query,
           const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.request.expected_snapshot_revision == 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id)
    return false;
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
         mailbox.executor == &ExecuteZhongguoB1CycleSnapshotMailboxQueryV1 &&
         mailbox.executor_context == const_cast<
             ZhongguoB1CycleSnapshotMailboxContextV1 *>(&query);
}

bool Main(void *opaque) noexcept {
  const auto *p = static_cast<const ProxyV1 *>(opaque);
  return p && p->query && p->stamp && Exact(*p->query, *p->stamp);
}

bool Frame(void *opaque, game::ZhongguoCaseFrameV1 &output) noexcept {
  const auto *p = static_cast<const ProxyV1 *>(opaque);
  if (!p || !p->query || !p->stamp || !Exact(*p->query, *p->stamp))
    return false;
  game::Snapshot snapshot{};
  if (!ReadSnapshot(p->query->bindings, snapshot) ||
      snapshot != p->query->expected_snapshot || !snapshot.paused ||
      snapshot.date_raw != p->stamp->date_raw)
    return false;
  output.snapshot_revision = p->query->request.expected_snapshot_revision;
  output.date_raw = snapshot.date_raw;
  output.paused = snapshot.paused;
  output.map_ready = snapshot.map_ready;
  output.has_played_character = snapshot.has_played_character;
  output.played_character_alive = snapshot.played_character_alive;
  output.played_character_id = snapshot.played_character_id;
  return true;
}

bool Memory(void *opaque, const void *address, void *output,
            std::size_t size) noexcept {
  const auto *p = static_cast<const ProxyV1 *>(opaque);
  return p && p->query && p->stamp && p->query->access.read_memory &&
         Exact(*p->query, *p->stamp) &&
         p->query->access.read_memory(p->query->access.context, address, output,
                                      size);
}

bool Character(void *opaque, std::int32_t id) noexcept {
  const auto *p = static_cast<const ProxyV1 *>(opaque);
  return p && p->query && p->stamp && p->query->access.validate_character &&
         Exact(*p->query, *p->stamp) &&
         p->query->access.validate_character(p->query->access.context, id);
}

bool Variable(void *opaque, std::int32_t id, std::string_view key,
              ZhongguoRawVariableV1 &output) noexcept {
  const auto *p = static_cast<const ProxyV1 *>(opaque);
  return p && p->query && p->stamp &&
         p->query->access.read_allowlisted_variable &&
         Exact(*p->query, *p->stamp) &&
         p->query->access.read_allowlisted_variable(
             p->query->access.context, id, key, output);
}

bool Space(char c) noexcept {
  return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}

bool Field(std::string_view json, std::string_view key,
           std::size_t &value_at) {
  std::string needle;
  try {
    needle = "\"";
    needle += key;
    needle += "\"";
  } catch (...) {
    return false;
  }
  const auto at = json.find(needle);
  if (at == std::string_view::npos ||
      json.find(needle, at + needle.size()) != std::string_view::npos)
    return false;
  auto cursor = at + needle.size();
  while (cursor < json.size() && Space(json[cursor])) ++cursor;
  if (cursor >= json.size() || json[cursor++] != ':') return false;
  while (cursor < json.size() && Space(json[cursor])) ++cursor;
  value_at = cursor;
  return cursor < json.size();
}

bool Delimiter(std::string_view json, std::size_t cursor) {
  while (cursor < json.size() && Space(json[cursor])) ++cursor;
  return cursor == json.size() || json[cursor] == ',' || json[cursor] == '}';
}

bool Revision(std::string_view json, std::uint64_t &value) {
  std::size_t begin = 0;
  if (!Field(json, "expected_revision", begin)) return false;
  auto end = begin;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') ++end;
  if (end == begin || !Delimiter(json, end)) return false;
  const auto parsed = std::from_chars(json.data() + begin, json.data() + end,
                                      value);
  return parsed.ec == std::errc{} && parsed.ptr == json.data() + end &&
         value > 0;
}

bool Nonce(std::string_view json, std::string &value) {
  std::size_t cursor = 0;
  if (!Field(json, "request_nonce", cursor) || json[cursor++] != '"')
    return false;
  const auto begin = cursor;
  while (cursor < json.size() && json[cursor] != '"') {
    const unsigned char c = json[cursor];
    if (c == '\\' || c < 0x20 || c > 0x7e) return false;
    ++cursor;
  }
  if (cursor >= json.size() || !Delimiter(json, cursor + 1)) return false;
  try {
    value.assign(json.substr(begin, cursor - begin));
  } catch (...) {
    return false;
  }
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t i = 0; i < value.size(); ++i) {
    const char c = value[i];
    const bool a = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
                   (c >= '0' && c <= '9');
    if ((!a && c != '.' && c != '_' && c != ':' && c != '-') ||
        (i == 0 && !a))
      return false;
  }
  return true;
}

bool Forbidden(std::string_view json) {
  constexpr std::string_view aliases[] = {
      "\"variable\"", "\"variables\"", "\"variable_name\"",
      "\"variable_names\"", "\"variable_key\"", "\"character_id\"",
      "\"manager_character_id\"", "\"owner_character_id\"",
      "\"subject_character_id\"", "\"case_kind\""};
  for (auto alias : aliases) {
    auto at = json.find(alias);
    while (at != std::string_view::npos) {
      auto cursor = at + alias.size();
      while (cursor < json.size() && Space(json[cursor])) ++cursor;
      if (cursor < json.size() && json[cursor] == ':') return true;
      at = json.find(alias, at + alias.size());
    }
  }
  return false;
}

} // namespace

bool ParseZhongguoB1CycleSnapshotV1Step(std::string_view step) noexcept {
  return step == kZhongguoB1CycleSnapshotV1Step;
}

bool ParseZhongguoB1CycleSnapshotRequestV1(
    std::string_view json, ZhongguoB1CycleSnapshotRequestV1 &output) noexcept {
  output = {};
  return !Forbidden(json) && Revision(json, output.expected_snapshot_revision) &&
         Nonce(json, output.request_nonce);
}

bool ExecuteZhongguoB1CycleSnapshotMailboxQueryV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query =
      static_cast<ZhongguoB1CycleSnapshotMailboxContextV1 *>(opaque_context);
  if (!query || !Exact(*query, stamp) ||
      query->completion !=
          ZhongguoB1CycleSnapshotMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query)
      query->completion =
          ZhongguoB1CycleSnapshotMailboxCompletionV1::infrastructure_rejected;
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    ProxyV1 proxy{query, &stamp};
    ZhongguoB1CycleAccessV1 access{};
    access.context = &proxy;
    access.capture_frame = &Frame;
    access.is_main_thread = &Main;
    access.read_memory = query->access.read_memory ? &Memory : nullptr;
    access.validate_character =
        query->access.validate_character ? &Character : nullptr;
    access.read_allowlisted_variable =
        query->access.read_allowlisted_variable ? &Variable : nullptr;
    query->read_result = ReadZhongguoB1CycleSnapshotV1(
        query->environment, access, query->request, query->result);
    const bool available =
        query->read_result == game::ReadZhongguoB1CycleSnapshotResultV1::available &&
        query->result.status == game::ZhongguoB1CycleSnapshotStatusV1::available &&
        query->result.readiness.ready;
    const bool unavailable =
        query->read_result == game::ReadZhongguoB1CycleSnapshotResultV1::unavailable &&
        query->result.status == game::ZhongguoB1CycleSnapshotStatusV1::unavailable &&
        !query->result.unavailable_reason.empty() &&
        !query->result.readiness.ready;
    if ((available || unavailable) &&
        query->result.snapshot_revision ==
            query->request.expected_snapshot_revision &&
        query->result.date_raw == stamp.date_raw &&
        query->result.case_kind == kZhongguoB1CycleSnapshotV1CaseKind &&
        query->result.request_nonce == query->request.request_nonce &&
        query->result.manager_character_id ==
            query->expected_snapshot.played_character_id) {
      query->completion = ZhongguoB1CycleSnapshotMailboxCompletionV1::completed;
      return true;
    }
  } catch (...) {
  }
  query->completion =
      ZhongguoB1CycleSnapshotMailboxCompletionV1::infrastructure_rejected;
  return false;
}

std::string_view ZhongguoB1CycleSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoB1CycleSnapshotMailboxCompletionV1 completion,
    bool stable) noexcept {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main ZhongGuo B1-cycle executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main ZhongGuo B1-cycle boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main ZhongGuo B1-cycle query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main ZhongGuo B1-cycle query timed out";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main ZhongGuo B1-cycle executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main ZhongGuo B1-cycle ticket mismatch";
    case MainThreadQueryWaitResultV1::completed: break;
    }
  }
  if (completion == ZhongguoB1CycleSnapshotMailboxCompletionV1::completed)
    return stable ? "application-main ZhongGuo B1-cycle result is inconsistent"
                  : "ZhongGuo B1-cycle completion snapshot changed";
  if (completion == ZhongguoB1CycleSnapshotMailboxCompletionV1::frame_changed)
    return "ZhongGuo B1-cycle application-main frame changed";
  return "application-main ZhongGuo B1-cycle executor was rejected";
}

} // namespace xar::ck3_11906
