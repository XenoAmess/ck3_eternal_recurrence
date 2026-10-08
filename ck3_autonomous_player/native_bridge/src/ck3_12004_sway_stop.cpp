#include "xar_bridge/ck3_12004_sway_stop.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <limits>
#include <windows.h>

namespace xar::ck3_12004 {
namespace {
std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { out += '\\'; out += static_cast<char>(ch); }
    else if (ch < 0x20) { out += "\\u00"; out += hex[ch >> 4]; out += hex[ch & 15]; }
    else out += static_cast<char>(ch);
  }
  return out + '"';
}
bool Parse(std::string_view payload, SwayStopMailboxContext12004 &q) noexcept {
  std::uint64_t actor{}, target{}, id{}, generation{};
  auto &request = q.request.instance;
  if (!bridge::JsonUnsignedField(payload, "expected_revision", request.expected_revision) ||
      !bridge::JsonUnsignedField(payload, "actor_character_id", actor) ||
      !bridge::JsonUnsignedField(payload, "target_character_id", target) ||
      !bridge::JsonUnsignedField(payload, "scheme_instance_id", id) ||
      !bridge::JsonUnsignedField(payload, "scheme_instance_generation", generation) ||
      !bridge::JsonStringField(payload, "action_id", q.action_id, 64) ||
      request.expected_revision == 0 || actor == 0 || target == 0 || actor == target ||
      actor > std::numeric_limits<std::int32_t>::max() ||
      target > std::numeric_limits<std::int32_t>::max() ||
      id >= std::numeric_limits<std::uint32_t>::max() || generation > 255 ||
      (id >> 24) != generation || !q.action_id.starts_with("stop-sway-") ||
      q.action_id.size() > 64) return false;
  for (const unsigned char ch : q.action_id)
    if (!((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
          (ch >= '0' && ch <= '9') || ch == '-' || ch == '_')) return false;
  request.actor_character_id = static_cast<std::int32_t>(actor);
  request.target_character_id = static_cast<std::int32_t>(target);
  request.scheme_id = static_cast<std::uint32_t>(id);
  q.request.scheme_instance_generation = static_cast<std::uint32_t>(generation);
  return true;
}
} // namespace

SwayStopBindings12004 BindSwayStopImage12004(
    std::uintptr_t base, std::string_view sha256,
    const SwayStopCommandProfile12004 &profile) noexcept {
  SwayStopBindings12004 bindings{};
  if (profile.executable_sha256 != kExecutableSha256 ||
      profile.primary_vtable_rva == 0 || profile.secondary_vtable_rva == 0) {
    return bindings;
  }
  bindings.commands = BindCommandImage12004(base, sha256);
  bindings.terminal = BindSwayTerminalImage12004(base, sha256);
  if (!bindings.commands.enabled || !bindings.terminal.enabled) return bindings;
  bindings.primary_vtable = base + profile.primary_vtable_rva;
  bindings.secondary_vtable = base + profile.secondary_vtable_rva;
  bindings.enabled = true;
  return bindings;
}

ck3_12002::CommandSubmitResult SubmitSelectedSwayStop12004(
    const SwayStopBindings12004 &bindings,
    const SwayStopRequest12004 &request,
    ck3_12002::SwayCompletionStateV1 &before) noexcept {
  using ck3_12002::CommandSubmitResult;
  before = {};
  if (!bindings.enabled ||
      !ReadSwayTerminal12004(bindings.terminal, request.instance, before) ||
      !before.available) return CommandSubmitResult::unavailable;
  if (!before.exact_instance_join_ready || !before.owner_matches_actor ||
      before.native_owner_raw !=
          static_cast<std::uint32_t>(request.instance.actor_character_id) ||
      before.scheme_instance_generation != request.scheme_instance_generation ||
      before.date_raw != request.expected_date_raw ||
      !before.native_status_observed || before.native_status_raw != 0) {
    return CommandSubmitResult::rejected;
  }
  SelectedEndSchemeCommand12004 command{};
  command.primary_vtable = bindings.primary_vtable;
  command.secondary_vtable = bindings.secondary_vtable;
  command.scheme_id = request.instance.scheme_id;
  // Native Cancel confirmation uses kind14, not the interaction/default kind7.
  return ck3_12002::SubmitCommandCopy(bindings.commands, &command, 14);
}

bool ExecuteSelectedSwayStop12004(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &q = *static_cast<SwayStopMailboxContext12004 *>(envelope->typed_context);
  if (q.request.instance.expected_revision != envelope->expected_snapshot_revision ||
      q.request.instance.actor_character_id != envelope->expected_snapshot.played_character_id ||
      !ck3_12002::EnterQueryMailbox(*envelope, stamp, &ExecuteSelectedSwayStop12004)) {
    q.failure = "selected_sway_stop_published_frame_changed";
    q.completed = true; return true;
  }
  q.request.expected_date_raw = stamp.date_raw;
  q.result = SubmitSelectedSwayStop12004(q.bindings, q.request, q.before);
  q.completed = true;
  (void)ck3_12002::FinishQueryMailbox(*envelope);
  return true;
}

std::string SerializeSelectedSwayStop12004(const SwayStopMailboxContext12004 &q,
    std::string_view request_id, const game::AdapterDescriptor &descriptor) {
  const bool submitted = q.result == ck3_12002::CommandSubmitResult::submitted;
  const auto &request = q.request.instance;
  const std::string pending = submitted ? "submitted_verification_pending" : "rejected";
  return game::Render12004BuildIdentity(
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id) + ",\"ok\":" + (submitted ? "true" : "false") +
      ",\"error\":" + Quote(submitted ? "" : "selected_sway_stop_native_rejected") +
      ",\"result\":{\"step\":" + Quote(kSwayStopStep12004) +
      ",\"accepted\":" + (submitted ? "true" : "false") +
      ",\"private_build\":true,\"advertised\":false,\"read_only\":false,"
      "\"backend_id\":\"native-headless\",\"status\":" + Quote(pending) +
      ",\"sway_stop\":{\"schema\":\"xar.ck3.selected-sway-stop.v1\",\"action_id\":" +
      Quote(q.action_id) + ",\"status\":" + Quote(pending) +
      ",\"actor_character_id\":" + std::to_string(request.actor_character_id) +
      ",\"target_character_id\":" + std::to_string(request.target_character_id) +
      ",\"scheme_instance_id\":" + std::to_string(request.scheme_id) +
      ",\"scheme_instance_generation\":" + std::to_string(q.request.scheme_instance_generation) +
      ",\"snapshot_revision\":" + std::to_string(request.expected_revision) +
      ",\"date_raw\":" + std::to_string(q.envelope.execution_stamp.date_raw) +
      ",\"exact_ck3_build\":" + Quote(kGameVersion) +
      ",\"exe_sha256\":" + Quote(kExecutableSha256) +
      ",\"submit_call_count\":" + (submitted ? "1" : "0") +
      ",\"postcondition_verified\":false,\"terminal_observed\":false,"
      "\"terminal_cause_observed\":false,\"terminal_cause\":\"unknown\"}}}", descriptor);
}

bool HandleSelectedSwayStop12004(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    SwayStopMailboxContext12004 q{};
    if (step != kSwayStopStep12004 || !Parse(payload, q) ||
        q.request.instance.expected_revision != revision || !adapter.enabled() ||
        !game::IsCk3_12004Descriptor(adapter.descriptor()) || !published.paused ||
        !published.map_ready || !published.has_played_character ||
        !published.played_character_alive ||
        published.played_character_id != q.request.instance.actor_character_id) {
      failure = "selected_sway_stop_frame_or_request_invalid"; return false;
    }
    q.envelope.game = &ck3_12002::NativeAdapter12002(adapter);
    q.envelope.mailbox = &mailbox;
    q.envelope.expected_snapshot = published;
    q.envelope.expected_snapshot_revision = revision;
    q.envelope.typed_context = &q;
    q.bindings = BindSwayStopImage12004(
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
        adapter.descriptor().executable_sha256);
    if (TrySubmitMainThreadQueryV1(mailbox, &ExecuteSelectedSwayStop12004,
          &q.envelope, q.envelope.ticket) != MainThreadQuerySubmitResultV1::submitted) {
      failure = "selected_sway_stop_executor_unavailable"; return false;
    }
    auto waited = WaitForMainThreadQueryV1(mailbox, q.envelope.ticket, 8000);
    while (waited == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      waited = WaitForMainThreadQueryV1(mailbox, q.envelope.ticket, 2000);
    const auto reclaimed = ReclaimMainThreadQueryV1(mailbox, q.envelope.ticket);
    if (waited != MainThreadQueryWaitResultV1::completed ||
        reclaimed != MainThreadQueryReclaimResultV1::reclaimed || !q.completed ||
        !q.envelope.frame_stable || !q.failure.empty()) {
      failure = q.failure.empty() ? "selected_sway_stop_executor_result_unavailable" : q.failure;
      return false;
    }
    serialized = SerializeSelectedSwayStop12004(q, request_id, adapter.descriptor());
    return true;
  } catch (...) { failure = "selected_sway_stop_handler_exception"; return false; }
}

} // namespace xar::ck3_12004
