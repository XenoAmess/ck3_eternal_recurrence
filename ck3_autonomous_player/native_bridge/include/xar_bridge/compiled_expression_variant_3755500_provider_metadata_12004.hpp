#pragma once

#include "xar_bridge/compiled_expression_variant_3755500_readonly_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {

// Owned metadata for the first positive-count row only. Slot copies are raw
// witnesses: actual3755500 invokes +30, tests its result, and reloads the
// receiver/vptr before the conditional +20 invocation. Neither invocation nor
// a stable invocation target follows from these existing read-only copies.
struct CompiledExpressionVariant3755500ProviderMetadata12004 {
  std::uintptr_t module_base = 0, expression_list_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
  CompiledExpressionVariantPack3755500Readonly12004 copied_parent_pack;
  std::optional<std::int32_t> list_count_before_raw_i32, list_count_after_raw_i32;
  std::optional<std::uintptr_t> list_data_identity, first_row_identity;
  std::optional<std::uintptr_t> provider_receiver_identity, provider_vtable;
  std::optional<std::uintptr_t> type_mask_slot30_raw_va, value_slot20_raw_va;
  // A fitted VA-minus-module difference. Exact image membership and a body
  // at this candidate RVA remain unqualified; no code bytes are read.
  std::optional<std::uint32_t> value_slot20_module_relative_rva_candidate;
  bool value_target_image_membership_qualified = false;
  bool value_target_body_qualified = false;
  bool provider_target_bookends_observed = false;
  std::uintptr_t original_named_tuple_identity = 0;
  std::optional<std::uintptr_t> embedded_tuple_first_qword, selected_tuple_identity;
  std::optional<std::array<std::uint8_t, 32>> selected_tuple_before_raw, selected_tuple_after_raw;
  std::optional<bool> original_named_tuple_selected_as_numeric_input;
  std::optional<std::uintptr_t> primary_scope_before_identity, primary_scope_after_identity;
  std::optional<std::array<std::uint8_t, 16>> incoming_root_before_raw, incoming_root_after_raw;
  bool source_operand_bookends_equal = false;
  std::string source_operand_unavailable_reason;
  // These stay nullable. Projecting a slot never supplies the +30 predicate,
  // the later +20 dispatch target, or its returned variant16.
  std::optional<bool> actual_value_call_reached;
  std::optional<std::uintptr_t> actual_value_call_target_va;
  std::optional<std::uint16_t> returned_variant_tag_raw_u16;
  std::optional<std::int64_t> returned_variant_payload_raw_q64;
  bool source_result_ready = false;
  bool provider_method_invoked_by_projector = false;
  std::string unavailable_reason;
};

// No access callback, second source-reader invocation, provider execution,
// image acquisition, or revision/role/clock gate. Absent or nonpositive copied
// count yields nullopt. Positive incomplete copies yield an incomplete record.
std::optional<CompiledExpressionVariant3755500ProviderMetadata12004>
ProjectCompiledExpressionVariant3755500ProviderMetadata12004(
    const CompiledExpressionVariant3755500Readonly12004 &);

} // namespace xar::ck3_12004::piety_price_raw_inputs
