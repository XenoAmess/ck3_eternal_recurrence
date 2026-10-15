#include "native_mandatory_choice_controller_v1.hpp"
#include "ck3_12004_modal_choice_port_v1.hpp"
#include "native_modal_choice_hint_policy_v1.hpp"

#include <cassert>
#include <map>

using namespace xar::mandatory_choice_v1;

struct Fixture : NativeModalPort {
  ModalRoot root{0x10, 0x20, 0x100, "modal", "instance-1", "modal",
                 "exact-source", true, true, std::string(64,'a'), 0x100};
  Fixture() {
             widgets[0x200].vtable_module_rva = 0x200;}
  std::map<std::uintptr_t,Widget> widgets{
      {0x100, {0x100,0,0x10,"modal",true,true,false,false,{0x200},0x100}},
      {0x200, {0x200,0x100,0x10,"choice",true,true,true,false,{},0x200}},
  };
  bool ReadModalRoot(ModalRoot &out) override {out = root; return true;}
  bool ReadWidget(std::uintptr_t address, Widget &out) override {
    auto it = widgets.find(address); if (it == widgets.end()) return false;
    out = it->second; return true;
  }
  bool CallbackAdmitted(std::uintptr_t) override {return true;}
  bool ReadCallbackIdentity(std::uintptr_t,
                            std::vector<CallbackIdentity> &out) override {
    out = {{0x300, 0x400}}; return true;
  }
  bool ReadRect(std::uintptr_t, Bounds &out) override {
    out = {10,20,100,30}; return true;
  }
};

int main() {
  xar::ck3_11906::MainThreadExecutionStampV1 owner{};
  owner.thread_id = 321;
  owner.tls_initialized = 1;
  owner.tls_main_thread_marker = 1;
  owner.tls_context = 0x10;
  owner.game_state = 0x20;
  owner.jomini_state = 0x30;
  owner.paused = false;
  assert(OwnerModalHintObservationAllowedV1(owner,321));
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  owner.pump_epoch = 7;
  owner.tls_initialized_flag_address = 0x40;
  mailbox.owner_thread_id.store(321);
  mailbox.owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs);
  assert(OwnerModalChoiceCommandAllowedV1(mailbox,owner,321));
  assert(!OwnerModalChoiceCommandAllowedV1(mailbox,owner,322));
  mailbox.owner_verified_pump_epochs.store(0);
  assert(!OwnerModalChoiceCommandAllowedV1(mailbox,owner,321));
  mailbox.owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumOwnerVerifiedPumpEpochs);
  owner.tls_main_thread_marker = 0;
  assert(!OwnerModalChoiceCommandAllowedV1(mailbox,owner,321));
  owner.tls_main_thread_marker = 1;
  assert(SemanticModalHintPublicationAllowedV1(true,true));
  owner.paused = true;
  assert(OwnerModalHintObservationAllowedV1(owner,321));
  owner.thread_id = 322;
  assert(!OwnerModalHintObservationAllowedV1(owner,321));
  assert(!SemanticModalHintPublicationAllowedV1(false,true));
  assert(ClassifyTypedRootPathsV1({0x10,0x100},{0x10,0x100}) ==
         TypedWindowRelationStatus::same_typed_root);
  assert(ClassifyTypedRootPathsV1({0x20,0x10,0x100},{0x10,0x100}) ==
         TypedWindowRelationStatus::same_typed_root);
  assert(ClassifyTypedRootPathsV1({0x20,0x100},{0x30,0x100}) ==
         TypedWindowRelationStatus::independent_top_modal);
  assert(ClassifyTypedRootPathsV1({0x20,0x100},{0x30,0x200}) ==
         TypedWindowRelationStatus::unknown);
  assert(ClassifyTypedRootPathsV1({0x20,0x100},{0x30,0x100,0x100}) ==
         TypedWindowRelationStatus::unknown);
  Fixture port{};
  Frame actual{226540,13,1,617,53169792,100,"episode","snapshot"};
  int nonce = 0, calls = 0;
  Controller controller(port,[&] {return std::optional<Frame>{actual};},
                        [&] {return std::string(32, char('a' + nonce++));},
                        [&](std::uintptr_t target, bool &handled) {
                          assert(target == 0x200); ++calls; handled = true;
                          return true;
                        });
  auto q = controller.Query();
  assert(q.available && q.choices.size() == 1);
  SelectRequest req{q.query_id,q.choices[0].action_token,q.frame,
                    q.window_instance_id};
  actual.date_raw++;
  assert(!controller.Select(req).accepted && calls == 0);
  actual.date_raw--;
  q = controller.Query();
  req = {q.query_id,q.choices[0].action_token,q.frame,q.window_instance_id};
  port.root.window_instance_id = "instance-2";
  assert(!controller.Select(req).accepted && calls == 0);
  port.root.window_instance_id = "instance-1";
  q = controller.Query();
  req = {q.query_id,q.choices[0].action_token,q.frame,q.window_instance_id};
  auto selected = controller.Select(req);
  assert(selected.accepted && selected.dispatch_invoked &&
         selected.verification_pending && calls == 1);
  assert(!controller.Select(req).accepted && calls == 1);
  return 0;
}
