#pragma once

#include "xar_bridge/ck3_12004_prisoner_negotiated_preview.hpp"
#include "xar_bridge/ck3_12004_prisoner_ransom_action.hpp"

namespace xar::ck3_12004 {

// Reuse the existing disposition ACK enum: quote_changed means observed
// release terms changed. A submitted value still has no material outcome.
using PrisonerReleaseSubmit12004 = PlayerPrisonerRansomSubmitV1;

struct PrisonerReleaseActionBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  PrisonerNegotiatedBindings12004 preview{};
  ck3_12002::CommandBindings commands{};
  ck3_12002::MarriageConstructSendInteractionCommand construct_send = nullptr;
  std::uintptr_t primary_vtable = 0;
  std::uintptr_t secondary_vtable = 0;
};

PrisonerReleaseActionBindings12004 BindPrisonerReleaseAction12004(
    std::uintptr_t module_base,
    std::string_view actual_executable_sha256) noexcept;

// Owning-thread action. All-off and nonzero selected terms share the same
// typed context/copy command path. Access comes from the existing mailbox.
PrisonerReleaseSubmit12004 SubmitPlayerPrisonerRelease12004(
    const PrisonerReleaseActionBindings12004 &,
    const PrisonerReleasePreviewAccess12004 &,
    const PrisonerNegotiatedPreview12004 &observed_terms,
    std::uint64_t expected_native_revision,
    std::int64_t expected_date_raw) noexcept;

std::string SerializePlayerPrisonerReleaseCommandResult12004(
    std::string_view request_id, PrisonerReleaseSubmit12004);

} // namespace xar::ck3_12004
