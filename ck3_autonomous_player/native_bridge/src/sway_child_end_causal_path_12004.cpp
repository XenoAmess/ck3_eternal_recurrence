#include "xar_bridge/sway_child_end_causal_path_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <windows.h>

namespace xar::ck3_12004 {
namespace {
thread_local SwayToastParentScope12004 *current_parent = nullptr;

bool SameStamp(const SwayToastParentStamp12004 &a,
               const SwayToastParentStamp12004 &b) noexcept {
  return a.observer_session_identity == b.observer_session_identity &&
      a.owner_thread_id == b.owner_thread_id &&
      a.toast_invocation_id == b.toast_invocation_id &&
      a.source_sequence == b.source_sequence;
}
bool OrderedPath(const SwayChildNativeReturns12004 &trace) noexcept {
  if (!trace.observed || trace.native_returns_truncated || trace.count < 3 ||
      trace.count > trace.rvas.size() || trace.rvas[0] != kSwayChildEndReturn12004)
    return false;
  bool dispatcher = false;
  for (std::size_t i = 1; i < trace.count; ++i) {
    // Only the nearest Toast child edge is admissible; do not skip it to use
    // an older outer branch whose source was not the current dynamic parent.
    if (trace.rvas[i] == kSwayToastChildReturn12004) return dispatcher;
    if (trace.rvas[i] == kSwayChildDispatcherReturn12004) dispatcher = true;
  }
  return false;
}
} // namespace

SwayToastParentScope12004::SwayToastParentScope12004(
    const SwayToastParentStamp12004 &stamp,
    const SwayCompleteBranchSource12004 &source, bool source_captured,
    std::string_view sha, std::uintptr_t original) noexcept
    : previous_(current_parent), stamp_(stamp),
      actor_(source.actor_character_id), target_(source.target_character_id),
      scheme_(source.scheme_id) {
  matched_ = source_captured && source.executing_input_observed &&
      sha == kExecutableSha256 && original == 0x2CC8470 &&
      stamp.observer_session_identity != 0 && stamp.toast_invocation_id != 0 &&
      stamp.source_sequence != 0 && stamp.owner_thread_id == GetCurrentThreadId() &&
      source.root.type == 4 && source.owner.type == 4 && source.target.type == 4 &&
      source.scheme.type == 9 && actor_ != 0xFFFFFFFFu &&
      target_ != 0xFFFFFFFFu && scheme_ != 0xFFFFFFFFu &&
      static_cast<std::uint32_t>(source.root.payload) == actor_ &&
      static_cast<std::uint32_t>(source.owner.payload) == actor_ &&
      static_cast<std::uint32_t>(source.target.payload) == target_ &&
      static_cast<std::uint32_t>(source.scheme.payload) == scheme_;
  current_parent = this;
}

SwayToastParentScope12004::~SwayToastParentScope12004() noexcept {
  // Normal stack nesting restores exactly the previous parent. A violated
  // ownership/LIFO contract must not leave a stale usable dynamic scope.
  current_parent = current_parent == this ? previous_ : nullptr;
}

bool CaptureSwayChildNativeReturns12004(std::uintptr_t base, std::size_t size,
                                      SwayChildNativeReturns12004 &out) noexcept {
  out = {};
  const auto *parent = current_parent;
  if (parent == nullptr || !parent->matched_ || base == 0 ||
      size <= kSwayChildDispatcherReturn12004 ||
      parent->stamp_.owner_thread_id != GetCurrentThreadId()) return false;
  out.parent = parent->stamp_;
  std::array<void *, 64> addresses{};
  const auto count = CaptureStackBackTrace(0, static_cast<DWORD>(addresses.size()),
                                         addresses.data(), nullptr);
  for (USHORT i = 0; i < count; ++i) {
    const auto address = reinterpret_cast<std::uintptr_t>(addresses[i]);
    if (address < base || address - base >= size) continue;
    if (out.count == out.rvas.size()) {
      out.native_returns_truncated = true;
      break;
    }
    out.rvas[out.count++] = address - base;
    // The closest native Toast tail is sufficient; retaining callers outside
    // this parent would add no causal information and could borrow an outer.
    if (out.rvas[out.count - 1] == kSwayToastChildReturn12004) break;
  }
  out.observed = out.count != 0;
  return out.observed;
}

bool JoinSwayChildEndCausalPath12004(const SwayEndInvocation12004 &end,
    const SwayChildNativeReturns12004 &trace,
    SwayChildEndCausalRelation12004 &out) noexcept {
  out = {};
  const auto *parent = current_parent;
  if (parent == nullptr || !parent->matched_ ||
      parent->stamp_.owner_thread_id != GetCurrentThreadId() ||
      !SameStamp(parent->stamp_, trace.parent) || !OrderedPath(trace) ||
      end.stamp.observer_session_identity != parent->stamp_.observer_session_identity ||
      end.stamp.owner_thread_id != parent->stamp_.owner_thread_id ||
      end.stamp.invocation_id == 0 ||
      !end.stamp.incoming_return_address_observed ||
      end.stamp.caller_return_rva != kSwayChildEndReturn12004 ||
      !end.original_forwarded_once || !end.original_returned ||
      !end.source.executing_source_observed ||
      end.source.input_root_scope_kind != 9 ||
      end.source.actor_character_id != parent->actor_ ||
      end.source.target_character_id != parent->target_ ||
      end.source.scheme_id != parent->scheme_ ||
      end.scheme_instance_generation != (parent->scheme_ >> 24)) return false;
  std::uintptr_t original = 0;
  if (end.source.source_class == SwayEndSourceClass12004::authored_end_scheme_false_execute)
    original = kSwayEndInvocationOriginalRvas12004[1];
  else if (end.source.source_class == SwayEndSourceClass12004::authored_end_scheme_true_execute)
    original = kSwayEndInvocationOriginalRvas12004[2];
  else return false;
  out.relationship_observed = true;
  out.source_contract_version = 1;
  out.observer_session_identity = parent->stamp_.observer_session_identity;
  out.owner_thread_id = parent->stamp_.owner_thread_id;
  out.branch_source_sequence = parent->stamp_.source_sequence;
  out.parent_toast_invocation_id = parent->stamp_.toast_invocation_id;
  out.end_original_invocation_id = end.stamp.invocation_id;
  out.end_original_rva = original;
  out.actor_character_id = parent->actor_;
  out.target_character_id = parent->target_;
  out.scheme_id = parent->scheme_;
  out.scheme_instance_generation = end.scheme_instance_generation;
  out.native_returns = trace;
  return true;
}

} // namespace xar::ck3_12004
