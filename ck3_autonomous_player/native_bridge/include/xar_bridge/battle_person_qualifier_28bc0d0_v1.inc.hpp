// Included inside namespace xar::game after ContextSourcePropertiesV1.
struct ContextSourceQualifier28bc0d0RelationshipV1 {
  std::uint32_t native_index = 0;
  std::optional<std::uint8_t> marker_u8;
  std::optional<std::uint64_t> definition_object;
  bool operator==(const ContextSourceQualifier28bc0d0RelationshipV1 &) const = default;
};
struct ContextSourceQualifier28bc0d0CandidateV1 {
  std::uint32_t native_index = 0;
  std::optional<std::uint64_t> definition_object;
  std::optional<bool> relationship_array_present;
  std::optional<std::int32_t> relationship_count_raw_i32;
  std::optional<std::vector<ContextSourceQualifier28bc0d0RelationshipV1>> relationships;
  bool operator==(const ContextSourceQualifier28bc0d0CandidateV1 &) const = default;
};
struct ContextSourceQualifier28bc0d0EvaluationV1 {
  std::uint32_t native_index = 0;
  std::optional<std::uint64_t> object;
  std::optional<bool> candidate_array_present;
  std::optional<std::int32_t> candidate_count_raw_i32;
  std::optional<std::vector<ContextSourceQualifier28bc0d0CandidateV1>> candidates;
  // Demanded only after the complete predicate returned true, including for
  // sentinel and repeated IDs. False predicates never read the ID.
  std::optional<std::uint32_t> id_u32;
  bool operator==(const ContextSourceQualifier28bc0d0EvaluationV1 &) const = default;
};
struct ContextSourceQualifier28bc0d0DefinitionV1 {
  std::uint32_t native_index = 0;
  std::optional<std::uint64_t> definition_object;
  bool ready = false;
  std::optional<std::vector<ContextSourceQualifier28bc0d0EvaluationV1>> scratch_evaluations;
  std::optional<std::vector<std::uint32_t>> accepted_ids_u32;
  std::optional<std::int32_t> repeat_count;
  std::optional<ContextSourcePropertiesV1> properties;
  std::string reason;
  bool operator==(const ContextSourceQualifier28bc0d0DefinitionV1 &) const = default;
};
struct ContextSourceQualifier28bc0d0InputsV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = 0;
  std::optional<std::uint64_t> manager_object;
  std::optional<bool> definition_array_present;
  std::optional<std::int32_t> definition_count_raw_i32;
  std::optional<bool> scratch_present;
  std::optional<std::int32_t> scratch_count_raw_i32;
  std::optional<std::uint64_t> fallback_definition_object;
  std::optional<std::vector<ContextSourceQualifier28bc0d0DefinitionV1>> definitions;
  std::string reason;
  bool operator==(const ContextSourceQualifier28bc0d0InputsV1 &) const = default;
};
