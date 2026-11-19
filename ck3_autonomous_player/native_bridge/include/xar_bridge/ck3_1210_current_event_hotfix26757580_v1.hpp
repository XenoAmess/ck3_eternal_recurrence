#pragma once
#include <array>
#include <cstddef>
#include <cstdint>

// Static integration input only. No binder, enabled flag or game call here.
// Native owner must admit exact bb3 mapped-image pins AND its independently
// qualified bb3 Core profile/custody. Keep the existing 2F2B profile unchanged.
// Evidence: BB3-CURRENT-EVENT-EVIDENCE36.json, static source only.
namespace xar::ck3_1210::bb3_current_event_profile36 {
inline constexpr char kExecutableSha256[] =
    "bb3fef106240e95ecdb6f1532982e89e9432c92a99d33db623521572f06e6f79";
inline constexpr std::uintptr_t kCurrentEventSelectorRvaV1 = 0x2EBF910;
inline constexpr std::uintptr_t kCurrentEventCharacterSlotRvaV1 = 0x5D51448;
inline constexpr std::uintptr_t kCurrentEventDefinitionVtableRvaV1 = 0x4E54028;
// Actual caller/selector/cache refs, not a replacement Core profile.
inline constexpr std::uintptr_t kReferencedGameStateSlotRva = 0x68B2FD0;
inline constexpr std::uintptr_t kReferencedJominiStateSlotRva = 0x68B4A40;
inline constexpr std::size_t kGameStateDataOffset = 0xA0;
inline constexpr std::size_t kCurrentEventManagerOffsetV1 = 0x44BC0;
inline constexpr std::size_t kCurrentEventQueuePointerOffsetV1 = 0x1F18;
inline constexpr std::size_t kCurrentEventQueueCountOffsetV1 = 0x1F24;
inline constexpr std::size_t kCurrentEventDefinitionOffsetV1 = 0x1B8;
inline constexpr std::size_t kCurrentEventCharacterOffsetV1 = 0x1C0;
inline constexpr std::size_t kCurrentEventInstanceOffsetV1 = 0x1C4;
inline constexpr std::size_t kCurrentEventAuthoredPointerOffsetV1 = 0x138;
inline constexpr std::size_t kCurrentEventAuthoredCapacityOffsetV1 = 0x140;
inline constexpr std::size_t kCurrentEventAuthoredCountOffsetV1 = 0x144;
// Preserve existing adapter work bounds, not engine maxima or eligibility.
inline constexpr std::size_t kCurrentEventMaxQueuedV1 = 512;
inline constexpr std::size_t kCurrentEventMaxAuthoredV1 = 512;
inline constexpr std::array<std::uint8_t, 32> kCurrentEventSelectorEntry32V1 = {
  0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xEC,0x30,0x48,
  0x8D,0x05,0x3E,0x4F,0x9F,0x03,0x48,0x89,0x44,0x24,0x20,0xB8,0x02,0x00,0x00,0x00};
} // namespace xar::ck3_1210::bb3_current_event_profile36
