#include "xar_bridge/ck3_12004_diplomacy.hpp"

namespace xar::ck3_12004 {

DiplomacyBindings BindDiplomacyImage(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const CoreBindings &actual_core,
    const ck3_12002::CommandBindings &actual_commands) noexcept {
  DiplomacyBindings output{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      !actual_core.enabled)
    return output;
  output.enabled = true;
  output.core = actual_core;
  output.commands = actual_commands;
  output.played_character_id = reinterpret_cast<const std::int32_t *>(
      image_base + kPlayedCharacterIdRva);
  output.interaction_database =
      reinterpret_cast<ck3_12002::GetInteractionDatabase>(
          image_base + kInteractionDatabaseRva);
  output.default_context =
      reinterpret_cast<ck3_12002::DefaultInteractionContext>(
          image_base + kDefaultInteractionContextRva);
  output.construct_context =
      reinterpret_cast<ck3_12002::ConstructInteractionContext>(
          image_base + kConstructInteractionContextRva);
  output.resolution_context =
      reinterpret_cast<ck3_12002::ConstructWarResolutionContext>(
          image_base + kWarResolutionContextRva);
  output.destroy_context =
      reinterpret_cast<ck3_12002::DestroyInteractionContext>(
          image_base + kDestroyInteractionContextRva);
  output.validate_context =
      reinterpret_cast<ck3_12002::ValidateInteractionContext>(
          image_base + kValidateInteractionContextRva);
  output.answer_score =
      reinterpret_cast<ck3_12002::ReadInteractionAnswerScore>(
          image_base + kInteractionAnswerScoreRva);
  output.evaluate_trigger =
      reinterpret_cast<ck3_12002::EvaluateInteractionTrigger>(
          image_base + kEvaluateInteractionTriggerRva);
  output.construct_send_command =
      reinterpret_cast<ck3_12002::ConstructSendInteractionCommand>(
          image_base + kSendInteractionCommandRva);
  output.contains_participant =
      reinterpret_cast<ck3_12002::ContainsWarParticipant>(
          image_base + kContainsWarParticipantRva);
  output.war_score = reinterpret_cast<ck3_12002::GetWarScore>(
      image_base + kWarScoreRva);
  output.imprisonment_score = reinterpret_cast<ck3_12002::GetWarScore>(
      image_base + kWarImprisonmentScoreRva);
  output.battle_base_score = reinterpret_cast<ck3_12002::GetWarScore>(
      image_base + kWarBattleBaseScoreRva);
  output.battle_side_score = reinterpret_cast<ck3_12002::GetWarScoreSide>(
      image_base + kWarBattleSideScoreRva);
  output.occupation_score =
      reinterpret_cast<ck3_12002::GetWarScoreOccupation>(
          image_base + kWarOccupationScoreRva);
  output.ticking_score = reinterpret_cast<ck3_12002::GetWarScoreTicking>(
      image_base + kWarTickingScoreRva);
  output.send_primary_vtable = image_base + kSendPrimaryVtableRva;
  output.send_secondary_vtable = image_base + kSendSecondaryVtableRva;
  output.auto_accept_trigger_offset = kDiplomacyAutoAcceptTriggerOffset;
  output.auto_accept_scalar_offset = kDiplomacyAutoAcceptScalarOffset;
  return output;
}

} // namespace xar::ck3_12004
