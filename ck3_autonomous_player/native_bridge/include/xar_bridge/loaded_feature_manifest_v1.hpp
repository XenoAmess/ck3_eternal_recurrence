#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

enum class LoadedFeatureManifestStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class LoadedFeatureComponentStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct LoadedFeatureFlagItemV1 {
  std::int32_t native_index = -1;
  std::uint32_t cstring_id = 0;
  std::string key;
  bool enabled = false;

  friend bool operator==(const LoadedFeatureFlagItemV1 &,
                         const LoadedFeatureFlagItemV1 &) = default;
};

struct EffectiveFeatureFlagsV1 {
  LoadedFeatureComponentStatusV1 status =
      LoadedFeatureComponentStatusV1::unavailable;
  std::optional<std::int32_t> native_count;
  std::vector<LoadedFeatureFlagItemV1> items;
  std::string unavailable_reason;

  friend bool operator==(const EffectiveFeatureFlagsV1 &,
                         const EffectiveFeatureFlagsV1 &) = default;
};

struct ScriptDlcKeysV1 {
  LoadedFeatureComponentStatusV1 status =
      LoadedFeatureComponentStatusV1::unavailable;
  std::optional<std::int32_t> enumerated_count;
  std::vector<std::string> keys;
  std::string unavailable_reason;

  friend bool operator==(const ScriptDlcKeysV1 &,
                         const ScriptDlcKeysV1 &) = default;
};

struct LoadedFeatureManifestReadinessV1 {
  bool effective_feature_flags_ready = false;
  bool script_dlc_keys_ready = false;
  bool entitlements_ready = false;
  bool same_frame_ready = false;
  bool actionable_ready = false;

  friend bool operator==(const LoadedFeatureManifestReadinessV1 &,
                         const LoadedFeatureManifestReadinessV1 &) = default;
};

struct LoadedFeatureManifestV1 {
  LoadedFeatureManifestStatusV1 status =
      LoadedFeatureManifestStatusV1::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::string unavailable_reason;
  EffectiveFeatureFlagsV1 effective_feature_flags;
  ScriptDlcKeysV1 script_dlc_keys;
  LoadedFeatureManifestReadinessV1 readiness;

  friend bool operator==(const LoadedFeatureManifestV1 &,
                         const LoadedFeatureManifestV1 &) = default;
};

struct LoadedFeatureManifestFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;

  friend bool operator==(const LoadedFeatureManifestFrameV1 &,
                         const LoadedFeatureManifestFrameV1 &) = default;
};

enum class ReadLoadedFeatureManifestResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kLoadedFeatureManifestV1Capability =
    "game.command.query-loaded-feature-manifest-v1";
inline constexpr std::string_view kLoadedFeatureManifestV1Step =
    "query-loaded-feature-manifest-v1";
inline constexpr std::string_view kLoadedFeatureManifestV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view kLoadedFeatureManifestV1ExecutableSha256 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kLoadedFeatureManifestV1BackendId =
    "ck3-1.19.0.6-native-loaded-feature-manifest-v1";

inline constexpr std::uintptr_t kLoadedFeatureRootSlotRva = 0x576CC68;
inline constexpr std::uintptr_t kLoadedFeatureScriptDlcSetRva = 0x5762590;
inline constexpr std::uintptr_t kLoadedFeatureEnumTableRva = 0x42F7850;
inline constexpr std::uintptr_t kLoadedFeatureEnumTableEndRva = 0x42F7900;
inline constexpr std::uintptr_t kLoadedFeatureScriptIdentifierNameRva =
    0x3B58970;
inline constexpr std::size_t kLoadedFeatureNativeCount = 44;

#if defined(_MSC_VER)
#define XAR_LOADED_FEATURE_FASTCALL __fastcall
#else
#define XAR_LOADED_FEATURE_FASTCALL
#endif

using NativeLoadedFeatureScriptIdentifierNameV1 =
    const std::string *(XAR_LOADED_FEATURE_FASTCALL *)(
        std::int32_t identifier);

#undef XAR_LOADED_FEATURE_FASTCALL

struct LoadedFeatureManifestNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  void **feature_root_slot = nullptr;
  void *script_dlc_set = nullptr;
  const std::uint32_t *feature_enum_table = nullptr;
  NativeLoadedFeatureScriptIdentifierNameV1 script_identifier_name = nullptr;
};

using CaptureLoadedFeatureManifestFrameV1 = bool (*)(
    void *context, game::LoadedFeatureManifestFrameV1 &output) noexcept;
using IsLoadedFeatureManifestMainThreadV1 =
    bool (*)(void *context) noexcept;
using ReadLoadedFeatureManifestMemoryV1 = bool (*)(
    void *context, const void *address, void *output,
    std::size_t size) noexcept;
using ReadLoadedFeatureManifestStringV1 = bool (*)(
    void *context, const void *native_string,
    std::string &output) noexcept;

struct LoadedFeatureManifestAccessV1 {
  void *context = nullptr;
  CaptureLoadedFeatureManifestFrameV1 capture_frame = nullptr;
  IsLoadedFeatureManifestMainThreadV1 is_main_thread = nullptr;
  ReadLoadedFeatureManifestMemoryV1 read_memory = nullptr;
  ReadLoadedFeatureManifestStringV1 read_string = nullptr;
};

struct LoadedFeatureManifestRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
};

LoadedFeatureManifestNativeEnvironmentV1
BindLoadedFeatureManifestNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadLoadedFeatureManifestResultV1 ReadLoadedFeatureManifestV1(
    const LoadedFeatureManifestNativeEnvironmentV1 &environment,
    const LoadedFeatureManifestAccessV1 &access,
    const LoadedFeatureManifestRequestV1 &request,
    game::LoadedFeatureManifestV1 &output) noexcept;

std::string SerializeLoadedFeatureManifestV1(
    const game::LoadedFeatureManifestV1 &manifest);

} // namespace xar::ck3_11906
