// External source candidate, NOT compiled or run.
// Real two readers -> real production body serializer. Sparse owned bytes and
// explicitly simulated outer admission do NOT prove loaded module/TLS/owner.
#include "current_player_observers12004.hpp"
#if defined(XAR_GHW_INCLUDE_ADDRESS_ONLY_BINDER_REGRESSION)
#include "ghw_permission_observer/ghw_variable_bindings_12004.hpp"
#endif
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <cstddef>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace vars=xar::ck3_12004::religion::ghw_variables_candidate;
namespace links=xar::ck3_12004::religion::ghw_links_candidate;
namespace combined=xar::ck3_12004::current_player_observers;
static_assert(vars::kExactSha==xar::ck3_12004::kExecutableSha256);
static_assert(links::kExactSha==xar::ck3_12004::kExecutableSha256);
namespace {
struct Region { std::uintptr_t address;std::vector<std::byte> bytes; };
struct Owned {
  static constexpr std::uintptr_t image=0x10000000,faith=0x10000,religion=0x11000;
  static constexpr std::uintptr_t ghw_db=0x60000,ghw_table=0x61000,ghw=0x62000;
  static constexpr std::uintptr_t war_db=0x63000,war_table=0x64000,war=0x65000;
  static constexpr std::uint32_t ghw_id=0x05000001,war_id=0x03000001;
  vars::BoundFrame frame{77,500,100,0x02000003,0x03000002,
      faith,religion,true,true,true};
  std::array<std::uintptr_t,3> contexts{0x20000,0x21000,0x22000};
  std::array<std::uintptr_t,3> rows{0x30000,0x31000,0x32000};
  std::vector<Region> regions;
  std::uintptr_t denied=0;
  int missing_context=-1;
  std::array<unsigned,4> identifier_calls{};
  unsigned frame_calls=0;

  Owned() {
    Add(faith,0x900);Add(religion,0x100);
    Put(faith+8,frame.faith_id);Put(faith+0x0C,std::uint32_t{0x46616974});
    Put(faith+0x8C,frame.religion_id);Put(faith+0x828,std::uint32_t{0xffffffff});
    Put(religion+8,frame.religion_id);Put(religion+0x0C,std::uint32_t{0x52656c67});
    for(std::size_t i=0;i<contexts.size();++i){
      Add(contexts[i],0x50);Add(rows[i],0x80);
      Put(contexts[i]+0x10,rows[i]);Put(contexts[i]+0x1C,std::int32_t{0});
      Put(contexts[i]+0x28,std::int32_t{20});
    }
    Add(image+links::kGhwDatabaseSlotRva,8);Add(ghw_db,0x40);
    Add(ghw_table,0x20);Add(ghw,0x100);
    Add(image+links::kWarDatabaseSlotRva,8);Add(war_db,0x40);
    Add(war_table,0x20);Add(war,0x100);
    Put(image+links::kGhwDatabaseSlotRva,ghw_db);
    Put(ghw_db+0x20,ghw_table);Put(ghw_db+0x2C,std::uint32_t{2});
    Put(ghw_table+0x18,ghw);Put(ghw+0x10,ghw_id);
    Put(ghw+0x14,links::kGhwMagic);Put(ghw+0x28,std::uint32_t{0xffffffff});
    Put(image+links::kWarDatabaseSlotRva,war_db);
    Put(war_db+0x20,war_table);Put(war_db+0x2C,std::uint32_t{2});
    Put(war_table+0x18,war);Put(war+8,war_id);Put(war+0x0C,links::kWarMagic);
  }
  void Add(std::uintptr_t address,std::size_t size){
    regions.push_back({address,std::vector<std::byte>(size)});
  }
  template<class T> void Put(std::uintptr_t address,T value){
    for(auto &r:regions)
      if(address>=r.address&&address-r.address<=r.bytes.size()&&
          sizeof(T)<=r.bytes.size()-(address-r.address)){
        std::memcpy(r.bytes.data()+(address-r.address),&value,sizeof(value));return;
      }
    throw std::runtime_error("Put outside finite owned bytes");
  }
  void Row(int domain,int index,int token,int expiry){
    auto address=rows.at(static_cast<std::size_t>(domain))+
        static_cast<std::uintptr_t>(index)*0x20;
    Put(address+8,static_cast<std::int32_t>(token));
    Put(address+0x0C,static_cast<std::int32_t>(expiry));
    Put(address+0x10,std::uint16_t{1});Put(address+0x18,std::int64_t{100000});
    Put(contexts.at(static_cast<std::size_t>(domain))+0x1C,
        static_cast<std::int32_t>(index+1));
  }
  void TimedRows(){
    Row(1,0,100,-1);Row(1,1,101,140);Row(2,0,102,19);Row(0,0,103,3670);
  }
  void LinkGhw(bool actual_war){
    Put(faith+0x828,ghw_id);
    Put(ghw+0x28,actual_war?war_id:std::uint32_t{0xffffffff});
  }
  static bool Memory(void *p,std::uintptr_t address,void *out,
                     std::size_t bytes) noexcept {
    auto &o=*static_cast<Owned*>(p);
    if(address==o.denied)return false;
    for(const auto&r:o.regions)
      if(address>=r.address&&address-r.address<=r.bytes.size()&&
          bytes<=r.bytes.size()-(address-r.address)){
        std::memcpy(out,r.bytes.data()+(address-r.address),bytes);return true;
      }
    return false;
  }
  static bool Frame(void *p,vars::BoundFrame &out) noexcept {
    auto &o=*static_cast<Owned*>(p);++o.frame_calls;out=o.frame;return true;
  }
  static bool Identifier(void *p,std::string_view key,std::int32_t &out) noexcept {
    auto &o=*static_cast<Owned*>(p);
    for(std::size_t i=0;i<vars::kKeys.size();++i)
      if(key==vars::kKeys[i]){
        ++o.identifier_calls[i];out=100+static_cast<std::int32_t>(i);return true;
      }
    return false;
  }
  static bool Context(void *p,vars::Scope scope,std::uint32_t id,
                      std::uintptr_t &out) noexcept {
    auto &o=*static_cast<Owned*>(p);
    int domain=scope==vars::Scope::global?0:scope==vars::Scope::religion?1:2;
    if(domain==o.missing_context||
        (scope==vars::Scope::global&&id!=0)||
        (scope==vars::Scope::religion&&id!=o.frame.religion_id)||
        (scope==vars::Scope::faith&&id!=o.frame.faith_id))return false;
    out=o.contexts[static_cast<std::size_t>(domain)];return true;
  }
  combined::GhwObservation Capture(){
    combined::GhwObservation out;
    // The real production frame/pin/TLS provider is deliberately not replaced.
    // This finite direct-reader fixture SIMULATES admitted outer metadata only.
    out.available=true;out.frame_verified=true;out.loaded_source_pins_verified=true;
    out.capture_epoch=frame.capture_epoch;out.date_raw=frame.date_raw;
    out.played_character_id=frame.played_character_id;
    out.faith_id=frame.faith_id;out.religion_id=frame.religion_id;
    out.unavailable_reason.clear();
    vars::Access a{this,Memory,Frame,Identifier,Context,vars::kExactSha};
    (void)vars::ReadCurrentPlayerGhwVariables12004(a,out.variables);
    links::Access b{Memory,this,image,faith,links::kExactSha};
    // Preserve stable partial fields even if this real reader returns false.
    (void)links::ReadGhwObjectLinks12004(b,out.object_links);
    if(frame_calls!=2||identifier_calls!=std::array<unsigned,4>{2,2,2,2})
      throw std::runtime_error("Real variable reader was not exercised twice");
    return out;
  }
};
void Check(bool value,const char *reason){if(!value)throw std::runtime_error(reason);}
void Emit(const std::filesystem::path &directory,const char *name,
          const combined::GhwObservation &value){
  const auto wire=combined::SerializeGhwPermissions12004(value);
  Check(!wire.empty(),"Production serializer rejected actual reader DTO");
  if(directory.empty())std::cout<<name<<'\t'<<wire<<'\n';
  else {
    const auto path=directory/(std::string(name)+".json");
    Check(!std::filesystem::exists(path),"Refuse to overwrite native wire");
    std::ofstream file(path,std::ios::binary);file.exceptions(std::ios::badbit|std::ios::failbit);
    file<<wire<<'\n';
  }
}
} // namespace

int main(int argc,char **argv){
  try {
    std::filesystem::path directory;
    if(argc!=1){
      Check(argc==3&&std::string_view(argv[1])=="--wire-dir","Expected --wire-dir FRESH_DIR");
      directory=std::filesystem::path(argv[2]);
      Check(!std::filesystem::exists(directory),"Wire directory must be new");
      Check(std::filesystem::create_directories(directory),"Cannot create wire directory");
    }
#if defined(XAR_GHW_INCLUDE_ADDRESS_ONLY_BINDER_REGRESSION)
    {
      Owned o;vars::BindingState state{};
      // Exercise the REAL address-only binder at the existing canonical .4
      // identity. This catches the lower/uppercase strict-factory seam without
      // invoking any pointer it produces or admitting a loaded image.
      const auto a=vars::BindGhwVariableAccess12004(state,Owned::image,
          xar::ck3_12004::kExecutableSha256,&o,&Owned::Memory,&Owned::Frame);
      Check(a.read_memory&&a.read_bound_frame&&state.identifiers.enabled&&state.global.enabled,
            "Canonical actual .4 identity must bind both existing factories");
      Check(o.frame_calls==0&&o.identifier_calls==std::array<unsigned,4>{0,0,0,0},
            "Address-only binding unexpectedly invoked a callback");
      const auto bad=vars::BindGhwVariableAccess12004(state,Owned::image,
          "different_build_not_admitted",&o,&Owned::Memory,&Owned::Frame);
      Check(!bad.read_memory&&!state.identifiers.enabled&&!state.global.enabled,
            "Wrong build cannot bind callbacks");
    }
#endif
    {
      Owned o;auto v=o.Capture();
      for(const auto &f:v.variables.fields)
        Check(f.read_available&&f.present==false&&f.timed==false&&f.remaining_raw==-1,
              "Known empty native collection differs from unknown");
      Check(v.object_links.available&&v.object_links.ghw==links::State::absent&&
            v.object_links.war==links::State::absent&&!v.object_links.has_war_started,
            "No linked GHW is not an observed WarStarted false");
      Emit(directory,"ghw-known-absence",v);
    }
    {
      Owned o;o.TimedRows();o.LinkGhw(false);auto v=o.Capture();
      Check(v.variables.fields[2].present==true&&v.variables.fields[2].timed==true&&
            v.variables.fields[2].remaining_raw==-1,"Computed minus-one is genuinely timed");
      Check(v.object_links.ghw==links::State::present&&v.object_links.war==links::State::absent&&
            v.object_links.has_war_started==false,"GHW is distinct from its War");
      Emit(directory,"ghw-present-no-war-timed-minus-one",v);
    }
    {
      Owned o;o.TimedRows();o.LinkGhw(true);auto v=o.Capture();
      Check(v.object_links.available&&v.object_links.ghw==links::State::present&&
            v.object_links.war==links::State::present&&
            v.object_links.war_reference_full_id==Owned::war_id,"Real independent War DB link");
      Emit(directory,"ghw-independent-war-present",v);
    }
    {
      Owned o;o.TimedRows();o.missing_context=2;auto v=o.Capture();
      Check(!v.variables.fields[2].read_available&&!v.variables.fields[2].present&&
            v.variables.fields[2].failure==vars::Failure::context_unavailable,
            "Faith context failure cannot become false");
      Emit(directory,"ghw-faith-context-unknown",v);
    }
    {
      Owned o;o.TimedRows();o.LinkGhw(true);o.Put(Owned::war+8,Owned::war_id+0x01000000U);
      auto v=o.Capture();
      Check(!v.object_links.available&&v.object_links.stable_two_pass&&
            v.object_links.ghw==links::State::present&&v.object_links.war==links::State::unknown&&
            v.object_links.has_war_started==true&&
            v.object_links.failure==links::Failure::generation_mismatch,
            "Stable partial GHW must survive stale War generation");
      Emit(directory,"ghw-stale-war-retains-partial",v);
    }
    {
      Owned o;o.denied=Owned::faith+0x828;auto v=o.Capture();
      Check(!v.object_links.available&&v.object_links.ghw==links::State::unknown&&
            !v.object_links.ghw_reference_full_id&&
            v.object_links.failure==links::Failure::memory_unreadable,
            "Unread reference cannot become absent");
      Emit(directory,"ghw-unread-reference-unknown",v);
    }
    {
      Owned o;o.Row(2,0,102,20);auto v=o.Capture();
      Check(v.variables.fields[2].present==true&&v.variables.fields[2].timed==true&&
            v.variables.fields[2].remaining_raw==0&&!v.variables.fields[2].expiry_date_raw,
            "Zero counter retains source presence without invented date");
      Emit(directory,"ghw-timed-zero",v);
    }
    {
      Owned o;o.TimedRows();o.LinkGhw(true);auto v=o.Capture();
      v.available=false;v.frame_verified=false;v.unavailable_reason="fixture_outer_identity_changed";
      Emit(directory,"ghw-outer-rejected-clears-current-facts",v);
    }
    {
      Owned o;o.TimedRows();o.LinkGhw(true);auto v=o.Capture();
      v.available=false;v.loaded_source_pins_verified=false;
      v.unavailable_reason="fixture_loaded_pins_not_admitted";
      Emit(directory,"ghw-unverified-pins-clears-current-facts",v);
    }
    std::cerr<<"PROVENANCE: compile-time canonical SHA checks; optional full binder test only if macro enabled; "
        "9 actual two-reader->production-serializer fixture bodies; "
        "owned byte regions; simulated outer metadata/pin admission; no actual loaded module, "
        "TLS/mailbox/process/runtime qualification; no CK3 IO\n";
    return 0;
  }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
