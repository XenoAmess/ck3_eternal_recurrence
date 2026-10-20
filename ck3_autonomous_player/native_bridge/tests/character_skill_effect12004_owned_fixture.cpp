// Source-only finite owned-memory fixture; not compiled or executed in delivery.
#include "xar_bridge/character_skill_effect12004.hpp"
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <unordered_map>
namespace {
using namespace xar::bridge::character_skill_effect12004;
constexpr std::uintptr_t base=0x140000000, actor=0x110000, values=0x120000;
constexpr std::uintptr_t cs=0x130000, cr=0x140000, rs=0x150000, rr=0x160000, rite=0x170000;
constexpr std::uintptr_t fs=0x180000, fr=0x190000, faith=0x1A0000;
constexpr std::uint32_t id=0x01000003U;
struct Owned {
 std::unordered_map<std::uintptr_t,unsigned char> bytes{};
 Frame frame{7,51394920,15893,true,true,true};
 int frame_reads=0,levels=0,texts=0;
 bool drift_frame=false,drift_text=false,drift_skill=false,fail_text=false;
 std::string text="Original native text fixture leaf; no real site attribution";
 template<class T>void Put(std::uintptr_t at,T v){
  const auto *p=reinterpret_cast<const unsigned char *>(&v);
  for(std::size_t i=0;i<sizeof(T);++i)bytes[at+i]=p[i];
 }
 void Populate(){
  Put(base+0x5C67568,cs);Put(cs+0x20,cr);Put(cs+0x2C,std::uint32_t{4});
  Put(cr+3*16+8,actor);Put(actor+0x18,id);Put(actor+0x1C,std::uint32_t{0x43686172});
  Put(actor+0x1B0,values);Put(actor+0xB4,std::uint32_t{2});
  Put(base+0x5D1E2F8,rs);Put(rs+0x20,rr);Put(rs+0x2C,std::uint32_t{3});
  Put(rr+2*16+8,rite);Put(rite+8,std::uint32_t{2});Put(rite+0x4B8,std::uint32_t{1});
  Put(base+0x5D1E300,fs);Put(fs+0x20,fr);Put(fs+0x2C,std::uint32_t{2});
  Put(fr+16+8,faith);Put(faith+8,std::uint32_t{1});
  for(std::size_t i=0;i<6;++i)Put(actor+0xD8+i*4,static_cast<std::int32_t>(10+i));
  Put(values+0x118,std::int64_t{40000000});
 }
};
bool Memory(void *p,std::uintptr_t at,void *out,std::size_t n)noexcept{
 auto &f=*static_cast<Owned *>(p);auto *to=static_cast<unsigned char *>(out);
 for(std::size_t i=0;i<n;++i){auto j=f.bytes.find(at+i);if(j==f.bytes.end())return false;to[i]=j->second;}return true;
}
bool FrameRead(void *p,Frame &out)noexcept{auto &f=*static_cast<Owned *>(p);out=f.frame;++f.frame_reads;if(f.drift_frame&&f.frame_reads>1)++out.revision;return true;}
bool Level(void *p,std::uintptr_t actual,std::int32_t &out)noexcept{auto &f=*static_cast<Owned *>(p);++f.levels;if(actual!=actor)return false;out=4;return true;}
bool Breakdown(void *p,const SkillItem &item,std::string &out)noexcept{
 auto &f=*static_cast<Owned *>(p);++f.texts;if(f.fail_text||item.character_id!=id||item.skill!=0)return false;
 out=f.text;if(f.drift_text&&f.texts>1)out+=" changed";
 if(f.drift_skill&&f.texts==1)f.Put(actor+0xD8,std::int32_t{99});return true;
}
Environment Env(Owned &f){return {true,kExeSha,base,&f,&Memory,&FrameRead,&Level,&Breakdown,CallbackProvenance::owned_fixture,true};}
void Check(bool b){if(!b)std::abort();}
void Success(){Owned f;f.Populate();Result out;Check(Read(Env(f),Request{f.frame,id,0},out));Check(out.available&&out.two_pass_stable&&out.current_skill_points->at(0)==10&&out.effective_devotion_level==4);Check(!out.site_attribution_observed&&!out.selected_site_contribution_raw&&f.levels==2&&f.texts==2);}
template<class Change>void Rejected(Change change){Owned f;f.Populate();auto e=Env(f);Request r{f.frame,id,0};change(f,e,r);Result out;Check(!Read(e,r,out)&&!out.available&&!out.current_skill_points&&!out.actual_skill_breakdown&&!out.site_attribution_observed);}
} // namespace
int main(){
 Success();
 Rejected([](auto&,auto&e,auto&){e.executable_sha256="wrong";});
 Rejected([](auto&,auto&e,auto&){e.callback_provenance=CallbackProvenance::unavailable;});
 Rejected([](auto&,auto&e,auto&){e.allow_owned_fixture=false;});
 Rejected([](auto&,auto&e,auto&){e.read_level=nullptr;});
 Rejected([](auto&,auto&,auto&r){r.expected.owner_thread=false;});
 Rejected([](auto&,auto&,auto&r){r.expected.paused=false;});
 Rejected([](auto&,auto&,auto&r){r.skill=6;});
 Rejected([](auto&,auto&,auto&r){r.character_id=0x02000003U;});
 Rejected([](auto&f,auto&,auto&){f.Put(actor+0x1C,std::uint32_t{0});});
 Rejected([](auto&f,auto&,auto&){f.Put(actor+0x1B0,std::uintptr_t{0});});
 Rejected([](auto&f,auto&,auto&){f.Put(rite+8,std::uint32_t{9});});
 Rejected([](auto&f,auto&,auto&){f.drift_frame=true;});
 Rejected([](auto&f,auto&,auto&){f.drift_skill=true;});
 Rejected([](auto&f,auto&,auto&){f.drift_text=true;});
 Rejected([](auto&f,auto&,auto&){f.fail_text=true;});
 Rejected([](auto&f,auto&,auto&){f.text.assign(kMaxBreakdownBytes+1,'x');});
 std::cout<<"17 finite owned-memory source cases; native ABI leaf invocation remains unqualified\n";
 return 0;
}
