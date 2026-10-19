#pragma once
#include "xar_bridge/camera_follow_readonly_12004.hpp"
#include <windows.h>
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace xar::presentation::tracked {
inline constexpr std::size_t kOffset = 0x18400, kRegionBytes = 8192;
inline constexpr std::uint32_t kMagic = 0x54434158, kVersion = 1;
inline constexpr std::size_t kProvinceCapacity = 32;
struct Province { std::int32_t id = 0; char title_key[128]{}; };
struct RequestV1 {
  std::uint32_t request_sequence = 0, province_count = 0;
  std::uint64_t owner_epoch = 0, scope_generation = 0;
  std::int32_t actor = -1, fullarmy_id = -1;
  std::int32_t start_date_raw = 0, max_date_raw = 0;
  std::array<Province, kProvinceCapacity> provinces{};
};
enum class State : std::uint32_t {
  idle = 0, tracking = 1, released = 2, invalid_request = 3,
  connection_changed = 4, scope_ended = 5, ui_or_identity_unknown = 6,
  province_unlisted = 7, geometry_unverified = 8, camera_unavailable = 9,
  superseded = 10, yielding_to_gameplay = 11, world_changed = 12
};
struct ResultV1 {
  std::uint32_t request_sequence = 0, state = 0;
  std::uint64_t owner_epoch = 0, scope_generation = 0, observed_uptime_ms = 0;
  std::int32_t actor = -1, fullarmy_id = -1, date_raw = 0;
  std::int32_t province_id = 0, combat_id = -1;
  std::uint32_t target_updates = 0;
  std::int32_t pending_slot_capacity = 0, pending_slots_visited = 0;
  std::uint64_t reader_elapsed_us = UINT64_MAX;
  std::uint32_t reader_reason = 1, reserved = 0;
};
struct SharedV1 {
  std::uint32_t magic = kMagic, version = kVersion;
  std::uint32_t byte_size = sizeof(SharedV1), provider_pid = 0;
  volatile LONG capability_sequence = 0;
  std::uint32_t active = 0;
  std::uint64_t owner_epoch = 0;
  volatile LONG result_sequence = 0;
  std::uint32_t reserved = 0;
  RequestV1 request{};
  ResultV1 result{};
};
static_assert(sizeof(Province) == 132);
static_assert(sizeof(RequestV1) == 4264);
static_assert(sizeof(ResultV1) == 80);
static_assert(offsetof(SharedV1, request) == 40);
static_assert(offsetof(SharedV1, result) == 4304);
static_assert(sizeof(SharedV1) == 4384);
static_assert(sizeof(SharedV1) <= kRegionBytes);
static_assert(kOffset + kRegionBytes <= 131072);
// Native worker alone sets this fence; SDK connection counters are not proof.
struct ConnectionV1 { bool active = false; std::uint64_t epoch = 0; };
inline std::atomic<std::uint64_t> connection_fence_v1{0};
inline void SetConnectionActiveV1(bool active) noexcept {
  auto old = connection_fence_v1.load(std::memory_order_relaxed);
  for (;;) {
    const auto next = ((old >> 1) + 1) << 1 | (active ? 1ULL : 0ULL);
    if (connection_fence_v1.compare_exchange_weak(old, next,
        std::memory_order_release, std::memory_order_relaxed)) return;
  }
}
inline ConnectionV1 ReadConnectionV1() noexcept {
  const auto value = connection_fence_v1.load(std::memory_order_acquire);
  return {(value & 1) != 0, value >> 1};
}
inline bool ValidRequestV1(const RequestV1 &r, std::uint32_t sequence) noexcept {
  if (!sequence || (sequence & 1U) || r.request_sequence != sequence ||
      !r.owner_epoch || !r.scope_generation || r.actor <= 0 || r.fullarmy_id <= 0 ||
      r.start_date_raw <= 0 || r.max_date_raw <= r.start_date_raw ||
      static_cast<std::int64_t>(r.max_date_raw) - r.start_date_raw > 30 * 24 ||
      !r.province_count || r.province_count > kProvinceCapacity) return false;
  for (std::size_t i = 0; i < r.province_count; ++i) {
    if (r.provinces[i].id <= 0 || r.provinces[i].title_key[0] != 'b' ||
        r.provinces[i].title_key[1] != '_' || r.provinces[i].title_key[127]) return false;
    for (std::size_t j = 0; j < i; ++j)
      if (r.provinces[i].id == r.provinces[j].id) return false;
  }
  return true;
}
inline State ValidateFrameV1(const RequestV1 &r, const Frame &f) noexcept {
  if (!f.complete || !f.alive || !f.map_ready || !f.ui_clear || !f.full_id_valid ||
      f.retreating || f.actor != r.actor || f.subject_owner != r.actor)
    return State::ui_or_identity_unknown;
  if (!f.scope_armed || f.scope_generation != r.scope_generation ||
      f.scope_start_date_raw != r.start_date_raw || f.scope_target_date_raw != r.max_date_raw ||
      f.date_raw < r.start_date_raw || f.date_raw >= r.max_date_raw ||
      (f.paused && f.date_raw > r.start_date_raw)) return State::scope_ended;
  return State::tracking;
}
inline std::int32_t ObservedProvinceV1(const Frame &f) noexcept {
  // Full ComponentIDs may be zero or signed-negative; only -1 is absent.
  return f.combat_id != -1 ? f.battle_province_id : f.current_province_id;
}
} // namespace xar::presentation::tracked
