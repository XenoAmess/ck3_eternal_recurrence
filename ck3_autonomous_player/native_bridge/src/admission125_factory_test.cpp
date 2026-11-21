#include "xar_bridge/adapter_admission125.hpp"
#include "xar_bridge/ck3_1210_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/scripted_widget_control12004.hpp"
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <cstring>
#include <iostream>
#include <stdexcept>

#define XAR_BRIDGE_VERSION "0.1.0"
namespace {
std::string Number(std::uint64_t n){return std::to_string(n);}
void AppendJsonString(std::string &out,std::string_view v){out+='"';for(unsigned char c:v){if(c=='"'||c=='\\'){out+='\\';out+=static_cast<char>(c);}else if(c<32){constexpr char d[]="0123456789abcdef";out+="\\u00";out+=d[c>>4U];out+=d[c&15U];}else out+=static_cast<char>(c);}out+='"';}
#include "hello_frame125.inc"
#include "hello_baseline125.inc"
void Need(bool b,const char *s){if(!b)throw std::runtime_error(s);}
namespace b=xar::ck3_121003::build26785313;
struct Image {
  std::uintptr_t base=0;
  explicit Image(bool loaded){base=reinterpret_cast<std::uintptr_t>(VirtualAlloc(nullptr,b::kImageSize,MEM_RESERVE,PAGE_NOACCESS));Need(base!=0,"reserve");Need(base!=0x140000000ULL,"ASLR model nonpreferred");
    commit(0,0x1000);put<std::uint16_t>(0,0x5A4D);put<std::uint32_t>(0x3C,0x100);put<std::uint32_t>(0x100,0x4550);put<std::uint16_t>(0x104,0x8664);put<std::uint32_t>(0x108,b::kPeTimestamp);put<std::uint16_t>(0x118,0x20B);put<std::uint64_t>(0x130,loaded?base:0x140000000ULL);put<std::uint32_t>(0x150,static_cast<std::uint32_t>(b::kImageSize));
    for(const auto &p:b::ReadonlyImagePins()){commit(p.rva,p.bytes.size());std::memcpy(reinterpret_cast<void*>(base+p.rva),p.bytes.data(),p.bytes.size());}
  }
  ~Image(){if(base)VirtualFree(reinterpret_cast<void*>(base),0,MEM_RELEASE);}
  void commit(std::size_t rva,std::size_t size){const auto start=rva&~std::size_t{4095};const auto bytes=((rva+size+4095)&~std::size_t{4095})-start;Need(VirtualAlloc(reinterpret_cast<void*>(base+start),bytes,MEM_COMMIT,PAGE_READWRITE)!=nullptr,"commit NX own pages");}
  template<class T>void put(std::size_t rva,T value){std::memcpy(reinterpret_cast<void*>(base+rva),&value,sizeof(value));}
};
void CheckFailure(const xar::game::GameAdapter &a,std::string_view stage,int pin=-1){Need(!a.enabled(),"negative admission");const auto r=xar::admission125::ReadAdapterReport(a);Need(r.image.stage==stage,"first failure stage");if(pin>=0)Need(r.image.pin_index==pin,"first failure pin index");auto json=HelloFrame(a,1);Need(json.find("\"ck3_build_match\":false")!=std::string::npos,"Hello match remains false");Need(json.find("\"capabilities\":[\"bridge.identity\",\"bridge.heartbeat\",\"bridge.ping\"]")!=std::string::npos,"no game capabilities on failure");Need(json.find("admission_diagnostic125")!=std::string::npos,"failure diagnostic present");std::cout<<json<<'\n';}
}
int main(int argc,char **argv){try{
 const bool loaded=argc>1&&std::string_view(argv[1])=="--loaded";
 Image image(loaded);auto good=xar::game::CreateCk3_1210AdapterForImage125(b::kExecutableSha256,image.base);
 Need(good&&good->enabled(),"real Factory cold globals admits source");
 const auto ready=HelloFrame(*good,17);Need(ready==BaselineHelloFrame125(*good,17),"ready Hello byte-for-byte baseline");Need(ready.find("admission_diagnostic125")==std::string::npos,"ready has no extra diagnostic");std::cout<<ready<<'\n';
 // Bind only: all dynamic roots remain uncommitted/zero. No getter is invoked.
 Need(xar::admission125::ReadAdapterReport(*good).image.stage==std::string_view("complete"),"real BindFull -> BindCore -> image pins");
 image.put<std::uint64_t>(0x130,loaded?0x140000000ULL:image.base);
 auto wrongbase=xar::game::CreateCk3_1210AdapterForImage125(b::kExecutableSha256,image.base);
 CheckFailure(*wrongbase,loaded?"header_image_base_loaded":"header_image_base_preferred112");
 image.put<std::uint64_t>(0x130,loaded?image.base:0x140000000ULL);
 image.put<std::uint16_t>(0,0);auto mz=xar::game::CreateCk3_1210AdapterForImage125(b::kExecutableSha256,image.base);CheckFailure(*mz,"header_mz");image.put<std::uint16_t>(0,0x5A4D);
 for(const auto index:{std::size_t{0},b::ReadonlyImagePins().size()-1}){const auto &p=b::ReadonlyImagePins()[index];auto *q=reinterpret_cast<unsigned char*>(image.base+p.rva);*q^=1;auto bad=xar::game::CreateCk3_1210AdapterForImage125(b::kExecutableSha256,image.base);CheckFailure(*bad,"pin_compare",static_cast<int>(index));*q^=1;}
 auto sha=xar::game::CreateCk3_1210AdapterForImage125("NOT_A_BUILD",image.base);Need(!sha->enabled(),"wrong sha stays rejected");
 xar::admission125::last_hash={};xar::admission125::last_hash.stage="file_open";xar::admission125::last_hash.error=ERROR_SHARING_VIOLATION;
 auto nohash=xar::game::CreateCk3_1210AdapterForImage125("",image.base);Need(!nohash->enabled(),"hash error rejects");
 const auto fileerror=xar::admission125::ReadAdapterReport(*nohash);Need(fileerror.hash.error==ERROR_SHARING_VIOLATION&&fileerror.hash.stage==std::string_view("file_open"),"original file failure retained through Factory");
 // A later failed Verify cannot overwrite the immutable report in good.
 Need(xar::admission125::ReadAdapterReport(*good).image.stage==std::string_view("complete"),"per-adapter immutable diagnosis");
 auto next=xar::game::CreateCk3_1210AdapterForImage125(b::kExecutableSha256,image.base);Need(next->enabled(),"next valid Factory restores independently");
 std::cout<<"FACTORY_HELLO125_PASS gate="<<(loaded?"published_loaded_base":"frozen112_preferred_base")<<"\n";return 0;
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
