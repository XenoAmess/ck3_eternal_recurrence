#include "xar_bridge/piety_price_named_definition_37540b0_readonly_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {

template<class T>
std::optional<T> ReadRaw(const PietyPriceNumericAccess12004 &access,
                        std::uintptr_t object, std::size_t offset) noexcept {
  T value{};
  if (!ReadPietyPriceNumericField12004(access, object, offset, value)) return {};
  return value;
}

} // namespace

PietyPriceNamedDefinition37540B0Readonly12004
ReadPietyPriceNamedDefinition37540B0Readonly12004(
    const PietyPriceNumericAccess12004 &access,
    std::uintptr_t actual_named_definition_identity,
    std::uint64_t unchanged_snapshot_revision) noexcept {
  PietyPriceNamedDefinition37540B0Readonly12004 out{};
  out.module_base = access.module_base;
  out.named_definition_identity = actual_named_definition_identity;
  out.unchanged_snapshot_revision = unchanged_snapshot_revision;
  if (!access.exact_12004_bound || !access.guarded_read) {
    out.unavailable_reason = "piety_named_definition_exact_access_unavailable";
    return out;
  }

  // 3754143 loads the provider after the optional profiling entry.
  out.provider_first_raw = ReadRaw<std::uintptr_t>(
      access, actual_named_definition_identity, 0x70);
  if (!out.provider_first_raw) {
    out.unavailable_reason = "piety_named_definition_provider_raw_unavailable";
    return out;
  }
  if (*out.provider_first_raw != 0) {
    out.unavailable_reason = "piety_named_definition_virtual_variant_37498a0_unavailable";
    return out;
  }

  out.enabled_first_raw_u8 = ReadRaw<std::uint8_t>(
      access, actual_named_definition_identity, 0x7A);
  if (!out.enabled_first_raw_u8) {
    out.unavailable_reason = "piety_named_definition_enabled_raw_unavailable";
    return out;
  }
  if (*out.enabled_first_raw_u8 != 0) {
    out.value_first_raw_i32 = ReadRaw<std::int32_t>(
        access, actual_named_definition_identity, 0x60);
    if (!out.value_first_raw_i32) {
      out.unavailable_reason = "piety_named_definition_value_raw_unavailable";
      return out;
    }
  }

  // Readonly consistency copies, separate from the literal native reads.
  out.provider_after_raw = ReadRaw<std::uintptr_t>(
      access, actual_named_definition_identity, 0x70);
  out.enabled_after_raw_u8 = ReadRaw<std::uint8_t>(
      access, actual_named_definition_identity, 0x7A);
  if (*out.enabled_first_raw_u8 != 0) {
    out.value_after_raw_i32 = ReadRaw<std::int32_t>(
        access, actual_named_definition_identity, 0x60);
  }
  if (!out.provider_after_raw || !out.enabled_after_raw_u8 ||
      (*out.enabled_first_raw_u8 != 0 && !out.value_after_raw_i32)) {
    out.unavailable_reason = "piety_named_definition_operand_bookend_unavailable";
    return out;
  }
  if (out.provider_after_raw != out.provider_first_raw ||
      out.enabled_after_raw_u8 != out.enabled_first_raw_u8 ||
      out.value_after_raw_i32 != out.value_first_raw_i32) {
    out.unavailable_reason = "piety_named_definition_source_operands_changed";
    return out;
  }

  // 37540F7 initialized EDI0; only 3754213 conditionally replaces it.
  out.eax_raw_i32 = *out.enabled_first_raw_u8 == 0
      ? std::int32_t{0} : *out.value_first_raw_i32;
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
