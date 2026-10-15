#pragma once
#include "xar_bridge/ck3_12004_generic_gui.hpp"
#include <array>

namespace xar::ck3_12004 {
// Actual R0177 slot2; finite source entry ends at its first indirect tail jmp.
// This is a common thunk, not a MilitaryView method-name binding.
inline constexpr std::uintptr_t kGuiCallbackThunkRva12004V1 = 0x3AA30E0;
inline constexpr std::array<unsigned char, 18> kGuiCallbackThunkBytes12004V1{{
    0x48,0x8B,0xC1,0x48,0x8D,0x51,0x10,0x48,0x8B,0x89,0xF0,0x00,0x00,0x00,0x48,0xFF,0x60,0x08}};
inline constexpr char kGuiCallbackThunkBytesSha25612004V1[] =
    "7a37683abfa5cb9317164e719bc14ba7cc067f79fee8e086267a11d8b18f3563";
} // namespace xar::ck3_12004
