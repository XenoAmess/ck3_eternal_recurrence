#include "../src/rite_creation_actions12004_guards.hpp"
#include "xar_bridge/rite_creation_actions12004_wire.hpp"
#include <array>
#include <cstring>
#include <cstdio>
#include <limits>
#include <stdexcept>
using namespace xar::ck3_12004::religion::rite_creation_actions;
namespace {
void Require(bool v,const char*why){if(!v)throw std::runtime_error(why);}
Result Base(Operation op=Operation::open_create_draft){
 Result v{};v.operation=op;v.frame={1,7,9,123,456};v.available=true;
 v.unavailable_reason.clear();v.status="observed";return v;
}
void Encodes(const Result&v){
 const auto wire=SerializeCommandResult12004(v,"guard-fixture");
 Require(!wire.empty(),"original formatter preserves negative guard metadata");
}
struct WindowBytes {
 // Ends after the proven16-byte doctrine prefix. No unconsumed allocator
 // bytes are supplied to the production reader by this owned fixture.
 alignas(void*) std::array<unsigned char,0x7A0>bytes{};
 std::size_t readable=bytes.size();
 static bool Read(void*context,const void*from,void*to,std::size_t count){
  const auto&self=*static_cast<WindowBytes*>(context);
  const auto first=reinterpret_cast<std::uintptr_t>(self.bytes.data());
  const auto address=reinterpret_cast<std::uintptr_t>(from);
  if(address<first||address-first>self.readable||count>self.readable-(address-first))return false;
  std::memcpy(to,from,count);return true;
 }
 void Header(std::size_t offset,const void*data,std::int32_t capacity,std::int32_t count){
  std::memcpy(bytes.data()+offset,&data,sizeof(data));
  std::memcpy(bytes.data()+offset+8,&capacity,sizeof(capacity));
  std::memcpy(bytes.data()+offset+0xC,&count,sizeof(count));
 }
};
int SelectedRowHeaderCases(){
 WindowBytes window{};Bindings bindings{};bindings.read_memory=WindowBytes::Read;bindings.read_context=&window;
 detail::SelectedRowHeaders rows{};const char*why=nullptr;int cases=0;
 const auto reset=[&]{window.readable=window.bytes.size();
  window.Header(0x778,window.bytes.data(),256,3);window.Header(0x790,window.bytes.data(),512,31);};
 const auto read=[&]{return detail::ReadSelectedRowHeaders(bindings,window.bytes.data(),rows,why);};
 const auto rejects=[&](const char*expected){Require(!read()&&why&&std::string_view(why)==expected,
  "production selected-row reader rejects the precise array predicate");++cases;};
 reset();Require(read()&&!why&&rows.tenets.count==3&&rows.tenets.capacity==256&&
  rows.doctrines.count==31&&rows.doctrines.capacity==512,"bounded row counts accept legitimate larger allocation reserve");++cases;
 reset();window.Header(0x790,window.bytes.data(),512,64);
 Require(read()&&rows.doctrines.count==64,"existing SDK doctrine row bound is retained");++cases;
 reset();window.Header(0x778,window.bytes.data(),128,65);rejects("rite_creation_selected_tenet_count_above_bound");
 reset();window.Header(0x790,window.bytes.data(),128,65);rejects("rite_creation_selected_doctrine_count_above_bound");
 reset();window.Header(0x790,window.bytes.data(),30,31);rejects("rite_creation_selected_doctrine_capacity_below_count");
 reset();window.Header(0x778,window.bytes.data(),256,-1);rejects("rite_creation_selected_tenet_count_negative");
 reset();window.Header(0x790,nullptr,512,31);rejects("rite_creation_selected_doctrine_rows_missing");
 reset();window.Header(0x778,nullptr,256,0);window.Header(0x790,nullptr,512,0);
 Require(read()&&rows.tenets.count==0&&rows.doctrines.count==0,"empty rows are values independent of allocation reserve");++cases;
 reset();window.readable=0x778+15;rejects("rite_creation_selected_tenet_header_unreadable");
 reset();window.readable=0x790+15;rejects("rite_creation_selected_doctrine_header_unreadable");
 reset();window.Header(0x790,nullptr,-1,0);rejects("rite_creation_selected_doctrine_capacity_below_count");
 reset();window.Header(0x778,window.bytes.data(),std::numeric_limits<std::int32_t>::max(),3);
 Require(read()&&rows.tenets.count==3,"only bounded count is consumed even when reserve is large");++cases;
 reset();window.Header(0x790,window.bytes.data()+1,512,31);rejects("rite_creation_selected_doctrine_rows_misaligned");
 reset();window.Header(0x778,reinterpret_cast<const void*>(std::numeric_limits<std::uintptr_t>::max()-7),256,3);
 rejects("rite_creation_selected_tenet_row_span_overflow");
 reset();Require(!detail::ReadSelectedRowHeaders(bindings,window.bytes.data()+1,rows,why)&&
  std::string_view(why)=="rite_creation_selected_tenet_header_misaligned","misaligned window header is rejected");++cases;
 reset();Require(!detail::ReadSelectedRowHeaders(bindings,
  reinterpret_cast<const void*>(std::numeric_limits<std::uintptr_t>::max()-0x777),rows,why)&&
  std::string_view(why)=="rite_creation_selected_tenet_header_unreadable","header address overflow is rejected before read callback");++cases;
 return cases;
}
}
int main(){
 try{
  Request q{};q.operation=Operation::open_create_draft;q.expected_source_rite_id=13;
  int opens=0,reads=0;auto open=[&](){++opens;return true;};
  auto existing=[&](Result&v){++reads;v=Base();v.draft.actual_outcome_kind=Outcome::create_faith;return true;};
  auto v=Base();
  Require(!detail::GuardOpenDraft(q,v,[](bool&){return false;},existing,open)&&!opens&&!reads&&!v.available,
          "unknown independent presence never calls original Open or full reader");Encodes(v);
  v=Base();
  Require(!detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},
          [&](Result&partial){++reads;partial=Base();return false;},open)&&!opens&&!v.available,
          "visible draft plus full-read failure cannot fall through to Open");Encodes(v);
  v=Base();
  Require(!detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},
          [&](Result&partial){++reads;partial=Base();partial.available=false;partial.unavailable_reason="preview unavailable";return true;},open)&&!opens&&!v.available,
          "visible draft with bool-success but unavailable complete read stays unavailable");Encodes(v);
  q.expected_outcome_kind=Outcome::create_rite;v=Base();
  Require(!detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},existing,open)&&!opens,
          "existing actual Faith versus expected Rite never reinitializes");
  q.expected_outcome_kind.reset();q.operation=Operation::open_edit_current_rite_draft;v=Base(q.operation);
  Require(!detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},existing,open)&&!opens,
          "existing create draft cannot be reopened as Edit");
  q.operation=Operation::open_create_draft;v=Base();
  Require(detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},existing,open)&&!opens&&
          v.already_in_requested_state&&v.draft_open_postcondition_observed,
          "verified matching existing draft is idempotent");
  const auto reads_before=reads;v=Base();
  Require(detail::GuardOpenDraft(q,v,[](bool&shown){shown=false;return true;},existing,open)&&
          opens==1&&reads==reads_before,"only verified absence calls original Open exactly once");
  v=Base(Operation::preview);detail::MarkCaptureException(v);
  Require(!v.available&&v.status=="unavailable"&&!v.native_dispatch_attempted,
          "capture exception after available result remains unavailable");Encodes(v);
  q.operation=Operation::confirm_once;q.action_id="guard-fixture";v=Base(q.operation);v.action_id=q.action_id;
  detail::MarkActionException(q,v);
  Require(!v.available&&!v.verification_pending&&!v.original_writer_may_have_been_queued,
          "predispatch exception preserves known no-dispatch");Encodes(v);
  v=Base(q.operation);v.action_id=q.action_id;v.native_dispatch_attempted=true;v.dispatch_invoked=true;v.native_once_claimed=true;
  detail::MarkActionException(q,v);
  Require(!v.available&&v.native_dispatch_attempted&&v.dispatch_invoked&&v.native_once_claimed&&
          v.verification_pending&&v.original_writer_may_have_been_queued&&v.status=="dispatch_result_unknown",
          "post-confirm exception retains attempted once claim and possible writer");Encodes(v);
  q.operation=Operation::set_name_field;v=Base(q.operation);v.native_dispatch_attempted=true;
  detail::MarkActionException(q,v);
  Require(!v.available&&v.verification_pending&&!v.original_writer_may_have_been_queued&&!v.dispatch_invoked,
          "draft exception retains attempted state without claiming gameplay queue");Encodes(v);
  q.operation=Operation::open_create_draft;v=Base();const auto before_throw=opens;
  try {detail::GuardOpenDraft(q,v,[](bool&shown){shown=true;return true;},
       [](Result&)->bool{throw std::runtime_error("injected full-reader exception");},open);}
  catch(...){detail::MarkActionException(q,v);}
  Require(opens==before_throw&&!v.available&&!v.native_dispatch_attempted,
          "injected existing reader exception remains no-Open and serializable");Encodes(v);
  const auto selected_cases=SelectedRowHeaderCases();
  std::printf("12 production open/exception guard cases and %d selected-row header cases passed; synthetic memory/callbacks; no live/native game calls\n",selected_cases);return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"FAIL %s\n",e.what());return 1;}
}
