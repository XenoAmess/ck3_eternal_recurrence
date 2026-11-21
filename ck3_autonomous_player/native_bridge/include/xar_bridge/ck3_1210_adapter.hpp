#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_1210.hpp"
#include "xar_bridge/ck3_1210_full_snapshot_v1.hpp"
#include "xar_bridge/ck3_121003_full_profile111.hpp"

namespace xar::ck3_11906 { struct MainThreadQueryMailboxV1; }
namespace xar::game {
const AdapterDescriptor &Ck3_1210AdapterDescriptor() noexcept;
inline bool IsCk3_1210Descriptor(const AdapterDescriptor &descriptor) noexcept {
  return descriptor.adapter_id == ck3_1210::kAdapterId &&
      descriptor.game_version == ck3_1210::kGameVersion &&
      descriptor.executable_sha256 == ck3_1210::kExecutableSha256;
}
const AdapterDescriptor &Ck3_1210Hotfix26757580AdapterDescriptor() noexcept;
const AdapterDescriptor &Ck3_121003Full111AdapterDescriptor() noexcept;
inline bool IsCk3_121003Full111Descriptor(const AdapterDescriptor &d) noexcept {
  return d.adapter_id==ck3_121003::full111::kAdapterId &&
      d.game_version==ck3_121003::full111::kGameVersion &&
      d.executable_sha256==ck3_121003::full111::kExecutableSha256;
}
inline bool IsCk3_1210Hotfix26757580Descriptor(const AdapterDescriptor &d) noexcept {
  return d.adapter_id==ck3_1210::hotfix26757580::kAdapterId && d.game_version==ck3_1210::kGameVersion &&
    d.executable_sha256==ck3_1210::hotfix26757580::kExecutableSha256;
}
// Only basic Core/Full/clock/exit consumers use this union. All other domain
// admission continues to use the historical exact descriptor predicate above.
inline bool IsCk3_1210BasicDescriptor(const AdapterDescriptor &d) noexcept {
  return IsCk3_1210Descriptor(d) || IsCk3_1210Hotfix26757580Descriptor(d) || IsCk3_121003Full111Descriptor(d);
}
inline ck3_1210::ImageBuildV1 Ck3_1210BasicBuild(const AdapterDescriptor &d) noexcept {
  if(IsCk3_121003Full111Descriptor(d))return ck3_1210::ImageBuildV1::full11126785313;
  return IsCk3_1210BasicDescriptor(d)?ck3_1210::ImageBuildForSha(d.executable_sha256):ck3_1210::ImageBuildV1::unknown;
}
std::unique_ptr<GameAdapter> CreateCk3_1210AdapterFromBindings(
    ck3_1210::CoreBindings bindings) noexcept;
ck3_1210::FullSnapshotDiagnosticsV1 ReadCk3_1210FullSnapshotDiagnostics(const GameAdapter&) noexcept;
// Existing bridge-owned mailbox; no wire field or new role is created.
bool BindCk3_1210SnapshotOwnerMailbox(const GameAdapter &,
    const ck3_11906::MainThreadQueryMailboxV1 &) noexcept;
bool ReadCk3_1210TimelineCoreSnapshot(const GameAdapter &adapter,
    Snapshot &output) noexcept;
// Identity-only by default. The explicit core-only build option admits no
// complete snapshot, gameplay command, frontend or domain capability.
std::unique_ptr<GameAdapter> CreateCk3_1210Adapter(
    std::string_view executable_sha256) noexcept;
} // namespace xar::game

#if defined(XAR_CK3_ENABLE_ADMISSION_DIAG125) && XAR_CK3_ENABLE_ADMISSION_DIAG125
namespace xar::game {
std::unique_ptr<GameAdapter> CreateCk3_1210AdapterForImage125(std::string_view,std::uintptr_t) noexcept;
}
#endif
