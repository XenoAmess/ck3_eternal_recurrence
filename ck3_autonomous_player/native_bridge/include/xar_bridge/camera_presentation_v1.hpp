#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/camera_settle_diagnostics_v1.hpp"
#include "xar_bridge/camera_tracking_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include <windows.h>
#include <array>
#include <chrono>
#include <cstdint>
namespace xar::presentation {
inline constexpr std::uint32_t kMagic = 0x43524158;
inline constexpr std::size_t kMappingBytes = 131072;
inline constexpr std::size_t kCountyCapacity = 16384;
enum class Mode : std::uint32_t { cancel = 0, realm = 1, hotspot = 2, query = 3, tracked_hotspot = 4 };
enum class Status : std::uint32_t {
  idle = 0, submitted = 1, settled = 2, cancelled = 3,
  stale_actor = 4, preempted = 5, unavailable = 6, target_changed = 7,
  bounds_available = 8,
  // Values 9-15 remain reserved. These additive failures preserve the v1 layout.
  window_unavailable = 16,
  camera_resolve_unavailable = 17,
  camera_target_write_blocked_or_unreadable = 18,
  camera_transient_x_active_or_unreadable = 19,
  camera_transient_z_active_or_unreadable = 20,
  camera_viewport_extent_unavailable = 21,
  camera_bucket_table_unavailable = 22,
  camera_bucket_read_or_match_unavailable = 23,
  camera_zoom_index_unavailable = 24,
  camera_zoom_or_target_state_unavailable = 25,
  camera_angle_state_unavailable = 26,
  camera_canonical_target_unavailable = 27,
  camera_target_write_or_readback_unavailable = 28
};
struct Request {
  std::uint32_t mode = 0;
  std::int32_t actor = -1;
  std::int32_t date_raw = 0;
  std::uint32_t reserved = 0;
  std::uint64_t expires_uptime_ms = 0;
  std::uint64_t hwnd = 0;
  float padding = .15F;
  char title_key[128]{};
};
struct Result {
  std::uint32_t request_sequence = 0;
  std::uint32_t status = 0;
  std::int32_t actor = -1;
  std::int32_t date_raw = 0;
  std::uint32_t county_count = 0;
  std::uint32_t client_width = 0;
  std::uint32_t client_height = 0;
  std::int32_t zoom_index = -1;
  std::array<std::int32_t, 4> bounds{};
  std::array<float, 6> target{};
  std::array<float, 6> current{};
  std::uint32_t native_elapsed_us = 0;
  std::uint32_t coverage_verified = 0;
  std::array<std::int32_t, kCountyCapacity> county_ids{};
};
struct Shared {
  std::uint32_t magic = kMagic;
  std::uint32_t version = 1;
  std::uint32_t pid = 0;
  std::uint32_t reserved = 0;
  volatile LONG request_sequence = 0;
  volatile LONG result_sequence = 0;
  Request request{};
  Result result{};
};
static_assert(sizeof(Shared) < kMappingBytes);
static_assert(offsetof(Shared, request) == 24);
// A changed legacy layout needs a new protocol, even if it still fits.
static_assert(sizeof(Request) == 168);
static_assert(sizeof(Result) == 65640);
static_assert(offsetof(Shared, result) == 192);
static_assert(sizeof(Shared) == 65832);
// The optional extension must never overlap the complete legacy v1 region.
static_assert(sizeof(Shared) <= kCameraSettleDiagnosticsOffsetV1);
static_assert(offsetof(Shared, result) + sizeof(Result) <= kCameraSettleDiagnosticsOffsetV1);
static_assert(kCameraSettleDiagnosticsOffsetV1 + sizeof(CameraSettleDiagnosticsV1) <= kMappingBytes);
class CameraPresentationRuntimeV1 {
public:
  ~CameraPresentationRuntimeV1();
  bool Initialize(std::uintptr_t base, std::string_view sha,
                  const game::GameAdapter *game,
                  const ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr) noexcept;
  static bool Pump(void *context,
      const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
private:
  bool Advance(const ck3_11906::MainThreadExecutionStampV1 &);
  bool AdvanceTracking(std::uint32_t sequence, std::uint64_t now);
  static bool ContinueTrackingRead(void *context) noexcept;
  bool ApplyBounds(const std::array<std::int32_t, 4> &, std::uint32_t,
                   std::uint64_t, std::chrono::steady_clock::time_point);
  void ReleaseTracking(tracked::State) noexcept;
  void PublishTracking(tracked::State) noexcept;
  void Publish(Status status,
      const CameraSettleDiagnosticsV1 *diagnostic = nullptr) noexcept;
  HANDLE mapping_ = nullptr;
  Shared *shared_ = nullptr;
  const game::GameAdapter *game_ = nullptr;
  const ck3_11906::MainThreadQueryMailboxV1 *mailbox_ = nullptr;
  std::uintptr_t base_ = 0;
  std::uint32_t seen_ = 0;
  std::uint64_t next_check_ms_ = 0;
  std::uint64_t settle_until_ms_ = 0;
  void *camera_ = nullptr;
  Request request_{};
  Result result_{};
  tracked::RequestV1 tracking_request_{};
  tracked::ResultV1 tracking_result_{};
  bool tracking_ = false;
  // Opaque identities only. Never cast back or dereference across pumps.
  std::uintptr_t tracking_game_state_ = 0, tracking_jomini_state_ = 0;
  std::uint64_t next_position_ms_ = 0;
};
} // namespace xar::presentation
