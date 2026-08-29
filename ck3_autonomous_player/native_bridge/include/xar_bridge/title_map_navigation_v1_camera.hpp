#pragma once

#include "xar_bridge/title_map_navigation_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::game {

enum class TitleMapNavigationCommandStatusV1 : std::uint32_t {
  pending = 0,
  centered = 1,
  already_centered = 2,
  unsupported_build = 3,
  requires_owning_thread = 4,
  requires_paused = 5,
  map_not_ready = 6,
  title_key_not_found = 7,
  title_generation_mismatch = 8,
  title_not_centerable = 9,
  camera_state_unavailable = 10,
  state_changed = 11,
  submission_failed = 12,
  internal_error = 13,
};

struct TitleMapNavigationCameraEvidenceV1 {
  // Native map-grid units returned by CK3's recursive title-bounds helper:
  // [min_x, min_z, max_x, max_z].
  std::array<std::int32_t, 4> bounds_extent{};
  // Exact signed int32 subtraction applied to the unadjusted X midpoint by
  // the stock title camera command.  Zero means no interface-mode offset.
  std::int32_t map_x_adjustment = 0;
  std::array<float, 3> expected_position_xyz{};
  // Independently read from camera+0x7B0[zoom_index].  It is never copied
  // back out of target_state.
  float expected_zoom_value = 0.0F;
  std::int32_t zoom_index = -1;
  // Exact-build state order:
  // [position_x, position_y, position_z, zoom,
  //  camera_param_4, camera_param_5].
  std::array<float, 6> current_state{};
  std::array<float, 6> target_state{};
  bool settled = false;
  // Conservative name for camera+0x777.  The bridge only proves that a set
  // byte prevents the stock command from writing its target position.
  bool target_write_blocked = false;

  friend bool operator==(const TitleMapNavigationCameraEvidenceV1 &,
                         const TitleMapNavigationCameraEvidenceV1 &) =
      default;
};

struct TitleMapNavigationCommandV1 {
  ck3_11906::TitleMapNavigationRequestV1 request;
  TitleMapNavigationFrameV1 binding{};
  LandedTitleMapAnchorV1 title{};
  TitleMapNavigationCameraEvidenceV1 camera{};
  TitleMapNavigationCommandStatusV1 status =
      TitleMapNavigationCommandStatusV1::pending;
  bool initialized = false;
  bool dispatched = false;
  // Borrowed identities only.  Every callback re-resolves and revalidates the
  // objects before comparing these values; no later callback dereferences a
  // pointer retained from an earlier pump.
  void *native_handler_identity = nullptr;
  void *native_camera_identity = nullptr;
  // The immediate post-dispatch target is retained separately because the
  // next native camera update may clamp it before the settled readback.
  std::array<float, 6> raw_expected_target{};
  std::array<float, 6> canonical_expected_target{};
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::uintptr_t kTitleMapIngameIdlerRootSlotRva =
    0x570F7B8;
inline constexpr std::uintptr_t kTitleMapRuntimeDynamicCastRva =
    0x3E631F4;
inline constexpr std::uintptr_t kTitleMapIdlerBaseTypeDescriptorRva =
    0x501EF28;
inline constexpr std::uintptr_t kTitleMapIngameIdlerTypeDescriptorRva =
    0x501EF50;
inline constexpr std::uintptr_t kTitleMapHandlerVtableRva = 0x40AF630;
inline constexpr std::uintptr_t kTitleMapCameraVtableRva = 0x40AF460;
inline constexpr std::uintptr_t kTitleMapComputeBoundsRva = 0x20B7DD0;
inline constexpr std::uintptr_t kTitleMapQueryHandlerModeRva = 0xA78200;
inline constexpr std::uintptr_t kTitleMapCenterCameraOnTitleRva = 0xA79C70;
inline constexpr std::uintptr_t kTitleMapCanonicalizeCameraStateRva =
    0x3473590;
inline constexpr std::uintptr_t kTitleMapBucketCountRva = 0x4F459A4;
inline constexpr std::uintptr_t kTitleMapBucketThresholdsSlotRva =
    0x4F45998;
inline constexpr std::uintptr_t kTitleMapHorizontalOffsetsSlotRva =
    0x4F459B0;
inline constexpr std::uintptr_t kTitleMapZoomIndexesSlotRva = 0x4F459C8;
inline constexpr std::uintptr_t kTitleMapDegreesToRadiansRva = 0x45945E0;

inline constexpr std::size_t kTitleMapHandlerCameraOffset = 0x628;
inline constexpr std::size_t kTitleMapCameraCurrentStateOffset = 0x710;
inline constexpr std::size_t kTitleMapCameraTargetStateOffset = 0x728;
inline constexpr std::size_t kTitleMapCameraZoomIndexOffset = 0x744;
inline constexpr std::size_t kTitleMapCameraTransientXOffset = 0x75C;
inline constexpr std::size_t kTitleMapCameraTransientZOffset = 0x760;
inline constexpr std::size_t kTitleMapCameraTargetWriteBlockedOffset =
    0x777;
inline constexpr std::size_t kTitleMapCameraZoomTableOffset = 0x7B0;
inline constexpr std::size_t kTitleMapCameraZoomCountOffset = 0x7BC;
inline constexpr std::size_t kTitleMapCameraParam4TableOffset = 0x7C8;
inline constexpr std::size_t kTitleMapCameraParam4EnabledOffset = 0x7D4;

#if defined(_MSC_VER)
#define XAR_TITLE_MAP_CAMERA_FASTCALL __fastcall
#define XAR_TITLE_MAP_CAMERA_CDECL __cdecl
#else
#define XAR_TITLE_MAP_CAMERA_FASTCALL
#define XAR_TITLE_MAP_CAMERA_CDECL
#endif

using NativeRuntimeDynamicCastV1 = void *(XAR_TITLE_MAP_CAMERA_CDECL *)(
    void *object, long vf_delta, const void *source_type,
    const void *target_type, int is_reference);
using NativeComputeTitleBoundsV1 = bool(XAR_TITLE_MAP_CAMERA_FASTCALL *)(
    void *landed_title, std::int32_t *bounds);
using NativeQueryTitleMapHandlerModeV1 = bool(
    XAR_TITLE_MAP_CAMERA_FASTCALL *)(void *handler, std::int32_t mask);
using NativeCenterCameraOnTitleV1 = void(XAR_TITLE_MAP_CAMERA_FASTCALL *)(
    void *handler, void *landed_title, bool force_zoom);
using NativeCanonicalizeCameraStateV1 = void(
    XAR_TITLE_MAP_CAMERA_FASTCALL *)(void *camera, float *state6);

#undef XAR_TITLE_MAP_CAMERA_FASTCALL
#undef XAR_TITLE_MAP_CAMERA_CDECL

struct TitleMapNavigationCameraEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  void **ingame_idler_root_slot = nullptr;
  NativeRuntimeDynamicCastV1 runtime_dynamic_cast = nullptr;
  const void *idler_base_type_descriptor = nullptr;
  const void *ingame_idler_type_descriptor = nullptr;
  const void *expected_handler_vtable = nullptr;
  const void *expected_camera_vtable = nullptr;
  NativeComputeTitleBoundsV1 compute_title_bounds = nullptr;
  NativeQueryTitleMapHandlerModeV1 query_handler_mode = nullptr;
  NativeCenterCameraOnTitleV1 center_camera_on_title = nullptr;
  NativeCanonicalizeCameraStateV1 canonicalize_camera_state = nullptr;
  const std::int32_t *bucket_count = nullptr;
  const std::int32_t *const *bucket_thresholds_slot = nullptr;
  const std::int32_t *const *horizontal_offsets_slot = nullptr;
  const std::int32_t *const *zoom_indexes_slot = nullptr;
  const float *degrees_to_radians = nullptr;
};

using ResolveTitleMapHandlerCameraFixtureV1 = bool (*)(
    void *context, void *&handler, void *&camera) noexcept;
using ComputeTitleMapBoundsFixtureV1 = bool (*)(
    void *context, void *landed_title,
    std::array<std::int32_t, 4> &bounds) noexcept;
using QueryTitleMapHandlerModeFixtureV1 = bool (*)(
    void *context, void *handler, std::int32_t mask,
    bool &enabled) noexcept;
using CanonicalizeTitleMapCameraStateFixtureV1 = bool (*)(
    void *context, void *camera, std::array<float, 6> &state) noexcept;
using DispatchTitleMapCameraFixtureV1 = bool (*)(
    void *context, void *handler, void *landed_title,
    bool force_zoom) noexcept;

struct TitleMapNavigationCameraAccessV1 {
  TitleMapNavigationAccessV1 title;
  ResolveTitleMapHandlerCameraFixtureV1 resolve_handler_camera_fixture =
      nullptr;
  ComputeTitleMapBoundsFixtureV1 compute_bounds_fixture = nullptr;
  QueryTitleMapHandlerModeFixtureV1 query_handler_mode_fixture = nullptr;
  CanonicalizeTitleMapCameraStateFixtureV1 canonicalize_fixture = nullptr;
  DispatchTitleMapCameraFixtureV1 dispatch_fixture = nullptr;
};

TitleMapNavigationCameraEnvironmentV1
BindTitleMapNavigationCameraEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

// Executes exactly one application-main callback worth of work.  A pending
// return must be followed by a fresh mailbox ticket on a later pump; callers
// must never spin or wait from inside the owning thread callback.
game::TitleMapNavigationCommandStatusV1 AdvanceTitleMapNavigationCommandV1(
    const TitleMapNavigationNativeEnvironmentV1 &title_environment,
    const TitleMapNavigationCameraEnvironmentV1 &camera_environment,
    const TitleMapNavigationCameraAccessV1 &access,
    game::TitleMapNavigationCommandV1 &command) noexcept;

bool IsTitleMapNavigationTerminalV1(
    game::TitleMapNavigationCommandStatusV1 status) noexcept;

std::string_view TitleMapNavigationCommandRejectionCodeV1(
    game::TitleMapNavigationCommandStatusV1 status) noexcept;

} // namespace xar::ck3_11906
