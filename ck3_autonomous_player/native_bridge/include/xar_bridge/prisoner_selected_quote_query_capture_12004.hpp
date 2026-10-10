#pragma once
#include "xar_bridge/prisoner_selected_quote_source_12004.hpp"
#include "xar_bridge/ck3_12004_prisoner_ransom.hpp"
#include "xar_bridge/ck3_12004_prisoner_negotiated_preview.hpp"

namespace xar::ck3_12004 {
PlayerPrisonerRansomQuoteV1 ReadPlayerPrisonerRansomQuoteSourcePrivateV1(
    const PrisonerRansomBindings12004 &, std::uintptr_t module,
    std::int32_t jailer, std::int32_t prisoner, std::uint32_t source_ordinal,
    const PrisonerQuoteSourceFrame12004 &, const PrisonerQuoteReadOnlyAccess12004 &,
    PrisonerSelectedQuoteSource12004 &) noexcept;
bool ReadPrisonerNegotiatedCollectionRowSource12004(
    const PrisonerNegotiatedBindings12004 &, const PrisonerReleasePreviewAccess12004 &,
    const bridge::PlayerPrisonerCollectionSnapshotV1 &, std::uint32_t ordinal, std::uint32_t requested_mask,
    std::array<PrisonerNegotiatedPreview12004, bridge::kPlayerPrisonerMaximumRowsV1> &,
    const PrisonerQuoteSourceFrame12004 &, const PrisonerQuoteReadOnlyAccess12004 &,
    PrisonerSelectedQuoteSource12004 &) noexcept;
// Used by the fresh connected fixture and the real query capture route. The
// callback is the existing getter. It is invoked exactly once with its same
// receiver/output, even if copying inputs fails. No native image is bound here.
using PrisonerExistingScoreQuery12004 = std::int64_t *(*)(void *, std::int64_t *);
using PrisonerExistingCostQuery12004 = void (*)(const void *, const void *, std::int64_t *);
std::int64_t *ObservePrisonerExistingScoreQuery12004(
    const PrisonerQuoteReadOnlyAccess12004 &, PrisonerQuoteSourceSample12004 &,
    PrisonerExistingScoreQuery12004, void *, std::int64_t *) noexcept;
void ObservePrisonerExistingCostQuery12004(const PrisonerQuoteReadOnlyAccess12004 &,
    PrisonerQuoteSourceSample12004 &, PrisonerExistingCostQuery12004,
    const void *, const void *, std::int64_t *) noexcept;
} // namespace xar::ck3_12004
