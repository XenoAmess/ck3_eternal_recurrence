#include <windows.h>
#include "xar_bridge/ck3_12002_battle.hpp"
#include "xar_bridge/ck3_12002_battle_journal.hpp"

#include <array>
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <string>
#include "xar_bridge/battle_terminal_transition_v1_mailbox.hpp"
#include <cstring>
#include <iostream>

namespace {
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
using namespace xar::ck3_12002;
using namespace xar::game;
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename T, std::size_t N>
void Put(Bytes<N> &o, std::size_t offset, T v) {
  std::memcpy(o.data() + offset, &v, sizeof(v));
}
template <typename T> T Get(void *o, std::size_t offset) {
  T v{};
  std::memcpy(&v, static_cast<std::byte *>(o) + offset, sizeof(v));
  return v;
}
struct Store {
  Bytes<0x38> storage{};
  Bytes<0x100> slots{};
  void *root = storage.data();
  Store() {
    Put(storage, 0x20, slots.data());
    Put<std::int32_t>(storage, 0x2C, 16);
  }
  void Set(std::int32_t id, void *p) {
    Put(slots, (id & 0xFFFFFF) * 0x10 + 8, p);
  }
};
struct Fixture {
  Bytes<0xA8> gs{}, js{};
  Bytes<0x158> game_data{};
  std::array<void *, 2587> province_rows{};
  void *g = gs.data(), *j = js.data();
  Bytes<0x720> combat{};
  Bytes<0x860> province{};
  Bytes<0x200> unit0{}, unit1{};
  Bytes<0x148> army0{}, army1{};
  Bytes<0x150> regiment0{}, regiment1{};
  Bytes<0xA20> type0{}, type1{};
  Bytes<0x210> char0{}, char1{};
  Bytes<0x210> land{};
  Bytes<0x48> rules{};
  Bytes<0xD8> result{};
  Bytes<0x60> entry0{}, entry1{};
  Bytes<0x18> hard{};
  Bytes<0x1C0> coordinator{};
  Bytes<0x98> parent{};
  Bytes<0x58> subunit{};
  Store combats, units, armies, regiments, characters, results, coordinators;
  std::array<std::int32_t, 1> aids{0x1000001}, dids{0x1000002},
      combat_ids{0x1000003}, member{0x1000001};
  std::array<void *, 1> parent_rows{parent.data()},
      subunit_rows{subunit.data()}, support{province.data()};
  std::int32_t minimum = 14;
  BattleBindings b{};
  Snapshot scope{};
  static Fixture *current;
  static void *ResolveProvince(void *ctx, std::int32_t id) {
    auto &f = *static_cast<Fixture *>(ctx);
    return id == 2586 ? f.province.data() : nullptr;
  }
  static void *Rules(void *owner) {
    Require(owner == current->char0.data(), "fixture owner-taking rules");
    return current->rules.data();
  }
  static std::int32_t Strength(void *) { return 31337; }
  static bool Hostile(void *a, void *d, bool) { return a != d; }
  static bool Retreat(void *c, void *, void *sink) {
    Require(!sink, "fixture retreat null sink");
    auto &f = *current;
    auto flag = Get<std::uint8_t>(static_cast<std::byte *>(c) + 0x20, 0xC0);
    auto early = Get<std::uint8_t>(static_cast<std::byte *>(c) + 0x20, 0xC1);
    auto days =
        (f.scope.date_raw - Get<std::int32_t>(f.result.data(), 0x2C)) / 24;
    return !flag && (early || days > f.minimum) &&
           Get<std::int32_t>(c, 0x6B0) < 2 &&
           (Get<std::uint32_t>(f.rules.data(), 0x40) & (1 << 10));
  }
  template <std::size_t N>
  static void Array(Bytes<N> &o, std::size_t off, void *data,
                    std::int32_t count) {
    Put(o, off, data);
    Put(o, off + 8, count);
    Put(o, off + 12, count);
  }
  Fixture() {
    current = this;
    scope.paused = true;
    scope.map_ready = true;
    scope.has_played_character = true;
    scope.played_character_id = 0x1000001;
    scope.date_raw = 0x029C55C0 + 15 * 24;
    Put(gs, 8, scope.date_raw);
    Put<std::uint32_t>(js, 0x20, 1);
    Put(gs, 0xA0, game_data.data());
    province_rows[2586] = province.data();
    Put(game_data, 0x140, province_rows.data());
    Put<std::int32_t>(game_data, 0x14C, 2587);
    b.enabled = true;
    b.game_state_slot = &g;
    b.jomini_state_slot = &j;
    b.combat_storage_slot = &combats.root;
    b.army_storage_slot = &units.root;
    b.army_internal_storage_slot = &armies.root;
    b.regiment_storage_slot = &regiments.root;
    b.character_storage_slot = &characters.root;
    b.battle_result_storage_slot = &results.root;
    b.battle_result_fallback_slot = &result_root;
    b.ai_war_coordinator_storage_slot = &coordinators.root;
    b.minimum_days_before_manual_retreat = &minimum;
    b.get_combat_side_strength = Strength;
    b.get_combat_regiment_strength = Strength;
    b.can_order_combat_retreat = Retreat;
    b.get_combat_retreat_rule_state = Rules;
    b.resolve_province = ResolveProvince;
    b.province_context = this;
    b.ai_war_coordinator_vtable = 0xAA11;
    b.ai_unit_stack_vtable = 0xAA22;
    b.ai_subunit_stack_vtable = 0xAA33;
    Put<std::int32_t>(combat, 8, 0x1000003);
    combats.Set(0x1000003, combat.data());
    Put<std::int32_t>(province, 0x10, 2586);
    Put<std::uint32_t>(province, 0x85C, 0x50726F76);
    Put(combat, 0x6B8, province.data());
    Put<std::int32_t>(combat, 0x6B0, 1);
    Put<std::int32_t>(combat, 0x6B4, 4);
    Put<std::int32_t>(combat, 0x6E0, -1);
    Put<std::int32_t>(combat, 0x700, -1);
    Put<std::int32_t>(combat, 0x708, 0x1000004);
    Put<std::int64_t>(combat, 0x6C8, 1LL << 40);
    Put<std::int64_t>(combat, 0x710, (1LL << 40) + 17);
    Put<std::int32_t>(result, 8, 0x1000004);
    Put<std::int32_t>(result, 0x2C, 0x029C55C0);
    results.Set(0x1000004, result.data());
    Put<std::int32_t>(char0, 0x18, 0x1000001);
    Put<std::int32_t>(char1, 0x18, 0x1000002);
    characters.Set(0x1000001, char0.data());
    characters.Set(0x1000002, char1.data());
    Put(char0, 0x1C0, land.data());
    Put<std::int32_t>(land, 0x1F8, -1);
    Put<std::uint32_t>(rules, 0x40, 1 << 10);
    InitArmy(unit0, army0, 0x1000001);
    InitArmy(unit1, army1, 0x1000002);
    Put<std::int32_t>(regiment0, 0x10, 0x1000005);
    Put(regiment0, 0x18, type0.data());
    Put<std::int32_t>(regiment0, 0x140, 0x1000001);
    regiments.Set(0x1000005, regiment0.data());
    Put<std::uint8_t>(type0, 0x98A, 1);
    Put<std::uint8_t>(type0, 0xA0A, 0);
    Put<std::int32_t>(regiment1, 0x10, 0x1000006);
    Put(regiment1, 0x18, type1.data());
    Put<std::int32_t>(regiment1, 0x140, 0x1000002);
    regiments.Set(0x1000006, regiment1.data());
    Put<std::uint8_t>(type1, 0x98A, 0);
    Put<std::uint8_t>(type1, 0xA0A, 1);
    Put<std::int32_t>(entry0, 8, 0x1000005);
    Put<std::int64_t>(entry0, 0x10, 10'000'000);
    Put<std::int64_t>(entry0, 0x18, 8'000'000);
    Put<std::int64_t>(entry0, 0x20, 1'000'000);
    Put<std::int32_t>(entry1, 8, 0x1000006);
    Put<std::int64_t>(entry1, 0x10, 4'000'000);
    Array(combat, 0x30, aids.data(), 1);
    Array(combat, 0x378, dids.data(), 1);
    Array(combat, 0x48, entry0.data(), 1);
    Array(combat, 0x390, entry1.data(), 1);
    Put(combat, 0xD8, combat.data());
    Put(combat, 0x420, combat.data());
    Put<std::int32_t>(combat, 0x90, 0x1000001);
    Put<std::int32_t>(combat, 0x94, -1);
    Put<std::int32_t>(combat, 0x3D8, 0x1000002);
    Put<std::int32_t>(combat, 0x3DC, -1);
    Put<std::int64_t>(combat, 0xB8, 9'000'000);
    Put<std::int64_t>(combat, 0xC0, 9'000'000);
    Array(province, 0x758, combat_ids.data(), 1);
    ArmySnapshot a{};
    a.army_id = 0x1000001;
    a.controllable = true;
    a.in_combat = true;
    scope.player_armies.push_back(a);
    Put<std::uintptr_t>(coordinator, 0, 0xAA11);
    Put<std::int32_t>(coordinator, 0x10, 0x1000007);
    coordinators.Set(0x1000007, coordinator.data());
    Array(coordinator, 0x50, parent_rows.data(), 1);
    Put<std::uintptr_t>(parent, 0, 0xAA22);
    Put(parent, 0x58, coordinator.data());
    Array(parent, 0x40, subunit_rows.data(), 1);
    Array(parent, 8, support.data(), 1);
    Put<std::uintptr_t>(subunit, 0, 0xAA33);
    Array(subunit, 0x10, member.data(), 1);
    Put(subunit, 0x38, parent.data());
    Put(subunit, 0x40, province.data());
    Put<std::uint8_t>(subunit, 0x48, 0x13);
    Put<std::int64_t>(subunit, 0x28, 12300000);
    Put<std::int64_t>(subunit, 0x30, 56700000);
    Put<std::uint8_t>(subunit, 0x54, 1);
    Put<std::int32_t>(unit0, 0x1C4, 0x1000007);
    Put(unit0, 0x1D0, subunit.data());
    Put(unit0, 0x30, province.data());
    b.route_bindings.enabled = true;
    b.route_bindings.game_state_slot = &g;
    b.route_bindings.jomini_state_slot = &j;
    b.route_bindings.army_storage_slot = &units.root;
    b.route_bindings.is_character_hostile = Hostile;
  }
  void *result_root = result.data();
  void InitArmy(Bytes<0x200> &u, Bytes<0x148> &a, std::int32_t id) {
    Put(u, 0x10, id);
    Put(u, 0x174, id);
    Put(u, 0x178, id);
    Put(u, 0x20, province.data());
    Put(a, 0x10, id);
    Put(a, 0x124, id);
    Put<std::int32_t>(a, 0x128, 0x1000003);
    units.Set(id, u.data());
    armies.Set(id, a.data());
  }
};
Fixture *Fixture::current = nullptr;
} // namespace

namespace xar::ck3_11906 {
bool ReadSnapshot(const Bindings &, game::Snapshot &) noexcept { return false; }
game::BattleTerminalTransitionStatusV1 ReadBattleTerminalTransitionV1(
    const Bindings &, const game::Snapshot &,
    const game::BattleTerminalTransitionRequestV1 &,
    game::BattleTerminalTransitionSnapshotV1 &output) noexcept {
  return output.status;
}
} // namespace xar::ck3_11906


namespace {
constexpr std::int32_t kCombatId = 0x1000003;
constexpr std::int32_t kForeignSubjectId = 0x1000002;

struct ReaderAttempt {
  std::uint32_t exception_code = 0;
  BattleTerminalTransitionStatusV1 status{};
};

// Test-only capture keeps the baseline AV as an explicit failed attempt.
// It adds no production fallback, gate, rearm or invalid-field substitution.
bool InvokeActualReaderWithSeh(
    Fixture &fixture, BattleTerminalTransitionSnapshotV1 &result,
    ReaderAttempt &attempt) noexcept {
  __try {
    attempt.status = ReadBattleTerminalTransitionV1(
        fixture.b, fixture.scope,
        {kCombatId, kForeignSubjectId, std::nullopt}, result);
    return true;
  } __except ((attempt.exception_code = GetExceptionCode()),
              EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
}

void ForeignAiBoundTerminal(const std::string &prefix) {
  Fixture f;
  f.scope.player_armies.clear();
  f.scope.date_raw = 53236632;
  Put<std::int32_t>(f.gs, 8, f.scope.date_raw);
  Put<std::int32_t>(f.combat, 0x6B0, 0);
  Put<std::int32_t>(f.combat, 0x6B4, 1);
  f.member[0] = kForeignSubjectId;
  Put<std::int32_t>(f.unit1, 0x1C4, 0x1000007);
  Put(f.unit1, 0x1D0, f.subunit.data());
  Put(f.unit1, 0x30, f.province.data());
  // Actual v37 evidence identifies the wrong binder root 0x5D204F0 and the
  // native getter's correct root 0x5D20550. The unreadable sentinel below is
  // a deterministic fixture value, not a claimed dump of CK3's actual RAM.
  struct CoordinatorImage {
    void *image = nullptr;
    CoordinatorImage() {
      image = VirtualAlloc(nullptr, 0x5D21000, MEM_RESERVE, PAGE_NOACCESS);
      Require(image != nullptr, "coordinator fixture image reservation failed");
      SYSTEM_INFO information{};
      GetSystemInfo(&information);
      constexpr std::uintptr_t root_rva = 0x5D20550;
      const auto page_rva = root_rva - root_rva % information.dwPageSize;
      auto *page = static_cast<std::byte *>(image)+page_rva;
      Require(VirtualAlloc(page, information.dwPageSize, MEM_COMMIT,
                           PAGE_READWRITE) == page,
              "coordinator fixture root page commit failed");
    }
    ~CoordinatorImage() {
      if (image != nullptr) VirtualFree(image, 0, MEM_RELEASE);
    }
  } coordinator_image;
  const auto image_base = reinterpret_cast<std::uintptr_t>(coordinator_image.image);
  void *wrong_storage = static_cast<std::byte *>(coordinator_image.image)+0x1000;
  std::memcpy(static_cast<std::byte *>(coordinator_image.image)+0x5D204F0,
              &wrong_storage, sizeof(wrong_storage));
  std::memcpy(static_cast<std::byte *>(coordinator_image.image)+0x5D20550,
              &f.coordinators.root, sizeof(f.coordinators.root));
  const auto native_binding = BindBattleImage(image_base, kExecutableSha256);
  Require(native_binding.enabled, "genuine exact-build battle binder disabled");
  // Preserve the real binder selection as the tested production input. All
  // unrelated reader bindings remain the existing byte fixture overrides.
  f.b.ai_war_coordinator_storage_slot =
      native_binding.ai_war_coordinator_storage_slot;
  Put<std::uint8_t>(f.subunit, 0x48, 0);
  Put<std::uint8_t>(f.subunit, 0x54, 0);

  Require(InitializeBattleTerminalJournalStorageV1(f.b), "journal initialize");
  BattleTerminalTransitionSnapshotV1 result{};
  ReaderAttempt attempt{};
  if (!InvokeActualReaderWithSeh(f, result, attempt)) {
    throw std::runtime_error("native_reader_access_violation code="+
                             std::to_string(attempt.exception_code));
  }
  Require(attempt.status == BattleTerminalTransitionStatusV1::available,
          "actual foreign AI-bound production reader unavailable");
  Require(result.subject.exists &&
              result.subject.active_combat_id == kCombatId &&
              result.subject.ai_membership_status ==
                  BattleTerminalAiMembershipStatusV1::observed &&
              result.subject.coordinator_id == 0x1000007 &&
              result.subject.unit_stack_stored_index == 0 &&
              result.subject.subunit_stored_index == 0,
          "actual foreign AI membership branch was bypassed or changed");
  Require(result.prior.terminal_kind == BattleTerminalKindV1::active_not_terminal &&
              result.prior.phase_day == 1 &&
              !result.prior.terminal_date_raw &&
              result.terminal_journal.latest_sequence == 0,
          "active terminal state changed while observing AI membership");
  result.snapshot_revision = 2;
  const auto wire = xar::ck3_11906::SerializeBattleTerminalTransitionV1(result);
  Require(!wire.empty(), "production reader -> serializer returned empty wire");
  std::ofstream output(prefix+"/foreign-ai-terminal.json", std::ios::binary);
  Require(output.good(), "native wire output unavailable");
  output << wire << '\n';
  Require(output.good(), "native wire output write failed");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
  try {
    ForeignAiBoundTerminal(argv[1]);
    std::cout << "foreign-ai-terminal GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "foreign-ai-terminal RED: " << error.what() << '\n';
    return 1;
  }
}
