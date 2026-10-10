#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {

// A source-qualified guarded-memory child adapter. This is an independent
// reader interface, never the native CALL ABI or a native getter.
struct ReadContextScalarChild2C4D1D0V1 {
  void *context = nullptr;
  bool (*read_raw_qword)(void *, const RawReceiverAccessV1 &,
                         std::uintptr_t character, std::uint16_t key,
                         std::uintptr_t detail, std::int64_t scale,
                         std::int64_t &raw_qword) noexcept = nullptr;
  bool actual_12004_source_closed = false;
};

enum class ContextScalarFailureV1 : std::uint8_t {
  none,
  exact_build,
  read_callback,
  detail_route,
  collection,
  occurrence_limit,
  title_globals,
  title_registry,
  title_fields,
  character_registry,
  character_fields,
  child_unavailable,
  allocation,
};

struct ContextScalarOccurrenceV1 {
  std::size_t index = 0;
  std::uintptr_t referenced_pointer = 0;
  std::uint32_t requested_title_full_id = 0;
  std::uintptr_t title_pointer = 0;
  std::uint8_t title_branch_byte = 0;
  std::optional<std::uint32_t> secondary_title_full_id;
  std::optional<std::uintptr_t> secondary_title_pointer;
  std::optional<std::uint32_t> character_full_id;
  std::optional<std::uintptr_t> character_pointer;
  std::optional<std::uintptr_t> domain_pointer;
  std::optional<std::uint32_t> candidate_full_id;
  bool used_first_title_candidate = false;
  bool skipped_sentinel = false;
  std::optional<std::size_t> unique_index;
};

struct ContextScalarChildOperandV1 {
  std::uint32_t requested_character_full_id = 0;
  std::uintptr_t character_pointer = 0;
  bool registry_matched = false;
  std::optional<std::int64_t> raw_qword;
};

struct ContextScalarResultV1 {
  bool observed = false;
  ContextScalarFailureV1 failure = ContextScalarFailureV1::none;
  std::optional<std::int64_t> raw_qword;
  std::uintptr_t context_pointer = 0;
  std::uint16_t key_u16 = 0;
  std::uintptr_t detail_pointer = 0;
  std::optional<std::int32_t> collection_count;
  std::uintptr_t collection_data_pointer = 0;
  std::vector<ContextScalarOccurrenceV1> occurrences;
  std::vector<std::uint32_t> ordered_unique_full_ids;
  std::vector<ContextScalarChildOperandV1> child_operands;
};

// Same-frame context is the actual R8 from2468E5A/2468F50 ([slots+848]).
// Only the reached detailNULL route is closed. A negative/oversized count or
// unavailable branch-required operand remains unknown, never native zero.
// Each unique complete DWORD is resolved again for CALL2C82664 in source
// order, with uint16 key/detail0/scale100000. Sum preserves qword bit wrap.
ContextScalarResultV1 ReadContextScalar2C82340V1(
    const RawReceiverAccessV1 &access, std::uintptr_t context,
    std::uint16_t key, std::uintptr_t detail,
    const ReadContextScalarChild2C4D1D0V1 &child,
    std::size_t maximum_occurrences = 4096) noexcept;

} // namespace xar::ck3_12004::construction_owner_mode3
