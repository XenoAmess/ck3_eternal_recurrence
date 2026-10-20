// Authored executable memory only. No CK3, native getter/formatter call, world
// action or loaded-game qualification. Real production Install/Uninstall and
// source verifier are linked from xar_ck3_12002_runtime; no duplicate validator.
#include "xar_bridge/ck3_12004_knight_stat_consumption.hpp"
#include "xar_bridge/knight_stat_context_source12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <windows.h>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace frozen {
#include "../src/character_knight_effectiveness12004_pins.inc"
}
namespace c=xar::ck3_12004;
namespace {
constexpr std::array<std::uint8_t,16> wrapper_original{
    0x48,0x89,0x5C,0x24,0x10,0x57,0x48,0x83,0xEC,0x20,0x8B,0x9A,0xEC,0,0,0};
unsigned cases=0,checks=0;
void Need(bool condition,const char *message){
  ++checks;if(!condition)throw std::runtime_error(message);
}
void Case(const char *name){++cases;std::cout<<name<<'\n';}

struct Image {
  void *reservation=nullptr;
  std::uintptr_t base=0;
  c::KnightStatConsumptionDetourState12004 state{};
  unsigned reads=0,mutate_on_read=0;
  enum class Mutation {none,state,tail,saved,read_failure};
  Mutation mutation=Mutation::none;
  const char *failure="";
  // Default production memory functions install real patches/trampolines in
  // committed authored pages. The existing bindings' read seam injects a
  // deterministic mid-validation change; its source bytes are still real.
  static bool Read(void *opaque,const void *address,void *out,std::size_t bytes) noexcept {
    auto &self=*static_cast<Image *>(opaque);
    ++self.reads;
    if(self.mutation==Mutation::read_failure&&self.reads==self.mutate_on_read)return false;
    std::memcpy(out,address,bytes);
    if(self.reads==self.mutate_on_read){
      if(self.mutation==Mutation::state)self.state.failure_flags.store(0x40000000U);
      if(self.mutation==Mutation::tail)self.WriteByte(self.Context()+219,static_cast<std::uint8_t>(frozen::kContextCode[219]^1U));
      if(self.mutation==Mutation::saved)self.Flip(static_cast<std::uint8_t *>(self.state.context_trampoline));
    }
    return true;
  }
  Image(){
    SYSTEM_INFO info{};GetSystemInfo(&info);
    Need(info.dwPageSize!=0,"page size unavailable");
    const auto page=static_cast<std::uintptr_t>(info.dwPageSize);
    const auto extent=c::kKnightStatWrapperRva12004+page;
    reservation=VirtualAlloc(nullptr,extent,MEM_RESERVE,PAGE_NOACCESS);
    Need(reservation!=nullptr,"authored address range reservation failed");
    base=reinterpret_cast<std::uintptr_t>(reservation);
    for(const auto rva:{c::kKnightStatContextGetterRva12004,c::kKnightStatWrapperRva12004}){
      const auto at=base+(rva/page)*page;
      if(VirtualAlloc(reinterpret_cast<void *>(at),page,MEM_COMMIT,PAGE_EXECUTE_READWRITE)==nullptr){
        (void)VirtualFree(reservation,0,MEM_RELEASE);reservation=nullptr;
        throw std::runtime_error("authored code page commit failed");
      }
    }
    std::memcpy(Context(),frozen::kContextCode.data(),frozen::kContextCode.size());
    std::memcpy(Wrapper(),wrapper_original.data(),wrapper_original.size());
  }
  ~Image(){
    if(state.installed.load()!=0)(void)c::UninstallKnightStatConsumption12004(state,true);
    if(reservation)(void)VirtualFree(reservation,0,MEM_RELEASE);
  }
  std::uint8_t *Context() const noexcept {
    return reinterpret_cast<std::uint8_t *>(base+c::kKnightStatContextGetterRva12004);
  }
  std::uint8_t *Wrapper() const noexcept {
    return reinterpret_cast<std::uint8_t *>(base+c::kKnightStatWrapperRva12004);
  }
  bool Install(){
    c::KnightStatConsumptionInstallEnvironment12004 env{};
    env.bindings=c::BindKnightStatConsumptionImage12004(base,c::kExecutableSha256);
    env.bindings.read_context=this;env.bindings.read_memory=&Read;
    env.primary_thread_suspended_proven=true; // Only this fixture owns these pages.
    return c::InstallKnightStatConsumption12004(state,env,c::kExecutableSha256);
  }
  bool Verify(){
    reads=0;failure="";
    return c::KnightStatContextSourceStillBound12004(base,frozen::kContextCode,failure);
  }
  void WriteByte(std::uint8_t *at,std::uint8_t value) noexcept {
    DWORD old=0;
    if(VirtualProtect(at,1,PAGE_EXECUTE_READWRITE,&old)==FALSE)std::terminate();
    *at=value;
    if(FlushInstructionCache(GetCurrentProcess(),at,1)==FALSE)std::terminate();
    DWORD ignored=0;
    if(VirtualProtect(at,1,old,&ignored)==FALSE)std::terminate();
  }
  void Flip(std::uint8_t *at) noexcept {WriteByte(at,static_cast<std::uint8_t>(*at^1U));}
  void RejectByte(std::uint8_t *at,const char *name){
    Case(name);const auto old=*at;Flip(at);
    Need(!Verify(),"modified installed source accepted");
    Need(failure!=nullptr&&*failure!='\0',"source rejection lacks diagnostic");
    WriteByte(at,old);Need(Verify(),"exact restored source rejected");
  }
};

void Run(){
  Image image;
  static_assert(frozen::kContextCode.size()==c::kKnightStatContextSourceBytes12004);
  Case("pristine-full220");Need(image.Verify(),"exact pristine source rejected");
  Case("pristine-tail-corruption");
  image.Flip(image.Context()+219);Need(!image.Verify(),"foreign pristine tail accepted");
  image.WriteByte(image.Context()+219,frozen::kContextCode[219]);Need(image.Verify(),"restored pristine source rejected");
  Case("production-install-verify");Need(image.Install(),"real production Install failed");
  Need(image.state.installed.load()==1,"Install did not publish installed state");
  Need(std::memcmp(image.Context(),frozen::kContextCode.data(),frozen::kContextCode.size())!=0,
      "real Install did not replace the original full220 image");
  Need(image.Verify(),"known exact installed source rejected");
  Need(std::string_view(image.failure).empty(),"successful source retained failure");
  image.RejectByte(image.Context(),"foreign-live-context-opcode");
  image.RejectByte(image.Context()+6,"foreign-live-context-jump-target");
  image.RejectByte(image.Wrapper(),"foreign-live-wrapper-opcode");
  image.RejectByte(image.Wrapper()+6,"foreign-live-wrapper-jump-target");
  image.RejectByte(image.Context()+14,"first-original-tail-byte");
  image.RejectByte(image.Context()+219,"last-original-tail-byte");
  auto *const context_saved=static_cast<std::uint8_t *>(image.state.context_trampoline);
  auto *const wrapper_saved=static_cast<std::uint8_t *>(image.state.wrapper_trampoline);
  image.RejectByte(context_saved,"context-saved-original-prefix");
  image.RejectByte(context_saved+14,"context-return-jump-opcode");
  image.RejectByte(context_saved+14+6,"context-return-jump-address");
  image.RejectByte(wrapper_saved,"wrapper-saved-original-prefix");
  image.RejectByte(wrapper_saved+16,"wrapper-return-jump-opcode");
  image.RejectByte(wrapper_saved+16+6,"wrapper-return-jump-address");
  Case("wrong-module-base");const char *why="";
  Need(!c::KnightStatContextSourceStillBound12004(image.base+1,frozen::kContextCode,why),"wrong base accepted");
  Case("wrong-owned-context-target");const auto context_target=image.state.context_target;
  image.state.context_target=context_target+1;Need(!image.Verify(),"wrong owned target accepted");
  image.state.context_target=context_target;Need(image.Verify(),"restored context target rejected");
  Case("wrong-owned-wrapper-target");const auto wrapper_target=image.state.wrapper_target;
  image.state.wrapper_target=wrapper_target+1;Need(!image.Verify(),"wrong owned wrapper accepted");
  image.state.wrapper_target=wrapper_target;Need(image.Verify(),"restored wrapper target rejected");
  Case("wrong-owned-context-trampoline");
  image.state.context_trampoline=context_saved+1;Need(!image.Verify(),"wrong original callback/trampoline identity accepted");
  image.state.context_trampoline=context_saved;Need(image.Verify(),"restored context trampoline rejected");
  Case("wrong-owned-wrapper-trampoline");
  image.state.wrapper_trampoline=wrapper_saved+1;Need(!image.Verify(),"wrong wrapper callback/trampoline identity accepted");
  image.state.wrapper_trampoline=wrapper_saved;Need(image.Verify(),"restored wrapper trampoline rejected");
  Case("installed-flag-required");image.state.installed.store(0);Need(!image.Verify(),"unpublished owned patch accepted");
  image.state.installed.store(1);Need(image.Verify(),"restored installed state rejected");
  Case("failure-flags-required-zero");image.state.failure_flags.store(1);Need(!image.Verify(),"failed owned installation accepted");
  image.state.failure_flags.store(0);Need(image.Verify(),"restored failure state rejected");
  Case("mid-read-state-bookend");image.mutation=Image::Mutation::state;image.mutate_on_read=5;
  Need(!image.Verify(),"mid-read state change accepted");
  Need(std::string_view(image.failure)=="knight_context_source_bookend_state_changed","state bookend did not diagnose failure");
  image.mutation=Image::Mutation::none;image.mutate_on_read=0;image.state.failure_flags.store(0);
  Need(image.Verify(),"restored post-state-bookend source rejected");
  Case("mid-read-tail-bookend");image.mutation=Image::Mutation::tail;image.mutate_on_read=5;
  Need(!image.Verify(),"mid-read tail change accepted");
  Need(std::string_view(image.failure)=="knight_context_source_bookend_bytes_changed","tail bookend did not diagnose failure");
  image.mutation=Image::Mutation::none;image.mutate_on_read=0;image.WriteByte(image.Context()+219,frozen::kContextCode[219]);
  Need(image.Verify(),"restored post-tail-bookend source rejected");
  Case("mid-read-saved-bookend");image.mutation=Image::Mutation::saved;image.mutate_on_read=5;
  Need(!image.Verify(),"mid-read saved source change accepted");
  Need(std::string_view(image.failure)=="knight_context_source_bookend_bytes_changed","saved-source bookend did not diagnose failure");
  image.mutation=Image::Mutation::none;image.mutate_on_read=0;image.WriteByte(context_saved,frozen::kContextCode[0]);
  Need(image.Verify(),"restored saved source rejected");
  Case("read-failure");image.mutation=Image::Mutation::read_failure;image.mutate_on_read=1;
  Need(!image.Verify(),"failed source read accepted");
  image.mutation=Image::Mutation::none;image.mutate_on_read=0;Need(image.Verify(),"restored reader rejected");
  Case("uninstall-requires-quiescence");
  Need(!c::UninstallKnightStatConsumption12004(image.state,false),"unqualified uninstall succeeded");
  Need(image.state.installed.load()==1,"failed uninstall lost installation");
  Need(!image.Verify(),"installation with failed lifecycle flag qualified");
  image.state.failure_flags.store(0);Need(image.Verify(),"restored lifecycle source rejected");
  Case("production-uninstall-pristine");
  Need(c::UninstallKnightStatConsumption12004(image.state,true),"production Uninstall failed");
  Need(image.state.installed.load()==0,"Uninstall did not clear state");
  Need(std::memcmp(image.Context(),frozen::kContextCode.data(),frozen::kContextCode.size())==0,"Uninstall did not restore original220");
  Need(image.Verify(),"exact source after real Uninstall rejected");
  Case("production-reinstall-cycle");
  Need(image.Install()&&image.Verify(),"real reinstall/verify failed");
  Need(c::UninstallKnightStatConsumption12004(image.state,true)&&image.Verify(),"real second uninstall/verify failed");
}
} // namespace

int main(int argc,char **argv){
  try{
    if(argc!=1&&argc!=2)throw std::runtime_error("optional unique NEW output directory only");
    std::filesystem::path output;
    if(argc==2){output=argv[1];Need(!std::filesystem::exists(output),"output directory already exists");
      Need(std::filesystem::create_directories(output),"new output directory creation failed");}
    Run();
    const auto body=std::string("{\"schema\":\"xar.ck3.knight-installed-context-source-fixture-v1\",\"authored_memory_only\":true,\"production_install_and_uninstall\":true,\"native_getter_calls\":0,\"cases\":")+
        std::to_string(cases)+",\"checks\":"+std::to_string(checks)+",\"passed\":true,\"loaded_game_qualified\":false}";
    if(!output.empty()){
      std::ofstream file(output/"knight-installed-context-source.actual.json",std::ios::binary);
      Need(static_cast<bool>(file),"fixture result could not be created");file<<body<<'\n';
      Need(static_cast<bool>(file),"fixture result could not be written");
    }
    std::cout<<body<<'\n';return 0;
  }catch(const std::exception &error){std::cerr<<error.what()<<'\n';return 1;}
}
