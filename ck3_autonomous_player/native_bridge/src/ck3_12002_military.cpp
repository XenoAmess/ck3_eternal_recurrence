#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/ck3_12002_commands.hpp"

#include <algorithm>
#include <cstring>

namespace xar::ck3_12002 {
namespace {

constexpr std::size_t kUnitInternalArmyId = 0x178;
constexpr std::size_t kUnitCurrentProvince = 0x20;
constexpr std::size_t kProvinceId = 0x10;
constexpr std::size_t kProvinceValidityTag = 0x85C;
constexpr std::size_t kProvinceActiveSiege = 0x788;
constexpr std::size_t kSiegeProvince = 0x200;
constexpr std::size_t kSiegeAssaultActive = 0x44C;
constexpr std::int32_t kMaximumRouteEntries = 4'096;

template <typename T> T LoadAt(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset,
              sizeof(result));
  return result;
}

bool IsNativeProvince(const void *province) noexcept {
  return province != nullptr &&
         LoadAt<std::uint32_t>(province, kProvinceValidityTag) == 0x50726F76U;
}

struct CommandCleanup {
  void *(*destroy)(void *, std::int32_t) = nullptr;
  void *command = nullptr;
  std::int32_t delete_flags = 0;
  ~CommandCleanup() {
    if (destroy != nullptr && command != nullptr) {
      destroy(command, delete_flags);
    }
  }
};

const game::ArmySnapshot *FindControllable(const Snapshot &snapshot,
                                          std::int32_t unit_id) noexcept {
  const auto found = std::find_if(
      snapshot.player_armies.begin(), snapshot.player_armies.end(),
      [unit_id](const game::ArmySnapshot &row) {
        return row.army_id == unit_id && row.controllable;
      });
  return found == snapshot.player_armies.end() ? nullptr : &*found;
}

bool ReadCurrent(const MilitaryWorldAccess &world, Snapshot &snapshot) noexcept {
  return world.read_snapshot != nullptr &&
         world.read_snapshot(world.context, snapshot);
}

bool HasLivingPlayer(const Snapshot &snapshot) noexcept {
  return snapshot.has_played_character && snapshot.played_character_alive;
}

bool CanSubmit(const MilitaryBindings &bindings) noexcept {
  return bindings.enabled && bindings.submit_copy != nullptr;
}

MilitaryCommandHeader Header(std::uintptr_t primary,
                             std::uintptr_t secondary) noexcept {
  MilitaryCommandHeader header{};
  header.primary_vtable = primary;
  header.secondary_vtable = secondary;
  return header;
}

bool ValidSiegeProvince(const MilitaryWorldAccess &world, void *siege,
                        std::int32_t siege_id) noexcept {
  void *const province = LoadAt<void *>(siege, kSiegeProvince);
  if (province == nullptr || world.resolve_province == nullptr) {
    return false;
  }
  const auto province_id = LoadAt<std::int32_t>(province, kProvinceId);
  return world.resolve_province(world.context, province_id) == province &&
         LoadAt<std::int32_t>(province, kProvinceActiveSiege) == siege_id;
}

} // namespace

MilitaryBindings BindMilitaryImage(std::uintptr_t image_base,
                                    std::string_view executable_sha256,
                                    const CommandBindings &commands) noexcept {
  MilitaryBindings bindings{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) {
    return bindings;
  }
  bindings.submit_context = const_cast<CommandBindings *>(&commands);
  bindings.submit_copy = &SubmitCommandCopyCompat;
  bindings.raise_primary = image_base + 0x45345C0;
  bindings.raise_secondary = image_base + 0x4534658;
  bindings.move_primary = image_base + 0x476B168;
  bindings.move_secondary = image_base + 0x476B138;
  bindings.disband_primary = image_base + 0x476AE48;
  bindings.disband_secondary = image_base + 0x476AE18;
  bindings.split_primary = image_base + 0x476AF10;
  bindings.split_secondary = image_base + 0x476AEE0;
  bindings.merge_primary = image_base + 0x476AB20;
  bindings.merge_secondary = image_base + 0x476ABB8;
  bindings.start_primary = image_base + 0x476A288;
  bindings.start_secondary = image_base + 0x476A320;
  bindings.stop_primary = image_base + 0x476A030;
  bindings.stop_secondary = image_base + 0x476A000;
#define XAR_MILITARY_BIND(member, rva)                                          \
  bindings.member = reinterpret_cast<decltype(bindings.member)>(image_base + rva)
  XAR_MILITARY_BIND(get_character_capital, 0x28B1CD0);
  XAR_MILITARY_BIND(resolve_raise_province, 0x24A51B0);
  XAR_MILITARY_BIND(construct_raise, 0x298C130);
  XAR_MILITARY_BIND(validate_raise, 0x298C2C0);
  XAR_MILITARY_BIND(destroy_raise, 0x11F2E00);
  XAR_MILITARY_BIND(move_mode, 0x296A0A0);
  XAR_MILITARY_BIND(character_command_allowed, 0x29675F0);
  XAR_MILITARY_BIND(army_move_allowed, 0x24AC1B0);
  XAR_MILITARY_BIND(move_allowed, 0x2969570);
  XAR_MILITARY_BIND(construct_move_path, 0xD1A0B0);
  XAR_MILITARY_BIND(destroy_move, 0x2969620);
  XAR_MILITARY_BIND(read_move_progress, 0x24AB2F0);
  XAR_MILITARY_BIND(read_route_first, 0x24AA7D0);
  XAR_MILITARY_BIND(read_route_last, 0x24AA820);
  XAR_MILITARY_BIND(construct_path_context, 0x2648060);
  XAR_MILITARY_BIND(build_route, 0x2648150);
  XAR_MILITARY_BIND(validate_disband, 0x296A620);
  XAR_MILITARY_BIND(validate_split, 0x296CF60);
  XAR_MILITARY_BIND(destroy_split, 0x9D1560);
  XAR_MILITARY_BIND(create_merge, 0x297BCF0);
  XAR_MILITARY_BIND(append_int_range, 0x9E3790);
  XAR_MILITARY_BIND(validate_merge, 0x296EF90);
  XAR_MILITARY_BIND(destroy_merge, 0x296A220);
  XAR_MILITARY_BIND(validate_start, 0x29738C0);
  XAR_MILITARY_BIND(validate_stop, 0x2973A70);
  XAR_MILITARY_BIND(destroy_assault, 0x9D1560);
#undef XAR_MILITARY_BIND
  bindings.move_progress_cutoff = reinterpret_cast<const std::int64_t *>(
      image_base + 0x5C699E8);
  bindings.enabled = true;
  return bindings;
}

void *ResolveMilitaryDefaultRaiseProvince(const MilitaryBindings &bindings,
                                          void *character) noexcept {
  if (!bindings.enabled || character == nullptr ||
      bindings.get_character_capital == nullptr ||
      bindings.resolve_raise_province == nullptr) {
    return nullptr;
  }
  void *const capital = bindings.get_character_capital(character);
  if (!IsNativeProvince(capital)) {
    return nullptr;
  }
  void *const selected =
      bindings.resolve_raise_province(character, capital, 0, -1);
  return IsNativeProvince(selected) ? selected : nullptr;
}

void *ResolveMilitaryMoveOrigin(const MilitaryBindings &bindings, void *unit,
                                void *target, bool mode_is_one) noexcept {
  if (!bindings.enabled || unit == nullptr ||
      bindings.read_move_progress == nullptr ||
      bindings.read_route_first == nullptr || bindings.read_route_last == nullptr ||
      bindings.move_progress_cutoff == nullptr) {
    return nullptr;
  }
  if (!mode_is_one) {
    std::int64_t progress = 0;
    const auto *value = bindings.read_move_progress(unit, &progress);
    if (value == nullptr) {
      return nullptr;
    }
    if (*value > *bindings.move_progress_cutoff) {
      void *const first = bindings.read_route_first(unit);
      if (IsNativeProvince(first)) {
        return first;
      }
    }
  }
  const auto route_count = LoadAt<std::int32_t>(unit, 0x44);
  if (!mode_is_one || route_count == 0) {
    void *const current = LoadAt<void *>(unit, kUnitCurrentProvince);
    if (IsNativeProvince(current)) {
      return current;
    }
  }
  if (route_count != 0) {
    void *const last = bindings.read_route_last(unit);
    if (IsNativeProvince(last)) {
      return last;
    }
  }
  return target;
}

RaiseTroopsResult SubmitRaiseTroopsDefault(const MilitaryBindings &bindings,
                                          const MilitaryWorldAccess &world)
    noexcept {
  if (!CanSubmit(bindings) || world.resolve_character == nullptr ||
      world.resolve_province == nullptr ||
      bindings.get_character_capital == nullptr ||
      bindings.resolve_raise_province == nullptr ||
      bindings.construct_raise == nullptr || bindings.validate_raise == nullptr ||
      bindings.destroy_raise == nullptr || bindings.raise_primary == 0 ||
      bindings.raise_secondary == 0) {
    return RaiseTroopsResult::unavailable;
  }
  Snapshot current{};
  if (!ReadCurrent(world, current)) {
    return RaiseTroopsResult::unavailable;
  }
  if (!HasLivingPlayer(current)) {
    return RaiseTroopsResult::no_played_character;
  }
  void *const character =
      world.resolve_character(world.context, current.played_character_id);
  if (character == nullptr) {
    return RaiseTroopsResult::no_played_character;
  }
  void *const province = ResolveMilitaryDefaultRaiseProvince(bindings, character);
  if (province == nullptr) {
    return RaiseTroopsResult::no_default_province;
  }
  const auto province_id = LoadAt<std::int32_t>(province, kProvinceId);
  if (province_id < 1 ||
      world.resolve_province(world.context, province_id) != province) {
    return RaiseTroopsResult::no_default_province;
  }
  alignas(16) std::array<std::byte, 0x50> storage{};
  const std::array<std::int32_t, 2> entry{province_id, -1};
  void *const command = storage.data();
  if (bindings.construct_raise(command, current.played_character_id,
                               entry.data()) != command) {
    return RaiseTroopsResult::unavailable;
  }
  CommandCleanup cleanup{bindings.destroy_raise, command, 0};
  if (LoadAt<std::uintptr_t>(command, 0) != bindings.raise_primary ||
      LoadAt<std::uintptr_t>(command, 0x18) != bindings.raise_secondary) {
    return RaiseTroopsResult::unavailable;
  }
  if (!bindings.validate_raise(command, nullptr)) {
    return RaiseTroopsResult::validation_failed;
  }
  return bindings.submit_copy(bindings.submit_context, command, 7)
             ? RaiseTroopsResult::submitted
             : RaiseTroopsResult::unavailable;
}

MoveArmyResult SubmitMoveArmy(const MilitaryBindings &bindings,
                              const MilitaryWorldAccess &world,
                              std::int32_t unit_id,
                              std::int32_t province_id) noexcept {
  if (!CanSubmit(bindings) || world.resolve_unit == nullptr ||
      world.resolve_province == nullptr || world.resolve_character == nullptr ||
      bindings.move_mode == nullptr ||
      bindings.character_command_allowed == nullptr ||
      bindings.army_move_allowed == nullptr || bindings.move_allowed == nullptr ||
      bindings.construct_move_path == nullptr || bindings.destroy_move == nullptr ||
      bindings.move_primary == 0 || bindings.move_secondary == 0) {
    return MoveArmyResult::unavailable;
  }
  Snapshot current{};
  if (!ReadCurrent(world, current)) {
    return MoveArmyResult::unavailable;
  }
  void *const unit = world.resolve_unit(world.context, unit_id);
  if (unit == nullptr) {
    return MoveArmyResult::army_not_found;
  }
  if (FindControllable(current, unit_id) == nullptr) {
    return MoveArmyResult::army_not_controllable;
  }
  void *const province = world.resolve_province(world.context, province_id);
  if (province == nullptr) {
    return MoveArmyResult::province_not_found;
  }
  const auto mode = bindings.move_mode(unit, province, 1);
  if (mode == 2) {
    return MoveArmyResult::move_mode_unavailable;
  }
  void *const character =
      world.resolve_character(world.context, current.played_character_id);
  if (character == nullptr || !bindings.character_command_allowed(character, 1)) {
    return MoveArmyResult::character_state_rejected;
  }
  if (!bindings.army_move_allowed(unit, mode)) {
    return MoveArmyResult::army_state_rejected;
  }
  if (!bindings.move_allowed(1, unit, mode)) {
    return MoveArmyResult::validation_failed;
  }
  MoveUnitCommand command{};
  command.header = Header(bindings.move_primary, bindings.move_secondary);
  command.unit_id = unit_id;
  command.province_id = province_id;
  command.mode = mode;
  if (bindings.construct_move_path(command.path.data()) != command.path.data()) {
    return MoveArmyResult::unavailable;
  }
  CommandCleanup cleanup{bindings.destroy_move, &command, 0};
  return bindings.submit_copy(bindings.submit_context, &command, 0x0E)
             ? MoveArmyResult::submitted
             : MoveArmyResult::unavailable;
}

PreviewMoveArmyResult PreviewMoveArmy(const MilitaryBindings &bindings,
                                      const MilitaryWorldAccess &world,
                                      std::int32_t unit_id,
                                      std::int32_t province_id) noexcept {
  PreviewMoveArmyResult result{};
  result.army_id = unit_id;
  result.target_province_id = province_id;
  if (!bindings.enabled || world.resolve_unit == nullptr ||
      world.resolve_province == nullptr || world.resolve_character == nullptr ||
      bindings.move_mode == nullptr ||
      bindings.character_command_allowed == nullptr ||
      bindings.army_move_allowed == nullptr || bindings.move_allowed == nullptr ||
      bindings.read_move_progress == nullptr ||
      bindings.read_route_first == nullptr || bindings.read_route_last == nullptr ||
      bindings.move_progress_cutoff == nullptr ||
      bindings.construct_path_context == nullptr || bindings.build_route == nullptr ||
      bindings.construct_move_path == nullptr || bindings.destroy_move == nullptr ||
      bindings.move_primary == 0 || bindings.move_secondary == 0) {
    return result;
  }
  Snapshot current{};
  if (!ReadCurrent(world, current)) {
    return result;
  }
  if (!current.paused) {
    result.status = PreviewMoveArmyStatus::requires_paused;
    return result;
  }
  void *const unit = world.resolve_unit(world.context, unit_id);
  if (unit == nullptr) {
    result.status = PreviewMoveArmyStatus::army_not_found;
    return result;
  }
  const auto *selected = FindControllable(current, unit_id);
  if (selected == nullptr) {
    result.status = PreviewMoveArmyStatus::army_not_controllable;
    return result;
  }
  void *const observed_origin = selected->has_current_province
      ? world.resolve_province(world.context, selected->current_province_id)
      : nullptr;
  if (observed_origin == nullptr ||
      LoadAt<void *>(unit, kUnitCurrentProvince) != observed_origin) {
    result.status = PreviewMoveArmyStatus::origin_unavailable;
    return result;
  }
  void *const target = world.resolve_province(world.context, province_id);
  if (target == nullptr) {
    result.status = PreviewMoveArmyStatus::province_not_found;
    return result;
  }
  const auto mode = bindings.move_mode(unit, target, 1);
  if (mode == 2) {
    result.status = PreviewMoveArmyStatus::move_mode_unavailable;
    return result;
  }
  void *const character =
      world.resolve_character(world.context, current.played_character_id);
  if (character == nullptr || !bindings.character_command_allowed(character, 1)) {
    result.status = PreviewMoveArmyStatus::character_state_rejected;
    return result;
  }
  if (!bindings.army_move_allowed(unit, mode)) {
    result.status = PreviewMoveArmyStatus::army_state_rejected;
    return result;
  }
  if (!bindings.move_allowed(1, unit, mode)) {
    result.status = PreviewMoveArmyStatus::validation_failed;
    return result;
  }
  void *const effective_origin =
      ResolveMilitaryMoveOrigin(bindings, unit, target, mode == 1);
  if (effective_origin == nullptr) {
    result.status = PreviewMoveArmyStatus::origin_unavailable;
    return result;
  }
  const auto effective_id = LoadAt<std::int32_t>(effective_origin, kProvinceId);
  const bool effective_is_observed = effective_origin == observed_origin;
  if (world.resolve_province(world.context, effective_id) != effective_origin ||
      (!effective_is_observed &&
       (selected->route_province_ids.empty() ||
        selected->route_province_ids.front() != effective_id))) {
    result.status = PreviewMoveArmyStatus::origin_unavailable;
    return result;
  }
  result.origin_province_id = selected->current_province_id;
  MoveUnitCommand command{};
  command.header = Header(bindings.move_primary, bindings.move_secondary);
  command.unit_id = unit_id;
  command.province_id = province_id;
  command.mode = mode;
  if (bindings.construct_move_path(command.path.data()) != command.path.data()) {
    return result;
  }
  CommandCleanup cleanup{bindings.destroy_move, &command, 0};
  if (effective_origin == target) {
    if (!effective_is_observed) {
      result.route_province_ids.push_back(effective_id);
    }
    result.status = PreviewMoveArmyStatus::available;
    return result;
  }
  alignas(8) std::array<std::byte, 0x70> path_context{};
  if (bindings.construct_path_context(path_context.data(), unit) !=
          path_context.data() ||
      !bindings.build_route(path_context.data(), effective_origin, target,
                             2, command.path.data())) {
    result.status = PreviewMoveArmyStatus::route_unavailable;
    return result;
  }
  const auto entries = LoadAt<void *>(command.path.data(), 0);
  const auto capacity = LoadAt<std::int32_t>(command.path.data(), 8);
  const auto count = LoadAt<std::int32_t>(command.path.data(), 0x0C);
  if (entries == nullptr || capacity < 0 || count < 1 || count > capacity ||
      count > kMaximumRouteEntries) {
    result.status = PreviewMoveArmyStatus::route_unavailable;
    return result;
  }
  std::vector<std::int32_t> route;
  route.reserve(static_cast<std::size_t>(count) + 1);
  if (!effective_is_observed) {
    route.push_back(effective_id);
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const auto entry = LoadAt<void *>(entries,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (entry == nullptr) {
      result.status = PreviewMoveArmyStatus::route_unavailable;
      return result;
    }
    const auto id = LoadAt<std::int32_t>(entry, 0);
    if (world.resolve_province(world.context, id) == nullptr) {
      result.status = PreviewMoveArmyStatus::route_unavailable;
      return result;
    }
    route.push_back(id);
  }
  if (route.back() != province_id) {
    result.status = PreviewMoveArmyStatus::route_unavailable;
    return result;
  }
  result.route_province_ids = std::move(route);
  result.status = PreviewMoveArmyStatus::available;
  return result;
}

DisbandArmyResult SubmitDisbandArmy(const MilitaryBindings &bindings,
                                    const MilitaryWorldAccess &world,
                                    std::int32_t unit_id) noexcept {
  if (!CanSubmit(bindings) || world.resolve_unit == nullptr ||
      bindings.validate_disband == nullptr || bindings.disband_primary == 0 ||
      bindings.disband_secondary == 0) {
    return DisbandArmyResult::unavailable;
  }
  Snapshot current{};
  if (!ReadCurrent(world, current)) {
    return DisbandArmyResult::unavailable;
  }
  void *const unit = world.resolve_unit(world.context, unit_id);
  if (unit == nullptr) {
    return DisbandArmyResult::army_not_found;
  }
  if (FindControllable(current, unit_id) == nullptr) {
    return DisbandArmyResult::army_not_controllable;
  }
  const auto army_id = LoadAt<std::int32_t>(unit, kUnitInternalArmyId);
  if (!bindings.validate_disband(1, army_id, nullptr)) {
    return DisbandArmyResult::army_not_controllable;
  }
  DisbandUnitCommand command{};
  command.header = Header(bindings.disband_primary, bindings.disband_secondary);
  command.internal_army_id = army_id;
  return bindings.submit_copy(bindings.submit_context, &command, 0x0E)
             ? DisbandArmyResult::submitted
             : DisbandArmyResult::unavailable;
}

SplitArmyHalfResult SubmitSplitArmyHalf(const MilitaryBindings &bindings,
                                        const MilitaryWorldAccess &world,
                                        std::int32_t unit_id) noexcept {
  if (!CanSubmit(bindings) || world.resolve_unit == nullptr ||
      bindings.validate_split == nullptr || bindings.destroy_split == nullptr ||
      bindings.split_primary == 0 || bindings.split_secondary == 0) {
    return SplitArmyHalfResult::unavailable;
  }
  Snapshot current{};
  if (!ReadCurrent(world, current)) {
    return SplitArmyHalfResult::unavailable;
  }
  if (!HasLivingPlayer(current)) {
    return SplitArmyHalfResult::no_played_character;
  }
  void *const unit = world.resolve_unit(world.context, unit_id);
  if (unit == nullptr) {
    return SplitArmyHalfResult::army_not_found;
  }
  if (FindControllable(current, unit_id) == nullptr) {
    return SplitArmyHalfResult::army_not_controllable;
  }
  const auto army_id = LoadAt<std::int32_t>(unit, kUnitInternalArmyId);
  if (!bindings.validate_split(1, army_id, current.played_character_id, nullptr)) {
    return SplitArmyHalfResult::validator_rejected;
  }
  SplitHalfUnitCommand command{};
  command.header = Header(bindings.split_primary, bindings.split_secondary);
  command.character_id = current.played_character_id;
  command.internal_army_id = army_id;
  CommandCleanup cleanup{bindings.destroy_split, &command, 0};
  return bindings.submit_copy(bindings.submit_context, &command, 0x0E)
             ? SplitArmyHalfResult::split_submitted
             : SplitArmyHalfResult::submission_failed;
}

MergeArmiesResult SubmitMergeArmies(const MilitaryBindings &bindings,
                                    const MilitaryWorldAccess &world,
                                    std::int32_t destination_unit_id,
                                    std::int32_t source_unit_id) noexcept {
  if (!CanSubmit(bindings) || world.resolve_unit == nullptr ||
      bindings.create_merge == nullptr || bindings.append_int_range == nullptr ||
      bindings.validate_merge == nullptr || bindings.destroy_merge == nullptr ||
      bindings.merge_primary == 0 || bindings.merge_secondary == 0) {
    return MergeArmiesResult::unavailable;
  }
  Snapshot current{};
  if (!ReadCurrent(world, current)) {
    return MergeArmiesResult::unavailable;
  }
  if (!HasLivingPlayer(current)) {
    return MergeArmiesResult::no_played_character;
  }
  if (destination_unit_id == source_unit_id) {
    return MergeArmiesResult::same_army;
  }
  if (world.resolve_unit(world.context, destination_unit_id) == nullptr) {
    return MergeArmiesResult::destination_not_found;
  }
  if (world.resolve_unit(world.context, source_unit_id) == nullptr) {
    return MergeArmiesResult::source_not_found;
  }
  if (FindControllable(current, destination_unit_id) == nullptr) {
    return MergeArmiesResult::destination_not_controllable;
  }
  if (FindControllable(current, source_unit_id) == nullptr) {
    return MergeArmiesResult::source_not_controllable;
  }
  auto *const command = static_cast<MergeUnitCommand *>(bindings.create_merge());
  if (command == nullptr) {
    return MergeArmiesResult::unavailable;
  }
  CommandCleanup cleanup{bindings.destroy_merge, command, 1};
  if (command->header.primary_vtable != bindings.merge_primary ||
      command->header.secondary_vtable != bindings.merge_secondary ||
      command->source_unit_ids.data != nullptr ||
      command->source_unit_ids.capacity != 0 ||
      command->source_unit_ids.count != 0 ||
      command->source_unit_ids.allocator == nullptr) {
    return MergeArmiesResult::unavailable;
  }
  command->kind = 1;
  command->destination_unit_id = destination_unit_id;
  bindings.append_int_range(&command->source_unit_ids, 0, &source_unit_id,
                            &source_unit_id + 1);
  if (command->source_unit_ids.data == nullptr ||
      command->source_unit_ids.capacity < 1 || command->source_unit_ids.count != 1 ||
      command->source_unit_ids.data[0] != source_unit_id) {
    return MergeArmiesResult::unavailable;
  }
  if (!bindings.validate_merge(command, nullptr)) {
    return MergeArmiesResult::validator_rejected;
  }
  return bindings.submit_copy(bindings.submit_context, command, 0x0E)
             ? MergeArmiesResult::merge_submitted
             : MergeArmiesResult::submission_failed;
}

StartAssaultResult SubmitStartAssault(const MilitaryBindings &bindings,
                                      const MilitaryWorldAccess &world,
                                      std::int32_t siege_id) noexcept {
  if (!CanSubmit(bindings) || world.resolve_siege == nullptr ||
      bindings.validate_start == nullptr || bindings.destroy_assault == nullptr ||
      bindings.start_primary == 0 || bindings.start_secondary == 0) {
    return StartAssaultResult::unavailable;
  }
  Snapshot current{};
  if (!ReadCurrent(world, current)) {
    return StartAssaultResult::unavailable;
  }
  if (!HasLivingPlayer(current)) {
    return StartAssaultResult::no_played_character;
  }
  void *const siege = world.resolve_siege(world.context, siege_id);
  if (siege == nullptr || !ValidSiegeProvince(world, siege, siege_id)) {
    return StartAssaultResult::siege_not_found;
  }
  const auto active = LoadAt<std::uint8_t>(siege, kSiegeAssaultActive);
  if (active > 1) {
    return StartAssaultResult::unavailable;
  }
  if (active != 0) {
    return StartAssaultResult::assault_already_active;
  }
  if (!bindings.validate_start(1, current.played_character_id, siege_id, nullptr)) {
    return StartAssaultResult::validator_rejected;
  }
  AssaultSiegeCommand command{};
  command.header = Header(bindings.start_primary, bindings.start_secondary);
  command.character_id = current.played_character_id;
  command.siege_id = siege_id;
  CommandCleanup cleanup{bindings.destroy_assault, &command, 0};
  return bindings.submit_copy(bindings.submit_context, &command, 0x0E)
             ? StartAssaultResult::start_submitted
             : StartAssaultResult::submission_failed;
}

StopAssaultResult SubmitStopAssault(const MilitaryBindings &bindings,
                                    const MilitaryWorldAccess &world,
                                    std::int32_t siege_id) noexcept {
  if (!CanSubmit(bindings) || world.resolve_siege == nullptr ||
      bindings.validate_stop == nullptr || bindings.destroy_assault == nullptr ||
      bindings.stop_primary == 0 || bindings.stop_secondary == 0) {
    return StopAssaultResult::unavailable;
  }
  Snapshot current{};
  if (!ReadCurrent(world, current)) {
    return StopAssaultResult::unavailable;
  }
  if (!HasLivingPlayer(current)) {
    return StopAssaultResult::no_played_character;
  }
  void *const siege = world.resolve_siege(world.context, siege_id);
  if (siege == nullptr || !ValidSiegeProvince(world, siege, siege_id)) {
    return StopAssaultResult::siege_not_found;
  }
  const auto active = LoadAt<std::uint8_t>(siege, kSiegeAssaultActive);
  if (active > 1) {
    return StopAssaultResult::unavailable;
  }
  if (active == 0) {
    return StopAssaultResult::assault_not_active;
  }
  if (!bindings.validate_stop(1, current.played_character_id, siege_id, nullptr)) {
    return StopAssaultResult::validator_rejected;
  }
  AssaultSiegeCommand command{};
  command.header = Header(bindings.stop_primary, bindings.stop_secondary);
  command.character_id = current.played_character_id;
  command.siege_id = siege_id;
  CommandCleanup cleanup{bindings.destroy_assault, &command, 0};
  return bindings.submit_copy(bindings.submit_context, &command, 0x0E)
             ? StopAssaultResult::stop_submitted
             : StopAssaultResult::submission_failed;
}

} // namespace xar::ck3_12002
