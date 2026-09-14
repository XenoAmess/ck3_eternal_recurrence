#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kActiveSchemeStateV1PrivateObserverExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view
    kActiveSchemeStateV1PrivateObserverEvidenceRevision =
        "scheme_state_1_19_0_6@a5438595";
inline constexpr std::size_t kActiveSchemeStateV1PrivateMaximumRows = 32;
inline constexpr std::size_t kActiveSchemeStateV1PrivateTypeKeyCapacity = 96;
inline constexpr std::size_t kActiveSchemeStateV1PrivateCategoryKeyCapacity =
    48;

enum class ActiveSchemeStateV1PrivateStatus : std::uint8_t {
  unavailable,
  available,
};

enum class ActiveSchemeStateV1PrivateFailure : std::uint8_t {
  none,
  exact_build_mismatch,
  source_adapter_unavailable,
  not_application_main_thread,
  not_paused,
  frame_drift,
  played_character_unavailable,
  container_identity_unavailable,
  container_drift,
  enumeration_incomplete,
  row_count_invalid,
  scheme_identity_unavailable,
  duplicate_scheme_identity,
  owner_mismatch,
  scheme_type_unavailable,
  scheme_category_unavailable,
  target_unavailable,
  definition_flags_unavailable,
  metric_unavailable,
  metric_invalid,
  basic_metric_claimed_available,
};

enum class ActiveSchemeStateV1PrivateValueStatus : std::uint8_t {
  unavailable,
  available,
  not_applicable,
};

enum class ActiveSchemeStateV1PrivateTargetKind : std::uint8_t {
  unavailable,
  character,
  title,
};

template <typename T> struct ActiveSchemeStateV1PrivateValue {
  ActiveSchemeStateV1PrivateValueStatus status =
      ActiveSchemeStateV1PrivateValueStatus::unavailable;
  T value{};
};

// This is the private, already-copied handoff from a future exact-build
// owning-thread reader. It deliberately contains no native pointer. The
// reader is not part of SCHEME2: until SCHEME1's manager/container/getter
// edges are closed, source_adapter_bound must remain false in production.
struct ActiveSchemeStateV1PrivateCapturedRow {
  bool scheme_identity_round_trip = false;
  std::uint64_t scheme_instance_id = 0;
  std::uint32_t scheme_instance_generation = 0;
  std::int64_t owner_character_id = 0;
  std::array<char, kActiveSchemeStateV1PrivateTypeKeyCapacity>
      scheme_type_key{};
  std::array<char, kActiveSchemeStateV1PrivateCategoryKeyCapacity>
      category_key{};

  bool target_identity_round_trip = false;
  ActiveSchemeStateV1PrivateTargetKind target_kind =
      ActiveSchemeStateV1PrivateTargetKind::unavailable;
  std::int64_t target_id = 0;

  bool definition_flags_verified = false;
  bool is_basic = false;
  bool is_secret = false;
  bool is_exposed = false;
  bool is_frozen = false;

  ActiveSchemeStateV1PrivateValue<std::int32_t> progress{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> progress_goal{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> success_chance{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> maximum_success_chance{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> secrecy{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> opportunity_charges{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> breaches{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> maximum_breaches{};
  ActiveSchemeStateV1PrivateValue<std::int32_t>
      phases_remaining_until_opportunity{};
};

struct ActiveSchemeStateV1PrivateCapture {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool source_adapter_bound = false;
  bool application_main_thread = false;
  bool paused = false;

  std::uint64_t capture_epoch_before = 0;
  std::uint64_t capture_epoch_after = 0;
  std::int64_t date_raw_before = 0;
  std::int64_t date_raw_after = 0;
  std::int64_t played_character_id_before = 0;
  std::int64_t played_character_id_after = 0;

  bool container_identity_round_trip = false;
  std::uint64_t container_identity_before = 0;
  std::uint64_t container_identity_after = 0;
  std::uint64_t container_generation_before = 0;
  std::uint64_t container_generation_after = 0;
  std::size_t row_count_before = 0;
  std::size_t row_count_after = 0;
  bool enumeration_complete = false;
  std::array<ActiveSchemeStateV1PrivateCapturedRow,
             kActiveSchemeStateV1PrivateMaximumRows>
      rows{};
};

// Pointer-free private result. A future bridge may translate this into a
// public schema only after the production source adapter and paused live
// fixtures exist.
struct ActiveSchemeStateV1PrivateRow {
  std::uint64_t scheme_instance_id = 0;
  std::uint32_t scheme_instance_generation = 0;
  std::int64_t owner_character_id = 0;
  std::array<char, kActiveSchemeStateV1PrivateTypeKeyCapacity>
      scheme_type_key{};
  std::array<char, kActiveSchemeStateV1PrivateCategoryKeyCapacity>
      category_key{};
  ActiveSchemeStateV1PrivateTargetKind target_kind =
      ActiveSchemeStateV1PrivateTargetKind::unavailable;
  std::int64_t target_id = 0;
  bool is_basic = false;
  bool is_secret = false;
  bool is_exposed = false;
  bool is_frozen = false;
  ActiveSchemeStateV1PrivateValue<std::int32_t> progress{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> progress_goal{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> success_chance{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> maximum_success_chance{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> secrecy{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> opportunity_charges{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> breaches{};
  ActiveSchemeStateV1PrivateValue<std::int32_t> maximum_breaches{};
  ActiveSchemeStateV1PrivateValue<std::int32_t>
      phases_remaining_until_opportunity{};
};

struct ActiveSchemeStateV1PrivateObservation {
  ActiveSchemeStateV1PrivateStatus status =
      ActiveSchemeStateV1PrivateStatus::unavailable;
  ActiveSchemeStateV1PrivateFailure unavailable_reason =
      ActiveSchemeStateV1PrivateFailure::source_adapter_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int64_t date_raw = 0;
  std::int64_t played_character_id = 0;
  std::uint64_t container_generation = 0;
  std::size_t row_count = 0;
  std::array<ActiveSchemeStateV1PrivateRow,
             kActiveSchemeStateV1PrivateMaximumRows>
      rows{};
};

bool ObserveActiveSchemeStateV1Private(
    const ActiveSchemeStateV1PrivateCapture &capture,
    ActiveSchemeStateV1PrivateObservation &output) noexcept;

std::string_view ActiveSchemeStateV1PrivateFailureName(
    ActiveSchemeStateV1PrivateFailure failure) noexcept;

} // namespace xar::bridge
