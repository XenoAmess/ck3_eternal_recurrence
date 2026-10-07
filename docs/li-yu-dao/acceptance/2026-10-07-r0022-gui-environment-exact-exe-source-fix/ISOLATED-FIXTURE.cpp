#include <cstdint>
#include <cstdlib>
#include <string_view>
#include <span>
#include <array>
#include <iostream>
namespace xar::ck3_12003{inline constexpr char kGameVersion[] = "1.20.0.3";inline constexpr char kAdapterId[] = "ck3-1.20.0.3-msvc-x64";inline constexpr char kExecutableSha256[] =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";}
namespace xar::ck3_12004{inline constexpr char kGameVersion[] = "1.20.0.4";inline constexpr char kAdapterId[] = "ck3-1.20.0.4-msvc-x64";inline constexpr char kExecutableSha256[] =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";}
namespace xar::game{struct AdapterDescriptor {
  std::string_view adapter_id;
  std::string_view game_version;
  std::string_view executable_sha256;
  std::string_view checkpoint_save_name;
  std::span<const std::string_view> capabilities;
};
bool IsCk3_12003Descriptor(const AdapterDescriptor &descriptor) noexcept {
  return descriptor.adapter_id == ck3_12003::kAdapterId &&
         descriptor.game_version == ck3_12003::kGameVersion &&
         descriptor.executable_sha256 == ck3_12003::kExecutableSha256;
}
bool IsCk3_12004Descriptor(const AdapterDescriptor &descriptor) noexcept {
  return descriptor.adapter_id == ck3_12004::kAdapterId &&
         descriptor.game_version == ck3_12004::kGameVersion &&
         descriptor.executable_sha256 == ck3_12004::kExecutableSha256;
}}
namespace xar::ck3_11906 {
enum class GuiAbiRevisionV1 { legacy11906,crozier12003,crozier12004 };
struct Variables { std::uintptr_t module_base{}; bool exact_build_admitted{}; };
using NativeZhongguoFindTopLevelWidgetV1=void(*)();
struct ZhongguoScoreboardNativeEnvironmentV1 {
 Variables variables{};std::uintptr_t module_base{};GuiAbiRevisionV1 gui_abi_revision{};
 std::string_view executable_sha256{};bool exact_build_admitted{};
 void **gui_global_slot{};NativeZhongguoFindTopLevelWidgetV1 find_top_level_widget{};
};
Variables BindZhongguoCaseNativeEnvironmentV1(std::uintptr_t base,bool admitted){return {base,admitted};}
std::uintptr_t GuiGlobalSlotRvaV1(GuiAbiRevisionV1){std::abort();}
std::uintptr_t GuiFindTopLevelWidgetRvaV1(GuiAbiRevisionV1){std::abort();}
ZhongguoScoreboardNativeEnvironmentV1 BindZhongguoScoreboardNativeEnvironmentV1(std::uintptr_t,bool,GuiAbiRevisionV1,std::string_view={}) noexcept;
ZhongguoScoreboardNativeEnvironmentV1 BindZhongguoScoreboardNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    GuiAbiRevisionV1 gui_abi_revision,
    std::string_view executable_sha256) noexcept {
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  const bool actual12004 = gui_abi_revision == GuiAbiRevisionV1::crozier12004;
  const bool admitted = exact_build_admitted &&
      (!actual12004 || executable_sha256 == ck3_12004::kExecutableSha256);
  if (actual12004) {
    // The closed .4 common-GUI packet supplies no Zhongguo variable callbacks.
    // Retain only the common environment metadata for the GUI helper route.
    environment.variables.module_base = module_base;
    environment.variables.exact_build_admitted = admitted;
  } else {
    environment.variables =
        BindZhongguoCaseNativeEnvironmentV1(module_base, exact_build_admitted);
  }
  environment.module_base = module_base;
  environment.gui_abi_revision = gui_abi_revision;
  environment.executable_sha256 = executable_sha256;
  environment.exact_build_admitted = admitted;
  if (module_base != 0 && admitted) {
    environment.gui_global_slot = reinterpret_cast<void **>(
        module_base + GuiGlobalSlotRvaV1(environment.gui_abi_revision));
    environment.find_top_level_widget =
        reinterpret_cast<NativeZhongguoFindTopLevelWidgetV1>(
            module_base + GuiFindTopLevelWidgetRvaV1(environment.gui_abi_revision));
  }
  return environment;
}
}
xar::ck3_11906::GuiAbiRevisionV1 LydPrivateGuiRevision(
    const xar::game::AdapterDescriptor &descriptor) noexcept {
  return xar::game::IsCk3_12004Descriptor(descriptor)
      ? xar::ck3_11906::GuiAbiRevisionV1::crozier12004
      : xar::ck3_11906::GuiAbiRevisionV1::crozier12003;
}
bool IsLydPrivateBuild(const xar::game::AdapterDescriptor &descriptor) noexcept {
  return xar::game::IsCk3_12003Descriptor(descriptor) ||
         xar::game::IsCk3_12004Descriptor(descriptor);
}
struct Game { xar::game::AdapterDescriptor d; const xar::game::AdapterDescriptor &descriptor() const {return d;} };
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 original0(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(base,true,LydPrivateGuiRevision(game.descriptor()));}
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 original1(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(base, true,
                  LydPrivateGuiRevision(game.descriptor()));}
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 original2(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(base,true,LydPrivateGuiRevision(game.descriptor()));}
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 original3(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(base,true,LydPrivateGuiRevision(game.descriptor()));}
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 original4(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(base,true,LydPrivateGuiRevision(game.descriptor()));}
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 fixed0(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(base,true,LydPrivateGuiRevision(game.descriptor()), game.descriptor().executable_sha256);}
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 fixed1(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(base, true,
                  LydPrivateGuiRevision(game.descriptor()), game.descriptor().executable_sha256);}
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 fixed2(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(base,true,LydPrivateGuiRevision(game.descriptor()), game.descriptor().executable_sha256);}
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 fixed3(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(base,true,LydPrivateGuiRevision(game.descriptor()), game.descriptor().executable_sha256);}
xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 fixed4(Game game){std::uintptr_t base=0;if(!IsLydPrivateBuild(game.descriptor()))return {};return xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(base,true,LydPrivateGuiRevision(game.descriptor()), game.descriptor().executable_sha256);}
int main(){using namespace xar;using namespace xar::game;
constexpr std::array<std::string_view,0> caps{};
Game three{{ck3_12003::kAdapterId,ck3_12003::kGameVersion,ck3_12003::kExecutableSha256,"",caps}};
Game four{{ck3_12004::kAdapterId,ck3_12004::kGameVersion,ck3_12004::kExecutableSha256,"",caps}};
auto mixed=four;mixed.d.executable_sha256=ck3_12003::kExecutableSha256;
if(!original0(three).exact_build_admitted||!fixed0(three).exact_build_admitted||original0(four).exact_build_admitted||!fixed0(four).exact_build_admitted||fixed0(mixed).exact_build_admitted)return 2;
if(!original1(three).exact_build_admitted||!fixed1(three).exact_build_admitted||original1(four).exact_build_admitted||!fixed1(four).exact_build_admitted||fixed1(mixed).exact_build_admitted)return 2;
if(!original2(three).exact_build_admitted||!fixed2(three).exact_build_admitted||original2(four).exact_build_admitted||!fixed2(four).exact_build_admitted||fixed2(mixed).exact_build_admitted)return 2;
if(!original3(three).exact_build_admitted||!fixed3(three).exact_build_admitted||original3(four).exact_build_admitted||!fixed3(four).exact_build_admitted||fixed3(mixed).exact_build_admitted)return 2;
if(!original4(three).exact_build_admitted||!fixed4(three).exact_build_admitted||original4(four).exact_build_admitted||!fixed4(four).exact_build_admitted||fixed4(mixed).exact_build_admitted)return 2;
using namespace xar::ck3_11906;
if(BindZhongguoScoreboardNativeEnvironmentV1(0,true,GuiAbiRevisionV1::crozier12004).exact_build_admitted ||
 BindZhongguoScoreboardNativeEnvironmentV1(0,true,GuiAbiRevisionV1::crozier12004,ck3_12003::kExecutableSha256).exact_build_admitted ||
 BindZhongguoScoreboardNativeEnvironmentV1(0,false,GuiAbiRevisionV1::crozier12004,ck3_12004::kExecutableSha256).exact_build_admitted)return 3;
std::cout<<"{\"exact_callsite_checks\":25,\"empty_wrong_hash_false_admission_checks\":3,\"GUI_callbacks_executed\":false}\n";return 0;}
