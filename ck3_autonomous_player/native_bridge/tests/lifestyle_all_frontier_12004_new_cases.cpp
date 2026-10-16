#include "xar_bridge/player_lifestyle_all_frontier_v3.hpp"
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
  std::array<std::array<std::byte,0x460>,162> definitions{};
  std::array<std::array<char,64>,162> keys{};
  std::array<std::uintptr_t,162> rows{};
  std::array<std::array<std::byte,0x150>,6> lifestyles{};
  std::array<std::int32_t,6> points{};
  std::array<std::array<char,64>,6> lifestyle_keys{};
  std::array<std::byte,0x30> character{};
  StockPerkLegalityFrameV1 frame{};
  std::array<bool,162> legal{};
  std::array<bool,162> owned{};
  int unavailable_index=-1;
  int calls=0, captures=0;
  bool command_valid=true, main=true, drift=false;
  static Fixture *active;
  static std::size_t LifeIndex(std::string_view key) {
    for(std::size_t i=0;i<6;++i)if(kAllLifestyleKeysV3[i]==key)return i;
    throw std::runtime_error("unknown lifestyle");
  }
  Fixture() {
    for(std::size_t i=0;i<6;++i) {
      const auto key=kAllLifestyleKeysV3[i];
      std::memcpy(lifestyle_keys[i].data(),key.data(),key.size());
      Put(lifestyles[i],0x18,reinterpret_cast<std::uintptr_t>(lifestyle_keys[i].data()));
      Put(lifestyles[i],0x28,static_cast<std::uint64_t>(key.size()));
      Put(lifestyles[i],0x30,std::uint64_t{63});
    }
    for(std::size_t i=0;i<162;++i) {
      const auto key=kAllLifestylePerksV3[i].key;
      std::memcpy(keys[i].data(),key.data(),key.size());
      rows[i]=reinterpret_cast<std::uintptr_t>(definitions[i].data());
      Put(definitions[i],0x18,reinterpret_cast<std::uintptr_t>(keys[i].data()));
      Put(definitions[i],0x28,static_cast<std::uint64_t>(key.size()));
      Put(definitions[i],0x30,std::uint64_t{63});
      Put(definitions[i],0x440,reinterpret_cast<std::uintptr_t>(lifestyles[LifeIndex(kAllLifestylePerksV3[i].lifestyle)].data()));
      owned[i]=false;
    }
    Put(database,0x50,reinterpret_cast<std::uintptr_t>(rows.data()));
    Put(database,0x58,std::int32_t{162});Put(database,0x5c,std::int32_t{162});
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
       Copy(address,out,bytes,f.lifestyles)||Copy(address,out,bytes,f.lifestyle_keys)||
       Copy(address,out,bytes,f.character))return true;
    for(std::size_t i=0;i<162;++i)
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

    for(std::size_t i=0;i<162;++i)if(kAllLifestylePerksV3[i].key==key) {
      if(static_cast<int>(i)==f.unavailable_index)return false;
      const auto index=LifeIndex(kAllLifestylePerksV3[i].lifestyle);
      if(target!=reinterpret_cast<std::uintptr_t>(f.lifestyles[index].data()))return false;
      out={};out.target_lifestyle_key=MakeKey(kAllLifestyleKeysV3[index]);
      out.target_xp_total_raw=1000;out.target_xp_within_level_raw=0;
      out.target_xp_per_level=1000;out.unspent_perk_points=f.points[index];out.used_perk_points=4;
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
    for(std::size_t i=0;i<162;++i)if(f.rows[i]==definition)return f.legal[i];
    f.command_valid=false;return false;
  }
  StockPerkLegalityResultV1 Target(std::string_view key,bool progress=false) {
    active=this;
    StockPerkLegalityEnvironmentV1 env{true,xar::ck3_12004::kExecutableSha256,module,true,&Database,&Validate};
    StockPerkLegalityAccessV1 access{};access.context=this;access.is_application_main_thread=&Main;
    access.capture_frame=&Capture;access.read_memory=&Read;access.read_target_player_state=&Player;
    return progress?life::ReadStockPerkProgress12004V3(env,access,key):life::ReadStockPerkLegality12004V1(env,access,key);
  }
  std::array<StockPerkLegalityResultV1,6> Progress() {
    std::array<StockPerkLegalityResultV1,6> progress_rows{};
    for(std::size_t i=0;i<6;++i)for(const auto &e:kAllLifestylePerksV3)if(e.lifestyle==kAllLifestyleKeysV3[i]) {
      progress_rows[i]=Target(e.key,true);break;
    }
    return progress_rows;
  }
  std::size_t Index(std::string_view key) {
    for(std::size_t i=0;i<162;++i)if(kAllLifestylePerksV3[i].key==key)return i;
    throw std::runtime_error("unknown perk");
  }
  StockPerkLegalityResultV1 Frontier(std::string_view current="stewardship_lifestyle") {
    return ReadAllLifestylePerkFrontierV3(Progress(),current,[&](std::string_view key)noexcept{return Target(key);});
  }
};
Fixture *Fixture::active=nullptr;
}

namespace life = xar::ck3_12004::lifestyle;
namespace xar::ck3_12004::lifestyle {
std::string RenderPlayerLifestyle12004(std::string_view,std::string_view,
    const PlayerLifestyleFormalWireContext12004V1 &,const game::AdapterDescriptor &);
}
static std::string rendered;
const char *AllLifestyleRenderedQueryFixture() {return rendered.c_str();}
int RunAllLifestyleFixture() {
 try {
  int checks=0;
  Require(kAllLifestylePerksV3.size()==162 && kAllLifestyleKeysV3.size()==6,"actual full catalogue");++checks;
  for(std::size_t i=0;i<162;++i)for(std::size_t j=0;j<i;++j)Require(kAllLifestylePerksV3[i].key!=kAllLifestylePerksV3[j].key,"unique perk key");++checks;
  auto zero_ptr=std::make_unique<Fixture>();auto &zero=*zero_ptr;const auto progress=zero.Progress();
  Require(zero.calls==0 && std::all_of(progress.begin(),progress.end(),LifestyleProgressObservedV3),"six double native progress getters no CanPick");++checks;
  const auto empty=zero.Frontier();Require(empty.status==Status::observed_native_illegal && zero.calls==0,"zero points skip all162 final validators");++checks;
  for(std::size_t l=0;l<6;++l) {
    auto f_ptr=std::make_unique<Fixture>();auto &f=*f_ptr;f.points[l]=1;std::string_view last;
    for(const auto &e:kAllLifestylePerksV3)if(e.lifestyle==kAllLifestyleKeysV3[l])last=e.key;
    f.legal[f.Index(last)]=true;const auto found=f.Frontier();
    Require(found.status==Status::observed_native_legal && View(found.lifestyle_key)==kAllLifestyleKeysV3[l] && View(found.target_key)==last && found.validator_invoked_twice && f.calls==54 && f.command_valid,"all six complete frontier incl last tree/native double validate");++checks;
  }
  auto legacy_ptr=std::make_unique<Fixture>();auto &legacy=*legacy_ptr;legacy.points[0]=1;legacy.legal[legacy.Index("thoughtful_perk")]=true;auto old=legacy.Frontier("stewardship_lifestyle");
  Require(old.status==Status::observed_native_legal && View(old.lifestyle_key)=="diplomacy_lifestyle" && legacy.calls==2,"current focus zero old diplomacy point consumed");++checks;
  auto priority_ptr=std::make_unique<Fixture>();auto &priority=*priority_ptr;priority.points[0]=1;priority.points[4]=1;priority.legal[priority.Index("thoughtful_perk")]=true;priority.legal[priority.Index("cutting_corners_perk")]=true;
  Require(View(priority.Frontier().target_key)=="cutting_corners_perk" && priority.calls==2,"positive current focus priority");++checks;
  auto dlc_ptr=std::make_unique<Fixture>();auto &dlc=*dlc_ptr;dlc.points[5]=1;const auto denied=dlc.Frontier();Require(denied.status==Status::observed_native_illegal && dlc.calls==54,"authored wanderer does not bypass native DLC refusal");++checks;
  auto partial_ptr=std::make_unique<Fixture>();auto &partial=*partial_ptr;auto partial_rows=partial.Progress();partial_rows[2].status=Status::unavailable_state;
  auto unavailable=ReadAllLifestylePerkFrontierV3(partial_rows,"stewardship_lifestyle",[&](std::string_view k)noexcept{return partial.Target(k);});
  Require(!LifestyleProgressObservedV3(unavailable) && partial.calls==0,"unknown class progress not global negative");++checks;
  partial.points[0]=1;partial.legal[partial.Index("thoughtful_perk")]=true;partial_rows=partial.Progress();partial_rows[2].status=Status::unavailable_state;
  auto independently_legal=ReadAllLifestylePerkFrontierV3(partial_rows,"stewardship_lifestyle",[&](std::string_view k)noexcept{return partial.Target(k);});
  Require(independently_legal.status==Status::observed_native_legal,"partial may preserve independently legal positive row");++checks;
  auto exact_ptr=std::make_unique<Fixture>();auto &exact=*exact_ptr;exact.points[2]=1;exact.legal[exact.Index("erudite_perk")]=true;const auto selected=exact.Target("erudite_perk");
  Require(selected.status==Status::observed_native_legal && exact.calls==2,"exact full catalogue submit recheck");++checks;
  exact.legal[exact.Index("erudite_perk")]=false;exact.legal[exact.Index("pedagogy_perk")]=true;exact.calls=0;
  Require(exact.Target("erudite_perk").status==Status::observed_native_illegal && exact.calls==2,"changed exact target never substituted");++checks;
  auto worker_ptr=std::make_unique<Fixture>();auto &worker=*worker_ptr;worker.main=false;Require(worker.Target("erudite_perk",true).status==Status::unavailable_binding && worker.calls==0,"progress owner guard");++checks;
  auto unknown_ptr=std::make_unique<Fixture>();auto &unknown=*unknown_ptr;Require(unknown.Target("invented_perk").status==Status::unavailable_candidate && unknown.calls==0,"unknown key rejected");++checks;
  auto drift_ptr=std::make_unique<Fixture>();auto &drift=*drift_ptr;drift.points[0]=1;drift.drift=true;drift.legal[drift.Index("thoughtful_perk")]=true;Require(drift.Target("thoughtful_perk").status!=Status::observed_native_legal,"native frame drift refused");++checks;
  auto snapshot_ptr=std::make_unique<xar::game::PlayerLifestyleSnapshotV1>();auto &snapshot=*snapshot_ptr;snapshot.status=xar::game::PlayerLifestyleSnapshotStatusV1::available;
  snapshot.readiness.current_focus_ready=true;snapshot.readiness.owned_perks_ready=true;snapshot.readiness.same_frame_ready=true;
  snapshot.snapshot_id=old.frame.snapshot_id;snapshot.public_revision=7;snapshot.native_revision=7;snapshot.proof_epoch=7;snapshot.date_raw=old.frame.date_raw;snapshot.player_character_id=40526;
  snapshot.state.current_focus_presence=xar::game::PlayerLifestyleFocusPresenceV1::present;
  AssignPlayerLifestyleStableKeyV1("stewardship_wealth_focus",snapshot.state.current_focus_key);
  auto observation_ptr=std::make_unique<xar::game::PlayerLifestyleSelectionStateObservationV1>();auto &observation=*observation_ptr;
  Require(BuildAllLifestylePerkObservationV3(snapshot,old,"native-40526-fixture",observation)==PlayerLifestyleFormalPreconditionResultV1::ready && View(observation.lifestyle_progress[0].lifestyle_key)=="diplomacy_lifestyle" && observation.lifestyle_progress[0].perk_points==1 && View(observation.current_focus_key)=="stewardship_wealth_focus","precondition uses actual target points preserves current focus");++checks;
  auto post_ptr=std::make_unique<Fixture>();auto &post=*post_ptr;post.points[0]=0;post.owned[post.Index("thoughtful_perk")]=true;auto after=post.Target("thoughtful_perk",true);
  Require(BuildAllLifestylePerkObservationV3(snapshot,after,"native-40526-fixture",observation)==PlayerLifestyleFormalPreconditionResultV1::ready && observation.lifestyle_progress[0].perk_points==0 && after.observed_target_owned,"independent post owned/old-lifestyle points reread");++checks;
  after.frame.date_raw+=24;Require(BuildAllLifestylePerkObservationV3(snapshot,after,"native-40526-fixture",observation)==PlayerLifestyleFormalPreconditionResultV1::frame_mismatch,"receipt frame bound");++checks;
  auto context_ptr=std::make_unique<life::PlayerLifestyleFormalWireContext12004V1>();auto &context=*context_ptr;context.completed=true;context.mode=PlayerLifestyleFormalWireModeV1::query;
  context.snapshot=std::make_unique<xar::game::PlayerLifestyleSnapshotV1>(snapshot);context.episode_run_id="native-40526-fixture";context.snapshot_id="native:7";context.expected_revision=7;context.expected_snapshot.date_raw=snapshot.date_raw;context.expected_snapshot.played_character_id=40526;context.all_lifestyle_progress_v3=legacy.Progress();context.precondition_result=PlayerLifestyleFormalPreconditionResultV1::ready;
  context.snapshot->state.legal_perk_candidate_status=xar::game::PlayerLifestyleCandidateCollectionStatusV1::available;
  context.snapshot->state.legal_perk_candidates_policy_scoped=true;context.snapshot->state.legal_perk_candidate_count=1;
  AssignPlayerLifestyleStableKeyV1("thoughtful_perk",context.snapshot->state.legal_perk_candidates[0].key);AssignPlayerLifestyleStableKeyV1("diplomacy_lifestyle",context.snapshot->state.legal_perk_candidates[0].lifestyle_key);
  auto candidates_ptr=std::make_unique<xar::game::PlayerLifestyleWindowCandidatesV1>();
  auto &candidates=*candidates_ptr;
  candidates.status=xar::game::PlayerLifestyleWindowCandidatesStatusV1::available;
  candidates.snapshot_id=snapshot.snapshot_id;candidates.public_revision=7;candidates.native_revision=7;candidates.proof_epoch=7;candidates.date_raw=snapshot.date_raw;candidates.player_character_id=40526;
  candidates.focus_status=xar::game::PlayerLifestyleWindowCollectionStatusV1::unavailable;candidates.perk_status=xar::game::PlayerLifestyleWindowCollectionStatusV1::available;
  candidates.perk_count=1;candidates.perks[0]={old.target_key,old.lifestyle_key,true,false};
  candidates.readiness.perk_candidates_ready=true;candidates.readiness.final_legality_ready=true;candidates.readiness.same_frame_ready=true;
  context.snapshot->state.legal_perk_candidate_count=0;
  Require(AttachPlayerLifestyleFinalCandidatesV1(candidates,*context.snapshot)==PlayerLifestyleFormalPreconditionResultV1::ready && context.snapshot->readiness.legal_perk_candidates_ready,"actual candidate attachment sets formal readiness");++checks;
  rendered=life::RenderPlayerLifestyle12004("fixture-query",kPlayerLifestyleFormalPrivateQueryStepV1,context,xar::game::AdapterDescriptor{});
  Require(rendered.find("all_lifestyle_progress_v3")!=std::string::npos,"actual query serializer linked");++checks;
  return checks;
 }catch(const std::exception &e){std::fprintf(stderr,"ALL_LIFESTYLE_RED: %s\n",e.what());return -1;}
}
