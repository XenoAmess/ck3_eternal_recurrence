#pragma once

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kActivityHostedIdentity12002ExeSha256V1 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::uintptr_t kActivityHosted12002GameStateRva = 0x5C68C50;
inline constexpr std::uintptr_t kActivityHosted12002CharacterStorageRva = 0x5C67568;
inline constexpr std::uintptr_t kActivityHosted12002CharacterFallbackRva = 0x5C67570;
inline constexpr std::uintptr_t kActivityHosted12002ActivityVtableRva = 0x472E130;
inline constexpr std::uintptr_t kActivityHosted12002ActivityTypeVtableRva = 0x48BFE50;
inline constexpr std::size_t kActivityHosted12002ManagerOffset = 0x22CB8;
inline constexpr std::size_t kActivityHosted12002ObjectStride = 0x628;
inline constexpr std::size_t kActivityFeast12002ResourceExtensionOffset = 0x1B0;

} // namespace xar::bridge
