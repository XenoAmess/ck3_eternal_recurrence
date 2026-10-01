#include "xar_bridge/ck3_12002_sway_completion.hpp"

#include <cstring>
#include <utility>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
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
  __try { return ReadCoreSnapshot(bindings, output); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool Chance(SwayCompletionSuccessChance12002 getter,
    std::uintptr_t scheme, std::int64_t &output) noexcept {
  if (getter == nullptr) return false;
  __try {
    return getter(reinterpret_cast<const void *>(scheme), &output) == &output;
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool IsSway(std::uintptr_t type, std::uintptr_t base) noexcept {
  std::uintptr_t vtable{}, text{};
  std::uint64_t length{}, capacity{};
  std::uint32_t tag{};
  std::array<char, 4> key{};
  if (!type || !Read(type, vtable) || vtable != base + kSwayTypeVtableRva12002 ||
      !Read(type + 0x28, length) || length != 4 ||
      !Read(type + 0x30, capacity) || capacity < length ||
      !Read(type + 0x38, tag) || tag != 0x4744624F) return false;
  text = type + 0x18;
  if (capacity >= 16 && (!Read(text, text) || !text)) return false;
  return Copy(text, key.data(), key.size()) && std::memcmp(key.data(), "sway", 4) == 0;
}
bool SameFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.paused == b.clock.paused &&
      a.clock.speed == b.clock.speed && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool Fail(SwayCompletionStateV1 &out, const char *reason) {
  out.available = false; out.unavailable_reason = reason; return false;
}
bool ReadOnce(const SwayCompletionBindings12002 &b,
    const SwayCompletionRequestV1 &request, SwayCompletionStateV1 &out) {
  out.request = request;
  out.scheme_instance_generation = request.scheme_id >> 24;
  CoreSnapshotPrefix frame{};
  if (!Core(b.core, frame) || !frame.clock.paused || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive ||
      frame.played_character_id != request.actor_character_id)
    return Fail(out, "sway_completion_paused_actor_unavailable");
  std::uintptr_t state{}, data{}, vtable{}, storage{}, slots{};
  std::int32_t capacity{};
  if (!Read(reinterpret_cast<std::uintptr_t>(b.core.game_state_slot), state) || !state ||
      !Read(state + 0xA0, data) || !data ||
      !Read(data + kSwayManagerOffset12002, vtable) ||
      vtable != b.image_base + kSwayManagerVtableRva12002 ||
      !Read(data + kSwayManagerOffset12002 + 0x20, storage) || !storage ||
      !Read(storage, vtable) || vtable != b.image_base + kSwayStorageVtableRva12002 ||
      !Read(storage + 0x20, slots) || !Read(storage + 0x2C, capacity) || capacity < 0 ||
      (capacity > 0 && !slots)) return Fail(out, "sway_completion_instance_source_unavailable");
  out.date_raw = frame.clock.date_raw;
  out.instance_source_observed = true;
  const auto index = request.scheme_id & 0x00FFFFFFu;
  std::uintptr_t scheme{};
  if (index < static_cast<std::uint32_t>(capacity) &&
      !Read(slots + static_cast<std::size_t>(index) * 0x10 + 8, scheme))
    return Fail(out, "sway_completion_instance_slot_unavailable");
  if (scheme) {
    std::uint32_t full_id{}, target_kind{}, target{};
    std::uintptr_t type{};
    if (!Read(scheme + 0x10, full_id))
      return Fail(out, "sway_completion_instance_identity_unavailable");
    if (full_id != request.scheme_id) {
      out.storage_slot_reused = true;
    } else {
      if (!Read(scheme, vtable) || vtable != b.image_base + kSwayInstanceVtableRva12002 ||
          !Read(scheme + 0x20, type) || !IsSway(type, b.image_base) ||
          !Read(scheme + 0x28, out.native_status_raw) ||
          !Read(scheme + 0x2C, out.native_owner_raw) ||
          !Read(scheme + 0x30, target_kind) || target_kind != 0 ||
          !Read(scheme + 0x34, target) || target != static_cast<std::uint32_t>(request.target_character_id))
        return Fail(out, "sway_completion_instance_join_unavailable");
      out.owner_matches_actor = out.native_owner_raw == static_cast<std::uint32_t>(request.actor_character_id);
      out.owner_cleared = out.native_owner_raw == 0xFFFFFFFFu;
      if (!out.owner_matches_actor && !(out.owner_cleared && out.native_status_raw == 1))
        return Fail(out, "sway_completion_native_owner_mismatch");
      out.instance_present = true; out.exact_instance_join_ready = true;
      out.native_status_observed = true;
      out.native_status_key = out.native_status_raw == 0 ? "continue" :
          out.native_status_raw == 1 ? "invalidated" :
          out.native_status_raw == 2 ? "invalid" : "unknown";
      out.native_terminal_state_observed = out.native_status_raw == 1;
      if (out.native_status_raw == 0) {
        if (!Chance(b.success_chance, scheme, out.native_success_chance_raw))
          return Fail(out, "sway_completion_current_chance_unavailable");
        out.native_success_chance_observed = true;
      }
    }
  }
  CoreSnapshotPrefix after{};
  if (!Core(b.core, after) || !SameFrame(frame, after))
    return Fail(out, "sway_completion_frame_changed");
  out.available = true; return true;
}
} // namespace

SwayCompletionBindings12002 BindSwayCompletionImage12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  SwayCompletionBindings12002 b{};
  b.core = BindCoreImage(base, sha);
  if (!b.core.enabled) return b;
  b.enabled = true; b.image_base = base;
  b.success_chance = reinterpret_cast<SwayCompletionSuccessChance12002>(
      base + kSwayCompletionSuccessChanceRva12002);
  return b;
}
bool ReadSwayCompletion12002(const SwayCompletionBindings12002 &b,
    const SwayCompletionRequestV1 &request, SwayCompletionStateV1 &output) noexcept {
  output = {}; output.request = request;
  if (!b.enabled || !b.core.enabled || !b.image_base || !request.expected_revision ||
      request.actor_character_id <= 0 || request.target_character_id <= 0 ||
      request.actor_character_id == request.target_character_id || request.scheme_id == 0xFFFFFFFFu)
    return Fail(output, "sway_completion_build_or_request_unavailable");
  try {
    SwayCompletionStateV1 first{}, second{};
    if (!ReadOnce(b, request, first)) { output = std::move(first); return false; }
    if (!ReadOnce(b, request, second)) { output = std::move(second); return false; }
    if (first != second) return Fail(output, "sway_completion_source_changed");
    output = std::move(second); return true;
  } catch (...) { return Fail(output, "sway_completion_internal_error"); }
}

} // namespace xar::ck3_12002
