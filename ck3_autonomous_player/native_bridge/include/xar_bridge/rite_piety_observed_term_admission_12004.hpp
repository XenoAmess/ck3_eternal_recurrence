#pragma once

#include "xar_bridge/rite_dynamic_call_journal_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>

namespace xar::ck3_12004::piety_price_raw_inputs {

// Copied by the reached dynamic term reader. These operands do not construct
// a physical native context and do not supply a virtual target's value.
struct RitePietyObservedTermExpected12004 {
  std::uintptr_t module_base{}, actor{}, current_rite{};
  std::uint64_t revision{};
  std::uintptr_t definition{}, expression{}, expression_receiver{};
  std::uintptr_t expression_vtable{}, expression_virtual_30{};
  std::optional<std::uint32_t> actor_full_id_raw_u32;
  std::optional<std::uint32_t> actor_context_key_raw_u32;
  std::optional<std::uint32_t> rite_full_id_raw_u32;
  std::optional<std::uint32_t> rite_context_key_raw_u32;
  std::optional<std::uint32_t> rite_link_full_id_raw_u32;
  std::optional<std::uint32_t> rite_link_context_key_raw_u32;
  bool dynamic_prefix_copied{};
};

struct RitePietyObservedTermInputs12004 {
  const RiteDynamicCallJournalSnapshot12004* journal{};
  // Independently copied from the real Begin inputs by the mailbox owner.
  // Equality is copied metadata coherence, never a native event-clock claim.
  RiteDynamicQueryBinding12004 expected_query_binding;
};

struct RitePietyObservedTermAdmission12004 {
  bool admitted{};
  std::optional<std::int64_t> observed_q64_raw;
  const char* reason{"actual_rite_dynamic_term_not_admitted"};
  std::size_t matching_record_count{};
  // Present only for one actual matching vector occurrence. Multiple equal
  // outputs prove agreement, without selecting a unique consumed occurrence.
  std::optional<std::size_t> selected_record_index;
  bool matching_values_agree{};
};

namespace rite_observed_term_detail {
inline bool AddAddress(std::uintptr_t address, std::uintptr_t offset,
                       std::uintptr_t& result) noexcept {
  if (!address || offset >
      (std::numeric_limits<std::uintptr_t>::max)() - address) return false;
  result = address + offset;
  return true;
}
inline bool Resolved(const RiteDynamicResolvedIdentity12004& identity) noexcept {
  return identity.ready && identity.selected_identity.has_value() &&
      *identity.selected_identity != 0 && identity.resolved_full_id.has_value();
}
} // namespace rite_observed_term_detail

// Readonly admission of original375438F's normally returned local signedQ64.
// No extra game-memory reads, virtual invocation, rawRAX substitution or cache.
// Persistent source bookends and actual Finish remain the owning packet's gates.
inline RitePietyObservedTermAdmission12004 AdmitRitePietyObservedTerm12004(
    const RitePietyObservedTermExpected12004& expected,
    const RitePietyObservedTermInputs12004& inputs) noexcept {
  RitePietyObservedTermAdmission12004 out;
  if (!expected.dynamic_prefix_copied || !expected.module_base ||
      !expected.actor || !expected.current_rite || !expected.definition ||
      !expected.expression || !expected.expression_receiver ||
      !expected.expression_vtable || !expected.expression_virtual_30 ||
      !expected.actor_full_id_raw_u32 || !expected.actor_context_key_raw_u32 ||
      !expected.rite_full_id_raw_u32 || !expected.rite_context_key_raw_u32 ||
      !expected.rite_link_full_id_raw_u32 ||
      !expected.rite_link_context_key_raw_u32) {
    out.reason = "actual_rite_dynamic_prefix_incomplete";
    return out;
  }
  std::uintptr_t receiver{}, parent_return{};
  if (!rite_observed_term_detail::AddAddress(expected.expression, 0x8, receiver) ||
      receiver != expected.expression_receiver ||
      !rite_observed_term_detail::AddAddress(expected.module_base,
          kRiteDynamicParentReturnRva12004, parent_return)) {
    out.reason = "actual_rite_dynamic_prefix_address_invalid";
    return out;
  }
  if (!inputs.journal) {
    out.reason = "actual_rite_dynamic_journal_absent";
    return out;
  }
  const auto& journal = *inputs.journal;
  if (!IsBorrowedRiteDynamicSnapshot12004(journal) ||
      !journal.scope_started || journal.scope_closed ||
      !journal.borrowed_scope_identity) {
    out.reason = "actual_rite_dynamic_scope_not_current";
    return out;
  }
  if (journal.source_pin != kRiteDynamicJournalSourcePin12004 ||
      journal.module_base != expected.module_base) {
    out.reason = "actual_rite_dynamic_source_binding_mismatch";
    return out;
  }
  const auto& binding = inputs.expected_query_binding;
  if (!(journal.binding == binding) || !binding.actual_application_query ||
      !binding.mailbox_before_accepted || !binding.owning_thread_id ||
      binding.owning_thread_id != journal.scope_thread_id ||
      !binding.actual_window || !binding.price_payload_identity ||
      !*binding.price_payload_identity ||
      !rite_observed_term_detail::Resolved(binding.first_actor) ||
      !rite_observed_term_detail::Resolved(binding.current_rite) ||
      !rite_observed_term_detail::Resolved(binding.second_actor) ||
      expected.revision != binding.snapshot_revision ||
      expected.actor != *binding.second_actor.selected_identity ||
      expected.current_rite != *binding.current_rite.selected_identity ||
      expected.actor_full_id_raw_u32 != binding.second_actor.resolved_full_id ||
      expected.rite_full_id_raw_u32 != binding.current_rite.resolved_full_id) {
    out.reason = "actual_rite_dynamic_query_inputs_mismatch";
    return out;
  }
  if (journal.allocation_failed || journal.capacity_exceeded ||
      journal.reentrant_callback_rejected || journal.thread_mismatch_observed ||
      journal.dropped_pre_count || journal.unmatched_post_count ||
      journal.occurrences.size() >
          RiteDynamicCallJournalScope12004::maximum_occurrences) {
    out.reason = "actual_rite_dynamic_journal_incomplete";
    return out;
  }

  std::optional<std::int64_t> agreed_value;
  std::optional<std::size_t> unique_index;
  for (std::size_t i = 0; i < journal.occurrences.size(); ++i) {
    const auto& record = journal.occurrences[i];
    if (record.occurrence_index != i ||
        record.borrowed_scope_identity != journal.borrowed_scope_identity ||
        record.pre_thread_id != journal.scope_thread_id) {
      out.reason = "actual_rite_dynamic_occurrence_scope_mismatch";
      return out;
    }
    // An unread returnPC cannot safely classify an occurrence as unrelated.
    if (!record.parent_return_address) {
      out.reason = "actual_rite_dynamic_parent_return_unreadable";
      return out;
    }
    if (*record.parent_return_address != parent_return) continue;
    if (!record.parent_actor || !record.parent_current_rite) {
      out.reason = "actual_rite_dynamic_parent_identity_unreadable";
      return out;
    }
    if (*record.parent_actor != expected.actor ||
        *record.parent_current_rite != expected.current_rite ||
        record.pre.definition_rsi != expected.definition ||
        record.pre.expression_receiver_rcx != expected.expression_receiver ||
        record.pre.vptr_rax != expected.expression_vtable ||
        record.pre.target_r10 != expected.expression_virtual_30) continue;
    if (!record.actor_full_id_raw_u32 || !record.rite_full_id_raw_u32 ||
        !record.actor_context_key_raw_u32 || !record.rite_context_key_raw_u32 ||
        !record.rite_link_full_id_raw_u32 ||
        !record.rite_link_context_key_raw_u32) {
      out.reason = "actual_rite_dynamic_context_operands_unreadable";
      return out;
    }
    if (record.actor_full_id_raw_u32 != expected.actor_full_id_raw_u32 ||
        record.rite_full_id_raw_u32 != expected.rite_full_id_raw_u32 ||
        record.actor_context_key_raw_u32 != expected.actor_context_key_raw_u32 ||
        record.rite_context_key_raw_u32 != expected.rite_context_key_raw_u32 ||
        record.rite_link_full_id_raw_u32 != expected.rite_link_full_id_raw_u32 ||
        record.rite_link_context_key_raw_u32 !=
            expected.rite_link_context_key_raw_u32) continue;

    ++out.matching_record_count;
    std::uintptr_t context{}, description{};
    if (!record.pre.helper_rbp || !record.parent_term_output ||
        !*record.parent_term_output || !record.parent_detail ||
        *record.parent_detail != 0 || record.pre.native_r9_r15 != 0 ||
        !record.description_pointer ||
        !rite_observed_term_detail::AddAddress(record.pre.helper_out_rdi,
            0x10, context) || context != record.pre.native_context_r12 ||
        !rite_observed_term_detail::AddAddress(context, 0x28, description) ||
        description != *record.description_pointer) {
      out.reason = "actual_rite_dynamic_native_call_arguments_unavailable";
      return out;
    }
    if (record.pairing_ambiguous || !record.normal_return_observed ||
        record.observed_normal_return_rva != kRiteDynamicNormalReturnRva12004 ||
        !record.post_thread_id ||
        *record.post_thread_id != journal.scope_thread_id) {
      out.reason = "actual_rite_dynamic_normal_pair_unavailable";
      return out;
    }
    if (!record.post_actor_full_id_raw_u32 ||
        !record.post_rite_full_id_raw_u32 ||
        record.post_actor_full_id_raw_u32 != expected.actor_full_id_raw_u32 ||
        record.post_rite_full_id_raw_u32 != expected.rite_full_id_raw_u32) {
      out.reason = "actual_rite_dynamic_post_full_id_mismatch";
      return out;
    }
    if (!record.local_output_raw_q64) {
      out.reason = "actual_rite_dynamic_local_q64_unreadable";
      return out;
    }
    if (agreed_value && *agreed_value != *record.local_output_raw_q64) {
      out.reason = "actual_rite_dynamic_matching_q64_disagree";
      return out;
    }
    agreed_value = record.local_output_raw_q64;
    if (out.matching_record_count == 1) unique_index = i;
    else unique_index.reset();
  }
  if (!agreed_value || !out.matching_record_count) {
    out.reason = "actual_rite_dynamic_matching_occurrence_absent";
    return out;
  }
  out.observed_q64_raw = agreed_value;
  out.selected_record_index = unique_index;
  out.matching_values_agree = true;
  out.admitted = true;
  out.reason = out.matching_record_count == 1
      ? "actual_rite_dynamic_unique_normal_q64_observed"
      : "actual_rite_dynamic_matching_normal_q64_agreement";
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
