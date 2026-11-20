#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/ck3_1210_commands.hpp"
#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>

namespace xar::ck3_121003::build26785313 {
// Independent current tuple. This is not an extension of ImageBuildV1 or the
// old ImageBuildForSha/BB3 SaveAdmission61 path.
struct CommandIdentityV1 {
  std::string_view game_version;
  std::string_view steam_build_id;
  std::string_view executable_sha256;
};
struct CommandImageReadV1 {
  void *context = nullptr;
  bool (*copy)(void *, std::uintptr_t, void *, std::size_t) noexcept = nullptr;
};
struct CommandPointerPinV1 {
  std::uintptr_t rva = 0;
  std::uintptr_t target_rva = 0;
};
inline constexpr std::uintptr_t kCommandManagerRvaV1 = 0x69DABA0;
inline constexpr std::uintptr_t kQueueOwnedCommandRvaV1 = 0x3E17C00;
inline constexpr std::uintptr_t kPausePrimaryVtableRvaV1 = 0x4E8BA38;
inline constexpr std::uintptr_t kPauseSecondaryVtableRvaV1 = 0x4E8BA00;
inline constexpr std::uintptr_t kSpeedPrimaryVtableRvaV1 = 0x4E8B898;
inline constexpr std::uintptr_t kSpeedSecondaryVtableRvaV1 = 0x4E8B860;
inline constexpr std::uintptr_t kAutoSavePrimaryVtableRvaV1 = 0x4B3DAA8;
inline constexpr std::uintptr_t kAutoSaveSecondaryVtableRvaV1 = 0x4B3DA70;
inline constexpr std::uintptr_t kGameSpeedCountRvaV1 = 0x5D3E3EC;

struct CommandImageBindingsV1 {
  // Literal code/table/tuple proof only: not owner, map, deadline, capability,
  // once-only dispatch, exact-day stopping, or physical-save authority.
  bool current_image_verified = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  ck3_1210::CommandBindings commands{};
};
std::span<const ImagePin> CommandCodePinsV1() noexcept;
std::span<const ImagePin> CommandMetadataPinsV1() noexcept;
std::span<const CommandPointerPinV1> CommandPointerPinsV1() noexcept;
bool ExactCommandIdentityV1(const CommandIdentityV1 &) noexcept;
bool VerifyCurrentCommandImageV1(std::uintptr_t, const CommandIdentityV1 &,
                                CommandImageReadV1 = {}) noexcept;
bool CurrentCommandTargetsMatchV1(const CommandImageBindingsV1 &) noexcept;
// Default OFF. A production binding can only refer to this process's primary
// module; it never accepts a caller-supplied memory reader.
CommandImageBindingsV1 BindCurrentCommandImageV1(
    std::uintptr_t, const CommandIdentityV1 &) noexcept;
#if defined(XAR_CK3_26785313_COMMANDS_OFFLINE_FIXTURE)
// Separate NoGame TU only. Returned RVA pointers are never invoked by tests.
CommandImageBindingsV1 BindCurrentCommandFixtureV1(
    std::uintptr_t, const CommandIdentityV1 &, CommandImageReadV1) noexcept;
#endif
} // namespace xar::ck3_121003::build26785313
