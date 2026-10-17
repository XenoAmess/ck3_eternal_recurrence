#include "xar_bridge/holy_site_creation12004.hpp"
#include "xar_bridge/holy_site_creation12004_source_pins.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <windows.h>
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
namespace hs=xar::ck3_12004::religion::holy_site_creation;
namespace {
constexpr std::uintptr_t base=0x10000000000ULL,owner=0x20000000000ULL,w=owner+0x10000;
constexpr std::uintptr_t type=owner+0x20000,other_type=owner+0x21000;
constexpr std::uint32_t actor=0x80000010U,faith=0x80000032U,barony=0x80000100U,art=0xF0000009U;
std::size_t checks=0;
void Check(bool ok,const char*why){++checks;if(!ok)throw std::runtime_error(why);}
struct Memory {
 std::map<std::uintptr_t,std::vector<unsigned char>>blocks;
 void Make(std::uintptr_t p,std::size_t size){blocks[p]=std::vector<unsigned char>(size);}
 void Bytes(std::uintptr_t p,const void*value,std::size_t size){
  auto it=blocks.upper_bound(p);if(it==blocks.begin())throw std::runtime_error("fixture address");--it;
  const auto off=p-it->first;
  if(off>it->second.size()||size>it->second.size()-off)throw std::runtime_error("fixture write bounds");
  std::memcpy(it->second.data()+off,value,size);
 }
 template<class T>void Put(std::uintptr_t p,const T&v){Bytes(p,&v,sizeof(v));}
 template<class T>void Global(std::uintptr_t rva,T v){Make(base+rva,sizeof(v));Put(base+rva,v);}
 template<class T>void Vec(std::size_t off,const std::vector<T>&v,std::uintptr_t rows){
  Make(rows,std::max<std::size_t>(1,v.size()*sizeof(T)));
  if(!v.empty())Bytes(rows,v.data(),v.size()*sizeof(T));
  Put(w+off,rows);Put(w+off+8,static_cast<std::int32_t>(v.size()));Put(w+off+12,static_cast<std::int32_t>(v.size()));
 }
 void Ref(std::uintptr_t global,std::uint32_t id,std::uintptr_t object,std::size_t idoff,std::uintptr_t store){
  auto count=(id&0xFFFFFFU)+1;Make(store,0x40);Make(store+0x100,static_cast<std::size_t>(count)*16);
  Global(global,store);Put(store+0x20,store+0x100);Put(store+0x2C,count);
  Put(store+0x100+static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object);Make(object,0x500);Put(object+idoff,id);
 }
 static bool Read(void*ctx,const void*p,void*out,std::size_t size)noexcept{
  auto&m=*static_cast<Memory*>(ctx);auto address=reinterpret_cast<std::uintptr_t>(p);auto it=m.blocks.upper_bound(address);
  if(it!=m.blocks.begin()){
   --it;auto off=address-it->first;
   if(off<=it->second.size()&&size<=it->second.size()-off){std::memcpy(out,it->second.data()+off,size);return true;}
  }
  // Native function I/O is the only substituted seam. Actual output CStrings
  // are owned fixture stack memory, consumed by the production reader.
  SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),p,out,size,&got)&&got==size;
 }
};
struct Fixture;
Fixture*active=nullptr;
struct Fixture {
 Memory m;hs::Bindings b;xar::ck3_12002::religion::Context ctx;
 bool enabled=true;std::uint8_t bypass=0;std::int64_t rarity=300000;
 std::array<unsigned char,32>settings{};std::size_t destroyed=0,selected_calls=0,opened=0;
 std::vector<std::uint32_t>selected{art};
 Fixture(){
  active=this;b=hs::BindImage12004(base,xar::ck3_12004::kExecutableSha256);b.read_memory=&Memory::Read;b.read_context=&m;
  for(const auto&p:hs::source::pins){m.Make(base+p.rva,p.size);m.Bytes(base+p.rva,p.bytes.data(),p.size);}
  m.Make(owner,0x700);m.Make(w,0xA88);m.Put(owner+0x5E8,w);m.Put(w,base+0x4593690);m.Put(w+0x10,base+0x4593760);
  m.Make(base+0x4593688,8);m.Put(base+0x4593688,base+0x4BC2388);m.Make(base+0x4BC2388,24);
  m.Put(base+0x4BC2388,std::uint32_t{1});m.Put(base+0x4BC2388+4,std::uint32_t{0});
  m.Put(base+0x4BC2388+12,std::uint32_t{0x57EC440});m.Put(base+0x4BC2388+20,std::uint32_t{0x4BC2388});
  m.Put(w+0xA0,owner);m.Put(w+0x98,owner+0x30000);m.Put(w+0x60,owner+0x31000);
  m.Put(w+0xC8,faith);m.Put(w+0xD0,type);m.Put(w+0xD8,barony);m.Global(0x54DBC00,actor);
  m.Ref(0x5D1E300,faith,owner+0x32000,8,owner+0x40000);m.Put(owner+0x32000+0xC,std::uint32_t{0x46616974});
  for(const auto&item:{std::pair{type,"valor"},std::pair{other_type,"healing"}}){
   m.Make(item.first,0x440);m.Put(item.first+0x38,std::uint32_t{0x4744624F});
   m.Bytes(item.first+0x18,item.second,std::strlen(item.second));m.Put(item.first+0x28,static_cast<std::uint64_t>(std::strlen(item.second)));
   m.Put(item.first+0x30,std::uint64_t{15});m.Put(item.first+0x418,std::uint8_t{1});
  }
  m.Vec(0x130,std::vector<std::uintptr_t>{type,other_type},owner+0x50000);
  m.Vec(0x100,std::vector<std::uint32_t>{barony,barony},owner+0x51000);
  m.Vec(0x118,std::vector<std::uint32_t>{art},owner+0x52000);m.Vec(0xE0,selected,owner+0x53000);
  const std::array<std::int64_t,10>quote{0,0,200000000,0,0,0,0,0,0,0};m.Put(w+0x178,quote);
  m.Ref(0x5D1DE68,art,owner+0x60000,0x10,owner+0x70000);m.Put(owner+0x60000+0x14,std::uint32_t{0x41727469});
  m.Make(base+0x54D70F8,8);m.Put(base+0x54D70F8,base+0x44B92F0);
  m.Make(base+0x44B92F0,0x68);
  for(const auto&edge:std::array<std::pair<std::size_t,std::uintptr_t>,6>{{{0x18,0x8522C0},{0x28,0x876E00},{0x38,0x877200},{0x50,0xB1AA90},{0x58,0x8771F0},{0x60,0x8771F0}}})m.Put(base+0x44B92F0+edge.first,base+edge.second);
  ctx.available=true;ctx.capture_epoch=84;ctx.date_raw=51394920;ctx.played_character_id=static_cast<std::int32_t>(actor);ctx.faith_id=faith;
  b.native_enabled=+[](void*){return active->enabled;};
  b.requirements_settings=+[]()->void*{return active->settings.data();};
  b.rarity_sum=+[](void*,std::int64_t*out)->std::int64_t*{*out=active->rarity;return out;};
  b.can_pick_type=+[](void*,const void*p,void*){return reinterpret_cast<std::uintptr_t>(p)!=other_type;};
  b.create_tooltip=+[](void*,void*out)->void*{
   const char*text=active->enabled?"ready":"need relic";std::memset(out,0,32);std::memcpy(out,text,std::strlen(text));
   auto*p=static_cast<unsigned char*>(out);auto n=static_cast<std::uint64_t>(std::strlen(text));std::uint64_t cap=15;
   std::memcpy(p+16,&n,8);std::memcpy(p+24,&cap,8);return out;
  };
  b.destroy_string=+[](void*){++active->destroyed;};
  b.select_artifact=+[](void*,const void*){
   ++active->selected_calls;auto&v=active->selected;
   if(v.empty())v.push_back(art);else v.clear();active->m.Vec(0xE0,v,owner+0x53000);
  };
  b.faith_any_type=+[]()->void*{return reinterpret_cast<void*>(base+0x54D70F8);};
  b.open_view=+[](void*p,std::uint32_t view,const void*value){
   Check(reinterpret_cast<std::uintptr_t>(p)==owner&&view==0xAA,"native view/owner");
   std::uint32_t id=0;std::memcpy(&id,static_cast<const unsigned char*>(value)+8,4);Check(id==faith,"actual Faith Any");++active->opened;
  };
 }
 hs::Snapshot Read(){settings[16]=bypass;hs::Snapshot v;hs::ReadContext12004(b,reinterpret_cast<void*>(owner),ctx,v);return v;}
};
void Save(const std::filesystem::path&dir,const char*name,const hs::Snapshot&v){
 static unsigned sequence=0;std::string request="g2-read-"+std::string(31,'0')+static_cast<char>('1'+sequence++);
 const auto path=dir/(std::string(name)+".json");if(std::filesystem::exists(path))throw std::runtime_error("immutable packet exists");
 std::ofstream f(path,std::ios::binary);f<<hs::SerializeCommand12004(v,request,37,v.date_raw)<<'\n';if(!f)throw std::runtime_error("packet write");
}
}
int main(int argc,char**argv){
 try{
  if(argc==3&&std::string(argv[2])=="--mcp-packets-only"){
   const std::filesystem::path dir=argv[1];if(std::filesystem::exists(dir))throw std::runtime_error("new attempt required");std::filesystem::create_directories(dir);
   const std::array<const char*,8>names{{"complete-selected","empty-unselected","bypass-nonzero","window-unavailable","hidden-root","model-unavailable","enabled-unobserved","signed-raw-extrema"}};
   for(std::size_t i=0;i<names.size();++i){Fixture f;f.ctx.played_character_id=15893;f.m.Global(0x54DBC00,std::uint32_t{15893});
    if(i==1){f.m.Vec(0xE0,std::vector<std::uint32_t>{},owner+0x53000);f.m.Put(w+0xD0,std::uintptr_t{0});f.m.Put(w+0xD8,std::uint32_t{0xFFFFFFFF});f.enabled=false;f.rarity=0;}
    if(i==2)f.bypass=1;
    if(i==3)f.m.Put(owner+0x5E8,std::uintptr_t{0});
    if(i==4)f.m.Put(w+0x60,std::uintptr_t{0});
    if(i==5){f.m.Put(w+0x13C,std::int32_t{16385});f.m.Put(w+0x138,std::int32_t{16385});}
    if(i==6)f.b.native_enabled=nullptr;
    if(i==7){const std::array<std::int64_t,10>raw{std::numeric_limits<std::int64_t>::min(),-1,0,1,std::numeric_limits<std::int64_t>::max(),0,0,0,0,0};f.m.Put(w+0x178,raw);}
    Save(dir,names[i],f.Read());
   }
   std::cout<<"{\"status\":\"EMITTED\",\"packets\":8,\"actor\":15893,\"game_contacted\":false}\n";return 0;
  }
  if(argc==2&&std::string(argv[1])=="--new-guards-only"){
   {Fixture f;hs::UiRequest q;bool attempted=false,already=false;std::string why;
    f.m.Put(base+0x44B92F0+0x50,base+0xB1AA91);
    Check(!hs::InvokeUi12004(f.b,reinterpret_cast<void*>(owner),f.ctx,q,attempted,already,why)&&!attempted,"changed Faith Any ABI edge rejects");
    q.action=hs::UiAction::set_artifact;q.object_id=0xFFFFFFFF;q.selected=false;
    Check(!hs::InvokeUi12004(f.b,reinterpret_cast<void*>(owner),f.ctx,q,attempted,already,why)&&!already&&!attempted,"absent artifact never already desired");
    q.action=hs::UiAction::select_barony;
    Check(!hs::InvokeUi12004(f.b,reinterpret_cast<void*>(owner),f.ctx,q,attempted,already,why)&&!already&&!attempted,"absent barony rejects");}
   {Fixture f;f.m.Put(type+0x418,std::uint8_t{2});Check(f.Read().available,"native dynamic nonzero remains candidate");
    f.m.Put(type+0x38,std::uint32_t{0});Check(!f.Read().available,"invalid selected type not unselected");}
   std::cout<<"{\"status\":\"PASS\",\"checks\":"<<checks<<",\"packets\":0,\"scope\":\"new guards only; no old fixture rerun\",\"game_contacted\":false}\n";return 0;
  }
  if(argc!=2)throw std::runtime_error("new packet directory required");
  const std::filesystem::path dir=argv[1];if(std::filesystem::exists(dir))throw std::runtime_error("new attempt required");std::filesystem::create_directories(dir);
  {Fixture f;auto v=f.Read();Check(v.available&&v.models_complete,"complete reader");
   Check(v.potential_barony_title_ids==std::vector<std::uint32_t>{barony,barony},"order/duplicates");
   Check(v.player_faith_id==faith&&v.played_character_id==static_cast<std::int32_t>(actor),"high full refs");
   Check(v.native_rarity_sum_raw==300000&&v.cached_resource_vector_raw[2]==200000000,"native numeric values");
   Check(!v.available_holy_site_types.at(1).native_can_pick,"disabled type remains candidate");Check(f.destroyed==3,"native cleanup");Save(dir,"complete-selected",v);}
  {Fixture f;f.m.Vec(0xE0,std::vector<std::uint32_t>{},owner+0x53000);f.m.Put(w+0xD0,std::uintptr_t{0});f.m.Put(w+0xD8,std::uint32_t{0xFFFFFFFF});f.enabled=false;f.rarity=0;
   auto v=f.Read();Check(v.available&&v.selected_artifact_ids.empty()&&!v.selected_type_key&&!v.selected_barony_title_id,"observed empty");Check(v.native_enabled_observed&&!v.native_create_button_enabled,"observed false");Save(dir,"empty-unselected",v);}
  {Fixture f;f.bypass=1;auto v=f.Read();Check(v.available&&v.native_create_button_enabled&&v.bypass_requirements_raw==1,"bypass raw");Save(dir,"bypass-nonzero",v);}
  {Fixture f;f.m.Put(owner+0x5E8,std::uintptr_t{0});auto v=f.Read();Check(!v.available,"absent window");Save(dir,"window-unavailable",v);}
  {Fixture f;f.m.Put(w+0x60,std::uintptr_t{0});auto v=f.Read();Check(v.available&&!v.root_present,"known root false");Save(dir,"hidden-root",v);}
  {Fixture f;f.m.Put(w+0x13C,std::int32_t{16385});f.m.Put(w+0x138,std::int32_t{16385});auto v=f.Read();Check(!v.available&&!v.models_complete,"incomplete not empty");Save(dir,"model-unavailable",v);}
  {Fixture f;f.b.native_enabled=nullptr;auto v=f.Read();Check(v.available&&!v.native_enabled_observed,"unobserved enabled");Save(dir,"enabled-unobserved",v);}
  {Fixture f;const std::array<std::int64_t,10>raw{std::numeric_limits<std::int64_t>::min(),-1,0,1,std::numeric_limits<std::int64_t>::max(),0,0,0,0,0};
   f.m.Put(w+0x178,raw);auto v=f.Read();Check(v.available&&v.cached_resource_vector_raw==raw,"signed raw preserved");Save(dir,"signed-raw-extrema",v);}
  {Fixture f;Check(!hs::BindImage12004(base,"wrong").enabled,"build guard");f.m.Put(base+hs::source::pins[0].rva,std::uint8_t{0});Check(!f.Read().available,"loaded pin");}
  {Fixture f;f.ctx.faith_id=0x80000033U;Check(!f.Read().available,"wrong Faith");}
  {Fixture f;hs::UiRequest q;bool attempted=false,already=false;std::string why;
   Check(hs::InvokeUi12004(f.b,reinterpret_cast<void*>(owner),f.ctx,q,attempted,already,why)&&attempted&&f.opened==1,"typed open once");
   q.action=hs::UiAction::select_type;q.type_key="healing";Check(!hs::InvokeUi12004(f.b,reinterpret_cast<void*>(owner),f.ctx,q,attempted,already,why)&&!attempted,"disabled native type");
   q.type_key="unknown";Check(!hs::InvokeUi12004(f.b,reinterpret_cast<void*>(owner),f.ctx,q,attempted,already,why),"unknown type");
   q.action=hs::UiAction::set_artifact;q.object_id=art;q.selected=true;
   Check(hs::InvokeUi12004(f.b,reinterpret_cast<void*>(owner),f.ctx,q,attempted,already,why)&&already&&!attempted&&f.selected_calls==0,"desired existing no toggle");
   q.selected=false;Check(hs::InvokeUi12004(f.b,reinterpret_cast<void*>(owner),f.ctx,q,attempted,already,why)&&attempted&&f.selected_calls==1,"remove once");
   Check(f.Read().selected_artifact_ids.empty(),"independent selected after");
   Check(hs::InvokeUi12004(f.b,reinterpret_cast<void*>(owner),f.ctx,q,attempted,already,why)&&already&&!attempted&&f.selected_calls==1,"repeated desired no toggle");
   q.selected=true;q.object_id=0x70000000U;Check(!hs::InvokeUi12004(f.b,reinterpret_cast<void*>(owner),f.ctx,q,attempted,already,why)&&!attempted,"noncandidate rejected");}
  std::cout<<"{\"status\":\"PASS\",\"checks\":"<<checks<<",\"packets\":8,\"provenance\":\"synthetic native I/O; production reader and serializer\",\"game_contacted\":false}\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
