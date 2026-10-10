#pragma once

#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"

#include <array>

namespace xar::ck3_12004 {

// Conditional projection of the real 9D7252 ->3755500 call. The list receiver
// is lane+8, R8 is the supplied internal alias shape, R9 is the descriptor,
// and the actual fifth BYTE and sixth DWORD arguments are both zero.
struct PrisonerCostVariant3755500Arguments12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uintptr_t receiver_identity = 0;
  PrisonerQuoteInternalAliases12004 internal_aliases;
  std::uintptr_t descriptor_identity = 0;
};

struct PrisonerCostVariant3755500Readonly12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uintptr_t receiver_identity = 0, descriptor_identity = 0;
  PrisonerQuoteInternalAliases12004 internal_aliases;
  std::uintptr_t callback_identity = 0;
  std::uint32_t consumer_callsite_rva = 0x9D7252;
  std::uint8_t argument5_raw_u8 = 0;
  std::int32_t argument6_raw_i32 = 0;
  bool same_frame_confirmed = false;
  bool conditional_value_only = true;
  bool native_method_invoked = false;
  bool source_result_ready = false;
  std::optional<std::uint16_t> variant_tag_raw_u16;
  std::optional<std::int64_t> variant_payload_raw_q64, numeric_raw_q64;
  std::optional<std::int32_t> list_count_raw_i32, list_count_after_raw_i32;
  std::optional<std::uintptr_t> list_data_identity;
  std::optional<std::array<std::uint8_t, 16>> incoming_root_raw;
  std::optional<std::uintptr_t> first_row_identity, expression_receiver_identity;
  std::optional<std::uintptr_t> expression_vtable, expression_type_mask_slot30;
  std::optional<std::uintptr_t> expression_value_slot20;
  std::optional<std::uintptr_t> embedded_descriptor_first_qword;
  std::optional<std::uintptr_t> selected_descriptor_identity;
  std::optional<std::array<std::uint8_t, 32>> selected_descriptor_raw;
  std::string unavailable_reason;
};

// No native method, script evaluator, clock, or current/history journal is
// called. A nonempty dynamic producer is unknown until its actual target has
// its own closed source contract. Unknown is distinct from a known tag0.
PrisonerCostVariant3755500Readonly12004
ReadPrisonerCostVariant3755500Readonly12004(
    const PrisonerQuoteReadOnlyAccess12004 &,
    const PrisonerCostVariant3755500Arguments12004 &);

} // namespace xar::ck3_12004
