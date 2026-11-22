#if defined(XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1) && !XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
#error Enabled test requires text feature ON.
#endif
#ifndef XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1
#define XAR_CK3_ENABLE_121003_26785313_RITE_TEXT_V1 1
#endif
#include "rite_text_owner_nogame_fixture.hpp"
namespace {
using namespace text_owner_fixture;
void SeparateNameDescriptionWritesAndIndependentReadback(){
  state.Reset();Session s;auto m=Mail();auto q=Query(s,m.get());auto name=Write(s,m.get(),A::set_name,q,"New name");
  Require(name.result.source->name=="Old name"&&state.name=="New name"&&state.calls==1,"setter returned after-data instead of beforeSource");
  auto afterName=Query(s,m.get());Require(afterName.result.source->name=="New name"&&afterName.result.query_sequence>q.result.query_sequence,"fresh actual query missed new name");
  auto desc=Write(s,m.get(),A::set_description,afterName,"line\n\tnew description");
  Require(desc.result.source->description=="Old description"&&desc.result.source->name=="New name","description beforeSource rebound");
  auto after=Query(s,m.get());Require(after.result.source->name=="New name"&&after.result.source->description=="line\n\tnew description"&&state.calls==2&&state.entered_calls==2,"independent final DATA readback failed");
  Wire(name);Wire(desc);const auto observations=state.observations;const auto claim=name.result.claim_sequence;Run(name);Run(desc);
  Require(name.result.status==S::claim_consumed&&name.result.claim_sequence==claim&&desc.result.status==S::claim_consumed&&state.calls==2&&state.observations==observations,"original setter replayed");
}
void CrossCustodyCoreRiteDeadlineAndNewSessionFail(){
  state.Reset();Session s,foreign;auto m=Mail();auto q=Query(s,m.get());
  for(unsigned x=0;x<7;++x){auto write=FromQuery(s,m.get(),A::set_name,q,"new");if(x==0)++write.connection_generation;if(x==1)++write.request.expected_source_rite_id;if(x==2)write.request.expected.clock.date_raw+=24;if(x==3)++write.request.deadline_unix_ms;if(x==4)--write.request.deadline_unix_ms;if(x==5)++write.request.provider_generation;if(x==6)++write.request.query_sequence;
    auto n=state.observations;Run(write);Require(write.result.status==S::stale_source&&!write.result.claim_sequence&&state.observations==n&&!state.calls,"cross-custody request reached Raw/effect");NoSource(write);}
  auto stolen=FromQuery(foreign,m.get(),A::set_name,q,"new");auto n=state.observations;Run(stolen);Require(stolen.result.status==S::stale_source&&state.observations==n&&!state.calls,"new receiver borrowed private text lease");
}
void EmptyClearIsLegalAndNoAppliedClaim(){
  state.Reset();Session s;auto m=Mail();auto q=Query(s,m.get());auto name=Write(s,m.get(),A::set_name,q,"");auto next=Query(s,m.get());Require(next.result.source->name.empty(),"actual empty name clear rejected/filled");
  auto desc=Write(s,m.get(),A::set_description,next,"");auto final=Query(s,m.get());Require(final.result.source->description.empty()&&final.result.source->name.empty(),"empty description clear changed");Wire(name);Wire(desc);
}
void ReadNulRichtextAnd4096AreDataOnly(){
  state.Reset();state.name=std::string("a\0b\x15",4);state.description="line\n\t";Session s;auto m=Mail();auto q=Query(s,m.get());
  Require(q.result.source->name==state.name&&q.result.source->description==state.description,"Source controls/NUL stripped or normalized");Wire(q);
  auto invalid=FromQuery(s,m.get(),A::set_name,q,std::string("a\0b",3));auto n=state.observations;Run(invalid);Require(invalid.result.status==S::unavailable&&state.observations==n&&!state.calls,"read-side NUL was used as write permission");
  state.name=std::string(4096,'x');auto longRead=Query(s,m.get());Require(longRead.result.source->name.size()==4096,"read bound wrongly reused write limit");
}
void CreatingFalseOrBlockedNeverWrites(){
  for(unsigned x=0;x<3;++x){state.Reset();state.admissible=false;if(x==0)state.creating=false;if(x==1)state.enabled=false;if(x==2)state.blocked=true;Session s;auto m=Mail();auto q=Query(s,m.get());auto w=FromQuery(s,m.get(),A::set_name,q,"new");Run(w);Require(w.result.status==S::prerequisite_rejected&&!w.result.claim_sequence&&!state.calls,"false actual gate dispatched setter");NoSource(w);}
}
void SamePriceChangedTextOrFullDraftIsStaleBeforeClaim(){
  for(unsigned x=0;x<5;++x){state.Reset();Session s;auto m=Mail();auto q=Query(s,m.get());if(x==0)state.name="Different name";if(x==1)state.description="Different description";if(x>=2)state.raw_mutation=x-1;
    auto w=FromQuery(s,m.get(),A::set_name,q,"new");Run(w);Require(w.result.status==S::stale_source&&!w.result.claim_sequence&&!state.calls,"same-price changed text/header/full draft acquired setter");NoSource(w);}
}
void PreclaimStaleKeepsKnownLeaseButSpentCalleeRefusalDoesNot(){
  state.Reset();Session s;auto m=Mail();auto q=Query(s,m.get());state.raw_mutation=2;auto stale=FromQuery(s,m.get(),A::set_name,q,"new");Run(stale);Require(stale.result.status==S::stale_source&&!stale.result.claim_sequence&&!state.calls,"preclaim stale spent claim");
  state.raw_mutation=0;state.call_status=RiteTextCallStatus267V1::unavailable;state.call_entered=false;auto refused=FromQuery(s,m.get(),A::set_name,q,"new");Run(refused);
  Require(refused.result.status==S::stale_source&&refused.result.claim_sequence==1&&!refused.result.effect_attempted&&!refused.result.native_returned&&state.calls==1&&!state.entered_calls,"callee preentry refusal lost spent claim/0effect");
  auto n=state.observations;Run(refused);Require(refused.result.status==S::claim_consumed&&refused.result.claim_sequence==1&&state.observations==n&&state.calls==1,"spent ID replayed");
  auto another=FromQuery(s,m.get(),A::set_description,q,"other");Run(another);Require(another.result.status==S::claim_consumed&&state.calls==1,"new ID bypassed spent query");
}
void UnknownObservationAndCompletionStaySticky(){
  for(bool observation:{false,true}){state.Reset();Session s;auto m=Mail();Context failed{};
    if(observation){state.raw_cleanup=false;failed=Request(s,m.get(),A::query);Run(failed);}else{auto q=Query(s,m.get());state.call_status=RiteTextCallStatus267V1::indeterminate;state.call_cleanup=false;failed=FromQuery(s,m.get(),A::set_name,q,"new");Run(failed);Require(failed.result.claim_sequence==1&&failed.result.effect_attempted&&!failed.result.native_returned,"unknown effect lost actual entry/claim");}
    Require(failed.result.status==S::indeterminate&&!failed.result.cleanup_known,"unknown cleanup became known");NoSource(failed);auto n=state.observations,calls=state.calls,bind=state.bindings;state.raw_cleanup=true;auto next=Request(s,m.get(),A::query);Run(next);Require(next.result.status==S::indeterminate&&!next.result.cleanup_known&&state.observations==n&&state.calls==calls&&state.bindings==bind,"unknown session resampled or retried");}
}
void ReturnedVoidMayLeaveTextUnchanged(){
  state.Reset();state.apply=false;Session s;auto m=Mail();auto q=Query(s,m.get());auto write=Write(s,m.get(),A::set_description,q,"wanted");auto after=Query(s,m.get());Require(after.result.source->description=="Old description"&&after.result.source->description!=write.request.text,"void return fabricated applied text");Wire(write);
}
void OriginalExpiryAndPostReadWorldDriftNeverCalls(){
  state.Reset();Session s;auto m=Mail();auto q=Query(s,m.get());auto expired=FromQuery(s,m.get(),A::set_name,q,"new");expired.monotonic_deadline_ms=0;auto n=state.observations;Run(expired);Require(expired.result.status==S::expired&&state.observations==n&&!state.calls,"expired request reached Raw");
  for(bool world:{false,true}){state.core_drift=!world;state.world_drift=world;auto w=FromQuery(s,m.get(),A::set_name,q,"new");Run(w);Require(w.result.status!=S::text_dispatched&&!w.result.claim_sequence&&!state.calls,"post-read world/Core drift entered setter");NoSource(w);}
}
void ActorZeroNegativeAndRiteZeroPreserved(){
  for(std::int32_t actor:{0,-2}){state.Reset();state.core=CoreFor(actor);state.rite=0;Session s;auto m=Mail();auto q=Query(s,m.get());auto w=Write(s,m.get(),A::set_name,q,"new");auto after=Query(s,m.get());Require(w.result.source->actor_id==actor&&after.result.source->actor_id==actor&&after.result.source->source_rite_id==0,"packed actor/Rite0 lost");}
}
void FixedSlot29AndMissingRawFailClosed(){
  for(unsigned x=0;x<5;++x){state.Reset();Session s;auto m=Mail();auto q=Request(s,m.get(),A::query);if(x==0)m->offline_fixture=true;if(x==1)m->permitted_executor_novemvigintary=nullptr;if(x==2){m->permitted_executor_novemvigintary=nullptr;m->permitted_executor_octovigintary=&ExecuteRiteTextOnOwner267V1;}if(x==3)q.connection_generation=0;if(x==4)q.mailbox=nullptr;Run(q);Require(q.result.status==S::unavailable&&!state.bindings&&!state.observations&&!state.calls,"invalid owner/slot29 reached observation");NoSource(q);}
  state.Reset();state.raw_missing=true;Session s;auto m=Mail();auto q=Request(s,m.get(),A::query);Run(q);Require(q.result.status==S::unavailable&&!state.calls,"missing source fabricated empty DATA");NoSource(q);Require(!ExecuteRiteTextOnOwner267V1(nullptr,StampNow()),"null context accepted");
}
}
int main(){try{unsigned n=0;auto test=[&](const char*name,auto body){body();++n;std::cout<<"PASS "<<name<<'\n';};
  test("once_name_fresh_query_description_readback",SeparateNameDescriptionWritesAndIndependentReadback);test("private_custody_source_original_deadline",CrossCustodyCoreRiteDeadlineAndNewSessionFail);
  test("empty_clear_no_applied_credit",EmptyClearIsLegalAndNoAppliedClaim);test("source_nul_controls_4096_only_data",ReadNulRichtextAnd4096AreDataOnly);
  test("creating_false_or_blocked_no_write",CreatingFalseOrBlockedNeverWrites);test("same_price_full_draft_changed",SamePriceChangedTextOrFullDraftIsStaleBeforeClaim);
  test("preclaim_vs_spent_zero_effect",PreclaimStaleKeepsKnownLeaseButSpentCalleeRefusalDoesNot);test("unknown_sticky_no_new_read",UnknownObservationAndCompletionStaySticky);
  test("void_return_not_applied",ReturnedVoidMayLeaveTextUnchanged);test("expiry_world_core_drift",OriginalExpiryAndPostReadWorldDriftNeverCalls);
  test("packed_zero_negative_rite_zero",ActorZeroNegativeAndRiteZeroPreserved);test("fixed_slot29_missing_source",FixedSlot29AndMissingRawFailClosed);
  std::cout<<"NoGame owner/session groups="<<n<<"; Native ABI/runtime qualification=false\n";return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
