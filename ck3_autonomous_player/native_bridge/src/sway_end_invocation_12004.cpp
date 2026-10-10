#include "xar_bridge/sway_end_invocation_12004.hpp"

#include <cstring>
#include <windows.h>

namespace xar::ck3_12004 {
namespace {
bool Copy(std::uintptr_t address, void *output, std::size_t size) noexcept {
  if (!address || !output) return false;
  __try {
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
template <class T> bool Read(std::uintptr_t address, T &output) noexcept {
  return Copy(address, &output, sizeof(output));
}
bool Frame(const CoreBindings &bindings, CoreSnapshotPrefix &output) noexcept {
  __try { return ck3_12004::ReadCoreSnapshot(bindings, output); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool ValidStamp(const SwayEndInvocationStamp12004 &stamp) noexcept {
  return stamp.observer_session_identity != 0 && stamp.invocation_id != 0 &&
         stamp.owner_thread_id == GetCurrentThreadId();
}
bool IsSway(std::uintptr_t type,
            const SwayEndInvocationBindings12004 &bindings) noexcept {
  std::uintptr_t table{}, text{};
  std::uint64_t length{}, capacity{};
  std::uint32_t marker{};
  std::array<char, 4> key{};
  if (!type || !Read(type, table) ||
      table != bindings.image_base + bindings.state.type_vtable_rva ||
      !Read(type + 0x28, length) || length != 4 ||
      !Read(type + 0x30, capacity) || capacity < length ||
      !Read(type + 0x38, marker) || marker != 0x4744624F) return false;
  text = type + 0x18;
  if (capacity >= 16 && (!Read(text, text) || !text)) return false;
  return Copy(text, key.data(), key.size()) &&
         std::memcmp(key.data(), "sway", key.size()) == 0;
}
struct Instance {
  bool present = false;
  bool reused = false;
  std::int32_t status = 0;
  std::uint32_t owner = 0xFFFFFFFFu;
  std::uint32_t target = 0xFFFFFFFFu;
};
bool ReadInstance(const SwayEndInvocationBindings12004 &bindings,
                  std::uint32_t full_id, Instance &output) noexcept {
  output = {};
  std::uintptr_t state{}, game{}, storage{}, slots{}, table{}, instance{}, type{};
  std::int32_t capacity{};
  const auto &profile = bindings.state;
  if (!Read(reinterpret_cast<std::uintptr_t>(profile.core.game_state_slot), state) || !state ||
      !Read(state + kGameStateDataOffset, game) || !game ||
      !Read(game + profile.manager_offset, table) ||
      table != bindings.image_base + profile.manager_vtable_rva ||
      !Read(game + profile.manager_offset + 0x20, storage) || !storage ||
      !Read(storage, table) || table != bindings.image_base + profile.storage_vtable_rva ||
      !Read(storage + 0x20, slots) || !Read(storage + 0x2C, capacity) || capacity < 0 ||
      (capacity > 0 && !slots)) return false;
  // The mask is used only to address a slot; the instance join is full32-bit.
  const auto index = full_id & 0x00FFFFFFu;
  if (index >= static_cast<std::uint32_t>(capacity)) return true;
  if (!Read(slots + static_cast<std::size_t>(index) * 0x10 + 8, instance)) return false;
  if (!instance) return true;
  std::uint32_t found_id{}, marker{}, target_kind{};
  if (!Read(instance + 0x10, found_id)) return false;
  if (found_id != full_id) { output.reused = true; return true; }
  if (!Read(instance, table) || table != bindings.image_base + profile.instance_vtable_rva ||
      !Read(instance + 0x14, marker) || marker != 0x5363686D ||
      !Read(instance + 0x20, type) || !IsSway(type, bindings) ||
      !Read(instance + 0x28, output.status) || !Read(instance + 0x2C, output.owner) ||
      !Read(instance + 0x30, target_kind) || target_kind != 0 ||
      !Read(instance + 0x34, output.target)) return false;
  output.present = true;
  return true;
}
bool Ready(const SwayEndInvocationBindings12004 &bindings) noexcept {
  return bindings.enabled && bindings.image_base && bindings.state.enabled &&
         bindings.state.core.enabled;
}
} // namespace

SwayEndInvocationBindings12004 BindSwayEndInvocationImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  SwayEndInvocationBindings12004 bindings{};
  bindings.state = BindSwayStateImage12004(image_base, executable_sha256);
  if (bindings.state.enabled) {
    bindings.enabled = true;
    bindings.image_base = image_base;
  }
  return bindings;
}

SwayEndCaptureResult12004 CaptureSwayEndBefore12004(
    const SwayEndInvocationBindings12004 &bindings,
    const SwayEndInvocationStamp12004 &stamp,
    SwayEndSourceClass12004 source_class, const void *native_self,
    const void *effect_context, SwayEndInvocation12004 &output) noexcept {
  output = {};
  output.stamp = stamp;
  if (!Ready(bindings) || !ValidStamp(stamp) || !native_self)
    return SwayEndCaptureResult12004::unavailable;
  const auto self = reinterpret_cast<std::uintptr_t>(native_self);
  std::uintptr_t table{};
  std::uint32_t full_id = 0xFFFFFFFFu;
  std::uint16_t root_kind{};
  if (!Read(self, table)) return SwayEndCaptureResult12004::unavailable;
  if (source_class == SwayEndSourceClass12004::end_scheme_command_execute) {
    std::uintptr_t primary{};
    if (table != bindings.image_base + kSwayEndCommandSecondaryVptr12004 || self < 0x18 ||
        !Read(self - 0x18, primary) ||
        primary != bindings.image_base + kSwayEndCommandPrimaryVptr12004)
      return SwayEndCaptureResult12004::ignored;
    if (!Read(self + 8, full_id)) return SwayEndCaptureResult12004::unavailable;
  } else if (source_class == SwayEndSourceClass12004::authored_end_scheme_false_execute ||
             source_class == SwayEndSourceClass12004::authored_end_scheme_true_execute) {
    const auto index = source_class == SwayEndSourceClass12004::authored_end_scheme_false_execute ? 0 : 1;
    if (table != bindings.image_base + kSwayEndEffectVptrRvas12004[index])
      return SwayEndCaptureResult12004::ignored;
    std::uintptr_t root{};
    if (!Read(reinterpret_cast<std::uintptr_t>(effect_context), root) || !root ||
        !Read(root, root_kind)) return SwayEndCaptureResult12004::unavailable;
    if (root_kind != 9) return SwayEndCaptureResult12004::ignored;
    if (!Read(root + 8, full_id)) return SwayEndCaptureResult12004::unavailable;
  } else return SwayEndCaptureResult12004::ignored;
  if (full_id == 0xFFFFFFFFu) return SwayEndCaptureResult12004::ignored;
  Instance before{};
  if (!ReadInstance(bindings, full_id, before)) return SwayEndCaptureResult12004::unavailable;
  if (!before.present || before.status != 0 || before.owner == 0xFFFFFFFFu ||
      before.target == 0xFFFFFFFFu) return SwayEndCaptureResult12004::ignored;
  output.pre_frame_observed = Frame(bindings.state.core, output.pre_frame);
  if (!output.pre_frame_observed || !output.pre_frame.map_ready ||
      !output.pre_frame.has_played_character || !output.pre_frame.played_character_alive)
    return SwayEndCaptureResult12004::unavailable;
  if (static_cast<std::uint32_t>(output.pre_frame.played_character_id) != before.owner)
    return SwayEndCaptureResult12004::ignored;
  auto &source = output.source;
  source.source_class = source_class;
  source.date_raw = output.pre_frame.clock.date_raw;
  source.actor_character_id = before.owner;
  source.target_character_id = before.target;
  source.scheme_id = full_id;
  source.input_root_scope_kind = root_kind;
  source.pre_status = before.status;
  source.pre_owner = before.owner;
  source.executing_source_observed = true;
  output.scheme_instance_generation = full_id >> 24;
  return SwayEndCaptureResult12004::captured;
}

bool CaptureSwayEndAfter12004(const SwayEndInvocationBindings12004 &bindings,
                            SwayEndInvocation12004 &output) noexcept {
  if (!Ready(bindings) || !ValidStamp(output.stamp) ||
      !output.source.executing_source_observed) return false;
  auto &source = output.source;
  source.post_read_succeeded = false;
  source.post_instance_present = false;
  source.post_storage_slot_reused = false;
  source.post_exact_instance_join_ready = false;
  source.post_status_observed = false;
  source.post_status = 0;
  source.post_owner = 0xFFFFFFFFu;
  source.native_terminal_state_observed = false;
  source.native_terminal_transition_observed = false;
  output.post_frame = {};
  // The frame read is independent of the instance read. Failure of either
  // is represented separately; no same-frame or causal assertion is made.
  output.post_frame_observed = Frame(bindings.state.core, output.post_frame);
  Instance after{};
  if (!ReadInstance(bindings, output.source.scheme_id, after)) return false;
  source.post_read_succeeded = true;
  source.post_instance_present = after.present;
  source.post_storage_slot_reused = after.reused;
  if (!after.present) return true;
  if (after.target != source.target_character_id ||
      (after.owner != source.actor_character_id &&
       !(after.status == 1 && after.owner == 0xFFFFFFFFu))) return true;
  source.post_exact_instance_join_ready = true;
  source.post_status_observed = true;
  source.post_status = after.status;
  source.post_owner = after.owner;
  source.native_terminal_state_observed = after.status == 1;
  source.native_terminal_transition_observed = source.pre_status == 0 && after.status == 1;
  return true;
}

SwayEndCaptureResult12004 ForwardSwayEndCommand12004(
    const SwayEndInvocationBindings12004 &bindings,
    const SwayEndInvocationStamp12004 &stamp,
    SwayEndNativeCommand12004 original, const void *secondary_this,
    SwayEndInvocation12004 &output) {
  if (!original) {
    output = {};
    output.stamp = stamp;
    return SwayEndCaptureResult12004::unavailable;
  }
  const auto result = CaptureSwayEndBefore12004(bindings, stamp,
      SwayEndSourceClass12004::end_scheme_command_execute, secondary_this, nullptr, output);
  output.original_forwarded_once = true;
  original(secondary_this);
  output.original_returned = true;
  if (result == SwayEndCaptureResult12004::captured)
    (void)CaptureSwayEndAfter12004(bindings, output);
  return result;
}
SwayEndCaptureResult12004 ForwardSwayEndEffect12004(
    const SwayEndInvocationBindings12004 &bindings,
    const SwayEndInvocationStamp12004 &stamp,
    SwayEndSourceClass12004 source_class, SwayEndNativeEffect12004 original,
    const void *effect, const void *effect_context, SwayEndInvocation12004 &output) {
  if (!original) {
    output = {};
    output.stamp = stamp;
    return SwayEndCaptureResult12004::unavailable;
  }
  const auto result = CaptureSwayEndBefore12004(bindings, stamp, source_class,
      effect, effect_context, output);
  output.original_forwarded_once = true;
  original(effect, effect_context);
  output.original_returned = true;
  if (result == SwayEndCaptureResult12004::captured)
    (void)CaptureSwayEndAfter12004(bindings, output);
  return result;
}
} // namespace xar::ck3_12004
