#pragma once
#include "xar_bridge/rite_creation_actions12004.hpp"
#include <limits>
#include <utility>

namespace xar::ck3_12004::religion::rite_creation_actions::detail {
// Same pointer/capacity/count prefix consumed by the qualified draft-group
// reader. The two window arrays are 0x18 apart; their unused trailing bytes
// are not an additional prerequisite for reading the selected rows.
struct SelectedRowArrayHeader {
 const void*data=nullptr;
 std::int32_t capacity=0,count=0;
};
static_assert(sizeof(SelectedRowArrayHeader)==16);
static_assert(offsetof(SelectedRowArrayHeader,capacity)==8);
static_assert(offsetof(SelectedRowArrayHeader,count)==0xC);
enum class SelectedRowArray {tenets,doctrines};
enum class SelectedRowHeaderFailure {none,unreadable,header_misaligned,negative_count,
 capacity_below_count,count_above_bound,nonempty_rows_missing,rows_misaligned,row_span_overflow};
struct SelectedRowHeaders {
 SelectedRowArrayHeader tenets{},doctrines{};
};
inline SelectedRowHeaderFailure ReadSelectedRowHeader(
 const Bindings&b,const void*window,SelectedRowArray kind,SelectedRowArrayHeader&out) noexcept {
 out={};
 const std::size_t offset=kind==SelectedRowArray::tenets?0x778:0x790;
 // Preserve the existing request/SDK64-row DTO limit for both collections.
 constexpr std::int32_t count_limit=64;
 const std::size_t stride=kind==SelectedRowArray::tenets?0x70:0x48;
 const auto address=reinterpret_cast<std::uintptr_t>(window);
 constexpr auto maximum=std::numeric_limits<std::uintptr_t>::max();
 if(!address||offset>maximum-address||sizeof(out)-1>maximum-(address+offset)||!b.read_memory)
  return SelectedRowHeaderFailure::unreadable;
 if(address%alignof(void*)!=0)return SelectedRowHeaderFailure::header_misaligned;
 if(!b.read_memory(b.read_context,reinterpret_cast<const void*>(address+offset),&out,sizeof(out)))
  return SelectedRowHeaderFailure::unreadable;
 if(out.count<0)return SelectedRowHeaderFailure::negative_count;
 if(out.capacity<out.count)return SelectedRowHeaderFailure::capacity_below_count;
 if(out.count>count_limit)return SelectedRowHeaderFailure::count_above_bound;
 if(out.count&&!out.data)return SelectedRowHeaderFailure::nonempty_rows_missing;
 if(out.count){
  const auto data=reinterpret_cast<std::uintptr_t>(out.data);
  if(data%alignof(void*)!=0)return SelectedRowHeaderFailure::rows_misaligned;
  if(static_cast<std::size_t>(out.count)>(maximum-data)/stride)
   return SelectedRowHeaderFailure::row_span_overflow;
 }
 // Allocation reserve is not a row count. No consumer reads capacity rows.
 return SelectedRowHeaderFailure::none;
}
inline const char*SelectedRowHeaderFailureKey(SelectedRowArray kind,SelectedRowHeaderFailure failure) noexcept {
 const bool tenets=kind==SelectedRowArray::tenets;
 switch(failure){
  case SelectedRowHeaderFailure::none:return "";
  case SelectedRowHeaderFailure::unreadable:return tenets?"rite_creation_selected_tenet_header_unreadable":"rite_creation_selected_doctrine_header_unreadable";
  case SelectedRowHeaderFailure::header_misaligned:return tenets?"rite_creation_selected_tenet_header_misaligned":"rite_creation_selected_doctrine_header_misaligned";
  case SelectedRowHeaderFailure::negative_count:return tenets?"rite_creation_selected_tenet_count_negative":"rite_creation_selected_doctrine_count_negative";
  case SelectedRowHeaderFailure::capacity_below_count:return tenets?"rite_creation_selected_tenet_capacity_below_count":"rite_creation_selected_doctrine_capacity_below_count";
  case SelectedRowHeaderFailure::count_above_bound:return tenets?"rite_creation_selected_tenet_count_above_bound":"rite_creation_selected_doctrine_count_above_bound";
  case SelectedRowHeaderFailure::nonempty_rows_missing:return tenets?"rite_creation_selected_tenet_rows_missing":"rite_creation_selected_doctrine_rows_missing";
  case SelectedRowHeaderFailure::rows_misaligned:return tenets?"rite_creation_selected_tenet_rows_misaligned":"rite_creation_selected_doctrine_rows_misaligned";
  case SelectedRowHeaderFailure::row_span_overflow:return tenets?"rite_creation_selected_tenet_row_span_overflow":"rite_creation_selected_doctrine_row_span_overflow";
 }
 return "rite_creation_selected_row_header_failure_unknown";
}
inline bool ReadSelectedRowHeaders(const Bindings&b,const void*window,SelectedRowHeaders&out,const char*&why) noexcept {
 out={};why=nullptr;
 for(const auto kind:{SelectedRowArray::tenets,SelectedRowArray::doctrines}){
  auto&header=kind==SelectedRowArray::tenets?out.tenets:out.doctrines;
  const auto failure=ReadSelectedRowHeader(b,window,kind,header);
  if(failure!=SelectedRowHeaderFailure::none){why=SelectedRowHeaderFailureKey(kind,failure);return false;}
 }
 return true;
}
// Presence is independent of complete command-preview/model availability.
// Only a verified absent/hidden draft may enter the original Open callback.
template<class ReadPresence,class ReadExisting,class OpenAbsent>
bool GuardOpenDraft(const Request&r,Result&out,ReadPresence&&presence,
                    ReadExisting&&read_existing,OpenAbsent&&open_absent) {
 auto fail=[&](const char*why){out.available=false;out.status="unavailable";out.unavailable_reason=why;return false;};
 bool visible=false;
 if(!presence(visible))return fail("rite_creation_current_draft_presence_unverified_do_not_reinitialize");
 if(!visible)return open_absent();
 Result existing{};
 if(!read_existing(existing)||!existing.available)return fail("rite_creation_existing_visible_draft_unreadable_do_not_reinitialize");
 const bool edit_requested=r.operation==Operation::open_edit_current_rite_draft;
 if(!existing.draft.actual_outcome_kind||
    ((*existing.draft.actual_outcome_kind==Outcome::edit_rite)!=edit_requested)||
    (r.expected_outcome_kind&&r.expected_outcome_kind!=existing.draft.actual_outcome_kind))
  return fail("rite_creation_existing_native_draft_mode_differs_do_not_reinitialize");
 out=std::move(existing);out.available=true;out.unavailable_reason.clear();out.already_in_requested_state=true;
 out.draft_open_postcondition_observed=true;out.status="already_in_requested_state";return true;
}
inline void MarkCaptureException(Result&out) {
 out.available=false;out.status="unavailable";out.unavailable_reason="rite_creation_capture_exception";
}
inline void MarkActionException(const Request&r,Result&out) {
 out.available=false;out.verification_pending=out.native_dispatch_attempted;
 out.status=out.native_dispatch_attempted?"dispatch_result_unknown":"unavailable";
 out.original_writer_may_have_been_queued=r.operation==Operation::confirm_once&&out.native_dispatch_attempted;
 out.unavailable_reason="rite_creation_action_exception_do_not_retry_if_attempted";
}
} // namespace xar::ck3_12004::religion::rite_creation_actions::detail
