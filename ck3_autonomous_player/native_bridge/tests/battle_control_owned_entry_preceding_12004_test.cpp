#include "xar_bridge/battle_control_owned_entry_preceding_12004.hpp"
#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

// New connection case only. Reused memory setup has no old main/case loop.
namespace {
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
  Bytes<0x720> combat{}, replacement_combat{};
  bool replace_during_sample = false;
  std::uint32_t strength_reads = 0;
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
    assert(owner == current->char0.data());
    return current->rules.data();
  }
  static std::int32_t Strength(void *) {
    auto &f = *current;
    ++f.strength_reads;
    if (f.replace_during_sample && f.strength_reads == 2) {
      f.replacement_combat = f.combat;
      Put(f.replacement_combat, 0xD8, f.replacement_combat.data());
      Put(f.replacement_combat, 0x420, f.replacement_combat.data());
      f.combats.Set(0x1000003, f.replacement_combat.data());
    }
    return 31337;
  }
  static bool Hostile(void *a, void *d, bool) { return a != d; }
  static bool Retreat(void *c, void *, void *sink) {
    assert(!sink);
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

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kFixtureBase = 0x18000000;
constexpr std::uintptr_t kOriginalBits = 0xB1B2C3C412345678ULL;
void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}
void Emit64(std::vector<std::uint8_t> &code, std::uint64_t value) {
  for (unsigned index = 0; index != 8; ++index)
    code.push_back(static_cast<std::uint8_t>(value >> (index * 8)));
}
void *CreateOneOriginalTarget(std::uint64_t &count) {
  std::vector<std::uint8_t> code{
      0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24,0x10,
      0x48,0x89,0x74,0x24,0x18,0x49,0xBA};
  Emit64(code, reinterpret_cast<std::uintptr_t>(&count));
  code.insert(code.end(), {0x49,0xFF,0x02,0x48,0xB8});
  Emit64(code, kOriginalBits);
  code.insert(code.end(), {
      0x48,0x8B,0x5C,0x24,0x08,0x48,0x8B,0x6C,0x24,0x10,
      0x48,0x8B,0x74,0x24,0x18,0xC3});
  auto *target = VirtualAlloc(nullptr, 128, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
  if (target == nullptr) return nullptr;
  std::memcpy(target, code.data(), code.size());
  DWORD original_protection = 0;
  if (!VirtualProtect(target, 128, PAGE_EXECUTE_READ, &original_protection) ||
      !FlushInstructionCache(GetCurrentProcess(), target, code.size())) {
    VirtualFree(target, 0, MEM_RELEASE);
    return nullptr;
  }
  return target;
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  void *target = nullptr;
  xar::ck3_12004::EntryPrecedingState12004 state;
  bool installed = false;
  try {
    Fixture fixture;
    Put<std::uint32_t>(fixture.combat, 0x0C, 0x436F6D62U);
    std::uint64_t original_count = 0;
    target = CreateOneOriginalTarget(original_count);
    Require(target != nullptr, "one new synthetic original target allocation");
    xar::ck3_12004::EntryPrecedingInstall12004 install;
    install.primary_thread_suspended_proven = true;
    install.offline_fixture = true;
    install.module_base = kFixtureBase;
    install.target_override = reinterpret_cast<std::uintptr_t>(target);
    install.bindings = xar::ck3_12004::BindEntryPrecedingCaptureImage12004(
        kFixtureBase, xar::ck3_12004::kEntryPrecedingExeSha12004);
    installed = xar::ck3_12004::InstallEntryPrecedingCapture12004(
        state, install, xar::ck3_12004::kEntryPrecedingExeSha12004);
    Require(installed, "qualified52 production setup for one new occurrence");
    std::uintptr_t caller_slot = kFixtureBase + xar::ck3_12004::kEntryPrecedingReturnRva12004;
    const auto bits = xar::ck3_12004::InvokeEntryPrecedingCapture12004(
        fixture.combat.data(), caller_slot, reinterpret_cast<std::uintptr_t>(&caller_slot));
    Require(bits == kOriginalBits && original_count == 1,
        "one original occurrence; retained collection cannot replay it");

    xar::ck3_12004::BattleControlOwnedEntryPreceding12004 positive;
    const auto status = xar::ck3_12004::ReadBattleControlOwnedEntryPreceding12004(
        fixture.b, fixture.scope, {0x1000001}, true, 76543, positive);
    Require(status == xar::game::BattleControlSnapshotStatus::available &&
        positive.snapshot.battle_control_ready && positive.entry_preceding_capture &&
        positive.entry_preceding_capture->request_filtered &&
        positive.entry_preceding_capture->records.size() == 1,
        "accepted actual Combat span reaches one owned retained record");
    const auto &record = positive.entry_preceding_capture->records.front();
    Require(record.combat_identity == reinterpret_cast<std::uintptr_t>(fixture.combat.data()) &&
        record.combat_full_id_before == 0x1000003U &&
        record.combat_full_id_after == 0x1000003U && record.identity_stable &&
        record.original_returned && record.offline_fixture && !record.outer_invocation,
        "exact owned identity/generation; no full outer invocation invented");
    const auto positive_wire = xar::ck3_12004::SerializeBattleControlOwnedEntryPreceding12004(positive);
    Require(positive_wire.find("\"entry_preceding_capture_12004\":{") != std::string::npos &&
        positive_wire.find("\"full_entry\":false") != std::string::npos &&
        positive_wire.find("\"outer_invocation\":null") != std::string::npos,
        "new raw sibling uses actual unchanged52 serializer facts");

    fixture.replace_during_sample = true;
    fixture.strength_reads = 0;
    xar::ck3_12004::BattleControlOwnedEntryPreceding12004 replaced;
    const auto replaced_status = xar::ck3_12004::ReadBattleControlOwnedEntryPreceding12004(
        fixture.b, fixture.scope, {0x1000001}, true, 76543, replaced);
    Require(replaced_status == xar::game::BattleControlSnapshotStatus::available &&
        replaced.snapshot.battle_control_ready && !replaced.entry_preceding_capture,
        "matching old numeric frame with differing actual Combat pointers preserves base and omits raw");
    fixture.replace_during_sample = false;
    fixture.strength_reads = 0;
    xar::ck3_12004::BattleControlOwnedEntryPreceding12004 nonactual4;
    Require(xar::ck3_12004::ReadBattleControlOwnedEntryPreceding12004(
        fixture.b, fixture.scope, {0x1000001}, false, 76543, nonactual4) ==
        xar::game::BattleControlSnapshotStatus::available && !nonactual4.entry_preceding_capture,
        "independent exact-build admission does not alter old availability");
    Require(original_count == 1 &&
        xar::ck3_12004::SerializeBattleControlOwnedEntryPreceding12004(positive) == positive_wire,
        "later pointer/admission changes never requery or mutate the prior owned record");
    auto unavailable_scope = fixture.scope;
    unavailable_scope.paused = false;
    auto unavailable = positive;
    Require(xar::ck3_12004::ReadBattleControlOwnedEntryPreceding12004(
        fixture.b, unavailable_scope, {0x1000001}, true, 76543, unavailable) !=
        xar::game::BattleControlSnapshotStatus::available &&
        !unavailable.entry_preceding_capture && original_count == 1,
        "a newly unavailable frame clears a previously owned optional without another original");

    const auto path = std::filesystem::path(argv[1]);
    std::filesystem::create_directories(path.parent_path());
    std::ofstream output(path, std::ios::binary);
    output << "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"new57e-owned-combat\",\"ok\":true,\"result\":{\"accepted\":true,\"status\":\"available\",\"query_sequence\":1,\"snapshot_revision\":76543,\"battle_control_snapshot\":"
        << positive_wire << "}}\n";
    Require(output.good(), "one actual new owned BattleControl wire written");
    output.close();
    Require(xar::ck3_12004::UninstallEntryPrecedingCapture12004(state, true),
        "new synthetic target restored after connection case");
    installed = false;
    Require(VirtualFree(target, 0, MEM_RELEASE) != FALSE, "new owned target released");
    target = nullptr;
    std::cout << "57e-owned-combat: original=1 positive=1 pointer-replaced=1 nonactual4=1 unavailable=1 full_entry=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    if (installed) xar::ck3_12004::UninstallEntryPrecedingCapture12004(state, true);
    if (target != nullptr) VirtualFree(target, 0, MEM_RELEASE);
    return 1;
  }
}
