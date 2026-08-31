#pragma once

#include "xar_bridge/game_contract.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::game {

enum class ZhongguoCaseSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

template <typename Value> struct ZhongguoTypedValueV1 {
  bool available = false;
  std::optional<Value> value;
  std::string unavailable_reason;

  friend bool operator==(const ZhongguoTypedValueV1 &,
                         const ZhongguoTypedValueV1 &) = default;
};

using ZhongguoTypedIntegerV1 = ZhongguoTypedValueV1<std::int64_t>;
using ZhongguoTypedBooleanV1 = ZhongguoTypedValueV1<bool>;
using ZhongguoTypedStringV1 = ZhongguoTypedValueV1<std::string>;

struct ZhongguoCaseIdentityV1 {
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedBooleanV1 active;
  ZhongguoTypedIntegerV1 revision;
  ZhongguoTypedIntegerV1 timeline_serial;
  ZhongguoTypedIntegerV1 feedback_revision;

  friend bool operator==(const ZhongguoCaseIdentityV1 &,
                         const ZhongguoCaseIdentityV1 &) = default;
};

struct ZhongguoCasePolicyV1 {
  ZhongguoTypedStringV1 policy_id;
  ZhongguoTypedIntegerV1 choice;

  friend bool operator==(const ZhongguoCasePolicyV1 &,
                         const ZhongguoCasePolicyV1 &) = default;
};

struct ZhongguoCaseOperationV1 {
  ZhongguoTypedIntegerV1 operation_id;
  ZhongguoTypedStringV1 operation_key;
  ZhongguoTypedStringV1 hook;
  ZhongguoTypedIntegerV1 pre_state;
  ZhongguoTypedIntegerV1 post_state;

  friend bool operator==(const ZhongguoCaseOperationV1 &,
                         const ZhongguoCaseOperationV1 &) = default;
};

enum class ZhongguoReceiptStatusV1 : std::uint32_t {
  unavailable = 0,
  not_recorded = 1,
  recorded = 2,
};

struct ZhongguoCaseReceiptV1 {
  ZhongguoReceiptStatusV1 status = ZhongguoReceiptStatusV1::unavailable;
  ZhongguoTypedStringV1 key;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 subject_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 state;
  ZhongguoTypedIntegerV1 choice;

  friend bool operator==(const ZhongguoCaseReceiptV1 &,
                         const ZhongguoCaseReceiptV1 &) = default;
};

enum class ZhongguoDeadlineStatusV1 : std::uint32_t {
  unavailable = 0,
  not_scheduled = 1,
  pending = 2,
  expired = 3,
};

struct ZhongguoCaseDeadlineV1 {
  ZhongguoDeadlineStatusV1 status = ZhongguoDeadlineStatusV1::unavailable;
  ZhongguoTypedIntegerV1 target_character_id;
  ZhongguoTypedIntegerV1 owner_character_id;
  ZhongguoTypedIntegerV1 cycle_serial;
  ZhongguoTypedIntegerV1 case_serial;
  ZhongguoTypedIntegerV1 expected_state;
  ZhongguoTypedIntegerV1 days;
  ZhongguoTypedBooleanV1 pending;
  ZhongguoTypedBooleanV1 expired;
  ZhongguoTypedIntegerV1 open_date_raw;
  ZhongguoTypedIntegerV1 due_date_raw;
  ZhongguoTypedStringV1 on_due_operation;

  friend bool operator==(const ZhongguoCaseDeadlineV1 &,
                         const ZhongguoCaseDeadlineV1 &) = default;
};

struct ZhongguoCaseReadinessV1 {
  bool player_binding_ready = false;
  bool case_identity_ready = false;
  bool policy_ready = false;
  bool operation_ready = false;
  bool receipt_ready = false;
  bool deadline_identity_ready = false;
  bool deadline_due_date_ready = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(const ZhongguoCaseReadinessV1 &,
                         const ZhongguoCaseReadinessV1 &) = default;
};

struct ZhongguoCaseSnapshotV1 {
  ZhongguoCaseSnapshotStatusV1 status =
      ZhongguoCaseSnapshotStatusV1::unavailable;
  std::string case_kind;
  std::string request_nonce;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t player_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::optional<std::int32_t> requested_owner_character_id;
  ZhongguoCaseIdentityV1 case_identity;
  ZhongguoCasePolicyV1 policy;
  ZhongguoCaseOperationV1 operation;
  ZhongguoCaseReceiptV1 receipt;
  ZhongguoCaseDeadlineV1 deadline;
  ZhongguoCaseReadinessV1 readiness;
  std::string unavailable_reason;

  friend bool operator==(const ZhongguoCaseSnapshotV1 &,
                         const ZhongguoCaseSnapshotV1 &) = default;
};

struct ZhongguoCaseFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  std::int32_t played_character_id = -1;

  friend bool operator==(const ZhongguoCaseFrameV1 &,
                         const ZhongguoCaseFrameV1 &) = default;
};

enum class ReadZhongguoCaseSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kZhongguoCaseSnapshotV1Capability =
    "game.command.query-zhongguo-case-snapshot-v1";
inline constexpr std::string_view kZhongguoCaseSnapshotV1Step =
    "query-zhongguo-case-snapshot-v1";
inline constexpr std::string_view kZhongguoCaseSnapshotV1CaseKind =
    "zhongguo.b1.performance";
inline constexpr std::string_view kZhongguoCaseSnapshotV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view kZhongguoCaseSnapshotV1ExecutableSha256 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kZhongguoCaseSnapshotV1BackendId =
    "ck3-1.19.0.6-native-zhongguo-case-snapshot-v1";
inline constexpr std::string_view kZhongguoCaseSnapshotV1ConsumerId =
    "xar-autoplayer-zhongguo-case-snapshot-v1";
inline constexpr std::string_view kZhongguoCaseSnapshotV1AllowlistId =
    "zg361-b1-performance-case-v1";

inline constexpr std::uintptr_t kZhongguoVariableContextForScopeRva =
    0x3329A40;
inline constexpr std::uintptr_t kZhongguoVariableIdentifierTableRva =
    0x3B971A0;
inline constexpr std::uintptr_t kZhongguoVariableIdentifierLookupRva =
    0x3B97020;
inline constexpr std::uintptr_t kZhongguoVariableIdentifierNameRva =
    0x3B97090;
inline constexpr std::uintptr_t kZhongguoCharacterStorageSlotRva =
    0x570C130;
inline constexpr std::uintptr_t kZhongguoCharacterFallbackSlotRva =
    0x570C138;

inline constexpr std::array<std::string_view, 26>
    kZhongguoCaseSnapshotV1VariableAllowlist{
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
        "zg361_b1_pending_deadline_owner",
        "zg361_b1_pending_deadline_subject",
        "zg361_b1_pending_deadline_ticket_cycle",
        "zg361_b1_pending_deadline_ticket_case",
        "zg361_b1_pending_deadline_ticket_state",
        "zg361_b1_pending_deadline_days",
        "zg361_b1_pending_deadline_pending",
        "zg361_b1_pending_deadline_expired",
        "zg361_b1_pending_open_date",
    };

struct ZhongguoNativeStringView32V1 {
  const char *data = nullptr;
  std::int32_t size = 0;
  std::int32_t pad = 0;
};

struct ZhongguoEventTarget16V1 {
  std::uint16_t kind = 0;
  std::array<std::uint8_t, 6> reserved{};
  std::int64_t payload = 0;
};
static_assert(sizeof(ZhongguoEventTarget16V1) == 0x10);

using NativeZhongguoVariableContextForScopeV1 =
    void *(*)(const ZhongguoEventTarget16V1 *);
using NativeZhongguoGetVariableIdentifierTableV1 = void *(*)();
using NativeZhongguoLookupVariableIdentifierV1 = std::int32_t *(*) (
    void *, std::int32_t *, const ZhongguoNativeStringView32V1 *);
using NativeZhongguoVariableIdentifierNameV1 =
    const std::string *(*)(void *, std::int32_t);

struct ZhongguoCaseNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_function_overrides = false;
  NativeZhongguoVariableContextForScopeV1 variable_context_for_scope = nullptr;
  NativeZhongguoGetVariableIdentifierTableV1 variable_identifier_table =
      nullptr;
  NativeZhongguoLookupVariableIdentifierV1 variable_identifier_lookup =
      nullptr;
  NativeZhongguoVariableIdentifierNameV1 variable_identifier_name = nullptr;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
};

struct ZhongguoRawVariableV1 {
  bool present = false;
  std::uint16_t kind = 0;
  std::int64_t payload = 0;

  friend bool operator==(const ZhongguoRawVariableV1 &,
                         const ZhongguoRawVariableV1 &) = default;
};

using CaptureZhongguoCaseFrameV1 = bool (*)(
    void *, game::ZhongguoCaseFrameV1 &) noexcept;
using IsZhongguoCaseMainThreadV1 = bool (*)(void *) noexcept;
using ReadZhongguoCaseMemoryV1 = bool (*)(
    void *, const void *, void *, std::size_t) noexcept;
using ValidateZhongguoCharacterV1 = bool (*)(
    void *, std::int32_t) noexcept;
using ReadZhongguoAllowlistedVariableV1 = bool (*)(
    void *, std::int32_t, std::string_view,
    ZhongguoRawVariableV1 &) noexcept;

struct ZhongguoCaseAccessV1 {
  void *context = nullptr;
  CaptureZhongguoCaseFrameV1 capture_frame = nullptr;
  IsZhongguoCaseMainThreadV1 is_main_thread = nullptr;
  ReadZhongguoCaseMemoryV1 read_memory = nullptr;
  // Both callbacks are fixture-only. Production resolves the frozen ABI above
  // and never accepts a caller-supplied variable name.
  ValidateZhongguoCharacterV1 validate_character = nullptr;
  ReadZhongguoAllowlistedVariableV1 read_allowlisted_variable = nullptr;
};

struct ZhongguoCaseSnapshotRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t subject_character_id = -1;
  std::optional<std::int32_t> owner_character_id;
  std::string case_kind;
  std::string request_nonce;
};

ZhongguoCaseNativeEnvironmentV1 BindZhongguoCaseNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadZhongguoCaseSnapshotResultV1 ReadZhongguoCaseSnapshotV1(
    const ZhongguoCaseNativeEnvironmentV1 &environment,
    const ZhongguoCaseAccessV1 &access,
    const ZhongguoCaseSnapshotRequestV1 &request,
    game::ZhongguoCaseSnapshotV1 &output) noexcept;

std::string SerializeZhongguoCaseSnapshotV1(
    const game::ZhongguoCaseSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
