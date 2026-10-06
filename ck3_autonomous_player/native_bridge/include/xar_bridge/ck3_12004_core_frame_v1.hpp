#pragma once

#include "xar_bridge/ck3_12002_adapter.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr char kCoreFrameStepV1[] = "query-core-frame-v1";
inline constexpr char kCoreFrameCapabilityV1[] = "game.query.core-frame.v1";
inline constexpr char kCoreFrameSchemaV1[] = "ck3_12004_core_frame_v1";

// Only the reviewed clock/player prefix is observable. This is never a
// complete game::Snapshot and has no gameplay snapshot revision.
struct CoreFrameObservationV1 {
  bool core_available = false;
  bool application_main_observed = false;
  std::string_view unavailable_reason = "core_not_read";
  CoreSnapshotPrefix core{};
};

using CoreFrameReadFunctionV1 = bool (*)(
    const game::GameAdapter &, game::Snapshot &) noexcept;

struct CoreFrameMailboxContextV1 {
  const xar::game::GameAdapter *game = nullptr;
  CoreFrameReadFunctionV1 read_core = &xar::game::ReadCk3_12002TimelineCoreSnapshot;
  CoreFrameObservationV1 observation{};
};

bool ExecuteCoreFrameMailboxV1(void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
ck3_11906::MainThreadQueryInstallEnvironmentV1 BindCoreFrameMailboxEnvironmentV1(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
std::string SerializeCoreFrameV1(const CoreFrameObservationV1 &observation);
std::string SerializeCoreFrameCommandResultV1(std::string_view request_id,
    const CoreFrameObservationV1 &observation);

} // namespace xar::ck3_12004
