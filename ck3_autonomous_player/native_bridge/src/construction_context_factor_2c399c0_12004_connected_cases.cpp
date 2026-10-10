#include "xar_bridge/construction_context_factor_2c399c0_12004.hpp"

#include <stdexcept>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
void Require(bool condition, const char *case_name) {
  if (!condition) throw std::runtime_error(case_name);
}
struct OwnedMemory {
  static constexpr std::uintptr_t context = 0x2000;
  static constexpr std::uintptr_t image = 0x180000000;
  std::uintptr_t object = 0x3000;
  std::int64_t loaded = 50000;
  std::uint32_t object_reads = 0, global_reads = 0;
  bool deny_global = false, change_object = false, change_global = false;
  static bool Read(void *opaque, const void *address, void *output, std::size_t size) {
    auto &memory = *static_cast<OwnedMemory *>(opaque);
    const auto numeric = reinterpret_cast<std::uintptr_t>(address);
    if (numeric == context + 0x848 && size == sizeof(std::uintptr_t)) {
      ++memory.object_reads;
      const auto value = memory.change_object && memory.object_reads > 1
          ? memory.object + 8 : memory.object;
      std::memcpy(output, &value, size);
      return true;
    }
    if (numeric == image + kContextFactorLoadedSlotRvaV1 && size == sizeof(std::int64_t)) {
      ++memory.global_reads;
      if (memory.deny_global) return false;
      const auto value = memory.change_global && memory.global_reads > 1
          ? memory.loaded + 1 : memory.loaded;
      std::memcpy(output, &value, size);
      return true;
    }
    return false;
  }
  LoadedInputAccessV1 Access() { return {this, &Read, true}; }
};
LoadedContextFactor2C399C0InputsV1 Copied(std::int64_t loaded) {
  LoadedContextFactor2C399C0InputsV1 inputs{};
  inputs.source_ready = true;
  inputs.frame_key = 72;
  inputs.context_pointer = OwnedMemory::context;
  inputs.context_object = 0x3000;
  inputs.image_base = OwnedMemory::image;
  inputs.loaded_slot_address = OwnedMemory::image + kContextFactorLoadedSlotRvaV1;
  inputs.loaded_qword_raw = loaded;
  return inputs;
}
ContextFactorProviderFirstQwordV1 Provider(std::int64_t first) {
  return {true, kContextFactor2C399C0SourcePinV1, 72, 0x3000, first};
}
} // namespace

// Fresh owned source-copy cases only.03/10 invokes this once in its new
// connected construction compound; this file has no standalone entry point.
void VerifyContextFactor2C399C0ConnectedCasesV1() {
  {
    OwnedMemory memory{};
    const auto inputs = ReadContextFactor2C399C0InputsV1(
        memory.Access(), OwnedMemory::image, OwnedMemory::context, 72);
    const auto result = EvaluateContextFactor2C399C0V1(inputs, Provider(5000000));
    Require(inputs.source_ready && inputs.loaded_qword_raw == 50000 &&
            inputs.context_object == 0x3000 && memory.object_reads == 2 &&
            memory.global_reads == 2 && result.observed &&
            result.difference_100000_raw == 50000 &&
            result.first_scaled_raw == 2500000 &&
            result.second_scale->result_raw == 25000 && result.factor_qword_raw == 75000,
            "same-frame copied child plus independently guarded actual slot");
  }
  {
    const auto result = EvaluateContextFactor2C399C0V1(Copied(0), Provider(10000000));
    Require(result.observed && result.first_scale_path == "native_fast64" &&
            result.second_scale->path == "native_fast64" &&
            result.factor_qword_raw == 100000,
            "native fast scales retain100000 and10000000 denominators");
  }
  {
    const auto result = EvaluateContextFactor2C399C0V1(Copied(200000), Provider(10000000));
    Require(result.difference_100000_raw == -100000 &&
            result.first_scaled_raw == -10000000 &&
            result.second_scale->result_raw == -100000 &&
            result.factor_qword_raw == 100000,
            "negative difference is arithmetic input without an eligibility gate");
  }
  {
    const auto result = EvaluateContextFactor2C399C0V1(Copied(50000), Provider(0));
    Require(result.observed && result.first_scaled_raw == 0 &&
            result.factor_qword_raw == 50000,
            "known zero provider contributes loaded raw value without early rejection");
  }
  {
    const auto result = EvaluateContextFactor2C399C0V1(Copied(0), Provider(-1));
    Require(result.first_scaled_raw == -1 && result.second_scale->fast_product_raw == -100000 &&
            result.second_scale->result_raw == 0 && result.factor_qword_raw == 0,
            "negative fractional scale truncates toward zero");
  }
  {
    const auto result = EvaluateContextFactor2C399C0V1(Copied(0), Provider(INT64_MAX));
    const auto &trace = *result.second_scale;
    Require(result.first_scale_path == "native_minmax_wrap64" &&
            result.first_scaled_raw == INT64_MAX && trace.path == "native_decomposed64" &&
            trace.quotient_100000_raw == INT64_C(92233720368547) &&
            trace.whole_product_raw == INT64_C(9223372036854700000) &&
            trace.remainder_100000_raw == 75807 &&
            trace.whole_quotient_10000000_raw == INT64_C(922337203685) &&
            trace.whole_remainder_10000000_raw == 4700000 &&
            trace.fractional_product_raw == INT64_C(7580700000) &&
            trace.fractional_quotient_raw == 758 &&
            trace.whole_remainder_quotient_raw == 47000 &&
            result.factor_qword_raw == INT64_C(92233720368547758),
            "positive signed maximum preserves every slow decomposition component");
  }
  {
    const auto result = EvaluateContextFactor2C399C0V1(Copied(0), Provider(INT64_MIN));
    Require(result.first_scaled_raw == INT64_MIN &&
            result.second_scale->path == "native_decomposed64" &&
            result.second_scale->remainder_100000_raw == -75808 &&
            result.factor_qword_raw == -INT64_C(92233720368547758),
            "signed minimum uses negative slow remainders without signed overflow");
  }
  {
    const auto result = EvaluateContextFactor2C399C0V1(Copied(INT64_MIN), Provider(100000));
    Require(result.difference_100000_raw == -INT64_C(9223372036854675808) &&
            result.first_scaled_raw == -INT64_C(9223372036854675808) &&
            result.factor_qword_raw == INT64_C(9131138316486229050),
            "difference and finaladd retain native low64 wrap");
  }
  {
    const auto result = EvaluateContextFactor2C399C0V1(
        Copied(-INT64_C(9223372036854675806)), Provider(INT64_MAX));
    Require(result.first_scaled_raw == INT64_C(9223279803134407260) &&
            result.second_scale->result_raw == INT64_C(92232798031344072) &&
            result.factor_qword_raw == -INT64_C(9131139238823331734),
            "wrapped first slow products are retained before second scale");
  }
  {
    const auto fast = EvaluateContextFactor2C399C0V1(
        Copied(0), Provider(INT64_C(92233720368547)));
    const auto slow = EvaluateContextFactor2C399C0V1(
        Copied(0), Provider(INT64_C(92233720368548)));
    Require(fast.second_scale->path == "native_fast64" &&
            slow.second_scale->path == "native_decomposed64" &&
            fast.factor_qword_raw == INT64_C(922337203685) &&
            slow.factor_qword_raw == fast.factor_qword_raw,
            "second native unsigned range boundary keeps distinct paths");
  }
  {
    auto provider = Provider(0);
    provider.first_qword_raw.reset();
    const auto result = EvaluateContextFactor2C399C0V1(Copied(100000), provider);
    Require(!result.observed && !result.factor_qword_raw &&
            result.failure == ContextFactor2C399C0FailureV1::provider_unavailable,
            "zero difference still requires originally called child input");
  }
  {
    auto provider = Provider(5000000);
    provider.frame_key = 73;
    const auto result = EvaluateContextFactor2C399C0V1(Copied(50000), provider);
    Require(!result.observed && result.loaded_qword_raw == 50000 &&
            result.failure == ContextFactor2C399C0FailureV1::provider_binding,
            "different snapshotrevision does not compose child facts");
  }
  {
    auto provider = Provider(5000000);
    provider.context_object = 0x3008;
    const auto result = EvaluateContextFactor2C399C0V1(Copied(50000), provider);
    Require(!result.observed &&
            result.failure == ContextFactor2C399C0FailureV1::provider_binding,
            "different context848 object does not compose child facts");
  }
  {
    auto provider = Provider(5000000);
    provider.source_pin = "old build";
    const auto result = EvaluateContextFactor2C399C0V1(Copied(50000), provider);
    Require(!result.observed &&
            result.failure == ContextFactor2C399C0FailureV1::provider_source_pin,
            "exact child executable pin is required");
  }
  {
    OwnedMemory memory{};
    memory.deny_global = true;
    const auto inputs = ReadContextFactor2C399C0InputsV1(
        memory.Access(), OwnedMemory::image, OwnedMemory::context, 72);
    Require(!inputs.source_ready && !inputs.loaded_qword_raw &&
            inputs.failure == ContextFactor2C399C0FailureV1::global_read,
            "unread actual loaded qword remains unavailable rather than zero");
  }
  {
    OwnedMemory memory{};
    memory.change_object = true;
    const auto inputs = ReadContextFactor2C399C0InputsV1(
        memory.Access(), OwnedMemory::image, OwnedMemory::context, 72);
    Require(!inputs.source_ready &&
            inputs.failure == ContextFactor2C399C0FailureV1::source_changed,
            "context848 bookend change withholds source readiness");
  }
  {
    OwnedMemory memory{};
    memory.change_global = true;
    const auto inputs = ReadContextFactor2C399C0InputsV1(
        memory.Access(), OwnedMemory::image, OwnedMemory::context, 72);
    Require(!inputs.source_ready && inputs.loaded_qword_raw == 50000 &&
            inputs.failure == ContextFactor2C399C0FailureV1::source_changed,
            "loadedglobal bookend change preserves raw diagnostic and withholds composition");
  }
  {
    OwnedMemory memory{};
    auto access = memory.Access();
    access.exact_12004_bound = false;
    const auto inputs = ReadContextFactor2C399C0InputsV1(
        access, OwnedMemory::image, OwnedMemory::context, 72);
    Require(!inputs.source_ready && memory.object_reads == 0 && memory.global_reads == 0 &&
            inputs.failure == ContextFactor2C399C0FailureV1::exact_build,
            "exact source admission precedes readonly memory copies");
  }
}
} // namespace xar::ck3_12004::construction_owner_mode3
