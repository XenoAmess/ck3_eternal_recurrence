#include "xar_bridge/ck3_12004_ingame_ui.hpp"

namespace xar::ck3_12004 {

IngameUiBindings12004V1 BindIngameUiImage12004V1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  if (!image_base || executable_sha256 != kExecutableSha256) return {};
  return {true, image_base};
}

} // namespace xar::ck3_12004
