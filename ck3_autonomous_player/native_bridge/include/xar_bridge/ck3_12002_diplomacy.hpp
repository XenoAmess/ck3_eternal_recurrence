#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_commands.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kWarResolutionContextRva = 0xCF57D0;
inline constexpr std::uintptr_t kInteractionDatabaseRva = 0x89DA60;
inline constexpr std::uintptr_t kDefaultInteractionContextRva = 0x3077320;
inline constexpr std::uintptr_t kConstructInteractionContextRva = 0x3076C90;
inline constexpr std::uintptr_t kDestroyInteractionContextRva = 0x30773A0;
inline constexpr std::uintptr_t kValidateInteractionContextRva = 0x307C040;
inline constexpr std::uintptr_t kInteractionAnswerScoreRva = 0x307C460;
inline constexpr std::uintptr_t kSendInteractionCommandRva = 0x2968170;
inline constexpr std::uintptr_t kPlayedCharacterIdRva = 0x5DDDC00;
inline constexpr std::size_t kDiplomacyWarManagerOffset = 0x2EBE0;
inline constexpr std::size_t kCasusBelliFlagsOffset = 0x1548;

using GetInteractionDatabase = void *(*)();
using DefaultInteractionContext = void *(*)(void *context);
using ConstructInteractionContext = void *(*)(
    void *context, void *interaction, std::int32_t actor_id,
    std::int32_t recipient_id, void *extra_context, bool redirect_roles);
using ConstructWarResolutionContext = void (*)(void *context, void *war,
                                               bool player_victory);
using DestroyInteractionContext = void (*)(void *context);
using ValidateInteractionContext = bool (*)(void *context, void *diagnostics);
using ReadInteractionAnswerScore = std::int64_t *(*)(void *, std::int64_t *);
using EvaluateInteractionTrigger = bool (*)(void *, const void *);
using ConstructSendInteractionCommand = void *(*)(void *, const void *);
using ContainsWarParticipant = bool (*)(void *, std::int32_t);
using GetWarScore = std::int32_t (*)(void *, void *);
using GetWarScoreSide = std::int32_t (*)(void *, bool, void *);
using GetWarScoreOccupation = std::uint64_t (*)(void *, bool, void *);
using GetWarScoreTicking = std::int32_t (*)(void *, bool, void *, bool);

struct DiplomacyBindings {
  bool enabled = false;
  CoreBindings core;
  CommandBindings commands;
  const std::int32_t *played_character_id = nullptr;
  GetInteractionDatabase interaction_database = nullptr;
  DefaultInteractionContext default_context = nullptr;
  ConstructInteractionContext construct_context = nullptr;
  ConstructWarResolutionContext resolution_context = nullptr;
  DestroyInteractionContext destroy_context = nullptr;
  ValidateInteractionContext validate_context = nullptr;
  ReadInteractionAnswerScore answer_score = nullptr;
  EvaluateInteractionTrigger evaluate_trigger = nullptr;
  ConstructSendInteractionCommand construct_send_command = nullptr;
  ContainsWarParticipant contains_participant = nullptr;
  GetWarScore war_score = nullptr;
  GetWarScore imprisonment_score = nullptr;
  GetWarScore battle_base_score = nullptr;
  GetWarScoreSide battle_side_score = nullptr;
  GetWarScoreOccupation occupation_score = nullptr;
  GetWarScoreTicking ticking_score = nullptr;
  std::uintptr_t send_primary_vtable = 0;
  std::uintptr_t send_secondary_vtable = 0;
  std::size_t auto_accept_trigger_offset = 0;
  std::size_t auto_accept_scalar_offset = 0;
};

// Pure binding calculation, never attaches to or reads another process.
DiplomacyBindings BindDiplomacyImage(std::uintptr_t image_base,
                                    std::string_view sha256) noexcept;

game::ReadWarTerminationOptionsResult ReadWarTerminationOptions(
    const DiplomacyBindings &, std::int32_t war_id,
    game::WarTerminationOptionsSnapshot &) noexcept;
game::EnforceDemandsResult SubmitEnforceDemands(const DiplomacyBindings &,
                                               std::int32_t war_id) noexcept;
game::SurrenderWarResult SubmitSurrenderWar(const DiplomacyBindings &,
                                           std::int32_t war_id) noexcept;
game::OfferWhitePeaceResult SubmitOfferWhitePeace(const DiplomacyBindings &,
                                                 std::int32_t war_id) noexcept;

// Used by the claim-terms module. Full-generation equality and the native
// ended BYTE are checked; adjacent bytes are not interpreted as an end flag.
void *ResolveDiplomacyWar(const CoreBindings &, std::int32_t war_id) noexcept;

} // namespace xar::ck3_12002
