#pragma once

#include "xar_bridge/construction_owner_mode3_loaded_inputs_12004.hpp"

#include <cstdint>
#include <optional>

namespace xar::ck3_12004::construction_owner_mode3 {

enum class ScaledCollectionKeyFailure12004 : std::uint8_t {
  none, exact_build, read_callback, detail_branch_not_supplied,
  selector_branch_not_supplied, collection, count_read, negative_count,
  keys_read, probe_read, values_read, selected_value_read, source_changed,
};

enum class ScaledCollectionKeySelection12004 : std::uint8_t {
  unavailable, factor_zero, key_sentinel, count_zero, key_absent, mapped,
};

struct ScaledCollectionKey12004 {
  bool ready = false;
  ScaledCollectionKeyFailure12004 failure = ScaledCollectionKeyFailure12004::none;
  ScaledCollectionKeySelection12004 selection = ScaledCollectionKeySelection12004::unavailable;
  std::uintptr_t collection_identity = 0;
  std::uintptr_t pc_identity = 0;
  std::uint32_t incoming_key_raw_u32 = 0;
  std::uint16_t property_key_u16 = 0;
  std::uintptr_t detail_identity = 0;
  std::int32_t selector_raw_i32 = 0;
  std::int64_t factor_raw_q64 = 0;
  std::optional<std::int32_t> pc_count_i32;
  std::optional<std::uint32_t> selected_index_u32;
  std::optional<std::int64_t> selected_value_raw_q64;
  std::optional<std::int64_t> scaled_value_raw_q64;
  std::uint32_t binary_probe_count = 0;
};

// Source-evaluated selected scalar from an already bound current source frame.
// Actual2C4D530 fifth-factor zero bypasses the collection/detail paths. Otherwise
// this independent API owns only the reached NULL-detail / selector0 branch.
// Caller03/17 retains the real receiver/owner/frame association independently.
// No native getter, formatter, initializer, counter or notification is invoked.
ScaledCollectionKey12004 ReadScaledCollectionKey12004(
    const LoadedInputAccessV1 &access, std::uintptr_t collection,
    std::uint32_t raw_key, std::int64_t factor_raw,
    std::uintptr_t detail = 0, std::int32_t selector = 0);

} // namespace xar::ck3_12004::construction_owner_mode3
