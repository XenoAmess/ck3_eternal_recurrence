#include "xar_bridge/entry_final_cache_postimage_12004.hpp"

#include <bit>

namespace xar::ck3_12004 {
namespace {
constexpr std::array<EntryFinalCacheStore12004, 6> kStores{{
    {0x08, 0x30, 4, 0x2657AF7}, {0x10, 0x38, 8, 0x2657AFE},
    {0x18, 0x40, 8, 0x2657B06}, {0x20, 0x48, 8, 0x2657B0E},
    {0x28, 0x50, 8, 0x2657B16}, {0x30, 0x58, 8, 0x2657B1E}}};

template <class UInt>
UInt Load(const EntryFinalCacheImage12004 &image, std::size_t offset) {
  UInt bits = 0;
  for (std::size_t i = 0; i < sizeof(UInt); ++i)
    bits |= static_cast<UInt>(image[offset + i]) << (8 * i);
  return bits;
}
template <class UInt>
void Store(EntryFinalCacheImage12004 &image, std::size_t offset, UInt bits) {
  for (std::size_t i = 0; i < sizeof(UInt); ++i)
    image[offset + i] = static_cast<std::uint8_t>(bits >> (8 * i));
}
} // namespace

EntryFinalRegimentResolution12004 ResolveEntryFinalRegiment12004(
    std::uint32_t requested, const EntryFinalRegimentEvidence12004 &evidence) {
  EntryFinalRegimentResolution12004 result;
  result.requested_regiment_id = requested;
  result.requested_low24_index = requested & 0x00FFFFFFU;
  auto fallback = [&](const char *branch) {
    result.used_fallback = true;
    result.branch = branch;
    result.resolved_regiment_identity = evidence.fallback_regiment_identity;
    result.resolved_regiment_id = evidence.fallback_regiment_id;
    if (!evidence.fallback_regiment_identity) {
      result.reason = "fallback_pointer_missing";
    } else if (*evidence.fallback_regiment_identity != 0 &&
               !evidence.fallback_regiment_id) {
      result.reason = "fallback_full_id_missing";
    } else {
      result.ready = true;
    }
  };
  if (!evidence.manager_identity) {
    result.reason = "manager_pointer_missing";
  } else if (*evidence.manager_identity == 0) {
    fallback("manager_absent");
  } else if (!evidence.manager_capacity) {
    result.reason = "manager_capacity_missing";
  } else if (result.requested_low24_index >= *evidence.manager_capacity) {
    fallback("index_out_of_capacity");
  } else if (!evidence.observed_row_index || !evidence.row_regiment_identity) {
    result.reason = "indexed_row_evidence_missing";
  } else if (*evidence.observed_row_index != result.requested_low24_index) {
    result.reason = "indexed_row_evidence_mismatch";
  } else if (*evidence.row_regiment_identity == 0) {
    fallback("row_pointer_null");
  } else if (!evidence.row_regiment_id) {
    result.reason = "row_full_id_missing";
  } else if (*evidence.row_regiment_id != requested) {
    fallback("full_id_mismatch");
  } else {
    result.ready = true;
    result.branch = "indexed_full_id_match";
    result.resolved_regiment_identity = evidence.row_regiment_identity;
    result.resolved_regiment_id = evidence.row_regiment_id;
  }
  return result;
}

EntryFinalCacheValues12004 ReadEntryFinalCacheValues12004(
    const EntryFinalCacheImage12004 &image) {
  return {std::bit_cast<std::int32_t>(Load<std::uint32_t>(image, 0x30)),
          std::bit_cast<std::int64_t>(Load<std::uint64_t>(image, 0x38)),
          std::bit_cast<std::int64_t>(Load<std::uint64_t>(image, 0x40)),
          std::bit_cast<std::int64_t>(Load<std::uint64_t>(image, 0x48)),
          std::bit_cast<std::int64_t>(Load<std::uint64_t>(image, 0x50)),
          std::bit_cast<std::int64_t>(Load<std::uint64_t>(image, 0x58))};
}

EntryFinalCachePostimage12004 ApplyEntryFinalCachePostimage12004(
    const EntryFinalCacheImage12004 &entering,
    const EntryFinalCacheOccurrence12004 &destination,
    const EntryFinalRegimentEvidence12004 &evidence,
    const std::optional<EntryFinalGetterResult12004> &getter) {
  EntryFinalCachePostimage12004 result;
  result.destination = destination;
  result.image = entering;
  result.supplied_getter = getter;
  result.resolution = ResolveEntryFinalRegiment12004(destination.regiment_id, evidence);
  // These are pure-model source bindings, not new guards in the native writer.
  if (Load<std::uint32_t>(entering, 8) != destination.regiment_id) {
    result.reason = "destination_entry_full_id_mismatch";
  } else if (!result.resolution.ready) {
    result.reason = result.resolution.reason;
  } else if (!getter || !getter->values || !getter->full_getter_construction_ready) {
    result.reason = "getter_inputs_or_complete_result_missing";
  } else if (getter->destination != destination) {
    result.reason = "getter_destination_occurrence_mismatch";
  } else if (getter->resolved_regiment_identity !=
                 result.resolution.resolved_regiment_identity ||
             getter->resolved_regiment_id != result.resolution.resolved_regiment_id) {
    result.reason = "getter_resolved_source_mismatch";
  } else if (getter->stage.empty() || getter->source_ledger.empty()) {
    result.reason = "getter_stage_or_source_ledger_missing";
  } else {
    const auto &v = *getter->values;
    Store(result.image, 0x30, std::bit_cast<std::uint32_t>(v.max_size));
    Store(result.image, 0x38, std::bit_cast<std::uint64_t>(v.siege_raw));
    Store(result.image, 0x40, std::bit_cast<std::uint64_t>(v.damage_raw));
    Store(result.image, 0x48, std::bit_cast<std::uint64_t>(v.toughness_raw));
    Store(result.image, 0x50, std::bit_cast<std::uint64_t>(v.pursuit_raw));
    Store(result.image, 0x58, std::bit_cast<std::uint64_t>(v.screen_raw));
    result.stores = kStores;
    result.store_count = kStores.size();
    result.modeled_return_bits = std::bit_cast<std::uint64_t>(v.screen_raw);
    result.refreshed = true;
  }
  return result;
}

} // namespace xar::ck3_12004
