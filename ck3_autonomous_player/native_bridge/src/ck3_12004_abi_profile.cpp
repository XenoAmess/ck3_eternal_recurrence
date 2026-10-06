#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"

#include <windows.h>
#include <cstring>

namespace xar::ck3_12004 {
namespace {
template <typename T>
T LoadAt(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

void *ResolveCharacter(void *storage, std::int32_t id) noexcept {
  if (storage == nullptr || id == -1) return nullptr;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  const auto capacity = LoadAt<std::int32_t>(storage, kCharacterStorageCapacityOffset);
  const auto slots = LoadAt<void *>(storage, kCharacterStorageSlotsOffset);
  if (slots == nullptr || capacity <= 0 ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  const auto character = LoadAt<void *>(slots,
      index * kCharacterStorageSlotStride + kCharacterStorageObjectOffset);
  return character != nullptr &&
                 LoadAt<std::int32_t>(character, kCharacterFullIdOffset) == id
             ? character : nullptr;
}
} // namespace

CoreBindings BindCoreImage(std::uintptr_t image_base,
                           std::string_view executable_sha256) noexcept {
  CoreBindings result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.game_state_slot = reinterpret_cast<void **>(image_base + kGameStateSlotRva);
  result.jomini_state_slot = reinterpret_cast<void **>(image_base + kJominiStateSlotRva);
  result.character_storage_slot = reinterpret_cast<void **>(image_base + kCharacterStorageSlotRva);
  result.get_local_player = reinterpret_cast<ck3_12002::GetLocalPlayer>(
      image_base + kGetLocalPlayerRva);
  return result;
}

void *ResolveCoreCharacter(const CoreBindings &bindings,
                           std::int32_t character_id) noexcept {
  if (!bindings.enabled || bindings.character_storage_slot == nullptr) return nullptr;
  return ResolveCharacter(*bindings.character_storage_slot, character_id);
}

bool ReadCoreSnapshot(const CoreBindings &bindings,
                      CoreSnapshotPrefix &output) noexcept {
  output = {};
  if (!bindings.enabled || bindings.game_state_slot == nullptr ||
      bindings.jomini_state_slot == nullptr) return false;
  const auto game_state = *bindings.game_state_slot;
  const auto jomini_state = *bindings.jomini_state_slot;
  if (game_state == nullptr || jomini_state == nullptr) return false;
  const auto players = LoadAt<void *>(jomini_state, kJominiPlayersOffset);
  if (players == nullptr ||
      !DecodeClockPrefix({static_cast<const std::byte *>(game_state), 0x74},
                         {static_cast<const std::byte *>(jomini_state), 0x21},
                         output.clock)) return false;
  output.local_player_id = LoadAt<std::int32_t>(players, kPlayersLocalPlayerIdOffset);
  const auto player = bindings.get_local_player != nullptr
                          ? bindings.get_local_player(jomini_state) : nullptr;
  // Preserve the native readiness operand; Python's exact-source clock route
  // reads this expression independently of a complete gameplay snapshot.
  output.map_ready = player != nullptr && LoadAt<std::int32_t>(player, 0x70) >= 0;
  if (!output.map_ready || output.local_player_id < 0 ||
      bindings.character_storage_slot == nullptr) return true;
  const auto data = LoadAt<void *>(game_state, kGameStateDataOffset);
  if (data == nullptr) return true;
  const auto manager = static_cast<const std::byte *>(data) + kPlayerCharacterManagerOffset;
  const auto entries = LoadAt<void *>(manager, kPlayerManagerEntriesOffset);
  const auto count = LoadAt<std::int32_t>(manager, kPlayerManagerCountOffset);
  if (entries == nullptr || count <= 0 || count > 1024) return true;
  for (std::int32_t index = 0; index < count; ++index) {
    const auto entry = LoadAt<void *>(entries,
        static_cast<std::size_t>(index) * sizeof(void *));
    if (entry == nullptr ||
        LoadAt<std::int32_t>(entry, kPlayerEntryLocalPlayerIdOffset) !=
            output.local_player_id) continue;
    const auto id = LoadAt<std::int32_t>(entry, kPlayerEntryCharacterIdOffset);
    const auto character = ResolveCharacter(*bindings.character_storage_slot, id);
    if (character == nullptr) continue;
    output.has_played_character = true;
    output.played_character_id = id;
    output.played_character_alive =
        LoadAt<void *>(character, kCharacterDeathDataOffset) == nullptr;
    break;
  }
  return true;
}

bool DecodeClockPrefix(std::span<const std::byte> game_state,
                       std::span<const std::byte> jomini_state,
                       ClockPrefix &output) noexcept {
  output = {};
  if (game_state.size() < 0x74 || jomini_state.size() < 0x21) return false;
  std::int32_t native_speed = 0;
  std::memcpy(&native_speed, game_state.data() + 0x70, sizeof(native_speed));
  if (native_speed < 0 || native_speed > 4) return false;
  std::memcpy(&output.date_raw, game_state.data() + 0x08,
              sizeof(output.date_raw));
  output.speed = native_speed + 1;
  output.paused = jomini_state[0x20] != std::byte{};
  return true;
}
} // namespace xar::ck3_12004

namespace xar::game {
bool IsCk3_12004Descriptor(const AdapterDescriptor &descriptor) noexcept {
  return descriptor.adapter_id == ck3_12004::kAdapterId &&
         descriptor.game_version == ck3_12004::kGameVersion &&
         descriptor.executable_sha256 == ck3_12004::kExecutableSha256;
}
} // namespace xar::game

namespace xar::ck3_12004 {
namespace {
// Actual new verifier bytes from CORE-FUNCTION-MAP.json.
constexpr std::array<std::uint8_t, 32> kThreadGuardWindowsPump{0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x18, 0x57, 0x48, 0x83, 0xEC, 0x60, 0xFF, 0x15, 0x4B, 0x11, 0x30, 0x00, 0x33, 0xF6, 0x8B, 0xF8, 0x8B, 0xDE, 0x39, 0x1D, 0x6F, 0x72, 0x35};
constexpr std::array<std::uint8_t, 16> kThreadGuardFirstPeekCall{0x45, 0x33, 0xC0, 0x48, 0x8D, 0x4C, 0x24, 0x30, 0x33, 0xD2, 0xFF, 0x15, 0x26, 0x1A, 0x30, 0x00};
constexpr std::array<std::uint8_t, 14> kThreadGuardDevicePumpInstall{0x48, 0x8D, 0x05, 0x2E, 0x5A, 0xFE, 0xFF, 0x48, 0x89, 0x85, 0x38, 0x02, 0x00, 0x00};
constexpr std::array<std::uint8_t, 15> kThreadGuardSdlPumpDispatch{0x48, 0x85, 0xF6, 0x74, 0x09, 0x48, 0x8B, 0xCE, 0xFF, 0x96, 0x38, 0x02, 0x00, 0x00, 0x83};
constexpr std::array<std::uint8_t, 18> kThreadGuardRngOwnerDiagnostic{0xE8, 0xB1, 0x63, 0x7B, 0x00, 0x48, 0x8B, 0x0B, 0x44, 0x8B, 0x41, 0x10, 0x44, 0x3B, 0xC0, 0x74, 0x20, 0x33};
constexpr std::array<std::uint8_t, 7> kThreadGuardCurrentThreadThunk{0x48, 0xFF, 0x25, 0xA1, 0x53, 0x2E, 0x00};
constexpr std::array<std::uint8_t, 32> kThreadGuardTlsGetter{0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x65, 0x48, 0x8B, 0x04, 0x25, 0x58, 0x00, 0x00, 0x00, 0x48, 0x8B, 0x08, 0xBA, 0x28, 0x32, 0x00, 0x00, 0x8B, 0x04, 0x0A, 0x41, 0xB8, 0x30, 0x32, 0x00, 0x00};
constexpr std::array<std::uint8_t, 16> kThreadGuardTlsGetterMarkerInit{0xC6, 0x43, 0x20, 0x00, 0xB8, 0x10, 0x00, 0x00, 0x00, 0x8B, 0x04, 0x08, 0x39, 0x05, 0x1D, 0x8D};
constexpr std::array<std::uint8_t, 16> kThreadGuardTlsStartup{0xC6, 0x05, 0xC0, 0xA0, 0x46, 0x05, 0x01, 0xE8, 0x9C, 0x3E, 0x72, 0x03, 0xC6, 0x40, 0x20, 0x01};
constexpr std::array<std::uint8_t, 22> kThreadGuardHandleTlsGate{0x0F, 0xB6, 0x05, 0x2B, 0xA0, 0xEA, 0x01, 0x84, 0xC0, 0x74, 0x28, 0xE8, 0x03, 0x3E, 0x16, 0x00, 0x80, 0x78, 0x20, 0x00, 0x74, 0x1D};
constexpr std::array<std::uint8_t, 19> kThreadGuardApplicationPumpGate{0x80, 0xB9, 0x60, 0x01, 0x00, 0x00, 0x00, 0x48, 0x8B, 0xD9, 0x75, 0x5B, 0x80, 0xB9, 0x89, 0x00, 0x00, 0x00, 0x00};
constexpr std::array<std::uint8_t, 8> kThreadGuardApplicationEventCall{0x48, 0x8B, 0xCB, 0xE8, 0xFD, 0xF8, 0xFF, 0xFF};
constexpr std::array<std::uint8_t, 35> kThreadGuardEventSingletonConstruct{0x48, 0x8D, 0x05, 0xE6, 0xB4, 0x14, 0x04, 0x48, 0x89, 0x03, 0x4C, 0x89, 0x63, 0x38, 0x4C, 0x89, 0x63, 0x40, 0x4C, 0x89, 0x63, 0x48, 0xFF, 0x15, 0x81, 0xF7, 0xC7, 0x04, 0x48, 0x89, 0x1D, 0xB2, 0x56, 0x41, 0x05};
constexpr std::array<std::uint8_t, 7> kThreadGuardEventSingletonLoad{0x48, 0x8B, 0x35, 0x50, 0x18, 0x34, 0x02};
constexpr std::array<std::uint8_t, 35> kThreadGuardEventSingletonVslot{0x48, 0x8B, 0x06, 0x4C, 0x8B, 0x50, 0x08, 0x48, 0x8B, 0x47, 0x28, 0x48, 0x89, 0x54, 0x24, 0x28, 0x48, 0x89, 0x44, 0x24, 0x20, 0x4C, 0x8B, 0x4F, 0x20, 0x4C, 0x8B, 0x47, 0x18, 0x48, 0x8B, 0xCE, 0x41, 0xFF, 0xD2};
constexpr std::array<std::uint8_t, 11> kThreadGuardPdxSdlPollSlot{0x48, 0x8D, 0x4C, 0x24, 0x48, 0xFF, 0x15, 0x0F, 0xFB, 0x6B, 0x01};
constexpr std::array<std::uint8_t, 14> kThreadGuardSdlPollSlotBind{0x48, 0x8D, 0x05, 0xA3, 0xEB, 0x02, 0x00, 0x48, 0x89, 0x05, 0x74, 0xA6, 0x43, 0x01};
constexpr std::array<std::uint8_t, 8> kThreadGuardSdlUpperPumpCall{0x8D, 0x48, 0x01, 0xE8, 0x98, 0xFE, 0xFF, 0xFF};

template <std::size_t Size>
bool ThreadBytesMatch(std::uintptr_t address,
                      const std::array<std::uint8_t, Size> &expected) noexcept {
  return std::memcmp(reinterpret_cast<const void *>(address), expected.data(),
                     expected.size()) == 0;
}
} // namespace

bool VerifyThreadRuntimeImage(std::uintptr_t image_base) noexcept {
  if (image_base == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return
        ThreadBytesMatch(image_base + 0x040D93D0, kThreadGuardWindowsPump) &&
        ThreadBytesMatch(image_base + 0x040D9402, kThreadGuardFirstPeekCall) &&
        ThreadBytesMatch(image_base + 0x040F399B, kThreadGuardDevicePumpInstall) &&
        ThreadBytesMatch(image_base + 0x040C8854, kThreadGuardSdlPumpDispatch) &&
        ThreadBytesMatch(image_base + 0x0393EE3A, kThreadGuardRngOwnerDiagnostic) &&
        ThreadBytesMatch(image_base + 0x040F51F0, kThreadGuardCurrentThreadThunk) &&
        ThreadBytesMatch(image_base + 0x03F784A0, kThreadGuardTlsGetter) &&
        ThreadBytesMatch(image_base + 0x03F784E5, kThreadGuardTlsGetterMarkerInit) &&
        ThreadBytesMatch(image_base + 0x008545F8, kThreadGuardTlsStartup) &&
        ThreadBytesMatch(image_base + 0x03E1468D, kThreadGuardHandleTlsGate) &&
        ThreadBytesMatch(image_base + 0x03929466, kThreadGuardApplicationPumpGate) &&
        ThreadBytesMatch(image_base + 0x039294BB, kThreadGuardApplicationEventCall) &&
        ThreadBytesMatch(image_base + 0x00854FAB, kThreadGuardEventSingletonConstruct) &&
        ThreadBytesMatch(image_base + 0x03928E29, kThreadGuardEventSingletonLoad) &&
        ThreadBytesMatch(image_base + 0x03928E6B, kThreadGuardEventSingletonVslot) &&
        ThreadBytesMatch(image_base + 0x03E148DE, kThreadGuardPdxSdlPollSlot) &&
        ThreadBytesMatch(image_base + 0x04099D76, kThreadGuardSdlPollSlotBind) &&
        ThreadBytesMatch(image_base + 0x040C8950, kThreadGuardSdlUpperPumpCall);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

const ck3_11906::MainThreadQueryBuildProfileV1 &ThreadRuntimeBuildProfile()
    noexcept {
  static const ck3_11906::MainThreadQueryBuildProfileV1 profile{
      kSdlWindowsPumpFirstPeekReturnRva, kPeekMessageWIatSlotRva,
      kGlobalRngWrapperSlotRva, kJominiStateSlotRva, kGameStateSlotRva,
      kMainThreadTlsInitializedFlagRva, kMainThreadTlsContextGetterRva,
      &VerifyThreadRuntimeImage};
  return profile;
}

ck3_11906::MainThreadQueryInstallEnvironmentV1 BindThreadRuntimeImage(
    std::uintptr_t image_base, std::string_view executable_sha256,
    std::span<const ck3_11906::MainThreadQueryExecutorV1> executors) noexcept {
  ck3_11906::MainThreadQueryInstallEnvironmentV1 output{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      executors.size() > 14) return output;
  output.module_base = image_base;
  output.exact_build_admitted = true;
  output.build_profile = &ThreadRuntimeBuildProfile();
  output.executor_submission_enabled = !executors.empty();
  // Software executor slots preserve the existing mailbox's aggregate layout.
  const std::array slots{
      &output.permitted_executor, &output.permitted_executor_secondary,
      &output.permitted_executor_tertiary, &output.permitted_executor_quaternary,
      &output.permitted_executor_quinary, &output.permitted_executor_senary,
      &output.permitted_executor_septenary, &output.permitted_executor_octonary,
      &output.permitted_executor_nonary, &output.permitted_executor_denary,
      &output.permitted_executor_undenary, &output.permitted_executor_duodenary,
      &output.permitted_executor_thirdenary,
      &output.permitted_executor_semantic12002};
  for (std::size_t i = 0; i < executors.size(); ++i) *slots[i] = executors[i];
  return output;
}
} // namespace xar::ck3_12004
