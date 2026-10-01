#include "xar_bridge/ck3_12002_sway_completion_termination.hpp"

#include <atomic>
#include <cstring>
#include <sstream>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
constexpr std::uintptr_t manager_offset = 0xA5C0;
constexpr std::uintptr_t manager_vtable = 0x4779538;
constexpr std::uintptr_t storage_vtable = 0x4779828;
constexpr std::uintptr_t scheme_vtable = 0x47794E8;
constexpr std::uintptr_t type_vtable = 0x48B9F20;
constexpr std::uintptr_t command_primary = 0x476ED30;
constexpr std::uintptr_t command_secondary = 0x476EB70;
constexpr std::array<std::uintptr_t, 2> effect_vtables{0x48521B0, 0x4852B68};
bool Copy(std::uintptr_t p, void *out, std::size_t size) noexcept {
  if (!p || !out) return false;
  __try { std::memcpy(out, reinterpret_cast<const void *>(p), size); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
template <typename T> bool Read(std::uintptr_t p, T &out) noexcept {
  return Copy(p, &out, sizeof(out));
}
bool Core(const CoreBindings &b, CoreSnapshotPrefix &out) noexcept {
  __try { return ReadCoreSnapshot(b, out); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool IsSway(std::uintptr_t type, std::uintptr_t base) noexcept {
  std::uintptr_t table{}, text{};
  std::uint64_t length{}, capacity{};
  std::uint32_t marker{};
  std::array<char, 4> key{};
  if (!type || !Read(type, table) || table != base + type_vtable ||
      !Read(type + 0x28, length) || length != 4 ||
      !Read(type + 0x30, capacity) || capacity < length ||
      !Read(type + 0x38, marker) || marker != 0x4744624F) return false;
  text = type + 0x18;
  if (capacity >= 16 && (!Read(text, text) || !text)) return false;
  return Copy(text, key.data(), key.size()) && std::memcmp(key.data(), "sway", 4) == 0;
}
struct Instance {
  bool present = false;
  bool reused = false;
  std::int32_t status = 0;
  std::uint32_t owner = 0xFFFFFFFFu;
  std::uint32_t target = 0xFFFFFFFFu;
};
bool ReadInstance(const SwayTerminationBindings12002 &b, std::uint32_t id,
                  Instance &out) noexcept {
  out = {};
  std::uintptr_t state{}, game{}, storage{}, slots{}, table{}, scheme{}, type{};
  std::int32_t capacity{};
  if (!Read(reinterpret_cast<std::uintptr_t>(b.core.game_state_slot), state) || !state ||
      !Read(state + 0xA0, game) || !game ||
      !Read(game + manager_offset, table) || table != b.image_base + manager_vtable ||
      !Read(game + manager_offset + 0x20, storage) || !storage ||
      !Read(storage, table) || table != b.image_base + storage_vtable ||
      !Read(storage + 0x20, slots) || !Read(storage + 0x2C, capacity) || capacity < 0 ||
      (capacity > 0 && !slots)) return false;
  const auto index = id & 0x00FFFFFFu;
  if (index >= static_cast<std::uint32_t>(capacity)) return true;
  if (!Read(slots + static_cast<std::size_t>(index) * 0x10 + 8, scheme)) return false;
  if (!scheme) return true;
  std::uint32_t found_id{}, marker{}, kind{};
  if (!Read(scheme + 0x10, found_id)) return false;
  if (found_id != id) { out.reused = true; return true; }
  if (!Read(scheme, table) || table != b.image_base + scheme_vtable ||
      !Read(scheme + 0x14, marker) || marker != 0x5363686D ||
      !Read(scheme + 0x20, type) || !IsSway(type, b.image_base) ||
      !Read(scheme + 0x28, out.status) || !Read(scheme + 0x2C, out.owner) ||
      !Read(scheme + 0x30, kind) || kind != 0 || !Read(scheme + 0x34, out.target)) return false;
  out.present = true;
  return true;
}
std::atomic<SwayTerminationInstall12002 *> observer{nullptr};
std::array<std::uintptr_t, 3> native_originals{};

void Invoke(std::size_t index, const void *self, const void *context) {
  auto *const state = observer.load(std::memory_order_acquire);
  SwayTerminationSource12002 source;
  bool captured = false;
  if (state && state->attached && state->recorder) {
    const auto source_class = index == 0 ? SwayTerminationSourceClass12002::end_scheme_command_execute :
        index == 1 ? SwayTerminationSourceClass12002::authored_end_scheme_false_execute :
                     SwayTerminationSourceClass12002::authored_end_scheme_true_execute;
    captured = CaptureSwayTerminationBefore12002(state->bindings, source_class, self, context, source) ==
        SwayTerminationCaptureResult12002::captured;
  }
  // Capture failures and non-Sway inputs never skip the original Execute.
  const auto original = native_originals[index];
  if (original) {
    if (index == 0) reinterpret_cast<SwayTerminationNativeCommand12002>(original)(self);
    else reinterpret_cast<SwayTerminationNativeEffect12002>(original)(self, context);
  }
  if (captured && state && state->attached && state->recorder) {
    (void)CaptureSwayTerminationAfter12002(state->bindings, source);
    (void)state->recorder->Append(source);
  }
}
void Command(const void *self) { Invoke(0, self, nullptr); }
void EffectFalse(const void *self, const void *context) { Invoke(1, self, context); }
void EffectTrue(const void *self, const void *context) { Invoke(2, self, context); }
const std::array<std::uintptr_t, 3> wrappers{
    reinterpret_cast<std::uintptr_t>(&Command), reinterpret_cast<std::uintptr_t>(&EffectFalse),
    reinterpret_cast<std::uintptr_t>(&EffectTrue)};
bool WriteSlot(std::uintptr_t *slot, std::uintptr_t expected,
               std::uintptr_t replacement, bool &changed) noexcept {
  changed = false;
  DWORD previous{};
  if (!slot || !VirtualProtect(slot, sizeof(*slot), PAGE_READWRITE, &previous)) return false;
  const auto found = InterlockedCompareExchangePointer(
      reinterpret_cast<void *volatile *>(slot), reinterpret_cast<void *>(replacement),
      reinterpret_cast<void *>(expected));
  changed = found == reinterpret_cast<void *>(expected);
  DWORD ignored{};
  const bool restored = VirtualProtect(slot, sizeof(*slot), previous, &ignored) != FALSE;
  return changed && restored;
}
bool Install(const SwayTerminationBindings12002 &bindings,
             const std::array<std::uintptr_t *, 3> &slots,
             const std::array<std::uintptr_t, 3> &originals,
             SwayTerminationRecorder12002 &recorder,
             SwayTerminationInstall12002 &state, bool fixture) noexcept {
  if (observer.load(std::memory_order_acquire) || state.attached) {
    state.unavailable_reason = "sway_termination_observer_already_installed"; return false;
  }
  if (!bindings.enabled || !bindings.core.enabled || !bindings.image_base) {
    state.unavailable_reason = "sway_termination_install_unsupported_build"; return false;
  }
  for (std::size_t i = 0; i < slots.size(); ++i) {
    std::uintptr_t found{};
    if (!originals[i] || !Read(reinterpret_cast<std::uintptr_t>(slots[i]), found) || found != originals[i]) {
      state.unavailable_reason = "sway_termination_install_native_slot_mismatch"; return false;
    }
  }
  state.bindings = bindings; state.recorder = &recorder;
  state.slots = slots; state.originals = originals; state.fixture_slots = fixture;
  native_originals = originals;
  recorder.SetObserverAttached(false);
  observer.store(&state, std::memory_order_release);
  for (std::size_t i = 0; i < slots.size(); ++i) {
    bool changed{};
    const bool written = WriteSlot(slots[i], originals[i], wrappers[i], changed);
    state.patched[i] = changed;
    if (!written) {
      (void)UninstallSwayCompletionTermination12002(state);
      state.unavailable_reason = "sway_termination_install_slot_write_failed"; return false;
    }
  }
  state.attached = true; state.unavailable_reason = ""; recorder.SetObserverAttached(true);
  return true;
}
} // namespace

SwayTerminationBindings12002 BindSwayTerminationImage12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  SwayTerminationBindings12002 b{};
  b.core = BindCoreImage(base, sha);
  if (b.core.enabled) { b.enabled = true; b.image_base = base; }
  return b;
}
SwayTerminationCaptureResult12002 CaptureSwayTerminationBefore12002(
    const SwayTerminationBindings12002 &b, SwayTerminationSourceClass12002 source_class,
    const void *native_self, const void *effect_context, SwayTerminationSource12002 &out) noexcept {
  out = {};
  if (!b.enabled || !b.core.enabled || !b.image_base || !native_self)
    return SwayTerminationCaptureResult12002::unavailable;
  const auto self = reinterpret_cast<std::uintptr_t>(native_self);
  std::uintptr_t table{};
  std::uint32_t id = 0xFFFFFFFFu;
  std::uint16_t root_kind{};
  if (!Read(self, table)) return SwayTerminationCaptureResult12002::unavailable;
  if (source_class == SwayTerminationSourceClass12002::end_scheme_command_execute) {
    std::uintptr_t primary{};
    if (table != b.image_base + command_secondary || self < 0x18 ||
        !Read(self - 0x18, primary) || primary != b.image_base + command_primary)
      return SwayTerminationCaptureResult12002::ignored;
    if (!Read(self + 8, id)) return SwayTerminationCaptureResult12002::unavailable;
  } else if (source_class == SwayTerminationSourceClass12002::authored_end_scheme_false_execute ||
             source_class == SwayTerminationSourceClass12002::authored_end_scheme_true_execute) {
    const auto index = source_class == SwayTerminationSourceClass12002::authored_end_scheme_false_execute ? 0 : 1;
    if (table != b.image_base + effect_vtables[index]) return SwayTerminationCaptureResult12002::ignored;
    std::uintptr_t root{};
    const auto context = reinterpret_cast<std::uintptr_t>(effect_context);
    if (!Read(context, root) || !root || !Read(root, root_kind))
      return SwayTerminationCaptureResult12002::unavailable;
    if (root_kind != 9) return SwayTerminationCaptureResult12002::ignored;
    if (!Read(root + 8, id)) return SwayTerminationCaptureResult12002::unavailable;
  } else return SwayTerminationCaptureResult12002::ignored;
  if (id == 0xFFFFFFFFu) return SwayTerminationCaptureResult12002::ignored;
  Instance before;
  if (!ReadInstance(b, id, before)) return SwayTerminationCaptureResult12002::unavailable;
  if (!before.present || before.status != 0 || before.owner == 0xFFFFFFFFu || before.target == 0xFFFFFFFFu)
    return SwayTerminationCaptureResult12002::ignored;
  CoreSnapshotPrefix frame{};
  if (!Core(b.core, frame) || !frame.map_ready || !frame.has_played_character || !frame.played_character_alive)
    return SwayTerminationCaptureResult12002::unavailable;
  if (static_cast<std::uint32_t>(frame.played_character_id) != before.owner)
    return SwayTerminationCaptureResult12002::ignored;
  out.source_class = source_class; out.date_raw = frame.clock.date_raw;
  out.actor_character_id = before.owner; out.target_character_id = before.target; out.scheme_id = id;
  out.input_root_scope_kind = root_kind; out.pre_status = before.status; out.pre_owner = before.owner;
  out.executing_source_observed = true;
  return SwayTerminationCaptureResult12002::captured;
}
bool CaptureSwayTerminationAfter12002(const SwayTerminationBindings12002 &b,
                                    SwayTerminationSource12002 &out) noexcept {
  if (!out.executing_source_observed) return false;
  Instance after;
  if (!ReadInstance(b, out.scheme_id, after)) return false;
  out.post_read_succeeded = true; out.post_instance_present = after.present;
  out.post_storage_slot_reused = after.reused;
  if (!after.present) return true;
  if (after.target != out.target_character_id ||
      (after.owner != out.actor_character_id && !(after.status == 1 && after.owner == 0xFFFFFFFFu))) return true;
  out.post_exact_instance_join_ready = true; out.post_status_observed = true;
  out.post_status = after.status; out.post_owner = after.owner;
  out.native_terminal_state_observed = after.status == 1;
  out.native_terminal_transition_observed = out.pre_status == 0 && after.status == 1;
  return true;
}
void SwayTerminationRecorder12002::SetObserverAttached(bool attached) noexcept { attached_ = attached; }
bool SwayTerminationRecorder12002::ObserverAttached() const noexcept { return attached_; }
bool SwayTerminationRecorder12002::Append(const SwayTerminationSource12002 &source) noexcept {
  if (!attached_ || !source.executing_source_observed || source.source_class == SwayTerminationSourceClass12002::none)
    return false;
  const auto at = (first_ + count_) % records_.size();
  records_[at] = {next_sequence_++, source};
  if (count_ < records_.size()) ++count_; else first_ = (first_ + 1) % records_.size();
  return true;
}
bool SwayTerminationRecorder12002::Query(const SwayTerminationQuery12002 &request,
                                       SwayTerminationQueryResult12002 &out) const noexcept {
  out = {}; out.request = request; out.observer_attached = attached_;
  try {
    if (!attached_) { out.unavailable_reason = "sway_termination_observer_not_attached"; return false; }
    if (request.actor_character_id == 0xFFFFFFFFu || request.target_character_id == 0xFFFFFFFFu ||
        request.scheme_id == 0xFFFFFFFFu) {
      out.unavailable_reason = "sway_termination_query_identity_unavailable"; return false;
    }
    if (count_) {
      out.earliest_sequence = records_[first_].sequence;
      out.latest_sequence = records_[(first_ + count_ - 1) % records_.size()].sequence;
      out.retention_gap = request.after_sequence != 0 && request.after_sequence < out.earliest_sequence - 1;
    }
    for (std::size_t i = 0; i < count_; ++i) {
      const auto &record = records_[(first_ + i) % records_.size()];
      if (record.sequence > request.after_sequence && record.source.actor_character_id == request.actor_character_id &&
          record.source.target_character_id == request.target_character_id && record.source.scheme_id == request.scheme_id)
        out.records.push_back(record);
    }
    out.available = true; return true;
  } catch (...) { out.available = false; out.records.clear(); out.unavailable_reason = "sway_termination_query_internal_error"; return false; }
}
const char *SwayTerminationSourceKey12002(SwayTerminationSourceClass12002 source) noexcept {
  switch (source) {
  case SwayTerminationSourceClass12002::end_scheme_command_execute: return "end_scheme_command_execute";
  case SwayTerminationSourceClass12002::authored_end_scheme_false_execute: return "authored_end_scheme_false_execute";
  case SwayTerminationSourceClass12002::authored_end_scheme_true_execute: return "authored_end_scheme_true_execute";
  default: return "none";
  }
}
std::string SerializeSwayCompletionTermination12002(const SwayTerminationQueryResult12002 &r) {
  std::ostringstream out;
  out << "{\"schema\":\"xar.ck3.sway-completion-termination.v1\",\"available\":" << (r.available ? "true" : "false")
      << ",\"unavailable_reason\":\"" << r.unavailable_reason << "\",\"read_only\":true,\"observer_attached\":"
      << (r.observer_attached ? "true" : "false") << ",\"actor_character_id\":" << r.request.actor_character_id
      << ",\"target_character_id\":" << r.request.target_character_id << ",\"scheme_instance_id\":" << r.request.scheme_id
      << ",\"after_sequence\":" << r.request.after_sequence << ",\"earliest_sequence\":" << r.earliest_sequence
      << ",\"latest_sequence\":" << r.latest_sequence << ",\"retention_gap\":" << (r.retention_gap ? "true" : "false")
      << ",\"session_records_only\":true,\"material_effect_observed\":false,\"records\":[";
  bool first = true;
  for (const auto &record : r.records) {
    if (!first) out << ',';
    first = false;
    const auto &s = record.source;
    out << "{\"sequence\":" << record.sequence << ",\"source_class\":\"" << SwayTerminationSourceKey12002(s.source_class)
        << "\",\"date_raw\":" << s.date_raw << ",\"actor_character_id\":" << s.actor_character_id
        << ",\"target_character_id\":" << s.target_character_id << ",\"scheme_instance_id\":" << s.scheme_id
        << ",\"scheme_instance_generation\":" << (s.scheme_id >> 24) << ",\"input_root_scope_kind\":" << s.input_root_scope_kind
        << ",\"executing_source_observed\":" << (s.executing_source_observed ? "true" : "false")
        << ",\"pre_status\":" << s.pre_status << ",\"pre_owner\":" << s.pre_owner
        << ",\"post_read_succeeded\":" << (s.post_read_succeeded ? "true" : "false")
        << ",\"post_instance_present\":" << (s.post_instance_present ? "true" : "false")
        << ",\"post_storage_slot_reused\":" << (s.post_storage_slot_reused ? "true" : "false")
        << ",\"post_exact_instance_join_ready\":" << (s.post_exact_instance_join_ready ? "true" : "false")
        << ",\"post_status_observed\":" << (s.post_status_observed ? "true" : "false") << ",\"post_status\":";
    if (s.post_status_observed) out << s.post_status; else out << "null";
    out << ",\"post_owner\":";
    if (s.post_status_observed) out << s.post_owner; else out << "null";
    out << ",\"native_terminal_state_observed\":" << (s.native_terminal_state_observed ? "true" : "false")
        << ",\"native_terminal_transition_observed\":" << (s.native_terminal_transition_observed ? "true" : "false")
        << ",\"material_effect_observed\":false,\"specific_invalidation_reason\":null}";
  }
  out << "]}"; return out.str();
}
bool InstallSwayCompletionTermination12002(std::uintptr_t base, std::string_view sha,
    SwayTerminationRecorder12002 &recorder, SwayTerminationInstall12002 &state) noexcept {
  const auto b = BindSwayTerminationImage12002(base, sha);
  if (!b.enabled) { state.unavailable_reason = "sway_termination_install_unsupported_build"; return false; }
  std::array<std::uintptr_t *, 3> slots{};
  std::array<std::uintptr_t, 3> originals{};
  for (std::size_t i = 0; i < slots.size(); ++i) {
    slots[i] = reinterpret_cast<std::uintptr_t *>(base + kSwayTerminationSlotRvas12002[i]);
    originals[i] = base + kSwayTerminationExecuteRvas12002[i];
  }
  return Install(b, slots, originals, recorder, state, false);
}
bool InstallSwayCompletionTerminationFixture12002(const SwayTerminationBindings12002 &b,
    const std::array<std::uintptr_t *, 3> &slots, const std::array<std::uintptr_t, 3> &originals,
    SwayTerminationRecorder12002 &recorder, SwayTerminationInstall12002 &state) noexcept {
  return Install(b, slots, originals, recorder, state, true);
}
bool UninstallSwayCompletionTermination12002(SwayTerminationInstall12002 &state) noexcept {
  auto *const current = observer.load(std::memory_order_acquire);
  if (current && current != &state) { state.unavailable_reason = "sway_termination_install_state_not_owner"; return false; }
  state.attached = false;
  if (state.recorder) state.recorder->SetObserverAttached(false);
  bool complete = true;
  for (std::size_t i = 0; i < state.slots.size(); ++i) {
    if (!state.patched[i]) continue;
    bool changed{};
    const bool written = WriteSlot(state.slots[i], wrappers[i], state.originals[i], changed);
    if (changed) state.patched[i] = false;
    complete = complete && written;
  }
  if (complete) { observer.store(nullptr, std::memory_order_release); state.unavailable_reason = "sway_termination_observer_not_installed"; }
  else state.unavailable_reason = "sway_termination_uninstall_slot_restore_failed";
  return complete;
}
} // namespace xar::ck3_12002
