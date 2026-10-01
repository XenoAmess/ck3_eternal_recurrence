#pragma once

#include "activity_stage5_canstart_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_private_transport_v1.hpp"

namespace xar::ck3_12002 {
struct ActivityStage5CanStartPrivate12002QueryV1
    : ck3_11906::ActivityStage5CanStartPrivateQueryV1 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  void *native_context = nullptr;
  FeastReadSnapshotV1 read_snapshot = nullptr;
};
bool ExecuteActivityStage5CanStartPrivate12002V1(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializeActivityStage5CanStartPrivate12002V1(
    const ActivityStage5CanStartPrivate12002QueryV1 &);
} // namespace xar::ck3_12002
