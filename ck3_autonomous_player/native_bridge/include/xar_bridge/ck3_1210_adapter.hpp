#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_1210.hpp"

namespace xar::game {
const AdapterDescriptor &Ck3_1210AdapterDescriptor() noexcept;
inline bool IsCk3_1210Descriptor(const AdapterDescriptor &descriptor) noexcept {
  return descriptor.adapter_id == ck3_1210::kAdapterId &&
      descriptor.game_version == ck3_1210::kGameVersion &&
      descriptor.executable_sha256 == ck3_1210::kExecutableSha256;
}
std::unique_ptr<GameAdapter> CreateCk3_1210AdapterFromBindings(
    ck3_1210::CoreBindings bindings) noexcept;
bool ReadCk3_1210TimelineCoreSnapshot(const GameAdapter &adapter,
    Snapshot &output) noexcept;
// Identity-only by default. The explicit core-only build option admits no
// complete snapshot, gameplay command, frontend or domain capability.
std::unique_ptr<GameAdapter> CreateCk3_1210Adapter(
    std::string_view executable_sha256) noexcept;
} // namespace xar::game
