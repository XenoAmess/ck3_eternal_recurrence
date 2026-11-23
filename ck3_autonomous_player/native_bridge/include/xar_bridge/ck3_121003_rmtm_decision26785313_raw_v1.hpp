#pragma once
#include "xar_bridge/ck3_121003_rmtm_decision26785313_v1.hpp"
#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct RmtmDecisionScene267V1{
 std::uint64_t connection_generation=0,wall_deadline=0;
 std::uintptr_t jomini=0,gfx=0,handler=0,context=0,global=0,list_root=0,detail_root=0;
 bool list_visible=false,list_enabled=false,detail_visible=false,detail_enabled=false;
 std::vector<GuiWindowNodeV1>hud;
 friend bool operator==(const RmtmDecisionScene267V1&,const RmtmDecisionScene267V1&)=default;
};
struct RmtmDecisionRaw267V1{
 RmtmDecisionSource267V1 source;std::uintptr_t list=0,detail=0,definition=0,controller=0,shortcut_manager=0,nav_widget=0;
 std::vector<std::byte>exact_model,modal_source;
 std::array<std::uintptr_t,5>rows{};
 std::vector<ck3_1210::GuiControlCallbackV1>nav_callbacks;
 bool native_read_entered=false,cleanup_known=true;
 friend bool operator==(const RmtmDecisionRaw267V1&,const RmtmDecisionRaw267V1&)=default;
};
enum class RmtmDecisionRawCallStatus267V1{refused,returned,indeterminate};
struct RmtmDecisionRawCall267V1{RmtmDecisionRawCallStatus267V1 status=RmtmDecisionRawCallStatus267V1::refused;bool effect_entered=false,cleanup_known=true,native_handled=false;};
bool VerifyRmtmDecisionImage267V1(std::uintptr_t)noexcept;
bool ReadRmtmDecisionRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const RmtmDecisionScene267V1&,std::uint64_t,RmtmDecisionRaw267V1&,std::string&)noexcept;
RmtmDecisionRawCall267V1 CallRmtmDecisionRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const RmtmDecisionScene267V1&,std::uint64_t,const RmtmDecisionRaw267V1&,RmtmDecisionAction267V1,std::optional<RmtmDecision267V1>)noexcept;
}
