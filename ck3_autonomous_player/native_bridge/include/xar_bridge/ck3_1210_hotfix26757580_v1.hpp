#pragma once
#include "xar_bridge/ck3_1210.hpp"
// Independent exact image. These operands are backed by hotfix36 bounded
// source-use/RTTI records; old profile and unrelated domain gates stay intact.
namespace xar::ck3_1210 {
namespace hotfix26757580 {
inline constexpr char kAdapterId[]="ck3-1.21.0-26757580-msvc-x64";
inline constexpr char kExecutableSha256[]="BB3FEF106240E95ECDB6F1532982E89E9432C92A99D33DB623521572F06E6F79";
inline constexpr char kSteamBuildId[]="26757580";
inline constexpr std::uintptr_t kImageSize=0x6FE6000;
inline constexpr std::uintptr_t kGameStateSlotRva=0x68B2FD0,kJominiStateSlotRva=0x68B4A40;
inline constexpr std::uintptr_t kCharacterStorageSlotRva=0x68A9868,kGetLocalPlayerRva=0x3E66030;
inline constexpr std::uintptr_t kTlsFlag=0x695A34C,kTlsGetter=0x44FF630;
inline constexpr std::uintptr_t kPause=0x3E66180,kManager=0x69DBAE0,kWorker=0x3E1DA10;
inline constexpr std::uintptr_t kRunner=0x3E1DE00,kScopeBegin=0x3E1DE14,kScopeEnd=0x3E1DF06;
inline constexpr std::uintptr_t kAcquire=0x3E65510,kDestroy=0x3E65820,kApplication=0x6A652F8;
inline constexpr std::uintptr_t kDailyFinal=0x2E77B60,kDailySlot=0x4B3E9B8;
inline constexpr std::uintptr_t kQuit=0x3F5BA40,kQuitTail=0x3F5BB05;
} // namespace hotfix26757580
inline constexpr bool IsHotfix(ImageBuildV1 b) noexcept {return b==ImageBuildV1::hotfix26757580;}
inline constexpr ImageBuildV1 ImageBuildForSha(std::string_view sha) noexcept {
  if(sha==kExecutableSha256)return ImageBuildV1::original26622941;
  if(sha==hotfix26757580::kExecutableSha256)return ImageBuildV1::hotfix26757580;
  return ImageBuildV1::unknown;
}
inline constexpr std::string_view ExecutableShaForBuild(ImageBuildV1 b) noexcept {
  return IsHotfix(b)?hotfix26757580::kExecutableSha256:
    b==ImageBuildV1::original26622941?std::string_view(kExecutableSha256):std::string_view{};
}
inline constexpr std::string_view AdapterIdForBuild(ImageBuildV1 b) noexcept {
  return IsHotfix(b)?hotfix26757580::kAdapterId:
    b==ImageBuildV1::original26622941?std::string_view(kAdapterId):std::string_view{};
}
inline constexpr std::uintptr_t ImageRva(ImageBuildV1 b,std::uintptr_t original,std::uintptr_t hotfix) noexcept {
  return IsHotfix(b)?hotfix:original;
}
inline constexpr std::uintptr_t ImageSize(ImageBuildV1 b) noexcept {return IsHotfix(b)?hotfix26757580::kImageSize:0x6FE5000;}
} // namespace xar::ck3_1210
