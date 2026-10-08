#include "xar_bridge/ck3_12004_prisoner_collection_result.hpp"

namespace xar::ck3_12004 {
namespace {
std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { out += '\\'; out += static_cast<char>(ch); }
    else if (ch < 0x20) { out += "\\u00"; out += hex[ch >> 4]; out += hex[ch & 15]; }
    else out += static_cast<char>(ch);
  }
  return out + '"';
}
} // namespace

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
    const PrisonerReleaseMaterialOpinion12004 *material) {
  return SerializePrisonerCollectionCommandResult12004(request_id, step,
      query_sequence, observation_revision, snapshot_revision, collection,
      quotes, quotes_complete, release_previews, material, nullptr);
}

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
    const KeeperOpinion12004 *keeper,
    const RetainedTargetState12004 *retained_state) {
  const auto value = SerializePlayerPrisonerCollectionPrivateV1(
      collection, snapshot_revision, quotes, quotes_complete, release_previews,
      negotiated_previews);
  if (value.empty()) return {};
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" +
      Quote(request_id) + ",\"ok\":true,\"result\":{\"step\":" + Quote(step) +
      ",\"accepted\":true,\"status\":\"" +
      (collection.available ? "available" : "unavailable") +
      "\",\"query_sequence\":" + std::to_string(query_sequence) +
      ",\"observation_revision\":" + std::to_string(observation_revision) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"player_prisoner_collection\":" + value;
  if (material != nullptr)
    out += ",\"prisoner_release_material_opinion\":" +
        SerializePrisonerReleaseMaterialOpinion12004(*material);
  if (keeper != nullptr)
    out += ",\"prisoner_keeper_opinion\":" + SerializeKeeperOpinion12004(*keeper);
  if (retained_state != nullptr)
    out += ",\"prisoner_retained_target_state\":" +
        SerializeRetainedTargetState12004(*retained_state);
  return out + ",\"private_build\":true,\"read_only\":true,\"advertised\":false,"
      "\"backend_id\":\"native-headless\"}}";
}

} // namespace xar::ck3_12004
