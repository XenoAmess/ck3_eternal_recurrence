#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include "xar_bridge/create_piety_base_cost_12004.hpp"
#include "xar_bridge/religion_owned_edit_base_price_2c64710_12004.hpp"
#include "xar_bridge/religion_owned_edit_base_price_2c64710_12004_focus.hpp"
#include <array>
#include <cstdio>
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004::piety_price_raw_inputs {
std::size_t RunPietyPriceNumeric31D9930NewCases12004();
void VerifyPietyPriceNumeric31DF3B0OwnedCases12004();
}

namespace {
using namespace xar::ck3_12004::piety_price_raw_inputs;
constexpr const char* actual_sha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::uint64_t revision = 0xF123456789ABCDEFULL;
std::array<char, 512> failure_text{};
std::size_t completed_cases{};

void Require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

struct Range { std::uintptr_t begin{}; std::size_t size{}; };
struct Memory {
    std::array<std::uint8_t, 0x80> payload{};
    std::array<std::uint8_t, 0x900> first_definition{};
    std::array<std::uint8_t, 0x900> second_definition{};
    std::array<std::uint8_t, 0x800> rite{};
    std::array<std::uintptr_t, 4> first_rows{};
    std::array<std::uintptr_t, 4> second_rows{};
    std::array<std::uintptr_t, 2> existing_first{};
    std::array<std::uintptr_t, 2> existing_second{};
    std::array<std::uintptr_t, 128> reads{};
    std::size_t read_count{};
    std::uintptr_t denied{};

    template<class T> void Set(std::size_t offset, T value) {
        std::memcpy(payload.data() + offset, &value, sizeof(value));
    }
    void Arrays(std::int32_t first_count, std::int32_t second_count) {
        Set<std::uintptr_t>(0x8, first_count == 0 ? 0 :
            reinterpret_cast<std::uintptr_t>(first_rows.data()));
        Set<std::int32_t>(0x14, first_count);
        Set<std::uintptr_t>(0x50, second_count == 0 ? 0 :
            reinterpret_cast<std::uintptr_t>(second_rows.data()));
        Set<std::int32_t>(0x5C, second_count);
    }
    std::uintptr_t Payload() const {
        return reinterpret_cast<std::uintptr_t>(payload.data());
    }
    std::uintptr_t First() const {
        return reinterpret_cast<std::uintptr_t>(first_definition.data());
    }
    std::uintptr_t Second() const {
        return reinterpret_cast<std::uintptr_t>(second_definition.data());
    }
    std::uintptr_t Rite() const {
        return reinterpret_cast<std::uintptr_t>(rite.data());
    }
    void Literal(std::array<std::uint8_t, 0x900>& object,
                 std::size_t raw_offset, std::int32_t value) {
        std::memcpy(object.data() + raw_offset, &value, sizeof(value));
    }
    bool Saw(std::uintptr_t address) const {
        for (std::size_t i = 0; i != read_count && i != reads.size(); ++i)
            if (reads[i] == address) return true;
        return false;
    }
};

bool Read(void* context, const void* source, void* output,
          std::size_t size) noexcept {
    auto& memory = *static_cast<Memory*>(context);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    if (memory.read_count < memory.reads.size()) memory.reads[memory.read_count] = address;
    ++memory.read_count;
    if (address == memory.denied) return false;
    const std::array<Range, 8> ranges{{
        {memory.Payload(), memory.payload.size()},
        {memory.First(), memory.first_definition.size()},
        {memory.Second(), memory.second_definition.size()},
        {reinterpret_cast<std::uintptr_t>(memory.first_rows.data()), sizeof(memory.first_rows)},
        {reinterpret_cast<std::uintptr_t>(memory.second_rows.data()), sizeof(memory.second_rows)},
        {memory.Rite(), memory.rite.size()},
        {reinterpret_cast<std::uintptr_t>(memory.existing_first.data()), sizeof(memory.existing_first)},
        {reinterpret_cast<std::uintptr_t>(memory.existing_second.data()), sizeof(memory.existing_second)},
    }};
    for (const auto& range : ranges) {
        if (address >= range.begin && size <= range.size &&
            address - range.begin <= range.size - size) {
            std::memcpy(output, source, size);
            return true;
        }
    }
    return false;
}

CreatePietyBaseCostBindings12004 Bind(Memory& memory) {
    Numeric31D9930Bindings12004 definition{1, &memory, Read, true};
    Numeric31DF3B0Bindings12004 entry{1, &memory, Read, true};
    return BindCreatePietyBaseCost12004(1, actual_sha, Read, &memory, definition, entry);
}

std::size_t ParentCases() {
    {
        Memory memory;
        memory.Arrays(0, 0);
        auto binding = Bind(memory);
        binding.definition_numeric = {};
        binding.entry_numeric = {};
        const auto value = ReadCreatePietyBaseCost12004(binding, memory.Payload(), 0, revision);
        Require(value.complete && value.native_base_price_raw == 0 &&
                value.ordered_contributions.empty() && value.first_count_raw == 0 &&
                value.second_count_raw == 0 && value.unchanged_snapshot_revision == revision,
                "empty arrays demanded an unreached scalar or fabricated unknown");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Arrays(3, 1);
        memory.Literal(memory.first_definition, 0x7F8, 2);
        memory.Literal(memory.second_definition, 0x7F8, -1);
        memory.Literal(memory.first_definition, 0x340, 3);
        memory.first_rows = {memory.First(), memory.First(), memory.Second(), 0};
        memory.second_rows[0] = memory.First();
        const auto value = ReadCreatePietyBaseCost12004(Bind(memory), memory.Payload(), 0xDEAD, revision);
        Require(value.complete && value.native_base_price_raw == 600000 &&
                value.ordered_contributions.size() == 4 &&
                value.ordered_contributions[0].full_element_pointer == memory.First() &&
                value.ordered_contributions[1].full_element_pointer == memory.First() &&
                value.ordered_contributions[2].native_eax_raw == -1 &&
                value.ordered_contributions[3].collection == 1 &&
                value.ordered_contributions[3].native_eax_raw == 3 &&
                !value.actual_original_consumed_values,
                "ordered duplicate first/second production scalar composition changed");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Arrays(1, 1);
        memory.Literal(memory.first_definition, 0x7F8, (std::numeric_limits<std::int32_t>::max)());
        memory.Literal(memory.first_definition, 0x340, (std::numeric_limits<std::int32_t>::min)());
        memory.first_rows[0] = memory.First();
        memory.second_rows[0] = memory.First();
        const auto value = ReadCreatePietyBaseCost12004(Bind(memory), memory.Payload(), 0xDEAD, revision);
        Require(value.complete && value.native_base_price_raw == -100000 &&
                value.native_base_price_bits == static_cast<std::uint64_t>(std::int64_t{-100000}),
                "signed32 boundaries or modulo64 final output changed");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Arrays(2, 1);
        memory.Literal(memory.first_definition, 0x7F8, 2);
        memory.first_rows[0] = memory.First();
        memory.first_rows[1] = memory.Second();
        memory.second_rows[0] = memory.First();
        memory.denied = memory.Second() + 0x7F8;
        const auto value = ReadCreatePietyBaseCost12004(Bind(memory), memory.Payload(), 0xDEAD, revision);
        Require(!value.complete && !value.native_base_price_raw &&
                value.completed_prefix_sum_bits == 200000 &&
                value.stopped_collection == 0 && value.stopped_ordinal == 1 &&
                value.reached_numeric_reason == "piety_numeric_static_eax_raw_unavailable" &&
                !value.second_data && !memory.Saw(memory.Payload() + 0x50) &&
                value.ordered_contributions.size() == 2 &&
                !value.ordered_contributions.back().contribution_applied,
                "reached first scalar unknown lost prefix/reason or read later collection");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Arrays(1, 1);
        memory.Literal(memory.first_definition, 0x7F8, -4);
        memory.first_rows[0] = memory.First();
        memory.second_rows[0] = memory.Second();
        memory.denied = memory.Second() + 0x340;
        const auto value = ReadCreatePietyBaseCost12004(Bind(memory), memory.Payload(), 0xDEAD, revision);
        Require(!value.complete && !value.native_base_price_raw &&
                value.completed_prefix_sum_bits == static_cast<std::uint64_t>(std::int64_t{-400000}) &&
                value.stopped_collection == 1 && value.stopped_ordinal == 0 &&
                value.reached_numeric_reason == "piety_numeric_static_eax_raw_unavailable",
                "second scalar unknown supplied a quote or lost first completed prefix");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Arrays(0, 1);
        memory.Literal(memory.first_definition, 0x340, -3);
        memory.second_rows[0] = memory.First();
        auto binding = Bind(memory);
        binding.definition_numeric = {};
        const auto value = ReadCreatePietyBaseCost12004(binding, memory.Payload(), 0xDEAD, revision);
        Require(value.complete && value.native_base_price_raw == -300000 &&
                value.ordered_contributions.size() == 1,
                "unused first scalar binding blocked second-only source traversal");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Arrays(-1, 0);
        const auto negative = ReadCreatePietyBaseCost12004(Bind(memory), memory.Payload(), 0xDEAD, revision);
        Require(!negative.complete && negative.first_count_raw == -1 &&
                !negative.native_base_price_raw && negative.ordered_contributions.empty(),
                "negative native range was clamped or reinterpreted");
        memory.Arrays(2, 0);
        auto binding = Bind(memory);
        binding.maximum_total_occurrences = 1;
        const auto bounded = ReadCreatePietyBaseCost12004(binding, memory.Payload(), 0xDEAD, revision);
        Require(!bounded.complete && bounded.first_count_raw == 2 &&
                !bounded.native_base_price_raw && bounded.ordered_contributions.empty(),
                "read budget supplied a partial range as a final quote");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Arrays(1, 1);
        memory.denied = memory.Payload() + 0x14;
        const auto unavailable = ReadCreatePietyBaseCost12004(Bind(memory), memory.Payload(), 0xDEAD, revision);
        Require(!unavailable.complete && unavailable.first_data && !unavailable.first_count_raw &&
                !unavailable.second_data && !unavailable.native_base_price_raw,
                "count read failure fabricated input or reached later fields");
        ++completed_cases;
    }
    return 8;
}

std::size_t CapturedArithmeticCases() {
    // MOVSXD/IMUL/ADD bytes are retained actual2C6430E/311/318 instruction bytes.
    const std::array<std::uint8_t, 34> code{{
        0x56, 0x41, 0x56, 0x51, 0x48, 0x8D, 0x34, 0x24, 0x8B, 0xC2,
        0x48, 0x63, 0xC8, 0x4C, 0x69, 0xF1, 0xA0, 0x86, 0x01, 0x00,
        0x4C, 0x01, 0x36,
        0x48, 0x8B, 0x06, 0x48, 0x83, 0xC4, 0x08, 0x41, 0x5E, 0x5E, 0xC3
    }};
    auto* executable = VirtualAlloc(nullptr, code.size(), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    Require(executable != nullptr, "captured arithmetic fixture allocation failed");
    std::memcpy(executable, code.data(), code.size());
    FlushInstructionCache(GetCurrentProcess(), executable, code.size());
    using Captured = std::uint64_t (__attribute__((ms_abi)) *)(std::uint64_t, std::int32_t);
    const auto captured = reinterpret_cast<Captured>(executable);
    const std::array<std::pair<std::uint64_t, std::int32_t>, 4> inputs{{
        {0, (std::numeric_limits<std::int32_t>::min)()},
        {(std::numeric_limits<std::uint64_t>::max)() - 9, 1},
        {0x8000000000000000ULL, -1},
        {0xFFFFFFFF00000000ULL, (std::numeric_limits<std::int32_t>::max)()},
    }};
    bool equal = true;
    for (const auto& input : inputs) {
        CreatePietyBaseCostObservation12004 parent;
        parent.completed_prefix_sum_bits = input.first;
        CreatePriceContribution12004 contribution;
        create_price_detail::Apply(parent, contribution, input.second);
        equal &= captured(input.first, input.second) == parent.completed_prefix_sum_bits;
    }
    VirtualFree(executable, 0, MEM_RELEASE);
    Require(equal, "pure arithmetic disagreed with captured signed/low64 instructions");
    ++completed_cases;
    return 1;
}

void ConnectedOwnedEditCase() {
    Memory memory;
    memory.Arrays(3, 2);
    memory.first_rows = {memory.First(), memory.First(), memory.Second(), 0};
    memory.second_rows = {memory.First(), memory.Second(), 0, 0};
    memory.existing_first[0] = memory.Second();
    memory.existing_second[0] = memory.Second();
    memory.Literal(memory.first_definition, 0x7F8, 2);
    memory.Literal(memory.second_definition, 0x7F8, -1);
    memory.Literal(memory.first_definition, 0x340, 3);
    memory.Literal(memory.second_definition, 0x340, 9);
    const auto first_existing = reinterpret_cast<std::uintptr_t>(memory.existing_first.data());
    const auto second_existing = reinterpret_cast<std::uintptr_t>(memory.existing_second.data());
    const std::int32_t one = 1;
    std::memcpy(memory.rite.data() + 0x758, &first_existing, sizeof(first_existing));
    std::memcpy(memory.rite.data() + 0x764, &one, sizeof(one));
    std::memcpy(memory.rite.data() + 0x7A0, &second_existing, sizeof(second_existing));
    std::memcpy(memory.rite.data() + 0x7AC, &one, sizeof(one));
    OwnedEditBasePriceBindings12004 binding;
    binding.access.context = &memory;
    binding.access.read_memory = Read;
    binding.access.module_base = 1;
    binding.access.exact_12004_bound = true;
    binding.read_31d9930 = ReadPietyPriceNumeric31D9930Adapter12004;
    binding.read_31df3b0 = ReadPietyPriceNumeric31DF3B0Adapter12004;
    const auto value = ReadOwnedEditBasePrice2C6471012004(
        binding, memory.Payload(), memory.Rite(), revision);
    Require(value.complete && value.base_price_raw_q64 == 700000 &&
            value.reached_occurrences.size() == 5 &&
            value.reached_occurrences[2].skip == true &&
            value.reached_occurrences[4].skip == true &&
            !memory.Saw(memory.Rite() + 8),
            "edit membership/scalar production chain changed or demanded unused Rite context");
    ++completed_cases;
}

} // namespace

extern "C" __declspec(dllexport) int RunCreatePietyConnectedGroup12004(int group) noexcept {
    try {
        failure_text.fill(0);
        switch (group) {
        case 0:
            completed_cases += xar::ck3_12004::piety_price_raw_inputs::RunPietyPriceNumeric31D9930NewCases12004();
            break;
        case 1:
            xar::ck3_12004::piety_price_raw_inputs::VerifyPietyPriceNumeric31DF3B0OwnedCases12004();
            completed_cases += 6;
            break;
        case 2: ParentCases(); break;
        case 3:
            Require(xar::ck3_12004::piety_price_raw_inputs::RunOwnedEditBasePriceFocus12004(),
                    "14e five new owned-edit source composition scenarios failed");
            completed_cases += 5;
            break;
        case 4: ConnectedOwnedEditCase(); break;
        case 5: CapturedArithmeticCases(); break;
        default: throw std::runtime_error("unknown connected fragment");
        }
        return 0;
    } catch (const std::exception& error) {
        std::snprintf(failure_text.data(), failure_text.size(), "%s", error.what());
        return 1;
    } catch (...) {
        std::snprintf(failure_text.data(), failure_text.size(), "%s", "nonstandard fixture failure");
        return 2;
    }
}

extern "C" __declspec(dllexport) int RunCreatePietyConnectedFocus12004() noexcept {
    completed_cases = 0;
    for (int group = 0; group != 6; ++group) {
        const auto result = RunCreatePietyConnectedGroup12004(group);
        if (result != 0) return result;
    }
    return 0;
}

extern "C" __declspec(dllexport) const char* GetCreatePietyFocusFailure12004() noexcept {
    return failure_text.data();
}
extern "C" __declspec(dllexport) std::size_t GetCreatePietyFocusCaseCount12004() noexcept {
    return completed_cases;
}
