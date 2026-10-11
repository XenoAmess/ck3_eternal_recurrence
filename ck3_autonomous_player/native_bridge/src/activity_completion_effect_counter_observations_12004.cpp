#include "xar_bridge/activity_completion_effect_counter_observations_12004.hpp"

#include <windows.h>

#include <atomic>
#include <limits>

namespace xar::ck3_12004 {
namespace {

struct Journal {
  std::atomic<bool> configured{false};
  std::atomic<bool> attached{false};
  std::atomic<const char *> reason{
      "activity_completion_effect_counter_observer_unavailable"};
  std::atomic<std::uint32_t> owner_thread{0};
  std::uintptr_t module_base = 0;
  std::uintptr_t type_vtable = 0;
  void *context = nullptr;
  ActivityTerminalReadMemory12004 read_memory = nullptr;
  ActivityTerminalReadFrame12004 read_frame = nullptr;
  std::uint64_t latest_sequence = 0;
  std::uint64_t overflow_dropped_count = 0;
  std::uint64_t pairing_dropped_count = 0;
  std::size_t first = 0;
  std::size_t count = 0;
  std::array<ActivityCompletionEffectCounterObservation12004,
             kActivityCompletionEffectCounterCapacity12004> records{};
};

Journal g_journal;

struct Pending {
  bridge::ActivityCompletionEffectOperands12004 operands{};
  ActivityCompletionEffectCounterFace12004 before{};
};
struct PendingList {
  std::array<Pending, 16> items{};
  std::size_t count = 0;
};
thread_local PendingList g_pending;

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &address) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  address = base + offset;
  return true;
}

template <typename T>
bool ReadAt(const Journal &journal, std::uintptr_t base, std::size_t offset,
            T &output) noexcept {
  std::uintptr_t address = 0;
  T copied{};
  if (!Add(base, offset, address) || journal.read_memory == nullptr ||
      !journal.read_memory(journal.context, address, &copied, sizeof(copied)))
    return false;
  output = copied;
  return true;
}

bool Owner(Journal &journal, std::uint32_t thread) noexcept {
  std::uint32_t unbound = 0;
  journal.owner_thread.compare_exchange_strong(unbound, thread,
                                               std::memory_order_acq_rel);
  return thread != 0 &&
      journal.owner_thread.load(std::memory_order_acquire) == thread;
}

bool TypeKey(const Journal &journal,
             ActivityCompletionEffectCounterFace12004 &face) noexcept {
  std::uintptr_t vtable = 0, data = 0;
  std::uint64_t size = 0, capacity = 0;
  if (!face.type_observed || face.type_identity == 0 ||
      !ReadAt(journal, face.type_identity, 0, vtable) ||
      vtable != journal.type_vtable ||
      !ReadAt(journal, face.type_identity, 0x28, size) ||
      !ReadAt(journal, face.type_identity, 0x30, capacity) || size == 0 ||
      size > capacity || size >= face.type_key.size() ||
      !Add(face.type_identity, 0x18, data))
    return false;
  if (capacity > 15 && !ReadAt(journal, face.type_identity, 0x18, data))
    return false;
  if (data == 0 || !journal.read_memory(journal.context, data,
                                       face.type_key.data(),
                                       static_cast<std::size_t>(size)))
    return false;
  for (std::size_t i = 0; i < size; ++i) {
    const char ch = face.type_key[i];
    if (!((ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '_'))
      return false;
  }
  face.type_key_size = static_cast<std::uint8_t>(size);
  return true;
}

ActivityCompletionEffectCounterFace12004 ReadFace(
    const Journal &journal,
    const bridge::ActivityCompletionEffectOperands12004 &operands,
    bool require_owned_entry = false) noexcept {
  ActivityCompletionEffectCounterFace12004 face{};
  ActivityTerminalCaptureFrame12004 frame{};
  if (journal.read_frame != nullptr && journal.read_frame(journal.context, frame) &&
      frame.owner_thread_id == operands.thread_id &&
      frame.owner_thread_id == GetCurrentThreadId() && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive) {
    face.frame_observed = true;
    face.frame = frame;
  }
  face.participant_full_id_observed =
      ReadAt(journal, operands.participant, 0x18, face.participant_full_id);
  if (require_owned_entry &&
      (!face.frame_observed || !face.participant_full_id_observed ||
       face.participant_full_id == 0xFFFFFFFFU ||
       face.participant_full_id !=
           static_cast<std::uint32_t>(face.frame.actor_character_id)))
    return face;
  // No preceding face/read failure substitutes a value for another raw load.
  face.activity_full_id_observed =
      ReadAt(journal, operands.activity, 0x8, face.activity_full_id);
  face.host_observed =
      ReadAt(journal, operands.activity, 0x3A8, face.host_character_id);
  face.type_observed =
      ReadAt(journal, operands.activity, 0x3A0, face.type_identity);
  face.type_key_observed = TypeKey(journal, face);
  if (require_owned_entry &&
      (!face.activity_full_id_observed || face.activity_full_id == 0xFFFFFFFFU ||
       !face.host_observed || !face.type_key_observed ||
       std::string_view(face.type_key.data(), face.type_key_size) != "activity_feast"))
    return face;
  face.resource_extension_observed = ReadAt(
      journal, operands.participant, 0x1B0, face.resource_extension_identity);
  if (face.resource_extension_observed) {
    if (face.resource_extension_identity == 0) {
      // Source-defined null-extension zero domain; unread is never zero.
      face.prestige_observed = true;
      face.stress_observed = true;
    } else {
      face.prestige_observed = ReadAt(journal, face.resource_extension_identity,
                                      0x130, face.prestige_raw);
      face.stress_observed = ReadAt(journal, face.resource_extension_identity,
                                    0x2F8, face.stress_raw);
    }
  }
  // Existing XP Sample invokes TraitDB/native track getters; no such call here.
  return face;
}

const char *KnownObservationScope(
    const bridge::ActivityCompletionEffectOperands12004 &operands) noexcept {
  if (operands.source_call_rva == 0x23F6B82 &&
      operands.source_return_rva == 0x23F6B87 &&
      operands.source_after_cut_rva == 0x23F6B87 &&
      operands.intervening_call_rva == 0 &&
      operands.intervening_callee_rva == 0) {
    return "original_completion_call";
  }
  if (operands.source_call_rva == 0x23F6B9A &&
      operands.source_return_rva == 0x23F6B9F &&
      operands.source_after_cut_rva == 0x23F6BA7 &&
      operands.intervening_call_rva == 0x23F6BA2 &&
      operands.intervening_callee_rva == 0x28BEF00) {
    return "original_completion_call_and_following_native_call";
  }
  return nullptr;
}

bool SameOperands(const bridge::ActivityCompletionEffectOperands12004 &a,
                  const bridge::ActivityCompletionEffectOperands12004 &b) noexcept {
  return a.invocation_sequence == b.invocation_sequence &&
      a.source_call_rva == b.source_call_rva &&
      a.source_return_rva == b.source_return_rva &&
      a.source_after_cut_rva == b.source_after_cut_rva &&
      a.intervening_call_rva == b.intervening_call_rva &&
      a.intervening_callee_rva == b.intervening_callee_rva &&
      a.thread_id == b.thread_id && a.activity == b.activity &&
      a.participant == b.participant && a.effect == b.effect &&
      a.native_context == b.native_context &&
      a.original_parent_rsp == b.original_parent_rsp;
}

bool CallbacksAdmitted(const Journal *journal,
    const bridge::ActivityCompletionEffectOperands12004 &operands) noexcept {
  return journal == &g_journal &&
      journal->configured.load(std::memory_order_acquire) &&
      journal->attached.load(std::memory_order_acquire) &&
      operands.activity != 0 && operands.participant != 0 &&
      operands.effect != 0 && operands.native_context != 0 &&
      operands.original_parent_rsp != 0 && operands.invocation_sequence != 0 &&
      operands.thread_id != 0 && operands.thread_id == GetCurrentThreadId() &&
      KnownObservationScope(operands) != nullptr;
}

void Before(void *opaque,
            const bridge::ActivityCompletionEffectOperands12004 &operands) noexcept {
  auto *journal = static_cast<Journal *>(opaque);
  if (!CallbacksAdmitted(journal, operands)) return;
  const auto face = ReadFace(*journal, operands, true);
  if (!face.frame_observed || !face.activity_full_id_observed ||
      face.activity_full_id == 0xFFFFFFFFU || !face.host_observed ||
      !face.type_key_observed ||
      std::string_view(face.type_key.data(), face.type_key_size) != "activity_feast" ||
      !face.participant_full_id_observed || face.participant_full_id == 0xFFFFFFFFU ||
      face.participant_full_id !=
          static_cast<std::uint32_t>(face.frame.actor_character_id) ||
      !Owner(*journal, operands.thread_id) ||
      !journal->attached.load(std::memory_order_acquire))
    return;
  if (g_pending.count == g_pending.items.size()) {
    for (std::size_t i = 1; i < g_pending.count; ++i)
      g_pending.items[i-1] = g_pending.items[i];
    --g_pending.count;
    ++journal->pairing_dropped_count;
  }
  g_pending.items[g_pending.count++] = {operands, face};
}

void After(void *opaque,
           const bridge::ActivityCompletionEffectOperands12004 &operands) noexcept {
  auto *journal = static_cast<Journal *>(opaque);
  if (!CallbacksAdmitted(journal, operands) ||
      journal->owner_thread.load(std::memory_order_acquire) != operands.thread_id)
    return;
  std::size_t matched = g_pending.count;
  for (std::size_t i = g_pending.count; i != 0; --i)
    if (SameOperands(g_pending.items[i-1].operands, operands)) {
      matched = i-1;
      break;
    }
  // An unqualified before or an evicted pair cannot supply entry values.
  if (matched == g_pending.count) return;
  const auto before = g_pending.items[matched].before;
  for (std::size_t i = matched+1; i < g_pending.count; ++i)
    g_pending.items[i-1] = g_pending.items[i];
  --g_pending.count;
  const auto after = ReadFace(*journal, operands);
  if (!journal->attached.load(std::memory_order_acquire) ||
      journal->latest_sequence == (std::numeric_limits<std::uint64_t>::max)())
    return;
  ActivityCompletionEffectCounterObservation12004 record{};
  record.capture_sequence = ++journal->latest_sequence;
  record.observer_invocation_sequence = operands.invocation_sequence;
  record.capture_thread_id = operands.thread_id;
  record.activity_identity = operands.activity;
  record.participant_identity = operands.participant;
  record.effect_identity = operands.effect;
  record.native_context_identity = operands.native_context;
  record.original_parent_rsp = operands.original_parent_rsp;
  // Genuine before pairs with the last-native return marker at the
  // descriptor-qualified after cut; bypass post never calls this seam.
  record.original_call_return_observed = true;
  record.source_call_rva = operands.source_call_rva;
  record.source_return_rva = operands.source_return_rva;
  record.source_after_cut_rva = operands.source_after_cut_rva;
  record.intervening_call_rva = operands.intervening_call_rva;
  record.intervening_callee_rva = operands.intervening_callee_rva;
  record.observation_scope = KnownObservationScope(operands);
  record.before = before;
  record.after = after;
  record.same_activity_full_id_observed =
      before.activity_full_id_observed && after.activity_full_id_observed;
  record.same_activity_full_id = record.same_activity_full_id_observed &&
      before.activity_full_id == after.activity_full_id;
  record.same_participant_full_id_observed =
      before.participant_full_id_observed && after.participant_full_id_observed;
  record.same_participant_full_id = record.same_participant_full_id_observed &&
      before.participant_full_id == after.participant_full_id;
  std::size_t slot = (journal->first + journal->count) % journal->records.size();
  if (journal->count == journal->records.size()) {
    slot = journal->first;
    journal->first = (journal->first+1) % journal->records.size();
    ++journal->overflow_dropped_count;
  } else {
    ++journal->count;
  }
  journal->records[slot] = record;
}

const char *Reason(const Journal &journal) noexcept {
  const char *reason = journal.reason.load(std::memory_order_acquire);
  return reason != nullptr && reason[0] != '\0' ? reason :
      "activity_completion_effect_counter_observer_unavailable";
}

} // namespace

bool BuildActivityCompletionEffectCounterObservations12004Environment(
    std::uintptr_t module_base, std::string_view executable_sha256,
    void *callback_context, ActivityTerminalReadMemory12004 read_memory,
    ActivityTerminalReadFrame12004 read_frame,
    ActivityCompletionEffectCounterObserver12004Environment &output) noexcept {
  output = {};
  std::uintptr_t vtable = 0;
  if (!bridge::IsActivity12004BuildV1(executable_sha256) || module_base == 0 ||
      read_memory == nullptr || read_frame == nullptr ||
      !Add(module_base, bridge::ActivityHostedCrozierRvaV1(executable_sha256,
              bridge::kActivityHosted12002ActivityTypeVtableRva), vtable))
    return false;
  if (g_journal.configured.load(std::memory_order_acquire)) {
    if (g_journal.module_base != module_base || g_journal.context != callback_context ||
        g_journal.read_memory != read_memory || g_journal.read_frame != read_frame)
      return false;
  } else {
    g_journal.module_base = module_base;
    g_journal.type_vtable = vtable;
    g_journal.context = callback_context;
    g_journal.read_memory = read_memory;
    g_journal.read_frame = read_frame;
    g_journal.configured.store(true, std::memory_order_release);
  }
  output.exact_12004_build_admitted = true;
  output.module_base = module_base;
  output.callback_context = &g_journal;
  output.before = &Before;
  output.after = &After;
  return true;
}

void SetActivityCompletionEffectCounterObservations12004Attached(
    bool attached, const char *reason) noexcept {
  if (!g_journal.configured.load(std::memory_order_acquire)) return;
  g_journal.reason.store(reason != nullptr && reason[0] != '\0' ? reason :
      "activity_completion_effect_counter_observer_unavailable",
      std::memory_order_release);
  g_journal.attached.store(attached, std::memory_order_release);
}

std::optional<ActivityCompletionEffectCounterSnapshot12004>
ReadActivityCompletionEffectCounterObservations12004(
    const bridge::ActivityHostedIdentityFrameV1 &query_frame,
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  if (!g_journal.configured.load(std::memory_order_acquire)) return std::nullopt;
  ActivityCompletionEffectCounterSnapshot12004 result{};
  result.observer_attached = g_journal.attached.load(std::memory_order_acquire);
  result.query_thread_id = static_cast<std::uint32_t>(GetCurrentThreadId());
  result.query_actor_full_id = static_cast<std::uint32_t>(query_frame.actor_character_id);
  if (!bridge::IsActivity12004BuildV1(executable_sha256) ||
      module_base != g_journal.module_base) {
    result.unavailable_reason = "activity_completion_effect_counter_query_binding_unavailable";
    return result;
  }
  if (!result.observer_attached) {
    result.unavailable_reason = Reason(g_journal);
    return result;
  }
  if (!query_frame.application_main_thread || !query_frame.paused ||
      !query_frame.map_ready || !query_frame.actor_alive ||
      !Owner(g_journal, result.query_thread_id)) {
    result.unavailable_reason = "activity_completion_effect_counter_query_owner_frame_unavailable";
    return result;
  }
  result.earliest_retained_sequence = g_journal.count == 0 ? 0 :
      g_journal.records[g_journal.first].capture_sequence;
  result.latest_capture_sequence = g_journal.latest_sequence;
  result.overflow_dropped_count = g_journal.overflow_dropped_count;
  result.pairing_dropped_count = g_journal.pairing_dropped_count;
  for (std::size_t i = 0; i < g_journal.count; ++i) {
    const auto &record = g_journal.records[(g_journal.first+i) % g_journal.records.size()];
    if (!record.before.participant_full_id_observed ||
        record.before.participant_full_id != result.query_actor_full_id ||
        !record.before.type_key_observed ||
        std::string_view(record.before.type_key.data(), record.before.type_key_size) !=
            "activity_feast")
      continue;
    result.records[result.record_count++] = record;
  }
  if (!g_journal.attached.load(std::memory_order_acquire)) {
    result.observer_attached = false;
    result.unavailable_reason = Reason(g_journal);
    result.record_count = 0;
    return result;
  }
  result.available = true;
  result.unavailable_reason = nullptr;
  return result;
}

} // namespace xar::ck3_12004
