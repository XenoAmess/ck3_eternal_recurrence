#include "xar_bridge/ck3_12002_prisoner.hpp"

namespace xar::ck3_12002 {
namespace {
void AppendPrisonerJsonString(std::string &out, std::string_view value) {
  out += '"';
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { out += '\\'; out += static_cast<char>(ch); }
    else if (ch < 0x20) {
      constexpr char hex[] = "0123456789abcdef";
      out += "\\u00"; out += hex[ch >> 4]; out += hex[ch & 15];
    } else out += static_cast<char>(ch);
  }
  out += '"';
}
} // namespace

std::string SerializePrisonerWarRetentionV1(
    const ck3_11906::WarPrisonerReleasePairsObservationV1 &value) {
  if (!value.same_frame_stable || !value.full_participant_scan ||
      !value.primary_and_first_three_successors_scanned) return {};
  std::string result = "{\"war_id\":" + std::to_string(value.war_id) +
      ",\"date_raw\":" + std::to_string(value.date_raw) +
      ",\"active_casus_belli_database_index\":" +
      std::to_string(value.active_casus_belli_database_index) + ",\"active_casus_belli_key\":";
  AppendPrisonerJsonString(result, value.active_casus_belli_key);
  result += ",\"primary_attacker_character_id\":" + std::to_string(value.primary_attacker_character_id) +
      ",\"primary_defender_character_id\":" + std::to_string(value.primary_defender_character_id);
  const auto ids = [&](std::string_view key, const std::vector<std::int32_t> &rows) {
    result += ",\"" + std::string(key) + "\":[";
    for (std::size_t index = 0; index < rows.size(); ++index) {
      if (index != 0) result += ',';
      result += std::to_string(rows[index]);
    }
    result += ']';
  };
  ids("attacker_participant_ids", value.attacker_participant_ids);
  ids("defender_participant_ids", value.defender_participant_ids);
  ids("attacker_release_candidate_ids", value.attacker_release_candidate_ids);
  ids("defender_release_candidate_ids", value.defender_release_candidate_ids);
  result += ",\"release_pairs\":[";
  for (std::size_t index = 0; index < value.release_pairs.size(); ++index) {
    if (index != 0) result += ',';
    const auto &pair = value.release_pairs[index];
    result += "{\"jailer_character_id\":" + std::to_string(pair.jailer_character_id) +
        ",\"prisoner_character_id\":" + std::to_string(pair.prisoner_character_id) + ",\"reason\":";
    AppendPrisonerJsonString(result, pair.reason);
    result += '}';
  }
  result += "],\"full_participant_scan\":true,\"primary_and_first_three_successors_scanned\":true,"
      "\"same_frame_stable\":true}";
  return result;
}

std::string SerializePlayerPrisonerCollectionPrivateV1(
    const bridge::PlayerPrisonerCollectionSnapshotV1 &snapshot,
    std::uint64_t revision,
    const std::array<PlayerPrisonerRansomQuoteV1, bridge::kPlayerPrisonerMaximumRowsV1> &quotes,
    bool quotes_complete,
    const std::array<ck3_12003::PrisonerReleasePreview12003,
        bridge::kPlayerPrisonerMaximumRowsV1> *release_previews,
    const std::array<ck3_12003::PrisonerNativeKinship12003,
        bridge::kPlayerPrisonerMaximumRowsV1> *kinship_inputs,
    const std::array<ck3_12003::PrisonerNegotiatedPreview12003,
        bridge::kPlayerPrisonerMaximumRowsV1> *negotiated_previews) {
  if (revision == 0 || snapshot.returned_count > bridge::kPlayerPrisonerMaximumRowsV1 ||
      (snapshot.available && (!snapshot.collection_complete ||
          snapshot.failure != bridge::PlayerPrisonerCollectionFailureV1::none ||
          snapshot.total_count != snapshot.returned_count ||
          snapshot.frame.played_character_id <= 0 || !quotes_complete))) return {};
  std::string value = "{\"schema\":\"player-prisoner-collection-private-v1\",\"schema_version\":" +
      std::string(kinship_inputs != nullptr ? "7" : "6") +
      ",\"snapshot_revision\":" + std::to_string(revision) + ",\"status\":\"" +
      (snapshot.available ? "available" : "unavailable") + "\",\"unavailable_reason\":";
  value += snapshot.available ? "null" : "\"" + std::string(
      bridge::PlayerPrisonerCollectionFailureNameV1(snapshot.failure)) + "\"";
  const auto scalar = [&](std::string_view key, auto raw, bool available) {
    value += ",\"" + std::string(key) + "\":";
    value += available ? std::to_string(raw) : "null";
  };
  scalar("date_raw", snapshot.frame.date_raw, snapshot.available);
  scalar("played_character_id", snapshot.frame.played_character_id, snapshot.available);
  scalar("played_house_id", snapshot.played_house_id, snapshot.available && snapshot.played_house_id >= 0);
  scalar("played_dynasty_id", snapshot.played_dynasty_id, snapshot.available && snapshot.played_dynasty_id >= 0);
  scalar("played_dread_raw", snapshot.played_dread_raw, snapshot.available);
  scalar("total_count", snapshot.total_count, snapshot.available);
  scalar("returned_count", snapshot.returned_count, snapshot.available);
  value += ",\"collection_complete\":";
  value += snapshot.available ? "true" : "false";
  value += ",\"prisoners\":[";
  if (snapshot.available) {
    for (std::uint32_t index = 0; index < snapshot.returned_count; ++index) {
      if (index != 0) value += ',';
      const auto &row = snapshot.rows[index];
      value += "{\"source_ordinal\":" + std::to_string(row.source_ordinal);
      scalar("prisoner_character_id", row.full_character_id, true);
      scalar("collection_owner_character_id", snapshot.frame.played_character_id, true);
      scalar("jailer_character_id", row.jailer_character_id, true);
      value += ",\"custody_relation_verified\":true";
      scalar("house_id", row.house_id, row.house_id >= 0);
      scalar("dynasty_id", row.dynasty_id, row.dynasty_id >= 0);
      value += ",\"same_house\":";
      value += snapshot.played_house_id >= 0 && snapshot.played_house_id == row.house_id ? "true" : "false";
      value += ",\"same_dynasty\":";
      value += snapshot.played_dynasty_id >= 0 && snapshot.played_dynasty_id == row.dynasty_id ? "true" : "false";
      value += ",\"is_child_of_played_character\":";
      value += row.child_of_played_character ? "true" : "false";
      scalar("primary_title_tier_raw", row.primary_title_tier_raw, row.primary_title_tier_raw >= 1);
      value += ",\"unconditional_release_preview\":";
      if (release_previews != nullptr) {
        value += ck3_12003::SerializePrisonerReleasePreview12003((*release_previews)[index]);
      } else {
        value += "{\"private_build\":true,\"read_only\":true,"
            "\"advertised\":false,\"action_surface_present\":false,\"status\":\"unavailable\","
            "\"unavailable_reason\":\"release_preview_not_enabled_for_12002_ransom\"}";
      }
      if (kinship_inputs != nullptr) {
        auto kinship = (*kinship_inputs)[index];
        if (kinship.available && (kinship.frame != snapshot.frame ||
            kinship.source_ordinal != row.source_ordinal ||
            kinship.jailer_character_id != row.jailer_character_id ||
            kinship.prisoner_character_id != row.full_character_id)) {
          kinship = {};
          kinship.unavailable_reason = "collection_binding_unverified";
        }
        value += ",\"native_kinship\":" +
            ck3_12003::SerializePrisonerNativeKinship12003(kinship);
      }
      const auto quote = ck3_11906::SerializePlayerPrisonerRansomQuotePrivateV1(
          quotes[index], revision, snapshot.frame.date_raw, snapshot.frame.proof_epoch);
      if (negotiated_previews != nullptr) {
        auto preview = (*negotiated_previews)[index];
        const auto &observed = preview.observation;
        if (observed.available && (observed.frame != snapshot.frame ||
            observed.actor_character_id !=
                static_cast<std::uint32_t>(snapshot.frame.played_character_id) ||
            observed.puppet_or_actor_character_id !=
                static_cast<std::uint32_t>(snapshot.frame.played_character_id) ||
            observed.recipient_character_id != row.full_character_id ||
            observed.prisoner_character_id != row.full_character_id ||
            observed.jailer_character_id != row.jailer_character_id ||
            preview.requested_option_mask_bits == 0 ||
            preview.requested_option_mask_bits >
                ck3_12003::kPrisonerReleaseAllOptionMask12003 ||
            observed.selected_option_mask_bits != preview.requested_option_mask_bits)) {
          const auto requested_mask = preview.requested_option_mask_bits;
          preview = {};
          preview.requested_option_mask_bits = requested_mask;
          preview.observation.unavailable_reason = "collection_binding_unverified";
        }
        value += ",\"negotiated_release_preview\":" +
            ck3_12003::SerializePrisonerNegotiatedPreview12003(preview);
      }
      if (quote.empty()) return {};
      value += ",\"ransom_quote_preview\":" + quote + '}';
    }
  }
  value += "]}";
  return value;
}

} // namespace xar::ck3_12002
