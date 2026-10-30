#include "xar_bridge/ck3_12002_sway_state.hpp"
#include "xar_bridge/ck3_12002_gift_opinion.hpp"
#include <bit>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>
#include <windows.h>

namespace {
using namespace xar::ck3_12002;
using namespace xar::bridge;
int checks = 0, failed = 0, opinion_calls = 0, fallback_calls = 0;
std::int32_t expected_actor = -1;
constexpr std::int32_t target_id = 0x03000002;
void *local_player = nullptr;
void Check(bool value, const char *what, std::int64_t actor) {
  ++checks;
  if (!value) { ++failed; std::cout << "FAIL actor=" << actor << " " << what << '\n'; }
}
template<class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template<class T> T Get(const void *object, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value)); return value;
}
void *Local(void *) { return local_player; }
std::int32_t Opinion(void *owner, void *toward) {
  ++opinion_calls;
  return Get<std::int32_t>(owner, 0x18) == target_id &&
      Get<std::int32_t>(toward, 0x18) == expected_actor ? -15 : 200;
}
struct World {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x23000);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x40> character_store{};
  std::array<std::array<std::byte, 0x1D8>, 2> characters{};
  void *slots = nullptr;
  std::array<std::byte, 0x58> scheme_store{};
  std::array<std::byte, 0x10> scheme_slots{};
  std::array<std::byte, 0x358> scheme{};
  std::array<void *, 1> blocks{scheme.data()};
  std::array<std::byte, 0xA60> type{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *store_ptr = character_store.data();
  SwayStateBindings12002 source{};
  explicit World(std::int32_t actor) {
    // Reserve the real 24-bit index extent, commit only the owned slot pages.
    // This covers -2/MAX without a 256MiB physical allocation or truncated IDs.
    slots = VirtualAlloc(nullptr, 0x10000000, MEM_RESERVE, PAGE_NOACCESS);
    if (!slots) throw std::runtime_error("reserve owned character slots");
    SYSTEM_INFO system{}; GetSystemInfo(&system);
    const std::array<std::int32_t, 2> ids{actor, target_id};
    for (std::size_t i = 0; i < ids.size(); ++i) {
      const auto slot = (static_cast<std::uint32_t>(ids[i]) & 0xFFFFFFU) * 16ULL + 8;
      const auto page = slot - slot % system.dwPageSize;
      if (!VirtualAlloc(static_cast<std::byte *>(slots) + page, system.dwPageSize,
          MEM_COMMIT, PAGE_READWRITE)) throw std::runtime_error("commit owned character slot");
      Put(characters[i].data(), 0x18, ids[i]);
      Put(slots, static_cast<std::size_t>(slot), characters[i].data());
    }
    local_player = local.data(); expected_actor = actor;
    Put(state.data(), 8, std::int32_t{53220000}); Put(state.data(), 0xA0, game.data());
    Put(jomini.data(), 0x18, players.data()); Put(jomini.data(), 0x20, std::uint8_t{1});
    Put(players.data(), 0x1F0, std::int32_t{0}); Put(local.data(), 0x70, std::int32_t{0});
    Put(game.data(), kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(game.data(), kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{0}); Put(entry.data(), 0xB0, actor);
    Put(character_store.data(), 0x20, slots); Put(character_store.data(), 0x2C, std::int32_t{0x1000000});
    source.enabled = true; source.module_base = 0x140000000;
    source.core = {true, &state_ptr, &jomini_ptr, &store_ptr, &Local}; source.opinion = &Opinion;
    Put(game.data(), source.manager_offset, source.module_base + source.manager_vtable_rva);
    Put(game.data(), source.manager_offset + 0x20, scheme_store.data());
    Put(scheme_store.data(), 0, source.module_base + source.storage_vtable_rva);
    Put(scheme_store.data(), 8, blocks.data()); Put(scheme_store.data(), 0x20, scheme_slots.data());
    Put(scheme_store.data(), 0x2C, std::int32_t{1}); Put(scheme_store.data(), 0x3C, std::int32_t{1});
    Put(scheme_slots.data(), 8, scheme.data());
    Put(scheme.data(), 0, source.module_base + source.instance_vtable_rva);
    Put(scheme.data(), 0x10, std::uint32_t{0}); Put(scheme.data(), 0x20, type.data());
    Put(scheme.data(), 0x2C, static_cast<std::uint32_t>(actor));
    Put(scheme.data(), 0x34, static_cast<std::uint32_t>(target_id));
    Put(scheme.data(), 0x78, std::int32_t{355}); Put(scheme.data(), 0x350, std::int32_t{365});
    Put(type.data(), 0, source.module_base + source.type_vtable_rva);
    std::memcpy(type.data() + 0x18, "sway", 5);
    Put(type.data(), 0x28, std::uint64_t{4}); Put(type.data(), 0x30, std::uint64_t{15});
    Put(type.data(), 0x38, std::uint32_t{0x4744624F}); Put(type.data(), 0xA4E, std::uint8_t{1});
  }
  ~World() { if (slots) VirtualFree(slots, 0, MEM_RELEASE); }
  World(const World &) = delete;
  World &operator=(const World &) = delete;
};
void Case(std::int32_t actor) {
  World world(actor); CoreSnapshotPrefix core{};
  Check(ReadCoreSnapshot(world.source.core, core) && core.has_played_character &&
      core.played_character_id == actor, "real Core retains complete signed ID", actor);
  ActiveSchemeStateV1PrivateObservation out{};
  const bool read = ReadActiveSwayState12002(world.source, 42, out);
  Check(read && out.played_character_id == actor && out.row_count == 1,
      "real state reader available with owned row", actor);
  Check(read && out.rows[0].owner_character_id == actor,
      "raw uint32 owner projects to canonical signed actor", actor);
  Check(read && out.rows[0].scheme_instance_id == 0 && out.rows[0].progress.value == 355 &&
      out.rows[0].progress_goal.value == 365, "scheme zero/progress domains preserved", actor);
  opinion_calls = 0; std::int32_t opinion = 999;
  Check(ReadSwayTargetOpinion12002(world.source, actor, target_id, opinion) &&
      opinion == -15 && opinion_calls == 1, "real direct-opinion direction and signed actor", actor);
  Put(world.scheme.data(), 0x2C, static_cast<std::uint32_t>(actor) ^ 0x01000000U);
  Check(ReadActiveSwayState12002(world.source, 43, out) && out.row_count == 0,
      "same low24 different owner generation excluded", actor);
  Put(world.scheme.data(), 0x2C, static_cast<std::uint32_t>(actor));
  Put(world.characters[0].data(), 0x18, std::bit_cast<std::int32_t>(static_cast<std::uint32_t>(actor) ^ 0x01000000U));
  Check(!ReadActiveSwayState12002(world.source, 44, out),
      "same slot wrong complete character ID unavailable", actor);
  Put(world.characters[0].data(), 0x18, actor);
  for (const std::int64_t invalid : {-1LL, -2147483649LL, 2147483648LL, 4294967294LL}) {
    opinion = 999; opinion_calls = 0;
    Check(!ReadSwayTargetOpinion12002(world.source, invalid, target_id, opinion) &&
        opinion == 0 && opinion_calls == 0, "invalid public actor rejected before callback", invalid);
  }
  Check(!ReadActiveSwayState12002(world.source, 0, out), "zero epoch remains invalid", actor);
}
}
// Deliberate link seam: no production gift fallback is linked or credited.
namespace xar::ck3_12002 {
bool ReadCharacterOpinion12002(std::uintptr_t, const CoreBindings &, std::uint32_t,
    std::uint32_t, std::int32_t &) noexcept { ++fallback_calls; return false; }
}
int main() {
  try {
    for (const std::int32_t actor : {std::numeric_limits<std::int32_t>::min(),
        std::int32_t{-2147483647}, std::int32_t{-2}, std::int32_t{0}, std::int32_t{1},
        std::int32_t{0x03000001}, std::numeric_limits<std::int32_t>::max()}) Case(actor);
    Check(fallback_calls == 0, "gift fallback not invoked or validated", 0);
    std::cout << "CHECKS " << checks << " FAILED " << failed << " FallbackCalls " << fallback_calls << '\n';
    return failed == 0 ? 0 : 1;
  } catch (const std::exception &e) { std::cerr << "ERROR " << e.what() << '\n'; return 2; }
}
