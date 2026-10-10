#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004 {

inline constexpr std::size_t kEntryFinalCacheImageBytes12004 = 0x60;
using EntryFinalCacheImage12004 =
    std::array<std::uint8_t, kEntryFinalCacheImageBytes12004>;

enum class EntryFinalCacheBucket12004 { levy, men_at_arms };
enum class EntryFinalCacheInputMode12004 { explicit_named_stage, held_current };

// Supplied by the outer caller. This primitive does not enumerate a Side,
// infer Army identity from the bucket, or substitute initial Army Province.
struct EntryFinalCacheOccurrence12004 {
  std::uint32_t side_index = 0;
  EntryFinalCacheBucket12004 bucket = EntryFinalCacheBucket12004::levy;
  std::uint32_t bucket_index = 0;
  std::uint64_t traversal_ordinal = 0;
  std::uintptr_t physical_entry_identity = 0;
  std::uint32_t native_carmy_id = 0;
  std::uint32_t regiment_id = 0;
  std::int32_t final_combat_province_id = 0;
  std::uintptr_t final_combat_province_identity = 0;
  friend bool operator==(const EntryFinalCacheOccurrence12004 &,
                         const EntryFinalCacheOccurrence12004 &) = default;
};

// nullopt means missing evidence; a present zero pointer is a known null.
// observed_row_index binds the supplied table row to the requested low24.
struct EntryFinalRegimentEvidence12004 {
  std::optional<std::uintptr_t> manager_identity;
  std::optional<std::uint32_t> manager_capacity;
  std::optional<std::uint32_t> observed_row_index;
  std::optional<std::uintptr_t> row_regiment_identity;
  std::optional<std::uint32_t> row_regiment_id;
  std::optional<std::uintptr_t> fallback_regiment_identity;
  std::optional<std::uint32_t> fallback_regiment_id;
};

struct EntryFinalRegimentResolution12004 {
  bool ready = false;
  bool used_fallback = false;
  std::uint32_t requested_regiment_id = 0;
  std::uint32_t requested_low24_index = 0;
  std::optional<std::uintptr_t> resolved_regiment_identity;
  std::optional<std::uint32_t> resolved_regiment_id;
  std::string branch;
  std::string reason;
};

struct EntryFinalCacheValues12004 {
  std::int32_t max_size = 0;
  std::int64_t siege_raw = 0, damage_raw = 0, toughness_raw = 0;
  std::int64_t pursuit_raw = 0, screen_raw = 0;
  friend bool operator==(const EntryFinalCacheValues12004 &,
                         const EntryFinalCacheValues12004 &) = default;
};

struct EntryFinalGetterResult12004 {
  EntryFinalCacheOccurrence12004 destination;
  std::uintptr_t resolved_regiment_identity = 0;
  std::optional<std::uint32_t> resolved_regiment_id;
  EntryFinalCacheInputMode12004 input_mode =
      EntryFinalCacheInputMode12004::explicit_named_stage;
  std::string stage;
  std::string source_ledger;
  bool full_getter_construction_ready = false;
  std::optional<EntryFinalCacheValues12004> values;
};

struct EntryFinalCacheStore12004 {
  std::uint32_t source_offset = 0, destination_offset = 0, width = 0;
  std::uintptr_t store_rva = 0;
  friend bool operator==(const EntryFinalCacheStore12004 &,
                         const EntryFinalCacheStore12004 &) = default;
};

struct EntryFinalCachePostimage12004 {
  EntryFinalCacheOccurrence12004 destination;
  EntryFinalCacheImage12004 image{};
  EntryFinalRegimentResolution12004 resolution;
  std::optional<EntryFinalGetterResult12004> supplied_getter;
  std::array<EntryFinalCacheStore12004, 6> stores{};
  std::size_t store_count = 0;
  bool refreshed = false;
  // Writer RAX is the final screen QWORD bits, never an Entry pointer.
  std::optional<std::uint64_t> modeled_return_bits;
  bool full_entry_ready = false;
  bool native_execution_performed = false;
  bool new_stage_observed = false;
  std::string reason;
};

EntryFinalRegimentResolution12004 ResolveEntryFinalRegiment12004(
    std::uint32_t requested_regiment_id,
    const EntryFinalRegimentEvidence12004 &);
EntryFinalCacheValues12004 ReadEntryFinalCacheValues12004(
    const EntryFinalCacheImage12004 &);
EntryFinalCachePostimage12004 ApplyEntryFinalCachePostimage12004(
    const EntryFinalCacheImage12004 &entering_image,
    const EntryFinalCacheOccurrence12004 &destination,
    const EntryFinalRegimentEvidence12004 &,
    const std::optional<EntryFinalGetterResult12004> &);

} // namespace xar::ck3_12004
