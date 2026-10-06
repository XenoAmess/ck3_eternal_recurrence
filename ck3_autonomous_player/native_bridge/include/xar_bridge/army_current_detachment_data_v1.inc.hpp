// Included inside xar::game, after ArmyCurrentCandidateDetachmentMapperInputsV1.
// Current-input observations only; each incoming ArRg is an independent baseline.
struct ArmyDetachmentDataOccurrenceV1 {
  std::int32_t native_index = 0;
  std::string record_identity, status = "unavailable", unavailable_reason;
  bool ready = false;
  std::optional<std::uint32_t> raw_regi_full_id_u32, magic_14_raw_u32;
  std::optional<std::int32_t> data_ordinal_raw_i32, physical_chunk_index;
  std::optional<std::string> held_fallback_regi_identity;
  ArmyDailyAssaultResolutionV1 resolution{};
  std::optional<bool> identity_valid, physical_chunk_present;
  friend bool operator==(const ArmyDetachmentDataOccurrenceV1 &, const ArmyDetachmentDataOccurrenceV1 &) = default;
};
struct ArmyDetachmentPhysicalChunkV1 {
  std::int32_t native_index = 0;
  std::string chunk_identity, status = "unavailable", unavailable_reason;
  bool ready = false;
  std::optional<std::int32_t> maximum_00_raw_i32, current_04_raw_i32, ordinal_0c_raw_i32;
  std::optional<std::uint32_t> owner_08_raw_u32, association_10_raw_u32;
  std::optional<std::uint8_t> flag_14_raw_u8;
  std::optional<std::int64_t> date_1c_raw64;
  friend bool operator==(const ArmyDetachmentPhysicalChunkV1 &, const ArmyDetachmentPhysicalChunkV1 &) = default;
};
struct ArmyDetachmentAssociationInputV1 {
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  std::uint32_t requested_full_id_u32 = 0;
  ArmyDailyAssaultResolutionV1 arrg_resolution{}, army_resolution{}, unit_resolution{}, character_resolution{};
  std::optional<std::uint32_t> army_full_id_140_u32, unit_full_id_124_u32, character_full_id_174_u32;
  std::optional<std::string> context_pointer_identity;
  std::optional<std::uint32_t> context_count_0c_raw_u32;
  friend bool operator==(const ArmyDetachmentAssociationInputV1 &, const ArmyDetachmentAssociationInputV1 &) = default;
};
struct ArmyDetachmentOwnerInputV1 {
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  std::uint32_t requested_full_id_u32 = 0;
  ArmyDailyAssaultResolutionV1 resolution{};
  std::optional<std::int32_t> state_138_raw_i32;
  std::optional<std::string> definition_identity, origin_identity;
  std::optional<std::uint32_t> definition_magic_38_raw_u32, origin_magic_85c_raw_u32;
  friend bool operator==(const ArmyDetachmentOwnerInputV1 &, const ArmyDetachmentOwnerInputV1 &) = default;
};
struct ArmyDetachmentDateInputV1 {
  std::string status = "unavailable", unavailable_reason, basis;
  bool ready = false;
  std::uint32_t association_full_id_u32 = 0, owner_full_id_u32 = 0;
  std::optional<std::string> unit_identity, source_origin_identity, capital_origin_identity;
  std::optional<std::uint32_t> source_origin_magic_85c_raw_u32, capital_origin_magic_85c_raw_u32;
  std::optional<std::int64_t> output_date_raw64;
  friend bool operator==(const ArmyDetachmentDateInputV1 &, const ArmyDetachmentDateInputV1 &) = default;
};
struct ArmyDetachmentPendingRecordV1 {
  std::int32_t native_index = 0;
  std::string record_identity, status = "unavailable", unavailable_reason;
  bool ready = false;
  std::optional<std::string> vtable_identity, slot0_target_identity;
  std::optional<std::uint32_t> owner_08_raw_u32;
  std::optional<std::int32_t> ordinal_0c_raw_i32;
  friend bool operator==(const ArmyDetachmentPendingRecordV1 &, const ArmyDetachmentPendingRecordV1 &) = default;
};
struct ArmyDetachmentPendingInputsV1 {
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  std::optional<std::string> header_identity, buffer_identity, allocator_identity;
  std::optional<std::int32_t> capacity_08_raw_i32, count_0c_raw_i32;
  std::vector<ArmyDetachmentPendingRecordV1> records;
  friend bool operator==(const ArmyDetachmentPendingInputsV1 &, const ArmyDetachmentPendingInputsV1 &) = default;
};
struct ArmyCurrentDetachmentIncomingV1 {
  std::int32_t native_index = 0;
  std::string arrg_identity, status = "unavailable", unavailable_reason;
  bool ready = false, data_ready = false;
  std::optional<std::uint32_t> arrg_full_id_u32, army_full_id_140_u32, unit_full_id_124_u32;
  ArmyDailyAssaultResolutionV1 army_resolution{}, unit_resolution{};
  std::optional<std::string> passed_province_identity, data_pointer_identity,
      captured_cursor_identity, captured_end_identity;
  std::optional<std::int32_t> data_count_raw_i32;
  std::optional<std::uint32_t> character_full_id_148_u32;
  ArmyDailyAssaultResolutionV1 character_resolution{};
  std::optional<bool> character_pointer_1b8_present;
  std::optional<std::string> character_pointer_1b8_identity;
  std::vector<ArmyDetachmentDataOccurrenceV1> data_occurrences;
  std::vector<ArmyDetachmentPhysicalChunkV1> physical_chunks;
  std::vector<ArmyDetachmentAssociationInputV1> association_inputs;
  std::vector<ArmyDetachmentOwnerInputV1> owner_inputs;
  std::vector<ArmyDetachmentDateInputV1> date_inputs;
  ArmyDetachmentPendingInputsV1 pending{};
  friend bool operator==(const ArmyCurrentDetachmentIncomingV1 &, const ArmyCurrentDetachmentIncomingV1 &) = default;
};
struct ArmyCurrentDetachmentCandidateOccurrenceV1 {
  std::int32_t native_index = 0;
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  std::optional<std::uint32_t> raw_full_id_u32, magic_14_raw_u32;
  ArmyDailyAssaultResolutionV1 resolution{};
  std::optional<bool> incoming_valid;
  std::optional<std::int32_t> incoming_index;
  friend bool operator==(const ArmyCurrentDetachmentCandidateOccurrenceV1 &, const ArmyCurrentDetachmentCandidateOccurrenceV1 &) = default;
};
struct ArmyCurrentDetachmentDataInputsV1 {
  std::int32_t schema_version = 1;
  std::string source = "native_current_detachment_data_inputs";
  std::string stage = "observed_current_incoming_2633ff0_seed";
  std::string status = "unavailable", unavailable_reason;
  bool ready = false, selection_ready = false, roster_ready = false;
  std::optional<std::int64_t> current_date_storage_raw64;
  std::optional<std::string> primary_receiver_identity, canonical_pending_vtable_identity,
      ready_pending_callback_identity;
  std::vector<ArmyCurrentDetachmentCandidateOccurrenceV1> candidate_occurrences;
  std::vector<ArmyCurrentDetachmentIncomingV1> incoming;
  friend bool operator==(const ArmyCurrentDetachmentDataInputsV1 &, const ArmyCurrentDetachmentDataInputsV1 &) = default;
};
