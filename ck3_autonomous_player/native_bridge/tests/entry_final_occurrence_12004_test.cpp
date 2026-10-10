#include "xar_bridge/entry_final_occurrence_12004.hpp"

#include <array>
#include <iostream>

namespace {
bool Check(bool condition, const char* message) {
    if (!condition) std::cerr << message << '\n';
    return condition;
}
}  // namespace

int main() {
    using namespace xar::ck3_12004;
    // Deliberately repeat a full Regiment handle across separate occurrences.
    // The zero-current levy must still receive the final refresh association.
    const std::array<FinalOccurrenceSourceRow12004, 2> levy{{
        {0x04000081, 0x08000045, 101, 0xA100, 0},
        {0x05000082, 0x09000046, 102, 0xA200, 17},
    }};
    const std::array<FinalOccurrenceSourceRow12004, 2> maa{{
        {0x06000083, 0x08000045, 103, 0xA300, -3},
        {0x07000084, 0x0A000047, 104, 0xA400, 11},
    }};
    const FinalSideOccurrenceInput12004 input{
        1, 299, 0xF000, {0xB000, levy}, {0xC000, maa}};
    const auto result = PlanFinalSideOccurrences12004(input);
    if (!Check(result.size() == 4, "All four stored occurrences required"))
        return 1;
    for (std::size_t i = 0; i < result.size(); ++i) {
        const bool is_levy = i < 2;
        const auto index = is_levy ? i : i - 2;
        const auto& source = is_levy ? levy[index] : maa[index];
        const auto& actual = result[i];
        const auto data = is_levy ? 0xB000u : 0xC000u;
        if (!Check(actual.side_index == 1 && actual.traversal_ordinal == i &&
                       actual.bucket_index == index &&
                       actual.bucket == (is_levy ? FinalOccurrenceBucket12004::levy
                                               : FinalOccurrenceBucket12004::men_at_arms),
                   "Levy-before-MAA single-side order")) return 1;
        if (!Check(actual.physical_entry_identity == data + index * 0x60 &&
                       actual.writer_call_rva == (is_levy ? 0x02651088u : 0x026510B6u),
                   "Actual stride and writer CALL occurrence")) return 1;
        if (!Check(actual.native_carmy_id == source.native_carmy_id &&
                       actual.regiment_id == source.regiment_id &&
                       actual.current_quantity_raw == source.current_quantity_raw,
                   "Full source identities and zero/negative quantity membership")) return 1;
        if (!Check(actual.final_combat_province_id == 299 &&
                       actual.final_combat_province_identity == 0xF000 &&
                       actual.initial_army_province_id == source.initial_army_province_id &&
                       actual.initial_army_province_identity == source.initial_army_province_identity,
                   "Initial Army and supplied final Combat Province stay distinct")) return 1;
    }
    std::cout << "PASS single-side final occurrence association12004\n";
    return 0;
}
