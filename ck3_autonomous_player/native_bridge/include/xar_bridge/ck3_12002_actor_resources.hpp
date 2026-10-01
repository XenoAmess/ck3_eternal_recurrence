#pragma once

#include <cstddef>
#include <cstdint>

namespace xar::ck3_12002 {

using ActorResourceReadMemory12002 = bool (*)(
    void *, std::uintptr_t, void *, std::size_t) noexcept;

struct ActorResourceBalances12002 {
  std::int64_t gold_raw = 0;
  std::int64_t prestige_raw = 0;
  std::int64_t piety_raw = 0;
  std::int32_t stress_points = 0;
  friend bool operator==(const ActorResourceBalances12002 &,
                         const ActorResourceBalances12002 &) = default;
};

// Frame-free leaf beneath the admitted 1.20 adapter. Gold/prestige/piety are
// signed Q100000; stress is an integer. Native getter fallback for an absent
// resource extension is a legal observed zero. A failed memory read is false.
bool ReadActorResourceBalances12002(
    ActorResourceReadMemory12002 read_memory, void *context,
    std::uintptr_t actor, std::int32_t expected_full_id,
    ActorResourceBalances12002 &output) noexcept;

} // namespace xar::ck3_12002
