#pragma once

#include "xar_bridge/construction_context_predicate_2c25010_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::uintptr_t kConstructionCollectionPredicateA11CC0RvaV1 =
    0xA11CC0;
inline constexpr std::size_t kConstructionCollectionCopyBoundV1 = 4096;

enum class CollectionPredicateA11CC0FailureV1 : std::uint8_t {
  none,
  exact_build,
  read_callback,
  copied_key_binding,
  header_count,
  header_buffer,
  negative_initial_count,
  copy_bound,
  initial_extent_overflow,
  array_pointer,
  array_read,
  reloaded_count,
  reloaded_buffer,
  copy_exception,
};

// Copied raw operands and source-model result. The observer does not execute
// A11CC0, its AVX child, initialization helpers or a native getter.
struct ConstructionCollectionPredicateA11CC0V1 {
  ContextPredicateInputsV1 inputs;
  std::uintptr_t collection_pointer = 0;
  std::uintptr_t key_qword = 0;
  CollectionPredicateA11CC0FailureV1 failure =
      CollectionPredicateA11CC0FailureV1::none;
  std::optional<std::int32_t> initial_count_raw;
  std::optional<std::uintptr_t> initial_buffer_pointer;
  std::optional<std::uintptr_t> initial_end_pointer;
  std::vector<std::uintptr_t> ordered_qwords;
  bool ordered_qwords_complete = false;
  std::optional<std::uint32_t> first_match_index;
  std::optional<std::uintptr_t> found_pointer;
  std::optional<std::int32_t> reloaded_count_raw;
  std::optional<std::uintptr_t> reloaded_buffer_pointer;
  std::optional<std::uintptr_t> reloaded_end_pointer;
  std::optional<bool> header_unchanged;
  std::optional<bool> value;
};

// The caller supplies21's existing admitted paused-frame Inputs and06 access.
// key_qword is the VALUE of first_pointer, not an observer stack address.
// Initial signed count0 and key0 are legal. A missing read, negative initial
// count or exceeded copy bound leaves value unavailable, never known false.
// The final native-width endpoint comparison is preserved even if the copied
// header changes; an observed header change does not invalidate the frame.
ConstructionCollectionPredicateA11CC0V1
ReadConstructionCollectionPredicateA11CC0V1(
    const RawReceiverAccessV1 &, const ContextPredicateInputsV1 &,
    std::uintptr_t collection_pointer, std::uintptr_t key_qword,
    std::size_t maximum_entries = kConstructionCollectionCopyBoundV1) noexcept;

// Optional adapter trace/budget. A null context uses the default bound and
// needs no additional03 DTO. A combined03 context can call the reader directly
// or forward its dedicated member to this exact21 callback signature.
struct CollectionPredicateA11CC0ReadContextV1 {
  std::size_t maximum_entries = kConstructionCollectionCopyBoundV1;
  ConstructionCollectionPredicateA11CC0V1 *last_result = nullptr;
};

bool ReadConstructionCollectionPredicateA11CC0ChildV1(
    void *, const RawReceiverAccessV1 &, const ContextPredicateInputsV1 &,
    std::uintptr_t collection_pointer, std::uintptr_t key_qword,
    bool &value) noexcept;

} // namespace xar::ck3_12004::construction_owner_mode3
