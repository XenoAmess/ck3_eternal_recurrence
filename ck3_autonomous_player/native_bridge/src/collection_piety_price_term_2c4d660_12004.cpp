#include "xar_bridge/collection_piety_price_term_2c4d660_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {
std::string_view FailureReason(
    construction_owner_mode3::ScaledCollectionKeyFailure12004 failure) noexcept {
  using Failure = construction_owner_mode3::ScaledCollectionKeyFailure12004;
  switch (failure) {
  case Failure::exact_build: return "exact_12004_binding_unavailable";
  case Failure::read_callback: return "collection_term_read_callback_unavailable";
  case Failure::collection: return "collection_term_identity_unavailable";
  case Failure::count_read: return "collection_term_count_unread";
  case Failure::negative_count: return "collection_term_negative_count";
  case Failure::keys_read: return "collection_term_keys_unread";
  case Failure::probe_read: return "collection_term_key_probe_unread";
  case Failure::values_read: return "collection_term_values_unread";
  case Failure::selected_value_read: return "collection_term_selected_value_unread";
  case Failure::source_changed: return "collection_term_source_changed";
  default: return "collection_term_selected_reader_unavailable";
  }
}
} // namespace

CollectionPietyPriceTerm2C4D660Result12004
ReadCollectionPietyPriceTerm2C4D66012004(
    const PietyPriceNumericAccess12004 &access,
    std::uintptr_t collection_identity, std::uint32_t incoming_key_raw_u32,
    std::int64_t scale_raw_q64, std::uint64_t source_revision_raw_u64) {
  CollectionPietyPriceTerm2C4D660Result12004 out;
  out.source_revision_raw_u64 = source_revision_raw_u64;
  const construction_owner_mode3::LoadedInputAccessV1 selected_access{
      access.context, access.guarded_read, access.exact_12004_bound};
  // Source2C4D7BA..7CD: original collection, low16 key, selector0, firstQ64.
  // Reuse the qualified selected reader once; no copied lookup or scaling.
  out.selected = construction_owner_mode3::ReadScaledCollectionKey12004(
      selected_access, collection_identity, incoming_key_raw_u32,
      scale_raw_q64, std::uintptr_t{0}, std::int32_t{0});
  if (!out.selected.ready || !out.selected.scaled_value_raw_q64) {
    out.unavailable_reason = FailureReason(out.selected.failure);
    return out;
  }
  out.scaled_term_raw_q64 = out.selected.scaled_value_raw_q64;
  out.source_ready = true;
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
