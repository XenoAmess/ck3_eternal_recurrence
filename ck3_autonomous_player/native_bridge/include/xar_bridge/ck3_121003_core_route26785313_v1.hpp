#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/ck3_1210_core_frame_v1.hpp"
#include "xar_bridge/game_adapter.hpp"

namespace xar::game {
const AdapterDescriptor &Ck3_121003Core26785313AdapterDescriptor() noexcept;
inline bool IsCk3_121003Core26785313Descriptor(const AdapterDescriptor &d) noexcept {
  namespace current=ck3_121003::build26785313;
  return d.game_version==current::kGameVersion && d.adapter_id==current::kAdapterId &&
      d.executable_sha256==current::kExecutableSha256;
}
} // namespace xar::game
namespace xar::ck3_121003::build26785313 {
// A single fixed owner executor; no timeline/control/semantic/GUI callbacks.
ck3_11906::MainThreadQueryInstallEnvironmentV1 BindCoreRouteMailboxEnvironmentV1(
    std::uintptr_t image_base,std::string_view executable_sha256) noexcept;
// A synthetic or resource-bearing observation cannot become a production Core.
ck3_1210::CoreFrameObservationV1 CoreRouteObservationV1(const ReadonlyObservation &) noexcept;
} // namespace xar::ck3_121003::build26785313
