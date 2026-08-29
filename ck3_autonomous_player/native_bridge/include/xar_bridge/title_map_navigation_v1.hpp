#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::game {

struct TitleMapNavigationFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;

  friend bool operator==(const TitleMapNavigationFrameV1 &,
                         const TitleMapNavigationFrameV1 &) = default;
};

struct LandedTitleMapAnchorV1 {
  std::string key;
  std::int32_t title_id = -1;
  std::int32_t tier_raw = 0;
  std::string tier_key;
  // Optional provenance only.  The stock camera command centers the complete
  // title bounds, not this province.  For c_bianzhou the current value is the
  // capital b_kaifeng / ProvinceID 9822 while the bounds cover all four
  // de-jure baronies.
  std::optional<std::int32_t> capital_province_id;

  // These pointers never cross the native bridge wire.  They bind the
  // subsequent owning-thread camera call to the exact objects validated by
  // this read.
  void *native_title = nullptr;
  void *native_capital_province = nullptr;

  friend bool operator==(const LandedTitleMapAnchorV1 &,
                         const LandedTitleMapAnchorV1 &) = default;
};

enum class ResolveLandedTitleMapAnchorResultV1 : std::uint32_t {
  resolved = 0,
  unsupported_build = 1,
  requires_owning_thread = 2,
  requires_paused = 3,
  map_not_ready = 4,
  title_key_not_found = 5,
  title_generation_mismatch = 6,
  title_not_centerable = 7,
  state_changed = 8,
  internal_error = 9,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kTitleMapNavigationV1Capability =
    "game.command.center-map-on-landed-title-v1";
inline constexpr std::string_view kTitleMapNavigationV1Step =
    "center-map-on-landed-title-v1";
inline constexpr std::string_view kTitleMapNavigationV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view kTitleMapNavigationV1ExecutableSha256 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kTitleMapNavigationV1BackendId =
    "ck3-1.19.0.6-native-title-map-navigation-v1";
inline constexpr std::string_view kTitleMapNavigationV1CompletionPredicate =
    "exact-build-native-camera-settled-v1";

inline constexpr std::uintptr_t kTitleMapGameStateSlotRva = 0x570E068;
inline constexpr std::uintptr_t kTitleMapLandedTitleStorageSlotRva =
    0x570C410;
inline constexpr std::uintptr_t kTitleMapLandedTitleFallbackSlotRva =
    0x570C3F8;
inline constexpr std::uintptr_t kTitleMapResolveLandedTitleByKeyRva =
    0xA0DC00;
inline constexpr std::uintptr_t kTitleMapResolveTitleProvinceRva =
    0x20B6B20;

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

struct TitleMapNavigationRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::string title_key;
};

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

} // namespace xar::ck3_11906
