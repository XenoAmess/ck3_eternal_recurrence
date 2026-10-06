#pragma once

#include "xar_bridge/ck3_12002_combat.hpp"
#include "xar_bridge/ck3_12002_province.hpp"
#include "xar_bridge/ck3_12003_commander.hpp"
#include "xar_bridge/ck3_12003_commander_target_roll_dto.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12003 {

struct CommanderTargetRollBindings {
  bool enabled = false;
  ck3_12002::ProvinceBindings provinces{};
  ck3_12002::CombatBindings combat{};
};

// The exact .3 image gate precedes reuse of the frozen .2 Province/combat
// binders, whose already reviewed storage/getter spans are unchanged in .3.
CommanderTargetRollBindings BindCommanderTargetRollImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Candidate-specific semantics over the existing read-only roll computation.
// This never selects/assigns a commander and never calls the native RNG.
CommanderCandidateTargetRollBoundsSnapshot ReadCommanderCandidateTargetRollBounds(
    const ck3_12002::CombatBindings &bindings, std::int32_t target_province_id,
    void *target_terrain, std::int32_t candidate_character_id) noexcept;

// Attach only after the genuine native pool read, on its same owning-thread
// paused query frame. Resolve the target Province and terrain once for all rows.
// Target failure leaves collection, eligibility, quality and read status intact.
void ReadArmyCommanderCandidateTargetRollBounds(
    const CommanderTargetRollBindings &bindings, std::int32_t target_province_id,
    ArmyCommanderCandidatesSnapshot &observation) noexcept;

} // namespace xar::ck3_12003
