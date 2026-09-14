#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::game {

enum class CouncilCompositionStewardCandidatesStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class CouncilCompositionStewardCandidatesFailureV1 : std::uint32_t {
  none = 0,
  invalid_request,
  exact_build_not_admitted,
  native_bindings_unavailable,
  application_main_thread_required,
  frame_capture_failed,
  snapshot_identity_mismatch,
  revision_drift,
  date_drift,
  not_paused,
  player_unavailable,
  active_steward_task_unavailable,
  position_outside_coverage,
  candidate_collection_unavailable,
  candidate_span_invalid,
  candidate_row_unreadable,
  candidate_generation_mismatch,
  duplicate_candidate_id,
  temporary_vector_release_failed,
};

struct CouncilCompositionStewardCandidateV1 {
  std::int32_t character_id = -1;
  std::uint32_t native_collection_ordinal = 0;

  friend bool operator==(const CouncilCompositionStewardCandidateV1 &,
                         const CouncilCompositionStewardCandidateV1 &) =
      default;
};

struct CouncilCompositionStewardCandidatesReadinessV1 {
  bool identity_ready = false;
  bool candidate_collection_ready = false;

  friend bool operator==(
      const CouncilCompositionStewardCandidatesReadinessV1 &,
      const CouncilCompositionStewardCandidatesReadinessV1 &) = default;
};

inline constexpr std::size_t
    kCouncilCompositionStewardCandidatesMaximumRowsV1 = 64;
inline constexpr std::size_t
    kCouncilCompositionStewardSnapshotIdCapacityV1 = 32;
inline constexpr std::size_t
    kCouncilCompositionStewardPositionKeyCapacityV1 = 32;

struct CouncilCompositionStewardCandidatesV1 {
  CouncilCompositionStewardCandidatesStatusV1 status =
      CouncilCompositionStewardCandidatesStatusV1::unavailable;
  CouncilCompositionStewardCandidatesFailureV1 unavailable_reason =
      CouncilCompositionStewardCandidatesFailureV1::none;
  std::array<char, kCouncilCompositionStewardSnapshotIdCapacityV1>
      snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t owner_character_id = -1;
  std::array<char, kCouncilCompositionStewardPositionKeyCapacityV1>
      position_key{};
  bool candidate_collection_complete = false;
  std::uint32_t candidate_count = 0;
  std::array<CouncilCompositionStewardCandidateV1,
             kCouncilCompositionStewardCandidatesMaximumRowsV1>
      candidates{};
  bool temporary_vector_released = false;
  CouncilCompositionStewardCandidatesReadinessV1 readiness{};
};

enum class ReadCouncilCompositionStewardCandidatesResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kCouncilCompositionStewardCandidatesReaderPrivateKeyV1 =
        "g2_council_composition_steward_candidates_reader_v1";
inline constexpr std::string_view
    kCouncilCompositionStewardCandidatesReaderGameVersionV1 = "1.19.0.6";
inline constexpr std::string_view
    kCouncilCompositionStewardCandidatesReaderExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view
    kCouncilCompositionStewardCandidatesReaderPositionKeyV1 =
        "councillor_steward";
inline constexpr std::uintptr_t
    kCouncilCompositionStewardCandidatesProducerRvaV1 = 0x293BD00;

struct CouncilCompositionStewardCandidatesFrameV1 {
  std::array<char, game::kCouncilCompositionStewardSnapshotIdCapacityV1>
      snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  std::int32_t played_character_id = -1;
  std::uintptr_t played_character = 0;
  bool played_character_identity_round_trip = false;
  std::int32_t active_task_id = -1;
  std::uintptr_t active_task = 0;
  bool active_task_identity_round_trip = false;
  std::array<char, game::kCouncilCompositionStewardPositionKeyCapacityV1>
      position_key{};

  friend bool operator==(const CouncilCompositionStewardCandidatesFrameV1 &,
                         const CouncilCompositionStewardCandidatesFrameV1 &) =
      default;
};

struct CouncilCompositionStewardNativeCandidateVectorV1 {
  std::uintptr_t data_address = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};

using CaptureCouncilCompositionStewardCandidatesFrameV1 = bool (*)(
    void *context,
    CouncilCompositionStewardCandidatesFrameV1 &output) noexcept;
using IsCouncilCompositionStewardCandidatesMainThreadV1 = bool (*)(
    void *context) noexcept;
using ProduceCouncilCompositionStewardCandidatesV1 = bool (*)(
    void *context, std::uintptr_t owner_character,
    std::uintptr_t active_task, bool gui_eligibility_mode,
    CouncilCompositionStewardNativeCandidateVectorV1 &output) noexcept;
using ReleaseCouncilCompositionStewardCandidatesV1 = bool (*)(
    void *context,
    CouncilCompositionStewardNativeCandidateVectorV1 &vector) noexcept;
using IsCouncilCompositionStewardCandidateSpanReadableV1 = bool (*)(
    void *context, std::uintptr_t address, std::size_t size) noexcept;
using ReadCouncilCompositionStewardCandidatePointerV1 = bool (*)(
    void *context, std::uintptr_t address,
    std::uintptr_t &candidate_character) noexcept;
using ReadCouncilCompositionStewardCandidateIdV1 = bool (*)(
    void *context, std::uintptr_t candidate_character,
    std::int32_t &character_id) noexcept;
using ResolveCouncilCompositionStewardCandidateV1 = bool (*)(
    void *context, std::int32_t character_id,
    std::uintptr_t &candidate_character) noexcept;

struct CouncilCompositionStewardCandidatesEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  std::uintptr_t producer_address = 0;
};

struct CouncilCompositionStewardCandidatesAccessV1 {
  void *context = nullptr;
  CaptureCouncilCompositionStewardCandidatesFrameV1 capture_frame = nullptr;
  IsCouncilCompositionStewardCandidatesMainThreadV1 is_main_thread = nullptr;
  ProduceCouncilCompositionStewardCandidatesV1 produce = nullptr;
  ReleaseCouncilCompositionStewardCandidatesV1 release = nullptr;
  IsCouncilCompositionStewardCandidateSpanReadableV1 is_readable_span =
      nullptr;
  ReadCouncilCompositionStewardCandidatePointerV1 read_candidate_pointer =
      nullptr;
  ReadCouncilCompositionStewardCandidateIdV1 read_candidate_id = nullptr;
  ResolveCouncilCompositionStewardCandidateV1 resolve_candidate = nullptr;
};

struct CouncilCompositionStewardCandidatesRequestV1 {
  std::string_view expected_snapshot_id{};
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::int32_t expected_date_raw = 0;
  std::int32_t expected_owner_character_id = -1;
};

game::ReadCouncilCompositionStewardCandidatesResultV1
ReadCouncilCompositionStewardCandidatesV1(
    const CouncilCompositionStewardCandidatesEnvironmentV1 &environment,
    const CouncilCompositionStewardCandidatesAccessV1 &access,
    const CouncilCompositionStewardCandidatesRequestV1 &request,
    game::CouncilCompositionStewardCandidatesV1 &output) noexcept;

std::string_view CouncilCompositionStewardCandidatesFailureKeyV1(
    game::CouncilCompositionStewardCandidatesFailureV1 reason) noexcept;

} // namespace xar::ck3_11906
