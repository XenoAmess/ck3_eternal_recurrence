#include "xar_bridge/ck3_12004_county_predicate_trace_context.hpp"
#include <array>
#include <stdexcept>

// Authored offline fixture; not a native-game observation. This target has not
// been built or executed by the a22 source-only task.
namespace {
using namespace xar::ck3_12004;
std::array<bool,4> answers{};
std::size_t calls=0;
bool recurse=false;
std::uintptr_t observed_r8=0,observed_r9=0;
void *const actor=reinterpret_cast<void*>(0x1000);
void *const source=reinterpret_cast<void*>(0x2000);
void *const target=reinterpret_cast<void*>(0x3000);
void Check(bool ok) {if(!ok)throw std::runtime_error("county P trace fixture failed");}
#if defined(_MSC_VER)
bool __fastcall Original(void *a,void *c,std::uintptr_t r8,std::uintptr_t r9) {
#else
bool Original(void *a,void *c,std::uintptr_t r8,std::uintptr_t r9) {
#endif
  const auto index=calls++;
  observed_r8=r8;observed_r9=r9;
  if(recurse){recurse=false;
    (void)InvokeCountyPredicateTrace12004(&Original,a,c,0x24E22B3,7,r8,r9);}
  return answers[index];
}
void Reset(std::array<bool,4> values){answers=values;calls=0;recurse=false;}
void SourceFalse(){
 Reset({false,false,false,false});
 CountyPredicateTraceScope12004 scope(true,1,7,actor,source,target);
 Check(!InvokeCountyPredicateTrace12004(&Original,actor,source,0x24E22B3,7,0x4444,0x5555));
 const auto result=scope.Finish(true,false,true,7,true,true,true);
 Check(calls==1 && result.available && result.stages[0].returned==false &&
       result.stages[1].call_count==0 && result.stages[2].call_count==0 &&
       observed_r8==0x4444 && observed_r9==0x5555);
}
void TwoSeparateTargetCalls(){
 Reset({true,true,false,false});
 CountyPredicateTraceScope12004 scope(true,1,7,actor,source,target);
 Check(InvokeCountyPredicateTrace12004(&Original,actor,source,0x24E22B3,7));
 Check(InvokeCountyPredicateTrace12004(&Original,actor,target,0x24E22F1,7));
 Check(!InvokeCountyPredicateTrace12004(&Original,actor,target,0x24E2348,7));
 const auto result=scope.Finish(true,false,true,7,true,true,true);
 Check(calls==3 && result.available && result.stages[1].returned==true &&
       result.stages[2].returned==false);
}
void PTrueDoesNotObserveQ(){
 Reset({true,true,true,false});
 CountyPredicateTraceScope12004 scope(true,1,7,actor,source,target);
 (void)InvokeCountyPredicateTrace12004(&Original,actor,source,0x24E22B3,7);
 (void)InvokeCountyPredicateTrace12004(&Original,actor,target,0x24E22F1,7);
 (void)InvokeCountyPredicateTrace12004(&Original,actor,target,0x24E2348,7);
 const auto result=scope.Finish(true,false,true,7,true,true,true);
 Check(calls==3 && result.available && result.final_condition_passes==false);
 for(const auto &stage:result.stages)Check(stage.returned==true);
}
void NestedAndIdentityFence(){
 Reset({false,true,false,false});
 Check(g_county_predicate_trace12004==nullptr);
 {
  CountyPredicateTraceScope12004 scope(true,1,7,actor,source,target);
  auto *const outer=g_county_predicate_trace12004;
  {CountyPredicateTraceScope12004 masked(true,0,7,actor,source,target);
   Check(g_county_predicate_trace12004!=outer);}
  Check(g_county_predicate_trace12004==outer);
  recurse=true;
  Check(!InvokeCountyPredicateTrace12004(&Original,actor,source,0x24E22B3,7));
  const auto valid=scope.Finish(true,false,true,7,true,true,true);
  Check(calls==2 && valid.available && valid.stages[0].call_count==1 && valid.ignored_nested_calls==1);
  Check(!scope.Finish(true,false,true,8,true,true,true).available);
 }
 Check(g_county_predicate_trace12004==nullptr);
 Reset({false,false,false,false});
 {CountyPredicateTraceScope12004 scope(true,1,7,actor,source,target);
  (void)InvokeCountyPredicateTrace12004(&Original,actor,target,0x24E22B3,7);
  Check(calls==1 && !scope.Finish(true,false,true,7,true,true,true).available);}
}
}
int main(){
 try{SourceFalse();TwoSeparateTargetCalls();PTrueDoesNotObserveQ();NestedAndIdentityFence();return 0;}
 catch(...){return 1;}
}
