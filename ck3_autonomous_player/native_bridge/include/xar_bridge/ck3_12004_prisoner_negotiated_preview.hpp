#pragma once

#include "xar_bridge/ck3_12004_prisoner_release_preview.hpp"
#include "xar_bridge/ck3_12003_prisoner_negotiated_collection.hpp"

namespace xar::ck3_12004 {

// Portable copied-value types and observer algorithm. This factory binds only
// current4 executable entries through the centrally admitted context image.
using PrisonerNegotiatedPreview12004 = ck3_12003::PrisonerNegotiatedPreview12003;
using PrisonerNegotiatedBindings12004 = ck3_12003::PrisonerNegotiatedBindings12003;
inline constexpr std::uint32_t kPrisonerReleaseAllOptionMask12004 =
    ck3_12003::kPrisonerReleaseAllOptionMask12003;

PrisonerNegotiatedBindings12004 BindPrisonerNegotiatedPreview12004(
    std::uintptr_t module_base, std::string_view actual_executable_sha256) noexcept;

bool ReadPrisonerNegotiatedPreview12004(
    const PrisonerNegotiatedBindings12004 &,
    const PrisonerReleasePreviewAccess12004 &,
    std::uint32_t jailer_character_id, std::uint32_t prisoner_character_id,
    std::uint32_t requested_option_mask_bits,
    PrisonerNegotiatedPreview12004 &) noexcept;

// The production mailbox and Root's eventual whole-wire FIRST can use this
// same selected-row routing; it preserves request metadata on unevaluated rows.
bool ReadPrisonerNegotiatedCollectionRow12004(
    const PrisonerNegotiatedBindings12004 &,
    const PrisonerReleasePreviewAccess12004 &,
    const bridge::PlayerPrisonerCollectionSnapshotV1 &,
    std::uint32_t ordinal, std::uint32_t requested_option_mask_bits,
    std::array<PrisonerNegotiatedPreview12004,
        bridge::kPlayerPrisonerMaximumRowsV1> &) noexcept;

std::string SerializePrisonerNegotiatedPreview12004(
    const PrisonerNegotiatedPreview12004 &);

} // namespace xar::ck3_12004
