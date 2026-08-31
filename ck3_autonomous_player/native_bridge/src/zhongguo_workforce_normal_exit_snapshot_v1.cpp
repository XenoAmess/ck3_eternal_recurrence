#include "xar_bridge/zhongguo_workforce_normal_exit_snapshot_v1.hpp"

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
  source_owner = 0,
  source_subject,
  source_cycle,
  source_case,
  source_state,
  source_route,
  source_offer_gold,
  source_receipt_serial,
  source_object_owner,
  source_object_subject,
  source_object_cycle,
  source_object_case,
  source_object_route,
  source_object_active,
  source_object_consumed,
  source_consumer_case,
  workflow_pending,
  workflow_owner,
  workflow_subject,
  workflow_cycle,
  workflow_case,
  workflow_state,
  workflow_migration_authorized,
  workflow_hc_authorized,
  workflow_hc_available,
  workflow_hc_reserved,
  workflow_hc_occupied,
  workflow_hc_frozen,
  workflow_hc_reclaimed,
  workflow_slot_case,
  live_hc_authorized,
  live_hc_available,
  live_hc_reserved,
  live_hc_occupied,
  live_hc_frozen,
  live_hc_reclaimed,
  live_formal_active,
  live_formal_case,
  receipt_active,
  receipt_sealed,
  receipt_published,
  receipt_consumed,
  receipt_operation,
  receipt_owner,
  receipt_subject,
  receipt_cycle,
  receipt_case,
  receipt_state,
  receipt_id,
  receipt_hash,
  receipt_hc_settled,
  receipt_hc_destination,
  receipt_hc_conservation,
  receipt_hc_before_authorized,
  receipt_hc_before_available,
  receipt_hc_before_reserved,
  receipt_hc_before_occupied,
  receipt_hc_before_frozen,
  receipt_hc_before_reclaimed,
  receipt_hc_after_authorized,
  receipt_hc_after_available,
  receipt_hc_after_reserved,
  receipt_hc_after_occupied,
  receipt_hc_after_frozen,
  receipt_hc_after_reclaimed,
  receipt_formal_before,
  receipt_formal_after,
  receipt_formal_case,
  rehire_state,
  rehire_subject,
  rehire_owner,
  rehire_cycle,
  rehire_case,
  rehire_exit_state,
  rehire_receipt_id,
  rehire_receipt_hash,
  rehire_verified,
  rehire_hc_before_authorized,
  rehire_hc_before_available,
  rehire_hc_before_reserved,
  rehire_hc_before_occupied,
  rehire_hc_before_frozen,
  rehire_hc_before_reclaimed,
  rehire_hc_after_authorized,
  rehire_hc_after_available,
  rehire_hc_after_reserved,
  rehire_hc_after_occupied,
  rehire_hc_after_frozen,
  rehire_hc_after_reclaimed,
  rehire_hc_destination,
  rehire_hc_conservation,
  rehire_formal_before,
  rehire_formal_after,
  rehire_formal_case,
};

using RawRows = std::array<
    ZhongguoWorkforceNormalExitRawVariableV1,
    kZhongguoWorkforceNormalExitVariableAllowlist.size()>;

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

bool ReadBytes(const ZhongguoWorkforceNormalExitAccessV1 &access,
               const void *address, void *output, std::size_t size) noexcept {
  return access.read_memory != nullptr
             ? access.read_memory(access.context, address, output, size)
             : GuardedDirectRead(address, output, size);
}

bool CheckedAddress(const void *base, std::size_t offset,
                    const void *&output) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - value) {
    output = nullptr;
    return false;
  }
  output = reinterpret_cast<const void *>(value + offset);
  return true;
}

template <typename Value>
bool ReadValue(const ZhongguoWorkforceNormalExitAccessV1 &access,
               const void *base, std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &environment) noexcept {
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
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceNormalExitAccessV1 &access,
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
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceNormalExitAccessV1 &access,
    std::int32_t character_id) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.validate_character != nullptr &&
           access.validate_character(access.context, character_id);
  }
  return ResolveCharacterNative(environment, access, character_id);
}

bool ResolveVariableIdentifier(
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &environment,
    std::string_view key, std::int32_t &identifier) noexcept {
  void *const table = environment.variable_identifier_table();
  if (table == nullptr || key.empty() ||
      key.size() >
          static_cast<std::size_t>((std::numeric_limits<std::int32_t>::max)())) {
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

bool FindVariableValue(
    const ZhongguoWorkforceNormalExitAccessV1 &access, void *context,
    std::int32_t identifier,
    ZhongguoWorkforceNormalExitRawVariableV1 &output) noexcept {
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
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceNormalExitAccessV1 &access,
    std::int32_t character_id, std::string_view key,
    ZhongguoWorkforceNormalExitRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) return false;
  const ZhongguoEventTarget16V1 target{4, {}, character_id};
  void *const context = environment.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

bool ReadAllowlistedRows(
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceNormalExitAccessV1 &access,
    std::int32_t character_id, RawRows &output) noexcept {
  for (std::size_t index = 0;
       index < kZhongguoWorkforceNormalExitVariableAllowlist.size(); ++index) {
    const auto key = kZhongguoWorkforceNormalExitVariableAllowlist[index];
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

void DecodeInteger(const ZhongguoWorkforceNormalExitRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1 || raw.payload % kFixedScale != 0) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload / kFixedScale);
  }
}

void DecodeBoolean(const ZhongguoWorkforceNormalExitRawVariableV1 &raw,
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
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceNormalExitAccessV1 &access,
    const ZhongguoWorkforceNormalExitRawVariableV1 &raw,
    game::ZhongguoTypedIntegerV1 &field) noexcept {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 4) {
    SetUnavailable(field, "value_type_mismatch");
  } else if (raw.payload <= 0 ||
             raw.payload > (std::numeric_limits<std::int32_t>::max)() ||
             !ValidateCharacter(environment, access,
                                static_cast<std::int32_t>(raw.payload))) {
    SetUnavailable(field, "value_out_of_range");
  } else {
    SetAvailable(field, raw.payload);
  }
}

void DecodePartition(const RawRows &rows, std::size_t begin,
                     game::ZhongguoWorkforceHcPartitionV1 &output) {
  DecodeInteger(rows[begin + 0], output.authorized);
  DecodeInteger(rows[begin + 1], output.available);
  DecodeInteger(rows[begin + 2], output.reserved);
  DecodeInteger(rows[begin + 3], output.occupied);
  DecodeInteger(rows[begin + 4], output.frozen);
  DecodeInteger(rows[begin + 5], output.reclaimed);
}

void DecodeRows(
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceNormalExitAccessV1 &access, const RawRows &rows,
    game::ZhongguoWorkforceNormalExitSnapshotV1 &output) {
  auto &source = output.source;
  DecodeCharacter(environment, access, rows[source_owner],
                  source.owner_character_id);
  DecodeCharacter(environment, access, rows[source_subject],
                  source.subject_character_id);
  DecodeInteger(rows[source_cycle], source.cycle_serial);
  DecodeInteger(rows[source_case], source.case_serial);
  DecodeInteger(rows[source_state], source.state);
  DecodeInteger(rows[source_route], source.route);
  DecodeInteger(rows[source_offer_gold], source.offer_gold);
  DecodeInteger(rows[source_receipt_serial], source.receipt_serial);
  DecodeCharacter(environment, access, rows[source_object_owner],
                  source.object_owner_character_id);
  DecodeCharacter(environment, access, rows[source_object_subject],
                  source.object_subject_character_id);
  DecodeInteger(rows[source_object_cycle], source.object_cycle_serial);
  DecodeInteger(rows[source_object_case], source.object_receipt_case_serial);
  DecodeInteger(rows[source_object_route], source.object_route);
  DecodeBoolean(rows[source_object_active], source.object_active);
  DecodeBoolean(rows[source_object_consumed], source.object_consumed);
  DecodeInteger(rows[source_consumer_case],
                source.consumer_receipt_case_serial);

  auto &workflow = output.workflow;
  DecodeBoolean(rows[workflow_pending], workflow.pending);
  DecodeCharacter(environment, access, rows[workflow_owner],
                  workflow.pending_owner_character_id);
  DecodeCharacter(environment, access, rows[workflow_subject],
                  workflow.pending_subject_character_id);
  DecodeInteger(rows[workflow_cycle], workflow.pending_cycle_serial);
  DecodeInteger(rows[workflow_case], workflow.pending_case_serial);
  DecodeInteger(rows[workflow_state], workflow.state);
  DecodeBoolean(rows[workflow_migration_authorized],
                workflow.pending_hc_migration_authorized);
  DecodePartition(rows, workflow_hc_authorized, workflow.pending_hc_before);
  DecodeInteger(rows[workflow_slot_case], workflow.pending_slot_case_serial);

  DecodePartition(rows, live_hc_authorized, output.current_hc.partition);
  DecodeBoolean(rows[live_formal_active], output.current_hc.formal_active);
  DecodeInteger(rows[live_formal_case],
                output.current_hc.formal_case_serial);

  auto &receipt = output.receipt;
  DecodeBoolean(rows[receipt_active], receipt.active);
  DecodeBoolean(rows[receipt_sealed], receipt.sealed);
  DecodeBoolean(rows[receipt_published], receipt.published);
  DecodeBoolean(rows[receipt_consumed], receipt.consumed);
  DecodeInteger(rows[receipt_operation], receipt.consumed_operation);
  DecodeCharacter(environment, access, rows[receipt_owner],
                  receipt.owner_character_id);
  DecodeCharacter(environment, access, rows[receipt_subject],
                  receipt.subject_character_id);
  DecodeInteger(rows[receipt_cycle], receipt.cycle_serial);
  DecodeInteger(rows[receipt_case], receipt.case_serial);
  DecodeInteger(rows[receipt_state], receipt.state);
  DecodeInteger(rows[receipt_id], receipt.receipt_id);
  DecodeInteger(rows[receipt_hash], receipt.receipt_hash);
  DecodeBoolean(rows[receipt_hc_settled], receipt.hc_ledger_settled);
  DecodeBoolean(rows[receipt_hc_destination], receipt.hc_destination_frozen);
  DecodeBoolean(rows[receipt_hc_conservation],
                receipt.hc_conservation_verified);
  DecodePartition(rows, receipt_hc_before_authorized, receipt.hc_before);
  DecodePartition(rows, receipt_hc_after_authorized, receipt.hc_after);
  DecodeBoolean(rows[receipt_formal_before],
                receipt.formal_hc_active_before);
  DecodeBoolean(rows[receipt_formal_after],
                receipt.formal_hc_active_after);
  DecodeInteger(rows[receipt_formal_case],
                receipt.formal_hc_case_serial);

  auto &rehire = output.rehire;
  DecodeInteger(rows[rehire_state], rehire.state);
  DecodeCharacter(environment, access, rows[rehire_subject],
                  rehire.subject_character_id);
  DecodeCharacter(environment, access, rows[rehire_owner],
                  rehire.exit_owner_character_id);
  DecodeInteger(rows[rehire_cycle], rehire.exit_cycle_serial);
  DecodeInteger(rows[rehire_case], rehire.exit_case_serial);
  DecodeInteger(rows[rehire_exit_state], rehire.exit_state);
  DecodeInteger(rows[rehire_receipt_id], rehire.exit_receipt_id);
  DecodeInteger(rows[rehire_receipt_hash], rehire.exit_receipt_hash);
  DecodeBoolean(rows[rehire_verified], rehire.normal_exit_verified);
  DecodePartition(rows, rehire_hc_before_authorized, rehire.exit_hc_before);
  DecodePartition(rows, rehire_hc_after_authorized, rehire.exit_hc_after);
  DecodeBoolean(rows[rehire_hc_destination],
                rehire.exit_hc_destination_frozen);
  DecodeBoolean(rows[rehire_hc_conservation],
                rehire.exit_hc_conservation_verified);
  DecodeBoolean(rows[rehire_formal_before],
                rehire.exit_formal_hc_active_before);
  DecodeBoolean(rows[rehire_formal_after],
                rehire.exit_formal_hc_active_after);
  DecodeInteger(rows[rehire_formal_case],
                rehire.exit_formal_hc_case_serial);
}

template <typename Value>
bool Available(const game::ZhongguoTypedValueV1<Value> &field) noexcept {
  return field.available && field.value.has_value();
}

template <typename Value>
bool Unavailable(const game::ZhongguoTypedValueV1<Value> &field) noexcept {
  return !field.available && !field.value.has_value();
}

bool IntEquals(const game::ZhongguoTypedIntegerV1 &field,
               std::int64_t value) noexcept {
  return Available(field) && *field.value == value;
}

bool BoolEquals(const game::ZhongguoTypedBooleanV1 &field,
                bool value) noexcept {
  return Available(field) && *field.value == value;
}

bool Positive(const game::ZhongguoTypedIntegerV1 &field) noexcept {
  return Available(field) && *field.value > 0;
}

bool PartitionComplete(
    const game::ZhongguoWorkforceHcPartitionV1 &value) noexcept {
  return Available(value.authorized) && Available(value.available) &&
         Available(value.reserved) && Available(value.occupied) &&
         Available(value.frozen) && Available(value.reclaimed);
}

bool PartitionAbsent(
    const game::ZhongguoWorkforceHcPartitionV1 &value) noexcept {
  return Unavailable(value.authorized) && Unavailable(value.available) &&
         Unavailable(value.reserved) && Unavailable(value.occupied) &&
         Unavailable(value.frozen) && Unavailable(value.reclaimed);
}

bool PartitionTouched(
    const game::ZhongguoWorkforceHcPartitionV1 &value) noexcept {
  return Available(value.authorized) || Available(value.available) ||
         Available(value.reserved) || Available(value.occupied) ||
         Available(value.frozen) || Available(value.reclaimed);
}

bool PartitionConserved(
    const game::ZhongguoWorkforceHcPartitionV1 &value) noexcept {
  return PartitionComplete(value) && *value.authorized.value >= 1 &&
         *value.available.value >= 0 && *value.reserved.value >= 0 &&
         *value.occupied.value >= 0 && *value.frozen.value >= 0 &&
         *value.reclaimed.value >= 0 &&
         *value.authorized.value ==
             *value.available.value + *value.reserved.value +
                 *value.occupied.value + *value.frozen.value +
                 *value.reclaimed.value;
}

bool PartitionValuesEqual(
    const game::ZhongguoWorkforceHcPartitionV1 &left,
    const game::ZhongguoWorkforceHcPartitionV1 &right) noexcept {
  return PartitionComplete(left) && PartitionComplete(right) &&
         left.authorized.value == right.authorized.value &&
         left.available.value == right.available.value &&
         left.reserved.value == right.reserved.value &&
         left.occupied.value == right.occupied.value &&
         left.frozen.value == right.frozen.value &&
         left.reclaimed.value == right.reclaimed.value;
}

bool MigrationValid(
    const game::ZhongguoWorkforceHcPartitionV1 &before,
    const game::ZhongguoWorkforceHcPartitionV1 &after) noexcept {
  return PartitionConserved(before) && PartitionConserved(after) &&
         before.authorized.value == after.authorized.value &&
         before.available.value == after.available.value &&
         before.reserved.value == after.reserved.value &&
         before.reclaimed.value == after.reclaimed.value &&
         *after.occupied.value == *before.occupied.value - 1 &&
         *after.frozen.value == *before.frozen.value + 1;
}

bool SourceCoreComplete(
    const game::ZhongguoWorkforceNormalExitSourceV1 &value) noexcept {
  return Available(value.owner_character_id) &&
         Available(value.subject_character_id) && Available(value.cycle_serial) &&
         Available(value.case_serial) && Available(value.state) &&
         Available(value.route) && Available(value.offer_gold) &&
         Available(value.receipt_serial) &&
         Available(value.object_owner_character_id) &&
         Available(value.object_subject_character_id) &&
         Available(value.object_cycle_serial) &&
         Available(value.object_receipt_case_serial) &&
         Available(value.object_route) && Available(value.object_active) &&
         Available(value.object_consumed);
}

bool SourceCoreAbsent(
    const game::ZhongguoWorkforceNormalExitSourceV1 &value) noexcept {
  return Unavailable(value.owner_character_id) &&
         Unavailable(value.subject_character_id) && Unavailable(value.cycle_serial) &&
         Unavailable(value.case_serial) && Unavailable(value.state) &&
         Unavailable(value.route) && Unavailable(value.offer_gold) &&
         Unavailable(value.receipt_serial) &&
         Unavailable(value.object_owner_character_id) &&
         Unavailable(value.object_subject_character_id) &&
         Unavailable(value.object_cycle_serial) &&
         Unavailable(value.object_receipt_case_serial) &&
         Unavailable(value.object_route) && Unavailable(value.object_active) &&
         Unavailable(value.object_consumed) &&
         Unavailable(value.consumer_receipt_case_serial);
}

bool PendingIdentityTouched(
    const game::ZhongguoWorkforceNormalExitWorkflowV1 &value) noexcept {
  return Available(value.pending) || Available(value.pending_owner_character_id) ||
         Available(value.pending_subject_character_id) ||
         Available(value.pending_cycle_serial) ||
         Available(value.pending_case_serial) ||
         Available(value.pending_slot_case_serial) ||
         PartitionTouched(value.pending_hc_before);
}

bool PendingIdentityComplete(
    const game::ZhongguoWorkforceNormalExitWorkflowV1 &value) noexcept {
  return Available(value.pending) && Available(value.pending_owner_character_id) &&
         Available(value.pending_subject_character_id) &&
         Available(value.pending_cycle_serial) &&
         Available(value.pending_case_serial) &&
         Available(value.pending_slot_case_serial) &&
         PartitionComplete(value.pending_hc_before);
}

bool WorkflowPendingAbsent(
    const game::ZhongguoWorkforceNormalExitWorkflowV1 &value) noexcept {
  return Unavailable(value.pending) &&
         Unavailable(value.pending_owner_character_id) &&
         Unavailable(value.pending_subject_character_id) &&
         Unavailable(value.pending_cycle_serial) &&
         Unavailable(value.pending_case_serial) &&
         Unavailable(value.pending_hc_migration_authorized) &&
         PartitionAbsent(value.pending_hc_before) &&
         Unavailable(value.pending_slot_case_serial);
}

bool ReceiptTouched(
    const game::ZhongguoWorkforceNormalExitReceiptV1 &value) noexcept {
  return Available(value.active) || Available(value.sealed) ||
         Available(value.published) || Available(value.consumed) ||
         Available(value.consumed_operation) || Available(value.owner_character_id) ||
         Available(value.subject_character_id) || Available(value.cycle_serial) ||
         Available(value.case_serial) || Available(value.state) ||
         Available(value.receipt_id) || Available(value.receipt_hash) ||
         Available(value.hc_ledger_settled) ||
         Available(value.hc_destination_frozen) ||
         Available(value.hc_conservation_verified) ||
         PartitionTouched(value.hc_before) || PartitionTouched(value.hc_after) ||
         Available(value.formal_hc_active_before) ||
         Available(value.formal_hc_active_after) ||
         Available(value.formal_hc_case_serial);
}

bool ReceiptComplete(
    const game::ZhongguoWorkforceNormalExitReceiptV1 &value) noexcept {
  return Available(value.active) && Available(value.sealed) &&
         Available(value.published) && Available(value.consumed) &&
         Available(value.consumed_operation) && Available(value.owner_character_id) &&
         Available(value.subject_character_id) && Available(value.cycle_serial) &&
         Available(value.case_serial) && Available(value.state) &&
         Available(value.receipt_id) && Available(value.receipt_hash) &&
         Available(value.hc_ledger_settled) &&
         Available(value.hc_destination_frozen) &&
         Available(value.hc_conservation_verified) &&
         PartitionComplete(value.hc_before) && PartitionComplete(value.hc_after) &&
         Available(value.formal_hc_active_before) &&
         Available(value.formal_hc_active_after) &&
         Available(value.formal_hc_case_serial);
}

bool RehireTouched(const game::ZhongguoWorkforceRehireExitV1 &value) noexcept {
  return Available(value.state) || Available(value.subject_character_id) ||
         Available(value.exit_owner_character_id) ||
         Available(value.exit_cycle_serial) || Available(value.exit_case_serial) ||
         Available(value.exit_state) || Available(value.exit_receipt_id) ||
         Available(value.exit_receipt_hash) || Available(value.normal_exit_verified) ||
         PartitionTouched(value.exit_hc_before) ||
         PartitionTouched(value.exit_hc_after) ||
         Available(value.exit_hc_destination_frozen) ||
         Available(value.exit_hc_conservation_verified) ||
         Available(value.exit_formal_hc_active_before) ||
         Available(value.exit_formal_hc_active_after) ||
         Available(value.exit_formal_hc_case_serial);
}

bool RehireComplete(const game::ZhongguoWorkforceRehireExitV1 &value) noexcept {
  return Available(value.state) && Available(value.subject_character_id) &&
         Available(value.exit_owner_character_id) &&
         Available(value.exit_cycle_serial) && Available(value.exit_case_serial) &&
         Available(value.exit_state) && Available(value.exit_receipt_id) &&
         Available(value.exit_receipt_hash) && Available(value.normal_exit_verified) &&
         PartitionComplete(value.exit_hc_before) &&
         PartitionComplete(value.exit_hc_after) &&
         Available(value.exit_hc_destination_frozen) &&
         Available(value.exit_hc_conservation_verified) &&
         Available(value.exit_formal_hc_active_before) &&
         Available(value.exit_formal_hc_active_after) &&
         Available(value.exit_formal_hc_case_serial);
}

template <typename Value>
void MarkUnavailable(game::ZhongguoTypedValueV1<Value> &field,
                     std::string_view reason) {
  SetUnavailable(field, reason);
}

void MarkPartitionUnavailable(game::ZhongguoWorkforceHcPartitionV1 &value,
                              std::string_view reason) {
  MarkUnavailable(value.authorized, reason);
  MarkUnavailable(value.available, reason);
  MarkUnavailable(value.reserved, reason);
  MarkUnavailable(value.occupied, reason);
  MarkUnavailable(value.frozen, reason);
  MarkUnavailable(value.reclaimed, reason);
}

void MakeAllFieldsUnavailable(
    game::ZhongguoWorkforceNormalExitSnapshotV1 &output,
    std::string_view reason) {
  auto &s = output.source;
  MarkUnavailable(s.owner_character_id, reason);
  MarkUnavailable(s.subject_character_id, reason);
  MarkUnavailable(s.cycle_serial, reason);
  MarkUnavailable(s.case_serial, reason);
  MarkUnavailable(s.state, reason);
  MarkUnavailable(s.route, reason);
  MarkUnavailable(s.offer_gold, reason);
  MarkUnavailable(s.receipt_serial, reason);
  MarkUnavailable(s.object_owner_character_id, reason);
  MarkUnavailable(s.object_subject_character_id, reason);
  MarkUnavailable(s.object_cycle_serial, reason);
  MarkUnavailable(s.object_receipt_case_serial, reason);
  MarkUnavailable(s.object_route, reason);
  MarkUnavailable(s.object_active, reason);
  MarkUnavailable(s.object_consumed, reason);
  MarkUnavailable(s.consumer_receipt_case_serial, reason);
  auto &w = output.workflow;
  MarkUnavailable(w.pending, reason);
  MarkUnavailable(w.pending_owner_character_id, reason);
  MarkUnavailable(w.pending_subject_character_id, reason);
  MarkUnavailable(w.pending_cycle_serial, reason);
  MarkUnavailable(w.pending_case_serial, reason);
  MarkUnavailable(w.state, reason);
  MarkUnavailable(w.pending_hc_migration_authorized, reason);
  MarkPartitionUnavailable(w.pending_hc_before, reason);
  MarkUnavailable(w.pending_slot_case_serial, reason);
  MarkPartitionUnavailable(output.current_hc.partition, reason);
  MarkUnavailable(output.current_hc.formal_active, reason);
  MarkUnavailable(output.current_hc.formal_case_serial, reason);
  auto &r = output.receipt;
  MarkUnavailable(r.active, reason);
  MarkUnavailable(r.sealed, reason);
  MarkUnavailable(r.published, reason);
  MarkUnavailable(r.consumed, reason);
  MarkUnavailable(r.consumed_operation, reason);
  MarkUnavailable(r.owner_character_id, reason);
  MarkUnavailable(r.subject_character_id, reason);
  MarkUnavailable(r.cycle_serial, reason);
  MarkUnavailable(r.case_serial, reason);
  MarkUnavailable(r.state, reason);
  MarkUnavailable(r.receipt_id, reason);
  MarkUnavailable(r.receipt_hash, reason);
  MarkUnavailable(r.hc_ledger_settled, reason);
  MarkUnavailable(r.hc_destination_frozen, reason);
  MarkUnavailable(r.hc_conservation_verified, reason);
  MarkPartitionUnavailable(r.hc_before, reason);
  MarkPartitionUnavailable(r.hc_after, reason);
  MarkUnavailable(r.formal_hc_active_before, reason);
  MarkUnavailable(r.formal_hc_active_after, reason);
  MarkUnavailable(r.formal_hc_case_serial, reason);
  auto &h = output.rehire;
  MarkUnavailable(h.state, reason);
  MarkUnavailable(h.subject_character_id, reason);
  MarkUnavailable(h.exit_owner_character_id, reason);
  MarkUnavailable(h.exit_cycle_serial, reason);
  MarkUnavailable(h.exit_case_serial, reason);
  MarkUnavailable(h.exit_state, reason);
  MarkUnavailable(h.exit_receipt_id, reason);
  MarkUnavailable(h.exit_receipt_hash, reason);
  MarkUnavailable(h.normal_exit_verified, reason);
  MarkPartitionUnavailable(h.exit_hc_before, reason);
  MarkPartitionUnavailable(h.exit_hc_after, reason);
  MarkUnavailable(h.exit_hc_destination_frozen, reason);
  MarkUnavailable(h.exit_hc_conservation_verified, reason);
  MarkUnavailable(h.exit_formal_hc_active_before, reason);
  MarkUnavailable(h.exit_formal_hc_active_after, reason);
  MarkUnavailable(h.exit_formal_hc_case_serial, reason);
}

void InitializeEnvelope(
    const ZhongguoWorkforceNormalExitSnapshotRequestV1 &request,
    const ZhongguoWorkforceNormalExitFrameV1 *frame,
    game::ZhongguoWorkforceNormalExitSnapshotV1 &output) {
  output = {};
  output.case_kind = kZhongguoWorkforceNormalExitSnapshotV1CaseKind;
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

void SetTopUnavailable(
    game::ZhongguoWorkforceNormalExitSnapshotV1 &output,
    std::string_view reason, bool same_frame = false) {
  output.status = game::ZhongguoWorkforceNormalExitSnapshotStatusV1::unavailable;
  output.lifecycle = game::ZhongguoWorkforceNormalExitLifecycleV1::unavailable;
  MakeAllFieldsUnavailable(output, "case_unavailable");
  output.readiness = {};
  output.readiness.same_frame_ready = same_frame;
  output.unavailable_reason.assign(reason);
}

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t index = 0; index < value.size(); ++index) {
    const char c = value[index];
    const bool alpha = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
    const bool digit = c >= '0' && c <= '9';
    const bool punctuation = c == '.' || c == '_' || c == ':' || c == '-';
    if ((!alpha && !digit && !punctuation) ||
        (index == 0 && !alpha && !digit)) {
      return false;
    }
  }
  return true;
}

bool ValidRequest(
    const ZhongguoWorkforceNormalExitSnapshotRequestV1 &request) noexcept {
  return request.expected_snapshot_revision > 0 &&
         request.owner_character_id > 0 && ValidNonce(request.request_nonce);
}

bool SourceCanonical(
    const game::ZhongguoWorkforceNormalExitSourceV1 &source,
    std::int32_t player, std::int32_t owner) noexcept {
  if (!SourceCoreComplete(source) ||
      !IntEquals(source.owner_character_id, owner) || owner == player ||
      !IntEquals(source.subject_character_id, player) ||
      !Positive(source.cycle_serial) || !Positive(source.case_serial) ||
      !IntEquals(source.route, 1) || !IntEquals(source.offer_gold, 50) ||
      source.receipt_serial.value != source.case_serial.value ||
      !IntEquals(source.object_owner_character_id, owner) ||
      !IntEquals(source.object_subject_character_id, player) ||
      source.object_cycle_serial.value != source.cycle_serial.value ||
      source.object_receipt_case_serial.value != source.case_serial.value ||
      !IntEquals(source.object_route, 1)) {
    return false;
  }
  if (IntEquals(source.state, 1)) {
    return BoolEquals(source.object_active, true) &&
           BoolEquals(source.object_consumed, false) &&
           Unavailable(source.consumer_receipt_case_serial);
  }
  return IntEquals(source.state, 3) &&
         BoolEquals(source.object_active, false) &&
         BoolEquals(source.object_consumed, true) &&
         source.consumer_receipt_case_serial.value == source.case_serial.value;
}

bool PendingCanonical(
    const game::ZhongguoWorkforceNormalExitWorkflowV1 &workflow,
    const game::ZhongguoWorkforceNormalExitSourceV1 &source,
    const game::ZhongguoWorkforceCurrentHcV1 &current, std::int32_t player,
    std::int32_t owner) noexcept {
  return PendingIdentityComplete(workflow) &&
         PartitionConserved(workflow.pending_hc_before) &&
         BoolEquals(workflow.pending, true) &&
         IntEquals(workflow.pending_owner_character_id, owner) &&
         IntEquals(workflow.pending_subject_character_id, player) &&
         workflow.pending_cycle_serial.value == source.cycle_serial.value &&
         workflow.pending_case_serial.value == source.case_serial.value &&
         workflow.pending_slot_case_serial.value == current.formal_case_serial.value;
}

bool ReceiptCanonical(
    const game::ZhongguoWorkforceNormalExitReceiptV1 &receipt,
    const game::ZhongguoWorkforceNormalExitSourceV1 &source,
    std::int32_t player, std::int32_t owner) noexcept {
  return ReceiptComplete(receipt) && MigrationValid(receipt.hc_before, receipt.hc_after) &&
         BoolEquals(receipt.active, true) && BoolEquals(receipt.sealed, true) &&
         BoolEquals(receipt.published, true) &&
         BoolEquals(receipt.consumed, true) &&
         IntEquals(receipt.consumed_operation, 75) &&
         IntEquals(receipt.owner_character_id, owner) &&
         IntEquals(receipt.subject_character_id, player) &&
         receipt.cycle_serial.value == source.cycle_serial.value &&
         receipt.case_serial.value == source.case_serial.value &&
         IntEquals(receipt.state, 6) && Positive(receipt.receipt_id) &&
         Positive(receipt.receipt_hash) &&
         BoolEquals(receipt.hc_ledger_settled, true) &&
         BoolEquals(receipt.hc_destination_frozen, true) &&
         BoolEquals(receipt.hc_conservation_verified, true) &&
         BoolEquals(receipt.formal_hc_active_before, true) &&
         BoolEquals(receipt.formal_hc_active_after, false) &&
         Positive(receipt.formal_hc_case_serial);
}

bool RehireCanonical(
    const game::ZhongguoWorkforceRehireExitV1 &rehire,
    const game::ZhongguoWorkforceNormalExitReceiptV1 &receipt,
    const game::ZhongguoWorkforceNormalExitSourceV1 &source,
    std::int32_t player, std::int32_t owner) noexcept {
  return RehireComplete(rehire) && Positive(rehire.state) &&
         IntEquals(rehire.subject_character_id, player) &&
         IntEquals(rehire.exit_owner_character_id, owner) &&
         rehire.exit_cycle_serial.value == source.cycle_serial.value &&
         rehire.exit_case_serial.value == source.case_serial.value &&
         IntEquals(rehire.exit_state, 6) &&
         rehire.exit_receipt_id.value == receipt.receipt_id.value &&
         rehire.exit_receipt_hash.value == receipt.receipt_hash.value &&
         BoolEquals(rehire.normal_exit_verified, true) &&
         PartitionValuesEqual(rehire.exit_hc_before, receipt.hc_before) &&
         PartitionValuesEqual(rehire.exit_hc_after, receipt.hc_after) &&
         BoolEquals(rehire.exit_hc_destination_frozen, true) &&
         BoolEquals(rehire.exit_hc_conservation_verified, true) &&
         BoolEquals(rehire.exit_formal_hc_active_before, true) &&
         BoolEquals(rehire.exit_formal_hc_active_after, false) &&
         rehire.exit_formal_hc_case_serial.value ==
             receipt.formal_hc_case_serial.value;
}

bool DeriveLifecycle(game::ZhongguoWorkforceNormalExitSnapshotV1 &output,
                     std::int32_t player, std::int32_t owner) noexcept {
  const auto &source = output.source;
  const auto &workflow = output.workflow;
  const auto &current = output.current_hc;
  const auto &receipt = output.receipt;
  const auto &rehire = output.rehire;
  if (!SourceCanonical(source, player, owner) ||
      !PartitionConserved(current.partition) ||
      !Available(current.formal_active) ||
      !Positive(current.formal_case_serial)) {
    return false;
  }

  auto &ready = output.readiness;
  ready.player_subject_binding_ready = true;
  ready.owner_binding_ready = true;
  ready.source_object_ready = true;
  ready.current_hc_partition_ready = true;
  const bool receipt_touched = ReceiptTouched(receipt);
  const bool rehire_touched = RehireTouched(rehire);
  const bool pending_touched = PendingIdentityTouched(workflow);

  if (receipt_touched || rehire_touched) {
    if (!IntEquals(source.state, 3) || !ReceiptCanonical(receipt, source, player, owner) ||
        !IntEquals(workflow.state, 4) || !WorkflowPendingAbsent(workflow)) {
      return false;
    }
    ready.migration_delta_ready = true;
    ready.sealed_receipt_ready = true;
    ready.current_hc_matches_stage_ready =
        PartitionValuesEqual(current.partition, receipt.hc_after) &&
        BoolEquals(current.formal_active, false) &&
        current.formal_case_serial.value == receipt.formal_hc_case_serial.value;
    if (rehire_touched) {
      if (!RehireCanonical(rehire, receipt, source, player, owner)) return false;
      output.lifecycle =
          game::ZhongguoWorkforceNormalExitLifecycleV1::rehire_captured;
      ready.rehire_capture_ready = true;
    } else {
      if (!RehireComplete(rehire) && RehireTouched(rehire)) return false;
      output.lifecycle = game::ZhongguoWorkforceNormalExitLifecycleV1::sealed;
    }
  } else {
    if (receipt_touched || rehire_touched) return false;
    const bool migrating = IntEquals(workflow.state, 3);
    output.lifecycle = migrating
                           ? game::ZhongguoWorkforceNormalExitLifecycleV1::migrating
                           : game::ZhongguoWorkforceNormalExitLifecycleV1::pre;
    if (pending_touched) {
      if (!PendingCanonical(workflow, source, current, player, owner)) return false;
      ready.pending_snapshot_ready = true;
    } else if (!WorkflowPendingAbsent(workflow) || Available(workflow.state)) {
      return false;
    }

    if (migrating) {
      if (!pending_touched || !IntEquals(source.state, 3) ||
          !BoolEquals(workflow.pending_hc_migration_authorized, true) ||
          !MigrationValid(workflow.pending_hc_before, current.partition) ||
          !BoolEquals(current.formal_active, false)) {
        return false;
      }
      ready.migration_delta_ready = true;
      ready.current_hc_matches_stage_ready = true;
    } else if (IntEquals(source.state, 3)) {
      if (!pending_touched || !IntEquals(workflow.state, 2) ||
          !Unavailable(workflow.pending_hc_migration_authorized) ||
          !PartitionValuesEqual(workflow.pending_hc_before, current.partition) ||
          !BoolEquals(current.formal_active, true)) {
        return false;
      }
      ready.current_hc_matches_stage_ready = true;
    } else if (pending_touched) {
      if (Available(workflow.state) ||
          Available(workflow.pending_hc_migration_authorized) ||
          !PartitionValuesEqual(workflow.pending_hc_before, current.partition) ||
          !BoolEquals(current.formal_active, true)) {
        return false;
      }
      ready.current_hc_matches_stage_ready = true;
    }
  }
  ready.lifecycle_ready = true;
  ready.ready = ready.player_subject_binding_ready && ready.owner_binding_ready &&
                ready.lifecycle_ready && ready.same_frame_ready;
  return ready.ready;
}

} // namespace

ZhongguoWorkforceNormalExitNativeEnvironmentV1
BindZhongguoWorkforceNormalExitNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base,
                                             exact_build_admitted);
}

game::ReadZhongguoWorkforceNormalExitSnapshotResultV1
ReadZhongguoWorkforceNormalExitSnapshotV1(
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceNormalExitAccessV1 &access,
    const ZhongguoWorkforceNormalExitSnapshotRequestV1 &request,
    game::ZhongguoWorkforceNormalExitSnapshotV1 &output) noexcept {
  try {
    InitializeEnvelope(request, nullptr, output);
    if (!ValidRequest(request) || !EnvironmentIsExact(environment)) {
      SetTopUnavailable(output, "unsupported_build");
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetTopUnavailable(output, "requires_application_main");
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    if (environment.offline_fixture_function_overrides &&
        (access.validate_character == nullptr ||
         access.read_allowlisted_variable == nullptr)) {
      SetTopUnavailable(output, "internal_error");
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }

    ZhongguoWorkforceNormalExitFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    InitializeEnvelope(request, &before, output);
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    if (!before.paused) {
      SetTopUnavailable(output, "requires_paused");
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0 ||
        !ValidateCharacter(environment, access, before.played_character_id)) {
      SetTopUnavailable(output, "map_not_ready");
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }

    RawRows first{};
    RawRows second{};
    if (!ReadAllowlistedRows(environment, access, before.played_character_id,
                             first)) {
      SetTopUnavailable(output, "variable_identifier_unavailable");
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    if (!ReadAllowlistedRows(environment, access, before.played_character_id,
                             second)) {
      SetTopUnavailable(output, "variable_context_unavailable");
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    ZhongguoWorkforceNormalExitFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first != second) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    output.readiness.same_frame_ready = true;
    DecodeRows(environment, access, first, output);
    if (SourceCoreAbsent(output.source)) {
      SetTopUnavailable(output, "case_not_found", true);
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    if (!SourceCoreComplete(output.source)) {
      SetTopUnavailable(output, "case_inconsistent", true);
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    if (!IntEquals(output.source.subject_character_id,
                   before.played_character_id)) {
      SetTopUnavailable(output, "not_received_self", true);
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    if (IntEquals(output.source.owner_character_id,
                  before.played_character_id)) {
      SetTopUnavailable(output, "not_received_self", true);
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    if (!IntEquals(output.source.owner_character_id,
                   request.owner_character_id)) {
      SetTopUnavailable(output, "owner_filter_mismatch", true);
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    if (!DeriveLifecycle(output, before.played_character_id,
                         request.owner_character_id)) {
      SetTopUnavailable(output, "case_inconsistent", true);
      return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
    }
    output.status =
        game::ZhongguoWorkforceNormalExitSnapshotStatusV1::available;
    output.unavailable_reason.clear();
    return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::available;
  } catch (...) {
    InitializeEnvelope(request, nullptr, output);
    SetTopUnavailable(output, "internal_error");
    return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
