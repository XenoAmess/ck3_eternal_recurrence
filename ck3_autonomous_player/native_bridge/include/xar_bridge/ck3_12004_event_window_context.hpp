#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_event_window_context.hpp"

namespace xar::ck3_12004 {

// The observation DTO and materialized-window reader are caller-owned software.
// The factory binds only the independently mapped actual .4 executable image.
using EventWindowBindings = ck3_12002::EventWindowBindings;

// Finite actual .4 constructor/registry operands and seven readonly callbacks:
// event-window-12004/DECLARED-NATIVE-MAP.json and LEAF-AND-TYPE-MAP.json.
inline constexpr std::uintptr_t kEventWindowIdlerGfxVtableRva12004V1 = 0x44BC418;
inline constexpr std::uintptr_t kEventWindowPrimaryVtableRva12004V1 = 0x4597920;
inline constexpr std::uintptr_t kEventSplashWindowPrimaryVtableRva12004V1 = 0x4596D48;
inline constexpr std::uintptr_t kActivityEventHandlerPrimaryVtableRva12004V1 = 0x44BA8A0;
inline constexpr std::uintptr_t kActivityEventWindowPrimaryVtableRva12004V1 = 0x4579020;
inline constexpr std::uintptr_t kEventIndicatorSchemeTypeVtableRva12004V1 = 0x48B9F30;
inline constexpr std::uintptr_t kEventIndicatorTraitDatabaseSlotRva12004V1 = 0x5C67528;
inline constexpr std::uintptr_t kEventIndicatorSchemeDatabaseSlotRva12004V1 = 0x5C67108;
inline constexpr std::uintptr_t kEventIndicatorSchemeFallbackSlotRva12004V1 = 0x5D1E2A0;
inline constexpr std::uintptr_t kEventIndicatorHashStableKeyRva12004V1 = 0x3F7E220;
inline constexpr std::uintptr_t kEventIndicatorLookupSchemeTypeRva12004V1 = 0xABFBA0;
inline constexpr std::uintptr_t kEventGenericTypeRegistryGetterRva12004V1 = 0x3795A60;
inline constexpr std::uintptr_t kEventGenericTypeRegistryRva12004V1 = 0x54F2AF0;
inline constexpr std::uintptr_t kEventGenericTypeNameResolverRva12004V1 = 0x3F4F8E0;
inline constexpr std::uintptr_t kEventGenericTypeNameFallbackRva12004V1 = 0x5DC1128;
inline constexpr std::uintptr_t kEventScriptIdentifierTableGetterRva12004V1 = 0x3F8A7E0;
inline constexpr std::uintptr_t kEventScriptIdentifierLookupRva12004V1 = 0x3F8A660;
inline constexpr std::uintptr_t kEventScriptIdentifierNameResolverRva12004V1 = 0x3F8A6D0;
inline constexpr std::uintptr_t kEventScriptIdentifierNameFallbackRva12004V1 = 0x5DC1368;

EventWindowBindings BindEventWindowImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
