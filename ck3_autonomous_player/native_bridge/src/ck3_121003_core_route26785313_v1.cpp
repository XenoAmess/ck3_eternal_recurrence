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
