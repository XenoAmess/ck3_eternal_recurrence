#include "xar_bridge/ck3_12004_player_heir_candidate_v1.hpp"
#include "xar_bridge/ck3_12004_family_break_penalty.hpp"

#include <array>
#include <cstdio>
#include <cstring>
#include <limits>
#include <memory>
#include <stdexcept>

namespace n = xar::ck3_12004;
namespace h = n::player_heir_candidate_v1;
namespace fv = xar::ck3_12002::family_value;
namespace { int unused_break_binder_calls = 0; }
// Link-only fixture seam for an unrelated, unused builder in family.cpp.
// The real used BindFamilyValuesImage and ReadCharacterLineage are linked.
// This stub is NEVER a production source or an admissible native binding.
namespace xar::ck3_12004 {
ck3_12002::family_break_penalty::Bindings BindFamilyBreakPenaltyImage(
    std::uintptr_t, std::string_view) noexcept {
  ++unused_break_binder_calls;
  return {};
}
}
namespace {
void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template<class T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  Check(offset + sizeof(value) <= N, "fixture write out of range");
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}
enum class Mutation {
  none, date_in_getter, actor_replaced, candidate_replaced,
  candidate_tag, candidate_death, candidate_lineage, roots,
  actor_death, lineage_becomes_unavailable
};
struct Fixture;
Fixture *active = nullptr;
void *LocalPlayer(void *);
const void *Getter(const void *);
bool Main(void *) noexcept;

struct Fixture {
  // Sign bits deliberately set: complete32bit IDs must not be narrowed or
  // mistaken for the -1 sentinel merely because signed representation is <0.
  static constexpr std::int32_t actor_id = static_cast<std::int32_t>(0x81000001U);
  static constexpr std::int32_t heir_id = static_cast<std::int32_t>(0x92000002U);
  static constexpr std::int32_t house_id = static_cast<std::int32_t>(0xE1000001U);
  static constexpr std::int32_t dynasty_id = static_cast<std::int32_t>(0xF1000001U);
  std::array<std::byte, 0x220> actor{}, heir{}, replacement{};
  std::array<std::byte, 0xA8> game{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F4> players{};
  std::array<std::byte, 0x78> player{};
  std::array<std::byte, 0x22360> data{};
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{};
  std::array<std::byte, 0x40> house{};
  std::array<std::byte, 0x20> dynasty{};
  std::array<std::byte, 0x30> char_store{}, other_store{}, house_store{}, dynasty_store{};
  std::array<std::byte, 0x40> char_slots{}, house_slots{}, dynasty_slots{};
  void *game_pointer = game.data(), *jomini_pointer = jomini.data();
  void *char_pointer = char_store.data(), *house_pointer = house_store.data();
  void *dynasty_pointer = dynasty_store.data();
  void *house_fallback = nullptr, *dynasty_fallback = nullptr;
  const void *returned = heir.data();
  h::Bindings b{};
  bool main = true, throw_getter = false;
  int getter_calls = 0, core_calls = 0;
  Mutation mutation = Mutation::none;

  Fixture() {
    active = this;
    for (auto *store : {&char_store, &house_store, &dynasty_store})
      Put(*store, 0x2C, std::int32_t{4});
    Put(char_store, 0x20, static_cast<void *>(char_slots.data()));
    Put(house_store, 0x20, static_cast<void *>(house_slots.data()));
    Put(dynasty_store, 0x20, static_cast<void *>(dynasty_slots.data()));
    other_store = char_store;
    Put(char_slots, 0x18, static_cast<void *>(actor.data()));
    Put(char_slots, 0x28, static_cast<void *>(heir.data()));
    Put(house_slots, 0x18, static_cast<void *>(house.data()));
    Put(dynasty_slots, 0x18, static_cast<void *>(dynasty.data()));
    Put(actor, n::kCharacterFullIdOffset, actor_id);
    Put(heir, n::kCharacterFullIdOffset, heir_id);
    for (auto *character : {&actor, &heir})
      Put(*character, 0x1C, std::uint32_t{0x43686172});
    Put(heir, fv::kCharacterHouseOffset, house_id);
    Put(house, 0x10, house_id);
    Put(house, fv::kHouseDynastyOffset, dynasty_id);
    Put(dynasty, 0x10, dynasty_id);
    // Poison unrelated CharacterValue inputs: narrow lineage must still work.
    Put(heir, fv::kCharacterSexSelectorOffset, std::uint8_t{0xFF});
    Put(game, n::kGameStateDateOffset, std::int32_t{53186880});
    Put(game, n::kGameStateSpeedOffset, std::int32_t{2});
    Put(game, n::kGameStateDataOffset, static_cast<void *>(data.data()));
    Put(jomini, n::kJominiPlayersOffset, static_cast<void *>(players.data()));
    Put(jomini, n::kJominiPausedOffset, std::uint8_t{1});
    Put(players, n::kPlayersLocalPlayerIdOffset, std::int32_t{7});
    Put(player, n::kPlayerIdOffset, std::int32_t{7});
    entries[0] = entry.data();
    Put(data, n::kPlayerCharacterManagerOffset + n::kPlayerManagerEntriesOffset,
        static_cast<void *>(entries.data()));
    Put(data, n::kPlayerCharacterManagerOffset + n::kPlayerManagerCountOffset,
        std::int32_t{1});
    Put(entry, n::kPlayerEntryLocalPlayerIdOffset, std::int32_t{7});
    Put(entry, n::kPlayerEntryCharacterIdOffset, actor_id);
    b.enabled = b.offline_fixture = true;
    b.executable_sha256 = n::kExecutableSha256;
    b.core.enabled = true;
    b.core.game_state_slot = &game_pointer;
    b.core.jomini_state_slot = &jomini_pointer;
    b.core.character_storage_slot = &char_pointer;
    b.core.get_local_player = &LocalPlayer;
    b.family.enabled = true;
    b.family.core = b.core;
    b.family.house_store = &house_pointer;
    b.family.house_fallback = &house_fallback;
    b.family.dynasty_store = &dynasty_pointer;
    b.family.dynasty_fallback = &dynasty_fallback;
    b.get_player_heir = &Getter;
    b.on_application_main = &Main;
    b.thread_context = this;
  }
};

void *LocalPlayer(void *) {
  auto &f = *active;
  ++f.core_calls;
  if (f.core_calls == 2) {
    switch (f.mutation) {
    case Mutation::actor_replaced:
      f.replacement = f.actor;
      Put(f.char_slots, 0x18, static_cast<void *>(f.replacement.data())); break;
    case Mutation::candidate_replaced:
      f.replacement = f.heir;
      Put(f.char_slots, 0x28, static_cast<void *>(f.replacement.data())); break;
    case Mutation::candidate_tag: Put(f.heir, 0x1C, std::uint32_t{0}); break;
    case Mutation::candidate_death:
      Put(f.heir, n::kCharacterDeathDataOffset, static_cast<void *>(f.house.data())); break;
    case Mutation::actor_death:
      Put(f.actor, n::kCharacterDeathDataOffset, static_cast<void *>(f.house.data())); break;
    case Mutation::candidate_lineage: Put(f.house, fv::kHouseDynastyOffset, std::int32_t{-1}); break;
    case Mutation::lineage_becomes_unavailable: Put(f.dynasty, 0x10, std::int32_t{123}); break;
    case Mutation::roots: f.char_pointer = f.other_store.data(); break;
    default: break;
    }
  }
  return f.player.data();
}
const void *Getter(const void *actor) {
  auto &f = *active;
  ++f.getter_calls;
  Check(actor == f.actor.data(), "original actor receiver must be supplied");
  if (f.throw_getter) throw std::runtime_error("synthetic getter failure");
  if (f.mutation == Mutation::date_in_getter)
    Put(f.game, n::kGameStateDateOffset, std::int32_t{53186881});
  return f.returned;
}
bool Main(void *context) noexcept { return static_cast<Fixture *>(context)->main; }

int cases = 0;
template<class F>
void Case(F test) {
  auto fixture = std::make_unique<Fixture>();
  test(*fixture);
  ++cases;
  active = nullptr;
}
void Unknown(Fixture &f, const char *reason, int calls) {
  const auto out = h::Read(f.b);
  Check(!out.available && !out.identity_and_frame_stable &&
        !out.lineage_available && out.candidate_character_id == -1,
        "unknown result must not publish candidate identity or lineage");
  Check(out.unavailable_reason == reason, "wrong diagnostic for unknown");
  Check(f.getter_calls == calls, "getter must run exactly once or be blocked before call");
}
void RunCases() {
  cases = 0;
  unused_break_binder_calls = 0;
  const auto bound = h::BindImage(0x140000000ULL, n::kExecutableSha256, Main);
#if defined(XAR_CK3_ENABLE_PLAYER_HEIR_CANDIDATE12004_V1)
  Check(bound.enabled && !bound.offline_fixture && bound.core.enabled &&
        bound.family.enabled &&
        reinterpret_cast<std::uintptr_t>(bound.get_player_heir) ==
            0x140000000ULL + h::kGetPlayerHeirRva,
        "opt-in exact binder must calculate exact getter address only");
#else
  Check(!bound.enabled && !bound.get_player_heir,
        "default build must leave native image binder disabled");
#endif
  Check(!h::BindImage(0, n::kExecutableSha256, Main).enabled &&
        !h::BindImage(0x140000000ULL, "wrong-build", Main).enabled &&
        !h::BindImage(0x140000000ULL, n::kExecutableSha256, nullptr).enabled &&
        !h::BindImage((std::numeric_limits<std::uintptr_t>::max)(),
                     n::kExecutableSha256, Main).enabled,
        "binder must reject missing/wrong/overflow inputs");
  ++cases;
  Case([](Fixture &f) {
    const auto out = h::Read(f.b);
    Check(out.available && out.getter_observed && out.candidate_present &&
          out.candidate_alive && out.identity_and_frame_stable && out.source_fixture &&
          !out.original_getter_source_bound && out.lineage_available &&
          out.actor_character_id == Fixture::actor_id &&
          out.candidate_character_id == Fixture::heir_id &&
          out.candidate_lineage.house_id == Fixture::house_id &&
          out.candidate_lineage.dynasty_id == Fixture::dynasty_id &&
          out.before.clock.date_raw == out.after.clock.date_raw &&
          f.getter_calls == 1 && f.core_calls == 2,
          "full generation/sign-bit IDs and independent lineage observation");
  });
  Case([](Fixture &f) {
    f.returned = nullptr;
    const auto out = h::Read(f.b);
    Check(out.available && out.getter_observed && !out.candidate_present &&
          out.identity_and_frame_stable && out.candidate_character_id == -1 &&
          !out.lineage_available && f.getter_calls == 1,
          "observed null is distinct from unavailable and no backup assertion");
  });
  Case([](Fixture &f) {
    Put(f.heir, fv::kCharacterHouseOffset, std::int32_t{-1});
    const auto out = h::Read(f.b);
    Check(out.available && out.lineage_available && out.candidate_alive &&
          out.candidate_lineage == fv::Lineage{}, "known no house/dynasty remains known");
  });
  Case([](Fixture &f) {
    Put(f.house, fv::kHouseDynastyOffset, std::int32_t{-1});
    const auto out = h::Read(f.b);
    Check(out.available && out.lineage_available &&
          out.candidate_lineage.house_id == Fixture::house_id &&
          out.candidate_lineage.dynasty_id == -1, "known no dynasty differs from unavailable");
  });
  Case([](Fixture &f) {
    Put(f.dynasty, 0x10, std::int32_t{123});
    const auto out = h::Read(f.b);
    Check(out.available && out.candidate_alive && !out.lineage_available &&
          out.lineage_unavailable_reason == "dynasty_full_id_unavailable" &&
          out.candidate_lineage == fv::Lineage{}, "missing lineage does not create known-none");
  });
  Case([](Fixture &f) {
    Put(f.heir, n::kCharacterDeathDataOffset, static_cast<void *>(f.house.data()));
    const auto out = h::Read(f.b);
    Check(out.available && out.candidate_present && !out.candidate_alive &&
          out.identity_and_frame_stable, "actual dead return retained without granting qualification");
  });
  Case([](Fixture &f) { f.main = false; Unknown(f, "application_main_required", 0); });
  Case([](Fixture &f) {
    Put(f.jomini, n::kJominiPausedOffset, std::uint8_t{0});
    Unknown(f, "paused_living_local_actor_required", 0);
  });
  Case([](Fixture &f) {
    Put(f.actor, n::kCharacterDeathDataOffset, static_cast<void *>(f.house.data()));
    Unknown(f, "paused_living_local_actor_required", 0);
  });
  Case([](Fixture &f) {
    f.b.family.core.character_storage_slot = &f.house_pointer;
    Unknown(f, "player_heir_binding_unavailable", 0);
  });
  Case([](Fixture &f) { f.b.executable_sha256 = "old"; Unknown(f, "player_heir_binding_unavailable", 0); });
  Case([](Fixture &f) { f.b.get_player_heir = nullptr; Unknown(f, "player_heir_binding_unavailable", 0); });
  Case([](Fixture &f) { f.returned = f.actor.data(); Unknown(f, "candidate_identity_unavailable", 1); });
  Case([](Fixture &f) {
    Put(f.heir, n::kCharacterFullIdOffset, std::int32_t{-1});
    Unknown(f, "candidate_identity_unavailable", 1);
  });
  Case([](Fixture &f) {
    Put(f.heir, 0x1C, std::uint32_t{0});
    Unknown(f, "candidate_identity_unavailable", 1);
  });
  Case([](Fixture &f) {
    f.replacement = f.heir;
    Put(f.char_slots, 0x28, static_cast<void *>(f.replacement.data()));
    Unknown(f, "candidate_identity_unavailable", 1);
  });
  Case([](Fixture &f) { f.throw_getter = true; Unknown(f, "player_heir_native_call_failed", 1); });
  Case([](Fixture &f) { f.mutation = Mutation::date_in_getter; Unknown(f, "player_heir_frame_or_roots_changed", 1); });
  Case([](Fixture &f) { f.mutation = Mutation::actor_replaced; Unknown(f, "actor_identity_or_liveness_changed", 1); });
  Case([](Fixture &f) { f.mutation = Mutation::candidate_replaced; Unknown(f, "candidate_identity_or_liveness_changed", 1); });
  Case([](Fixture &f) { f.mutation = Mutation::candidate_tag; Unknown(f, "candidate_identity_or_liveness_changed", 1); });
  Case([](Fixture &f) { f.mutation = Mutation::candidate_death; Unknown(f, "candidate_identity_or_liveness_changed", 1); });
  Case([](Fixture &f) { f.mutation = Mutation::candidate_lineage; Unknown(f, "candidate_lineage_changed", 1); });
  Case([](Fixture &f) { f.mutation = Mutation::lineage_becomes_unavailable; Unknown(f, "candidate_lineage_changed", 1); });
  Case([](Fixture &f) { f.mutation = Mutation::actor_death; Unknown(f, "player_heir_frame_or_roots_changed", 1); });
  Case([](Fixture &f) { f.mutation = Mutation::roots; Unknown(f, "player_heir_frame_or_roots_changed", 1); });
#if defined(_MSC_VER)
  Case([](Fixture &f) {
    f.returned = reinterpret_cast<const void *>(1);
    Unknown(f, "player_heir_memory_access_failed", 1);
  });
#endif
  Check(unused_break_binder_calls == 0,
        "unrelated fixture-only break binder must never be called");
  ++cases;
}
} // namespace

#if defined(_WIN32)
#define FIXTURE_EXPORT extern "C" __declspec(dllexport)
#else
#define FIXTURE_EXPORT extern "C"
#endif
FIXTURE_EXPORT int RunPlayerHeirCandidateFixtures(char *output,
                                                 std::size_t capacity) noexcept {
  try {
    RunCases();
    std::snprintf(output, capacity,
        "{\"status\":\"PASS\",\"synthetic_cases\":%d,\"getter_calls_per_read_max\":1,"
        "\"unused_break_binder_calls\":%d,\"Game_RPC_process_access\":0,"
        "\"actual_H_credit\":false}", cases, unused_break_binder_calls);
    return 0;
  } catch (const std::exception &e) {
    std::snprintf(output, capacity, "FAIL after%d cases: %s", cases, e.what());
    return 1;
  }
}
