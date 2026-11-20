// Reuse the existing real reader fixture and all its owner/generation/drift guards.
#define main OriginalReadonlyMainForGoldV2
#include "ck3_121003_readonly26785313_static_test.cpp"
#undef main
#include "xar_bridge/ck3_121003_personal_gold26785313_v2.hpp"
#include <limits>

namespace {
f::ReadonlyObservation GoldData() {
  f::ReadonlyObservation in{};in.available=true;in.main_owner_observed=true;
  in.core.clock={53176992,3,true};in.core.local_player_id=7;in.core.map_ready=true;
  in.core.has_played_character=true;in.core.played_character_id=-16777215;
  in.core.played_character_alive=true;in.raw_resources=f::RawResources{};
  in.raw_resources->personal_gold_raw=-12345;return in;
}
bool Available(std::string_view result) {
  return result.find("\"personal_gold_available\":true")!=std::string_view::npos;
}
std::string Emit(const f::ReadonlyObservation &in,const xar::game::AdapterDescriptor &d) {
  return f::SerializePersonalGoldCommandResultV2("gold-v2-nogame-DATA",in,d);
}
#if defined(XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2)
void Write(const std::filesystem::path &root,const char *name,const std::string &body) {
  std::ofstream out(root/name,std::ios::binary);Require(bool(out),"golden output open");
  out<<body<<'\n';Require(bool(out),"golden output write");
}
#endif
}
int main(int argc,char **argv) {
  try {
    Require(argc==2||argc==3,"explicit synthetic image/disk EXE and optional output directory");
    Require(OriginalReadonlyMainForGoldV2(2,argv)==0,"original unchanged reader/Core guard suite");
    const auto &d=f::PersonalGoldAdapterDescriptorV2();auto in=GoldData();
#if defined(XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2)
    Require(f::PersonalGoldRouteEnabledV2(d),"current V2 opt-in profile");
    Require(f::PersonalGoldStepCapabilityV2(d,f::kPersonalGoldStepV2)==f::kPersonalGoldCapabilityV2,"exact V2 dispatch mapping");
    Require(f::PersonalGoldStepCapabilityV2(d,c::kCoreFrameStepV1).empty(),"V2 cannot claim Core dispatch");
    const auto partial=Emit(in,d);Require(Available(partial),"hand-authored mapper DATA only");
    Require(partial.find("\"personal_gold\":{\"raw\":\"-12345\",\"scale\":100000}")!=std::string::npos,"raw signed64 string and actual scale");
    Require(!f::CoreRouteObservationV1(in).core_available,"Core-only still refuses resource-bearing observation");
    auto bad=d;bad.executable_sha256=c::kExecutableSha256;Require(!Available(Emit(in,bad)),"old 2F2 exact tuple denied");
    bad=d;bad.executable_sha256="BB3FEF106240E95ECDB6F1532982E89E9432C92A99D33DB623521572F06E6F79";Require(!Available(Emit(in,bad)),"BB3 denied");
    bad=d;bad.adapter_id="wrong";Require(!Available(Emit(in,bad)),"wrong adapter denied");
    bad=d;bad.game_version="1.21.0";Require(!Available(Emit(in,bad)),"wrong version denied");
    bad=d;bad.capabilities={};Require(!Available(Emit(in,bad)),"missing V2 capability denied");
    auto reject=GoldData();reject.core.clock.paused=false;Require(!Available(Emit(reject,d)),"unpaused denied");
    reject=GoldData();reject.main_owner_observed=false;Require(!Available(Emit(reject,d)),"missing owner denied");
    reject=GoldData();reject.offline_fixture=true;Require(!Available(Emit(reject,d)),"offline fixture never live partial");
    reject=GoldData();reject.core.map_ready=false;Require(!Available(Emit(reject,d)),"missing map denied");
    reject=GoldData();reject.core.has_played_character=false;Require(!Available(Emit(reject,d)),"missing actor denied");
    reject=GoldData();reject.core.played_character_alive=false;Require(!Available(Emit(reject,d)),"dead actor denied");
    reject=GoldData();reject.core.played_character_id=-1;Require(!Available(Emit(reject,d)),"invalid actor denied");
    reject=GoldData();reject.partial=false;Require(!Available(Emit(reject,d)),"nonpartial source denied");
    reject=GoldData();reject.available=false;Require(!Available(Emit(reject,d)),"reader unavailable denied");
    reject=GoldData();reject.raw_resources.reset();Require(!Available(Emit(reject,d)),"missing raw amount denied");
    PeWindows pe;const auto base=reinterpret_cast<std::uintptr_t>(pe.image);f::ReadonlyObservation observed{};
    {Fixture fixture;Require(Run(fixture,base,observed)&&observed.available&&!Available(Emit(observed,d)),"real NoGame reader cannot grant main owner");}
    {Fixture fixture;fixture.drift=true;Require(Run(fixture,base,observed)&&!observed.available&&!Available(Emit(observed,d)),"actual amount drift rejected");}
    {Fixture fixture;fixture.actor_drift=true;Require(Run(fixture,base,observed)&&!observed.available&&!Available(Emit(observed,d)),"actual full generation drift rejected");}
    {Fixture fixture;Put(fixture.actor,0x18,std::int32_t{-16777214});Require(Run(fixture,base,observed)&&!observed.available,"wrong full actor generation rejected");}
    {Fixture fixture;Require(Run(fixture,base,observed,false)&&!observed.available&&fixture.calls==0,"wrong owner context rejected before actor read");}
    {Fixture fixture;Put(fixture.actor,0x1B0,std::uintptr_t{0});Require(Run(fixture,base,observed)&&observed.available&&observed.raw_resources->personal_gold_raw==0,"native null-living zero branch");}
    if(argc==3) {
      const std::filesystem::path output=argv[2];Require(std::filesystem::is_directory(output),"caller-created golden directory");
      Write(output,"personal-gold-v2-partial.json",partial);
      reject=GoldData();reject.main_owner_observed=false;Write(output,"personal-gold-v2-unavailable.json",Emit(reject,d));
      for(const auto value:{(std::numeric_limits<std::int64_t>::min)(),std::int64_t{-1},std::int64_t{0},std::int64_t{1},(std::numeric_limits<std::int64_t>::max)()}) {
        auto boundary=GoldData();boundary.raw_resources->personal_gold_raw=value;
        Write(output,("personal-gold-v2-raw-"+std::to_string(value)+".json").c_str(),Emit(boundary,d));
      }
    }
    std::cout<<"PASS V2 ON exact tuple/raw64-string/scale/paused/owner/map/actor/drift; hand-authored DATA golden, LIVE NOT_RUN\n";
#else
    Require(!f::PersonalGoldRouteEnabledV2(d)&&!Available(Emit(in,d)),"defaultOFF denies V2");
    std::array<std::string_view,2> fake_caps{c::kCoreFrameCapabilityV1,f::kPersonalGoldCapabilityV2};
    auto fake=d;fake.capabilities=fake_caps;Require(!Available(Emit(in,fake)),"copied capability cannot enable compile-time OFF");
    Require(f::PersonalGoldStepCapabilityV2(fake,f::kPersonalGoldStepV2).empty(),"defaultOFF V2 dispatch closed");
    std::cout<<"PASS V2 defaultOFF remains unavailable even with copied capability; LIVE NOT_RUN\n";
#endif
    return 0;
  } catch(const std::exception &e) {std::cerr<<e.what()<<'\n';return 1;}
}
