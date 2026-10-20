#pragma once
#include "xar_bridge/player_inventory_open_post12004.hpp"
namespace xar::ck3_12004 {
// Same real structural witness as the open reader, with an independent hidden
// desired state. A returned Close call is never a postcondition observation.
inline bool PlayerInventoryCloseDesiredObserved12004(
    const PlayerInventoryOpenPost12004& b,const PlayerInventoryOpenPost12004& a) noexcept {
  return b.available&&a.available&&b.current_admission&&a.current_admission&&
      b.pid&&b.actor_id&&b.actor_id!=0xFFFFFFFFU&&b.owner&&b.actor&&b.handler&&b.view&&b.root&&
      b.gui_context&&b.gui_lookup_owner&&b.subject_id==b.actor_id&&b.native_visible&&b.effective_visible&&
      b.revision&&b.capture_epoch&&b.generation&&a.capture_epoch>b.capture_epoch&&
      a.revision>=b.revision&&a.date_raw>=b.date_raw&&a.pid==b.pid&&
      a.generation==b.generation&&a.actor_id==b.actor_id&&a.owner==b.owner&&
      a.actor==b.actor&&a.handler==b.handler&&a.view==b.view&&
      a.gui_context==b.gui_context&&a.gui_lookup_owner==b.gui_lookup_owner&&
      a.subject_id==a.actor_id&&!a.native_visible&&!a.effective_visible;
}
}
