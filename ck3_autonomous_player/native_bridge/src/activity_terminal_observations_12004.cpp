#include "xar_bridge/activity_terminal_observations_12004.hpp"

#include <windows.h>

#include <atomic>
#include <limits>

namespace xar::ck3_12004 {
namespace {

// Configuration is written in the existing cold, suspended startup window.
// Only the actual admitted owner thread reads/writes the ring thereafter.
// Stop changes atomic publication only; backing remains for process lifetime.
struct ProcessJournal {
  std::atomic<bool> configured{false};
  std::atomic<bool> attached{false};
  std::atomic<const char *> reason{"activity_terminal_observer_unavailable"};
  std::atomic<std::uint32_t> owner_thread_id{0};
  std::uintptr_t module_base = 0;
  std::uintptr_t type_vtable = 0;
  void *callback_context = nullptr;
  ActivityTerminalReadMemory12004 read_memory = nullptr;
  ActivityTerminalReadFrame12004 read_frame = nullptr;
  std::uint64_t latest_sequence = 0;
  std::uint64_t overflow_dropped_count = 0;
  std::size_t first = 0;
  std::size_t count = 0;
  std::array<ActivityTerminalObservation12004,
             kActivityTerminalObservations12004Capacity> records{};
};

ProcessJournal g_journal;

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &output) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  output = base + offset;
  return true;
}

template <typename T>
bool ReadAt(const ProcessJournal &journal, std::uintptr_t base,
            std::size_t offset, T &output) noexcept {
  std::uintptr_t address = 0;
  T copied{};
  if (!Add(base, offset, address) || journal.read_memory == nullptr ||
      !journal.read_memory(journal.callback_context, address, &copied,
                           sizeof(copied)))
    return false;
  output = copied;
  return true;
}

bool AdmitOwner(ProcessJournal &journal, std::uint32_t actual_thread) noexcept {
  std::uint32_t unbound = 0;
  journal.owner_thread_id.compare_exchange_strong(
      unbound, actual_thread, std::memory_order_acq_rel);
  return actual_thread != 0 &&
         journal.owner_thread_id.load(std::memory_order_acquire) == actual_thread;
}

// Same bounded type-name layout and character contract as the existing
// ActivityHostedIdentityV1 reader; no native type/name getter is called.
bool ReadFeastTypeKey(ProcessJournal &journal, std::uintptr_t type,
                      ActivityTerminalObservation12004 &record) noexcept {
  std::uintptr_t vtable = 0, data = 0;
  std::uint64_t size = 0, capacity = 0;
  if (type == 0 || !ReadAt(journal, type, 0, vtable) ||
      vtable != journal.type_vtable || !ReadAt(journal, type, 0x28, size) ||
      !ReadAt(journal, type, 0x30, capacity) || size == 0 ||
      size > capacity || size >= record.type_key.size() ||
      !Add(type, 0x18, data))
    return false;
  if (capacity > 15 && !ReadAt(journal, type, 0x18, data)) return false;
  if (data == 0 || !journal.read_memory(
          journal.callback_context, data, record.type_key.data(),
          static_cast<std::size_t>(size)))
    return false;
  for (std::size_t i = 0; i < size; ++i) {
    const char ch = record.type_key[i];
    if (!((ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '_'))
      return false;
  }
  record.type_key_size = static_cast<std::uint8_t>(size);
  return std::string_view(record.type_key.data(), record.type_key_size) == "activity_feast";
}

void Capture(void *opaque, std::uintptr_t actual_manager,
             std::uintptr_t actual_activity) noexcept {
  auto *journal = static_cast<ProcessJournal *>(opaque);
  if (journal != &g_journal || actual_manager == 0 || actual_activity == 0 ||
      !journal->configured.load(std::memory_order_acquire) ||
      !journal->attached.load(std::memory_order_acquire) ||
      journal->read_frame == nullptr)
    return;
  ActivityTerminalCaptureFrame12004 frame{};
  const auto actual_thread = static_cast<std::uint32_t>(GetCurrentThreadId());
  if (!journal->read_frame(journal->callback_context, frame) ||
      frame.owner_thread_id == 0 || frame.owner_thread_id != actual_thread ||
      !frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive || !AdmitOwner(*journal, actual_thread))
    return;

  ActivityTerminalObservation12004 record{};
  record.capture_thread_id = actual_thread;
  record.capture_frame = frame;
  record.manager_identity = actual_manager;
  record.activity_identity = actual_activity;
  if (!ReadAt(*journal, actual_activity, 0x8, record.activity_full_id) ||
      record.activity_full_id == 0xFFFFFFFFU ||
      !ReadAt(*journal, actual_activity, 0x3A8, record.host_character_id) ||
      static_cast<std::uint32_t>(record.host_character_id) !=
          static_cast<std::uint32_t>(frame.actor_character_id) ||
      !ReadAt(*journal, actual_activity, 0x3A0, record.type_identity) ||
      !ReadFeastTypeKey(*journal, record.type_identity, record))
    return;
  record.activity_instance_generation =
      static_cast<std::uint8_t>(record.activity_full_id >> 24);
  record.completed_observed =
      ReadAt(*journal, actual_activity, 0x421, record.completed_raw_u8);
  record.invalidated_observed =
      ReadAt(*journal, actual_activity, 0x422, record.invalidated_raw_u8);
  record.native_completion_stamp_observed =
      ReadAt(*journal, actual_activity, 0x408, record.native_completion_stamp_raw);
  if (!journal->attached.load(std::memory_order_acquire) ||
      journal->latest_sequence == (std::numeric_limits<std::uint64_t>::max)())
    return;
  record.capture_sequence = ++journal->latest_sequence;
  std::size_t slot = (journal->first + journal->count) % journal->records.size();
  if (journal->count == journal->records.size()) {
    slot = journal->first;
    journal->first = (journal->first + 1) % journal->records.size();
    ++journal->overflow_dropped_count;
  } else {
    ++journal->count;
  }
  journal->records[slot] = record;
}

const char *Reason(const ProcessJournal &journal) noexcept {
  const char *reason = journal.reason.load(std::memory_order_acquire);
  return reason != nullptr && reason[0] != '\0'
             ? reason : "activity_terminal_observer_unavailable";
}

} // namespace

bool BuildActivityTerminalObservations12004Environment(
    std::uintptr_t module_base, std::string_view executable_sha256,
    void *callback_context, ActivityTerminalReadMemory12004 read_memory,
    ActivityTerminalReadFrame12004 read_frame,
    ActivityInvalidationPrecallObserver12004Environment &output) noexcept {
  output = {};
  std::uintptr_t vtable = 0;
  if (!bridge::IsActivity12004BuildV1(executable_sha256) || module_base == 0 ||
      read_memory == nullptr || read_frame == nullptr ||
      !Add(module_base, bridge::ActivityHostedCrozierRvaV1(
              executable_sha256, bridge::kActivityHosted12002ActivityTypeVtableRva),
           vtable))
    return false;
  if (g_journal.configured.load(std::memory_order_acquire)) {
    if (g_journal.module_base != module_base ||
        g_journal.callback_context != callback_context ||
        g_journal.read_memory != read_memory || g_journal.read_frame != read_frame)
      return false;
  } else {
    g_journal.module_base = module_base;
    g_journal.type_vtable = vtable;
    g_journal.callback_context = callback_context;
    g_journal.read_memory = read_memory;
    g_journal.read_frame = read_frame;
    g_journal.configured.store(true, std::memory_order_release);
  }
  output.exact_12004_build_admitted = true;
  output.module_base = module_base;
  output.callback_context = &g_journal;
  output.capture = &Capture;
  return true;
}

void SetActivityTerminalObservations12004Attached(
    bool attached, const char *reason) noexcept {
  if (!g_journal.configured.load(std::memory_order_acquire)) return;
  g_journal.reason.store(
      reason != nullptr && reason[0] != '\0'
          ? reason : "activity_terminal_observer_unavailable",
      std::memory_order_release);
  g_journal.attached.store(attached, std::memory_order_release);
}

std::optional<ActivityTerminalObservationsSnapshot12004>
ReadActivityTerminalObservations12004(
    const bridge::ActivityHostedIdentityFrameV1 &query_frame,
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  if (!g_journal.configured.load(std::memory_order_acquire)) return std::nullopt;
  ActivityTerminalObservationsSnapshot12004 result{};
  result.observer_attached = g_journal.attached.load(std::memory_order_acquire);
  result.query_thread_id = static_cast<std::uint32_t>(GetCurrentThreadId());
  result.query_actor_full_id =
      static_cast<std::uint32_t>(query_frame.actor_character_id);
  if (!bridge::IsActivity12004BuildV1(executable_sha256) ||
      module_base != g_journal.module_base) {
    result.unavailable_reason = "activity_terminal_query_binding_unavailable";
    return result;
  }
  if (!result.observer_attached) {
    result.unavailable_reason = Reason(g_journal);
    return result;
  }
  if (!query_frame.application_main_thread || !query_frame.paused ||
      !query_frame.map_ready || !query_frame.actor_alive ||
      !AdmitOwner(g_journal, result.query_thread_id)) {
    result.unavailable_reason = "activity_terminal_query_owner_frame_unavailable";
    return result;
  }
  result.earliest_retained_sequence = g_journal.count == 0 ? 0 :
      g_journal.records[g_journal.first].capture_sequence;
  result.latest_capture_sequence = g_journal.latest_sequence;
  result.overflow_dropped_count = g_journal.overflow_dropped_count;
  for (std::size_t i = 0; i < g_journal.count; ++i) {
    const auto &record = g_journal.records[
        (g_journal.first + i) % g_journal.records.size()];
    if (static_cast<std::uint32_t>(record.host_character_id) !=
            result.query_actor_full_id ||
        std::string_view(record.type_key.data(), record.type_key_size) != "activity_feast")
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
