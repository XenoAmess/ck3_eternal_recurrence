#include "xar_bridge/person_transfer_postimage_capture_12004.hpp"

#include <limits>
#include <utility>

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view kVersion = "1.20.0.4";
constexpr std::string_view kHash =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

std::optional<std::uintptr_t> At(std::uintptr_t model,
                                std::uintptr_t offset) noexcept {
  if (model == 0 || model > std::numeric_limits<std::uintptr_t>::max() - offset)
    return std::nullopt;
  return model + offset;
}

bool ReadRows(void *context, const void *source, void *target,
              std::size_t bytes) noexcept {
  const auto &bindings = *static_cast<PersonTransferPostimageBindings12004 *>(context);
  return bindings.read_memory && bindings.read_memory(
      bindings.read_context, reinterpret_cast<std::uintptr_t>(source), target, bytes);
}

bool EventEqual(const PersonInstalledTransferEvent12004 &a,
                const PersonInstalledTransferEvent12004 &b) noexcept {
  return a.clock_identity == b.clock_identity && a.sequence == b.sequence &&
         a.thread_id == b.thread_id;
}

bool ScopeEqual(const PersonTransferSnapshotScope12004 &a,
                const PersonTransferSnapshotScope12004 &b) noexcept {
  return EventEqual(a.occurrence, b.occurrence) && EventEqual(a.event, b.event) &&
         a.phase == b.phase && a.side == b.side &&
         a.model_identity == b.model_identity &&
         a.original_return_rva == b.original_return_rva;
}

PersonTransferSnapshotScope12004 Scope(
    const PersonInstalledTransferStage12004 &stage,
    PersonTransferSnapshotPhase12004 phase,
    PersonTransferSnapshotSide12004 side) noexcept {
  return {stage.before_event,
          phase == PersonTransferSnapshotPhase12004::before_original
              ? stage.before_event : stage.completed_event,
          phase, side,
          side == PersonTransferSnapshotSide12004::a
              ? stage.model_a_identity : stage.model_b_identity,
          stage.original_return_rva};
}

PersonTransferModelPhysicalSnapshot12004 CaptureModel(
    const PersonTransferPostimageBindings12004 &bindings,
    const PersonTransferSnapshotScope12004 &scope) noexcept {
  PersonTransferModelPhysicalSnapshot12004 result;
  result.scope = scope;
  // Keep scope visible even when an operand cannot be copied.
  result.block78_keys.scope = scope;
  result.blocke0_values.scope = scope;
  result.block248_raw64.scope = scope;
  if (!bindings.enabled || !bindings.read_memory) {
    result.reason = "physical_exact_build_binding_unavailable";
    return result;
  }
  if (scope.model_identity == 0) {
    result.reason = "physical_model_unavailable";
    return result;
  }
  auto borrowed = bindings;
  const auto row_bindings = BindPersonTransferBlock10Inputs12004(
      kVersion, kHash, ReadRows, &borrowed);
  // The retained row API budgets row count, while the public aggregate limits
  // consistently budget bytes. Its header arithmetic also needs this guard.
  if (At(scope.model_identity, 0x1F))
    result.block10_rows = ReadPersonTransferBlock10ForModel12004(
        row_bindings, scope.model_identity,
        bindings.limits.row_payload_bytes / kPersonTransferBlock10RowBytes12004);
  else {
    result.block10_rows.model_identity = scope.model_identity;
    result.block10_rows.reason = "row_header_address_unrepresentable";
  }
  try {
    if (At(scope.model_identity, 0x87))
      result.block78_keys = CapturePersonTransferKeysSnapshot12004(
          *At(scope.model_identity, 0x78), scope,
          bindings.read_context, bindings.read_memory, bindings.limits.key_payload_bytes);
    else
      result.block78_keys.raw.reason = "key_header_address_unrepresentable";
  } catch (...) {
    // Clearing is allocation-free: reporting an allocation failure must not
    // itself allocate inside this noexcept observer boundary.
    result.block78_keys.raw.reason.clear();
  }
  try {
    // The retained E0 copier accepts a model and uses these native operands.
    // Guard its unsigned header arithmetic before handing it the receiver.
    if (At(scope.model_identity, 0xF7))
      result.blocke0_values = CapturePersonTransferValuesSnapshot12004(
          scope, bindings.read_context, bindings.read_memory,
          bindings.limits.value_payload_bytes);
    else
      result.blocke0_values.raw.values_reason = "value_header_address_unrepresentable";
  } catch (...) {
    result.blocke0_values.raw.values_reason.clear();
  }
  try {
    // This retained copier already checks each field address independently.
    result.block248_raw64 = CapturePersonTransferBlock248Snapshot12004(
        scope, bindings.read_context, bindings.read_memory,
        bindings.limits.block248_payload_bytes);
  } catch (...) {
    result.block248_raw64.raw.reason.clear();
  }
  result.four_descriptors_copy_complete = result.block10_rows.descriptor_ready &&
      result.block78_keys.descriptor_copy_complete &&
      result.blocke0_values.descriptor_copy_complete &&
      result.block248_raw64.descriptor_copy_complete;
  result.four_payloads_copy_complete = result.block10_rows.rows_ready &&
      result.block78_keys.payload_copy_complete &&
      result.blocke0_values.payload_copy_complete &&
      result.block248_raw64.payload_copy_complete;
  result.four_operands_copy_complete = result.four_descriptors_copy_complete &&
      result.four_payloads_copy_complete;
  result.reason = result.four_operands_copy_complete
      ? "four_physical_operands_copied" : "one_or_more_physical_operands_partial";
  return result;
}

bool ModelScopeMatches(const PersonTransferModelPhysicalSnapshot12004 &copy,
                       const PersonTransferSnapshotScope12004 &expected) noexcept {
  return ScopeEqual(copy.scope, expected) &&
      ScopeEqual(copy.block78_keys.scope, expected) &&
      ScopeEqual(copy.blocke0_values.scope, expected) &&
      ScopeEqual(copy.block248_raw64.scope, expected);
}

template <class T> bool HeaderComplete(const T &copy) noexcept {
  return copy.data_identity.has_value() && copy.capacity_i32.has_value() &&
         copy.count_i32.has_value();
}

template <class T> std::optional<bool> HeaderEqual(const T &a, const T &b) noexcept {
  if (!HeaderComplete(a) || !HeaderComplete(b)) return std::nullopt;
  return a.data_identity == b.data_identity && a.capacity_i32 == b.capacity_i32 &&
         a.count_i32 == b.count_i32;
}

std::optional<bool> Raw248HeaderEqual(
    const PersonTransferBlock248Snapshot12004 &a,
    const PersonTransferBlock248Snapshot12004 &b) noexcept {
  auto equal = HeaderEqual(a, b);
  if (!equal || !a.allocator_identity || !b.allocator_identity ||
      !a.allocator_dispatch_vtable_identity || !b.allocator_dispatch_vtable_identity)
    return std::nullopt;
  return *equal && a.allocator_identity == b.allocator_identity &&
      a.allocator_dispatch_vtable_identity == b.allocator_dispatch_vtable_identity;
}

template <class T> std::optional<bool> VectorEqual(
    const std::optional<T> &a, const std::optional<T> &b) noexcept {
  if (!a || !b) return std::nullopt;
  return *a == *b;
}

std::optional<bool> Both(std::optional<bool> a, std::optional<bool> b) noexcept {
  if (!a || !b) return std::nullopt;
  return *a && *b;
}

template <class T, class DescriptorReady, class PayloadReady,
          class DescriptorEqual, class PayloadEqual>
PersonTransferPhysicalBlockComparison12004 CompareBlock(
    const T &pre_a, const T &pre_b, const T &post_a, const T &post_b,
    bool comparison_allowed, DescriptorReady descriptor_ready,
    PayloadReady payload_ready, DescriptorEqual descriptor_equal,
    PayloadEqual payload_equal) noexcept {
  PersonTransferPhysicalBlockComparison12004 result;
  result.four_descriptors_copy_complete = descriptor_ready(pre_a) &&
      descriptor_ready(pre_b) && descriptor_ready(post_a) && descriptor_ready(post_b);
  result.four_payloads_copy_complete = payload_ready(pre_a) && payload_ready(pre_b) &&
      payload_ready(post_a) && payload_ready(post_b);
  result.four_operands_copy_complete = result.four_descriptors_copy_complete &&
      result.four_payloads_copy_complete;
  if (!comparison_allowed) return result;
  result.a_descriptor_equals_b_before = descriptor_equal(pre_b, post_a);
  result.b_descriptor_equals_a_before = descriptor_equal(pre_a, post_b);
  result.descriptor_cross_equal = Both(result.a_descriptor_equals_b_before,
                                      result.b_descriptor_equals_a_before);
  if (payload_ready(pre_b) && payload_ready(post_a))
    result.a_payload_equals_b_before = payload_equal(pre_b, post_a);
  if (payload_ready(pre_a) && payload_ready(post_b))
    result.b_payload_equals_a_before = payload_equal(pre_a, post_b);
  result.payload_cross_equal = Both(result.a_payload_equals_b_before,
                                   result.b_payload_equals_a_before);
  return result;
}

std::optional<bool> PcCountEqual(const PersonTransferModelPhysicalSnapshot12004 &copy) noexcept {
  if (!copy.block78_keys.raw.count_i32 || !copy.blocke0_values.raw.count_i32)
    return std::nullopt;
  return *copy.block78_keys.raw.count_i32 == *copy.blocke0_values.raw.count_i32;
}
} // namespace

PersonTransferPostimageBindings12004 BindPersonTransferPostimageInputs12004(
    std::string_view version, std::string_view executable_sha256,
    PersonTransferSnapshotRead12004 read_memory, void *read_context,
    PersonTransferSnapshotLimits12004 limits) noexcept {
  if (version != kVersion || executable_sha256 != kHash || !read_memory) return {};
  return {true, read_context, read_memory, limits};
}

PersonTransferPhysicalPair12004 CapturePersonTransferPhysicalPair12004(
    const PersonTransferPostimageBindings12004 &bindings,
    const PersonInstalledTransferStage12004 &stage,
    PersonTransferSnapshotPhase12004 phase) noexcept {
  PersonTransferPhysicalPair12004 result;
  result.configured = bindings.enabled && bindings.read_memory;
  result.phase = phase;
  if (!stage.observed || stage.original_return_rva != kPersonInstalledTransferCallerReturnRva12004 ||
      (phase == PersonTransferSnapshotPhase12004::after_original && !stage.original_returned)) {
    result.a.scope = Scope(stage, phase, PersonTransferSnapshotSide12004::a);
    result.b.scope = Scope(stage, phase, PersonTransferSnapshotSide12004::b);
    result.a.reason = result.b.reason = "physical_original_boundary_unobserved";
    return result;
  }
  result.a = CaptureModel(bindings, Scope(stage, phase, PersonTransferSnapshotSide12004::a));
  result.b = CaptureModel(bindings, Scope(stage, phase, PersonTransferSnapshotSide12004::b));
  return result;
}

PersonTransferPhysicalComparison12004 ComparePersonTransferPhysicalPostimage12004(
    const PersonInstalledTransferStage12004 &stage,
    const PersonTransferPhysicalPair12004 &before,
    const PersonTransferPhysicalPair12004 &after) noexcept {
  PersonTransferPhysicalComparison12004 result;
  result.original_transfer_returned = stage.observed && stage.original_called &&
      stage.original_returned && stage.original_return_rva == kPersonInstalledTransferCallerReturnRva12004;
  result.model_pair_matches_transfer = stage.model_a_identity != 0 && stage.model_b_identity != 0 &&
      before.a.scope.model_identity == stage.model_a_identity && after.a.scope.model_identity == stage.model_a_identity &&
      before.b.scope.model_identity == stage.model_b_identity && after.b.scope.model_identity == stage.model_b_identity;
  result.snapshot_scopes_match_transfer = before.configured && after.configured &&
      before.phase == PersonTransferSnapshotPhase12004::before_original &&
      after.phase == PersonTransferSnapshotPhase12004::after_original &&
      ModelScopeMatches(before.a, Scope(stage, before.phase, PersonTransferSnapshotSide12004::a)) &&
      ModelScopeMatches(before.b, Scope(stage, before.phase, PersonTransferSnapshotSide12004::b)) &&
      ModelScopeMatches(after.a, Scope(stage, after.phase, PersonTransferSnapshotSide12004::a)) &&
      ModelScopeMatches(after.b, Scope(stage, after.phase, PersonTransferSnapshotSide12004::b));
  if (stage.before_event.clock_identity && stage.completed_event.clock_identity &&
      stage.before_event.thread_id && stage.completed_event.thread_id) {
    result.same_clock_and_thread = stage.before_event.clock_identity == stage.completed_event.clock_identity &&
        stage.before_event.thread_id == stage.completed_event.thread_id;
    if (*result.same_clock_and_thread && stage.before_event.sequence != 0 && stage.completed_event.sequence != 0)
      result.completion_after_begin = stage.completed_event.sequence > stage.before_event.sequence;
  }
  result.same_original_observation_ready = result.original_transfer_returned &&
      result.model_pair_matches_transfer && result.snapshot_scopes_match_transfer &&
      result.same_clock_and_thread.value_or(false) && result.completion_after_begin.value_or(false);
  const bool compare = result.original_transfer_returned && result.model_pair_matches_transfer &&
      result.snapshot_scopes_match_transfer;
  result.block10_rows = CompareBlock(before.a.block10_rows, before.b.block10_rows,
      after.a.block10_rows, after.b.block10_rows, compare,
      [](const auto &x) { return x.descriptor_ready; },
      [](const auto &x) { return x.rows_ready && x.rows.has_value(); },
      [](const auto &a, const auto &b) { return HeaderEqual(a,b); },
      [](const auto &, const auto &) -> std::optional<bool> { return std::nullopt; });
  if (compare) {
    const auto rows = ComparePersonTransferBlock10Postimage12004(
        before.a.block10_rows, before.b.block10_rows,
        after.a.block10_rows, after.b.block10_rows);
    result.block10_rows.a_payload_equals_b_before = rows.a_after_rows_equal_b_before;
    result.block10_rows.b_payload_equals_a_before = rows.b_after_rows_equal_a_before;
    result.block10_rows.payload_cross_equal = rows.row_postimage_matches_exchange;
  }
  result.block78_keys = CompareBlock(before.a.block78_keys, before.b.block78_keys,
      after.a.block78_keys, after.b.block78_keys, compare,
      [](const auto &x) { return x.descriptor_copy_complete; },
      [](const auto &x) { return x.payload_copy_complete && x.raw.keys_u16.has_value(); },
      [](const auto &a, const auto &b) { return HeaderEqual(a.raw,b.raw); },
      [](const auto &a, const auto &b) { return VectorEqual(a.raw.keys_u16,b.raw.keys_u16); });
  result.blocke0_values = CompareBlock(before.a.blocke0_values, before.b.blocke0_values,
      after.a.blocke0_values, after.b.blocke0_values, compare,
      [](const auto &x) { return x.descriptor_copy_complete; },
      [](const auto &x) { return x.payload_copy_complete && x.values_q64_raw_bits.has_value(); },
      [](const auto &a, const auto &b) { return HeaderEqual(a.raw,b.raw); },
      [](const auto &a, const auto &b) { return VectorEqual(a.values_q64_raw_bits,b.values_q64_raw_bits); });
  result.block248_raw64 = CompareBlock(before.a.block248_raw64, before.b.block248_raw64,
      after.a.block248_raw64, after.b.block248_raw64, compare,
      [](const auto &x) { return x.descriptor_copy_complete; },
      [](const auto &x) { return x.payload_copy_complete && x.raw.ordered_payload_raw64.has_value(); },
      [](const auto &a, const auto &b) { return Raw248HeaderEqual(a.raw,b.raw); },
      [](const auto &, const auto &) -> std::optional<bool> { return std::nullopt; });
  if (compare) {
    // Retain the qualified tail comparator's actual-original/model attribution
    // as well as its independently known directionals. The new scope gate
    // precedes it; generic descriptor diagnostics remain independent.
    try {
      const auto tail = ComparePersonTransferBlock24812004(stage,
          before.a.block248_raw64.raw, before.b.block248_raw64.raw,
          after.a.block248_raw64.raw, after.b.block248_raw64.raw);
      result.block248_raw64.a_payload_equals_b_before = tail.post_a_equals_pre_b;
      result.block248_raw64.b_payload_equals_a_before = tail.post_b_equals_pre_a;
      result.block248_raw64.payload_cross_equal = tail.two_way_payload_equality;
    } catch (...) {
      // An auxiliary string allocation must not erase other block facts.
    }
  }
  result.four_block_operand_copies_complete = result.block10_rows.four_operands_copy_complete &&
      result.block78_keys.four_operands_copy_complete && result.blocke0_values.four_operands_copy_complete &&
      result.block248_raw64.four_operands_copy_complete;
  result.four_block_payloads_cross_equal = Both(Both(result.block10_rows.payload_cross_equal,
      result.block78_keys.payload_cross_equal), Both(result.blocke0_values.payload_cross_equal,
      result.block248_raw64.payload_cross_equal));
  result.four_block_payload_comparison_ready = result.four_block_payloads_cross_equal.has_value();
  result.four_block_payload_exchange_observed = result.same_original_observation_ready &&
      result.four_block_payloads_cross_equal.value_or(false);
  if (stage.preparation.observed && stage.preparation.preparation_model_identity &&
      stage.preparation.preparation_context_identity && stage.preparation_owner_matches_before) {
    const auto b_context = At(before.b.scope.model_identity, 0x10);
    result.preparation_descriptor_matches_before_b = b_context.has_value() &&
        stage.preparation.preparation_capture_complete &&
        stage.preparation.preparation_capture_sequence != 0 &&
        *stage.preparation.preparation_model_identity == before.b.scope.model_identity &&
        *stage.preparation.preparation_context_identity == *b_context &&
        *stage.preparation_owner_matches_before;
  }
  if (stage.preparation.preparation_capture_thread_id &&
      stage.preparation.preparation_completion_thread_id && stage.before_event.thread_id) {
    result.preparation_threads_match_original =
        *stage.preparation.preparation_capture_thread_id == *stage.before_event.thread_id &&
        *stage.preparation.preparation_completion_thread_id == *stage.before_event.thread_id;
  }
  result.b_before_pc_key_value_counts_equal = PcCountEqual(before.b);
  result.a_after_pc_key_value_counts_equal = PcCountEqual(after.a);
  if (!result.original_transfer_returned) result.reason = "physical_original_return_unobserved";
  else if (!result.model_pair_matches_transfer) result.reason = "physical_receiver_pair_mismatch";
  else if (!result.snapshot_scopes_match_transfer) result.reason = "physical_occurrence_scope_mismatch";
  else if (!result.same_original_observation_ready) result.reason = "physical_clock_or_thread_order_unproven";
  else if (!result.four_block_payload_comparison_ready) result.reason = "physical_payload_comparison_partial";
  else if (!*result.four_block_payloads_cross_equal) result.reason = "physical_payload_postimage_differs";
  else result.reason = "same_original_four_block_payload_exchange_observed";
  return result;
}

PersonTransferPhysicalPostimage12004 JoinPersonTransferPhysicalPostimage12004(
    const PersonInstalledTransferStage12004 &stage,
    PersonTransferPhysicalPair12004 before,
    PersonTransferPhysicalPair12004 after) noexcept {
  auto comparison = ComparePersonTransferPhysicalPostimage12004(stage, before, after);
  return {std::move(before), std::move(after), comparison};
}
} // namespace xar::ck3_12004
