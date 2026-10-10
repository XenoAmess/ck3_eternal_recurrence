#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::uintptr_t kPointerKeyPredicate31C1D10RvaV1 = 0x31C1D10;

enum class PointerKeyPredicateFailureV1 : std::uint8_t {
  none, exact_build, read_callback, entries_pointer, mask,
  address_unrepresentable, probe_control, probe_key, probe_budget,
  end_tail, selected_control,
};
enum class PointerKeyPredicatePathV1 : std::uint8_t {
  unavailable, copied_key_match, copied_end_record,
};

struct PointerKeyPredicate31C1D10V1 {
  std::uintptr_t singleton_pointer = 0;
  std::uintptr_t copied_first_pointer = 0;
  std::size_t maximum_probe_records = 0;
  std::optional<std::uint32_t> pointer_hash_raw_u32;
  std::optional<std::uintptr_t> entries_pointer;
  std::optional<std::int32_t> mask_raw_i32;
  std::optional<std::int64_t> initial_slot_index_i64;
  std::optional<std::uint8_t> probe_distance_raw_u8;
  std::size_t copied_probe_key_count = 0;
  std::optional<std::uint8_t> end_tail_raw_u8;
  std::optional<std::int32_t> end_slot_index_i32;
  std::uintptr_t selected_record_pointer = 0;
  std::optional<std::uint8_t> selected_control_raw_u8;
  PointerKeyPredicatePathV1 path = PointerKeyPredicatePathV1::unavailable;
  PointerKeyPredicateFailureV1 failure = PointerKeyPredicateFailureV1::none;
  // Exactly the consumed native AL predicate: selected control != FF.
  // null means unavailable copied operands/guarded address/budget, not false.
  std::optional<bool> value;
};

// The passed singleton is 28d's copied D2BE00 return, and first_pointer is the
// actual parent's copied RDX pointer key. Zero/high-bit keys are legal raw bits.
// This copies memory only. The caller owns the admitted frame across all leaves.
// maximum_probe_records is an observer operation budget, not a native bound.
PointerKeyPredicate31C1D10V1 ReadPointerKeyPredicate31C1D10V1(
    const RawReceiverAccessV1 &, std::uintptr_t copied_singleton,
    std::uintptr_t copied_first_pointer,
    std::size_t maximum_probe_records = 4096) noexcept;

} // namespace xar::ck3_12004::construction_owner_mode3
