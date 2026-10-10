#pragma once

#include "xar_bridge/piety_price_a0f0b0_readonly_12004.hpp"
#include "xar_bridge/piety_price_named_definition_37540b0_readonly_12004.hpp"
#include "xar_bridge/piety_fixed_rounded_i32_37498a0_12004.hpp"
#include "xar_bridge/compiled_expression_variant_3755500_readonly_12004.hpp"
#include "xar_bridge/compiled_expression_variant_3755500_provider_metadata_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {

// A supplied actual A0F185 output belongs only to the expression+B0 virtual
// branch. It never supplies or replaces a3755500 positive-list result.
// Identities/operands must match the copied parent; their agreement alone
// does not observe a native output or prove freshness.
// An observed physical pack carrier must be present in both copies; two
// unavailable carriers never bind a supplied provider output.
struct PietyPriceProviderA0F185Output12004 {
  std::uintptr_t expression_identity = 0, provider_identity = 0;
  std::uintptr_t receiver_identity = 0, callback_identity = 0;
  CompiledExpressionVariantPack3755500Readonly12004 copied_pack;
  std::uintptr_t original_named_tuple_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
  std::optional<std::int64_t> actual_output_raw_q64;
};

struct PietyPriceA0F0B0DynamicInputs12004 {
  std::uintptr_t expression_identity = 0;
  CompiledExpressionVariantPack3755500Readonly12004 copied_pack;
  std::uintptr_t original_named_tuple_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
  std::optional<PietyPriceProviderA0F185Output12004> provider_output;
};

struct PietyPriceA0F0B0DynamicReadonly12004 {
  std::uintptr_t module_base = 0, expression_identity = 0;
  CompiledExpressionVariantPack3755500Readonly12004 copied_pack;
  std::uintptr_t original_named_tuple_identity = 0;
  std::uint64_t unchanged_snapshot_revision = 0;
  PietyPriceA0F0B0Readonly12004 source_classifier;
  std::optional<std::int32_t> mode_raw_i32, mode_after_raw_i32;
  std::optional<std::uintptr_t> provider_before_identity, provider_after_identity;
  std::optional<std::uintptr_t> provider_receiver_identity, provider_vtable;
  std::optional<std::uintptr_t> provider_slot30, provider_vtable_after, provider_slot30_after;
  std::optional<std::uintptr_t> named_before_identity, named_after_identity;
  std::optional<std::int32_t> count_before_raw_i32, count_after_raw_i32;
  std::optional<std::int32_t> fallback_before_raw_i32, fallback_after_raw_i32;
  std::optional<PietyPriceNamedDefinition37540B0Readonly12004> named_source;
  std::optional<PietyFixedRoundedI3237498A012004> provider_conversion;
  std::optional<CompiledExpressionVariant3755500Readonly12004> variant_source;
  // Raw copied positive-row metadata; no provider call or returned value.
  std::optional<CompiledExpressionVariant3755500ProviderMetadata12004> compiled_provider_metadata;
  bool provider_output_conditionally_supplied = false;
  std::optional<std::int32_t> eax_raw_i32;
  std::string unavailable_reason;
};

// Literal R8 is zero. The unique static40 reader is reused unchanged.
// Dynamic routes use only reached header operands and owned44/48/64 leaves.
// Missing providers/pack operands retain unknown. Native evaluation,
// profiling and diagnostic effects are neither invoked nor claimed.
PietyPriceA0F0B0DynamicReadonly12004 ReadPietyPriceA0F0B0DynamicReadonly12004(
    const PietyPriceNumericAccess12004 &access,
    const PietyPriceA0F0B0DynamicInputs12004 &inputs);

} // namespace xar::ck3_12004::piety_price_raw_inputs
