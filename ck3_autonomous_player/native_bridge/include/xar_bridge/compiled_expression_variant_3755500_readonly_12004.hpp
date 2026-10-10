#pragma once

#include "xar_bridge/piety_price_numeric_access_12004.hpp"

#include <array>
#include <optional>
#include <string>

namespace xar::ck3_12004::piety_price_raw_inputs {

// Copied literal R8 operands. A source-defined caller pack has no invented
// physical native stack identity. Optional zero is a copied null pointer;
// nullopt is unavailable. Unused fields never gate a numerical branch.
struct CompiledExpressionVariantPack3755500Readonly12004 {
  std::optional<std::uintptr_t> physical_pack_identity;
  std::optional<std::uintptr_t> primary_scope_identity, secondary_scope_identity;
  std::optional<std::uintptr_t> tertiary_scope_identity, support_identity;
  std::optional<std::uint8_t> evaluation_flag_raw_u8;
};

struct CompiledExpressionVariant3755500Inputs12004 {
  std::uintptr_t expression_list_identity = 0;
  CompiledExpressionVariantPack3755500Readonly12004 copied_pack;
  std::uintptr_t named_tuple_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
};

struct CompiledExpressionVariant3755500Readonly12004 {
  std::uintptr_t module_base = 0, expression_list_identity = 0;
  CompiledExpressionVariantPack3755500Readonly12004 copied_pack;
  std::uintptr_t named_tuple_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
  std::uint8_t argument5_raw_u8 = 0;
  std::int32_t argument6_raw_i32 = 0;
  std::optional<std::int32_t> list_count_before_raw_i32, list_count_after_raw_i32;
  std::optional<std::uintptr_t> primary_scope_before_identity, primary_scope_after_identity;
  bool physical_primary_alias_copied = false;
  std::optional<std::array<std::uint8_t, 16>> incoming_root_before_raw, incoming_root_after_raw;
  std::optional<std::uint16_t> incoming_root_tag_raw_u16;
  std::optional<std::uint16_t> variant_tag_raw_u16;
  std::optional<std::int64_t> variant_payload_raw_q64;
  bool source_result_ready = false;
  bool copied_operand_bookends_equal = false;
  bool named_tuple_numeric_input_demanded = false;
  bool native_method_invoked = false;
  std::optional<std::uintptr_t> list_data_identity, first_row_identity;
  std::optional<std::uintptr_t> provider_receiver_identity, provider_vtable;
  std::optional<std::uintptr_t> type_mask_slot30, value_producer_slot20;
  std::optional<std::uintptr_t> embedded_tuple_first_qword, selected_tuple_identity;
  std::optional<std::array<std::uint8_t, 32>> selected_tuple_before_raw, selected_tuple_after_raw;
  std::string unavailable_reason;
};

// Generic actual3755500 companion for the literal A0F2D6 call with stack5
// BYTE0/stack6 DWORD0. Count0 uses no pack/tuple; negative count uses only the
// primary root16. Positive virtual-provider outputs remain unknown. Revision
// is an unchanged copied carrier, never a numeric prerequisite or new clock.
CompiledExpressionVariant3755500Readonly12004
ReadCompiledExpressionVariant3755500Readonly12004(
    const PietyPriceNumericAccess12004 &,
    const CompiledExpressionVariant3755500Inputs12004 &);

} // namespace xar::ck3_12004::piety_price_raw_inputs
