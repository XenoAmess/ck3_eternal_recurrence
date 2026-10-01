#include "xar_bridge/ck3_12002_world.hpp"

#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_province.hpp"

#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12002 {
namespace {
constexpr std::int32_t kMaximumStorageCapacity = 1'048'576;
constexpr std::int32_t kMaximumWarParticipants = 65'536;
constexpr std::int32_t kMaximumTargetTitles = 4'096;

template <typename T>
T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

void *WarStorage(const WorldBindings &bindings) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      *bindings.game_state_slot == nullptr) {
    return nullptr;
  }
  void *const data = Load<void *>(*bindings.game_state_slot, 0xA0);
  return data == nullptr
             ? nullptr
             : Load<void *>(data, kWorldWarManagerOffset + 0x20);
}

bool ReadStorage(const WorldBindings &bindings, void *&slots,
                  std::int32_t &capacity) noexcept {
  slots = nullptr;
  capacity = 0;
  void *const storage = WarStorage(bindings);
  if (storage == nullptr) {
    return false;
  }
  slots = Load<void *>(storage, 0x20);
  capacity = Load<std::int32_t>(storage, 0x2C);
  return capacity >= 0 && capacity <= kMaximumStorageCapacity &&
         (capacity == 0 || slots != nullptr);
}

void *Character(const WorldBindings &bindings, std::int32_t id) noexcept {
  if (id == -1 || bindings.character_storage_slot == nullptr ||
      *bindings.character_storage_slot == nullptr) {
    return nullptr;
  }
  void *const storage = *bindings.character_storage_slot;
  void *const slots = Load<void *>(storage, 0x20);
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (slots == nullptr || capacity <= 0 || capacity > kMaximumStorageCapacity ||
      index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const character = Load<void *>(slots, index * 0x10ULL + 8);
  return character != nullptr && Load<std::int32_t>(character, 0x18) == id
             ? character
             : nullptr;
}

void ReadOpponentRaiseProvince(const WorldBindings &bindings,
                               const ProvinceBindings &provinces,
                               game::ActiveWarSnapshot &war) noexcept {
  if (bindings.get_character_capital == nullptr ||
      bindings.resolve_raise_province == nullptr) {
    return;
  }
  void *const character =
      Character(bindings, war.primary_opponent_character_id);
  if (character == nullptr) {
    return;
  }
  void *const capital = bindings.get_character_capital(character);
  if (capital == nullptr ||
      ResolveObjectiveProvince(provinces, Load<std::int32_t>(capital, 0x10)) !=
          capital) {
    return;
  }
  // Native default range values are 0 and -1, as in the new raise path.
  void *const province =
      bindings.resolve_raise_province(character, capital, 0, -1);
  if (province == nullptr) {
    return;
  }
  const auto id = Load<std::int32_t>(province, 0x10);
  if (ResolveObjectiveProvince(provinces, id) == province) {
    war.enemy_primary_default_raise_province_id = id;
  }
}
} // namespace

WorldBindings BindWorldImage(std::uintptr_t image_base,
                             std::string_view executable_sha256) noexcept {
  WorldBindings bindings{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) {
    return bindings;
  }
  bindings.enabled = true;
  bindings.game_state_slot =
      reinterpret_cast<void **>(image_base + kGameStateSlotRva);
  bindings.contains_war_participant =
      reinterpret_cast<ContainsWarParticipant12002>(
          image_base + kWorldContainsParticipantRva);
  bindings.get_war_score = reinterpret_cast<GetWarScore12002>(
      image_base + kWorldGetWarScoreRva);
  bindings.character_storage_slot =
      reinterpret_cast<void **>(image_base + kCharacterStorageSlotRva);
  bindings.get_character_capital =
      reinterpret_cast<WorldCharacterCapitalGetter12002>(
          image_base + kWorldCharacterCapitalRva);
  bindings.resolve_raise_province =
      reinterpret_cast<WorldRaiseProvinceSelector12002>(
          image_base + kWorldRaiseProvinceSelectorRva);
  return bindings;
}

void *ResolveWar(const WorldBindings &bindings, std::int32_t war_id) noexcept {
  if (war_id == -1) {
    return nullptr;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadStorage(bindings, slots, capacity)) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(war_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) {
    return nullptr;
  }
  void *const war = Load<void *>(slots, index * 0x10ULL + 8);
  if (war == nullptr || Load<std::int32_t>(war, kWorldWarIdOffset) != war_id ||
      Load<std::uint8_t>(war, kWorldWarEndedOffset) != 0) {
    return nullptr;
  }
  return war;
}

bool ReadWarParticipantIds(const void *side,
                           std::vector<std::int32_t> &output) noexcept {
  output.clear();
  if (side == nullptr) {
    return false;
  }
  const auto capacity = Load<std::int32_t>(side, 0x10);
  const auto count = Load<std::int32_t>(side, 0x14);
  void *const records = Load<void *>(side, 8);
  if (capacity < 0 || count < 0 || count > capacity ||
      capacity > kMaximumWarParticipants || (count != 0 && records == nullptr)) {
    return false;
  }
  output.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    void *const participant = Load<void *>(records, index * sizeof(void *));
    if (participant == nullptr) {
      output.clear();
      return false;
    }
    const auto id = Load<std::int32_t>(participant, 8);
    if (id == -1) {
      output.clear();
      return false;
    }
    if (std::find(output.begin(), output.end(), id) == output.end()) {
      output.push_back(id);
    }
  }
  return true;
}

bool ReadWarTargetTitleIds(const void *war,
                           std::vector<std::int32_t> &output) noexcept {
  output.clear();
  if (war == nullptr) {
    return false;
  }
  const auto capacity = Load<std::int32_t>(war, 0x278);
  const auto count = Load<std::int32_t>(war, 0x27C);
  void *const ids = Load<void *>(war, kWorldWarTargetTitleIdsOffset);
  if (capacity < 0 || count < 0 || count > capacity ||
      capacity > kMaximumTargetTitles || (count != 0 && ids == nullptr)) {
    return false;
  }
  output.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    const auto id = Load<std::int32_t>(ids, index * sizeof(std::int32_t));
    if (id == -1) {
      output.clear();
      return false;
    }
    output.push_back(id);
  }
  return true;
}

WorldReadResult ReadActiveWars(
    const WorldBindings &bindings, std::int32_t played_character_id,
    std::span<const game::ArmySnapshot> all_armies,
    std::vector<game::ActiveWarSnapshot> &output) noexcept {
  output.clear();
  if (!bindings.enabled || played_character_id == -1 ||
      bindings.contains_war_participant == nullptr ||
      bindings.get_war_score == nullptr) {
    return WorldReadResult::unavailable;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadStorage(bindings, slots, capacity)) {
    return WorldReadResult::unavailable;
  }
  bool partial = false;
  for (std::int32_t index = 0; index < capacity; ++index) {
    void *const war = Load<void *>(slots, index * 0x10ULL + 8);
    if (war == nullptr || Load<std::uint8_t>(war, kWorldWarEndedOffset) != 0) {
      continue;
    }
    const auto id = Load<std::int32_t>(war, kWorldWarIdOffset);
    if (id == -1 || (static_cast<std::uint32_t>(id) & 0x00FFFFFFU) !=
                       static_cast<std::uint32_t>(index)) {
      partial = true;
      continue;
    }
    const void *const attackers = static_cast<const std::byte *>(war) + 0x20;
    const void *const defenders = static_cast<const std::byte *>(war) + 0x80;
    std::vector<std::int32_t> attacker_ids, defender_ids;
    if (!ReadWarParticipantIds(attackers, attacker_ids) ||
        !ReadWarParticipantIds(defenders, defender_ids)) {
      partial = true;
      continue;
    }
    const bool attacking =
        bindings.contains_war_participant(attackers, played_character_id);
    const bool defending =
        bindings.contains_war_participant(defenders, played_character_id);
    if (attacking == defending) {
      continue;
    }
    game::ActiveWarSnapshot row{};
    row.war_id = id;
    row.player_side = attacking ? game::PlayerWarSide::attacker
                               : game::PlayerWarSide::defender;
    row.player_is_primary_war_leader =
        Load<std::int32_t>(war, attacking ? 0x288 : 0x28C) ==
        played_character_id;
    row.primary_opponent_character_id =
        Load<std::int32_t>(war, attacking ? 0x28C : 0x288);
    if (!ReadWarTargetTitleIds(war, row.targeted_title_ids)) {
      partial = true;
      continue;
    }
    const auto score = bindings.get_war_score(war, nullptr);
    row.player_relative_war_score = attacking ? score : -score;
    const void *const allies = attacking ? attackers : defenders;
    const void *const enemies = attacking ? defenders : attackers;
    for (const auto &army : all_armies) {
      if (bindings.contains_war_participant(allies, army.owner_character_id)) {
        row.allied_armies.push_back(army);
      } else if (bindings.contains_war_participant(enemies,
                                                 army.owner_character_id)) {
        row.enemy_armies.push_back(army);
      }
    }
    output.push_back(std::move(row));
  }
  return partial ? WorldReadResult::partial : WorldReadResult::available;
}

WorldReadResult ReadWorldSnapshot(
    const WorldBindings &bindings, const ArmyBindings &army_bindings,
    const ProvinceBindings &province_bindings, const CoreSnapshotPrefix &prefix,
    game::Snapshot &output) noexcept {
  output.player_armies.clear();
  output.active_wars.clear();
  if (!prefix.map_ready || !prefix.has_played_character) {
    return WorldReadResult::available;
  }
  if (!bindings.enabled || !army_bindings.enabled ||
      !province_bindings.enabled) {
    return WorldReadResult::unavailable;
  }
  std::vector<game::ArmySnapshot> all_armies;
  if (!ReadArmiesForCharacters(army_bindings, {}, all_armies,
                               prefix.played_character_id)) {
    return WorldReadResult::unavailable;
  }
  for (const auto &army : all_armies) {
    if (army.owner_character_id == prefix.played_character_id) {
      output.player_armies.push_back(army);
    }
  }
  auto result = ReadActiveWars(bindings, prefix.played_character_id, all_armies,
                               output.active_wars);
  if (result == WorldReadResult::unavailable) {
    output.player_armies.clear();
    return result;
  }
  std::size_t remaining_province_budget = 256;
  for (auto &war : output.active_wars) {
    ReadOpponentRaiseProvince(bindings, province_bindings, war);
    if (!CollectObjectiveProvinceIds(province_bindings, war.targeted_title_ids,
                                     war.war_objective_province_ids)) {
      result = WorldReadResult::partial;
      continue;
    }
    for (const auto id : war.war_objective_province_ids) {
      if (remaining_province_budget == 0) {
        result = WorldReadResult::partial;
        break;
      }
      --remaining_province_budget;
      war.objective_province_states.push_back(ReadObjectiveProvince(
          province_bindings, id, all_armies, prefix.played_character_id,
          prefix.clock.paused));
    }
  }
  return result;
}

} // namespace xar::ck3_12002
