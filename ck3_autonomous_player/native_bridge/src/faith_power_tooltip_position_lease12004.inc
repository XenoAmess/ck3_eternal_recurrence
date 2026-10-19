// Fixed presentation lifecycle; original tooltip strategies receive a point
// derived from the current typed widget, never caller/desktop coordinates.
MainThreadQueryMailboxV1*presentation_position_mailbox12004=nullptr;
std::atomic<std::uint32_t>presentation_position_thread12004{0};
std::atomic<std::uint64_t>presentation_position_connection12004{0};
struct PresentationPositionFrame12004 {
 std::uintptr_t jomini=0,game=0,tls=0;std::uint32_t actor=0;
 std::int32_t date=0;std::uint8_t initialized=0,main=0,paused=0;
 bool operator==(const PresentationPositionFrame12004&)const=default;
};
struct PresentationPositionSource12004 {
 void*window=nullptr,*root=nullptr,*source=nullptr,*vtable=nullptr,*data_context=nullptr;
 std::uint32_t subject=0;
 bool operator==(const PresentationPositionSource12004&)const=default;
};
struct PresentationPositionLease12004 {
 ZhongguoScoreboardNativeEnvironmentV1 environment{};
 PresentationTargetBinding12004 binding{};
 PresentationPositionFrame12004 frame{};
 PresentationPositionSource12004 source{};
 void*handler=nullptr;std::string nonce;
 std::uint32_t window_kind=0;std::uint64_t origin_epoch=0,generation=0,updates=0;
 bool active=false;const char*failure="presentation_tooltip_position_not_activated";
};
PresentationPositionLease12004 presentation_position_lease12004{};
void CancelPresentationTooltipPosition12004() noexcept {
 presentation_position_thread12004.store(0,std::memory_order_release);
 presentation_position_lease12004.active=false;
}
bool PresentationPositionTls12004(MainThreadTlsContextGetterV1 getter,std::uintptr_t&out) noexcept {
 out=0;if(!getter)return false;
#if defined(_MSC_VER)
 __try{out=reinterpret_cast<std::uintptr_t>(getter());return out!=0;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
 return false;
#endif
}
bool ReadPresentationPositionFrame12004(const ZhongguoScoreboardNativeEnvironmentV1&e,
    PresentationPositionFrame12004&out,std::string*why=nullptr) {
 out={};const auto fail=[&](const char*reason){if(why)*why=reason;return false;};
 auto*m=presentation_position_mailbox12004;
 if(!m)return fail("presentation_position_mailbox_missing");
 if(m->module_base!=e.module_base)return fail("presentation_position_mailbox_module_differs");
 if(m->stop_requested.load(std::memory_order_acquire))return fail("presentation_position_owner_stopped");
 if(m->owner_thread_id.load(std::memory_order_acquire)!=GetCurrentThreadId())return fail("presentation_position_owner_thread_differs");
 if(!Slot(m->jomini_state_slot,out.jomini)||!out.jomini)return fail("presentation_position_jomini_slot_unreadable_or_null");
 if(!Slot(m->game_state_slot,out.game)||!out.game)return fail("presentation_position_game_slot_unreadable_or_null");
 if(!Slot(m->tls_initialized_flag,out.initialized)||out.initialized!=1)return fail("presentation_position_tls_flag_unverified");
 if(!PresentationPositionTls12004(m->tls_context_getter,out.tls))return fail("presentation_position_original_tls_getter_failed");
 if(!Value(reinterpret_cast<void*>(out.tls),kMainThreadTlsMarkerOffset,out.main)||out.main!=1)return fail("presentation_position_tls_main_marker_unverified");
 if(!Value(reinterpret_cast<void*>(out.jomini),kJominiPausedOffset,out.paused)||!out.paused)return fail("presentation_position_actual_pause_unverified");
 if(!Value(reinterpret_cast<void*>(out.game),kGameStateDateRawOffset,out.date))return fail("presentation_position_actual_date_unreadable");
 if(!Slot(e.module_base+0x54DBC00,out.actor)||!out.actor||out.actor==0xFFFFFFFFU)return fail("presentation_position_actual_actor_unreadable_or_invalid");
 return true;
}
bool ReadPresentationPositionSource12004(const PresentationPositionLease12004&lease,
    PresentationPositionSource12004&out) {
 out={};const auto&e=lease.environment;const auto&binding=lease.binding;
 IngameUiGuiOwnerBindingV1 gui{};void*handler=nullptr;
 if(!ReadIngameUiGuiOwnerBindingV1(e,gui)||gui!=binding.gui||
     !ResolveHandler(e,handler)||handler!=lease.handler)return false;
 const auto kind=static_cast<IngameUiWindowKindV1>(lease.window_kind);
 if(kind==IngameUiWindowKindV1::faith){
   ck3_12004::religion_ui::Selection s{};
   if(!ck3_12004::religion_ui::ReadSelection12004(ck3_12004::religion_ui::BindImage12004(e.module_base,e.executable_sha256),
       handler,ck3_12004::religion_ui::Window::faith,s)||!s.window||!s.root||!s.subject_available)return false;
   out.window=const_cast<void*>(s.window);out.root=const_cast<void*>(s.root);out.subject=s.subject_id;
 }else if(kind==IngameUiWindowKindV1::holding||kind==IngameUiWindowKindV1::personal_beliefs){
   PresentationWindow12004 s{};std::string why;
   if(!ReadPresentationOwnedWindow12004(e,handler,kind,s,why)||!s.present||!s.subject_available)return false;
   out.window=s.window;out.root=s.root;out.subject=s.subject;
   if(kind==IngameUiWindowKindV1::holding&&binding.root!=out.root){
     // Preview/Construct carriers belong to the owned tracks root, while
     // installed-building carriers remain under the main holding root.
     void*tracks=nullptr,*owner=nullptr,*back=nullptr,*tracks_handler=nullptr,*root=nullptr;
     std::uintptr_t primary=0,secondary=0;
     if(!PresentationDetailSourcePins12004(e)||!Value(s.window,0xC8,tracks)||!tracks||
         !Value(tracks,0,primary)||primary!=e.module_base+0x45435C0||
         !Value(tracks,0x10,secondary)||secondary!=e.module_base+0x4543690||
         !TypedObject(e.module_base,tracks,0x5769298,UiExactImageSizeV1(e.gui_abi_revision))||
         !ReadPresentationOuterOwner12004(e,handler,tracks,owner)||
         !Value(tracks,0xC8,back)||back!=s.window||!Value(tracks,0xA0,tracks_handler)||tracks_handler!=handler||
         !Value(tracks,0x60,root)||root!=binding.root)return false;
     ZhongguoScoreboardAccessV1 access{};void*named=nullptr,*widget=nullptr;
     if(!ResolveNamedGuiWidgetV1(e,access,"holding_tracks_view","holding_tracks_view",named,widget)||named!=root||widget!=root)return false;
     out.window=tracks;out.root=root;
   }
 }else if(kind==IngameUiWindowKindV1::rite_creation){
   // The supplied epoch labels the original lease. No new mailbox observation
   // or Snapshot is fabricated here; only actual current typed fields are used.
   ck3_12002::religion_reform::DraftWindowView s{};
   if(!ck3_12002::religion_reform::ReadCurrentRiteCreationWindow12002(
       ck3_12004::religion::BindCurrentRiteCreationWindow12004(e.module_base,e.executable_sha256),lease.origin_epoch,s)||
       !s.available||!s.present||!s.source_rite_id||s.date_raw!=lease.frame.date||
       s.played_character_id!=lease.frame.actor)return false;
   out.window=const_cast<void*>(s.window);out.subject=*s.source_rite_id;
   if(!Value(s.window,0x60,out.root))return false;
 }else return false;
 if(out.root!=binding.root||out.subject!=binding.subject||
     !ArmyTooltipVisibleAncestors(e,out.root,gui.context)||
     !ArmyTooltipResolvePath(e,out.root,gui.context,binding.path,out.source,false)||out.source!=binding.source||
     !ArmyTooltipVisibleAncestors(e,out.source,gui.context)||
     !Value(out.source,0,out.vtable)||!Value(out.source,0xE0,out.data_context))return false;
 if(kind==IngameUiWindowKindV1::personal_beliefs&&out.subject!=lease.frame.actor)return false;
 IngameUiModalAdmissionV1 modal{};
 return ReadModalNavigationAdmission(gui.context,modal);
}
struct PresentationPositionAncestor12004 {
 void*widget=nullptr,*parent=nullptr,*context=nullptr;float scale=0,cumulative=0;
 bool operator==(const PresentationPositionAncestor12004&)const=default;
};
bool ReadPresentationPositionAncestors12004(void*source,void*context,
    std::vector<PresentationPositionAncestor12004>&out,std::string*why=nullptr) {
 out.clear();void*at=source;
 const auto fail=[&](const char*reason){if(why)*why=std::string(reason)+";depth="+std::to_string(out.size());return false;};
 while(at){
   if(out.size()>=64||std::any_of(out.begin(),out.end(),[&](const auto&r){return r.widget==at;}))return fail("presentation_geometry_parent_cycle_or_bound");
   PresentationPositionAncestor12004 r{};r.widget=at;
   if(!Value(at,0xD8,r.context)||!Value(at,0xE8,r.parent)||!Value(at,0x110,r.scale))return fail("presentation_geometry_ancestor_fields_unreadable");
   if(r.context!=context)return fail("presentation_geometry_ancestor_context_differs");
   if(!std::isfinite(r.scale)||r.scale<=0||r.scale>64)return fail("presentation_geometry_ancestor_scale_invalid");
   // Original3A75EA0 uses +114 only on the source when it has a parent.
   // Root/other ancestors' unused fields are neither gated nor bookended.
   if(at==source&&r.parent){
     if(!Value(at,0x114,r.cumulative))return fail("presentation_geometry_source_cumulative_unreadable");
     if(!std::isfinite(r.cumulative)||r.cumulative<=0||r.cumulative>4096)return fail("presentation_geometry_source_cumulative_invalid");
   }
   out.push_back(r);at=r.parent;
 }
 return !out.empty()||fail("presentation_geometry_source_null");
}
bool InvokePresentationPositionRect12004(std::uintptr_t base,void*source,const UiRectV1&local,UiRectV1&rect,const char*&why) noexcept {
#if defined(_MSC_VER)
 __try{if(reinterpret_cast<GuiRectGetter>(base+0x3A75EA0)(source,&rect,&local)!=&rect){why="presentation_geometry_original_transform_unexpected_return";return false;}return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){why="presentation_geometry_original_transform_fault";return false;}
#else
 return false;
#endif
}
bool PresentationPositionPoint12004(const PresentationPositionLease12004&lease,std::uint64_t&point,std::string*why=nullptr) {
 const auto&e=lease.environment;void*source=lease.source.source;
 const auto fail=[&](const std::string&reason){if(why)*why=reason;return false;};
 // Original exact4 3A77D60 tests local [0,width128)x[0,height12C).
 // Exact4 3A75EA0 is its original local-rect to input-point-space transform.
 constexpr std::array<unsigned char,16>pin{0x48,0x89,0x5C,0x24,0x18,0x55,0x56,0x57,0x48,0x83,0xEC,0x40,0x0F,0x29,0x74,0x24};
 std::array<unsigned char,16>actual{};
 if(!Read(reinterpret_cast<void*>(e.module_base+0x3A75EA0),actual.data(),actual.size())||actual!=pin)return fail("presentation_geometry_loaded_rect_transform_prefix_mismatch");
 std::vector<PresentationPositionAncestor12004>first,last;
 UiRectV1 local{},again{},rect{};
 if(!ReadPresentationPositionAncestors12004(source,lease.binding.gui.context,first,why))return false;
 if(!Value(source,0x128,local.width)||!Value(source,0x12C,local.height))return fail("presentation_geometry_source_extent_unreadable");
 if(!FiniteRect(local,true))return fail("presentation_geometry_source_extent_invalid;w="+std::to_string(local.width)+";h="+std::to_string(local.height));
 const char*call_failure="presentation_geometry_original_transform_not_available";
 if(!InvokePresentationPositionRect12004(e.module_base,source,local,rect,call_failure))return fail(call_failure);
 if(!FiniteRect(rect,true))return fail("presentation_geometry_original_rect_invalid;w="+std::to_string(rect.width)+";h="+std::to_string(rect.height));
 if(!Value(source,0x128,again.width)||!Value(source,0x12C,again.height))return fail("presentation_geometry_extent_bookend_unreadable");
 if(local.width!=again.width||local.height!=again.height)return fail("presentation_geometry_extent_bookend_changed");
 if(!ReadPresentationPositionAncestors12004(source,lease.binding.gui.context,last,why))return false;
 if(last!=first)return fail("presentation_geometry_ancestor_bookend_changed");
 const UiFloat2V1 xy{rect.x+rect.width/2,rect.y+rect.height/2};
 if(!std::isfinite(xy.x)||!std::isfinite(xy.y)||std::abs(xy.x)>1048576||std::abs(xy.y)>1048576)return fail("presentation_geometry_final_native_point_invalid");
 static_assert(sizeof(xy)==sizeof(point));std::memcpy(&point,&xy,sizeof(point));return true;
}
bool PreparePresentationTooltipPosition12004(const ZhongguoScoreboardNativeEnvironmentV1&e,
    const IngameUiRequestV1&r,const game::Snapshot&snapshot,const MainThreadExecutionStampV1&stamp,
    const PresentationTargetBinding12004&binding,void*handler,std::string_view nonce,std::string&why) {
 CancelPresentationTooltipPosition12004();
 why.clear();const auto fail=[&](const char*reason){why=reason;return false;};
 if(!PresentationTooltipPositionHooksReady12004())return fail("presentation_position_fixed_hooks_not_ready");
 if(!presentation_position_mailbox12004)return fail("presentation_position_mailbox_not_bound");
 if(!r.connection_generation||presentation_position_connection12004.load(std::memory_order_acquire)!=r.connection_generation)return fail("presentation_position_active_connection_differs");
 PresentationPositionLease12004 next{};next.environment=e;next.binding=binding;next.handler=handler;
 next.window_kind=static_cast<std::uint32_t>(r.window_kind);next.origin_epoch=stamp.pump_epoch;
 next.generation=r.connection_generation;next.nonce=nonce;
 PresentationPositionFrame12004 last{};PresentationPositionSource12004 source2{};std::uint64_t point=0;
 if(!ReadPresentationPositionFrame12004(e,next.frame,&why))return false;
 if(next.frame.jomini!=stamp.jomini_state)return fail("presentation_position_stamp_jomini_differs");
 if(next.frame.game!=stamp.game_state)return fail("presentation_position_stamp_game_differs");
 if(next.frame.tls!=stamp.tls_context)return fail("presentation_position_stamp_tls_differs");
 if(next.frame.actor!=static_cast<std::uint32_t>(snapshot.played_character_id))return fail("presentation_position_snapshot_actor_differs");
 if(next.frame.date!=snapshot.date_raw)return fail("presentation_position_snapshot_date_differs");
 if(!ReadPresentationPositionSource12004(next,next.source))return fail("presentation_position_current_source_binding_unverified");
 if(!PresentationPositionPoint12004(next,point,&why))return false;
 if(!ReadPresentationPositionSource12004(next,source2))return fail("presentation_position_source_bookend_unreadable");
 if(source2!=next.source)return fail("presentation_position_source_bookend_changed");
 if(!ReadPresentationPositionFrame12004(e,last,&why))return false;
 if(last!=next.frame)return fail("presentation_position_actual_frame_bookend_changed");
 next.failure="presentation_tooltip_position_waiting_original_update";
 presentation_position_lease12004=std::move(next);return true;
}
void ActivatePresentationTooltipPosition12004() noexcept {
 auto&lease=presentation_position_lease12004;lease.active=true;
 presentation_position_thread12004.store(GetCurrentThreadId(),std::memory_order_release);
}
bool PresentationTooltipPositionOverride12004(void*gui,std::uint64_t&point) noexcept {
 // Only the actual owner thread may touch the non-atomic receipt/source data.
 if(presentation_position_thread12004.load(std::memory_order_acquire)!=GetCurrentThreadId())return false;
 auto&lease=presentation_position_lease12004;
 const auto fail=[&](const char*why){lease.failure=why;CancelPresentationTooltipPosition12004();return false;};
 if(!lease.active||lease.binding.gui.context!=gui)return false;
 if(!lease.generation||presentation_position_connection12004.load(std::memory_order_acquire)!=lease.generation)
   return fail("presentation_tooltip_position_connection_closed_or_changed");
 try{
   PresentationPositionFrame12004 first{},last{};PresentationPositionSource12004 source{},source2{};
   void*hover=nullptr;std::uint64_t candidate=point;
   if(!ReadPresentationPositionFrame12004(lease.environment,first)||first!=lease.frame)
     return fail("presentation_tooltip_position_actual_owner_frame_changed");
   if(!Value(gui,0xF0,hover)||hover!=lease.binding.source)
     return fail("presentation_tooltip_position_actual_hover_changed");
   if(!ReadPresentationPositionSource12004(lease,source)||source!=lease.source||
       !PresentationPositionPoint12004(lease,candidate)||!ReadPresentationPositionSource12004(lease,source2)||source2!=source||
       !ReadPresentationPositionFrame12004(lease.environment,last)||last!=first)
     return fail("presentation_tooltip_position_actual_source_geometry_or_owner_changed");
   point=candidate;++lease.updates;lease.failure=nullptr;return true;
 }catch(...){return fail("presentation_tooltip_position_capture_exception");}
}
bool PresentationTooltipPositionReceipt12004(std::string_view nonce,std::string&why) {
 const auto&lease=presentation_position_lease12004;
 if(!lease.active||lease.nonce!=nonce||!lease.updates){
   why=lease.failure?lease.failure:"presentation_tooltip_position_receipt_inactive";return false;
 }
 return true;
}
