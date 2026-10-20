#ifdef NDEBUG
#error "Owned assertion fixture requires NDEBUG undefined"
#endif
#include "xar_bridge/player_inventory_window12004_transport.hpp"
#include "xar_bridge/player_inventory_open_ledger12004.hpp"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <stdexcept>
namespace win=xar::ck3_12004::player_inventory_window;
using Post=xar::ck3_12004::PlayerInventoryOpenPost12004;
Post Before(){Post p{};p.available=p.current_admission=true;p.revision=10;p.capture_epoch=5;p.generation=7;
  p.date_raw=53144328;p.pid=1234;p.actor_id=77;p.subject_id=0xffffffffU;
  p.owner=0x1000;p.actor=0x2000;p.handler=0x3000;p.view=0x4000;p.gui_context=0x5000;p.gui_lookup_owner=0x6000;return p;}
int main(int argc,char**argv){
  std::filesystem::path dir;
  if(argc!=1){assert(argc==3&&std::string_view(argv[1])=="--wire-dir");dir=argv[2];assert(!std::filesystem::exists(dir));std::filesystem::create_directories(dir);}
  // Real software ledger + real inline postcondition + actual JSON serializer.
  // Frame and native pointer witnesses here are authored owned metadata, not a
  // substitute for actual GUI reader/owner/module/source qualification.
  xar::ck3_12004::PlayerInventoryOpenLedger12004 ledger;const auto before=Before();
  assert(ledger.Claim(21,before));auto changed=before;changed.generation++;changed.view++;
  assert(!ledger.Claim(22,changed));
  ledger.Record(21,1234,77,true,true,"inventory_original_open_invoked_post_pending");
  xar::ck3_12004::PlayerInventoryOpenLedger12004::Receipt receipt{};
  assert(ledger.Find(0,1234,77,receipt)&&receipt.sequence==21&&receipt.pending&&receipt.invoked);
  assert(!ledger.Find(21,1234,78,receipt));assert(ledger.Find(21,1234,77,receipt));
  win::Observation query{};query.available=query.code_pins_verified=query.gui_sources_verified=true;
  query.current=before;query.intent_found=query.once_consumed=query.invoked=query.call_returned=query.needs_recovery=true;
  query.intent_sequence=21;query.before=before;query.has_before=true;query.status="inventory_window_observed";query.unavailable_reason.clear();
  const auto emit=[&](const char*name,const win::Observation&o){const auto wire=win::Serialize(o);assert(!wire.empty());
    if(!dir.empty()){const auto p=dir/(std::string(name)+".json");assert(!std::filesystem::exists(p));std::ofstream file(p,std::ios::binary);file.exceptions(std::ios::failbit|std::ios::badbit);file<<wire<<'\n';}};
  emit("inventory-query-recovers-original-sequence",query);
  auto opened=before;opened.capture_epoch++;opened.revision++;opened.subject_id=77;opened.root=0x7000;opened.native_visible=opened.effective_visible=true;
  auto submit=query;submit.operation="open";submit.read_only=false;submit.status="inventory_original_open_invoked_post_pending";
  emit("inventory-open-ack-not-proof",submit);
  auto post=query;post.operation="post";post.current=post.after=opened;post.has_after=true;
  assert(ledger.Reconcile(21,opened));post.desired_window_observed=true;post.needs_recovery=false;post.status="inventory_window_desired_observed";
  emit("inventory-post-independent-positive",post);
  opened.native_visible=false;opened.effective_visible=false;opened.capture_epoch++;
  assert(!ledger.Reconcile(21,opened));assert(ledger.Find(21,1234,77,receipt)&&!receipt.pending);
  post.current=post.after=opened;post.desired_window_observed=false;post.status="inventory_intent_previously_resolved_current_window_not_observed";
  emit("inventory-post-history-not-current-proof",post);
  post.available=post.code_pins_verified=post.gui_sources_verified=false;post.current.available=post.current.current_admission=false;
  post.after=post.current;post.needs_recovery=true;post.status="inventory_intent_pending_or_unknown";post.unavailable_reason="fixture_current_frame_changed";
  emit("inventory-post-invalid-outer-clears-current",post);
  post.desired_window_observed=true;assert(win::Serialize(post).empty());
}
