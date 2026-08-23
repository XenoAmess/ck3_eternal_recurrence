#include "xar_bridge/ck3_11906.hpp"

#include <windows.h>
#include <bcrypt.h>

#include <array>
#include <cstddef>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kGameStateSlotRva = 0x570E068;
constexpr std::uintptr_t kJominiStateSlotRva = 0x570F7B8;
constexpr std::uintptr_t kCommandManagerRva = 0x57621F0;
constexpr std::uintptr_t kPausePrimaryVtableRva = 0x432F1C8;
constexpr std::uintptr_t kPauseSecondaryVtableRva = 0x432F198;
constexpr std::uintptr_t kSetSpeedPrimaryVtableRva = 0x432F3F0;
constexpr std::uintptr_t kSetSpeedSecondaryVtableRva = 0x432F260;
constexpr std::uintptr_t kSubmitCommandRva = 0x0973E00;
constexpr std::uintptr_t kGetLocalPlayerRva = 0x346B7C0;

constexpr std::size_t kGameStateDateOffset = 0x08;
constexpr std::size_t kGameStateSpeedOffset = 0x70;
constexpr std::size_t kJominiPlayersOffset = 0x18;
constexpr std::size_t kJominiPausedOffset = 0x20;
constexpr std::size_t kPlayersLocalIdOffset = 0x1F0;
constexpr std::size_t kPlayerIdOffset = 0x70;

struct PauseCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t player_id = -1;
  std::uint8_t paused = 0;
  std::array<std::byte, 3> payload_padding{};
};

struct SetSpeedCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> flags_padding{};
  std::uint32_t metadata_0c = 0;
  std::uint32_t metadata_10 = 0;
  std::uint32_t metadata_14 = 0;
  std::uintptr_t secondary_vtable = 0;
  std::int32_t speed = 0;
  std::array<std::byte, 4> payload_padding{};
};

static_assert(sizeof(PauseCommand) == 0x28);
static_assert(offsetof(PauseCommand, secondary_vtable) == 0x18);
static_assert(offsetof(PauseCommand, player_id) == 0x20);
static_assert(offsetof(PauseCommand, paused) == 0x24);
static_assert(sizeof(SetSpeedCommand) == 0x28);
static_assert(offsetof(SetSpeedCommand, secondary_vtable) == 0x18);
static_assert(offsetof(SetSpeedCommand, speed) == 0x20);

template <typename Value>
Value LoadAt(const void *base, std::size_t offset) noexcept {
  Value result{};
  std::memcpy(&result, static_cast<const std::byte *>(base) + offset,
              sizeof(result));
  return result;
}

bool HashCurrentExecutable(std::array<std::uint8_t, 32> &output) noexcept {
  std::array<wchar_t, 32'768> path{};
  const DWORD path_length =
      GetModuleFileNameW(nullptr, path.data(), static_cast<DWORD>(path.size()));
  if (path_length == 0 || path_length >= path.size()) {
    return false;
  }

  HANDLE file = CreateFileW(path.data(), GENERIC_READ, FILE_SHARE_READ, nullptr,
                            OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
  if (file == INVALID_HANDLE_VALUE) {
    return false;
  }

  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  std::vector<std::uint8_t> object;
  bool ok = false;
  do {
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                    nullptr, 0) < 0) {
      break;
    }
    DWORD object_size = 0;
    DWORD copied = 0;
    if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                          reinterpret_cast<PUCHAR>(&object_size),
                          sizeof(object_size), &copied, 0) < 0 ||
        object_size == 0) {
      break;
    }
    object.resize(object_size);
    if (BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr,
                         0, 0) < 0) {
      break;
    }

    // The bridge worker uses the default Windows thread stack. Keep the file
    // buffer comfortably below that limit; ck3.exe is streamed in chunks.
    std::array<std::uint8_t, 64U * 1024U> buffer{};
    while (true) {
      DWORD read = 0;
      if (!ReadFile(file, buffer.data(), static_cast<DWORD>(buffer.size()),
                    &read, nullptr)) {
        break;
      }
      if (read == 0) {
        ok = BCryptFinishHash(hash, output.data(),
                              static_cast<ULONG>(output.size()), 0) >= 0;
        break;
      }
      if (BCryptHashData(hash, buffer.data(), read, 0) < 0) {
        break;
      }
    }
  } while (false);

  if (hash != nullptr) {
    BCryptDestroyHash(hash);
  }
  if (algorithm != nullptr) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
  }
  CloseHandle(file);
  return ok;
}

bool MatchesExpectedExecutable() noexcept {
  std::array<std::uint8_t, 32> digest{};
  if (!HashCurrentExecutable(digest)) {
    return false;
  }
  constexpr char digits[] = "0123456789ABCDEF";
  std::array<char, 65> encoded{};
  for (std::size_t index = 0; index < digest.size(); ++index) {
    encoded[index * 2] = digits[digest[index] >> 4U];
    encoded[index * 2 + 1] = digits[digest[index] & 0x0fU];
  }
  return std::string(encoded.data()) == kExecutableSha256;
}

} // namespace

Bindings BindCurrentProcess() noexcept {
  Bindings result{};
  if (!MatchesExpectedExecutable()) {
    return result;
  }
  const auto module =
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
  if (module == 0) {
    return result;
  }
  result.enabled = true;
  result.game_state_slot =
      reinterpret_cast<void **>(module + kGameStateSlotRva);
  result.jomini_state_slot =
      reinterpret_cast<void **>(module + kJominiStateSlotRva);
  result.command_manager =
      reinterpret_cast<void *>(module + kCommandManagerRva);
  result.pause_primary_vtable = module + kPausePrimaryVtableRva;
  result.pause_secondary_vtable = module + kPauseSecondaryVtableRva;
  result.set_speed_primary_vtable = module + kSetSpeedPrimaryVtableRva;
  result.set_speed_secondary_vtable = module + kSetSpeedSecondaryVtableRva;
  result.submit_command =
      reinterpret_cast<SubmitCommand>(module + kSubmitCommandRva);
  result.get_local_player =
      reinterpret_cast<GetLocalPlayer>(module + kGetLocalPlayerRva);
  return result;
}

bool ReadSnapshot(const Bindings &bindings, Snapshot &output) noexcept {
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr) {
    return false;
  }
  void *const game_state = *bindings.game_state_slot;
  void *const jomini_state = *bindings.jomini_state_slot;
  if (game_state == nullptr || jomini_state == nullptr) {
    return false;
  }
  void *const players = LoadAt<void *>(jomini_state, kJominiPlayersOffset);
  if (players == nullptr) {
    return false;
  }

  output.date_raw = LoadAt<std::int32_t>(game_state, kGameStateDateOffset);
  const std::int32_t native_speed =
      LoadAt<std::int32_t>(game_state, kGameStateSpeedOffset);
  if (native_speed < 0 || native_speed > 4) {
    return false;
  }
  output.speed = native_speed + 1;
  output.paused = LoadAt<std::uint8_t>(jomini_state, kJominiPausedOffset) != 0;
  output.player_id = LoadAt<std::int32_t>(players, kPlayersLocalIdOffset);
  return true;
}

PauseSubmitResult SubmitPauseMap(const Bindings &bindings) noexcept {
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return PauseSubmitResult::unavailable;
  }
  if (current.paused) {
    return PauseSubmitResult::already_paused;
  }
  if (bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.get_local_player == nullptr ||
      bindings.pause_primary_vtable == 0 ||
      bindings.pause_secondary_vtable == 0) {
    return PauseSubmitResult::unavailable;
  }

  void *const jomini_state = *bindings.jomini_state_slot;
  void *const player = bindings.get_local_player(jomini_state);
  if (player == nullptr) {
    return PauseSubmitResult::unavailable;
  }
  const std::int32_t player_id = LoadAt<std::int32_t>(player, kPlayerIdOffset);
  if (player_id < 0) {
    return PauseSubmitResult::unavailable;
  }

  PauseCommand command{};
  command.primary_vtable = bindings.pause_primary_vtable;
  command.flags = 0x08;
  command.secondary_vtable = bindings.pause_secondary_vtable;
  command.player_id = player_id;
  command.paused = 1;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return PauseSubmitResult::submitted;
}

ResumeSubmitResult SubmitResumeMap(const Bindings &bindings) noexcept {
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return ResumeSubmitResult::unavailable;
  }
  if (!current.paused) {
    return ResumeSubmitResult::already_running;
  }
  if (bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.get_local_player == nullptr ||
      bindings.pause_primary_vtable == 0 ||
      bindings.pause_secondary_vtable == 0) {
    return ResumeSubmitResult::unavailable;
  }

  void *const jomini_state = *bindings.jomini_state_slot;
  void *const player = bindings.get_local_player(jomini_state);
  if (player == nullptr) {
    return ResumeSubmitResult::unavailable;
  }
  const std::int32_t player_id = LoadAt<std::int32_t>(player, kPlayerIdOffset);
  if (player_id < 0) {
    return ResumeSubmitResult::unavailable;
  }

  PauseCommand command{};
  command.primary_vtable = bindings.pause_primary_vtable;
  command.flags = 0x08;
  command.secondary_vtable = bindings.pause_secondary_vtable;
  command.player_id = player_id;
  command.paused = 0;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return ResumeSubmitResult::submitted;
}

bool SubmitSetSpeed(const Bindings &bindings, std::int32_t speed) noexcept {
  if (!bindings.enabled || speed < 1 || speed > 5 ||
      bindings.command_manager == nullptr ||
      bindings.submit_command == nullptr ||
      bindings.set_speed_primary_vtable == 0 ||
      bindings.set_speed_secondary_vtable == 0) {
    return false;
  }
  Snapshot current{};
  if (!ReadSnapshot(bindings, current)) {
    return false;
  }

  SetSpeedCommand command{};
  command.primary_vtable = bindings.set_speed_primary_vtable;
  command.secondary_vtable = bindings.set_speed_secondary_vtable;
  command.speed = speed - 1;
  bindings.submit_command(bindings.command_manager, &command, 7);
  return true;
}

} // namespace xar::ck3_11906
