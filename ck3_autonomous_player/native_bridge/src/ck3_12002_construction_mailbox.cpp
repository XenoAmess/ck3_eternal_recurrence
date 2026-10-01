#include "ck3_12002_construction_mailbox.hpp"
#include "ck3_12002_construction.hpp"
#include "ck3_12002_construction_submit_binding.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include <windows.h>
#include <atomic>
#include <cstring>
namespace xar::ck3_12002 {
namespace {
using Stamp=ck3_11906::MainThreadExecutionStampV1;
using Completion=ck3_11906::PlayerConstructionViewProbeMailboxCompletionV1;
struct Proxy { ConstructionMailboxContextV1* owner; const Stamp* stamp; };
bool Owns(const ConstructionMailboxContextV1& owner,const Stamp& stamp) noexcept {
  const auto& q=owner.query;
  if(q.mailbox==nullptr||q.ticket.sequence==0||!owner.core.enabled||q.module_base==0||
      stamp.pump_epoch==0||stamp.thread_id!=GetCurrentThreadId()||!stamp.paused||
      stamp.tls_initialized_flag_address==0||stamp.tls_initialized!=1||
      stamp.tls_context==0||stamp.tls_main_thread_marker!=1||stamp.jomini_state==0||stamp.game_state==0) return false;
  const auto& m=*q.mailbox;
  return m.state.load(std::memory_order_acquire)==ck3_11906::MainThreadQueryMailboxStateV1::executing&&
      !m.stop_requested.load(std::memory_order_acquire)&&m.failure_flags.load(std::memory_order_acquire)==0&&
      m.published_sequence.load(std::memory_order_acquire)==q.ticket.sequence&&
      m.owner_thread_id.load(std::memory_order_acquire)==stamp.thread_id&&
      m.paused_owner_verified_pump_epochs.load(std::memory_order_acquire)>=ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs&&
      m.executor==&ExecuteConstructionMailboxV1&&m.executor_context==&owner;
}
bool Same(const ConstructionMailboxContextV1& owner,const Stamp& stamp) noexcept {
  CoreSnapshotPrefix now{};
  const auto& expected=owner.query.expected_snapshot;
  return ReadCoreSnapshot(owner.core,now)&&now.clock.paused&&now.map_ready&&now.has_played_character&&now.played_character_alive&&
      now.clock.date_raw==expected.date_raw&&now.clock.date_raw==stamp.date_raw&&
      now.played_character_id==expected.played_character_id&&expected.paused&&expected.map_ready&&
      expected.has_played_character&&expected.played_character_alive;
}
bool Main(void* opaque) noexcept {const auto* p=static_cast<Proxy*>(opaque);return p&&p->owner&&p->stamp&&Owns(*p->owner,*p->stamp);}
bool Capture(void* opaque,game::CampaignRootFrameV1& frame) noexcept {
  const auto* p=static_cast<Proxy*>(opaque);
  if(!p||!p->owner||!p->stamp||!Owns(*p->owner,*p->stamp)||!Same(*p->owner,*p->stamp)) return false;
  const auto& q=p->owner->query;const auto& s=q.expected_snapshot;
  frame={q.expected_revision,s.date_raw,s.paused,s.map_ready,s.has_played_character,s.played_character_alive,s.played_character_id};return true;
}
bool Memory(void* opaque,const void* address,void* output,std::size_t size) noexcept {
  if(!Main(opaque)||!address||!output||size==0) return false;
#if defined(_MSC_VER)
  __try {std::memcpy(output,address,size);return true;} __except(EXCEPTION_EXECUTE_HANDLER) {return false;}
#else
  std::memcpy(output,address,size);return true;
#endif
}
} // namespace
bool ExecuteConstructionMailboxV1(void* context,const Stamp& stamp) noexcept {
  auto* owner=static_cast<ConstructionMailboxContextV1*>(context);
  if(!owner) return false;
  auto& q=owner->query;
  if(!Owns(*owner,stamp)||q.completion!=Completion::not_executed||q.executor_invocations!=0) {
    q.completion=Completion::infrastructure_rejected;return false;
  }
  ++q.executor_invocations;q.execution_stamp=stamp;
  // No CHoldingView cache or old GUI owner ABI is read. World manager data is
  // independent of a selected/open GUI view; cache diagnostics remain unqueried.
  Proxy proxy{owner,&stamp};
  PlayerWorldBuildingSourceAccessV1 access{};
  access.campaign={&proxy,&Capture,&Main,&Memory,nullptr};
  PlayerWorldBuildingNativeCallAccessV1 native{q.module_base,true};
  access.final_legality=ck3_12002::BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(native);
  access.final_legality_context=&native;
  access.native_cost=ck3_12002::BindCurrentProcessPlayerWorldBuildingCostV1(native);
  access.native_cost_context=&native;
  q.player_world_building_source_executed=true;
  q.player_world_building_sources=ck3_12002::ReadPlayerWorldBuildingDefinitionSourcesV1(
      q.module_base,true,access,{q.expected_revision,-1,512,64});
  if(q.player_world_building_sources.source_available&&Same(*owner,stamp)) {
    if(q.request_private_action) {
      q.private_action_candidate=ck3_11906::SelectPlayerWorldBuildingActionCandidateV1(
          q.player_world_building_sources,stamp.pump_epoch,q.minimum_gold_reserve_raw);
      if(q.private_action_candidate.ready) {
        ConstructionActionRequestV1 request{};
        request.exact_build_admitted=true;request.session_live=true;request.module_base=q.module_base;
        request.source=&q.player_world_building_sources;request.candidate=&q.private_action_candidate;
        request.native_calls=ck3_12002::BindCurrentProcessDomainConstructionExactNativeCallsV1(q.module_base);
        (void)ck3_12002::SubmitPlayerWorldBuildingDirectActionV1(q.private_action_state,request,stamp);
      }
    }
  } else if(!Same(*owner,stamp)) {
    q.player_world_building_sources={};q.player_world_building_sources.failure=PlayerWorldBuildingFailureV1::frame_changed;
  }
  q.completion=Completion::completed;return true;
}
std::string SerializeConstructionMailboxV1(const ConstructionMailboxContextV1& context) {
  auto json=ck3_12002::RenderQueryBuildIdentity(
      ck3_11906::SerializePlayerConstructionViewProbePrivateV1(context.query));
  if(!json.empty()&&json.back()=='}') {json.pop_back();json+=",\"game_version\":\"1.20.0.2\",\"source_binding\":\"direct-world-building-manager\",\"gui_cache_sampled\":false}";}
  return json;
}
} // namespace xar::ck3_12002
