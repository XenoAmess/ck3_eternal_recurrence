#include "xar_bridge/ck3_12002_diplomacy.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <span>
#include <vector>

namespace {
template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <class T> T Get(const void *object, std::size_t offset) {
  T result; std::memcpy(&result, static_cast<const std::byte *>(object)+offset, sizeof(result));
  return result;
}
void *local_player;
std::array<std::byte, 0x1020> database;
std::array<std::byte, 0x2720> interaction;
std::array<void *, 9> send_vtable{};
std::int32_t actor_id = 0x03000004;
bool fixture_attacker = true, validator = true, queue_accept = true;
bool selected_player_victory = false;
int destroyed_contexts = 0, queued = 0, clones = 0;
void *FixturePlayer(void *) { return local_player; }
void *Database() { return database.data(); }
void *Default(void *context) {
  std::memset(context, 0, 0x338); Put(context, 0, interaction.data()); return context;
}
void Resolution(void *context, void *, bool player_victory) {
  selected_player_victory = player_victory;
  Put(context, 0x330, interaction.data());
  Put(context, 0x2D8, actor_id);
}
void *Construct(void *context, void *definition, std::int32_t actor,
                 std::int32_t recipient, void *, bool special) {
  Default(context); Put(context, 0, definition);
  Put(context, 0x2D8, actor); Put(context, 0x2DC, recipient);
  if (special) Put(context, 0x330, interaction.data()); return context;
}
void DestroyContext(void *) { ++destroyed_contexts; }
bool Validate(void *, void *) { return validator; }
std::int64_t *Score(void *, std::int64_t *out) { *out = 1250000; return out; }
bool Contains(void *side, std::int32_t id) {
  return Get<std::int32_t>(side, 0) == id;
}
std::int32_t WarScore(void *, void *) { return 37; }
void **Clone(const void *source, void **out) {
  ++clones; auto *copy = new std::array<std::byte, 0x368>;
  std::memcpy(copy->data(), source, copy->size()); *out = copy->data(); return out;
}
bool Queue(void *, void **owned, std::uint32_t flags) {
  if (flags != 0x0E || *owned == nullptr) return false;
  ++queued; delete static_cast<std::array<std::byte, 0x368> *>(*owned);
  *owned = nullptr; return queue_accept;
}
void *Send(void *command, const void *context) {
  std::memset(command, 0, 0x368);
  Put(command, 0, send_vtable.data()); Put(command, 0x18, std::uintptr_t{0xAABB});
  std::memcpy(static_cast<std::byte *>(command)+0x20, context, 0x338);
  return command;
}
struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> record{};
  std::array<void *, 1> entries{record.data()};
  std::array<std::byte, 0x30> char_storage{}, war_storage{};
  std::array<std::byte, 0x80> char_slots{}, war_slots{};
  std::array<std::byte, 0x1D8> character{};
  std::array<std::byte, 0x360> war{};
  std::array<std::byte, 0x1550> cb{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *char_ptr=char_storage.data();
  xar::ck3_12002::DiplomacyBindings bindings;
  static constexpr std::int32_t war_id=0x02000003;
  Fixture() {
    using namespace xar::ck3_12002;
    Put(state.data(),8,std::int32_t{53175816}); Put(state.data(),0x70,std::int32_t{2});
    Put(state.data(),0xA0,data.data()); Put(jomini.data(),0x18,players.data());
    jomini[0x20]=std::byte{1}; Put(players.data(),0x1F0,std::int32_t{7});
    Put(player.data(),0x70,std::int32_t{7}); local_player=player.data();
    Put(data.data(),0x222E8+0x58,entries.data()); Put(data.data(),0x222E8+0x64,std::int32_t{1});
    Put(record.data(),0xD8,std::int32_t{7}); Put(record.data(),0xB0,actor_id);
    Put(char_storage.data(),0x20,char_slots.data()); Put(char_storage.data(),0x2C,std::int32_t{8});
    Put(char_slots.data(),4*0x10+8,character.data()); Put(character.data(),0x18,actor_id);
    Put(data.data(),0x2EBE0+0x20,war_storage.data());
    Put(war_storage.data(),0x20,war_slots.data()); Put(war_storage.data(),0x2C,std::int32_t{8});
    Put(war_slots.data(),3*0x10+8,war.data()); Put(war.data(),8,war_id);
    Put(war.data(),0xE0,std::int32_t{53171016}); Put(war.data(),0x100,cb.data());
    // Adjacent nonzero bytes must not become a false pointer-sized ended flag.
    war[0x359]=std::byte{0xAB};
    Put(cb.data(),0x10,std::int32_t{2}); std::memcpy(cb.data()+0x18,"claim_cb",8);
    Put(cb.data(),0x28,std::uint64_t{8}); Put(cb.data(),0x30,std::uint64_t{15});
    Put(cb.data(),0x1548,std::uint32_t{1U<<7U});
    Put(interaction.data(),0x38,std::uint32_t{0x4744624F});
    interaction[0x2718]=std::byte{1}; Put(database.data(),0x1018,interaction.data());
    send_vtable[8]=reinterpret_cast<void *>(&Clone);
    bindings.enabled=true;
    bindings.core={true,&state_ptr,&jomini_ptr,&char_ptr,&FixturePlayer};
    bindings.commands.enabled=true; bindings.commands.command_manager=this;
    bindings.commands.queue_owned_command=&Queue;
    bindings.played_character_id=&actor_id; bindings.interaction_database=&Database;
    bindings.default_context=&Default; bindings.construct_context=&Construct;
    bindings.resolution_context=&Resolution; bindings.destroy_context=&DestroyContext;
    bindings.validate_context=&Validate; bindings.answer_score=&Score;
    bindings.construct_send_command=&Send; bindings.contains_participant=&Contains;
    bindings.war_score=&WarScore;
    bindings.send_primary_vtable=reinterpret_cast<std::uintptr_t>(send_vtable.data());
    bindings.send_secondary_vtable=0xAABB;
    bindings.auto_accept_trigger_offset=0x2290;
    bindings.auto_accept_scalar_offset=0x2718;
    Side(true);
  }
  void Side(bool attacker) {
    fixture_attacker=attacker;
    Put(war.data(),0x20,attacker ? actor_id : std::int32_t{42});
    Put(war.data(),0x80,attacker ? std::int32_t{42} : actor_id);
    Put(war.data(),0x288,attacker ? actor_id : std::int32_t{42});
    Put(war.data(),0x28C,attacker ? std::int32_t{42} : actor_id);
  }
};
}
int main() {
  using namespace xar::ck3_12002;
  Fixture f;
  for (bool attacker : {true,false}) {
    f.Side(attacker);
    xar::game::WarTerminationOptionsSnapshot options;
    destroyed_contexts=0;
    if (ReadWarTerminationOptions(f.bindings,Fixture::war_id,options) !=
          xar::game::ReadWarTerminationOptionsResult::available ||
        options.player_relative_war_score != (attacker ? 37 : -37) ||
        !options.player_is_primary_war_leader || options.war_duration_days != 200 ||
        !options.victory.native_validator_passed ||
        !options.white_peace.auto_accept_observable || !options.white_peace.auto_accept ||
        !options.victory.ai_acceptance_observable || destroyed_contexts != 3) return 1;
    if (SubmitEnforceDemands(f.bindings,Fixture::war_id) !=
          xar::game::EnforceDemandsResult::submitted || !selected_player_victory) return 2;
    if (SubmitSurrenderWar(f.bindings,Fixture::war_id) !=
          xar::game::SurrenderWarResult::submitted || selected_player_victory) return 3;
    if (SubmitOfferWhitePeace(f.bindings,Fixture::war_id) !=
          xar::game::OfferWhitePeaceResult::submitted) return 4;
  }
  queue_accept=false;
  if (SubmitSurrenderWar(f.bindings,Fixture::war_id) !=
      xar::game::SurrenderWarResult::submission_failed) return 5;
  queue_accept=true; validator=false; int before=queued;
  if (SubmitEnforceDemands(f.bindings,Fixture::war_id) !=
      xar::game::EnforceDemandsResult::validation_failed || queued != before) return 6;
  validator=true; Put(f.cb.data(),0x1548,std::uint32_t{0});
  if (SubmitOfferWhitePeace(f.bindings,Fixture::war_id) !=
      xar::game::OfferWhitePeaceResult::white_peace_not_allowed) return 7;
  f.war[0x358]=std::byte{1};
  if (SubmitSurrenderWar(f.bindings,Fixture::war_id) !=
      xar::game::SurrenderWarResult::war_not_found) return 8;
  f.war[0x358]=std::byte{}; f.jomini[0x20]=std::byte{};
  if (SubmitSurrenderWar(f.bindings,Fixture::war_id) !=
      xar::game::SurrenderWarResult::requires_paused) return 9;
  f.jomini[0x20]=std::byte{1};
  if (SubmitSurrenderWar(f.bindings,0x03000003) !=
      xar::game::SurrenderWarResult::war_not_found) return 10;
  const auto bound=BindDiplomacyImage(0x140000000,kExecutableSha256);
  if (!bound.enabled || !bound.commands.enabled ||
      reinterpret_cast<std::uintptr_t>(bound.resolution_context) != 0x140CF57D0 ||
      reinterpret_cast<std::uintptr_t>(bound.played_character_id) != 0x1454DBC00 ||
      BindDiplomacyImage(0x140000000,"legacy").enabled) return 11;
  std::cout << "PASS 1.20 termination both-side polarity, query and command lifecycle fixtures\n";
}
