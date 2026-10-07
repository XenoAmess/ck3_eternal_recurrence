#pragma once

#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"

namespace xar::ck3_12004 {

// Software profile shared with the preserved .3 implementation. Actual .4
// entries are individually source-mapped, not derived with one image delta.
// Finite full bodies and COL/type names: grant/FINITE-GRANT-CAPTURE-003..006.
struct GrantTitlePickerImageProfileV1 {
  bool actual4;
  ck3_11906::GuiAbiRevisionV1 gui_revision;
  std::uintptr_t logical_vtable;
  std::uint32_t logical_type;
  std::uintptr_t gfx_vtable;
  std::uint32_t gfx_type;
  std::uintptr_t handler_vtable;
  std::uint32_t handler_type;
  std::uintptr_t grant_vtable;
  std::uint32_t grant_type;
  std::uintptr_t confirmation_vtable;
  std::uint32_t confirmation_type;
  std::uintptr_t title_vtable;
  std::uintptr_t row_title, row_selected, row_selectable, row_toggle;
  std::uintptr_t can_send, send, copy_context, handler_open, refresh, is_open;
};

inline constexpr GrantTitlePickerImageProfileV1 kGrantTitlePickerImageProfile12004V1{
    true, ck3_11906::GuiAbiRevisionV1::crozier12004,
    0x44D6058, 0x55072C0, 0x44BC418, 0x5514460,
    0x44BA8A0, 0x5694B20, 0x452DBE8, 0x5742F58,
    0x45250E8, 0x5731D88, 0x4712A28,
    0x10EC1F0, 0x10EC2F0, 0x10EC4B0, 0x10EC0E0,
    0x117C520, 0x117BAD0, 0x10E6FE0, 0xAF34A0, 0x10E7800, 0x2160380};

} // namespace xar::ck3_12004
