#include "xar_bridge/zhongguo_case_snapshot_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>
#include <charconv>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

struct MailboxAccessProxyV1 {
  ZhongguoCaseSnapshotMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const ZhongguoCaseSnapshotMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.request.expected_snapshot_revision == 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
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
         mailbox.executor == &ExecuteZhongguoCaseSnapshotMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<ZhongguoCaseSnapshotMailboxContextV1 *>(&query);
}

bool ProxyIsMainThread(void *opaque) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp);
}

bool ProxyCaptureFrame(void *opaque,
                       game::ZhongguoCaseFrameV1 &output) noexcept {
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

bool ProxyValidateCharacter(void *opaque,
                            std::int32_t character_id) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.validate_character != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.validate_character(
             proxy->query->access.context, character_id);
}

bool ProxyReadAllowlistedVariable(
    void *opaque, std::int32_t character_id, std::string_view key,
    ZhongguoRawVariableV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.read_allowlisted_variable != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.read_allowlisted_variable(
             proxy->query->access.context, character_id, key, output);
}

bool IsWhitespace(char value) noexcept {
  return value == ' ' || value == '\t' || value == '\r' || value == '\n';
}

bool FieldStart(std::string_view json, std::string_view key,
                std::size_t &value_at) noexcept {
  std::string needle;
  try {
    needle.reserve(key.size() + 2);
    needle.push_back('"');
    needle.append(key);
    needle.push_back('"');
  } catch (...) {
    return false;
  }
  const auto at = json.find(needle);
  if (at == std::string_view::npos ||
      json.find(needle, at + needle.size()) != std::string_view::npos) {
    return false;
  }
  auto cursor = at + needle.size();
  while (cursor < json.size() && IsWhitespace(json[cursor])) ++cursor;
  if (cursor >= json.size() || json[cursor] != ':') return false;
  ++cursor;
  while (cursor < json.size() && IsWhitespace(json[cursor])) ++cursor;
  value_at = cursor;
  return cursor < json.size();
}

bool ValidDelimiter(std::string_view json, std::size_t cursor) noexcept {
  while (cursor < json.size() && IsWhitespace(json[cursor])) ++cursor;
  return cursor == json.size() || json[cursor] == ',' || json[cursor] == '}';
}

template <typename Value>
bool ParseUnsignedField(std::string_view json, std::string_view key,
                        Value &output) noexcept {
  output = 0;
  std::size_t begin = 0;
  if (!FieldStart(json, key, begin)) return false;
  auto end = begin;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') ++end;
  if (end == begin || (json[begin] == '0' && end - begin != 1U) ||
      !ValidDelimiter(json, end)) {
    return false;
  }
  const auto parsed =
      std::from_chars(json.data() + begin, json.data() + end, output);
  return parsed.ec == std::errc{} && parsed.ptr == json.data() + end;
}

bool ParseStringField(std::string_view json, std::string_view key,
                      std::string &output) noexcept {
  output.clear();
  std::size_t cursor = 0;
  if (!FieldStart(json, key, cursor) || json[cursor] != '"') return false;
  ++cursor;
  const auto begin = cursor;
  while (cursor < json.size() && json[cursor] != '"') {
    const auto value = static_cast<unsigned char>(json[cursor]);
    if (json[cursor] == '\\' || value < 0x20U || value > 0x7EU) {
      return false;
    }
    ++cursor;
  }
  if (cursor >= json.size() || !ValidDelimiter(json, cursor + 1)) {
    return false;
  }
  try {
    output.assign(json.substr(begin, cursor - begin));
  } catch (...) {
    return false;
  }
  return true;
}

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t index = 0; index < value.size(); ++index) {
    const char character = value[index];
    const bool alpha = (character >= 'a' && character <= 'z') ||
                       (character >= 'A' && character <= 'Z');
    const bool digit = character >= '0' && character <= '9';
    const bool punctuation = character == '.' || character == '_' ||
                             character == ':' || character == '-';
    if ((!alpha && !digit && !punctuation) ||
        (index == 0 && !alpha && !digit)) {
      return false;
    }
  }
  return true;
}

bool ContainsForbiddenVariableAlias(std::string_view json) noexcept {
  constexpr std::string_view aliases[] = {
      "\"variable\"", "\"variables\"", "\"variable_id\"",
      "\"variable_name\"", "\"variable_names\"",
      "\"variable_key\"", "\"variable_keys\"",
      "\"character_variable\"", "\"character_variable_name\"",
      "\"key\"", "\"case\"", "\"case_type\"", "\"case_id\"",
      "\"kind\"", "\"subject\"", "\"owner\"", "\"nonce\"",
  };
  for (const auto alias : aliases) {
    auto at = json.find(alias);
    while (at != std::string_view::npos) {
      auto cursor = at + alias.size();
      while (cursor < json.size() && IsWhitespace(json[cursor])) ++cursor;
      if (cursor < json.size() && json[cursor] == ':') return true;
      at = json.find(alias, at + alias.size());
    }
  }
  return false;
}

} // namespace

bool ParseZhongguoCaseSnapshotV1Step(std::string_view step) noexcept {
  return step == kZhongguoCaseSnapshotV1Step;
}

bool ParseZhongguoCaseSnapshotRequestV1(
    std::string_view json, ZhongguoCaseSnapshotRequestV1 &output) noexcept {
  output = {};
  std::uint64_t revision = 0;
  std::uint64_t subject = 0;
  std::uint64_t owner = 0;
  std::string case_kind;
  std::string request_nonce;
  if (ContainsForbiddenVariableAlias(json) ||
      !ParseUnsignedField(json, "expected_revision", revision) ||
      !ParseUnsignedField(json, "subject_character_id", subject) ||
      !ParseUnsignedField(json, "owner_character_id", owner) ||
      !ParseStringField(json, "case_kind", case_kind) ||
      !ParseStringField(json, "request_nonce", request_nonce) ||
      revision == 0 || subject == 0 ||
      subject > static_cast<std::uint64_t>(
                    std::numeric_limits<std::int32_t>::max()) ||
      owner > static_cast<std::uint64_t>(
                  std::numeric_limits<std::int32_t>::max()) ||
      case_kind != kZhongguoCaseSnapshotV1CaseKind ||
      !ValidNonce(request_nonce)) {
    return false;
  }
  output.expected_snapshot_revision = revision;
  output.subject_character_id = static_cast<std::int32_t>(subject);
  if (owner != 0) {
    output.owner_character_id = static_cast<std::int32_t>(owner);
  }
  output.case_kind = std::move(case_kind);
  output.request_nonce = std::move(request_nonce);
  return true;
}

bool ExecuteZhongguoCaseSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query =
      static_cast<ZhongguoCaseSnapshotMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          ZhongguoCaseSnapshotMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          ZhongguoCaseSnapshotMailboxCompletionV1::infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    MailboxAccessProxyV1 proxy{query, &stamp};
    ZhongguoCaseAccessV1 access{};
    access.context = &proxy;
    access.capture_frame = &ProxyCaptureFrame;
    access.is_main_thread = &ProxyIsMainThread;
    access.read_memory = query->access.read_memory == nullptr
                             ? nullptr
                             : &ProxyReadMemory;
    access.validate_character = query->access.validate_character == nullptr
                                    ? nullptr
                                    : &ProxyValidateCharacter;
    access.read_allowlisted_variable =
        query->access.read_allowlisted_variable == nullptr
            ? nullptr
            : &ProxyReadAllowlistedVariable;
    query->read_result = ReadZhongguoCaseSnapshotV1(
        query->environment, access, query->request, query->result);
    const bool typed_available =
        query->read_result ==
            game::ReadZhongguoCaseSnapshotResultV1::available &&
        query->result.status ==
            game::ZhongguoCaseSnapshotStatusV1::available &&
        query->result.readiness.case_identity_ready;
    const bool typed_unavailable =
        query->read_result ==
            game::ReadZhongguoCaseSnapshotResultV1::unavailable &&
        query->result.status ==
            game::ZhongguoCaseSnapshotStatusV1::unavailable &&
        !query->result.unavailable_reason.empty() &&
        !query->result.readiness.ready;
    if ((typed_available || typed_unavailable) &&
        query->result.snapshot_revision ==
            query->request.expected_snapshot_revision &&
        query->result.date_raw == stamp.date_raw &&
        query->result.case_kind == query->request.case_kind &&
        query->result.request_nonce == query->request.request_nonce &&
        query->result.subject_character_id ==
            query->request.subject_character_id &&
        query->result.requested_owner_character_id ==
            query->request.owner_character_id) {
      query->completion =
          ZhongguoCaseSnapshotMailboxCompletionV1::completed;
      return true;
    }
    query->completion =
        ZhongguoCaseSnapshotMailboxCompletionV1::infrastructure_rejected;
    return false;
  } catch (...) {
    query->completion =
        ZhongguoCaseSnapshotMailboxCompletionV1::infrastructure_rejected;
    return false;
  }
}

std::string_view ZhongguoCaseSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoCaseSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main ZhongGuo case executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main ZhongGuo case boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main ZhongGuo case query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main ZhongGuo case query timed out";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main ZhongGuo case executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main ZhongGuo case ticket mismatch";
    case MainThreadQueryWaitResultV1::completed:
      break;
    }
  }
  if (completion == ZhongguoCaseSnapshotMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main ZhongGuo case result is inconsistent"
               : "ZhongGuo case completion snapshot changed";
  }
  if (completion ==
      ZhongguoCaseSnapshotMailboxCompletionV1::frame_changed) {
    return "ZhongGuo case application-main frame changed";
  }
  return "application-main ZhongGuo case executor was rejected";
}

} // namespace xar::ck3_11906
