#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace xar::ck3_12004 {

// Actual2651050's single-Side traversal. The outer two-Side caller is not
// qualified by this leaf. Every identity below is an explicit stage input.
inline constexpr std::uintptr_t kFinalEntryStride12004 = 0x60;
inline constexpr std::uint32_t kLevyFinalWriterCall12004 = 0x02651088;
inline constexpr std::uint32_t kMaaFinalWriterCall12004 = 0x026510B6;

enum class FinalOccurrenceBucket12004 { levy, men_at_arms };

struct FinalOccurrenceSourceRow12004 {
    std::uint32_t native_carmy_id{};
    std::uint32_t regiment_id{};  // Requested full Entry handle, never masked.
    std::int32_t initial_army_province_id{};
    std::uintptr_t initial_army_province_identity{};
    std::int64_t current_quantity_raw{};  // Carried, never an admission gate.
};

struct FinalOccurrenceBucketInput12004 {
    std::uintptr_t data_identity{};
    std::span<const FinalOccurrenceSourceRow12004> rows;
};

struct FinalSideOccurrenceInput12004 {
    std::uint32_t side_index{};  // Supplied caller association, not inferred.
    std::int32_t final_combat_province_id{};
    std::uintptr_t final_combat_province_identity{};
    FinalOccurrenceBucketInput12004 levy;
    FinalOccurrenceBucketInput12004 men_at_arms;
};

struct PlannedFinalOccurrence12004 {
    std::uint32_t side_index{};
    FinalOccurrenceBucket12004 bucket{};
    std::size_t bucket_index{};
    std::size_t traversal_ordinal{};  // Local to this single-Side invocation.
    std::uintptr_t physical_entry_identity{};
    std::uint32_t native_carmy_id{};
    std::uint32_t regiment_id{};
    std::int32_t final_combat_province_id{};
    std::uintptr_t final_combat_province_identity{};
    std::int32_t initial_army_province_id{};
    std::uintptr_t initial_army_province_identity{};
    std::int64_t current_quantity_raw{};
    std::uint32_t writer_call_rva{};
};

// Inputs describe already supplied, ordered stage rows. This does not read
// native memory, resolve Regiment fallback, evaluate getters or write caches.
std::vector<PlannedFinalOccurrence12004> PlanFinalSideOccurrences12004(
    const FinalSideOccurrenceInput12004& input);

}  // namespace xar::ck3_12004
