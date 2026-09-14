#include "xar_bridge/marriage_alliance_readback_adapter_v1.hpp"

#include <array>
#include <limits>
#include <type_traits>

namespace xar::bridge {
namespace {

template <typename Value>
bool AddRva(std::uintptr_t base, std::uintptr_t rva, Value &output) noexcept {
  if (base == 0 || rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = {};
    return false;
  }
  if constexpr (std::is_pointer_v<Value>) {
    output = reinterpret_cast<Value>(base + rva);
  } else {
    output = static_cast<Value>(base + rva);
  }
  return true;
}

void SetFailure(MarriageAllianceReadbackStateV1 &state,
                MarriageAllianceReadbackFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

bool ReadMemory(const MarriageAllianceReadbackEnvironmentV1 &env,
                std::uintptr_t address, void *output, std::size_t size) {
  return env.read_memory != nullptr && address != 0 && output != nullptr &&
      size != 0 && env.read_memory(env.memory_context, address, output, size);
}

MarriageAllianceReadbackFailureV1 Validate(
    const MarriageAllianceReadbackEnvironmentV1 &env) {
  if (!env.exact_build_admitted ||
      env.admitted_executable_sha256 !=
          kMarriageProposalNativeBinderExecutableSha256V1 ||
      (!env.offline_fixture && env.module_base == 0))
    return MarriageAllianceReadbackFailureV1::exact_build_not_admitted;
  if (env.read_memory == nullptr)
    return MarriageAllianceReadbackFailureV1::memory_reader_unavailable;
  if (env.is_allied_to == nullptr)
    return MarriageAllianceReadbackFailureV1::binding_mismatch;
  if (env.offline_fixture) return MarriageAllianceReadbackFailureV1::none;
  MarriageCharacterIsAlliedToV1 expected = nullptr;
  if (!AddRva(env.module_base, kMarriageCharacterIsAlliedToRvaV1, expected) ||
      env.is_allied_to != expected)
    return MarriageAllianceReadbackFailureV1::binding_mismatch;
  struct Prefix {
    std::uintptr_t rva;
    std::array<std::uint8_t, 16> bytes;
  };
  constexpr std::array<Prefix, 3> prefixes{{
      {kMarriageCharacterIsAlliedToRvaV1,
       {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74,
        0x24, 0x18, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x48}},
      {kMarriageIsAlliedToTriggerEvaluatorRvaV1,
       {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
        0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x57}},
      {kMarriageAllianceProjectionConsumerRvaV1,
       {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
        0x24, 0x10, 0x48, 0x89, 0x7C, 0x24, 0x20, 0x4C}},
  }};
  for (const auto &prefix : prefixes) {
    std::array<std::uint8_t, 16> actual{};
    if (!ReadMemory(env, env.module_base + prefix.rva, actual.data(),
                    actual.size()) ||
        actual != prefix.bytes)
      return MarriageAllianceReadbackFailureV1::signature_mismatch;
  }
  return MarriageAllianceReadbackFailureV1::none;
}

} // namespace

MarriageAllianceReadbackEnvironmentV1 BindMarriageAllianceReadbackEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  MarriageAllianceReadbackEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  AddRva(module_base, kMarriageCharacterIsAlliedToRvaV1,
         output.is_allied_to);
  return output;
}

bool ConfigureMarriageAllianceReadbackV1(
    MarriageAllianceReadbackStateV1 &adapter,
    MarriageProposalNativeBinderStateV1 &binder) noexcept {
  const auto failure = Validate(adapter.environment);
  if (failure != MarriageAllianceReadbackFailureV1::none) {
    SetFailure(adapter, failure);
    return false;
  }
  binder.environment.alliance_context = &adapter;
  binder.environment.read_alliance_pair = &ReadMarriageAlliancePairExactV1;
  binder.environment.alliance_readback_certified = true;
  SetFailure(adapter, MarriageAllianceReadbackFailureV1::none);
  return true;
}

bool ReadMarriageAlliancePairExactV1(
    void *context, std::uintptr_t subject_character,
    std::uintptr_t candidate_character, bool &subject_has_candidate,
    bool &candidate_has_subject) noexcept {
  subject_has_candidate = false;
  candidate_has_subject = false;
  if (context == nullptr) return false;
  auto &state = *static_cast<MarriageAllianceReadbackStateV1 *>(context);
  auto failure = Validate(state.environment);
  if (failure == MarriageAllianceReadbackFailureV1::none &&
      (subject_character == 0 || candidate_character == 0 ||
       subject_character == candidate_character))
    failure = MarriageAllianceReadbackFailureV1::invalid_input;
  if (failure != MarriageAllianceReadbackFailureV1::none) {
    SetFailure(state, failure);
    return false;
  }
  const auto &env = state.environment;
  subject_has_candidate = env.is_allied_to(
      reinterpret_cast<const void *>(subject_character),
      reinterpret_cast<const void *>(candidate_character));
  candidate_has_subject = env.is_allied_to(
      reinterpret_cast<const void *>(candidate_character),
      reinterpret_cast<const void *>(subject_character));
  SetFailure(state, MarriageAllianceReadbackFailureV1::none);
  return true;
}

MarriageAllianceReadbackFailureV1 ReadMarriageAllianceReadbackFailureV1(
    const MarriageAllianceReadbackStateV1 &adapter) noexcept {
  return static_cast<MarriageAllianceReadbackFailureV1>(
      adapter.last_failure.load(std::memory_order_acquire));
}

} // namespace xar::bridge
