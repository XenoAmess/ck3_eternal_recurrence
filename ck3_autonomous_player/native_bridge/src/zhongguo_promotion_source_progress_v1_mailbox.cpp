#include "xar_bridge/zhongguo_promotion_source_progress_v1_mailbox.hpp"

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

bool IsWhitespace(char value) noexcept {
  return value == ' ' || value == '\t' || value == '\r' || value == '\n';
}

void SkipWhitespace(std::string_view json, std::size_t &cursor) noexcept {
  while (cursor < json.size() && IsWhitespace(json[cursor])) ++cursor;
}

bool ParseJsonString(std::string_view json, std::size_t &cursor,
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
    return ParseJsonString(json, cursor, ignored);
  }
  const auto begin = cursor;
  while (cursor < json.size() && json[cursor] != ',' && json[cursor] != '}')
    ++cursor;
  auto end = cursor;
  while (end > begin && IsWhitespace(json[end - 1])) --end;
  return end > begin;
}

template <std::size_t Size>
bool HasExactFields(std::string_view json,
                    const std::array<std::string_view, Size> &fields) noexcept {
  static_assert(Size < 32);
  std::uint32_t seen = 0;
  std::size_t cursor = 0;
  SkipWhitespace(json, cursor);
  if (cursor >= json.size() || json[cursor++] != '{') return false;
  SkipWhitespace(json, cursor);
  while (cursor < json.size() && json[cursor] != '}') {
    std::string_view key;
    if (!ParseJsonString(json, cursor, key)) return false;
    std::size_t index = 0;
    while (index < fields.size() && fields[index] != key) ++index;
    if (index == fields.size() || (seen & (1U << index)) != 0) return false;
    seen |= 1U << index;
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
  return cursor == json.size() && seen == ((1U << Size) - 1U);
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
    if (!ParseJsonString(json, cursor, observed)) return false;
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

bool ParseUnsigned(std::string_view value, std::uint64_t &output) noexcept {
  if (value.empty() || value.front() == '+' || value.front() == '-') return false;
  const auto parsed =
      std::from_chars(value.data(), value.data() + value.size(), output);
  return parsed.ec == std::errc{} && parsed.ptr == value.data() + value.size();
}

bool ParsePositiveCharacter(std::string_view value,
                            std::int32_t &output) noexcept {
  std::uint64_t parsed = 0;
  if (!ParseUnsigned(value, parsed) || parsed == 0 ||
      parsed > static_cast<std::uint64_t>(
                   std::numeric_limits<std::int32_t>::max())) return false;
  output = static_cast<std::int32_t>(parsed);
  return true;
}

bool ParseString(std::string_view value, std::string &output) noexcept {
  std::size_t cursor = 0;
  std::string_view parsed;
  if (!ParseJsonString(value, cursor, parsed) || cursor != value.size())
    return false;
  output.assign(parsed);
  return true;
}

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t index = 0; index < value.size(); ++index) {
    const char current = value[index];
    const bool alpha = (current >= 'a' && current <= 'z') ||
                       (current >= 'A' && current <= 'Z');
    const bool digit = current >= '0' && current <= '9';
    const bool punctuation = current == '.' || current == '_' ||
                             current == ':' || current == '-';
    if ((!alpha && !digit && !punctuation) ||
        (index == 0 && !alpha && !digit)) return false;
  }
  return true;
}

template <typename Context>
bool IsExactSlot(const Context &context,
                 const MainThreadExecutionStampV1 &stamp,
                 MainThreadQueryExecutorV1 executor) noexcept {
  if (context.mailbox == nullptr || context.ticket.sequence == 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) return false;
  const auto &mailbox = *context.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             context.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor == executor &&
         mailbox.executor_context == const_cast<Context *>(&context);
}

struct QueryProxy {
  ZhongguoPromotionSourceProgressMailboxContextV1 *context = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

struct ActionProxy {
  ZhongguoReviewNowActionMailboxContextV1 *context = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool QueryIsMain(void *opaque) noexcept {
  const auto *proxy = static_cast<QueryProxy *>(opaque);
  return proxy != nullptr && proxy->context != nullptr && proxy->stamp != nullptr &&
         IsExactSlot(*proxy->context, *proxy->stamp,
                     &ExecuteZhongguoPromotionSourceMailboxV1);
}

bool ActionIsMain(void *opaque) noexcept {
  const auto *proxy = static_cast<ActionProxy *>(opaque);
  return proxy != nullptr && proxy->context != nullptr && proxy->stamp != nullptr &&
         IsExactSlot(*proxy->context, *proxy->stamp,
                     &ExecuteZhongguoPromotionSourceMailboxV1);
}

template <typename Proxy, typename Context>
bool CaptureFrame(Proxy *proxy, Context *context,
                  const MainThreadExecutionStampV1 *stamp,
                  std::uint64_t revision,
                  game::ZhongguoCaseFrameV1 &output) noexcept {
  if (proxy == nullptr || context == nullptr || stamp == nullptr) return false;
  game::Snapshot snapshot{};
  if (!ReadSnapshot(context->bindings, snapshot) ||
      snapshot != context->expected_snapshot || !snapshot.paused ||
      snapshot.date_raw != stamp->date_raw) return false;
  output.snapshot_revision = revision;
  output.date_raw = snapshot.date_raw;
  output.paused = snapshot.paused;
  output.map_ready = snapshot.map_ready;
  output.has_played_character = snapshot.has_played_character;
  output.played_character_alive = snapshot.played_character_alive;
  output.played_character_id = snapshot.played_character_id;
  return true;
}

bool QueryCapture(void *opaque, game::ZhongguoCaseFrameV1 &output) noexcept {
  auto *proxy = static_cast<QueryProxy *>(opaque);
  if (!QueryIsMain(opaque)) return false;
  return CaptureFrame(proxy, proxy->context, proxy->stamp,
                      proxy->context->request.expected_snapshot_revision,
                      output);
}

bool ActionCapture(void *opaque, game::ZhongguoCaseFrameV1 &output) noexcept {
  auto *proxy = static_cast<ActionProxy *>(opaque);
  if (!ActionIsMain(opaque)) return false;
  return CaptureFrame(proxy, proxy->context, proxy->stamp,
                      proxy->context->request.expected_native_revision,
                      output);
}

template <typename Proxy>
bool ForwardReadMemory(Proxy *proxy, bool main_thread, const void *address,
                       void *output, std::size_t size) noexcept {
  return main_thread && proxy->context->access.read_memory != nullptr &&
         proxy->context->access.read_memory(proxy->context->access.context,
                                            address, output, size);
}

bool QueryReadMemory(void *opaque, const void *address, void *output,
                     std::size_t size) noexcept {
  auto *proxy = static_cast<QueryProxy *>(opaque);
  return proxy != nullptr &&
         ForwardReadMemory(proxy, QueryIsMain(opaque), address, output, size);
}

bool ActionReadMemory(void *opaque, const void *address, void *output,
                      std::size_t size) noexcept {
  auto *proxy = static_cast<ActionProxy *>(opaque);
  return proxy != nullptr &&
         ForwardReadMemory(proxy, ActionIsMain(opaque), address, output, size);
}

template <typename Proxy>
bool ForwardValidate(Proxy *proxy, bool main_thread,
                     std::int32_t character) noexcept {
  return main_thread && proxy->context->access.validate_character != nullptr &&
         proxy->context->access.validate_character(
             proxy->context->access.context, character);
}

bool QueryValidate(void *opaque, std::int32_t character) noexcept {
  auto *proxy = static_cast<QueryProxy *>(opaque);
  return proxy != nullptr &&
         ForwardValidate(proxy, QueryIsMain(opaque), character);
}

bool ActionValidate(void *opaque, std::int32_t character) noexcept {
  auto *proxy = static_cast<ActionProxy *>(opaque);
  return proxy != nullptr &&
         ForwardValidate(proxy, ActionIsMain(opaque), character);
}

template <typename Proxy>
void *ForwardFind(Proxy *proxy, bool main_thread, std::string_view name) noexcept {
  if (!main_thread || proxy->context->access.find_fixed_widget == nullptr)
    return nullptr;
  return proxy->context->access.find_fixed_widget(
      proxy->context->access.context, name);
}

bool QueryResolve(void *opaque, void *&gui_context, void *&gui_owner) noexcept;

void *QueryFind(void *opaque, std::string_view name) noexcept {
  auto *proxy = static_cast<QueryProxy *>(opaque);
  return proxy == nullptr ? nullptr : ForwardFind(proxy, QueryIsMain(opaque), name);
}

void *ActionFind(void *opaque, std::string_view name) noexcept {
  auto *proxy = static_cast<ActionProxy *>(opaque);
  return proxy == nullptr ? nullptr : ForwardFind(proxy, ActionIsMain(opaque), name);
}

template <typename Proxy>
bool ForwardResolve(Proxy *proxy, bool main_thread, void *&gui_context,
                    void *&gui_owner) noexcept {
  gui_context = nullptr;
  gui_owner = nullptr;
  return main_thread && proxy->context->access.resolve_fixture_gui != nullptr &&
         proxy->context->access.resolve_fixture_gui(
             proxy->context->access.context, gui_context, gui_owner);
}

bool QueryResolve(void *opaque, void *&gui_context, void *&gui_owner) noexcept {
  auto *proxy = static_cast<QueryProxy *>(opaque);
  return proxy != nullptr && ForwardResolve(proxy, QueryIsMain(opaque),
                                            gui_context, gui_owner);
}

bool ActionResolve(void *opaque, void *&gui_context, void *&gui_owner) noexcept {
  auto *proxy = static_cast<ActionProxy *>(opaque);
  return proxy != nullptr && ForwardResolve(proxy, ActionIsMain(opaque),
                                             gui_context, gui_owner);
}

bool ActionDispatch(void *opaque, std::string_view identity,
                    std::string_view runtime_name,
                    std::string_view instance_pointer,
                    std::string_view vtable_pointer,
                    bool &native_handled) noexcept {
  native_handled = false;
  auto *proxy = static_cast<ActionProxy *>(opaque);
  return proxy != nullptr && ActionIsMain(opaque) &&
         proxy->context->action_access.dispatch != nullptr &&
         proxy->context->action_access.dispatch(
             proxy->context->action_access.context, identity, runtime_name,
             instance_pointer, vtable_pointer, native_handled);
}

template <typename Proxy>
ZhongguoPromotionSourceProgressAccessV1 ProxiedAccess(Proxy &proxy,
    bool (*is_main)(void *) noexcept,
    bool (*capture)(void *, game::ZhongguoCaseFrameV1 &) noexcept,
    bool (*read)(void *, const void *, void *, std::size_t) noexcept,
    bool (*validate)(void *, std::int32_t) noexcept,
    void *(*find)(void *, std::string_view) noexcept,
    bool (*resolve)(void *, void *&, void *&) noexcept) {
  ZhongguoPromotionSourceProgressAccessV1 access{};
  access.context = &proxy;
  access.is_main_thread = is_main;
  access.capture_frame = capture;
  access.read_memory = proxy.context->access.read_memory == nullptr ? nullptr : read;
  access.validate_character =
      proxy.context->access.validate_character == nullptr ? nullptr : validate;
  access.find_fixed_widget =
      proxy.context->access.find_fixed_widget == nullptr ? nullptr : find;
  access.resolve_fixture_gui =
      proxy.context->access.resolve_fixture_gui == nullptr ? nullptr : resolve;
  return access;
}

} // namespace

bool ParseZhongguoPromotionSourceProgressV1Step(
    std::string_view step) noexcept {
  return step == kZhongguoPromotionSourceProgressV1Step;
}

bool ParseZhongguoPromotionSourceProgressRequestV1(
    std::string_view json, ZhongguoPromotionSourceProgressRequestV1 &output,
    std::int32_t &requested_owner_character_id) noexcept {
  constexpr std::array<std::string_view, 7> fields{
      "type", "protocol_version", "request_id", "step",
      "expected_revision", "owner_character_id", "request_nonce"};
  output = {};
  requested_owner_character_id = -1;
  std::string_view raw;
  std::uint64_t protocol = 0;
  std::string type;
  std::string step;
  if (!HasExactFields(json, fields) ||
      !FindRawField(json, "type", raw) || !ParseString(raw, type) ||
      type != "execute_step" ||
      !FindRawField(json, "protocol_version", raw) ||
      !ParseUnsigned(raw, protocol) || protocol != 1 ||
      !FindRawField(json, "step", raw) || !ParseString(raw, step) ||
      step != kZhongguoPromotionSourceProgressV1Step ||
      !FindRawField(json, "expected_revision", raw) ||
      !ParseUnsigned(raw, output.expected_snapshot_revision) ||
      output.expected_snapshot_revision == 0 ||
      !FindRawField(json, "owner_character_id", raw) ||
      !ParsePositiveCharacter(raw, requested_owner_character_id) ||
      !FindRawField(json, "request_nonce", raw) ||
      !ParseString(raw, output.request_nonce) ||
      !ValidNonce(output.request_nonce)) {
    output = {};
    requested_owner_character_id = -1;
    return false;
  }
  return true;
}

bool ParseZhongguoReviewNowActionV1Step(std::string_view step) noexcept {
  return step == kZhongguoReviewNowActionV1Step;
}

bool ParseZhongguoReviewNowActionRequestV1(
    std::string_view json, game::ZhongguoReviewNowActionRequestV1 &output) noexcept {
  constexpr std::array<std::string_view, 10> fields{
      "type", "protocol_version", "request_id", "step", "expected_revision",
      "request_nonce", "expected_public_revision", "expected_native_revision",
      "expected_connection_generation", "expected_player_character_id"};
  output = {};
  std::string_view raw;
  std::uint64_t protocol = 0;
  std::uint64_t wire_revision = 0;
  std::string type;
  std::string step;
  if (!HasExactFields(json, fields) ||
      !FindRawField(json, "type", raw) || !ParseString(raw, type) ||
      type != "execute_step" ||
      !FindRawField(json, "protocol_version", raw) ||
      !ParseUnsigned(raw, protocol) || protocol != 1 ||
      !FindRawField(json, "step", raw) || !ParseString(raw, step) ||
      step != kZhongguoReviewNowActionV1Step ||
      !FindRawField(json, "expected_revision", raw) ||
      !ParseUnsigned(raw, wire_revision) || wire_revision == 0 ||
      !FindRawField(json, "expected_public_revision", raw) ||
      !ParseUnsigned(raw, output.expected_revision) ||
      output.expected_revision == 0 ||
      !FindRawField(json, "expected_native_revision", raw) ||
      !ParseUnsigned(raw, output.expected_native_revision) ||
      output.expected_native_revision != wire_revision ||
      !FindRawField(json, "expected_connection_generation", raw) ||
      !ParseUnsigned(raw, output.expected_connection_generation) ||
      output.expected_connection_generation == 0 ||
      !FindRawField(json, "expected_player_character_id", raw) ||
      !ParsePositiveCharacter(raw, output.expected_player_character_id) ||
      !FindRawField(json, "request_nonce", raw) ||
      !ParseString(raw, output.request_nonce) ||
      !ValidNonce(output.request_nonce)) {
    output = {};
    return false;
  }
  return true;
}

bool ExecuteZhongguoPromotionSourceProgressMailboxV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *context =
      static_cast<ZhongguoPromotionSourceProgressMailboxContextV1 *>(opaque_context);
  if (context == nullptr ||
      !IsExactSlot(*context, stamp,
                   &ExecuteZhongguoPromotionSourceMailboxV1)) {
    if (context != nullptr)
      context->completion = ZhongguoPromotionSourceMailboxCompletionV1::
          infrastructure_rejected;
    return false;
  }
  try {
    ++context->executor_invocations;
    context->execution_stamp = stamp;
    QueryProxy proxy{context, &stamp};
    const auto access = ProxiedAccess(
        proxy, &QueryIsMain, &QueryCapture, &QueryReadMemory, &QueryValidate,
        &QueryFind, &QueryResolve);
    context->read_result = ReadZhongguoPromotionSourceProgressV1(
        context->environment, access, context->request, context->result);
    if (context->result.snapshot_revision !=
            context->request.expected_snapshot_revision ||
        context->result.date_raw != stamp.date_raw ||
        context->result.player_character_id !=
            context->requested_owner_character_id) {
      context->completion =
          ZhongguoPromotionSourceMailboxCompletionV1::frame_changed;
      return true;
    }
    context->completion = context->read_result ==
                                  game::ReadZhongguoPromotionSourceProgressResultV1::available
                              ? ZhongguoPromotionSourceMailboxCompletionV1::completed_available
                              : ZhongguoPromotionSourceMailboxCompletionV1::completed_unavailable;
    return true;
  } catch (...) {
    context->completion =
        ZhongguoPromotionSourceMailboxCompletionV1::infrastructure_rejected;
    return false;
  }
}

bool ExecuteZhongguoReviewNowActionMailboxV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *context =
      static_cast<ZhongguoReviewNowActionMailboxContextV1 *>(opaque_context);
  if (context == nullptr ||
      !IsExactSlot(*context, stamp, &ExecuteZhongguoPromotionSourceMailboxV1)) {
    if (context != nullptr)
      context->completion = ZhongguoPromotionSourceMailboxCompletionV1::
          infrastructure_rejected;
    return false;
  }
  try {
    ++context->executor_invocations;
    context->execution_stamp = stamp;
    ActionProxy proxy{context, &stamp};
    const auto state_access = ProxiedAccess(
        proxy, &ActionIsMain, &ActionCapture, &ActionReadMemory,
        &ActionValidate, &ActionFind, &ActionResolve);
    ZhongguoPromotionSourceProgressRequestV1 source_request{};
    source_request.expected_snapshot_revision =
        context->request.expected_native_revision;
    source_request.request_nonce = context->request.request_nonce;
    context->read_result = ReadZhongguoPromotionSourceProgressV1(
        context->environment, state_access, source_request, context->source);
    if (context->read_result !=
            game::ReadZhongguoPromotionSourceProgressResultV1::available ||
        context->source.status !=
            game::ZhongguoPromotionSourceProgressStatusV1::available ||
        context->source.date_raw != stamp.date_raw ||
        context->source.player_character_id !=
            context->request.expected_player_character_id) {
      context->result = {};
      context->result.request_nonce = context->request.request_nonce;
      context->result.rejection_reason = "source_progress_unavailable";
      context->completion =
          ZhongguoPromotionSourceMailboxCompletionV1::completed_unavailable;
      return true;
    }
    ZhongguoReviewNowActionAccessV1 action_access{};
    action_access.context = &proxy;
    action_access.dispatch = context->action_access.dispatch == nullptr
                                 ? nullptr
                                 : &ActionDispatch;
    if (ExecuteZhongguoReviewNowActionV1(context->request, context->source,
                                         action_access, context->result)) {
      context->completion =
          ZhongguoPromotionSourceMailboxCompletionV1::completed_available;
      return true;
    }
    context->completion =
        ZhongguoPromotionSourceMailboxCompletionV1::completed_unavailable;
    return true;
  } catch (...) {
    context->completion =
        ZhongguoPromotionSourceMailboxCompletionV1::infrastructure_rejected;
    return false;
  }
}

bool ExecuteZhongguoPromotionSourceMailboxV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept {
  if (opaque_context == nullptr) return false;
  const auto operation = *static_cast<
      const ZhongguoPromotionSourceMailboxOperationV1 *>(opaque_context);
  if (operation == ZhongguoPromotionSourceMailboxOperationV1::query_progress) {
    return ExecuteZhongguoPromotionSourceProgressMailboxV1(opaque_context,
                                                            stamp);
  }
  if (operation ==
      ZhongguoPromotionSourceMailboxOperationV1::activate_review_now) {
    return ExecuteZhongguoReviewNowActionMailboxV1(opaque_context, stamp);
  }
  return false;
}

std::string_view ZhongguoPromotionSourceFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoPromotionSourceMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (!completion_snapshot_stable)
    return "ZhongGuo promotion source operation crossed its paused revision";
  if (wait == MainThreadQueryWaitResultV1::timeout_cancelled_before_execution)
    return "application-main ZhongGuo promotion source operation timed out";
  if (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
    return "application-main ZhongGuo promotion source operation is still running";
  if (wait != MainThreadQueryWaitResultV1::completed)
    return "application-main ZhongGuo promotion source operation failed";
  if (completion == ZhongguoPromotionSourceMailboxCompletionV1::frame_changed)
    return "ZhongGuo promotion source frame changed during operation";
  return "application-main ZhongGuo promotion source executor rejected request";
}

} // namespace xar::ck3_11906
