#include "../src/rite_creation_actions12004_guards.hpp"
#include "xar_bridge/rite_creation_actions12004_wire.hpp"
#include <cstdio>
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
  std::puts("12 new production open/exception guard cases passed; synthetic callbacks; no live/native game calls");return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"FAIL %s\n",e.what());return 1;}
}
