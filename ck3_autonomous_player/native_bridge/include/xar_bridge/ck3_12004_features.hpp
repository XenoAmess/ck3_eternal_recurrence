#pragma once

#include "xar_bridge/ck3_12002_campaign.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12002::detail {

struct LoadedFeatureManifestRvaProfileV1 {
  std::uintptr_t feature_root_slot_rva;
  std::uintptr_t script_dlc_set_rva;
  std::uintptr_t feature_enum_table_rva;
  std::uintptr_t script_identifier_name_rva;
};

struct LoadedFeatureManifestRenderProfileV1 {
  std::string_view game_version;
  std::string_view executable_sha256;
  std::string_view backend_id;
  std::string_view feature_root_slot_rva;
  std::string_view feature_enum_table_rva;
  std::string_view script_dlc_set_rva;
};

game::ReadLoadedFeatureManifestResultV1
ReadLoadedFeatureManifestV1ForProfile(
    const LoadedFeatureManifestNativeEnvironmentV1 &environment,
    const LoadedFeatureManifestAccessV1 &access,
    const LoadedFeatureManifestRequestV1 &request,
    const LoadedFeatureManifestRvaProfileV1 &profile,
    game::LoadedFeatureManifestV1 &output) noexcept;

std::string SerializeLoadedFeatureManifestV1ForProfile(
    const game::LoadedFeatureManifestV1 &manifest,
    const LoadedFeatureManifestRenderProfileV1 &profile);

} // namespace xar::ck3_12002::detail

namespace xar::ck3_12004 {

inline constexpr std::string_view kLoadedFeatureManifestV1Capability =
    "game.command.query-loaded-feature-manifest-v1";
inline constexpr std::string_view kLoadedFeatureManifestV1Step =
    "query-loaded-feature-manifest-v1";
inline constexpr std::string_view kLoadedFeatureManifestV1GameVersion =
    "1.20.0.4";
inline constexpr std::string_view kLoadedFeatureManifestV1ExecutableSha256 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::string_view kLoadedFeatureManifestV1BackendId =
    "ck3-1.20.0.4-native-loaded-feature-manifest-v1";

// Closed Government feature packets and Faith ParameterTokenKey map.
inline constexpr std::uintptr_t kLoadedFeatureRootSlotRva = 0x5CB87F8;
inline constexpr std::uintptr_t kLoadedFeatureScriptDlcSetRva = 0x5CC15E0;
inline constexpr std::uintptr_t kLoadedFeatureEnumTableRva = 0x47334D0;
inline constexpr std::uintptr_t kLoadedFeatureEnumTableEndRva = 0x4733580;
inline constexpr std::uintptr_t kLoadedFeatureScriptIdentifierNameRva =
    0x3F4F8E0;
inline constexpr std::size_t kLoadedFeatureNativeCount = 44;
static_assert(kLoadedFeatureEnumTableEndRva - kLoadedFeatureEnumTableRva ==
              kLoadedFeatureNativeCount * sizeof(std::uint32_t));

using NativeLoadedFeatureScriptIdentifierNameV1 =
    ck3_12002::NativeLoadedFeatureScriptIdentifierNameV1;
using LoadedFeatureManifestNativeEnvironmentV1 =
    ck3_12002::LoadedFeatureManifestNativeEnvironmentV1;
using CaptureLoadedFeatureManifestFrameV1 =
    ck3_12002::CaptureLoadedFeatureManifestFrameV1;
using IsLoadedFeatureManifestMainThreadV1 =
    ck3_12002::IsLoadedFeatureManifestMainThreadV1;
using ReadLoadedFeatureManifestMemoryV1 =
    ck3_12002::ReadLoadedFeatureManifestMemoryV1;
using ReadLoadedFeatureManifestStringV1 =
    ck3_12002::ReadLoadedFeatureManifestStringV1;
using LoadedFeatureManifestAccessV1 = ck3_12002::LoadedFeatureManifestAccessV1;
using LoadedFeatureManifestRequestV1 =
    ck3_12002::LoadedFeatureManifestRequestV1;

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

} // namespace xar::ck3_12004
