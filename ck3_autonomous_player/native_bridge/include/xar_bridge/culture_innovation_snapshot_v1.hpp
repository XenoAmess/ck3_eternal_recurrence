#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::game {

enum class CultureInnovationSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class CultureInnovationSnapshotFailureV1 : std::uint32_t {
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
  native_source_read_failed,
  culture_identity_invalid,
  culture_head_invariant_failed,
  fascination_invariant_failed,
  era_collection_invalid,
  innovation_collection_invalid,
  stable_key_invalid,
  progress_invalid,
  duplicate_stable_key,
  native_sample_drift,
};

// Optional native identities use three states. `unknown` means that the
// observer could not establish the value. `absent` is a successfully observed
// null native identity and must never be collapsed into unavailable.
enum class CultureInnovationPresenceV1 : std::uint32_t {
  unknown = 0,
  absent = 1,
  present = 2,
};

inline constexpr std::size_t kCultureInnovationStableKeyCapacityV1 = 128;
inline constexpr std::size_t kCultureInnovationSnapshotIdCapacityV1 = 48;
inline constexpr std::size_t kCultureInnovationGameBuildCapacityV1 = 16;
inline constexpr std::size_t kCultureInnovationExecutableSha256CapacityV1 =
    65;
inline constexpr std::size_t kCultureInnovationMaximumErasV1 = 16;
inline constexpr std::size_t kCultureInnovationMaximumInnovationsV1 = 128;

struct CultureInnovationStableKeyV1 {
  std::uint16_t size = 0;
  std::array<char, kCultureInnovationStableKeyCapacityV1> bytes{};

  friend bool operator==(const CultureInnovationStableKeyV1 &,
                         const CultureInnovationStableKeyV1 &) = default;
};

struct CultureInnovationEraV1 {
  CultureInnovationStableKeyV1 key{};
  // Adapter-normalized fixed-point progress. Zero is a legal observed value.
  std::int64_t progress_raw = 0;

  friend bool operator==(const CultureInnovationEraV1 &,
                         const CultureInnovationEraV1 &) = default;
};

struct CultureInnovationRowV1 {
  CultureInnovationStableKeyV1 key{};
  CultureInnovationStableKeyV1 era_key{};
  CultureInnovationStableKeyV1 group_key{};
  CultureInnovationStableKeyV1 skill_key{};
  // 100% is kCultureInnovationCompleteFixedPointV1. Zero is legal.
  std::int64_t progress_raw = 0;
  bool is_active = false;
  bool can_gain_progress = false;
  bool can_be_fascination = false;
  bool is_fascination = false;
  bool has_spread_marker = false;

  friend bool operator==(const CultureInnovationRowV1 &,
                         const CultureInnovationRowV1 &) = default;
};

struct CultureInnovationStateV1 {
  // -1 is the unavailable sentinel. Signed zero is a legal stable identity.
  std::int32_t culture_id = -1;
  CultureInnovationPresenceV1 culture_head_presence =
      CultureInnovationPresenceV1::unknown;
  std::int32_t culture_head_character_id = -1;
  bool is_player_culture_head = false;

  CultureInnovationPresenceV1 fascination_presence =
      CultureInnovationPresenceV1::unknown;
  CultureInnovationStableKeyV1 current_fascination_key{};

  std::uint32_t era_count = 0;
  std::array<CultureInnovationEraV1, kCultureInnovationMaximumErasV1> eras{};
  std::uint32_t innovation_count = 0;
  std::array<CultureInnovationRowV1,
             kCultureInnovationMaximumInnovationsV1>
      innovations{};

  friend bool operator==(const CultureInnovationStateV1 &,
                         const CultureInnovationStateV1 &) = default;
};

struct CultureInnovationSnapshotReadinessV1 {
  bool culture_identity_ready = false;
  bool culture_head_ready = false;
  bool fascination_ready = false;
  bool era_collection_ready = false;
  bool innovation_collection_ready = false;
  bool same_frame_ready = false;

  friend bool operator==(const CultureInnovationSnapshotReadinessV1 &,
                         const CultureInnovationSnapshotReadinessV1 &) =
      default;
};

struct CultureInnovationSnapshotV1 {
  CultureInnovationSnapshotStatusV1 status =
      CultureInnovationSnapshotStatusV1::unavailable;
  CultureInnovationSnapshotFailureV1 unavailable_reason =
      CultureInnovationSnapshotFailureV1::none;
  std::array<char, kCultureInnovationSnapshotIdCapacityV1> snapshot_id{};
  std::array<char, kCultureInnovationGameBuildCapacityV1> game_build{};
  std::array<char, kCultureInnovationExecutableSha256CapacityV1>
      executable_sha256{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t player_character_id = -1;
  CultureInnovationStateV1 state{};
  CultureInnovationSnapshotReadinessV1 readiness{};
};

enum class ReadCultureInnovationSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kCultureInnovationSnapshotPrivateKeyV1 =
    "g2_culture_innovation_snapshot_v1";
inline constexpr std::string_view kCultureInnovationSnapshotGameVersionV1 =
    "1.19.0.6";
inline constexpr std::string_view
    kCultureInnovationSnapshotExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr bool kCultureInnovationSnapshotAdvertisedByDefaultV1 = false;

// Frozen CULTURE1 layout anchors. This core consumes adapter-owned copies and
// never publishes these addresses or a borrowed CK3 pointer.
inline constexpr std::size_t kCultureEraStateVectorOffsetV1 = 0x728;
inline constexpr std::size_t kCultureEraStateCountOffsetV1 = 0x734;
inline constexpr std::size_t kCultureEraStateStrideV1 = 0x58;
inline constexpr std::size_t kCultureInnovationStateVectorOffsetV1 = 0x740;
inline constexpr std::size_t kCultureInnovationStateCountOffsetV1 = 0x74C;
inline constexpr std::size_t kCultureInnovationStateStrideV1 = 0x790;
inline constexpr std::size_t kCultureInnovationDefinitionVectorOffsetV1 =
    0x770;
inline constexpr std::size_t kCultureInnovationDefinitionCountOffsetV1 =
    0x77C;
inline constexpr std::size_t kCultureSpreadMarkerOffsetV1 = 0x848;
inline constexpr std::size_t kCultureFascinationMarkerOffsetV1 = 0x860;
inline constexpr std::size_t kCultureHeadHandleOffsetV1 = 0x8F8;
inline constexpr std::size_t kCultureNeedsFascinationReselectionOffsetV1 =
    0x8FC;
inline constexpr std::size_t kInnovationCultureOffsetV1 = 0x8;
inline constexpr std::size_t kInnovationDefinitionOffsetV1 = 0x10;
inline constexpr std::size_t kInnovationProgressOffsetV1 = 0x18;
inline constexpr std::int64_t kCultureInnovationCompleteFixedPointV1 =
    10'000'000;

struct CultureInnovationSnapshotFrameV1 {
  std::array<char, game::kCultureInnovationSnapshotIdCapacityV1> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  std::int32_t played_character_id = -1;
  std::uintptr_t played_character = 0;
  bool played_character_identity_round_trip = false;

  friend bool operator==(const CultureInnovationSnapshotFrameV1 &,
                         const CultureInnovationSnapshotFrameV1 &) = default;
};

struct CultureInnovationSourceSampleV1 {
  std::int32_t player_character_id = -1;
  bool player_identity_round_trip = false;
  game::CultureInnovationStateV1 state{};

  friend bool operator==(const CultureInnovationSourceSampleV1 &,
                         const CultureInnovationSourceSampleV1 &) = default;
};

struct CultureInnovationSnapshotEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
};

using CaptureCultureInnovationSnapshotFrameV1 = bool (*)(
    void *context, CultureInnovationSnapshotFrameV1 &output) noexcept;
using IsCultureInnovationSnapshotMainThreadV1 = bool (*)(
    void *context) noexcept;
using ReadCultureInnovationNativeSourceV1 = bool (*)(
    void *context, std::uintptr_t played_character,
    CultureInnovationSourceSampleV1 &output) noexcept;

struct CultureInnovationSnapshotAccessV1 {
  void *context = nullptr;
  CaptureCultureInnovationSnapshotFrameV1 capture_frame = nullptr;
  IsCultureInnovationSnapshotMainThreadV1 is_main_thread = nullptr;
  ReadCultureInnovationNativeSourceV1 read_source = nullptr;
};

struct CultureInnovationSnapshotRequestV1 {
  std::string_view expected_snapshot_id{};
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::int32_t expected_date_raw = 0;
  std::int32_t expected_player_character_id = -1;
};

bool AssignCultureInnovationStableKeyV1(
    std::string_view value,
    game::CultureInnovationStableKeyV1 &output) noexcept;

std::string_view CultureInnovationStableKeyViewV1(
    const game::CultureInnovationStableKeyV1 &value) noexcept;

game::ReadCultureInnovationSnapshotResultV1 ReadCultureInnovationSnapshotV1(
    const CultureInnovationSnapshotEnvironmentV1 &environment,
    const CultureInnovationSnapshotAccessV1 &access,
    const CultureInnovationSnapshotRequestV1 &request,
    game::CultureInnovationSnapshotV1 &output) noexcept;

std::string_view CultureInnovationSnapshotFailureKeyV1(
    game::CultureInnovationSnapshotFailureV1 reason) noexcept;

} // namespace xar::ck3_11906
