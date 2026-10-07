#pragma once

#include "xar_bridge/ck3_12004_prisoner.hpp"
#include "xar_bridge/ck3_12004_prisoner_keeper_opinion.hpp"
#include "xar_bridge/ck3_12004_prisoner_release_material_opinion.hpp"

namespace xar::ck3_12004 {

// Production collection handler and the fresh source fixture emit this same
// complete command_result. A null material pointer preserves the old wire.
std::string SerializePrisonerCollectionCommandResult12004(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence, std::uint64_t observation_revision,
    std::uint64_t snapshot_revision,
    const bridge::PlayerPrisonerCollectionSnapshotV1 &collection,
    const std::array<PlayerPrisonerRansomQuoteV1,
        bridge::kPlayerPrisonerMaximumRowsV1> &quotes,
    bool quotes_complete,
    const std::array<PrisonerReleasePreview12004,
        bridge::kPlayerPrisonerMaximumRowsV1> *release_previews,
    const PrisonerReleaseMaterialOpinion12004 *material);

std::string SerializePrisonerCollectionCommandResult12004(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence, std::uint64_t observation_revision,
    std::uint64_t snapshot_revision,
    const bridge::PlayerPrisonerCollectionSnapshotV1 &collection,
    const std::array<PlayerPrisonerRansomQuoteV1,
        bridge::kPlayerPrisonerMaximumRowsV1> &quotes,
    bool quotes_complete,
    const std::array<PrisonerReleasePreview12004,
        bridge::kPlayerPrisonerMaximumRowsV1> *release_previews,
    const PrisonerReleaseMaterialOpinion12004 *material,
    const std::array<PrisonerNegotiatedPreview12004,
        bridge::kPlayerPrisonerMaximumRowsV1> *negotiated_previews,
    const KeeperOpinion12004 *keeper = nullptr);

} // namespace xar::ck3_12004
