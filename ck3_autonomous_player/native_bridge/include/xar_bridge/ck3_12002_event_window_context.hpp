#pragma once

#include "xar_bridge/ck3_12002_events.hpp"
#include "xar_bridge/event_window_context_v1.hpp"

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kEventScopeLandedTitleStorageSlotRva = 0x5D1DAF8;
inline constexpr std::uintptr_t kEventScopeLandedTitleFallbackSlotRva = 0x5D1DAE0;
inline constexpr std::uintptr_t kEventWindowIdlerGfxVtableRva = 0x44BC408;
inline constexpr std::uintptr_t kEventWindowPrimaryVtableRva = 0x4597910;
inline constexpr std::uintptr_t kEventSplashWindowPrimaryVtableRva = 0x4596D38;
inline constexpr std::uintptr_t kActivityEventHandlerPrimaryVtableRva = 0x44BA890;
inline constexpr std::uintptr_t kActivityEventWindowPrimaryVtableRva = 0x4579010;
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
using EventLookupTraitDefinition = void *(*)(void *, std::int32_t);
using EventGetRegistry = void *(*)();
using EventResolveTypeName = const std::string *(*)(std::int32_t);
using EventResolveIdentifierName = const std::string *(*)(void *, std::int32_t);
using EventLookupIdentifier = std::int32_t *(*)(void *, std::int32_t *, const void *);

struct EventWindowBindings {
  EventsBindings events;
  std::uintptr_t ingame_interface_idler_vtable = 0;
  std::uintptr_t event_window_primary_vtable = 0;
  std::uintptr_t splash_window_primary_vtable = 0;
  // The exact patch3 activity window presents its selected ViewInsert data.
  std::uintptr_t activity_handler_primary_vtable = 0;
  std::uintptr_t activity_window_primary_vtable = 0;
  // Only the exact patch3 binder admits the observed native null payload in
  // named saved scopes. Root scopes and legacy patch2 behavior stay strict.
  bool allow_null_saved_character_scope = false;
  // Numeric kind1/value/subtype0 is independently bound to exact patch3.
  bool read_numeric_scope_value = false;
  // Exact patch3 type5 FullRef storage; legacy patch2 generic scopes stay opaque.
  void **landed_title_storage_slot = nullptr;
  void **landed_title_fallback_slot = nullptr;
  void **faction_scope_storage_slot = nullptr;
  void **faction_scope_fallback_slot = nullptr;
  std::uintptr_t faction_scope_expected_vtable = 0;
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
  // Actual .4 supplies its independent Core/Events observation algorithms.
  // Historical factories leave this null and retain their original readers.
  bool (*read_observation_prefix)(const EventWindowBindings &,
                                  game::Snapshot &) noexcept = nullptr;
  // Actual .4 resolves the canonical definition by native database ID.
  // Historical factories keep their original definition-member identity path.
  EventLookupTraitDefinition lookup_trait_definition = nullptr;
};

EventWindowBindings BindEventWindowImage(std::uintptr_t image_base,
                                       std::string_view executable_sha256) noexcept;

game::ReadEventWindowContextResultV1 ReadEventWindowContextV1(
    const EventWindowBindings &bindings, std::uint64_t expected_snapshot_revision,
    std::int32_t expected_event_instance_id,
    game::EventWindowContextV1 &output) noexcept;

std::string SerializeEventWindowContextV1(
    const game::EventWindowContextV1 &context,
    bool allow_null_saved_character_scope = false);

bool ParseEventWindowContextRequestV1(
    std::string_view json, std::uint64_t &expected_revision,
    std::int32_t &event_instance_id) noexcept;

} // namespace xar::ck3_12002
