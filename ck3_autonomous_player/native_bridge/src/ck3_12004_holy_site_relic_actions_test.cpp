#include "xar_bridge/ck3_12004_holy_site_relic_actions.hpp"
#include "xar_bridge/holy_site_relic_request12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
#if defined(XAR_RELIC_FULL_UI_PACKET_FIXTURE)
#include "xar_bridge/ingame_ui_mailbox_v1.hpp"
#endif

namespace relic=xar::ck3_12004::religion::relic_actions;
namespace {
constexpr std::uint32_t actor_id=0x01000001,site_id=0x84000002,artifact_id=0x83000003,foreign_id=0x83000004;
struct Header {const void*data=nullptr;std::int32_t capacity=0,count=0;std::uint64_t allocator=0;};
struct Slot {std::uintptr_t vtable=0,type=0;std::uint32_t artifact=relic::absent,magic=0x496E7653U;};
template<class T>void Put(void*p,std::size_t offset,const T&v){std::memcpy(static_cast<unsigned char*>(p)+offset,&v,sizeof(v));}
template<class T>T Get(const void*p,std::size_t offset){T value{};std::memcpy(&value,static_cast<const unsigned char*>(p)+offset,sizeof(value));return value;}
struct Region {const unsigned char*address=nullptr;std::size_t bytes=0;};
struct Fixture {
 std::array<unsigned char,0x200>actor{},site{},artifact{},foreign{},owner{},gfx{},window{},root{};
 std::array<unsigned char,0x600>handler{};
 std::array<unsigned char,0x40>actor_store{},site_store{},artifact_store{};
 std::array<std::uintptr_t,4>actor_rows{};
 std::array<std::uintptr_t,6>site_rows{};
 std::array<std::uintptr_t,10>artifact_rows{};
 std::array<Slot,2>slots{};std::array<std::uint32_t,1>candidates{artifact_id};
 void*actor_store_pointer=actor_store.data(),*site_store_pointer=site_store.data(),*artifact_store_pointer=artifact_store.data();
 std::uint32_t current_actor=actor_id;
 std::vector<Region>regions;
 relic::Bindings bindings{};relic::Admission admission{};relic::Frame frame{71,701,17,51394920,static_cast<std::int32_t>(actor_id)};
 relic::PreviewProof proof{};
 int select_calls=0,toggle_calls=0,button_calls=0,click_calls=0,preview_calls=0,presentation_calls=0;
 bool button_allowed=true,click_returns=true,selection_returns=true,preview_drift=false,presentation_visible=true;
 Fixture(){
  const auto region=[&](auto&v){regions.push_back({reinterpret_cast<const unsigned char*>(&v),sizeof(v)});};
  region(actor);region(site);region(artifact);region(foreign);region(owner);region(gfx);region(window);region(root);region(handler);
  region(actor_store);region(site_store);region(artifact_store);region(actor_rows);region(site_rows);region(artifact_rows);
  region(slots);region(candidates);region(actor_store_pointer);region(site_store_pointer);region(artifact_store_pointer);region(current_actor);
  Put(actor.data(),0x18,actor_id);Put(actor.data(),0x1C,std::uint32_t{0x43686172});
  Put(site.data(),0x10,site_id);Put(site.data(),0x14,std::uint32_t{0x486F5374});
  Put(artifact.data(),0x10,artifact_id);Put(artifact.data(),0x14,std::uint32_t{0x41727469});Put(artifact.data(),0x78,actor_id);Put(artifact.data(),0x7C,relic::absent);
  Put(foreign.data(),0x10,foreign_id);Put(foreign.data(),0x14,std::uint32_t{0x41727469});
  actor_rows[3]=reinterpret_cast<std::uintptr_t>(actor.data());site_rows[5]=reinterpret_cast<std::uintptr_t>(site.data());
  artifact_rows[7]=reinterpret_cast<std::uintptr_t>(artifact.data());artifact_rows[9]=reinterpret_cast<std::uintptr_t>(foreign.data());
  Put(actor_store.data(),0x20,actor_rows.data());Put(actor_store.data(),0x2C,std::uint32_t{2});
  Put(site_store.data(),0x20,site_rows.data());Put(site_store.data(),0x2C,std::uint32_t{3});
  Put(artifact_store.data(),0x20,artifact_rows.data());Put(artifact_store.data(),0x2C,std::uint32_t{5});
  const std::uintptr_t base=0x140000000;
  Put(owner.data(),0x10,gfx.data());Put(gfx.data(),0x88,handler.data());Put(handler.data(),0x5D8,window.data());
  Put(window.data(),0,base+0x4592338);Put(window.data(),0x10,base+0x4592310);
  Put(window.data(),0x98,owner.data());Put(window.data(),0xA0,handler.data());Put(window.data(),0x60,root.data());
  Put(window.data(),0xC8,site_id);Put(window.data(),0x108,relic::absent);Put(window.data(),0x110,static_cast<const void*>(nullptr));
  Put(site.data(),0x68,Header{slots.data(),2,2,0});Put(window.data(),0x130,Header{candidates.data(),1,1,0});
  bindings.enabled=true;bindings.image_base=base;bindings.read_memory=&Read;bindings.read_context=this;
  bindings.holy_site_storage=&site_store_pointer;bindings.artifact_storage=&artifact_store_pointer;bindings.character_storage=&actor_store_pointer;
  bindings.current_actor_reference=&current_actor;bindings.select_artifact=&Select;bindings.toggle_slot=&Toggle;
  bindings.enshrine_button=&Button;bindings.remove_button=&Button;bindings.enshrine_click=&Click;bindings.remove_click=&Click;
  bindings.backend="owned_fixture_injected_original_dependencies";
  admission={owner.data(),handler.data(),root.data(),true,true,true,true};
 }
 static bool Read(void*context,const void*p,void*out,std::size_t bytes) noexcept {
  const auto&f=*static_cast<const Fixture*>(context);const auto at=reinterpret_cast<std::uintptr_t>(p);
  for(const auto&r:f.regions){const auto begin=reinterpret_cast<std::uintptr_t>(r.address);
   if(at>=begin&&at-begin<=r.bytes&&bytes<=r.bytes-(at-begin)){std::memcpy(out,p,bytes);return true;}}
  return false;
 }
 static bool Select(const relic::Bindings&b,const void*w,const void*a,bool&attempted) noexcept {
  auto&f=*static_cast<Fixture*>(b.read_context);++f.select_calls;attempted=true;
  if(w!=f.window.data()||a!=f.artifact.data())return false;
  Put(f.window.data(),0x108,Get<std::uint32_t>(a,0x10));return f.selection_returns;
 }
 static bool Toggle(const relic::Bindings&b,const void*w,const void*s,bool&attempted) noexcept {
  auto&f=*static_cast<Fixture*>(b.read_context);++f.toggle_calls;attempted=true;
  if(w!=f.window.data()||(s!=&f.slots[0]&&s!=&f.slots[1]))return false;
  Put(f.window.data(),0x110,Get<const void*>(w,0x110)==s?nullptr:s);return f.selection_returns;
 }
 static bool Button(const relic::Bindings&b,const void*w,bool&v) noexcept {
  auto&f=*static_cast<Fixture*>(b.read_context);++f.button_calls;if(w!=f.window.data())return false;v=f.button_allowed;return true;
 }
 static bool Click(const relic::Bindings&b,const void*w,bool&attempted) noexcept {
  auto&f=*static_cast<Fixture*>(b.read_context);++f.click_calls;attempted=true;if(w!=f.window.data())return false;
  Put(f.window.data(),0x108,relic::absent);Put(f.window.data(),0x110,static_cast<const void*>(nullptr));return f.click_returns;
 }
 static bool Preview(void*opaque,const relic::Admission&,const relic::Frame&,const relic::Request&,relic::PreviewProof&out) noexcept {
  auto&f=*static_cast<Fixture*>(opaque);++f.preview_calls;out=f.proof;
  if(f.preview_drift&&f.preview_calls>1)out.replacing_artifact_id=foreign_id;return true;
 }
 static bool Presentation(void*opaque,const relic::Admission&,const relic::Request&,relic::ButtonPresentation&out) noexcept {
  auto&f=*static_cast<Fixture*>(opaque);++f.presentation_calls;out={true,f.presentation_visible,true,"0/1",f.root.data(),f.root.data()};return true;
 }
 relic::Request SelectRequest(){relic::Request r{};r.holy_site_id=site_id;r.artifact_id=artifact_id;return r;}
 relic::Request SlotRequest(std::uint32_t index,bool selected){relic::Request r{};r.operation=relic::Operation::set_slot;r.holy_site_id=site_id;r.slot_index=index;r.desired_selected=selected;return r;}
 relic::Request ActionRequest(relic::Operation op){
  auto r=SelectRequest();r.operation=op;r.frozen_preconditions=true;r.expected_preview_identity_sha256=std::string(64,'a');
  if(op==relic::Operation::enshrine)r.expected_effective_slot_index=0;
  Put(window.data(),0x108,artifact_id);
  proof.available=true;proof.source_qualified=true;proof.live_qualified=true;proof.frame=frame;
  proof.holy_site_id=site_id;proof.artifact_id=artifact_id;proof.effective_slot_index=r.expected_effective_slot_index;
  proof.artifact_character_owner_matches_player=true;proof.player_owned_ids_contains_artifact=true;
  proof.site_equipped_slot_member=op==relic::Operation::remove;proof.preview_observed=true;proof.preview_identity_sha256=r.expected_preview_identity_sha256;
  if(op==relic::Operation::remove){Put(artifact.data(),0x7C,site_id);slots[0].artifact=artifact_id;}
  bindings.gameplay_action_lane_enabled=true;bindings.preview_reader=&Preview;bindings.preview_context=this;
  bindings.presentation_reader=&Presentation;bindings.presentation_context=this;return r;
 }
 bool Run(const relic::Request&r,relic::Result&out){return relic::ExecuteHolySiteRelicAction12004(bindings,admission,frame,r,out);}
};
int checks=0;
void Check(bool value,const char*why){++checks;if(!value)throw std::runtime_error(why);}
void Packet(const std::filesystem::path&dir,const char*name,const relic::Result&r,const relic::Request&request){
 if(dir.empty())return;const auto p=dir/(std::string(name)+".json");if(std::filesystem::exists(p))throw std::runtime_error("refuse existing packet");
 std::ofstream out(p,std::ios::binary);
#if defined(XAR_RELIC_FULL_UI_PACKET_FIXTURE)
 namespace ui=xar::ck3_11906;
 // Only owning-fixture admission metadata is synthetic; helper Result above
 // is the real production reader/callback-policy result. Both outer serializer
 // and command envelope below are the unchanged shared production functions.
 std::string wire="{\"window_kind\":\"holy_site\",\"subject_id\":"+std::to_string(request.holy_site_id)+
  ",\"operation\":\""+std::string(relic::OperationName(request.operation))+"\"";
 if(request.artifact_id!=relic::absent)wire+=",\"relic_artifact_id\":"+std::to_string(request.artifact_id);
 if(request.slot_index)wire+=",\"relic_slot_index\":"+std::to_string(*request.slot_index);
 if(request.desired_selected)wire+=",\"relic_desired_selected\":"+std::string(*request.desired_selected?"true":"false");
 if(request.frozen_preconditions){
  wire+=",\"relic_expected_preview_sha256\":\""+request.expected_preview_identity_sha256+"\",\"relic_expected_replacing_empty\":"+
   (request.expected_replacing_artifact_id?std::string("false"):std::string("true"));
  if(request.expected_replacing_artifact_id)wire+=",\"relic_expected_replacing_artifact_id\":"+std::to_string(*request.expected_replacing_artifact_id);
  if(request.expected_effective_slot_index)wire+=",\"relic_expected_effective_slot_index\":"+std::to_string(*request.expected_effective_slot_index);
 }
 wire+='}';ui::IngameUiRequestV1 parsed{};
 if(!ui::ParseIngameUiRequestV1(wire,false,parsed)||parsed.relic_action!=request||
  !ui::IsIngameUiRequestSupportedV1(ui::GuiAbiRevisionV1::crozier12004,parsed))throw std::runtime_error("whole native request parser mismatch");
 parsed.connection_generation=71;parsed.native_revision=701;
 ui::IngameUiResultV1 value{};value.gui_abi_revision=ui::GuiAbiRevisionV1::crozier12004;
 value.available=r.available;value.dispatch_invoked=r.dispatch_invoked;value.native_dispatch_attempted=r.native_dispatch_attempted;
 value.verification_pending=r.verification_pending;value.window_exists=true;value.effective_visible=true;value.enabled=true;
 value.subject_id_available=true;value.current_subject_id=site_id;value.date_raw=51394920;value.paused=true;value.played_character_id=static_cast<std::int32_t>(actor_id);
 value.pump_epoch=17;value.thread_id=211;value.application_owner_thread_verified=true;value.gui_owner_binding_verified=true;
 value.gui_context_address=0x100000;value.gui_owner_address=0x200000;value.modal_admission.attempted=true;
 value.modal_admission.header_read=true;value.modal_admission.receivers_verified=true;value.modal_admission.receiver_count=0;
 value.tree.scope_root_name="holy_site_window";value.tree.root_available=true;value.tree.widget_count=1;
 ui::NamedGuiWidgetInspectionV1 widget{};widget.runtime_name="holy_site_window";widget.vtable_rva=0x4000000;widget.effective_visible=true;widget.enabled=true;
 value.tree.widgets.push_back(widget);value.relic_action_requested=true;value.relic_action=r;value.status=r.status;value.unavailable_reason=r.unavailable_reason;
 out<<ui::IngameUiCommandResultFrameV1("relic-ui-typed-fixture",parsed,value,701)<<'\n';
 std::ofstream input(dir/(std::string(name)+".request"),std::ios::binary);input<<wire<<'\n';
#else
 (void)request;
 out<<"{\"owned_fixture\":true,\"original_engine_code_executed\":false,\"action_ready\":false,\"result\":"<<relic::SerializeHolySiteRelicAction12004(r)<<"}\n";
#endif
}
}
int main(int argc,char**argv){try{
 const std::filesystem::path dir=argc>1?argv[1]:"";
 if(!dir.empty()){if(std::filesystem::exists(dir))throw std::runtime_error("refuse existing packet directory");std::filesystem::create_directories(dir);}
 {Fixture f;relic::Result r;Put(f.window.data(),0x110,static_cast<const void*>(&f.slots[1]));Check(f.Run(f.SelectRequest(),r)&&f.select_calls==1&&r.selection_postcondition_observed&&r.after.slot_index==1U,"select preserves slot");Packet(dir,"select-preserves-slot",r,f.SelectRequest());}
 {Fixture f;relic::Result r;Check(f.Run(f.SlotRequest(0,true),r)&&f.toggle_calls==1&&r.after.slot_index==0U,"select requested actual slot");Check(f.Run(f.SlotRequest(0,true),r)&&f.toggle_calls==1&&r.already_in_requested_state&&!r.dispatch_invoked&&!r.native_dispatch_attempted,"desired-selected no duplicate toggle or false dispatch claim");Packet(dir,"slot-already-selected",r,f.SlotRequest(0,true));}
 {Fixture f;relic::Result r;Put(f.window.data(),0x110,static_cast<const void*>(&f.slots[1]));Check(f.Run(f.SlotRequest(0,false),r)&&f.toggle_calls==0&&r.after.slot_index==1U,"clear unselected target is no-op");Check(f.Run(f.SlotRequest(1,false),r)&&f.toggle_calls==1&&!r.after.slot_index,"clear selected target toggles non-null row once");Packet(dir,"slot-clear",r,f.SlotRequest(1,false));}
 {Fixture f;relic::Result r;Check(!f.Run(f.SlotRequest(2,true),r)&&!r.native_dispatch_attempted&&f.toggle_calls==0,"out-of-range actual slot rejected");}
 {Fixture f;relic::Result r;Put(f.window.data(),0x110,static_cast<const void*>(f.foreign.data()));Check(!f.Run(f.SlotRequest(0,true),r)&&!r.native_dispatch_attempted,"foreign selected slot rejected");Packet(dir,"foreign-selected-slot",r,f.SlotRequest(0,true));}
 {Fixture f;relic::Result r;auto q=f.SelectRequest();q.artifact_id^=0x01000000;Check(!f.Run(q,r)&&f.select_calls==0,"stale artifact generation rejected");Packet(dir,"stale-artifact-generation",r,q);}
 {Fixture f;relic::Result r;auto q=f.SelectRequest();q.artifact_id=foreign_id;Check(!f.Run(q,r)&&f.select_calls==0,"resolved world artifact outside GUI source rejected");}
 {Fixture f;relic::Result r;f.admission.modal_admitted=false;Check(!f.Run(f.SelectRequest(),r)&&!r.native_dispatch_attempted,"modal rejects selection");}
 {Fixture f;relic::Result r;f.bindings.source_bound=true;Check(!f.Run(f.SelectRequest(),r)&&!r.native_dispatch_attempted,"loaded source pin failure rejects selection");Packet(dir,"loaded-pin-rejected",r,f.SelectRequest());}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::enshrine);f.bindings.gameplay_action_lane_enabled=false;Check(!f.Run(q,r)&&f.click_calls==0&&f.button_calls==0,"non-opted-in actions hard closed");Packet(dir,"action-closed",r,q);}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::enshrine);f.proof.player_owned_ids_contains_artifact=false;Check(!f.Run(q,r)&&f.click_calls==0,"owner flag alone not ownership list");}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::enshrine);f.proof.artifact_character_owner_matches_player=false;Check(!f.Run(q,r)&&f.click_calls==0,"owned reference alone not actual owner");}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::enshrine);f.proof.preview_observed=false;Check(!f.Run(q,r)&&f.click_calls==0,"missing effect preview rejected");}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::enshrine);q.expected_preview_identity_sha256=std::string(64,'b');Check(!f.Run(q,r)&&f.click_calls==0,"changed frozen preview rejected");}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::enshrine);f.presentation_visible=false;Check(!f.Run(q,r)&&f.click_calls==0,"hidden actual button rejected");Packet(dir,"hidden-button",r,q);}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::enshrine);f.button_allowed=false;Check(!f.Run(q,r)&&f.click_calls==0&&r.original_button_enabled==false,"native final button false rejected");}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::enshrine);f.preview_drift=true;Check(!f.Run(q,r)&&f.click_calls==0,"preview replacement drift rejected before click");Packet(dir,"preview-drift",r,q);}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::enshrine);Check(f.Run(q,r)&&f.click_calls==1&&f.preview_calls==2&&f.presentation_calls==2&&r.verification_pending&&!r.business_outcome_observed&&!r.action_ready,"original click ACK requires independent gameplay readback");Packet(dir,"enshrine-ack-only",r,q);}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::remove);f.proof.site_equipped_slot_member=false;Check(!f.Run(q,r)&&f.click_calls==0,"remove requires actual site equipped member");}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::remove);Check(f.Run(q,r)&&f.click_calls==1&&r.gameplay_command_may_have_been_queued&&!r.business_outcome_observed,"remove ACK not business");Packet(dir,"remove-ack-only",r,q);}
 {Fixture f;relic::Result r;auto q=f.ActionRequest(relic::Operation::enshrine);f.click_returns=false;Check(!f.Run(q,r)&&f.click_calls==1&&r.native_dispatch_attempted&&r.verification_pending&&r.status=="dispatch_result_unknown","unknown callback never retried");Packet(dir,"callback-result-unknown",r,q);}
 {relic::Request r;Check(relic::ParseRelicRequest12004("{\"relic_artifact_id\":2197815299}",100,site_id,r)&&r.artifact_id==artifact_id,"selection parser keeps full ID");
  Check(!relic::ParseRelicRequest12004("{\"relic_artifact_id\":2197815299,\"relic_slot_index\":0}",100,site_id,r),"irrelevant relic fields rejected");
  Check(relic::ParseRelicRequest12004("{\"relic_slot_index\":0,\"relic_desired_selected\":false}",101,site_id,r)&&r.desired_selected==false,"explicit false parsed");
  Check(!relic::ParseRelicRequest12004("{\"relic_slot_index\":0}",101,site_id,r),"missing desired state rejected");
  const std::string json="{\"relic_artifact_id\":2197815299,\"relic_expected_effective_slot_index\":0,\"relic_expected_replacing_empty\":true,\"relic_expected_preview_sha256\":\""+std::string(64,'a')+"\"}";
  Check(relic::ParseRelicRequest12004(json,102,site_id,r)&&r.frozen_preconditions&&!r.expected_replacing_artifact_id,"action parser requires known empty replacement");}
 {const auto b=relic::BindHolySiteRelicActionsImage12004(0x140000000,xar::ck3_12004::kExecutableSha256);
  Check(!b.gameplay_action_lane_enabled&&!b.preview_reader,"production binder never enables actions silently");
  Check(!relic::BindHolySiteRelicActionsImage12004(0x140000000,"foreign").enabled,"foreign build rejected");}
 std::cout<<"{\"status\":\"PASS\",\"checks\":"<<checks<<",\"synthetic_storage\":true,\"injected_dependencies\":true,\"original_engine_code_executed\":false,\"live_qualification\":false,\"business_outcome_observed\":false,\"action_ready\":false}\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
