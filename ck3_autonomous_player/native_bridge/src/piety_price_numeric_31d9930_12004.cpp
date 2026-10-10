#include "xar_bridge/piety_price_numeric_31d9930_12004.hpp"

#include <limits>
#include <utility>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {

bool ReadFromRawReceiverAccess(void *context, const void *source, void *out,
                               std::size_t size) noexcept {
  const auto *access =
      static_cast<const construction_owner_mode3::RawReceiverAccessV1 *>(context);
  if (!access || !access->read_memory) return false;
  try {
    return access->read_memory(access->context, source, out, size);
  } catch (...) {
    return false;
  }
}

} // namespace

Numeric31D9930Observation12004 ReadPietyPriceNumeric31D993012004(
    const Numeric31D9930Bindings12004 &bindings,
    std::uintptr_t definition_pointer,
    std::uintptr_t current_rite_pointer,
    std::uint64_t unchanged_snapshot_revision) noexcept {
  Numeric31D9930Observation12004 out;
  out.definition_pointer = definition_pointer;
  out.current_rite_pointer = current_rite_pointer;
  out.frame_key = unchanged_snapshot_revision;
  if (!bindings.exact_12004_bound || !bindings.guarded_read) {
    out.reason = "numeric31d9930_exact_read_binding_unavailable";
    return out;
  }
  if (!definition_pointer ||
      definition_pointer >
          (std::numeric_limits<std::uintptr_t>::max)() - 0x760) {
    out.reason = "numeric31d9930_definition_expression_pointer_unavailable";
    return out;
  }
  out.selected_expression_identity = definition_pointer + 0x760;
  auto evaluator = ProjectSelectedPietyPriceEax12004(
      bindings, *out.selected_expression_identity, unchanged_snapshot_revision);
  out.native_eax_raw = evaluator.eax_raw_i32;
  out.source_ready = out.native_eax_raw.has_value();
  if (out.source_ready) {
    out.status = "available";
    out.reason = "actual31d9930_selected_numeric_eax_available";
  } else {
    out.reason = evaluator.unavailable_reason;
  }
  out.evaluator = std::move(evaluator);
  return out;
}

bool ReadPietyPriceNumeric31D9930Adapter12004(
    void *unused_context,
    const construction_owner_mode3::RawReceiverAccessV1 &access,
    std::uintptr_t definition_pointer,
    std::uintptr_t current_rite_pointer,
    std::uint64_t unchanged_snapshot_revision,
    std::int32_t &out) noexcept {
  (void)unused_context;
  Numeric31D9930Bindings12004 bindings;
  bindings.module_base = access.module_base;
  bindings.context = const_cast<construction_owner_mode3::RawReceiverAccessV1 *>(
      &access);
  bindings.guarded_read = ReadFromRawReceiverAccess;
  bindings.exact_12004_bound = access.exact_12004_bound;
  const auto observation = ReadPietyPriceNumeric31D993012004(
      bindings, definition_pointer, current_rite_pointer,
      unchanged_snapshot_revision);
  if (!observation.source_ready || !observation.native_eax_raw) return false;
  out = *observation.native_eax_raw;
  return true;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
