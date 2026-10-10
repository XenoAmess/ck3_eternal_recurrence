#pragma once

#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"
#include "xar_bridge/prisoner_cost_variant_3755500_readonly_12004.hpp"

namespace xar::ck3_12004 {

// Actual310CF66 always supplies R9=0. The original descriptor is the fifth
// argument. Internal aliases can be a source-defined copied shape; a physical
// stack identity is never manufactured for it.
struct PrisonerCostLane9D7060Arguments12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uintptr_t lane_identity = 0;
  PrisonerQuoteInternalAliases12004 internal_aliases;
  std::uintptr_t descriptor_identity = 0;
};

// A source-derived producer supplies this only after closing its consumed raw
// inputs. These identities bind the conditional result to the same lane and
// source frame. Merely copying a slot pointer does not produce a return value.
struct PrisonerCostLaneConditionalResult12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uintptr_t lane_identity = 0;
  PrisonerQuoteInternalAliases12004 internal_aliases;
  std::uintptr_t descriptor_identity = 0;
  std::uintptr_t receiver_identity = 0;
  std::uintptr_t callback_identity = 0;
  std::uintptr_t consumer_callsite_rva = 0;
  bool source_result_ready = false;
  std::optional<std::uint16_t> variant_tag_u16;
  std::optional<std::int64_t> result_q64;
};

struct PrisonerCostLane9D7060Readonly12004 {
  std::uintptr_t lane_identity = 0;
  std::optional<std::int32_t> mode_c0_i32;
  std::optional<std::uintptr_t> provider_b8_identity;
  std::optional<std::uintptr_t> provider_receiver_identity;
  std::optional<std::uintptr_t> provider_vtable_identity;
  std::optional<std::uintptr_t> provider_slot30_identity;
  std::optional<std::uintptr_t> named_a8_identity;
  std::optional<PrisonerNamedFixedReadonly12004> named;
  std::optional<std::int32_t> expression_count_14_i32;
  std::optional<PrisonerCostVariant3755500Readonly12004> variant;
  std::optional<std::uint16_t> variant_tag_u16;
  std::optional<std::int64_t> fallback_98_q64;
  std::optional<std::int64_t> raw_temp_q64;
  std::string branch = "unavailable";
  std::string unavailable_reason;
};

// Memory-only projection of every output branch reached by the actual null-R9
// parent. It returns the raw temporary Q64; parent310CEC0 owns accumulation,
// clamping and rounding. It invokes no evaluator, virtual callback or cleanup.
PrisonerCostLane9D7060Readonly12004 ReadPrisonerCostLane9D7060Readonly12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerCostLane9D7060Arguments12004 &arguments,
    const PrisonerCostLaneConditionalResult12004 *conditional_result = nullptr) noexcept;

} // namespace xar::ck3_12004
