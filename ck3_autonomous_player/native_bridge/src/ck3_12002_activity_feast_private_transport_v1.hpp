#pragma once

#include "activity_feast_stage5_start_private_transport_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_start.hpp"

namespace xar::ck3_12002 {

using FeastReadSnapshotV1 = bool (*)(void *, game::Snapshot &) noexcept;
using FeastResolveScriptIdentifierV1 = bool (*)(
    void *, std::int32_t, std::string_view &) noexcept;

// The old DTO carries no executable-dependent addresses. The new context
// replaces its legacy Bindings with a full snapshot callback from this exact
// build's adapter. Legacy bindings are never dereferenced by the new executor.
struct ActivityFeastStage5Private12002QueryV1
    : ck3_11906::ActivityFeastStage5PrivateQueryV1 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  void *native_context = nullptr;
  FeastReadSnapshotV1 read_snapshot = nullptr;
  FeastResolveScriptIdentifierV1 resolve_script_identifier = nullptr;
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
  bridge::ActivityGuestRuleProvenanceObserverV1 *provenance_observer = nullptr;
#endif
};

bool ExecuteActivityFeastStage5Private12002V1(
    void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityFeastStage5Private12002V1(
    const ActivityFeastStage5Private12002QueryV1 &query);

} // namespace xar::ck3_12002
