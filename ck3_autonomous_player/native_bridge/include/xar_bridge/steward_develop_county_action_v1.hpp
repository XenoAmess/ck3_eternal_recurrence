#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::game {

enum class StewardDevelopCountyActionFailureClassV1 : std::uint32_t {
  none = 0,
  request_contract,
  snapshot_binding,
  councillor_binding,
  task_or_target_legality,
  native_command_dispatch,
};

enum class StewardDevelopCountyActionAckStatusV1 : std::uint32_t {
  rejected_before_submit = 0,
  submitted_verification_pending = 1,
};

enum class StewardDevelopCountyActionReceiptStatusV1 : std::uint32_t {
  rejected = 0,
  applied = 1,
  postcondition_failed = 2,
};

struct StewardDevelopCountyActionRequestV1 {
  std::string request_id;
  std::int32_t councillor_character_id = -1;
  std::string task_key;
  std::int32_t target_county_title_id = -1;
  std::uint64_t expected_revision = 0;
  bool replace_existing_task = false;
};

// This observation is produced by a single, version-bound observer seam.  It
// is deliberately independent of the command object and is used both for the
// final pre-submit binding check and for the later receipt.
struct StewardDevelopCountyTaskObservationV1 {
  bool available = false;
  bool paused = false;
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_snapshot_revision = 0;
  std::int32_t observed_date_raw = 0;
  std::int32_t player_character_id = -1;
  std::int32_t steward_character_id = -1;
  bool target_candidate_present = false;
  std::int32_t target_county_title_id = -1;
  std::int32_t target_capital_province_id = -1;
  bool target_native_legal = false;
  bool has_active_task = false;
  std::string active_task_key;
  std::string active_task_type;
  std::optional<std::int32_t> active_target_county_title_id;
  std::optional<std::int32_t> active_target_province_id;
  bool progress_available = false;
  std::string progress_kind;
  std::int64_t progress_current_raw = 0;
  std::int64_t progress_max_raw = 0;
  bool progress_frozen = false;

  friend bool operator==(const StewardDevelopCountyTaskObservationV1 &,
                         const StewardDevelopCountyTaskObservationV1 &) =
      default;
};

struct StewardDevelopCountyActionAckV1 {
  StewardDevelopCountyActionAckStatusV1 status =
      StewardDevelopCountyActionAckStatusV1::rejected_before_submit;
  bool verification_pending = false;
  std::string request_id;
  std::uint64_t pre_snapshot_revision = 0;
  std::uint64_t pre_native_snapshot_revision = 0;
  std::int32_t councillor_character_id = -1;
  std::string task_key;
  std::int32_t target_county_title_id = -1;
  std::int32_t submitted_target_province_id = -1;
  bool replaced_existing_task = false;
  StewardDevelopCountyActionFailureClassV1 failure_class =
      StewardDevelopCountyActionFailureClassV1::none;
  std::string rejection_reason;
  std::string native_reason_key;
};

struct StewardDevelopCountyActionReceiptV1 {
  StewardDevelopCountyActionReceiptStatusV1 status =
      StewardDevelopCountyActionReceiptStatusV1::postcondition_failed;
  std::string request_id;
  std::string reason;
  std::uint64_t post_snapshot_revision = 0;
  std::uint64_t post_native_snapshot_revision = 0;
  std::int32_t post_observed_date_raw = 0;
  std::int32_t councillor_character_id = -1;
  std::string active_task_key;
  std::optional<std::int32_t> target_county_title_id;
  std::optional<std::int32_t> target_province_id;
  std::string progress_kind;
  std::optional<std::int64_t> progress_current_raw;
  std::optional<std::int64_t> progress_max_raw;
  std::optional<bool> progress_frozen;
  bool postcondition_verified = false;
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kStewardDevelopCountyActionV1Capability =
    "game.command.change-steward-develop-county-task-v1";
inline constexpr std::string_view kStewardDevelopCountyActionV1Step =
    "change-steward-develop-county-task-v1";
inline constexpr std::string_view kStewardDevelopCountyActionV1TaskKey =
    "task_develop_county";
inline constexpr std::string_view kStewardDevelopCountyActionV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view kStewardDevelopCountyActionV1ExecutableSha256 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kStewardDevelopCountyActionV1BackendId =
    "ck3-1.19.0.6-native-steward-develop-county-action-v1";
inline constexpr std::string_view kStewardDevelopCountyActionV1ContractStage =
    "exact_build_action_seam_pending_command_abi_certification";

struct StewardDevelopCountyActionNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool command_abi_certified = false;
  bool offline_fixture_command = false;
};

using CaptureStewardDevelopCountyTaskObservationV1 = bool (*)(
    void *context,
    game::StewardDevelopCountyTaskObservationV1 &output) noexcept;

// The validator must call CK3's final task/location validator and preserve the
// returned localization key.  A true return means the call completed; `valid`
// is the native verdict.
using ValidateStewardDevelopCountyCommandV1 = bool (*)(
    void *context, std::int32_t councillor_character_id,
    std::int32_t target_capital_province_id, bool &valid,
    std::string &native_reason_key) noexcept;

// A true return means exactly one CChangeCouncilTaskCommand was handed to the
// engine command submitter.  It does not mean the command has been applied.
using SubmitStewardDevelopCountyCommandV1 = bool (*)(
    void *context, std::int32_t councillor_character_id,
    std::int32_t target_capital_province_id) noexcept;

struct StewardDevelopCountyActionAccessV1 {
  void *context = nullptr;
  CaptureStewardDevelopCountyTaskObservationV1 capture_observation = nullptr;
  ValidateStewardDevelopCountyCommandV1 validate_native = nullptr;
  SubmitStewardDevelopCountyCommandV1 submit_native = nullptr;
};

StewardDevelopCountyActionNativeEnvironmentV1
BindStewardDevelopCountyActionNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::StewardDevelopCountyActionAckStatusV1
ExecuteStewardDevelopCountyActionV1(
    const StewardDevelopCountyActionNativeEnvironmentV1 &environment,
    const StewardDevelopCountyActionAccessV1 &access,
    const game::StewardDevelopCountyActionRequestV1 &request,
    game::StewardDevelopCountyActionAckV1 &ack) noexcept;

game::StewardDevelopCountyActionReceiptStatusV1
VerifyStewardDevelopCountyActionReceiptV1(
    const game::StewardDevelopCountyActionAckV1 &ack,
    const game::StewardDevelopCountyTaskObservationV1 &post_observation,
    game::StewardDevelopCountyActionReceiptV1 &receipt) noexcept;

std::string_view StewardDevelopCountyActionFailureClassKeyV1(
    game::StewardDevelopCountyActionFailureClassV1 value) noexcept;
std::string SerializeStewardDevelopCountyActionAckV1(
    const game::StewardDevelopCountyActionAckV1 &ack);
std::string SerializeStewardDevelopCountyActionReceiptV1(
    const game::StewardDevelopCountyActionReceiptV1 &receipt);

} // namespace xar::ck3_11906
