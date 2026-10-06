// Included inside xar::game after army_daily_assault_roster_admission_v1.inc.hpp.
// Raw observed-current inputs. No refresh executor is called by this family.
struct ArmyPostAdmissionRefreshArRgV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::string unavailable_reason = "not_demanded";
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 arrg_resolution{};
  std::optional<std::uint32_t> magic_14_raw_u32;
  std::optional<bool> identity_valid;
  std::optional<std::int32_t> current_38_raw_i32;
  std::optional<std::int64_t> value_40_raw_i64;
  bool numeric_24_inputs_ready = false;
  bool numeric_28_inputs_ready = false;
  friend bool operator==(const ArmyPostAdmissionRefreshArRgV1 &, const ArmyPostAdmissionRefreshArRgV1 &) = default;
};
struct ArmyPostAdmissionRefreshOccurrenceV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::string unavailable_reason = "not_demanded";
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 original_army_resolution{};
  ArmyDailyAssaultRawReferencesV1 original_arrg_references{};
  std::vector<ArmyPostAdmissionRefreshArRgV1> arrg_occurrences;
  std::optional<std::int32_t> actual_army_24_raw_i32;
  std::optional<std::int64_t> actual_army_28_raw_i64;
  std::optional<std::uint8_t> actual_army_20_raw_u8, actual_army_21_raw_u8;
  std::optional<std::uint8_t> actual_army_30_raw_u8, actual_army_31_raw_u8;
  bool arrg_rows_ready = false;
  bool numeric_24_inputs_ready = false;
  bool numeric_28_inputs_ready = false;
  friend bool operator==(const ArmyPostAdmissionRefreshOccurrenceV1 &, const ArmyPostAdmissionRefreshOccurrenceV1 &) = default;
};
struct ArmyCurrentPostAdmissionRefreshInputsV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::string unavailable_reason = "not_demanded";
  std::int32_t schema_version = 1;
  std::string source = "native_current_post_admission_refresh_inputs";
  std::string stage = "observed_current_post_admission_refresh_inputs";
  std::string projection_stage = "post24df4c3_pre24df4c7";
  std::optional<bool> manager_loaded;
  std::optional<std::string> manager_identity;
  ArmyDailyAssaultRawReferencesV1 original_roster{};
  std::vector<ArmyPostAdmissionRefreshOccurrenceV1> occurrences;
  bool raw_roster_references_ready = false;
  bool original_army_selections_ready = false;
  bool numeric_24_inputs_ready = false;
  bool numeric_28_inputs_ready = false;
  bool source_operands_ready = false;
  bool actual_refresh_execution_ready = false;
  bool actual_next_occurrence_ready = false;
  bool full_callback_ready = false;
  bool full_daily_assault_ready = false;
  bool full_monthly_ready = false;
  friend bool operator==(const ArmyCurrentPostAdmissionRefreshInputsV1 &, const ArmyCurrentPostAdmissionRefreshInputsV1 &) = default;
};
