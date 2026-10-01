#pragma once

#include "xar_bridge/ck3_12002_family_value.hpp"
#include "xar_bridge/ck3_12002_phase_character.hpp"
#include "xar_bridge/ck3_12002_phase_definitions.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12002::family_break_penalty {

inline constexpr std::uintptr_t kHighestTierRva = 0x28AC6B0;
inline constexpr std::uintptr_t kMatchmakerRva = 0x2B94D10;
inline constexpr std::uintptr_t kCloseFamilyRva = 0x29120A0;
inline constexpr std::uintptr_t kCloseOrExtendedFamilyRva = 0x2912290;
inline constexpr std::uintptr_t kTraitFlagRva = 0x2BB0EB0;
inline constexpr std::uintptr_t kYieldsAllianceRva = 0x2C7C650;
inline constexpr std::uintptr_t kCharacterRiteRva = 0x28D2F90;
inline constexpr std::uintptr_t kRiteParameterSetContainsRva = 0xB9DE80;
inline constexpr std::size_t kRiteParameterSetOffset = 0x7B8;

using HighestTier = std::int32_t (*)(void *);
using Matchmaker = void *(*)(void *);
using FamilyPredicate = bool (*)(void *, void *);
using TraitFlag = bool (*)(void *, const std::int32_t *);
using YieldsAlliance = bool (*)(void *, void *, void *, void *);
using CharacterRite = void *(*)(void *);
using ParameterSetContains = bool (*)(const void *, const std::int32_t *);

struct Bindings {
  bool enabled = false;
  family_value::Bindings lineage{};
  phase_character::Bindings traits{};
  PhaseDefinitionBindings identifiers{};
  HighestTier highest_tier = nullptr;
  Matchmaker matchmaker = nullptr;
  FamilyPredicate close_family = nullptr;
  FamilyPredicate close_or_extended_family = nullptr;
  TraitFlag has_trait_flag = nullptr;
  YieldsAlliance yields_alliance = nullptr;
  CharacterRite character_rite = nullptr;
  ParameterSetContains parameter_set_contains = nullptr;
};

struct Penalty {
  bool resource_penalty_available = false;
  bool effects_complete = false;
  bool proper_reason = false;
  bool grand_wedding_promised = false;
  bool ordinary_prestige_relevant = false;
  bool native_yields_alliance_evaluated = false;
  bool yields_alliance = false;
  std::int32_t rejected_owner_character_id = -1;
  std::int32_t highest_rejected_tier = 0;
  // Exact frozen stock's prospective add_prestige argument, scale 100000.
  // This is not the interaction's native send-charge vector, a loaded override
  // observation, or an independently observed post-command resource delta.
  std::int64_t stock_prestige_effect_raw = 0;
  std::int32_t stock_prestige_level_effect = 0;
  std::string_view source = "stock_branch_projection_1.20.0.2";
  std::string_view unavailable_reason = "break_penalty_native_inputs_unavailable";
};

Bindings BindFamilyBreakPenaltyImage(std::uintptr_t image_base,
                                    std::string_view executable_sha256) noexcept;

// Owning paused application thread only. The enclosing interaction reader
// supplies the native finalized rejecting/rejected roles, checks the frame and
// full CharacterIDs before/after, and retains responsibility for CanSend.
// This leaf reads traits, variables, ancestry, native marriage-only predicates,
// and the exact stock branch. It never executes an effect or an interaction.
bool ReadFamilyBreakPenalty(const Bindings &, void *actor,
                            void *rejecting_betrothed,
                            void *rejected_betrothed, Penalty &) noexcept;

} // namespace xar::ck3_12002::family_break_penalty
