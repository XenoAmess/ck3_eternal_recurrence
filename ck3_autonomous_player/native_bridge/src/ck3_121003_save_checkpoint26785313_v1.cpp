#include "xar_bridge/ck3_121003_save_checkpoint26785313_v1.hpp"
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <algorithm>
#include <chrono>
#include <limits>
#include <windows.h>

namespace xar::ck3_121003::build26785313 { namespace {
using Status=SaveCheckpointStatus267V1;
using Decision=SaveCheckpointClaimDecision267V1;
[[maybe_unused]] bool Equal(const ck3_1210::CoreSnapshotPrefix&a,const ck3_1210::CoreSnapshotPrefix&b) noexcept {
  return a.clock.date_raw==b.clock.date_raw&&a.clock.speed==b.clock.speed&&a.clock.paused==b.clock.paused&&
      a.local_player_id==b.local_player_id&&a.map_ready==b.map_ready&&a.has_played_character==b.has_played_character&&
      a.played_character_id==b.played_character_id&&a.played_character_alive==b.played_character_alive;
}
bool SameSource(const SaveCheckpointSource267V1&a,const SaveCheckpointSource267V1&b) noexcept {
  // A reconnect does not reset or change the already bound source/claims.
  return a.module_base==b.module_base&&a.game_state==b.game_state&&a.jomini_state==b.jomini_state;
}
bool ValidId(const SaveCheckpointRequest267V1&r) noexcept {
  if(!r.request_id_size||r.request_id_size>96||r.request_id[r.request_id_size]!=0)return false;
  for(const char c:r.id())if(!((c>='0'&&c<='9')||(c>='a'&&c<='z')||
      (c>='A'&&c<='Z')||c=='-'||c=='_'||c=='.'))return false;
  return true;
}
std::uint64_t WallNow() noexcept {
  const auto now=std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::system_clock::now().time_since_epoch()).count();
  return now>=0?static_cast<std::uint64_t>(now):0;
}
[[maybe_unused]] bool Unexpired(const SaveCheckpointContext267V1&q) noexcept {
  const auto wall=WallNow();return wall&&q.monotonic_deadline_ms&&
      wall<q.request.control.deadline_unix_ms&&GetTickCount64()<q.monotonic_deadline_ms;
}
[[maybe_unused]] Status Denial(Decision d) noexcept {
  return d==Decision::consumed?Status::claim_consumed:d==Decision::source_changed?Status::source_changed:
      d==Decision::capacity_exhausted?Status::capacity_exhausted:Status::unavailable;
}
[[maybe_unused]] SaveCheckpointSource267V1 Source(const SaveCheckpointContext267V1&q,
    const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
  return {q.bindings.module_base,s.game_state,s.jomini_state,q.connection_generation};
}
[[maybe_unused]] bool ReadCurrent(SaveCheckpointContext267V1&q,
    const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1) && XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1
  ReadonlyObservation current;
  if(!ReadSaveCheckpointCoreOnOwner267V1(q.bindings,q.mailbox,q.ticket,s,&q,current)||
      !current.available||current.offline_fixture||!current.main_owner_observed||
      !Equal(current.core,q.request.control.expected)||current.core.clock.date_raw!=s.date_raw||
      current.core.clock.paused!=s.paused) {q.result.status=Status::stale_core;return false;}
  q.result.observed=current.core;
  if(!current.core.clock.paused||!current.core.map_ready||current.core.local_player_id<0||
      !current.core.has_played_character||current.core.played_character_id==-1||
      !current.core.played_character_alive) {q.result.status=Status::requires_paused_map_living;return false;}
  return true;
#else
  (void)q;(void)s;return false;
#endif
}
struct Admission {
  SaveCheckpointContext267V1&query;
  const ck3_11906::MainThreadExecutionStampV1&stamp;
  CommandImageBindingsV1 bound;
};
[[maybe_unused]] bool BeforeQueue(void *opaque) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1) && XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1
  if(!opaque)return false;auto&a=*static_cast<Admission*>(opaque);auto&q=a.query;
  if(!Unexpired(q)){q.result.status=Status::expired;return false;}
  if(!ReadCurrent(q,a.stamp))return false;
  const auto bound=BindCurrentCommandImageV1(q.bindings.module_base,{kGameVersion,kSteamBuildId,kExecutableSha256});
  if(!bound.current_image_verified||bound.offline_fixture||!CurrentCommandTargetsMatchV1(bound)||
      bound.commands.command_manager!=a.bound.commands.command_manager||
      bound.commands.queue_owned_command!=a.bound.commands.queue_owned_command||
      bound.commands.auto_save_primary_vtable!=a.bound.commands.auto_save_primary_vtable||
      bound.commands.auto_save_secondary_vtable!=a.bound.commands.auto_save_secondary_vtable)return false;
  if(!Unexpired(q)){q.result.status=Status::expired;return false;}
  const auto decision=ClaimSaveCheckpoint267V1(*q.session,q.request,Source(q,a.stamp),q.result.submission_sequence);
  if(decision!=Decision::ready){q.result.status=Denial(decision);return false;}
  // The manager call follows immediately in the existing move/queue algorithm.
  // Retain this claim and UNKNOWN if any queue/cleanup boundary becomes uncertain.
  q.result.effect_attempted=true;q.result.status=Status::indeterminate;return true;
#else
  (void)opaque;return false;
#endif
}
bool Execute(SaveCheckpointContext267V1&q,
    [[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
  q.result={};q.command_ownership_entered=false;
#if defined(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1) && XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1
  if(!q.mailbox||q.mailbox->offline_fixture||!q.session||!q.connection_generation||
      !SaveCheckpointRequestShape267V1(q.request))return true;
  if(!Unexpired(q)){q.result.status=Status::expired;return true;}
  if(!ReadCurrent(q,s))return true;
  const auto decision=InspectSaveCheckpointClaim267V1(*q.session,q.request,Source(q,s));
  if(decision!=Decision::ready){q.result.status=Denial(decision);return true;}
  const auto bound=BindCurrentCommandImageV1(q.bindings.module_base,{kGameVersion,kSteamBuildId,kExecutableSha256});
  if(!bound.current_image_verified||bound.offline_fixture||!CurrentCommandTargetsMatchV1(bound))return true;
  if(!Unexpired(q)){q.result.status=Status::expired;return true;}
  const auto command=ck3_1210::MakeSaveCheckpointCommand(bound.commands);
  Admission admission{q,s,bound};q.command_ownership_entered=true;
  const auto submitted=ck3_1210::SubmitCommandCopy(bound.commands,&command,7,&BeforeQueue,&admission);
  q.command_ownership_entered=false;
  if(!q.result.effect_attempted)return true; // BeforeQueue's actual refusal remains intact.
  q.result.status=submitted==ck3_1210::CommandSubmitResult::submitted?Status::submitted:
      submitted==ck3_1210::CommandSubmitResult::rejected?Status::rejected:Status::indeterminate;
  FinishSaveCheckpointClaim267V1(*q.session,q.result.submission_sequence,q.result.status);
#endif
  return true;
}
} // namespace

bool SaveCheckpointRequestShape267V1(const SaveCheckpointRequest267V1&r) noexcept {
  const auto&p=r.control.expected;
  return ValidId(r)&&r.control.operation==ck3_1210::CoreControlOperationV1::save&&
      r.control.step==kSaveCheckpointStep267V1&&r.control.deadline_unix_ms&&
      p.clock.speed>=1&&p.clock.speed<=5&&p.clock.paused&&p.map_ready&&p.local_player_id>=0&&
      p.has_played_character&&p.played_character_id!=-1&&p.played_character_alive;
}
SaveCheckpointClaimDecision267V1 InspectSaveCheckpointClaim267V1(const SaveCheckpointSession267V1&s,
    const SaveCheckpointRequest267V1&r,const SaveCheckpointSource267V1&source) noexcept {
  if(!SaveCheckpointRequestShape267V1(r)||!source.module_base||!source.game_state||
      !source.jomini_state||!source.connection_generation)return Decision::invalid;
  if(s.unknown_)return Decision::consumed;
  for(std::size_t i=0;i<s.size_;++i)if(s.claims_[i].request.id()==r.id())return Decision::consumed;
  if(s.size_) {
    const auto&first=s.claims_[0];const auto&last=s.claims_[s.size_-1];
    if(!SameSource(first.source,source)||first.request.control.expected.local_player_id!=r.control.expected.local_player_id||
        first.request.control.expected.played_character_id!=r.control.expected.played_character_id)return Decision::source_changed;
    if(last.status==Status::indeterminate||r.control.expected.clock.date_raw<=last.request.control.expected.clock.date_raw)
      return Decision::consumed;
  }
  return s.size_==s.claims_.size()?Decision::capacity_exhausted:Decision::ready;
}
SaveCheckpointClaimDecision267V1 ClaimSaveCheckpoint267V1(SaveCheckpointSession267V1&s,
    const SaveCheckpointRequest267V1&r,const SaveCheckpointSource267V1&source,std::uint64_t&sequence) noexcept {
  sequence=0;const auto decision=InspectSaveCheckpointClaim267V1(s,r,source);
  if(decision!=Decision::ready)return decision;
  auto&claim=s.claims_[s.size_++];claim.request=r;claim.source=source;claim.status=Status::indeterminate;
  sequence=s.size_;return Decision::ready;
}
void FinishSaveCheckpointClaim267V1(SaveCheckpointSession267V1&s,std::uint64_t sequence,Status status) noexcept {
  if(!sequence||sequence!=s.size_||(status!=Status::submitted&&status!=Status::rejected&&status!=Status::indeterminate)) {
    s.unknown_=true;return;
  }
  auto&claim=s.claims_[static_cast<std::size_t>(sequence-1)];
  if(claim.status!=Status::indeterminate){s.unknown_=true;return;}
  claim.status=status;if(status==Status::indeterminate)s.unknown_=true;
}
void BlockSaveCheckpointUnknown267V1(SaveCheckpointSession267V1&s) noexcept {s.unknown_=true;}
void ArmSaveCheckpointDeadline267V1(SaveCheckpointContext267V1&q) noexcept {
  q.monotonic_deadline_ms=0;const auto wall=WallNow(),mono=GetTickCount64();
  if(!wall||q.request.control.deadline_unix_ms<=wall)return;
  const auto remaining=q.request.control.deadline_unix_ms-wall;
  const auto delta=remaining<8000?remaining:8000;
  if(mono>(std::numeric_limits<std::uint64_t>::max)()-delta)return;
  q.monotonic_deadline_ms=mono+delta;
}
bool ExecuteSaveCheckpointOnOwner267V1(void *opaque,const ck3_11906::MainThreadExecutionStampV1&s) noexcept {
  if(!opaque)return false;auto&q=*static_cast<SaveCheckpointContext267V1*>(opaque);
  __try {return Execute(q,s);}
  __except(EXCEPTION_EXECUTE_HANDLER) {
    if(q.command_ownership_entered&&q.session) {
      BlockSaveCheckpointUnknown267V1(*q.session);q.result.status=Status::indeterminate;
    } else q.result.status=Status::unavailable;
    return true;
  }
}
bool SaveCheckpointRouteEnabled267V1([[maybe_unused]]const game::AdapterDescriptor&d) noexcept {
#if defined(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1) && XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1
  return game::IsCk3_121003Core26785313Descriptor(d)&&
      std::find(d.capabilities.begin(),d.capabilities.end(),ck3_1210::kCoreFrameCapabilityV1)!=d.capabilities.end()&&
      std::find(d.capabilities.begin(),d.capabilities.end(),kSaveCheckpointCapability267V1)!=d.capabilities.end();
#else
  return false;
#endif
}
} // namespace xar::ck3_121003::build26785313
