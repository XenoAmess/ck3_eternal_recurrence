// Source-only self-owned simulation; never an actual CK3 ABI/live qualification.
#define XAR_FRONTEND_SEED_SELF_OWNED_TEST 1
#include "ck3_121003_frontend_seed26785313_test_fixture.hpp"
#include <iostream>
#include <limits>
#include <optional>
#include <unordered_set>
#include <vector>

namespace raw {
using namespace xar::ck3_121003::build26785313;
using Action=FrontendMenuAction267V1;using Route=FrontendMenuRoute267V1;
bool Copy(const void*p,void*out,std::size_t n)noexcept{
 if(!p||!out||!n)return false;
 __try{std::memcpy(out,p,n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
template<class T>bool At(std::uintptr_t p,std::size_t off,T&out)noexcept{
 constexpr auto max=(std::numeric_limits<std::uintptr_t>::max)();
 return p&&off<=max-p&&sizeof(T)-1<=max-p-off&&Copy(reinterpret_cast<const void*>(p+off),&out,sizeof(out));
}
#define XAR_FRONTEND_SEED_CALL_ADDRESS(image,rva) ::xar::ck3_121003::build26785313::frontend_seed_test::CallAddress((image),(rva))
#define GetTickCount64 ::xar::ck3_121003::build26785313::frontend_seed_test::MockTick
#ifndef XAR_FRONTEND_SEED_NATIVE_TEST_INC
#define XAR_FRONTEND_SEED_NATIVE_TEST_INC "ck3_121003_frontend_seed26785313_native_v1.inc"
#endif
#include XAR_FRONTEND_SEED_NATIVE_TEST_INC
#undef GetTickCount64
#undef XAR_FRONTEND_SEED_CALL_ADDRESS
}
namespace {
using namespace xar::ck3_121003::build26785313;
using namespace frontend_seed_test;
using Action=FrontendMenuAction267V1;using Route=FrontendMenuRoute267V1;
bool Read(FakeImage&f,Route route,raw::SeedSnapshot267V1&out){return raw::ReadSeed267V1(f.image,f.application,f.context,route==Route::main_menu?f.main_root:f.book_root,route,out);}
raw::SeedSnapshot267V1 Book(FakeImage&f){
 f.Book();raw::SeedSnapshot267V1 s;
 Require(Read(f,Route::bookmarks,s),"actual raw reader constructs complete fake-owned bookmark source");return s;
}
void NoEffects(const FakeImage&f){Require(f.Effects()==0&&f.calls.layout_errors==0,"readonly refusal never calls action or violates own typed stub ABI");}
void RejectRead(FakeImage&f){
 raw::SeedSnapshot267V1 out;out.application=f.application;out.target_character=f.characters;
 Require(!Read(f,Route::bookmarks,out)&&out.application==0&&out.target_character==0&&out.bookmarks.empty(),"invalid raw source returns no stale partial snapshot");NoEffects(f);
}
bool Invoke(FakeImage&f,Action a,const raw::SeedSnapshot267V1&s,std::uint64_t wall=0,std::uint64_t mono=100){
 return raw::InvokeSeed267V1(f.image,a,s,&f.world,wall?wall:WallFuture(),mono);
}
}
int main(){
 try {
  FakeImage f;raw::SeedSnapshot267V1 s;
  Require(Read(f,Route::main_menu,s)&&s.main==f.main&&s.setup==f.setup&&s.main_root==f.main_root&&!s.complete&&!s.native_can_start,"main no-world controller exact back-links");NoEffects(f);
  f.Reset();s=Book(f);
  Require(s.complete&&s.groups.size()==1&&s.bookmarks.size()==1&&s.bookmarks[0].roles.size()==1&&
      s.target_group==f.group&&s.target_bookmark==f.bookmark&&s.target_character==f.characters&&s.target_index==0&&
      s.selected_group==f.group&&s.selected_bookmark==f.bookmark&&s.selected_index==0&&s.native_can_start==true,
      "CPdxArray8 groups/bookmarks plus contiguous0x1A0 role use real included layouts");NoEffects(f);
  f.Reset();f.Book();f.can_start=false;
  Require(Read(f,Route::bookmarks,s)&&s.complete&&s.native_can_start==false&&f.calls.can==1,"CanStart false is actual clean readonly DATA, never caller permission");NoEffects(f);
  f.Reset();f.Book();f.Put(f.setup,0x128,std::int32_t{-1});
  Require(Read(f,Route::bookmarks,s)&&s.complete&&!s.native_can_start&&f.calls.can==0,"unselected role retains complete model without fabricated CanStart");NoEffects(f);
  f.Reset();f.Book();f.throw_rva=0x11320B0;RejectRead(f);

  // Each case changes actual owned bytes, never a caller-provided available flag.
  for(unsigned which=0;which<25;++which){
   f.Reset();f.Book();
   switch(which){
    case 0:{const auto&p=frontend_seed_pins::kPins.front();f.Put(f.image,p.rva,static_cast<std::uint8_t>(p.bytes.front()^1));break;}
    case 1:f.Put(f.owner,0,std::uintptr_t{0});break;
    case 2:f.Put(f.image+0x51C8AF8,0,std::uint32_t{0});break;
    case 3:f.Put(f.owner,0x18,f.wrapper);break;
    case 4:f.Put(f.wrapper,8,f.owner);break;
    case 5:f.Put(f.main+0x10,0,f.image+0x4C620D8);break;
    case 6:f.Put(f.setup+0x10,0,f.image+0x4B9FB58);break;
    case 7:f.Put(f.main,0x68,f.main_root);break;
    case 8:f.Put(f.setup,0x68,f.book_root);break;
    case 9:f.Put(f.handler,8,std::int32_t{3});break;
    case 10:f.Put(f.setup,0xC8,std::int32_t{0});break;
    case 11:f.Put(f.setup,0xCC,std::int32_t{0});break;
    case 12:f.Put(f.setup,0xC8,std::int32_t{65537});break;
    case 13:f.Group(f.other_group,"bm_group_1066",4);f.Put(f.group_rows,8,f.other_group);f.Put(f.setup,0xC8,std::int32_t{2});f.Put(f.setup,0xCC,std::int32_t{2});break;
    case 14:f.Put(f.group_rows,8,f.group);f.Put(f.setup,0xC8,std::int32_t{2});f.Put(f.setup,0xCC,std::int32_t{2});break;
    case 15:f.Bookmark(f.other_bookmark,kFrontendRobertBookmark267V1,5,f.group);f.Put(f.bookmark_rows,8,f.other_bookmark);f.Put(f.database,0x58,std::int32_t{2});f.Put(f.database,0x5C,std::int32_t{2});break;
    case 16:f.Character(f.characters+0x1A0,kFrontendRobertCharacter267V1,6,f.bookmark);f.Put(f.bookmark,0x110,std::int32_t{2});f.Put(f.bookmark,0x114,std::int32_t{2});break;
    case 17:f.Put(f.characters,0x130,f.other_bookmark);break;
    case 18:f.Key(f.characters,8,"not_robert",7);break;
    case 19:f.Put(f.bookmark,0x40,std::int32_t{53144352});break;
    case 20:f.Put(f.bookmark,0xF8,f.other_group);break;
    case 21:f.Put(f.bookmark,0x100,std::uint8_t{2});break;
    case 22:f.Put(f.setup,0x128,std::int32_t{1});break;
    case 23:f.Put(f.setup,0x130,std::uint8_t{2});break;
    case 24:f.Put(f.group,0x28,std::uint64_t{129});break;
   }
   RejectRead(f);
  }
  f.Reset();f.Book();
  Require(!raw::ReadSeed267V1(f.image,f.application,f.context,f.main_root,Route::bookmarks,s),"actual route root mismatch refuses");NoEffects(f);

  f.Reset();Require(Read(f,Route::main_menu,s),"actual main before one OnNewGame");
  Require(Invoke(f,Action::open_bookmarks,s)&&f.calls.open==1&&f.calls.layout_errors==0&&f.Get<std::int32_t>(f.handler,8)==4,"fixed OnNewGame calls only actual bound main view");
  f.Reset();f.Book();f.Put(f.setup,0xD8,f.other_group);s=Book(f);
  Require(Invoke(f,Action::select_1066_bookmark,s)&&f.calls.group==1&&f.calls.bookmark==1&&f.Get<std::uintptr_t>(f.setup,0xD8)==f.group&&f.Get<std::uintptr_t>(f.setup,0x120)==f.bookmark,"group setter then exact bookmark setter typed arguments");
  Require(f.calls.layout_errors==0,"group/bookmark exact ABI");
  f.Reset();s=Book(f);
  Require(Invoke(f,Action::select_1066_bookmark,s)&&f.calls.group==0&&f.calls.bookmark==1,"already selected group does not add redundant group call");
  f.Reset();f.Book();f.Put(f.setup,0x128,std::int32_t{-1});s=Book(f);
  Require(Invoke(f,Action::select_robert_1066,s)&&f.calls.character==1&&f.Get<std::int32_t>(f.setup,0x128)==0&&f.calls.layout_errors==0,"fixed character setter receives actual contiguous Robert object");
  f.Reset();s=Book(f);
  Require(Invoke(f,Action::start_robert_1066,s)&&f.calls.start_game==1&&f.calls.on_start==1&&f.calls.layout_errors==0,"StartGame prepares then OnStart exactly once; not an actual world-load proof");

  for(unsigned which=0;which<5;++which){
   f.Reset();s=Book(f);std::uint64_t wall=WallFuture(),mono=100;
   switch(which){case 0:wall=1;break;case 1:mock_tick=100;break;case 2:f.world=reinterpret_cast<void*>(f.application);break;
    case 3:f.Put(f.application,0x78,f.other_group);break;case 4:f.Put(f.wrapper,8,f.owner);break;}
   Require(!raw::InvokeSeed267V1(f.image,Action::start_robert_1066,s,&f.world,wall,mono),"expired/world/owner drift pre-entry refusal");NoEffects(f);
  }
  // False after a callback entered cannot be called zero-dispatch or retried.
  f.Reset();f.Book();f.Put(f.setup,0xD8,f.other_group);s=Book(f);f.ignore_group=true;
  Require(!Invoke(f,Action::select_1066_bookmark,s)&&f.calls.group==1&&f.calls.bookmark==0,"group postcondition failure stops second callback; first may have effects");
  f.Reset();s=Book(f);f.ignore_start_game=true;
  Require(!Invoke(f,Action::start_robert_1066,s)&&f.calls.start_game==1&&f.calls.on_start==0,"prepare-only StartGame must not be mistaken for actual OnStart");
  for(unsigned which=0;which<5;++which){
   f.Reset();s=Book(f);
   switch(which){
    case 0:f.after_start_game=[](FakeImage*x){x->world=reinterpret_cast<void*>(x->application);};break;
    case 1:f.after_start_game=[](FakeImage*x){x->Put(x->application,0x78,x->other_group);};break;
    case 2:f.after_start_game=[](FakeImage*){mock_tick=100;};break;
    case 3:f.throw_rva=0x1130E90;break;
    case 4:f.throw_rva=0x11315F0;break;
   }
   Require(!Invoke(f,Action::start_robert_1066,s)&&f.calls.start_game==1&&f.calls.on_start==(which==4?1u:0u)&&f.calls.layout_errors==0,
       "post-entry world/owner/deadline drift or SEH remains possible-effect uncertainty without another OnStart");
  }
  std::cout<<"NoGame owned raw frontend layout and typed callback Source tests complete; no CK3 ABI/live/product qualification\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
