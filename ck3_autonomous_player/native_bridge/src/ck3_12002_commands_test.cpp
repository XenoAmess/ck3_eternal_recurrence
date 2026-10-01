#include "xar_bridge/ck3_12002_commands.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using namespace xar::ck3_12002;

struct FixtureTable {
  std::array<std::uintptr_t, 9> entries{};
  std::size_t object_size = 0;
};
struct FixtureManager {
  bool accept = true;
  std::uint32_t last_channel_flags = 0;
  std::size_t submitted = 0;
  std::vector<std::byte> last_copy;
  std::vector<void *> pending;
};
std::size_t clones = 0;
std::size_t deletes = 0;
void *fixture_player = nullptr;

void *DeleteFixtureCommand(void *command, std::uint32_t flags) {
  if (flags != 1) {
    std::terminate();
  }
  ++deletes;
  delete[] static_cast<std::byte *>(command);
  return nullptr;
}
void **CloneFixtureCommand(const void *command, void **result) {
  const FixtureTable *table = nullptr;
  std::memcpy(&table, command, sizeof(table));
  auto *copy = new std::byte[table->object_size];
  std::memcpy(copy, command, table->object_size);
  *result = copy;
  ++clones;
  return result;
}
bool QueueFixtureCommand(void *context, void **owned, std::uint32_t flags) {
  auto &manager = *static_cast<FixtureManager *>(context);
  manager.last_channel_flags = flags;
  const FixtureTable *table = nullptr;
  std::memcpy(&table, *owned, sizeof(table));
  manager.last_copy.assign(static_cast<const std::byte *>(*owned),
                           static_cast<const std::byte *>(*owned) +
                               table->object_size);
  // A native manager assigns metadata to its clone. Check below that this
  // leaves the bridge's source untouched and that it retains only the copy.
  const std::uint32_t sequence = 0x12345678;
  std::memcpy(static_cast<std::byte *>(*owned) + 0x0C, &sequence,
              sizeof(sequence));
  if (!manager.accept) {
    DestroyOwnedCommand(*owned);
    return false;
  }
  manager.pending.push_back(*owned);
  *owned = nullptr;
  ++manager.submitted;
  return true;
}
FixtureTable MakeTable(std::size_t size) {
  FixtureTable result{};
  result.entries[0] = reinterpret_cast<std::uintptr_t>(&DeleteFixtureCommand);
  result.entries[8] = reinterpret_cast<std::uintptr_t>(&CloneFixtureCommand);
  result.object_size = size;
  return result;
}
void *GetFixturePlayer(void *) { return fixture_player; }

template <typename T>
void Put(std::span<std::byte> bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}
template <typename T> T Last(const FixtureManager &manager) {
  T result{};
  if (manager.last_copy.size() == sizeof(T)) {
    std::memcpy(&result, manager.last_copy.data(), sizeof(T));
  }
  return result;
}
void Drain(FixtureManager &manager) {
  for (void *&command : manager.pending) {
    DestroyOwnedCommand(command);
  }
  manager.pending.clear();
}

bool CheckQueueLifecycle() {
  FixtureTable table = MakeTable(sizeof(TimeCommand));
  FixtureManager manager{};
  CommandBindings bindings{};
  bindings.enabled = true;
  bindings.command_manager = &manager;
  bindings.queue_owned_command = &QueueFixtureCommand;
  TimeCommand source{};
  source.primary_vtable = reinterpret_cast<std::uintptr_t>(&table);
  source.value = 4;
  const auto initial_clones = clones;
  const auto initial_deletes = deletes;
  if (SubmitCommandCopy(bindings, &source) != CommandSubmitResult::submitted ||
      manager.pending.size() != 1 || clones != initial_clones + 1 ||
      deletes != initial_deletes || manager.last_channel_flags != 7 ||
      manager.pending[0] == &source || Last<TimeCommand>(manager).value != 4) {
    return false;
  }
  std::uint32_t source_metadata = 1;
  std::memcpy(&source_metadata, reinterpret_cast<const std::byte *>(&source) +
                                   0x0C,
              sizeof(source_metadata));
  if (source_metadata != 0) {
    return false;
  }
  Drain(manager);
  if (deletes != initial_deletes + 1) {
    return false;
  }
  manager.accept = false;
  if (SubmitCommandCopy(bindings, &source, 15) != CommandSubmitResult::rejected ||
      manager.last_channel_flags != 15 || !manager.pending.empty() ||
      clones != initial_clones + 2 || deletes != initial_deletes + 2 ||
      SubmitCommandCopyCompat(&bindings, &source, 7)) {
    return false;
  }
  manager.accept = true;
  if (!SubmitCommandCopyCompat(&bindings, &source, 7)) {
    return false;
  }
  Drain(manager);
  bindings.enabled = false;
  const auto before_unavailable = clones;
  if (SubmitCommandCopy(bindings, &source) != CommandSubmitResult::unavailable ||
      SubmitCommandCopyCompat(nullptr, &source, 7) ||
      clones != before_unavailable) {
    return false;
  }
  return true;
}

bool CheckTimeAndCheckpoint() {
  FixtureTable time_table = MakeTable(sizeof(TimeCommand));
  FixtureTable save_table = MakeTable(sizeof(AutoSaveCommand));
  FixtureManager manager{};
  CommandBindings commands{};
  commands.enabled = true;
  commands.command_manager = &manager;
  commands.queue_owned_command = &QueueFixtureCommand;
  commands.pause_primary_vtable = reinterpret_cast<std::uintptr_t>(&time_table);
  commands.pause_secondary_vtable = 0x11223344;
  commands.set_speed_primary_vtable = commands.pause_primary_vtable;
  commands.set_speed_secondary_vtable = 0x22334455;
  commands.auto_save_primary_vtable =
      reinterpret_cast<std::uintptr_t>(&save_table);
  commands.auto_save_secondary_vtable = 0x33445566;
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> player{};
  Put(game_state, 8, std::int32_t{53175816});
  Put(game_state, 0x70, std::int32_t{2});
  Put(jomini, 0x18, players.data());
  Put(players, 0x1F0, std::int32_t{9});
  Put(player, 0x70, std::int32_t{9});
  void *state_pointer = game_state.data();
  void *jomini_pointer = jomini.data();
  CoreBindings core{true, &state_pointer, &jomini_pointer, nullptr,
                     &GetFixturePlayer};
  fixture_player = player.data();
  if (SubmitPauseMap(commands, core) != xar::game::PauseSubmitResult::submitted) {
    return false;
  }
  auto pause = Last<TimeCommand>(manager);
  if (pause.flags != 8 || pause.value != 9 || pause.paused != 1 ||
      pause.secondary_vtable != commands.pause_secondary_vtable) {
    return false;
  }
  const auto after_pause = manager.submitted;
  jomini[0x20] = std::byte{1};
  if (SubmitPauseMap(commands, core) !=
          xar::game::PauseSubmitResult::already_paused ||
      manager.submitted != after_pause ||
      SubmitResumeMap(commands, core) != xar::game::ResumeSubmitResult::submitted ||
      Last<TimeCommand>(manager).paused != 0) {
    return false;
  }
  jomini[0x20] = std::byte{};
  if (SubmitResumeMap(commands, core) !=
      xar::game::ResumeSubmitResult::already_running) {
    return false;
  }
  for (int speed = 1; speed <= 5; ++speed) {
    if (!SubmitSetSpeed(commands, core, speed)) {
      return false;
    }
    const auto command = Last<TimeCommand>(manager);
    if (command.flags != 0 || command.value != speed - 1 ||
        command.secondary_vtable != commands.set_speed_secondary_vtable) {
      return false;
    }
  }
  if (SubmitSetSpeed(commands, core, 0) || SubmitSetSpeed(commands, core, 6)) {
    return false;
  }
  const auto save_result = SubmitSaveCheckpoint(commands, core);
  const auto save = Last<AutoSaveCommand>(manager);
  if (save_result.status != xar::game::SaveCheckpointStatus::submitted ||
      save_result.date_raw != 53175816 || save.flags != 0x20 ||
      save.secondary_vtable != commands.auto_save_secondary_vtable ||
      save.save_name.size != 14 || save.save_name.capacity != 15 ||
      std::string_view(save.save_name.buffer.data()) != kCheckpointSaveName) {
    return false;
  }
  const auto before_missing_map = manager.submitted;
  fixture_player = nullptr;
  const auto missing_map = SubmitSaveCheckpoint(commands, core);
  if (missing_map.status != xar::game::SaveCheckpointStatus::map_not_ready ||
      missing_map.date_raw != 53175816 ||
      SubmitPauseMap(commands, core) != xar::game::PauseSubmitResult::unavailable ||
      SubmitResumeMap(commands, core) !=
          xar::game::ResumeSubmitResult::unavailable ||
      SubmitSetSpeed(commands, core, 3) ||
      manager.submitted != before_missing_map) {
    return false;
  }
  fixture_player = player.data();
  manager.accept = false;
  if (SubmitSaveCheckpoint(commands, core).status !=
          xar::game::SaveCheckpointStatus::unavailable ||
      SubmitSetSpeed(commands, core, 3)) {
    return false;
  }
  Drain(manager);
  return clones == deletes;
}

bool CheckExactBindings() {
  constexpr std::uintptr_t image_base = 0x140000000;
  const auto bindings = BindCommandImage(image_base, kExecutableSha256);
  return bindings.enabled &&
         bindings.command_manager ==
             reinterpret_cast<void *>(image_base + kCommandManagerRva) &&
         reinterpret_cast<std::uintptr_t>(bindings.queue_owned_command) ==
             image_base + kQueueOwnedCommandRva &&
         bindings.auto_save_primary_vtable ==
             image_base + kAutoSavePrimaryVtableRva &&
         !BindCommandImage(0, kExecutableSha256).enabled &&
         !BindCommandImage(image_base, "1.19.0.6").enabled;
}
} // namespace

int main() {
  if (!CheckExactBindings() || !CheckQueueLifecycle() ||
      !CheckTimeAndCheckpoint()) {
    std::cerr << "CK3 1.20.0.2 command lifecycle fixture failed\n";
    return 1;
  }
  std::cout << "CK3 1.20.0.2 command lifecycle fixture passed; "
            << clones << " native-layout clones and " << deletes
            << " matching native-layout deletes; no game access\n";
  return 0;
}
