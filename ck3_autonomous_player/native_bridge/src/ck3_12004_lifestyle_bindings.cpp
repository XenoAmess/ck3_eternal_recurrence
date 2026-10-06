#include "xar_bridge/ck3_12004_lifestyle.hpp"
namespace xar::ck3_12004::lifestyle {
PlayerLifestyleBindings12004 BindPlayerLifestyleImage12004(
    std::uintptr_t module_base, std::string_view actual_executable_sha256) noexcept {
  PlayerLifestyleBindings12004 output{};
  if (module_base == 0 || actual_executable_sha256 != ck3_12004::kExecutableSha256)
    return output;
  output.module_base = module_base;
  output.admitted_executable_sha256 = actual_executable_sha256;
  output.core = ck3_12004::BindCoreImage(module_base, actual_executable_sha256);
  output.snapshot = BindPlayerLifestyleSnapshotEnvironment12004V1(
      module_base, true, actual_executable_sha256);
  output.focus = BindStockFocusLegalityEnvironment12004V1(
      module_base, true, actual_executable_sha256);
  output.perk = BindStockPerkLegalityEnvironment12004V1(
      module_base, true, actual_executable_sha256);
  output.selection = BindPlayerLifestyleSelectionNativeAdapterEnvironment12004V1(
      module_base, true, actual_executable_sha256);
  output.enabled = output.core.enabled &&
      PlayerLifestyleSelectionNativeAdapterEnvironmentReady12004V1(output.selection);
  return output;
}
} // namespace xar::ck3_12004::lifestyle
