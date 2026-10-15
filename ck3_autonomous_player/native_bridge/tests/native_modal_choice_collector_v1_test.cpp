#include "native_modal_choice_collector_v1.hpp"

#include <cassert>
#include <map>

using namespace xar::mandatory_choice_v1;

struct Fixture : NativeModalPort {
  ModalRoot root{0x10, 0x20, 0x100, "unknown_modal", "instance-1",
                 "unknown_modal", "exact-12004-source", true, true,
                 std::string(64,'a'), 0x100};
  Fixture() {
             widgets[0x300].vtable_module_rva = 0x200;
             widgets[0x400].vtable_module_rva = 0x200;}
  std::map<std::uintptr_t, Widget> widgets{
      {0x100, {0x100, 0, 0x10, "modal", true, true, false, false,
               {0x200, 0x300, 0x400}, 0x100}},
      {0x200, {0x200, 0x100, 0x10, "close_button", true, true, true,
               true, {}, 0x200}},
      {0x300, {0x300, 0x100, 0x10, "unknown_second", true, true, true,
               false, {}, 0x200}},
      {0x400, {0x400, 0x100, 0x10, "unknown_first", true, true, true,
               false, {}, 0x200}},
  };
  bool callback_ok = true, geometry_ok = true, second_read_changed = false;
  int root_reads = 0;
  bool ReadModalRoot(ModalRoot &out) override {
    out = root; ++root_reads;
    if (second_read_changed && root_reads == 2)
      out.window_instance_id = "instance-2";
    return true;
  }
  bool ReadWidget(std::uintptr_t address, Widget &out) override {
    auto it = widgets.find(address);
    if (it == widgets.end()) return false;
    out = it->second; return true;
  }
  bool CallbackAdmitted(std::uintptr_t) override {return callback_ok;}
  bool ReadCallbackIdentity(std::uintptr_t,
                            std::vector<CallbackIdentity> &out) override {
    out = {{0x300, 0x400}}; return true;
  }
  bool ReadRect(std::uintptr_t address, Bounds &out) override {
    if (!geometry_ok) return false;
    out = address == 0x400 ? Bounds{10, 30, 100, 20}
                            : Bounds{20, 100, 100, 20};
    return true;
  }
};

int main() {
  Frame frame{226540, 13, 1, 617, 53169792, 100, "episode", "snapshot"};
  std::string reason;
  Fixture f{};
  auto o = CollectTopModalChoices(frame, f, reason);
  assert(o && reason.empty() && o->choices_complete);
  assert(o->blocking_proof.kind == BlockerKind::exclusive_modal_blocks_input);
  assert(o->choices.size() == 2); // close decoration excluded
  assert(o->choices[0].choice_id == "2:unknown_second");
  assert(o->choices[1].choice_id == "3:unknown_first");
  assert(o->choices[1].bounds->top < o->choices[0].bounds->top);
  f = {}; f.root.blocks_input = false;
  assert(!CollectTopModalChoices(frame, f, reason));
  f = {}; f.callback_ok = false;
  assert(!CollectTopModalChoices(frame, f, reason));
  f = {}; f.geometry_ok = false;
  assert(!CollectTopModalChoices(frame, f, reason));
  f = {}; f.geometry_ok = false; f.widgets[0x300].enabled = false;
  o = CollectTopModalChoices(frame, f, reason);
  assert(o && o->choices.size() == 2 &&
         !o->choices[0].enabled && o->choices[1].enabled &&
         !o->choices[1].bounds);
  f = {}; f.widgets[0x400].parent = 0x200;
  assert(!CollectTopModalChoices(frame, f, reason));
  f = {}; f.second_read_changed = true;
  assert(!CollectTopModalChoices(frame, f, reason));
  f = {}; f.widgets[0x100].children.push_back(0x300);
  assert(!CollectTopModalChoices(frame, f, reason));
  return 0;
}
