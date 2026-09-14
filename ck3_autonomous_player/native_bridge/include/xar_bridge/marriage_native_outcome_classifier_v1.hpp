#pragma once

#include "xar_bridge/marriage_proposal_native_binder_v1.hpp"

#include <atomic>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kMarriageNativeOutcomeClassifierPrivateKeyV1 =
    "marriage_native_outcome_classifier_v1";
inline constexpr std::uintptr_t kMarriageReadBooleanOptionRvaV1 = 0x2C40770;
inline constexpr std::uintptr_t kMarriageGrandWeddingOptionIdSlotRvaV1 =
    0x57EB964;
inline constexpr std::uintptr_t kMarriageAdultThresholdZeroSlotRvaV1 =
    0x570E1D8;
inline constexpr std::uintptr_t kMarriageAdultThresholdOneSlotRvaV1 =
    0x570F0E4;
inline constexpr std::size_t kMarriageCharacterAdultMeasureOffsetV1 = 0x68;
inline constexpr std::size_t kMarriageCharacterAdultSelectorOffsetV1 = 0x199;

using ReadMarriageBooleanOptionV1 = bool (*)(void *context,
                                             std::uint32_t option_id);

enum class MarriageNativeOutcomeClassifierFailureV1 : std::uint32_t {
  none = 0,
  exact_build_not_admitted,
  binding_mismatch,
  signature_mismatch,
  memory_reader_unavailable,
  invalid_input,
  secondary_pair_identity_mismatch,
  runtime_threshold_unavailable,
  option_identifier_unavailable,
  outcome_sample_drift,
};

struct MarriageNativeOutcomeClassifierEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  void *memory_context = nullptr;
  MarriageSourceAdapterMemoryReadV1 read_memory = nullptr;
  ReadMarriageBooleanOptionV1 read_boolean_option = nullptr;
  std::uintptr_t grand_wedding_option_id_slot = 0;
  std::uintptr_t adult_threshold_zero_slot = 0;
  std::uintptr_t adult_threshold_one_slot = 0;
};

struct MarriageNativeOutcomeClassifierStateV1 {
  MarriageNativeOutcomeClassifierEnvironmentV1 environment{};
  std::atomic<std::uint32_t> last_failure{static_cast<std::uint32_t>(
      MarriageNativeOutcomeClassifierFailureV1::none)};
};

MarriageNativeOutcomeClassifierEnvironmentV1
BindMarriageNativeOutcomeClassifierEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

bool ConfigureMarriageNativeOutcomeClassifierV1(
    MarriageNativeOutcomeClassifierStateV1 &classifier,
    MarriageProposalNativeBinderStateV1 &binder) noexcept;

bool ClassifyMarriageNativeOutcomeExactV1(
    void *context, std::uintptr_t subject_character,
    std::uintptr_t candidate_character, const void *finalized_context,
    MarriagePredictedOutcomeV1 &output) noexcept;

MarriageNativeOutcomeClassifierFailureV1
ReadMarriageNativeOutcomeClassifierFailureV1(
    const MarriageNativeOutcomeClassifierStateV1 &classifier) noexcept;

} // namespace xar::bridge
