#pragma once

#include "xar_bridge/construction_collection_predicate_a11cc0_12004.hpp"
#include "xar_bridge/piety_complete_qword_iterator_a11f60_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace xar::ck3_12004::piety_price_raw_inputs {

using OwnedEditReadAccess12004 = construction_owner_mode3::RawReceiverAccessV1;

// Software callbacks to the separately source-closed22e/23e scalar readers.
// They are neither native addresses nor a cache of a later price quotation.
// false leaves the reached EAX unavailable; the output is consumed only true.
using ReadOwnedEditScalar12004 = bool (*)(
    void *, const OwnedEditReadAccess12004 &, std::uintptr_t definition,
    std::uintptr_t current_rite, std::uint64_t unchanged_snapshot_revision,
    std::int32_t &native_eax_raw) noexcept;

struct OwnedEditBasePriceBindings12004 {
  OwnedEditReadAccess12004 access;
  void *first_scalar_context = nullptr;
  ReadOwnedEditScalar12004 read_31d9930 = nullptr;
  void *second_scalar_context = nullptr;
  ReadOwnedEditScalar12004 read_31df3b0 = nullptr;
  std::size_t maximum_entries =
      construction_owner_mode3::kConstructionCollectionCopyBoundV1;
};

enum class OwnedEditPriceArray12004 : std::uint8_t { first, second };

enum class OwnedEditBasePriceFailure12004 : std::uint8_t {
  none,
  exact_build,
  read_callback,
  draft_header,
  negative_draft_count,
  copy_bound,
  draft_extent,
  draft_element,
  current_collection_address,
  first_membership,
  second_membership_header,
  negative_membership_count,
  membership_extent,
  membership_element,
  second_membership_model,
  second_membership_reload,
  scalar_31d9930,
  scalar_31df3b0,
  copy_exception,
};

struct OwnedEditPriceArrayHeader12004 {
  std::optional<std::uintptr_t> pointer_raw;
  std::optional<std::int32_t> count_raw;
};

struct OwnedEditPriceContribution12004 {
  OwnedEditPriceArray12004 array = OwnedEditPriceArray12004::first;
  std::size_t index = 0;
  std::uint64_t definition_qword = 0;
  std::uintptr_t current_collection_identity = 0;
  std::optional<std::uintptr_t> membership_iterator_raw;
  std::optional<std::uintptr_t> membership_reloaded_end_raw;
  std::optional<bool> skip;
  std::optional<std::int32_t> scalar_native_eax_raw;
  std::optional<std::int64_t> scaled_raw_q64;
};

struct OwnedEditBasePrice12004 {
  std::uintptr_t draft_identity = 0;
  std::uintptr_t current_rite_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
  OwnedEditBasePriceFailure12004 failure = OwnedEditBasePriceFailure12004::none;
  OwnedEditPriceArray12004 reached_array = OwnedEditPriceArray12004::first;
  OwnedEditPriceArrayHeader12004 first_header;
  OwnedEditPriceArrayHeader12004 second_header;
  std::vector<OwnedEditPriceContribution12004> reached_occurrences;
  // The zero-initialized output and completed ordered prefix are diagnostic.
  // Only base_price_raw_q64 carries a complete base result.
  std::uint64_t completed_prefix_sum_bits = 0;
  std::optional<std::int64_t> base_price_raw_q64;
  bool complete = false;
};

// Source model of actual2C64710 ->2C665A0 with NULL detail/reason. The caller
// supplies one guarded unchanged source frame, the actual price subdraft and
// current Rite. Revision is retained as a carrier, not a freshness proof.
// First+8/count14 is processed before second+50/count5C; duplicates and full
// QWORDs remain ordered. Only reached membership/scalar dependencies matter.
// No getter, native function, allocator, text formatter or output store runs.
OwnedEditBasePrice12004 ReadOwnedEditBasePrice2C6471012004(
    const OwnedEditBasePriceBindings12004 &, std::uintptr_t draft,
    std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision) noexcept;

} // namespace xar::ck3_12004::piety_price_raw_inputs
