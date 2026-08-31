#include "xar_bridge/zhongguo_result_case_snapshot_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string_view>
#include <utility>

namespace xar::ck3_11906 {
namespace {

constexpr std::int64_t kFixedScale = 100'000;
constexpr std::int32_t kMaximumComponents = 4'194'304;
constexpr std::int32_t kMaximumVariableRows = 65'536;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;

enum VariableIndex : std::size_t {
  case_owner = 0,
  cycle_serial,
  case_serial,
  case_state,
  grade,
  absolute_grade,
  kpi_frozen,
  rank_frozen,
  cohort_n_frozen,
  delivery_method,
  objection_recorded,
  settlement_posted_serial,
  appeal_open,
};

using RawRows =
    std::array<ZhongguoResultRawVariableV1,
               kZhongguoResultCaseSnapshotV1VariableAllowlist.size()>;

bool GuardedDirectRead(const void *address, void *output,
                       std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

bool ReadBytes(const ZhongguoResultAccessV1 &access, const void *address,
               void *output, std::size_t size) noexcept {
  if (access.read_memory != nullptr) {
    return access.read_memory(access.context, address, output, size);
  }
  return GuardedDirectRead(address, output, size);
}

bool CheckedAddress(const void *base, std::size_t offset,
                    const void *&output) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > std::numeric_limits<std::uintptr_t>::max() - value) {
    output = nullptr;
    return false;
  }
  output = reinterpret_cast<const void *>(value + offset);
  return true;
}

template <typename Value>
bool ReadValue(const ZhongguoResultAccessV1 &access, const void *base,
               std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const ZhongguoResultNativeEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) {
    return environment.variable_context_for_scope == nullptr &&
           environment.variable_identifier_table == nullptr &&
           environment.variable_identifier_lookup == nullptr &&
           environment.variable_identifier_name == nullptr &&
           environment.character_storage_slot == nullptr &&
           environment.character_fallback_slot == nullptr;
  }
  if (environment.module_base == 0 ||
      environment.variable_context_for_scope == nullptr ||
      environment.variable_identifier_table == nullptr ||
      environment.variable_identifier_lookup == nullptr ||
      environment.variable_identifier_name == nullptr ||
      environment.character_storage_slot == nullptr ||
      environment.character_fallback_slot == nullptr) {
    return false;
  }
  const auto base = environment.module_base;
  return reinterpret_cast<std::uintptr_t>(
             environment.variable_context_for_scope) ==
             base + kZhongguoVariableContextForScopeRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.variable_identifier_table) ==
             base + kZhongguoVariableIdentifierTableRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.variable_identifier_lookup) ==
             base + kZhongguoVariableIdentifierLookupRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.variable_identifier_name) ==
             base + kZhongguoVariableIdentifierNameRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.character_storage_slot) ==
             base + kZhongguoCharacterStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.character_fallback_slot) ==
             base + kZhongguoCharacterFallbackSlotRva;
}

bool ResolveCharacterNative(
    const ZhongguoResultNativeEnvironmentV1 &environment,
    const ZhongguoResultAccessV1 &access,
    std::int32_t character_id) noexcept {
  if (character_id <= 0) {
    return false;
  }
  void *storage = nullptr;
  void *fallback = nullptr;
  if (!ReadBytes(access, environment.character_storage_slot, &storage,
                 sizeof(storage)) ||
      !ReadBytes(access, environment.character_fallback_slot, &fallback,
                 sizeof(fallback)) ||
      storage == nullptr) {
    return false;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadValue(access, storage, kStorageSlotsOffset, slots) ||
      !ReadValue(access, storage, kStorageCapacityOffset, capacity) ||
      slots == nullptr || capacity <= 0 || capacity > kMaximumComponents) {
    return false;
  }
  const auto index = static_cast<std::uint32_t>(character_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) {
    return false;
  }
  void *character = nullptr;
  if (!ReadValue(access, slots,
                 static_cast<std::size_t>(index) * kStorageSlotStride +
                     kStorageObjectOffset,
                 character) ||
      character == nullptr || character == fallback) {
    return false;
  }
  std::int32_t identity = -1;
  return ReadValue(access, character, kCharacterIdentityOffset, identity) &&
         identity == character_id;
}

bool ValidateCharacter(
    const ZhongguoResultNativeEnvironmentV1 &environment,
    const ZhongguoResultAccessV1 &access,
    std::int32_t character_id) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.validate_character != nullptr &&
           access.validate_character(access.context, character_id);
  }
  return ResolveCharacterNative(environment, access, character_id);
}

bool ResolveVariableIdentifier(
    const ZhongguoResultNativeEnvironmentV1 &environment,
    std::string_view key, std::int32_t &identifier) noexcept {
  void *const table = environment.variable_identifier_table();
  if (table == nullptr || key.empty() ||
      key.size() >
          static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max())) {
    return false;
  }
  const ZhongguoNativeStringView32V1 view{
      key.data(), static_cast<std::int32_t>(key.size()), 0};
  identifier = -1;
  if (environment.variable_identifier_lookup(table, &identifier, &view) ==
          nullptr ||
      identifier < 0) {
    return false;
  }
  const auto *const name =
      environment.variable_identifier_name(table, identifier);
  return name != nullptr && *name == key;
}

bool FindVariableValue(const ZhongguoResultAccessV1 &access, void *context,
                       std::int32_t identifier,
                       ZhongguoResultRawVariableV1 &output) noexcept {
  output = {};
  if (context == nullptr) {
    return false;
  }
  void *data = nullptr;
  std::int32_t count = 0;
  if (!ReadValue(access, context, 0x10, data) ||
      !ReadValue(access, context, 0x1C, count) || count < 0 ||
      count > kMaximumVariableRows || (count != 0 && data == nullptr)) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const void *row = nullptr;
    if (!CheckedAddress(data, static_cast<std::size_t>(index) * 0x20, row)) {
      return false;
    }
    std::int32_t row_identifier = -1;
    if (!ReadValue(access, row, 0x08, row_identifier)) {
      return false;
    }
    if (row_identifier != identifier) {
      continue;
    }
    if (output.present || !ReadValue(access, row, 0x10, output.kind) ||
        !ReadValue(access, row, 0x18, output.payload)) {
      return false;
    }
    output.present = true;
  }
  return true;
}

bool ReadAllowlistedVariableNative(
    const ZhongguoResultNativeEnvironmentV1 &environment,
    const ZhongguoResultAccessV1 &access, std::int32_t character_id,
    std::string_view key, ZhongguoResultRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) {
    return false;
  }
  // The only readable scope is the paused played character.  Owner is data
  // inside that scope and never becomes a caller-selectable read target.
  const ZhongguoEventTarget16V1 target{4, {}, character_id};
  void *const context = environment.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

bool ReadAllowlistedRows(
    const ZhongguoResultNativeEnvironmentV1 &environment,
    const ZhongguoResultAccessV1 &access, std::int32_t character_id,
    RawRows &output) noexcept {
  for (std::size_t index = 0;
       index < kZhongguoResultCaseSnapshotV1VariableAllowlist.size();
       ++index) {
    const auto key =
        kZhongguoResultCaseSnapshotV1VariableAllowlist[index];
    const bool read = environment.offline_fixture_function_overrides
                          ? access.read_allowlisted_variable != nullptr &&
                                access.read_allowlisted_variable(
                                    access.context, character_id, key,
                                    output[index])
                          : ReadAllowlistedVariableNative(
                                environment, access, character_id, key,
                                output[index]);
    if (!read) {
      return false;
    }
  }
  return true;
}

template <typename Value>
void SetUnavailable(game::ZhongguoTypedValueV1<Value> &field,
                    std::string_view reason) {
  field.available = false;
  field.value.reset();
  field.unavailable_reason.assign(reason);
}

template <typename Value>
void SetAvailable(game::ZhongguoTypedValueV1<Value> &field, Value value) {
  field.available = true;
  field.value = std::move(value);
  field.unavailable_reason.clear();
}

void DecodeInteger(const ZhongguoResultRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1 || raw.payload % kFixedScale != 0) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload / kFixedScale);
  }
}

void DecodeQ100000(const ZhongguoResultRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload);
  }
}

void DecodeBoolean(const ZhongguoResultRawVariableV1 &raw,
                   game::ZhongguoTypedBooleanV1 &field,
                   bool absent_is_false = false) {
  if (!raw.present && absent_is_false) {
    SetAvailable(field, false);
    return;
  }
  game::ZhongguoTypedIntegerV1 integer;
  DecodeInteger(raw, integer);
  if (!integer.available) {
    SetUnavailable(field, integer.unavailable_reason);
  } else if (*integer.value != 0 && *integer.value != 1) {
    SetUnavailable(field, "value_out_of_range");
  } else {
    SetAvailable(field, *integer.value == 1);
  }
}

void DecodeCharacter(
    const ZhongguoResultNativeEnvironmentV1 &environment,
    const ZhongguoResultAccessV1 &access,
    const ZhongguoResultRawVariableV1 &raw,
    game::ZhongguoTypedIntegerV1 &field) noexcept {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 4) {
    SetUnavailable(field, "value_type_mismatch");
  } else if (raw.payload <= 0 ||
             raw.payload > std::numeric_limits<std::int32_t>::max() ||
             !ValidateCharacter(environment, access,
                                static_cast<std::int32_t>(raw.payload))) {
    SetUnavailable(field, "value_out_of_range");
  } else {
    SetAvailable(field, raw.payload);
  }
}

void MakeAllFieldsUnavailable(game::ZhongguoResultCaseSnapshotV1 &output,
                              std::string_view reason) {
  SetUnavailable(output.case_identity.owner_character_id, reason);
  SetUnavailable(output.case_identity.subject_character_id, reason);
  SetUnavailable(output.case_identity.cycle_serial, reason);
  SetUnavailable(output.case_identity.case_serial, reason);
  SetUnavailable(output.case_identity.state, reason);
  SetUnavailable(output.case_identity.grade, reason);
  SetUnavailable(output.notice.absolute_grade, reason);
  SetUnavailable(output.notice.kpi_frozen_q100000, reason);
  SetUnavailable(output.notice.rank_frozen, reason);
  SetUnavailable(output.notice.cohort_n_frozen, reason);
  SetUnavailable(output.delivery.method, reason);
  SetUnavailable(output.delivery.objection_recorded, reason);
  SetUnavailable(output.delivery.settlement_posted_serial, reason);
  SetUnavailable(output.delivery.appeal_open, reason);
}

void InitializeEnvelope(const ZhongguoResultCaseSnapshotRequestV1 &request,
                        const ZhongguoResultFrameV1 *frame,
                        game::ZhongguoResultCaseSnapshotV1 &output) {
  output = {};
  output.case_kind = kZhongguoResultCaseSnapshotV1CaseKind;
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  output.requested_owner_character_id = request.owner_character_id;
  if (frame != nullptr) {
    output.date_raw = frame->date_raw;
    output.paused = frame->paused;
    output.player_character_id = frame->played_character_id;
    output.subject_character_id = frame->played_character_id;
  }
  MakeAllFieldsUnavailable(output, "case_unavailable");
}

void SetTopUnavailable(game::ZhongguoResultCaseSnapshotV1 &output,
                       std::string_view reason,
                       bool same_frame_ready = false) {
  output.status = game::ZhongguoResultCaseSnapshotStatusV1::unavailable;
  MakeAllFieldsUnavailable(output, "case_unavailable");
  output.readiness = {};
  output.readiness.same_frame_ready = same_frame_ready;
  output.unavailable_reason.assign(reason);
}

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) {
    return false;
  }
  for (std::size_t index = 0; index < value.size(); ++index) {
    const char character = value[index];
    const bool alpha = (character >= 'a' && character <= 'z') ||
                       (character >= 'A' && character <= 'Z');
    const bool digit = character >= '0' && character <= '9';
    const bool punctuation = character == '.' || character == '_' ||
                             character == ':' || character == '-';
    if ((!alpha && !digit && !punctuation) ||
        (index == 0 && !alpha && !digit)) {
      return false;
    }
  }
  return true;
}

bool ValidRequest(
    const ZhongguoResultCaseSnapshotRequestV1 &request) noexcept {
  return request.expected_snapshot_revision > 0 &&
         request.owner_character_id > 0 && ValidNonce(request.request_nonce);
}

bool AllCoreAbsent(const RawRows &rows) noexcept {
  return !rows[case_owner].present && !rows[cycle_serial].present &&
         !rows[case_serial].present && !rows[case_state].present &&
         !rows[grade].present;
}

bool IntegerInRange(const game::ZhongguoTypedIntegerV1 &field,
                    std::int64_t minimum, std::int64_t maximum) noexcept {
  return field.available && field.value.has_value() &&
         *field.value >= minimum && *field.value <= maximum;
}

bool IntegerEquals(const game::ZhongguoTypedIntegerV1 &field,
                   std::int64_t expected) noexcept {
  return field.available && field.value.has_value() &&
         *field.value == expected;
}

bool BooleanEquals(const game::ZhongguoTypedBooleanV1 &field,
                   bool expected) noexcept {
  return field.available && field.value.has_value() &&
         *field.value == expected;
}

bool DeliveryMatchesProductMatrix(
    const game::ZhongguoResultCaseSnapshotV1 &output) noexcept {
  if (!IntegerEquals(output.case_identity.grade, 1) ||
      !output.delivery.method.available ||
      !output.delivery.objection_recorded.available ||
      !output.delivery.settlement_posted_serial.available ||
      !output.delivery.appeal_open.available) {
    return false;
  }
  const auto state = *output.case_identity.state.value;
  const auto method = *output.delivery.method.value;
  const auto settlement = *output.delivery.settlement_posted_serial.value;
  const auto case_id = *output.case_identity.case_serial.value;
  const auto objection = *output.delivery.objection_recorded.value;
  const auto appeal = *output.delivery.appeal_open.value;
  const bool open = state == 1 && method == 0 && settlement == 0 &&
                    !appeal && !objection;
  const bool signed_a = state == 3 && method == 1 &&
                        settlement == case_id && appeal && !objection;
  const bool signed_b = state == 3 && method == 2 &&
                        settlement == case_id && appeal && objection;
  const bool refused_c = state == 2 && method == 3 && settlement == 0 &&
                         !appeal && !objection;
  return open || signed_a || signed_b || refused_c;
}

bool ComponentGate(
    const game::ZhongguoResultCaseReadinessV1 &value) noexcept {
  return value.player_subject_binding_ready && value.owner_binding_ready &&
         value.case_identity_ready && value.notice_facts_ready &&
         value.delivery_state_ready && value.same_frame_ready;
}

} // namespace

ZhongguoResultNativeEnvironmentV1 BindZhongguoResultNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base,
                                             exact_build_admitted);
}

game::ReadZhongguoResultCaseSnapshotResultV1
ReadZhongguoResultCaseSnapshotV1(
    const ZhongguoResultNativeEnvironmentV1 &environment,
    const ZhongguoResultAccessV1 &access,
    const ZhongguoResultCaseSnapshotRequestV1 &request,
    game::ZhongguoResultCaseSnapshotV1 &output) noexcept {
  try {
    InitializeEnvelope(request, nullptr, output);
    if (!ValidRequest(request) || !EnvironmentIsExact(environment)) {
      SetTopUnavailable(output, "unsupported_build");
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetTopUnavailable(output, "requires_application_main");
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    if (environment.offline_fixture_function_overrides &&
        (access.validate_character == nullptr ||
         access.read_allowlisted_variable == nullptr)) {
      SetTopUnavailable(output, "internal_error");
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }

    ZhongguoResultFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    InitializeEnvelope(request, &before, output);
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    if (!before.paused) {
      SetTopUnavailable(output, "requires_paused");
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0 ||
        !ValidateCharacter(environment, access,
                           before.played_character_id)) {
      SetTopUnavailable(output, "map_not_ready");
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }

    RawRows first{};
    RawRows second{};
    if (!ReadAllowlistedRows(environment, access,
                             before.played_character_id, first)) {
      SetTopUnavailable(output, "variable_identifier_unavailable");
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    if (!ReadAllowlistedRows(environment, access,
                             before.played_character_id, second)) {
      SetTopUnavailable(output, "variable_context_unavailable");
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    ZhongguoResultFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first != second) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    output.readiness.same_frame_ready = true;

    if (AllCoreAbsent(first)) {
      SetTopUnavailable(output, "case_not_found", true);
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }

    DecodeCharacter(environment, access, first[case_owner],
                    output.case_identity.owner_character_id);
    SetAvailable(output.case_identity.subject_character_id,
                 static_cast<std::int64_t>(before.played_character_id));
    DecodeInteger(first[cycle_serial], output.case_identity.cycle_serial);
    DecodeInteger(first[case_serial], output.case_identity.case_serial);
    DecodeInteger(first[case_state], output.case_identity.state);
    DecodeInteger(first[grade], output.case_identity.grade);

    const bool core_valid =
        output.case_identity.owner_character_id.available &&
        IntegerEquals(output.case_identity.subject_character_id,
                      before.played_character_id) &&
        IntegerInRange(output.case_identity.cycle_serial, 1,
                       std::numeric_limits<std::int64_t>::max()) &&
        IntegerInRange(output.case_identity.case_serial, 1, 999'999) &&
        IntegerInRange(output.case_identity.state, 1, 5) &&
        IntegerInRange(output.case_identity.grade, 1, 3);
    if (!core_valid) {
      SetTopUnavailable(output, "case_inconsistent", true);
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    output.readiness.player_subject_binding_ready = true;
    output.readiness.case_identity_ready = true;

    const auto actual_owner = static_cast<std::int32_t>(
        *output.case_identity.owner_character_id.value);
    if (actual_owner == before.played_character_id) {
      SetTopUnavailable(output, "not_received_self", true);
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    if (actual_owner != request.owner_character_id) {
      SetTopUnavailable(output, "owner_filter_mismatch", true);
      return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
    }
    output.readiness.owner_binding_ready = true;

    DecodeInteger(first[absolute_grade], output.notice.absolute_grade);
    DecodeQ100000(first[kpi_frozen], output.notice.kpi_frozen_q100000);
    DecodeInteger(first[rank_frozen], output.notice.rank_frozen);
    DecodeInteger(first[cohort_n_frozen], output.notice.cohort_n_frozen);
    output.readiness.notice_facts_ready =
        IntegerInRange(output.notice.absolute_grade, 1, 3) &&
        output.notice.kpi_frozen_q100000.available &&
        IntegerInRange(output.notice.rank_frozen, 1,
                       std::numeric_limits<std::int64_t>::max()) &&
        IntegerInRange(output.notice.cohort_n_frozen, 1,
                       std::numeric_limits<std::int64_t>::max()) &&
        *output.notice.rank_frozen.value <=
            *output.notice.cohort_n_frozen.value;

    DecodeInteger(first[delivery_method], output.delivery.method);
    DecodeBoolean(first[objection_recorded],
                  output.delivery.objection_recorded, true);
    DecodeInteger(first[settlement_posted_serial],
                  output.delivery.settlement_posted_serial);
    DecodeBoolean(first[appeal_open], output.delivery.appeal_open);
    const bool delivery_fields_in_range =
        IntegerInRange(output.delivery.method, 0, 3) &&
        output.delivery.objection_recorded.available &&
        IntegerInRange(output.delivery.settlement_posted_serial, 0,
                       999'999) &&
        output.delivery.appeal_open.available;
    output.readiness.delivery_state_ready =
        delivery_fields_in_range && DeliveryMatchesProductMatrix(output);

    output.status = game::ZhongguoResultCaseSnapshotStatusV1::available;
    output.unavailable_reason.clear();
    output.readiness.ready = ComponentGate(output.readiness);
    return game::ReadZhongguoResultCaseSnapshotResultV1::available;
  } catch (...) {
    InitializeEnvelope(request, nullptr, output);
    SetTopUnavailable(output, "internal_error");
    return game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
