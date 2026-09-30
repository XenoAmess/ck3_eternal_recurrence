#include "xar_bridge/ck3_12002_phase_culture.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

namespace {
using namespace xar::ck3_12002::phase_culture;
template<class T> void Put(void *base, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
template<std::size_t N> struct Object {
  alignas(8) std::array<std::byte,N> bytes{};
  void *data() { return bytes.data(); }
};
struct Definition {
  std::array<std::byte,0x18> prefix{};
  std::string key;
  std::uint32_t kind = 0x4744624F;
  std::uint32_t pad = 0;
  explicit Definition(std::string_view key) : key(key) {}
};
static_assert(offsetof(Definition,key) == 0x18);
static_assert(offsetof(Definition,kind) == 0x38);
void *g_liege = nullptr;
Object<0x10> g_perks;
std::array<std::string,10> g_names{
    "knights_slightly_more_prone_to_injury", "blademaster_traits_more_common",
    "unlock_zhanmadao", "unlock_burenjia", "unlock_maa_cataphract_archers",
    "unlock_maa_black_armor_cavalry", "unlock_maa_horse_archers",
    "unlock_maa_mangudai", "unlock_emishi_horse_archers_units",
    "unlock_mounted_samurai_units"};
void *Context(void *) { return g_liege; }
void *Perks(void *) { return g_perks.data(); }
bool Parameter(void *, std::int32_t id) { return id == 0 || id == 5; }
std::int32_t Lookup(const NativeStringView64 *value) {
  const auto key = std::string_view(value->data,static_cast<std::size_t>(value->size));
  for (std::size_t i=0;i<g_names.size();++i)
    if (g_names[i] == key) return static_cast<std::int32_t>(i);
  return 12;
}
const std::string *Name(std::int32_t id) {
  return id >= 0 && id < 10 ? &g_names[static_cast<std::size_t>(id)] : nullptr;
}
struct Store {
  Object<0x30> object;
  Object<0x40> slots;
  void *pointer = object.data();
  Store() {
    Put(object.data(),0x20,slots.data());
    Put(object.data(),0x2C,std::int32_t{4});
  }
  void Set(std::uint32_t index,void *object_pointer) {
    Put(slots.data(),index * 0x10 + 8,object_pointer);
  }
};
struct Database {
  Object<0x80> object;
  std::vector<std::unique_ptr<Definition>> owned;
  std::vector<void *> rows;
  void *pointer = object.data();
  Definition *Add(std::string_view key) {
    owned.push_back(std::make_unique<Definition>(key));
    rows.push_back(owned.back().get());
    Refresh();
    return owned.back().get();
  }
  void Refresh() {
    Put(object.data(),0x50,rows.data());
    Put(object.data(),0x5C,static_cast<std::int32_t>(rows.size()));
    // These old offsets are deliberately empty. The migrated reader must
    // discover actual 1.20 definitions instead of returning legal false.
    Put(object.data(),0x68,static_cast<void *>(nullptr));
    Put(object.data(),0x74,std::int32_t{0});
  }
};
}

int main() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bound = BindImage(base,xar::ck3_12002::kExecutableSha256);
  assert(bound.enabled);
  assert(reinterpret_cast<std::uintptr_t>(bound.culture_store) == base + kCultureStoreSlot);
  assert(reinterpret_cast<std::uintptr_t>(bound.character_context) == base + kCharacterKnightContextRva);
  assert(!BindImage(base,"wrong-build").enabled);
  Store characters, houses, dynasties, cultures;
  Object<0x1D8> character,liege;
  Object<0x40> house;
  Object<0x200> dynasty;
  Object<0x540> culture;
  Object<0x130> culture_template;
  Object<0x90> resolved;
  Object<0xD0> relation;
  void *fallback = nullptr;
  constexpr std::int32_t id = 0x01000001;
  constexpr std::int32_t liege_id = 0x01000002;
  Put(character.data(),0x18,id);
  Put(liege.data(),0x18,liege_id);
  Put(character.data(),0x158,id);
  Put(character.data(),0xB0,id);
  Put(liege.data(),0x158,id);
  Put(house.data(),0x10,id);
  Put(house.data(),0x2C,id);
  Put(dynasty.data(),0x10,id);
  Put(culture.data(),0x10,id);
  Put(character.data(),0x1B8,relation.data());
  Put(relation.data(),0xC8,liege_id);
  characters.Set(1,character.data());characters.Set(2,liege.data());
  houses.Set(1,house.data());dynasties.Set(1,dynasty.data());cultures.Set(1,culture.data());
  g_liege = liege.data();
  Database dynasty_db,perk_db,innovation_db,tradition_db;
  const auto warfare = dynasty_db.Add("warfare_legacy_3");
  const auto stalwart = perk_db.Add("stalwart_leader_perk");
  std::array<void *,1> warfare_span{warfare},perk_span{stalwart};
  Put(dynasty.data(),0x178,warfare_span.data());
  Put(dynasty.data(),0x184,std::int32_t{1});
  Put(g_perks.data(),0,perk_span.data());Put(g_perks.data(),0x0C,std::int32_t{1});
  for (const auto key : std::array<std::string_view,12>{
      "innovation_quilted_armor", "innovation_sarawit", "innovation_legionnaires",
      "innovation_arched_saddle", "innovation_valets", "innovation_tiefutu",
      "innovation_advanced_bowmaking", "innovation_repeating_crossbow",
      "innovation_war_camels", "innovation_elephantry", "innovation_gunpowder",
      "innovation_fire_medicine"}) innovation_db.Add(key);
  for (const auto key : std::array<std::string_view,14>{
      "tradition_fp1_coastal_warriors", "tradition_hird", "tradition_futuwaa",
      "tradition_druzhina", "tradition_khadga_puja", "tradition_garuda_warriors",
      "tradition_himalayan_settlers", "tradition_mubarizuns",
      "tradition_burman_royal_army", "tradition_mountaineer_ruralism",
      "tradition_caucasian_wolves", "tradition_roman_legacy",
      "tradition_ep3_audacious_cadets", "tradition_ep3_imperial_tagmata"}) tradition_db.Add(key);
  Definition north("heritage_north_germanic"),other("other_pillar");
  std::array<void *,5> pillars{&other,&other,&north,&other,&other};
  std::array<void *,1> innovations{innovation_db.rows[0]}, traditions{tradition_db.rows[1]};
  Put(culture.data(),0x20,culture_template.data());
  Put(culture_template.data(),0x128,resolved.data());
  Put(resolved.data(),0x70,pillars.data());
  Put(resolved.data(),0x58,traditions.data());Put(resolved.data(),0x64,std::int32_t{1});
  Put(culture.data(),0x518,innovations.data());Put(culture.data(),0x524,std::int32_t{1});
  Bindings bindings;
  bindings.enabled=true;
  bindings.character_store=&characters.pointer;bindings.character_fallback=&fallback;
  bindings.house_store=&houses.pointer;bindings.house_fallback=&fallback;
  bindings.dynasty_store=&dynasties.pointer;bindings.dynasty_fallback=&fallback;
  bindings.culture_store=&cultures.pointer;bindings.culture_fallback=&fallback;
  bindings.dynasty_perk_database=&dynasty_db.pointer;
  bindings.character_perk_database=&perk_db.pointer;
  bindings.innovation_database=&innovation_db.pointer;bindings.innovation_fallback=&fallback;
  bindings.tradition_database=&tradition_db.pointer;bindings.tradition_fallback=&fallback;
  bindings.character_context=Context;bindings.character_perks=Perks;
  bindings.culture_has_parameter=Parameter;
  bindings.lookup_script_identifier=Lookup;bindings.script_identifier_name=Name;
  xar::game::CombatPhaseCharacterV3 output;
  output.faith={true,123};output.death_is_glory=true;
  assert(ReadPhaseCharacterCultureRelations(bindings,character.data(),output));
  assert(output.house.present && output.house.value == id);
  assert(output.dynasty.present && output.warfare_legacy_3 && output.stalwart_leader);
  assert(output.employer.present && output.employer.value == liege_id);
  assert(output.liege.present && output.liege_house.present);
  assert(output.heritage_north_germanic && output.knights_slightly_more_prone_to_injury);
  assert(!output.blademaster_traits_more_common);
  assert(output.innovations.size()==12 && output.innovations[0].value && !output.innovations[1].value);
  assert(output.traditions.size()==14 && !output.traditions[0].value && output.traditions[1].value);
  assert(output.culture_parameters.size()==10 && output.culture_parameters[5].value);
  assert(output.faith.present && output.faith.value==123 && output.death_is_glory);
  // Legal zero ownership is observed false; stale same-index generation is a
  // read failure. Malformed new spans must never alias valid old locations.
  Put(dynasty.data(),0x184,std::int32_t{0});
  assert(ReadPhaseCharacterCultureRelations(bindings,character.data(),output));
  assert(!output.warfare_legacy_3);
  Put(culture.data(),0x10,std::int32_t{0x02000001});
  assert(!ReadPhaseCharacterCultureRelations(bindings,character.data(),output));
  Put(culture.data(),0x10,id);
  Put(resolved.data(),0x64,std::int32_t{-1});
  assert(!ReadPhaseCharacterCultureRelations(bindings,character.data(),output));
  Put(resolved.data(),0x64,std::int32_t{1});
  tradition_db.owned[0]->kind=0;
  assert(!ReadPhaseCharacterCultureRelations(bindings,character.data(),output));
  tradition_db.owned[0]->kind=0x4744624F;
  auto duplicate=innovation_db.Add("innovation_quilted_armor");
  assert(!ReadPhaseCharacterCultureRelations(bindings,character.data(),output));
  innovation_db.rows.pop_back();innovation_db.Refresh();
  (void)duplicate;
  Put(character.data(),0xB0,std::int32_t{-1});
  assert(ReadPhaseCharacterCultureRelations(bindings,character.data(),output));
  assert(!output.culture.present && !output.heritage_north_germanic);
  assert(!output.innovations[0].value && !output.traditions[1].value);
  assert(!output.culture_parameters[0].value);
}
