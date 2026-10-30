#include "xar_bridge/ck3_12004_campaign_root_faction.hpp"
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12004;
template<class T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
int checks = 0;
void Check(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
void *current_player = nullptr, *current_vassal = nullptr, *current_title = nullptr;
bool direct = true;
void *LocalPlayer(void *jomini) { return *static_cast<void **>(jomini); }
void *Liege(void *character) { return character == current_vassal && direct ? current_player : nullptr; }
void *Title(void *character) { return character == current_vassal ? current_title : nullptr; }
bool Main(void *) noexcept { return true; }
struct World {
  std::array<std::byte, 0xa8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1f8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> data = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xe0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> store{}, title_store{};
  std::array<std::byte, 8 * 0x10> slots{}, title_slots{};
  std::array<std::byte, 0x1d8> actor{}, vassal{};
  std::array<std::byte, 0x20> title{};
  void *state_pointer = state.data(), *jomini_pointer = jomini.data();
  void *store_pointer = store.data(), *title_store_pointer = title_store.data();
  void *character_fallback = nullptr, *title_fallback = nullptr;
  xar::game::CampaignRootFrameV1 frame{};
  CampaignRootFactionBindings12004 b{};
  xar::ck3_12002::CampaignRootAccessV1 access{};
  int captures = 0;
  bool drift = false;
  World(std::int32_t actor_id, std::int32_t vassal_id, int vassal_slot = -1) {
    const auto actor_slot = static_cast<std::uint32_t>(actor_id) & 0xffffffU;
    auto selected_slot = vassal_slot < 0 ? static_cast<std::uint32_t>(vassal_id) & 0xffffffU : static_cast<std::uint32_t>(vassal_slot);
    Check(actor_slot < 8 && selected_slot < 8 && actor_slot != selected_slot, "fixture slots");
    current_player = actor.data(); current_vassal = vassal.data(); current_title = title.data(); direct = true;
    Put(state.data(), 8, std::int32_t{53175816}); Put(state.data(), 0x70, std::int32_t{2});
    Put(state.data(), 0xa0, data.data()); Put(jomini.data(), 0, local.data());
    Put(jomini.data(), 0x18, players.data()); jomini[0x20] = std::byte{1};
    Put(players.data(), 0x1f0, std::int32_t{7}); Put(local.data(), 0x70, std::int32_t{7});
    Put(data.data(), 0x222e8 + 0x58, entries.data()); Put(data.data(), 0x222e8 + 0x64, std::int32_t{1});
    Put(entry.data(), 0xd8, std::int32_t{7}); Put(entry.data(), 0xb0, actor_id);
    Put(store.data(), 0x20, slots.data()); Put(store.data(), 0x2c, std::int32_t{8});
    Put(actor.data(), 0x18, actor_id); Put(vassal.data(), 0x18, vassal_id);
    Put(slots.data(), actor_slot * 0x10 + 8, actor.data()); Put(slots.data(), selected_slot * 0x10 + 8, vassal.data());
    Put(title_store.data(), 0x20, title_slots.data()); Put(title_store.data(), 0x2c, std::int32_t{8});
    Put(title.data(), 0x10, std::int32_t{0x02000003}); Put(title_slots.data(), 3 * 0x10 + 8, title.data());
    b.enabled = true; b.core = {true, &state_pointer, &jomini_pointer, &store_pointer, &LocalPlayer};
    b.character_fallback_slot = &character_fallback; b.title_storage_slot = &title_store_pointer;
    b.title_fallback_slot = &title_fallback; b.immediate_liege = &Liege; b.primary_title = &Title;
    frame.snapshot_revision = 5; frame.date_raw = 53175816; frame.paused = true; frame.map_ready = true;
    frame.has_played_character = true; frame.played_character_id = actor_id; frame.played_character_alive = true;
    access.context = this; access.is_main_thread = &Main; access.capture_frame = &Capture;
  }
  static bool Capture(void *context, xar::game::CampaignRootFrameV1 &out) noexcept {
    auto &world = *static_cast<World *>(context); out = world.frame;
    if (++world.captures > 1 && world.drift) ++out.snapshot_revision;
    return true;
  }
  bool Read(xar::game::CampaignRootContextV1 &out) {
    xar::ck3_12002::CampaignRootContextRequestV1 request{}; request.expected_snapshot_revision = 5;
    return ReadCampaignRootFaction12004(b, access, request, out);
  }
};
int failures = 0;
void Scene(const char *name, std::int32_t actor, std::int32_t member, int mutation, bool ready, bool included, int slot = -1) {
  World world(actor, member, slot);
  if (mutation == 1) Put(world.vassal.data(), 0x1d0, world.title.data());
  if (mutation == 2) direct = false;
  if (mutation == 3) world.drift = true;
  if (mutation == 4) Put(world.title_slots.data(), 3 * 0x10 + 8, world.vassal.data());
  CoreSnapshotPrefix core{};
  Check(xar::ck3_12004::ReadCoreSnapshot(world.b.core, core), "actual core read unavailable");
  Check(core.has_played_character && core.played_character_id == actor, "actual core identity mismatch");
  Check(xar::ck3_12004::ResolveCoreCharacter(world.b.core, actor) == world.actor.data(), "actual core resolve mismatch");
  xar::game::CampaignRootContextV1 out{};
  const bool actual = world.Read(out);
  bool pass = actual == ready;
  if (actual) pass = pass && out.player_character_id == actor && out.readiness.direct_landed_vassals_ready &&
      out.direct_landed_vassal_character_ids == (included ? std::vector<std::int32_t>{member} : std::vector<std::int32_t>{});
  ++checks; if (!pass) ++failures;
  std::cout << name << " actor=" << actor << " member=" << member << " root=" << actual << " members=" << out.direct_landed_vassal_character_ids.size() << " " << (pass ? "PASS" : "FAIL") << '\n';
}
}
int main() {
  try {
    Scene("positive", 0x01000001, 0x02000002, 0, true, true);
    Scene("signed-member", 0x01000001, static_cast<std::int32_t>(0x80000002U), 0, true, true);
    Scene("zero-member", 0x01000001, 0, 0, true, true);
    Scene("signed-actor", static_cast<std::int32_t>(0x80000001U), 0x02000002, 0, true, true);
    Scene("zero-actor", 0, 0x02000002, 0, true, true);
    Scene("both-signed", static_cast<std::int32_t>(0x80000001U), static_cast<std::int32_t>(0x80000002U), 0, true, true);
    Scene("int32-min-member", 0x01000001, static_cast<std::int32_t>(0x80000000U), 0, true, true);
    Scene("wrong-slot", 0x01000001, 0x02000003, 0, true, false, 2);
    Scene("invalid-sentinel", 0x01000001, -1, 0, true, false, 2);
    Scene("dead", 0x01000001, 0x02000002, 1, true, false);
    Scene("other-liege", 0x01000001, 0x02000002, 2, true, false);
    Scene("changed-frame", 0x01000001, 0x02000002, 3, false, false);
    Scene("wrong-title-roundtrip", 0x01000001, 0x02000002, 4, false, false);
    std::cout << "checks=" << checks << " failures=" << failures << " scenes=13\n";
    return failures ? 1 : 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 2; }
}
