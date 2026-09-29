#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kActivityHostedIdentityExeSha256V1 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

struct ActivityHostedIdentityFrameV1 {
  std::uint64_t revision = 0;
  std::int64_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  bool application_main_thread = false;
  bool paused = false;
  bool map_ready = false;
  bool actor_alive = false;

  friend bool operator==(const ActivityHostedIdentityFrameV1 &,
                         const ActivityHostedIdentityFrameV1 &) = default;
};

using ActivityHostedIdentityReadMemoryV1 =
    bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;
using ActivityHostedIdentityReadFrameV1 =
    bool (*)(void *, ActivityHostedIdentityFrameV1 &) noexcept;

struct ActivityHostedIdentityEnvironmentV1 {
  bool enabled = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  void *context = nullptr;
  ActivityHostedIdentityReadMemoryV1 read_memory = nullptr;
  ActivityHostedIdentityReadFrameV1 read_frame = nullptr;
};

struct ActivityHostedIdentityV1 {
  std::uint32_t activity_id = 0;
  std::int32_t host_character_id = -1;
  std::array<char, 64> type_key{};
  std::uint8_t type_key_size = 0;
};

enum class ActivityHostedIdentityStatusV1 {
  observed,
  exact_build_rejected,
  frame_rejected,
  manager_unavailable,
  actor_identity_unavailable,
  activity_identity_unavailable,
  output_capacity_exceeded,
  snapshot_changed,
};

struct ActivityHostedIdentityResultV1 {
  ActivityHostedIdentityStatusV1 status =
      ActivityHostedIdentityStatusV1::exact_build_rejected;
  ActivityHostedIdentityFrameV1 frame{};
  std::uint32_t manager_active_count = 0;
  std::uint32_t hosted_count = 0;
  std::array<ActivityHostedIdentityV1, 64> hosted{};
};

// Copies identities only. No activity pointer survives this paused-frame call.
ActivityHostedIdentityResultV1 ReadActivityHostedIdentityV1(
    const ActivityHostedIdentityEnvironmentV1 &environment,
    const ActivityHostedIdentityFrameV1 &expected) noexcept;

} // namespace xar::bridge
