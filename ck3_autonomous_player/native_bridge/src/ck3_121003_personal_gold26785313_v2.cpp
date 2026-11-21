#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_V1
#include "xar_bridge/ck3_121003_letter26785313_owner_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1
#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_owner_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1) && XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1
#include "xar_bridge/ck3_121003_succession_lifecycle26785313_owner_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1
#include "xar_bridge/ck3_121003_djc_target_query26785313_owner_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
#include "xar_bridge/ck3_121003_aub_observer_fixture26785313_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1) && XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1
#include "xar_bridge/ck3_121003_frontend_menu26785313_v1.hpp"
#endif
#include <iterator>
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
#include "xar_bridge/ck3_121003_rite_doctrine26785313_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
#include "xar_bridge/ck3_121003_date_advance26785313_v1.hpp"
#include <iterator>
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1) && XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1
#include "xar_bridge/ck3_121003_save_checkpoint26785313_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) && XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
#include "xar_bridge/ck3_121003_gui_controls26785313_wire_v2.hpp"
#endif
#include "xar_bridge/ck3_121003_personal_gold26785313_v2.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include <algorithm>
#include <array>

namespace xar::ck3_121003::build26785313 {
namespace {
void String(std::string &out,std::string_view value) {
  constexpr char hex[]="0123456789abcdef";out+='"';
  for(const unsigned char c:value) {
    if(c=='"')out+="\\\"";
    else if(c=='\\')out+="\\\\";
    else if(c<0x20){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}
    else out+=static_cast<char>(c);
  }
  out+='"';
}
const char *Boolean(bool value) noexcept {return value?"true":"false";}
bool Prefix(const ReadonlyObservation &in) noexcept {
  const auto &p=in.core;
  return in.available&&in.partial&&!in.offline_fixture&&in.main_owner_observed&&
      p.clock.paused&&p.clock.speed>=1&&p.clock.speed<=5&&p.map_ready&&
      p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;
}
} // namespace
const game::AdapterDescriptor &PersonalGoldAdapterDescriptorV2() noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
  static constexpr std::string_view caps[]{ck3_1210::kCoreFrameCapabilityV1,kRiteDoctrineCapability267V1,kRiteFinalConfirmCapability267V1,
    kGuiControlsQueryCapability267V2,kGuiControlsActivateCapability267V2,
#if defined(XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2)
    kPersonalGoldCapabilityV2,
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
    ck3_1210::kApplicationExitCapabilityV1,
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1) && XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1
    kSaveCheckpointCapability267V1,
#endif
  };
#elif defined(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1) && XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1
  static constexpr std::string_view caps[]{ck3_1210::kCoreFrameCapabilityV1,kSaveCheckpointCapability267V1,
#if defined(XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2)
    kPersonalGoldCapabilityV2,
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
    ck3_1210::kApplicationExitCapabilityV1,
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) && XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
    kGuiControlsQueryCapability267V2,kGuiControlsActivateCapability267V2,
#endif
  };
#elif defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) && XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
  static constexpr std::string_view caps[]{ck3_1210::kCoreFrameCapabilityV1,
#if defined(XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2)
    kPersonalGoldCapabilityV2,
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
    ck3_1210::kApplicationExitCapabilityV1,
#endif
    kGuiControlsQueryCapability267V2,kGuiControlsActivateCapability267V2};
#elif defined(XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2) && defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
  static constexpr std::array<std::string_view,3> caps{ck3_1210::kCoreFrameCapabilityV1,
    kPersonalGoldCapabilityV2,ck3_1210::kApplicationExitCapabilityV1};
#elif defined(XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2)
  static constexpr std::array<std::string_view,2> caps{ck3_1210::kCoreFrameCapabilityV1,kPersonalGoldCapabilityV2};
#elif defined(XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1) && defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
  static constexpr std::array<std::string_view,2> caps{ck3_1210::kCoreFrameCapabilityV1,ck3_1210::kApplicationExitCapabilityV1};
#elif defined(XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
  static constexpr std::array<std::string_view,1> caps{ck3_1210::kCoreFrameCapabilityV1};
#else
  static constexpr std::array<std::string_view,0> caps{};
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
  static const auto date_caps=[] {
    std::array<std::string_view,std::size(caps)+1> combined{};
    std::copy(std::begin(caps),std::end(caps),combined.begin());
    combined.back()=kDateAdvanceCapability267V1;return combined;
  }();
  const auto &base_caps=date_caps;
#else
  const auto &base_caps=caps;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1) && XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1
  static const auto menu_caps=[&] {
    std::array<std::string_view,std::size(base_caps)+2> combined{};
    std::copy(std::begin(base_caps),std::end(base_caps),combined.begin());
    combined[std::size(base_caps)]=kFrontendMenuQueryCapability267V1;
    combined[std::size(base_caps)+1]=kFrontendMenuQuitCapability267V1;
    return combined;
  }();
  const auto&frontend_caps=menu_caps;
#else
  const auto&frontend_caps=base_caps;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
  static const auto fixture_caps=[&] {
    std::array<std::string_view,std::size(frontend_caps)+1> combined{};
    std::copy(std::begin(frontend_caps),std::end(frontend_caps),combined.begin());
    combined.back()=kAubObserverFixtureCapability267V1;return combined;
  }();
  const auto&final_base_caps=fixture_caps;
#else
  const auto&final_base_caps=frontend_caps;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1
  static const auto djc_caps=[&] {
    std::array<std::string_view,std::size(final_base_caps)+1> combined{};
    std::copy(std::begin(final_base_caps),std::end(final_base_caps),combined.begin());
    combined.back()=kDjcTargetQueryCapability267V1;return combined;
  }();
  const auto&lifecycle_base_caps=djc_caps;
#else
  const auto&lifecycle_base_caps=final_base_caps;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1) && XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1
  static const auto succession_caps=[&] {
    std::array<std::string_view,std::size(lifecycle_base_caps)+2> combined{};
    std::copy(std::begin(lifecycle_base_caps),std::end(lifecycle_base_caps),combined.begin());
    combined[std::size(lifecycle_base_caps)]=kSuccessionQueryCapability267V1;
    combined[std::size(lifecycle_base_caps)+1]=kSuccessionContinueCapability267V1;return combined;
  }();
  const auto&ui_base_caps=succession_caps;
#else
  const auto&ui_base_caps=lifecycle_base_caps;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1
  constexpr std::size_t selected_cost_extra=1;
#else
  constexpr std::size_t selected_cost_extra=0;
#endif
  static const auto ui_caps=[&]{std::array<std::string_view,std::size(ui_base_caps)+kDjcUiCapabilities267V1.size()+selected_cost_extra> combined{};
    std::copy(std::begin(ui_base_caps),std::end(ui_base_caps),combined.begin());std::copy(kDjcUiCapabilities267V1.begin(),kDjcUiCapabilities267V1.end(),combined.begin()+std::size(ui_base_caps));
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1
    combined.back()=kDjcSelectedCostCapability267V1;
#endif
    return combined;}();
  const auto&letter_base_caps=ui_caps;
#else
  const auto&letter_base_caps=ui_base_caps;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_V1
  static const auto letter_caps=[&]{std::array<std::string_view,std::size(letter_base_caps)+kLetterCapabilities267V1.size()> combined{};
    std::copy(std::begin(letter_base_caps),std::end(letter_base_caps),combined.begin());std::copy(kLetterCapabilities267V1.begin(),kLetterCapabilities267V1.end(),combined.begin()+std::size(letter_base_caps));return combined;}();
  static const game::AdapterDescriptor descriptor{kAdapterId,kGameVersion,kExecutableSha256,"xar_checkpoint",letter_caps};
#else
  static const game::AdapterDescriptor descriptor{kAdapterId,kGameVersion,kExecutableSha256,"xar_checkpoint",letter_base_caps};
#endif
  return descriptor;
}
bool PersonalGoldRouteEnabledV2([[maybe_unused]]const game::AdapterDescriptor &d) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2)
  return game::IsCk3_121003Core26785313Descriptor(d)&&
      std::find(d.capabilities.begin(),d.capabilities.end(),kPersonalGoldCapabilityV2)!=d.capabilities.end();
#else
  return false;
#endif
}
std::string_view PersonalGoldStepCapabilityV2(const game::AdapterDescriptor &d,
    std::string_view step) noexcept {
  return step==kPersonalGoldStepV2&&PersonalGoldRouteEnabledV2(d)
      ?std::string_view{kPersonalGoldCapabilityV2}:std::string_view{};
}
std::string SerializePersonalGoldCommandResultV2(std::string_view id,
    const ReadonlyObservation &in,const game::AdapterDescriptor &descriptor) {
  ck3_1210::CoreFrameObservationV1 core{};
  std::string_view reason="exact_personal_gold_v2_profile_unavailable";
  bool available=false;
  if(PersonalGoldRouteEnabledV2(descriptor)) {
    core.application_main_observed=!in.offline_fixture&&in.main_owner_observed;
    reason=in.offline_fixture?"offline_fixture_has_no_application_main":
        !in.main_owner_observed?"application_main_not_observed":
        !in.available?(in.unavailable_reason.empty()?"paused_readonly_source_unavailable":in.unavailable_reason):
        !Prefix(in)?"paused_living_player_core_unavailable":
        !in.raw_resources?"personal_gold_raw_not_read":std::string_view{};
    if(Prefix(in)){core.core_available=true;core.core=in.core;core.unavailable_reason={};}
    available=core.core_available&&in.raw_resources.has_value();
  }
  if(!core.core_available)core.unavailable_reason=reason;
  std::string out="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  String(out,id);out+=",\"ok\":true,\"result\":{\"step\":";String(out,kPersonalGoldStepV2);
  out+=",\"schema\":";String(out,kPersonalGoldSchemaV2);
  out+=",\"game_version\":";String(out,kGameVersion);
  out+=",\"executable_sha256\":";String(out,kExecutableSha256);
  out+=",\"adapter_id\":";String(out,kAdapterId);
  out+=",\"backend\":\"ck3-1.21.0.3-native-headless-main-thread\",\"status\":";
  String(out,available?"partial":"unavailable");
  out+=",\"personal_gold_available\":";out+=Boolean(available);
  out+=",\"application_main_observed\":";out+=Boolean(core.application_main_observed);
  out+=",\"complete_snapshot\":false,\"treasury_observed\":false,\"monthly_flow_observed\":false,\"core_frame\":";
  out+=ck3_1210::SerializeCoreFrameV1(core,ck3_1210::CoreFrameReadonlySourceV1::hotfix26785313);
  out+=",\"personal_gold\":";
  if(available) {
    out+="{\"raw\":";String(out,std::to_string(in.raw_resources->personal_gold_raw));
    out+=",\"scale\":"+std::to_string(kPersonalGoldScaleV2)+'}';
  } else out+="null";
  out+=",\"unavailable_reason\":";
  if(available)out+="null";else String(out,reason);
  out+="}}";return out;
}
} // namespace xar::ck3_121003::build26785313
