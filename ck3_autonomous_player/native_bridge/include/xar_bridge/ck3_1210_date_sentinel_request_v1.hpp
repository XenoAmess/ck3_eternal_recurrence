#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_1210 {

inline constexpr char kDateSentinelArmRequestClaimSchemaV1[] =
    "ck3_1210_date_sentinel_arm_v1";

// Owned DATA only. Copying or moving the DTO never leaves a view into the
// source DTO or request payload. No legacy execution specification is held.
struct DateSentinelArmRequestV1 {
  std::array<char, 192> step_bytes{};
  std::size_t step_size = 0;
  std::int32_t starting_date_raw = 0;
  std::int32_t target_date_raw = 0;
  std::int32_t speed = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t deadline_unix_ms = 0;

  std::string_view Step() const noexcept {
    return step_size <= step_bytes.size() ?
        std::string_view{step_bytes.data(), step_size} : std::string_view{};
  }
};

// Closed execute_step envelope and exactly one date_sentinel_arm claim.
// Same exact eight identity/revision/deadline claim fields as Full-clock,
// with this schema; arguments may be omitted or {}. Canonical step only:
// research-arm-tactical-daily-sentinel-v1-<positive int32 start>-to-
// <positive int32 target>-speed-<1..5>-mode-terminal-a-0
// Target must exceed start by a multiple of24 raw ticks. No mode omission,
// decision mode, positive army selector, signed/zero/leading-zero dates or
// numeric aliases. Failure clears all owned bytes and scalar fields.
// Pure parser: no legacy parser, Native API, clock, queue or authority call.
bool ParseDateSentinelArmRequestV1(std::string_view payload,
    DateSentinelArmRequestV1 &output) noexcept;

} // namespace xar::ck3_1210
