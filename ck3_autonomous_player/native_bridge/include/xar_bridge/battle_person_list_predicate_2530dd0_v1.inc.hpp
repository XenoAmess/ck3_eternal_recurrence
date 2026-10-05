// Included inside namespace xar::game after ContextSourcePropertiesV1.
struct ContextSourceListPredicate2530dd0ScopeV1 {
  std::optional<std::uint32_t> root_scope_kind_u32;
  std::optional<std::uint32_t> root_character_full_id_u32;
  std::optional<std::uint32_t> named_scope_kind_u32;
  std::optional<std::uint32_t> named_selected_full_id_u32;
  std::optional<std::int32_t> named_binding_key_i32;
  std::optional<std::uint64_t> trigger_object;
  std::optional<std::uint64_t> trigger_vtable;
  std::optional<std::uint64_t> trigger_evaluator_function;
  bool operator==(const ContextSourceListPredicate2530dd0ScopeV1 &) const = default;
};
struct ContextSourceListPredicate2530dd0RowV1 {
  std::uint32_t native_index = 0;
  std::optional<std::uint32_t> key_u32;
  bool ready = false;
  std::optional<std::string> resolution_selection;
  std::optional<std::uint64_t> selected_object;
  std::optional<std::uint32_t> selected_full_id_u32;
  std::optional<bool> used_fallback;
  std::optional<std::uint64_t> predicate_receiver;
  std::optional<std::uint32_t> magic_u32;
  std::optional<std::int32_t> condition_count_raw_i32;
  std::optional<bool> predicate_result;
  std::optional<std::string> pc_selection;
  std::optional<ContextSourceListPredicate2530dd0ScopeV1> scope_inputs;
  std::optional<ContextSourcePropertiesV1> properties;
  std::string reason;
  bool operator==(const ContextSourceListPredicate2530dd0RowV1 &) const = default;
};
struct ContextSourceListPredicate2530dd0InputsV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = 0;
  std::optional<bool> scratch_present;
  std::optional<std::string> header_selection;
  std::optional<std::int32_t> default_header_guard_raw;
  std::optional<bool> source_array_present;
  std::optional<std::int32_t> source_count_raw;
  std::optional<std::vector<ContextSourceListPredicate2530dd0RowV1>> rows;
  std::string reason;
  bool operator==(const ContextSourceListPredicate2530dd0InputsV1 &) const = default;
};
