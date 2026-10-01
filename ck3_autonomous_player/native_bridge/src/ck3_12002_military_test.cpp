#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/ck3_12002_commands.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using namespace xar::ck3_12002;
constexpr std::int32_t kActor = 0x0300000A;
constexpr std::int32_t kUnit = 0x0500000B, kOtherUnit = 0x0500000C;
constexpr std::int32_t kInternalArmy = 0x06000014;
constexpr std::int32_t kSiege = 0x07000015;

template <typename T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <typename T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}
void Require(bool value, const char *description) {
  if (!value) {
    std::cerr << "FAIL " << description << '\n';
    std::exit(1);
  }
}

struct Fixture {
  Snapshot snapshot;
  std::array<std::byte, 0x1D8> actor{};
  std::array<std::byte, 0x180> unit{}, other_unit{};
  std::array<std::array<std::byte, 0x860>, 3> provinces{};
  std::array<std::byte, 0x450> siege{};
  MilitaryBindings bindings;
  bool validation_ok = true, submission_ok = true, route_ok = true;
  bool has_unit = true, has_character = true;
  std::int32_t mode = 0;
  std::int64_t progress = 0, cutoff = 50;
  void *first = nullptr, *last = nullptr;
  std::int32_t submissions = 0, cleanups = 0, validations = 0;
  std::int32_t raise_constructed = 0, raise_destroyed = 0;
  std::int32_t merge_created = 0, merge_destroyed = 0;
  std::int32_t move_destroyed = 0;
  std::uint32_t last_channel = 0;
  std::uintptr_t submitted_primary = 0;
  std::array<std::int32_t, 4> payload{};
  std::vector<std::int32_t> copied_array;
  std::vector<std::int32_t> route_ids{2, 3};
  void *build_origin = nullptr;

  Fixture();
};
Fixture *active = nullptr;

bool Read(void *context, Snapshot &snapshot) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  snapshot = f.snapshot;
  return true;
}
void *Character(void *context, std::int32_t id) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  return f.has_character && id == kActor ? f.actor.data() : nullptr;
}
void *Unit(void *context, std::int32_t id) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  if (id == kUnit && f.has_unit) return f.unit.data();
  if (id == kOtherUnit) return f.other_unit.data();
  return nullptr;
}
void *Province(void *context, std::int32_t id) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  return id >= 1 && id <= 3 ? f.provinces[id - 1].data() : nullptr;
}
void *Siege(void *context, std::int32_t id) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  return id == kSiege ? f.siege.data() : nullptr;
}
MilitaryWorldAccess World(Fixture &f) {
  return {&f, &Read, &Character, &Unit, &Province, &Siege};
}

bool Submit(void *context, void *command, std::uint32_t channel) noexcept {
  auto &f = *static_cast<Fixture *>(context);
  ++f.submissions;
  f.last_channel = channel;
  f.submitted_primary = Get<std::uintptr_t>(command, 0);
  f.payload = {Get<std::int32_t>(command, 0x20),
               Get<std::int32_t>(command, 0x24), 0, 0};
  if (f.submitted_primary == f.bindings.split_primary ||
      f.submitted_primary == f.bindings.start_primary ||
      f.submitted_primary == f.bindings.stop_primary) {
    f.payload[2] = Get<std::int32_t>(command, 0x28);
  } else if (f.submitted_primary == f.bindings.move_primary) {
    f.payload[2] = Get<std::int32_t>(command, 0x28);
    f.payload[3] = Get<std::int32_t>(command, 0x2C);
  } else if (f.submitted_primary == f.bindings.merge_primary) {
    auto &array = static_cast<MergeUnitCommand *>(command)->source_unit_ids;
    f.copied_array.assign(array.data, array.data + array.count);
  } else if (f.submitted_primary == f.bindings.raise_primary) {
    const auto data = Get<std::int32_t *>(command, 0x28);
    f.copied_array.assign(data, data + 2);
  }
  return f.submission_ok;
}
void *Capital(void *character) {
  Require(character == active->actor.data(), "capital actor");
  return active->provinces[0].data();
}
void *DefaultProvince(void *character, void *capital, std::int32_t arg3,
                       std::int32_t arg4) {
  Require(character == active->actor.data() &&
          capital == active->provinces[0].data() && arg3 == 0 && arg4 == -1,
          "default raise native arguments");
  return capital;
}
void *ConstructRaise(void *command, std::int32_t actor, const void *entry) {
  ++active->raise_constructed;
  Put(command, 0, active->bindings.raise_primary);
  Put(command, 0x18, active->bindings.raise_secondary);
  Put(command, 0x20, actor);
  auto *data = new std::int32_t[2];
  std::memcpy(data, entry, 8);
  Put(command, 0x28, data);
  Put(command, 0x30, std::int32_t{1});
  Put(command, 0x34, std::int32_t{1});
  Put(command, 0x38, static_cast<void *>(active));
  return command;
}
bool ValidateRaise(void *command, void *error) {
  ++active->validations;
  Require(error == nullptr && Get<std::int32_t>(command, 0x20) == kActor,
          "raise native validator");
  const auto *entry = Get<std::int32_t *>(command, 0x28);
  Require(entry[0] == 1 && entry[1] == -1, "default native raise entry");
  return active->validation_ok;
}
void *DestroyRaise(void *command, std::int32_t flags) {
  Require(flags == 0, "raise stack destructor flags");
  delete[] Get<std::int32_t *>(command, 0x28);
  ++active->raise_destroyed;
  return command;
}
std::int32_t Mode(void *unit, void *province, std::int32_t direct) {
  Require(unit == active->unit.data() && province != nullptr && direct == 1,
          "move native mode arguments");
  return active->mode;
}
bool CharacterAllowed(void *character, std::int32_t kind) {
  Require(character == active->actor.data() && kind == 1,
          "player command character gate");
  return active->validation_ok;
}
bool ArmyAllowed(void *unit, std::int32_t mode) {
  Require(unit == active->unit.data() && mode == active->mode,
          "move mode army gate");
  return active->validation_ok;
}
bool MoveAllowed(std::int32_t kind, void *unit, std::int32_t mode) {
  ++active->validations;
  Require(kind == 1 && unit == active->unit.data() && mode == active->mode,
          "complete native move gate");
  return active->validation_ok;
}
void *ConstructPath(void *path) {
  Put(path, 0, static_cast<void *>(nullptr));
  Put(path, 8, std::int32_t{0});
  Put(path, 0x0C, std::int32_t{0});
  return path;
}
void *DestroyMove(void *command, std::int32_t flags) {
  Require(flags == 0, "move stack destructor flags");
  auto *path = static_cast<MoveUnitCommand *>(command)->path.data();
  delete[] Get<void **>(path, 0);
  ++active->move_destroyed;
  return command;
}
std::int64_t *Progress(void *, std::int64_t *output) {
  *output = active->progress;
  return output;
}
void *First(void *) { return active->first; }
void *Last(void *) { return active->last; }
void *PathContext(void *context, void *unit) {
  Require(unit == active->unit.data(), "path context actor unit");
  Put(context, 0x10, unit);
  return context;
}
bool BuildRoute(void *context, void *origin, void *target, std::int32_t kind,
                 void *path) {
  Require(Get<void *>(context, 0x10) == active->unit.data() && kind == 2 &&
          target == active->provinces[2].data(), "native path planner ABI");
  active->build_origin = origin;
  if (!active->route_ok) return false;
  auto **entries = new void *[active->route_ids.size()];
  for (std::size_t i = 0; i < active->route_ids.size(); ++i) {
    entries[i] = &active->route_ids[i];
  }
  Put(path, 0, entries);
  Put(path, 8, static_cast<std::int32_t>(active->route_ids.size()));
  Put(path, 0x0C, static_cast<std::int32_t>(active->route_ids.size()));
  return true;
}
bool ValidateDisband(std::int32_t kind, std::int32_t army, void *error) {
  ++active->validations;
  Require(kind == 1 && army == kInternalArmy && error == nullptr,
          "disband consumes internal generation army id");
  return active->validation_ok;
}
bool ValidateSplit(std::int32_t kind, std::int32_t army,
                    std::int32_t actor, void *error) {
  ++active->validations;
  Require(kind == 1 && army == kInternalArmy && actor == kActor && error == nullptr,
          "split native argument order");
  return active->validation_ok;
}
void *DestroyPod(void *command, std::int32_t flags) {
  Require(flags == 0, "POD stack destructor flags");
  ++active->cleanups;
  return command;
}
void *CreateMerge() {
  ++active->merge_created;
  auto *command = new MergeUnitCommand{};
  command->header.primary_vtable = active->bindings.merge_primary;
  command->header.secondary_vtable = active->bindings.merge_secondary;
  command->source_unit_ids.allocator = active;
  return command;
}
void Append(void *array_pointer, std::int32_t index,
              const std::int32_t *begin, const std::int32_t *end) {
  Require(index == 0 && end - begin == 1 && *begin == kOtherUnit,
          "merge native range uses public unit ids");
  auto &array = *static_cast<NativeMilitaryIntArray *>(array_pointer);
  array.data = new std::int32_t[1]{*begin};
  array.capacity = array.count = 1;
}
bool ValidateMerge(void *pointer, void *error) {
  ++active->validations;
  const auto &command = *static_cast<MergeUnitCommand *>(pointer);
  Require(error == nullptr && command.kind == 1 &&
          command.destination_unit_id == kUnit &&
          command.source_unit_ids.count == 1 &&
          command.source_unit_ids.data[0] == kOtherUnit,
          "merge complete native validator payload");
  return active->validation_ok;
}
void *DestroyMerge(void *pointer, std::int32_t flags) {
  Require(flags == 1, "merge engine heap deleting destructor flags");
  auto *command = static_cast<MergeUnitCommand *>(pointer);
  delete[] command->source_unit_ids.data;
  delete command;
  ++active->merge_destroyed;
  return nullptr;
}
bool ValidateAssault(std::int32_t kind, std::int32_t actor,
                      std::int32_t siege, void *error) {
  ++active->validations;
  Require(kind == 1 && actor == kActor && siege == kSiege && error == nullptr,
          "assault complete native argument order");
  return active->validation_ok;
}

Fixture::Fixture() {
  active = this;
  snapshot.map_ready = snapshot.has_played_character =
      snapshot.played_character_alive = snapshot.paused = true;
  snapshot.played_character_id = kActor;
  for (std::size_t i = 0; i < provinces.size(); ++i) {
    Put(provinces[i].data(), 0x10, static_cast<std::int32_t>(i + 1));
    Put(provinces[i].data(), 0x85C, std::uint32_t{0x50726F76});
  }
  Put(unit.data(), 0x10, kUnit);
  Put(unit.data(), 0x178, kInternalArmy);
  Put(unit.data(), 0x20, static_cast<void *>(provinces[0].data()));
  Put(other_unit.data(), 0x10, kOtherUnit);
  Put(other_unit.data(), 0x178, std::int32_t{0x06000016});
  Put(siege.data(), 0x200, static_cast<void *>(provinces[0].data()));
  Put(provinces[0].data(), 0x788, kSiege);
  // The legacy offset deliberately carries an unrelated handle.
  Put(provinces[0].data(), 0x790, std::int32_t{-1});
  xar::game::ArmySnapshot row{};
  row.army_id = kUnit;
  row.owner_character_id = kActor;
  row.controllable = row.has_current_province = true;
  row.current_province_id = 1;
  snapshot.player_armies.push_back(row);
  row.army_id = kOtherUnit;
  snapshot.player_armies.push_back(row);
  bindings.enabled = true;
  bindings.submit_context = this;
  bindings.submit_copy = &Submit;
  bindings.raise_primary = 10; bindings.raise_secondary = 11;
  bindings.move_primary = 20; bindings.move_secondary = 21;
  bindings.disband_primary = 30; bindings.disband_secondary = 31;
  bindings.split_primary = 40; bindings.split_secondary = 41;
  bindings.merge_primary = 50; bindings.merge_secondary = 51;
  bindings.start_primary = 60; bindings.start_secondary = 61;
  bindings.stop_primary = 70; bindings.stop_secondary = 71;
  bindings.get_character_capital = &Capital;
  bindings.resolve_raise_province = &DefaultProvince;
  bindings.construct_raise = &ConstructRaise;
  bindings.validate_raise = &ValidateRaise;
  bindings.destroy_raise = &DestroyRaise;
  bindings.move_mode = &Mode;
  bindings.character_command_allowed = &CharacterAllowed;
  bindings.army_move_allowed = &ArmyAllowed;
  bindings.move_allowed = &MoveAllowed;
  bindings.construct_move_path = &ConstructPath;
  bindings.destroy_move = &DestroyMove;
  bindings.read_move_progress = &Progress;
  bindings.read_route_first = &First;
  bindings.read_route_last = &Last;
  bindings.move_progress_cutoff = &cutoff;
  bindings.construct_path_context = &PathContext;
  bindings.build_route = &BuildRoute;
  bindings.validate_disband = &ValidateDisband;
  bindings.validate_split = &ValidateSplit;
  bindings.destroy_split = &DestroyPod;
  bindings.create_merge = &CreateMerge;
  bindings.append_int_range = &Append;
  bindings.validate_merge = &ValidateMerge;
  bindings.destroy_merge = &DestroyMerge;
  bindings.validate_start = bindings.validate_stop = &ValidateAssault;
  bindings.destroy_assault = &DestroyPod;
  first = provinces[1].data(); last = provinces[2].data();
}

void CheckRaise() {
  Fixture f;
  auto world = World(f);
  Require(SubmitRaiseTroopsDefault(f.bindings, world) == RaiseTroopsResult::submitted,
          "raise submitted");
  Require(f.last_channel == 7 && f.raise_constructed == 1 && f.raise_destroyed == 1 &&
          f.copied_array == std::vector<std::int32_t>{1, -1}, "raise clone source life");
  f.validation_ok = false;
  Require(SubmitRaiseTroopsDefault(f.bindings, world) == RaiseTroopsResult::validation_failed &&
          f.submissions == 1 && f.raise_destroyed == 2, "raise rejected cleanup");
  f.validation_ok = true; f.submission_ok = false;
  Require(SubmitRaiseTroopsDefault(f.bindings, world) == RaiseTroopsResult::unavailable &&
          f.raise_destroyed == 3, "raise queue failure is no ACK");
  Put(f.provinces[0].data(), 0x85C, std::uint32_t{0});
  Require(SubmitRaiseTroopsDefault(f.bindings, world) == RaiseTroopsResult::no_default_province &&
          f.raise_constructed == 3, "invalid capital avoids selector");
  f.snapshot.played_character_alive = false;
  Require(SubmitRaiseTroopsDefault(f.bindings, world) == RaiseTroopsResult::no_played_character,
          "raise dead player");
}
void CheckMoveAndPreview() {
  Fixture f;
  auto world = World(f);
  Require(SubmitMoveArmy(f.bindings, world, kUnit, 3) == MoveArmyResult::submitted &&
          f.last_channel == 0x0E && f.payload == std::array<std::int32_t, 4>{1,kUnit,3,0} &&
          f.move_destroyed == 1, "move correct player payload cleanup");
  f.submission_ok = false;
  Require(SubmitMoveArmy(f.bindings, world, kUnit, 3) == MoveArmyResult::unavailable &&
          f.move_destroyed == 2, "move queue failure is no ACK");
  f.submission_ok = true;
  const auto preview = PreviewMoveArmy(f.bindings, world, kUnit, 3);
  Require(preview.status == PreviewMoveArmyStatus::available && preview.origin_province_id == 1 &&
          preview.route_province_ids == std::vector<std::int32_t>{2,3} &&
          f.submissions == 2 && f.move_destroyed == 3, "preview creates no command queue action");
  f.progress = 100;
  Put(f.unit.data(), 0x44, std::int32_t{2});
  f.snapshot.player_armies[0].route_province_ids = {2,3};
  f.route_ids = {1,3};
  const auto mid_edge = PreviewMoveArmy(f.bindings, world, kUnit, 3);
  Require(mid_edge.status == PreviewMoveArmyStatus::available &&
          mid_edge.origin_province_id == 1 &&
          mid_edge.route_province_ids == std::vector<std::int32_t>{2,1,3} &&
          f.build_origin == f.provinces[1].data(), "mid-edge preserves native revisited origin");
  const auto completing = PreviewMoveArmy(f.bindings, world, kUnit, 2);
  Require(completing.status == PreviewMoveArmyStatus::available &&
          completing.route_province_ids == std::vector<std::int32_t>{2}, "current edge destination");
  f.progress = 0; f.route_ids = {2};
  Require(PreviewMoveArmy(f.bindings, world, kUnit, 3).status == PreviewMoveArmyStatus::route_unavailable,
          "preview rejects wrong path endpoint");
  f.route_ok = false;
  Require(PreviewMoveArmy(f.bindings, world, kUnit, 3).status == PreviewMoveArmyStatus::route_unavailable,
          "native planner unavailable");
  f.snapshot.paused = false;
  Require(PreviewMoveArmy(f.bindings, world, kUnit, 3).status == PreviewMoveArmyStatus::requires_paused,
          "preview requires stable paused observation");
  f.mode = 2;
  Require(SubmitMoveArmy(f.bindings, world, kUnit, 3) == MoveArmyResult::move_mode_unavailable,
          "native unavailable mode");
  f.mode = 0; f.snapshot.player_armies[0].controllable = false;
  Require(SubmitMoveArmy(f.bindings, world, kUnit, 3) == MoveArmyResult::army_not_controllable,
          "foreign unit cannot receive move");
}
void CheckSplitDisbandMerge() {
  Fixture f;
  auto world = World(f);
  Require(SubmitDisbandArmy(f.bindings, world, kUnit) == DisbandArmyResult::submitted &&
          f.payload[0] == 1 && f.payload[1] == kInternalArmy, "disband internal army id");
  Require(SubmitSplitArmyHalf(f.bindings, world, kUnit) == SplitArmyHalfResult::split_submitted &&
          f.payload[1] == kActor && f.payload[2] == kInternalArmy && f.cleanups == 1,
          "split internal army id and actor");
  Require(SubmitMergeArmies(f.bindings, world, kUnit, kOtherUnit) == MergeArmiesResult::merge_submitted &&
          f.payload[1] == kUnit && f.copied_array == std::vector<std::int32_t>{kOtherUnit} &&
          f.merge_created == 1 && f.merge_destroyed == 1, "merge full public ids and heap cleanup");
  f.validation_ok = false;
  Require(SubmitSplitArmyHalf(f.bindings, world, kUnit) == SplitArmyHalfResult::validator_rejected,
          "split native validator rejects");
  Require(SubmitMergeArmies(f.bindings, world, kUnit, kOtherUnit) == MergeArmiesResult::validator_rejected &&
          f.merge_destroyed == 2, "merge rejected cleanup");
  f.validation_ok = true; f.submission_ok = false;
  Require(SubmitSplitArmyHalf(f.bindings, world, kUnit) == SplitArmyHalfResult::submission_failed &&
          f.cleanups == 2, "split queue rejects and stack cleanup");
  Require(SubmitMergeArmies(f.bindings, world, kUnit, kOtherUnit) == MergeArmiesResult::submission_failed &&
          f.merge_destroyed == 3, "merge queue rejects and owned cleanup");
  Require(SubmitDisbandArmy(f.bindings, world, kUnit) == DisbandArmyResult::unavailable,
          "disband queue rejection has no ACK");
  Require(SubmitMergeArmies(f.bindings, world, kUnit, kUnit) == MergeArmiesResult::same_army,
          "merge requires distinct source");
  f.has_unit = false;
  Require(SubmitSplitArmyHalf(f.bindings, world, kUnit) == SplitArmyHalfResult::army_not_found,
          "generation-resolved missing unit");
}
void CheckAssault() {
  Fixture f;
  auto world = World(f);
  Require(SubmitStartAssault(f.bindings, world, kSiege) == StartAssaultResult::start_submitted &&
          f.payload[1] == kActor && f.payload[2] == kSiege && f.cleanups == 1,
          "start assault new province siege offset");
  Put(f.siege.data(), 0x44C, std::uint8_t{1});
  Require(SubmitStartAssault(f.bindings, world, kSiege) == StartAssaultResult::assault_already_active,
          "assault current active state");
  Require(SubmitStopAssault(f.bindings, world, kSiege) == StopAssaultResult::stop_submitted &&
          f.cleanups == 2, "stop assault payload and stack cleanup");
  f.submission_ok = false;
  Require(SubmitStopAssault(f.bindings, world, kSiege) == StopAssaultResult::submission_failed &&
          f.cleanups == 3, "stop assault queue rejection cleanup");
  f.validation_ok = false; f.submission_ok = true;
  Require(SubmitStopAssault(f.bindings, world, kSiege) == StopAssaultResult::validator_rejected,
          "stop complete native validator");
  Put(f.siege.data(), 0x44C, std::uint8_t{0});
  Require(SubmitStopAssault(f.bindings, world, kSiege) == StopAssaultResult::assault_not_active,
          "stop inactive assault");
  Put(f.provinces[0].data(), 0x788, std::int32_t{0x08000015});
  Require(SubmitStartAssault(f.bindings, world, kSiege) == StartAssaultResult::siege_not_found,
          "generation-bearing province siege mismatch");
}
void CheckOriginAndBinding() {
  Fixture f;
  auto &b = f.bindings;
  Require(ResolveMilitaryMoveOrigin(b, f.unit.data(), f.provinces[2].data(), false) ==
          f.provinces[0].data(), "stationary current origin");
  f.progress = 51;
  Require(ResolveMilitaryMoveOrigin(b, f.unit.data(), f.provinces[2].data(), false) ==
          f.provinces[1].data(), "progress past cutoff chooses route front");
  f.progress = 50;
  Require(ResolveMilitaryMoveOrigin(b, f.unit.data(), f.provinces[2].data(), false) ==
          f.provinces[0].data(), "cutoff uses strict greater comparison");
  Put(f.unit.data(), 0x44, std::int32_t{1});
  Require(ResolveMilitaryMoveOrigin(b, f.unit.data(), f.provinces[2].data(), true) ==
          f.provinces[2].data(), "mode one uses route tail");
  Put(f.provinces[0].data(), 0x85C, std::uint32_t{0});
  Require(ResolveMilitaryMoveOrigin(b, f.unit.data(), f.provinces[1].data(), false) ==
          f.provinces[2].data(), "invalid current falls back tail");
  Put(f.provinces[2].data(), 0x85C, std::uint32_t{0});
  Require(ResolveMilitaryMoveOrigin(b, f.unit.data(), f.provinces[1].data(), false) ==
          f.provinces[1].data(), "invalid tail falls back target");
  CommandBindings commands{};
  const auto bound = BindMilitaryImage(0x140000000, kExecutableSha256, commands);
  Require(bound.enabled && bound.move_primary == 0x14476B168 &&
          reinterpret_cast<std::uintptr_t>(bound.validate_split) == 0x14296CF60 &&
          reinterpret_cast<std::uintptr_t>(bound.move_progress_cutoff) == 0x145C699E8,
          "exact pinned module address calculation");
  Require(!BindMilitaryImage(0x140000000, "old-build", commands).enabled &&
          !BindMilitaryImage(0, kExecutableSha256, commands).enabled,
          "wrong build does not bind");
}
} // namespace

int main() {
  CheckRaise();
  CheckMoveAndPreview();
  CheckSplitDisbandMerge();
  CheckAssault();
  CheckOriginAndBinding();
  std::cout << "PASS CK3 1.20.0.2 military offline fixtures: commands, native gates, "
               "payload ownership, route preview and inlined origin\n";
  return 0;
}
