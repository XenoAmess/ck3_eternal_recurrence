#include "xar_bridge/zhongguo_ai_owned_case_snapshot_v1_mailbox.hpp"

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
  ZhongguoAiOwnedCaseSnapshotMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const ZhongguoAiOwnedCaseSnapshotMailboxContextV1 &query,
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
         mailbox.executor ==
             &ExecuteZhongguoAiOwnedCaseSnapshotMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<ZhongguoAiOwnedCaseSnapshotMailboxContextV1 *>(&query);
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
         proxy->query->access.variables.read_memory != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.variables.read_memory(
             proxy->query->access.variables.context, address, output, size);
}

bool ProxyValidateCharacter(void *opaque,
                            std::int32_t character_id) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.variables.validate_character != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.variables.validate_character(
             proxy->query->access.variables.context, character_id);
}

bool ProxyReadAllowlistedVariable(
    void *opaque, std::int32_t character_id, std::string_view key,
    ZhongguoRawVariableV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.variables.read_allowlisted_variable != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.variables.read_allowlisted_variable(
             proxy->query->access.variables.context, character_id, key,
             output);
}

bool ProxyObserveOwnerEligibility(
    void *opaque, std::int32_t owner_character_id,
    std::int32_t subject_character_id,
    ZhongguoAiOwnerEligibilityObservationV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.observe_owner_eligibility != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.observe_owner_eligibility(
             proxy->query->access.variables.context, owner_character_id,
             subject_character_id, output);
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

bool ContainsForbiddenAlias(std::string_view json) noexcept {
  constexpr std::string_view aliases[] = {
      "\"variable\"", "\"variables\"", "\"variable_id\"",
      "\"variable_name\"", "\"variable_names\"",
      "\"variable_key\"", "\"variable_keys\"",
      "\"character_variable\"", "\"character_variable_name\"",
      "\"key\"", "\"case\"", "\"case_kind\"", "\"case_type\"",
      "\"case_id\"", "\"kind\"", "\"subject\"", "\"owner\"",
      "\"nonce\"",
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

bool HasOnlyAllowlistedRequestFields(std::string_view json) noexcept {
  constexpr std::string_view fields[] = {
      "type",          "protocol_version", "request_id",
      "step",          "expected_revision", "owner_character_id",
      "subject_character_id", "request_nonce",
  };
  std::array<bool, std::size(fields)> seen{};
  std::size_t cursor = 0;
  while (cursor < json.size()) {
    const auto quote = json.find('"', cursor);
    if (quote == std::string_view::npos) break;
    auto end = quote + 1;
    while (end < json.size() && json[end] != '"') {
      if (json[end] == '\\' ||
          static_cast<unsigned char>(json[end]) < 0x20U) {
        return false;
      }
      ++end;
    }
    if (end >= json.size()) return false;
    auto after = end + 1;
    while (after < json.size() && IsWhitespace(json[after])) ++after;
    if (after < json.size() && json[after] == ':') {
      const auto key = json.substr(quote + 1, end - quote - 1);
      std::size_t index = 0;
      while (index < std::size(fields) && fields[index] != key) ++index;
      if (index == std::size(fields) || seen[index]) return false;
      seen[index] = true;
    }
    cursor = end + 1;
  }
  return true;
}

} // namespace

bool ParseZhongguoAiOwnedCaseSnapshotV1Step(
    std::string_view step) noexcept {
  return step == kZhongguoAiOwnedCaseSnapshotV1Step;
}

bool ParseZhongguoAiOwnedCaseSnapshotRequestV1(
    std::string_view json,
    ZhongguoAiOwnedCaseSnapshotRequestV1 &output) noexcept {
  output = {};
  std::uint64_t revision = 0;
  std::uint64_t owner = 0;
  std::uint64_t subject = 0;
  std::string request_nonce;
  if (ContainsForbiddenAlias(json) ||
      !HasOnlyAllowlistedRequestFields(json) ||
      !ParseUnsignedField(json, "expected_revision", revision) ||
      !ParseUnsignedField(json, "owner_character_id", owner) ||
      !ParseUnsignedField(json, "subject_character_id", subject) ||
      !ParseStringField(json, "request_nonce", request_nonce) ||
      revision == 0 || owner == 0 || subject == 0 || owner == subject ||
      owner > static_cast<std::uint64_t>(
                  std::numeric_limits<std::int32_t>::max()) ||
      subject > static_cast<std::uint64_t>(
                    std::numeric_limits<std::int32_t>::max()) ||
      !ValidNonce(request_nonce)) {
    return false;
  }
  output.expected_snapshot_revision = revision;
  output.owner_character_id = static_cast<std::int32_t>(owner);
  output.subject_character_id = static_cast<std::int32_t>(subject);
  output.request_nonce = std::move(request_nonce);
  return true;
}

bool ExecuteZhongguoAiOwnedCaseSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<ZhongguoAiOwnedCaseSnapshotMailboxContextV1 *>(
      opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1::
              infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    MailboxAccessProxyV1 proxy{query, &stamp};
    ZhongguoAiOwnedCaseAccessV1 access{};
    access.variables.context = &proxy;
    access.variables.capture_frame = &ProxyCaptureFrame;
    access.variables.is_main_thread = &ProxyIsMainThread;
    access.variables.read_memory =
        query->access.variables.read_memory == nullptr ? nullptr
                                                       : &ProxyReadMemory;
    access.variables.validate_character =
        query->access.variables.validate_character == nullptr
            ? nullptr
            : &ProxyValidateCharacter;
    access.variables.read_allowlisted_variable =
        query->access.variables.read_allowlisted_variable == nullptr
            ? nullptr
            : &ProxyReadAllowlistedVariable;
    access.observe_owner_eligibility =
        query->access.observe_owner_eligibility == nullptr
            ? nullptr
            : &ProxyObserveOwnerEligibility;
    query->read_result = ReadZhongguoAiOwnedCaseSnapshotV1(
        query->environment, access, query->request, query->result);
    const bool typed_available =
        query->read_result ==
            game::ReadZhongguoAiOwnedCaseSnapshotResultV1::available &&
        query->result.status ==
            game::ZhongguoAiOwnedCaseSnapshotStatusV1::available &&
        query->result.readiness.owner_eligibility_ready &&
        query->result.readiness.case_identity_ready &&
        query->result.readiness.route_ready;
    const bool typed_unavailable =
        query->read_result ==
            game::ReadZhongguoAiOwnedCaseSnapshotResultV1::unavailable &&
        query->result.status ==
            game::ZhongguoAiOwnedCaseSnapshotStatusV1::unavailable &&
        !query->result.unavailable_reason.empty() &&
        !query->result.readiness.ready;
    if ((typed_available || typed_unavailable) &&
        query->result.snapshot_revision ==
            query->request.expected_snapshot_revision &&
        query->result.date_raw == stamp.date_raw &&
        query->result.case_kind ==
            kZhongguoAiOwnedCaseSnapshotV1CaseKind &&
        query->result.request_nonce == query->request.request_nonce &&
        query->result.subject_character_id ==
            query->request.subject_character_id &&
        query->result.requested_owner_character_id ==
            query->request.owner_character_id) {
      query->completion =
          ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1::completed;
      return true;
    }
    query->completion =
        ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1::
            infrastructure_rejected;
    return false;
  } catch (...) {
    query->completion =
        ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1::
            infrastructure_rejected;
    return false;
  }
}

std::string_view ZhongguoAiOwnedCaseSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main ZhongGuo AI-owned case executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main ZhongGuo AI-owned case boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main ZhongGuo AI-owned case query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main ZhongGuo AI-owned case query timed out";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main ZhongGuo AI-owned case executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main ZhongGuo AI-owned case ticket mismatch";
    case MainThreadQueryWaitResultV1::completed: break;
    }
  }
  if (completion ==
      ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main ZhongGuo AI-owned case result is inconsistent"
               : "ZhongGuo AI-owned case completion snapshot changed";
  }
  if (completion ==
      ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1::frame_changed) {
    return "ZhongGuo AI-owned case application-main frame changed";
  }
  return "application-main ZhongGuo AI-owned case executor was rejected";
}

} // namespace xar::ck3_11906
