#include "xar_bridge/piety_complete_qword_iterator_a11f60_12004.hpp"

#include <cstddef>
#include <limits>

namespace xar::ck3_12004::piety_price_raw_inputs {

std::optional<std::uintptr_t> FindCompleteQwordIteratorA11F6012004(
    const std::vector<std::uint64_t>& copied_values,
    bool complete_values_observed,
    std::uintptr_t initial_begin,
    std::uintptr_t initial_end,
    std::uint64_t literal_definition_key) noexcept {
    if (!complete_values_observed || initial_end < initial_begin) {
        return std::nullopt;
    }

    constexpr std::uintptr_t stride = sizeof(std::uint64_t);
    const std::uintptr_t byte_count = initial_end - initial_begin;
    const auto maximum_signed_distance =
        static_cast<std::uintptr_t>(std::numeric_limits<std::intptr_t>::max());
    if (byte_count > maximum_signed_distance || byte_count % stride != 0) {
        return std::nullopt;
    }
    if (byte_count / stride != copied_values.size()) {
        return std::nullopt;
    }

    for (std::size_t index = 0; index < copied_values.size(); ++index) {
        if (copied_values[index] == literal_definition_key) {
            return initial_begin + static_cast<std::uintptr_t>(index) * stride;
        }
    }
    return initial_end;
}

}  // namespace xar::ck3_12004::piety_price_raw_inputs
