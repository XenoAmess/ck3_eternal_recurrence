// Included inside xar::game. Captured current table numerical operands only.
struct ArmyDailyAssaultLossRegimentV1 {
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultResolutionV1 resolution{};
  std::optional<bool> identity_valid;
  std::optional<std::int32_t> current_soldiers, maximum_soldiers;
  friend bool operator==(const ArmyDailyAssaultLossRegimentV1 &, const ArmyDailyAssaultLossRegimentV1 &) = default;
};
struct ArmyDailyAssaultLossTargetV1 {
  ArmyDailyAssaultResolutionV1 resolution{};
  std::optional<bool> identity_valid;
  std::optional<std::int32_t> current_soldiers, maximum_soldiers;
  std::optional<bool> native_loss_writer_skipped;
  std::optional<ArmyRegimentReplenishmentRecordsSnapshotV1> replenishment_records_v1;
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  friend bool operator==(const ArmyDailyAssaultLossTargetV1 &, const ArmyDailyAssaultLossTargetV1 &) = default;
};
struct ArmyDailyAssaultLossArmyCountV1 {
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultResolutionV1 resolution{};
  std::optional<std::int32_t> native_whole_current_soldiers;
  std::vector<ArmyDailyAssaultLossRegimentV1> regiments;
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  friend bool operator==(const ArmyDailyAssaultLossArmyCountV1 &, const ArmyDailyAssaultLossArmyCountV1 &) = default;
};
struct ArmyDailyAssaultLossGroupV1 {
  std::int32_t native_index = 0;
  std::int64_t physical_slot_i64 = 0;
  std::optional<std::int32_t> native_current_expected_loss;
  std::optional<std::uint32_t> province_magic_raw_u32;
  std::optional<ArmyCurrentProvinceBesiegingContributorsV1> besieging_inputs_v1;
  std::vector<ArmyDailyAssaultLossArmyCountV1> army_counts;
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  friend bool operator==(const ArmyDailyAssaultLossGroupV1 &, const ArmyDailyAssaultLossGroupV1 &) = default;
};
struct ArmyCurrentDailyAssaultLossInputsV1 {
  std::int32_t schema_version = 1;
  std::string source = "native_current_daily_assault_loss_inputs";
  std::string stage = "observed_current_daily_assault_table";
  std::string status = "unavailable", unavailable_reason;
  bool ready = false;
  std::vector<ArmyDailyAssaultLossGroupV1> groups;
  std::vector<ArmyDailyAssaultLossTargetV1> target_regiments;
  friend bool operator==(const ArmyCurrentDailyAssaultLossInputsV1 &, const ArmyCurrentDailyAssaultLossInputsV1 &) = default;
};
