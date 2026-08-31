#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <string_view>

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
  case_subject,
  cycle_serial,
  case_serial,
  case_state,
  case_active,
  case_revision,
  case_timeline,
  case_feedback,
  case_last_operation,
  case_last_choice,
  receipt_owner,
  receipt_subject,
  receipt_cycle,
  receipt_case,
  receipt_state,
  receipt_choice,
  deadline_owner,
  deadline_subject,
  deadline_cycle,
  deadline_case,
  deadline_state,
  deadline_days,
  deadline_pending,
  deadline_expired,
  deadline_open_date,
};

using RawRows = std::array<ZhongguoRawVariableV1,
                           kZhongguoCaseSnapshotV1VariableAllowlist.size()>;

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

bool ReadBytes(const ZhongguoCaseAccessV1 &access, const void *address,
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
bool ReadValue(const ZhongguoCaseAccessV1 &access, const void *base,
               std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const ZhongguoCaseNativeEnvironmentV1 &environment) noexcept {
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
    const ZhongguoCaseNativeEnvironmentV1 &environment,
    const ZhongguoCaseAccessV1 &access, std::int32_t character_id) noexcept {
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
    const ZhongguoCaseNativeEnvironmentV1 &environment,
    const ZhongguoCaseAccessV1 &access, std::int32_t character_id) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.validate_character != nullptr &&
           access.validate_character(access.context, character_id);
  }
  return ResolveCharacterNative(environment, access, character_id);
}

bool ResolveVariableIdentifier(
    const ZhongguoCaseNativeEnvironmentV1 &environment,
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

bool FindVariableValue(const ZhongguoCaseAccessV1 &access, void *context,
                       std::int32_t identifier,
                       ZhongguoRawVariableV1 &output) noexcept {
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
    const ZhongguoCaseNativeEnvironmentV1 &environment,
    const ZhongguoCaseAccessV1 &access, std::int32_t character_id,
    std::string_view key, ZhongguoRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) {
    return false;
  }
  const ZhongguoEventTarget16V1 target{4, {}, character_id};
  void *const context = environment.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

bool ReadAllowlistedRows(
    const ZhongguoCaseNativeEnvironmentV1 &environment,
    const ZhongguoCaseAccessV1 &access, std::int32_t character_id,
    RawRows &output) noexcept {
  for (std::size_t index = 0;
       index < kZhongguoCaseSnapshotV1VariableAllowlist.size(); ++index) {
    const auto key = kZhongguoCaseSnapshotV1VariableAllowlist[index];
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

void DecodeInteger(const ZhongguoRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1 || raw.payload % kFixedScale != 0) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload / kFixedScale);
  }
}

void DecodeBoolean(const ZhongguoRawVariableV1 &raw,
                   game::ZhongguoTypedBooleanV1 &field) {
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
    const ZhongguoCaseNativeEnvironmentV1 &environment,
    const ZhongguoCaseAccessV1 &access, const ZhongguoRawVariableV1 &raw,
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

// No exact-build evidence currently identifies the event-target kind and
// payload conversion used by `set_variable = current_date`.  The provider
// observes the two explicit allowlisted variables but must not reinterpret a
// numeric or opaque payload as CK3 date_raw until that ABI is frozen.
void DecodePersistedDate(const ZhongguoRawVariableV1 &raw,
                         game::ZhongguoTypedIntegerV1 &field) {
  SetUnavailable(field,
                 raw.present ? "value_type_mismatch" : "variable_absent");
}

bool IntegerEquals(const game::ZhongguoTypedIntegerV1 &field,
                   std::int64_t expected) noexcept {
  return field.available && field.value.has_value() &&
         *field.value == expected;
}

bool AllCoreAbsent(const RawRows &rows) noexcept {
  return !rows[case_owner].present && !rows[case_subject].present &&
         !rows[cycle_serial].present && !rows[case_serial].present &&
         !rows[case_state].present && !rows[case_active].present;
}

void MakeAllFieldsUnavailable(game::ZhongguoCaseSnapshotV1 &output,
                              std::string_view reason) {
  SetUnavailable(output.case_identity.owner_character_id, reason);
  SetUnavailable(output.case_identity.subject_character_id, reason);
  SetUnavailable(output.case_identity.cycle_serial, reason);
  SetUnavailable(output.case_identity.case_serial, reason);
  SetUnavailable(output.case_identity.state, reason);
  SetUnavailable(output.case_identity.active, reason);
  SetUnavailable(output.case_identity.revision, reason);
  SetUnavailable(output.case_identity.timeline_serial, reason);
  SetUnavailable(output.case_identity.feedback_revision, reason);
  SetUnavailable(output.policy.policy_id, reason);
  SetUnavailable(output.policy.choice, reason);
  SetUnavailable(output.operation.operation_id, reason);
  SetUnavailable(output.operation.operation_key, reason);
  SetUnavailable(output.operation.hook, reason);
  SetUnavailable(output.operation.pre_state, reason);
  SetUnavailable(output.operation.post_state, reason);
  output.receipt.status = game::ZhongguoReceiptStatusV1::unavailable;
  SetUnavailable(output.receipt.key, reason);
  SetUnavailable(output.receipt.owner_character_id, reason);
  SetUnavailable(output.receipt.subject_character_id, reason);
  SetUnavailable(output.receipt.cycle_serial, reason);
  SetUnavailable(output.receipt.case_serial, reason);
  SetUnavailable(output.receipt.state, reason);
  SetUnavailable(output.receipt.choice, reason);
  output.deadline.status = game::ZhongguoDeadlineStatusV1::unavailable;
  SetUnavailable(output.deadline.target_character_id, reason);
  SetUnavailable(output.deadline.owner_character_id, reason);
  SetUnavailable(output.deadline.cycle_serial, reason);
  SetUnavailable(output.deadline.case_serial, reason);
  SetUnavailable(output.deadline.expected_state, reason);
  SetUnavailable(output.deadline.days, reason);
  SetUnavailable(output.deadline.pending, reason);
  SetUnavailable(output.deadline.expired, reason);
  SetUnavailable(output.deadline.open_date_raw, reason);
  SetUnavailable(output.deadline.due_date_raw, reason);
  SetUnavailable(output.deadline.on_due_operation, reason);
}

void MakeReceiptUnavailable(game::ZhongguoCaseReceiptV1 &receipt,
                            std::string_view reason) {
  SetUnavailable(receipt.key, reason);
  SetUnavailable(receipt.owner_character_id, reason);
  SetUnavailable(receipt.subject_character_id, reason);
  SetUnavailable(receipt.cycle_serial, reason);
  SetUnavailable(receipt.case_serial, reason);
  SetUnavailable(receipt.state, reason);
  SetUnavailable(receipt.choice, reason);
}

void MakeDeadlineUnavailable(game::ZhongguoCaseDeadlineV1 &deadline,
                             std::string_view reason) {
  SetUnavailable(deadline.target_character_id, reason);
  SetUnavailable(deadline.owner_character_id, reason);
  SetUnavailable(deadline.cycle_serial, reason);
  SetUnavailable(deadline.case_serial, reason);
  SetUnavailable(deadline.expected_state, reason);
  SetUnavailable(deadline.days, reason);
  SetUnavailable(deadline.pending, reason);
  SetUnavailable(deadline.expired, reason);
  SetUnavailable(deadline.open_date_raw, reason);
  SetUnavailable(deadline.due_date_raw, reason);
  SetUnavailable(deadline.on_due_operation, reason);
}

void InitializeEnvelope(const ZhongguoCaseSnapshotRequestV1 &request,
                        const game::ZhongguoCaseFrameV1 *frame,
                        game::ZhongguoCaseSnapshotV1 &output) {
  output = {};
  output.case_kind = request.case_kind;
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  output.subject_character_id = request.subject_character_id;
  output.requested_owner_character_id = request.owner_character_id;
  if (frame != nullptr) {
    output.date_raw = frame->date_raw;
    output.paused = frame->paused;
    output.player_character_id = frame->played_character_id;
  }
  MakeAllFieldsUnavailable(output, "case_unavailable");
}

void SetTopUnavailable(game::ZhongguoCaseSnapshotV1 &output,
                       std::string_view reason) {
  output.status = game::ZhongguoCaseSnapshotStatusV1::unavailable;
  MakeAllFieldsUnavailable(output, "case_unavailable");
  output.readiness = {};
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

bool ValidRequest(const ZhongguoCaseSnapshotRequestV1 &request) noexcept {
  return request.expected_snapshot_revision > 0 &&
         request.subject_character_id > 0 &&
         (!request.owner_character_id.has_value() ||
          *request.owner_character_id > 0) &&
         request.case_kind == kZhongguoCaseSnapshotV1CaseKind &&
         ValidNonce(request.request_nonce);
}

bool ComponentGate(const game::ZhongguoCaseReadinessV1 &value) noexcept {
  return value.player_binding_ready && value.case_identity_ready &&
         value.policy_ready && value.operation_ready && value.receipt_ready &&
         value.deadline_identity_ready && value.deadline_due_date_ready &&
         value.same_frame_ready;
}

} // namespace

ZhongguoCaseNativeEnvironmentV1 BindZhongguoCaseNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  ZhongguoCaseNativeEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  if (module_base == 0) {
    return output;
  }
  output.variable_context_for_scope =
      reinterpret_cast<NativeZhongguoVariableContextForScopeV1>(
          module_base + kZhongguoVariableContextForScopeRva);
  output.variable_identifier_table =
      reinterpret_cast<NativeZhongguoGetVariableIdentifierTableV1>(
          module_base + kZhongguoVariableIdentifierTableRva);
  output.variable_identifier_lookup =
      reinterpret_cast<NativeZhongguoLookupVariableIdentifierV1>(
          module_base + kZhongguoVariableIdentifierLookupRva);
  output.variable_identifier_name =
      reinterpret_cast<NativeZhongguoVariableIdentifierNameV1>(
          module_base + kZhongguoVariableIdentifierNameRva);
  output.character_storage_slot =
      reinterpret_cast<void **>(module_base +
                                kZhongguoCharacterStorageSlotRva);
  output.character_fallback_slot =
      reinterpret_cast<void **>(module_base +
                                kZhongguoCharacterFallbackSlotRva);
  return output;
}

game::ReadZhongguoCaseSnapshotResultV1 ReadZhongguoCaseSnapshotV1(
    const ZhongguoCaseNativeEnvironmentV1 &environment,
    const ZhongguoCaseAccessV1 &access,
    const ZhongguoCaseSnapshotRequestV1 &request,
    game::ZhongguoCaseSnapshotV1 &output) noexcept {
  try {
    InitializeEnvelope(request, nullptr, output);
    if (!ValidRequest(request) || !EnvironmentIsExact(environment)) {
      SetTopUnavailable(output, "unsupported_build");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetTopUnavailable(output, "requires_application_main");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }
    if (environment.offline_fixture_function_overrides &&
        (access.validate_character == nullptr ||
         access.read_allowlisted_variable == nullptr)) {
      SetTopUnavailable(output, "internal_error");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }

    game::ZhongguoCaseFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }
    InitializeEnvelope(request, &before, output);
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }
    if (!before.paused) {
      SetTopUnavailable(output, "requires_paused");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0) {
      SetTopUnavailable(output, "map_not_ready");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }
    if (!ValidateCharacter(environment, access,
                           request.subject_character_id)) {
      SetTopUnavailable(output, "subject_not_found");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }

    RawRows first{};
    RawRows second{};
    if (!ReadAllowlistedRows(environment, access,
                             request.subject_character_id, first)) {
      SetTopUnavailable(output, "variable_identifier_unavailable");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }
    if (!ReadAllowlistedRows(environment, access,
                             request.subject_character_id, second)) {
      SetTopUnavailable(output, "variable_context_unavailable");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }
    game::ZhongguoCaseFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first != second) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }
    output.readiness.same_frame_ready = true;

    if (AllCoreAbsent(first)) {
      SetTopUnavailable(output, "case_not_found");
      output.readiness.same_frame_ready = true;
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }

    DecodeCharacter(environment, access, first[case_owner],
                    output.case_identity.owner_character_id);
    DecodeCharacter(environment, access, first[case_subject],
                    output.case_identity.subject_character_id);
    DecodeInteger(first[cycle_serial], output.case_identity.cycle_serial);
    DecodeInteger(first[case_serial], output.case_identity.case_serial);
    DecodeInteger(first[case_state], output.case_identity.state);
    DecodeBoolean(first[case_active], output.case_identity.active);
    DecodeInteger(first[case_revision], output.case_identity.revision);
    DecodeInteger(first[case_timeline],
                  output.case_identity.timeline_serial);
    DecodeInteger(first[case_feedback],
                  output.case_identity.feedback_revision);
    DecodeInteger(first[case_last_operation], output.operation.operation_id);
    DecodeInteger(first[case_last_choice], output.policy.choice);

    const bool identity_ready =
        output.case_identity.owner_character_id.available &&
        output.case_identity.subject_character_id.available &&
        output.case_identity.cycle_serial.available &&
        output.case_identity.case_serial.available &&
        output.case_identity.state.available &&
        output.case_identity.active.available &&
        output.case_identity.revision.available &&
        output.case_identity.timeline_serial.available &&
        output.case_identity.feedback_revision.available &&
        IntegerEquals(output.case_identity.subject_character_id,
                      request.subject_character_id) &&
        *output.case_identity.cycle_serial.value > 0 &&
        *output.case_identity.case_serial.value > 0 &&
        *output.case_identity.state.value > 0 &&
        *output.case_identity.revision.value > 0 &&
        *output.case_identity.timeline_serial.value > 0 &&
        *output.case_identity.feedback_revision.value > 0;
    output.readiness.case_identity_ready = identity_ready;
    if (!identity_ready) {
      SetTopUnavailable(output, "case_not_found");
      output.readiness.same_frame_ready = true;
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }

    const auto owner_id = *output.case_identity.owner_character_id.value;
    output.readiness.player_binding_ready =
        owner_id == before.played_character_id;
    if (!output.readiness.player_binding_ready) {
      MakeAllFieldsUnavailable(output, "case_unavailable");
      SetTopUnavailable(output, "player_binding_mismatch");
      output.readiness.same_frame_ready = true;
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }
    if (request.owner_character_id.has_value() &&
        owner_id != *request.owner_character_id) {
      SetTopUnavailable(output, "owner_filter_mismatch");
      output.readiness.same_frame_ready = true;
      return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
    }

    const std::optional<std::int64_t> operation_id =
        output.operation.operation_id.available
            ? output.operation.operation_id.value
            : std::nullopt;
    if (operation_id == 39 &&
        IntegerEquals(output.policy.choice, 1)) {
      SetAvailable(output.policy.policy_id, std::string("mechanism_039"));
      SetAvailable(output.operation.operation_key,
                   std::string("roster_lock"));
      SetAvailable(output.operation.hook, std::string("roster_lock"));
    } else if (operation_id == 39) {
      SetUnavailable(output.policy.policy_id,
                     "unknown_allowlisted_operation");
      SetAvailable(output.operation.operation_key,
                   std::string("roster_lock"));
      SetAvailable(output.operation.hook, std::string("roster_lock"));
    } else if (operation_id == 0) {
      SetUnavailable(output.policy.policy_id, "no_operation_recorded");
      SetUnavailable(output.operation.operation_key,
                     "no_operation_recorded");
      SetUnavailable(output.operation.hook, "no_operation_recorded");
    } else {
      SetUnavailable(output.policy.policy_id,
                     "unknown_allowlisted_operation");
      SetUnavailable(output.operation.operation_key,
                     "unknown_allowlisted_operation");
      SetUnavailable(output.operation.hook,
                     "unknown_allowlisted_operation");
    }

    DecodeCharacter(environment, access, first[receipt_owner],
                    output.receipt.owner_character_id);
    DecodeCharacter(environment, access, first[receipt_subject],
                    output.receipt.subject_character_id);
    DecodeInteger(first[receipt_cycle], output.receipt.cycle_serial);
    DecodeInteger(first[receipt_case], output.receipt.case_serial);
    DecodeInteger(first[receipt_state], output.receipt.state);
    DecodeInteger(first[receipt_choice], output.receipt.choice);
    const bool receipt_matches =
        output.receipt.owner_character_id.available &&
        output.receipt.subject_character_id.available &&
        output.receipt.cycle_serial.available &&
        output.receipt.case_serial.available && output.receipt.state.available &&
        output.receipt.choice.available &&
        IntegerEquals(output.receipt.owner_character_id, owner_id) &&
        IntegerEquals(output.receipt.subject_character_id,
                      request.subject_character_id) &&
        IntegerEquals(output.receipt.cycle_serial,
                      *output.case_identity.cycle_serial.value) &&
        IntegerEquals(output.receipt.case_serial,
                      *output.case_identity.case_serial.value) &&
        *output.receipt.state.value > 0 &&
        output.policy.choice.available &&
        IntegerEquals(output.policy.choice, 1) &&
        IntegerEquals(output.receipt.choice, *output.policy.choice.value);
    // Case initialization resets the authoritative operation marker to zero
    // without clearing the generic receipt tuple.  A residual prior-case
    // tuple must therefore remain the complete typed negative.
    if (operation_id == 0) {
      output.receipt.status = game::ZhongguoReceiptStatusV1::not_recorded;
      MakeReceiptUnavailable(output.receipt, "receipt_not_recorded");
      SetUnavailable(output.operation.pre_state, "receipt_not_recorded");
      SetUnavailable(output.operation.post_state, "receipt_not_recorded");
      output.readiness.receipt_ready = true;
    } else if (operation_id == 39 && receipt_matches) {
      output.receipt.status = game::ZhongguoReceiptStatusV1::recorded;
      SetAvailable(output.receipt.key, std::string("roster_lock"));
      SetAvailable(output.operation.pre_state, *output.receipt.state.value);
      SetAvailable(output.operation.post_state, *output.receipt.state.value);
      output.readiness.receipt_ready = true;
    } else {
      output.receipt.status = game::ZhongguoReceiptStatusV1::unavailable;
      MakeReceiptUnavailable(output.receipt, "receipt_inconsistent");
      SetUnavailable(output.operation.pre_state, "receipt_inconsistent");
      SetUnavailable(output.operation.post_state, "receipt_inconsistent");
    }
    output.readiness.policy_ready = operation_id == 39 &&
                                    output.policy.choice.available &&
                                    IntegerEquals(output.policy.choice, 1) &&
                                    output.policy.policy_id.available;
    output.readiness.operation_ready =
        operation_id == 39 && output.operation.operation_key.available &&
        output.operation.hook.available &&
        output.operation.pre_state.available &&
        output.operation.post_state.available;

    DecodeCharacter(environment, access, first[deadline_subject],
                    output.deadline.target_character_id);
    DecodeCharacter(environment, access, first[deadline_owner],
                    output.deadline.owner_character_id);
    DecodeInteger(first[deadline_cycle], output.deadline.cycle_serial);
    DecodeInteger(first[deadline_case], output.deadline.case_serial);
    DecodeInteger(first[deadline_state], output.deadline.expected_state);
    DecodeInteger(first[deadline_days], output.deadline.days);
    DecodeBoolean(first[deadline_pending], output.deadline.pending);
    DecodeBoolean(first[deadline_expired], output.deadline.expired);
    DecodePersistedDate(first[deadline_open_date],
                        output.deadline.open_date_raw);
    // B1 currently persists an open date only. There is no due-date variable
    // in the product, and the native variable registry is lookup-only, so a
    // fictitious future key must not be queried here.
    DecodePersistedDate({}, output.deadline.due_date_raw);

    const bool all_deadline_absent =
        std::none_of(first.begin() + deadline_owner, first.end(),
                     [](const auto &raw) { return raw.present; });
    // B1 initializes/reset the product deadline by writing numeric days=0 and
    // removing its open date; the shared ticket tuple can remain from the
    // previous case.  The explicit zero duration is the authoritative typed
    // negative and must dominate those residual rows.
    const bool deadline_reset = IntegerEquals(output.deadline.days, 0);
    if (all_deadline_absent || deadline_reset) {
      output.deadline.status =
          game::ZhongguoDeadlineStatusV1::not_scheduled;
      SetUnavailable(output.deadline.target_character_id,
                     "deadline_not_scheduled");
      SetUnavailable(output.deadline.owner_character_id,
                     "deadline_not_scheduled");
      SetUnavailable(output.deadline.cycle_serial,
                     "deadline_not_scheduled");
      SetUnavailable(output.deadline.case_serial,
                     "deadline_not_scheduled");
      SetUnavailable(output.deadline.expected_state,
                     "deadline_not_scheduled");
      SetUnavailable(output.deadline.days, "deadline_not_scheduled");
      SetUnavailable(output.deadline.pending, "deadline_not_scheduled");
      SetUnavailable(output.deadline.expired, "deadline_not_scheduled");
      SetUnavailable(output.deadline.open_date_raw, "not_applicable");
      SetUnavailable(output.deadline.due_date_raw, "not_applicable");
      SetUnavailable(output.deadline.on_due_operation,
                     "deadline_not_scheduled");
      output.readiness.deadline_identity_ready = true;
      output.readiness.deadline_due_date_ready = true;
    } else {
      const bool deadline_identity_matches =
          output.deadline.target_character_id.available &&
          output.deadline.owner_character_id.available &&
          output.deadline.cycle_serial.available &&
          output.deadline.case_serial.available &&
          output.deadline.expected_state.available &&
          output.deadline.days.available && output.deadline.pending.available &&
          output.deadline.expired.available &&
          IntegerEquals(output.deadline.target_character_id,
                        request.subject_character_id) &&
          IntegerEquals(output.deadline.owner_character_id, owner_id) &&
          IntegerEquals(output.deadline.cycle_serial,
                        *output.case_identity.cycle_serial.value) &&
          IntegerEquals(output.deadline.case_serial,
                        *output.case_identity.case_serial.value) &&
          *output.deadline.expected_state.value > 0 &&
          *output.deadline.days.value > 0 &&
          !(*output.deadline.pending.value &&
            *output.deadline.expired.value);
      if (!deadline_identity_matches) {
        output.deadline.status =
            game::ZhongguoDeadlineStatusV1::unavailable;
        MakeDeadlineUnavailable(output.deadline, "deadline_inconsistent");
      } else if (*output.deadline.pending.value) {
        output.deadline.status = game::ZhongguoDeadlineStatusV1::pending;
        SetAvailable(output.deadline.on_due_operation,
                     std::string("resolve_pending_milestone"));
        SetUnavailable(output.deadline.due_date_raw,
                       "due_date_not_persisted_by_product");
        output.readiness.deadline_identity_ready = true;
        output.readiness.deadline_due_date_ready =
            output.deadline.due_date_raw.available;
      } else if (*output.deadline.expired.value) {
        output.deadline.status = game::ZhongguoDeadlineStatusV1::expired;
        SetAvailable(output.deadline.on_due_operation,
                     std::string("resolve_pending_milestone"));
        SetUnavailable(output.deadline.due_date_raw,
                       "due_date_not_persisted_by_product");
        output.readiness.deadline_identity_ready = true;
        output.readiness.deadline_due_date_ready =
            output.deadline.due_date_raw.available;
      } else {
        output.deadline.status =
            game::ZhongguoDeadlineStatusV1::unavailable;
        MakeDeadlineUnavailable(output.deadline, "deadline_inconsistent");
      }
    }

    output.status = game::ZhongguoCaseSnapshotStatusV1::available;
    output.unavailable_reason.clear();
    output.readiness.ready = ComponentGate(output.readiness);
    return game::ReadZhongguoCaseSnapshotResultV1::available;
  } catch (...) {
    InitializeEnvelope(request, nullptr, output);
    SetTopUnavailable(output, "internal_error");
    return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
