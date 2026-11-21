#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1
#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_owner_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1) && XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1
#include "xar_bridge/ck3_121003_succession_lifecycle26785313_owner_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1
#include "xar_bridge/ck3_121003_djc_target_query26785313_owner_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1) && XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1
#include "xar_bridge/ck3_121003_frontend_menu26785313_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
#include "xar_bridge/ck3_121003_date_advance26785313_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1) && XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1
#include "xar_bridge/ck3_121003_save_checkpoint26785313_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) && XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
#include "xar_bridge/ck3_121003_gui_controls26785313_v2.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
#include "xar_bridge/ck3_121003_rite_doctrine26785313_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
#include "xar_bridge/ck3_121003_doctrine_category26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_select26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_knowledge26785313_v1.hpp"
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
#include "xar_bridge/ck3_121003_aub_observer_fixture26785313_v1.hpp"
#endif
#include "xar_bridge/ck3_121003_aub_private_console26785313_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
#include "xar_bridge/ck3_121003_application_exit26785313_v1.hpp"
#endif

namespace xar::ck3_121003::build26785313 {
ck3_11906::MainThreadQueryInstallEnvironmentV1 BindCoreRouteMailboxEnvironmentV1(
    std::uintptr_t image_base,std::string_view sha) noexcept {
  ck3_11906::MainThreadQueryInstallEnvironmentV1 out{};
  if(!BindReadonlyImage(image_base,sha).exact_image_admitted)return out;
  out.module_base=image_base;out.exact_build_admitted=true;
  out.build_profile=&ReadonlyThreadProfile();
  out.executor_submission_enabled=true;out.permitted_executor=&ExecuteReadonlyOnOwner;
#if defined(XAR_CK3_ENABLE_121003_26785313_APPLICATION_EXIT_V1)
  if(!VerifyApplicationExitImage267V1(image_base))return {};
  out.permitted_executor_secondary=&ExecuteApplicationExitOnOwner267V1;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2) && XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2
  if(!VerifyGuiControlImage267V2(image_base))return {};
  out.permitted_executor_tertiary=&ExecuteGuiControlsOnOwner267V2;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1) && XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1
  const auto commands=BindCurrentCommandImageV1(image_base,{kGameVersion,kSteamBuildId,kExecutableSha256});
  if(!commands.current_image_verified||commands.offline_fixture||!CurrentCommandTargetsMatchV1(commands))return {};
  out.permitted_executor_quaternary=&ExecuteSaveCheckpointOnOwner267V1;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
  if(!VerifyDoctrineCategoryImage267V1(image_base)||!VerifyDoctrineSelectImage267V1(image_base)||
     !VerifyDoctrineKnowledgeImage267V1(image_base))return {};
  out.permitted_executor_quinary=&ExecuteRiteDoctrineOnOwner267V1;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1) && XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
  const auto current_date_commands=BindCurrentCommandImageV1(image_base,{kGameVersion,kSteamBuildId,kExecutableSha256});
  if(!current_date_commands.current_image_verified||current_date_commands.offline_fixture||
      !CurrentCommandTargetsMatchV1(current_date_commands))return {};
  out.permitted_executor_senary=&ExecuteDateAdvanceOnOwner267V1;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1) && XAR_CK3_ENABLE_121003_26785313_FRONTEND_MENU_V1
  if(!VerifyGuiWindowImageV1(image_base)||!VerifyApplicationExitImage267V1(image_base))return {};
  out.permitted_frontend_executor=&ExecuteFrontendMenuOnOwner267V1;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
  // Static exact-image admission only: Console/World need not yet exist at startup.
  if(!VerifyAubPrivateInboxImage267V1(image_base))return {};
  out.permitted_executor_septenary=&ExecuteAubObserverFixtureOnOwner267V1;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1
  // Static exact image only: lazy database/world are not required during startup.
  if(!VerifyCurrentDjcDeclarationsImage267V1(image_base))return {};
  out.permitted_executor_octonary=&ExecuteDjcTargetQueryOnOwner267V1;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1) && XAR_CK3_ENABLE_121003_26785313_SUCCESSION_CONTINUE_V1
  // Static source verification only: no loaded/dead actor or resident window at startup.
  if(!VerifySuccessionContinueImage267V1(image_base))return {};
  out.permitted_executor_denary=&ExecuteSuccessionLifecycleOnOwner267V1;
#endif
#if defined(XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1) && XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1
  if(!VerifyDjcUiImage267V1(image_base))return {};
  out.permitted_executor_undenary=&ExecuteDjcUiOnOwner267V1;
#endif
  return out;
}
ck3_1210::CoreFrameObservationV1 CoreRouteObservationV1(const ReadonlyObservation &in) noexcept {
  ck3_1210::CoreFrameObservationV1 out{};
  if(in.offline_fixture) {out.unavailable_reason="offline_fixture_has_no_live_core_qualification";return out;}
  out.application_main_observed=in.main_owner_observed;
  if(!in.available) {out.unavailable_reason=in.unavailable_reason.empty()?"exact_core_unavailable":in.unavailable_reason;return out;}
  if(!in.partial||in.raw_resources||in.gui_root_index||in.gui_window||in.rite_draft||!in.main_owner_observed||!in.core.clock.paused||
      in.core.clock.speed<1||in.core.clock.speed>5||!in.core.map_ready||
      !in.core.has_played_character||!in.core.played_character_alive||in.core.played_character_id==-1) {
    out.unavailable_reason="exact_core_only_owner_observation_required";return out;
  }
  out.core=in.core;out.core_available=true;out.unavailable_reason={};return out;
}
} // namespace xar::ck3_121003::build26785313
