#pragma once

// CK3 1.20.0.2 exact-build bindings. Shared DTOs retain the v1 wire schema.
#include "xar_bridge/title_map_navigation_v1_camera.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kTitleMapNavigationV1Capability =
    "game.command.center-map-on-landed-title-v1";
inline constexpr std::string_view kTitleMapNavigationV1Step =
    "center-map-on-landed-title-v1";
inline constexpr std::string_view kTitleMapNavigationV1GameVersion =
    "1.20.0.2";
inline constexpr std::string_view kTitleMapNavigationV1ExecutableSha256 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::string_view kTitleMapNavigationV1BackendId =
    "ck3-1.20.0.2-native-title-map-navigation-v1";
inline constexpr std::string_view kTitleMapNavigationV1CompletionPredicate =
    "exact-build-native-camera-settled-v1";

inline constexpr std::uintptr_t kTitleMapGameStateSlotRva = 0x5C68C50;
inline constexpr std::uintptr_t kTitleMapLandedTitleStorageSlotRva =
    0x5D1DAF8;
inline constexpr std::uintptr_t kTitleMapLandedTitleFallbackSlotRva =
    0x5D1DAE0;
inline constexpr std::uintptr_t kTitleMapResolveLandedTitleByKeyRva =
    0xA847A0;
inline constexpr std::uintptr_t kTitleMapResolveTitleProvinceRva =
    0x230F900;

#if defined(_MSC_VER)
#define XAR_TITLE_MAP_FASTCALL __fastcall
#else
#define XAR_TITLE_MAP_FASTCALL
#endif

// The first argument is an exact MSVC x64 std::string object.  The bridge
// constructs a read-only ABI mirror instead of transferring allocation
// ownership across the executable/DLL CRT boundary.
using NativeResolveLandedTitleByKeyV1 =
    void *(XAR_TITLE_MAP_FASTCALL *)(const void *native_msvc_string);
using NativeResolveTitleProvinceV1 =
    void *(XAR_TITLE_MAP_FASTCALL *)(void *landed_title);

#undef XAR_TITLE_MAP_FASTCALL

struct TitleMapNavigationNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  void **game_state_slot = nullptr;
  void **landed_title_storage_slot = nullptr;
  void **landed_title_fallback_slot = nullptr;
  NativeResolveLandedTitleByKeyV1 resolve_landed_title_by_key = nullptr;
  NativeResolveTitleProvinceV1 resolve_title_province = nullptr;
};

using CaptureTitleMapNavigationFrameV1 = bool (*)(
    void *context, game::TitleMapNavigationFrameV1 &output) noexcept;
using IsTitleMapNavigationOwningThreadV1 =
    bool (*)(void *context) noexcept;
using ReadTitleMapNavigationMemoryV1 = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;
using ReadTitleMapNavigationStringV1 = bool (*)(
    void *context, const void *native_string,
    std::string &output) noexcept;
using ResolveTitleMapNavigationTitleFixtureV1 = bool (*)(
    void *context, std::string_view key, void *&output) noexcept;
using ResolveTitleMapNavigationProvinceFixtureV1 = bool (*)(
    void *context, void *landed_title, void *&output) noexcept;

struct TitleMapNavigationAccessV1 {
  void *context = nullptr;
  CaptureTitleMapNavigationFrameV1 capture_frame = nullptr;
  IsTitleMapNavigationOwningThreadV1 is_owning_thread = nullptr;
  ReadTitleMapNavigationMemoryV1 read_memory = nullptr;
  ReadTitleMapNavigationStringV1 read_string = nullptr;

  // Test-only ABI-independent seams.  Production exact-environment
  // validation rejects environments that opt into these overrides.
  ResolveTitleMapNavigationTitleFixtureV1 resolve_title_fixture = nullptr;
  ResolveTitleMapNavigationProvinceFixtureV1 resolve_province_fixture =
      nullptr;
};

using TitleMapNavigationRequestV1 = ck3_11906::TitleMapNavigationRequestV1;

TitleMapNavigationNativeEnvironmentV1 BindTitleMapNavigationNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

bool IsCanonicalLandedTitleKeyV1(std::string_view key) noexcept;

game::ResolveLandedTitleMapAnchorResultV1 ResolveLandedTitleMapAnchorV1(
    const TitleMapNavigationNativeEnvironmentV1 &environment,
    const TitleMapNavigationAccessV1 &access,
    const TitleMapNavigationRequestV1 &request,
    game::TitleMapNavigationFrameV1 &binding,
    game::LandedTitleMapAnchorV1 &output) noexcept;

std::string_view TitleMapNavigationRejectionCodeV1(
    game::ResolveLandedTitleMapAnchorResultV1 result) noexcept;

} // namespace xar::ck3_12002

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kTitleMapIngameIdlerRootSlotRva =
    0x5C6A520;
inline constexpr std::uintptr_t kTitleMapRuntimeDynamicCastRva =
    0x4260E94;
inline constexpr std::uintptr_t kTitleMapIdlerBaseTypeDescriptorRva =
    0x5514438;
inline constexpr std::uintptr_t kTitleMapIngameIdlerTypeDescriptorRva =
    0x5514460;
inline constexpr std::uintptr_t kTitleMapHandlerVtableRva = 0x44BA890;
inline constexpr std::uintptr_t kTitleMapCameraVtableRva = 0x44BA688;
inline constexpr std::uintptr_t kTitleMapComputeBoundsRva = 0x2311040;
inline constexpr std::uintptr_t kTitleMapQueryHandlerModeRva = 0xAF2530;
inline constexpr std::uintptr_t kTitleMapCenterCameraOnTitleRva = 0xAF3FB0;
inline constexpr std::uintptr_t kTitleMapCanonicalizeCameraStateRva =
    0x3846160;
inline constexpr std::uintptr_t kTitleMapBucketCountRva = 0x5438C2C;
inline constexpr std::uintptr_t kTitleMapBucketThresholdsSlotRva =
    0x5438C20;
inline constexpr std::uintptr_t kTitleMapHorizontalOffsetsSlotRva =
    0x5438C38;
inline constexpr std::uintptr_t kTitleMapZoomIndexesSlotRva = 0x5438C50;
inline constexpr std::uintptr_t kTitleMapDegreesToRadiansRva = 0x49F60C0;

inline constexpr std::size_t kTitleMapHandlerCameraOffset = 0x670;
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

} // namespace xar::ck3_12002

namespace xar::ck3_12002 {

std::string SerializeTitleMapNavigationResultV1(
    const game::TitleMapNavigationCommandV1 &command,
    std::uint64_t dispatch_ticket_sequence);

} // namespace xar::ck3_12002
