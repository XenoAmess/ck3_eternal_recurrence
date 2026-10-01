#pragma once

#include <array>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {
inline constexpr std::string_view kFeastExecutableSha256 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::uintptr_t kFeastFinalCanStartRva = 0x11B8670;
inline constexpr std::uintptr_t kFeastFinalStage5BranchRva = 0x11B88E8;
inline constexpr std::uintptr_t kFeastCommitRva = 0x11B8D90;
inline constexpr std::uintptr_t kFeastNativeStringDestroyRva = 0x856050;
inline constexpr std::array<std::uint8_t, 13> kFeastCommitPrefix{
    0x40, 0x55, 0x53, 0x56, 0x57, 0x48, 0x8D, 0xAC, 0x24, 0x18, 0xF6,
    0xFF, 0xFF};
inline constexpr std::array<std::uint8_t, 7> kFeastFinalCanStartPrefix{
    0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89};
inline constexpr std::array<std::uint8_t, 7> kFeastFinalStage5Prefix{
    0x48, 0x8D, 0x91, 0x00, 0x15, 0x00, 0x00};
} // namespace xar::ck3_12002
