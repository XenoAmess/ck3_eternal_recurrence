#pragma once

#include "xar_bridge/collection_piety_price_term_2c4d660_12004.hpp"
#include "xar_bridge/conception_modifier_context_12004.hpp"
#include "xar_bridge/create_piety_dynamic_base_cost_12004.hpp"
#include "xar_bridge/piety_final_arithmetic_2c62cc0_12004.hpp"
#include "xar_bridge/rite_piety_price_term_2c628a0_readonly_12004.hpp"

#include <bit>
#include <limits>
#include <optional>
#include <string>
#include <utility>

namespace xar::ck3_12004::piety_price_raw_inputs {

enum class CreatePietyFinalPriceStage12004 {
  create_base, actor_property_223, rite_term, actor_property_224, complete
};

struct ActorPietyCollectionTermObservation12004 {
  std::uint32_t requested_key_raw_u32{};
  std::optional<ConceptionModifierContextObservation12004> collection_selection;
  std::optional<CollectionPietyPriceTerm2C4D660Result12004> collection_term;
  bool collection_still_current{};
  bool source_ready{};
  std::optional<std::int64_t> scaled_term_raw_q64;
  std::string reason{"not_read"};
};

struct CreatePietyFinalPriceSourceObservation12004 {
  bool source_ready{};
  bool actual_original_consumed_values{};
  const char* status{"unavailable"};
  std::string reason{"not_read"};
  CreatePietyFinalPriceStage12004 stopped_stage{
      CreatePietyFinalPriceStage12004::create_base};
  std::uintptr_t price_payload{}, current_rite{}, actor{};
  std::uint32_t actor_full_id_raw_u32{}, rite_full_id_carrier_u32{};
  std::uint64_t unchanged_snapshot_revision{};
  bool source_qualified_actor_fallback{};
  std::optional<CreatePietyDynamicBaseCostObservation12004> create_base;
  std::optional<ActorPietyCollectionTermObservation12004> actor_property_223;
  std::optional<std::uint64_t> entered_base_with223_bits;
  std::optional<std::int64_t> entered_base_with223_raw_q64;
  std::optional<RitePietyPriceTerm2C628A012004> rite_term;
  std::optional<ActorPietyCollectionTermObservation12004> actor_property_224;
  std::optional<PietyFinalArithmetic2C62CC0Observation12004> final_arithmetic;
  std::optional<std::int64_t> final_piety_price_raw_q64;
};

namespace create_final_price_detail {

// Adapt the same common guarded reader to the existing actual28C3AC0 model.
// Context points to a local access copy for the synchronous Resolve/Check only.
inline bool ReadModifierMemory(void* context, std::uintptr_t address,
                               void* output, std::size_t bytes) noexcept {
  const auto& access = *static_cast<const PietyPriceNumericAccess12004*>(context);
  if (!access.exact_12004_bound || !access.guarded_read || !address ||
      (bytes && bytes - 1 >
          (std::numeric_limits<std::uintptr_t>::max)() - address)) return false;
  return access.guarded_read(access.context,
      reinterpret_cast<const void*>(address), output, bytes);
}

inline ActorPietyCollectionTermObservation12004 ReadActorCollectionTerm(
    const PietyPriceNumericAccess12004& access,
    std::uintptr_t actor, std::uint32_t physical_actor_id,
    bool source_qualified_actor_fallback, std::uint32_t key,
    std::uint64_t revision) {
  ActorPietyCollectionTermObservation12004 out;
  out.requested_key_raw_u32 = key;
  auto modifier_access = access;
  const ConceptionModifierContextBindings12004 modifier_bindings{
      access.exact_12004_bound && access.guarded_read != nullptr,
      access.module_base, ReadModifierMemory, &modifier_access};
  out.collection_selection.emplace(ResolveRawCharacterModifierContext12004(
      modifier_bindings, actor, physical_actor_id,
      source_qualified_actor_fallback));
  if (!out.collection_selection->ready) {
    out.reason = out.collection_selection->reason;
    return out;
  }
  out.collection_term.emplace(ReadCollectionPietyPriceTerm2C4D66012004(
      access, out.collection_selection->context_address, key,
      std::int64_t{100000}, revision));
  if (!out.collection_term->source_ready ||
      !out.collection_term->scaled_term_raw_q64) {
    out.reason = std::string(out.collection_term->unavailable_reason);
    return out;
  }
  out.collection_still_current = CheckRawCharacterModifierContextStillCurrent12004(
      modifier_bindings, *out.collection_selection, physical_actor_id,
      source_qualified_actor_fallback, out.reason);
  if (!out.collection_still_current) return out;
  out.scaled_term_raw_q64 = out.collection_term->scaled_term_raw_q64;
  out.source_ready = true;
  out.reason = "actor_collection_piety_term_copied";
  return out;
}

} // namespace create_final_price_detail

// Actual2C64BB0 false-edit/mode0/detailNULL numeric composition. Native order
// is base, key0x223, Rite term, key0x224, final fixed arithmetic. The owning
// caller supplies the original resolved receiver/draft/Rite and stable frame.
// Full revision and Rite ID are carriers; they are not freshness witnesses.
// This source model never calls the native getter or publishes a native quote.
inline CreatePietyFinalPriceSourceObservation12004
ReadCreatePietyFinalPriceSourceModel12004(
    const CreatePietyDynamicBaseCostBindings12004& base_bindings,
    std::uintptr_t price_payload, std::uintptr_t current_rite,
    std::uintptr_t actor, std::uint32_t actor_full_id_raw_u32,
    std::uint32_t rite_full_id_carrier_u32,
    std::uint64_t unchanged_snapshot_revision,
    bool source_qualified_actor_fallback = false) {
  CreatePietyFinalPriceSourceObservation12004 out;
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
    return out;
  }

  out.stopped_stage = CreatePietyFinalPriceStage12004::actor_property_223;
  out.actor_property_223.emplace(create_final_price_detail::ReadActorCollectionTerm(
      access, actor, actor_full_id_raw_u32, source_qualified_actor_fallback,
      std::uint32_t{0x223}, unchanged_snapshot_revision));
  if (!out.actor_property_223->source_ready ||
      !out.actor_property_223->scaled_term_raw_q64) {
    out.reason = out.actor_property_223->reason;
    return out;
  }
  const auto entered_bits =
      std::bit_cast<std::uint64_t>(*out.create_base->base_price_raw_q64) +
      std::bit_cast<std::uint64_t>(*out.actor_property_223->scaled_term_raw_q64);
  out.entered_base_with223_bits = entered_bits;
  out.entered_base_with223_raw_q64 = std::bit_cast<std::int64_t>(entered_bits);

  out.stopped_stage = CreatePietyFinalPriceStage12004::rite_term;
  out.rite_term.emplace(ReadRitePietyPriceTerm2C628A012004(
      access, current_rite, actor, unchanged_snapshot_revision));
  if (!out.rite_term->source_ready || !out.rite_term->native_term_raw_q64) {
    out.reason = out.rite_term->reason;
    return out;
  }

  // The actual final-price helper calls the actor selector again. Its result
  // need not equal the key0x223 selection and is never cached across calls.
  out.stopped_stage = CreatePietyFinalPriceStage12004::actor_property_224;
  out.actor_property_224.emplace(create_final_price_detail::ReadActorCollectionTerm(
      access, actor, actor_full_id_raw_u32, source_qualified_actor_fallback,
      std::uint32_t{0x224}, unchanged_snapshot_revision));
  if (!out.actor_property_224->source_ready ||
      !out.actor_property_224->scaled_term_raw_q64) {
    out.reason = out.actor_property_224->reason;
    return out;
  }

  // Negative/zero entered base still reaches both child terms, just as native.
  out.final_arithmetic.emplace(ProjectPietyFinalArithmetic2C62CC012004(
      *out.entered_base_with223_raw_q64, *out.rite_term->native_term_raw_q64,
      *out.actor_property_224->scaled_term_raw_q64));
  out.final_piety_price_raw_q64 = out.final_arithmetic->final_piety_price_raw_q64;
  out.source_ready = true;
  out.status = "available";
  out.reason = "create_final_piety_source_arithmetic_complete";
  out.stopped_stage = CreatePietyFinalPriceStage12004::complete;
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
