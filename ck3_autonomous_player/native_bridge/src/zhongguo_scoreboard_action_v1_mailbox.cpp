#include "xar_bridge/zhongguo_scoreboard_action_v1_mailbox.hpp"

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
  ZhongguoScoreboardActionMailboxContextV1 *action = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const ZhongguoScoreboardActionMailboxContextV1 &action,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (action.mailbox == nullptr || action.ticket.sequence == 0 ||
      action.request.expected_native_revision == 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *action.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             action.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor == &ExecuteZhongguoScoreboardActionMailboxV1 &&
         mailbox.executor_context == const_cast<
             ZhongguoScoreboardActionMailboxContextV1 *>(&action);
}

bool ProxyIsMainThread(void *opaque) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->action != nullptr &&
         proxy->stamp != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->action, *proxy->stamp);
}

bool ProxyCaptureFrame(void *opaque,
                       game::ZhongguoCaseFrameV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->action == nullptr || proxy->stamp == nullptr ||
      !IsExecutingExactMailboxSlot(*proxy->action, *proxy->stamp)) {
    return false;
  }
  game::Snapshot snapshot{};
  if (!ReadSnapshot(proxy->action->bindings, snapshot) ||
      snapshot != proxy->action->expected_snapshot || !snapshot.paused ||
      snapshot.date_raw != proxy->stamp->date_raw) {
    return false;
  }
  output.snapshot_revision =
      proxy->action->request.expected_native_revision;
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
  return proxy != nullptr && proxy->action != nullptr &&
         proxy->stamp != nullptr &&
         proxy->action->state_access.read_memory != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->action, *proxy->stamp) &&
         proxy->action->state_access.read_memory(
             proxy->action->state_access.context, address, output, size);
}

bool ProxyValidateCharacter(void *opaque,
                            std::int32_t character_id) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->action != nullptr &&
         proxy->stamp != nullptr &&
         proxy->action->state_access.validate_character != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->action, *proxy->stamp) &&
         proxy->action->state_access.validate_character(
             proxy->action->state_access.context, character_id);
}

bool ProxyReadAllowlistedVariable(
    void *opaque, std::int32_t character_id, std::string_view key,
    ZhongguoRawVariableV1 &output) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->action != nullptr &&
         proxy->stamp != nullptr &&
         proxy->action->state_access.read_allowlisted_variable != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->action, *proxy->stamp) &&
         proxy->action->state_access.read_allowlisted_variable(
             proxy->action->state_access.context, character_id, key, output);
}

void *ProxyFindFixedWidget(void *opaque, std::string_view name) noexcept {
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->action == nullptr || proxy->stamp == nullptr ||
      proxy->action->state_access.find_fixed_widget == nullptr ||
      !IsExecutingExactMailboxSlot(*proxy->action, *proxy->stamp)) {
    return nullptr;
  }
  return proxy->action->state_access.find_fixed_widget(
      proxy->action->state_access.context, name);
}

bool ProxyResolveFixtureGui(void *opaque, void *&gui_context,
                            void *&gui_owner) noexcept {
  gui_context = nullptr;
  gui_owner = nullptr;
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->action != nullptr &&
         proxy->stamp != nullptr &&
         proxy->action->state_access.resolve_fixture_gui != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->action, *proxy->stamp) &&
         proxy->action->state_access.resolve_fixture_gui(
             proxy->action->state_access.context, gui_context, gui_owner);
}

bool ProxyDispatch(void *opaque, game::ZhongguoScoreboardActionV1 action,
                   std::string_view stable_identity,
                   std::string_view runtime_name,
                   std::string_view instance_pointer,
                   std::string_view vtable_pointer,
                   bool &native_handled) noexcept {
  native_handled = false;
  const auto *proxy = static_cast<const MailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->action != nullptr &&
         proxy->stamp != nullptr &&
         proxy->action->action_access.dispatch != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->action, *proxy->stamp) &&
         proxy->action->action_access.dispatch(
             proxy->action->action_access.context, action, stable_identity,
             runtime_name, instance_pointer, vtable_pointer, native_handled);
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

constexpr std::array<std::string_view, 18> kControlFields{
    "type",
    "protocol_version",
    "request_id",
    "step",
    "expected_revision",
    "request_nonce",
    "action",
    "expected_public_revision",
    "expected_native_revision",
    "expected_connection_generation",
    "expected_player_character_id",
    "expected_provider_session_id",
    "expected_observation_sequence",
    "expected_observed_state_revision",
    "expected_tree_fingerprint_v1",
    "expected_semantic_fingerprint_v1",
    "expected_window_instance_pointer",
    "expected_target_instance_pointer",
};

// The vtable pointer is kept separate only because a uint32 bit mask is used
// below and the explicit array makes unknown/duplicate field rejection easy to
// audit.
constexpr std::string_view kVtableField =
    "expected_target_vtable_pointer";

bool HasExactControlFields(std::string_view json) noexcept {
  std::uint32_t seen = 0;
  bool saw_vtable = false;
  std::size_t cursor = 0;
  SkipWhitespace(json, cursor);
  if (cursor >= json.size() || json[cursor++] != '{') return false;
  SkipWhitespace(json, cursor);
  while (cursor < json.size() && json[cursor] != '}') {
    std::string_view key;
    if (!ParseJsonStringSpan(json, cursor, key)) return false;
    std::size_t field_index = kControlFields.size();
    for (std::size_t index = 0; index < kControlFields.size(); ++index) {
      if (kControlFields[index] == key) {
        field_index = index;
        break;
      }
    }
    if (field_index == kControlFields.size()) {
      if (key != kVtableField || saw_vtable) return false;
      saw_vtable = true;
    } else {
      if ((seen & (1U << field_index)) != 0) return false;
      seen |= 1U << field_index;
    }
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
         (SkipWhitespace(json, cursor), cursor == json.size()) && saw_vtable &&
         seen == ((1U << kControlFields.size()) - 1U);
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
  return parsed.ec == std::errc{} &&
         parsed.ptr == value.data() + value.size();
}

bool ParsePositiveInt32(std::string_view value,
                        std::int32_t &output) noexcept {
  std::uint64_t parsed = 0;
  if (!ParseUint64(value, parsed) || parsed == 0 ||
      parsed > static_cast<std::uint64_t>(
                   std::numeric_limits<std::int32_t>::max())) {
    return false;
  }
  output = static_cast<std::int32_t>(parsed);
  return true;
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

bool ValidPointer(std::string_view value) noexcept {
  if (value.size() < 3 || !value.starts_with("0x")) return false;
  for (std::size_t index = 2; index < value.size(); ++index) {
    const char current = value[index];
    if (!((current >= '0' && current <= '9') ||
          (current >= 'A' && current <= 'F'))) {
      return false;
    }
  }
  return true;
}

bool ValidUpperHex(std::string_view value, std::size_t expected_size) noexcept {
  if (value.size() != expected_size) return false;
  for (const char current : value) {
    if (!((current >= '0' && current <= '9') ||
          (current >= 'A' && current <= 'F'))) {
      return false;
    }
  }
  return true;
}

bool ParseAction(std::string_view value,
                 game::ZhongguoScoreboardActionV1 &output) noexcept {
  if (value == "\"open\"") {
    output = game::ZhongguoScoreboardActionV1::open;
  } else if (value == "\"switch-managed\"") {
    output = game::ZhongguoScoreboardActionV1::switch_managed;
  } else if (value == "\"switch-received\"") {
    output = game::ZhongguoScoreboardActionV1::switch_received;
  } else if (value == "\"switch-system\"") {
    output = game::ZhongguoScoreboardActionV1::switch_system;
  } else if (value == "\"close\"") {
    output = game::ZhongguoScoreboardActionV1::close;
  } else if (value == "\"reopen\"") {
    output = game::ZhongguoScoreboardActionV1::reopen;
  } else {
    return false;
  }
  return true;
}

} // namespace

bool ParseZhongguoScoreboardActionV1Step(std::string_view step) noexcept {
  return step == kZhongguoScoreboardActionV1Step;
}

bool ParseZhongguoScoreboardActionRequestV1(
    std::string_view json,
    game::ZhongguoScoreboardActionRequestV1 &output) noexcept {
  output = {};
  if (!HasExactControlFields(json)) return false;
  std::string_view raw;
  std::uint64_t protocol_revision = 0;
  if (!FindRawField(json, "type", raw) || raw != "\"execute_step\"" ||
      !FindRawField(json, "protocol_version", raw) || raw != "1" ||
      !FindRawField(json, "step", raw) ||
      raw != "\"activate-zhongguo-scoreboard-v1\"" ||
      !FindRawField(json, "expected_revision", raw) ||
      !ParseUint64(raw, protocol_revision) || protocol_revision == 0 ||
      !FindRawField(json, "request_nonce", raw) ||
      !ParseString(raw, output.request_nonce) ||
      !ValidNonce(output.request_nonce) ||
      !FindRawField(json, "action", raw) || !ParseAction(raw, output.action) ||
      !FindRawField(json, "expected_public_revision", raw) ||
      !ParseUint64(raw, output.expected_revision) ||
      !FindRawField(json, "expected_native_revision", raw) ||
      !ParseUint64(raw, output.expected_native_revision) ||
      output.expected_native_revision == 0 ||
      output.expected_native_revision != protocol_revision ||
      !FindRawField(json, "expected_connection_generation", raw) ||
      !ParseUint64(raw, output.expected_connection_generation) ||
      output.expected_connection_generation == 0 ||
      !FindRawField(json, "expected_player_character_id", raw) ||
      !ParsePositiveInt32(raw, output.expected_player_character_id) ||
      !FindRawField(json, "expected_provider_session_id", raw) ||
      !ParseString(raw, output.expected_provider_session_id) ||
      !ValidUpperHex(output.expected_provider_session_id, 32) ||
      !FindRawField(json, "expected_observation_sequence", raw) ||
      !ParseUint64(raw, output.expected_observation_sequence) ||
      output.expected_observation_sequence == 0 ||
      !FindRawField(json, "expected_observed_state_revision", raw) ||
      !ParseUint64(raw, output.expected_observed_state_revision) ||
      output.expected_observed_state_revision == 0 ||
      !FindRawField(json, "expected_tree_fingerprint_v1", raw) ||
      !ParseString(raw, output.expected_tree_fingerprint_v1) ||
      !ValidUpperHex(output.expected_tree_fingerprint_v1, 64) ||
      !FindRawField(json, "expected_semantic_fingerprint_v1", raw) ||
      !ParseString(raw, output.expected_semantic_fingerprint_v1) ||
      !ValidUpperHex(output.expected_semantic_fingerprint_v1, 64) ||
      !FindRawField(json, "expected_window_instance_pointer", raw) ||
      !ParseString(raw, output.expected_window_instance_pointer) ||
      !ValidPointer(output.expected_window_instance_pointer) ||
      !FindRawField(json, "expected_target_instance_pointer", raw) ||
      !ParseString(raw, output.expected_target_instance_pointer) ||
      !ValidPointer(output.expected_target_instance_pointer) ||
      !FindRawField(json, "expected_target_vtable_pointer", raw) ||
      !ParseString(raw, output.expected_target_vtable_pointer) ||
      !ValidPointer(output.expected_target_vtable_pointer)) {
    output = {};
    return false;
  }
  return true;
}

bool ExecuteZhongguoScoreboardActionMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *action =
      static_cast<ZhongguoScoreboardActionMailboxContextV1 *>(opaque_context);
  if (action == nullptr || !IsExecutingExactMailboxSlot(*action, stamp)) {
    if (action != nullptr) {
      action->completion = ZhongguoScoreboardActionMailboxCompletionV1::
          infrastructure_rejected;
    }
    return false;
  }
  try {
    ++action->executor_invocations;
    action->execution_stamp = stamp;
    MailboxAccessProxyV1 proxy{action, &stamp};
    ZhongguoScoreboardAccessV1 state_access{};
    state_access.context = &proxy;
    state_access.capture_frame = &ProxyCaptureFrame;
    state_access.is_main_thread = &ProxyIsMainThread;
    state_access.read_memory = action->state_access.read_memory == nullptr
                                   ? nullptr
                                   : &ProxyReadMemory;
    state_access.validate_character =
        action->state_access.validate_character == nullptr
            ? nullptr
            : &ProxyValidateCharacter;
    state_access.read_allowlisted_variable =
        action->state_access.read_allowlisted_variable == nullptr
            ? nullptr
            : &ProxyReadAllowlistedVariable;
    state_access.find_fixed_widget =
        action->state_access.find_fixed_widget == nullptr
            ? nullptr
            : &ProxyFindFixedWidget;
    state_access.resolve_fixture_gui =
        action->state_access.resolve_fixture_gui == nullptr
            ? nullptr
            : &ProxyResolveFixtureGui;

    ZhongguoScoreboardStateRequestV1 state_request{};
    state_request.expected_snapshot_revision =
        action->request.expected_native_revision;
    state_request.request_nonce = action->request.request_nonce;
    state_request.provider_session_id =
        action->request.expected_provider_session_id;
    state_request.connection_generation =
        action->request.expected_connection_generation;
    state_request.provider_read_mode =
        ZhongguoScoreboardProviderReadModeV1::validate_without_advancing;
    state_request.provider_revision_tracker =
        action->provider_revision_tracker;
    action->state_read_result = ReadZhongguoScoreboardStateV1(
        action->environment, state_access, state_request, action->source);
    if (action->state_read_result !=
            game::ReadZhongguoScoreboardStateResultV1::available ||
        action->source.status !=
            game::ZhongguoScoreboardStateStatusV1::available ||
        action->source.snapshot_revision !=
            action->request.expected_native_revision ||
        action->source.date_raw != stamp.date_raw || !action->source.paused) {
      action->result = {};
      action->result.request_nonce = action->request.request_nonce;
      action->result.action = action->request.action;
      action->result.rejection_reason =
          "scoreboard_source_state_unavailable";
      action->completion =
          ZhongguoScoreboardActionMailboxCompletionV1::completed_unavailable;
      return true;
    }

    game::ZhongguoScoreboardActionBindingV1 binding{};
    binding.revision = action->request.expected_revision;
    binding.native_revision = action->request.expected_native_revision;
    binding.connection_generation =
        action->request.expected_connection_generation;
    binding.date_raw = action->source.date_raw;
    binding.player_character_id = action->source.player_character_id;
    binding.provider_session_id = action->source.provider_session_id;
    binding.observation_sequence = action->source.observation_sequence;
    binding.observed_state_revision =
        action->source.observed_state_revision;
    binding.tree_fingerprint_v1 = action->source.tree_fingerprint_v1;
    binding.semantic_fingerprint_v1 =
        action->source.semantic_fingerprint_v1;

    ZhongguoScoreboardActionAccessV1 action_access{};
    action_access.context = &proxy;
    action_access.dispatch = action->action_access.dispatch == nullptr
                                 ? nullptr
                                 : &ProxyDispatch;
    const auto result = ExecuteZhongguoScoreboardActionV1(
        action->request, binding, action->source, action_access,
        action->result);
    if (result == game::ZhongguoScoreboardActionResultV1::
                      acknowledged_verification_pending) {
      action->completion = ZhongguoScoreboardActionMailboxCompletionV1::
          completed_acknowledged;
      return true;
    }
    if (!action->result.rejection_reason.empty() &&
        !action->result.accepted) {
      action->completion =
          ZhongguoScoreboardActionMailboxCompletionV1::completed_unavailable;
      return true;
    }
    action->completion =
        ZhongguoScoreboardActionMailboxCompletionV1::infrastructure_rejected;
    return false;
  } catch (...) {
    action->completion =
        ZhongguoScoreboardActionMailboxCompletionV1::infrastructure_rejected;
    return false;
  }
}

std::string_view ZhongguoScoreboardActionFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoScoreboardActionMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (!completion_snapshot_stable) {
    return "ZhongGuo scoreboard action crossed its paused revision";
  }
  if (wait == MainThreadQueryWaitResultV1::timeout_cancelled_before_execution) {
    return "application-main ZhongGuo scoreboard action timed out";
  }
  if (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running) {
    return "application-main ZhongGuo scoreboard action is still running";
  }
  if (wait != MainThreadQueryWaitResultV1::completed) {
    return "application-main ZhongGuo scoreboard action failed";
  }
  if (completion == ZhongguoScoreboardActionMailboxCompletionV1::
                        frame_changed) {
    return "ZhongGuo scoreboard state changed during action admission";
  }
  return "application-main ZhongGuo scoreboard action executor rejected request";
}

} // namespace xar::ck3_11906
