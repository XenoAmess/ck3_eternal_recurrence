#pragma once

#include "xar_bridge/ck3_12004_generic_gui.hpp"

namespace xar::ck3_12004 {

// Named source-use closure, not an alias of the .3 GUI profile.
inline constexpr std::uintptr_t kUiSelectUnitRva12004V1 = 0xAF9000;
inline constexpr std::uintptr_t kUiArmyWindowTypeDescriptor12004V1 = 0x5776990;
inline constexpr std::uintptr_t kUiArmyStorage12004V1 = 0x5D1DE48;
inline constexpr std::uintptr_t kUiUnitStorage12004V1 = 0x5D1E380;
inline constexpr std::size_t kUiArmyWindowHandlerSlot12004V1 = 0xC8;
inline constexpr std::size_t kUiArmyWindowSubjectOffset12004V1 = 0xC8;
inline constexpr std::size_t kUiArmyWindowGuiRootOffset12004V1 = 0x60;
inline constexpr std::size_t kUiArmyWindowHandlerOffset12004V1 = 0xA0;
inline constexpr std::uintptr_t kUiRuntimeDynamicCastRva12004V1 = 0x4260E74;
inline constexpr std::uintptr_t kUiIdlerRootSlotRva12004V1 = 0x5C6A520;
inline constexpr std::uintptr_t kUiIdlerBaseTypeDescriptor12004V1 = 0x5514438;
inline constexpr std::uintptr_t kUiIngameIdlerTypeDescriptor12004V1 = 0x5514460;
inline constexpr std::uintptr_t kUiHandlerPrimaryVtable12004V1 = 0x44BA8A0;
inline constexpr std::uintptr_t kUiArmyWindowPrimaryVtable12004V1 = 0x454C5C0;
inline constexpr std::uintptr_t kUiArmyWindowCol12004V1 = 0x4B43498;
inline constexpr std::uintptr_t kUiArmyTooltipSetHover12004V1 = 0x3AA6020;
inline constexpr std::uintptr_t kUiArmyTooltipTextboxVtable12004V1 = 0x497B878;
inline constexpr std::uintptr_t kUiArmyTooltipTextboxCol12004V1 = 0x5082290;
inline constexpr std::uintptr_t kUiArmyTooltipTextboxTypeDescriptor12004V1 = 0x55BD330;
inline constexpr std::uintptr_t kUiArmyTooltipTextGetter12004V1 = 0x1042240;

struct IngameUiBindings12004V1 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
};

IngameUiBindings12004V1 BindIngameUiImage12004V1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
