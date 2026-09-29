#include "xar_bridge/h2743_preaction_existing_truce_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <cstring>
#include <limits>
#include <string>

namespace xar::ck3_11906 {
namespace {

bool GuardedHasTruce(H2743HasTruceV1 function, void *owner, void *toward,
                    bool &output) noexcept {
  if (function == nullptr || owner == nullptr || toward == nullptr) return false;
#if defined(_MSC_VER)
  __try {
    output = function(owner, toward);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = function(owner, toward);
  return true;
#endif
}

bool GuardedEndDate(H2743GetTruceEndDateV1 function, void *owner,
                    void *toward, std::int32_t &output) noexcept {
  if (function == nullptr || owner == nullptr || toward == nullptr) return false;
#if defined(_MSC_VER)
  __try {
    const void *const value = function(owner, toward);
    if (value == nullptr) return false;
    std::memcpy(&output, value, sizeof(output));
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  const void *const value = function(owner, toward);
  if (value == nullptr) return false;
  std::memcpy(&output, value, sizeof(output));
  return true;
#endif
}

bool IsExactWar(const H2743TruceWarIdentityV1 &war) noexcept {
  return war.war_object != nullptr && war.casus_belli_object != nullptr &&
         war.war_id == kH2743TruceWarIdV1 &&
         war.primary_attacker_id == kH2743TruceAttackerIdV1 &&
         war.primary_defender_id == kH2743TruceDefenderIdV1 &&
         war.casus_belli_database_index == 17 && war.exact_casus_belli_key &&
         war.target_title_ids.size() == 1 && war.target_title_ids[0] == 2128;
}

bool IsExactPausedFrame(const game::Snapshot &snapshot) noexcept {
  if (!snapshot.paused || !snapshot.map_ready ||
      !snapshot.has_played_character || !snapshot.played_character_alive ||
      snapshot.played_character_id != kH2743TruceDefenderIdV1 ||
      snapshot.date_raw != kH2743TruceDateRawV1) return false;
  const auto matching_war_id = std::count_if(
      snapshot.active_wars.begin(), snapshot.active_wars.end(),
      [](const game::ActiveWarSnapshot &war) {
        return war.war_id == kH2743TruceWarIdV1;
      });
  if (matching_war_id != 1) return false;
  const auto war = std::find_if(
      snapshot.active_wars.begin(), snapshot.active_wars.end(),
      [](const game::ActiveWarSnapshot &candidate) {
        return candidate.war_id == kH2743TruceWarIdV1;
      });
  return war != snapshot.active_wars.end() &&
         war->player_side == game::PlayerWarSide::defender &&
         war->player_is_primary_war_leader &&
         war->primary_opponent_character_id == kH2743TruceAttackerIdV1 &&
         war->targeted_title_ids.size() == 1 &&
         war->targeted_title_ids[0] == 2128;
}

std::string_view StatusName(game::H2743ExistingTruceStatusV1 status) noexcept {
  switch (status) {
  case game::H2743ExistingTruceStatusV1::existing_truce:
    return "existing_truce";
  case game::H2743ExistingTruceStatusV1::no_existing_truce:
    return "no_existing_truce";
  case game::H2743ExistingTruceStatusV1::unavailable:
    return "unavailable";
  }
  return "unavailable";
}

} // namespace

bool AdmitH2743PreactionFrameClaimV1(
    const H2743PreactionFrameClaimV1 &claim,
    std::uint64_t state_revision,
    const game::Snapshot &actual) {
  if (state_revision == 0 ||
      state_revision == std::numeric_limits<std::uint64_t>::max() ||
      claim.native_revision != state_revision ||
      claim.public_revision != state_revision + 1 ||
      claim.snapshot_id != "native:" + std::to_string(state_revision) ||
      claim.date_raw != static_cast<std::uint64_t>(kH2743TruceDateRawV1) ||
      claim.actor_character_id !=
          static_cast<std::uint64_t>(kH2743TruceDefenderIdV1) ||
      claim.war_id != static_cast<std::uint64_t>(kH2743TruceWarIdV1) ||
      claim.episode_id != kH2743EpisodeIdV1 ||
      claim.checkpoint_sha256 != kH2743CheckpointSha256V1 ||
      claim.exe_sha256 != kH2743ExeSha256V1) {
    return false;
  }
  return IsExactPausedFrame(actual) &&
         actual.date_raw == static_cast<std::int32_t>(claim.date_raw) &&
         actual.played_character_id ==
             static_cast<std::int32_t>(claim.actor_character_id);
}

game::H2743ExistingTruceStatusV1 ReadH2743PreactionExistingTruceV1(
    const H2743ExistingTruceAccessV1 &access,
    game::H2743ExistingTruceSnapshotV1 &output) noexcept {
  using Status = game::H2743ExistingTruceStatusV1;
  output = {};
  if (!access.exact_build_admitted || access.read_snapshot == nullptr ||
      access.read_war_identity == nullptr ||
      access.resolve_living_character == nullptr || access.has_truce == nullptr ||
      access.get_truce_end_date == nullptr) {
    output.unavailable_reason = "exact_build_or_read_binding_unavailable";
    return Status::unavailable;
  }
  game::Snapshot before{};
  if (!access.read_snapshot(access.context, before)) {
    output.unavailable_reason = "snapshot_read_failed";
    return Status::unavailable;
  }
  output.date_raw = before.date_raw;
  if (!IsExactPausedFrame(before)) {
    output.unavailable_reason = "exact_h2743_paused_frame_unavailable";
    return Status::unavailable;
  }
  H2743TruceWarIdentityV1 war_before{};
  if (!access.read_war_identity(access.context, war_before) ||
      !IsExactWar(war_before)) {
    output.unavailable_reason = "exact_h2743_war_identity_unavailable";
    return Status::unavailable;
  }
  void *const owner = access.resolve_living_character(
      access.context, kH2743TruceAttackerIdV1);
  void *const toward = access.resolve_living_character(
      access.context, kH2743TruceDefenderIdV1);
  if (owner == nullptr || toward == nullptr || owner == toward) {
    output.unavailable_reason = "full_generation_character_identity_unavailable";
    return Status::unavailable;
  }

  bool has_first = false;
  bool has_second = false;
  std::int32_t expiry_first = 0;
  std::int32_t expiry_second = 0;
  if (!GuardedHasTruce(access.has_truce, owner, toward, has_first) ||
      (has_first && !GuardedEndDate(access.get_truce_end_date, owner, toward,
                                    expiry_first)) ||
      !GuardedHasTruce(access.has_truce, owner, toward, has_second) ||
      (has_second && !GuardedEndDate(access.get_truce_end_date, owner, toward,
                                     expiry_second))) {
    output.unavailable_reason = "native_truce_read_failed";
    return Status::unavailable;
  }

  game::Snapshot after{};
  H2743TruceWarIdentityV1 war_after{};
  if (!access.read_snapshot(access.context, after) || after != before ||
      !access.read_war_identity(access.context, war_after) ||
      war_after != war_before || !IsExactWar(war_after) ||
      access.resolve_living_character(access.context,
                                      kH2743TruceAttackerIdV1) != owner ||
      access.resolve_living_character(access.context,
                                      kH2743TruceDefenderIdV1) != toward) {
    output.unavailable_reason = "same_frame_or_war_identity_drift";
    return Status::unavailable;
  }
  if (has_first != has_second ||
      (has_first && (expiry_first != expiry_second ||
                     expiry_first <= before.date_raw))) {
    output.unavailable_reason = "existing_truce_slot_unstable_or_expired";
    return Status::unavailable;
  }
  output.same_frame_stable = true;
  if (!has_first) {
    output.status = Status::no_existing_truce;
    output.unavailable_reason = "no_existing_truce";
    return output.status;
  }
  output.status = Status::existing_truce;
  output.preaction_existing_expiry_observable = true;
  output.preaction_existing_expiry_date_raw = expiry_first;
  output.unavailable_reason = {};
  return output.status;
}

std::string SerializeH2743PreactionExistingTruceV1(
    const game::H2743ExistingTruceSnapshotV1 &snapshot) {
  std::string result =
      "{\"schema\":\"xar.ck3.h2743_preaction_existing_truce.v1\","
      "\"backend_id\":\"ck3-1.19.0.6-native-h2743-existing-truce-v1\","
      "\"war_id\":16777231,\"owner_character_id\":30097,"
      "\"toward_character_id\":29829,\"episode_id_claim\":\"native-29829-2bc2d599f7f9\","
      "\"episode_authenticated_here\":false,\"checkpoint_sha256_claim\":\""
      "A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9\","
      "\"checkpoint_bytes_authenticated_here\":false,\"status\":\"";
  result += StatusName(snapshot.status);
  result += "\",\"snapshot_revision\":" +
            std::to_string(snapshot.snapshot_revision);
  result += ",\"date_raw\":" + std::to_string(snapshot.date_raw);
  result += ",\"same_frame_stable\":";
  result += snapshot.same_frame_stable ? "true" : "false";
  result += ",\"preaction_existing_expiry_observable\":";
  result += snapshot.preaction_existing_expiry_observable ? "true" : "false";
  result += ",\"preaction_existing_expiry_date_raw\":";
  if (snapshot.preaction_existing_expiry_observable) {
    result += std::to_string(snapshot.preaction_existing_expiry_date_raw);
  } else {
    result += "null";
  }
  result +=
      ",\"post_surrender_actual_expiry_date_raw\":null,"
      "\"script_candidate_days\":null,\"effect_projection_complete\":false,"
      "\"material_complete\":false,\"recommended_outcome\":null,"
      "\"action_literal\":null,\"unavailable_reason\":";
  if (snapshot.unavailable_reason.empty()) {
    result += "null";
  } else {
    result += '"';
    result += snapshot.unavailable_reason;
    result += '"';
  }
  result += '}';
  return result;
}

} // namespace xar::ck3_11906
