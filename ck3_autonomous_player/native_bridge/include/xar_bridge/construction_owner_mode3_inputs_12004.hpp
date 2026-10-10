#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"
#include "xar_bridge/construction_owner_mode3_loaded_inputs_12004.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {

inline constexpr std::string_view kMode3InputSourcePin12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

// Every value is a copied same-frame source input or its exact conditional
// software projection. None is an observed invocation of the native producer.
struct Mode3NumericComponentV1 {
  std::uint32_t call_rva = 0;
  std::uint16_t key_u16 = 0;
  bool reached = false;
  std::optional<std::int64_t> raw_q64;
  std::string unavailable_input;
};

struct ConstructionOwnerMode3InputsV1 {
  bool inputs_observed = false;
  bool all_reached_inputs_observed = false;
  std::string unavailable_input;
  std::uint64_t snapshot_revision = 0;
  std::int32_t province_id = -1;
  // Borrowed pointers never leave application-main or enter serialization.
  std::uintptr_t province_pointer = 0, slots_pointer = 0;
  std::uintptr_t context_pointer = 0, context_object_848 = 0;
  std::uintptr_t returned_receiver_pointer = 0;
  std::optional<std::int64_t> loaded_publisher_718_raw;
  std::optional<std::int64_t> loaded_key_3f_raw;
  std::optional<std::uint16_t> selected_a3_or_a4_key;
  std::optional<std::uint16_t> selected_a6_or_a7_key;
  std::optional<std::uint16_t> context_dynamic_key;
  std::optional<std::int32_t> child_28be0b0_signed_eax;
  std::optional<std::int32_t> child_28b9300_signed_eax;
  std::optional<bool> context_predicate_2c25010;
  std::vector<Mode3NumericComponentV1> components;
  std::optional<std::int64_t> factor_before_context;
  std::optional<std::int64_t> context_factor_raw;
  std::optional<std::int64_t> owner_factor_raw;
  std::optional<std::int64_t> conditional_aggregate_raw;
  bool observed_native_producer_call = false;
  bool per_building_attribution = false;
  bool realized_holder_net = false;
};

// The source owners of the two signed-EAX children supply memory-model
// readers. These are deliberately not native CALL ABIs or callable addresses.
struct Mode3SignedEaxChildV1 {
  void *context = nullptr;
  bool (*read)(void *, const RawReceiverAccessV1 &, std::uintptr_t,
               std::uint64_t, std::int32_t &) noexcept = nullptr;
  bool actual_12004_source_closed = false;
};

struct Mode3CurrentInputRequestV1 {
  std::uintptr_t module_base = 0;
  bool exact_12004_bound = false;
  std::uintptr_t province_pointer = 0;
  std::int32_t expected_province_id = -1;
  // The existing CampaignRootFrameV1::snapshot_revision, copied unchanged.
  std::uint64_t snapshot_revision = 0;
};

// The current query owns the complete before/after paused-frame check. This
// reader binds raw pointer bookends to its supplied Province/current frame,
// uses only source-closed memory readers and preserves unavailable operands.
ConstructionOwnerMode3InputsV1 ReadConstructionOwnerMode3InputsV1(
    const LoadedInputAccessV1 &, const Mode3CurrentInputRequestV1 &,
    const Mode3SignedEaxChildV1 &piety_child,
    const Mode3SignedEaxChildV1 &reduction_child);

// Production overload binds the same source owners through readonly models.
ConstructionOwnerMode3InputsV1 ReadConstructionOwnerMode3InputsV1(
    const LoadedInputAccessV1 &, const Mode3CurrentInputRequestV1 &);

} // namespace xar::ck3_12004::construction_owner_mode3
