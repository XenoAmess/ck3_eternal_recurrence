#pragma once
#include "xar_bridge/ck3_121003_gui_window26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
inline constexpr char kRiteDraftStepV2[]="query-rite-draft-costs-v2";
inline constexpr char kRiteDraftRequestSchemaV2[]="ck3.rite_draft_costs_request.v2";
inline constexpr char kRiteDraftSchemaV2[]="ck3.rite_draft_costs.v2";
inline constexpr char kRiteDraftBackendV2[]="ck3-1.21.0.3-native-headless-main-thread";
struct RiteDraftRequestV2 {GuiWindowRequestV1 window;std::uint32_t expected_source_rite_id=0xFFFFFFFFU;};
struct RiteDraftV2 {
 GuiWindowV1 window;
 std::uintptr_t gfx=0,handler=0,controller=0;
 std::uint32_t source_rite_id=0xFFFFFFFFU;
 bool can_edit_rite_native=false;
 std::int64_t piety_cost_raw=0,piety_missing_raw=0;
 friend bool operator==(const RiteDraftV2&,const RiteDraftV2&)=default;
};
#if defined(XAR_CK3_26785313_OFFLINE_FIXTURE)
struct RiteDraftNativeFixtureV2 {
 void *context=nullptr;
 bool (*read)(void*,std::uintptr_t,bool&,std::int64_t&,std::int64_t&) noexcept=nullptr;
};
#endif
} // namespace
