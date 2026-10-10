#include "xar_bridge/entry_final_cache_postimage_12004.hpp"

#include <algorithm>
#include <iostream>
#include <limits>
#include <stdexcept>

namespace {
using namespace xar::ck3_12004;
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
void Unrefreshed(const EntryFinalCachePostimage12004 &result,
                const EntryFinalCacheImage12004 &entering) {
  Require(!result.refreshed && result.store_count == 0 &&
              !result.modeled_return_bits && result.image == entering,
          "missing or mismatched source must preserve the entire entering image");
}

// One compound fixture of the actual six-store source contract. No game,
// native getter, old fixture or constructor initialization is executed.
void BoundedFinalCachePostimage() {
  EntryFinalCacheImage12004 entering;
  for (std::size_t i = 0; i < entering.size(); ++i)
    entering[i] = static_cast<std::uint8_t>(i ^ 0xA5);
  // Full generation ID 0x81000002, not its low24 index. A retained current=0
  // row is still refreshed by the actual writer; the amount bytes stay zero.
  entering[8] = 2; entering[9] = 0; entering[10] = 0; entering[11] = 0x81;
  std::fill(entering.begin() + 0x18, entering.begin() + 0x20, std::uint8_t{0});
  const auto original = entering;
  EntryFinalCacheOccurrence12004 occurrence;
  occurrence.side_index = 1;
  occurrence.bucket = EntryFinalCacheBucket12004::men_at_arms;
  occurrence.bucket_index = 7;
  occurrence.traversal_ordinal = 10;
  occurrence.physical_entry_identity = 0x1700;
  occurrence.native_carmy_id = 0x84000009U;
  occurrence.regiment_id = 0x81000002U;
  occurrence.final_combat_province_id = 17;
  occurrence.final_combat_province_identity = 0x3300;
  EntryFinalRegimentEvidence12004 evidence;
  evidence.manager_identity = 0x4400;
  evidence.manager_capacity = 3;
  evidence.observed_row_index = 2;
  evidence.row_regiment_identity = 0x5500;
  evidence.row_regiment_id = occurrence.regiment_id;
  // Deliberately omit fallback evidence: direct match does not consume it.
  EntryFinalGetterResult12004 getter;
  getter.destination = occurrence;
  getter.resolved_regiment_identity = 0x5500;
  getter.resolved_regiment_id = occurrence.regiment_id;
  getter.stage = "explicit-after-source-operation";
  getter.source_ledger = "fixture supplied changed Character/selector/environment operands";
  getter.full_getter_construction_ready = true;
  getter.values = EntryFinalCacheValues12004{
      std::numeric_limits<std::int32_t>::min(),
      std::numeric_limits<std::int64_t>::min(), -1, 0,
      std::numeric_limits<std::int64_t>::max(), -0x0123456789ABCDEFL};
  const auto result = ApplyEntryFinalCachePostimage12004(entering, occurrence, evidence, getter);
  Require(result.refreshed && result.store_count == 6 && result.resolution.ready &&
              !result.resolution.used_fallback &&
              result.resolution.requested_low24_index == 2,
          "direct full generation ID must resolve and write all six fields");
  auto expected = entering;
  // Independent byte oracle: exact DWORD width leaves Entry+34..37 intact.
  const std::array<std::uint8_t, 4> max_size{0, 0, 0, 0x80};
  const std::array<std::uint8_t, 40> qwords{
      0, 0, 0, 0, 0, 0, 0, 0x80,
      0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
      0, 0, 0, 0, 0, 0, 0, 0,
      0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x7F,
      0x11, 0x32, 0x54, 0x76, 0x98, 0xBA, 0xDC, 0xFE};
  std::copy(max_size.begin(), max_size.end(), expected.begin() + 0x30);
  std::copy(qwords.begin(), qwords.end(), expected.begin() + 0x38);
  Require(result.image == expected && entering == original,
          "only exact cache ranges change; identities, amounts and result headers survive");
  Require(ReadEntryFinalCacheValues12004(result.image) == *getter.values &&
              result.modeled_return_bits == 0xFEDCBA9876543211ULL,
          "signed widths and final screen return bits must be preserved");
  const std::array<std::uintptr_t, 6> store_order{
      0x2657AF7, 0x2657AFE, 0x2657B06, 0x2657B0E, 0x2657B16, 0x2657B1E};
  for (std::size_t i = 0; i < store_order.size(); ++i)
    Require(result.stores[i].store_rva == store_order[i], "actual native store order");
  Require(!result.full_entry_ready && !result.native_execution_performed &&
              !result.new_stage_observed && result.supplied_getter->stage == getter.stage,
          "bounded supplied-stage calculation grants no full/native/observed credit");

  auto fallback = evidence;
  fallback.row_regiment_id = 0x82000002U; // Same index, different generation.
  fallback.fallback_regiment_identity = 0x6600;
  fallback.fallback_regiment_id = 0x8500000AU;
  auto fallback_getter = getter;
  fallback_getter.resolved_regiment_identity = 0x6600;
  fallback_getter.resolved_regiment_id = 0x8500000AU;
  fallback_getter.input_mode = EntryFinalCacheInputMode12004::held_current;
  fallback_getter.stage = "held-current-under-explicit-unchanged-operands";
  const auto fallback_result = ApplyEntryFinalCachePostimage12004(
      entering, occurrence, fallback, fallback_getter);
  Require(fallback_result.refreshed && fallback_result.resolution.used_fallback &&
              fallback_result.resolution.branch == "full_id_mismatch" &&
              fallback_result.resolution.requested_regiment_id == 0x81000002U &&
              fallback_result.resolution.resolved_regiment_id == 0x8500000AU &&
              fallback_result.destination == occurrence && fallback_result.image == expected,
          "fallback source differs from unchanged destination requested full ID");
  Unrefreshed(ApplyEntryFinalCachePostimage12004(entering, occurrence, fallback, getter), entering);
  for (int branch = 0; branch < 3; ++branch) {
    auto e = fallback;
    if (branch == 0) e.manager_identity = 0;
    if (branch == 1) e.manager_capacity = 2; // Unsigned index == capacity fails.
    if (branch == 2) e.row_regiment_identity = 0;
    Require(ResolveEntryFinalRegiment12004(occurrence.regiment_id, e).used_fallback,
            "all actual manager/index/null branches use the explicit fallback");
  }
  auto missing = evidence;
  missing.manager_identity.reset();
  Unrefreshed(ApplyEntryFinalCachePostimage12004(entering, occurrence, missing, getter), entering);
  missing = evidence;
  missing.observed_row_index = 1;
  Unrefreshed(ApplyEntryFinalCachePostimage12004(entering, occurrence, missing, getter), entering);
  Unrefreshed(ApplyEntryFinalCachePostimage12004(entering, occurrence, evidence, std::nullopt), entering);
  auto partial = getter;
  partial.full_getter_construction_ready = false;
  Unrefreshed(ApplyEntryFinalCachePostimage12004(entering, occurrence, evidence, partial), entering);
  partial = getter;
  partial.values.reset();
  Unrefreshed(ApplyEntryFinalCachePostimage12004(entering, occurrence, evidence, partial), entering);
  partial = getter;
  ++partial.destination.bucket_index;
  Unrefreshed(ApplyEntryFinalCachePostimage12004(entering, occurrence, evidence, partial), entering);
  partial = getter;
  partial.destination.final_combat_province_id = 19;
  Unrefreshed(ApplyEntryFinalCachePostimage12004(entering, occurrence, evidence, partial), entering);
  auto wrong_entry = entering;
  wrong_entry[11] = 0x82;
  Unrefreshed(ApplyEntryFinalCachePostimage12004(wrong_entry, occurrence, evidence, getter), wrong_entry);
}
} // namespace

int main() {
  try {
    BoundedFinalCachePostimage();
    std::cout << "entry_final_cache_postimage_12004: 1/1 GREEN (pure bounded fixture)\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "entry_final_cache_postimage_12004: " << error.what() << '\n';
    return 1;
  }
}
