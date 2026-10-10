#pragma once

#include "xar_bridge/piety_price_numeric_31d9930_dynamic_12004.hpp"
#include "xar_bridge/piety_price_numeric_31df3b0_dynamic_12004.hpp"

#include <cstring>
#include <limits>
#include <optional>
#include <string>
#include <utility>
#include <variant>
#include <vector>

namespace xar::ck3_12004::piety_price_raw_inputs {

static_assert(sizeof(std::uintptr_t) == 8);

using CreateDefinitionDynamicObservation12004 = decltype(
    ReadPietyPriceNumeric31D9930Dynamic12004(
        std::declval<const Numeric31D9930DynamicBindings12004&>(),
        std::uintptr_t{}, std::uintptr_t{}, std::uint64_t{}));
using CreateEntryDynamicObservation12004 = decltype(
    ReadPietyPriceNumeric31DF3B0Dynamic12004(
        std::declval<const Numeric31DF3B0DynamicBindings12004&>(),
        std::uintptr_t{}, std::uintptr_t{}, std::uint64_t{}));

struct CreatePietyDynamicBaseCostBindings12004 {
    PietyPriceNumericAccess12004 access;
    Numeric31D9930DynamicBindings12004 definition_numeric;
    Numeric31DF3B0DynamicBindings12004 entry_numeric;
    std::size_t maximum_total_occurrences{4096};
};

struct CreatePietyDynamicContribution12004 {
    std::uint8_t collection{};
    std::size_t ordinal{};
    std::uintptr_t full_element_pointer{};
    std::optional<std::int32_t> native_eax_raw;
    std::optional<std::int64_t> scaled_raw;
    std::uint64_t prefix_before_bits{}, prefix_after_bits{};
    bool contribution_applied{};
    std::variant<std::monostate, CreateDefinitionDynamicObservation12004,
        CreateEntryDynamicObservation12004> child;
};

struct CreatePietyDynamicBaseCostObservation12004 {
    bool composition_source_ready{true};
    bool reached_numeric_sources_ready{true};
    bool complete{};
    const char* status{"unavailable"};
    std::string reason{"not_read"};
    std::uintptr_t price_payload{}, current_rite{};
    std::uint64_t unchanged_snapshot_revision{};
    std::optional<std::uintptr_t> first_data, second_data;
    std::optional<std::int32_t> first_count_raw, second_count_raw;
    std::optional<std::uint8_t> stopped_collection;
    std::optional<std::size_t> stopped_ordinal;
    std::vector<CreatePietyDynamicContribution12004> ordered_contributions;
    std::uint64_t completed_prefix_bits{};
    std::optional<std::uint64_t> base_price_bits;
    std::optional<std::int64_t> base_price_raw_q64;
    bool actual_original_consumed_values{};
};

namespace create_dynamic_price_detail {
inline bool SameAccess(const PietyPriceNumericAccess12004& first,
                       const PietyPriceNumericAccess12004& second) noexcept {
    return first.module_base == second.module_base && first.context == second.context &&
        first.guarded_read == second.guarded_read;
}

inline void Apply(CreatePietyDynamicBaseCostObservation12004& output,
                  CreatePietyDynamicContribution12004& row,
                  std::int32_t raw) noexcept {
    row.native_eax_raw = raw;
    row.scaled_raw = static_cast<std::int64_t>(raw) * std::int64_t{100000};
    output.completed_prefix_bits += static_cast<std::uint64_t>(*row.scaled_raw);
    row.prefix_after_bits = output.completed_prefix_bits;
    row.contribution_applied = true;
}
} // namespace create_dynamic_price_detail

// Source-bound nullaux2C641E0 arithmetic. Supplied operands/witnesses retain
// their child diagnostics; this reader never observes a native provider.
inline CreatePietyDynamicBaseCostObservation12004 ReadCreatePietyDynamicBaseCost12004(
    const CreatePietyDynamicBaseCostBindings12004& bindings,
    std::uintptr_t price_payload, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision) {
    CreatePietyDynamicBaseCostObservation12004 output;
    output.price_payload = price_payload;
    output.current_rite = current_rite;
    output.unchanged_snapshot_revision = unchanged_snapshot_revision;
    if (!bindings.access.exact_12004_bound || !bindings.access.guarded_read) {
        output.composition_source_ready = false;
        output.reason = "create_dynamic_exact_access_unavailable";
        return output;
    }
    if (price_payload == 0) {
        output.reason = "create_dynamic_payload_unavailable";
        return output;
    }
    for (std::uint8_t collection = 0; collection != 2; ++collection) {
        output.stopped_collection = collection;
        output.stopped_ordinal.reset();
        std::uintptr_t data{};
        if (!ReadPietyPriceNumericField12004(bindings.access, price_payload,
                collection == 0 ? 0x8 : 0x50, data)) {
            output.reason = collection == 0 ? "create_dynamic_first_data_unavailable" :
                                             "create_dynamic_second_data_unavailable";
            return output;
        }
        (collection == 0 ? output.first_data : output.second_data) = data;
        std::int32_t count{};
        if (!ReadPietyPriceNumericField12004(bindings.access, price_payload,
                collection == 0 ? 0x14 : 0x5C, count)) {
            output.reason = collection == 0 ? "create_dynamic_first_count_unavailable" :
                                             "create_dynamic_second_count_unavailable";
            return output;
        }
        (collection == 0 ? output.first_count_raw : output.second_count_raw) = count;
        if (count < 0) {
            output.reason = "create_dynamic_negative_parent_range_unsupported";
            return output;
        }
        const auto occurrences = static_cast<std::size_t>(count);
        const auto consumed = output.ordered_contributions.size();
        if (consumed > bindings.maximum_total_occurrences ||
            occurrences > bindings.maximum_total_occurrences - consumed) {
            output.reason = "create_dynamic_occurrence_budget_exceeded";
            return output;
        }
        if (occurrences != 0 && (data == 0 ||
            occurrences > ((std::numeric_limits<std::uintptr_t>::max)() - data) / 8)) {
            output.reason = "create_dynamic_parent_range_unavailable_or_wraps";
            return output;
        }
        for (std::size_t ordinal = 0; ordinal != occurrences; ++ordinal) {
            output.stopped_ordinal = ordinal;
            CreatePietyDynamicContribution12004 row;
            row.collection = collection;
            row.ordinal = ordinal;
            row.prefix_before_bits = row.prefix_after_bits = output.completed_prefix_bits;
            if (!ReadPietyPriceNumericField12004(bindings.access, data, ordinal * 8,
                    row.full_element_pointer)) {
                output.reason = "create_dynamic_ordered_element_unavailable";
                return output;
            }
            if (collection == 0) {
                if (!create_dynamic_price_detail::SameAccess(bindings.access,
                        bindings.definition_numeric.access)) {
                    output.reason = "create_dynamic_first_read_source_mismatch";
                    output.reached_numeric_sources_ready = false;
                    output.ordered_contributions.push_back(std::move(row));
                    return output;
                }
                auto child = ReadPietyPriceNumeric31D9930Dynamic12004(
                    bindings.definition_numeric, row.full_element_pointer,
                    current_rite, unchanged_snapshot_revision);
                const bool ready = child.source_ready;
                const auto raw = child.native_eax_raw;
                if (!ready || !raw) output.reason = child.reason;
                row.child.template emplace<1>(std::move(child));
                if (!ready || !raw) {
                    output.reached_numeric_sources_ready &= ready;
                    output.ordered_contributions.push_back(std::move(row));
                    return output;
                }
                create_dynamic_price_detail::Apply(output, row, *raw);
            } else {
                if (!create_dynamic_price_detail::SameAccess(bindings.access,
                        bindings.entry_numeric.access)) {
                    output.reason = "create_dynamic_second_read_source_mismatch";
                    output.reached_numeric_sources_ready = false;
                    output.ordered_contributions.push_back(std::move(row));
                    return output;
                }
                auto child = ReadPietyPriceNumeric31DF3B0Dynamic12004(
                    bindings.entry_numeric, row.full_element_pointer,
                    current_rite, unchanged_snapshot_revision);
                const bool ready = child.source_ready;
                const auto raw = child.native_eax_raw;
                if (!ready || !raw) output.reason = child.reason;
                row.child.template emplace<2>(std::move(child));
                if (!ready || !raw) {
                    output.reached_numeric_sources_ready &= ready;
                    output.ordered_contributions.push_back(std::move(row));
                    return output;
                }
                create_dynamic_price_detail::Apply(output, row, *raw);
            }
            output.ordered_contributions.push_back(std::move(row));
        }
    }
    output.complete = true;
    output.status = "available";
    output.reason = "create_dynamic_base_arithmetic_complete";
    output.stopped_collection.reset();
    output.stopped_ordinal.reset();
    output.base_price_bits = output.completed_prefix_bits;
    std::int64_t signed_value{};
    std::memcpy(&signed_value, &output.completed_prefix_bits, sizeof(signed_value));
    output.base_price_raw_q64 = signed_value;
    return output;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
