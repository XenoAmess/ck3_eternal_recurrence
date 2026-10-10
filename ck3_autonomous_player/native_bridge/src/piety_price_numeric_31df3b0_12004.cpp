#include "xar_bridge/piety_price_numeric_31df3b0_12004.hpp"

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"

#include <limits>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {

bool ReadRawReceiverCopy(void* context, const void* source, void* destination,
                         std::size_t bytes) noexcept {
  const auto* access =
      static_cast<const construction_owner_mode3::RawReceiverAccessV1*>(context);
  if (!access || !access->read_memory) return false;
  try {
    return access->read_memory(access->context, source, destination, bytes);
  } catch (...) {
    return false;
  }
}

} // namespace

Numeric31DF3B0Observation12004 ReadPietyPriceNumeric31DF3B012004(
    const Numeric31DF3B0Bindings12004& bindings, std::uintptr_t definition,
    std::uintptr_t current_rite, std::uint64_t unchanged_snapshot_revision) {
  Numeric31DF3B0Observation12004 result;
  result.definition_pointer = definition;
  result.current_rite_pointer = current_rite;
  result.frame_key = unchanged_snapshot_revision;
  if (!bindings.exact_12004_bound || !bindings.guarded_read) {
    result.reason = "piety_entry_exact_access_unavailable";
    return result;
  }
  if (definition > (std::numeric_limits<std::uintptr_t>::max)() -
                       kPietyPrice31DF3B0ExpressionOffset12004) {
    result.reason = "piety_entry_expression_copy_address_overflow";
    return result;
  }
  const auto selected = definition + kPietyPrice31DF3B0ExpressionOffset12004;
  result.selected_expression_identity = selected;
  result.copied_diagnostics.emplace(ProjectSelectedPietyPriceEax12004(
      bindings, selected, unchanged_snapshot_revision));
  const auto& child = *result.copied_diagnostics;
  if (child.module_base != bindings.module_base ||
      child.expression_identity != selected ||
      child.unchanged_snapshot_revision != unchanged_snapshot_revision) {
    result.reason = "piety_entry_numeric_identity_mismatch";
    return result;
  }
  if (!child.unavailable_reason.empty()) {
    result.reason = child.unavailable_reason;
    return result;
  }
  if (!child.eax_raw_i32.has_value()) {
    result.reason = "piety_entry_numeric_eax_unavailable";
    return result;
  }
  result.native_eax_raw = child.eax_raw_i32;
  result.source_ready = true;
  result.status = "source_ready";
  result.reason = "actual_entry_numeric_raw_eax_copied";
  return result;
}

bool ReadPietyPriceNumeric31DF3B0Adapter12004(
    void* context,
    const construction_owner_mode3::RawReceiverAccessV1& access,
    std::uintptr_t definition, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision,
    std::int32_t& native_eax_raw) noexcept {
  static_cast<void>(context);
  auto access_copy = access;
  const Numeric31DF3B0Bindings12004 bindings{
      access.module_base, &access_copy, &ReadRawReceiverCopy,
      access.exact_12004_bound && access.read_memory != nullptr};
  try {
    const auto result = ReadPietyPriceNumeric31DF3B012004(
        bindings, definition, current_rite, unchanged_snapshot_revision);
    if (!result.source_ready || !result.native_eax_raw.has_value() ||
        result.definition_pointer != definition ||
        result.current_rite_pointer != current_rite ||
        result.frame_key != unchanged_snapshot_revision ||
        result.source_pin != kPietyPrice31DF3B0SourcePin12004) return false;
    native_eax_raw = *result.native_eax_raw;
    return true;
  } catch (...) {
    return false;
  }
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
