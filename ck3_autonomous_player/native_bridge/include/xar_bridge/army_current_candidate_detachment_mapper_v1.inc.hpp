// Included inside xar::game, after ArmyCurrentAssaultRemovalReferenceInputsV1.
struct ArmyCandidateMapperCountChunkV1 {
  std::int32_t physical_index = 0;
  std::optional<std::int32_t> maximum_00_raw_i32, current_04_raw_i32, state_18_raw_i32;
  friend bool operator==(const ArmyCandidateMapperCountChunkV1 &,
                         const ArmyCandidateMapperCountChunkV1 &) = default;
};
struct ArmyCandidateMapperCountInputV1 {
  std::int32_t native_index = 0;
  std::string regi_identity, status = "unavailable", unavailable_reason;
  bool ready = false;
  std::optional<std::int32_t> count_base_128_raw_i32;
  std::vector<ArmyCandidateMapperCountChunkV1> chunks;
  friend bool operator==(const ArmyCandidateMapperCountInputV1 &,
                         const ArmyCandidateMapperCountInputV1 &) = default;
};
struct ArmyCandidateDetachmentMapperV1 {
  std::int32_t native_index = 0;
  std::string arrg_identity, status = "unavailable", unavailable_reason;
  bool ready = false;
  std::optional<std::int32_t> kind_14c_raw_i32, data_count_raw_i32;
  std::optional<std::string> first_data_record_identity;
  std::optional<std::uint32_t> first_regi_full_id_u32;
  std::optional<ArmyDailyAssaultResolutionV1> selected_regi_resolution;
  std::optional<std::uint32_t> selected_regi_magic_14_raw_u32;
  std::optional<bool> selected_regi_identity_valid;
  std::optional<std::int32_t> count_input_index;
  std::optional<std::string> fallback_regi_identity;
  bool return_selection_ready = false;
  std::optional<std::string> return_selection, returned_regi_identity;
  std::optional<std::uint32_t> returned_regi_full_id_u32, returned_regi_magic_14_raw_u32;
  std::optional<std::int32_t> returned_state_138_raw_i32;
  std::string return_basis = "source2A977A0_from_same_capture_raw_operands";
  friend bool operator==(const ArmyCandidateDetachmentMapperV1 &,
                         const ArmyCandidateDetachmentMapperV1 &) = default;
};
struct ArmyCandidateDetachmentOccurrenceV1 {
  std::int32_t native_index = 0;
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultResolutionV1 resolution{};
  std::optional<std::int32_t> mapper_index;
  friend bool operator==(const ArmyCandidateDetachmentOccurrenceV1 &,
                         const ArmyCandidateDetachmentOccurrenceV1 &) = default;
};
struct ArmyCurrentCandidateDetachmentMapperInputsV1 {
  std::int32_t schema_version = 1;
  std::string source = "native_current_candidate_detachment_mapper_inputs";
  std::string stage = "observed_current_first_candidate_mapper_seed";
  std::string status = "unavailable", unavailable_reason;
  bool ready = false, selection_ready = false, roster_ready = false;
  std::optional<std::string> selection_branch;
  std::optional<std::int32_t> candidate_reference_native_index, candidate_pending_native_index;
  std::optional<std::uint32_t> candidate_raw_full_id_u32, candidate_actual_full_id_u32;
  std::optional<std::string> candidate_army_identity;
  std::optional<std::int32_t> roster_count_raw_i32;
  std::optional<bool> roster_data_present;
  std::optional<std::string> roster_data_identity;
  std::vector<ArmyCandidateDetachmentOccurrenceV1> occurrences;
  std::vector<ArmyCandidateDetachmentMapperV1> mappers;
  std::vector<ArmyCandidateMapperCountInputV1> count_inputs;
  friend bool operator==(const ArmyCurrentCandidateDetachmentMapperInputsV1 &,
                         const ArmyCurrentCandidateDetachmentMapperInputsV1 &) = default;
};
