#pragma once

#include "xar_bridge/marriage_proposal_native_binder_v1.hpp"

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kMarriageAllianceProjectionPrivateKeyV1 =
    "marriage_alliance_projection_adapter_v1";
inline constexpr std::uintptr_t kMarriageInfoAllianceItemsCallbackRvaV1 =
    0x1274610;
inline constexpr std::uintptr_t kMarriageInfoAllianceProducerRvaV1 =
    0x126D4E0;
inline constexpr std::uintptr_t kMarriageInfoAllianceClearRvaV1 = 0x1273AE0;
inline constexpr std::uintptr_t kMarriageInfoAllianceAppendRvaV1 = 0x1274F20;
inline constexpr std::uintptr_t kMarriageInfoAllianceRowResolverRvaV1 =
    0x1274CA0;
inline constexpr std::uintptr_t kMarriageInfoCurrentPlayerIdRvaV1 =
    0x4FE7EE0;

inline constexpr std::size_t kMarriageInfoAllianceDataOffsetV1 = 0x50;
inline constexpr std::size_t kMarriageInfoAllianceCapacityOffsetV1 = 0x58;
inline constexpr std::size_t kMarriageInfoAllianceCountOffsetV1 = 0x5C;
inline constexpr std::size_t kMarriageInfoAllianceAllocatorOffsetV1 = 0x60;
inline constexpr std::size_t kMarriageInfoAllianceRowStrideV1 = 0x480;
inline constexpr std::size_t kMarriageInfoAllianceRowCharacterIdOffsetV1 = 0;
inline constexpr std::size_t kMarriageInfoAllianceRowMilitaryInfoOffsetV1 = 8;
inline constexpr std::int32_t kMarriageInfoMaximumAllianceRowsV1 = 1'000'000;

enum class MarriageAllianceProjectionFailureV1 : std::uint32_t {
  none = 0,
  exact_build_not_admitted,
  binding_mismatch,
  signature_mismatch,
  memory_reader_unavailable,
  invalid_input,
  projection_header_invalid,
  current_player_identity_unavailable,
  row_identity_unavailable,
  projection_sample_drift,
  pair_not_current_player,
};

struct MarriageAllianceProjectionEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool offline_fixture = false;
  void *memory_context = nullptr;
  MarriageSourceAdapterMemoryReadV1 read_memory = nullptr;
  std::uintptr_t character_storage_slot = 0;
  std::uintptr_t current_player_id_address = 0;
};

struct MarriageAllianceProjectionStateV1 {
  MarriageAllianceProjectionEnvironmentV1 environment{};
  std::atomic<std::uint32_t> last_failure{static_cast<std::uint32_t>(
      MarriageAllianceProjectionFailureV1::none)};
};

MarriageAllianceProjectionEnvironmentV1
BindMarriageAllianceProjectionEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

// CMarriageInfo+0x50 is the current player's projected alliance list for the
// marriage UI.  This resolver intentionally cannot certify an arbitrary live
// alliance relationship and must not be installed as the M5 receipt callback.
bool ReadMarriageAllianceProjectionPairExactV1(
    MarriageAllianceProjectionStateV1 &state,
    std::uintptr_t marriage_info, std::uint32_t first_character_id,
    std::uint32_t second_character_id, bool &projected) noexcept;

MarriageAllianceProjectionFailureV1 ReadMarriageAllianceProjectionFailureV1(
    const MarriageAllianceProjectionStateV1 &state) noexcept;

} // namespace xar::bridge
