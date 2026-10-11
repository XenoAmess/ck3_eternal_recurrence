#pragma once

#include "xar_bridge/create_piety_final_price_source_model_12004.hpp"
#include "xar_bridge/rite_piety_price_term_observed_12004.hpp"

#include <bit>
#include <optional>
#include <utility>

namespace xar::ck3_12004::piety_price_raw_inputs {

struct CreatePietyFinalPriceObservedTermObservation12004 {
  CreatePietyFinalPriceSourceObservation12004 source_model;
  std::optional<RitePietyObservedTermAdmission12004> rite_observed_admission;
  std::optional<RitePietyObservedTermExpected12004> rite_observed_expectation;
};

// Insert one observed-term reader at the exact old parent's Rite stage. Other
// source operands remain readonly projections and retain original_values=false.
// This overload neither invokes the quote nor observes/evaluates a new target.
inline CreatePietyFinalPriceObservedTermObservation12004
ReadCreatePietyFinalPriceSourceModel12004(
    const CreatePietyDynamicBaseCostBindings12004& base_bindings,
    std::uintptr_t price_payload, std::uintptr_t current_rite,
    std::uintptr_t actor, std::uint32_t actor_full_id_raw_u32,
    std::uint32_t rite_full_id_carrier_u32,
    std::uint64_t unchanged_snapshot_revision,
    bool source_qualified_actor_fallback,
    const RitePietyObservedTermInputs12004& observed_inputs) {
  CreatePietyFinalPriceObservedTermObservation12004 result;
  auto& out = result.source_model;
  out.price_payload = price_payload;
  out.current_rite = current_rite;
  out.actor = actor;
  out.actor_full_id_raw_u32 = actor_full_id_raw_u32;
  out.rite_full_id_carrier_u32 = rite_full_id_carrier_u32;
  out.unchanged_snapshot_revision = unchanged_snapshot_revision;
  out.source_qualified_actor_fallback = source_qualified_actor_fallback;
  const auto& access = base_bindings.access;

  out.create_base.emplace(ReadCreatePietyDynamicBaseCost12004(
      base_bindings, price_payload, current_rite, unchanged_snapshot_revision));
  if (!out.create_base->complete || !out.create_base->base_price_raw_q64) {
    out.reason = out.create_base->reason;
    return result;
  }
  out.stopped_stage = CreatePietyFinalPriceStage12004::actor_property_223;
  out.actor_property_223.emplace(create_final_price_detail::ReadActorCollectionTerm(
      access, actor, actor_full_id_raw_u32, source_qualified_actor_fallback,
      std::uint32_t{0x223}, unchanged_snapshot_revision));
  if (!out.actor_property_223->source_ready ||
      !out.actor_property_223->scaled_term_raw_q64) {
    out.reason = out.actor_property_223->reason;
    return result;
  }
  const auto entered_bits =
      std::bit_cast<std::uint64_t>(*out.create_base->base_price_raw_q64) +
      std::bit_cast<std::uint64_t>(*out.actor_property_223->scaled_term_raw_q64);
  out.entered_base_with223_bits = entered_bits;
  out.entered_base_with223_raw_q64 = std::bit_cast<std::int64_t>(entered_bits);

  out.stopped_stage = CreatePietyFinalPriceStage12004::rite_term;
  auto observed_term = ReadRitePietyPriceTerm2C628A012004(
      access, current_rite, actor, unchanged_snapshot_revision, observed_inputs);
  out.rite_term.emplace(std::move(observed_term.source_term));
  result.rite_observed_admission = std::move(observed_term.admission);
  result.rite_observed_expectation = std::move(observed_term.expectation);
  if (!out.rite_term->source_ready || !out.rite_term->native_term_raw_q64) {
    out.reason = out.rite_term->reason;
    return result;
  }
  // An admitted individual term may remain diagnostic even if the model's
  // caller supplied a different payload or ID carrier. It cannot complete an
  // aggregate projection using that different source input.
  if (result.rite_observed_admission &&
      result.rite_observed_admission->admitted) {
    const auto& binding = observed_inputs.expected_query_binding;
    if (binding.price_payload_identity !=
            std::optional<std::uintptr_t>{price_payload} ||
        binding.second_actor.resolved_full_id !=
            std::optional<std::uint32_t>{actor_full_id_raw_u32} ||
        binding.current_rite.resolved_full_id !=
            std::optional<std::uint32_t>{rite_full_id_carrier_u32}) {
      out.reason = "observed_rite_model_caller_inputs_mismatch";
      return result;
    }
  }

  // Native selects the actor collection independently a second time.
  out.stopped_stage = CreatePietyFinalPriceStage12004::actor_property_224;
  out.actor_property_224.emplace(create_final_price_detail::ReadActorCollectionTerm(
      access, actor, actor_full_id_raw_u32, source_qualified_actor_fallback,
      std::uint32_t{0x224}, unchanged_snapshot_revision));
  if (!out.actor_property_224->source_ready ||
      !out.actor_property_224->scaled_term_raw_q64) {
    out.reason = out.actor_property_224->reason;
    return result;
  }
  out.final_arithmetic.emplace(ProjectPietyFinalArithmetic2C62CC012004(
      *out.entered_base_with223_raw_q64, *out.rite_term->native_term_raw_q64,
      *out.actor_property_224->scaled_term_raw_q64));
  out.final_piety_price_raw_q64 = out.final_arithmetic->final_piety_price_raw_q64;
  out.source_ready = true;
  out.status = "available";
  out.reason = "create_final_piety_source_arithmetic_complete";
  out.stopped_stage = CreatePietyFinalPriceStage12004::complete;
  return result;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
