#include "xar_bridge/actor_army_role_source_gate_v1.hpp"

#include <array>
#include <cstdint>
#include <vector>

int main() {
  using namespace xar::ck3_11906;
  std::array<ActorArmyRoleStorageHeaderV1, 4> headers{};
  for (std::size_t index = 0; index < headers.size(); ++index) {
    headers[index] = {
        reinterpret_cast<void *>(static_cast<std::uintptr_t>(0x1000 + index)),
        reinterpret_cast<void *>(static_cast<std::uintptr_t>(0x2000 + index)),
        100};
  }
  // The raw stream includes component generation IDs, commander identity,
  // regiment header, each regiment ID, knight ID, and reverse backlink.
  const std::vector<std::uint64_t> sample = {
      83886367, 50331794, 29829, 0x4000, 2, 2,
      101, 50331794, 29829, 101, 102, 50331794, -1ULL};
  if (!StableActorArmyRoleSourceV1(headers, headers, sample, sample)) return 1;
  for (std::size_t slot = 0; slot < headers.size(); ++slot) {
    auto changed = headers;
    changed[slot].slots = reinterpret_cast<void *>(0x9000);
    if (StableActorArmyRoleSourceV1(headers, changed, sample, sample)) return 2;
    changed = headers;
    ++changed[slot].capacity;
    if (StableActorArmyRoleSourceV1(headers, changed, sample, sample)) return 3;
  }
  for (std::size_t field = 0; field < sample.size(); ++field) {
    auto changed = sample;
    ++changed[field];
    if (StableActorArmyRoleSourceV1(headers, headers, sample, changed)) return 4;
  }
  const std::vector<std::int32_t> regiments = {101, 102};
  if (UniqueActorArmyRoleRegimentIdV1(regiments, 101) ||
      !UniqueActorArmyRoleRegimentIdV1(regiments, 103) ||
      UniqueActorArmyRoleRegimentIdV1(regiments, 0)) return 5;
  return 0;
}
