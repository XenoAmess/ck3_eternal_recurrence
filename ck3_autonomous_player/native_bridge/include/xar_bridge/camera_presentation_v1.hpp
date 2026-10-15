#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include <windows.h>
#include <array>
#include <cstdint>
namespace xar::presentation {
inline constexpr std::uint32_t kMagic = 0x43524158;
inline constexpr std::size_t kMappingBytes = 131072;
inline constexpr std::size_t kCountyCapacity = 16384;
enum class Mode : std::uint32_t { cancel = 0, realm = 1, hotspot = 2, query = 3 };
enum class Status : std::uint32_t {
  idle = 0, submitted = 1, settled = 2, cancelled = 3,
  stale_actor = 4, preempted = 5, unavailable = 6, target_changed = 7,
  bounds_available = 8
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
class CameraPresentationRuntimeV1 {
public:
  ~CameraPresentationRuntimeV1();
  bool Initialize(std::uintptr_t base, std::string_view sha,
                  const game::GameAdapter *game) noexcept;
  static bool Pump(void *context,
      const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
private:
  bool Advance(const ck3_11906::MainThreadExecutionStampV1 &);
  void Publish(Status status) noexcept;
  HANDLE mapping_ = nullptr;
  Shared *shared_ = nullptr;
  const game::GameAdapter *game_ = nullptr;
  std::uintptr_t base_ = 0;
  std::uint32_t seen_ = 0;
  std::uint64_t next_check_ms_ = 0;
  std::uint64_t settle_until_ms_ = 0;
  void *camera_ = nullptr;
  Request request_{};
  Result result_{};
};
} // namespace xar::presentation
