#pragma once
#include "xar_bridge/ck3_121003_zg361_ae226785313_v1.hpp"
#include "xar_bridge/ck3_121003_gui_window26785313_v1.hpp"
#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
namespace xar::ck3_121003::build26785313::zg361_ae2_control {
using Zg361Ae2Manage267V1=Zg361Ae2Control267V1;
enum class Zg361Ae2ManageAction267V1 {query,open_list,open_detail,confirm};
inline std::optional<Zg361Ae2Manage267V1>ParseZg361Ae2ManageKey267V1(std::string_view key)noexcept {
 if(key==kZg361Ae2ControlKeys267V1[0])return Zg361Ae2Manage267V1::present;
 if(key==kZg361Ae2ControlKeys267V1[1])return Zg361Ae2Manage267V1::verify;
 return std::nullopt;
}
struct Zg361Ae2ManageRow267V1{Zg361Ae2Manage267V1 decision{};bool can_open_detail=false,is_selected=false;friend bool operator==(const Zg361Ae2ManageRow267V1&,const Zg361Ae2ManageRow267V1&)=default;};
struct Zg361Ae2ManageSource267V1{
 bool list_found=false,list_visible=false,list_enabled=false,detail_found=false,detail_visible=false,detail_enabled=false,other_decision_selected=false,open_list_admissible=false,complete_model_census=false,blocked_by_visible_modal=false,confirm_admissible=false;
 bool owner_bound=false;std::optional<std::string>confirm_tooltip;bool confirm_tooltip_observed=false;
 std::optional<std::int32_t>groups_count,total_model_rows,widget_state;std::optional<Zg361Ae2Manage267V1>selected_decision;std::optional<bool>native_can_confirm;std::vector<Zg361Ae2ManageRow267V1>rows;
 friend bool operator==(const Zg361Ae2ManageSource267V1&,const Zg361Ae2ManageSource267V1&)=default;
};

struct Zg361Ae2ManageScene267V1 {
 std::uint64_t connection_generation=0,wall_deadline=0;
 std::uintptr_t jomini=0,gfx=0,handler=0,context=0,global=0,list_root=0,detail_root=0;
 bool list_visible=false,list_enabled=false,detail_visible=false,detail_enabled=false;
 bool owner_bound=false; // Set only after Entry Raw joins the actual owned fixture target.
 std::vector<GuiWindowNodeV1>hud;
 friend bool operator==(const Zg361Ae2ManageScene267V1&,const Zg361Ae2ManageScene267V1&)=default;
};
struct Zg361Ae2ManageFrame267V1 {
 ck3_1210::CoreSnapshotPrefix core{};
 Zg361Ae2ManageScene267V1 scene;
 std::vector<GuiWindowNodeV1>witness;
 bool facts_verified=false;
};
struct Zg361Ae2ManageRaw267V1 {
 Zg361Ae2ManageSource267V1 source;
 std::uintptr_t list=0,detail=0,definition=0,controller=0,shortcut_manager=0,nav_widget=0;
 std::vector<std::byte>exact_model,modal_source;
 std::array<std::uintptr_t,2>rows{};
 std::vector<ck3_1210::GuiControlCallbackV1>nav_callbacks;
 bool native_read_entered=false,cleanup_known=true;
 friend bool operator==(const Zg361Ae2ManageRaw267V1&,const Zg361Ae2ManageRaw267V1&)=default;
};
enum class Zg361Ae2ManageRawCallStatus267V1 {refused,returned,indeterminate};
struct Zg361Ae2ManageRawCall267V1 {
 Zg361Ae2ManageRawCallStatus267V1 status=Zg361Ae2ManageRawCallStatus267V1::refused;
 bool effect_entered=false,cleanup_known=true,native_handled=false;
};
bool VerifyZg361Ae2ManageImage267V1(std::uintptr_t)noexcept;
bool ReadZg361Ae2ManageRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,
 const Zg361Ae2ManageScene267V1&,std::uint64_t,Zg361Ae2ManageRaw267V1&,std::string&)noexcept;
Zg361Ae2ManageRawCall267V1 CallZg361Ae2ManageRaw267V1(const ReadonlyBindings&,
 const ck3_1210::CoreSnapshotPrefix&,const Zg361Ae2ManageScene267V1&,std::uint64_t,
 const Zg361Ae2ManageRaw267V1&,Zg361Ae2ManageAction267V1,std::optional<Zg361Ae2Manage267V1>)noexcept;
}
