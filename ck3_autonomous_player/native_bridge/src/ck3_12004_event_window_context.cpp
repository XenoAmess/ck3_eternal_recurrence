#include "xar_bridge/ck3_12004_event_window_context.hpp"
#include "xar_bridge/ck3_12004_events.hpp"
#include "xar_bridge/ck3_12004_faction_alerts.hpp"
#include "xar_bridge/ck3_12004_snapshot_foundation.hpp"

namespace xar::ck3_12004 {
namespace {

bool ReadEventWindowObservationPrefix12004(
    const EventWindowBindings &bindings, game::Snapshot &output) noexcept {
  output = {};
  CoreSnapshotPrefix core{};
  auto events = ck3_12004::BindSnapshotEventsImage(
      bindings.events.image_base, ck3_12004::kExecutableSha256);
  events.core = bindings.events.core;
  events.get_current_event = bindings.events.get_current_event;
  events.pending_interaction_storage_slot =
      bindings.events.pending_interaction_storage_slot;
  events.is_pending_for_character = bindings.events.is_pending_for_character;
  events.validate_reply = bindings.events.validate_reply;
  // The independent snapshot factory keeps actual .4 Reply vptrs. The old
  // Events reader embeds historical tables and cannot validate this frame.
  if (!ck3_12004::ReadCoreSnapshot(bindings.events.core, core) ||
      !ck3_12004::ReadEventsSnapshot(events, output)) {
    return false;
  }
  output.date_raw = core.clock.date_raw;
  output.paused = core.clock.paused;
  output.speed = core.clock.speed;
  output.map_ready = core.map_ready;
  output.player_id = core.local_player_id;
  output.has_played_character = core.has_played_character;
  output.played_character_id = core.played_character_id;
  output.played_character_alive = core.played_character_alive;
  return true;
}

} // namespace

EventWindowBindings BindEventWindowImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  EventWindowBindings result{};
  result.events = ck3_12004::BindEventsImage(image_base, executable_sha256);
  if (!result.events.core.enabled) return result;

  const auto factions = ck3_12004::BindPlayerFactionAlertsImage12004(
      image_base, executable_sha256);
  result.landed_title_storage_slot = factions.landed_title_storage_slot;
  result.landed_title_fallback_slot = factions.landed_title_fallback_slot;
  result.faction_scope_storage_slot = factions.faction_storage_slot;
  result.faction_scope_fallback_slot = factions.faction_fallback_slot;
  result.faction_scope_expected_vtable = factions.expected_faction_vtable;
  result.allow_null_saved_character_scope = true;
  result.read_numeric_scope_value = true;
  result.read_observation_prefix = &ReadEventWindowObservationPrefix12004;

  result.ingame_interface_idler_vtable =
      image_base + kEventWindowIdlerGfxVtableRva12004V1;
  result.event_window_primary_vtable =
      image_base + kEventWindowPrimaryVtableRva12004V1;
  result.splash_window_primary_vtable =
      image_base + kEventSplashWindowPrimaryVtableRva12004V1;
  result.activity_handler_primary_vtable =
      image_base + kActivityEventHandlerPrimaryVtableRva12004V1;
  result.activity_window_primary_vtable =
      image_base + kActivityEventWindowPrimaryVtableRva12004V1;
  result.scheme_type_primary_vtable =
      image_base + kEventIndicatorSchemeTypeVtableRva12004V1;
  result.trait_database_slot = reinterpret_cast<void **>(
      image_base + kEventIndicatorTraitDatabaseSlotRva12004V1);
  result.scheme_type_database_slot = reinterpret_cast<void **>(
      image_base + kEventIndicatorSchemeDatabaseSlotRva12004V1);
  result.scheme_type_fallback_slot = reinterpret_cast<void **>(
      image_base + kEventIndicatorSchemeFallbackSlotRva12004V1);
  result.expected_generic_value_type_registry = reinterpret_cast<void *>(
      image_base + kEventGenericTypeRegistryRva12004V1);
  result.generic_value_type_name_fallback =
      reinterpret_cast<const std::string *>(
          image_base + kEventGenericTypeNameFallbackRva12004V1);
  result.script_identifier_name_fallback = reinterpret_cast<const std::string *>(
      image_base + kEventScriptIdentifierNameFallbackRva12004V1);
  result.hash_stable_key = reinterpret_cast<ck3_12002::EventHashStableKey>(
      image_base + kEventIndicatorHashStableKeyRva12004V1);
  result.lookup_scheme_type =
      reinterpret_cast<ck3_12002::EventLookupSchemeType>(
          image_base + kEventIndicatorLookupSchemeTypeRva12004V1);
  result.get_generic_value_type_registry =
      reinterpret_cast<ck3_12002::EventGetRegistry>(
          image_base + kEventGenericTypeRegistryGetterRva12004V1);
  result.resolve_generic_value_type_name =
      reinterpret_cast<ck3_12002::EventResolveTypeName>(
          image_base + kEventGenericTypeNameResolverRva12004V1);
  result.get_script_identifier_table =
      reinterpret_cast<ck3_12002::EventGetRegistry>(
          image_base + kEventScriptIdentifierTableGetterRva12004V1);
  result.lookup_script_identifier_id =
      reinterpret_cast<ck3_12002::EventLookupIdentifier>(
          image_base + kEventScriptIdentifierLookupRva12004V1);
  result.resolve_script_identifier_name =
      reinterpret_cast<ck3_12002::EventResolveIdentifierName>(
          image_base + kEventScriptIdentifierNameResolverRva12004V1);
  return result;
}

} // namespace xar::ck3_12004
