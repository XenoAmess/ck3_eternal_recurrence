#pragma once
#include <cstdint>
namespace xar::ck3_12004 {
// Provider-private structural witness. Never serialize these addresses. The
// producer fills it only after two real source-bound window/frame reads.
struct PlayerInventoryOpenPost12004 {
  bool available=false,current_admission=false;
  std::uint64_t revision=0,capture_epoch=0,generation=0;
  std::int64_t date_raw=0;
  std::uint32_t pid=0,actor_id=0xFFFFFFFFU,subject_id=0xFFFFFFFFU;
  std::uintptr_t owner=0,actor=0,handler=0,view=0,root=0,gui_context=0,gui_lookup_owner=0;
  bool native_visible=false,effective_visible=false;
};
inline bool PlayerInventoryOpenDesiredObserved12004(
    const PlayerInventoryOpenPost12004&b,const PlayerInventoryOpenPost12004&a) noexcept {
  return b.available&&a.available&&b.current_admission&&a.current_admission&&
      b.pid&&b.actor_id&&b.actor_id!=0xFFFFFFFFU&&b.owner&&b.actor&&b.handler&&b.view&&
      b.gui_context&&b.gui_lookup_owner&&
      b.revision&&b.capture_epoch&&b.generation&&a.capture_epoch>b.capture_epoch&&
      a.revision>=b.revision&&a.date_raw>=b.date_raw&&a.pid==b.pid&&
      a.generation==b.generation&&a.actor_id==b.actor_id&&a.owner==b.owner&&
      a.actor==b.actor&&a.handler==b.handler&&a.view==b.view&&a.root&&
      a.gui_context==b.gui_context&&a.gui_lookup_owner==b.gui_lookup_owner&&
      a.native_visible&&a.effective_visible&&a.subject_id==a.actor_id;
}
}
