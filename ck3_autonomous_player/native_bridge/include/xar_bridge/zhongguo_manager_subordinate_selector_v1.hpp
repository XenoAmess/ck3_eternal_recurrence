#pragma once

#include "xar_bridge/zhongguo_ai_owned_case_snapshot_v1.hpp"
#include "xar_bridge/zhongguo_manager_governance_snapshot_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoManagerSubordinateSelectorStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class ReadZhongguoManagerSubordinateSelectorResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoManagerSubordinateSelectionV1 {
  std::int32_t manager_character_id = -1;
  std::int32_t subordinate_character_id = -1;
  std::int32_t manager_contract_id = -1;
  std::int32_t subordinate_contract_id = -1;
  std::int32_t manager_primary_title_id = -1;
  std::int32_t manager_primary_title_tier_raw = 0;
  std::string manager_primary_title_tier_key;
  std::string manager_government_key;

  friend bool operator==(const ZhongguoManagerSubordinateSelectionV1 &,
                         const ZhongguoManagerSubordinateSelectionV1 &) =
      default;
};

struct ZhongguoManagerSubordinateSelectorReadinessV1 {
  bool exact_build_ready = false;
  bool player_binding_ready = false;
  bool relationship_enumeration_ready = false;
  bool manager_eligibility_ready = false;
  bool direct_subordinate_ready = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(
      const ZhongguoManagerSubordinateSelectorReadinessV1 &,
      const ZhongguoManagerSubordinateSelectorReadinessV1 &) = default;
};

struct ZhongguoManagerSubordinateSelectorSnapshotV1 {
  ZhongguoManagerSubordinateSelectorStatusV1 status =
      ZhongguoManagerSubordinateSelectorStatusV1::unavailable;
  std::string selector_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  ZhongguoManagerSubordinateSelectionV1 selection;
  ZhongguoManagerSubordinateSelectorReadinessV1 readiness;
  std::string unavailable_reason;

  friend bool operator==(
      const ZhongguoManagerSubordinateSelectorSnapshotV1 &,
      const ZhongguoManagerSubordinateSelectorSnapshotV1 &) = default;
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kZhongguoManagerSubordinateSelectorV1Capability =
        "game.command.query-zhongguo-manager-subordinate-selector-v1";
inline constexpr std::string_view kZhongguoManagerSubordinateSelectorV1Step =
    "query-zhongguo-manager-subordinate-selector-v1";
inline constexpr std::string_view kZhongguoManagerSubordinateSelectorV1Kind =
    "zg361-bounded-ai-direct-manager-selection-v1";
inline constexpr std::uintptr_t kZhongguoSubjectContractStorageSlotRva =
    0x570CCA0;
inline constexpr std::uintptr_t kZhongguoSubjectContractFallbackSlotRva =
    0x570CC50;

enum class ZhongguoManagerSubordinateObservationResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
  no_bounded_ai_direct_manager = 2,
  bounded_ai_manager_has_no_direct_subordinate = 3,
};

struct ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 {
  ZhongguoAiOwnedCaseNativeEnvironmentV1 eligibility{};
  void **subject_contract_storage_slot = nullptr;
  void **subject_contract_fallback_slot = nullptr;
};

using ObserveZhongguoManagerSubordinateSelectionV1 =
    ZhongguoManagerSubordinateObservationResultV1 (*)(
        void *, std::int32_t,
        game::ZhongguoManagerSubordinateSelectionV1 &) noexcept;
using AuthorizeZhongguoManagerFixtureV1 =
    ZhongguoBoundedAiManagerAuthorizationV1 (*)(
        void *, std::int32_t, std::int32_t, std::int32_t) noexcept;

struct ZhongguoManagerSubordinateSelectorAccessV1 {
  void *context = nullptr;
  CaptureZhongguoCaseFrameV1 capture_frame = nullptr;
  IsZhongguoCaseMainThreadV1 is_main_thread = nullptr;
  ReadZhongguoCaseMemoryV1 read_memory = nullptr;
  // Both callbacks are fixture-only semantic replacements. Production leaves
  // them null and mirrors the exact native relationship containers.
  ObserveZhongguoManagerSubordinateSelectionV1 observe_selection = nullptr;
  AuthorizeZhongguoManagerFixtureV1 authorize_manager_fixture = nullptr;
};

struct ZhongguoManagerSubordinateSelectorRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::string request_nonce;
};

ZhongguoManagerSubordinateSelectorNativeEnvironmentV1
BindZhongguoManagerSubordinateSelectorNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoManagerSubordinateSelectorResultV1
ReadZhongguoManagerSubordinateSelectorV1(
    const ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 &environment,
    const ZhongguoManagerSubordinateSelectorAccessV1 &access,
    const ZhongguoManagerSubordinateSelectorRequestV1 &request,
    game::ZhongguoManagerSubordinateSelectorSnapshotV1 &output) noexcept;

ZhongguoBoundedAiManagerAuthorizationV1
AuthorizeZhongguoBoundedAiDirectManagerV1(
    const ZhongguoManagerSubordinateSelectorNativeEnvironmentV1 &environment,
    const ZhongguoManagerSubordinateSelectorAccessV1 &access,
    std::int32_t player_character_id, std::int32_t manager_character_id,
    std::int32_t owner_character_id) noexcept;

std::string SerializeZhongguoManagerSubordinateSelectorV1(
    const game::ZhongguoManagerSubordinateSelectorSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
