// Synthetic memory only. Executes the production DATA reader and JSON serializer.
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>

template<class T, std::size_t N>
void Put(std::array<std::byte, N> &object, std::size_t offset, T value) {
  std::memcpy(object.data() + offset, &value, sizeof value);
}
void Require(bool value) { if (!value) throw std::runtime_error("fixture failed"); }
int main() {
  using namespace xar;
  std::array<std::byte, 0x150> arrg{};
  std::array<std::byte, 0x200> character{}, fallback{};
  std::array<std::byte, 0x180> extension{};
  std::array<std::byte, 0x40> storage{};
  std::array<std::byte, 301 * 0x10> objects{};
  Put(arrg, 0x10, std::int32_t{900}); Put(arrg, 0x14, std::uint32_t{0x41725267});
  Put(arrg, 0x140, std::int32_t{88}); Put(arrg, 0x148, std::int32_t{300});
  Put(character, 0x18, std::int32_t{300}); Put(character, 0x1C, std::uint32_t{0x43686172});
  Put(character, 0x1B8, extension.data());
  Put(extension, 0xF4, std::int32_t{-1}); Put(extension, 0xF8, std::int32_t{900});
  Put(fallback, 0x18, std::int32_t{-1});
  Put(objects, 300 * 0x10 + 8, character.data());
  Put(storage, 0x20, objects.data()); Put(storage, 0x2C, std::int32_t{301});
  void *storage_slot=storage.data(), *fallback_slot=fallback.data(), *persistent_slot=nullptr;
  ck3_12002::ArmyBindings bindings{}; bindings.enabled=true;
  bindings.persistent_regiment_storage_slot=&persistent_slot;
  bindings.can_regiment_replenish=[](void *,void *) { return false; };
  bindings.can_chunk_replenish=[](void *) { return false; };
  bindings.get_regiment_monthly_replenishment_fraction=[](void *,std::int64_t *out) { return out; };
  bindings.is_army_regiment_loss_writer_skipped=[](void *) { return true; };
  bindings.regiment_character_role_executable_sha256="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  bindings.regiment_character_role_storage_slot=&storage_slot;
  bindings.regiment_character_role_fallback_slot=&fallback_slot;
  const auto current=ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(bindings,arrg.data(),900,88);
  Require(current.status==game::ArmyRegimentReplenishmentRecordsStatusV1::available);
  Require(current.native_character_role_v1.has_value());
  Require(current.native_character_role_v1->status=="available");
  Require(current.native_character_role_v1->resolved_character_id==300);
  Require(current.native_character_role_v1->extension_army_id_f4==-1);
  const auto wrong_army=ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(bindings,arrg.data(),900,89);
  Require(wrong_army.native_character_role_v1->status=="unavailable");
  const auto legacy=ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(bindings,arrg.data(),900);
  Require(!legacy.native_character_role_v1);
  bindings.regiment_character_role_executable_sha256="wrong";
  const auto wrong_build=ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(bindings,arrg.data(),900,88);
  Require(wrong_build.native_character_role_v1->status=="unavailable");
  const auto number=[](auto value) { return std::to_string(value); };
  const auto json=[](std::string &out,std::string_view text) {
    out+='"'; for (const char c:text) { if(c=='"'||c=='\\') out+='\\'; out+=c; } out+='"';
  };
  std::string output="[";
  game::AppendArmyRegimentReplenishmentRecordsSnapshotV1(output,current,number,json);
  output+=',';
  game::AppendArmyRegimentReplenishmentRecordsSnapshotV1(output,legacy,number,json);
  output+=']'; std::cout<<output;
}
