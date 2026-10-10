#include "xar_bridge/construction_context_predicate_2c25010_12004.hpp"

namespace xar::ck3_12004::construction_owner_mode3 {

ConstructionContextPredicateV1 ReadConstructionContextPredicate2C25010V1(
    const RawReceiverAccessV1 &access, const AggregateRawReceiverV1 &receiver,
    const ReturnedObject28C2DF0Result12004 &selector,
    std::uint64_t snapshot_revision,
    const ReadContextPredicateChildrenV1 &children) noexcept {
  ConstructionContextPredicateV1 result{};
  result.inputs.frame_key = snapshot_revision;
  result.inputs.slots_pointer = receiver.slots_pointer;
  result.inputs.raw_receiver_pointer = receiver.returned_receiver_pointer;
  result.inputs.selector_object_pointer = selector.returned_object;
  const auto fail = [&](ContextPredicateFailureV1 failure) {
    result.failure = failure;
    return result;
  };
  const auto finish = [&](bool value, ContextPredicatePathV1 path) {
    result.value = value;
    result.path = path;
    return result;
  };
  if (!access.exact_12004_bound)
    return fail(ContextPredicateFailureV1::exact_build);
  if (access.read_memory == nullptr)
    return fail(ContextPredicateFailureV1::read_callback);
  if (!receiver.observed || !selector.source_ready ||
      receiver.returned_receiver_pointer == 0 || selector.returned_object == 0 ||
      selector.input_receiver != receiver.returned_receiver_pointer ||
      selector.frame_key != snapshot_revision)
    return fail(ContextPredicateFailureV1::copied_operand_binding);
  // Actual 246934B reloads the first qword of the original slots receiver.
  if (!RawReceiverReadV1(access, receiver.slots_pointer, 0,
                        result.inputs.first_pointer))
    return fail(ContextPredicateFailureV1::first_pointer);
  bool child_value = false;
  if (children.read_30a6080 == nullptr ||
      !children.read_30a6080(children.context, access, result.inputs,
                            selector.returned_object, result.inputs.first_pointer,
                            child_value))
    return fail(ContextPredicateFailureV1::child_30a6080);
  result.child_30a6080_value = child_value;
  if (child_value)
    return finish(true, ContextPredicatePathV1::first_child_true);

  // Actual 2C25033 global; full ID is read only when storage is nonnull.
  if (!RawReceiverReadV1(access, access.module_base, 0x5D1E2F8,
                        result.registry_storage_pointer))
    return fail(ContextPredicateFailureV1::registry_storage);
  if (result.registry_storage_pointer != 0) {
    std::uint32_t full_id = 0;
    if (!RawReceiverReadV1(access, receiver.returned_receiver_pointer, 0xB4,
                          full_id))
      return fail(ContextPredicateFailureV1::registry_id);
    result.registry_full_id_raw = full_id;
    // Same low24/stride16/+8 pointer rule as 06; this registry's identity is
    // the full uint32 at object+8, as the actual 2C25063 comparison requires.
    if (!ReadRawReceiverRegistryV1(access, result.registry_storage_pointer,
                                  full_id, 8, 0,
                                  result.selected_registry_object_pointer,
                                  result.registry_full_id_matched))
      return fail(ContextPredicateFailureV1::registry_lookup);
  }
  if (!result.registry_full_id_matched &&
      !RawReceiverReadV1(access, access.module_base, 0x5C67670,
                        result.selected_registry_object_pointer))
    return fail(ContextPredicateFailureV1::registry_fallback);
  if (!RawReceiverAddV1(result.selected_registry_object_pointer, 0x8D8,
                       result.collection_pointer))
    return fail(ContextPredicateFailureV1::collection_address);
  if (children.read_a11cc0 == nullptr ||
      !children.read_a11cc0(children.context, access, result.inputs,
                            result.collection_pointer, result.inputs.first_pointer,
                            child_value))
    return fail(ContextPredicateFailureV1::child_a11cc0);
  result.child_a11cc0_value = child_value;
  if (child_value)
    return finish(true, ContextPredicatePathV1::collection_child_true);

  if (children.read_28bfc50 == nullptr ||
      !children.read_28bfc50(children.context, access, result.inputs,
                            receiver.returned_receiver_pointer,
                            result.late_receiver_pointer))
    return fail(ContextPredicateFailureV1::child_28bfc50);
  if (!RawReceiverReadV1(access, result.late_receiver_pointer, 0x1C0,
                        result.late_context_pointer))
    return fail(ContextPredicateFailureV1::late_context);
  // EAX=-1 for null context is an observed native branch, not missing data.
  std::uint32_t late_id = 0xFFFFFFFFu;
  if (result.late_context_pointer != 0 &&
      !RawReceiverReadV1(access, result.late_context_pointer, 0x1B8, late_id))
    return fail(ContextPredicateFailureV1::late_ids);
  result.late_context_id_raw = late_id;
  std::uint32_t receiver_id = 0;
  if (!RawReceiverReadV1(access, receiver.returned_receiver_pointer, 0x18,
                        receiver_id))
    return fail(ContextPredicateFailureV1::late_ids);
  result.raw_receiver_id_raw = receiver_id;
  // Actual cmp/jne compares DWORD bit patterns; no signed or validity gate.
  if (late_id != receiver_id)
    return finish(false, ContextPredicatePathV1::late_id_mismatch_false);
  if (children.read_d2be00 == nullptr ||
      !children.read_d2be00(children.context, access, result.inputs,
                            result.singleton_pointer))
    return fail(ContextPredicateFailureV1::child_d2be00);
  if (children.read_31c1d10 == nullptr ||
      !children.read_31c1d10(children.context, access, result.inputs,
                            result.singleton_pointer, result.inputs.first_pointer,
                            child_value))
    return fail(ContextPredicateFailureV1::child_31c1d10);
  result.child_31c1d10_value = child_value;
  return finish(child_value, child_value ? ContextPredicatePathV1::last_child_true
                                         : ContextPredicatePathV1::last_child_false);
}

} // namespace xar::ck3_12004::construction_owner_mode3
