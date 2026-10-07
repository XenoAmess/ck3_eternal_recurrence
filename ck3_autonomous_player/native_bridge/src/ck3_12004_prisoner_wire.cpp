#include "xar_bridge/ck3_12004_prisoner.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12002_prisoner.hpp"

namespace xar::ck3_12004 {

std::string SerializePlayerPrisonerCollectionPrivateV1(
    const bridge::PlayerPrisonerCollectionSnapshotV1 &snapshot,
    std::uint64_t revision,
    const std::array<PlayerPrisonerRansomQuoteV1,
        bridge::kPlayerPrisonerMaximumRowsV1> &quotes,
    bool quotes_complete,
    const std::array<PrisonerReleasePreview12004,
        bridge::kPlayerPrisonerMaximumRowsV1> *release_previews) {
  return SerializePlayerPrisonerCollectionPrivateV1(
      snapshot, revision, quotes, quotes_complete, release_previews, nullptr);
}

std::string SerializePlayerPrisonerCollectionPrivateV1(
    const bridge::PlayerPrisonerCollectionSnapshotV1 &snapshot,
    std::uint64_t revision,
    const std::array<PlayerPrisonerRansomQuoteV1,
        bridge::kPlayerPrisonerMaximumRowsV1> &quotes,
    bool quotes_complete,
    const std::array<PrisonerReleasePreview12004,
        bridge::kPlayerPrisonerMaximumRowsV1> *release_previews,
    const std::array<PrisonerNegotiatedPreview12004,
        bridge::kPlayerPrisonerMaximumRowsV1> *negotiated_previews) {
  // This is software serialization of copied values. No .2/.3 native binder
  // or native read is called. Native kinship is not supplied by this route.
  return game::Render12004BuildIdentity(
      ck3_12002::SerializePlayerPrisonerCollectionPrivateV1(
          snapshot, revision, quotes, quotes_complete, release_previews,
          nullptr, negotiated_previews),
      game::Ck3_12004AdapterDescriptor());
}

} // namespace xar::ck3_12004
