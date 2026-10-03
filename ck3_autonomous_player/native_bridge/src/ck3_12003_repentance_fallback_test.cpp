#include "xar_bridge/ck3_12003_repentance_fallback.hpp"

#include <array>
#include <bit>
#include <cassert>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <unordered_map>

namespace f = xar::ck3_12003::religion::repentance_fallback;
template <std::size_t N> struct Blob {
  alignas(8) std::array<std::byte, N> bytes{};
  template <typename T> void Put(std::size_t offset, T value) {
    assert(offset + sizeof(T) <= N); std::memcpy(bytes.data() + offset, &value, sizeof(T));
  }
  void *Ptr() { return bytes.data(); }
};
constexpr std::int32_t Id(std::uint32_t value) { return std::bit_cast<std::int32_t>(value); }
struct Fixture {
  static constexpr auto actor = Id(0x01000001), child = Id(0x83000002), grandchild = Id(0x04000003);
  static constexpr auto bishop = Id(0x05000004), first_contract = Id(0x82000006), second_contract = Id(0x84000007);
  static constexpr auto primary_id = Id(0x01000008), county1_id = Id(0x02000009), county2_id = Id(0x0300000a);
  static constexpr auto county3_id = Id(0x0400000b), region1_id = Id(0x0500000c), region2_id = Id(0x0600000d);
  Blob<0x200> player, first, second, cleric;
  Blob<0x240> player_land, first_land;
  Blob<0x40> contract1, contract2;
  Blob<0x350> primary, county1, county2, county3, region1, region2;
  Blob<0x68> primary_definition, county_definition;
  Blob<0x30> char_storage, contract_storage, title_storage;
  Blob<64*16> char_rows, contract_rows, title_rows;
  std::array<std::int32_t, 1> player_contracts{first_contract}, first_contracts{second_contract};
  std::array<std::int32_t, 3> title_children{county1_id, county2_id, county3_id};
  void *char_slot = nullptr, *contract_slot = nullptr, *title_slot = nullptr;
  bool primary_absent = false, region_failure = false;
  unsigned region_calls = 0;
  std::unordered_map<std::int32_t, std::int32_t> regions;
  Fixture() {
    player.Put(0x18, actor); first.Put(0x18, child); second.Put(0x18, grandchild); cleric.Put(0x18, bishop);
    player.Put(0x1c0, player_land.Ptr()); first.Put(0x1c0, first_land.Ptr());
    player_land.Put(0x218, player_contracts.data()); player_land.Put(0x224, std::int32_t{1});
    first_land.Put(0x218, first_contracts.data()); first_land.Put(0x224, std::int32_t{1});
    contract1.Put(8, first_contract); contract1.Put(0x20, first.Ptr());
    contract2.Put(8, second_contract); contract2.Put(0x20, second.Ptr());
    primary.Put(0x10, primary_id); primary_definition.Put(0x64, std::int32_t{3});
    primary.Put(0x48, primary_definition.Ptr()); primary.Put(0x110, title_children.data()); primary.Put(0x11c, std::int32_t{3});
    county_definition.Put(0x64, std::int32_t{2});
    county1.Put(0x10, county1_id); county2.Put(0x10, county2_id); county3.Put(0x10, county3_id);
    for (auto *county : {&county1, &county2, &county3}) county->Put(0x48, county_definition.Ptr());
    region1.Put(0x10, region1_id); region1.Put(0x128, child);
    region2.Put(0x10, region2_id); region2.Put(0x128, bishop);
    regions = {{county1_id, region1_id}, {county2_id, region1_id}, {county3_id, region2_id}};
    Setup(char_storage, char_rows, char_slot); Setup(contract_storage, contract_rows, contract_slot); Setup(title_storage, title_rows, title_slot);
    Entry(char_rows, actor, player.Ptr()); Entry(char_rows, child, first.Ptr());
    Entry(char_rows, grandchild, second.Ptr()); Entry(char_rows, bishop, cleric.Ptr());
    Entry(contract_rows, first_contract, contract1.Ptr()); Entry(contract_rows, second_contract, contract2.Ptr());
    Entry(title_rows, primary_id, primary.Ptr()); Entry(title_rows, county1_id, county1.Ptr());
    Entry(title_rows, county2_id, county2.Ptr()); Entry(title_rows, county3_id, county3.Ptr());
    Entry(title_rows, region1_id, region1.Ptr()); Entry(title_rows, region2_id, region2.Ptr());
  }
  static void Setup(Blob<0x30> &storage, Blob<64*16> &rows, void *&slot) {
    storage.Put(0x20, rows.Ptr()); storage.Put(0x2c, std::int32_t{64}); slot = storage.Ptr();
  }
  static void Entry(Blob<64*16> &rows, std::int32_t id, void *pointer) {
    rows.Put((static_cast<std::uint32_t>(id) & 0xffffffU)*16ULL+8, pointer);
  }
};
Fixture *current = nullptr;
void *Primary(void *player) {
  assert(player == current->player.Ptr()); return current->primary_absent ? nullptr : current->primary.Ptr();
}
f::Scope16 *Region(void *, f::Scope16 *out, const f::Scope16 **input) {
  assert(input && *input && (*input)->kind == 5);
  ++current->region_calls;
  const auto id = Id(static_cast<std::uint32_t>((*input)->id));
  if (current->region_failure && id == Fixture::county3_id) return nullptr;
  out->kind = 5; out->padding = 0;
  out->id = static_cast<std::uint32_t>(current->regions.at(id)); return out;
}
f::Bindings Bind(Fixture &fixture) {
  current = &fixture; f::Bindings b{}; b.enabled = true;
  b.character_storage_slot = &fixture.char_slot; b.contract_storage_slot = &fixture.contract_slot;
  b.title_storage_slot = &fixture.title_slot; b.primary_title = &Primary; b.clerical_region = &Region;
  return b;
}
f::Context Read(Fixture &fixture) {
  const auto b = Bind(fixture); f::Context out;
  (void)f::ReadRepentanceFallback12003(b, fixture.player.Ptr(), Fixture::actor, 53237640, 35754, out);
  return out;
}
void Save(const std::filesystem::path &folder, const char *name, const f::Context &out) {
  std::ofstream stream(folder / (std::string{name} + ".json")); stream << f::SerializeRepentanceFallback12003(out) << '\n';
}
int main(int argc, char **argv) {
  assert(argc == 2); const std::filesystem::path output(argv[1]);
  {
    Fixture fixture; const auto result = Read(fixture);
    assert(result.available && result.complete_source_traversal);
    assert(result.realm_vassals.rows.size() == 2 && result.realm_vassals.visited_nodes == 3);
    assert(result.realm_vassals.rows[0].character_id == Fixture::child);
    assert(result.realm_vassals.rows[1].character_id == Fixture::grandchild);
    assert(fixture.region_calls == 3 && result.dejure_clerical_holders.rows.size() == 2);
    assert(result.candidates.size() == 3 && result.candidates[0].sources.size() == 2);
    assert(result.candidates[0].origin_title_ids == std::vector<std::int32_t>{Fixture::region1_id});
    Save(output, "recursive-fullid-dejure-dedup", result);
  }
  {
    Fixture fixture; fixture.player.Put(0x1c0, static_cast<void *>(nullptr)); fixture.primary_absent = true;
    const auto result = Read(fixture); assert(result.available && result.complete_source_traversal && result.candidates.empty());
    assert(result.primary_title_id == -1); Save(output, "known-empty-sources", result);
  }
  {
    Fixture fixture; fixture.contract2.Put(8, Id(0x85000007)); const auto result = Read(fixture);
    assert(!result.available && !result.complete_source_traversal && !result.realm_vassals.traversal_complete);
    assert(result.realm_vassals.rows.size() == 1 && result.dejure_clerical_holders.available);
    Save(output, "realm-partial-other-source-preserved", result);
  }
  {
    Fixture fixture; fixture.region_failure = true; const auto result = Read(fixture);
    assert(!result.available && !result.dejure_clerical_holders.traversal_complete && result.realm_vassals.available);
    assert(result.dejure_clerical_holders.rows.size() == 1 && result.candidates.size() == 2);
    Save(output, "dejure-partial-realm-preserved", result);
  }
  {
    Fixture fixture; fixture.regions[Fixture::county3_id] = -1; fixture.region1.Put(0x128, std::int32_t{-1});
    const auto result = Read(fixture); assert(result.available && result.dejure_clerical_holders.rows.empty());
    assert(result.candidates.size() == 2); Save(output, "known-absent-region-and-holder", result);
  }
  std::cout << "GREEN: 5 new fallback collection scenarios\n";
}
