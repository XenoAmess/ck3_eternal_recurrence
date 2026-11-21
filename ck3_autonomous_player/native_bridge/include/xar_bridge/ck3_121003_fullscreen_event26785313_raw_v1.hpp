#pragma once
#include "xar_bridge/ck3_121003_fullscreen_event26785313_v1.hpp"
#include "xar_bridge/ck3_121003_letter26785313_raw_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct FullscreenEventBindings267V1{std::uintptr_t image=0;bool verified=false;};
struct FullscreenEventScene267V1{std::uint64_t wall_deadline=0;std::uintptr_t jomini=0,gfx=0,context=0,global=0,top=0,fullscreen=0;bool visible=false,enabled=false;friend bool operator==(const FullscreenEventScene267V1&,const FullscreenEventScene267V1&)=default;};
struct FullscreenEventRaw267V1{
 FullscreenEventSource267V1 source;std::uintptr_t game=0,jomini=0,manager=0,items=0,window=0,item=0,data=0,runtime_event=0,definition=0,options=0,custom=0,completion=0;
 std::array<std::byte,16>items_header{},options_header{},authored_header{},template_pool_header{};
 std::vector<std::uintptr_t>item_pointers,item_data_pointers,option_pointers,authored_option_pointers;
 std::int32_t authored_option_count=0,selected_index=-1;std::uint32_t template_id=0;
 bool cleanup_known=true,native_read_entered=false;
 friend bool operator==(const FullscreenEventRaw267V1&,const FullscreenEventRaw267V1&)=default;
};
enum class FullscreenEventRawCallStatus267V1{unavailable,returned,indeterminate};
struct FullscreenEventRawCall267V1{FullscreenEventRawCallStatus267V1 status=FullscreenEventRawCallStatus267V1::unavailable;bool effect_entered=false,cleanup_known=true;};
bool VerifyFullscreenEventImage267V1(std::uintptr_t)noexcept;
FullscreenEventBindings267V1 BindFullscreenEventImage267V1(std::uintptr_t,std::string_view)noexcept;
bool ReadFullscreenEventRaw267V1(const ReadonlyBindings&,const FullscreenEventBindings267V1&,const ck3_1210::CoreSnapshotPrefix&,const FullscreenEventScene267V1&,std::uint64_t,FullscreenEventRaw267V1&,std::string&)noexcept;
FullscreenEventRawCall267V1 AcknowledgeKnownFullscreenEventRaw267V1(const ReadonlyBindings&,const FullscreenEventBindings267V1&,const ck3_1210::CoreSnapshotPrefix&,const FullscreenEventScene267V1&,std::uint64_t,const FullscreenEventRaw267V1&)noexcept;
enum class RuntimeEventTimeGate267V1{unavailable,clear,blocked,indeterminate};
RuntimeEventTimeGate267V1 ReadRuntimeEventTimeGate267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&)noexcept;
}
