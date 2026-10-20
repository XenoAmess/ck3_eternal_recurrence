#ifdef NDEBUG
#error Inventory Close wire fixture requires active assertions
#endif
#include "xar_bridge/player_inventory_window12004_transport.hpp"
#include "xar_bridge/player_inventory_close_ledger12004.hpp"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <cstdio>
namespace win=xar::ck3_12004::player_inventory_window;
using Post=xar::ck3_12004::PlayerInventoryOpenPost12004;
Post Before() {Post p{};p.available=p.current_admission=true;p.revision=10;p.capture_epoch=5;p.generation=7;
  p.date_raw=53144328;p.pid=1234;p.actor_id=p.subject_id=77;p.root=0x7000;
  p.owner=0x1000;p.actor=0x2000;p.handler=0x3000;p.view=0x4000;p.gui_context=0x5000;p.gui_lookup_owner=0x6000;
  p.native_visible=p.effective_visible=true;return p;}
int main(int argc,char**argv) {
  std::filesystem::path dir;
  if(argc!=1){assert(argc==3&&std::string_view(argv[1])=="--wire-dir");dir=argv[2];assert(!std::filesystem::exists(dir));std::filesystem::create_directories(dir);}
  // Authored owned metadata; actual production ledger/predicate/serializer.
  // No native GUI/TLS/module/callee is fabricated or invoked by this target.
  xar::ck3_12004::PlayerInventoryCloseLedger12004 ledger;const auto before=Before();
  assert(ledger.Claim(41,before));ledger.Record(41,1234,77,true,false,"inventory_close_unknown_do_not_retry");
  win::Observation q{};q.operation="close_query";q.available=q.code_pins_verified=q.gui_sources_verified=true;
  q.current=q.before=before;q.has_before=q.intent_found=q.once_consumed=q.invoked=q.needs_recovery=true;
  q.intent_sequence=41;q.status="inventory_window_observed";q.unavailable_reason.clear();
  const auto emit=[&](const char* name,const win::Observation& value){const auto body=win::SerializeClose(value);assert(!body.empty());
    if(!dir.empty()){const auto path=dir/(std::string(name)+".json");assert(!std::filesystem::exists(path));
      std::ofstream f(path,std::ios::binary);f.exceptions(std::ios::failbit|std::ios::badbit);f<<body<<'\n';}};
  emit("close-query-recovers-unknown-sequence",q);
  auto submit=q;submit.operation="close";submit.read_only=false;submit.call_returned=true;
  submit.status="inventory_close_invoked_post_pending";emit("close-ack-not-hidden-proof",submit);
  auto hidden=before;hidden.capture_epoch++;hidden.revision++;hidden.native_visible=hidden.effective_visible=false;
  hidden.root=0; // Native root may disappear; actual registered window remains.
  auto hidden_query=q;hidden_query.current=hidden;emit("close-query-hidden-not-resolved",hidden_query);
  xar::ck3_12004::PlayerInventoryCloseLedger12004::Receipt receipt{};
  assert(ledger.Find(41,1234,77,receipt)&&receipt.pending);
  auto post=q;post.operation="close_post";post.current=post.after=hidden;post.has_after=true;
  assert(ledger.Reconcile(41,hidden));post.desired_window_observed=true;post.needs_recovery=false;
  post.status="inventory_window_closed_observed";emit("close-post-independent-hidden",post);
  auto visible=hidden;visible.capture_epoch++;visible.root=before.root;visible.native_visible=visible.effective_visible=true;
  assert(!ledger.Reconcile(41,visible));post.current=post.after=visible;post.desired_window_observed=false;
  post.status="inventory_intent_previously_resolved_current_window_not_observed";emit("close-post-history-not-current-hidden",post);
  post.available=post.code_pins_verified=post.gui_sources_verified=false;
  post.current.available=post.current.current_admission=false;post.after=post.current;post.needs_recovery=true;
  post.status="inventory_intent_pending_or_unknown";post.unavailable_reason="fixture_current_frame_changed";
  emit("close-post-invalid-outer-clears-current",post);
  post.desired_window_observed=true;assert(win::SerializeClose(post).empty());
  submit.desired_window_observed=true;assert(win::SerializeClose(submit).empty());
  std::puts("inventory_close_wire six_real_serializer_bodies owned_metadata_only");
}
