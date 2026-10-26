#pragma once
#include "xar_bridge/rite_creation_actions12004.hpp"
#include <limits>
#include <unordered_set>
#include <utility>

namespace xar::ck3_12004::religion::rite_creation_actions::detail {
// Same pointer/capacity/count prefix consumed by the qualified draft-group
// reader. The two window arrays are 0x18 apart; their unused trailing bytes
// are not an additional prerequisite for reading the selected rows.
struct SelectedRowArrayHeader {
 const void*data=nullptr;
 std::int32_t capacity=0,count=0;
 bool operator==(const SelectedRowArrayHeader&)const=default;
};
static_assert(sizeof(SelectedRowArrayHeader)==16);
static_assert(offsetof(SelectedRowArrayHeader,capacity)==8);
static_assert(offsetof(SelectedRowArrayHeader,count)==0xC);
enum class SelectedRowArray {tenets,doctrines};
enum class SelectedRowHeaderFailure {none,unreadable,header_misaligned,negative_count,
 capacity_below_count,count_above_bound,nonempty_rows_missing,rows_misaligned,row_span_overflow};
struct SelectedRowHeaders {
 SelectedRowArrayHeader tenets{},doctrines{};
 bool operator==(const SelectedRowHeaders&)const=default;
};
inline SelectedRowHeaderFailure ReadBoundedArrayPrefix(const Bindings&b,const void*window,
 std::size_t offset,std::size_t stride,std::int32_t count_limit,SelectedRowArrayHeader&out) noexcept {
 out={};
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
inline SelectedRowHeaderFailure ReadSelectedRowHeader(
 const Bindings&b,const void*window,SelectedRowArray kind,SelectedRowArrayHeader&out) noexcept {
 // Tenets are physical editor slots, including exact native-default blanks.
 return ReadBoundedArrayPrefix(b,window,kind==SelectedRowArray::tenets?0x778:0x790,
     kind==SelectedRowArray::tenets?0x70:0x48,kind==SelectedRowArray::tenets?100:64,out);
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
inline bool SelectedRowHeadersUnchanged(const Bindings&b,const void*window,
 const SelectedRowHeaders&expected,const char*&why) noexcept {
 SelectedRowHeaders observed{};
 if(!ReadSelectedRowHeaders(b,window,observed,why))return false;
 if(observed!=expected){why="rite_creation_owned_draft_collections_changed";return false;}
 return true;
}
template<class DefinitionReader>
bool ReadSelectedTenetSlots(const Bindings&b,const SelectedRowArrayHeader&header,
    const void*native_default,DefinitionReader&&definition,
    std::vector<TenetSelection>&valid,std::vector<const void*>&raw,
    std::vector<std::string>&raw_keys,const char*&why) {
 valid.clear();raw.clear();raw_keys.clear();why=nullptr;
 const auto address=reinterpret_cast<std::uintptr_t>(header.data);
 if(header.count<0||header.count>100||header.capacity<header.count||
    (header.count&&(!address||!b.read_memory||address%alignof(void*)||
      static_cast<std::size_t>(header.count)>(std::numeric_limits<std::uintptr_t>::max()-address)/0x70))){
  why="rite_creation_selected_tenet_header_unverified";return false;}
 if(!native_default){why="rite_creation_native_default_tenet_unavailable";return false;}
 for(std::int32_t i=0;i<header.count;++i){
  const auto row=reinterpret_cast<std::uintptr_t>(header.data)+static_cast<std::size_t>(i)*0x70;
  std::uint32_t slot=absent;const void*item=nullptr;
  if(!b.read_memory(b.read_context,reinterpret_cast<const void*>(row+0x20),&slot,sizeof(slot))||
     !b.read_memory(b.read_context,reinterpret_cast<const void*>(row+0x28),&item,sizeof(item))){
   why="rite_creation_selected_tenet_row_unreadable";return false;}
  if(slot!=static_cast<std::uint32_t>(i)){why="rite_creation_selected_tenet_physical_slot_mismatch";return false;}
  // Only the exact previously qualified native-default object is a blank
  // slot. A null or unknown definition is unavailable, never silently empty.
  std::string key;
  if(item!=native_default){
   if(!item||!definition(item,key)){why="rite_creation_selected_tenet_definition_unavailable";return false;}
   for(const auto&prior:valid)if(prior.tenet_key==key){why="rite_creation_selected_tenet_duplicate";return false;}
   valid.push_back({slot,key});
  }
  raw.push_back(item);raw_keys.push_back(std::move(key));
 }
 return true;
}
inline const TenetSelection*SelectedTenetAt(const std::vector<TenetSelection>&rows,std::uint32_t slot) noexcept {
 for(const auto&row:rows)if(row.slot_index==slot)return &row;
 return nullptr;
}
template<class TraitReader>
bool ReadVirtueSinCatalogueRows(const Bindings&b,const void*window,std::size_t virtues_offset,
    std::size_t sins_offset,VirtueSinScope scope,std::uint32_t rite,const void*draft_core,
    TraitReader&&trait,VirtueSinCatalogue&out) {
 out={};out.scope=scope;if(rite!=absent)out.rite_id=rite;
 const auto fail=[&](const char*reason){out.observed=false;out.unavailable_reason=reason;
  out.virtues.clear();out.sins.clear();out.description_rite_ids.clear();out.description_draft_cores.clear();return false;};
 if(rite==absent||!window||(scope!=VirtueSinScope::draft&&scope!=VirtueSinScope::current_rite))
  return fail("rite_virtue_sin_actual_model_identity_unavailable");
 std::array<SelectedRowArrayHeader,2>headers{};
 for(std::size_t kind=0;kind<2;++kind)
  if(ReadBoundedArrayPrefix(b,window,kind?sins_offset:virtues_offset,0x28,8192,headers[kind])!=SelectedRowHeaderFailure::none)
   return fail("rite_virtue_sin_native_collection_unavailable");
 if(headers[0].count>8192-headers[1].count)return fail("rite_virtue_sin_combined_count_above_bound");
 std::unordered_set<std::uint32_t>ids;std::unordered_set<std::string>keys;
 for(std::size_t kind=0;kind<2;++kind){
  auto&destination=kind?out.sins:out.virtues;
  for(std::int32_t index=0;index<headers[kind].count;++index){
   const auto row=reinterpret_cast<std::uintptr_t>(headers[kind].data)+static_cast<std::size_t>(index)*0x28;
   const auto read=[&](std::size_t offset,void*value,std::size_t bytes){return b.read_memory(b.read_context,reinterpret_cast<const void*>(row+offset),value,bytes);};
   VirtueSinRow value{};const void*definition=nullptr,*core=nullptr;std::uint32_t source=absent;
   if(!read(0,&value.classification,sizeof(value.classification))||!read(8,&definition,sizeof(definition))||
      !read(0x10,&source,sizeof(source))||!read(0x18,&value.weight_raw,sizeof(value.weight_raw))||
      !read(0x20,&core,sizeof(core)))return fail("rite_virtue_sin_native_row_unreadable");
   if(value.classification!=(kind?2:1)||!definition||!trait(definition,value.trait_id,value.trait_key))
    return fail("rite_virtue_sin_native_classification_or_trait_unavailable");
   // The row's description source is not the list's observation scope. Keep
   // both original branches private; no reconstructed tooltip is published.
   if(source==absent){if(scope!=VirtueSinScope::draft||!draft_core||core!=draft_core)
     return fail("rite_virtue_sin_draft_core_reference_unbound");}
   else if(source!=rite||core)return fail("rite_virtue_sin_persistent_reference_unbound");
   if(!ids.insert(value.trait_id).second||!keys.insert(value.trait_key).second)
    return fail("rite_virtue_sin_native_trait_duplicate");
   destination.push_back(std::move(value));out.description_rite_ids.push_back(source);out.description_draft_cores.push_back(core);
  }
 }
 for(std::size_t kind=0;kind<2;++kind){SelectedRowArrayHeader again{};
  if(ReadBoundedArrayPrefix(b,window,kind?sins_offset:virtues_offset,0x28,8192,again)!=SelectedRowHeaderFailure::none||again!=headers[kind])
   return fail("rite_virtue_sin_native_collection_changed");}
 out.observed=true;out.unavailable_reason.clear();return true;
}
inline bool Utf8Text(std::string_view s,std::size_t max_characters,bool multiline,
                     bool native_description_markup=false) noexcept {
 std::size_t i=0,count=0;
 while(i<s.size()){
  const auto c=static_cast<unsigned char>(s[i++]);std::uint32_t cp=c;unsigned continuation=0;
  if(c<0x80){}
  else if(c>=0xC2&&c<=0xDF){cp=c&31;continuation=1;}
  else if(c>=0xE0&&c<=0xEF){cp=c&15;continuation=2;}
  else if(c>=0xF0&&c<=0xF4){cp=c&7;continuation=3;}
  else return false;
  const unsigned length=continuation;
  if(continuation>s.size()-i)return false;
  while(continuation--){const auto d=static_cast<unsigned char>(s[i++]);if((d&0xC0)!=0x80)return false;cp=(cp<<6)|(d&63);}
  if((length==1&&cp<0x80)||(length==2&&cp<0x800)||(length==3&&cp<0x10000)||cp>0x10FFFF||
     (cp>=0xD800&&cp<=0xDFFF)||cp==0||cp==0x7F||
     (cp<32&&!(multiline&&(cp==10||cp==9))&&!(native_description_markup&&cp==0x15)))return false;
  if(++count>max_characters)return false;
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
