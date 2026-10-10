#include "xar_bridge/ck3_12004_knight_stat_consumption.hpp"
#include "xar_bridge/person_installed_transfer_capture_12004.hpp"
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include "xar_bridge/entry_selected_receiver_stage_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <limits>
#include <cstring>
#include <memory>
#include <mutex>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {
constexpr std::array<std::uint8_t, kKnightStatWrapperPatchBytes12004> kWrapperAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x10, 0x57, 0x48, 0x83,
    0xEC, 0x20, 0x8B, 0x9A, 0xEC, 0, 0, 0};
// Ends exactly before JE at+14. The trampoline's absolute JMP preserves ZF.
constexpr std::array<std::uint8_t, kKnightStatContextPatchBytes12004> kContextAnchor{
    0x48, 0x83, 0xEC, 0x28, 0x48, 0x8B, 0x81, 0xB0, 1, 0, 0,
    0x48, 0x85, 0xC0};
using Event = KnightStatConsumptionEvent12004;
KnightStatConsumptionBindings12004 g_bindings;
std::atomic<KnightStatWrapperOriginal12004> g_wrapper_original{nullptr};
std::atomic<KnightStatContextOriginal12004> g_context_original{nullptr};
std::atomic<KnightStatConsumptionDetourState12004 *> g_active_state{nullptr};
std::atomic<bool> g_available{false};
std::mutex g_mutex;
std::array<std::shared_ptr<const Event>, kKnightStatConsumptionCapacity12004> g_ring;
std::uint64_t g_sequence = 0;
std::atomic<std::uint64_t> g_writer_sequence{0};
std::atomic<std::uint64_t> g_capture_failures{0};
thread_local Event *g_pending = nullptr;
thread_local KnightStatBridgeQueryScope12004 *g_query_scope = nullptr;
thread_local KnightStatPhysicalEntryScope12004 *g_physical_scope = nullptr;

template <class Callback> bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}
bool Copy(const void *address, void *output, std::size_t bytes) noexcept {
  if (address == nullptr) return false;
  return FaultBoundary([&]() noexcept {
    if (g_bindings.read_memory != nullptr)
      return g_bindings.read_memory(g_bindings.read_context, address, output, bytes);
    std::memcpy(output, address, bytes);
    return true;
  });
}
template <class T> std::optional<T> At(const void *object, std::size_t offset) noexcept {
  T value{};
  if (object != nullptr && Copy(static_cast<const std::byte *>(object) + offset,
                                &value, sizeof(value))) return value;
  return std::nullopt;
}
std::optional<std::int64_t> Operand(void *character, std::size_t index) noexcept {
  if (index == 0) return 100000;
  if (index == 1 || index == 2) {
    const auto carrier = At<void *>(character, 0x1C0);
    if (!carrier) return std::nullopt;
    if (*carrier == nullptr) return 0;
    return At<std::int64_t>(*carrier, index == 1 ? 0x350 : 0x358);
  }
  constexpr std::array<std::size_t, 6> offsets{0xEC, 0xD8, 0xE4, 0xE8, 0xDC, 0xE0};
  const auto points = At<std::int32_t>(character, offsets[index - 3]);
  if (!points) return std::nullopt;
  return static_cast<std::int64_t>(*points) * 100000;
}
void Clock(Event &event) noexcept {
  void *state = nullptr;
  if (Copy(g_bindings.game_state_slot, &state, sizeof(state)))
    event.observed_date_raw = At<std::int32_t>(state, 8);
}
void Output(void *cache, KnightConsumedOutput12004 &result) noexcept {
  result.max_size = At<std::int32_t>(cache, 8);
  result.siege_value_raw = At<std::int64_t>(cache, 0x10);
  result.damage_raw = At<std::int64_t>(cache, 0x18);
  result.toughness_raw = At<std::int64_t>(cache, 0x20);
  result.pursuit_raw = At<std::int64_t>(cache, 0x28);
  result.screen_raw = At<std::int64_t>(cache, 0x30);
  result.ready = result.max_size && result.siege_value_raw && result.damage_raw &&
      result.toughness_raw && result.pursuit_raw && result.screen_raw;
  if (!result.ready) result.reason = "native_output_copy_failed";
}
void EntryOutput(void *entry, KnightConsumedOutput12004 &result) noexcept {
  result.max_size = At<std::int32_t>(entry, 0x30);
  result.siege_value_raw = At<std::int64_t>(entry, 0x38);
  result.damage_raw = At<std::int64_t>(entry, 0x40);
  result.toughness_raw = At<std::int64_t>(entry, 0x48);
  result.pursuit_raw = At<std::int64_t>(entry, 0x50);
  result.screen_raw = At<std::int64_t>(entry, 0x58);
  result.ready = result.max_size && result.siege_value_raw && result.damage_raw &&
      result.toughness_raw && result.pursuit_raw && result.screen_raw;
  if (!result.ready) result.reason = "physical_entry_cache_copy_failed";
}
template <class T>
std::optional<bool> EqualObserved(const std::optional<T> &left,
                                const std::optional<T> &right) noexcept {
  if (left && right) return *left == *right;
  return std::nullopt;
}
bool Initialize(const KnightStatConsumptionBindings12004 &bindings,
                KnightStatWrapperOriginal12004 wrapper,
                KnightStatContextOriginal12004 context) noexcept {
  if (!bindings.enabled || wrapper == nullptr || context == nullptr) return false;
  g_available.store(false, std::memory_order_release);
  {
    const std::lock_guard lock(g_mutex);
    g_bindings = bindings;
    g_sequence = 0;
    for (auto &record : g_ring) record.reset();
  }
  g_capture_failures.store(0, std::memory_order_release);
  g_writer_sequence.store(0, std::memory_order_release);
  g_wrapper_original.store(wrapper, std::memory_order_release);
  g_context_original.store(context, std::memory_order_release);
  g_available.store(true, std::memory_order_release);
  return true;
}
void Jump(std::uint8_t *destination, std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF, 0x25, 0, 0, 0, 0};
  std::memcpy(destination, prefix.data(), prefix.size());
  std::memcpy(destination + prefix.size(), &target, sizeof(target));
}
template <std::size_t N>
std::array<std::uint8_t, N> Patch(std::uintptr_t hook) noexcept {
  std::array<std::uint8_t, N> bytes;
  bytes.fill(0x90);
  Jump(bytes.data(), hook);
  return bytes;
}
bool DefaultFree(void *, void *address, std::size_t bytes, DWORD kind) noexcept {
  return VirtualFree(address, bytes, kind) != FALSE;
}
void *DefaultAlloc(void *, std::size_t bytes, DWORD kind, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, bytes, kind, protection);
}
bool DefaultProtect(void *, void *address, std::size_t bytes, DWORD protection,
                    DWORD &old) noexcept {
  return VirtualProtect(address, bytes, protection, &old) != FALSE;
}
bool DefaultFlush(void *, const void *address, std::size_t bytes) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, bytes) != FALSE;
}
void Fail(KnightStatConsumptionDetourState12004 &state, std::uint32_t flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}
template <std::size_t N>
bool WritePatch(KnightStatConsumptionDetourState12004 &state, std::uintptr_t target,
                const std::array<std::uint8_t, N> &expected,
                const std::array<std::uint8_t, N> &desired) noexcept {
  auto *address = reinterpret_cast<void *>(target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(address, expected.data(), N) == 0;
      })) { Fail(state, actual_loss_install_anchor); return false; }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, address, N, PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, actual_loss_install_protection); return false;
  }
  std::memcpy(address, desired.data(), N);
  const bool flushed = state.flush_instruction_cache(state.memory_context, address, N);
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, address, N, old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? actual_loss_install_protection : actual_loss_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, address, N,
                                             PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(address, expected.data(), N);
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, address, N);
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, address, N, old, ignored);
  if (!rollback_flushed || !rollback_restored) Fail(state, actual_loss_install_rollback);
  return false;
}
template <std::size_t N>
void *Trampoline(KnightStatConsumptionDetourState12004 &state,
                 ActualLossWriterVirtualAllocV1 allocate, std::uintptr_t target,
                 const std::array<std::uint8_t, N> &anchor) noexcept {
  constexpr std::size_t bytes = N + 14;
  void *memory = allocate(state.memory_context, bytes, MEM_RESERVE | MEM_COMMIT,
                          PAGE_READWRITE);
  if (memory == nullptr) { Fail(state, actual_loss_install_allocation); return nullptr; }
  std::memcpy(memory, anchor.data(), N);
  Jump(static_cast<std::uint8_t *>(memory) + N, target + N);
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, memory, bytes, PAGE_EXECUTE_READ, old) ||
      !state.flush_instruction_cache(state.memory_context, memory, bytes)) {
    Fail(state, actual_loss_install_protection);
    (void)state.virtual_free(state.memory_context, memory, 0, MEM_RELEASE);
    return nullptr;
  }
  return memory;
}
auto WrapperPatch() noexcept {
  return Patch<kKnightStatWrapperPatchBytes12004>(
      reinterpret_cast<std::uintptr_t>(&XarKnightStatWrapperHook12004));
}
auto ContextPatch() noexcept {
  return Patch<kKnightStatContextPatchBytes12004>(
      reinterpret_cast<std::uintptr_t>(&XarKnightStatContextHook12004));
}
} // namespace

KnightStatConsumptionBindings12004 BindKnightStatConsumptionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  KnightStatConsumptionBindings12004 result;
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.image_base = image_base;
  result.game_state_slot = reinterpret_cast<void **>(image_base + kGameStateSlotRva);
  result.damage_multiplier = reinterpret_cast<const std::int32_t *>(image_base + 0x5C699A8);
  result.toughness_multiplier = reinterpret_cast<const std::int32_t *>(image_base + 0x5C699B0);
  return result;
}

KnightStatBridgeQueryScope12004::KnightStatBridgeQueryScope12004(
    void *output_cache, std::int32_t regiment_id, std::int32_t target_province_id) noexcept
    : previous_(g_query_scope), output_cache_(output_cache), regiment_id_(regiment_id),
      target_province_id_(target_province_id) {
  g_query_scope = this;
}
KnightStatBridgeQueryScope12004::~KnightStatBridgeQueryScope12004() {
  g_query_scope = static_cast<KnightStatBridgeQueryScope12004 *>(previous_);
}

KnightStatPhysicalEntryScope12004::KnightStatPhysicalEntryScope12004(
    void *entry, void *province) noexcept
    : previous_(g_physical_scope), entry_(entry), province_(province),
      writer_sequence_(g_writer_sequence.fetch_add(1, std::memory_order_acq_rel) + 1),
      regiment_id_(At<std::uint32_t>(entry, 8)),
      province_id_(At<std::int32_t>(province, 0x10)) {
  g_physical_scope = this;
}
KnightStatPhysicalEntryScope12004::~KnightStatPhysicalEntryScope12004() {
  g_physical_scope = previous_;
}
void KnightStatPhysicalEntryScope12004::Complete(
    std::uint64_t original_return_value) noexcept {
  if (completed_) return;
  completed_ = true;
  if (wrapper_count_ == 0) return;
  try {
    KnightStatPhysicalEntryWriteback12004 writeback;
    writeback.writer_sequence = writer_sequence_;
    writeback.entry_identity = reinterpret_cast<std::uintptr_t>(entry_);
    writeback.province_identity = reinterpret_cast<std::uintptr_t>(province_);
    writeback.regiment_id = regiment_id_;
    writeback.province_id = province_id_;
    writeback.original_return_value = original_return_value;
    EntryOutput(entry_, writeback.entry_cache);
    if (!writeback.entry_cache.ready) writeback.reason = writeback.entry_cache.reason;
    if (wrapper_sequence_overflow_) writeback.reason = "writer_wrapper_sequence_capacity";
    const std::lock_guard lock(g_mutex);
    for (std::size_t index = 0; index < wrapper_count_; ++index) {
      const auto sequence = wrapper_sequences_[index];
      auto &retained = g_ring[(sequence - 1) % g_ring.size()];
      if (!retained || retained->sequence != sequence) continue;
      // Previously returned query copies remain immutable. Attach only after the
      // actual writer stores its caches and returns to its observation scope.
      auto updated = std::make_shared<Event>(*retained);
      auto sidecar = writeback;
      sidecar.output_cache_identity_matches_entry =
          updated->output_cache_identity == sidecar.entry_identity;
      const auto &output = updated->observed_output;
      const auto &cache = sidecar.entry_cache;
      sidecar.wrapper_output_field_matches = {
          EqualObserved(output.max_size, cache.max_size),
          EqualObserved(output.siege_value_raw, cache.siege_value_raw),
          EqualObserved(output.damage_raw, cache.damage_raw),
          EqualObserved(output.toughness_raw, cache.toughness_raw),
          EqualObserved(output.pursuit_raw, cache.pursuit_raw),
          EqualObserved(output.screen_raw, cache.screen_raw)};
      sidecar.wrapper_output_comparison_ready = std::all_of(
          sidecar.wrapper_output_field_matches.begin(),
          sidecar.wrapper_output_field_matches.end(),
          [](const auto &match) { return match.has_value(); });
      if (sidecar.wrapper_output_comparison_ready)
        sidecar.wrapper_output_matches_entry_cache = std::all_of(
            sidecar.wrapper_output_field_matches.begin(),
            sidecar.wrapper_output_field_matches.end(),
            [](const auto &match) { return *match; });
      updated->origin = "native_physical_entry_writer";
      updated->entry_association_proven = true;
      if (sidecar.regiment_id)
        updated->regiment_id = static_cast<std::int32_t>(*sidecar.regiment_id);
      if (sidecar.province_id) updated->target_province_id = *sidecar.province_id;
      updated->physical_entry_writeback = std::move(sidecar);
      retained = std::move(updated);
    }
  } catch (...) { g_capture_failures.fetch_add(1); }
}

bool InitializeKnightStatConsumptionFixture12004(
    const KnightStatConsumptionBindings12004 &bindings,
    KnightStatWrapperOriginal12004 wrapper, KnightStatContextOriginal12004 context) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  return Initialize(bindings, wrapper, context);
}

void *InvokeKnightStatWrapper12004(void *output_cache, void *linked_character,
                                  std::uintptr_t caller_return_address) noexcept {
  const auto original = g_wrapper_original.load(std::memory_order_acquire);
  if (original == nullptr) return nullptr;
  std::unique_ptr<Event> event;
  try {
    if (g_available.load(std::memory_order_acquire)) {
      event = std::make_unique<Event>();
      event->thread_id = GetCurrentThreadId();
      event->output_cache_identity = reinterpret_cast<std::uintptr_t>(output_cache);
      event->linked_character_identity = reinterpret_cast<std::uintptr_t>(linked_character);
      event->linked_character_id = At<std::uint32_t>(linked_character, 0x18);
      event->linked_prowess_points = At<std::int32_t>(linked_character, 0xEC);
      event->loaded_damage_multiplier = At<std::int32_t>(g_bindings.damage_multiplier, 0);
      event->loaded_toughness_multiplier = At<std::int32_t>(g_bindings.toughness_multiplier, 0);
      if (g_bindings.image_base != 0 && caller_return_address >= g_bindings.image_base)
        event->wrapper_caller_return_rva = caller_return_address - g_bindings.image_base;
      if (g_query_scope != nullptr && g_query_scope->output_cache_ == output_cache) {
        event->origin = "bridge_query_scratch";
        event->regiment_id = g_query_scope->regiment_id_;
        event->target_province_id = g_query_scope->target_province_id_;
      }
      Clock(*event);
      event->contexts.reserve(9);
    }
  } catch (...) { event.reset(); g_capture_failures.fetch_add(1); }
  auto *previous = g_pending;
  g_pending = event.get();
  // No observer exception boundary wraps or repeats the native operation.
  void *const result = original(output_cache, linked_character);
  g_pending = previous;
  if (event) {
    try {
      event->native_return_identity = reinterpret_cast<std::uintptr_t>(result);
      Output(output_cache, event->observed_output);
      if (event->contexts.size() != 9) event->capture_reason = "consumed_context_calls_incomplete";
      const std::lock_guard lock(g_mutex);
      event->sequence = ++g_sequence;
      if (g_physical_scope != nullptr) {
        if (g_physical_scope->wrapper_count_ < g_physical_scope->wrapper_sequences_.size())
          g_physical_scope->wrapper_sequences_[g_physical_scope->wrapper_count_++] = event->sequence;
        else g_physical_scope->wrapper_sequence_overflow_ = true;
      }
      const auto ring_index = (event->sequence - 1) % g_ring.size();
      g_ring[ring_index] = std::shared_ptr<const Event>(std::move(event));
    } catch (...) { g_capture_failures.fetch_add(1); }
  }
  return result;
}

namespace {
KnightNaturalLineageEvent12004 OwnedEvent(
    const PersonInstalledTransferEvent12004 &event) noexcept {
  return {event.clock_identity, event.sequence, event.thread_id};
}

KnightInstalledTransferLineage12004 InstalledTransferLineage(
    const std::optional<PersonInstalledTransferCaptureRecord12004> &record,
    const KnightNaturalLineageEvent12004 &begin,
    const KnightNaturalLineageEvent12004 &end,
    const KnightConsumedContext12004 &context, std::uint32_t thread) {
  KnightInstalledTransferLineage12004 out;
  out.getter_begin_event = begin;
  out.getter_completed_event = end;
  if (!record) {
    out.reason = "installed_transfer_unobserved_before_getter";
    return out;
  }
  PersonInstalledTransferCaptureQuery12004 owned;
  owned.records.push_back(*record);
  // The record was copied before the actual getter. Its four-block payload
  // reaches this Ci through the same retained serializer, without a new query.
  out.physical_postimage_owned_at_consumption = record->physical_postimage.has_value();
  out.capture_at_consumption = SerializePersonInstalledTransferCapture12004(owned);
  const auto &stage = record->stage;
  const auto &before = stage.before_event;
  const auto &completed = stage.completed_event;
  if (before.clock_identity != 0 && completed.clock_identity != 0 &&
      begin.clock_identity != 0 && end.clock_identity != 0 &&
      before.thread_id && completed.thread_id && begin.thread_id && end.thread_id) {
    out.transfer_completed_before_getter = thread != 0 &&
        before.clock_identity == completed.clock_identity &&
        completed.clock_identity == begin.clock_identity &&
        begin.clock_identity == end.clock_identity &&
        *before.thread_id == thread && *completed.thread_id == thread &&
        *begin.thread_id == thread && *end.thread_id == thread &&
        before.sequence != 0 && before.sequence < completed.sequence &&
        completed.sequence < begin.sequence && begin.sequence < end.sequence;
  }
  if (context.selected_character_identity && context.selected_character_id &&
      stage.before.observed_owner_identity && stage.before.observed_owner_character_id &&
      stage.after.observed_owner_identity && stage.after.observed_owner_character_id) {
    out.selected_matches_transfer_owner = *context.selected_character_identity != 0 &&
        context.selected_character_identity == stage.before.observed_owner_identity &&
        context.selected_character_id == stage.before.observed_owner_character_id &&
        context.selected_character_identity == stage.after.observed_owner_identity &&
        context.selected_character_id == stage.after.observed_owner_character_id;
  }
  if (context.context_identity && context.selected_character_identity &&
      context.selected_character_id && stage.after.installed_model_identity &&
      stage.after.installed_model_owner_identity &&
      stage.after.matching_installed_inline_context_identity &&
      stage.after.model_a_owner_identity && stage.after.model_a_owner_character_id) {
    out.getter_matches_installed_context = *context.context_identity != 0 &&
        stage.model_a_identity != 0 &&
        stage.model_a_identity <= std::numeric_limits<std::uintptr_t>::max() - 0x10 &&
        *stage.after.installed_model_identity == stage.model_a_identity &&
        stage.after.installed_model_is_a == true &&
        stage.after.installed_owner_matches_observed_owner == true &&
        context.selected_character_identity == stage.after.installed_model_owner_identity &&
        context.selected_character_identity == stage.after.model_a_owner_identity &&
        context.selected_character_id == stage.after.model_a_owner_character_id &&
        *stage.after.matching_installed_inline_context_identity == stage.model_a_identity + 0x10 &&
        context.context_identity == stage.after.matching_installed_inline_context_identity;
  }
  out.installed_identity_associated = stage.observed && stage.original_called &&
      stage.original_returned &&
      stage.original_return_rva == kPersonInstalledTransferCallerReturnRva12004 &&
      out.transfer_completed_before_getter == true &&
      out.selected_matches_transfer_owner == true &&
      out.getter_matches_installed_context == true;
  out.reason = out.installed_identity_associated
      ? "installed_identity_associated_numeric_postimage_unproven"
      : "installed_transfer_not_associated_with_consumed_context";
  return out;
}
} // namespace

void *InvokeKnightStatContext12004(void *selected_character,
                                  std::uintptr_t caller_return_address) noexcept {
  const auto original = g_context_original.load(std::memory_order_acquire);
  if (original == nullptr) return nullptr;
  if (g_pending == nullptr) return original(selected_character);
  const auto rva = caller_return_address >= g_bindings.image_base
      ? caller_return_address - g_bindings.image_base : 0;
  const auto site = std::find(kKnightStatContextReturns12004.begin(),
                             kKnightStatContextReturns12004.end(), rva);
  const bool observed = site != kKnightStatContextReturns12004.end();
  const auto index = observed ? static_cast<std::size_t>(site - kKnightStatContextReturns12004.begin()) : 0;
  const auto operand = observed ? Operand(selected_character, index) : std::nullopt;
  std::optional<std::uint32_t> selected_id;
  std::optional<PersonInstalledTransferCaptureRecord12004> transfer;
  if (observed) {
    try {
      selected_id = At<std::uint32_t>(selected_character, 0x18);
      if (selected_id)
        transfer = ReadPersonInstalledTransferCaptureForOwner12004(
            reinterpret_cast<std::uintptr_t>(selected_character), *selected_id);
    } catch (...) { g_capture_failures.fetch_add(1); }
  }
  // Only shared natural events are comparable to transfer completion. The
  // family's retention sequence and Native65 preparation counter stay separate.
  const auto begin = observed ? OwnedEvent(NextPersonNaturalLineageEvent12004())
                              : KnightNaturalLineageEvent12004{};
  // This is the actual getter return used by the original numeric function.
  void *const result = original(selected_character);
  const auto end = observed ? OwnedEvent(NextPersonNaturalLineageEvent12004())
                            : KnightNaturalLineageEvent12004{};
  if (observed) {
    try {
      KnightConsumedContext12004 context;
      context.property_key = static_cast<std::uint16_t>(0xC1 + index);
      context.caller_return_rva = rva;
      context.selected_character_identity = reinterpret_cast<std::uintptr_t>(selected_character);
      context.selected_character_id = selected_id;
      context.context_identity = reinterpret_cast<std::uintptr_t>(result);
      context.operand_raw = operand;
      context.consumed_pc.weight_q100000 = 0;
      if (result != nullptr) {
        context.consumed_pc = CopyPersonSixStageAggregatePc12004(
            reinterpret_cast<std::uintptr_t>(result) + 0x68);
      } else context.consumed_pc.reason = "consumed_context_null";
      if (!operand) context.reason = "consumed_operand_copy_failed";
      else if (!context.consumed_pc.ready) context.reason = context.consumed_pc.reason;
      PersonSixStageCapture12004DTO capture;
      if (context.selected_character_id) {
        capture = ReadPersonSixStageCaptureForCharacter12004(
            reinterpret_cast<std::uintptr_t>(selected_character), *context.selected_character_id);
        if (capture.capture_observed) {
          context.preparation_capture_sequence = capture.capture_sequence;
          context.preparation_model_identity = capture.preparation_model.model_identity;
          context.preparation_context_identity = capture.context_identity;
          context.preparation_owner_character_id = capture.preparation_model.owner_character_id;
          if (capture.context_identity)
            context.context_matches_preparation = *capture.context_identity ==
                reinterpret_cast<std::uintptr_t>(result);
          if (capture.preparation_model.owner_character_id)
            context.owner_matches_preparation = *capture.preparation_model.owner_character_id ==
                *context.selected_character_id;
          if (capture.post_six_aggregate.observed && capture.post_six_aggregate.pc.ready &&
              context.consumed_pc.ready)
            context.pc_matches_preparation_post =
                capture.post_six_aggregate.pc == context.consumed_pc;
        }
      }
      context.preparation_stage_lineage = ObserveEntrySelectedReceiverStage12004(
          capture, context, {g_pending->linked_character_id,
                             g_pending->linked_character_identity, g_pending->thread_id});
      if (capture.capture_observed)
        context.preparation_capture_at_consumption = std::move(capture);
      context.installed_transfer_lineage = InstalledTransferLineage(
          transfer, begin, end, context, g_pending->thread_id);
      g_pending->contexts.push_back(std::move(context));
    } catch (...) { g_capture_failures.fetch_add(1); }
  }
  return result;
}

std::optional<KnightStatConsumptionQuery12004> ReadKnightStatConsumptionQuery12004(
    std::span<const std::int32_t> current_regiment_ids,
    std::span<const std::int32_t> current_linked_character_ids) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return std::nullopt;
  try {
    KnightStatConsumptionQuery12004 result;
    result.executable_sha256 = std::string(kExecutableSha256);
    result.configured = true;
    const auto *state = g_active_state.load(std::memory_order_acquire);
    result.observer_installed = state != nullptr && state->installed.load(std::memory_order_acquire) != 0;
    const std::lock_guard lock(g_mutex);
    result.latest_sequence = g_sequence;
    result.oldest_available_sequence = g_sequence == 0 ? 0 :
        g_sequence <= g_ring.size() ? 1 : g_sequence - g_ring.size() + 1;
    result.overwritten_events = g_sequence > g_ring.size() ? g_sequence - g_ring.size() : 0;
    if (g_capture_failures.load() != 0) result.reason = "auxiliary_capture_failed";
    for (auto sequence = result.oldest_available_sequence; sequence != 0 && sequence <= g_sequence; ++sequence) {
      const auto &event = g_ring[(sequence - 1) % g_ring.size()];
      if (!event || event->sequence != sequence) continue;
      const bool regiment_match = event->regiment_id &&
          std::find(current_regiment_ids.begin(), current_regiment_ids.end(), *event->regiment_id) != current_regiment_ids.end();
      const bool character_match = !event->regiment_id && event->linked_character_id &&
          std::find(current_linked_character_ids.begin(), current_linked_character_ids.end(),
                    static_cast<std::int32_t>(*event->linked_character_id)) != current_linked_character_ids.end();
      if (event->physical_entry_writeback && event->physical_entry_writeback->regiment_id) {
        const auto full_id = *event->physical_entry_writeback->regiment_id;
        const bool physical_member = std::any_of(
            current_regiment_ids.begin(), current_regiment_ids.end(),
            [full_id](std::int32_t id) { return static_cast<std::uint32_t>(id) == full_id; });
        if (physical_member) {
          auto copy = *event;
          copy.physical_entry_writeback->regiment_member_at_query = true;
          result.events.push_back(std::move(copy));
        }
      } else if (regiment_match || character_match) result.events.push_back(*event);
    }
    return result;
  } catch (...) { return std::nullopt; }
}

bool InstallKnightStatConsumption12004(KnightStatConsumptionDetourState12004 &state,
    const KnightStatConsumptionInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(0, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) { Fail(state, actual_loss_install_exact_build); return false; }
  if (!environment.primary_thread_suspended_proven) { Fail(state, actual_loss_install_quiescence); return false; }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  KnightStatConsumptionDetourState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state)) {
    Fail(state, actual_loss_install_already_installed); return false;
  }
  state.wrapper_target = environment.wrapper_target_override != 0
      ? environment.wrapper_target_override : environment.bindings.image_base + kKnightStatWrapperRva12004;
  state.context_target = environment.context_target_override != 0
      ? environment.context_target_override : environment.bindings.image_base + kKnightStatContextGetterRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override ? environment.virtual_free_override : DefaultFree;
  state.virtual_protect = environment.virtual_protect_override ? environment.virtual_protect_override : DefaultProtect;
  state.flush_instruction_cache = environment.flush_instruction_cache_override ? environment.flush_instruction_cache_override : DefaultFlush;
  const bool anchors = FaultBoundary([&]() noexcept {
    return std::memcmp(reinterpret_cast<const void *>(state.wrapper_target), kWrapperAnchor.data(), kWrapperAnchor.size()) == 0 &&
        std::memcmp(reinterpret_cast<const void *>(state.context_target), kContextAnchor.data(), kContextAnchor.size()) == 0;
  });
  if (!anchors) { Fail(state, actual_loss_install_anchor); g_active_state.store(nullptr); return false; }
  const auto allocate = environment.virtual_alloc_override ? environment.virtual_alloc_override : DefaultAlloc;
  state.wrapper_trampoline = Trampoline(state, allocate, state.wrapper_target, kWrapperAnchor);
  if (state.wrapper_trampoline != nullptr)
    state.context_trampoline = Trampoline(state, allocate, state.context_target, kContextAnchor);
  const bool initialized = state.wrapper_trampoline != nullptr && state.context_trampoline != nullptr &&
      Initialize(environment.bindings, reinterpret_cast<KnightStatWrapperOriginal12004>(state.wrapper_trampoline),
                 reinterpret_cast<KnightStatContextOriginal12004>(state.context_trampoline));
  const bool wrapper_patched = initialized && WritePatch(state, state.wrapper_target, kWrapperAnchor, WrapperPatch());
  const bool context_patched = wrapper_patched && WritePatch(state, state.context_target, kContextAnchor, ContextPatch());
  if (!context_patched) {
    if (wrapper_patched) (void)WritePatch(state, state.wrapper_target, WrapperPatch(), kWrapperAnchor);
    g_available.store(false);
    g_wrapper_original.store(nullptr); g_context_original.store(nullptr);
    if (state.wrapper_trampoline) (void)state.virtual_free(state.memory_context, state.wrapper_trampoline, 0, MEM_RELEASE);
    if (state.context_trampoline) (void)state.virtual_free(state.memory_context, state.context_trampoline, 0, MEM_RELEASE);
    state.wrapper_trampoline = nullptr; state.context_trampoline = nullptr;
    g_active_state.store(nullptr); return false;
  }
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallKnightStatConsumption12004(KnightStatConsumptionDetourState12004 &state,
                                       bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) return true;
  if (!primary_thread_suspended_proven) { Fail(state, actual_loss_install_quiescence); return false; }
  if (!WritePatch(state, state.context_target, ContextPatch(), kContextAnchor)) return false;
  if (!WritePatch(state, state.wrapper_target, WrapperPatch(), kWrapperAnchor)) {
    (void)WritePatch(state, state.context_target, kContextAnchor, ContextPatch()); return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_available.store(false); g_wrapper_original.store(nullptr); g_context_original.store(nullptr);
  g_active_state.store(nullptr);
  const bool first = state.virtual_free(state.memory_context, state.wrapper_trampoline, 0, MEM_RELEASE);
  const bool second = state.virtual_free(state.memory_context, state.context_trampoline, 0, MEM_RELEASE);
  if (first) state.wrapper_trampoline = nullptr;
  if (second) state.context_trampoline = nullptr;
  return first && second;
}

extern "C" __declspec(noinline) void *__fastcall XarKnightStatWrapperHook12004(
    void *output_cache, void *linked_character) noexcept {
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  return InvokeKnightStatWrapper12004(output_cache, linked_character, caller);
}
extern "C" __declspec(noinline) void *__fastcall XarKnightStatContextHook12004(void *selected_character) noexcept {
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  return InvokeKnightStatContext12004(selected_character, caller);
}
} // namespace xar::ck3_12004
