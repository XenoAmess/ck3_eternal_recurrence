#include "xar_bridge/ck3_12004_features.hpp"

namespace xar::ck3_12004 {
namespace {

constexpr ck3_12002::detail::LoadedFeatureManifestRvaProfileV1 kRvaProfile{
    kLoadedFeatureRootSlotRva,
    kLoadedFeatureScriptDlcSetRva,
    kLoadedFeatureEnumTableRva,
    kLoadedFeatureScriptIdentifierNameRva,
};

constexpr ck3_12002::detail::LoadedFeatureManifestRenderProfileV1
    kRenderProfile{
        kLoadedFeatureManifestV1GameVersion,
        kLoadedFeatureManifestV1ExecutableSha256,
        kLoadedFeatureManifestV1BackendId,
        "0x5CB87F8",
        "0x47334D0..0x4733580",
        "0x5CC15E0",
    };

} // namespace

LoadedFeatureManifestNativeEnvironmentV1
BindLoadedFeatureManifestNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  LoadedFeatureManifestNativeEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  if (module_base == 0 || !exact_build_admitted) {
    return output;
  }
  output.feature_root_slot = reinterpret_cast<void **>(
      module_base + kLoadedFeatureRootSlotRva);
  output.script_dlc_set = reinterpret_cast<void *>(
      module_base + kLoadedFeatureScriptDlcSetRva);
  output.feature_enum_table = reinterpret_cast<const std::uint32_t *>(
      module_base + kLoadedFeatureEnumTableRva);
  output.script_identifier_name = reinterpret_cast<
      NativeLoadedFeatureScriptIdentifierNameV1>(
      module_base + kLoadedFeatureScriptIdentifierNameRva);
  return output;
}

game::ReadLoadedFeatureManifestResultV1 ReadLoadedFeatureManifestV1(
    const LoadedFeatureManifestNativeEnvironmentV1 &environment,
    const LoadedFeatureManifestAccessV1 &access,
    const LoadedFeatureManifestRequestV1 &request,
    game::LoadedFeatureManifestV1 &output) noexcept {
  return ck3_12002::detail::ReadLoadedFeatureManifestV1ForProfile(
      environment, access, request, kRvaProfile, output);
}

std::string SerializeLoadedFeatureManifestV1(
    const game::LoadedFeatureManifestV1 &manifest) {
  return ck3_12002::detail::SerializeLoadedFeatureManifestV1ForProfile(
      manifest, kRenderProfile);
}

} // namespace xar::ck3_12004
