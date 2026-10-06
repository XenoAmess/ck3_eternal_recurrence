#pragma once

#include "xar_bridge/ck3_12003_prisoner_release_preview.hpp"

namespace xar::ck3_12003 {

inline constexpr std::uint32_t kPrisonerReleaseAllOptionMask12003 =
    (std::uint32_t{1} << kPrisonerReleaseOptionKeys12003.size()) - 1;

// Source-only candidate. The common observation carries identity/frame/costs;
// it is never serialized through the unconditional-release serializer.
struct PrisonerNegotiatedPreview12003 {
  PrisonerReleasePreview12003 observation{};
  std::uint32_t requested_option_mask_bits = 0;
  bool recipient_answer_available = false;
  std::int64_t recipient_acceptance_score_raw = 0;
  std::uint8_t recipient_answer_status_raw = 3;
};

struct PrisonerNegotiatedBindings12003 {
  PrisonerReleasePreviewBindings12003 release{};
  void (*select_local_option)(void *, std::int32_t) = nullptr;
  ck3_11906::EvaluateCharacterInteractionAnswer evaluate_answer = nullptr;
};

PrisonerNegotiatedBindings12003 BindPrisonerNegotiatedPreview12003(
    std::uintptr_t module_base, std::string_view actual_executable_sha256) noexcept;

// An explicit nonempty subset of the current thirteen authored flags.
// Native refresh/finalize may change a requested combination. Such a result
// keeps its observed mask but has no option-bound acceptance qualification.
bool ReadPrisonerNegotiatedPreview12003(
    const PrisonerNegotiatedBindings12003 &,
    const PrisonerReleasePreviewAccess12003 &,
    std::uint32_t jailer_character_id, std::uint32_t prisoner_character_id,
    std::uint32_t requested_option_mask_bits,
    PrisonerNegotiatedPreview12003 &) noexcept;

std::string SerializePrisonerNegotiatedPreview12003(
    const PrisonerNegotiatedPreview12003 &);

} // namespace xar::ck3_12003
