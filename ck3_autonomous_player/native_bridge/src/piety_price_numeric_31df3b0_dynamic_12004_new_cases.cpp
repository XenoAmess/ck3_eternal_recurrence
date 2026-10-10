#include "xar_bridge/piety_price_numeric_31df3b0_dynamic_12004.hpp"

#include <cstring>
#include <map>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12004::piety_price_raw_inputs;
using xar::ck3_12004::construction_owner_mode3::RawReceiverAccessV1;

constexpr std::uintptr_t kDefinition = 0x10000;
constexpr std::uintptr_t kExpression = kDefinition + 0x2A8;
constexpr std::uintptr_t kRite = 0xFA12000000000910ULL;
constexpr std::uint64_t kRevision = 0xFEDCBA9800000011ULL;

struct CopiedFields {
  std::map<std::uintptr_t, std::vector<std::byte>> fields;
  std::size_t read_calls = 0;

  template<class T> void Put(std::uintptr_t at, T value) {
    auto &bytes = fields[at];
    bytes.resize(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
  }

  static bool Read(void *context, const void *at, void *out,
                   std::size_t size) noexcept {
    auto &self = *static_cast<CopiedFields *>(context);
    ++self.read_calls;
    const auto found = self.fields.find(reinterpret_cast<std::uintptr_t>(at));
    if (found == self.fields.end() || found->second.size() != size) return false;
    std::memcpy(out, found->second.data(), size);
    return true;
  }

  Numeric31DF3B0DynamicBindings12004 Bind() {
    return {{0, this, Read, true}, nullptr, nullptr};
  }

  RawReceiverAccessV1 Raw() {
    RawReceiverAccessV1 access;
    access.context = this;
    access.read_memory = Read;
    access.exact_12004_bound = true;
    return access;
  }

  void NonzeroModeEmptyList(std::int32_t fallback) {
    Put(kExpression + 0xB8, std::int32_t{1});
    Put(kExpression + 0xB0, std::uintptr_t{0});
    Put(kExpression + 0xA0, std::uintptr_t{0});
    Put(kExpression + 0x14, std::int32_t{0});
    Put(kExpression + 0x98, fallback);
  }
};

void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}

bool WrongRevision(void *, const PietyPriceNumericAccess12004 &,
                   std::uintptr_t, std::uintptr_t, std::uint64_t revision,
                   PietyPriceA0F0B0DynamicInputs12004 &out) noexcept {
  out.unchanged_snapshot_revision = revision ^ (std::uint64_t{1} << 63);
  return true;
}

bool MissingReachedOperands(void *, const PietyPriceNumericAccess12004 &,
                            std::uintptr_t, std::uintptr_t, std::uint64_t,
                            PietyPriceA0F0B0DynamicInputs12004 &out) noexcept {
  out.expression_identity = 0;
  out.unchanged_snapshot_revision = 0;
  return false;
}
} // namespace

// Physical ABI is void. Three scenarios; the central fresh main owns counting.
void VerifyPietyPriceNumeric31DF3B0DynamicOwnedCases12004() {
  {
    CopiedFields memory;
    memory.NonzeroModeEmptyList(std::int32_t{0});
    const auto observed = ReadPietyPriceNumeric31DF3B0Dynamic12004(
        memory.Bind(), kDefinition, kRite, kRevision);
    Require(observed.source_ready && observed.native_eax_raw == std::int32_t{0} &&
                observed.frame_key == kRevision && observed.evaluator &&
                observed.evaluator->mode_raw_i32 == std::int32_t{1} &&
                observed.evaluator->count_before_raw_i32 == std::int32_t{0} &&
                !observed.dynamic_input_copy.callback_attempted &&
                !observed.dynamic_input_copy.inputs.copied_pack.physical_pack_identity &&
                observed.dynamic_input_copy.inputs.original_named_tuple_identity ==
                    std::uintptr_t{0} && !observed.actual_original_consumed_values,
            "dynamic31df3b0 empty-list zero without invented operands");
    CopiedFields unrelated;
    auto context_binding = unrelated.Bind();
    auto actual_access = memory.Raw();
    auto output = std::int32_t{91};
    Require(ReadPietyPriceNumeric31DF3B0DynamicAdapter12004(
                &context_binding, actual_access, kDefinition, kRite, kRevision,
                output) && output == std::int32_t{0} &&
                unrelated.read_calls == std::size_t{0},
            "dynamic31df3b0 adapter reads current parent access and accepts zero");
  }
  {
    CopiedFields memory;
    auto binding = memory.Bind();
    binding.read_dynamic_inputs = WrongRevision;
    const auto observed = ReadPietyPriceNumeric31DF3B0Dynamic12004(
        binding, kDefinition, kRite, kRevision);
    Require(!observed.source_ready && !observed.evaluator &&
                observed.dynamic_input_copy.callback_returned_inputs &&
                observed.dynamic_input_copy.selected_expression_matches == true &&
                observed.dynamic_input_copy.unchanged_revision_matches == false &&
                memory.read_calls == std::size_t{0},
            "dynamic31df3b0 full revision mismatch stops before numeric reads");
    auto actual_access = memory.Raw();
    auto output = std::int32_t{-31};
    Require(!ReadPietyPriceNumeric31DF3B0DynamicAdapter12004(
                &binding, actual_access, kDefinition, kRite, kRevision, output) &&
                output == std::int32_t{-31},
            "dynamic31df3b0 mismatched resolver preserves callback output");
  }
  {
    CopiedFields memory;
    memory.NonzeroModeEmptyList(std::int32_t{137});
    memory.Put(kExpression + 0x14, std::int32_t{-1});
    auto binding = memory.Bind();
    binding.read_dynamic_inputs = MissingReachedOperands;
    const auto observed = ReadPietyPriceNumeric31DF3B0Dynamic12004(
        binding, kDefinition, kRite, kRevision);
    Require(!observed.source_ready && !observed.native_eax_raw &&
                observed.evaluator && observed.evaluator->variant_source &&
                !observed.evaluator->variant_source->source_result_ready &&
                !observed.dynamic_input_copy.callback_returned_inputs &&
                observed.dynamic_input_copy.inputs.expression_identity == kExpression &&
                observed.dynamic_input_copy.inputs.unchanged_snapshot_revision == kRevision &&
                !observed.dynamic_input_copy.inputs.copied_pack.primary_scope_identity &&
                !observed.dynamic_input_copy.inputs.copied_pack.physical_pack_identity &&
                !observed.evaluator->fallback_before_raw_i32,
            "dynamic31df3b0 missing actual scope remains unknown without fallback");
  }
}
