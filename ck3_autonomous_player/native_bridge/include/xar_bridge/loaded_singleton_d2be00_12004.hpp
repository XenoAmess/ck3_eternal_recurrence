#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"
#include <cstdint>
#include <optional>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::uintptr_t kLoadedSingletonGetterRva12004 = 0xD2BE00;
inline constexpr std::uintptr_t kLoadedSingletonSlotRva12004 = 0x5D1FBF8;

enum class LoadedSingletonFailure12004 : std::uint8_t {
  none, exact_build, read_callback, slot_address, slot_read, singleton_not_loaded,
};

struct LoadedD2BE00Singleton12004 {
  // Caller-supplied admitted snapshot revision; a pointer never proves a frame.
  std::uint64_t frame_key = 0;
  std::uintptr_t copied_slot_address = 0;
  std::optional<std::uintptr_t> singleton_slot_raw;
  std::optional<bool> nonnull_branch_admitted;
  std::optional<std::uintptr_t> conditional_return_pointer;
  LoadedSingletonFailure12004 failure = LoadedSingletonFailure12004::none;
  bool source_ready = false;
  bool native_function_invoked = false;
  bool diagnostic_or_initializer_invoked = false;
};

// One guarded QWORD read of an already loaded singleton. A readable zero is
// retained, while the native null-path's post-diagnostic return stays unknown.
LoadedD2BE00Singleton12004 ReadLoadedD2BE00Singleton12004(
    const RawReceiverAccessV1 &, std::uint64_t snapshot_revision) noexcept;

struct ContextPredicateInputsV1;
// Exact 21c model callback signature, not a native ABI. On unavailable input
// the caller's output is unchanged and no native diagnostic/initializer runs.
bool ReadLoadedD2BE00ContextChild12004(void *, const RawReceiverAccessV1 &,
    const ContextPredicateInputsV1 &, std::uintptr_t &copied_return) noexcept;

} // namespace xar::ck3_12004::construction_owner_mode3
