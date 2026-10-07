#include <string>
#include <string_view>
#include <span>
#include <array>
#include <utility>
#include <fstream>
#include <iterator>
#include <iostream>
#include <stdexcept>
namespace xar::ck3_12002{
inline constexpr char kExecutableSha256[] =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
}
namespace xar::ck3_12003{
inline constexpr char kGameVersion[] = "1.20.0.3";
inline constexpr char kAdapterId[] = "ck3-1.20.0.3-msvc-x64";
inline constexpr char kExecutableSha256[] =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
}
namespace xar::ck3_12004{
inline constexpr char kGameVersion[] = "1.20.0.4";
inline constexpr char kAdapterId[] = "ck3-1.20.0.4-msvc-x64";
inline constexpr char kExecutableSha256[] =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
}
namespace xar::game{
struct AdapterDescriptor {
  std::string_view adapter_id;
  std::string_view game_version;
  std::string_view executable_sha256;
  std::string_view checkpoint_save_name;
  std::span<const std::string_view> capabilities;
};
bool IsCk3_12004Descriptor(const AdapterDescriptor &descriptor) noexcept {
  return descriptor.adapter_id == ck3_12004::kAdapterId &&
         descriptor.game_version == ck3_12004::kGameVersion &&
         descriptor.executable_sha256 == ck3_12004::kExecutableSha256;
}
}
namespace xar::ck3_12002{
void ReplaceIdentity(std::string &value, std::string_view from,
                     std::string_view to) {
  std::size_t at = 0;
  while ((at = value.find(from, at)) != std::string::npos) {
    value.replace(at, from.size(), to);
    at += to.size();
  }
}
std::string RenderQueryBuildIdentity(std::string serialized) {
  ReplaceIdentity(serialized, "\"game_version\":\"1.19.0.6\"",
                  "\"game_version\":\"1.20.0.2\"");
  ReplaceIdentity(serialized, "\"exact_ck3_build\":\"1.19.0.6\"",
                  "\"exact_ck3_build\":\"1.20.0.2\"");
  ReplaceIdentity(serialized, "\"exact_build\":\"1.19.0.6\"",
                  "\"exact_build\":\"1.20.0.2\"");
  ReplaceIdentity(serialized, "\"version\":\"1.19.0.6\"",
                  "\"version\":\"1.20.0.2\"");
  ReplaceIdentity(serialized, "\"backend_id\":\"ck3-1.19.0.6-native-",
                  "\"backend_id\":\"ck3-1.20.0.2-native-");
  ReplaceIdentity(serialized,
                  "\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\"",
                  "\"AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D\"");
  ReplaceIdentity(serialized,
                  "\"played-character-event-icon-indicators-1.19.0.6-v1\"",
                  "\"played-character-event-icon-indicators-1.20.0.2-v1\"");
  return serialized;
}
}
namespace xar::ck3_12003{
inline constexpr std::string_view kNormalExitMapV1Step = "normal-exit-map-v1";
inline constexpr std::string_view kNormalExitMapV1Capability = "normal-exit-map-v1";
}
namespace original {
using namespace xar;using namespace xar::game;
void ReplaceIdentityToken(std::string &serialized, std::string_view from,
                          std::string_view to) {
  std::size_t at = 0;
  while ((at = serialized.find(from, at)) != std::string::npos) {
    serialized.replace(at, from.size(), to);
    at += to.size();
  }
}
std::string Render12004BuildIdentity(
    std::string serialized, const AdapterDescriptor &descriptor) {
  if (!IsCk3_12004Descriptor(descriptor)) return serialized;
  serialized = ck3_12002::RenderQueryBuildIdentity(std::move(serialized));
  // The shared event-window serializer retains its historical .2 locator.
  // The independently mapped .4 factory uses 0x44BC418 (SOURCE-CLOSURE.json).
  if (serialized.find("\"schema\":\"current-event-window-context-v1\"") !=
      std::string::npos) {
    ReplaceIdentityToken(serialized,
        "\"idler_vtable_rva\":\"0x44BC408\"",
        "\"idler_vtable_rva\":\"0x44BC418\"");
  }
  for (const auto old_version : {"1.20.0.2", "1.20.0.3"}) {
    for (const auto key : {"game_version", "exact_ck3_build", "exact_build",
                           "version", "build_version", "build"}) {
      ReplaceIdentityToken(serialized,
          std::string("\"") + key + "\":\"" + old_version + "\"",
          std::string("\"") + key + "\":\"1.20.0.4\"");
    }
    for (const auto key : {"backend_id", "campaign_backend_id", "feature_backend_id"}) {
      ReplaceIdentityToken(serialized,
          std::string("\"") + key + "\":\"ck3-" + old_version + "-",
          std::string("\"") + key + "\":\"ck3-1.20.0.4-");
    }
    ReplaceIdentityToken(serialized,
        std::string("\"adapter_id\":\"ck3-") + old_version + "-msvc-x64\"",
        "\"adapter_id\":\"ck3-1.20.0.4-msvc-x64\"");
    ReplaceIdentityToken(serialized,
        std::string("\"played-character-event-icon-indicators-") + old_version + "-v1\"",
        "\"played-character-event-icon-indicators-1.20.0.4-v1\"");
  }
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12002_", "\"schema\":\"ck3_12004_");
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12003_", "\"schema\":\"ck3_12004_");
  // This nested Army semantic contract is independent of executable identity.
  // Its production normalizer and shared serializer retain the canonical name.
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12004_owned_regiments_v1\"",
      "\"schema\":\"ck3_12003_owned_regiments_v1\"");
  // Knight semantic contracts retain their canonical schema across builds.
  // The actual V2 consumer rejected a rewritten effectiveness schema in R0060.
  ReplaceIdentityToken(serialized,
      "\"schema\":\"ck3_12004_knight_effectiveness_context_v1\"",
      "\"schema\":\"ck3_12003_knight_effectiveness_context_v1\"");
  ReplaceIdentityToken(serialized,
      "\"schema\":\"ck3_12004_knight_current_model_association_v1\"",
      "\"schema\":\"ck3_12003_knight_current_model_association_v1\"");
  for (const auto old_hash : {std::string_view(ck3_12002::kExecutableSha256),
                            std::string_view(ck3_12003::kExecutableSha256)}) {
    ReplaceIdentityToken(serialized, std::string("\"") + std::string(old_hash) + "\"",
        std::string("\"") + ck3_12004::kExecutableSha256 + "\"");
  }
  for (const auto old_hash : {
      "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d",
      "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"}) {
    ReplaceIdentityToken(serialized, std::string("\"") + old_hash + "\"",
        "\"98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518\"");
  }
  return serialized;
}
class GameAdapter { AdapterDescriptor d_; bool enabled_; public:
explicit GameAdapter(AdapterDescriptor d, bool enabled=true):d_(d),enabled_(enabled){}
const AdapterDescriptor &descriptor() const noexcept { return d_; }
bool enabled() const noexcept { return enabled_; }
bool supports(std::string_view capability) const noexcept;
bool supports_step(std::string_view step) const noexcept;
};
bool GameAdapter::supports(std::string_view capability) const noexcept {
  if (!enabled()) {
    return false;
  }
  for (const auto candidate : descriptor().capabilities) {
    if (candidate == capability) {
      return true;
    }
  }
  return false;
}
bool GameAdapter::supports_step(std::string_view step) const noexcept { std::string_view capability;
if (step == ck3_12003::kNormalExitMapV1Step) {

    if (descriptor().game_version != ck3_12003::kGameVersion ||
        descriptor().executable_sha256 != ck3_12003::kExecutableSha256) return false;
    capability = ck3_12003::kNormalExitMapV1Capability;
}else{return false;}
return !capability.empty() && supports(capability);}
}
namespace fixed {
using namespace xar;using namespace xar::game;
void ReplaceIdentityToken(std::string &serialized, std::string_view from,
                          std::string_view to) {
  std::size_t at = 0;
  while ((at = serialized.find(from, at)) != std::string::npos) {
    serialized.replace(at, from.size(), to);
    at += to.size();
  }
}
std::string Render12004BuildIdentity(
    std::string serialized, const AdapterDescriptor &descriptor) {
  if (!IsCk3_12004Descriptor(descriptor)) return serialized;
  serialized = ck3_12002::RenderQueryBuildIdentity(std::move(serialized));
  // The shared event-window serializer retains its historical .2 locator.
  // The independently mapped .4 factory uses 0x44BC418 (SOURCE-CLOSURE.json).
  if (serialized.find("\"schema\":\"current-event-window-context-v1\"") !=
      std::string::npos) {
    ReplaceIdentityToken(serialized,
        "\"idler_vtable_rva\":\"0x44BC408\"",
        "\"idler_vtable_rva\":\"0x44BC418\"");
  }
  for (const auto old_version : {"1.20.0.2", "1.20.0.3"}) {
    for (const auto key : {"game_version", "exact_ck3_build", "exact_build",
                           "version", "build_version", "build"}) {
      ReplaceIdentityToken(serialized,
          std::string("\"") + key + "\":\"" + old_version + "\"",
          std::string("\"") + key + "\":\"1.20.0.4\"");
    }
    for (const auto key : {"backend_id", "campaign_backend_id", "feature_backend_id"}) {
      ReplaceIdentityToken(serialized,
          std::string("\"") + key + "\":\"ck3-" + old_version + "-",
          std::string("\"") + key + "\":\"ck3-1.20.0.4-");
    }
    ReplaceIdentityToken(serialized,
        std::string("\"adapter_id\":\"ck3-") + old_version + "-msvc-x64\"",
        "\"adapter_id\":\"ck3-1.20.0.4-msvc-x64\"");
    ReplaceIdentityToken(serialized,
        std::string("\"played-character-event-icon-indicators-") + old_version + "-v1\"",
        "\"played-character-event-icon-indicators-1.20.0.4-v1\"");
  }
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12002_", "\"schema\":\"ck3_12004_");
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12003_", "\"schema\":\"ck3_12004_");
  // Confucian DTO schemas describe the shared semantic wire contract, not the
  // executable build. Their exact Python/reader normalizers retain these names.
  for (const auto schema : {"confucian_assembly_predicates_v1",
                           "confucian_religious_title_v1",
                           "confucian_challenger_graph_v1"}) {
    ReplaceIdentityToken(serialized,
        std::string("\"schema\":\"ck3_12004_") + schema + "\"",
        std::string("\"schema\":\"ck3_12003_") + schema + "\"");
  }
  // This nested Army semantic contract is independent of executable identity.
  // Its production normalizer and shared serializer retain the canonical name.
  ReplaceIdentityToken(serialized, "\"schema\":\"ck3_12004_owned_regiments_v1\"",
      "\"schema\":\"ck3_12003_owned_regiments_v1\"");
  // Knight semantic contracts retain their canonical schema across builds.
  // The actual V2 consumer rejected a rewritten effectiveness schema in R0060.
  ReplaceIdentityToken(serialized,
      "\"schema\":\"ck3_12004_knight_effectiveness_context_v1\"",
      "\"schema\":\"ck3_12003_knight_effectiveness_context_v1\"");
  ReplaceIdentityToken(serialized,
      "\"schema\":\"ck3_12004_knight_current_model_association_v1\"",
      "\"schema\":\"ck3_12003_knight_current_model_association_v1\"");
  for (const auto old_hash : {std::string_view(ck3_12002::kExecutableSha256),
                            std::string_view(ck3_12003::kExecutableSha256)}) {
    ReplaceIdentityToken(serialized, std::string("\"") + std::string(old_hash) + "\"",
        std::string("\"") + ck3_12004::kExecutableSha256 + "\"");
  }
  for (const auto old_hash : {
      "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d",
      "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"}) {
    ReplaceIdentityToken(serialized, std::string("\"") + old_hash + "\"",
        "\"98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518\"");
  }
  return serialized;
}
class GameAdapter { AdapterDescriptor d_; bool enabled_; public:
explicit GameAdapter(AdapterDescriptor d, bool enabled=true):d_(d),enabled_(enabled){}
const AdapterDescriptor &descriptor() const noexcept { return d_; }
bool enabled() const noexcept { return enabled_; }
bool supports(std::string_view capability) const noexcept;
bool supports_step(std::string_view step) const noexcept;
};
bool GameAdapter::supports(std::string_view capability) const noexcept {
  if (!enabled()) {
    return false;
  }
  for (const auto candidate : descriptor().capabilities) {
    if (candidate == capability) {
      return true;
    }
  }
  return false;
}
bool GameAdapter::supports_step(std::string_view step) const noexcept { std::string_view capability;
if (step == ck3_12003::kNormalExitMapV1Step) {

    if ((descriptor().game_version != ck3_12003::kGameVersion ||
         descriptor().executable_sha256 != ck3_12003::kExecutableSha256) &&
        !IsCk3_12004Descriptor(descriptor())) return false;
    capability = ck3_12003::kNormalExitMapV1Capability;
}else{return false;}
return !capability.empty() && supports(capability);}
}
int main(int argc,char**argv){
using namespace xar;using namespace xar::game;
constexpr std::array<std::string_view,1> cap{ck3_12003::kNormalExitMapV1Capability};
const AdapterDescriptor three{ck3_12003::kAdapterId,ck3_12003::kGameVersion,ck3_12003::kExecutableSha256,"",cap};
const AdapterDescriptor four{ck3_12004::kAdapterId,ck3_12004::kGameVersion,ck3_12004::kExecutableSha256,"",cap};
auto no_cap=four;no_cap.capabilities={};auto mixed=four;mixed.executable_sha256=ck3_12003::kExecutableSha256;
auto wrong_adapter=four;wrong_adapter.adapter_id=ck3_12003::kAdapterId;
const auto step=ck3_12003::kNormalExitMapV1Step;
if(!original::GameAdapter(three).supports_step(step)||original::GameAdapter(four).supports_step(step)||
 !fixed::GameAdapter(three).supports_step(step)||!fixed::GameAdapter(four).supports_step(step)||
 fixed::GameAdapter(no_cap).supports_step(step)||fixed::GameAdapter(mixed).supports_step(step)||
 fixed::GameAdapter(wrong_adapter).supports_step(step)||fixed::GameAdapter(four,false).supports_step(step))return 2;
std::cout<<"{\"admission_checks\":8,\"cases\":[";
for(int i=1;i<argc;++i){std::ifstream file(argv[i],std::ios::binary);std::string raw((std::istreambuf_iterator<char>(file)),{});
if(!file)return 3;if(i>1)std::cout<<',';
std::cout<<"{\"original\":"<<original::Render12004BuildIdentity(raw,four)<<",\"fixed\":"<<fixed::Render12004BuildIdentity(raw,four)<<'}';
if(fixed::Render12004BuildIdentity(raw,three)!=raw)return 4;}
std::cout<<"]}\n";return 0;}
