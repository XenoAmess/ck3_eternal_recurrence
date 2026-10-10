#include "xar_bridge/sway_child_end_causal_path_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <windows.h>

#include <iostream>
#include <stdexcept>
#include <thread>

using namespace xar::ck3_12004;

namespace {
unsigned checks = 0;
void Check(bool passed, const char *name) {
  ++checks;
  if (!passed) throw std::runtime_error(name);
}

SwayCompleteBranchSource12004 Branch(std::uint32_t scheme = 0x8A001234u) {
  SwayCompleteBranchSource12004 out{};
  out.actor_character_id = 0x03001001u;
  out.target_character_id = 0x06001002u;
  out.scheme_id = scheme;
  out.root.type = out.owner.type = out.target.type = 4;
  out.scheme.type = 9;
  out.root.payload = out.owner.payload = out.actor_character_id;
  out.target.payload = out.target_character_id;
  out.scheme.payload = out.scheme_id;
  out.executing_input_observed = true;
  return out;
}

SwayToastParentStamp12004 Stamp(std::uint64_t invocation = 100,
                              std::uint64_t sequence = 80) {
  return {0x1729u, GetCurrentThreadId(), invocation, sequence};
}

SwayEndInvocation12004 End(const SwayCompleteBranchSource12004 &branch,
                          const SwayToastParentStamp12004 &parent) {
  SwayEndInvocation12004 out{};
  out.stamp = {parent.observer_session_identity, parent.owner_thread_id, 200,
               true, kSwayChildEndReturn12004};
  out.source.source_class =
      SwayEndSourceClass12004::authored_end_scheme_true_execute;
  out.source.actor_character_id = branch.actor_character_id;
  out.source.target_character_id = branch.target_character_id;
  out.source.scheme_id = branch.scheme_id;
  out.source.input_root_scope_kind = 9;
  out.source.executing_source_observed = true;
  out.scheme_instance_generation = branch.scheme_id >> 24;
  out.original_forwarded_once = out.original_returned = true;
  return out;
}

// Synthetic copied native return witnesses, never an actual CK3 occurrence.
// Extra frames represent nested native scoped-effect bodies, whose unknown
// semantics are not invented; the three exact admitted edges still appear.
SwayChildNativeReturns12004 Returns(const SwayToastParentStamp12004 &stamp) {
  SwayChildNativeReturns12004 out{};
  out.parent = stamp;
  out.observed = true;
  out.count = 5;
  out.rvas[0] = kSwayChildEndReturn12004;
  out.rvas[1] = 0x3300100;
  out.rvas[2] = kSwayChildDispatcherReturn12004;
  out.rvas[3] = 0x3300200;
  out.rvas[4] = kSwayToastChildReturn12004;
  return out;
}

void Reject(const SwayEndInvocation12004 &end,
            const SwayChildNativeReturns12004 &returns, const char *name) {
  SwayChildEndCausalRelation12004 relation{};
  relation.relationship_observed = true;
  relation.parent_toast_invocation_id = 987;
  Check(!JoinSwayChildEndCausalPath12004(end, returns, relation), name);
  Check(!relation.relationship_observed &&
        relation.parent_toast_invocation_id == 0 &&
        relation.end_original_invocation_id == 0,
        "rejected relation clears reused output");
}

void Positive(const SwayEndInvocation12004 &end,
              const SwayChildNativeReturns12004 &returns,
              const SwayToastParentStamp12004 &parent,
              std::uintptr_t expected_original) {
  SwayChildEndCausalRelation12004 relation{};
  Check(JoinSwayChildEndCausalPath12004(end, returns, relation),
        "ordered copied native path joins guarded parent");
  Check(relation.relationship_observed && relation.source_contract_version == 1,
        "source relationship version is explicit");
  Check(relation.observer_session_identity == parent.observer_session_identity &&
        relation.owner_thread_id == parent.owner_thread_id &&
        relation.branch_source_sequence == parent.source_sequence &&
        relation.parent_toast_invocation_id == parent.toast_invocation_id &&
        relation.end_original_invocation_id == end.stamp.invocation_id &&
        relation.end_original_rva == expected_original,
        "specific parent/source sequence/original identity survives copy");
  Check(relation.scheme_id == end.source.scheme_id &&
        relation.scheme_instance_generation == (end.source.scheme_id >> 24) &&
        relation.actor_character_id == end.source.actor_character_id &&
        relation.target_character_id == end.source.target_character_id,
        "full identities and generation survive copy");
  Check(!end.causal_parent_observed && end.causal_parent_invocation_id == 0 &&
        !end.source.native_terminal_state_observed &&
        !end.source.native_terminal_transition_observed,
        "relationship does not mutate producer or manufacture terminal facts");
}

void Compound() {
  const auto branch = Branch();
  const auto parent = Stamp();
  const auto end = End(branch, parent);
  const auto trace = Returns(parent);
  Reject(end, trace, "no active Toast scope has no parent");
  {
    SwayToastParentScope12004 outer(parent, branch, true, kExecutableSha256,
                                  0x2CC8470);
    Positive(end, trace, parent, 0x2D11AD0);
    auto false_end = end;
    false_end.source.source_class =
        SwayEndSourceClass12004::authored_end_scheme_false_execute;
    Positive(false_end, trace, parent, 0x2D11B30);

    auto altered = trace;
    altered.rvas[0] = 0x2D67C05;
    Reject(end, altered, "nearby return point is not the typed end caller");
    altered = trace;
    altered.rvas[2] = 0x3765780;
    Reject(end, altered, "old inherited dispatcher is not actual reached edge");
    altered = trace;
    altered.rvas[1] = kSwayToastChildReturn12004;
    Reject(end, altered, "cannot skip nearest Toast to borrow older outer edge");
    altered = trace;
    altered.rvas[4] = 0x2CC93D0;
    Reject(end, altered, "active extent without exact Toast CALL return rejects");
    altered = trace;
    altered.native_returns_truncated = true;
    Reject(end, altered, "truncated witness is unavailable");
    altered = trace;
    altered.observed = false;
    Reject(end, altered, "unobserved witness is unavailable");
    altered = trace;
    altered.count = altered.rvas.size() + 1;
    Reject(end, altered, "oversized copied trace rejects safely");
    altered = trace;
    ++altered.parent.source_sequence;
    Reject(end, altered, "neighbor source counter does not establish cause");
    altered = trace;
    ++altered.parent.toast_invocation_id;
    Reject(end, altered, "neighbor invocation cannot borrow current extent");

    auto wrong_end = end;
    ++wrong_end.stamp.observer_session_identity;
    Reject(wrong_end, trace, "previous observer session is unavailable");
    wrong_end = end;
    ++wrong_end.stamp.owner_thread_id;
    Reject(wrong_end, trace, "different owning thread is unavailable");
    wrong_end = end;
    wrong_end.stamp.invocation_id = 0;
    Reject(wrong_end, trace, "unallocated original ID is unavailable");
    wrong_end = end;
    wrong_end.stamp.incoming_return_address_observed = false;
    Reject(wrong_end, trace, "helper return point cannot replace direct caller");
    wrong_end = end;
    ++wrong_end.stamp.caller_return_rva;
    Reject(wrong_end, trace, "direct entry caller must agree with copied path");
    wrong_end = end;
    wrong_end.source.scheme_id ^= 0x01000000u;
    wrong_end.scheme_instance_generation = wrong_end.source.scheme_id >> 24;
    Reject(wrong_end, trace, "reused low24 scheme slot is not same full instance");
    wrong_end = end;
    ++wrong_end.scheme_instance_generation;
    Reject(wrong_end, trace, "generation must agree with full scheme ID");
    wrong_end = end;
    ++wrong_end.source.actor_character_id;
    Reject(wrong_end, trace, "foreign owner is unavailable");
    wrong_end = end;
    ++wrong_end.source.target_character_id;
    Reject(wrong_end, trace, "foreign target is unavailable");
    wrong_end = end;
    wrong_end.source.input_root_scope_kind = 4;
    Reject(wrong_end, trace, "end requires actual scheme root kind9");
    wrong_end = end;
    wrong_end.source.executing_source_observed = false;
    Reject(wrong_end, trace, "unavailable original source does not join");
    wrong_end = end;
    wrong_end.original_forwarded_once = false;
    Reject(wrong_end, trace, "unforwarded original cannot join");
    wrong_end = end;
    wrong_end.original_returned = false;
    Reject(wrong_end, trace, "unreturned original cannot be published completed");
    wrong_end = end;
    wrong_end.source.source_class = SwayEndSourceClass12004::end_scheme_command_execute;
    Reject(wrong_end, trace, "manual Stop original is not the child slot24 edge");

    // The actual original can be associated even when its post state/frame is
    // unavailable. Consumer23 must separately require its terminal predicates.
    Check(!end.post_frame_observed && !end.source.post_read_succeeded,
          "missing post fixture is explicit");
    Positive(end, trace, parent, 0x2D11AD0);

    {
      const auto inner_stamp = Stamp(101, 81);
      SwayToastParentScope12004 ignored(inner_stamp, branch, false,
                                       kExecutableSha256, 0x2CC8470);
      Reject(end, trace, "ignored nested Toast blocks borrowing outer source");
      SwayChildNativeReturns12004 captured{};
      Check(!CaptureSwayChildNativeReturns12004(1, 0x4000000, captured) &&
            !captured.observed && captured.parent.toast_invocation_id == 0,
            "ignored nested Toast cannot produce return witness");
    }
    Positive(end, trace, parent, 0x2D11AD0);
    {
      const auto inner_branch = Branch(0x8B004321u);
      const auto inner_stamp = Stamp(102, 82);
      SwayToastParentScope12004 nested(inner_stamp, inner_branch, true,
                                      kExecutableSha256, 0x2CC8470);
      const auto inner_end = End(inner_branch, inner_stamp);
      const auto inner_trace = Returns(inner_stamp);
      Reject(end, trace, "matching inner parent cannot use outer trace stamp");
      Positive(inner_end, inner_trace, inner_stamp, 0x2D11AD0);
    }
    Positive(end, trace, parent, 0x2D11AD0);
    try {
      const auto inner_stamp = Stamp(103, 83);
      SwayToastParentScope12004 exception_scope(inner_stamp, branch, false,
                                               kExecutableSha256, 0x2CC8470);
      throw std::runtime_error("synthetic original exception");
    } catch (const std::runtime_error &) {}
    Positive(end, trace, parent, 0x2D11AD0);

    bool other_thread_joined = true;
    std::thread worker([&] {
      SwayChildEndCausalRelation12004 relation{};
      other_thread_joined = JoinSwayChildEndCausalPath12004(end, trace, relation);
    });
    worker.join();
    Check(!other_thread_joined, "TLS extent cannot cross a worker thread");

    SwayChildNativeReturns12004 unavailable{};
    Check(!CaptureSwayChildNativeReturns12004(0, 0, unavailable) &&
          !unavailable.observed, "missing image binding cannot capture");
    SwayChildNativeReturns12004 local_stack{};
    Check(CaptureSwayChildNativeReturns12004(
              reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
              0x4000000, local_stack),
          "Windows stack collector copies this synthetic executable frames");
    Reject(end, local_stack, "synthetic executable stack cannot claim CK3 path");
  }
  Reject(end, trace, "returned Toast destroys dynamic parent");
  {
    auto bad_branch = branch;
    bad_branch.scheme.payload ^= 0x01000000u;
    SwayToastParentScope12004 bad(parent, bad_branch, true, kExecutableSha256,
                                 0x2CC8470);
    Reject(end, trace, "branch named scheme token must agree with full ID");
  }
  {
    SwayToastParentScope12004 bad(parent, branch, true, "old-image", 0x2CC8470);
    Reject(end, trace, "old executable pin cannot admit association");
  }
  {
    SwayToastParentScope12004 bad(parent, branch, true, kExecutableSha256,
                                 0x2CC8490);
    Reject(end, trace, "legacy Toast original cannot admit association");
  }
}
} // namespace

int main() {
  try {
    Compound();
    std::cout << "PASS sway_child_end_causal_path_12004 " << checks
              << " checks; synthetic copied-fact and Windows local stack fixture;"
                 " no CK3/runtime/terminal sample\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "FAIL " << e.what() << '\n';
    return 1;
  }
}
