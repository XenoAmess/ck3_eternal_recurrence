#pragma once
#include "xar_bridge/ck3_12003_prisoner_release_preview.hpp"

namespace xar::ck3_12003 {
using PrisonerKinshipPredicate12003 = bool (*)(void *, void *);
using PrisonerNativeKinshipAccess12003 = PrisonerReleasePreviewAccess12003;
struct PrisonerNativeKinshipBindings12003 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  PrisonerKinshipPredicate12003 close_family = nullptr;
  PrisonerKinshipPredicate12003 close_or_extended_family = nullptr;
};
struct PrisonerNativeKinship12003 {
  bool available = false;
  std::string unavailable_reason = "not_evaluated";
  bridge::PlayerPrisonerFrameV1 frame{};
  std::uint32_t source_ordinal = 0;
  std::uint32_t jailer_character_id = 0;
  std::uint32_t prisoner_character_id = 0;
  bool is_close_family_of_played_character = false;
  bool is_close_or_extended_family_of_played_character = false;
};
PrisonerNativeKinshipBindings12003 BindPrisonerNativeKinship12003(
    std::uintptr_t module_base, std::string_view actual_executable_sha256) noexcept;
bool ReadPrisonerNativeKinship12003(
    const PrisonerNativeKinshipBindings12003 &,
    const PrisonerNativeKinshipAccess12003 &, std::uint32_t jailer,
    std::uint32_t prisoner, std::uint32_t source_ordinal,
    PrisonerNativeKinship12003 &) noexcept;
std::string SerializePrisonerNativeKinship12003(const PrisonerNativeKinship12003 &);
} // namespace xar::ck3_12003
