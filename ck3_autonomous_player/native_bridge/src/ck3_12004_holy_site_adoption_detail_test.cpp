// Owned synthetic typed storage and callbacks, production reader+full serializer.
// No CK3 process, original game function or desktop operation executes.
#include "xar_bridge/ck3_12004_holy_site_adoption_detail.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
namespace h=xar::ck3_12004::religion::holy_site;
namespace{
unsigned checks=0;
void Check(bool v,const char*why){++checks;if(!v)throw std::runtime_error(why);}
template<std::size_t N>using Bytes=std::array<std::byte,N>;
template<class B,class T>void Put(B&b,std::size_t o,T v){std::memcpy(b.data()+o,&v,sizeof(v));}
struct Fixture{
 static constexpr std::uintptr_t base=0x140000000;
 static constexpr std::uint32_t actor=0x03000004,site_id=0x81000002,token=44;
 Bytes<0x28>owner{};Bytes<0x90>gfx{};Bytes<0x1C0>handler{};Bytes<0x250>detail{};
 Bytes<0x40>controller{},context{},definition{};Bytes<128>entries{};Bytes<48>dict{};
 Bytes<0x30>store{};Bytes<0x50>slots{};Bytes<0x18>site{};Bytes<0x20>settings{};
 std::array<Bytes<24>,3>cols{};
 void*storeptr=store.data();std::uint32_t actual_actor=actor,selected_token=token;
 std::string key="adopt_holy_site_decision",reason="native fixture reason";
 bool legal=false;unsigned confirms=0,reasons=0,destroys=0;
 Fixture(){
  Put(owner,0x10,gfx.data());Put(gfx,0x88,handler.data());Put(handler,0x1B8,detail.data());
  Put(detail,0,base+0x455D4F8);Put(detail,0xA0,handler.data());Put(detail,0x60,site.data());
  Put(detail,0xD0,definition.data());Put(detail,0xD8,actor);Put(detail,0xDC,std::int32_t{-1});Put(detail,0x248,controller.data());
  Put(definition,0,base+0x48BD150);Put(definition,0x18,key.c_str());
  Put(definition,0x28,static_cast<std::uint64_t>(key.size()));Put(definition,0x30,std::uint64_t{31});Put(definition,0x38,std::uint32_t{0x4744624F});
  Put(controller,0,base+0x45A08F0);Put(controller,8,detail.data());Put(controller,0x10,handler.data());Put(controller,0x18,context.data());
  Put(controller,0x20,entries.data());Put(controller,0x28,std::int32_t{2});Put(controller,0x2C,std::int32_t{2});Put(controller,0x38,std::int32_t{1});
  Put(context,0x28,dict.data());Put(context,0x30,std::int32_t{2});Put(context,0x34,std::int32_t{2});
  Put(dict,0,std::uint32_t{99});Scope(dict,8,0x82000003);Put(dict,24,token);Scope(dict,32,site_id);
  Scope(entries,0,0x82000003);Scope(entries,64,site_id);entries[64+0x38]=std::byte{1};
  // Different padding must not make native semantic equality fail.
  Put(entries,64+4,std::uint32_t{0xA5A5A5A5});Put(dict,32+4,std::uint32_t{0x5A5A5A5A});
  Put(store,0x20,slots.data());Put(store,0x2C,std::uint32_t{5});Put(slots,2*16+8,site.data());
  Put(site,0x10,site_id);Put(site,0x14,std::uint32_t{0x486F5374});
  const std::array<std::uint32_t,3>td{0x5795050,0x5586B90,0x5802AC0};
  for(std::size_t i=0;i<3;++i){Put(cols[i],0,std::uint32_t{1});Put(cols[i],12,td[i]);Put(cols[i],20,static_cast<std::uint32_t>(0x1000+i*0x100));}
 }
 template<class B>static void Scope(B&b,std::size_t o,std::uint32_t id){Put(b,o,std::uint16_t{23});Put(b,o+2,std::uint16_t{0});Put(b,o+8,static_cast<std::uint64_t>(id));}
};
Fixture*f=nullptr;
struct Code{std::uintptr_t rva;std::string_view hex;};
constexpr Code code[]{
 {0x1471140,"33d2e9c90a0000"},{0x1471C10,"48895c240848896c24104889742418574883ec60488bea488bf140b701488b89"},
 {0x1471190,"40534883ec60488bd933d2e8700a000084c0745a488d542420488bcbe80f0b00"},
 {0x1471CC0,"48895c2410555657415641574883ec30488bfa488be94533ff44897c2420448b"},
 {0x18D1890,"48895c2408574883ec304c8b4a28488bf9486352348b0541aa47044c8d04524b"},
 {0x26C3F10,"40534883ec20488bda4885c90f84c70000006683391775058b5108eb05baffff"},
 {0xA75D00,"48895c2408564883ec20be1000000065488b042558000000488b188b041e3905"},
 {0x1471150,"4889542410534883ec30488bda33c0894424204889024889421048c742180f00"},
 {0x856050,"40534883ec20488b5118488bd94883fa10722c488b0948ffc24881fa00100000"}};
bool Copy(void*,const void*p,void*out,std::size_t n)noexcept{
 const auto address=reinterpret_cast<std::uintptr_t>(p);
 for(const auto&c:code)if(address==Fixture::base+c.rva){
  if(n>c.hex.size()/2)return false;
  const auto digit=[](char v){return v>='0'&&v<='9'?v-'0':v-'a'+10;};
  for(std::size_t i=0;i<n;++i)static_cast<unsigned char*>(out)[i]=static_cast<unsigned char>((digit(c.hex[2*i])<<4)|digit(c.hex[2*i+1]));return true;
 }
 const std::array<std::uintptr_t,3>vt{0x455D4F8,0x48BD150,0x45A08F0};
 for(std::size_t i=0;i<3;++i){
  if(address==Fixture::base+vt[i]-8&&n==8){const auto col=Fixture::base+0x1000+i*0x100;std::memcpy(out,&col,8);return true;}
  const auto start=Fixture::base+0x1000+i*0x100;
  if(address>=start&&address+n<=start+24){std::memcpy(out,f->cols[i].data()+(address-start),n);return true;}
 }
 if(!p)return false;std::memcpy(out,p,n);return true;
}
bool __fastcall Can(void*p){Check(p==f->detail.data(),"CanConfirm receives actual fixture-owned detail");return f->legal;}
void __fastcall Confirm(void*p){Check(p==f->detail.data(),"Confirm receives actual fixture-owned detail");++f->confirms;}
void*__fastcall Settings(){return f->settings.data();}
void*__fastcall Reason(void*p,void*out){Check(p==f->detail.data(),"reason receives actual detail");++f->reasons;
 std::memset(out,0,32);const auto text=f->reason.c_str();const auto size=static_cast<std::uint64_t>(f->reason.size());
 std::memcpy(out,&text,8);std::memcpy(static_cast<std::byte*>(out)+16,&size,8);const std::uint64_t cap=31;std::memcpy(static_cast<std::byte*>(out)+24,&cap,8);return out;}
void __fastcall Destroy(void*){++f->destroys;}
h::AdoptionDetailBindings Bind(Fixture&v){f=&v;h::AdoptionDetailBindings b{};b.enabled=true;b.image_base=Fixture::base;
 b.holy_site_storage=&v.storeptr;b.selected_item_token=&v.selected_token;b.current_actor_reference=&v.actual_actor;b.read_memory=&Copy;
 b.can_confirm=&Can;b.confirm=&Confirm;b.requirements_settings=&Settings;b.confirm_tooltip=&Reason;b.destroy_string=&Destroy;return b;}
xar::ck3_12002::religion::Context Frame(){xar::ck3_12002::religion::Context c{};c.available=true;c.capture_epoch=17;c.date_raw=53175816;c.played_character_id=Fixture::actor;return c;}
void Save(const std::filesystem::path&d,const char*name,const h::AdoptionDetailSnapshot&s){std::ofstream out(d/name);out<<h::SerializeHolySiteAdoptionDetailCommand12004(s,"g2-read-adoption-fixture",701,s.date_raw)<<'\n';Check(bool(out),"whole native command_result written");}
}
int main(int argc,char**argv){try{
 Check(argc==2,"output directory required");const std::filesystem::path d(argv[1]);std::filesystem::create_directories(d);
 Fixture v;auto b=Bind(v);const auto c=Frame();h::AdoptionDetailSnapshot s{};
 Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.available&&!s.native_can_confirm&&
  s.parameter_and_selection_match&&s.selected_index==1&&s.parameter_holy_site_id==Fixture::site_id,"native observed false, second actual entry and padding-independent parameter identity");
 Check(s.confirm_tooltip_available&&s.confirm_tooltip==v.reason&&v.reasons==v.destroys,"actual callback reason copied and original destroy paired");Save(d,"native-false.json",s);
 bool attempted=true;Check(!h::ConfirmHolySiteAdoptionDetail12004(b,s,attempted)&&!attempted&&v.confirms==0,"observed false cannot invoke original Confirm");
 v.legal=true;Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_can_confirm,"native true stays distinct from unavailable");Save(d,"native-true.json",s);
 attempted=false;Check(h::ConfirmHolySiteAdoptionDetail12004(b,s,attempted)&&attempted&&v.confirms==1,"one authorized original Confirm callback after fresh full binding");
 v.settings[0x10]=std::byte{1};Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_can_confirm&&s.bypass_requirements_raw==1,"engine true with requirements bypass remains observed separately");Save(d,"bypass-enabled.json",s);
 attempted=true;Check(!h::ConfirmHolySiteAdoptionDetail12004(b,s,attempted)&&!attempted&&v.confirms==1,"bypass never qualifies ordinary original Confirm");v.settings[0x10]=std::byte{0};
 b.requirements_settings=nullptr;Check(h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&s.native_can_confirm&&!s.bypass_requirements_observed,"unavailable bypass setting does not invent regular native legality");Save(d,"bypass-unavailable.json",s);
 attempted=true;Check(!h::ConfirmHolySiteAdoptionDetail12004(b,s,attempted)&&!attempted&&v.confirms==1,"unknown bypass setting blocks original Confirm");b.requirements_settings=&Settings;
 Put(v.dict,32+8,static_cast<std::uint64_t>(Fixture::site_id)+(1ULL<<32));
 Check(!h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s)&&!s.available,"upper payload bits cannot alias a valid HolySite full ID");Save(d,"parameter-mismatch.json",s);
 Fixture::Scope(v.dict,32,Fixture::site_id);Put(v.controller,0x38,std::int32_t{0});v.entries[0x38]=std::byte{1};
 Check(!h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s),"fallback first entry does not prove requested target");Save(d,"fallback-first-rejected.json",s);
 Put(v.controller,0x38,std::int32_t{1});v.actual_actor=Fixture::actor+1;
 Check(!h::ReadHolySiteAdoptionDetail12004(b,v.owner.data(),c,Fixture::site_id,s),"current-global actor mismatch blocks binding");
 Check(!h::BindHolySiteAdoptionDetailImage12004(Fixture::base,"wrong-exe").enabled,"foreign source image rejected");
 std::cout<<"PASS checks="<<checks<<" actual_reader=true actual_serializer=true synthetic_storage=true synthetic_callbacks=true live=false\n";return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
