#pragma once

#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::conception_pair_value_inputs {

inline constexpr std::string_view kExecutableSha256 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::uint32_t kProviderRva = 0x2B95670;
inline constexpr std::array<std::uint32_t, 7> kLoadedNumericSlotRvas{
    0x5C6A1B0, 0x5C69DB8, 0x5C69DC0, 0x5C69ED0,
    0x5C69DF0, 0x5C69E00, 0x5C69DF8};

// These are provider roles, not inferred authored define names. All seven
// values are actual loaded signed Q64 values, including genuine zero/negative.
struct LoadedNumericInputs {
    std::int64_t base_average_floor{};
    std::int64_t linked_pair_addend{};
    std::int64_t linked_pair_title_state_addend{};
    std::int64_t both_title_state_absent_multiplier{};
    std::int64_t first_relation_multiplier{};
    std::int64_t second_relation_multiplier{};
    std::int64_t alternate_relation_multiplier{};
};

using ReadMemory = bool (*)(void* context, std::uintptr_t address,
                           void* output, std::size_t size);

// The caller supplies its already qualified actual4 module and held build pin.
// No original provider or nested native function is called by this leaf.
struct Bindings {
    std::uintptr_t module_base{};
    std::string_view executable_sha256;
    ReadMemory read_memory{};
    void* context{};
};

enum class LoadedReadStatus {
    available,
    actual_build_unavailable,
    module_base_unavailable,
    memory_reader_unavailable,
    slot_read_failed,
};

struct LoadedReadResult {
    LoadedReadStatus status{LoadedReadStatus::actual_build_unavailable};
    std::optional<LoadedNumericInputs> inputs;
    std::uint32_t failed_slot_rva{};
};

[[nodiscard]] LoadedReadResult ReadLoadedNumericInputs(const Bindings& bindings);

enum class BaseStatus {
    available,
    first_raw_unavailable,
    second_raw_unavailable,
    floor_unavailable,
};

enum class BaseBranch { unavailable, signed_minimum, fast_scale, split_scale };

struct BaseResult {
    BaseStatus status{BaseStatus::first_raw_unavailable};
    BaseBranch branch{BaseBranch::unavailable};
    std::optional<std::int64_t> raw;
};

namespace detail {

[[nodiscard]] constexpr std::int64_t WrapAdd(std::int64_t first,
                                           std::int64_t second) noexcept {
    return std::bit_cast<std::int64_t>(std::bit_cast<std::uint64_t>(first) +
                                       std::bit_cast<std::uint64_t>(second));
}

[[nodiscard]] constexpr std::int64_t WrapMultiply(std::int64_t first,
                                                std::int64_t second) noexcept {
    return std::bit_cast<std::int64_t>(std::bit_cast<std::uint64_t>(first) *
                                       std::bit_cast<std::uint64_t>(second));
}

}  // namespace detail

// Exact base stage at actual2B95F87..2B96056. This accepts raw values supplied
// by separately qualified per-character providers; it does not alias ordinary
// effective fertility, run preceding eligibility gates, or return the final
// conception provider qword. The caller retains missing source as unavailable.
[[nodiscard]] constexpr BaseResult EvaluateBaseStage(
    std::optional<std::int64_t> first_raw,
    std::optional<std::int64_t> second_raw,
    std::optional<std::int64_t> loaded_floor) noexcept {
    if (!first_raw) {
        return {BaseStatus::first_raw_unavailable, BaseBranch::unavailable, {}};
    }
    if (!second_raw) {
        return {BaseStatus::second_raw_unavailable, BaseBranch::unavailable, {}};
    }
    if (!loaded_floor) {
        return {BaseStatus::floor_unavailable, BaseBranch::unavailable, {}};
    }
    const auto minimum = *first_raw < *second_raw ? *first_raw : *second_raw;
    if (minimum < *loaded_floor) {
        return {BaseStatus::available, BaseBranch::signed_minimum, minimum};
    }

    const auto sum = detail::WrapAdd(*first_raw, *second_raw);
    // LEA/CMP/JA selects the source fast path using an unsigned wrapped check.
    const auto adjusted_bits = std::bit_cast<std::uint64_t>(sum) + 0xB504F333ULL;
    if (adjusted_bits <= 0x16A09E666ULL) {
        return {BaseStatus::available, BaseBranch::fast_scale,
                detail::WrapMultiply(sum, 50000) / 100000};
    }

    // Source split path: max/min, signed quotient, wrapped remainder product,
    // signed quotient, wrapped addition. For large negative sums the product
    // can wrap, so replacing this whole path with sum/2 changes native results.
    const auto maximum = sum > 50000 ? sum : std::int64_t{50000};
    const auto smaller = sum < 50000 ? sum : std::int64_t{50000};
    const auto quotient = maximum / 100000;
    const auto remainder = maximum - quotient * 100000;
    const auto fractional = detail::WrapMultiply(remainder, smaller) / 100000;
    return {BaseStatus::available, BaseBranch::split_scale,
            detail::WrapAdd(fractional, detail::WrapMultiply(smaller, quotient))};
}

}  // namespace xar::ck3_12004::conception_pair_value_inputs
