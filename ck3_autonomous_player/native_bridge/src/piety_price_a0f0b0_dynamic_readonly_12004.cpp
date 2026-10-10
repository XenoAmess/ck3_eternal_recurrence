#include "xar_bridge/piety_price_a0f0b0_dynamic_readonly_12004.hpp"

#include <bit>
#include <limits>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {

template <class T>
std::optional<T> ReadOperand(const PietyPriceNumericAccess12004 &access,
                            std::uintptr_t receiver, std::size_t offset = 0) {
  T value{};
  if (!ReadPietyPriceNumericField12004(access, receiver, offset, value)) return {};
  return value;
}

bool SamePack(const CompiledExpressionVariantPack3755500Readonly12004 &a,
              const CompiledExpressionVariantPack3755500Readonly12004 &b) {
  return a.physical_pack_identity == b.physical_pack_identity &&
      a.primary_scope_identity == b.primary_scope_identity &&
      a.secondary_scope_identity == b.secondary_scope_identity &&
      a.tertiary_scope_identity == b.tertiary_scope_identity &&
      a.support_identity == b.support_identity &&
      a.evaluation_flag_raw_u8 == b.evaluation_flag_raw_u8;
}

// Exact A0F2E2..2FE: signedMUL constant, highhalf SAR14, add signbit.
// Unsigned limb arithmetic preserves native two's-complement bit operations.
std::int32_t ProjectVariantPayload(std::int64_t raw) noexcept {
  constexpr std::uint64_t multiplier = 0x29F16B11C6D1E109ULL;
  constexpr std::uint64_t low_mask = 0xFFFFFFFFULL;
  const auto bits = std::bit_cast<std::uint64_t>(raw);
  const auto a0 = bits & low_mask, a1 = bits >> 32;
  const auto b0 = multiplier & low_mask, b1 = multiplier >> 32;
  const auto w0 = a0 * b0;
  const auto t = a1 * b0 + (w0 >> 32);
  const auto w1 = a0 * b1 + (t & low_mask);
  auto high = a1 * b1 + (t >> 32) + (w1 >> 32);
  if (raw < 0) high -= multiplier;
  const auto shifted = (high >> 14) |
      ((high >> 63) != 0 ? (~std::uint64_t{0} << 50) : std::uint64_t{0});
  const auto corrected = shifted + (shifted >> 63);
  return std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(corrected));
}

bool RecopyReachedParent(const PietyPriceNumericAccess12004 &access,
                         PietyPriceA0F0B0DynamicReadonly12004 &out) {
  out.mode_after_raw_i32 = ReadOperand<std::int32_t>(access, out.expression_identity, 0xB8);
  out.provider_after_identity = ReadOperand<std::uintptr_t>(access, out.expression_identity, 0xB0);
  if (!out.mode_after_raw_i32 || out.mode_after_raw_i32 != out.mode_raw_i32 ||
      !out.provider_after_identity || out.provider_after_identity != out.provider_before_identity) {
    out.unavailable_reason = "piety_dynamic_mode_or_provider_changed_or_unavailable";
    return false;
  }
  if (out.named_before_identity) {
    out.named_after_identity = ReadOperand<std::uintptr_t>(access, out.expression_identity, 0xA0);
    if (!out.named_after_identity || out.named_after_identity != out.named_before_identity) {
      out.unavailable_reason = "piety_dynamic_named_operand_changed_or_unavailable";
      return false;
    }
  }
  if (out.count_before_raw_i32) {
    out.count_after_raw_i32 = ReadOperand<std::int32_t>(access, out.expression_identity, 0x14);
    if (!out.count_after_raw_i32 || out.count_after_raw_i32 != out.count_before_raw_i32) {
      out.unavailable_reason = "piety_dynamic_count_changed_or_unavailable";
      return false;
    }
  }
  if (out.fallback_before_raw_i32) {
    out.fallback_after_raw_i32 = ReadOperand<std::int32_t>(access, out.expression_identity, 0x98);
    if (!out.fallback_after_raw_i32 || out.fallback_after_raw_i32 != out.fallback_before_raw_i32) {
      out.unavailable_reason = "piety_dynamic_fallback_changed_or_unavailable";
      return false;
    }
  }
  if (out.provider_output_conditionally_supplied) {
    out.provider_vtable_after = ReadOperand<std::uintptr_t>(access, *out.provider_receiver_identity);
    if (out.provider_vtable_after && *out.provider_vtable_after != 0)
      out.provider_slot30_after = ReadOperand<std::uintptr_t>(access, *out.provider_vtable_after, 0x30);
    if (!out.provider_vtable_after || out.provider_vtable_after != out.provider_vtable ||
        !out.provider_slot30_after || out.provider_slot30_after != out.provider_slot30) {
      out.unavailable_reason = "piety_dynamic_provider_target_changed_or_unavailable";
      return false;
    }
  }
  return true;
}

} // namespace

PietyPriceA0F0B0DynamicReadonly12004 ReadPietyPriceA0F0B0DynamicReadonly12004(
    const PietyPriceNumericAccess12004 &access,
    const PietyPriceA0F0B0DynamicInputs12004 &inputs) {
  PietyPriceA0F0B0DynamicReadonly12004 out{};
  out.module_base = access.module_base;
  out.expression_identity = inputs.expression_identity;
  out.copied_pack = inputs.copied_pack;
  out.original_named_tuple_identity = inputs.original_named_tuple_identity;
  out.unchanged_snapshot_revision = inputs.unchanged_snapshot_revision;
  out.source_classifier = ReadPietyPriceA0F0B0Readonly12004(
      access, inputs.expression_identity, inputs.unchanged_snapshot_revision);
  out.mode_raw_i32 = out.source_classifier.mode_raw_i32;
  if (!out.mode_raw_i32 || *out.mode_raw_i32 == 0) {
    out.eax_raw_i32 = out.source_classifier.eax_raw_i32;
    out.unavailable_reason = out.source_classifier.unavailable_reason;
    return out;
  }

  out.provider_before_identity = ReadOperand<std::uintptr_t>(access, inputs.expression_identity, 0xB0);
  if (!out.provider_before_identity) {
    out.unavailable_reason = "piety_dynamic_provider_pointer_unavailable";
    return out;
  }
  if (*out.provider_before_identity != 0) {
    std::optional<std::int64_t> raw_q64;
    if (*out.provider_before_identity <= (std::numeric_limits<std::uintptr_t>::max)() - 8) {
      out.provider_receiver_identity = *out.provider_before_identity + 8;
      out.provider_vtable = ReadOperand<std::uintptr_t>(access, *out.provider_receiver_identity);
      if (out.provider_vtable && *out.provider_vtable != 0)
        out.provider_slot30 = ReadOperand<std::uintptr_t>(access, *out.provider_vtable, 0x30);
    }
    if (inputs.provider_output) {
      const auto &witness = *inputs.provider_output;
      if (out.provider_receiver_identity && out.provider_slot30 && *out.provider_slot30 != 0 &&
          inputs.copied_pack.physical_pack_identity.has_value() &&
          witness.copied_pack.physical_pack_identity.has_value() &&
          witness.expression_identity == inputs.expression_identity &&
          witness.provider_identity == *out.provider_before_identity &&
          witness.receiver_identity == *out.provider_receiver_identity &&
          witness.callback_identity == *out.provider_slot30 &&
          witness.original_named_tuple_identity == inputs.original_named_tuple_identity &&
          witness.unchanged_snapshot_revision == inputs.unchanged_snapshot_revision &&
          SamePack(witness.copied_pack, inputs.copied_pack) && witness.actual_output_raw_q64) {
        raw_q64 = witness.actual_output_raw_q64;
        out.provider_output_conditionally_supplied = true;
      }
    }
    // Actual A0F18B passes the tempQWORD scalar; it is not a variant pointer.
    out.provider_conversion = ProjectPietyFixedRoundedI3237498A012004(
        access, raw_q64, inputs.original_named_tuple_identity, inputs.unchanged_snapshot_revision);
    out.eax_raw_i32 = out.provider_conversion->eax_raw_i32;
    if (!out.eax_raw_i32) out.unavailable_reason = inputs.provider_output && !raw_q64
        ? "piety_dynamic_provider_output_binding_unavailable"
        : out.provider_conversion->unavailable_reason;
  } else {
    out.named_before_identity = ReadOperand<std::uintptr_t>(access, inputs.expression_identity, 0xA0);
    if (!out.named_before_identity) {
      out.unavailable_reason = "piety_dynamic_named_pointer_unavailable";
      return out;
    }
    if (*out.named_before_identity != 0) {
      out.named_source = ReadPietyPriceNamedDefinition37540B0Readonly12004(
          access, *out.named_before_identity, inputs.unchanged_snapshot_revision);
      out.eax_raw_i32 = out.named_source->eax_raw_i32;
      if (!out.eax_raw_i32) out.unavailable_reason = out.named_source->unavailable_reason;
    } else {
      out.count_before_raw_i32 = ReadOperand<std::int32_t>(access, inputs.expression_identity, 0x14);
      if (!out.count_before_raw_i32) {
        out.unavailable_reason = "piety_dynamic_expression_count_unavailable";
        return out;
      }
      if (*out.count_before_raw_i32 != 0) {
        if (inputs.expression_identity > (std::numeric_limits<std::uintptr_t>::max)() - 8) {
          out.unavailable_reason = "piety_dynamic_expression_list_identity_overflow";
          return out;
        }
        CompiledExpressionVariant3755500Inputs12004 variant_inputs{};
        variant_inputs.expression_list_identity = inputs.expression_identity + 8;
        variant_inputs.copied_pack = inputs.copied_pack;
        variant_inputs.named_tuple_identity = inputs.original_named_tuple_identity;
        variant_inputs.unchanged_snapshot_revision = inputs.unchanged_snapshot_revision;
        out.variant_source = ReadCompiledExpressionVariant3755500Readonly12004(access, variant_inputs);
        out.compiled_provider_metadata =
            ProjectCompiledExpressionVariant3755500ProviderMetadata12004(*out.variant_source);
        if (out.variant_source->list_count_before_raw_i32 != out.count_before_raw_i32) {
          out.unavailable_reason = "piety_dynamic_parent_and_variant_count_mismatch";
        } else if (!out.variant_source->source_result_ready || !out.variant_source->variant_tag_raw_u16 ||
                   !out.variant_source->variant_payload_raw_q64) {
          out.unavailable_reason = out.variant_source->unavailable_reason;
          if (out.unavailable_reason.empty()) out.unavailable_reason = "piety_dynamic_variant_output_unavailable";
        } else if (out.variant_source->list_count_after_raw_i32 != out.count_before_raw_i32) {
          out.unavailable_reason = "piety_dynamic_parent_and_variant_count_mismatch";
        } else if (*out.variant_source->variant_tag_raw_u16 == 1) {
          out.eax_raw_i32 = ProjectVariantPayload(*out.variant_source->variant_payload_raw_q64);
        } else {
          out.fallback_before_raw_i32 = ReadOperand<std::int32_t>(access, inputs.expression_identity, 0x98);
          out.eax_raw_i32 = out.fallback_before_raw_i32;
          if (!out.eax_raw_i32) out.unavailable_reason = "piety_dynamic_known_other_tag_fallback_unavailable";
        }
      } else {
        out.fallback_before_raw_i32 = ReadOperand<std::int32_t>(access, inputs.expression_identity, 0x98);
        out.eax_raw_i32 = out.fallback_before_raw_i32;
        if (!out.eax_raw_i32) out.unavailable_reason = "piety_dynamic_empty_expression_fallback_unavailable";
      }
    }
  }
  if (!RecopyReachedParent(access, out)) out.eax_raw_i32.reset();
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
