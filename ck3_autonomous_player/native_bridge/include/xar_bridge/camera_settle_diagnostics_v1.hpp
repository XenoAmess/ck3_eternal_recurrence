#pragma once
// Optional v1 mapping-tail diagnostics. Does not alter Request/Result/Shared ABI.
// These observations explain legacy status7; they do not change its guard.
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace xar::presentation {
inline constexpr std::size_t kCameraSettleDiagnosticsOffsetV1 = 0x18000;
inline constexpr std::uint32_t kCameraSettleDiagnosticsMagicV1 = 0x44434158;
inline constexpr std::uint32_t kCameraSettleDiagnosticsBytesV1 = 168;
enum class CameraSettleReasonV1 : std::uint32_t {
  none = 0, current_read_failed = 1, target_read_failed = 2,
  current_nonfinite = 3, target_changed = 4
};
inline constexpr std::uint32_t kSettleCurrentReadV1 = 1;
inline constexpr std::uint32_t kSettleTargetReadV1 = 2;
inline constexpr std::uint32_t kSettleCurrentFiniteV1 = 4;
inline constexpr std::uint32_t kSettleTargetFiniteV1 = 8;

struct CameraSettleDiagnosticsV1 {
  std::uint32_t magic = 0; // zero clears an absent diagnostic
  std::uint32_t version = 1;
  std::uint32_t byte_size = kCameraSettleDiagnosticsBytesV1;
  std::uint32_t request_sequence = 0;
  std::uint32_t legacy_status = 0;
  std::uint32_t reason = 0;
  std::uint32_t provider_pid = 0;
  std::int32_t actor = -1;
  std::int32_t submit_date_raw = 0; // Snapshot used on initial submission
  std::int32_t request_date_raw = 0; // Original request source date
  std::uint32_t request_mode = 0;
  std::uint32_t observation_flags = 0;
  std::uint32_t target_difference_mask = 0;
  std::uint32_t county_count = 0;
  std::uint32_t client_width = 0;
  std::uint32_t client_height = 0;
  std::int32_t zoom_index = -1;
  std::array<std::int32_t, 4> bounds{};
  std::array<float, 6> expected_target{};
  // Raw storage is zero if unread. Consumers MUST use observation_flags.
  std::array<float, 6> observed_current{};
  std::array<float, 6> observed_target{};
  std::uint32_t reserved = 0;
  std::uint64_t observation_uptime_ms = 0; // OS time; NOT a Game frame/date
};
static_assert(std::is_standard_layout_v<CameraSettleDiagnosticsV1>);
static_assert(std::is_trivially_copyable_v<CameraSettleDiagnosticsV1>);
static_assert(sizeof(CameraSettleDiagnosticsV1) == kCameraSettleDiagnosticsBytesV1);
static_assert(offsetof(CameraSettleDiagnosticsV1, expected_target) == 84);
static_assert(offsetof(CameraSettleDiagnosticsV1, observed_current) == 108);
static_assert(offsetof(CameraSettleDiagnosticsV1, observed_target) == 132);
static_assert(offsetof(CameraSettleDiagnosticsV1, observation_uptime_ms) == 160);

inline bool CameraSettleFiniteV1(const std::array<float, 6> &values) noexcept {
  for (float value : values) if (!std::isfinite(value)) return false;
  return true;
}
inline CameraSettleDiagnosticsV1 ObserveCameraSettleV1(
    const std::array<float, 6> &expected, bool current_read,
    const std::array<float, 6> &current, bool target_read,
    const std::array<float, 6> &target) noexcept {
  CameraSettleDiagnosticsV1 out{};
  out.magic = kCameraSettleDiagnosticsMagicV1;
  out.expected_target = expected;
  if (current_read) {
    out.observation_flags |= kSettleCurrentReadV1;
    out.observed_current = current;
    if (CameraSettleFiniteV1(current))
      out.observation_flags |= kSettleCurrentFiniteV1;
  }
  if (target_read) {
    out.observation_flags |= kSettleTargetReadV1;
    out.observed_target = target;
    if (CameraSettleFiniteV1(target))
      out.observation_flags |= kSettleTargetFiniteV1;
  }
  // Same precedence as the legacy short-circuit guard. The caller must not
  // perform a target read when its original current read failed.
  auto reason = CameraSettleReasonV1::none;
  if (!current_read) reason = CameraSettleReasonV1::current_read_failed;
  else if (!target_read) reason = CameraSettleReasonV1::target_read_failed;
  else if (!CameraSettleFiniteV1(current))
    reason = CameraSettleReasonV1::current_nonfinite;
  else {
    for (std::size_t i = 0; i < expected.size(); ++i)
      if (target[i] != expected[i]) out.target_difference_mask |= 1U << i;
    if (out.target_difference_mask)
      reason = CameraSettleReasonV1::target_changed;
  }
  out.reason = static_cast<std::uint32_t>(reason);
  return out;
}
} // namespace xar::presentation

