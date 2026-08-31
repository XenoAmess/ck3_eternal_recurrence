#pragma once

#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoAiOwnedCaseSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct ZhongguoAiOwnerEligibilityV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedBooleanV1 owner_alive;
  ZhongguoTypedBooleanV1 owner_is_ai;
  ZhongguoTypedIntegerV1 primary_title_id;
  ZhongguoTypedIntegerV1 primary_title_tier_raw;
  ZhongguoTypedStringV1 primary_title_tier_key;
  ZhongguoTypedStringV1 government_key;
  ZhongguoTypedIntegerV1 subject_immediate_liege_character_id;
  ZhongguoTypedBooleanV1 subject_is_direct_subject;
  ZhongguoTypedBooleanV1 authorized;

  friend bool operator==(const ZhongguoAiOwnerEligibilityV1 &,
                         const ZhongguoAiOwnerEligibilityV1 &) = default;
};

struct ZhongguoAiOwnedCaseStageV1 {
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedStringV1 key;
  ZhongguoTypedBooleanV1 active;

  friend bool operator==(const ZhongguoAiOwnedCaseStageV1 &,
                         const ZhongguoAiOwnedCaseStageV1 &) = default;
};

struct ZhongguoAiOwnedCaseRouteV1 {
  ZhongguoTypedStringV1 kind;
  ZhongguoTypedBooleanV1 visible_event_allowed;
  ZhongguoTypedBooleanV1 owner_is_ai;
  ZhongguoTypedBooleanV1 manager_eligible;
  ZhongguoTypedBooleanV1 direct_subject_eligible;

  friend bool operator==(const ZhongguoAiOwnedCaseRouteV1 &,
                         const ZhongguoAiOwnedCaseRouteV1 &) = default;
};

struct ZhongguoAiOwnedCaseReadinessV1 {
  bool owner_eligibility_ready = false;
  bool case_identity_ready = false;
  bool stage_ready = false;
  bool route_ready = false;
  bool receipt_ready = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(const ZhongguoAiOwnedCaseReadinessV1 &,
                         const ZhongguoAiOwnedCaseReadinessV1 &) = default;
};

struct ZhongguoAiOwnedCaseSnapshotV1 {
  ZhongguoAiOwnedCaseSnapshotStatusV1 status =
      ZhongguoAiOwnedCaseSnapshotStatusV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t requested_owner_character_id = -1;
  std::int32_t subject_character_id = -1;
  ZhongguoAiOwnerEligibilityV1 owner_eligibility;
  ZhongguoCaseIdentityV1 case_identity;
  ZhongguoAiOwnedCaseStageV1 stage;
  ZhongguoAiOwnedCaseRouteV1 route;
  ZhongguoCasePolicyV1 policy;
  ZhongguoCaseOperationV1 operation;
  ZhongguoCaseReceiptV1 receipt;
  ZhongguoAiOwnedCaseReadinessV1 readiness;
  std::string unavailable_reason;

  friend bool operator==(const ZhongguoAiOwnedCaseSnapshotV1 &,
                         const ZhongguoAiOwnedCaseSnapshotV1 &) = default;
};

enum class ReadZhongguoAiOwnedCaseSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoAiOwnedCaseSnapshotV1Capability =
    "game.command.query-zhongguo-ai-owned-case-snapshot-v1";
inline constexpr std::string_view kZhongguoAiOwnedCaseSnapshotV1Step =
    "query-zhongguo-ai-owned-case-snapshot-v1";
inline constexpr std::string_view kZhongguoAiOwnedCaseSnapshotV1CaseKind =
    "zhongguo.b1.performance";
inline constexpr std::string_view kZhongguoAiOwnedCaseSnapshotV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-ai-owned-case-snapshot-v1";
inline constexpr std::string_view kZhongguoAiOwnedCaseSnapshotV1ConsumerId =
    "xar-autoplayer-zhongguo-ai-owned-case-snapshot-v1";
inline constexpr std::string_view kZhongguoAiOwnedCaseSnapshotV1AllowlistId =
    "zg361-b1-ai-owned-case-v1";
inline constexpr std::string_view kZhongguoAiOwnedCaseBackgroundRouteV1 =
    "authorized_ai_background";

inline constexpr std::uintptr_t kZhongguoAiCaseLandedTitleStorageSlotRva =
    0x570C410;
inline constexpr std::uintptr_t kZhongguoAiCaseLandedTitleFallbackSlotRva =
    0x570C3F8;
inline constexpr std::uintptr_t kZhongguoAiCaseGovernmentFallbackSlotRva =
    0x570CB50;
inline constexpr std::uintptr_t kZhongguoAiCasePrimaryTitleRva = 0x25F3350;
inline constexpr std::uintptr_t kZhongguoAiCaseImmediateLiegeRva = 0x2613480;
inline constexpr std::uintptr_t kZhongguoAiCaseGovernmentRva = 0x26165B0;
inline constexpr std::uintptr_t kZhongguoAiCaseIsHumanPlayerRva = 0x28BCEB0;

inline constexpr std::array<std::string_view, 17>
    kZhongguoAiOwnedCaseSnapshotV1VariableAllowlist{
        "zg361_b1_case_owner",
        "zg361_b1_case_subject",
        "zg361_b1_cycle_serial",
        "zg361_b1_case_serial",
        "zg361_b1_case_state",
        "zg361_b1_case_active",
        "zg361_b1_case_revision",
        "zg361_b1_case_timeline_serial",
        "zg361_b1_case_feedback_revision",
        "zg361_b1_case_last_operation",
        "zg361_b1_case_last_choice",
        "zg361_b1_roster_lock_receipt_owner",
        "zg361_b1_roster_lock_receipt_subject",
        "zg361_b1_roster_lock_receipt_cycle",
        "zg361_b1_roster_lock_receipt_case",
        "zg361_b1_roster_lock_receipt_state",
        "zg361_b1_roster_lock_receipt_choice",
    };

#if defined(_MSC_VER)
#define XAR_ZHONGGUO_AI_CASE_FASTCALL __fastcall
#else
#define XAR_ZHONGGUO_AI_CASE_FASTCALL
#endif

using NativeZhongguoAiCaseCharacterResolverV1 =
    void *(XAR_ZHONGGUO_AI_CASE_FASTCALL *)(void *character);
using NativeZhongguoAiCaseIsHumanPlayerV1 =
    bool(XAR_ZHONGGUO_AI_CASE_FASTCALL *)(std::int32_t character_id);

#undef XAR_ZHONGGUO_AI_CASE_FASTCALL

struct ZhongguoAiOwnedCaseNativeEnvironmentV1 {
  ZhongguoCaseNativeEnvironmentV1 variables;
  void **landed_title_storage_slot = nullptr;
  void **landed_title_fallback_slot = nullptr;
  void **government_fallback_slot = nullptr;
  NativeZhongguoAiCaseCharacterResolverV1 primary_title = nullptr;
  NativeZhongguoAiCaseCharacterResolverV1 immediate_liege = nullptr;
  NativeZhongguoAiCaseCharacterResolverV1 government = nullptr;
  NativeZhongguoAiCaseIsHumanPlayerV1 is_human_player = nullptr;
};

struct ZhongguoAiOwnerEligibilityObservationV1 {
  std::int32_t owner_character_id = -1;
  bool owner_alive = false;
  bool owner_is_ai = false;
  std::int32_t primary_title_id = -1;
  std::int32_t primary_title_tier_raw = 0;
  std::string primary_title_tier_key;
  std::string government_key;
  std::int32_t subject_immediate_liege_character_id = -1;

  friend bool operator==(const ZhongguoAiOwnerEligibilityObservationV1 &,
                         const ZhongguoAiOwnerEligibilityObservationV1 &) =
      default;
};

using ObserveZhongguoAiOwnerEligibilityV1 = bool (*)(
    void *, std::int32_t, std::int32_t,
    ZhongguoAiOwnerEligibilityObservationV1 &) noexcept;

struct ZhongguoAiOwnedCaseAccessV1 {
  ZhongguoCaseAccessV1 variables;
  // Fixture-only exact semantic replacement for the native relationship,
  // control, government and title observation. Production leaves it null.
  ObserveZhongguoAiOwnerEligibilityV1 observe_owner_eligibility = nullptr;
};

struct ZhongguoAiOwnedCaseSnapshotRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t owner_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::string request_nonce;
};

ZhongguoAiOwnedCaseNativeEnvironmentV1
BindZhongguoAiOwnedCaseNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoAiOwnedCaseSnapshotResultV1
ReadZhongguoAiOwnedCaseSnapshotV1(
    const ZhongguoAiOwnedCaseNativeEnvironmentV1 &environment,
    const ZhongguoAiOwnedCaseAccessV1 &access,
    const ZhongguoAiOwnedCaseSnapshotRequestV1 &request,
    game::ZhongguoAiOwnedCaseSnapshotV1 &output) noexcept;

std::string SerializeZhongguoAiOwnedCaseSnapshotV1(
    const game::ZhongguoAiOwnedCaseSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
