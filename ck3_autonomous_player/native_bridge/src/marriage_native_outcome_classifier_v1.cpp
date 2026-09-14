#include "xar_bridge/marriage_native_outcome_classifier_v1.hpp"

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

void SetFailure(MarriageNativeOutcomeClassifierStateV1 &state,
                MarriageNativeOutcomeClassifierFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

bool ReadMemory(const MarriageNativeOutcomeClassifierEnvironmentV1 &env,
                std::uintptr_t address, void *output, std::size_t size) {
  return env.read_memory != nullptr && address != 0 && output != nullptr &&
      size != 0 &&
      env.read_memory(env.memory_context, address, output, size);
}

template <typename Value>
bool ReadAt(const MarriageNativeOutcomeClassifierEnvironmentV1 &env,
            std::uintptr_t base, std::size_t offset, Value &output) {
  return base != 0 &&
      offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
      ReadMemory(env, base + offset, &output, sizeof(output));
}

MarriageNativeOutcomeClassifierFailureV1 Validate(
    const MarriageNativeOutcomeClassifierEnvironmentV1 &env) {
  if (!env.exact_build_admitted ||
      env.admitted_executable_sha256 !=
          kMarriageProposalNativeBinderExecutableSha256V1 ||
      (!env.offline_fixture && env.module_base == 0))
    return MarriageNativeOutcomeClassifierFailureV1::
        exact_build_not_admitted;
  if (env.read_memory == nullptr)
    return MarriageNativeOutcomeClassifierFailureV1::
        memory_reader_unavailable;
  if (env.read_boolean_option == nullptr ||
      env.grand_wedding_option_id_slot == 0 ||
      env.adult_threshold_zero_slot == 0 ||
      env.adult_threshold_one_slot == 0)
    return MarriageNativeOutcomeClassifierFailureV1::binding_mismatch;
  if (!env.offline_fixture) {
    ReadMarriageBooleanOptionV1 expected_reader = nullptr;
    std::uintptr_t expected_option = 0;
    std::uintptr_t expected_zero = 0;
    std::uintptr_t expected_one = 0;
    if (!AddRva(env.module_base, kMarriageReadBooleanOptionRvaV1,
                expected_reader) ||
        !AddRva(env.module_base, kMarriageGrandWeddingOptionIdSlotRvaV1,
                expected_option) ||
        !AddRva(env.module_base, kMarriageAdultThresholdZeroSlotRvaV1,
                expected_zero) ||
        !AddRva(env.module_base, kMarriageAdultThresholdOneSlotRvaV1,
                expected_one) ||
        env.read_boolean_option != expected_reader ||
        env.grand_wedding_option_id_slot != expected_option ||
        env.adult_threshold_zero_slot != expected_zero ||
        env.adult_threshold_one_slot != expected_one)
      return MarriageNativeOutcomeClassifierFailureV1::binding_mismatch;
    struct Prefix {
      std::uintptr_t rva;
      std::array<std::uint8_t, 16> bytes;
    };
    constexpr std::array<Prefix, 2> prefixes{{
        {kMarriageReadBooleanOptionRvaV1,
         {0x4C, 0x8B, 0x09, 0x33, 0xC0, 0x4C, 0x8B, 0xD9,
          0x45, 0x8B, 0x91, 0x54, 0x25, 0x00, 0x00, 0x45}},
        {kMarriageOutcomeDispatchRvaV1,
         {0x40, 0x53, 0x56, 0x57, 0x48, 0x83, 0xEC, 0x60,
          0x48, 0x8B, 0xF2, 0x4C, 0x89, 0xB4, 0x24, 0x80}},
    }};
    for (const auto &prefix : prefixes) {
      std::array<std::uint8_t, 16> actual{};
      if (!ReadMemory(env, env.module_base + prefix.rva, actual.data(),
                      actual.size()) ||
          actual != prefix.bytes)
        return MarriageNativeOutcomeClassifierFailureV1::signature_mismatch;
    }
  }
  return MarriageNativeOutcomeClassifierFailureV1::none;
}

struct OutcomeSampleV1 {
  std::uint32_t subject_context_id = 0;
  std::uint32_t candidate_context_id = 0;
  std::uint32_t subject_object_id = 0;
  std::uint32_t candidate_object_id = 0;
  std::uint8_t subject_selector = 0;
  std::uint8_t candidate_selector = 0;
  std::int16_t subject_adult_measure = 0;
  std::int16_t candidate_adult_measure = 0;
  std::int32_t adult_threshold_zero = 0;
  std::int32_t adult_threshold_one = 0;
  std::uint32_t grand_wedding_option_id = 0;
  bool grand_wedding = false;

  friend bool operator==(const OutcomeSampleV1 &, const OutcomeSampleV1 &) =
      default;
};

MarriageNativeOutcomeClassifierFailureV1 ReadSample(
    const MarriageNativeOutcomeClassifierEnvironmentV1 &env,
    std::uintptr_t subject, std::uintptr_t candidate,
    std::uintptr_t context, OutcomeSampleV1 &output) {
  output = {};
  if (!ReadAt(env, context, kMarriageContextSecondaryActorIdOffsetV1,
              output.subject_context_id) ||
      !ReadAt(env, context, kMarriageContextSecondaryRecipientIdOffsetV1,
              output.candidate_context_id) ||
      !ReadAt(env, subject, kMarriageCharacterIdOffsetV1,
              output.subject_object_id) ||
      !ReadAt(env, candidate, kMarriageCharacterIdOffsetV1,
              output.candidate_object_id) ||
      output.subject_context_id != output.subject_object_id ||
      output.candidate_context_id != output.candidate_object_id)
    return MarriageNativeOutcomeClassifierFailureV1::
        secondary_pair_identity_mismatch;
  if (!ReadAt(env, subject, kMarriageCharacterAdultSelectorOffsetV1,
              output.subject_selector) ||
      !ReadAt(env, candidate, kMarriageCharacterAdultSelectorOffsetV1,
              output.candidate_selector) ||
      !ReadAt(env, subject, kMarriageCharacterAdultMeasureOffsetV1,
              output.subject_adult_measure) ||
      !ReadAt(env, candidate, kMarriageCharacterAdultMeasureOffsetV1,
              output.candidate_adult_measure) ||
      !ReadMemory(env, env.adult_threshold_zero_slot,
                  &output.adult_threshold_zero,
                  sizeof(output.adult_threshold_zero)) ||
      !ReadMemory(env, env.adult_threshold_one_slot,
                  &output.adult_threshold_one,
                  sizeof(output.adult_threshold_one)))
    return MarriageNativeOutcomeClassifierFailureV1::
        runtime_threshold_unavailable;
  if (!ReadMemory(env, env.grand_wedding_option_id_slot,
                  &output.grand_wedding_option_id,
                  sizeof(output.grand_wedding_option_id)))
    return MarriageNativeOutcomeClassifierFailureV1::
        option_identifier_unavailable;
  output.grand_wedding = env.read_boolean_option(
      reinterpret_cast<void *>(context), output.grand_wedding_option_id);
  return MarriageNativeOutcomeClassifierFailureV1::none;
}

} // namespace

MarriageNativeOutcomeClassifierEnvironmentV1
BindMarriageNativeOutcomeClassifierEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  MarriageNativeOutcomeClassifierEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  const bool complete =
      AddRva(module_base, kMarriageReadBooleanOptionRvaV1,
             output.read_boolean_option) &&
      AddRva(module_base, kMarriageGrandWeddingOptionIdSlotRvaV1,
             output.grand_wedding_option_id_slot) &&
      AddRva(module_base, kMarriageAdultThresholdZeroSlotRvaV1,
             output.adult_threshold_zero_slot) &&
      AddRva(module_base, kMarriageAdultThresholdOneSlotRvaV1,
             output.adult_threshold_one_slot);
  if (!complete) {
    output.read_boolean_option = nullptr;
    output.grand_wedding_option_id_slot = 0;
    output.adult_threshold_zero_slot = 0;
    output.adult_threshold_one_slot = 0;
  }
  return output;
}

bool ConfigureMarriageNativeOutcomeClassifierV1(
    MarriageNativeOutcomeClassifierStateV1 &classifier,
    MarriageProposalNativeBinderStateV1 &binder) noexcept {
  const auto failure = Validate(classifier.environment);
  if (failure != MarriageNativeOutcomeClassifierFailureV1::none) {
    SetFailure(classifier, failure);
    return false;
  }
  binder.environment.source_adapter.outcome_context = &classifier;
  binder.environment.source_adapter.classify_outcome =
      &ClassifyMarriageNativeOutcomeExactV1;
  binder.environment.outcome_classifier_certified = true;
  SetFailure(classifier, MarriageNativeOutcomeClassifierFailureV1::none);
  return true;
}

bool ClassifyMarriageNativeOutcomeExactV1(
    void *context, std::uintptr_t subject_character,
    std::uintptr_t candidate_character, const void *finalized_context,
    MarriagePredictedOutcomeV1 &output) noexcept {
  output = MarriagePredictedOutcomeV1::unavailable;
  if (context == nullptr) return false;
  auto &state = *static_cast<MarriageNativeOutcomeClassifierStateV1 *>(context);
  const auto failure = Validate(state.environment);
  if (failure != MarriageNativeOutcomeClassifierFailureV1::none) {
    SetFailure(state, failure);
    return false;
  }
  if (subject_character == 0 || candidate_character == 0 ||
      finalized_context == nullptr || subject_character == candidate_character) {
    SetFailure(state, MarriageNativeOutcomeClassifierFailureV1::invalid_input);
    return false;
  }
  OutcomeSampleV1 first{};
  auto sample_failure = ReadSample(
      state.environment, subject_character, candidate_character,
      reinterpret_cast<std::uintptr_t>(finalized_context), first);
  if (sample_failure != MarriageNativeOutcomeClassifierFailureV1::none) {
    SetFailure(state, sample_failure);
    return false;
  }
  OutcomeSampleV1 second{};
  sample_failure = ReadSample(
      state.environment, subject_character, candidate_character,
      reinterpret_cast<std::uintptr_t>(finalized_context), second);
  if (sample_failure != MarriageNativeOutcomeClassifierFailureV1::none ||
      second != first) {
    SetFailure(state,
               sample_failure == MarriageNativeOutcomeClassifierFailureV1::none
                   ? MarriageNativeOutcomeClassifierFailureV1::
                         outcome_sample_drift
                   : sample_failure);
    return false;
  }
  const auto subject_threshold = second.subject_selector == 0
      ? second.adult_threshold_zero
      : second.adult_threshold_one;
  const auto candidate_threshold = second.candidate_selector == 0
      ? second.adult_threshold_zero
      : second.adult_threshold_one;
  const bool both_adult =
      second.subject_adult_measure >= subject_threshold &&
      second.candidate_adult_measure >= candidate_threshold;
  output = both_adult && !second.grand_wedding
      ? MarriagePredictedOutcomeV1::marriage
      : MarriagePredictedOutcomeV1::betrothal;
  SetFailure(state, MarriageNativeOutcomeClassifierFailureV1::none);
  return true;
}

MarriageNativeOutcomeClassifierFailureV1
ReadMarriageNativeOutcomeClassifierFailureV1(
    const MarriageNativeOutcomeClassifierStateV1 &classifier) noexcept {
  return static_cast<MarriageNativeOutcomeClassifierFailureV1>(
      classifier.last_failure.load(std::memory_order_acquire));
}

} // namespace xar::bridge
