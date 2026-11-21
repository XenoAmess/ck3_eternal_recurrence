#include "xar_bridge/ck3_121003_rite_doctrine26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_category26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_select26785313_v1.hpp"
#include "xar_bridge/ck3_121003_doctrine_knowledge26785313_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstring>
#include <limits>
#include <windows.h>
namespace xar::ck3_121003::build26785313 { namespace {
using Action=RiteDoctrineAction267V1;using Status=RiteDoctrineStatus267V1;
std::atomic<std::uint64_t> next_provider{1};
[[maybe_unused]]bool SameCore(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b) noexcept {
 return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&
  a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&
  a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;
}
std::uint64_t Wall() noexcept {
 const auto n=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return n<0?0:static_cast<std::uint64_t>(n);
}
[[maybe_unused]]bool Unexpired(const RiteDoctrineContext267V1&q) noexcept {
 const auto wall=Wall();return wall&&q.monotonic_deadline_ms&&wall<q.request.window.deadline_unix_ms&&GetTickCount64()<q.monotonic_deadline_ms;
}
[[maybe_unused]]RiteDraftV2 StructuralDraft(RiteDraftV2 value) {
 value.window.ticket_sequence=0;value.window.pump_epoch=0;return value;
}
struct Frame {
 std::uintptr_t game_state=0,jomini_state=0;
 RiteDraftV2 draft{};
 DynasticCategoryTarget267V1 category{};
 RiteDoctrineItems267V1 picker{};
 std::uintptr_t item=0,doctrine=0;
 RiteDoctrineFacts267V1 facts{};
 std::optional<ck3_1210::GuiControlCaptureV1> controls;
};
[[maybe_unused]]bool SameSource(const Frame&a,const Frame&b) {
 return a.game_state==b.game_state&&a.jomini_state==b.jomini_state&&StructuralDraft(a.draft)==StructuralDraft(b.draft)&&a.category==b.category&&a.picker==b.picker&&a.item==b.item&&a.doctrine==b.doctrine&&a.controls==b.controls&&
  SameCore(a.facts.core,b.facts.core)&&a.facts.should_display_evaluated==b.facts.should_display_evaluated&&a.facts.should_display==b.facts.should_display&&
  a.facts.can_pick_evaluated==b.facts.can_pick_evaluated&&a.facts.can_pick==b.facts.can_pick&&
  a.facts.knowledge_evaluated==b.facts.knowledge_evaluated&&a.facts.known_doctrine==b.facts.known_doctrine&&
  a.facts.selected_evaluated==b.facts.selected_evaluated&&a.facts.selected==b.facts.selected;
}
[[maybe_unused]]bool Capture(RiteDoctrineContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&stamp,Frame&out,std::string&reason) {
 out={};ReadonlyObservation observation;
 RiteDraftRequestV2 request{q.request.window,q.request.expected_source_rite_id};
 if(!Unexpired(q)||!ReadRiteDoctrineDraftOnOwner267V1(q.bindings,q.mailbox,q.ticket,stamp,&q,request,observation)||
    !observation.available||observation.offline_fixture||!observation.main_owner_observed||!observation.partial||
    !observation.rite_draft||observation.gui_window||observation.gui_root_index||observation.raw_resources||
    !SameCore(observation.core,q.request.window.expected_core)) {reason="current_rite_owner_source_unavailable";return false;}
 auto&facts=out.facts;facts.core=observation.core;facts.core_before_verified=true;facts.source_rite_verified=true;
 out.game_state=stamp.game_state;out.jomini_state=stamp.jomini_state;
 facts.source_rite_id=observation.rite_draft->source_rite_id;facts.connection_generation=q.connection_generation;
 facts.ticket_sequence=q.ticket.sequence;facts.pump_epoch=stamp.pump_epoch;facts.thread_id=stamp.thread_id;
 facts.can_edit_evaluated=true;facts.can_edit=observation.rite_draft->can_edit_rite_native;
 facts.piety_cost_raw=observation.rite_draft->piety_cost_raw;facts.piety_missing_raw=observation.rite_draft->piety_missing_raw;
 out.draft=*observation.rite_draft;
 ck3_1210::GuiControlCaptureV1 controls;
 if(CaptureGuiControlWindow267V2(BindGuiControlImage267V2(q.bindings.module_base,kExecutableSha256),out.draft.window,controls,reason))out.controls=std::move(controls);
 // The read-only query walks actual typed draft values. It never invokes
 // GetCategoryHelper/GetCategoryArray, which can construct UI helper caches.
 if(!ReadRawDynasticDraftTarget267V1(q.bindings,out.draft.controller,out.category,reason))return false;
 if(!ReadRiteDoctrineItems267V1(q.bindings,out.draft.controller,out.picker,reason))return false;
 const auto*target=FindUniqueRiteDoctrineKey267V1(out.picker,kRiteDoctrineTarget267V1);
 facts.category_available=true;facts.target_available=target!=nullptr;
 const auto selected=BindDoctrineSelectImage267V1(q.bindings.module_base,kExecutableSha256);
 // The picker may legitimately close/clear after selection. Confirm can still
 // prove the selected doctrine from the same key-qualified actual draft item.
 const auto selected_doctrine=target?target->doctrine:
  out.category.doctrine_key.exact_bytes==kRiteDoctrineTarget267V1?out.category.doctrine:0;
 if(selected_doctrine) {
  const auto has=ReadRawHasDoctrineSelected267V1(q.bindings,selected,out.draft.controller,selected_doctrine);
  facts.selected_evaluated=has.status==RawDoctrineObservationStatus267V1::observed;facts.selected=has.has_selected;
 }
 if(target) {
  out.item=target->item;out.doctrine=target->doctrine;
  const auto predicates=ReadRawDoctrinePredicates267V1(q.bindings,selected,out.draft.controller,out.item);
  facts.should_display_evaluated=predicates.status==RawDoctrineObservationStatus267V1::observed;
  facts.can_pick_evaluated=facts.should_display_evaluated;
  facts.should_display=predicates.should_display;facts.can_pick=predicates.can_pick;
  // Resolve the same played character through the already verified Core DB;
  // the raw helper rechecks identity, generation, death and actual membership.
  auto*actor=ck3_1210::ResolveCoreCharacter(q.bindings.core,observation.core.played_character_id);
  const auto known=ReadRawKnowsDoctrine267V1(q.bindings,reinterpret_cast<std::uintptr_t>(actor),out.doctrine);
  facts.knowledge_evaluated=known.status!=RawDoctrineKnowledgeStatus267V1::unavailable;
  facts.known_doctrine=known.status==RawDoctrineKnowledgeStatus267V1::native_true;
 }
 if(!Unexpired(q)){reason="current_rite_deadline_expired";return false;}
 reason.clear();return true;
}
// Each SEH wrapper contains POD only, with C++ owners outside the native call.
[[maybe_unused]]bool ShowCategory(const DoctrineCategoryBindings267V1&b,std::uintptr_t controller,std::int32_t slot) noexcept {
 __try {b.show_window(reinterpret_cast<void*>(controller+0x890),slot);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
[[maybe_unused]]bool CategoryState(const Frame&f,bool after) noexcept {
 const auto controller=f.draft.controller;
 if(!controller||controller>(std::numeric_limits<std::uintptr_t>::max)()-0x8E8)return false;
 std::uintptr_t parent=0,group=0,doctrine=0;std::int32_t slot=-1;SIZE_T got=0;
 const auto read=[&](std::uintptr_t address,void*value,std::size_t size){got=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<const void*>(address),value,size,&got)&&got==size;};
 if(!read(controller+0x890,&parent,sizeof(parent))||parent!=controller)return false;
 if(!after)return true;
 return read(controller+0x898,&group,sizeof(group))&&group==f.category.group&&
  read(controller+0x8A0,&doctrine,sizeof(doctrine))&&doctrine==f.category.doctrine&&
  read(controller+0x8E0,&slot,sizeof(slot))&&slot==f.category.slot;
}
[[maybe_unused]]bool ModalScope(const Frame&f) noexcept {
 if(!f.controls||f.draft.window.tree.empty())return false;
 const auto&root=f.draft.window.tree.front();if(!root.visible||!root.enabled)return false;
 const auto&capture=*f.controls;
 if(capture.modal_receivers.size()!=capture.modal_flags.size())return false;
 bool visible=false;for(const auto flags:capture.modal_flags)if((flags&8)==0)visible=true;
 if(!visible)return true;if(capture.modal_receivers.empty())return false;
 const auto selected=capture.modal_receivers.back();
 if(selected==root.widget||selected==f.draft.window.global_root)return true;
 for(const auto&ancestor:f.draft.window.ancestors)if(ancestor.widget==selected)return true;
 return false;
}
// Pure retained bookkeeping, exercised independently in NoGame. Possessing a
// record never proves an owner or dispatches a callback. The fixed executor
// supplies the actual native world/source only after its repeated admission.
struct RiteClaimSource {
 std::uintptr_t game_state=0,jomini_state=0;
 std::uint32_t source_rite_id=0xFFFFFFFFU;
 ck3_1210::CoreSnapshotPrefix core{};
};
enum class RiteClaimDecision { ready,consumed,unknown,capacity_exhausted };
struct RiteClaimBook {
 struct Claim {RiteDoctrineRequest267V1 request{};RiteClaimSource source{};Status status=Status::indeterminate;};
 std::array<Claim,kRiteDoctrineMaximumClaims267V1> claims{};
 std::size_t size=0;std::atomic_bool unknown{false};
 RiteClaimDecision Inspect(const RiteDoctrineRequest267V1&r,const RiteClaimSource&source) const noexcept {
  if(unknown.load(std::memory_order_acquire))return RiteClaimDecision::unknown;
  for(std::size_t i=0;i<size;++i) {
   const auto&old=claims[i];
   const bool same_role=old.source.game_state==source.game_state&&old.source.jomini_state==source.jomini_state&&
    old.source.source_rite_id==source.source_rite_id&&old.source.core.clock.date_raw==source.core.clock.date_raw&&
    old.source.core.local_player_id==source.core.local_player_id&&old.source.core.played_character_id==source.core.played_character_id;
   // Window reopening, reconnecting, changing speed or replacing the request
   // ID does not authorize the same effect again for the original actor/day.
   if(old.request.id()==r.id()||(same_role&&old.request.action==r.action))return RiteClaimDecision::consumed;
  }
  return size==claims.size()?RiteClaimDecision::capacity_exhausted:RiteClaimDecision::ready;
 }
 std::size_t ClaimOnce(const RiteDoctrineRequest267V1&r,const RiteClaimSource&source) {
  if(Inspect(r,source)!=RiteClaimDecision::ready)return 0;
  claims[size]={r,source,Status::indeterminate};return ++size;
 }
 void Finish(std::size_t sequence,Status status) noexcept {
  if(!sequence||sequence>size){unknown.store(true,std::memory_order_release);return;}
  claims[sequence-1].status=status;
  if(status==Status::indeterminate)unknown.store(true,std::memory_order_release);
 }
};
[[maybe_unused]]bool ConfirmNative(std::uintptr_t function,std::uintptr_t manager,std::uintptr_t widget,bool&handled) noexcept {
 using Native=bool(*)(void*,std::int32_t,void*,void*);
 alignas(void*)std::byte text[0x20]{};alignas(void*)std::byte pimpl[0x50]{};const std::uint64_t capacity=15;
 std::memcpy(text+0x18,&capacity,8);std::memcpy(pimpl+0x48,&widget,8);
 __try {handled=reinterpret_cast<Native>(function)(reinterpret_cast<void*>(manager),0,text,pimpl);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
} // namespace
struct RiteDoctrineSession267V1::State {
 RiteClaimBook book;
 bool query_valid=false;
 std::uint64_t provider_generation=0,query_sequence=0,connection_generation=0;
 Frame issued{};
};
RiteDoctrineSession267V1::RiteDoctrineSession267V1():state_(std::make_unique<State>()){}
RiteDoctrineSession267V1::~RiteDoctrineSession267V1()=default;
void BlockRiteDoctrineUnknown267V1(RiteDoctrineSession267V1&s) noexcept {s.state_->book.unknown.store(true,std::memory_order_release);}
void ArmRiteDoctrineDeadline267V1(RiteDoctrineContext267V1&q) noexcept {
 q.monotonic_deadline_ms=0;const auto wall=Wall();if(!wall||q.request.window.deadline_unix_ms<=wall)return;
 q.monotonic_deadline_ms=GetTickCount64()+(std::min)(q.request.window.deadline_unix_ms-wall,std::uint64_t{8000});
}
bool ExecuteRiteDoctrineInner267V1(RiteDoctrineContext267V1&q,const ck3_11906::MainThreadExecutionStampV1&stamp) noexcept {
 q.result={};q.result.action=q.request.action;
 q.result.provider_generation=q.request.provider_generation;q.result.query_sequence=q.request.query_sequence;
#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1) && XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
 try {
  const auto reject=[&](Status status,const char*reason){q.result.status=status;q.result.reason=reason;return true;};
  if(!q.session||!q.game||!q.game->enabled()||!game::IsCk3_121003Core26785313Descriptor(q.game->descriptor())||
     !q.game->supports(kRiteDoctrineCapability267V1)||!q.mailbox||q.mailbox->offline_fixture||!q.connection_generation||
     q.request.window.connection_generation!=q.connection_generation||!RiteDoctrineRequestShape267V1(q.request))return reject(Status::unavailable,"current_rite_profile_unavailable");
  auto&s=*q.session->state_;if(s.book.unknown.load(std::memory_order_acquire))return reject(Status::indeterminate,"current_rite_prior_unknown_no_replay");
  if(!Unexpired(q))return reject(Status::expired,"current_rite_deadline_expired");
  Frame first,second;std::string reason;
  if(!Capture(q,stamp,first,reason)||!Capture(q,stamp,second,reason)||!SameSource(first,second))return reject(Status::source_changed,"current_rite_repeated_source_unavailable");
  q.result.facts=second.facts;
  if(q.request.action==Action::query) {
   if(!s.provider_generation){s.provider_generation=next_provider.fetch_add(1);if(!s.provider_generation)return reject(Status::capacity_exhausted,"current_rite_generation_exhausted");}
   if(s.query_sequence==(std::numeric_limits<std::uint64_t>::max)())return reject(Status::capacity_exhausted,"current_rite_sequence_exhausted");
   ++s.query_sequence;s.connection_generation=q.connection_generation;s.issued=std::move(second);s.query_valid=true;
   q.result.provider_generation=s.provider_generation;q.result.query_sequence=s.query_sequence;q.result.status=Status::available;return true;
  }
  if(!s.query_valid||s.provider_generation!=q.request.provider_generation||s.query_sequence!=q.request.query_sequence||
     s.connection_generation!=q.connection_generation||!SameSource(s.issued,second))return reject(Status::query_consumed,"current_rite_private_query_changed_or_consumed");
  s.query_valid=false;
  const RiteClaimSource claim_source{second.game_state,second.jomini_state,q.request.expected_source_rite_id,second.facts.core};
  const auto decision=s.book.Inspect(q.request,claim_source);
  if(decision==RiteClaimDecision::consumed)return reject(Status::claim_consumed,"current_rite_retained_claim_no_replay");
  if(decision==RiteClaimDecision::unknown)return reject(Status::indeterminate,"current_rite_prior_unknown_no_replay");
  if(decision==RiteClaimDecision::capacity_exhausted)return reject(Status::capacity_exhausted,"current_rite_claim_capacity_exhausted");
  const auto&f=second.facts;
  if(!ModalScope(second))return reject(Status::unavailable,"current_rite_enabled_modal_source_unavailable");
  if(q.request.action==Action::open_dynastic_category&&!CategoryState(second,false))return reject(Status::prerequisite_rejected,"current_rite_category_parent_unavailable");
  if(q.request.action==Action::select_dynastic&&(!f.knowledge_evaluated||!f.known_doctrine))
    return reject(Status::unavailable,"current_rite_pam_unresolved_known_branch_not_true");
  if(q.request.action==Action::select_dynastic&&(!f.target_available||!f.should_display_evaluated||!f.should_display||
     !f.can_pick_evaluated||!f.can_pick||!f.selected_evaluated||f.selected))
    return reject(Status::prerequisite_rejected,"current_rite_native_display_pick_or_selection_rejected");
  if(q.request.action==Action::confirm_edit&&(!f.selected_evaluated||!f.selected||!f.can_edit_evaluated||!f.can_edit||f.piety_missing_raw>0))
    return reject(Status::prerequisite_rejected,"current_rite_full_native_can_cost_or_dynastic_selection_rejected");
  ck3_1210::GuiControlCaptureV1 controls;std::uintptr_t confirmation_widget=0;
  if(q.request.action==Action::confirm_edit) {
   if(!second.controls)return reject(Status::source_changed,"current_rite_confirmation_callback_source_unavailable");
   controls=*second.controls;
   unsigned matches=0;
   for(const auto&row:controls.widgets)if(row.row.runtime_name=="edit_faith"&&row.row.clickable){confirmation_widget=row.widget;++matches;}
   if(matches!=1)return reject(Status::prerequisite_rejected,"current_rite_confirmation_not_unique_and_admissible");
  }
  Frame final;
  if(!Capture(q,stamp,final,reason)||!SameSource(second,final)||!Unexpired(q)||s.book.unknown.load(std::memory_order_acquire))return reject(Status::source_changed,"current_rite_prewrite_source_changed");
  const auto sequence=s.book.ClaimOnce(q.request,claim_source);
  if(!sequence)return reject(Status::claim_consumed,"current_rite_claim_changed_before_native_call");
  q.result.claim_sequence=sequence;q.result.effect_attempted=true;
  if(q.request.action==Action::open_dynastic_category) {
   const auto b=BindDoctrineCategoryImage267V1(q.bindings.module_base,kExecutableSha256);
   if(!b.verified){q.result.effect_attempted=false;s.book.Finish(sequence,Status::unavailable);return reject(Status::unavailable,"current_rite_category_binding_unavailable");}
   q.result.native_returned=ShowCategory(b,final.draft.controller,final.category.slot);
  }else if(q.request.action==Action::select_dynastic) {
   const auto b=BindDoctrineSelectImage267V1(q.bindings.module_base,kExecutableSha256);
   const auto call=CallRawSelectDoctrine267V1(q.bindings,b,final.draft.controller,final.item);
   q.result.effect_attempted=call.effect_attempted;q.result.native_returned=call.status==RawDoctrineSelectDispatch267V1::call_returned;
  }else q.result.native_returned=ConfirmNative(q.bindings.module_base+0x4089380,controls.shortcut_manager,confirmation_widget,q.result.native_handled);
  if(!q.result.native_returned&&!q.result.effect_attempted){s.book.Finish(sequence,Status::unavailable);return reject(Status::unavailable,"current_rite_native_call_not_entered_claim_retained");}
  if(!q.result.native_returned){s.book.Finish(sequence,Status::indeterminate);return reject(Status::indeterminate,"current_rite_native_call_unknown_no_replay");}
  if(q.request.action==Action::confirm_edit) {
   // The native engine mode0 honors enabled/visibility/modal/callback gates.
   // A returned handled callback does not prove the edited Rite persisted.
   q.result.status=q.result.native_handled?Status::confirmation_dispatched:Status::indeterminate;
   if(!q.result.native_handled)s.book.unknown.store(true,std::memory_order_release);
  }else {
   Frame after;
   if(!Capture(q,stamp,after,reason)||after.draft.controller!=final.draft.controller||
      after.draft.source_rite_id!=final.draft.source_rite_id||!SameCore(after.facts.core,final.facts.core)) {
    s.book.Finish(sequence,Status::indeterminate);return reject(Status::indeterminate,"current_rite_postwrite_source_unknown_no_replay");
   }
   if(q.request.action==Action::open_dynastic_category) {
    if(!CategoryState(final,true)||!CategoryState(final,true)){s.book.Finish(sequence,Status::indeterminate);return reject(Status::indeterminate,"current_rite_category_readback_unknown_no_replay");}
    q.result.status=Status::category_opened;
   }
   else if(after.facts.selected_evaluated&&after.facts.selected){q.result.post_selected_evaluated=true;q.result.post_selected=true;q.result.status=Status::draft_selected;}
   else {s.book.Finish(sequence,Status::indeterminate);return reject(Status::indeterminate,"current_rite_selection_not_observed_no_replay");}
  }
  s.book.Finish(sequence,q.result.status);return true;
 }catch(...){if(q.result.effect_attempted&&q.session)BlockRiteDoctrineUnknown267V1(*q.session);q.result.status=q.result.effect_attempted?Status::indeterminate:Status::unavailable;q.result.reason="current_rite_executor_exception_no_retry";}
#else
 (void)stamp;
#endif
 return true;
}
bool ExecuteRiteDoctrineOnOwner267V1(void*ptr,const ck3_11906::MainThreadExecutionStampV1&stamp) noexcept {
 if(!ptr)return false;auto&q=*static_cast<RiteDoctrineContext267V1*>(ptr);
 __try {return ExecuteRiteDoctrineInner267V1(q,stamp);}
 __except(EXCEPTION_EXECUTE_HANDLER){if(q.result.effect_attempted&&q.session)BlockRiteDoctrineUnknown267V1(*q.session);q.result.status=q.result.effect_attempted?Status::indeterminate:Status::unavailable;return true;}
}
} // namespace xar::ck3_121003::build26785313
