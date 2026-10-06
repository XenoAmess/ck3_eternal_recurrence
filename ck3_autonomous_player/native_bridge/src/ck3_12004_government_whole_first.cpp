#include "xar_bridge/ck3_12004_government_runtime_binder.hpp"
#include "xar_bridge/government_runtime_adapter_bridge_binder_v1.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

// New whole-wire fixture for the actual .4 collector and existing source
// adapter. It uses owned memory and callbacks; it opens no game or process.
namespace {
namespace current = xar::ck3_12004;
namespace observer = xar::bridge::private_observer;
namespace game = xar::game;
constexpr std::int32_t kActor = 29'829;
constexpr std::uint64_t kRevision = 701;
constexpr std::int32_t kDate = 1'220'410;
// Captured 176-byte actual .4 native registry, an input fixture fact.
constexpr std::array<std::uint32_t, 44> kRegistry{
    0x3587,0x3588,0x34A7,0x3538,0x3539,0x3270,0x366D,0x34DC,
    0x3773,0x3608,0x37CF,0x37CE,0x36C4,0x377A,0x35E0,0x394A,
    0x3B0A,0x3A5B,0x3A09,0x3A08,0x3953,0x3A00,0x3A02,0x3A01,
    0x39DA,0x3CBB,0x3A07,0x3C98,0x3CA1,0x3A06,0x39F7,0x3D67,
    0x39ED,0x39EE,0x39EF,0x39F0,0x39DB,0x39DC,0x39DD,0x39DE,
    0x39DF,0x4101,0x4102,0x4169};
template<class Value> void Put(void* target, std::size_t offset, Value value) {
  std::memcpy(static_cast<std::byte*>(target)+offset, &value, sizeof(value));
}
struct Fixture;
Fixture* active_fixture = nullptr;
struct Fixture {
  std::array<std::byte,0x40> storage{};
  std::vector<std::byte> slots{static_cast<std::size_t>(kActor+1)*0x10};
  std::array<std::byte,0x1D8> character{};
  std::array<std::byte,0x70> government{};
  std::array<std::byte,0x2C0> features{};
  std::array<std::byte,0x20> dlc{};
  std::array<std::byte,0x20> state{}, jomini{};
  std::array<std::int32_t,2> flag_ids{1,2};
  std::array<std::string,2> flag_names{
      "government_uses_domain_limit", "government_is_feudal"};
  std::vector<std::string> feature_names;
  std::string key = "feudal_government";
  void* storage_pointer = storage.data();
  void* state_pointer = state.data();
  void* jomini_pointer = jomini.data();
  void* feature_pointer = features.data();
  void* fallback_pointer = nullptr;
  current::GovernmentRuntimeBindingsV1 bindings{};
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  bool drift = false;
  std::uint32_t samples = 0;
  explicit Fixture(bool change) : drift(change) {
    Put(storage.data(),0x20,slots.data());
    Put(storage.data(),0x2C,kActor+1);
    Put(slots.data(),static_cast<std::size_t>(kActor)*0x10+8,character.data());
    Put(character.data(),0x18,kActor);
    Put(government.data(),0x50,flag_ids.data());
    Put(government.data(),0x5C,std::int32_t{2});
    SetKey("feudal_government");
    const auto names = observer::GovernmentRuntimeAdapterExpectedFeatureKeysV1(
        observer::GovernmentRuntimeAdapterBuildProfileV1::ck3_12004);
    for (const auto name : names) feature_names.emplace_back(name);
    stamp.thread_id=1; stamp.paused=true; stamp.date_raw=kDate;
    stamp.game_state=reinterpret_cast<std::uintptr_t>(state_pointer);
    stamp.jomini_state=reinterpret_cast<std::uintptr_t>(jomini_pointer);
    bindings.enabled=true;
    bindings.core.enabled=true;
    bindings.core.game_state_slot=&state_pointer;
    bindings.core.jomini_state_slot=&jomini_pointer;
    bindings.core.character_storage_slot=&storage_pointer;
    bindings.government_fallback_slot=&fallback_pointer;
    bindings.feature_root_slot=&feature_pointer;
    bindings.feature_registry=kRegistry.data();
    bindings.script_dlc_set=dlc.data();
  }
  void SetKey(std::string value) {
    key=std::move(value);
    // The production reader handles the same heap shape as Root's .4 source
    // witness: key at +18, size at string+10 and capacity at string+18.
    Put(government.data(),0x18,key.data());
    Put(government.data(),0x28,key.size());
    Put(government.data(),0x30,std::size_t{31});
  }
};
bool Main(void* raw) noexcept { return raw!=nullptr; }
bool Memory(void*,const void* source,void* output,std::size_t bytes) noexcept {
  if(source==nullptr || output==nullptr || bytes==0) return false;
  std::memcpy(output,source,bytes); return true;
}
void* Government(void* character) {
  return active_fixture!=nullptr && character==active_fixture->character.data()
      ? active_fixture->government.data() : nullptr;
}
const std::string* Identifier(std::int32_t id) {
  if(active_fixture==nullptr) return nullptr;
  if(id==1 || id==2) return &active_fixture->flag_names[static_cast<std::size_t>(id-1)];
  for(std::size_t index=0;index<kRegistry.size();++index)
    if(kRegistry[index]==static_cast<std::uint32_t>(id))
      return &active_fixture->feature_names[index];
  return nullptr;
}
bool CampaignFrame(void*,game::CampaignRootFrameV1& frame) noexcept {
  frame={}; frame.snapshot_revision=kRevision; frame.date_raw=kDate;
  frame.paused=true; frame.map_ready=true; frame.has_played_character=true;
  frame.played_character_alive=true; frame.played_character_id=kActor;
  return true;
}
bool FeatureFrame(void*,game::LoadedFeatureManifestFrameV1& frame) noexcept {
  frame={}; frame.snapshot_revision=kRevision; frame.date_raw=kDate;
  frame.paused=true; frame.map_ready=true; return true;
}
bool Capture(void* raw,observer::GovernmentRuntimeAdapterCollectorSampleV1& sample) noexcept {
  auto& fixture=*static_cast<Fixture*>(raw);
  if(++fixture.samples==2 && fixture.drift) fixture.SetKey("clan_government");
  xar::ck3_11906::CampaignRootAccessV1 campaign{};
  campaign.context=&fixture; campaign.capture_frame=CampaignFrame;
  campaign.is_main_thread=Main; campaign.read_memory=Memory;
  xar::ck3_11906::LoadedFeatureManifestAccessV1 features{};
  features.context=&fixture; features.capture_frame=FeatureFrame;
  features.is_main_thread=Main; features.read_memory=Memory;
  return current::ReadGovernmentRuntimeCollectorSampleV1(fixture.bindings,
      campaign,features,kRevision,fixture.stamp,sample);
}
std::string Envelope(const observer::GovernmentRuntimeAdapterSourceResultV1& result,
                     std::string_view request) {
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+
      std::string(request)+"\",\"ok\":true,\"result\":{\"step\":\""+
      std::string(observer::kGovernmentRuntimeAdapterV1Step)+
      "\",\"accepted\":true,\"private_build\":true,\"read_only\":true,"
      "\"advertised\":false,\"snapshot_revision\":701,\"government_runtime_adapter\":"+
      observer::SerializeGovernmentRuntimeAdapterSourceV1(result,
          observer::GovernmentRuntimeAdapterBuildProfileV1::ck3_12004,kRevision)+"}}";
}
bool Emit(const std::filesystem::path& directory,bool drift) {
  Fixture fixture(drift); active_fixture=&fixture;
  fixture.bindings.government=Government;
  fixture.bindings.identifier_name=Identifier;
  observer::GovernmentRuntimeAdapterSourceAccessV1 access{
      true,&fixture,Main,Capture,observer::GovernmentRuntimeAdapterBuildProfileV1::ck3_12004};
  observer::GovernmentRuntimeAdapterSourceResultV1 result{};
  observer::ReadGovernmentRuntimeAdapterSourceV1(access,result);
  active_fixture=nullptr;
  const bool valid=fixture.samples==2 && (drift
      ? result.failure==observer::GovernmentRuntimeAdapterSourceFailureV1::government_identity_drift
      : result.status==observer::GovernmentRuntimeAdapterSourceStatusV1::available &&
        result.input.effective_government_stable_key=="feudal_government" &&
        result.input.effective_feature_flags.size()==44);
  if(!valid) return false;
  const auto name=drift ? "government-key-drift" : "government-available";
  std::ofstream output(directory/(std::string(name)+".json"),std::ios::binary);
  output<<Envelope(result,name)<<'\n'; return static_cast<bool>(output);
}
} // namespace
int main(int argc,char** argv) {
  if(argc!=2) { std::cerr<<"usage: government-whole-first OUTPUT_DIR\n"; return 2; }
  try {
    if(current::BindGovernmentRuntimeImageV1(1,xar::ck3_12002::kExecutableSha256).enabled ||
       !current::BindGovernmentRuntimeImageV1(1,current::kExecutableSha256).enabled) return 1;
    const std::filesystem::path output=argv[1];
    std::filesystem::create_directories(output);
    if(!Emit(output,false) || !Emit(output,true)) return 1;
    std::ofstream receipt(output/"NATIVE-FIRST.json",std::ios::binary);
    receipt<<"{\"schema\":\"ck3.actual4.government-whole-first.v1\","
        "\"whole_wire_cases\":2,\"native_collector_samples\":4,"
        "\"fixture_owned_memory\":true,\"new_build_production_live\":false,"
        "\"future_binding\":false}\n";
    std::cout<<"actual4-government-whole-first: two whole wires emitted\n";
    return receipt ? 0 : 1;
  } catch(const std::exception& error) { std::cerr<<error.what()<<'\n'; return 1; }
}
