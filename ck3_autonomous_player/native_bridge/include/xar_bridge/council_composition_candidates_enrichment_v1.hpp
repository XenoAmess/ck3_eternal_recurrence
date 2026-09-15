#pragma once

#include "xar_bridge/council_composition_candidates_public_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::game {

enum class CouncilCompositionCandidatesEnrichmentFailureV1 : std::uint32_t {
  none = 0,
  invalid_private_result,
  exact_build_not_admitted,
  native_bindings_unavailable,
  application_main_thread_required,
  frame_capture_failed,
  same_frame_binding_mismatch,
  incumbent_unreadable,
  incumbent_generation_mismatch,
  incumbent_main_skill_unreadable,
  candidate_generation_mismatch,
  candidate_main_skill_unreadable,
  frame_drift,
};

enum class ReadCouncilCompositionCandidatesEnrichmentResultV1
    : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kCouncilCompositionCandidatesEnrichmentPrivateKeyV1 =
        "g2_council_composition_candidates_enrichment_v1";
inline constexpr std::string_view
    kCouncilCompositionCandidatesEnrichmentGameVersionV1 = "1.19.0.6";
inline constexpr std::string_view
    kCouncilCompositionCandidatesEnrichmentExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::size_t
    kCouncilCompositionActiveTaskIncumbentIdOffsetV1 = 0x38;
inline constexpr std::size_t kCouncilCompositionCharacterIdentityOffsetV1 =
    0x18;
inline constexpr std::size_t
    kCouncilCompositionCharacterStewardshipOffsetV1 = 0xDC;

using CouncilCompositionCandidatesEnrichmentReadMemoryV1 = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;
using CouncilCompositionCandidatesEnrichmentResolveCharacterV1 = bool (*)(
    void *context, std::int32_t full_character_id,
    std::uintptr_t &character) noexcept;

struct CouncilCompositionCandidatesEnrichmentEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
};

struct CouncilCompositionCandidatesEnrichmentAccessV1 {
  void *context = nullptr;
  CaptureCouncilCompositionStewardCandidatesFrameV1 capture_frame = nullptr;
  IsCouncilCompositionStewardCandidatesMainThreadV1 is_main_thread = nullptr;
  CouncilCompositionCandidatesEnrichmentReadMemoryV1 read_memory = nullptr;
  CouncilCompositionCandidatesEnrichmentResolveCharacterV1 resolve_character =
      nullptr;
};

game::ReadCouncilCompositionCandidatesEnrichmentResultV1
ReadCouncilCompositionCandidatesEnrichmentV1(
    const CouncilCompositionCandidatesEnrichmentEnvironmentV1 &environment,
    const CouncilCompositionCandidatesEnrichmentAccessV1 &access,
    const game::CouncilCompositionStewardCandidatesV1 &private_result,
    CouncilCompositionCandidatesPublicEnrichmentV1 &output,
    game::CouncilCompositionCandidatesEnrichmentFailureV1 &failure) noexcept;

std::string_view CouncilCompositionCandidatesEnrichmentFailureKeyV1(
    game::CouncilCompositionCandidatesEnrichmentFailureV1 failure) noexcept;

} // namespace xar::ck3_11906
