#include "native_mandatory_choice_gate_v1.hpp"

#include <cassert>
#include <string>

using namespace xar::mandatory_choice_v1;

namespace {
Observation Model() {
  Observation o{};
  o.frame = {226540, 13, 1, 617, 53169792, 100, "episode-1", "snap-1"};
  o.blocking_proof = {BlockerKind::exclusive_modal_blocks_input, true,
                      "stock_modal_receiver_vector_and_input_gate", 0xCAFE};
  o.window_id = "unknown-window";
  o.window_instance_id = "instance-7";
  o.window_type = "generic_choice";
  o.source_identity = "ck3-1.20.0.4-exact-build";
  o.executable_sha256 = std::string(64, 'a');
  o.root_vtable_module_rva = 0x100;
  o.choices_complete = true;
  o.choices = {
      {0x1000, "bottom", "bottom", true, true, true, true,
       "verified_choice_callback", Bounds{30, 200, 100, 20}, {}, 0x200,
       {{0x300, 0x400}}},
      {0x2000, "top", "top", true, true, true, true,
       "verified_choice_callback", Bounds{20, 40, 100, 20}, {}, 0x200,
       {{0x300, 0x400}}},
  };
  return o;
}
struct Nonces {
  int count = 0;
  std::string operator()() {return std::string(32, char('a' + count++));}
};
} // namespace

int main() {
  auto o = Model();
  Nonces nonces{};
  Gate gate{};
  auto issue = [&] {return gate.Query(o, [&] {return nonces();});};
  auto q = issue();
  assert(q.available && q.choices.size() == 2 && q.choices_complete);
  assert(q.blocking_proof.kind == BlockerKind::exclusive_modal_blocks_input);
  assert(q.choices[1].choice_id == "top");
  assert(!q.choices[1].action_token.empty() && q.choices[1].action_token != q.query_id);
  int dispatch_count = 0;
  std::uintptr_t target = 0;
  const auto dispatch = [&](std::uintptr_t value, bool &handled) {
    ++dispatch_count; target = value; handled = true; return true;
  };
  SelectRequest request{q.query_id, q.choices[1].action_token, q.frame,
                        q.window_instance_id};
  auto wrong = request; wrong.action_token = std::string(32, 'z');
  assert(!gate.Select(wrong, [&] {return o;}, dispatch).accepted);
  assert(dispatch_count == 0);
  wrong = request; wrong.expected_frame.native_revision++;
  assert(!gate.Select(wrong, [&] {return o;}, dispatch).accepted);
  assert(dispatch_count == 0);
  auto changed = o; changed.window_instance_id = "instance-8";
  assert(!gate.Select(request, [&] {return changed;}, dispatch).accepted);
  assert(dispatch_count == 0);
  assert(!gate.Select(request, [&] {return o;}, dispatch).accepted);
  q = issue(); request = {q.query_id, q.choices[1].action_token, q.frame,
                          q.window_instance_id};
  auto result = gate.Select(request, [&] {return o;}, dispatch);
  assert(result.accepted && result.dispatch_attempted && result.dispatch_invoked &&
         result.native_handled && result.verification_pending);
  assert(dispatch_count == 1 && target == 0x2000);
  assert(!gate.Select(request, [&] {return o;}, dispatch).accepted);
  assert(dispatch_count == 1);
  q = issue(); request = {q.query_id, q.choices[0].action_token, q.frame,
                          q.window_instance_id};
  auto failed = gate.Select(request, [&] {return o;},
                            [&](std::uintptr_t, bool &) {
                              ++dispatch_count; return false;
                            });
  assert(failed.accepted && failed.dispatch_attempted && !failed.dispatch_invoked &&
         !failed.verification_pending);
  assert(!gate.Select(request, [&] {return o;}, dispatch).accepted);
  assert(dispatch_count == 2);

  o = Model(); o.blocking_proof.verified = false;
  assert(!issue().available);
  o = Model(); o.blocking_proof.kind = BlockerKind::none;
  assert(!issue().available);
  o = Model(); o.choices[1].is_choice = false;
  assert(!issue().available); // close X or arbitrary navigation button
  o = Model(); o.choices_complete = false;
  assert(!issue().available);
  o = Model(); o.choices[0].bounds.reset();
  assert(!issue().available); // multi-choice must have a proven order
  o = Model(); o.choices.erase(o.choices.begin()); o.choices[0].bounds.reset();
  assert(issue().available); // only one visible enabled choice
  o = Model(); o.choices[0].bounds.reset(); o.choices[1].bounds.reset();
  o.choices[0].rendered_index = 1; o.choices[1].rendered_index = 0;
  assert(!issue().available); // integer order alone is not provenance
  o.rendered_order_source = "event_window_rendered_options";
  assert(issue().available); // only if adapter proves rendered order
  o = Model(); o.choices[0].bounds.reset(); o.choices[1].bounds.reset();
  assert(!issue().available);
  o = Model(); o.choices[0].visible = false;
  q = issue(); assert(q.available && q.choices.size() == 2);
  assert(!q.choices[0].visible && q.choices[0].action_token.empty());
  assert(q.choices[1].visible && !q.choices[1].action_token.empty());
  return 0;
}
