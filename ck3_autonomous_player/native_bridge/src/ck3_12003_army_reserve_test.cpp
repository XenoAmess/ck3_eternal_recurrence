#include "xar_bridge/ck3_12003_army_reserve.hpp"
#include "xar_bridge/ck3_12003_default_raise_mailbox.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
using namespace xar::ck3_12003;
using xar::ck3_12002::PlayerDefaultRaiseObservationV1;
void Require(bool value,const char *message) {
  if (!value) throw std::runtime_error(message);
}
struct Fixture {
  std::array<std::byte,0x40> actor{};
  xar::game::Snapshot snapshot{};
  PlayerArmyReserveBindingsV1 bindings{};
  xar::ck3_12002::MilitaryWorldAccess world{};
  void *composition = nullptr;
  bool initialized = false;
  std::int32_t count = 0;
  int constructors = 0,initializers = 0,reads = 0,destructors = 0;
};
Fixture *active = nullptr;
bool Snapshot(void *context,xar::game::Snapshot &value) noexcept {
  value = static_cast<Fixture *>(context)->snapshot;
  return true;
}
void *Actor(void *context,std::int32_t id) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  return id == 29829 ? f.actor.data() : nullptr;
}
void *Construct(void *composition) {
  Require(reinterpret_cast<std::uintptr_t>(composition)%8 == 0,
          "native ArmyComposition storage aligned");
  const auto *bytes = static_cast<const std::byte *>(composition);
  for (std::size_t i = 0;i<0xB8;++i)
    Require(bytes[i] == std::byte{0},"complete native storage zero before ctor");
  Require(composition != active->actor.data(),"constructor receiver is local composition");
  active->composition = composition;
  active->initialized = false;
  ++active->constructors;
  return composition;
}
void Initialize(void *composition,void *character) {
  Require(composition == active->composition && character == active->actor.data(),
          "owner initializer receives composition and exact current Character");
  const std::int32_t full_id = 29829;
  std::memcpy(static_cast<std::byte *>(composition)+0x90,&full_id,sizeof(full_id));
  active->initialized = true;
  ++active->initializers;
}
std::int32_t Count(void *composition) {
  Require(composition == active->composition && active->initialized &&
              composition != active->actor.data(),
          "complete native aggregate receives initialized composition, not Character");
  ++active->reads;
  return active->count;
}
void Destroy(void *composition) {
  Require(composition == active->composition && active->initialized,
          "non-deleting cleanup receives initialized local composition");
  ++active->destructors;
  active->composition = nullptr;
  active->initialized = false;
}
void Prepare(Fixture &f,PlayerDefaultRaiseObservationV1 &output) {
  active = &f;
  const std::int32_t actor_id = 29829;
  std::memcpy(f.actor.data()+0x18,&actor_id,sizeof(actor_id));
  f.snapshot.paused = true;
  f.snapshot.map_ready = true;
  f.snapshot.has_played_character = true;
  f.snapshot.played_character_alive = true;
  f.snapshot.played_character_id = actor_id;
  f.snapshot.date_raw = 53238336;
  xar::game::ArmySnapshot raised{};
  raised.army_id = 83886367;
  raised.owner_character_id = actor_id;
  raised.controllable = true;
  f.snapshot.player_armies.push_back(raised);
  f.bindings = {true,Construct,Initialize,Count,Destroy};
  f.world.context = &f;
  f.world.read_snapshot = Snapshot;
  f.world.resolve_character = Actor;
  // The old final raise legality observation is retained independently.
  // These are caller-owned fixture values, not a repeated raise validation.
  output.status = xar::ck3_12002::PrewarDefaultMusterStatusV1::available;
  output.actor.character_id = actor_id;
  output.actor.default_raise_province_id = 2610;
  output.actor.native_default_raise_legal = false;
  output.actor.failure = "none";
  output.default_raise_legality_ready = true;
  output.date_raw = f.snapshot.date_raw;
}
} // namespace

int main(int argc,char **argv) {
  try {
    Require(argc==2,"native reserve fixture output path required");
    const std::uintptr_t base = 0x140000000ULL;
    const auto bound = BindPlayerArmyReserveImageV1(base,kExecutableSha256);
    Require(bound.enabled &&
        reinterpret_cast<std::uintptr_t>(bound.construct_empty)==base+0xC6D5B0 &&
        reinterpret_cast<std::uintptr_t>(bound.initialize_owner)==base+0x25A7120 &&
        reinterpret_cast<std::uintptr_t>(bound.count_all_unraised)==base+0x25A6790 &&
        reinterpret_cast<std::uintptr_t>(bound.destroy_contents)==base+0xB03250 &&
        !BindPlayerArmyReserveImageV1(base,"wrong-exact-build").enabled,
        "four exact .3 callbacks match sealed native ABI, no other-build binding");
    Fixture f;
    PlayerDefaultRaiseObservationV1 output{};
    Prepare(f,output);
    const auto before = f.snapshot;
    Require(ReadPlayerUnraisedTroopsV1(f.bindings,f.world,output) &&
        output.unraised_troops_ready && output.unraised_soldiers==0 &&
        output.actor.native_default_raise_legal==false &&
        output.default_raise_legality_ready && f.destructors==1,
        "native zero is available and released independently from raise legality");
    const auto zero = SerializePlayerDefaultRaiseV1(output,1,11,before.date_raw);
    f.count = 1373;
    Require(ReadPlayerUnraisedTroopsV1(f.bindings,f.world,output) &&
        output.unraised_troops_ready && output.unraised_soldiers==1373 &&
        f.constructors==2 && f.initializers==2 && f.reads==2 && f.destructors==2 &&
        f.snapshot==before,
        "positive native integer aggregate survives production reader and cleanup");
    const auto positive = SerializePlayerDefaultRaiseV1(output,2,11,before.date_raw);
    f.bindings.enabled = false;
    Require(!ReadPlayerUnraisedTroopsV1(f.bindings,f.world,output) &&
        !output.unraised_troops_ready && !output.unraised_soldiers.has_value() &&
        output.unraised_troops_failure=="reserve_bindings_unavailable" &&
        f.constructors==2 && f.destructors==2,
        "unreadable binding resets prior result to typed unavailable, not zero");
    std::ofstream file(argv[1],std::ios::binary);
    file << "{\"zero\":" << zero << ",\"positive\":" << positive << "}\n";
    Require(static_cast<bool>(file),"native reserve wire fixture written");
    std::cout << "PASS: 4 new complete-unraised producer/wire cases\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
