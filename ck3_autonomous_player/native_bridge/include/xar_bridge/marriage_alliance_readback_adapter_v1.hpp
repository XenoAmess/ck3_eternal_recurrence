#pragma once

#include "xar_bridge/marriage_proposal_native_binder_v1.hpp"

#include <atomic>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kMarriageAllianceReadbackPrivateKeyV1 =
    "marriage_alliance_readback_adapter_v1";
inline constexpr std::uintptr_t kMarriageCharacterIsAlliedToRvaV1 =
    0x2661E00;
inline constexpr std::uintptr_t kMarriageIsAlliedToTriggerEvaluatorRvaV1 =
    0x2886B90;
inline constexpr std::uintptr_t kMarriageAllianceProjectionConsumerRvaV1 =
    0x2283470;

using MarriageCharacterIsAlliedToV1 = bool (*)(const void *subject,
                                                const void *target);

enum class MarriageAllianceReadbackFailureV1 : std::uint32_t {
  none = 0,
  exact_build_not_admitted,
  binding_mismatch,
  signature_mismatch,
  memory_reader_unavailable,
  invalid_input,
};

struct MarriageAllianceReadbackEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  void *memory_context = nullptr;
  MarriageSourceAdapterMemoryReadV1 read_memory = nullptr;
  MarriageCharacterIsAlliedToV1 is_allied_to = nullptr;
};

struct MarriageAllianceReadbackStateV1 {
  MarriageAllianceReadbackEnvironmentV1 environment{};
  std::atomic<std::uint32_t> last_failure{static_cast<std::uint32_t>(
      MarriageAllianceReadbackFailureV1::none)};
};

MarriageAllianceReadbackEnvironmentV1 BindMarriageAllianceReadbackEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

bool ConfigureMarriageAllianceReadbackV1(
    MarriageAllianceReadbackStateV1 &adapter,
    MarriageProposalNativeBinderStateV1 &binder) noexcept;

bool ReadMarriageAlliancePairExactV1(
    void *context, std::uintptr_t subject_character,
    std::uintptr_t candidate_character, bool &subject_has_candidate,
    bool &candidate_has_subject) noexcept;

MarriageAllianceReadbackFailureV1 ReadMarriageAllianceReadbackFailureV1(
    const MarriageAllianceReadbackStateV1 &adapter) noexcept;

} // namespace xar::bridge
