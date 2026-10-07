#include "xar_bridge/ck3_12004_sway_terminal.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <utility>
#include <windows.h>

namespace xar::ck3_12004 {
namespace {
using ck3_12002::SwayCompletionBindings12002;
using ck3_12002::SwayCompletionRequestV1;
using ck3_12002::SwayCompletionStateV1;
using ck3_12002::SwayStateBindings12002;

bool Copy(std::uintptr_t source, void *output, std::size_t size) noexcept {
  if (source == 0 || output == nullptr) return false;
  __try {
    std::memcpy(output, reinterpret_cast<const void *>(source), size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
template <typename T> bool Read(std::uintptr_t source, T &output) noexcept {
  return Copy(source, &output, sizeof(output));
}
bool Core(const CoreBindings &bindings, CoreSnapshotPrefix &output) noexcept {
  __try { return xar::ck3_12004::ReadCoreSnapshot(bindings, output); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool SameFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.paused == b.clock.paused &&
      a.clock.speed == b.clock.speed && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool IsSway(std::uintptr_t type, const SwayStateBindings12002 &b) noexcept {
  std::uintptr_t vtable{}, text{};
  std::uint64_t length{}, capacity{};
  std::uint32_t tag{};
  std::array<char, 4> key{};
  if (!type || !Read(type, vtable) || vtable != b.module_base + b.type_vtable_rva ||
      !Read(type + 0x28, length) || length != 4 ||
      !Read(type + 0x30, capacity) || capacity < length ||
      !Read(type + 0x38, tag) || tag != 0x4744624F) return false;
  text = type + 0x18;
  if (capacity >= 16 && (!Read(text, text) || !text)) return false;
  return Copy(text, key.data(), key.size()) && std::memcmp(key.data(), "sway", 4) == 0;
}
bool Fail(SwayCompletionStateV1 &out, const char *reason) {
  out.available = false; out.unavailable_reason = reason; return false;
}
bool ReadOnce(const SwayStateBindings12002 &b,
    const SwayCompletionRequestV1 &request, SwayCompletionStateV1 &out) {
  out.request = request;
  out.scheme_instance_generation = request.scheme_id >> 24;
  CoreSnapshotPrefix frame{};
  if (!Core(b.core, frame) || !frame.clock.paused || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive ||
      frame.played_character_id != request.actor_character_id)
    return Fail(out, "sway_terminal_paused_actor_unavailable");
  std::uintptr_t state{}, data{}, vtable{}, storage{}, slots{};
  std::int32_t capacity{};
  if (!Read(reinterpret_cast<std::uintptr_t>(b.core.game_state_slot), state) || !state ||
      !Read(state + kGameStateDataOffset, data) || !data ||
      !Read(data + b.manager_offset, vtable) ||
      vtable != b.module_base + b.manager_vtable_rva ||
      !Read(data + b.manager_offset + 0x20, storage) || !storage ||
      !Read(storage, vtable) || vtable != b.module_base + b.storage_vtable_rva ||
      !Read(storage + 0x20, slots) || !Read(storage + 0x2C, capacity) || capacity < 0 ||
      (capacity > 0 && !slots))
    return Fail(out, "sway_terminal_instance_source_unavailable");
  out.date_raw = frame.clock.date_raw;
  out.instance_source_observed = true;
  const auto index = request.scheme_id & 0x00FFFFFFu;
  std::uintptr_t scheme{};
  if (index < static_cast<std::uint32_t>(capacity) &&
      !Read(slots + static_cast<std::size_t>(index) * 0x10 + 8, scheme))
    return Fail(out, "sway_terminal_instance_slot_unavailable");
  if (scheme) {
    std::uint32_t full_id{}, target_kind{}, target{};
    std::uintptr_t type{};
    if (!Read(scheme + 0x10, full_id))
      return Fail(out, "sway_terminal_instance_identity_unavailable");
    if (full_id != request.scheme_id) {
      out.storage_slot_reused = true;
    } else {
      if (!Read(scheme, vtable) || vtable != b.module_base + b.instance_vtable_rva ||
          !Read(scheme + 0x20, type) || !IsSway(type, b) ||
          !Read(scheme + 0x28, out.native_status_raw) ||
          !Read(scheme + 0x2C, out.native_owner_raw) ||
          !Read(scheme + 0x30, target_kind) || target_kind != 0 ||
          !Read(scheme + 0x34, target) ||
          target != static_cast<std::uint32_t>(request.target_character_id))
        return Fail(out, "sway_terminal_instance_join_unavailable");
      out.owner_matches_actor =
          out.native_owner_raw == static_cast<std::uint32_t>(request.actor_character_id);
      out.owner_cleared = out.native_owner_raw == 0xFFFFFFFFu;
      if (!out.owner_matches_actor && !(out.owner_cleared && out.native_status_raw == 1))
        return Fail(out, "sway_terminal_native_owner_mismatch");
      out.instance_present = true;
      out.exact_instance_join_ready = true;
      out.native_status_observed = true;
      // Root's actual paired 68B proves the common status1 write/owner clear.
      // The row has no completed/failed/canceled cause and is transient until purge.
      out.native_status_key = out.native_status_raw == 0 ? "continue" :
          out.native_status_raw == 1 ? "terminated_unattributed" :
          out.native_status_raw == 2 ? "invalid" : "unknown";
      out.native_terminal_state_observed = out.native_status_raw == 1;
    }
  }
  CoreSnapshotPrefix after{};
  if (!Core(b.core, after) || !SameFrame(frame, after))
    return Fail(out, "sway_terminal_frame_changed");
  out.available = true;
  return true;
}
bool Parse(std::string_view payload, SwayCompletionRequestV1 &request) noexcept {
  std::uint64_t actor{}, target{}, scheme{};
  if (!bridge::JsonUnsignedField(payload, "expected_revision", request.expected_revision) ||
      !bridge::JsonUnsignedField(payload, "actor_character_id", actor) ||
      !bridge::JsonUnsignedField(payload, "target_character_id", target) ||
      !bridge::JsonUnsignedField(payload, "scheme_instance_id", scheme) ||
      actor > std::numeric_limits<std::int32_t>::max() ||
      target > std::numeric_limits<std::int32_t>::max() ||
      scheme >= std::numeric_limits<std::uint32_t>::max()) return false;
  request.actor_character_id = static_cast<std::int32_t>(actor);
  request.target_character_id = static_cast<std::int32_t>(target);
  request.scheme_id = static_cast<std::uint32_t>(scheme);
  return request.expected_revision != 0 && actor != 0 && target != 0 && actor != target;
}
} // namespace

ck3_12002::SwayCompletionBindings12002 BindSwayTerminalImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::SwayCompletionBindings12002 b{};
  b.core = xar::ck3_12004::BindCoreImage(base, sha);
  if (!b.core.enabled) return b;
  b.enabled = true;
  b.image_base = base;
  return b;
}

bool ReadSwayTerminal12004(const ck3_12002::SwayCompletionBindings12002 &b,
    const ck3_12002::SwayCompletionRequestV1 &request,
    ck3_12002::SwayCompletionStateV1 &output) noexcept {
  output = {}; output.request = request;
  output.scheme_instance_generation = request.scheme_id >> 24;
  if (!b.enabled || !b.core.enabled || !b.image_base || !request.expected_revision ||
      request.actor_character_id <= 0 || request.target_character_id <= 0 ||
      request.actor_character_id == request.target_character_id || request.scheme_id == 0xFFFFFFFFu)
    return Fail(output, "sway_terminal_build_or_request_unavailable");
  try {
    auto source = BindSwayStateImage12004(b.image_base, kExecutableSha256);
    if (!source.enabled) return Fail(output, "sway_terminal_actual4_profile_unavailable");
    source.core = b.core;
    ck3_12002::SwayCompletionStateV1 first{}, second{};
    if (!ReadOnce(source, request, first)) { output = std::move(first); return false; }
    if (!ReadOnce(source, request, second)) { output = std::move(second); return false; }
    if (first != second) return Fail(output, "sway_terminal_source_changed");
    output = std::move(second); return true;
  } catch (...) { return Fail(output, "sway_terminal_internal_error"); }
}

bool ExecuteSwayTerminalMailbox12004(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) return false;
  auto &query = *static_cast<ck3_12002::SwayCompletionMailboxContextV1 *>(envelope->typed_context);
  if (query.request.expected_revision != envelope->expected_snapshot_revision ||
      query.request.actor_character_id != envelope->expected_snapshot.played_character_id ||
      !ck3_12002::EnterQueryMailbox(*envelope, stamp, &ExecuteSwayTerminalMailbox12004)) {
    query.failure = "sway_terminal_published_frame_changed";
    query.completed = true;
    return true;
  }
  (void)ReadSwayTerminal12004(query.bindings, query.request, query.result);
  if (query.result.available && query.result.date_raw != stamp.date_raw) {
    query.result.available = false;
    query.result.unavailable_reason = "sway_terminal_native_date_changed";
  }
  query.completed = true;
  (void)ck3_12002::FinishQueryMailbox(*envelope);
  return true;
}

std::string SerializeSwayTerminalCommandResult12004(
    const ck3_12002::SwayCompletionStateV1 &output,
    std::uint64_t revision, std::int32_t date_raw,
    std::string_view request_id, const game::AdapterDescriptor &descriptor) {
  return game::Render12004BuildIdentity(
      ck3_12002::SerializeSwayCompletionCommandResultV1(
          output, revision, date_raw, request_id), descriptor);
}

bool HandleSwayTerminal12004(const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  using namespace ck3_11906;
  serialized.clear(); failure.clear();
  try {
    ck3_12002::SwayCompletionMailboxContextV1 query{};
    if (step != ck3_12002::kSwayCompletionStepV1 || !Parse(payload, query.request) ||
        query.request.expected_revision != revision || !adapter.enabled() ||
        !game::IsCk3_12004Descriptor(adapter.descriptor()) || !published.paused ||
        !published.map_ready || !published.has_played_character ||
        !published.played_character_alive ||
        published.played_character_id != query.request.actor_character_id) {
      failure = "sway_terminal_frame_or_request_invalid"; return false;
    }
    query.envelope.game = &ck3_12002::NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.envelope.typed_context = &query;
    query.bindings = BindSwayTerminalImage12004(
        reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
        adapter.descriptor().executable_sha256);
    if (TrySubmitMainThreadQueryV1(mailbox, &ExecuteSwayTerminalMailbox12004,
                                  &query.envelope, query.envelope.ticket) !=
        MainThreadQuerySubmitResultV1::submitted) {
      failure = "sway_terminal_executor_unavailable"; return false;
    }
    auto waited = WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 8000);
    while (waited == MainThreadQueryWaitResultV1::timeout_executor_already_running)
      waited = WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 2000);
    const auto reclaimed = ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
    if (waited != MainThreadQueryWaitResultV1::completed ||
        reclaimed != MainThreadQueryReclaimResultV1::reclaimed || !query.completed ||
        !query.envelope.frame_stable || !query.failure.empty()) {
      failure = query.failure.empty() ? "sway_terminal_executor_result_unavailable" : query.failure;
      return false;
    }
    serialized = SerializeSwayTerminalCommandResult12004(
        query.result, revision, query.envelope.execution_stamp.date_raw,
        request_id, adapter.descriptor());
    return true;
  } catch (...) { failure = "sway_terminal_handler_exception"; return false; }
}
} // namespace xar::ck3_12004
