#pragma once

#include "xar_bridge/ck3_1210_core_control_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_1210 {

inline constexpr char kFullClockRequestClaimSchemaV1[] =
    "ck3_1210_full_clock_control_v1";

struct FullClockRequestV1 {
  CoreControlOperationV1 operation = CoreControlOperationV1::unavailable;
  // On success this always refers to a static canonical literal, never the
  // input payload. All other accepted identity strings are validation only.
  std::string_view step;
  std::int32_t public_speed = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t deadline_unix_ms = 0;
};

// Closed, unescaped-ASCII grammar, bounded to 16384 bytes. Required outer
// members: type/protocol_version/request_id/step/expected_revision and exactly
// full_snapshot_clock_control. arguments is optional and must be empty {}.
// Claim requires exactly schema/game_version/executable_sha256/adapter_id/
// backend/snapshot_id/native_revision/deadline_unix_ms. Its native:<revision>
// ID and native revision must equal outer expected_revision; all are positive
// canonical uint64 integers. Deadline is syntax only, not a clock observation.
// Clears the DTO on every failure. No Full/Core/queue calls, time reads,
// authority, freshness, permission or published-Snapshot qualification.
bool ParseFullClockRequestV1(std::string_view payload,
    FullClockRequestV1 &output,ImageBuildV1 build=ImageBuildV1::original26622941) noexcept;

} // namespace xar::ck3_1210
