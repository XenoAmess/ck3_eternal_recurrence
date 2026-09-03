#include "xar_bridge/zhongguo_projects_metrics_postcondition_v1_mailbox.hpp"

#include <windows.h>

#include <algorithm>
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
  ZhongguoProjectsMetricsMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const ZhongguoProjectsMetricsMailboxContextV1 &query,
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
         mailbox.executor ==
             &ExecuteZhongguoProjectsMetricsMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<ZhongguoProjectsMetricsMailboxContextV1 *>(
                 &query);
}

bool ProxyIsMainThread(void *opaque) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr && proxy->stamp != nullptr &&
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
  output.snapshot_revision = proxy->query->request.expected_snapshot_revision;
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
  return proxy != nullptr && proxy->query != nullptr && proxy->stamp != nullptr &&
         proxy->query->access.read_memory != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.read_memory(proxy->query->access.context, address,
                                          output, size);
}

bool ProxyValidateCharacter(void *opaque,
                            std::int32_t character_id) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr && proxy->stamp != nullptr &&
         proxy->query->access.validate_character != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.validate_character(proxy->query->access.context,
                                                 character_id);
}

bool ProxyReadAllowlistedVariable(
    void *opaque, std::int32_t character_id, std::string_view key,
    ZhongguoRawVariableV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr && proxy->stamp != nullptr &&
         proxy->query->access.read_allowlisted_variable != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.read_allowlisted_variable(
             proxy->query->access.context, character_id, key, output);
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
        static_cast<unsigned char>(json[cursor]) < 0x20U) return false;
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
  const auto begin = cursor;
  while (cursor < json.size() && json[cursor] != ',' && json[cursor] != '}')
    ++cursor;
  auto end = cursor;
  while (end > begin && IsWhitespace(json[end - 1])) --end;
  return end > begin;
}

bool HasExactControlFields(std::string_view json) noexcept {
  constexpr std::array<std::string_view, 7> fields{
      "type", "protocol_version", "request_id", "step",
      "expected_revision", "owner_character_id", "request_nonce"};
  std::uint32_t seen = 0;
  std::size_t cursor = 0;
  SkipWhitespace(json, cursor);
  if (cursor >= json.size() || json[cursor++] != '{') return false;
  SkipWhitespace(json, cursor);
  while (cursor < json.size() && json[cursor] != '}') {
    std::string_view key;
    if (!ParseJsonStringSpan(json, cursor, key)) return false;
    const auto match = std::find(fields.begin(), fields.end(), key);
    if (match == fields.end()) return false;
    const auto bit = 1U << static_cast<std::uint32_t>(match - fields.begin());
    if ((seen & bit) != 0) return false;
    seen |= bit;
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
  if (cursor >= json.size() || json[cursor++] != '}') return false;
  SkipWhitespace(json, cursor);
  return cursor == json.size() && seen == ((1U << fields.size()) - 1U);
}

bool FieldStart(std::string_view json, std::string_view key,
                std::size_t &value_at) noexcept {
  std::string needle;
  try {
    needle = "\"" + std::string(key) + "\"";
  } catch (...) {
    return false;
  }
  const auto at = json.find(needle);
  if (at == std::string_view::npos ||
      json.find(needle, at + needle.size()) != std::string_view::npos)
    return false;
  auto cursor = at + needle.size();
  SkipWhitespace(json, cursor);
  if (cursor >= json.size() || json[cursor++] != ':') return false;
  SkipWhitespace(json, cursor);
  value_at = cursor;
  return cursor < json.size();
}

bool ValidDelimiter(std::string_view json, std::size_t cursor) noexcept {
  SkipWhitespace(json, cursor);
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
      !ValidDelimiter(json, end)) return false;
  const auto parsed =
      std::from_chars(json.data() + begin, json.data() + end, output);
  return parsed.ec == std::errc{} && parsed.ptr == json.data() + end;
}

bool ParseStringField(std::string_view json, std::string_view key,
                      std::string &output) noexcept {
  output.clear();
  std::size_t cursor = 0;
  if (!FieldStart(json, key, cursor) || json[cursor] != '"') return false;
  std::string_view value;
  if (!ParseJsonStringSpan(json, cursor, value) ||
      !ValidDelimiter(json, cursor)) return false;
  try {
    output.assign(value);
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
        (index == 0 && !alpha && !digit)) return false;
  }
  return true;
}

} // namespace

bool ParseZhongguoProjectsMetricsPostconditionV1Step(
    std::string_view step) noexcept {
  return step == kZhongguoProjectsMetricsPostconditionV1Step;
}

bool ParseZhongguoProjectsMetricsPostconditionRequestV1(
    std::string_view json, ZhongguoProjectsMetricsPostconditionRequestV1 &output,
    std::int32_t &requested_owner_character_id) noexcept {
  output = {};
  requested_owner_character_id = -1;
  std::uint64_t protocol = 0;
  std::uint64_t revision = 0;
  std::uint64_t owner = 0;
  std::string type;
  std::string request_id;
  std::string step;
  std::string nonce;
  if (!HasExactControlFields(json) || !ParseStringField(json, "type", type) ||
      !ParseUnsignedField(json, "protocol_version", protocol) ||
      !ParseStringField(json, "request_id", request_id) ||
      !ParseStringField(json, "step", step) ||
      !ParseUnsignedField(json, "expected_revision", revision) ||
      !ParseUnsignedField(json, "owner_character_id", owner) ||
      !ParseStringField(json, "request_nonce", nonce) ||
      type != "execute_step" || protocol != 1 || request_id.empty() ||
      request_id.size() > 256 ||
      step != kZhongguoProjectsMetricsPostconditionV1Step ||
      revision == 0 || owner == 0 ||
      owner > static_cast<std::uint64_t>(
                  (std::numeric_limits<std::int32_t>::max)()) ||
      !ValidNonce(nonce)) {
    return false;
  }
  output.expected_snapshot_revision = revision;
  output.owner_character_id = static_cast<std::int32_t>(owner);
  output.request_nonce = std::move(nonce);
  requested_owner_character_id = static_cast<std::int32_t>(owner);
  return true;
}

bool ExecuteZhongguoProjectsMetricsMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query =
      static_cast<ZhongguoProjectsMetricsMailboxContextV1 *>(
          opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          ZhongguoProjectsMetricsMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr)
      query->completion =
          ZhongguoProjectsMetricsMailboxCompletionV1::
              infrastructure_rejected;
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    MailboxAccessProxyV1 proxy{query, &stamp};
    ZhongguoProjectsMetricsAccessV1 access{};
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
    query->read_result = ReadZhongguoProjectsMetricsPostconditionV1(
        query->environment, access, query->request, query->result);
    const bool typed_available =
        query->read_result ==
            game::ReadZhongguoProjectsMetricsPostconditionResultV1::available &&
        query->result.status ==
            game::ZhongguoProjectsMetricsPostconditionStatusV1::available;
    const bool typed_unavailable =
        query->read_result ==
            game::ReadZhongguoProjectsMetricsPostconditionResultV1::unavailable &&
        query->result.status ==
            game::ZhongguoProjectsMetricsPostconditionStatusV1::unavailable &&
        !query->result.unavailable_reason.empty() &&
        !query->result.readiness.ready;
    if ((typed_available || typed_unavailable) &&
        query->result.snapshot_revision ==
            query->request.expected_snapshot_revision &&
        query->result.date_raw == stamp.date_raw &&
        query->result.request_nonce == query->request.request_nonce &&
        query->result.requested_owner_character_id ==
            query->requested_owner_character_id &&
        query->result.player_character_id ==
            query->expected_snapshot.played_character_id) {
      query->completion =
          ZhongguoProjectsMetricsMailboxCompletionV1::completed;
      return true;
    }
    query->completion =
        ZhongguoProjectsMetricsMailboxCompletionV1::
            infrastructure_rejected;
    return false;
  } catch (...) {
    query->completion =
        ZhongguoProjectsMetricsMailboxCompletionV1::
            infrastructure_rejected;
    return false;
  }
}

std::string_view ZhongguoProjectsMetricsFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoProjectsMetricsMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main projects/metrics executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main projects/metrics boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main projects/metrics query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main projects/metrics query timed out";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main projects/metrics executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main projects/metrics ticket mismatch";
    case MainThreadQueryWaitResultV1::completed: break;
    }
  }
  if (completion ==
      ZhongguoProjectsMetricsMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main projects/metrics result is inconsistent"
               : "projects/metrics completion snapshot changed";
  }
  if (completion ==
      ZhongguoProjectsMetricsMailboxCompletionV1::frame_changed)
    return "projects/metrics application-main frame changed";
  return "application-main projects/metrics executor was rejected";
}

} // namespace xar::ck3_11906
