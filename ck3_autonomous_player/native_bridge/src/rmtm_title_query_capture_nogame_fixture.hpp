// SOURCE DRAFT ONLY: never compiled or executed in this work package.
// Single TU, candidate include directory first, canonical include second.
// Build two separate executables later, feature=1 and default/OFF respectively.
#include <windows.h>
#include "ck3_121003_rmtm_title26785313_raw_v1.hpp"
#include "ck3_121003_rmtm_title26785313_pins_v1.hpp"
#include <array>
#include <bit>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <string>
namespace c=xar::ck3_121003::build26785313;
namespace test {
struct Fixture;Fixture*active=nullptr;
void Need(bool x,const char*s){if(!x)throw std::runtime_error(s);}
template<class T>void Put(std::uintptr_t p,std::size_t n,const T&v){std::memcpy(reinterpret_cast<void*>(p+n),&v,sizeof(v));}
template<class T>T Get(std::uintptr_t p,std::size_t n){T v{};std::memcpy(&v,reinterpret_cast<void*>(p+n),sizeof(v));return v;}
struct Fixture {
 std::uintptr_t image=0,rows=0;
 alignas(16)std::array<unsigned char,0x400>title{},actor{},heir{};
 alignas(16)std::array<unsigned char,0x100>law{},storage{},title_storage{},game{},jomini{},players{};
 std::array<std::uintptr_t,3>law_rows{};std::array<std::uint32_t,2>successors{};
 std::array<unsigned char,64>title_rows{};
 c::ReadonlyBindings bindings{};c::RmtmTitleFrame267V1 frame{};c::RmtmTitleRequest267V1 request{};
 unsigned calls=0;bool throw_heir=false,mutate_after_heir=false,no_apply=false;
 std::uint32_t actor_id=0,heir_id=0xFE000001U,title_id=0xA5000001U;
 static void Commit(std::uintptr_t p,std::size_t n){const auto first=p&~std::uintptr_t{4095};const auto end=(p+n+4095)&~std::uintptr_t{4095};Need(VirtualAlloc(reinterpret_cast<void*>(first),end-first,MEM_COMMIT,PAGE_READWRITE)!=nullptr,"self-owned commit");}
 Fixture(){image=reinterpret_cast<std::uintptr_t>(VirtualAlloc(nullptr,c::kImageSize,MEM_RESERVE,PAGE_READWRITE));rows=reinterpret_cast<std::uintptr_t>(VirtualAlloc(nullptr,0x10000000ULL,MEM_RESERVE,PAGE_READWRITE));Need(image&&rows,"self-owned reserve");
  for(const auto&p:c::rmtm_title_pins::kPins){Commit(image+p.rva,p.bytes.size());std::memcpy(reinterpret_cast<void*>(image+p.rva),p.bytes.data(),p.bytes.size());}
  for(const auto&p:c::rmtm_title_pins::kPointers){Commit(image+p.slot,8);Put(image,p.slot,image+p.target);}
  for(auto r:{c::kGameStateSlotRva,c::kJominiStateSlotRva,c::kCharacterStorageSlotRva,std::uintptr_t{0x6A66648},std::uintptr_t{0x6A66638},std::uintptr_t{0x68A8930},std::uintptr_t{0x69487B0}})Commit(image+r,8);
  Reset();}
 ~Fixture(){active=nullptr;VirtualFree(reinterpret_cast<void*>(rows),0,MEM_RELEASE);VirtualFree(reinterpret_cast<void*>(image),0,MEM_RELEASE);}
 std::uintptr_t T()const{return reinterpret_cast<std::uintptr_t>(title.data());}
 std::uintptr_t A()const{return reinterpret_cast<std::uintptr_t>(actor.data());}
 std::uintptr_t H()const{return reinterpret_cast<std::uintptr_t>(heir.data());}
 std::uintptr_t L()const{return reinterpret_cast<std::uintptr_t>(law.data());}
 void Row(std::uint32_t id,std::uintptr_t object){const auto p=rows+static_cast<std::uintptr_t>(id&0xFFFFFFU)*16;Commit(p,16);Put(p,8,object);}
 void Reset(){active=this;calls=0;throw_heir=mutate_after_heir=no_apply=false;title.fill(0);actor.fill(0);heir.fill(0);law.fill(0);storage.fill(0);title_storage.fill(0);title_rows.fill(0);
  const auto g=reinterpret_cast<std::uintptr_t>(game.data()),j=reinterpret_cast<std::uintptr_t>(jomini.data()),st=reinterpret_cast<std::uintptr_t>(storage.data());
  Put(image,c::kGameStateSlotRva,g);Put(image,c::kJominiStateSlotRva,j);Put(image,c::kCharacterStorageSlotRva,st);Put(image,0x6A66648,reinterpret_cast<std::uintptr_t>(title_storage.data()));Put(image,0x6A66638,std::uintptr_t{1});Put(image,0x68A8930,std::uintptr_t{2});Put(image,0x69487B0,image+0x4CDD140);
  Put(st,0x20,rows);Put(st,0x2C,std::uint32_t{0x1000000});Row(actor_id,A());Row(heir_id,H());
  Put(reinterpret_cast<std::uintptr_t>(title_storage.data()),0x20,reinterpret_cast<std::uintptr_t>(title_rows.data()));Put(reinterpret_cast<std::uintptr_t>(title_storage.data()),0x2C,std::uint32_t{4});Put(reinterpret_cast<std::uintptr_t>(title_rows.data()),static_cast<std::size_t>(title_id&0xFFFFFFU)*16+8,T());
  Put(T(),0,image+0x4E21980);Put(T(),0x10,title_id);Put(T(),0x14,std::uint32_t{0x4C616E64});Put(T(),0x168,actor_id);
  for(auto p:{A(),H()}){Put(p,0x18,p==A()?actor_id:heir_id);Put(p,0x1C,std::uint32_t{0x43686172});Put(p,0x1C0,std::uintptr_t{3});Put(p,0x1D0,std::uintptr_t{0});}
  successors={heir_id,0xFFFFFFFFU};Put(T(),0x190,reinterpret_cast<std::uintptr_t>(successors.data()));Put(T(),0x198,std::int32_t{2});Put(T(),0x19C,std::int32_t{1});
  Put(L(),0,image+0x4FFAF78);Put(L(),0x10,std::uint32_t{0});Put(L(),0x38,std::uint32_t{0x4744624F});const char key[]="test_law";std::memcpy(law.data()+0x18,key,sizeof(key));Put(L(),0x28,std::uint64_t{8});Put(L(),0x30,std::uint64_t{15});
  law_rows={L(),0,0};Put(T(),0x270,reinterpret_cast<std::uintptr_t>(law_rows.data()));Put(T(),0x278,std::int32_t{3});Put(T(),0x27C,std::int32_t{1});
  frame={};frame.core.clock={};frame.core.clock.date_raw=53144328;frame.core.clock.speed=3;frame.core.clock.paused=true;frame.core.local_player_id=1;frame.core.map_ready=true;frame.core.has_played_character=true;frame.core.played_character_id=std::bit_cast<std::int32_t>(actor_id);frame.core.played_character_alive=true;
  frame.game=g;frame.jomini=j;frame.storage=st;frame.data=4;frame.players=reinterpret_cast<std::uintptr_t>(players.data());frame.player=5;frame.actor=A();frame.facts_verified=true;Put(g,0xA0,frame.data);Put(j,0x18,frame.players);
  bindings={};bindings.exact_image_admitted=true;bindings.module_base=image;bindings.core.enabled=true;bindings.core.game_state_slot=reinterpret_cast<void**>(image+c::kGameStateSlotRva);bindings.core.jomini_state_slot=reinterpret_cast<void**>(image+c::kJominiStateSlotRva);bindings.core.character_storage_slot=reinterpret_cast<void**>(image+c::kCharacterStorageSlotRva);bindings.core.get_local_player=[](void*)->void*{return reinterpret_cast<void*>(active->frame.player);};
  request={frame.core,title_id,static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count())+60000};
 }
 bool Read(c::RmtmTitleRaw267V1&out){std::string why;return c::ReadRmtmTitleRaw267V1(bindings,frame,request,GetTickCount64()+60000,out,why);}
};
HMODULE WINAPI Module(LPCWSTR){return reinterpret_cast<HMODULE>(active->image);}
const void* __fastcall Primary(const void*self){Need(self==reinterpret_cast<void*>(active->A()),"actual primary receiver");++active->calls;return reinterpret_cast<void*>(active->T());}
const void* __fastcall Holder(const void*self){Need(self==reinterpret_cast<void*>(active->T()),"actual holder receiver");++active->calls;return reinterpret_cast<void*>(Get<std::uint32_t>(active->T(),0x168)==0xFFFFFFFFU?std::uintptr_t{2}:active->A());}
const void* __fastcall Laws(const void*self){Need(self==reinterpret_cast<void*>(active->T()),"actual law receiver");++active->calls;return reinterpret_cast<void*>(active->T()+0x270);}
struct Scope16{std::uint32_t kind,reserved;std::uint64_t id;};
Scope16* __fastcall Heir(const void*self,Scope16*out,const Scope16*const*in){Need(self==reinterpret_cast<void*>(active->image+0x69487B0),"actual scope link receiver");Need(in&&*in&&(*in)->kind==5&&(*in)->id==active->title_id,"full Title scope zeroextension");++active->calls;if(active->throw_heir)RaiseException(0xE04D0001,0,0,nullptr);out->kind=4;out->id=Get<std::int32_t>(active->T(),0x19C)?active->successors[0]:0xFFFFFFFFU;if(active->mutate_after_heir)active->law[0x18]^=1;return out;}
std::uintptr_t Address(std::uintptr_t,std::uintptr_t r){switch(r){case 0x2D83960:return reinterpret_cast<std::uintptr_t>(&Primary);case 0x2704B40:return reinterpret_cast<std::uintptr_t>(&Holder);case 0xE18850:return reinterpret_cast<std::uintptr_t>(&Laws);case 0x1F27FC0:return reinterpret_cast<std::uintptr_t>(&Heir);default:std::abort();}}
}
namespace xar::ck3_1210 {
bool ReadCoreSnapshot(const CoreBindings&,CoreSnapshotPrefix&out)noexcept{out=test::active->frame.core;return true;}
void*ResolveCoreCharacter(const CoreBindings&,std::int32_t id)noexcept{const auto u=std::bit_cast<std::uint32_t>(id);return u==test::active->actor_id?reinterpret_cast<void*>(test::active->A()):u==test::active->heir_id?reinterpret_cast<void*>(test::active->H()):nullptr;}
}
namespace xar::ck3_121003::build26785313 {bool VerifyReadonlyImage(std::uintptr_t i)noexcept{return test::active&&i==test::active->image;}}
#define GetModuleHandleW test::Module
#define XAR_RMTM_TITLE_CALL_ADDRESS(image,rva) test::Address(image,rva)
#include "ck3_121003_rmtm_title26785313_raw_v1.cpp"
#undef GetModuleHandleW
int main(){try{test::Fixture f;c::RmtmTitleRaw267V1 out;
#if defined(XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1) && XAR_CK3_ENABLE_121003_26785313_RMTM_TITLE_V1
 test::Need(f.Read(out)&&out.source.sampled_twice&&out.source.full_title_id==f.title_id&&out.source.engine_current_heir->full_id==f.heir_id,"complete baseline/high generation");

 f.Reset();std::array<char,64>long_key{};const char exact_law[]="single_heir_succession_law";std::memcpy(long_key.data(),exact_law,sizeof(exact_law));test::Put(f.L(),0x18,reinterpret_cast<std::uintptr_t>(long_key.data()));test::Put(f.L(),0x28,std::uint64_t{sizeof(exact_law)-1});test::Put(f.L(),0x30,std::uint64_t{63});test::Need(f.Read(out)&&out.source.physical_own_laws.at(0).key==exact_law,"original long succession key out-of-line CString");
 const auto saved_title=f.title_id;f.title_id=0;f.Reset();test::Need(f.Read(out)&&out.source.full_title_id==0,"full Title ID zero is legal");f.title_id=saved_title;
 f.Reset();test::Put(f.T(),0x27C,std::int32_t{0});test::Need(f.Read(out)&&out.source.physical_own_laws.empty(),"known EMPTY not unavailable");
 f.Reset();test::Put(f.T(),0x19C,std::int32_t{0});test::Need(f.Read(out)&&!out.source.engine_current_heir,"official none current_heir");
 f.Reset();test::Put(f.T(),0x168,std::uint32_t{0xFFFFFFFF});test::Need(f.Read(out)&&!out.source.holder,"official none holder");
 f.Reset();test::Put(f.T(),0x10,f.title_id^0x01000000U);test::Need(!f.Read(out)&&!out.entered,"same short index wrong generation before entry");
 f.Reset();test::Put(f.T(),0x14,std::uint32_t{0});test::Need(!f.Read(out),"wrong Title magic");
 f.Reset();test::Put(f.L(),0,std::uintptr_t{0});test::Need(!f.Read(out),"wrong actual Law type");
 f.Reset();test::Put(f.L(),0x38,std::uint32_t{0});test::Need(!f.Read(out),"wrong Law database magic");
 f.Reset();test::Put(f.T(),0x27C,std::int32_t{4});test::Need(!f.Read(out),"count exceeds capacity");
 f.Reset();f.law_rows[1]=f.L();test::Put(f.T(),0x27C,std::int32_t{2});test::Need(!f.Read(out),"duplicate row not complete semantic source");
 f.Reset();f.mutate_after_heir=true;test::Need(!f.Read(out),"full Law header/value drift between samples");
 f.Reset();f.throw_heir=true;test::Need(!f.Read(out)&&!out.cleanup_known,"native SEH read unknown stays unknown");
 f.Reset();f.request.deadline_unix_ms=1;test::Need(!f.Read(out)&&f.calls==0,"original expired no native entry");
 f.Reset();f.request.expected_full_title_id=0xFFFFFFFFU;test::Need(!f.Read(out)&&f.calls==0,"invalid fullTitle not a selector");
 f.actor_id=0xFFFFFFFEU;f.Reset();test::Need(f.Read(out)&&out.source.holder->full_id==0xFFFFFFFEU,"full signed -2 with sparse owned rows");
#else
 test::Need(!f.Read(out)&&f.calls==0&&out.cleanup_known,"default OFF no native call");
#endif
 return 0;}catch(...){return 1;}}
