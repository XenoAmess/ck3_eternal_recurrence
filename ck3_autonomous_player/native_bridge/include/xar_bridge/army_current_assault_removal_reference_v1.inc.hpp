// Included inside xar::game, after the actual current-table DTO.
struct ArmyCurrentAssaultRemovalBucketRowV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> pointer_identity;
  std::optional<bool> native_same_helper_pointer;
  friend bool operator==(const ArmyCurrentAssaultRemovalBucketRowV1 &,
                         const ArmyCurrentAssaultRemovalBucketRowV1 &) = default;
};
struct ArmyCurrentAssaultRemovalTargetV1 {
  std::int32_t native_index = 0;
  std::uint32_t argument_full_id_u32 = 0;
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  ArmyDailyAssaultResolutionV1 helper_resolution{};
  std::optional<std::uint32_t> selected_bucket_index_u32;
  std::optional<std::int32_t> bucket_count_raw_i32;
  std::optional<bool> bucket_data_present;
  std::optional<std::vector<ArmyCurrentAssaultRemovalBucketRowV1>> bucket_rows;
  friend bool operator==(const ArmyCurrentAssaultRemovalTargetV1 &,
                         const ArmyCurrentAssaultRemovalTargetV1 &) = default;
};
struct ArmyCurrentAssaultRemovalReferenceV1 {
  std::int32_t native_index = 0;
  std::string status = "unavailable", unavailable_reason, reference_scope;
  bool ready = false;
  std::optional<std::int32_t> pending_native_index, group_native_index, group_army_native_index;
  std::optional<std::int64_t> group_physical_slot_i64;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultResolutionV1 resolution{};
  std::optional<std::uint32_t> army_magic_14_raw_u32;
  std::optional<bool> native_army_identity_valid;
  std::string identity_scalar_basis;
  std::optional<std::int32_t> cleanup_target_index;
  friend bool operator==(const ArmyCurrentAssaultRemovalReferenceV1 &,
                         const ArmyCurrentAssaultRemovalReferenceV1 &) = default;
};
struct ArmyCurrentAssaultRemovalReferenceInputsV1 {
  std::int32_t schema_version = 1;
  std::string source = "native_current_assault_removal_references";
  std::string stage = "observed_current_removal_reference_context";
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  std::optional<std::string> manager_identity;
  std::optional<std::vector<std::int32_t>> observed_pending_ids_i32;
  std::vector<ArmyManagerCleanupIdListV1> manager_id_lists;
  std::optional<std::vector<std::array<std::uint32_t, 4>>> records_b0;
  std::vector<ArmyCurrentAssaultRemovalReferenceV1> reference_occurrences;
  std::vector<ArmyCurrentAssaultRemovalTargetV1> cleanup_targets;
  friend bool operator==(const ArmyCurrentAssaultRemovalReferenceInputsV1 &,
                         const ArmyCurrentAssaultRemovalReferenceInputsV1 &) = default;
};
