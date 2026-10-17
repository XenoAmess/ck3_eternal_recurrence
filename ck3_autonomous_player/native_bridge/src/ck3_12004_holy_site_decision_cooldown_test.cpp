// Production wrapper -> real ByDefinition helper -> production full serializer.
// Only owned memory, registry hash/lookup and native expiry lookup are synthetic.
// No game process, original game function, detail window or desktop is used.
#include "xar_bridge/ck3_12004_holy_site_decision_cooldown.hpp"
#include <array>
#include <cstddef>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
namespace h=xar::ck3_12004::religion::holy_site;
namespace {
unsigned checks=0;
void Check(bool value,const char*why){++checks;if(!value)throw std::runtime_error(why);}
template<std::size_t N>using Bytes=std::array<std::byte,N>;
template<class B,class T>void Put(B&b,std::size_t at,T value){std::memcpy(b.data()+at,&value,sizeof(value));}
constexpr std::array actions{h::DecisionAction::adopt,h::DecisionAction::promote,h::DecisionAction::demote,h::DecisionAction::abandon};
struct Fixture {
 static constexpr std::uintptr_t base=0x140000000;
 static constexpr std::int32_t actor_id=0x03000004;
 std::array<Bytes<0x40>,4>definitions{};Bytes<0x40>replacement{},fallback{};
 std::array<std::string,4>keys{};Bytes<24>col{};
 Bytes<0x30>store{};Bytes<0x50>slots{};Bytes<0x1C8>actor{};Bytes<0x450>state{};
 Bytes<0x10>clock{};Bytes<0x150>rows{};Bytes<8>database{};
 void*database_ptr=database.data(),*store_ptr=store.data(),*clock_ptr=clock.data();
 const void*fallback_ptr=fallback.data();std::uint32_t current_actor=actor_id;
 bool changed_registry=false,foreign_key=false;unsigned registry_lookups=0,native_lookups=0;
 h::DecisionAction requested=h::DecisionAction::adopt;
 Fixture(){
  Put(col,0,std::uint32_t{1});Put(col,12,std::uint32_t{0x5586B90});Put(col,20,std::uint32_t{0x1000});
  for(std::size_t i=0;i<4;++i){keys[i]=h::DecisionKey(actions[i]);Definition(definitions[i],keys[i]);}
  Definition(replacement,keys[0]);
  Put(store,xar::ck3_12004::kCharacterStorageSlotsOffset,slots.data());
  Put(store,xar::ck3_12004::kCharacterStorageCapacityOffset,std::int32_t{5});
  Put(slots,4*xar::ck3_12004::kCharacterStorageSlotStride+xar::ck3_12004::kCharacterStorageObjectOffset,actor.data());
  Put(actor,xar::ck3_12004::kCharacterFullIdOffset,actor_id);Put(actor,0x1C0,state.data());
  Put(state,0x444,std::int32_t{-1});Put(clock,8,std::int32_t{100});
 }
 void Definition(Bytes<0x40>&target,const std::string&key){
  Put(target,0,base+0x48BD150);Put(target,0x18,key.c_str());
  Put(target,0x28,static_cast<std::uint64_t>(key.size()));Put(target,0x30,std::uint64_t{63});
  Put(target,0x38,std::uint32_t{0x4744624F});
 }
 void Timed(h::DecisionAction action,std::int32_t expiry){
  requested=action;const auto i=static_cast<std::size_t>(action);
  Put(state,0x438,rows.data());Put(state,0x440,std::int32_t{1});Put(state,0x444,std::int32_t{7});Put(state,0x448,std::uint8_t{5});
  rows[4]=std::byte{1};Put(rows,8,definitions[i].data());Put(rows,0x10,expiry);
  rows[13*0x18+4]=std::byte{0xFF};
 }
};
Fixture*f=nullptr;
struct Code {std::uintptr_t rva;std::string_view hex;};
constexpr Code code[]{
 {0xA14850,"4883ec38488b05959630054885c07542c74424281e000000488d05a987a70348"},
 {0x3F7E220,"894c2408534883ec2033c0488d4c2430418bd889442430458bc8894424404c8b"},
 {0xCAA8D0,"48895c24084533c04863da443881e00e0000458bc8410f94c1458d58fe4585c9"},
 {0x1A74790,"4c8bd90fb6c235c59d1c814c8bd24469c893010001488bc248c1e808440fb6c0"},
 {0x2957F10,"48895c241048897424185557415441564157488dac24b0fdffff4881ec50030000"}};
bool Copy(void*,const void*p,void*out,std::size_t n)noexcept{
 const auto address=reinterpret_cast<std::uintptr_t>(p);
 for(const auto&c:code)if(address==Fixture::base+c.rva){
  if(n>c.hex.size()/2)return false;
  const auto digit=[](char v){return v>='0'&&v<='9'?v-'0':v-'a'+10;};
  for(std::size_t i=0;i<n;++i)static_cast<unsigned char*>(out)[i]=static_cast<unsigned char>((digit(c.hex[2*i])<<4)|digit(c.hex[2*i+1]));return true;
 }
 if(address==Fixture::base+0x48BD150-8&&n==8){const auto col=Fixture::base+0x1000;std::memcpy(out,&col,8);return true;}
 if(address>=Fixture::base+0x1000&&address+n<=Fixture::base+0x1018){std::memcpy(out,f->col.data()+(address-(Fixture::base+0x1000)),n);return true;}
 const auto copy=[&](const void*start,std::size_t size){const auto begin=reinterpret_cast<std::uintptr_t>(start);
  if(address<begin||address-begin>size||n>size-(address-begin))return false;std::memcpy(out,p,n);return true;};
 for(std::size_t i=0;i<4;++i)if(copy(f->definitions[i].data(),f->definitions[i].size())||copy(f->keys[i].c_str(),f->keys[i].size()+1))return true;
 return copy(f->replacement.data(),f->replacement.size())||copy(f->col.data(),f->col.size())||
  copy(f->store.data(),f->store.size())||copy(f->slots.data(),f->slots.size())||copy(f->actor.data(),f->actor.size())||
  copy(f->state.data(),f->state.size())||copy(f->clock.data(),f->clock.size())||copy(f->rows.data(),f->rows.size())||
  copy(&f->database_ptr,sizeof(f->database_ptr))||copy(&f->fallback_ptr,sizeof(f->fallback_ptr))||
  copy(&f->store_ptr,sizeof(f->store_ptr))||copy(&f->clock_ptr,sizeof(f->clock_ptr))||copy(&f->current_actor,sizeof(f->current_actor));
}
std::uint32_t Hash(void*database,const char*key,std::uint32_t n){
 Check(database==f->database.data(),"native hash receives actual bound registry");
 for(std::size_t i=0;i<4;++i)if(std::string_view(key,n)==f->keys[i])return static_cast<std::uint32_t>(i+1);
 throw std::runtime_error("non-allowlisted decision key reached native hash");
}
const void*Lookup(void*database,std::uint32_t hash){
 Check(database==f->database.data()&&hash>=1&&hash<=4,"native registry receives fixed key hash");++f->registry_lookups;
 if(f->foreign_key)return f->definitions[hash%4].data();
 if(f->changed_registry&&f->registry_lookups>1)return f->replacement.data();
 return f->definitions[hash-1].data();
}
const std::int32_t*__fastcall Expiry(const void*map,const void*definition){
 Check(map==f->state.data()+0x430&&definition==f->definitions[static_cast<std::size_t>(f->requested)].data(),
  "real helper supplies actual actor map and definition pointer value");++f->native_lookups;
 return reinterpret_cast<const std::int32_t*>(f->rows.data()+0x10);
}
h::DecisionCooldownBindings Bind(Fixture&v){
 f=&v;h::DecisionCooldownBindings b{};b.enabled=true;b.image_base=Fixture::base;
 b.decision_database=&v.database_ptr;b.decision_fallback=&v.fallback_ptr;b.decision_hash=&Hash;b.decision_lookup=&Lookup;
 b.native.enabled=true;b.native.image_base=Fixture::base;b.native.read_memory=&Copy;
 b.native.current_actor_reference=&v.current_actor;b.native.character_storage=&v.store_ptr;b.native.decision_clock=&v.clock_ptr;b.native.cooldown_lookup=&Expiry;
 // Intentionally no detail, GUI owner, controller, selected_item or HolySite store.
 return b;
}
xar::ck3_12002::religion::Context Frame(){xar::ck3_12002::religion::Context c{};c.available=true;c.capture_epoch=17;c.date_raw=53175816;c.played_character_id=Fixture::actor_id;return c;}
void Save(const std::filesystem::path&dir,std::string_view name,const h::DecisionCooldownSnapshot&s){
 std::ofstream stream(dir/std::string(name));stream<<h::SerializeHolySiteDecisionCooldownCommand12004(s,"g2-read-cooldown-fixture",701,s.date_raw)<<'\n';Check(bool(stream),"full native command_result packet written");
}
}
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("pass a new external fixture output directory");
 const std::filesystem::path output=argv[1];
 if(std::filesystem::exists(output))throw std::runtime_error("fixture output must be new");std::filesystem::create_directories(output);
 const auto context=Frame();h::DecisionCooldownSnapshot result{};
 for(const auto action:actions){Fixture value;const auto bindings=Bind(value);
  Check(h::ReadHolySiteDecisionCooldown12004(bindings,context,action,result)&&result.available&&!result.cooldown.present&&
   !result.cooldown.active&&value.registry_lookups==2&&value.native_lookups==0,"four exact keys resolve twice and real helper observes empty map without detail");
  Save(output,std::string(h::DecisionActionName(action))+"-absent.json",result);
 }
 {Fixture value;const auto bindings=Bind(value);value.Timed(h::DecisionAction::promote,172);
  Check(h::ReadHolySiteDecisionCooldown12004(bindings,context,h::DecisionAction::promote,result)&&result.available&&result.cooldown.present&&
   result.cooldown.active&&result.cooldown.current_counter_raw==100&&result.cooldown.expiry_raw==172&&value.native_lookups==2,"wrapper calls real helper and retains active raw cooldown");Save(output,"promote-active-afterdetail-none.json",result);
  Put(value.clock,8,std::int32_t{172});value.registry_lookups=0;
  Check(h::ReadHolySiteDecisionCooldown12004(bindings,context,h::DecisionAction::promote,result)&&!result.cooldown.active,"expiry equality is expired");Save(output,"promote-expired.json",result);}
 {Fixture value;auto bindings=Bind(value);value.changed_registry=true;
  Check(!h::ReadHolySiteDecisionCooldown12004(bindings,context,h::DecisionAction::adopt,result)&&!result.available,"same-key different definition after helper is unavailable");Save(output,"changed-registry.json",result);}
 {Fixture value;const auto bindings=Bind(value);value.foreign_key=true;
  Check(!h::ReadHolySiteDecisionCooldown12004(bindings,context,h::DecisionAction::adopt,result)&&!result.available,"hash lookup foreign full key is unavailable");Save(output,"foreign-key.json",result);}
 {Fixture value;auto bindings=Bind(value);bindings.enabled=false;
  Check(!h::BindHolySiteDecisionCooldownImage12004(Fixture::base,"foreign-exe").enabled&&
   !h::ReadHolySiteDecisionCooldown12004(bindings,context,h::DecisionAction::abandon,result)&&!result.available,"foreign build cannot observe cooldown");Save(output,"foreign-build.json",result);}
 std::ofstream receipt(output/"fixture-provenance.json");receipt<<"{\"source_only_fixture\":true,\"wrapper_executed\":true,\"real_by_definition_helper_executed\":true,\"full_serializer_executed\":true,\"synthetic_registry_callbacks\":true,\"synthetic_native_expiry_lookup\":true,\"live\":false}";
 Check(bool(receipt),"fixture qualification boundary written");
 std::cout<<"PASS checks="<<checks<<" real_by_definition_helper=true synthetic_registry=true synthetic_native_lookup=true live=false\n";return 0;
 }catch(const std::exception&error){std::cerr<<"FAIL "<<error.what()<<'\n';return 1;}}
