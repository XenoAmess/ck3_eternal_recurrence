#pragma once
#include "xar_bridge/player_inventory_open_post12004.hpp"
#include <array>
#include <mutex>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {
// One instance for the native process lifetime, owned by the mailbox transport.
// Not one per request, revision, SDK connection or native connection generation.
// The caller passes only the bridge-assigned owner mailbox sequence.
class PlayerInventoryOpenLedger12004 {
 public:
  struct Receipt {
    bool found=false,pending=false,invoked=false,call_returned=false;
    std::uint64_t sequence=0;
    PlayerInventoryOpenPost12004 before{};
    std::string status="inventory_intent_claimed_before_dispatch";
  };
  bool Claim(std::uint64_t sequence,const PlayerInventoryOpenPost12004&actual_before) noexcept {
    try {std::lock_guard lock(mutex_);
      if(!sequence||!actual_before.available||!actual_before.current_admission||
          !actual_before.pid||!actual_before.owner||!actual_before.actor||!actual_before.handler||
          !actual_before.view||!actual_before.gui_context||!actual_before.gui_lookup_owner||
          !actual_before.actor_id||actual_before.actor_id==0xFFFFFFFFU)return false;
      Entry*same=nullptr;Entry*empty=nullptr;
      for(auto&e:entries_){
        if(!e.used){if(!empty)empty=&e;continue;}
        // A new owner/view/connection never releases an unresolved same-actor
        // UI intent. It must be reconciled with the original qualified window.
        if(e.before.pid==actual_before.pid&&e.before.actor_id==actual_before.actor_id&&e.pending)return false;
        if(e.before.pid==actual_before.pid&&e.before.actor_id==actual_before.actor_id&&
            e.before.owner==actual_before.owner&&e.before.view==actual_before.view)same=&e;
      }
      auto*row=same?same:empty;if(!row)return false;
      if(same&&sequence<=same->sequence)return false;
      row->used=row->pending=true;row->sequence=sequence;row->before=actual_before;
      row->invoked=row->call_returned=false;row->status="inventory_intent_claimed_before_dispatch";return true;
    }catch(...){return false;}
  }
  // Query is a new owner mailbox read, independent of the original call. A
  // historical resolved bit is never returned as current desired-state proof.
  bool Reconcile(std::uint64_t original_sequence,const PlayerInventoryOpenPost12004&after) noexcept {
    try {std::lock_guard lock(mutex_);
      for(auto&e:entries_)if(e.used&&e.sequence==original_sequence&&
          e.before.pid==after.pid&&e.before.actor_id==after.actor_id){
        const bool fresh=PlayerInventoryOpenDesiredObserved12004(e.before,after);
        if(fresh)e.pending=false;return fresh;
      }
      return false;
    }catch(...){return false;}
  }
  // Native-only retention. A read can recover the actual original sequence
  // after an ACK loss, but neither Find nor a visible query resolves pending.
  bool Find(std::uint64_t sequence,std::uint32_t pid,std::uint32_t actor,Receipt&out) noexcept {
    out={};try {std::lock_guard lock(mutex_);const Entry*selected=nullptr;
      for(const auto&e:entries_)if(e.used&&e.before.pid==pid&&e.before.actor_id==actor&&
          (!sequence||e.sequence==sequence)&&(!selected||e.sequence>selected->sequence))selected=&e;
      if(!selected)return false;
      out={true,selected->pending,selected->invoked,selected->call_returned,
           selected->sequence,selected->before,selected->status};return true;
    }catch(...){out={};return false;}
  }
  void Record(std::uint64_t sequence,std::uint32_t pid,std::uint32_t actor,
              bool invoked,bool returned,std::string_view status) noexcept {
    try {std::lock_guard lock(mutex_);
      for(auto&e:entries_)if(e.used&&e.sequence==sequence&&e.before.pid==pid&&e.before.actor_id==actor){
        e.invoked=invoked;e.call_returned=returned;e.status.assign(status);return;}
    }catch(...){} // Claim remains consumed even if receipt allocation fails.
  }
 private:
  struct Entry {bool used=false,pending=false,invoked=false,call_returned=false;std::uint64_t sequence=0;PlayerInventoryOpenPost12004 before{};std::string status;};
  std::array<Entry,128> entries_{};
  std::mutex mutex_;
};
}
