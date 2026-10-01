#pragma once

#include "xar_bridge/ck3_12002_events.hpp"
#include "xar_bridge/event_window_context_v1.hpp"

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kEventWindowIdlerGfxVtableRva = 0x44BC408;
inline constexpr std::uintptr_t kEventWindowPrimaryVtableRva = 0x4597910;
inline constexpr std::uintptr_t kEventSplashWindowPrimaryVtableRva = 0x4596D38;
inline constexpr std::uintptr_t kEventIndicatorSchemeTypeVtableRva = 0x48B9F20;
inline constexpr std::uintptr_t kEventIndicatorTraitDatabaseSlotRva = 0x5C67528;
inline constexpr std::uintptr_t kEventIndicatorSchemeDatabaseSlotRva = 0x5C67108;
inline constexpr std::uintptr_t kEventIndicatorSchemeFallbackSlotRva = 0x5D1E2A0;
inline constexpr std::uintptr_t kEventIndicatorHashStableKeyRva = 0x3F7E240;
inline constexpr std::uintptr_t kEventIndicatorLookupSchemeTypeRva = 0xABFBA0;
inline constexpr std::uintptr_t kEventGenericTypeRegistryGetterRva = 0x3795A80;
inline constexpr std::uintptr_t kEventGenericTypeRegistryRva = 0x54F2AF0;
inline constexpr std::uintptr_t kEventGenericTypeNameResolverRva = 0x3F4F900;
inline constexpr std::uintptr_t kEventGenericTypeNameFallbackRva = 0x5DC1128;
inline constexpr std::uintptr_t kEventScriptIdentifierTableGetterRva = 0x3F8A800;
inline constexpr std::uintptr_t kEventScriptIdentifierLookupRva = 0x3F8A680;
inline constexpr std::uintptr_t kEventScriptIdentifierNameResolverRva = 0x3F8A6F0;
inline constexpr std::uintptr_t kEventScriptIdentifierNameFallbackRva = 0x5DC1368;

using EventHashStableKey = std::int32_t (*)(void *, const char *, std::uint32_t);
using EventLookupSchemeType = void *(*)(void *, std::int32_t);
using EventGetRegistry = void *(*)();
using EventResolveTypeName = const std::string *(*)(std::int32_t);
using EventResolveIdentifierName = const std::string *(*)(void *, std::int32_t);
using EventLookupIdentifier = std::int32_t *(*)(void *, std::int32_t *, const void *);

struct EventWindowBindings {
  EventsBindings events;
  std::uintptr_t ingame_interface_idler_vtable = 0;
  std::uintptr_t event_window_primary_vtable = 0;
  std::uintptr_t splash_window_primary_vtable = 0;
  std::uintptr_t scheme_type_primary_vtable = 0;
  void **trait_database_slot = nullptr;
  void **scheme_type_database_slot = nullptr;
  void **scheme_type_fallback_slot = nullptr;
  void *expected_generic_value_type_registry = nullptr;
  const std::string *generic_value_type_name_fallback = nullptr;
  const std::string *script_identifier_name_fallback = nullptr;
  EventHashStableKey hash_stable_key = nullptr;
  EventLookupSchemeType lookup_scheme_type = nullptr;
  EventGetRegistry get_generic_value_type_registry = nullptr;
  EventResolveTypeName resolve_generic_value_type_name = nullptr;
  EventGetRegistry get_script_identifier_table = nullptr;
  EventLookupIdentifier lookup_script_identifier_id = nullptr;
  EventResolveIdentifierName resolve_script_identifier_name = nullptr;
};

EventWindowBindings BindEventWindowImage(std::uintptr_t image_base,
                                       std::string_view executable_sha256) noexcept;

game::ReadEventWindowContextResultV1 ReadEventWindowContextV1(
    const EventWindowBindings &bindings, std::uint64_t expected_snapshot_revision,
    std::int32_t expected_event_instance_id,
    game::EventWindowContextV1 &output) noexcept;

std::string SerializeEventWindowContextV1(
    const game::EventWindowContextV1 &context);

bool ParseEventWindowContextRequestV1(
    std::string_view json, std::uint64_t &expected_revision,
    std::int32_t &event_instance_id) noexcept;

} // namespace xar::ck3_12002
