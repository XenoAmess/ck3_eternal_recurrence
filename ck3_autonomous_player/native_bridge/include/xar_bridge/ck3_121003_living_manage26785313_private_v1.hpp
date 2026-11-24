#pragma once
#include "xar_bridge/ck3_121003_living_inventory26785313_raw_v1.hpp"
#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
namespace xar::ck3_121003::build26785313 {
enum class LivingManage267V1:std::uint8_t {manage};
enum class LivingManageAction267V1 {query,open_list,open_detail,confirm};
inline std::optional<LivingManage267V1>ParseLivingManageKey267V1(std::string_view key)noexcept {
 return key=="xalw_manage_decision"?std::optional{LivingManage267V1::manage}:std::nullopt;
}
struct LivingManageRow267V1{LivingManage267V1 decision{};bool can_open_detail=false,is_selected=false;friend bool operator==(const LivingManageRow267V1&,const LivingManageRow267V1&)=default;};
struct LivingManageSource267V1{
 bool list_found=false,list_visible=false,list_enabled=false,detail_found=false,detail_visible=false,detail_enabled=false,other_decision_selected=false,open_list_admissible=false,complete_model_census=false,blocked_by_visible_modal=false,confirm_admissible=false;
 bool owner_bound=false;std::optional<std::string>confirm_tooltip;bool confirm_tooltip_observed=false;
 std::optional<std::int32_t>groups_count,total_model_rows,widget_state;std::optional<LivingManage267V1>selected_decision;std::optional<bool>native_can_confirm;std::vector<LivingManageRow267V1>rows;
 friend bool operator==(const LivingManageSource267V1&,const LivingManageSource267V1&)=default;
};

struct LivingManageScene267V1 {
 std::uint64_t connection_generation=0,wall_deadline=0;
 std::uintptr_t jomini=0,gfx=0,handler=0,context=0,global=0,list_root=0,detail_root=0;
 bool list_visible=false,list_enabled=false,detail_visible=false,detail_enabled=false;
 bool owner_bound=false; // Set only after Entry Raw joins the actual owned fixture target.
 std::vector<GuiWindowNodeV1>hud;
 friend bool operator==(const LivingManageScene267V1&,const LivingManageScene267V1&)=default;
};
struct LivingManageFrame267V1 {
 ck3_1210::CoreSnapshotPrefix core{};
 LivingManageScene267V1 scene;
 std::vector<GuiWindowNodeV1>witness;
 bool facts_verified=false;
};
struct LivingManageRaw267V1 {
 LivingManageSource267V1 source;
 std::uintptr_t list=0,detail=0,definition=0,controller=0,shortcut_manager=0,nav_widget=0;
 std::vector<std::byte>exact_model,modal_source;
 std::array<std::uintptr_t,1>rows{};
 std::vector<ck3_1210::GuiControlCallbackV1>nav_callbacks;
 bool native_read_entered=false,cleanup_known=true;
 friend bool operator==(const LivingManageRaw267V1&,const LivingManageRaw267V1&)=default;
};
enum class LivingManageRawCallStatus267V1 {refused,returned,indeterminate};
struct LivingManageRawCall267V1 {
 LivingManageRawCallStatus267V1 status=LivingManageRawCallStatus267V1::refused;
 bool effect_entered=false,cleanup_known=true,native_handled=false;
};
bool VerifyLivingManageImage267V1(std::uintptr_t)noexcept;
bool ReadLivingManageRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,
 const LivingManageScene267V1&,std::uint64_t,LivingManageRaw267V1&,std::string&)noexcept;
LivingManageRawCall267V1 CallLivingManageRaw267V1(const ReadonlyBindings&,
 const ck3_1210::CoreSnapshotPrefix&,const LivingManageScene267V1&,std::uint64_t,
 const LivingManageRaw267V1&,LivingManageAction267V1,std::optional<LivingManage267V1>)noexcept;
}
