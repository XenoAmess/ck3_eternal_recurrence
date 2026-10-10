#include "xar_bridge/create_piety_dynamic_base_cost_12004.hpp"
#include "xar_bridge/religion_owned_edit_dynamic_base_price_12004.hpp"
#include "xar_bridge/religion_owned_edit_dynamic_base_price_12004_focus.hpp"

#include <array>
#include <cstdio>
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004::piety_price_raw_inputs {
std::size_t RunPietyPriceNumeric31D9930DynamicNewCases12004();
}
void VerifyPietyPriceNumeric31DF3B0DynamicOwnedCases12004();
void RunPietyPriceNamedDefinition37540B0Focus12004();

namespace {
using namespace xar::ck3_12004::piety_price_raw_inputs;
constexpr std::uint64_t revision = 0xFEDCBA9876543210ULL;
std::size_t completed_cases{};
std::array<char, 512> failure_text{};
void Require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}
struct Region { std::uintptr_t begin; std::size_t bytes; };
struct Memory {
    std::array<unsigned char, 0x80> payload{};
    std::array<unsigned char, 0x900> first{}, second{};
    std::array<unsigned char, 0x80> named_first{}, named_second{};
    std::array<unsigned char, 0x800> rite{};
    std::array<unsigned char, 16> root{}, provider{};
    std::array<unsigned char, 32> tuple{};
    std::array<unsigned char, 0x40> vtable{};
    std::array<std::uintptr_t, 5> physical_pack{};
    std::array<std::uintptr_t, 1> list_rows{};
    std::array<std::uintptr_t, 4> first_rows{}, second_rows{}, existing_first{}, existing_second{};
    std::array<std::uintptr_t, 512> read_log{};
    std::size_t read_count{}, root_copies{};
    bool change_root{}, supply_provider{true}, bad_provider_revision{}, unavailable_physical_pack{};
    std::int64_t supplied_q64{150000};
    static constexpr std::uintptr_t callback = 0x14000AB30ULL;
    template<class Block> static std::uintptr_t Address(const Block& block) {
        return reinterpret_cast<std::uintptr_t>(block.data());
    }
    template<class T, class Block> static void Put(Block& block, std::size_t offset, T value) {
        std::memcpy(reinterpret_cast<unsigned char*>(block.data()) + offset, &value, sizeof(value));
    }
    std::uintptr_t FirstExpression() const { return Address(first) + 0x760; }
    std::uintptr_t SecondExpression() const { return Address(second) + 0x2A8; }
    void Parent(std::int32_t first_count, std::int32_t second_count) {
        Put(payload, 8, first_count ? Address(first_rows) : std::uintptr_t{0});
        Put(payload, 0x14, first_count);
        Put(payload, 0x50, second_count ? Address(second_rows) : std::uintptr_t{0});
        Put(payload, 0x5C, second_count);
        first_rows[0] = first_rows[1] = Address(first);
        second_rows[0] = Address(second);
        physical_pack[0] = Address(root);
        Put(provider, 8, Address(vtable));
        Put(vtable, 0x30, callback);
        Put(vtable, 0x20, std::uintptr_t{0x14000AB20ULL});
    }
    template<class Block> void Named(Block& definition, std::size_t expression_offset,
                                     std::array<unsigned char, 0x80>& named, std::int32_t value) {
        Put(definition, expression_offset + 0xB8, std::int32_t{1});
        Put(definition, expression_offset + 0xB0, std::uintptr_t{0});
        Put(definition, expression_offset + 0xA0, Address(named));
        Put(named, 0x70, std::uintptr_t{0});
        Put(named, 0x7A, std::uint8_t{1});
        Put(named, 0x60, value);
    }
    template<class Block> void Negative(Block& definition, std::size_t expression_offset,
                                        std::uint16_t tag, std::int64_t value, std::int32_t fallback) {
        Put(definition, expression_offset + 0xB8, std::int32_t{1});
        Put(definition, expression_offset + 0xB0, std::uintptr_t{0});
        Put(definition, expression_offset + 0xA0, std::uintptr_t{0});
        Put(definition, expression_offset + 0x14, std::int32_t{-1});
        Put(definition, expression_offset + 0x98, fallback);
        Put(root, 0, tag);
        Put(root, 8, value);
    }
    template<class Block> void Provider(Block& definition, std::size_t expression_offset) {
        Put(definition, expression_offset + 0xB8, std::int32_t{1});
        Put(definition, expression_offset + 0xB0, Address(provider));
    }
    bool Saw(std::uintptr_t address) const {
        for (std::size_t i = 0; i < read_count && i < read_log.size(); ++i)
            if (read_log[i] == address) return true;
        return false;
    }
    PietyPriceNumericAccess12004 Access();
    CreatePietyDynamicBaseCostBindings12004 Bind();
};

bool Read(void* context, const void* source, void* output, std::size_t bytes) noexcept {
    auto& memory = *static_cast<Memory*>(context);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    if (memory.read_count < memory.read_log.size()) memory.read_log[memory.read_count] = address;
    ++memory.read_count;
    if (address == Memory::Address(memory.rite) + 8) return false;
    const std::array<Region, 16> regions{{
        {Memory::Address(memory.payload), sizeof(memory.payload)},
        {Memory::Address(memory.first), sizeof(memory.first)}, {Memory::Address(memory.second), sizeof(memory.second)},
        {Memory::Address(memory.named_first), sizeof(memory.named_first)}, {Memory::Address(memory.named_second), sizeof(memory.named_second)},
        {Memory::Address(memory.rite), sizeof(memory.rite)}, {Memory::Address(memory.root), sizeof(memory.root)},
        {Memory::Address(memory.provider), sizeof(memory.provider)}, {Memory::Address(memory.tuple), sizeof(memory.tuple)},
        {Memory::Address(memory.vtable), sizeof(memory.vtable)}, {Memory::Address(memory.physical_pack), sizeof(memory.physical_pack)},
        {Memory::Address(memory.first_rows), sizeof(memory.first_rows)}, {Memory::Address(memory.second_rows), sizeof(memory.second_rows)},
        {Memory::Address(memory.existing_first), sizeof(memory.existing_first)}, {Memory::Address(memory.existing_second), sizeof(memory.existing_second)},
        {Memory::Address(memory.list_rows), sizeof(memory.list_rows)},
    }};
    for (const auto& region : regions) {
        if (address >= region.begin && address - region.begin <= region.bytes &&
            bytes <= region.bytes - (address - region.begin)) {
            if (address == Memory::Address(memory.root) && bytes == 16) {
                ++memory.root_copies;
                if (memory.change_root && memory.root_copies == 2)
                    Memory::Put(memory.root, 8, std::int64_t{99999});
            }
            std::memcpy(output, source, bytes);
            return true;
        }
    }
    return false;
}
bool Resolve(void* context, const PietyPriceNumericAccess12004& access,
             std::uintptr_t definition, std::uintptr_t current_rite,
             std::uint64_t frame, PietyPriceA0F0B0DynamicInputs12004& output) noexcept {
    auto& memory = *static_cast<Memory*>(context);
    if (!access.exact_12004_bound || !access.guarded_read || access.module_base != 1 ||
        (definition != Memory::Address(memory.first) && definition != Memory::Address(memory.second)) ||
        current_rite != Memory::Address(memory.rite) || frame != revision) return false;
    output.copied_pack.physical_pack_identity = memory.unavailable_physical_pack
        ? std::optional<std::uintptr_t>{} : Memory::Address(memory.physical_pack);
    output.copied_pack.primary_scope_identity = Memory::Address(memory.root);
    output.copied_pack.secondary_scope_identity = 0;
    output.copied_pack.tertiary_scope_identity = 0;
    output.copied_pack.support_identity = 0;
    output.copied_pack.evaluation_flag_raw_u8 = 0;
    output.original_named_tuple_identity = Memory::Address(memory.tuple);
    if (memory.supply_provider) {
        PietyPriceProviderA0F185Output12004 witness;
        witness.expression_identity = output.expression_identity;
        witness.provider_identity = Memory::Address(memory.provider);
        witness.receiver_identity = witness.provider_identity + 8;
        witness.callback_identity = Memory::callback;
        witness.copied_pack = output.copied_pack;
        witness.original_named_tuple_identity = output.original_named_tuple_identity;
        witness.unchanged_snapshot_revision = memory.bad_provider_revision ? frame + 1 : frame;
        witness.actual_output_raw_q64 = memory.supplied_q64;
        output.provider_output = std::move(witness);
    }
    return true;
}
PietyPriceNumericAccess12004 Memory::Access() { return {1, this, Read, true}; }
CreatePietyDynamicBaseCostBindings12004 Memory::Bind() {
    const PietyPriceNumericDynamicBindings12004 child{Access(), this, Resolve};
    return {Access(), child, child, 4096};
}
PietyPriceA0F0B0DynamicInputs12004 GenericInputs(Memory& memory, std::uintptr_t expression) {
    PietyPriceA0F0B0DynamicInputs12004 inputs;
    inputs.expression_identity = expression;
    inputs.unchanged_snapshot_revision = revision;
    inputs.copied_pack.primary_scope_identity = Memory::Address(memory.root);
    return inputs;
}

void ParentDynamicCases() {
    {
        Memory memory;
        memory.Parent(2, 1);
        memory.Named(memory.first, 0x760, memory.named_first, -2);
        memory.Named(memory.second, 0x2A8, memory.named_second, 3);
        auto bindings = memory.Bind();
        bindings.definition_numeric.read_dynamic_inputs = nullptr;
        bindings.entry_numeric.read_dynamic_inputs = nullptr;
        const auto value = ReadCreatePietyDynamicBaseCost12004(bindings,
            Memory::Address(memory.payload), Memory::Address(memory.rite), revision);
        Require(value.complete && value.base_price_raw_q64 == -100000 &&
            value.ordered_contributions.size() == 3 &&
            value.ordered_contributions[0].full_element_pointer == value.ordered_contributions[1].full_element_pointer &&
            !memory.Saw(Memory::Address(memory.rite) + 8) && !value.actual_original_consumed_values,
            "dynamic named constants required unconsumed pack/Rite or lost duplicate order");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Parent(1, 0);
        memory.Negative(memory.first, 0x760, 0x2A, 12345, -7);
        const auto value = ReadCreatePietyDynamicBaseCost12004(memory.Bind(),
            Memory::Address(memory.payload), Memory::Address(memory.rite), revision);
        const auto& child = std::get<1>(value.ordered_contributions.at(0).child);
        Require(value.complete && value.base_price_raw_q64 == -700000 && child.evaluator &&
            child.evaluator->variant_source && child.evaluator->variant_source->variant_tag_raw_u16 == 0x2A &&
            !memory.Saw(Memory::Address(memory.rite) + 8),
            "supplied actual-tag2A copied context did not retain fallback boundary");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Parent(1, 0);
        memory.Provider(memory.first, 0x760);
        const auto value = ReadCreatePietyDynamicBaseCost12004(memory.Bind(),
            Memory::Address(memory.payload), Memory::Address(memory.rite), revision);
        const auto& child = std::get<1>(value.ordered_contributions.at(0).child);
        Require(value.complete && value.base_price_raw_q64 == 200000 && child.evaluator &&
            child.evaluator->provider_output_conditionally_supplied && child.evaluator->provider_conversion &&
            child.evaluator->provider_conversion->raw_q64_i64 == 150000 && !child.actual_original_consumed_values,
            "source-matched supplied B0 Q64 failed conversion or claimed native observation");
        ++completed_cases;
    }
    {
        for (int mismatch = 0; mismatch != 2; ++mismatch) {
            Memory memory;
            memory.Parent(1, 1);
            memory.Named(memory.first, 0x760, memory.named_first, -2);
            memory.Provider(memory.second, 0x2A8);
            memory.supply_provider = mismatch != 0;
            memory.bad_provider_revision = mismatch != 0;
            const auto value = ReadCreatePietyDynamicBaseCost12004(memory.Bind(),
                Memory::Address(memory.payload), Memory::Address(memory.rite), revision);
            Require(!value.complete && !value.base_price_raw_q64 &&
                value.completed_prefix_bits == static_cast<std::uint64_t>(-200000LL) &&
                value.stopped_collection == 1 && value.stopped_ordinal == 0 &&
                !value.ordered_contributions.back().contribution_applied && !value.reason.empty(),
                "missing or frame-mismatched B0 output became final price");
        }
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Parent(1, 0);
        memory.Provider(memory.first, 0x760);
        memory.unavailable_physical_pack = true;
        const auto value = ReadCreatePietyDynamicBaseCost12004(memory.Bind(),
            Memory::Address(memory.payload), Memory::Address(memory.rite), revision);
        Require(!value.complete && !value.base_price_raw_q64 &&
            value.reason == "piety_dynamic_provider_output_binding_unavailable",
            "two absent physical pack carriers were accepted as a provider witness");
        ++completed_cases;
    }
}

void NewGenericLeafCases() {
    {
        // Generic root-tag1 qualification only. Actual Rite constructors use2A.
        Memory memory;
        memory.Parent(0, 0);
        memory.Negative(memory.first, 0x760, 1, -250000, 123);
        const auto value = ReadPietyPriceA0F0B0DynamicReadonly12004(memory.Access(),
            GenericInputs(memory, memory.FirstExpression()));
        Require(value.eax_raw_i32 == -2 && value.variant_source &&
            value.variant_source->source_result_ready && value.variant_source->variant_tag_raw_u16 == 1,
            "generic signed negative variant MUL conversion changed");
        ++completed_cases;
    }
    {
        Memory memory;
        const std::array<std::pair<std::int64_t, std::int32_t>, 7> known{{
            {-150000, -2}, {-50000, -1}, {0, 0}, {49999, 0}, {50000, 1},
            {-214748364800000LL, (std::numeric_limits<std::int32_t>::min)()},
            {214748364700000LL, (std::numeric_limits<std::int32_t>::max)()},
        }};
        for (const auto& input : known) {
            const auto value = ProjectPietyFixedRoundedI3237498A012004(memory.Access(), input.first, 0, 0);
            Require(value.source_ready && value.eax_raw_i32 == input.second &&
                value.raw_q64_i64 == input.first, "new48 conversion half/sign/guard endpoint changed");
        }
        for (const auto raw : {-214748364800001LL, 214748364700001LL}) {
            const auto value = ProjectPietyFixedRoundedI3237498A012004(memory.Access(), raw, 0, revision);
            Require(!value.eax_raw_i32 && !value.source_ready, "outside conversion guard was clamped");
        }
        Require(!ProjectPietyFixedRoundedI3237498A012004(memory.Access(), {}, 0, revision).eax_raw_i32,
            "missing Q64 was converted to zero");
        Require(memory.read_count == 0, "closed conversion guard read unconsumed memory");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Parent(0, 0);
        memory.Negative(memory.first, 0x760, 1, 200000, 123);
        memory.change_root = true;
        const auto value = ReadPietyPriceA0F0B0DynamicReadonly12004(memory.Access(),
            GenericInputs(memory, memory.FirstExpression()));
        Require(!value.eax_raw_i32 && value.variant_source &&
            value.unavailable_reason == "compiled_variant_primary_root_changed_or_unavailable",
            "changed negative-root copy became a numeric result");
        ++completed_cases;
    }
    {
        Memory memory;
        memory.Parent(0, 0);
        memory.Negative(memory.first, 0x760, 0x2A, 12345, 123);
        Memory::Put(memory.first, 0x760 + 0x14, std::int32_t{1});
        Memory::Put(memory.first, 0x760 + 8, Memory::Address(memory.list_rows));
        memory.list_rows[0] = Memory::Address(memory.provider) + 8;
        Memory::Put(memory.tuple, 0, std::uintptr_t{0x123456789ABCDEF0ULL});
        auto inputs = GenericInputs(memory, memory.FirstExpression());
        inputs.original_named_tuple_identity = Memory::Address(memory.tuple);
        const auto value = ReadPietyPriceA0F0B0DynamicReadonly12004(memory.Access(), inputs);
        Require(!value.eax_raw_i32 && value.variant_source && value.compiled_provider_metadata &&
            value.compiled_provider_metadata->type_mask_slot30_raw_va == Memory::callback &&
            value.compiled_provider_metadata->value_slot20_raw_va == 0x14000AB20ULL &&
            value.compiled_provider_metadata->original_named_tuple_selected_as_numeric_input == true &&
            value.compiled_provider_metadata->selected_tuple_before_raw ==
                value.compiled_provider_metadata->selected_tuple_after_raw &&
            !value.compiled_provider_metadata->actual_value_call_reached &&
            !value.compiled_provider_metadata->returned_variant_payload_raw_q64 &&
            !value.compiled_provider_metadata->source_result_ready &&
            !value.compiled_provider_metadata->provider_method_invoked_by_projector &&
            !value.compiled_provider_metadata->value_target_body_qualified,
            "positive provider metadata fabricated dispatch or numeric completion");
        ++completed_cases;
    }
}

void NewEditProviderCase() {
    Memory memory;
    memory.Parent(2, 1);
    memory.Named(memory.first, 0x760, memory.named_first, -2);
    memory.Provider(memory.second, 0x2A8);
    OwnedEditDynamicBasePriceBindings12004 bindings;
    bindings.access.context = &memory;
    bindings.access.read_memory = Read;
    bindings.access.module_base = 1;
    bindings.access.exact_12004_bound = true;
    const auto dynamic = memory.Bind();
    bindings.first = dynamic.definition_numeric;
    bindings.second = dynamic.entry_numeric;
    const auto value = ReadOwnedEditDynamicBasePrice2C6471012004(bindings,
        Memory::Address(memory.payload), Memory::Address(memory.rite), revision);
    Require(value.complete && value.base_price_raw_q64 == -200000 &&
        value.reached_occurrences.size() == 3 &&
        value.reached_occurrences[2].scalar_native_eax_raw == 2 &&
        !memory.Saw(Memory::Address(memory.rite) + 8),
        "new edit production adapter failed B0 typed output composition");
    ++completed_cases;
}
} // namespace

extern "C" __declspec(dllexport) int RunCreatePietyDynamicGroup12004(int group) noexcept {
    try {
        failure_text.fill(0);
        switch (group) {
        case 0: RunPietyPriceNamedDefinition37540B0Focus12004(); completed_cases += 4; break;
        case 1: completed_cases += RunPietyPriceNumeric31D9930DynamicNewCases12004(); break;
        case 2: VerifyPietyPriceNumeric31DF3B0DynamicOwnedCases12004(); completed_cases += 3; break;
        case 3: ParentDynamicCases(); break;
        case 4: NewGenericLeafCases(); break;
        case 5:
            Require(RunOwnedEditDynamicBasePriceFocus12004(), "14f new edit dynamic scenarios failed");
            completed_cases += 2;
            break;
        case 6: NewEditProviderCase(); break;
        default: throw std::runtime_error("unknown new dynamic fragment");
        }
        return 0;
    } catch (const std::exception& error) {
        std::snprintf(failure_text.data(), failure_text.size(), "%s", error.what());
        return 1;
    } catch (...) {
        std::snprintf(failure_text.data(), failure_text.size(), "%s", "dynamic nonstandard failure");
        return 2;
    }
}
extern "C" __declspec(dllexport) std::size_t GetCreatePietyDynamicCaseCount12004() noexcept {
    return completed_cases;
}
extern "C" __declspec(dllexport) const char* GetCreatePietyDynamicFailure12004() noexcept {
    return failure_text.data();
}
