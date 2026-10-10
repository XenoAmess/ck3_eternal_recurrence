#pragma once

#include "xar_bridge/piety_price_numeric_31d9930_12004.hpp"
#include "xar_bridge/piety_price_numeric_31df3b0_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <variant>
#include <vector>

namespace xar::ck3_12004::piety_price_raw_inputs {

static_assert(sizeof(std::uintptr_t) == 8, "actual1.20.0.4 price arrays contain full QWORD pointers");

using CreatePriceGuardedRead12004 =
    bool (*)(void*, const void*, void*, std::size_t) noexcept;

using DefinitionPriceObservation12004 = decltype(ReadPietyPriceNumeric31D993012004(
    std::declval<const Numeric31D9930Bindings12004&>(),
    std::uintptr_t{}, std::uintptr_t{}, std::uint64_t{}));
using EntryPriceObservation12004 = decltype(ReadPietyPriceNumeric31DF3B012004(
    std::declval<const Numeric31DF3B0Bindings12004&>(),
    std::uintptr_t{}, std::uintptr_t{}, std::uint64_t{}));

struct CreatePietyBaseCostBindings12004 {
    std::uintptr_t module_base{};
    void* context{};
    CreatePriceGuardedRead12004 guarded_read{};
    bool exact_12004_bound{};
    std::size_t maximum_total_occurrences{4096};
    Numeric31D9930Bindings12004 definition_numeric{};
    Numeric31DF3B0Bindings12004 entry_numeric{};
};

inline CreatePietyBaseCostBindings12004 BindCreatePietyBaseCost12004(
    std::uintptr_t module_base, std::string_view held_executable_sha256,
    CreatePriceGuardedRead12004 guarded_read, void* context,
    Numeric31D9930Bindings12004 definition_numeric,
    Numeric31DF3B0Bindings12004 entry_numeric,
    std::size_t maximum_total_occurrences = 4096) {
    CreatePietyBaseCostBindings12004 result;
    result.module_base = module_base;
    result.context = context;
    result.guarded_read = guarded_read;
    result.exact_12004_bound = module_base != 0 && guarded_read != nullptr &&
        held_executable_sha256 ==
            "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    result.maximum_total_occurrences = maximum_total_occurrences;
    result.definition_numeric = std::move(definition_numeric);
    result.entry_numeric = std::move(entry_numeric);
    return result;
}

struct CreatePriceContribution12004 {
    std::uint8_t collection{};
    std::size_t ordinal{};
    std::uintptr_t full_element_pointer{};
    std::optional<std::int32_t> native_eax_raw;
    std::optional<std::int64_t> scaled_contribution_raw;
    std::uint64_t prefix_before_bits{};
    std::uint64_t prefix_after_bits{};
    bool contribution_applied{};
    std::variant<std::monostate, DefinitionPriceObservation12004,
                 EntryPriceObservation12004> numeric_observation;
};

struct CreatePietyBaseCostObservation12004 {
    bool composition_source_ready{true};
    bool reached_numeric_sources_ready{true};
    bool complete{};
    const char* status{"unavailable"};
    const char* reason{"not_read"};
    std::uintptr_t price_payload{};
    std::uintptr_t current_rite{};
    std::uint64_t unchanged_snapshot_revision{};
    std::optional<std::uintptr_t> first_data;
    std::optional<std::int32_t> first_count_raw;
    std::optional<std::uintptr_t> second_data;
    std::optional<std::int32_t> second_count_raw;
    std::optional<std::uint8_t> stopped_collection;
    std::optional<std::size_t> stopped_ordinal;
    std::optional<std::string> reached_numeric_reason;
    std::vector<CreatePriceContribution12004> ordered_contributions;
    std::uint64_t completed_prefix_sum_bits{};
    std::optional<std::uint64_t> native_base_price_bits;
    std::optional<std::int64_t> native_base_price_raw;
    bool actual_original_consumed_values{};
};

namespace create_price_detail {

inline std::string CopyReason(std::string_view reason) {
    return std::string(reason);
}

inline std::string CopyReason(const char* reason) {
    return reason ? std::string(reason) : std::string{};
}

template<class T>
inline bool ReadAt(const CreatePietyBaseCostBindings12004& bindings,
                   std::uintptr_t base, std::size_t offset, T& value) noexcept {
    if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
        return false;
    const auto address = base + offset;
    if (sizeof(T) - 1 > (std::numeric_limits<std::uintptr_t>::max)() - address)
        return false;
    return bindings.guarded_read && bindings.guarded_read(
        bindings.context, reinterpret_cast<const void*>(address), &value, sizeof(T));
}

template<class B>
inline bool SameReadSource(const CreatePietyBaseCostBindings12004& parent,
                          const B& child) noexcept {
    return child.module_base == parent.module_base &&
        child.context == parent.context && child.guarded_read == parent.guarded_read;
}

inline std::int64_t SignedBits(std::uint64_t bits) noexcept {
    std::int64_t value;
    static_assert(sizeof(value) == sizeof(bits));
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

inline void Apply(CreatePietyBaseCostObservation12004& result,
                  CreatePriceContribution12004& contribution,
                  std::int32_t native_eax) noexcept {
    const auto scaled = static_cast<std::int64_t>(native_eax) * std::int64_t{100000};
    contribution.native_eax_raw = native_eax;
    contribution.scaled_contribution_raw = scaled;
    result.completed_prefix_sum_bits += static_cast<std::uint64_t>(scaled);
    contribution.prefix_after_bits = result.completed_prefix_sum_bits;
    contribution.contribution_applied = true;
}

} // namespace create_price_detail

// Caller supplies a stable source-bound frame. This reader never invokes a native getter.
inline CreatePietyBaseCostObservation12004 ReadCreatePietyBaseCost12004(
    const CreatePietyBaseCostBindings12004& bindings,
    std::uintptr_t price_payload, std::uintptr_t current_rite,
    std::uint64_t unchanged_snapshot_revision) {
    CreatePietyBaseCostObservation12004 result;
    result.price_payload = price_payload;
    result.current_rite = current_rite;
    result.unchanged_snapshot_revision = unchanged_snapshot_revision;
    if (!bindings.exact_12004_bound || !bindings.guarded_read) {
        result.composition_source_ready = false;
        result.reason = "exact4_read_binding_unavailable";
        return result;
    }
    if (!price_payload) {
        result.reason = "required_input_pointer_unavailable";
        return result;
    }
    for (std::uint8_t collection = 0; collection != 2; ++collection) {
        result.stopped_collection = collection;
        result.stopped_ordinal.reset();
        const std::size_t data_offset = collection == 0 ? 0x8 : 0x50;
        const std::size_t count_offset = collection == 0 ? 0x14 : 0x5C;
        std::uintptr_t data{};
        if (!create_price_detail::ReadAt(bindings, price_payload, data_offset, data)) {
            result.reason = collection == 0 ? "first_data_read_unavailable" :
                                             "second_data_read_unavailable";
            return result;
        }
        (collection == 0 ? result.first_data : result.second_data) = data;
        std::int32_t count{};
        if (!create_price_detail::ReadAt(bindings, price_payload, count_offset, count)) {
            result.reason = collection == 0 ? "first_count_read_unavailable" :
                                             "second_count_read_unavailable";
            return result;
        }
        (collection == 0 ? result.first_count_raw : result.second_count_raw) = count;
        if (count < 0) {
            result.reason = "negative_native_range_not_supported";
            return result;
        }
        const auto occurrences = static_cast<std::size_t>(count);
        const auto used = result.ordered_contributions.size();
        if (used > bindings.maximum_total_occurrences ||
            occurrences > bindings.maximum_total_occurrences - used) {
            result.reason = "readonly_occurrence_budget_exceeded";
            return result;
        }
        if (occurrences != 0 && (data == 0 ||
            occurrences > ((std::numeric_limits<std::uintptr_t>::max)() - data) / 8)) {
            result.reason = "native_range_unavailable_or_wraps";
            return result;
        }
        for (std::size_t ordinal = 0; ordinal != occurrences; ++ordinal) {
            result.stopped_ordinal = ordinal;
            CreatePriceContribution12004 contribution;
            contribution.collection = collection;
            contribution.ordinal = ordinal;
            contribution.prefix_before_bits = result.completed_prefix_sum_bits;
            contribution.prefix_after_bits = result.completed_prefix_sum_bits;
            if (!create_price_detail::ReadAt(bindings, data, ordinal * 8,
                                            contribution.full_element_pointer)) {
                result.reason = "ordered_element_read_unavailable";
                return result;
            }
            if (collection == 0) {
                if (!create_price_detail::SameReadSource(bindings, bindings.definition_numeric)) {
                    result.reached_numeric_sources_ready = false;
                    result.reason = "definition_numeric_read_source_mismatch";
                    result.ordered_contributions.push_back(std::move(contribution));
                    return result;
                }
                auto child = ReadPietyPriceNumeric31D993012004(
                    bindings.definition_numeric, contribution.full_element_pointer,
                    current_rite, unchanged_snapshot_revision);
                const auto ready = child.source_ready;
                const auto raw = child.native_eax_raw;
                if (!ready || !raw)
                    result.reached_numeric_reason = create_price_detail::CopyReason(child.reason);
                contribution.numeric_observation.template emplace<1>(std::move(child));
                if (!ready || !raw) {
                    result.reached_numeric_sources_ready &= ready;
                    result.reason = "definition_numeric_reached_unavailable";
                    result.ordered_contributions.push_back(std::move(contribution));
                    return result;
                }
                create_price_detail::Apply(result, contribution, *raw);
            } else {
                if (!create_price_detail::SameReadSource(bindings, bindings.entry_numeric)) {
                    result.reached_numeric_sources_ready = false;
                    result.reason = "entry_numeric_read_source_mismatch";
                    result.ordered_contributions.push_back(std::move(contribution));
                    return result;
                }
                auto child = ReadPietyPriceNumeric31DF3B012004(
                    bindings.entry_numeric, contribution.full_element_pointer,
                    current_rite, unchanged_snapshot_revision);
                const auto ready = child.source_ready;
                const auto raw = child.native_eax_raw;
                if (!ready || !raw)
                    result.reached_numeric_reason = create_price_detail::CopyReason(child.reason);
                contribution.numeric_observation.template emplace<2>(std::move(child));
                if (!ready || !raw) {
                    result.reached_numeric_sources_ready &= ready;
                    result.reason = "entry_numeric_reached_unavailable";
                    result.ordered_contributions.push_back(std::move(contribution));
                    return result;
                }
                create_price_detail::Apply(result, contribution, *raw);
            }
            result.ordered_contributions.push_back(std::move(contribution));
        }
    }
    result.complete = true;
    result.stopped_collection.reset();
    result.stopped_ordinal.reset();
    result.status = "available";
    result.reason = "actual_create_base_price_arithmetic_complete";
    result.native_base_price_bits = result.completed_prefix_sum_bits;
    result.native_base_price_raw = create_price_detail::SignedBits(result.completed_prefix_sum_bits);
    return result;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
