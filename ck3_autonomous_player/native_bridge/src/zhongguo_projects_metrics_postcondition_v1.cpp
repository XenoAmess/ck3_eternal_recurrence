#include "xar_bridge/zhongguo_projects_metrics_postcondition_v1.hpp"

#include <windows.h>

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
  source_ready = 0,
  source_owner,
  source_subject,
  source_cycle,
  source_case,
  contribution_receipt_id,
  contribution_receipt_revision,
  contribution_value,
  result_owner,
  result_subject,
  result_cycle,
  result_case,
  metrics_source_receipt_id,
  metrics_source_receipt_revision,
  metrics_revision,
  dictionary_key_code,
  consumed_owner,
  consumed_subject,
  consumed_cycle,
  consumed_case,
  consumed_state,
  receipt_choice,
  visible_value,
  visible_provenance_case,
};

using RawRows = std::array<
    ZhongguoProjectsMetricsRawVariableV1,
    kZhongguoProjectsMetricsPostconditionV1VariableAllowlist.size()>;

bool GuardedDirectRead(const void *address, void *output,
                       std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
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

bool ReadBytes(const ZhongguoProjectsMetricsAccessV1 &access,
               const void *address, void *output, std::size_t size) noexcept {
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
bool ReadValue(const ZhongguoProjectsMetricsAccessV1 &access,
               const void *base, std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const ZhongguoProjectsMetricsNativeEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted) return false;
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
         reinterpret_cast<std::uintptr_t>(environment.character_storage_slot) ==
             base + kZhongguoCharacterStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.character_fallback_slot) ==
             base + kZhongguoCharacterFallbackSlotRva;
}

bool ResolveCharacterNative(
    const ZhongguoProjectsMetricsNativeEnvironmentV1 &environment,
    const ZhongguoProjectsMetricsAccessV1 &access,
    std::int32_t character_id) noexcept {
  if (character_id <= 0) return false;
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
  if (index >= static_cast<std::uint32_t>(capacity)) return false;
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
    const ZhongguoProjectsMetricsNativeEnvironmentV1 &environment,
    const ZhongguoProjectsMetricsAccessV1 &access,
    std::int32_t character_id) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.validate_character != nullptr &&
           access.validate_character(access.context, character_id);
  }
  return ResolveCharacterNative(environment, access, character_id);
}

bool ResolveVariableIdentifier(
    const ZhongguoProjectsMetricsNativeEnvironmentV1 &environment,
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

bool FindVariableValue(const ZhongguoProjectsMetricsAccessV1 &access,
                       void *context, std::int32_t identifier,
                       ZhongguoProjectsMetricsRawVariableV1 &output) noexcept {
  output = {};
  if (context == nullptr) return false;
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
    if (!ReadValue(access, row, 0x08, row_identifier)) return false;
    if (row_identifier != identifier) continue;
    if (output.present || !ReadValue(access, row, 0x10, output.kind) ||
        !ReadValue(access, row, 0x18, output.payload)) {
      return false;
    }
    output.present = true;
  }
  return true;
}

bool ReadAllowlistedVariableNative(
    const ZhongguoProjectsMetricsNativeEnvironmentV1 &environment,
    const ZhongguoProjectsMetricsAccessV1 &access,
    std::int32_t character_id, std::string_view key,
    ZhongguoProjectsMetricsRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) return false;
  const ZhongguoEventTarget16V1 target{4, {}, character_id};
  void *const context = environment.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

bool ReadAllowlistedRows(
    const ZhongguoProjectsMetricsNativeEnvironmentV1 &environment,
    const ZhongguoProjectsMetricsAccessV1 &access,
    std::int32_t character_id, RawRows &output) noexcept {
  for (std::size_t index = 0;
       index < kZhongguoProjectsMetricsPostconditionV1VariableAllowlist.size();
       ++index) {
    const auto key =
        kZhongguoProjectsMetricsPostconditionV1VariableAllowlist[index];
    const bool read = environment.offline_fixture_function_overrides
                          ? access.read_allowlisted_variable != nullptr &&
                                access.read_allowlisted_variable(
                                    access.context, character_id, key,
                                    output[index])
                          : ReadAllowlistedVariableNative(
                                environment, access, character_id, key,
                                output[index]);
    if (!read) return false;
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

void DecodeInteger(const ZhongguoProjectsMetricsRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1 || raw.payload % kFixedScale != 0) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload / kFixedScale);
  }
}

void DecodeCharacter(
    const ZhongguoProjectsMetricsNativeEnvironmentV1 &environment,
    const ZhongguoProjectsMetricsAccessV1 &access,
    const ZhongguoProjectsMetricsRawVariableV1 &raw,
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

void MarkIdentityUnavailable(game::ZhongguoProjectsMetricsIdentityV1 &identity,
                             std::string_view reason) {
  SetUnavailable(identity.owner_character_id, reason);
  SetUnavailable(identity.subject_character_id, reason);
  SetUnavailable(identity.cycle_serial, reason);
  SetUnavailable(identity.case_serial, reason);
}

void MarkAllUnavailable(game::ZhongguoProjectsMetricsPostconditionV1 &output,
                        std::string_view reason) {
  MarkIdentityUnavailable(output.source_identity, reason);
  MarkIdentityUnavailable(output.result_identity, reason);
  MarkIdentityUnavailable(output.contribution.identity, reason);
  SetUnavailable(output.contribution.receipt_id, reason);
  SetUnavailable(output.contribution.receipt_revision, reason);
  SetUnavailable(output.contribution.value, reason);
  MarkIdentityUnavailable(output.metrics_result.identity, reason);
  SetUnavailable(output.metrics_result.source_contribution_receipt_id, reason);
  SetUnavailable(output.metrics_result.source_contribution_receipt_revision,
                 reason);
  SetUnavailable(output.metrics_result.metrics_revision, reason);
  SetUnavailable(output.metrics_result.dictionary_key, reason);
}

void InitializeEnvelope(
    const ZhongguoProjectsMetricsPostconditionRequestV1 &request,
    const ZhongguoProjectsMetricsFrameV1 *frame,
    game::ZhongguoProjectsMetricsPostconditionV1 &output) {
  output = {};
  output.case_kind = kZhongguoProjectsMetricsPostconditionV1CaseKind;
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  output.requested_owner_character_id = request.owner_character_id;
  if (frame != nullptr) {
    output.date_raw = frame->date_raw;
    output.paused = frame->paused;
    output.player_character_id = frame->played_character_id;
  }
  MarkAllUnavailable(output, "postcondition_unavailable");
}

void SetTopUnavailable(
    game::ZhongguoProjectsMetricsPostconditionV1 &output,
    std::string_view reason, bool same_frame_ready = false) {
  output.status =
      game::ZhongguoProjectsMetricsPostconditionStatusV1::unavailable;
  MarkAllUnavailable(output, "postcondition_unavailable");
  output.readiness = {};
  output.readiness.same_frame_ready = same_frame_ready;
  output.unavailable_reason.assign(reason);
}

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
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
    const ZhongguoProjectsMetricsPostconditionRequestV1 &request) noexcept {
  return request.expected_snapshot_revision > 0 &&
         request.owner_character_id > 0 && ValidNonce(request.request_nonce);
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

bool SameIdentity(const game::ZhongguoProjectsMetricsIdentityV1 &left,
                  const game::ZhongguoProjectsMetricsIdentityV1 &right) {
  return left.owner_character_id.available &&
         right.owner_character_id.available &&
         left.owner_character_id.value == right.owner_character_id.value &&
         left.subject_character_id.value == right.subject_character_id.value &&
         left.cycle_serial.value == right.cycle_serial.value &&
         left.case_serial.value == right.case_serial.value;
}

bool IdentityReady(const game::ZhongguoProjectsMetricsIdentityV1 &identity,
                   std::int32_t owner, std::int32_t subject) {
  return IntegerEquals(identity.owner_character_id, owner) &&
         IntegerEquals(identity.subject_character_id, subject) &&
         IntegerInRange(identity.cycle_serial, 1,
                        std::numeric_limits<std::int64_t>::max()) &&
         IntegerInRange(identity.case_serial, 1,
                        std::numeric_limits<std::int32_t>::max());
}

void CopyIdentity(const game::ZhongguoProjectsMetricsIdentityV1 &source,
                  game::ZhongguoProjectsMetricsIdentityV1 &target) {
  target = source;
}

bool ComponentGate(
    const game::ZhongguoProjectsMetricsPostconditionReadinessV1 &value) {
  return value.player_subject_binding_ready && value.owner_binding_ready &&
         value.source_identity_ready && value.result_identity_ready &&
         value.contribution_ready && value.metrics_ready &&
         value.same_project_case_identity && value.receipt_lineage_ready &&
         value.result_operation_committed && value.same_frame_ready;
}

} // namespace

ZhongguoProjectsMetricsNativeEnvironmentV1
BindZhongguoProjectsMetricsNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base,
                                             exact_build_admitted);
}

game::ReadZhongguoProjectsMetricsPostconditionResultV1
ReadZhongguoProjectsMetricsPostconditionV1(
    const ZhongguoProjectsMetricsNativeEnvironmentV1 &environment,
    const ZhongguoProjectsMetricsAccessV1 &access,
    const ZhongguoProjectsMetricsPostconditionRequestV1 &request,
    game::ZhongguoProjectsMetricsPostconditionV1 &output) noexcept {
  try {
    InitializeEnvelope(request, nullptr, output);
    if (!ValidRequest(request) || !EnvironmentIsExact(environment)) {
      SetTopUnavailable(output, "unsupported_build");
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetTopUnavailable(output, "requires_application_main");
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }
    if (environment.offline_fixture_function_overrides &&
        (access.validate_character == nullptr ||
         access.read_allowlisted_variable == nullptr)) {
      SetTopUnavailable(output, "internal_error");
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }

    ZhongguoProjectsMetricsFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }
    InitializeEnvelope(request, &before, output);
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }
    if (!before.paused) {
      SetTopUnavailable(output, "requires_paused");
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0 ||
        !ValidateCharacter(environment, access, before.played_character_id)) {
      SetTopUnavailable(output, "map_not_ready");
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }

    RawRows first{};
    RawRows second{};
    if (!ReadAllowlistedRows(environment, access, before.played_character_id,
                             first) ||
        !ReadAllowlistedRows(environment, access, before.played_character_id,
                             second)) {
      SetTopUnavailable(output, "variable_context_unavailable");
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }
    ZhongguoProjectsMetricsFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first != second) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }
    output.readiness.same_frame_ready = true;

    if (!first[source_ready].present) {
      SetTopUnavailable(output, "project_source_not_found", true);
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }
    game::ZhongguoTypedIntegerV1 source_ready_value;
    DecodeInteger(first[source_ready], source_ready_value);
    if (!IntegerEquals(source_ready_value, 1)) {
      SetTopUnavailable(output, "project_source_not_ready", true);
      return game::ReadZhongguoProjectsMetricsPostconditionResultV1::
          unavailable;
    }

    DecodeCharacter(environment, access, first[source_owner],
                    output.source_identity.owner_character_id);
    DecodeCharacter(environment, access, first[source_subject],
                    output.source_identity.subject_character_id);
    DecodeInteger(first[source_cycle], output.source_identity.cycle_serial);
    DecodeInteger(first[source_case], output.source_identity.case_serial);

    DecodeCharacter(environment, access, first[result_owner],
                    output.result_identity.owner_character_id);
    DecodeCharacter(environment, access, first[result_subject],
                    output.result_identity.subject_character_id);
    DecodeInteger(first[result_cycle], output.result_identity.cycle_serial);
    DecodeInteger(first[result_case], output.result_identity.case_serial);

    CopyIdentity(output.source_identity, output.contribution.identity);
    DecodeInteger(first[contribution_receipt_id],
                  output.contribution.receipt_id);
    DecodeInteger(first[contribution_receipt_revision],
                  output.contribution.receipt_revision);
    DecodeInteger(first[contribution_value], output.contribution.value);

    CopyIdentity(output.result_identity, output.metrics_result.identity);
    DecodeInteger(first[metrics_source_receipt_id],
                  output.metrics_result.source_contribution_receipt_id);
    DecodeInteger(first[metrics_source_receipt_revision],
                  output.metrics_result.source_contribution_receipt_revision);
    DecodeInteger(first[metrics_revision],
                  output.metrics_result.metrics_revision);
    game::ZhongguoTypedIntegerV1 dictionary_code;
    DecodeInteger(first[dictionary_key_code], dictionary_code);
    if (IntegerEquals(dictionary_code, 1)) {
      SetAvailable(output.metrics_result.dictionary_key,
                   std::string("metric_dictionary_subject_v1"));
    } else if (IntegerEquals(dictionary_code, 2)) {
      SetAvailable(output.metrics_result.dictionary_key,
                   std::string("metric_dictionary_manager_v1"));
    } else {
      SetUnavailable(output.metrics_result.dictionary_key,
                     "value_out_of_range");
    }

    const auto owner = request.owner_character_id;
    const auto subject = before.played_character_id;
    output.readiness.player_subject_binding_ready =
        IntegerEquals(output.source_identity.subject_character_id, subject) &&
        IntegerEquals(output.result_identity.subject_character_id, subject);
    output.readiness.owner_binding_ready =
        owner != subject &&
        IntegerEquals(output.source_identity.owner_character_id, owner) &&
        IntegerEquals(output.result_identity.owner_character_id, owner);
    output.readiness.source_identity_ready =
        IdentityReady(output.source_identity, owner, subject);
    output.readiness.result_identity_ready =
        IdentityReady(output.result_identity, owner, subject);
    output.readiness.contribution_ready =
        IntegerInRange(output.contribution.receipt_id, 1,
                       std::numeric_limits<std::int64_t>::max()) &&
        IntegerInRange(output.contribution.receipt_revision, 1,
                       std::numeric_limits<std::int64_t>::max()) &&
        output.contribution.value.available;
    output.readiness.metrics_ready =
        IntegerInRange(output.metrics_result.source_contribution_receipt_id, 1,
                       std::numeric_limits<std::int64_t>::max()) &&
        IntegerInRange(
            output.metrics_result.source_contribution_receipt_revision, 1,
            std::numeric_limits<std::int64_t>::max()) &&
        IntegerInRange(output.metrics_result.metrics_revision, 1,
                       std::numeric_limits<std::int64_t>::max()) &&
        output.metrics_result.dictionary_key.available;
    output.readiness.same_project_case_identity =
        SameIdentity(output.source_identity, output.result_identity) &&
        SameIdentity(output.source_identity, output.contribution.identity) &&
        SameIdentity(output.source_identity, output.metrics_result.identity);
    output.readiness.receipt_lineage_ready =
        output.contribution.receipt_id.available &&
        output.metrics_result.source_contribution_receipt_id.available &&
        output.contribution.receipt_id.value ==
            output.metrics_result.source_contribution_receipt_id.value &&
        output.contribution.receipt_revision.available &&
        output.metrics_result.source_contribution_receipt_revision.available &&
        output.contribution.receipt_revision.value ==
            output.metrics_result.source_contribution_receipt_revision.value;

    game::ZhongguoTypedIntegerV1 committed_owner;
    game::ZhongguoTypedIntegerV1 committed_subject;
    game::ZhongguoTypedIntegerV1 committed_cycle;
    game::ZhongguoTypedIntegerV1 committed_case;
    game::ZhongguoTypedIntegerV1 committed_state;
    game::ZhongguoTypedIntegerV1 committed_choice;
    game::ZhongguoTypedIntegerV1 committed_visible_value;
    game::ZhongguoTypedIntegerV1 committed_visible_case;
    DecodeCharacter(environment, access, first[consumed_owner], committed_owner);
    DecodeCharacter(environment, access, first[consumed_subject],
                    committed_subject);
    DecodeInteger(first[consumed_cycle], committed_cycle);
    DecodeInteger(first[consumed_case], committed_case);
    DecodeInteger(first[consumed_state], committed_state);
    DecodeInteger(first[receipt_choice], committed_choice);
    DecodeInteger(first[visible_value], committed_visible_value);
    DecodeInteger(first[visible_provenance_case], committed_visible_case);
    output.readiness.result_operation_committed =
        IntegerEquals(committed_owner, owner) &&
        IntegerEquals(committed_subject, subject) &&
        output.source_identity.cycle_serial.available &&
        committed_cycle.value == output.source_identity.cycle_serial.value &&
        IntegerInRange(committed_case, 1,
                       std::numeric_limits<std::int32_t>::max()) &&
        IntegerEquals(committed_state, 1) &&
        (IntegerEquals(committed_choice, 1) ||
         IntegerEquals(committed_choice, 2)) &&
        dictionary_code.available &&
        committed_visible_value.value == dictionary_code.value &&
        committed_visible_case.value == committed_case.value;

    output.status =
        game::ZhongguoProjectsMetricsPostconditionStatusV1::available;
    output.unavailable_reason.clear();
    output.readiness.ready = ComponentGate(output.readiness);
    return game::ReadZhongguoProjectsMetricsPostconditionResultV1::available;
  } catch (...) {
    InitializeEnvelope(request, nullptr, output);
    SetTopUnavailable(output, "internal_error");
    return game::ReadZhongguoProjectsMetricsPostconditionResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
