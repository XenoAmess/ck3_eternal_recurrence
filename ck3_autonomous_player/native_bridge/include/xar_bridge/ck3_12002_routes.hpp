#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/projected_contact_scope_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

// Owning-thread readers. The caller supplies its complete paused snapshot;
// the reader checks the native clock and resolves every full-generation ID.
struct RouteBindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **jomini_state_slot = nullptr;
  void **army_storage_slot = nullptr;
  void **army_internal_storage_slot = nullptr;
  void **regiment_storage_slot = nullptr;
  void **character_storage_slot = nullptr;
  void **combat_storage_slot = nullptr;
  void **battle_result_storage_slot = nullptr;
  void **contact_game_mode_slot = nullptr;

  using UnitSpeed = std::int64_t *(*)(void *, std::int64_t *);
  using TravelDuration = std::int64_t *(*)(void *, std::int64_t *, const void *, void *);
  using MoveMode = std::int32_t (*)(void *, void *, std::int32_t);
  using MoveOrigin = void *(*)(void *);
  using PathContext = void *(*)(void *, void *);
  using PathConstructor = void *(*)(void *);
  using BuildRoute = bool (*)(void *, void *, void *, std::int32_t, void *);
  using Destructor = void *(*)(void *, std::int32_t);
  using Hostile = bool (*)(void *, void *, bool);
  using ArmyPredicate = bool (*)(void *);
  using ProvinceHolder = std::int32_t *(*)(void *, std::int32_t *);
  using DefenderPredicate = bool (*)(void *, void *);
  using UnitProvince = void *(*)(void *);

  UnitSpeed read_unit_land_route_speed = nullptr;
  UnitSpeed read_unit_naval_route_speed = nullptr;
  UnitSpeed read_unit_current_edge_speed = nullptr;
  TravelDuration read_route_travel_duration = nullptr;
  MoveMode get_army_move_mode = nullptr;
  MoveOrigin resolve_move_origin = nullptr;
  UnitSpeed read_route_progress = nullptr;
  const std::int64_t *movement_locked_threshold = nullptr;
  UnitProvince get_route_front = nullptr;
  UnitProvince get_route_tail = nullptr;
  PathContext construct_move_path_context = nullptr;
  PathConstructor construct_army_move_path = nullptr;
  BuildRoute build_army_move_route = nullptr;
  Destructor destroy_move_army_command = nullptr;
  std::uintptr_t move_army_primary_vtable = 0;
  std::uintptr_t move_army_secondary_vtable = 0;
  Hostile is_character_hostile = nullptr;
  ArmyPredicate is_army_empty_for_contact = nullptr;
  ArmyPredicate is_army_in_combat = nullptr;
  ProvinceHolder read_province_holder_character_id = nullptr;
  DefenderPredicate classify_contact_defender_by_holder = nullptr;
  DefenderPredicate classify_contact_defender_fallback = nullptr;
};

RouteBindings BindRouteImage(std::uintptr_t image_base,
                             std::string_view executable_sha256) noexcept;

// Project only the engine's already committed remaining path. The battle
// reader owns its complete-frame double sampling and scope comparison.
bool ReadCommittedRouteTimeline(
    const RouteBindings &, const game::Snapshot &paused_scope,
    std::int32_t public_cunit_id, std::vector<std::int32_t> &province_ids,
    std::vector<std::int32_t> &arrival_date_raws) noexcept;

game::RouteContactHorizonStatus ReadRouteContactHorizon(
    const RouteBindings &, const game::Snapshot &paused_scope,
    const game::RouteContactHorizonRequest &,
    game::RouteContactHorizonSnapshot &) noexcept;

game::ActualContactScopeStatus ReadActualContactScope(
    const RouteBindings &, const game::Snapshot &paused_scope,
    const game::ActualContactScopeRequest &,
    game::ActualContactScopeSnapshot &) noexcept;

// Hypothetical arrival against current target state. The real incoming unit
// stays at its current Province; only a caller-owned membership list is used.
game::ProjectedContactScopeStatus ReadProjectedContactScope(
    const RouteBindings &, const game::Snapshot &paused_scope,
    const game::ProjectedContactScopeRequest &,
    game::ProjectedContactScopeSnapshot &) noexcept;

} // namespace xar::ck3_12002
