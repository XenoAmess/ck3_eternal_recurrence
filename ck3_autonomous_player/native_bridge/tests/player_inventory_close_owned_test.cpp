#ifdef NDEBUG
#error Inventory Close owned fixture requires active assertions
#endif
#include "xar_bridge/player_inventory_close_ledger12004.hpp"
#include "xar_bridge/player_inventory_open_ledger12004.hpp"
#include <cassert>
#include <cstdio>
using namespace xar::ck3_12004;
PlayerInventoryOpenPost12004 Before() {
  PlayerInventoryOpenPost12004 p{};p.available=p.current_admission=true;
  p.revision=10;p.capture_epoch=5;p.generation=7;p.date_raw=53144328;p.pid=1234;
  p.actor_id=p.subject_id=77;p.owner=0x1000;p.actor=0x2000;p.handler=0x3000;p.view=0x4000;
  p.gui_context=0x5000;p.gui_lookup_owner=0x6000;p.root=0x7000;
  p.native_visible=p.effective_visible=true;return p;
}
int main() {
  const auto before=Before();auto hidden=before;hidden.capture_epoch++;hidden.revision++;
  hidden.native_visible=hidden.effective_visible=false;
  assert(PlayerInventoryCloseDesiredObserved12004(before,hidden));
  assert(!PlayerInventoryOpenDesiredObserved12004(before,hidden));
  auto no_root=hidden;no_root.root=0;assert(PlayerInventoryCloseDesiredObserved12004(before,no_root));
  const auto reject=[&](auto mutate){auto v=hidden;mutate(v);assert(!PlayerInventoryCloseDesiredObserved12004(before,v));};
  reject([](auto&v){v.capture_epoch=5;});reject([](auto&v){v.revision=9;});
  reject([](auto&v){v.date_raw--;});reject([](auto&v){v.generation++;});
  reject([](auto&v){v.pid++;});reject([](auto&v){v.actor_id++;});
  reject([](auto&v){v.subject_id++;});reject([](auto&v){v.owner++;});
  reject([](auto&v){v.actor++;});reject([](auto&v){v.handler++;});reject([](auto&v){v.view++;});
  reject([](auto&v){v.gui_context++;});reject([](auto&v){v.gui_lookup_owner++;});
  reject([](auto&v){v.native_visible=true;});reject([](auto&v){v.effective_visible=true;});
  reject([](auto&v){v.available=false;});reject([](auto&v){v.current_admission=false;});
  PlayerInventoryCloseLedger12004 ledger;auto not_visible=before;not_visible.native_visible=false;
  assert(!ledger.Claim(20,not_visible));assert(!ledger.Claim(0,before));assert(ledger.Claim(21,before));
  ledger.Record(21,1234,77,true,false,"inventory_close_unknown_do_not_retry");
  PlayerInventoryCloseLedger12004::Receipt receipt{};
  assert(ledger.Find(0,1234,77,receipt)&&receipt.sequence==21&&receipt.pending&&receipt.invoked&&!receipt.call_returned);
  auto changed=before;changed.generation++;changed.owner++;changed.view++;
  assert(!ledger.Claim(22,changed)); // Unknown remains across owner/generation.
  assert(!ledger.Find(21,1234,78,receipt));assert(ledger.Find(21,1234,77,receipt)&&receipt.pending);
  // Reading a hidden DTO does not itself resolve; only explicit Reconcile does.
  assert(PlayerInventoryCloseDesiredObserved12004(before,hidden));
  assert(ledger.Find(21,1234,77,receipt)&&receipt.pending);
  auto stale=hidden;stale.capture_epoch=5;assert(!ledger.Reconcile(21,stale));
  assert(ledger.Find(21,1234,77,receipt)&&receipt.pending);
  assert(ledger.Reconcile(21,hidden));assert(ledger.Find(21,1234,77,receipt)&&!receipt.pending);
  auto visible_again=hidden;visible_again.capture_epoch++;visible_again.native_visible=visible_again.effective_visible=true;
  assert(!ledger.Reconcile(21,visible_again));assert(ledger.Find(21,1234,77,receipt)&&!receipt.pending);
  assert(!ledger.Claim(21,visible_again));assert(ledger.Claim(22,visible_again));
  // Software objects are independent: neither original open desired-state nor
  // reconciliation can accidentally settle the actual close ledger.
  PlayerInventoryOpenLedger12004 opens;assert(opens.Claim(31,before));
  assert(!opens.Reconcile(31,hidden));assert(ledger.Find(22,1234,77,receipt)&&receipt.pending);
  std::puts("inventory_close_owned actual_hidden_predicate independent_once_unknown_history");
}
