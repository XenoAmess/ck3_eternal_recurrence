#include "xar_bridge/character_knight_effectiveness12004.hpp"
#include "xar_bridge/character_knight_effectiveness12004_owned_string.hpp"
#include "xar_bridge/character_skill_effect12004_mailbox.hpp"
#include <windows.h>
#include <cassert>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <vector>
#ifdef NDEBUG
#error Assertions are required for this owned-memory fixture.
#endif
namespace c=xar::bridge::character_skill_effect12004;
namespace m=xar::ck3_12004::character_skill_effects;
namespace {
constexpr std::uint32_t player=0x01000001U,second=0x01000002U;
struct Owned {
  std::map<std::uintptr_t,std::vector<unsigned char>> blocks;
  c::Frame frame{7,10660101,player,true,true,true};
  unsigned calls=0;bool fail=false,change_text=false,change_id=false;
  std::int64_t player_raw=125000,second_raw=130000;
  std::string player_text="Player source\n+25%",second_text="Second actor source\n+30%";
  void block(std::uintptr_t at,std::size_t n){blocks[at].resize(n);}
  template<class T>void put(std::uintptr_t at,T value){
    for(auto &[base,bytes]:blocks)if(at>=base&&at-base<=bytes.size()&&sizeof(T)<=bytes.size()-(at-base)){
      std::memcpy(bytes.data()+at-base,&value,sizeof(T));return;
    }assert(false);
  }
  Owned(){
    block(0x100000+0x5C67568,8);block(0x100000+0x5D1E2F8,8);block(0x100000+0x5D1E300,8);
    block(0x2000,0x40);block(0x3000,0x40);block(0x4000,0x40);
    put<std::uintptr_t>(0x100000+0x5C67568,0x2000);put<std::uintptr_t>(0x2020,0x3000);put<std::uint32_t>(0x202C,3);
    put<std::uintptr_t>(0x3018,0x5000);put<std::uintptr_t>(0x3028,0x6000);
    for(auto actor:{std::uintptr_t{0x5000},std::uintptr_t{0x6000}}){
      block(actor,0x200);block(actor+0x2000,0x300);block(actor+0x4000,0x100);
      put<std::uint32_t>(actor+0x18,actor==0x5000?player:second);put<std::uint32_t>(actor+0x1C,0x43686172U);
      put<std::uintptr_t>(actor+0x1B0,actor+0x2000);put<std::uintptr_t>(actor+0x2258,actor+0x4000);
      put<std::uintptr_t>(actor+0x4008,actor);put<std::uint32_t>(actor+0xB4,1);
    }
    block(0xB000,0x500);block(0xC000,0x40);block(0xD000,0x40);block(0xE000,0x40);
    put<std::uintptr_t>(0x100000+0x5D1E2F8,0xC000);put<std::uintptr_t>(0xC020,0xD000);put<std::uint32_t>(0xC02C,2);
    put<std::uintptr_t>(0xD018,0xB000);put<std::uint32_t>(0xB008,1);put<std::uint32_t>(0xB4B8,1);
    block(0xF000,0x40);put<std::uintptr_t>(0x100000+0x5D1E300,0xE000);
    put<std::uintptr_t>(0xE020,0xF000);put<std::uint32_t>(0xE02C,2);put<std::uintptr_t>(0xF018,0x11000);
    block(0x11000,0x20);put<std::uint32_t>(0x11008,1);
  }
  static bool memory(void *opaque,std::uintptr_t at,void *out,std::size_t n) noexcept {
    auto &s=*static_cast<Owned *>(opaque);
    for(const auto &[base,bytes]:s.blocks)if(at>=base&&at-base<=bytes.size()&&n<=bytes.size()-(at-base)){
      std::memcpy(out,bytes.data()+at-base,n);return true;
    }return false;
  }
  static bool read_frame(void *opaque,c::Frame &out) noexcept{out=static_cast<Owned *>(opaque)->frame;return true;}
  static bool knight(void *opaque,std::uintptr_t actor,std::int64_t &raw,std::string &text) noexcept{
    auto &s=*static_cast<Owned *>(opaque);++s.calls;
    if(s.fail)return false;
    try{
      if(actor==0x5000){raw=s.player_raw;text=s.player_text;}
      else if(actor==0x6000){raw=s.second_raw;text=s.second_text;}
      else return false;
      if(s.change_text&&s.calls==2)text+=" changed";
      if(s.change_id&&s.calls==1)s.put<std::uint32_t>(0x5018,0x02000001U);
      return true;
    }catch(...){return false;}
  }
  c::KnightEnvironment env(){
    c::KnightEnvironment out{};out.actor.enabled=true;out.actor.executable_sha256=c::kExeSha;
    out.actor.image_base=0x100000;out.actor.context=this;out.actor.read_memory=&memory;
    out.actor.read_frame=&read_frame;out.actor.callback_provenance=c::CallbackProvenance::owned_fixture;
    out.actor.allow_owned_fixture=true;out.read_knight=&knight;return out;
  }
};
bool read(Owned &s,std::uint32_t id,c::KnightResult &out){return c::ReadKnightEffectiveness(s.env(),{s.frame,id},out);}
void absent(const c::KnightResult &v){
  assert(!v.available&&!v.two_pass_stable&&!v.own_actor_context_verified&&!v.rite_id&&!v.faith_id);
  assert(!v.knight_effectiveness_raw&&!v.actual_knight_effectiveness_breakdown&&!v.selected_site_contribution_raw);
  assert(v.callback_provenance==c::CallbackProvenance::unavailable&&!v.unavailable_reason.empty());
}
m::Query authored(bool available,std::uint32_t id){
  // Deliberately AUTHORED DTO, separate from the owned callback result. The
  // production serializer is real; this is not native getter/callee evidence.
  m::Query q{};q.knight_query=true;q.completed=true;q.invocations=1;q.expected_revision=7;
  q.executable_sha256=c::kExeSha;q.character_id=id;q.expected_snapshot.date_raw=10660101;
  q.expected_snapshot.played_character_id=static_cast<std::int32_t>(player);
  auto &v=q.knight_observation;v.frame={7,10660101,player,true,true,true};v.character_id=id;
  if(available){v.available=true;v.two_pass_stable=true;v.own_actor_context_verified=true;
    v.unavailable_reason.clear();v.rite_id=1;v.faith_id=1;v.knight_effectiveness_raw=id==player?125000:130000;
    v.actual_knight_effectiveness_breakdown=id==player?"Player source\n+25%":"Second actor source\n+30%";
    v.callback_provenance=c::CallbackProvenance::exact4_native;
  }else v.unavailable_reason="native_knight_own_actor_context_or_source_unavailable";
  return q;
}
} // namespace
int main(int argc,char **argv){
  // The actual pure string helper owns copy/bound/cleanup control flow. These
  // callbacks touch only owned storage and do not replace any native symbol.
  struct OwnedString {std::array<unsigned char,16> storage{};std::uint64_t size=0,capacity=15;};
  static_assert(sizeof(OwnedString)==32);
  for(const unsigned scene:{0U,1U,2U,3U,4U}){
    OwnedString text{};text.storage[0]='x';text.size=scene==2?c::kMaxBreakdownBytes+1:1;
    unsigned destroys=0;std::string copy="stale";
    const bool ok=c::knight_string_detail::CopyThenDestroy(scene!=1,text,copy,
      [](std::uintptr_t p,void *out,std::size_t n) noexcept{std::memcpy(out,reinterpret_cast<void *>(p),n);return true;},
      [scene](std::string_view) noexcept{return scene!=3;},
      [&destroys,scene](OwnedString &) noexcept{++destroys;return scene!=4;});
    assert(destroys==1);assert(ok==(scene==0));assert(ok?copy=="x":copy.empty());
  }
  // a02: real owned UTF8 bytes cover the production helper's long-string
  // pointer branch, copy-before-cleanup, unsafe/copyfalse/bounds/partial call.
  // These callbacks never substitute a native symbol or touch game memory.
  constexpr char expected[]="mecca: \xE9\xBA\xA6\xE5\x8A\xA0 original source +4%";
  constexpr std::size_t length=sizeof(expected)-1;
  static_assert(length>16&&length<64);
  const auto expected_view=std::string_view(expected,length);
  for(const unsigned scene:{0U,1U,2U,3U,4U,5U}){
    std::array<unsigned char,64> owned{};std::memcpy(owned.data(),expected,length);
    OwnedString text{};text.size=length;text.capacity=owned.size();
    const auto actual=reinterpret_cast<std::uintptr_t>(owned.data());
    const std::uintptr_t pointer=scene==2?0:scene==3?~std::uintptr_t{0}:actual;
    std::memcpy(text.storage.data(),&pointer,sizeof(pointer));
    if(scene==4)text.capacity=16; // size exceeds capacity, before any copy.
    unsigned destroys=0,copies=0;std::string copy="stale";
    const bool ok=c::knight_string_detail::CopyThenDestroy(scene!=5,text,copy,
      [scene,actual,&copies](std::uintptr_t p,void *to,std::size_t n) noexcept{
        ++copies;if(scene==1||p!=actual||n!=length)return false;
        std::memcpy(to,reinterpret_cast<const void *>(p),n);return true;
      },
      [expected_view](std::string_view value) noexcept{return value==expected_view;},
      [&owned,&destroys,&copy,scene,expected_view](OwnedString &) noexcept{
        ++destroys;if(scene==0)assert(copy==expected_view);
        owned.fill('x');return true;
      });
    assert(destroys==1&&ok==(scene==0));
    assert(scene==0?copy==expected_view:copy.empty());
    assert(copies==((scene==0||scene==1||scene==3)?1U:0U));
    assert(owned[0]=='x'); // Successful copy survives source cleanup mutation.
  }
  c::KnightResult v{};
  {Owned s;assert(read(s,player,v)&&s.calls==2&&v.character_id==player&&*v.knight_effectiveness_raw==125000);assert(v.callback_provenance==c::CallbackProvenance::owned_fixture);}
  {Owned s;assert(read(s,second,v)&&v.character_id==second&&*v.knight_effectiveness_raw==130000&&*v.actual_knight_effectiveness_breakdown==s.second_text);}
  {Owned s;assert(!read(s,0x02000001U,v)&&s.calls==0);absent(v);}
  {Owned s;s.put<std::uintptr_t>(0x7258,0);assert(!read(s,player,v)&&s.calls==0);absent(v);}
  {Owned s;s.put<std::uintptr_t>(0x9008,0x6000);assert(!read(s,player,v)&&s.calls==0);absent(v);}
  {Owned s;s.fail=true;assert(!read(s,player,v));absent(v);}
  {Owned s;s.change_id=true;assert(!read(s,player,v));absent(v);}
  {Owned s;s.change_text=true;assert(!read(s,player,v));absent(v);}
  {Owned s;auto e=s.env();auto expected=s.frame;expected.revision=8;assert(!c::ReadKnightEffectiveness(e,{expected,player},v)&&s.calls==0);absent(v);}
  {Owned s;auto e=s.env();e.actor.executable_sha256="wrong";assert(!c::ReadKnightEffectiveness(e,{s.frame,player},v)&&s.calls==0);absent(v);}
  {Owned s;s.player_raw=-1000;s.player_text="";assert(read(s,player,v)&&*v.knight_effectiveness_raw==-1000&&v.actual_knight_effectiveness_breakdown->empty());}
  {Owned s;s.player_raw=0;assert(read(s,player,v)&&*v.knight_effectiveness_raw==0);}
  {Owned s;s.player_text=std::string(c::kMaxBreakdownBytes+1,'x');assert(!read(s,player,v));absent(v);}
  {Owned s;auto e=s.env();e.actor.allow_owned_fixture=false;assert(!c::ReadKnightEffectiveness(e,{s.frame,player},v)&&s.calls==0);absent(v);}
  auto one=authored(true,player),two=authored(true,second),unknown=authored(false,player);
  const auto first=m::SerializeKnight(one),second_body=m::SerializeKnight(two),missing=m::SerializeKnight(unknown);
  assert(!first.empty()&&!second_body.empty()&&!missing.empty());
  one.knight_observation.own_actor_context_verified=false;assert(m::SerializeKnight(one).empty());
  unknown.knight_observation.knight_effectiveness_raw=100000;assert(m::SerializeKnight(unknown).empty());
  xar::game::Snapshot snap{};snap.date_raw=10660101;snap.played_character_id=static_cast<std::int32_t>(player);
  auto payload=std::string("{\"expected_revision\":7,\"expected_snapshot_revision\":7,\"expected_date_raw\":10660101,\"expected_actor_character_id\":")+
      std::to_string(player)+",\"expected_game_pid\":"+std::to_string(GetCurrentProcessId())+
      ",\"expected_connection_generation\":2,\"character_id\":"+std::to_string(second)+"}";
  std::uint32_t target=0;assert(m::ParseKnightRequest(payload,snap,7,2,target)&&target==second);
  assert(!m::ParseKnightRequest(payload,snap,8,2,target));assert(!m::ParseKnightRequest(payload,snap,7,3,target));
  auto stale=payload;const auto pos=stale.find(std::to_string(second));stale.replace(pos,std::to_string(second).size(),"4294967295");
  assert(!m::ParseKnightRequest(stale,snap,7,2,target));
  if(argc==3&&std::string_view(argv[1])=="--wire-dir"){
    const std::filesystem::path dir=argv[2];std::filesystem::create_directories(dir);
    for(const auto &[name,body]:std::array<std::pair<const char *,std::string>,3>{{
      {"authored-player-knight-total.json",first},{"authored-second-actor-knight-total.json",second_body},
      {"authored-unavailable-own-context.json",missing}}}){
      std::ofstream stream(dir/name,std::ios::binary);stream<<body;assert(stream.good());
    }
  }else assert(argc==1);
  std::cout<<"owned-memory actor/owner/generation/unknown and real serializer/parser; authored DTO wires; no native callee or live qualification\n";
}
