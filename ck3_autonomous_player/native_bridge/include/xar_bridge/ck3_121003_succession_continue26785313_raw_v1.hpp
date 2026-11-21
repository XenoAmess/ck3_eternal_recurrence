#pragma once
#include "xar_bridge/ck3_121003_succession_lifecycle26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct SuccessionRawBindings267V1 {std::uintptr_t image=0;bool verified=false;};
struct SuccessionExpectedWindow267V1 {std::uintptr_t jomini=0,gfx=0,handler=0,root=0,gui_context=0;};
struct SuccessionRawSample267V1 {
 std::uintptr_t controller=0,root=0,context=0,handler=0,jomini=0,dead_character=0,continue_character=0;
 std::uintptr_t game_state=0,game_data=0,player_rows=0,active_player_row=0;
 std::int32_t dead_character_id=-1,continue_character_id=-1,player_id=-1,opaque_token=-1,kind=-1,alternate_id=-1;
 std::int32_t row_capacity=0,row_count=0;std::uint8_t alternate_mode=0,row_active=0;
 bool native_open=false,native_paused_by_succession=false;
 friend bool operator==(const SuccessionRawSample267V1&,const SuccessionRawSample267V1&)=default;
};
enum class SuccessionRawCallStatus267V1 {unavailable,returned,indeterminate};
struct SuccessionRawCall267V1 {SuccessionRawCallStatus267V1 status=SuccessionRawCallStatus267V1::unavailable;bool effect_entered=false;};
bool VerifySuccessionContinueImage267V1(std::uintptr_t) noexcept;
SuccessionRawBindings267V1 BindSuccessionContinueImage267V1(std::uintptr_t,std::string_view) noexcept;
// Raw primitives do not authorize an owner. The fixed lifecycle executor must
// independently bind real world/app/TLS/ticket, named root/default button and
// query/claim/deadlines. Caller-supplied pointers/booleans never enter the wire.
bool ReadSuccessionContinueRaw267V1(const ReadonlyBindings&,const SuccessionRawBindings267V1&,
 const SuccessionExpectedWindow267V1&,SuccessionRawSample267V1&,std::string&) noexcept;
SuccessionRawCall267V1 CallSuccessionContinueRaw267V1(const ReadonlyBindings&,const SuccessionRawBindings267V1&,
 const SuccessionExpectedWindow267V1&,const SuccessionRawSample267V1&) noexcept;
}
