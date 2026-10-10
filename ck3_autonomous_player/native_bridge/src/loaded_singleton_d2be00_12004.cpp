#include "xar_bridge/loaded_singleton_d2be00_12004.hpp"
#include "xar_bridge/construction_context_predicate_2c25010_12004.hpp"

namespace xar::ck3_12004::construction_owner_mode3 {

LoadedD2BE00Singleton12004 ReadLoadedD2BE00Singleton12004(
    const RawReceiverAccessV1 &access, std::uint64_t snapshot_revision) noexcept {
  static_assert(sizeof(std::uintptr_t) == 8);
  LoadedD2BE00Singleton12004 result;
  result.frame_key = snapshot_revision;
  if (!access.exact_12004_bound) {
    result.failure = LoadedSingletonFailure12004::exact_build;
    return result;
  }
  if (access.read_memory == nullptr) {
    result.failure = LoadedSingletonFailure12004::read_callback;
    return result;
  }
  if (!RawReceiverAddV1(access.module_base, kLoadedSingletonSlotRva12004,
                       result.copied_slot_address)) {
    result.failure = LoadedSingletonFailure12004::slot_address;
    return result;
  }
  std::uintptr_t copied = 0;
  try {
    if (!RawReceiverReadV1(access, access.module_base,
                          kLoadedSingletonSlotRva12004, copied)) {
      result.failure = LoadedSingletonFailure12004::slot_read;
      return result;
    }
  } catch (...) {
    result.failure = LoadedSingletonFailure12004::slot_read;
    return result;
  }
  result.singleton_slot_raw = copied;
  result.nonnull_branch_admitted = copied != 0;
  if (copied == 0) {
    result.failure = LoadedSingletonFailure12004::singleton_not_loaded;
    return result;
  }
  // Actual D2BE0E skips all null-path work and returns this loaded RAX.
  result.conditional_return_pointer = copied;
  result.source_ready = true;
  return result;
}

bool ReadLoadedD2BE00ContextChild12004(void *, const RawReceiverAccessV1 &access,
    const ContextPredicateInputsV1 &inputs,
    std::uintptr_t &copied_return) noexcept {
  const auto result = ReadLoadedD2BE00Singleton12004(access, inputs.frame_key);
  if (!result.source_ready || !result.conditional_return_pointer) return false;
  copied_return = *result.conditional_return_pointer;
  return true;
}

} // namespace xar::ck3_12004::construction_owner_mode3
