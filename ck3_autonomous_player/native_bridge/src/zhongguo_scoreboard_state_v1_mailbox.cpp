#include "xar_bridge/zhongguo_scoreboard_state_v1_mailbox.hpp"

#include <windows.h>

#include <array>
#include <atomic>
#include <charconv>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

struct MailboxAccessProxyV1 {
  ZhongguoScoreboardStateMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const ZhongguoScoreboardStateMailboxContextV1 &query,
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
         mailbox.executor == &ExecuteZhongguoScoreboardStateMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<ZhongguoScoreboardStateMailboxContextV1 *>(&query);
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
         proxy->stamp != nullptr && proxy->query->access.read_memory != nullptr &&
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
         proxy->query->access.validate_character(proxy->query->access.context,
                                                 character_id);
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

void *ProxyFindFixedWidget(void *opaque, std::string_view name) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      proxy->query->access.find_fixed_widget == nullptr ||
      !IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp)) {
    return nullptr;
  }
  return proxy->query->access.find_fixed_widget(proxy->query->access.context,
                                                name);
}

bool IsWhitespace(char value) noexcept {
  return value == ' ' || value == '\t' || value == '\r' || value == '\n';
}

void SkipWhitespace(std::string_view json, std::size_t &cursor) noexcept {
  while (cursor < json.size() && IsWhitespace(json[cursor])) ++cursor;
}

bool ParseJsonStringSpan(std::string_view json, std::size_t &cursor,
                         std::string_view &value) noexcept {
  if (cursor >= json.size() || json[cursor] != '"') return false;
  const auto begin = ++cursor;
  while (cursor < json.size() && json[cursor] != '"') {
    if (json[cursor] == '\\' ||
        static_cast<unsigned char>(json[cursor]) < 0x20U) {
      return false;
    }
    ++cursor;
  }
  if (cursor >= json.size()) return false;
  value = json.substr(begin, cursor - begin);
  ++cursor;
  return true;
}

bool SkipJsonValue(std::string_view json, std::size_t &cursor) noexcept {
  SkipWhitespace(json, cursor);
  if (cursor >= json.size()) return false;
  if (json[cursor] == '"') {
    std::string_view ignored;
    return ParseJsonStringSpan(json, cursor, ignored);
  }
  if (json[cursor] == '{' || json[cursor] == '[') {
    const char opening = json[cursor++];
    const char closing = opening == '{' ? '}' : ']';
    std::uint32_t depth = 1;
    bool in_string = false;
    bool escaped = false;
    while (cursor < json.size() && depth != 0) {
      const char value = json[cursor++];
      if (in_string) {
        if (escaped) escaped = false;
        else if (value == '\\') escaped = true;
        else if (value == '"') in_string = false;
      } else if (value == '"') in_string = true;
      else if (value == opening) ++depth;
      else if (value == closing) --depth;
    }
    return depth == 0 && !in_string;
  }
  const auto begin = cursor;
  while (cursor < json.size() && json[cursor] != ',' &&
         json[cursor] != '}') ++cursor;
  auto end = cursor;
  while (end > begin && IsWhitespace(json[end - 1])) --end;
  return end > begin;
}

bool HasExactControlFields(std::string_view json) noexcept {
  constexpr std::array<std::string_view, 6> fields{
      "type", "protocol_version", "request_id", "step",
      "expected_revision", "request_nonce"};
  std::uint32_t seen = 0;
  std::size_t cursor = 0;
  SkipWhitespace(json, cursor);
  if (cursor >= json.size() || json[cursor++] != '{') return false;
  SkipWhitespace(json, cursor);
  while (cursor < json.size() && json[cursor] != '}') {
    std::string_view key;
    if (!ParseJsonStringSpan(json, cursor, key)) return false;
    std::size_t field_index = fields.size();
    for (std::size_t index = 0; index < fields.size(); ++index) {
      if (fields[index] == key) {
        field_index = index;
        break;
      }
    }
    if (field_index == fields.size() ||
        (seen & (1U << field_index)) != 0) return false;
    seen |= 1U << field_index;
    SkipWhitespace(json, cursor);
    if (cursor >= json.size() || json[cursor++] != ':') return false;
    if (!SkipJsonValue(json, cursor)) return false;
    SkipWhitespace(json, cursor);
    if (cursor < json.size() && json[cursor] == ',') {
      ++cursor;
      SkipWhitespace(json, cursor);
      continue;
    }
    break;
  }
  return cursor < json.size() && json[cursor++] == '}' &&
         (SkipWhitespace(json, cursor), cursor == json.size()) &&
         seen == ((1U << fields.size()) - 1U);
}

bool FindRawField(std::string_view json, std::string_view key,
                  std::string_view &value) noexcept {
  std::size_t cursor = 0;
  SkipWhitespace(json, cursor);
  if (cursor >= json.size() || json[cursor++] != '{') return false;
  while (cursor < json.size()) {
    SkipWhitespace(json, cursor);
    if (cursor < json.size() && json[cursor] == '}') return false;
    std::string_view observed;
    if (!ParseJsonStringSpan(json, cursor, observed)) return false;
    SkipWhitespace(json, cursor);
    if (cursor >= json.size() || json[cursor++] != ':') return false;
    SkipWhitespace(json, cursor);
    const auto begin = cursor;
    if (!SkipJsonValue(json, cursor)) return false;
    auto end = cursor;
    while (end > begin && IsWhitespace(json[end - 1])) --end;
    if (observed == key) {
      value = json.substr(begin, end - begin);
      return true;
    }
    SkipWhitespace(json, cursor);
    if (cursor < json.size() && json[cursor] == ',') ++cursor;
  }
  return false;
}

bool ParseUint64(std::string_view value, std::uint64_t &output) noexcept {
  if (value.empty() || value.front() == '-' || value.front() == '+') {
    return false;
  }
  const auto parsed =
      std::from_chars(value.data(), value.data() + value.size(), output);
  return parsed.ec == std::errc{} && parsed.ptr == value.data() + value.size();
}

bool ParseString(std::string_view value, std::string &output) noexcept {
  std::size_t cursor = 0;
  std::string_view parsed;
  if (!ParseJsonStringSpan(value, cursor, parsed) || cursor != value.size()) {
    return false;
  }
  output.assign(parsed);
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
        (index == 0 && !alpha && !digit)) return false;
  }
  return true;
}

} // namespace

bool ParseZhongguoScoreboardStateV1Step(std::string_view step) noexcept {
  return step == kZhongguoScoreboardStateV1Step;
}

bool ParseZhongguoScoreboardStateRequestV1(
    std::string_view json, ZhongguoScoreboardStateRequestV1 &output) noexcept {
  output = {};
  if (!HasExactControlFields(json)) return false;
  std::string_view raw;
  if (!FindRawField(json, "type", raw) || raw != "\"command\"" ||
      !FindRawField(json, "protocol_version", raw) || raw != "1" ||
      !FindRawField(json, "step", raw) ||
      raw != "\"query-zhongguo-scoreboard-state-v1\"" ||
      !FindRawField(json, "expected_revision", raw) ||
      !ParseUint64(raw, output.expected_snapshot_revision) ||
      output.expected_snapshot_revision == 0 ||
      !FindRawField(json, "request_nonce", raw) ||
      !ParseString(raw, output.request_nonce) ||
      !ValidNonce(output.request_nonce)) {
    output = {};
    return false;
  }
  return true;
}

bool ExecuteZhongguoScoreboardStateMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query =
      static_cast<ZhongguoScoreboardStateMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp)) {
    if (query != nullptr) {
      query->completion =
          ZhongguoScoreboardStateMailboxCompletionV1::infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    MailboxAccessProxyV1 proxy{query, &stamp};
    ZhongguoScoreboardAccessV1 access{};
    access.context = &proxy;
    access.capture_frame = &ProxyCaptureFrame;
    access.is_main_thread = &ProxyIsMainThread;
    access.read_memory =
        query->access.read_memory == nullptr ? nullptr : &ProxyReadMemory;
    access.validate_character = query->access.validate_character == nullptr
                                    ? nullptr
                                    : &ProxyValidateCharacter;
    access.read_allowlisted_variable =
        query->access.read_allowlisted_variable == nullptr
            ? nullptr
            : &ProxyReadAllowlistedVariable;
    access.find_fixed_widget = query->access.find_fixed_widget == nullptr
                                   ? nullptr
                                   : &ProxyFindFixedWidget;
    query->read_result = ReadZhongguoScoreboardStateV1(
        query->environment, access, query->request, query->result);
    const bool typed_available =
        query->read_result ==
            game::ReadZhongguoScoreboardStateResultV1::available &&
        query->result.status ==
            game::ZhongguoScoreboardStateStatusV1::available &&
        query->result.readiness.state_acl_query_ready &&
        !query->result.readiness.full_widget_gate_ready &&
        !query->result.readiness.production_live_ready;
    const bool typed_unavailable =
        query->read_result ==
            game::ReadZhongguoScoreboardStateResultV1::unavailable &&
        query->result.status ==
            game::ZhongguoScoreboardStateStatusV1::unavailable &&
        !query->result.unavailable_reason.empty() &&
        !query->result.readiness.state_acl_query_ready;
    if ((typed_available || typed_unavailable) &&
        query->result.snapshot_revision ==
            query->request.expected_snapshot_revision &&
        query->result.date_raw == stamp.date_raw && query->result.paused) {
      query->completion =
          ZhongguoScoreboardStateMailboxCompletionV1::completed;
      return true;
    }
    query->completion =
        ZhongguoScoreboardStateMailboxCompletionV1::frame_changed;
    return false;
  } catch (...) {
    query->completion =
        ZhongguoScoreboardStateMailboxCompletionV1::infrastructure_rejected;
    return false;
  }
}

std::string_view ZhongguoScoreboardStateFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoScoreboardStateMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (!completion_snapshot_stable) {
    return "ZhongGuo scoreboard state crossed its paused revision";
  }
  if (wait == MainThreadQueryWaitResultV1::timeout_cancelled_before_execution) {
    return "application-main ZhongGuo scoreboard state query timed out";
  }
  if (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running) {
    return "application-main ZhongGuo scoreboard state query is still running";
  }
  if (wait != MainThreadQueryWaitResultV1::completed) {
    return "application-main ZhongGuo scoreboard state query failed";
  }
  if (completion ==
      ZhongguoScoreboardStateMailboxCompletionV1::frame_changed) {
    return "ZhongGuo scoreboard state changed during query";
  }
  return "application-main ZhongGuo scoreboard state executor rejected query";
}

} // namespace xar::ck3_11906
