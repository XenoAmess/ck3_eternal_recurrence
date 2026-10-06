#include "xar_bridge/ck3_12003_commander_target_roll.hpp"

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12003.hpp"

namespace xar::ck3_12003 {
namespace {

CommanderCandidateTargetRollBoundsSnapshot UnavailableTargetBounds(
    std::int32_t target_province_id, std::string_view reason) {
  CommanderCandidateTargetRollBoundsSnapshot output{};
  output.source_target_province_id = target_province_id;
  output.unavailable_reason = reason;
  return output;
}

void AttachUnavailableTargetBounds(
    ArmyCommanderCandidatesSnapshot &observation,
    std::int32_t target_province_id, std::string_view reason) {
  for (auto &candidate : observation.candidates) {
    candidate.target_roll_bounds =
        UnavailableTargetBounds(target_province_id, reason);
  }
}

} // namespace

CommanderTargetRollBindings BindCommanderTargetRollImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  CommanderTargetRollBindings output{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return output;
  output.enabled = true;
  output.provinces = ck3_12002::BindProvinceImage(
      image_base, ck3_12002::kExecutableSha256);
  output.combat = ck3_12002::BindCombatImage(
      image_base, ck3_12002::kExecutableSha256);
  return output;
}

CommanderCandidateTargetRollBoundsSnapshot ReadCommanderCandidateTargetRollBounds(
    const ck3_12002::CombatBindings &bindings, std::int32_t target_province_id,
    void *target_terrain, std::int32_t candidate_character_id) noexcept {
  // The selected helper's -1 means an absent selected commander. A candidate
  // must have an actual identity, so never reuse that absent-side convention.
  if (candidate_character_id == -1) {
    return UnavailableTargetBounds(target_province_id,
                                   "candidate_identity_unavailable");
  }
  const auto native = ck3_12002::ReadSelectedCommanderNextRollBounds(
      bindings, target_province_id, target_terrain, candidate_character_id);
  CommanderCandidateTargetRollBoundsSnapshot output{};
  output.source_target_province_id = target_province_id;
  output.status = native.available ? "available" : "unavailable";
  output.unavailable_reason = native.unavailable_reason;
  if (native.available) {
    output.effective_min_roll = native.effective_min_roll;
    output.effective_max_roll = native.effective_max_roll;
  }
  return output;
}

void ReadArmyCommanderCandidateTargetRollBounds(
    const CommanderTargetRollBindings &bindings, std::int32_t target_province_id,
    ArmyCommanderCandidatesSnapshot &observation) noexcept {
  observation.target_province_id = target_province_id;
  if (target_province_id <= 0) {
    AttachUnavailableTargetBounds(observation, target_province_id,
                                  "target_province_id_invalid");
    return;
  }
  if (!bindings.enabled || !bindings.provinces.enabled) {
    AttachUnavailableTargetBounds(observation, target_province_id,
                                  "target_province_bindings_unavailable");
    return;
  }
  void *const province = ck3_12002::ResolveObjectiveProvince(
      bindings.provinces, target_province_id);
  if (province == nullptr) {
    AttachUnavailableTargetBounds(observation, target_province_id,
                                  "target_province_unavailable");
    return;
  }
  if (!bindings.combat.enabled ||
      bindings.combat.get_province_terrain == nullptr) {
    AttachUnavailableTargetBounds(observation, target_province_id,
                                  "target_terrain_reader_unavailable");
    return;
  }
  void *const terrain = bindings.combat.get_province_terrain(province);
  if (terrain == nullptr) {
    AttachUnavailableTargetBounds(observation, target_province_id,
                                  "target_terrain_unavailable");
    return;
  }
  for (auto &candidate : observation.candidates) {
    if (!candidate.available || candidate.character_id == -1) {
      candidate.target_roll_bounds = UnavailableTargetBounds(
          target_province_id, candidate.unavailable_reason.empty()
              ? std::string_view("candidate_identity_unavailable")
              : candidate.unavailable_reason);
      continue;
    }
    // CanAssign and target context have independent meanings. Observe every
    // valid native row, preserving current manual eligibility and quality.
    candidate.target_roll_bounds = ReadCommanderCandidateTargetRollBounds(
        bindings.combat, target_province_id, terrain, candidate.character_id);
  }
}

} // namespace xar::ck3_12003
