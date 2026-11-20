#pragma once
#include "xar_bridge/ck3_121003_full_profile111.hpp"
#include "xar_bridge/ck3_1210_full_snapshot_v1.hpp"
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"

namespace xar::ck3_121003::full111 {
// Separate from the published Core-only route. No SHA is added to the legacy
// ImageBuildForSha lookup and no BB3 address is selected for this binding.
ck3_1210::CoreBindings BindCore(std::uintptr_t,std::string_view) noexcept;
ck3_1210::FullSnapshotBindingsV1 BindFull(std::uintptr_t,std::string_view) noexcept;
bool ReadFull(const ck3_1210::FullSnapshotBindingsV1 &,xar::game::Snapshot &,
    ck3_1210::FullSnapshotDiagnosticsV1 &) noexcept;
}
