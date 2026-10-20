// Finite consumer of the actual production postcondition, not a native wire or
// game fixture. One C++20 TU; no runtime archive, Windows APIs or game dependency.
#ifdef NDEBUG
#undef NDEBUG
#endif
#include "xar_bridge/player_inventory_open_post12004.hpp"
#include "xar_bridge/player_inventory_open_ledger12004.hpp"
#include <cassert>

int main(){
  using namespace xar::ck3_12004;
  PlayerInventoryOpenPost12004 b{},a{};
  b.available=b.current_admission=true;b.revision=7;b.capture_epoch=11;b.generation=3;
  b.date_raw=100;b.pid=123;b.actor_id=0x01000021;b.owner=1;b.actor=2;b.handler=3;b.view=4;
  b.gui_context=6;b.gui_lookup_owner=7;
  a=b;a.revision=8;a.capture_epoch=12;a.root=5;a.subject_id=b.actor_id;
  a.native_visible=a.effective_visible=true;
  assert(PlayerInventoryOpenDesiredObserved12004(b,a));
  {auto x=a;x.capture_epoch=b.capture_epoch;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.generation++;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.pid++;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.owner++;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.gui_context++;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.gui_lookup_owner++;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.actor_id++;x.subject_id=x.actor_id;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.subject_id++;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.view++;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.root=0;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.native_visible=false;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.effective_visible=false;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.current_admission=false;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=b;x.available=false;assert(!PlayerInventoryOpenDesiredObserved12004(x,a));}
  {auto x=a;x.date_raw--;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  {auto x=a;x.revision--;x.revision--;assert(!PlayerInventoryOpenDesiredObserved12004(b,x));}
  PlayerInventoryOpenLedger12004 ledger;
  assert(ledger.Claim(31,b));
  assert(!ledger.Claim(32,b)); // rename cannot replay unknown
  {auto x=b;x.generation++;assert(!ledger.Claim(33,x));}
  {auto x=b;x.owner++;x.view++;assert(!ledger.Claim(34,x));}
  {auto x=a;x.capture_epoch=b.capture_epoch;assert(!ledger.Reconcile(31,x));}
  assert(!ledger.Claim(35,b)); // failed post preserved pending
  assert(ledger.Reconcile(31,a));
  {auto x=a;x.effective_visible=false;assert(!ledger.Reconcile(31,x));} // no historical credit
  assert(!ledger.Claim(31,b)); // original sequence cannot replay after resolution
  assert(ledger.Claim(36,b));
  assert(!ledger.Reconcile(999,a));
  return 0;
}
