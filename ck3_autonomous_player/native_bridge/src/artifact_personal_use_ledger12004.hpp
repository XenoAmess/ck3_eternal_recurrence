#pragma once
#include "xar_bridge/artifact_personal_use12004.hpp"
#include <array>
#include <mutex>

namespace xar::ck3_12004::current_player_observers {
// Process-life owner-bound state. This is software admission, never a world
// mutation. Only the actual owner provider can supply admitted Frame/Witness.
class ArtifactIntentLedger12004 {
  using Frame=artifact_personal_use::Frame;
  using Request=artifact_personal_use::Request;
  using Observation=artifact_personal_use::Observation;
  using Witness=artifact_personal_use::Witness;
  using Result=artifact_personal_use::Result;
  struct Intent {
    bool used=false,pending=false;
    std::uint32_t pid=0,actor=artifact_personal_use::absent,artifact=artifact_personal_use::absent;
    std::uintptr_t owner=0;
    Request request{};
    Result result{};
  };
  std::mutex mutex_;
  std::array<Intent,128> entries_{};
  static bool SameActor(const Intent& i,const Frame& frame) noexcept {
    return i.pid==frame.bridge_pid&&i.owner==frame.owner&&i.actor==frame.actor_id;
  }
public:
  bool Claim(const Frame& frame,const Request& request,
             const Observation& before,const Witness& witness) noexcept {
    if(!frame.bridge_pid||!frame.owner||!frame.revision||!frame.capture_epoch||!frame.connection_generation||
       !frame.application_main_thread||!frame.native_tls_ready||!frame.paused||!frame.map_ready||!frame.actor_alive||
       !frame.actor_id||frame.actor_id==artifact_personal_use::absent||
       !request.request_sequence||request.artifact_id==artifact_personal_use::absent||request.expected_slot_index>=64||
       !before.available||!before.loaded_source_pins_verified||!before.personally_owned||
       before.frame!=frame||before.artifact_id!=request.artifact_id||
       !witness.actor||!witness.artifact||witness.character_owner!=frame.actor_id||
       witness.site_owner!=artifact_personal_use::absent)return false;
    std::lock_guard lock(mutex_);
    Intent* same=nullptr;Intent* empty=nullptr;
    for(auto& i:entries_) {
      if(!i.used){if(!empty)empty=&i;continue;}
      if(SameActor(i,frame)) {
        // Unresolved A forbids B as well: B must not replace A's slot before
        // A has an independent postcondition. Generation/nonce never clears it.
        if(i.pending)return false;
        if(i.artifact==request.artifact_id)same=&i;
      }
    }
    Intent* selected=same?same:empty;
    if(!selected)return false; // Never evict an unknown intent for capacity.
    *selected={};selected->used=true;selected->pending=true;
    selected->pid=frame.bridge_pid;selected->owner=frame.owner;selected->actor=frame.actor_id;
    selected->artifact=request.artifact_id;selected->request=request;
    selected->result.before=before;selected->result.once_intent_consumed=true;
    selected->result.invoked=true;selected->result.needs_recovery=true;
    selected->result.status="central_intent_consumed_dispatch_not_yet_observed";
    return true;
  }
  void RecordResult(const Frame& frame,const Request& request,const Result& result) {
    if(!result.once_intent_consumed)return;
    std::lock_guard lock(mutex_);
    for(auto& i:entries_) {
      if(i.used&&SameActor(i,frame)&&i.artifact==request.artifact_id&&
         i.request.request_sequence==request.request_sequence) {i.result=result;return;}
    }
  }
  // Updates only from a genuine independent reader. Callers must first close
  // their outer current owner/frame transaction; this function never reads or
  // mutates the game and cannot make unavailable input into a positive result.
  bool ObserveAfter(const Observation& after,std::uint64_t expected_sequence,
                    Request& request,Result& result,bool& desired_now) {
    desired_now=false;
    if(!after.available||!after.loaded_source_pins_verified)return false;
    std::lock_guard lock(mutex_);
    for(auto& i:entries_) {
      if(!i.used||!SameActor(i,after.frame)||i.artifact!=after.artifact_id)continue;
      const bool proof=artifact_personal_use::DesiredStateObserved12004(i.result.before,i.request,after);
      if(i.pending&&proof){i.pending=false;i.result.needs_recovery=false;}
      if(!expected_sequence||i.request.request_sequence!=expected_sequence)return false;
      request=i.request;result=i.result;desired_now=proof;
      return true;
    }
    return false;
  }
};
}
