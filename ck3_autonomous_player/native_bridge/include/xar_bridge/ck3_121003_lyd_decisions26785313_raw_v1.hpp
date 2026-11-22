#pragma once
#include "xar_bridge/ck3_121003_lyd26785313_v1.hpp"
#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
namespace xar::ck3_121003::build26785313 {
enum class LydDecisionAction267V1{query,open_list,open_detail,confirm};
struct LydDecisionScene267V1{
 std::uintptr_t jomini=0,gfx=0,handler=0,context=0,global=0,list_root=0,detail_root=0;
 bool list_visible=false,list_enabled=false,detail_visible=false,detail_enabled=false;
 std::vector<GuiWindowNodeV1>hud;
 friend bool operator==(const LydDecisionScene267V1&,const LydDecisionScene267V1&)=default;
};
struct LydDecisionRaw267V1{
 LydDecisionSource267V1 source;std::uintptr_t list=0,detail=0,definition=0,controller=0,shortcut_manager=0,nav_widget=0;
 std::vector<std::byte>exact_model,modal_source;
 std::array<std::uintptr_t,5>rows{};
 std::vector<ck3_1210::GuiControlCallbackV1>nav_callbacks;
 bool native_read_entered=false,cleanup_known=true;
 friend bool operator==(const LydDecisionRaw267V1&,const LydDecisionRaw267V1&)=default;
};
enum class LydDecisionRawCallStatus267V1{refused,returned,indeterminate};
struct LydDecisionRawCall267V1{LydDecisionRawCallStatus267V1 status=LydDecisionRawCallStatus267V1::refused;bool effect_entered=false,cleanup_known=true,native_handled=false;};
bool VerifyLydDecisionImage267V1(std::uintptr_t)noexcept;
bool ReadLydDecisionRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const LydDecisionScene267V1&,std::uint64_t,LydDecisionRaw267V1&,std::string&)noexcept;
LydDecisionRawCall267V1 CallLydDecisionRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const LydDecisionScene267V1&,std::uint64_t,const LydDecisionRaw267V1&,LydDecisionAction267V1,std::optional<LydDecision267V1>)noexcept;
}
