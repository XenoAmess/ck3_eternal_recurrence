// Private scalar checkpoints, no native calls, retries, selectors or authority.
// Included in rmtm_observation_native before its current mechanical helpers.
enum class OfferStage267V1:unsigned {
 none,call_begin,issued_read_enter,issued_read_returned,issued_source_changed,
 right_click_enter,right_click_returned,post_click_fresh_rejected,opened_take_enter,
 opened_take_returned,opened_item_missing,opened_definition_missing,opened_recipient_mismatch,
 fixed_trigger_guard_enter,fixed_trigger_guard_returned,fixed_trigger_guard_rejected,
 item_can_enter,item_can_returned,item_can_payload_valid,item_can_payload_rejected,
 item_any_destroy_enter,item_any_destroy_returned,any_destroy_enter,any_destroy_returned,
 text_destroy_enter,text_destroy_returned,record_construct_enter,record_construct_returned,
 record_construct_output_matched,record_construct_output_rejected,trigger_eval_enter,
 trigger_eval_returned_true,trigger_eval_returned_false,window_getter_enter,
 window_getter_returned_match,window_getter_returned_mismatch,populate_enter,populate_returned,
 activate_enter,activate_returned,refresh_enter,refresh_returned,record_destroy_enter,
 record_destroy_returned,populate_returned_true,populate_returned_false,final_fresh_rejected,
 call_returned,call_refused,call_cpp_exception,record_definition_mismatch
};
struct OfferScalarPoint267V1 {
 std::uint32_t known=0,menu_selected_id=0;
 std::uint8_t menu_logical_visible=0,confirmation_logical_visible=0;
 std::int32_t category_count=0,more_count=0;
 std::uint8_t menu_flags=0,confirmation_flags=0;
 std::uint32_t view_B0_slot_rva=0;
 std::uint8_t cached_equals_origin=0,cached_anchor=0,chosen_anchor=0,context_matches=0;
};
struct OfferTrace267V1 {
 volatile unsigned stage=0,last_completed=0,event_count=0;
 volatile std::uint64_t milestones=0;
 volatile std::uint32_t exception_code=0,exception_module_rva=0,exception_stage=0,exception_count=0;
 volatile int item_handled=-1,item_payload=-1,item_cleanup=-1;volatile bool item_type_expected=false;
 volatile bool exception_observed=false,exception_in_module=false,active=false;
 std::uintptr_t image=0;
 std::array<unsigned char,192>events{};
 std::array<OfferScalarPoint267V1,3>scalar_points{};
 std::array<char,161>take_reason{};
 std::array<char,97>subreason{};
};
thread_local OfferTrace267V1 offer_trace267;
__declspec(noinline) void OfferTraceMark267(OfferStage267V1 stage,bool completed=false)noexcept{
 auto&d=offer_trace267;if(!d.active)return;
 _ReadWriteBarrier();const auto value=static_cast<unsigned>(stage);
 d.stage=value;if(completed)d.last_completed=value;
 if(value<64)d.milestones=d.milestones|(std::uint64_t{1}<<value);
 const unsigned count=d.event_count;
 d.events[count%d.events.size()]=static_cast<unsigned char>(value);d.event_count=count+1;
 _ReadWriteBarrier();
}
void OfferTraceTakeReason267(std::string_view reason)noexcept{
 auto&d=offer_trace267;if(!d.active)return;d.take_reason={};
 const auto length=(std::min)(reason.size(),d.take_reason.size()-1);
 for(std::size_t n=0;n<length;++n){const unsigned char c=static_cast<unsigned char>(reason[n]);
  d.take_reason[n]=c>=0x20&&c<0x7F?static_cast<char>(c):'_';}
}
void OfferTraceSub267(const char*reason)noexcept{
 auto&d=offer_trace267;if(!d.active)return;d.subreason={};
 for(std::size_t n=0;n+1<d.subreason.size()&&reason[n];++n)d.subreason[n]=reason[n];
}
void OfferTraceCan267(bool handled,bool expected,unsigned value,bool known,int cleanup=-1)noexcept{
 auto&d=offer_trace267;if(!d.active)return;d.item_handled=handled?1:0;
 d.item_type_expected=expected;d.item_payload=known&&value<=1?static_cast<int>(value):-1;
 if(cleanup>=0)d.item_cleanup=cleanup;
}
// Read-only snapshots of already-bound objects on the existing open path.
// known bits distinguish failed reads from actual zero. This never rejects,
// grants authority, changes status or invokes any additional native callback.
__declspec(noinline) void OfferTraceScalar267(unsigned point,const RmtmObservationFrame267V1&f,
 const RmtmObservationRaw267V1&bound)noexcept{
 auto&d=offer_trace267;if(!d.active||point>=d.scalar_points.size())return;
 _ReadWriteBarrier();OfferScalarPoint267V1 value;
 const auto anchor=[&](std::uintptr_t p){for(const auto&n:f.witness)if(n.widget==p&&n.parent==f.scene.global){if(n.name=="hud_layer")return std::uint8_t{1};if(n.name=="windows_layer")return std::uint8_t{2};}return p?std::uint8_t{3}:std::uint8_t{0};};
 value.chosen_anchor=anchor(bound.origin_widget);
 std::uintptr_t root=0,cache=0,context=0;
 if(At(bound.menu,0x60,root)&&At(root,0xD0,value.menu_flags))value.known|=1;
 if(At(bound.window,0x60,root)&&At(root,0xD0,value.confirmation_flags))value.known|=2;
 std::uintptr_t viewVt=0,viewB0=0;
 if(At(bound.menu,0,viewVt)&&At(viewVt,0xB0,viewB0)&&viewB0>=d.image&&viewB0-d.image<kImageSize){value.known|=4;value.view_B0_slot_rva=static_cast<std::uint32_t>(viewB0-d.image);}
 if(At(f.scene.handler,0x16C38,cache)){value.known|=16;value.cached_equals_origin=cache==bound.origin_widget;value.cached_anchor=anchor(cache);}
 if(At(bound.menu,0xD0,value.menu_selected_id))value.known|=32;
 if(At(bound.menu,0x98,context)){value.known|=64;value.context_matches=context==f.scene.jomini;}
 if(At(bound.menu,0x124,value.category_count))value.known|=128;
 if(At(bound.menu,0xEC,value.more_count))value.known|=256;
 try{std::vector<std::byte>temporary;bool logical=false;
  if(OfferLogicalVisible267V1(d.image,bound.menu,temporary,logical)){value.known|=512;value.menu_logical_visible=logical?1:0;}
  temporary.clear();
  if(OfferLogicalVisible267V1(d.image,bound.window,temporary,logical)){value.known|=1024;value.confirmation_logical_visible=logical?1:0;}
 }catch(...){/* telemetry is best effort and never changes action/status */}
 d.scalar_points[point]=value;_ReadWriteBarrier();
}
int OfferTraceException267(EXCEPTION_POINTERS*exception)noexcept{
 auto&d=offer_trace267;
 if(d.active&&exception&&exception->ExceptionRecord){
  d.exception_count=d.exception_count+1;
  // Preserve the first observed exception if best-effort cleanup also faults.
  if(!d.exception_observed){
   d.exception_observed=true;d.exception_code=exception->ExceptionRecord->ExceptionCode;d.exception_stage=d.stage;
   const auto pc=reinterpret_cast<std::uintptr_t>(exception->ExceptionRecord->ExceptionAddress);
   if(pc>=d.image&&pc-d.image<kImageSize){d.exception_in_module=true;d.exception_module_rva=static_cast<std::uint32_t>(pc-d.image);}
   else{d.exception_in_module=false;d.exception_module_rva=0;}
  }
 }
 return EXCEPTION_EXECUTE_HANDLER;
}
struct OfferTraceScope267 {
 explicit OfferTraceScope267(std::uintptr_t image,bool enabled)noexcept{
  offer_trace267={};offer_trace267.image=image;offer_trace267.active=enabled;
  OfferTraceMark267(OfferStage267V1::call_begin);
 }
 ~OfferTraceScope267(){offer_trace267.active=false;}
};
