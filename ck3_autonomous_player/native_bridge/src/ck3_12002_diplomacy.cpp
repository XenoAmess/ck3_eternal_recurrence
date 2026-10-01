#include "xar_bridge/ck3_12002_diplomacy.hpp"
#include "xar_bridge/ck3_12002_world.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <string>

namespace xar::ck3_12002 {
namespace {
template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  if (object != nullptr) {
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
                sizeof(value));
  }
  return value;
}
struct alignas(8) ContextStorage { std::array<std::byte, 0x338> bytes{}; };
struct alignas(8) SendStorage { std::array<std::byte, 0x368> bytes{}; };

bool QueryReady(const DiplomacyBindings &b) noexcept {
  return b.enabled && b.core.enabled && b.played_character_id != nullptr &&
         b.contains_participant != nullptr && b.war_score != nullptr &&
         b.default_context != nullptr && b.construct_context != nullptr &&
         b.resolution_context != nullptr && b.interaction_database != nullptr &&
         b.destroy_context != nullptr && b.validate_context != nullptr;
}
bool ReadCbKey(const void *cb, std::string &key) noexcept {
  key.clear();
  if (cb == nullptr) return false;
  const auto size = Load<std::uint64_t>(cb, 0x28);
  const auto capacity = Load<std::uint64_t>(cb, 0x30);
  if (size == 0 || size > 512 || size > capacity) return false;
  const char *data = capacity < 16
      ? reinterpret_cast<const char *>(cb) + 0x18
      : Load<const char *>(cb, 0x18);
  if (data == nullptr) return false;
  try { key.assign(data, static_cast<std::size_t>(size)); }
  catch (...) { return false; }
  return true;
}
bool Narrow(std::int64_t raw, std::int32_t &out) noexcept {
  if (raw < std::numeric_limits<std::int32_t>::min() ||
      raw > std::numeric_limits<std::int32_t>::max()) return false;
  out = static_cast<std::int32_t>(raw); return true;
}
void ReadBreakdown(const DiplomacyBindings &b, void *war,
                   game::WarScoreBreakdownSnapshot &out) noexcept {
  out = {};
  if (!b.imprisonment_score || !b.battle_base_score || !b.battle_side_score ||
      !b.occupation_score || !b.ticking_score) return;
  std::int32_t battles = 0, occupation = 0, ticking = 0;
  if (!Narrow(static_cast<std::int64_t>(b.battle_base_score(war, nullptr)) +
              b.battle_side_score(war, false, nullptr) -
              b.battle_side_score(war, true, nullptr), battles)) return;
  const auto first = b.occupation_score(war, false, nullptr);
  const auto first_score = static_cast<std::int32_t>(first & 0xFFFFFFFFU);
  if (((first >> 32U) & 0xFFU) != 0) occupation = first_score;
  else {
    const auto second = b.occupation_score(war, true, nullptr);
    const auto second_score = static_cast<std::int32_t>(second & 0xFFFFFFFFU);
    if (!Narrow(((second >> 32U) & 0xFFU) != 0
                   ? -static_cast<std::int64_t>(second_score)
                   : static_cast<std::int64_t>(first_score) - second_score,
                occupation)) return;
  }
  if (!Narrow(static_cast<std::int64_t>(
                  b.ticking_score(war, false, nullptr, true)) -
                  b.ticking_score(war, true, nullptr, false), ticking)) return;
  out.observable = true;
  out.imprisonment = b.imprisonment_score(war, nullptr);
  out.battles = battles; out.occupation = occupation; out.ticking = ticking;
}
void ReadAcceptance(const DiplomacyBindings &b, void *context,
                    game::WarTerminationOptionSnapshot &out) noexcept {
  if (b.answer_score != nullptr) {
    std::int64_t raw = 0;
    if (b.answer_score(context, &raw) == &raw) {
      out.ai_acceptance_observable = true;
      out.ai_acceptance = {raw, 100'000};
    }
  }
  void *interaction = Load<void *>(context, 0);
  if (interaction == nullptr || b.auto_accept_trigger_offset == 0 ||
      b.auto_accept_scalar_offset == 0) return;
  void *trigger = Load<void *>(interaction, b.auto_accept_trigger_offset);
  if (trigger != nullptr) {
    if (b.evaluate_trigger != nullptr) {
      out.auto_accept_observable = true;
      out.auto_accept = b.evaluate_trigger(
          trigger, static_cast<const std::byte *>(context) + 8);
    }
  } else {
    const auto scalar = Load<std::uint8_t>(interaction,
                                          b.auto_accept_scalar_offset);
    if (scalar <= 1) {
      out.auto_accept_observable = true; out.auto_accept = scalar != 0;
    }
  }
}
bool WhitePeaceContext(const DiplomacyBindings &b, void *out,
                       std::int32_t actor, std::int32_t recipient) noexcept {
  void *database = b.interaction_database();
  void *interaction = Load<void *>(database, 0x1000 + 3 * sizeof(void *));
  // Native UI uses GDbO as the loaded database-object identity predicate.
  if (interaction == nullptr ||
      Load<std::uint32_t>(interaction, 0x38) != 0x4744624FU) return false;
  return b.construct_context(out, interaction, actor, recipient, nullptr, true)
         == out;
}
bool EvaluateOption(const DiplomacyBindings &b, void *war,
                     bool player_victory,
                     game::WarTerminationOptionSnapshot &out) noexcept {
  ContextStorage storage;
  void *context = storage.bytes.data();
  if (b.default_context(context) != context) return false;
  b.resolution_context(context, war, player_victory);
  out.context_constructed = Load<void *>(context, 0x330) != nullptr;
  if (out.context_constructed) {
    out.native_validator_observable = true;
    out.native_validator_passed = b.validate_context(context, nullptr);
    ReadAcceptance(b, context, out);
  }
  b.destroy_context(context); return true;
}
enum class NativeOutcome { victory, surrender, white_peace };
enum class SubmitResult {
  submitted, rejected, paused_required, no_player, missing_war,
  not_participant, not_leader, missing_cb, white_peace_forbidden,
  missing_context, invalid, unavailable
};
SubmitResult Submit(const DiplomacyBindings &b, std::int32_t id,
                    NativeOutcome outcome) noexcept {
  if (!QueryReady(b) || !b.commands.enabled || !b.construct_send_command ||
      b.send_primary_vtable == 0 || b.send_secondary_vtable == 0)
    return SubmitResult::unavailable;
  CoreSnapshotPrefix frame;
  if (!ReadCoreSnapshot(b.core, frame)) return SubmitResult::unavailable;
  if (!frame.clock.paused) return SubmitResult::paused_required;
  if (!frame.has_played_character || !frame.played_character_alive)
    return SubmitResult::no_player;
  if (*b.played_character_id != frame.played_character_id)
    return SubmitResult::unavailable;
  void *war = ResolveDiplomacyWar(b.core, id);
  if (war == nullptr) return SubmitResult::missing_war;
  const bool attacker = b.contains_participant(
      static_cast<std::byte *>(war) + 0x20, frame.played_character_id);
  const bool defender = b.contains_participant(
      static_cast<std::byte *>(war) + 0x80, frame.played_character_id);
  if (!attacker && !defender) return SubmitResult::not_participant;
  if (attacker == defender) return SubmitResult::unavailable;
  const bool leader = Load<std::int32_t>(war, attacker ? 0x288 : 0x28C)
                      == frame.played_character_id;
  if (!leader) return SubmitResult::not_leader;
  ContextStorage context_storage;
  void *context = context_storage.bytes.data();
  if (outcome == NativeOutcome::white_peace) {
    void *cb = Load<void *>(war, 0x100);
    if (cb == nullptr) return SubmitResult::missing_cb;
    if ((Load<std::uint32_t>(cb, kCasusBelliFlagsOffset) & (1U << 7U)) == 0)
      return SubmitResult::white_peace_forbidden;
    const auto recipient = Load<std::int32_t>(war, attacker ? 0x28C : 0x288);
    if (!WhitePeaceContext(b, context, frame.played_character_id, recipient))
      return SubmitResult::missing_context;
  } else {
    if (b.default_context(context) != context) return SubmitResult::unavailable;
    // Native UI passes true for the player's victory on BOTH physical sides.
    b.resolution_context(context, war, outcome == NativeOutcome::victory);
  }
  if (Load<void *>(context, 0x330) == nullptr) {
    b.destroy_context(context); return SubmitResult::missing_context;
  }
  if (!b.validate_context(context, nullptr)) {
    b.destroy_context(context); return SubmitResult::invalid;
  }
  SendStorage command_storage;
  void *command = command_storage.bytes.data();
  const auto constructed = b.construct_send_command(command, context);
  const bool valid = constructed == command &&
      Load<std::uintptr_t>(command, 0) == b.send_primary_vtable &&
      Load<std::uintptr_t>(command, 0x18) == b.send_secondary_vtable;
  CommandSubmitResult sent = CommandSubmitResult::unavailable;
  if (valid) sent = SubmitCommandCopy(b.commands, command, 0x0E);
  if (constructed == command)
    b.destroy_context(static_cast<std::byte *>(command) + 0x20);
  b.destroy_context(context);
  if (!valid) return SubmitResult::unavailable;
  if (sent == CommandSubmitResult::submitted) return SubmitResult::submitted;
  if (sent == CommandSubmitResult::rejected) return SubmitResult::rejected;
  return SubmitResult::unavailable;
}
} // namespace

DiplomacyBindings BindDiplomacyImage(std::uintptr_t image_base,
                                    std::string_view sha256) noexcept {
  DiplomacyBindings b;
  if (image_base == 0 || sha256 != kExecutableSha256) return b;
  b.enabled = true; b.core = BindCoreImage(image_base, sha256);
  b.commands = BindCommandImage(image_base, sha256);
  b.played_character_id = reinterpret_cast<const std::int32_t *>(
      image_base + kPlayedCharacterIdRva);
  b.interaction_database = reinterpret_cast<GetInteractionDatabase>(image_base + kInteractionDatabaseRva);
  b.default_context = reinterpret_cast<DefaultInteractionContext>(image_base + kDefaultInteractionContextRva);
  b.construct_context = reinterpret_cast<ConstructInteractionContext>(image_base + kConstructInteractionContextRva);
  b.resolution_context = reinterpret_cast<ConstructWarResolutionContext>(image_base + kWarResolutionContextRva);
  b.destroy_context = reinterpret_cast<DestroyInteractionContext>(image_base + kDestroyInteractionContextRva);
  b.validate_context = reinterpret_cast<ValidateInteractionContext>(image_base + kValidateInteractionContextRva);
  b.answer_score = reinterpret_cast<ReadInteractionAnswerScore>(image_base + kInteractionAnswerScoreRva);
  b.evaluate_trigger = reinterpret_cast<EvaluateInteractionTrigger>(image_base + 0x372DF30);
  b.construct_send_command = reinterpret_cast<ConstructSendInteractionCommand>(image_base + kSendInteractionCommandRva);
  b.contains_participant = reinterpret_cast<ContainsWarParticipant>(image_base + 0x2494B60);
  b.war_score = reinterpret_cast<GetWarScore>(image_base + 0x249AC40);
  b.imprisonment_score = reinterpret_cast<GetWarScore>(image_base + 0x2C0C310);
  b.battle_base_score = reinterpret_cast<GetWarScore>(image_base + 0x2C0C3B0);
  b.battle_side_score = reinterpret_cast<GetWarScoreSide>(image_base + 0x2C0D000);
  b.occupation_score = reinterpret_cast<GetWarScoreOccupation>(image_base + 0x2C0DDB0);
  b.ticking_score = reinterpret_cast<GetWarScoreTicking>(image_base + 0x2C0EE70);
  b.send_primary_vtable = image_base + 0x448BCE0;
  b.send_secondary_vtable = image_base + 0x448BCB0;
  b.auto_accept_trigger_offset = 0x2290;
  b.auto_accept_scalar_offset = 0x2718;
  return b;
}

void *ResolveDiplomacyWar(const CoreBindings &core, std::int32_t id) noexcept {
  WorldBindings world;
  world.enabled = core.enabled; world.game_state_slot = core.game_state_slot;
  return ResolveWar(world, id);
}

game::ReadWarTerminationOptionsResult ReadWarTerminationOptions(
    const DiplomacyBindings &b, std::int32_t id,
    game::WarTerminationOptionsSnapshot &out) noexcept {
  out = {};
  using Result = game::ReadWarTerminationOptionsResult;
  if (!QueryReady(b)) return Result::unavailable;
  CoreSnapshotPrefix frame;
  if (!ReadCoreSnapshot(b.core, frame)) return Result::unavailable;
  if (!frame.clock.paused) return Result::requires_paused;
  if (!frame.has_played_character || !frame.played_character_alive)
    return Result::no_played_character;
  if (*b.played_character_id != frame.played_character_id)
    return Result::unavailable;
  void *war = ResolveDiplomacyWar(b.core, id);
  if (!war) return Result::war_not_found;
  const bool attacker = b.contains_participant(
      static_cast<std::byte *>(war) + 0x20, frame.played_character_id);
  const bool defender = b.contains_participant(
      static_cast<std::byte *>(war) + 0x80, frame.played_character_id);
  if (!attacker && !defender) return Result::player_not_participant;
  if (attacker == defender) return Result::unavailable;
  game::WarTerminationOptionsSnapshot value;
  value.war_id = id;
  value.player_side = attacker ? game::PlayerWarSide::attacker
                               : game::PlayerWarSide::defender;
  value.player_is_primary_war_leader =
      Load<std::int32_t>(war, attacker ? 0x288 : 0x28C) == frame.played_character_id;
  const auto score = b.war_score(war, nullptr);
  if (score < -100 || score > 100) return Result::unavailable;
  value.absolute_war_scores_observable = true;
  value.attacker_war_score = score; value.defender_war_score = -score;
  value.player_relative_war_score = attacker ? score : -score;
  const auto duration = static_cast<std::int64_t>(frame.clock.date_raw) -
                        Load<std::int32_t>(war, 0xE0);
  if (duration >= 0 && duration / 24 <= std::numeric_limits<std::int32_t>::max()) {
    value.war_duration_days_observable = true;
    value.war_duration_days = static_cast<std::int32_t>(duration / 24);
  }
  ReadBreakdown(b, war, value.war_score_breakdown);
  value.surrender.outcome = attacker ? "attacker_defeat" : "attacker_victory";
  value.victory.outcome = attacker ? "attacker_victory" : "attacker_defeat";
  value.white_peace.outcome = "white_peace";
  void *cb = Load<void *>(war, 0x100);
  value.active_casus_belli_observable = true;
  value.active_casus_belli_present = cb != nullptr;
  if (cb != nullptr) {
    const auto index = Load<std::int32_t>(cb, 0x10);
    if (index >= 0 && index < 10'000 && ReadCbKey(cb, value.active_casus_belli_key)) {
      value.active_casus_belli_identity_observable = true;
      value.active_casus_belli_database_index = index;
    }
    value.white_peace_permission_observable = true;
    value.cb_allows_white_peace =
        (Load<std::uint32_t>(cb, kCasusBelliFlagsOffset) & (1U << 7U)) != 0;
  }
  if (value.player_is_primary_war_leader) {
    if (!EvaluateOption(b, war, false, value.surrender) ||
        !EvaluateOption(b, war, true, value.victory)) return Result::unavailable;
    if (value.cb_allows_white_peace) {
      ContextStorage storage;
      void *context = storage.bytes.data();
      const auto opponent = Load<std::int32_t>(war, attacker ? 0x28C : 0x288);
      if (!WhitePeaceContext(b, context, frame.played_character_id, opponent))
        return Result::unavailable;
      value.white_peace.context_constructed = Load<void *>(context, 0x330) != nullptr;
      if (value.white_peace.context_constructed) {
        value.white_peace.native_validator_observable = true;
        value.white_peace.native_validator_passed = b.validate_context(context, nullptr);
        ReadAcceptance(b, context, value.white_peace);
      }
      b.destroy_context(context);
    }
  }
  out = std::move(value); return Result::available;
}

game::EnforceDemandsResult SubmitEnforceDemands(const DiplomacyBindings &b,
                                               std::int32_t id) noexcept {
  using R = game::EnforceDemandsResult;
  switch (Submit(b, id, NativeOutcome::victory)) {
  case SubmitResult::submitted: return R::submitted;
  case SubmitResult::no_player: return R::no_played_character;
  case SubmitResult::missing_war: return R::war_not_found;
  case SubmitResult::not_participant: return R::player_not_participant;
  case SubmitResult::not_leader: return R::player_not_war_leader;
  case SubmitResult::invalid: return R::validation_failed;
  default: return R::unavailable;
  }
}
game::SurrenderWarResult SubmitSurrenderWar(const DiplomacyBindings &b,
                                           std::int32_t id) noexcept {
  using R = game::SurrenderWarResult;
  switch (Submit(b, id, NativeOutcome::surrender)) {
  case SubmitResult::submitted: return R::submitted;
  case SubmitResult::rejected: return R::submission_failed;
  case SubmitResult::paused_required: return R::requires_paused;
  case SubmitResult::no_player: return R::no_played_character;
  case SubmitResult::missing_war: return R::war_not_found;
  case SubmitResult::not_participant: return R::player_not_participant;
  case SubmitResult::not_leader: return R::player_not_war_leader;
  case SubmitResult::missing_context: return R::context_unavailable;
  case SubmitResult::invalid: return R::validation_failed;
  default: return R::unavailable;
  }
}
game::OfferWhitePeaceResult SubmitOfferWhitePeace(const DiplomacyBindings &b,
                                                 std::int32_t id) noexcept {
  using R = game::OfferWhitePeaceResult;
  switch (Submit(b, id, NativeOutcome::white_peace)) {
  case SubmitResult::submitted: return R::submitted;
  case SubmitResult::rejected: return R::submission_failed;
  case SubmitResult::paused_required: return R::requires_paused;
  case SubmitResult::no_player: return R::no_played_character;
  case SubmitResult::missing_war: return R::war_not_found;
  case SubmitResult::not_participant: return R::player_not_participant;
  case SubmitResult::not_leader: return R::player_not_war_leader;
  case SubmitResult::missing_cb: return R::casus_belli_unavailable;
  case SubmitResult::white_peace_forbidden: return R::white_peace_not_allowed;
  case SubmitResult::missing_context: return R::context_unavailable;
  case SubmitResult::invalid: return R::validation_failed;
  default: return R::unavailable;
  }
}
} // namespace xar::ck3_12002
