#include "xar_bridge/conception_pair_list_bonus_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t image = 0x10000000, storage = 0x20000000,
    slots = 0x21000000, first = 0x30000000, second = 0x31000000,
    child_a = 0x32000000, child_b = 0x33000000, fallback = 0x34000000,
    family_a = 0x40000000, family_b = 0x41000000,
    child_family_a = 0x42000000, child_family_b = 0x43000000,
    default_family = 0x44000000, list_a = 0x50000000, list_b = 0x51000000;
constexpr std::uint32_t first_id = 0x01000001, second_id = 0x02000002,
    child_a_id = 0x03000003, child_b_id = 0x04000004, no_id = 0xFFFFFFFF;

struct Owned {
  std::map<std::uintptr_t, std::vector<std::byte>> blocks;
  std::vector<std::pair<std::uintptr_t, std::size_t>> reads;
  std::uintptr_t denied = 0;
  template <typename T> void Put(std::uintptr_t address, T value) {
    for (auto &[start, bytes] : blocks) {
      if (address >= start && address - start <= bytes.size() &&
          sizeof(T) <= bytes.size() - (address - start)) {
        std::memcpy(bytes.data() + (address - start), &value, sizeof(T));
        return;
      }
    }
    throw std::runtime_error("fixture store outside owned block");
  }
};
bool Read(void *context, const void *raw, void *out, std::size_t size) noexcept {
  auto &m = *static_cast<Owned *>(context);
  const auto address = reinterpret_cast<std::uintptr_t>(raw);
  m.reads.emplace_back(address, size);
  if (address == m.denied) return false;
  for (const auto &[start, bytes] : m.blocks) {
    if (address >= start && address - start <= bytes.size() &&
        size <= bytes.size() - (address - start)) {
      std::memcpy(out, bytes.data() + (address - start), size);
      return true;
    }
  }
  return false;
}
void Need(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
bool ReadAt(const Owned &m, std::uintptr_t address) {
  for (const auto &row : m.reads) if (row.first == address) return true;
  return false;
}
Owned Make() {
  Owned m;
  for (const auto address : {first, second, child_a, child_b, fallback})
    m.blocks.emplace(address, std::vector<std::byte>(0x1D8));
  for (const auto address : {family_a, family_b, child_family_a,
                             child_family_b, default_family})
    m.blocks.emplace(address, std::vector<std::byte>(0x60));
  m.blocks.emplace(image + 0x5C67568, std::vector<std::byte>(16));
  m.blocks.emplace(image + 0x5D59588, std::vector<std::byte>(16));
  m.blocks.emplace(storage, std::vector<std::byte>(0x30));
  m.blocks.emplace(slots, std::vector<std::byte>(16 * 5));
  m.blocks.emplace(list_a, std::vector<std::byte>(8));
  m.blocks.emplace(list_b, std::vector<std::byte>(8));
  m.Put(image + 0x5C67568, storage);
  m.Put(image + 0x5C67570, fallback);
  m.Put(storage + 0x20, slots);
  m.Put(storage + 0x2C, std::uint32_t{5});
  m.Put(slots + 3 * 16 + 8, child_a);
  m.Put(slots + 4 * 16 + 8, child_b);
  for (const auto pair : {std::pair{first, first_id}, {second, second_id},
                          {child_a, child_a_id}, {child_b, child_b_id}}) {
    m.Put(pair.first + 0x18, pair.second);
    m.Put(pair.first + 0x1C, std::uint32_t{0x43686172});
  }
  m.Put(first + 0x1A8, family_a);
  m.Put(second + 0x1A8, family_b);
  m.Put(child_a + 0x1A8, child_family_a);
  m.Put(child_b + 0x1A8, child_family_b);
  m.Put(fallback + 0x1A8, default_family);
  for (const auto address : {family_a, family_b, child_family_a,
                             child_family_b, default_family}) {
    m.Put(address, no_id);
    m.Put(address + 4, no_id);
    m.Put(address + 0x14, no_id);
  }
  m.Put(family_b + 0x14, first_id);
  m.Put(family_a + 0x38, list_a);
  m.Put(family_b + 0x38, list_b);
  m.Put(family_a + 0x44, std::int32_t{1});
  m.Put(family_b + 0x44, std::int32_t{1});
  m.Put(list_a, child_a_id);
  m.Put(list_b, child_b_id);
  return m;
}
ConceptionPairListBonus12004Read Run(Owned &m) {
  const auto before = m.blocks;
  const auto b = BindConceptionPairListBonus12004(
      image, kGameVersion, kExecutableSha256, Read, &m);
  const auto r = ReadConceptionPairListBonusForCharacters12004(
      b, first, first_id, second, second_id);
  Need(m.blocks == before, "reader modified owned source memory");
  return r;
}
void Focus() {
  {
    auto m = Make();
    m.Put(family_b + 0x14, no_id);
    m.denied = family_a + 0x44;
    const auto r = Run(m);
    Need(r.status == "available" && r.primary_relation_match == false &&
        r.apply_relation_bonus == false && r.apply_land_state_bonus == false &&
        !ReadAt(m, family_a + 0x44), "unrelated pair consumed child inputs");
  }
  {
    auto m = Make();
    m.Put(family_a + 0x44, std::int32_t{0});
    m.denied = family_b + 0x44;
    const auto r = Run(m);
    Need(r.status == "available" && r.apply_relation_bonus == true &&
        r.apply_land_state_bonus == false && !r.second_child_count_raw &&
        !ReadAt(m, family_b + 0x44) && !ReadAt(m, list_a),
        "native first-empty short circuit was lost");
  }
  {
    auto m = Make();
    m.Put(child_family_a + 4, second_id);
    m.Put(child_a + 0x1D0, std::uintptr_t{0x1234});
    m.denied = list_b;
    const auto r = Run(m);
    Need(r.status == "available" && r.apply_relation_bonus == false &&
        r.first_list_has_second_parent_witness == true &&
        !r.second_list_has_first_parent_witness && !ReadAt(m, list_b) &&
        !ReadAt(m, child_a + 0x1D0),
        "parent4 witness or dead-child/second-list short circuit differs");
  }
  {
    auto m = Make();
    m.Put(child_family_b, first_id);
    const auto r = Run(m);
    Need(r.status == "available" && r.apply_relation_bonus == false &&
        r.first_list_has_second_parent_witness == false &&
        r.second_list_has_first_parent_witness == true,
        "second-list parent0 witness did not skip relation bonus");
  }
  {
    auto m = Make();
    m.Put(second + 0x1C0, std::uintptr_t{0x9999});
    m.denied = first + 0x1C0;
    const auto r = Run(m);
    Need(r.status == "available" && r.apply_relation_bonus == true &&
        r.apply_land_state_bonus == true && !ReadAt(m, first + 0x1C0),
        "no-common-parent or native land pointer short circuit differs");
  }
  {
    auto m = Make();
    m.Put(list_a, std::uint32_t{0x05000003});
    m.Put(default_family + 4, second_id);
    const auto r = Run(m);
    Need(r.status == "available" && r.apply_relation_bonus == false &&
        r.first_list_has_second_parent_witness == true &&
        ReadAt(m, default_family + 4),
        "same low24 stale generation failed to use native fallback witness");
  }
  {
    auto m = Make();
    m.Put(first + 0x1A8, std::uintptr_t{0});
    const auto r = Run(m);
    Need(r.status == "available" && r.apply_relation_bonus == true &&
        r.first_child_count_raw == 0 && ReadAt(m, image + 0x5D59588 + 0xC),
        "null Family did not read caller static default list");
  }
  {
    auto m = Make();
    m.denied = child_family_a + 4;
    const auto r = Run(m);
    Need(r.status == "unavailable" && !r.apply_relation_bonus &&
        !r.first_list_has_second_parent_witness && !ReadAt(m, list_b),
        "failed parent read became a false witness or consumed second list");
  }
  {
    auto m = Make();
    m.Put(family_a + 0x44, std::int32_t{-1});
    const auto r = Run(m);
    Need(r.status == "unavailable" && !r.apply_relation_bonus,
        "negative nonempty native count became a known result");
  }
  {
    auto m = Make();
    const auto b = BindConceptionPairListBonus12004(
        image, "1.20.0.3", kExecutableSha256, Read, &m);
    const auto r = ReadConceptionPairListBonusForCharacters12004(
        b, first, first_id, second, second_id);
    Need(!b.enabled && r.status == "unavailable" && m.reads.empty(),
        "wrong exact build performed source reads");
  }
  Need(ConceptionPairRelationBonusCondition12004(
      false, {}, {}, {}, {}) == false,
      "pure condition required inputs for an unrelated pair");
  Need(ConceptionPairRelationBonusCondition12004(
      true, 0, {}, {}, {}) == true,
      "pure condition failed native first-empty short circuit");
  Need(!ConceptionPairRelationBonusCondition12004(
      true, 1, 1, {}, {}).has_value(),
      "pure condition turned missing witness into known bonus");
}
} // namespace

int main() {
  try {
    Focus();
    std::cout << "{\"status\":\"GREEN\",\"focus\":\"new_pair_list_bonus_owned_inputs\","
        "\"scenes\":10,\"pure_condition_checks\":3,\"game_operations\":0,"
        "\"live_qualification\":false}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
