#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"
#include "xar_bridge/returned_selector_28c2df0_12004.hpp"

#include <cstdint>
#include <optional>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::uintptr_t kConstructionContextPredicateRvaV1 = 0x2C25010;

// Copied operands of the actual 246935F call. The frame is the caller's existing
// paused snapshot revision; no native function is invoked to obtain these.
struct ContextPredicateInputsV1 {
  std::uint64_t frame_key = 0;
  std::uintptr_t slots_pointer = 0;
  std::uintptr_t first_pointer = 0;
  std::uintptr_t raw_receiver_pointer = 0;
  std::uintptr_t selector_object_pointer = 0;
};

// These callbacks implement the source-closed children's memory models. They
// are NOT the native functions' calling conventions or executable addresses.
// false means a required copy/model is unavailable, never native AL == false.
struct ReadContextPredicateChildrenV1 {
  void *context = nullptr;
  bool (*read_30a6080)(void *, const RawReceiverAccessV1 &,
                       const ContextPredicateInputsV1 &, std::uintptr_t,
                       std::uintptr_t, bool &) noexcept = nullptr;
  // The last argument by value is the qword stored in the native stack key;
  // it is not the address of our observer's stack storage.
  bool (*read_a11cc0)(void *, const RawReceiverAccessV1 &,
                       const ContextPredicateInputsV1 &, std::uintptr_t,
                       std::uintptr_t, bool &) noexcept = nullptr;
  bool (*read_28bfc50)(void *, const RawReceiverAccessV1 &,
                       const ContextPredicateInputsV1 &, std::uintptr_t,
                       std::uintptr_t &) noexcept = nullptr;
  bool (*read_d2be00)(void *, const RawReceiverAccessV1 &,
                       const ContextPredicateInputsV1 &,
                       std::uintptr_t &) noexcept = nullptr;
  bool (*read_31c1d10)(void *, const RawReceiverAccessV1 &,
                       const ContextPredicateInputsV1 &, std::uintptr_t,
                       std::uintptr_t, bool &) noexcept = nullptr;
};

enum class ContextPredicateFailureV1 : std::uint8_t {
  none,
  exact_build,
  read_callback,
  copied_operand_binding,
  first_pointer,
  child_30a6080,
  registry_storage,
  registry_id,
  registry_lookup,
  registry_fallback,
  collection_address,
  child_a11cc0,
  child_28bfc50,
  late_context,
  late_ids,
  child_d2be00,
  child_31c1d10,
};

enum class ContextPredicatePathV1 : std::uint8_t {
  unavailable,
  first_child_true,
  collection_child_true,
  late_id_mismatch_false,
  last_child_true,
  last_child_false,
};

struct ConstructionContextPredicateV1 {
  ContextPredicateInputsV1 inputs;
  ContextPredicateFailureV1 failure = ContextPredicateFailureV1::none;
  ContextPredicatePathV1 path = ContextPredicatePathV1::unavailable;
  std::optional<bool> value;
  std::optional<bool> child_30a6080_value;
  std::optional<bool> child_a11cc0_value;
  std::optional<bool> child_31c1d10_value;
  std::uintptr_t registry_storage_pointer = 0;
  std::optional<std::uint32_t> registry_full_id_raw;
  std::uintptr_t selected_registry_object_pointer = 0;
  bool registry_full_id_matched = false;
  std::uintptr_t collection_pointer = 0;
  std::uintptr_t late_receiver_pointer = 0;
  std::uintptr_t late_context_pointer = 0;
  std::optional<std::uint32_t> late_context_id_raw;
  std::optional<std::uint32_t> raw_receiver_id_raw;
  std::uintptr_t singleton_pointer = 0;
};

// Caller owns one admitted paused-frame read boundary across the 06 receiver,
// 04 selector and this reader. The actual raw receiver and copied selector's
// receiver/revision must match. Unknown reached children keep value null;
// missing children on an unreached branch do not reject a known native result.
ConstructionContextPredicateV1 ReadConstructionContextPredicate2C25010V1(
    const RawReceiverAccessV1 &, const AggregateRawReceiverV1 &,
    const ReturnedObject28C2DF0Result12004 &, std::uint64_t snapshot_revision,
    const ReadContextPredicateChildrenV1 &) noexcept;

} // namespace xar::ck3_12004::construction_owner_mode3
