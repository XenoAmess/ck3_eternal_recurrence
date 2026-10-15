#include "xar_bridge/ck3_12002_faction_alerts.hpp"
#include <array>
#include <cstddef>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using Bytes = std::array<std::byte, 1024>;
template<class T> void Put(Bytes &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
struct Storage {
  Bytes header{}, slots{};
  void *pointer = header.data();
  Storage() { Put(header, 0x20, slots.data()); Put(header, 0x2C, std::int32_t{64}); }
  void Add(std::int32_t id, Bytes &object, std::size_t identity) {
    Put(slots, static_cast<std::size_t>(id) * 0x10 + 8, object.data()); Put(object, identity, id);
  }
};
}
int main() {
  Storage characters, titles, contracts;
  Bytes actor{}, vassal{}, actor_land{}, vassal_land{}, own_county{}, other_county{},
      duchy{}, county_definition{}, duchy_definition{}, contract{};
  characters.Add(1, actor, 0x18); characters.Add(2, vassal, 0x18);
  Put(actor, 0x1C0, actor_land.data()); Put(vassal, 0x1C0, vassal_land.data());
  titles.Add(11, own_county, 0x10); titles.Add(12, other_county, 0x10); titles.Add(13, duchy, 0x10);
  Put(county_definition, 0x64, std::int32_t{2}); Put(duchy_definition, 0x64, std::int32_t{3});
  Put(own_county, 0x48, county_definition.data()); Put(other_county, 0x48, county_definition.data());
  Put(duchy, 0x48, duchy_definition.data());
  Put(own_county, 0x11C, std::int32_t{1}); Put(other_county, 0x11C, std::int32_t{1});
  std::array<std::int32_t, 3> own_ids{11, 13, 11};
  std::array<std::int32_t, 1> vassal_ids{12}, contract_ids{21};
  Put(actor_land, 0x1E0, own_ids.data()); Put(actor_land, 0x1EC, std::int32_t{3});
  Put(vassal_land, 0x1E0, vassal_ids.data()); Put(vassal_land, 0x1EC, std::int32_t{1});
  contracts.Add(21, contract, 8); Put(contract, 0x20, vassal.data());
  Put(actor_land, 0x218, contract_ids.data()); Put(actor_land, 0x224, std::int32_t{1});
  xar::ck3_12002::PlayerFactionAlertsNativeEnvironmentV1 env{};
  env.exact_build_admitted = true;
  env.character_storage_slot = &characters.pointer;
  env.landed_title_storage_slot = &titles.pointer;
  env.vassal_contract_storage_slot = &contracts.pointer;
  xar::ck3_12002::PlayerFactionAlertsAccessV1 access{};
  std::vector<std::int32_t> counties;
  if (!xar::ck3_12002::ReadSubrealmCountyIdsV1(env, access, 1, counties) ||
      counties != std::vector<std::int32_t>{11, 12}) return 1;
  Put(own_county, 0x10, std::int32_t{0x100000B});
  if (xar::ck3_12002::ReadSubrealmCountyIdsV1(env, access, 1, counties)) return 2;
  env.exact_build_admitted = false;
  if (xar::ck3_12002::ReadSubrealmCountyIdsV1(env, access, 1, counties) || !counties.empty()) return 3;
  std::cout << "real county reader: actor, vassal, deduplication, tiers and full-generation rejection passed\n";
  return 0;
}
