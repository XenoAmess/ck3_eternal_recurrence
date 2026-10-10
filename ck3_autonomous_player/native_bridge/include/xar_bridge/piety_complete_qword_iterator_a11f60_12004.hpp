#pragma once

#include <cstdint>
#include <optional>
#include <vector>

namespace xar::ck3_12004::piety_price_raw_inputs {

// Exact A11F60 iterator projection over a complete copied source extent.
// A known end iterator, including zero for a known empty extent, is distinct
// from unavailable. The caller separately applies its post-return header read.
// This helper performs no native call, memory read, TLS initialization, or query.
std::optional<std::uintptr_t> FindCompleteQwordIteratorA11F6012004(
    const std::vector<std::uint64_t>& copied_values,
    bool complete_values_observed,
    std::uintptr_t initial_begin,
    std::uintptr_t initial_end,
    std::uint64_t literal_definition_key) noexcept;

}  // namespace xar::ck3_12004::piety_price_raw_inputs
