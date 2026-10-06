#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_prisoner_ransom.hpp"
#include "xar_bridge/ck3_12004_prisoner_release_preview.hpp"
#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"

namespace xar::ck3_12004 {

// Original118B getter mapped through its actual adjacent runtime gap, then
// complete instructions/branches/RIP operands compared in primary-title-map01.
inline constexpr std::uintptr_t kPrisonerPrimaryTitleRva12004 = 0x289DA10;
inline constexpr std::uintptr_t kPrisonerTitleStorageSlotRva12004 = 0x5D1DAF8;
inline constexpr std::uintptr_t kPrisonerTitleFallbackSlotRva12004 = 0x5D1DAE0;

// Copied collection values retain the established private wire contract.
// The reader below admits only the actual .4 executable and its mapped fields.
bool ReadPlayerPrisonerCollectionV1(
    const bridge::PlayerPrisonerCollectionAccessV1 &access,
    bridge::PlayerPrisonerCollectionSnapshotV1 &output) noexcept;

std::string SerializePlayerPrisonerCollectionPrivateV1(
    const bridge::PlayerPrisonerCollectionSnapshotV1 &snapshot,
    std::uint64_t snapshot_revision,
    const std::array<PlayerPrisonerRansomQuoteV1,
        bridge::kPlayerPrisonerMaximumRowsV1> &quotes,
    bool quotes_complete,
    const std::array<PrisonerReleasePreview12004,
        bridge::kPlayerPrisonerMaximumRowsV1> *release_previews = nullptr);

} // namespace xar::ck3_12004
