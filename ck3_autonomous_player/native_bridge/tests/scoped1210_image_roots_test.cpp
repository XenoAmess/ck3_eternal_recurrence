// Owned sparse RAM only. This source has not been compiled or executed here.
#include "xar_bridge/ck3_1210_battle_scoped_source_v1.hpp"
#include <array>
#include <bit>
#include <cstdio>
#include <cstring>
#include <map>
#include <utility>

namespace {
using namespace xar::ck3_1210;
constexpr std::uintptr_t base = 0x140000000ULL;
constexpr std::uintptr_t state = 0x200000000ULL, jomini = 0x210000000ULL;
constexpr std::uintptr_t data = 0x300000000ULL, characters = 0x400000000ULL;
constexpr std::uintptr_t units = 0x410000000ULL, wars = 0x420000000ULL;
constexpr std::uintptr_t sieges = 0x430000000ULL, tasks = 0x440000000ULL;
constexpr std::uintptr_t armies = 0x450000000ULL, combats = 0x460000000ULL;
constexpr std::uintptr_t unit_rows = 0x470000000ULL, army_rows = 0x480000000ULL;
constexpr std::uintptr_t combat_rows = 0x490000000ULL;
constexpr std::uintptr_t unit = 0x500000000ULL, army = 0x510000000ULL;
constexpr std::uintptr_t combat = 0x520000000ULL, clone_units = 0x530000000ULL;
constexpr auto actor_id = std::bit_cast<std::int32_t>(0x84000000U);
constexpr auto unit_id = std::bit_cast<std::int32_t>(0x81000000U);
constexpr auto army_id = std::bit_cast<std::int32_t>(0x82000000U);
constexpr auto combat_id = std::bit_cast<std::int32_t>(0x83000000U);
struct Cell { std::array<std::byte, 8> value{}; std::size_t size = 0; };
struct Fixture {
  std::map<std::uintptr_t, Cell> memory;
  xar::game::AdapterDescriptor descriptor{
      kAdapterId, kGameVersion, kExecutableSha256, "xar_checkpoint", {}};
  Scoped1210ImageSourceV1 source{base, &descriptor, BindCoreImage(base, kExecutableSha256)};
  CoreSnapshotPrefix expected{};
  std::size_t copies = 0, validations = 0, deny_validation = 0;
  std::uintptr_t deny_address = 0;
  bool valid_core_identity = true, replace_root_after_validation = false;
  bool replace_manager_after_validation = false;
  template <class T> void Put(std::uintptr_t at, T value) {
    static_assert(sizeof(T) <= 8);
    Cell cell{}; cell.size = sizeof(T);
    std::memcpy(cell.value.data(), &value, sizeof(T)); memory[at] = cell;
  }
  Fixture() {
    expected.clock = {123456, 3, true}; expected.local_player_id = 7;
    expected.map_ready = expected.has_played_character = expected.played_character_alive = true;
    expected.played_character_id = actor_id;
    Put(base + kGameStateSlotRva, state); Put(base + kJominiStateSlotRva, jomini);
    Put(base + kCharacterStorageSlotRva, characters); Put(state + kGameStateDataOffset, data);
    Manager(0x3ABF8, 0x4EA4090, 0x20, 0x6A667A8, units, 0x4EA40C8);
    Manager(0x3F2D8, 0x4E9C2C0, 0x20, 0x6A666D0, wars, 0x4E9C188);
    Manager(0x3F130, 0x4E4B000, 0x28, 0x6A67198, sieges, 0x4E4AE18);
    Manager(0x1EFA0, 0x4EA0060, 0x20, 0x6A666F8, tasks, 0x4EA0110);
    Put(data + 0x3F540, base + 0x4E83550);
    Put(data + 0x3F540 + 0x20, std::uintptr_t{0});
    Put(data + 0x3F540 + 0x2C, std::int32_t{0});
    Put(base + 0x6A666F0, armies); Put(base + 0x6A66718, combats);
    for (const auto &[registry, rows] : {
        std::pair{units, unit_rows}, std::pair{armies, army_rows},
        std::pair{combats, combat_rows}}) {
      Put(registry + 0x20, rows); Put(registry + 0x2C, std::int32_t{1});
    }
    Put(unit_rows + 8, unit); Put(army_rows + 8, army); Put(combat_rows + 8, combat);
    Put(unit + 0x10, unit_id); Put(unit + 0x14, std::uint32_t{0x556E6974U});
    Put(unit + 0x174, actor_id); Put(unit + 0x178, army_id);
    Put(army + 0x10, army_id); Put(army + 0x14, std::uint32_t{0x41726D79U});
    Put(army + 0x124, unit_id); Put(army + 0x128, combat_id);
    Put(combat + 8, combat_id); Put(combat + 0xC, std::uint32_t{0x436F6D62U});
    Put(clone_units, base + 0x4EA40C8);
  }
  void Manager(std::uintptr_t offset, std::uintptr_t vt, std::uintptr_t owned_offset,
      std::uintptr_t slot, std::uintptr_t registry, std::uintptr_t registry_vt) {
    Put(data + offset, base + vt); Put(data + offset + owned_offset, registry);
    Put(base + slot, registry); Put(registry, base + registry_vt);
  }
  static bool Copy(void *context, const void *from, void *to, std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(context); ++f.copies;
    const auto address = reinterpret_cast<std::uintptr_t>(from);
    if (address == f.deny_address) return false;
    const auto it = f.memory.find(address);
    if (it == f.memory.end() || it->second.size != size) return false;
    std::memcpy(to, it->second.value.data(), size); return true;
  }
  static bool Validate(void *context, const Scoped1210ImageSourceV1 &s,
      const CoreSnapshotPrefix &e) noexcept {
    auto &f = *static_cast<Fixture *>(context); ++f.validations;
    if (f.validations == 2 && f.replace_root_after_validation)
      f.Put(state + kGameStateDataOffset, data + 0x100000);
    if (f.validations == 2 && f.replace_manager_after_validation) {
      f.Put(data + 0x3ABF8 + 0x20, clone_units);
      f.Put(base + 0x6A667A8, clone_units);
    }
    return f.valid_core_identity && s.image_base == base &&
        f.validations != f.deny_validation &&
        e.clock.date_raw == f.expected.clock.date_raw &&
        e.played_character_id == f.expected.played_character_id;
  }
  Scoped1210SourceAccessV1 Access() { return {this, Copy, Validate}; }
  bool Root(Scoped1210ImageRootsV1 &out) {
    return ResolveScoped1210ImageRootsV1(source, expected, Access(), out);
  }
  bool Typed(Scoped1210ManagerKindV1 kind, Scoped1210ManagerRootsV1 &out) {
    return ResolveScoped1210ManagerV1(source, expected, Access(), kind, out);
  }
  bool Battle(BattleCandidateObservationV1 &out) {
    return ReadBattleCandidateFromScoped1210ImageV1(source, expected, unit_id, out, Access());
  }
};
int failures = 0;
void Check(bool condition, const char *name) {
  if (!condition) { ++failures; std::fprintf(stderr, "FAIL %s\n", name); }
}
void RejectRoot(Fixture &f, const char *name, bool expect_zero_copy = false) {
  Scoped1210ImageRootsV1 out{1, 2, 3, 4, 5};
  Check(!f.Root(out) && out == Scoped1210ImageRootsV1{}, name);
  if (expect_zero_copy) Check(f.copies == 0, "rejected identity before memory copy");
}
void RejectManager(Fixture &f, Scoped1210ManagerKindV1 kind, const char *name) {
  Scoped1210ManagerRootsV1 out{}; out.registry = 1;
  Check(!f.Typed(kind, out) && out == Scoped1210ManagerRootsV1{}, name);
}
void RejectBattle(Fixture &f, const char *name) {
  BattleCandidateObservationV1 out{};
  out.status = BattleCandidateStatusV1::identity_candidate; out.candidate_combat_id = 123;
  Check(!f.Battle(out) && out.status == BattleCandidateStatusV1::unavailable &&
      !out.candidate_combat_id && out.subject_public_cunit_id == -1, name);
}
} // namespace
int main() {
  { Fixture f; Scoped1210ImageRootsV1 out{};
    Check(f.Root(out) && out.image_base == base && out.game == state &&
        out.jomini == jomini && out.data == data && out.characters == characters,
        "roots are read from exact image globals"); }
  { Fixture f; f.descriptor.adapter_id = "ck3-1.20.0.4-msvc-x64";
    RejectRoot(f, "crossed adapter ID", true); }
  { Fixture f; f.descriptor.game_version = "1.20.0.4";
    RejectRoot(f, "crossed version", true); }
  { Fixture f; f.descriptor.executable_sha256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    RejectRoot(f, "crossed SHA", true); }
  { Fixture f; f.source.descriptor = nullptr; RejectRoot(f, "descriptor required", true); }
  { Fixture f; f.source.image_base = 0; RejectRoot(f, "image base required", true); }
  { Fixture f; f.source.image_base = (std::numeric_limits<std::uintptr_t>::max)() - kJominiStateSlotRva + 1;
    RejectRoot(f, "image addition overflow", true); }
  { Fixture f; f.source.image_base = base + 0x10000000;
    f.source.core = BindCoreImage(f.source.image_base, kExecutableSha256);
    RejectRoot(f, "correct relative addresses from another module lack owner identity", true); }
  { Fixture f; f.source.core.enabled = false; RejectRoot(f, "Core admission required", true); }
  { Fixture f; f.source.core.game_state_slot = reinterpret_cast<void **>(base + 0x5C68C50);
    RejectRoot(f, "legacy game slot rejected", true); }
  { Fixture f; f.source.core.jomini_state_slot = nullptr; RejectRoot(f, "entire Jomini bundle", true); }
  { Fixture f; f.source.core.character_storage_slot = nullptr; RejectRoot(f, "entire Character bundle", true); }
  { Fixture f; f.source.core.get_local_player = nullptr; RejectRoot(f, "entire getter bundle", true); }
  { Fixture f; f.valid_core_identity = false; RejectRoot(f, "existing Core validator rejects", true); }
  { Fixture f; f.expected.clock.paused = false; RejectRoot(f, "paused scope required", true); }
  { Fixture f; f.expected.played_character_id = -1; RejectRoot(f, "actual actor required", true); }
  { Fixture f; f.deny_address = base + kGameStateSlotRva; RejectRoot(f, "checked copy failure"); }
  { Fixture f; f.Put(base + kJominiStateSlotRva, std::uintptr_t{0}); RejectRoot(f, "Jomini null"); }
  { Fixture f; f.Put(state + kGameStateDataOffset, std::uintptr_t{0}); RejectRoot(f, "GameData null"); }
  { Fixture f; f.deny_validation = 2; RejectRoot(f, "final Core custody lost"); }
  { Fixture f; f.replace_root_after_validation = true;
    RejectRoot(f, "root changes inside final Core validation"); }
  for (const auto kind : {Scoped1210ManagerKindV1::unit, Scoped1210ManagerKindV1::war,
      Scoped1210ManagerKindV1::siege, Scoped1210ManagerKindV1::council_task,
      Scoped1210ManagerKindV1::character}) {
    Fixture f; Scoped1210ManagerRootsV1 out{};
    Check(f.Typed(kind, out) && out.kind == kind && out.image.data == data && out.manager != 0,
        "typed actual1210 manager source");
  }
  { Fixture f; f.Put(state + kGameStateDataOffset, (std::numeric_limits<std::uintptr_t>::max)() - 8);
    RejectManager(f, Scoped1210ManagerKindV1::unit, "embedded manager address overflow"); }
  { Fixture f; f.Put(data + 0x3ABF8, base + 0x4EA0060);
    RejectManager(f, Scoped1210ManagerKindV1::unit, "wrong manager type"); }
  { Fixture f; f.Put(data + 0x3ABF8 + 0x20, wars);
    RejectManager(f, Scoped1210ManagerKindV1::unit, "manager global owner mismatch"); }
  { Fixture f; f.Put(units, base + 0x4E9C188);
    RejectManager(f, Scoped1210ManagerKindV1::unit, "wrong typed registry"); }
  { Fixture f; f.Put(base + 0x6A667A8, std::uintptr_t{0});
    RejectManager(f, Scoped1210ManagerKindV1::unit, "registry unavailable"); }
  { Fixture f; f.replace_manager_after_validation = true;
    RejectManager(f, Scoped1210ManagerKindV1::unit, "equal VT is not lifetime ownership"); }
  { Fixture f; f.Put(data + 0x3F130 + 0x28, units);
    RejectManager(f, Scoped1210ManagerKindV1::siege, "Siege uses proven owned+28"); }
  { Fixture f; f.Put(data + 0x3F540 + 0x2C, std::int32_t{-1});
    RejectManager(f, Scoped1210ManagerKindV1::character, "maintained member count negative"); }
  { Fixture f; f.Put(data + 0x3F540 + 0x2C, std::int32_t{1});
    RejectManager(f, Scoped1210ManagerKindV1::character, "nonnull vector for nonempty count"); }
  { Fixture f; f.Put(data + 0x3F540 + 0x2C, std::int32_t{131073});
    RejectManager(f, Scoped1210ManagerKindV1::character, "authored observation budget"); }
  { Fixture f; RejectManager(f, static_cast<Scoped1210ManagerKindV1>(99), "unproved manager rejected"); }
  { Fixture f; Scoped1210ImageRootsV1 out{}; auto a = f.Access(); a.copy = nullptr;
    Check(!ResolveScoped1210ImageRootsV1(f.source, f.expected, a, out) && f.copies == 0,
        "checked copy required"); }
  { Fixture f; Scoped1210ImageRootsV1 out{}; auto a = f.Access(); a.validate_core_identity = nullptr;
    Check(!ResolveScoped1210ImageRootsV1(f.source, f.expected, a, out) && f.copies == 0,
        "existing actual Core identity required"); }
  { Fixture f; BattleCandidateObservationV1 out{};
    Check(f.Battle(out) && out.status == BattleCandidateStatusV1::identity_candidate &&
        out.subject_public_cunit_id == unit_id && out.source_native_carmy_id == army_id &&
        out.candidate_combat_id == combat_id, "battle reads signed full-ID chain through image source"); }
  { Fixture f; f.Put(army + 0x128, std::int32_t{-1}); f.Put(base + 0x6A66718, std::uintptr_t{0});
    BattleCandidateObservationV1 out{};
    Check(f.Battle(out) && out.status == BattleCandidateStatusV1::not_referenced &&
        !out.candidate_combat_id, "battle sentinel stays narrow field observation"); }
  { Fixture f; f.source.core.game_state_slot = nullptr;
    RejectBattle(f, "detached Core bundle cannot use valid registry RVAs"); }
  { Fixture f; f.Put(data + 0x3ABF8 + 0x20, wars);
    RejectBattle(f, "battle cannot use registry detached from Unit manager"); }
  { Fixture f; f.Put(combat + 8, std::int32_t{0});
    RejectBattle(f, "battle stale generation remains unavailable"); }
  { Fixture f; f.deny_validation = 5;
    RejectBattle(f, "battle loses actual Core scope during read"); }
  if (failures == 0) std::puts("PASS Scoped1210 image roots, typed manager source and scoped battle candidate");
  return failures == 0 ? 0 : 1;
}
