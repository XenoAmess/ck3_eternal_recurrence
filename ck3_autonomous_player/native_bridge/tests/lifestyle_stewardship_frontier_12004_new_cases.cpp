#include "xar_bridge/player_lifestyle_stewardship_frontier_v2.hpp"
#include "xar_bridge/ck3_12004_lifestyle.hpp"
#include <array>
#include <cstring>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {
using namespace xar::ck3_11906;
namespace life = xar::ck3_12004::lifestyle;
using Status = StockPerkLegalityStatusV1;
using Key = xar::game::PlayerLifestyleWindowStableKeyV1;
void Require(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
template<class T, std::size_t N>
void Put(std::array<std::byte, N> &data, std::size_t at, T value) {
  Require(at+sizeof(T)<=N,"fixture bounds");
  std::memcpy(data.data()+at,&value,sizeof(T));
}
Key MakeKey(std::string_view text) {
  Key key{};key.size=static_cast<std::uint16_t>(text.size());
  std::memcpy(key.bytes.data(),text.data(),text.size());return key;
}
std::string_view View(const Key &key) {return {key.bytes.data(),key.size};}
struct Fixture {
  static constexpr std::uintptr_t module=0x1000000000ULL;
  std::array<std::byte,0x90> database{};
  std::array<std::array<std::byte,0x460>,27> definitions{};
  std::array<std::array<char,64>,27> keys{};
  std::array<std::uintptr_t,27> rows{};
  std::array<std::byte,0x50> lifestyle{};
  std::array<char,64> lifestyle_key{};
  std::array<std::byte,0x30> character{};
  StockPerkLegalityFrameV1 frame{};
  std::array<bool,27> legal{};
  std::array<bool,27> owned{};
  int unavailable_index=-1;
  int calls=0, captures=0;
  bool command_valid=true, main=true, drift=false;
  static Fixture *active;
  Fixture() {
    for(std::size_t i=0;i<27;++i) {
      const auto key=kStewardshipPerkPriorityV2[i];
      std::memcpy(keys[i].data(),key.data(),key.size());
      rows[i]=reinterpret_cast<std::uintptr_t>(definitions[i].data());
      Put(definitions[i],0x18,reinterpret_cast<std::uintptr_t>(keys[i].data()));
      Put(definitions[i],0x28,static_cast<std::uint64_t>(key.size()));
      Put(definitions[i],0x30,std::uint64_t{63});
      Put(definitions[i],0x440,reinterpret_cast<std::uintptr_t>(lifestyle.data()));
      owned[i]=i<4;
    }
    constexpr std::string_view life_key="stewardship_lifestyle";
    std::memcpy(lifestyle_key.data(),life_key.data(),life_key.size());
    Put(lifestyle,0x18,reinterpret_cast<std::uintptr_t>(lifestyle_key.data()));
    Put(lifestyle,0x28,static_cast<std::uint64_t>(life_key.size()));
    Put(lifestyle,0x30,std::uint64_t{63});
    Put(database,0x50,reinterpret_cast<std::uintptr_t>(rows.data()));
    Put(database,0x58,std::int32_t{27});Put(database,0x5c,std::int32_t{27});
    Put(character,0x18,std::uint32_t{40526});
    std::memcpy(frame.episode_run_id.data(),"native-40526-fixture",20);
    std::memcpy(frame.snapshot_id.data(),"native:7",9);
    frame.public_revision=7;frame.native_revision=7;frame.proof_epoch=7;
    frame.date_raw=53411184;frame.played_character_id=40526;
    frame.played_character=reinterpret_cast<std::uintptr_t>(character.data());
    frame.paused=true;frame.map_ready=true;frame.played_character_alive=true;
    frame.storage_round_trip=true;active=this;
  }
  template<class T> static bool Copy(std::uintptr_t address,void *out,
                                    std::size_t bytes,const T &object) noexcept {
    const auto begin=reinterpret_cast<std::uintptr_t>(object.data());
    if(address<begin||bytes>sizeof(object)||address-begin>sizeof(object)-bytes)return false;
    std::memcpy(out,reinterpret_cast<const std::byte *>(object.data())+address-begin,bytes);return true;
  }
  static bool Read(void *opaque,std::uintptr_t address,void *out,std::size_t bytes) noexcept {
    const auto &f=*static_cast<Fixture *>(opaque);
    const std::uint32_t player=40526;const auto validator=module+0x288AE00;
    if(address==module+0x54DBC00&&bytes==sizeof(player)){std::memcpy(out,&player,bytes);return true;}
    if(address==module+0x4760A30&&bytes==sizeof(validator)){std::memcpy(out,&validator,bytes);return true;}
    if(Copy(address,out,bytes,f.database)||Copy(address,out,bytes,f.rows)||
       Copy(address,out,bytes,f.lifestyle)||Copy(address,out,bytes,f.lifestyle_key)||
       Copy(address,out,bytes,f.character))return true;
    for(std::size_t i=0;i<27;++i)
      if(Copy(address,out,bytes,f.definitions[i])||Copy(address,out,bytes,f.keys[i]))return true;
    return false;
  }
  static bool Main(void *p) noexcept{return static_cast<Fixture *>(p)->main;}
  static bool Capture(void *p,StockPerkLegalityFrameV1 &out) noexcept {
    auto &f=*static_cast<Fixture *>(p);++f.captures;out=f.frame;
    // The actual formal capture withdraws its bound frame after a date change.
    // Source-fact collectors may perform extra captures; do not count them as
    // though they were the final validator's three mandatory captures.
    return !f.drift || f.frame.date_raw==53411184;
  }
  static bool Player(void *p,const StockPerkLegalityFrameV1 &,
                     std::uintptr_t target,std::string_view key,
                     StockPerkLegalityPlayerStateV1 &out) noexcept {
    auto &f=*static_cast<Fixture *>(p);
    if(target!=reinterpret_cast<std::uintptr_t>(f.lifestyle.data()))return false;
    for(std::size_t i=0;i<27;++i)if(kStewardshipPerkPriorityV2[i]==key) {
      if(static_cast<int>(i)==f.unavailable_index)return false;
      out={};out.target_lifestyle_key=MakeKey("stewardship_lifestyle");
      out.target_xp_total_raw=1000;out.target_xp_within_level_raw=0;
      out.target_xp_per_level=1000;out.unspent_perk_points=1;out.used_perk_points=4;
      out.owned_perk_state_known=true;out.target_perk_owned=f.owned[i];return true;
    }
    return false;
  }
  static void *Database(){return active->database.data();}
  static bool Validate(void *opaque,void *context) {
    auto &f=*active;++f.calls;const auto *p=static_cast<const std::byte *>(opaque);
    if(f.drift)f.frame.date_raw+=24;
    std::uintptr_t primary=0,secondary=0,definition=0;std::uint32_t player=0;
    std::memcpy(&primary,p,sizeof(primary));std::memcpy(&secondary,p+0x18,sizeof(secondary));
    std::memcpy(&player,p+0x20,sizeof(player));std::memcpy(&definition,p+0x28,sizeof(definition));
    f.command_valid=f.command_valid&&context==nullptr&&primary==module+0x4760A00&&
        secondary==module+0x47609D0&&player==40526;
    for(std::size_t i=0;i<27;++i)if(f.rows[i]==definition)return f.legal[i];
    f.command_valid=false;return false;
  }
  StockPerkLegalityResultV1 Target(std::string_view key) {
    active=this;
    StockPerkLegalityEnvironmentV1 env{true,xar::ck3_12004::kExecutableSha256,module,true,&Database,&Validate};
    StockPerkLegalityAccessV1 access{};access.context=this;access.is_application_main_thread=&Main;
    access.capture_frame=&Capture;access.read_memory=&Read;access.read_target_player_state=&Player;
    return life::ReadStockPerkLegality12004V1(env,access,key);
  }
  StockPerkLegalityResultV1 Frontier(bool submit=false,std::string_view key={}) {
    return ReadLifestylePolicyPerkFrontierV2(submit,key,true,{},[&](std::string_view target)noexcept{return Target(target);});
  }
};
Fixture *Fixture::active=nullptr;
}

int RunStewardshipFrontierFixture() {
  try {
    Require(kStewardshipPerkPriorityV2.size()==27,"complete vanilla catalogue");
    for(std::size_t i=0;i<27;++i)for(std::size_t j=0;j<i;++j)
      Require(kStewardshipPerkPriorityV2[i]!=kStewardshipPerkPriorityV2[j],"unique catalogue");
    Fixture first;first.legal[4]=true;const auto next=first.Frontier();
    Require(next.status==Status::observed_native_legal&&View(next.target_key)=="defensive_measures_perk"&&
            first.calls==10&&next.validator_invoked_twice&&first.command_valid,"old four owned must reach genuine next legal perk");
    Fixture wealth;wealth.legal[9]=true;const auto wealth_row=wealth.Frontier();
    Require(wealth_row.status==Status::observed_native_legal&&View(wealth_row.target_key)=="golden_obligations_perk"&&wealth.calls==20,"wealth branch fallback");
    Fixture duty;duty.legal[26]=true;const auto duty_row=duty.Frontier();
    Require(duty_row.status==Status::observed_native_legal&&View(duty_row.target_key)=="administrator_perk"&&duty.calls==54,"last authored duty candidate covered");
    Fixture illegal;const auto none=illegal.Frontier();
    Require(none.status==Status::observed_native_illegal&&illegal.calls==54,"all27 genuine double-read negatives");
    Fixture missing;missing.unavailable_index=4;const auto partial=missing.Frontier();
    Require(partial.status!=Status::observed_native_illegal&&partial.status!=Status::observed_native_legal,"one unavailable cannot masquerade as all illegal");
    Fixture later;later.unavailable_index=4;later.legal[9]=true;const auto known=later.Frontier();
    Require(known.status==Status::observed_native_legal&&View(known.target_key)=="golden_obligations_perk","independent later legal survives earlier unknown");
    Fixture exact;exact.legal[4]=true;exact.legal[8]=true;const auto chosen=exact.Frontier(true,"architect_perk");
    Require(chosen.status==Status::observed_native_legal&&View(chosen.target_key)=="architect_perk"&&exact.calls==2,"submit revalidates exact requested target only");
    exact.calls=0;exact.legal[8]=false;const auto changed=exact.Frontier(true,"architect_perk");
    Require(changed.status==Status::observed_native_illegal&&View(changed.target_key)=="architect_perk"&&exact.calls==2,"submit never switches to other legal target after changed legality");
    Fixture drift;drift.drift=true;drift.legal[4]=true;const auto stale=drift.Frontier();
    Require(stale.status!=Status::observed_native_legal,"drift never admitted");
    Fixture worker;worker.main=false;const auto wrong_thread=worker.Target("defensive_measures_perk");
    Require(wrong_thread.status==Status::unavailable_binding&&worker.calls==0,"owner thread guard retained");
    Fixture arbitrary;const auto rejected=arbitrary.Target("invented_perk");
    Require(rejected.status==Status::unavailable_candidate&&arbitrary.calls==0,"arbitrary key remains rejected");
    return 12;
  } catch(const std::exception &error) {
    std::fprintf(stderr,"STEWARDSHIP_FIXTURE_RED: %s\n",error.what());return -1;
  }
}
