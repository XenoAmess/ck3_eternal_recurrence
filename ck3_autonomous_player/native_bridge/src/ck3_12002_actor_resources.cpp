#include "xar_bridge/ck3_12002_actor_resources.hpp"

#include <limits>

namespace xar::ck3_12002 {
namespace {
template <typename T>
bool Read(ActorResourceReadMemory12002 callback, void *context,
          std::uintptr_t base, std::size_t offset, T &output) noexcept {
  return callback != nullptr && base != 0 &&
         offset <= (std::numeric_limits<std::uintptr_t>::max)() - base &&
         callback(context, base + offset, &output, sizeof(output));
}
}

bool ReadActorResourceBalances12002(
    ActorResourceReadMemory12002 read_memory, void *context,
    std::uintptr_t actor, std::int32_t expected_full_id,
    ActorResourceBalances12002 &output) noexcept {
  std::int32_t observed_id = -1;
  std::uintptr_t extension = 0;
  if (expected_full_id <= 0 ||
      !Read(read_memory, context, actor, 0x18, observed_id) ||
      observed_id != expected_full_id ||
      !Read(read_memory, context, actor, 0x1B0, extension))
    return false;
  ActorResourceBalances12002 sampled{};
  if (extension != 0 &&
      (!Read(read_memory, context, extension, 0x100, sampled.gold_raw) ||
       !Read(read_memory, context, extension, 0x130, sampled.prestige_raw) ||
       !Read(read_memory, context, extension, 0x110, sampled.piety_raw) ||
       !Read(read_memory, context, extension, 0x2F8, sampled.stress_points)))
    return false;
  output = sampled;
  return true;
}

} // namespace xar::ck3_12002
