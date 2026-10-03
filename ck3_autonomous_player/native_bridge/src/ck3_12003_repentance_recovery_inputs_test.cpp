#include "xar_bridge/ck3_12003_repentance_recovery_inputs.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
using namespace xar::ck3_12003::religion::repentance_recovery_inputs;
namespace {
template<std::size_t N> using Bytes = std::array<std::byte,N>;
template<typename T> void Put(void* object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte*>(object)+offset, &value, sizeof(value));
}
Bytes<0x200> actor{}, pool{};
Bytes<0x400> script{};
Bytes<0x40> flags{}, storage{};
Bytes<0x20> flag_rows{};
Bytes<0x90> modifier_rows{}, recent_definition{}, promised_definition{};
Bytes<0x340> held_title{}, other_title{};
Bytes<0x30> title_rows{};
void* storage_pointer = storage.data(); void* fallback = nullptr;
bool flag_registered = true, recent_definition_available = true;
std::int32_t tier = 4; int flag_getter_calls = 0;
std::uint32_t* Atom(void*, std::uint32_t* out, const NativeStringView* text) {
  assert(std::string_view(text->data, static_cast<std::size_t>(text->length)) == "pope_excom");
  *out = flag_registered ? 8U : 0xFFFFFFFFU; return out;
}
void* FlagCollection(void* value) { assert(value==script.data()); ++flag_getter_calls; return flags.data(); }
std::int32_t Highest(void* value) { assert(value==actor.data()); return tier; }
void* Database() { return pool.data(); }
std::uint32_t Hash(void*, const char* key, std::uint32_t length) {
  const std::string_view text(key,length);
  if (text=="recent_excommunication") return 11;
  assert(text=="promised_pilgrimage_to_clergy_modifier"); return 12;
}
void* Lookup(void*, std::int32_t key) {
  if (key==11) return recent_definition_available ? recent_definition.data() : nullptr;
  assert(key==12); return promised_definition.data();
}
void Definition(void* pointer, const char* key) {
  Put(pointer,0x18,key); Put(pointer,0x28,static_cast<std::uint64_t>(std::strlen(key)));
  Put(pointer,0x30,static_cast<std::uint64_t>(std::strlen(key)));
}
Bindings Setup() {
  actor.fill({}); script.fill({}); flags.fill({}); flag_rows.fill({});
  modifier_rows.fill({}); storage.fill({}); title_rows.fill({}); held_title.fill({}); other_title.fill({});
  flag_registered=true; recent_definition_available=true; tier=4; flag_getter_calls=0;
  Put(actor.data(),0x18,std::int32_t{29829}); Put(actor.data(),0x1C,std::uint32_t{0x43686172});
  Put(actor.data(),0x1B0,script.data()); Put(script.data(),0,std::int32_t{0});
  Put(pool.data(),0x10,flag_rows.data()); Put(pool.data(),0x1C,std::int32_t{1});
  Put(flags.data(),0x10,flag_rows.data()); Put(flags.data(),0x1C,std::int32_t{1}); Put(flag_rows.data(),8,std::uint32_t{8});
  Definition(recent_definition.data(),"recent_excommunication"); Definition(promised_definition.data(),"promised_pilgrimage_to_clergy_modifier");
  Put(script.data(),0x188,modifier_rows.data()); Put(script.data(),0x194,std::int32_t{2});
  Put(modifier_rows.data(),0,recent_definition.data()); Put(modifier_rows.data(),8,std::int32_t{53236608+3840});
  Put(modifier_rows.data(),0x48,promised_definition.data()); Put(modifier_rows.data(),0x50,std::int32_t{53236608+600});
  Put(storage.data(),0x20,title_rows.data()); Put(storage.data(),0x2C,std::uint32_t{3});
  Put(title_rows.data(),0x18,held_title.data()); Put(title_rows.data(),0x28,other_title.data());
  Put(held_title.data(),0x10,std::int32_t{1}); Put(held_title.data(),0x128,std::int32_t{29829});
  Put(other_title.data(),0x10,std::int32_t{2}); Put(other_title.data(),0x128,std::int32_t{29097});
  Put(other_title.data(),0x328,std::int32_t{4});
  Bindings b{}; b.enabled=true; b.existing_atom=Atom; b.atom_pool=pool.data();
  b.character_flag_collection=FlagCollection; b.highest_held_tier=Highest; b.title_storage_slot=&storage_pointer;
  b.modifier_database=Database; b.stable_key_hash=Hash; b.modifier_lookup=Lookup; b.modifier_fallback_slot=&fallback;
  return b;
}
void Wire(const std::filesystem::path& folder, const char* name, const Context& c) {
  std::ofstream(folder/(std::string(name)+".json")) << SerializePlayerRepentanceRecoveryInputs12003(c);
}
}
int main(int argc,char** argv) {
  assert(argc==2); const auto folder=std::filesystem::path(argv[1]); Context c{};
  auto b=Setup();
  assert(ReadPlayerRepentanceRecoveryInputs12003(b,actor.data(),29829,53236608,35754,c));
  assert(c.pope_excom.value==true && c.highest_held_title_tier.value==4);
  assert(c.any_held_title_has_clerical_region.value==false); // foreign clergy title does not count.
  assert(c.recent_excommunication.present==true && c.recent_excommunication.expiry_date_raw==53240448);
  assert(c.recent_excommunication.remaining_calendar_days==160 && c.promised_pilgrimage_to_clergy.remaining_calendar_days==25);
  Wire(folder,"current_cooldowns",c);
  b=Setup(); Put(flags.data(),0x1C,std::int32_t{0}); Put(script.data(),0x194,std::int32_t{0});
  Put(held_title.data(),0x328,std::int32_t{4}); tier=3;
  assert(ReadPlayerRepentanceRecoveryInputs12003(b,actor.data(),29829,53236608,35754,c));
  assert(c.pope_excom.value==false && c.any_held_title_has_clerical_region.value==true && c.highest_held_title_tier.value==3);
  assert(c.recent_excommunication.present==false && !c.recent_excommunication.expiry_date_raw);
  Wire(folder,"no_cooldown_archbishop_input",c);
  b=Setup(); Put(actor.data(),0x1B0,static_cast<void*>(nullptr));
  assert(ReadPlayerRepentanceRecoveryInputs12003(b,actor.data(),29829,53236608,35754,c));
  assert(c.pope_excom.value==false && c.recent_excommunication.present==false && c.promised_pilgrimage_to_clergy.present==false);
  assert(flag_getter_calls==0); Wire(folder,"legal_empty_script_data",c);
  b=Setup(); flag_registered=false;
  assert(ReadPlayerRepentanceRecoveryInputs12003(b,actor.data(),29829,53236608,35754,c));
  assert(c.pope_excom.value==false && flag_getter_calls==0); Wire(folder,"unregistered_flag_absent",c);
  b=Setup(); recent_definition_available=false;
  assert(!ReadPlayerRepentanceRecoveryInputs12003(b,actor.data(),29829,53236608,35754,c));
  assert(!c.recent_excommunication.available && !c.recent_excommunication.present);
  assert(c.pope_excom.available && c.highest_held_title_tier.available && c.any_held_title_has_clerical_region.available);
  assert(c.promised_pilgrimage_to_clergy.available); Wire(folder,"modifier_failure_keeps_route_inputs",c);
  b=Setup(); Put(modifier_rows.data(),8,std::int32_t{53236608-24});
  assert(ReadPlayerRepentanceRecoveryInputs12003(b,actor.data(),29829,53236608,35754,c));
  assert(c.recent_excommunication.present==true && c.recent_excommunication.remaining_calendar_days==-1);
  Wire(folder,"actual_row_presence_kept_until_native_removal",c);
  assert(!ReadPlayerRepentanceRecoveryInputs12003(b,actor.data(),29830,53236608,35754,c));
  assert(!c.pope_excom.value && !c.highest_held_title_tier.value);
  assert(!BindPlayerRepentanceRecoveryInputsImage12003(0x140000000,"wrong").enabled);
  std::cout << "GREEN: six new recovery-input semantic scenarios; actual reader and serializer.\n";
}
