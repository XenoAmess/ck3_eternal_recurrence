#pragma once

#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {

// Independent actual .4 source profile. The finite receipt identifies each
// function and field operand; no legacy or .3 executable identity is admitted.
inline constexpr std::uintptr_t kGuiGlobalSlotRva12004V1 = 0x5CB87F8;
inline constexpr std::uintptr_t kGuiFindTopLevelWidgetRva12004V1 = 0x3AAB0E0;
inline constexpr std::uintptr_t kGuiShortcutManagerActivateRva12004V1 = 0x3ABC4B0;
inline constexpr std::uintptr_t kGuiStrictDescendantRva12004V1 = 0x3A78210;
inline constexpr std::uintptr_t kGuiButtonBaseSlot13Rva12004V1 = 0x3AA0D20;
inline constexpr std::size_t kGuiImageSize12004V1 = 0x61C5000;

inline constexpr std::size_t kGuiApplicationHostOffset12004V1 = 0x1B8;
inline constexpr std::size_t kGuiHostContextOffset12004V1 = 0x58;
inline constexpr std::size_t kGuiContextOwnerLookupHostOffset12004V1 = 0x3D0;
inline constexpr std::size_t kGuiLookupHostOwnerOffset12004V1 = 0x08;
inline constexpr std::size_t kGuiOwnerRootOffset12004V1 = 0xD0;
inline constexpr std::size_t kGuiWidgetFlagsOffset12004V1 = 0xD0;
inline constexpr std::size_t kGuiWidgetContextOffset12004V1 = 0xD8;
inline constexpr std::size_t kGuiWidgetParentOffset12004V1 = 0xE8;
inline constexpr std::size_t kGuiWidgetChildrenOffset12004V1 = 0xF0;
inline constexpr std::size_t kGuiWidgetChildCountOffset12004V1 = 0xFC;
inline constexpr std::size_t kGuiWidgetNameOffset12004V1 = 0x1B8;

} // namespace xar::ck3_12004
