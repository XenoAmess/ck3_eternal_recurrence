#include "xar_bridge/ck3_121003_commands26785313_v1.hpp"
#include "xar_bridge/ck3_121003_command_pins26785313_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
#if defined(_WIN32)
#include <windows.h>
#endif

namespace xar::ck3_121003::build26785313 {
namespace {
bool Copy(CommandImageReadV1 access, std::uintptr_t from, void *to,
          std::size_t size) noexcept {
  if (!from || !to || !size) return false;
  if (access.copy) return access.copy(access.context, from, to, size);
  if (access.context) return false;
#if defined(_MSC_VER)
  __try {
    std::memcpy(to, reinterpret_cast<const void *>(from), size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return false;
#endif
}
bool Range(std::uintptr_t base, std::uintptr_t rva, std::size_t size) noexcept {
  constexpr auto max = (std::numeric_limits<std::uintptr_t>::max)();
  return base && base <= max - kImageSize && size && size <= kImageSize &&
         rva <= kImageSize - size;
}
template <class T>
bool At(std::uintptr_t base, std::uintptr_t rva, T &value,
        CommandImageReadV1 access) noexcept {
  return Range(base, rva, sizeof(T)) && Copy(access, base + rva, &value, sizeof(T));
}
bool BytePins(std::uintptr_t base, std::span<const ImagePin> pins,
              CommandImageReadV1 access) noexcept {
  std::array<unsigned char, 2048> observed{};
  for (const auto &pin : pins) {
    if (pin.bytes.empty() || pin.bytes.size() > observed.size() ||
        !Range(base, pin.rva, pin.bytes.size()) ||
        !Copy(access, base + pin.rva, observed.data(), pin.bytes.size()) ||
        std::memcmp(observed.data(), pin.bytes.data(), pin.bytes.size()) != 0)
      return false;
  }
  return true;
}
CommandImageBindingsV1 Targets(std::uintptr_t base) noexcept {
  CommandImageBindingsV1 out{};
  out.current_image_verified = true;
  out.module_base = base;
  auto &b = out.commands;
  b.enabled = true;
  b.command_manager = reinterpret_cast<void *>(base + kCommandManagerRvaV1);
  b.queue_owned_command = reinterpret_cast<ck3_1210::QueueOwnedCommand>(
      base + kQueueOwnedCommandRvaV1);
  b.pause_primary_vtable = base + kPausePrimaryVtableRvaV1;
  b.pause_secondary_vtable = base + kPauseSecondaryVtableRvaV1;
  b.set_speed_primary_vtable = base + kSpeedPrimaryVtableRvaV1;
  b.set_speed_secondary_vtable = base + kSpeedSecondaryVtableRvaV1;
  b.auto_save_primary_vtable = base + kAutoSavePrimaryVtableRvaV1;
  b.auto_save_secondary_vtable = base + kAutoSaveSecondaryVtableRvaV1;
  b.game_speed_count = reinterpret_cast<const std::int32_t *>(base + kGameSpeedCountRvaV1);
  return out;
}
} // namespace

std::span<const ImagePin> CommandCodePinsV1() noexcept { return command_pins_v1::kCode; }
std::span<const ImagePin> CommandMetadataPinsV1() noexcept { return command_pins_v1::kMetadata; }
std::span<const CommandPointerPinV1> CommandPointerPinsV1() noexcept { return command_pins_v1::kPointers; }
bool ExactCommandIdentityV1(const CommandIdentityV1 &id) noexcept {
  if (id.game_version != kGameVersion || id.steam_build_id != kSteamBuildId ||
      id.executable_sha256.size() != 64) return false;
  for (std::size_t i = 0; i < 64; ++i) {
    char value = id.executable_sha256[i];
    if (value >= 'a' && value <= 'f') value = static_cast<char>(value - 'a' + 'A');
    if (value != kExecutableSha256[i]) return false;
  }
  return true;
}
bool VerifyCurrentCommandImageV1(std::uintptr_t base, const CommandIdentityV1 &id,
                                CommandImageReadV1 access) noexcept {
  if (!ExactCommandIdentityV1(id) || !Range(base, 0, 1) ||
      (access.context && !access.copy)) return false;
  std::uint16_t mz = 0, machine = 0, magic = 0;
  std::uint32_t pe = 0, signature = 0, timestamp = 0, size = 0;
  std::uint64_t preferred = 0;
  if (!At(base, 0, mz, access) || mz != 0x5A4D ||
      !At(base, 0x3C, pe, access) || pe < 0x40 || pe > 0x800 ||
      !At(base, pe, signature, access) || signature != 0x4550 ||
      !At(base, pe + 4, machine, access) || machine != 0x8664 ||
      !At(base, pe + 8, timestamp, access) || timestamp != kPeTimestamp ||
      !At(base, pe + 24, magic, access) || magic != 0x20B ||
      !At(base, pe + 48, preferred, access) || preferred != base ||
      !At(base, pe + 80, size, access) || size != kImageSize ||
      !BytePins(base, CommandCodePinsV1(), access) ||
      !BytePins(base, CommandMetadataPinsV1(), access)) return false;
  for (const auto &pin : CommandPointerPinsV1()) {
    std::uintptr_t value = 0;
    if (pin.target_rva >= kImageSize || !At(base, pin.rva, value, access) ||
        value != base + pin.target_rva) return false;
  }
  return true;
}
bool CurrentCommandTargetsMatchV1(const CommandImageBindingsV1 &image) noexcept {
  if (!image.current_image_verified || !Range(image.module_base, 0, 1) ||
      !image.commands.enabled) return false;
#if !defined(XAR_CK3_26785313_COMMANDS_OFFLINE_FIXTURE)
  if (image.offline_fixture) return false;
#endif
  const auto expected = Targets(image.module_base);
  const auto &a = image.commands;
  const auto &b = expected.commands;
  return a.command_manager == b.command_manager && a.queue_owned_command == b.queue_owned_command &&
      a.pause_primary_vtable == b.pause_primary_vtable && a.pause_secondary_vtable == b.pause_secondary_vtable &&
      a.set_speed_primary_vtable == b.set_speed_primary_vtable && a.set_speed_secondary_vtable == b.set_speed_secondary_vtable &&
      a.auto_save_primary_vtable == b.auto_save_primary_vtable && a.auto_save_secondary_vtable == b.auto_save_secondary_vtable &&
      a.game_speed_count == b.game_speed_count;
}
CommandImageBindingsV1 BindCurrentCommandImageV1(
    std::uintptr_t base, const CommandIdentityV1 &id) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1 == 1
#if defined(_WIN32)
  if (base == reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)) &&
      VerifyCurrentCommandImageV1(base, id)) return Targets(base);
#endif
#else
  static_cast<void>(base); static_cast<void>(id);
#endif
  return {};
}
#if defined(XAR_CK3_26785313_COMMANDS_OFFLINE_FIXTURE)
CommandImageBindingsV1 BindCurrentCommandFixtureV1(
    std::uintptr_t base, const CommandIdentityV1 &id, CommandImageReadV1 access) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1) && XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1 == 1
  if (!access.copy || !VerifyCurrentCommandImageV1(base, id, access)) return {};
  auto out = Targets(base); out.offline_fixture = true; return out;
#else
  static_cast<void>(base); static_cast<void>(id); static_cast<void>(access);
  return {};
#endif
}
#endif
} // namespace xar::ck3_121003::build26785313
