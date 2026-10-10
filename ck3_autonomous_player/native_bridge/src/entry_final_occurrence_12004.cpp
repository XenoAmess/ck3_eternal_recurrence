#include "xar_bridge/entry_final_occurrence_12004.hpp"

namespace xar::ck3_12004 {

std::vector<PlannedFinalOccurrence12004> PlanFinalSideOccurrences12004(
    const FinalSideOccurrenceInput12004& input) {
    std::vector<PlannedFinalOccurrence12004> result;
    result.reserve(input.levy.rows.size() + input.men_at_arms.rows.size());
    const auto append = [&](const FinalOccurrenceBucketInput12004& source,
                            FinalOccurrenceBucket12004 bucket,
                            std::uint32_t writer_call_rva) {
        for (std::size_t index = 0; index < source.rows.size(); ++index) {
            const auto& row = source.rows[index];
            result.push_back({
                input.side_index,
                bucket,
                index,
                result.size(),
                source.data_identity + index * kFinalEntryStride12004,
                row.native_carmy_id,
                row.regiment_id,
                input.final_combat_province_id,
                input.final_combat_province_identity,
                row.initial_army_province_id,
                row.initial_army_province_identity,
                row.current_quantity_raw,
                writer_call_rva,
            });
        }
    };
    append(input.levy, FinalOccurrenceBucket12004::levy,
           kLevyFinalWriterCall12004);
    append(input.men_at_arms, FinalOccurrenceBucket12004::men_at_arms,
           kMaaFinalWriterCall12004);
    return result;
}

}  // namespace xar::ck3_12004
