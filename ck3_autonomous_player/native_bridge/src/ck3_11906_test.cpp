#include "xar_bridge/ck3_11906.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>

namespace {

using xar::ck3_11906::Bindings;

std::array<std::byte, 0x78> g_player{};
std::array<std::byte, 0x1C2> g_active_event{};
std::array<std::byte, 0x1C0> g_event_data{};
std::array<std::byte, 0x40> g_pending_storage{};
std::array<std::byte, 0x20> g_pending_slots{};
std::array<std::byte, 0x5C8> g_pending_interaction{};
std::array<std::byte, 0x40> g_character_storage{};
std::array<std::byte, 0x30> g_character_slots{};
std::array<std::byte, 0x1D0> g_played_character{};
std::array<std::byte, 0xE0> g_player_character_entry{};
std::array<std::byte, sizeof(void *)> g_player_character_entries{};
std::array<std::byte, 0x40> g_war_storage{};
std::array<std::byte, 0x20> g_war_slots{};
std::array<std::byte, 0x360> g_war{};
std::array<std::byte, 0x10> g_attacker_participant{};
std::array<std::byte, 0x10> g_defender_participant{};
std::array<std::byte, sizeof(void *)> g_attacker_participants{};
std::array<std::byte, sizeof(void *)> g_defender_participants{};
std::array<std::byte, 0x40> g_army_storage{};
std::array<std::byte, 0x40> g_army_slots{};
std::array<std::byte, 0x178> g_player_army{};
std::array<std::byte, 0x178> g_enemy_army{};
std::array<std::byte, 0x20> g_player_province{};
std::array<std::byte, 0x20> g_enemy_province{};
std::array<std::byte, 4 * sizeof(void *)> g_provinces{};
void *g_pending_storage_pointer = nullptr;
void *g_character_storage_pointer = nullptr;
void *g_army_storage_pointer = nullptr;
void *g_expected_event_manager = nullptr;
bool g_has_active_event = true;
bool g_has_local_player = false;
bool g_submit_called = false;
bool g_raise_construct_called = false;
bool g_raise_validate_called = false;
bool g_raise_validate_result = true;
bool g_raise_destroy_called = false;
bool g_move_path_initialized = false;
bool g_move_destroy_called = false;
enum class ExpectedCommand {
  pause,
  resume,
  speed,
  event_option,
  auto_save,
  reply_accept,
  reply_reject,
  raise_troops,
  move_army,
  disband_army,
};
ExpectedCommand g_expected_command = ExpectedCommand::pause;

template <typename Value, std::size_t Size>
void Store(std::array<std::byte, Size> &target, std::size_t offset,
           Value value) {
  std::memcpy(target.data() + offset, &value, sizeof(value));
}

void *FixtureGetLocalPlayer(void *) {
  return g_has_local_player ? g_player.data() : nullptr;
}

void *FixtureGetCurrentEvent(void *event_manager) {
  if (event_manager != g_expected_event_manager || !g_has_active_event) {
    return nullptr;
  }
  return g_active_event.data();
}

bool FixtureContainsWarParticipant(void *container,
                                   std::int32_t character_id) {
  auto *const bytes = static_cast<std::byte *>(container);
  void *entries = nullptr;
  std::int32_t count = 0;
  std::memcpy(&entries, bytes + 0x08, sizeof(entries));
  std::memcpy(&count, bytes + 0x14, sizeof(count));
  for (std::int32_t index = 0; entries != nullptr && index < count; ++index) {
    void *entry = nullptr;
    std::memcpy(&entry, static_cast<std::byte *>(entries) +
                            static_cast<std::size_t>(index) * sizeof(void *),
                sizeof(entry));
    std::int32_t candidate_id = -1;
    if (entry != nullptr) {
      std::memcpy(&candidate_id, static_cast<std::byte *>(entry) + 0x08,
                  sizeof(candidate_id));
    }
    if (candidate_id == character_id) {
      return true;
    }
  }
  return false;
}

std::int32_t FixtureGetWarScore(void *war, void *context) {
  return war == g_war.data() && context == nullptr ? 37 : 0;
}

void *FixtureResolveDefaultRaiseProvince(void *character) {
  return character == g_played_character.data() ? g_player_province.data()
                                                 : nullptr;
}

void *FixtureConstructRaiseTroopsCommand(void *opaque_command,
                                         std::int32_t character_id,
                                         const void *opaque_entry) {
  auto *const command = static_cast<std::byte *>(opaque_command);
  std::int32_t province_id = -1;
  std::int32_t regiment_id = 0;
  std::memcpy(&province_id, opaque_entry, sizeof(province_id));
  std::memcpy(&regiment_id,
              static_cast<const std::byte *>(opaque_entry) + 4,
              sizeof(regiment_id));
  const std::uintptr_t primary = 0xBBBBBBBB;
  const std::uintptr_t secondary = 0xCCCCCCCC;
  const std::int32_t all_regiments = -1;
  const std::int32_t entry_count = 1;
  std::memcpy(command, &primary, sizeof(primary));
  std::memcpy(command + 0x18, &secondary, sizeof(secondary));
  std::memcpy(command + 0x20, &character_id, sizeof(character_id));
  std::memcpy(command + 0x40, &all_regiments, sizeof(all_regiments));
  std::memcpy(command + 0x44, &entry_count, sizeof(entry_count));
  command[0x48] = std::byte{0};
  g_raise_construct_called =
      character_id == 0x01000002 && province_id == 2 && regiment_id == -1;
  return opaque_command;
}

bool FixtureValidateRaiseTroopsCommand(void *opaque_command, void *context) {
  g_raise_validate_called =
      opaque_command != nullptr && context == nullptr;
  return g_raise_validate_result;
}

void *FixtureDestroyRaiseTroopsCommand(void *command,
                                       std::int32_t delete_flags) {
  g_raise_destroy_called = command != nullptr && delete_flags == 0;
  return command;
}

std::int32_t FixtureGetArmyMoveMode(void *army, void *province,
                                    std::int32_t direct_target) {
  return army == g_player_army.data() && province == g_enemy_province.data() &&
                 direct_target == 1
             ? 5
             : 2;
}

bool FixtureCanMoveArmy(std::int32_t command_kind, void *army,
                        std::int32_t move_mode) {
  return command_kind == 2 && army == g_player_army.data() && move_mode == 5;
}

void FixtureInitializeArmyMovePath(void *path_storage) {
  static_cast<std::byte *>(path_storage)[0] = std::byte{0x5A};
  g_move_path_initialized = true;
}

void *FixtureDestroyMoveArmyCommand(void *opaque_command,
                                    std::int32_t delete_flags) {
  auto *const command = static_cast<std::byte *>(opaque_command);
  g_move_destroy_called = delete_flags == 0 && command[0x38] == std::byte{0x5A};
  return opaque_command;
}

void FixtureSubmit(void *manager, void *opaque_command, std::uint32_t flags) {
  const auto *command = static_cast<const std::byte *>(opaque_command);
  std::uintptr_t primary = 0;
  std::uintptr_t secondary = 0;
  std::int32_t player_id = -1;
  std::memcpy(&primary, command, sizeof(primary));
  std::memcpy(&secondary, command + 0x18, sizeof(secondary));
  std::memcpy(&player_id, command + 0x20, sizeof(player_id));
  const auto paused = static_cast<std::uint8_t>(command[0x24]);
  const auto command_flags = static_cast<std::uint8_t>(command[0x08]);
  if (g_expected_command == ExpectedCommand::pause ||
      g_expected_command == ExpectedCommand::resume) {
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0x11111111 &&
                      secondary == 0x22222222 && command_flags == 0x08 &&
                      player_id == 41 &&
                      paused ==
                          (g_expected_command == ExpectedCommand::pause ? 1 : 0);
  } else if (g_expected_command == ExpectedCommand::speed) {
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0x33333333 &&
                      secondary == 0x44444444 && command_flags == 0 &&
                      player_id == 4;
  } else if (g_expected_command == ExpectedCommand::event_option) {
    std::int32_t option_index = -1;
    std::memcpy(&option_index, command + 0x24, sizeof(option_index));
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0x55555555 &&
                      secondary == 0x66666666 && command_flags == 0 &&
                      player_id == 77 && option_index == 2;
  } else if (g_expected_command == ExpectedCommand::auto_save) {
    std::uint64_t save_name_size = 0;
    std::uint64_t save_name_capacity = 0;
    std::memcpy(&save_name_size, command + 0x30, sizeof(save_name_size));
    std::memcpy(&save_name_capacity, command + 0x38,
                sizeof(save_name_capacity));
    const std::string save_name(reinterpret_cast<const char *>(command + 0x20),
                                save_name_size);
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0x77777777 &&
                      secondary == 0x88888888 && command_flags == 0x20 &&
                      save_name == xar::ck3_11906::kCheckpointSaveName &&
                      save_name_capacity == 15;
  } else if (g_expected_command == ExpectedCommand::reply_accept ||
             g_expected_command == ExpectedCommand::reply_reject) {
    std::int32_t reply = -1;
    std::memcpy(&reply, command + 0x24, sizeof(reply));
    g_submit_called =
        manager == reinterpret_cast<void *>(0x1234) && flags == 0x0E &&
        primary == 0x99999999 && secondary == 0xAAAAAAAA &&
        command_flags == 0 && player_id == 0x01000001 &&
        reply == (g_expected_command == ExpectedCommand::reply_accept ? 0 : 1);
  } else if (g_expected_command == ExpectedCommand::raise_troops) {
    std::int32_t all_regiments = 0;
    std::int32_t entry_count = 0;
    std::memcpy(&all_regiments, command + 0x40, sizeof(all_regiments));
    std::memcpy(&entry_count, command + 0x44, sizeof(entry_count));
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0xBBBBBBBB &&
                      secondary == 0xCCCCCCCC && player_id == 0x01000002 &&
                      all_regiments == -1 && entry_count == 1 &&
                      command[0x48] == std::byte{0};
  } else if (g_expected_command == ExpectedCommand::move_army) {
    std::int32_t army_id = -1;
    std::int32_t destination = -1;
    std::int32_t move_mode = -1;
    std::int32_t route_kind = -1;
    std::int32_t direct_target = -1;
    std::memcpy(&army_id, command + 0x24, sizeof(army_id));
    std::memcpy(&destination, command + 0x28, sizeof(destination));
    std::memcpy(&move_mode, command + 0x2C, sizeof(move_mode));
    std::memcpy(&route_kind, command + 0x30, sizeof(route_kind));
    std::memcpy(&direct_target, command + 0x34, sizeof(direct_target));
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0xDDDDDDDD &&
                      secondary == 0xEEEEEEEE && command_flags == 0 &&
                      player_id == 2 && army_id == 0x01000001 &&
                      destination == 3 && move_mode == 5 &&
                      route_kind == 2 && direct_target == 1 &&
                      command[0x38] == std::byte{0x5A};
  } else if (g_expected_command == ExpectedCommand::disband_army) {
    std::int32_t army_id = -1;
    std::memcpy(&army_id, command + 0x24, sizeof(army_id));
    g_submit_called = manager == reinterpret_cast<void *>(0x1234) &&
                      flags == 7 && primary == 0xFFFFFFFF &&
                      secondary == 0xABABABAB && command_flags == 0 &&
                      player_id == 2 && army_id == 0x01000001;
  }
}

int Fail(const char *message) {
  std::cerr << "FAIL: " << message << '\n';
  return 1;
}

} // namespace

int main() {
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x28> jomini_state{};
  std::array<std::byte, 0x200> players{};
  std::array<std::byte, 0x400> game_data{};
  void *game_state_pointer = game_state.data();
  void *jomini_state_pointer = jomini_state.data();
  Store(game_state, 0x08, std::int32_t{43'823'104});
  Store(game_state, 0x70, std::int32_t{3});
  Store(game_state, 0xA0, static_cast<void *>(game_data.data()));
  Store(jomini_state, 0x18, static_cast<void *>(players.data()));
  Store(jomini_state, 0x20, std::uint8_t{0});
  Store(players, 0x1F0, std::int32_t{41});
  Store(g_player, 0x70, std::int32_t{41});
  Store(g_active_event, 0x1B0, static_cast<void *>(g_event_data.data()));
  Store(g_active_event, 0x1BC, std::int32_t{77});
  Store(g_event_data, 0x1BC, std::int32_t{3});
  g_expected_event_manager = game_data.data();

  constexpr std::int32_t played_character_id = 0x01000002;
  Store(game_data, 0x158,
        static_cast<void *>(g_player_character_entries.data()));
  Store(game_data, 0x164, std::int32_t{1});
  Store(g_player_character_entries, 0,
        static_cast<void *>(g_player_character_entry.data()));
  Store(g_player_character_entry, 0xB0, played_character_id);
  Store(g_player_character_entry, 0xD8, std::int32_t{41});
  Store(g_character_storage, 0x20,
        static_cast<void *>(g_character_slots.data()));
  Store(g_character_storage, 0x2C, std::int32_t{3});
  Store(g_character_slots, 0x28,
        static_cast<void *>(g_played_character.data()));
  Store(g_played_character, 0x18, played_character_id);
  Store(g_played_character, 0x1C8, static_cast<void *>(nullptr));
  g_character_storage_pointer = g_character_storage.data();

  constexpr std::int32_t enemy_character_id = 0x01000003;
  constexpr std::int32_t player_army_id = 0x01000001;
  constexpr std::int32_t enemy_army_id = 0x01000002;
  constexpr std::int32_t active_war_id = 0x01000001;
  Store(g_player_province, 0x10, std::int32_t{2});
  Store(g_enemy_province, 0x10, std::int32_t{3});
  Store(g_provinces, 2 * sizeof(void *),
        static_cast<void *>(g_player_province.data()));
  Store(g_provinces, 3 * sizeof(void *),
        static_cast<void *>(g_enemy_province.data()));
  Store(game_data, 0x140, static_cast<void *>(g_provinces.data()));
  Store(game_data, 0x14C, std::int32_t{4});

  Store(g_player_army, 0x10, player_army_id);
  Store(g_player_army, 0x20,
        static_cast<void *>(g_player_province.data()));
  Store(g_player_army, 0x174, played_character_id);
  Store(g_enemy_army, 0x10, enemy_army_id);
  Store(g_enemy_army, 0x20,
        static_cast<void *>(g_enemy_province.data()));
  Store(g_enemy_army, 0x174, enemy_character_id);
  Store(g_army_slots, 0x18, static_cast<void *>(g_player_army.data()));
  Store(g_army_slots, 0x28, static_cast<void *>(g_enemy_army.data()));
  Store(g_army_storage, 0x20, static_cast<void *>(g_army_slots.data()));
  Store(g_army_storage, 0x2C, std::int32_t{4});
  g_army_storage_pointer = g_army_storage.data();

  Store(g_attacker_participant, 0x08, played_character_id);
  Store(g_defender_participant, 0x08, enemy_character_id);
  Store(g_attacker_participants, 0,
        static_cast<void *>(g_attacker_participant.data()));
  Store(g_defender_participants, 0,
        static_cast<void *>(g_defender_participant.data()));
  Store(g_war, 0x08, active_war_id);
  Store(g_war, 0x28, static_cast<void *>(g_attacker_participants.data()));
  Store(g_war, 0x34, std::int32_t{1});
  Store(g_war, 0x88, static_cast<void *>(g_defender_participants.data()));
  Store(g_war, 0x94, std::int32_t{1});
  Store(g_war, 0x358, static_cast<void *>(nullptr));
  Store(g_war_slots, 0x18, static_cast<void *>(g_war.data()));
  Store(g_war_storage, 0x20, static_cast<void *>(g_war_slots.data()));
  Store(g_war_storage, 0x2C, std::int32_t{2});
  Store(game_data, 0x220, static_cast<void *>(g_war_storage.data()));

  Bindings bindings{};
  bindings.enabled = true;
  bindings.game_state_slot = &game_state_pointer;
  bindings.jomini_state_slot = &jomini_state_pointer;
  bindings.command_manager = reinterpret_cast<void *>(0x1234);
  bindings.pause_primary_vtable = 0x11111111;
  bindings.pause_secondary_vtable = 0x22222222;
  bindings.set_speed_primary_vtable = 0x33333333;
  bindings.set_speed_secondary_vtable = 0x44444444;
  bindings.select_event_option_primary_vtable = 0x55555555;
  bindings.select_event_option_secondary_vtable = 0x66666666;
  bindings.auto_save_primary_vtable = 0x77777777;
  bindings.auto_save_secondary_vtable = 0x88888888;
  bindings.reply_character_interaction_primary_vtable = 0x99999999;
  bindings.reply_character_interaction_secondary_vtable = 0xAAAAAAAA;
  bindings.raise_troops_primary_vtable = 0xBBBBBBBB;
  bindings.raise_troops_secondary_vtable = 0xCCCCCCCC;
  bindings.move_army_primary_vtable = 0xDDDDDDDD;
  bindings.move_army_secondary_vtable = 0xEEEEEEEE;
  bindings.disband_army_primary_vtable = 0xFFFFFFFF;
  bindings.disband_army_secondary_vtable = 0xABABABAB;
  bindings.pending_character_interaction_storage_slot =
      &g_pending_storage_pointer;
  bindings.character_storage_slot = &g_character_storage_pointer;
  bindings.army_storage_slot = &g_army_storage_pointer;
  bindings.player_character_manager_offset = 0x100;
  bindings.war_manager_offset = 0x200;
  bindings.submit_command = FixtureSubmit;
  bindings.get_local_player = FixtureGetLocalPlayer;
  bindings.get_current_event = FixtureGetCurrentEvent;
  bindings.contains_war_participant = FixtureContainsWarParticipant;
  bindings.get_war_score = FixtureGetWarScore;
  bindings.resolve_default_raise_province =
      FixtureResolveDefaultRaiseProvince;
  bindings.construct_raise_troops_command =
      FixtureConstructRaiseTroopsCommand;
  bindings.validate_raise_troops_command =
      FixtureValidateRaiseTroopsCommand;
  bindings.destroy_raise_troops_command =
      FixtureDestroyRaiseTroopsCommand;
  bindings.get_army_move_mode = FixtureGetArmyMoveMode;
  bindings.can_move_army = FixtureCanMoveArmy;
  bindings.initialize_army_move_path = FixtureInitializeArmyMovePath;
  bindings.destroy_move_army_command = FixtureDestroyMoveArmyCommand;

  xar::ck3_11906::Snapshot snapshot{};
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot)) {
    return Fail("fixture snapshot was unavailable");
  }
  if (snapshot.date_raw != 43'823'104 || snapshot.speed != 4 ||
      snapshot.paused || snapshot.player_id != 41 ||
      snapshot.map_ready ||
      snapshot.has_played_character || snapshot.played_character_id != -1 ||
      snapshot.played_character_alive ||
      !snapshot.has_active_event || snapshot.active_event_instance_id != 77 ||
      snapshot.active_event_option_count != 3 ||
      snapshot.has_pending_character_interaction ||
      snapshot.pending_character_interaction_id != -1 ||
      snapshot.pending_sender_character_id != -1) {
    return Fail("fixture snapshot fields did not match the pinned offsets");
  }
  g_has_local_player = true;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.map_ready || !snapshot.has_played_character ||
      snapshot.played_character_id != played_character_id ||
      !snapshot.played_character_alive || snapshot.player_armies.size() != 1 ||
      snapshot.player_armies[0].army_id != player_army_id ||
      snapshot.player_armies[0].owner_character_id != played_character_id ||
      !snapshot.player_armies[0].has_current_province ||
      snapshot.player_armies[0].current_province_id != 2 ||
      !snapshot.player_armies[0].controllable ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].war_id != active_war_id ||
      snapshot.active_wars[0].player_side !=
          xar::ck3_11906::PlayerWarSide::attacker ||
      snapshot.active_wars[0].player_relative_war_score != 37 ||
      snapshot.active_wars[0].allied_armies.size() != 1 ||
      snapshot.active_wars[0].enemy_armies.size() != 1 ||
      snapshot.active_wars[0].enemy_armies[0].army_id != enemy_army_id ||
      snapshot.active_wars[0].enemy_armies[0].current_province_id != 3) {
    return Fail("map-ready did not follow the resolved local player");
  }
  Store(g_attacker_participant, 0x08, enemy_character_id);
  Store(g_defender_participant, 0x08, played_character_id);
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].player_side !=
          xar::ck3_11906::PlayerWarSide::defender ||
      snapshot.active_wars[0].player_relative_war_score != -37 ||
      snapshot.active_wars[0].allied_armies.size() != 1 ||
      snapshot.active_wars[0].allied_armies[0].army_id != player_army_id ||
      snapshot.active_wars[0].enemy_armies.size() != 1 ||
      snapshot.active_wars[0].enemy_armies[0].army_id != enemy_army_id) {
    return Fail("defender war score and army sides did not project relatively");
  }
  Store(g_attacker_participant, 0x08, played_character_id);
  Store(g_defender_participant, 0x08, enemy_character_id);
  Store(g_played_character, 0x1C8,
        reinterpret_cast<void *>(0x12345678));
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.has_played_character || snapshot.played_character_alive) {
    return Fail("played-character death data did not project alive=false");
  }
  Store(g_played_character, 0x1C8, static_cast<void *>(nullptr));
  g_has_local_player = false;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitSaveCheckpoint(bindings).status !=
          xar::ck3_11906::SaveCheckpointStatus::map_not_ready ||
      g_submit_called) {
    return Fail("save-checkpoint ignored the early map-ready gate");
  }
  g_has_local_player = true;
  g_expected_command = ExpectedCommand::auto_save;
  const auto save_result = xar::ck3_11906::SubmitSaveCheckpoint(bindings);
  if (save_result.status !=
          xar::ck3_11906::SaveCheckpointStatus::submitted ||
      save_result.date_raw != 43'823'104 || !g_submit_called) {
    return Fail("save-checkpoint did not submit the pinned autosave command");
  }
  g_expected_command = ExpectedCommand::pause;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitPauseMap(bindings) !=
          xar::ck3_11906::PauseSubmitResult::submitted ||
      !g_submit_called) {
    return Fail("pause-map did not construct and submit the pinned command");
  }

  g_expected_command = ExpectedCommand::speed;
  g_submit_called = false;
  if (!xar::ck3_11906::SubmitSetSpeed(bindings, 5) || !g_submit_called ||
      xar::ck3_11906::SubmitSetSpeed(bindings, 0) ||
      xar::ck3_11906::SubmitSetSpeed(bindings, 6)) {
    return Fail("set-speed did not construct the pinned command for 1..5");
  }

  g_expected_command = ExpectedCommand::event_option;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitSelectEventOption(bindings, 2) !=
          xar::ck3_11906::SelectEventOptionResult::submitted ||
      !g_submit_called) {
    return Fail("event option did not construct and submit the pinned command");
  }
  g_submit_called = false;
  if (xar::ck3_11906::SubmitSelectEventOption(bindings, -1) !=
          xar::ck3_11906::SelectEventOptionResult::option_out_of_range ||
      xar::ck3_11906::SubmitSelectEventOption(bindings, 3) !=
          xar::ck3_11906::SelectEventOptionResult::option_out_of_range ||
      g_submit_called) {
    return Fail("event option accepted an index outside the active event");
  }

  g_has_active_event = false;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.has_active_event || snapshot.active_event_instance_id != -1 ||
      snapshot.active_event_option_count != 0 ||
      xar::ck3_11906::SubmitSelectEventOption(bindings, 0) !=
          xar::ck3_11906::SelectEventOptionResult::no_active_event) {
    return Fail("no-active-event state was not represented explicitly");
  }
  g_has_active_event = true;

  Store(g_pending_storage, 0x20,
        static_cast<void *>(g_pending_slots.data()));
  Store(g_pending_storage, 0x2C, std::int32_t{2});
  Store(g_pending_slots, 0x18,
        static_cast<void *>(g_pending_interaction.data()));
  Store(g_pending_interaction, 0x10, std::int32_t{0x01000001});
  Store(g_pending_interaction, 0x2F0, std::int32_t{8675309});
  Store(g_pending_interaction, 0x5C6, std::uint8_t{0});
  g_pending_storage_pointer = g_pending_storage.data();
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      !snapshot.has_pending_character_interaction ||
      snapshot.pending_character_interaction_id != 0x01000001 ||
      snapshot.pending_sender_character_id != 8675309 ||
      snapshot.pending_auto_accept_notification) {
    return Fail("pending character interaction snapshot did not match");
  }
  g_expected_command = ExpectedCommand::reply_accept;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitReplyToPendingInteraction(
          bindings, xar::ck3_11906::PendingInteractionReply::accept) !=
          xar::ck3_11906::ReplyPendingInteractionResult::submitted ||
      !g_submit_called) {
    return Fail("pending interaction accept command layout did not match");
  }
  g_expected_command = ExpectedCommand::reply_reject;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitReplyToPendingInteraction(
          bindings, xar::ck3_11906::PendingInteractionReply::reject) !=
          xar::ck3_11906::ReplyPendingInteractionResult::submitted ||
      !g_submit_called) {
    return Fail("pending interaction reject command layout did not match");
  }
  Store(g_pending_interaction, 0x5C6, std::uint8_t{1});
  g_submit_called = false;
  if (xar::ck3_11906::SubmitReplyToPendingInteraction(
          bindings, xar::ck3_11906::PendingInteractionReply::accept) !=
          xar::ck3_11906::ReplyPendingInteractionResult::
              acknowledgement_required ||
      g_submit_called) {
    return Fail("auto-accept notification was submitted as a normal reply");
  }
  g_pending_storage_pointer = nullptr;
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot) ||
      snapshot.has_pending_character_interaction ||
      xar::ck3_11906::SubmitReplyToPendingInteraction(
          bindings, xar::ck3_11906::PendingInteractionReply::accept) !=
          xar::ck3_11906::ReplyPendingInteractionResult::
              no_pending_interaction) {
    return Fail("no-pending-interaction state was not explicit");
  }

  g_expected_command = ExpectedCommand::raise_troops;
  g_submit_called = false;
  g_raise_construct_called = false;
  g_raise_validate_called = false;
  g_raise_destroy_called = false;
  if (xar::ck3_11906::SubmitRaiseTroopsDefault(bindings) !=
          xar::ck3_11906::RaiseTroopsResult::submitted ||
      !g_raise_construct_called || !g_raise_validate_called ||
      !g_submit_called || !g_raise_destroy_called) {
    return Fail("raise-troops did not use the native construct/validate queue");
  }
  g_raise_validate_result = false;
  g_submit_called = false;
  g_raise_destroy_called = false;
  if (xar::ck3_11906::SubmitRaiseTroopsDefault(bindings) !=
          xar::ck3_11906::RaiseTroopsResult::validation_failed ||
      g_submit_called || !g_raise_destroy_called) {
    return Fail("raise-troops submitted after native validation failed");
  }
  g_raise_validate_result = true;

  g_expected_command = ExpectedCommand::move_army;
  g_submit_called = false;
  g_move_path_initialized = false;
  g_move_destroy_called = false;
  if (xar::ck3_11906::SubmitMoveArmy(bindings, player_army_id, 3) !=
          xar::ck3_11906::MoveArmyResult::submitted ||
      !g_move_path_initialized || !g_submit_called ||
      !g_move_destroy_called) {
    return Fail("move-army did not use the native mode/path/queue layout");
  }
  g_submit_called = false;
  if (xar::ck3_11906::SubmitMoveArmy(bindings, enemy_army_id, 2) !=
          xar::ck3_11906::MoveArmyResult::army_not_controllable ||
      xar::ck3_11906::SubmitMoveArmy(bindings, player_army_id, 99) !=
          xar::ck3_11906::MoveArmyResult::province_not_found ||
      g_submit_called) {
    return Fail("move-army ignored controllability or province resolution");
  }

  g_expected_command = ExpectedCommand::disband_army;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitDisbandArmy(bindings, player_army_id) !=
          xar::ck3_11906::DisbandArmyResult::submitted ||
      !g_submit_called) {
    return Fail("disband-army did not submit the pinned command layout");
  }
  g_submit_called = false;
  if (xar::ck3_11906::SubmitDisbandArmy(bindings, enemy_army_id) !=
          xar::ck3_11906::DisbandArmyResult::army_not_controllable ||
      g_submit_called) {
    return Fail("disband-army accepted a non-player army");
  }

  Store(jomini_state, 0x20, std::uint8_t{1});
  g_expected_command = ExpectedCommand::pause;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitPauseMap(bindings) !=
          xar::ck3_11906::PauseSubmitResult::already_paused ||
      g_submit_called) {
    return Fail("already-paused fixture should be idempotent");
  }

  g_expected_command = ExpectedCommand::resume;
  g_submit_called = false;
  if (xar::ck3_11906::SubmitResumeMap(bindings) !=
          xar::ck3_11906::ResumeSubmitResult::submitted ||
      !g_submit_called) {
    return Fail("resume-map did not submit paused=false");
  }
  Store(jomini_state, 0x20, std::uint8_t{0});
  g_submit_called = false;
  if (xar::ck3_11906::SubmitResumeMap(bindings) !=
          xar::ck3_11906::ResumeSubmitResult::already_running ||
      g_submit_called) {
    return Fail("already-running fixture should be idempotent");
  }

  bindings.enabled = false;
  if (xar::ck3_11906::ReadSnapshot(bindings, snapshot)) {
    return Fail("disabled build binding exposed game state");
  }
  std::cout << "PASS: snapshot=1 active_event_snapshot=1 "
               "pause_resume_command_layout=1 "
               "set_speed_zero_based_mapping=1 "
               "select_event_option_layout=1 auto_save_layout=1 "
               "pending_interaction_snapshot=1 "
               "reply_character_interaction_layout=1 "
               "played_character_snapshot=1 alive_dead_projection=1 "
               "war_army_snapshot=1 relative_war_score=1 "
               "raise_troops_command=1 move_army_command=1 "
               "disband_army_command=1 "
               "map_ready_gate=1 exact_build_gate=1\n";
  return 0;
}
