// Included inside the current-person collector anonymous namespace after the
// paired Properties reader. Only physical inputs and known early AL1 branches
// are evaluated locally; generic native/scripted evaluators are never called.
const void *ListPredicate2530dd0Pointer(std::uint64_t value) noexcept {
  return reinterpret_cast<const void *>(static_cast<std::uintptr_t>(value));
}
bool ListPredicate2530dd0Resolve(const ContextSourceBindingsV1 &b,
    game::ContextSourceListPredicate2530dd0RowV1 &row) {
  const auto &binding = b.list_predicate_2530dd0;
  const auto storage = Read<const void *>(b, binding.registry_storage_slot);
  if (!storage) {
    row.reason = "list_predicate_registry_storage_unavailable";
    return false;
  }
  if (*storage) {
    const auto capacity = Read<std::uint32_t>(b, *storage, 0x2C);
    if (!capacity) {
      row.reason = "list_predicate_registry_capacity_unavailable";
      return false;
    }
    const auto index = *row.key_u32 & 0xFFFFFFU;
    if (index < *capacity) {
      const auto table = Read<const void *>(b, *storage, 0x20);
      if (!table || !*table) {
        row.reason = "list_predicate_registry_table_unavailable";
        return false;
      }
      const auto candidate = Read<std::uint64_t>(
          b, *table, static_cast<std::size_t>(index) * 16 + 8);
      if (!candidate) {
        row.reason = "list_predicate_registry_candidate_unavailable";
        return false;
      }
      if (*candidate != 0) {
        const auto full_id = Read<std::uint32_t>(
            b, ListPredicate2530dd0Pointer(*candidate), 0x10);
        if (!full_id) {
          row.reason = "list_predicate_registry_full_id_unavailable";
          return false;
        }
        if (*full_id == *row.key_u32) {
          row.selected_object = candidate;
          row.selected_full_id_u32 = full_id;
          row.used_fallback = false;
          row.resolution_selection = "registry_full_id";
          return true;
        }
      }
    }
  }
  row.used_fallback = true;
  row.resolution_selection = "native_fallback";
  row.selected_object = Read<std::uint64_t>(b, binding.registry_fallback_slot);
  if (!row.selected_object) {
    row.reason = "list_predicate_native_fallback_pointer_unavailable";
    return false;
  }
  return true;
}
void ListPredicate2530dd0ObserveRow(const ContextSourceBindingsV1 &b,
    const void *character, game::ContextSourceListPredicate2530dd0RowV1 &row) {
  if (!ListPredicate2530dd0Resolve(b, row)) return;
  const auto *selected = ListPredicate2530dd0Pointer(*row.selected_object);
  row.predicate_receiver = Read<std::uint64_t>(b, selected, 0x490);
  if (!row.predicate_receiver) {
    row.reason = "list_predicate_receiver_pointer_unavailable";
    return;
  }
  const auto *receiver = ListPredicate2530dd0Pointer(*row.predicate_receiver);
  row.magic_u32 = Read<std::uint32_t>(b, receiver, 0x38);
  if (!row.magic_u32) {
    row.reason = "list_predicate_receiver_magic_unavailable";
    return;
  }
  if (*row.magic_u32 != 0x4744624FU) row.predicate_result = true;
  else {
    row.condition_count_raw_i32 = Read<std::int32_t>(b, receiver, 0x15C);
    if (!row.condition_count_raw_i32) {
      row.reason = "list_predicate_condition_field_unavailable";
      return;
    }
    if (*row.condition_count_raw_i32 == 0) row.predicate_result = true;
    else {
      auto &scope = row.scope_inputs.emplace();
      scope.root_scope_kind_u32 = 4U;
      scope.root_character_full_id_u32 = Read<std::uint32_t>(b, character, 0x18);
      scope.named_scope_kind_u32 = 31U;
      if (!row.selected_full_id_u32)
        row.selected_full_id_u32 = Read<std::uint32_t>(b, selected, 0x10);
      scope.named_selected_full_id_u32 = row.selected_full_id_u32;
      scope.named_binding_key_i32 = Read<std::int32_t>(
          b, b.list_predicate_2530dd0.named_binding_key_slot);
      scope.trigger_object = static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(
          Offset(receiver, 0x110)));
      scope.trigger_vtable = Read<std::uint64_t>(b, receiver, 0x110);
      if (scope.trigger_vtable && *scope.trigger_vtable != 0)
        scope.trigger_evaluator_function = Read<std::uint64_t>(
            b, ListPredicate2530dd0Pointer(*scope.trigger_vtable), 0xC8);
      row.reason = "list_predicate_nonzero_condition_evaluator_unclosed";
      return;
    }
  }
  row.pc_selection = "selected_d8";
  row.properties = Properties(b, Offset(selected, 0xD8));
  row.ready = PropertiesReady(*row.properties);
  if (!row.ready) row.reason = "list_predicate_consumed_properties_unavailable";
}
game::ContextSourceListPredicate2530dd0InputsV1 ListPredicate2530dd0Inputs(
    const ContextSourceBindingsV1 &b, const void *character,
    std::int32_t character_id) {
  game::ContextSourceListPredicate2530dd0InputsV1 out{};
  out.character_id = character_id;
  const auto &binding = b.list_predicate_2530dd0;
  out.default_header_guard_raw = Read<std::int32_t>(b, binding.default_header_guard_slot);
  const auto scratch = Read<const void *>(b, character, 0x1B0);
  if (!scratch) {
    out.reason = "list_predicate_scratch_pointer_unavailable";
    return out;
  }
  out.scratch_present = *scratch != nullptr;
  const auto *header = *scratch ? Offset(*scratch, 0x458) : binding.default_inline_header;
  out.header_selection = *scratch ? "held_scratch_458" : "static_default_54e7180";
  // The caller demands the actual +40 pointer before +4C, including at zero.
  const auto data = Read<const void *>(b, header, 0x40);
  if (data) out.source_array_present = *data != nullptr;
  out.source_count_raw = Read<std::int32_t>(b, header, 0x4C);
  if (!*scratch && (!out.default_header_guard_raw ||
      *out.default_header_guard_raw == 0 || *out.default_header_guard_raw == -1)) {
    out.reason = "list_predicate_selected_default_uninitialized";
    return out;
  }
  if (!data || !out.source_count_raw) {
    out.reason = "list_predicate_list_header_unavailable";
    return out;
  }
  if (*out.source_count_raw < 0) {
    out.reason = "list_predicate_negative_source_count_unrepresentable";
    return out;
  }
  out.rows.emplace();
  if (*out.source_count_raw == 0) {
    out.ready = true;
    out.status = "available";
    return out;
  }
  if (!*data) {
    out.reason = "list_predicate_positive_count_null_array";
    return out;
  }
  bool all_ready = true;
  for (std::int32_t i = 0; i < *out.source_count_raw; ++i) {
    game::ContextSourceListPredicate2530dd0RowV1 row{};
    row.native_index = static_cast<std::uint32_t>(i);
    row.key_u32 = Read<std::uint32_t>(b, *data,
        static_cast<std::size_t>(i) * 24 + 0x10);
    if (!row.key_u32) row.reason = "list_predicate_source_key_unavailable";
    else if (*row.key_u32 == 0xFFFFFFFFU) row.ready = true;
    else ListPredicate2530dd0ObserveRow(b, character, row);
    if (!row.ready) {
      all_ready = false;
      Reason(out.reason, row.reason.c_str());
    }
    out.rows->push_back(std::move(row));
  }
  out.ready = all_ready;
  out.status = all_ready ? "available" : "partial";
  return out;
}
