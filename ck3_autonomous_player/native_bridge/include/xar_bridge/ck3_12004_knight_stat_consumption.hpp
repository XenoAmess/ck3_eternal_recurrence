#pragma once

#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include "xar_bridge/knight_stat_consumption_12004.hpp"

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kKnightStatWrapperRva12004 = 0x2C06D10;
inline constexpr std::uintptr_t kKnightStatContextGetterRva12004 = 0x28C3AC0;
inline constexpr std::uintptr_t kKnightStatPhysicalEntryWriterRva12004 = 0x2657AA0;
inline constexpr std::array<std::uintptr_t, 9> kKnightStatContextReturns12004{
    0x2C06B03, 0x2C06B51, 0x2C06B8D, 0x2C06BC4, 0x2C06BFB,
    0x2C06C32, 0x2C06C69, 0x2C06CA0, 0x2C06CD7};
inline constexpr std::size_t kKnightStatWrapperPatchBytes12004 = 16;
inline constexpr std::size_t kKnightStatContextPatchBytes12004 = 14;
using KnightStatWrapperOriginal12004 = void *(__fastcall *)(void *, void *);
using KnightStatContextOriginal12004 = void *(__fastcall *)(void *);

struct KnightStatConsumptionBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void **game_state_slot = nullptr;
  const std::int32_t *damage_multiplier = nullptr;
  const std::int32_t *toughness_multiplier = nullptr;
  void *read_context = nullptr;
  ActualLossWriterReadMemoryV1 read_memory = nullptr;
};
struct KnightStatConsumptionInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  KnightStatConsumptionBindings12004 bindings;
  std::uintptr_t wrapper_target_override = 0;
  std::uintptr_t context_target_override = 0;
  void *memory_context = nullptr;
  ActualLossWriterVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free_override = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect_override = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache_override = nullptr;
};
struct KnightStatConsumptionDetourState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t wrapper_target = 0, context_target = 0;
  void *wrapper_trampoline = nullptr, *context_trampoline = nullptr;
  void *memory_context = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache = nullptr;
};

KnightStatConsumptionBindings12004 BindKnightStatConsumptionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallKnightStatConsumption12004(
    KnightStatConsumptionDetourState12004 &,
    const KnightStatConsumptionInstallEnvironment12004 &,
    std::string_view executable_sha256) noexcept;
bool UninstallKnightStatConsumption12004(
    KnightStatConsumptionDetourState12004 &, bool primary_thread_suspended_proven) noexcept;
bool InitializeKnightStatConsumptionFixture12004(
    const KnightStatConsumptionBindings12004 &,
    KnightStatWrapperOriginal12004, KnightStatContextOriginal12004) noexcept;

// The production and sole fixture use the same two dispatches. Original calls
// and returned pointer bits are preserved, including failed auxiliary copies.
void *InvokeKnightStatWrapper12004(void *output_cache, void *linked_character,
                                  std::uintptr_t caller_return_address) noexcept;
void *InvokeKnightStatContext12004(void *selected_character,
                                  std::uintptr_t caller_return_address) noexcept;

// Marks the existing native stat query's real scratch buffer. It makes no
// native calls and does not turn an unclassified native output into an Entry.
class KnightStatBridgeQueryScope12004 {
public:
  KnightStatBridgeQueryScope12004(void *output_cache, std::int32_t regiment_id,
                                std::int32_t target_province_id) noexcept;
  ~KnightStatBridgeQueryScope12004();
  KnightStatBridgeQueryScope12004(const KnightStatBridgeQueryScope12004 &) = delete;
  KnightStatBridgeQueryScope12004 &operator=(const KnightStatBridgeQueryScope12004 &) = delete;
private:
  void *previous_ = nullptr;
  void *output_cache_ = nullptr;
  std::int32_t regiment_id_ = -1, target_province_id_ = -1;
  friend void *InvokeKnightStatWrapper12004(void *, void *, std::uintptr_t) noexcept;
};

// Created only around the actual2657AA0 writer. Complete runs after its original
// call and stores owned physical caches, without relabelling wrapper scratch.
class KnightStatPhysicalEntryScope12004 {
public:
  KnightStatPhysicalEntryScope12004(void *entry, void *province) noexcept;
  ~KnightStatPhysicalEntryScope12004();
  void Complete(std::uint64_t original_return_value) noexcept;
  KnightStatPhysicalEntryScope12004(const KnightStatPhysicalEntryScope12004 &) = delete;
  KnightStatPhysicalEntryScope12004 &operator=(const KnightStatPhysicalEntryScope12004 &) = delete;
private:
  KnightStatPhysicalEntryScope12004 *previous_ = nullptr;
  void *entry_ = nullptr, *province_ = nullptr;
  std::uint64_t writer_sequence_ = 0;
  std::optional<std::uint32_t> regiment_id_;
  std::optional<std::int32_t> province_id_;
  std::array<std::uint64_t, kKnightStatConsumptionCapacity12004> wrapper_sequences_{};
  std::size_t wrapper_count_ = 0;
  bool completed_ = false, wrapper_sequence_overflow_ = false;
  friend void *InvokeKnightStatWrapper12004(void *, void *, std::uintptr_t) noexcept;
};

std::optional<KnightStatConsumptionQuery12004> ReadKnightStatConsumptionQuery12004(
    std::span<const std::int32_t> current_regiment_ids,
    std::span<const std::int32_t> current_linked_character_ids) noexcept;

extern "C" __declspec(noinline) void *__fastcall XarKnightStatWrapperHook12004(
    void *output_cache, void *linked_character) noexcept;
extern "C" __declspec(noinline) void *__fastcall XarKnightStatContextHook12004(
    void *selected_character) noexcept;
} // namespace xar::ck3_12004
