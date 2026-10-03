#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_province.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::religion::pilgrimage_route {

inline constexpr std::string_view kSchema = "ck3_12003_pilgrimage_candidate_route_v1";
inline constexpr std::string_view kConfigurationSource = "native_local_candidate";
inline constexpr std::size_t kCreationInputBytes = 0x358;
inline constexpr std::size_t kTravelDataBytes = 0x898;

using ArrayInitialize = void *(*)(void *);
using ProvinceIdAppend = void (*)(void *, std::int32_t, const std::int32_t *, const std::int32_t *);
using RootConstruct = void *(*)(void *);
using NativeDestroy = void (*)(void *);
using TravelDataConstruct = void *(*)(void *, const void *);
using StartProvince = const void *(*)(const void *);
using RouteEvaluate = bool (*)(void *);
using ArrivalEvaluate = void (*)(void *);

struct Bindings {
  bool enabled = false;
  ck3_12002::ProvinceBindings provinces;
  const void *participant_allocator = nullptr;
  const void *travel_option_allocator = nullptr;
  const void *descriptor_allocator = nullptr;
  const std::uint64_t *native_default_date = nullptr;
  ArrayInitialize province_ids_initialize = nullptr;
  ArrayInitialize waypoints_initialize = nullptr;
  ProvinceIdAppend province_ids_append = nullptr;
  RootConstruct root_construct = nullptr;
  NativeDestroy creation_input_destroy = nullptr;
  TravelDataConstruct data_construct = nullptr;
  NativeDestroy data_destroy = nullptr;
  StartProvince start_province = nullptr;
  RouteEvaluate evaluate_route = nullptr;
  ArrivalEvaluate evaluate_arrival = nullptr;
};

struct Terms {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1, candidate_province_id = -1;
  std::optional<std::int32_t> native_start_province_id;
  std::optional<bool> route_valid;
  // The first int32 of the engine's native 8-byte Date, matching date_raw.
  // Preserve its value; this is neither elapsed days nor a formatted date.
  std::optional<std::int32_t> outbound_arrival_date_raw;
};

Bindings BindPlayerPilgrimageCandidateRouteImage12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Run on the existing application owner thread with its actual resolved player.
// candidate_province_id is an explicit full ProvinceID provided by the caller;
// this leaf does not establish holy-site eligibility or final selection legality.
// All native buffers belong to temporary local input/CData, never a live plan.
// The exact creation defaults retain no selected travel options or waypoints.
bool ReadPlayerPilgrimageCandidateRoute12003(const Bindings &, void *actual_played_character,
    std::int32_t played_character_id, std::int32_t date_raw, std::uint64_t capture_epoch,
    std::int32_t candidate_province_id, Terms &) noexcept;
std::string SerializePlayerPilgrimageCandidateRoute12003(const Terms &);

} // namespace xar::ck3_12003::religion::pilgrimage_route
