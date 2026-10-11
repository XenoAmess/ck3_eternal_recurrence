#include "xar_bridge/rite_dynamic_call_journal_12004.hpp"

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>

#include <limits>
#include <utility>

namespace xar::ck3_12004 {
namespace {

thread_local RiteDynamicCallJournalScope12004 *g_borrowed_scope = nullptr;

std::uint32_t CurrentThread() noexcept {
  return static_cast<std::uint32_t>(::GetCurrentThreadId());
}

void Increment(std::size_t &value) noexcept {
  if (value != (std::numeric_limits<std::size_t>::max)()) ++value;
}

template<class T>
void CopyField(const piety_price_raw_inputs::PietyPriceNumericAccess12004 &access,
               std::uintptr_t base, std::size_t offset,
               std::optional<T> &output) noexcept {
  T value{};
  if (piety_price_raw_inputs::ReadPietyPriceNumericField12004(
          access, base, offset, value)) output = value;
}

bool IsParentReturn(const RiteDynamicCallJournalSnapshot12004 &snapshot,
                    const RiteDynamicCallOccurrence12004 &record) noexcept {
  return snapshot.module_base &&
      kRiteDynamicParentReturnRva12004 <=
          (std::numeric_limits<std::uintptr_t>::max)() - snapshot.module_base &&
      record.parent_return_address == std::optional<std::uintptr_t>{
          snapshot.module_base + kRiteDynamicParentReturnRva12004};
}

} // namespace

RiteDynamicCallJournalScope12004::RiteDynamicCallJournalScope12004(
    const piety_price_raw_inputs::PietyPriceNumericAccess12004 &access,
    const RiteDynamicQueryBinding12004 &binding) noexcept : access_(access) {
  snapshot_.binding = binding;
  snapshot_.module_base = access.module_base;
  snapshot_.borrowed_scope_identity = reinterpret_cast<std::uintptr_t>(this);
  snapshot_.scope_thread_id = CurrentThread();
  if (!access.exact_12004_bound || !access.guarded_read || !access.module_base ||
      !binding.actual_application_query || !binding.mailbox_before_accepted ||
      !binding.owning_thread_id ||
      binding.owning_thread_id != snapshot_.scope_thread_id) {
    snapshot_.thread_mismatch_observed = binding.owning_thread_id &&
        binding.owning_thread_id != snapshot_.scope_thread_id;
    return;
  }
  try {
    // One finite allocation before original execution; callbacks never grow it.
    snapshot_.occurrences.reserve(maximum_occurrences);
  } catch (...) {
    snapshot_.allocation_failed = true;
    return;
  }
  previous_ = g_borrowed_scope;
  g_borrowed_scope = this;
  attached_ = true;
  snapshot_.scope_started = true;
}

RiteDynamicCallJournalScope12004::~RiteDynamicCallJournalScope12004() noexcept {
  Close();
}

const RiteDynamicCallJournalSnapshot12004 &
RiteDynamicCallJournalScope12004::Snapshot() const noexcept {
  return snapshot_;
}

bool RiteDynamicCallJournalScope12004::IsBorrowedCurrentScope() const noexcept {
  return attached_ && !snapshot_.scope_closed && g_borrowed_scope == this &&
      snapshot_.scope_thread_id == CurrentThread();
}

void RiteDynamicCallJournalScope12004::Close() noexcept {
  if (snapshot_.scope_thread_id != CurrentThread()) {
    snapshot_.thread_mismatch_observed = true;
    return;
  }
  if (attached_) {
    if (g_borrowed_scope == this) {
      g_borrowed_scope = previous_;
    } else {
      // Same-thread early close of an outer scope detaches its link without
      // changing the current inner scope or leaving a dangling previous link.
      for (auto *scope = g_borrowed_scope; scope; scope = scope->previous_) {
        if (scope->previous_ == this) {
          scope->previous_ = previous_;
          break;
        }
      }
    }
    attached_ = false;
    previous_ = nullptr;
  }
  snapshot_.scope_closed = true;
}

RiteDynamicCallJournalSnapshot12004
RiteDynamicCallJournalScope12004::TakeSnapshot() noexcept {
  if (snapshot_.scope_thread_id != CurrentThread()) {
    snapshot_.thread_mismatch_observed = true;
    return {};
  }
  Close();
  return std::move(snapshot_);
}

void RiteDynamicCallJournalScope12004::CapturePre(
    const RiteDynamicPrecallRegisters12004 &registers) noexcept {
  if (!IsBorrowedCurrentScope()) {
    snapshot_.thread_mismatch_observed = true;
    return;
  }
  if (in_callback_) {
    snapshot_.reentrant_callback_rejected = true;
    Increment(snapshot_.dropped_pre_count);
    return;
  }
  in_callback_ = true;
  bool duplicate = false;
  for (std::size_t i = 0; i < snapshot_.occurrences.size(); ++i) {
    if (pending_[i] &&
        snapshot_.occurrences[i].pre.helper_rbp == registers.helper_rbp) {
      snapshot_.occurrences[i].pairing_ambiguous = true;
      duplicate = true;
    }
  }
  if (!registers.helper_rbp ||
      snapshot_.occurrences.size() >= maximum_occurrences) {
    if (snapshot_.occurrences.size() >= maximum_occurrences)
      snapshot_.capacity_exceeded = true;
    Increment(snapshot_.dropped_pre_count);
    in_callback_ = false;
    return;
  }
  RiteDynamicCallOccurrence12004 record;
  record.occurrence_index = snapshot_.occurrences.size();
  record.borrowed_scope_identity = snapshot_.borrowed_scope_identity;
  record.pre_thread_id = CurrentThread();
  record.pre = registers;
  record.pairing_ambiguous = duplicate;
  CopyField(access_, registers.helper_rbp, 0x7F, record.description_pointer);
  CopyField(access_, registers.helper_rbp, 0x57, record.parent_return_address);
  // The saved-register slots are actor/Rite/output only for this exact parent.
  // Calls from other helpers retain register/return provenance without guessing
  // that their saved pointer belongs to a Character or current Rite.
  if (IsParentReturn(snapshot_, record)) {
    CopyField(access_, registers.helper_rbp, 0x2F, record.parent_actor);
    CopyField(access_, registers.helper_rbp, 0x67, record.parent_current_rite);
    CopyField(access_, registers.helper_rbp, 0x6F, record.parent_term_output);
    CopyField(access_, registers.helper_rbp, 0x37, record.parent_detail);
    if (record.parent_actor)
      CopyField(access_, *record.parent_actor, 0x18,
                record.actor_full_id_raw_u32);
    if (record.parent_current_rite) {
      CopyField(access_, *record.parent_current_rite, 0x8,
                record.rite_full_id_raw_u32);
      CopyField(access_, *record.parent_current_rite, 0x4B8,
                record.rite_link_full_id_raw_u32);
    }
    // These literal source operands already belong to the existing readonly
    // term prefix. Copying a cell never claims equivalence to all R12 bytes.
    CopyField(access_, access_.module_base, 0x5D4BF0C,
              record.actor_context_key_raw_u32);
    CopyField(access_, access_.module_base, 0x5D4C2CC,
              record.rite_context_key_raw_u32);
    CopyField(access_, access_.module_base, 0x5D4BE98,
              record.rite_link_context_key_raw_u32);
  }
  try {
    snapshot_.occurrences.push_back(std::move(record));
    pending_[snapshot_.occurrences.size() - 1] = true;
  } catch (...) {
    snapshot_.allocation_failed = true;
    Increment(snapshot_.dropped_pre_count);
  }
  in_callback_ = false;
}

void RiteDynamicCallJournalScope12004::CapturePost(
    std::uintptr_t helper_rbp, std::uint64_t returned_rax) noexcept {
  if (!IsBorrowedCurrentScope()) {
    snapshot_.thread_mismatch_observed = true;
    return;
  }
  if (in_callback_) {
    snapshot_.reentrant_callback_rejected = true;
    Increment(snapshot_.unmatched_post_count);
    return;
  }
  in_callback_ = true;
  std::size_t count = 0;
  std::size_t match = 0;
  for (std::size_t i = 0; i < snapshot_.occurrences.size(); ++i) {
    if (pending_[i] && snapshot_.occurrences[i].pre.helper_rbp == helper_rbp) {
      ++count;
      match = i;
    }
  }
  if (count != 1 || snapshot_.occurrences[match].pairing_ambiguous) {
    Increment(snapshot_.unmatched_post_count);
    for (std::size_t i = 0; i < snapshot_.occurrences.size(); ++i) {
      if (pending_[i] && snapshot_.occurrences[i].pre.helper_rbp == helper_rbp) {
        snapshot_.occurrences[i].pairing_ambiguous = true;
        pending_[i] = false;
      }
    }
    in_callback_ = false;
    return;
  }
  auto &record = snapshot_.occurrences[match];
  pending_[match] = false;
  record.post_thread_id = CurrentThread();
  // Only40's exact3754392 post window invokes this callback. The original CALL
  // has returned; this does not imply an effect, a specific target store, or a
  // successful numerical read. rawRAX is recorded even when local copy fails.
  record.normal_return_observed = true;
  record.observed_normal_return_rva = kRiteDynamicNormalReturnRva12004;
  record.raw_returned_rax = returned_rax;
  CopyField(access_, helper_rbp, 0x5F, record.local_output_raw_q64);
  if (IsParentReturn(snapshot_, record)) {
    if (record.parent_actor)
      CopyField(access_, *record.parent_actor, 0x18,
                record.post_actor_full_id_raw_u32);
    if (record.parent_current_rite)
      CopyField(access_, *record.parent_current_rite, 0x8,
                record.post_rite_full_id_raw_u32);
  }
  in_callback_ = false;
}

void CaptureRiteDynamicPrecall12004(
    void *, const RiteDynamicPrecallRegisters12004 &registers) noexcept {
  if (g_borrowed_scope) g_borrowed_scope->CapturePre(registers);
}

void CaptureRiteDynamicPostcall12004(
    void *, std::uintptr_t helper_rbp, std::uint64_t raw_returned_rax) noexcept {
  if (g_borrowed_scope)
    g_borrowed_scope->CapturePost(helper_rbp, raw_returned_rax);
}

bool IsBorrowedRiteDynamicSnapshot12004(
    const RiteDynamicCallJournalSnapshot12004 &snapshot) noexcept {
  return g_borrowed_scope && g_borrowed_scope->IsBorrowedCurrentScope() &&
      &g_borrowed_scope->snapshot_ == &snapshot;
}

} // namespace xar::ck3_12004
