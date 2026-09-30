#pragma once

#include <algorithm>
#include <array>
#include <cstdint>
#include <vector>

namespace xar::ck3_11906 {

struct ActorArmyRoleStorageHeaderV1 {
  void *storage = nullptr;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  friend bool operator==(const ActorArmyRoleStorageHeaderV1 &,
                         const ActorArmyRoleStorageHeaderV1 &) = default;
};

inline bool UniqueActorArmyRoleRegimentIdV1(
    const std::vector<std::int32_t> &seen, std::int32_t id) noexcept {
  return id > 0 && std::find(seen.begin(), seen.end(), id) == seen.end();
}

inline bool StableActorArmyRoleSourceV1(
    const std::array<ActorArmyRoleStorageHeaderV1, 4> &before,
    const std::array<ActorArmyRoleStorageHeaderV1, 4> &after,
    const std::vector<std::uint64_t> &first,
    const std::vector<std::uint64_t> &second) noexcept {
  return before == after && first == second;
}

} // namespace xar::ck3_11906
