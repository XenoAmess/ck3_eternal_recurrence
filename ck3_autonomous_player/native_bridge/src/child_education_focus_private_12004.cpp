#include "xar_bridge/child_education_focus_private_12004.hpp"
#include "xar_bridge/child_education_focus_definition_readonly_12004.hpp"
#include "xar_bridge/child_education_focus_native_command_12004.hpp"
#include "xar_bridge/child_education_focus_receipt_v1.hpp"
#include "xar_bridge/ck3_12004_child_current_focus_readonly.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <Windows.h>
#include <bit>
#include <limits>
#include <memory>
#include <utility>

namespace xar::ck3_12004::education {
namespace {
using namespace ck3_11906;
enum class Mode { query, submit, receipt };

struct Context {
  ck3_12002::QueryMailboxEnvelope envelope{};
  lifestyle::PlayerLifestyleBindings12004 bindings{};
  ChildEducationFocusSourceFrame12004 frame{};
  std::uint32_t child = 0;
  std::string key{};
  Mode mode = Mode::query;
  MainThreadExecutionStampV1 stamp{};
  ChildEducationFocusQuery12004 query{};
  ChildEducationFocusSubmission12004 submission{};
  ChildEducationFocusReceipt12004 receipt{};
  bool completed = false;
  bool dispatch_entered = false;
  std::string failure{};
};

bool ValidFullId(std::uint64_t value) noexcept {
  return value != 0 && value < 0xFFFFFFFFULL;
}
bool SameCoreFrame(const game::Snapshot &a, const game::Snapshot &b) noexcept {
  return a.date_raw == b.date_raw && a.speed == b.speed &&
      a.paused == b.paused && a.player_id == b.player_id &&
      a.map_ready == b.map_ready &&
      a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t bytes) noexcept {
  SIZE_T actual = 0;
  return address != 0 && output != nullptr && bytes != 0 &&
      ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void *>(address),
                        output, bytes, &actual) != 0 && actual == bytes;
}
bool ReadChildMemory(void *opaque, const void *address, void *output,
                     std::size_t bytes) noexcept {
  return ReadMemory(opaque, reinterpret_cast<std::uintptr_t>(address), output, bytes);
}
bool OnMain(const Context &context) noexcept {
  return context.stamp.thread_id != 0 && context.stamp.paused &&
      context.stamp.tls_initialized != 0 && context.stamp.tls_main_thread_marker != 0 &&
      GetCurrentThreadId() == context.stamp.thread_id;
}
bool CurrentBound(const Context &context) noexcept {
  CoreSnapshotPrefix current{};
  const auto &expected = context.envelope.expected_snapshot;
  return OnMain(context) && ReadCoreSnapshot(context.bindings.core, current) &&
      current.clock.date_raw == expected.date_raw &&
      current.clock.paused == expected.paused &&
      current.played_character_id == expected.played_character_id &&
      current.played_character_alive == expected.played_character_alive &&
      current.map_ready == expected.map_ready && expected.paused && expected.map_ready &&
      expected.has_played_character && expected.played_character_alive &&
      std::bit_cast<std::uint32_t>(expected.played_character_id) ==
          context.frame.controller_full_id && context.stamp.date_raw == expected.date_raw;
}
bool IsMain(void *opaque) noexcept {
  const auto *context = static_cast<const Context *>(opaque);
  return context != nullptr && OnMain(*context);
}
bool IsPaused(void *opaque) noexcept {
  const auto *context = static_cast<const Context *>(opaque);
  return context != nullptr && CurrentBound(*context);
}
lifestyle::PlayerLifestyleSelectionNativeAdapterAccessV1 CommandAccess(Context &context) {
  lifestyle::PlayerLifestyleSelectionNativeAdapterAccessV1 access{};
  access.execution_context = &context;
  access.is_application_main_thread = &IsMain;
  access.is_paused = &IsPaused;
  return access;
}

std::uintptr_t ResolveChild(Context &context, std::string_view &reason) noexcept {
  const auto child = reinterpret_cast<std::uintptr_t>(ResolveCoreCharacter(
      context.bindings.core, std::bit_cast<std::int32_t>(context.child)));
  const ChildCurrentFocusReadonlyAccess12004 access{nullptr, &ReadChildMemory};
  return child_current_focus_readonly_detail::SameLivingChild(
      access, child, std::bit_cast<std::int32_t>(context.child), reason) ? child : 0;
}
CurrentFirstHeirChildFocusV1 ReadFocus(Context &context, std::uintptr_t child) noexcept {
  const ChildCurrentFocusReadonlyAccess12004 access{nullptr, &ReadChildMemory};
  return ReadChildCurrentFocusReadonly12004(context.bindings.snapshot, access,
      std::bit_cast<std::int32_t>(context.child), child);
}
ChildEducationFocusDefinitionRead12004 ReadDefinition(Context &context) noexcept {
  const ChildEducationFocusDefinitionReadAccess12004 access{nullptr, &ReadMemory};
  return ReadChildEducationFocusDefinitionReadonly12004(access,
      context.bindings.module_base, context.bindings.enabled,
      context.bindings.admitted_executable_sha256, context.key);
}

void ExecuteBody(Context &context) {
  if (!CurrentBound(context)) {
    context.failure = "child_focus_owning_frame_unavailable";
    return;
  }
  std::string_view child_reason{};
  const auto child = ResolveChild(context, child_reason);
  if (context.mode == Mode::receipt) {
    ChildEducationFocusPostObservation12004 post{};
    post.action_id = context.submission.action_id;
    post.source_frame = context.frame;
    post.child_full_id = context.child;
    post.independently_published_after_submission =
        context.frame.native_revision > context.submission.pre_frame.native_revision &&
        context.frame.snapshot_id != context.submission.pre_frame.snapshot_id;
    post.current_focus = ReadFocus(context, child);
    context.receipt = EvaluateChildEducationFocusReceipt12004(context.submission, post);
    context.completed = true;
    return;
  }

  if (context.mode == Mode::query) {
    context.query.source_frame = context.frame;
    context.query.child_full_id = context.child;
    context.query.target_key = context.key;
    context.query.current_focus = ReadFocus(context, child);
  }
  if (child == 0) {
    if (context.mode == Mode::query) context.query.unavailable_reason.assign(child_reason);
    else context.submission.unavailable_reason.assign(child_reason);
    context.completed = true;
    return;
  }
  const auto definition = ReadDefinition(context);
  if (!definition.available) {
    if (context.mode == Mode::query)
      context.query.unavailable_reason.assign(definition.unavailable_reason);
    else context.submission.unavailable_reason.assign(definition.unavailable_reason);
    context.completed = true;
    return;
  }
  const auto access = CommandAccess(context);
  if (context.mode == Mode::query) {
    context.query.native_legal =
        lifestyle::ValidateResolvedChildEducationFocusNativeAdapter12004V1(
            context.bindings.selection, access, context.child,
            context.frame.controller_full_id, definition.definition_identity);
    context.query.available = context.query.native_legal.has_value();
    if (!context.query.available)
      context.query.unavailable_reason = "child_focus_native_validator_unavailable";
  } else {
    // Only this once-call can submit. The command leaf revalidates the original
    // child/controller/definition command immediately before its native copy.
    context.dispatch_entered = true;
    const auto result = lifestyle::DispatchResolvedChildEducationFocusNativeAdapter12004V1(
        context.bindings.selection, access, context.child,
        context.frame.controller_full_id, definition.definition_identity);
    using Dispatch = lifestyle::PlayerLifestyleSelectionNativeDispatchResultV1;
    if (result == Dispatch::submitted_verification_pending) {
      context.submission.accepted = true;
      context.submission.status = "submitted_verification_pending";
    } else if (result == Dispatch::submit_rejected) {
      // The existing submit wrapper can return false after an exception. Keep
      // this attempt pending for inspection instead of automatically retrying.
      context.submission.status = "submit_unknown";
      context.submission.unavailable_reason = "child_focus_native_submit_not_confirmed";
    } else {
      context.submission.unavailable_reason =
          result == Dispatch::command_validator_rejected
              ? "child_focus_native_validator_rejected"
              : "child_focus_native_adapter_unavailable";
    }
  }
  context.completed = true;
}

void String(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  out += '"';
  for (unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  out += '"';
}
void Reason(std::string &out, std::string_view value) {
  if (value.empty()) out += "null"; else String(out, value);
}
void Frame(std::string &out, const ChildEducationFocusSourceFrame12004 &frame) {
  out += "{\"snapshot_id\":"; String(out, frame.snapshot_id);
  out += ",\"episode_run_id\":"; String(out, frame.episode_run_id);
  out += ",\"native_revision\":" + std::to_string(frame.native_revision);
  out += ",\"date_raw\":" + std::to_string(frame.date_raw);
  out += ",\"controller_full_id\":" + std::to_string(frame.controller_full_id);
  out += frame.paused ? ",\"paused\":true}" : ",\"paused\":false}";
}
void Focus(std::string &out, const CurrentFirstHeirChildFocusV1 &focus) {
  out += focus.available ? "{\"available\":true" : "{\"available\":false";
  out += ",\"unavailable_reason\":"; Reason(out, focus.unavailable_reason);
  out += ",\"presence\":"; String(out, focus.presence);
  out += ",\"key\":";
  if (focus.key) String(out, *focus.key); else out += "null";
  out += '}';
}
void Submission(std::string &out, const ChildEducationFocusSubmission12004 &value) {
  out += "\"status\":"; String(out, value.status);
  out += ",\"unavailable_reason\":"; Reason(out, value.unavailable_reason);
  out += ",\"action_request_id\":"; String(out, value.action_id);
  out += value.accepted ? ",\"accepted\":true" : ",\"accepted\":false";
  out += ",\"child_full_id\":" + std::to_string(value.child_full_id);
  out += ",\"requested_focus_key\":"; String(out, value.requested_focus_key);
  out += ",\"pre_frame\":"; Frame(out, value.pre_frame);
}
std::string Error(std::string_view request_id, std::string_view reason,
                  const game::AdapterDescriptor &descriptor) {
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  String(out, request_id); out += ",\"ok\":false,\"error\":"; String(out, reason); out += '}';
  return game::Render12004BuildIdentity(std::move(out), descriptor);
}
std::string Render(const Context &context, std::string_view request_id,
                   const game::AdapterDescriptor &descriptor) {
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  String(out, request_id); out += ",\"ok\":true,\"result\":{\"schema\":";
  String(out, kChildEducationFocusSchema12004);
  if (context.mode == Mode::query) {
    const auto &query = context.query;
    out += ",\"kind\":\"query\",\"status\":";
    String(out, query.available ? "available" : "unavailable");
    out += ",\"unavailable_reason\":"; Reason(out, query.unavailable_reason);
    out += ",\"source_frame\":"; Frame(out, query.source_frame);
    out += ",\"child_full_id\":" + std::to_string(query.child_full_id);
    out += ",\"target_key\":"; String(out, query.target_key);
    out += ",\"native_legal\":";
    out += query.native_legal ? (*query.native_legal ? "true" : "false") : "null";
    out += ",\"current_focus\":"; Focus(out, query.current_focus);
  } else if (context.mode == Mode::submit) {
    out += ",\"kind\":\"submit\","; Submission(out, context.submission);
  } else {
    const auto &receipt = context.receipt;
    out += ",\"kind\":\"receipt\",\"status\":"; String(out, receipt.status);
    out += ",\"unavailable_reason\":"; Reason(out, receipt.unavailable_reason);
    out += receipt.observed_applied ? ",\"observed_applied\":true" : ",\"observed_applied\":false";
    out += ",\"submission\":{"; Submission(out, receipt.submission); out += '}';
    out += ",\"post_observation\":";
    if (!receipt.post) out += "null";
    else {
      const auto &post = *receipt.post;
      out += "{\"action_request_id\":"; String(out, post.action_id);
      out += post.independently_published_after_submission
          ? ",\"independently_published_after_submission\":true"
          : ",\"independently_published_after_submission\":false";
      out += ",\"source_frame\":"; Frame(out, post.source_frame);
      out += ",\"child_full_id\":" + std::to_string(post.child_full_id);
      out += ",\"current_focus\":"; Focus(out, post.current_focus); out += '}';
    }
  }
  out += "}}";
  return game::Render12004BuildIdentity(std::move(out), descriptor);
}
} // namespace

bool AcceptsChildEducationFocusStep12004(std::string_view step) noexcept {
  return step == kChildEducationFocusQueryStep12004 ||
      step == kChildEducationFocusSubmitStep12004 || step == kChildEducationFocusReceiptStep12004;
}
bool ChildEducationFocusExpectedRevision12004(std::string_view payload,
                                            std::uint64_t &revision) noexcept {
  return bridge::JsonUnsignedField(payload, "expected_revision", revision) && revision != 0;
}
bool ChildEducationFocusNeedsPostSubmitSnapshot12004(
    const ChildEducationFocusTransport12004 &transport, std::string_view request_id) noexcept {
  return transport.needs_post_submit_snapshot && transport.last_submit_request_id == request_id;
}

bool ExecuteChildEducationFocusMailbox12004(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  auto *context = envelope == nullptr ? nullptr : static_cast<Context *>(envelope->typed_context);
  if (context == nullptr) return false;
  if (!ck3_12002::EnterQueryMailbox(*envelope, stamp, &ExecuteChildEducationFocusMailbox12004)) {
    context->failure = "child_focus_owning_frame_unavailable";
    return true;
  }
  context->stamp = stamp;
  try {
    ExecuteBody(*context);
  } catch (...) {
    if (context->mode == Mode::submit && context->dispatch_entered) {
      context->submission.status = "submit_unknown";
      context->submission.unavailable_reason = "child_focus_executor_exception_after_dispatch";
    }
    context->failure = "child_focus_executor_exception";
  }
  if (!ck3_12002::FinishQueryMailbox(*envelope)) {
    context->completed = false;
    context->failure = "child_focus_owning_frame_changed";
  }
  return true;
}

std::string HandleChildEducationFocus12004(ChildEducationFocusTransport12004 &transport,
    std::string_view request_id, std::string_view step, std::string_view payload,
    const game::GameAdapter &adapter, const lifestyle::PlayerLifestyleBindings12004 &bindings,
    const game::Snapshot &published, std::uint64_t published_revision,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox) {
  using namespace ck3_11906;
  if (!AcceptsChildEducationFocusStep12004(step)) return {};
  const auto &descriptor = adapter.descriptor();
  std::string snapshot_id, episode, key, action_id;
  std::uint64_t revision = 0, date = 0, controller = 0, child = 0;
  if (!bridge::JsonStringField(payload, "expected_snapshot_id", snapshot_id, 48) ||
      !bridge::JsonStringField(payload, "episode_run_id", episode, 128) || episode.empty() ||
      !ChildEducationFocusExpectedRevision12004(payload, revision) ||
      !bridge::JsonUnsignedField(payload, "expected_date_raw", date) ||
      !bridge::JsonUnsignedField(payload, "expected_player_character_id", controller) ||
      !bridge::JsonUnsignedField(payload, "child_full_id", child) ||
      !bridge::JsonStringField(payload, "target_key", key, 128) ||
      !ValidFullId(child) || !ValidFullId(controller) || revision != published_revision ||
      snapshot_id != "native:" + std::to_string(published_revision) ||
      date > static_cast<std::uint64_t>((std::numeric_limits<std::int32_t>::max)()) ||
      published.date_raw < 0 || date != static_cast<std::uint64_t>(published.date_raw) ||
      controller != std::bit_cast<std::uint32_t>(published.played_character_id)) {
    return Error(request_id, "child_focus_request_frame_invalid", descriptor);
  }
  if (!game::IsCk3_12004Descriptor(descriptor) || !bindings.enabled)
    return Error(request_id, "child_focus_actual4_bind_unavailable", descriptor);
  game::Snapshot current{};
  if (!published.paused || !published.map_ready || !published.has_played_character ||
      !published.played_character_alive ||
      !game::ReadCk3_12002TimelineCoreSnapshot(adapter, current) || !SameCoreFrame(current, published))
    return Error(request_id, "child_focus_published_frame_stale", descriptor);
  const Mode mode = step == kChildEducationFocusQueryStep12004 ? Mode::query
      : step == kChildEducationFocusSubmitStep12004 ? Mode::submit : Mode::receipt;
  if (mode != Mode::query &&
      !bridge::JsonStringField(payload, "action_request_id", action_id, 128))
    return Error(request_id, "child_focus_action_id_missing", descriptor);
  if (mode == Mode::submit && (action_id != request_id || action_id.empty() ||
      transport.action_may_have_submitted || transport.pending))
    return Error(request_id, "child_focus_submission_binding_or_pending_invalid", descriptor);
  if (mode == Mode::receipt && (!transport.pending ||
      action_id != transport.pending->action_id || child != transport.pending->child_full_id ||
      key != transport.pending->requested_focus_key || episode != transport.pending->pre_frame.episode_run_id ||
      controller != transport.pending->pre_frame.controller_full_id))
    return Error(request_id, "child_focus_pending_receipt_invalid", descriptor);

  auto context = std::make_unique<Context>();
  context->bindings = bindings;
  context->frame = {snapshot_id, episode, revision, published.date_raw,
                    static_cast<std::uint32_t>(controller), published.paused};
  context->child = static_cast<std::uint32_t>(child);
  context->key = key;
  context->mode = mode;
  context->envelope.game = &adapter;
  context->envelope.mailbox = &mailbox;
  context->envelope.expected_snapshot = current;
  context->envelope.expected_snapshot_revision = published_revision;
  context->envelope.typed_context = context.get();
  context->envelope.snapshot_comparison = ck3_12002::QuerySnapshotComparison12002::core_frame;
  if (mode == Mode::submit) {
    context->submission.action_id = action_id;
    context->submission.child_full_id = context->child;
    context->submission.requested_focus_key = key;
    context->submission.pre_frame = context->frame;
    transport.needs_post_submit_snapshot = false;
  } else if (mode == Mode::receipt) context->submission = *transport.pending;
  auto &ticket = context->envelope.ticket;
  if (TrySubmitMainThreadQueryV1(mailbox, &ExecuteChildEducationFocusMailbox12004,
      &context->envelope, ticket) != MainThreadQuerySubmitResultV1::submitted)
    return Error(request_id, "child_focus_application_main_unavailable", descriptor);
  if (mode == Mode::submit) transport.action_may_have_submitted = true;
  auto wait = WaitForMainThreadQueryV1(mailbox, ticket, 8'000);
  while (wait == MainThreadQueryWaitResultV1::timeout_executor_already_running)
    wait = WaitForMainThreadQueryV1(mailbox, ticket, 2'000);
  game::Snapshot completion{};
  const bool stable = wait == MainThreadQueryWaitResultV1::completed &&
      context->envelope.frame_stable && context->completed &&
      game::ReadCk3_12002TimelineCoreSnapshot(adapter, completion) && SameCoreFrame(completion, current);
  if (mode == Mode::submit) {
    const auto &submission = context->submission;
    if (submission.accepted || submission.status == "submit_unknown") {
      transport.pending = submission;
      transport.last_submit_request_id.assign(request_id);
      transport.needs_post_submit_snapshot = true;
    } else if (!context->dispatch_entered || submission.status == "rejected_before_submit") {
      transport.action_may_have_submitted = false;
    }
  }
  const auto response = stable ? Render(*context, request_id, descriptor)
      : Error(request_id, context->failure.empty() ? "child_focus_executor_or_completion_unavailable"
                                                  : context->failure, descriptor);
  if (stable && mode == Mode::receipt && context->receipt.observed_applied) {
    transport.pending.reset();
    transport.action_may_have_submitted = false;
    transport.needs_post_submit_snapshot = false;
  }
  if (ReclaimMainThreadQueryV1(mailbox, ticket) != MainThreadQueryReclaimResultV1::reclaimed)
    return Error(request_id, "child_focus_mailbox_result_not_reclaimed", descriptor);
  return response;
}
} // namespace xar::ck3_12004::education
