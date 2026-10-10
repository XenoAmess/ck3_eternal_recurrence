#include "xar_bridge/conception_pair_value_inputs_12004.hpp"

#include <cstring>
#include <limits>

namespace pair = xar::ck3_12004::conception_pair_value_inputs;

namespace {

unsigned checks = 0;

#define CHECK(condition) do { ++checks; if (!(condition)) return __LINE__; } while (false)

struct MemoryFixture {
    std::uintptr_t base{0x140000000ULL};
    std::array<std::int64_t, 7> slots{40000, 0, -100, 100000, 75000, -1, 120000};
    std::uint32_t failed_rva{};
    unsigned reads{};

    static bool Read(void* context, std::uintptr_t address,
                     void* output, std::size_t size) {
        auto& fixture = *static_cast<MemoryFixture*>(context);
        ++fixture.reads;
        if (size != sizeof(std::int64_t)) return false;
        for (std::size_t index = 0; index < pair::kLoadedNumericSlotRvas.size(); ++index) {
            const auto rva = pair::kLoadedNumericSlotRvas[index];
            if (address == fixture.base + rva) {
                if (fixture.failed_rva == rva) return false;
                std::memcpy(output, &fixture.slots[index], size);
                return true;
            }
        }
        return false;
    }
};

}  // namespace

extern "C" __declspec(dllexport) int RunConceptionPairValueFixture12004() {
    checks = 0;
    auto result = pair::EvaluateBaseStage(40000, 25000, 30000);
    CHECK(result.status == pair::BaseStatus::available);
    CHECK(result.branch == pair::BaseBranch::signed_minimum);
    CHECK(result.raw == 25000);
    result = pair::EvaluateBaseStage(40000, 60000, 40000);
    CHECK(result.branch == pair::BaseBranch::fast_scale);
    CHECK(result.raw == 50000);
    CHECK(pair::EvaluateBaseStage(60000, 40000, 40000).raw == result.raw);
    CHECK(pair::EvaluateBaseStage(0, 1, 0).raw == 0);
    CHECK(pair::EvaluateBaseStage(-1, -2, -2).raw == -1);
    CHECK(pair::EvaluateBaseStage(-10, 50, 0).raw == -10);

    result = pair::EvaluateBaseStage(3000000000LL, 6000000000LL, 0);
    CHECK(result.branch == pair::BaseBranch::split_scale);
    CHECK(result.raw == 4500000000LL);
    constexpr auto maximum = std::numeric_limits<std::int64_t>::max();
    constexpr auto minimum = std::numeric_limits<std::int64_t>::min();
    CHECK(pair::EvaluateBaseStage(maximum, maximum, 0).raw == -1);
    result = pair::EvaluateBaseStage(minimum / 4, minimum / 4, minimum);
    CHECK(result.branch == pair::BaseBranch::split_scale);
    CHECK(result.raw == 0);  // Wrapped50000*(MIN/2) is0, not mathematicalmean.
    result = pair::EvaluateBaseStage(1, 3037000498LL, 0);
    CHECK(result.branch == pair::BaseBranch::fast_scale);
    result = pair::EvaluateBaseStage(1, 3037000499LL, 0);
    CHECK(result.branch == pair::BaseBranch::split_scale);
    CHECK(result.raw == 1518500250LL);
    result = pair::EvaluateBaseStage(-1, -3037000498LL, minimum);
    CHECK(result.branch == pair::BaseBranch::fast_scale);
    result = pair::EvaluateBaseStage(-1, -3037000499LL, minimum);
    CHECK(result.branch == pair::BaseBranch::split_scale);
    CHECK(result.raw == -1518500250LL);

    result = pair::EvaluateBaseStage({}, 5, 0);
    CHECK(result.status == pair::BaseStatus::first_raw_unavailable);
    CHECK(!result.raw.has_value());
    result = pair::EvaluateBaseStage(5, {}, 0);
    CHECK(result.status == pair::BaseStatus::second_raw_unavailable);
    CHECK(!result.raw.has_value());
    result = pair::EvaluateBaseStage(5, 5, {});
    CHECK(result.status == pair::BaseStatus::floor_unavailable);
    CHECK(!result.raw.has_value());

    MemoryFixture memory;
    pair::Bindings bindings{memory.base, pair::kExecutableSha256,
                            MemoryFixture::Read, &memory};
    auto loaded = pair::ReadLoadedNumericInputs(bindings);
    CHECK(loaded.status == pair::LoadedReadStatus::available);
    CHECK(memory.reads == 7);
    CHECK(loaded.inputs.has_value());
    CHECK(loaded.inputs->base_average_floor == 40000);
    CHECK(loaded.inputs->linked_pair_addend == 0);
    CHECK(loaded.inputs->linked_pair_title_state_addend == -100);
    CHECK(loaded.inputs->both_title_state_absent_multiplier == 100000);
    CHECK(loaded.inputs->first_relation_multiplier == 75000);
    CHECK(loaded.inputs->second_relation_multiplier == -1);
    CHECK(loaded.inputs->alternate_relation_multiplier == 120000);
    memory.failed_rva = pair::kLoadedNumericSlotRvas[2];
    memory.reads = 0;
    loaded = pair::ReadLoadedNumericInputs(bindings);
    CHECK(loaded.status == pair::LoadedReadStatus::slot_read_failed);
    CHECK(loaded.failed_slot_rva == memory.failed_rva);
    CHECK(memory.reads == 3);
    CHECK(!loaded.inputs.has_value());

    bindings.executable_sha256 = "historical-build";
    memory.reads = 0;
    loaded = pair::ReadLoadedNumericInputs(bindings);
    CHECK(loaded.status == pair::LoadedReadStatus::actual_build_unavailable);
    CHECK(memory.reads == 0);
    CHECK(!loaded.inputs.has_value());
    bindings.executable_sha256 = pair::kExecutableSha256;
    bindings.module_base = 0;
    CHECK(pair::ReadLoadedNumericInputs(bindings).status ==
          pair::LoadedReadStatus::module_base_unavailable);
    CHECK(memory.reads == 0);
    bindings.module_base = memory.base;
    bindings.read_memory = nullptr;
    CHECK(pair::ReadLoadedNumericInputs(bindings).status ==
          pair::LoadedReadStatus::memory_reader_unavailable);
    CHECK(memory.reads == 0);
    return 0;
}

extern "C" __declspec(dllexport) unsigned ConceptionPairValueFixtureCheckCount12004() {
    return checks;
}
