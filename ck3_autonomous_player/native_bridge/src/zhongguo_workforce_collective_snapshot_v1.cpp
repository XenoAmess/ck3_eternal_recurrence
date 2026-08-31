#include "xar_bridge/zhongguo_workforce_collective_snapshot_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <initializer_list>
#include <limits>
#include <string>
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

using SubjectRows =
    std::array<ZhongguoWorkforceRawVariableV1,
               kZhongguoWorkforceSubjectVariableAllowlist.size()>;
using OwnerRows =
    std::array<ZhongguoWorkforceRawVariableV1,
               kZhongguoWorkforceOwnerVariableAllowlist.size()>;

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

bool ReadBytes(const ZhongguoWorkforceAccessV1 &access, const void *address,
               void *output, std::size_t size) noexcept {
  return access.read_memory != nullptr
             ? access.read_memory(access.context, address, output, size)
             : GuardedDirectRead(address, output, size);
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
bool ReadValue(const ZhongguoWorkforceAccessV1 &access, const void *base,
               std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment) noexcept {
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
         reinterpret_cast<std::uintptr_t>(
             environment.character_storage_slot) ==
             base + kZhongguoCharacterStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.character_fallback_slot) ==
             base + kZhongguoCharacterFallbackSlotRva;
}

bool ResolveCharacterNative(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access,
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
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access,
    std::int32_t character_id) noexcept {
  return environment.offline_fixture_function_overrides
             ? access.validate_character != nullptr &&
                   access.validate_character(access.context, character_id)
             : ResolveCharacterNative(environment, access, character_id);
}

bool ResolveVariableIdentifier(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
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

bool FindVariableValue(const ZhongguoWorkforceAccessV1 &access,
                       void *context, std::int32_t identifier,
                       ZhongguoWorkforceRawVariableV1 &output) noexcept {
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
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access, std::int32_t character_id,
    std::string_view key, ZhongguoWorkforceRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) return false;
  const ZhongguoEventTarget16V1 target{4, {}, character_id};
  void *const context = environment.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

template <std::size_t Size>
bool ReadAllowlistedRows(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access, std::int32_t character_id,
    const std::array<std::string_view, Size> &allowlist,
    std::array<ZhongguoWorkforceRawVariableV1, Size> &output) noexcept {
  for (std::size_t index = 0; index < Size; ++index) {
    const auto key = allowlist[index];
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

template <std::size_t Size>
const ZhongguoWorkforceRawVariableV1 &Row(
    const std::array<std::string_view, Size> &allowlist,
    const std::array<ZhongguoWorkforceRawVariableV1, Size> &rows,
    std::string_view key) {
  const auto found = std::find(allowlist.begin(), allowlist.end(), key);
  if (found == allowlist.end()) throw 0;
  return rows[static_cast<std::size_t>(found - allowlist.begin())];
}

const ZhongguoWorkforceRawVariableV1 &SubjectRow(
    const SubjectRows &rows, std::string_view key) {
  return Row(kZhongguoWorkforceSubjectVariableAllowlist, rows, key);
}

const ZhongguoWorkforceRawVariableV1 &OwnerRow(
    const OwnerRows &rows, std::string_view key) {
  return Row(kZhongguoWorkforceOwnerVariableAllowlist, rows, key);
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

void DecodeInteger(const ZhongguoWorkforceRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1 || raw.payload % kFixedScale != 0) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload / kFixedScale);
  }
}

void DecodeBoolean(const ZhongguoWorkforceRawVariableV1 &raw,
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
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access,
    const ZhongguoWorkforceRawVariableV1 &raw,
    game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 4 || raw.payload <= 0 ||
             raw.payload > std::numeric_limits<std::int32_t>::max() ||
             !ValidateCharacter(environment, access,
                                static_cast<std::int32_t>(raw.payload))) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload);
  }
}

template <typename Value>
bool Available(const game::ZhongguoTypedValueV1<Value> &field) noexcept {
  return field.available && field.value.has_value();
}

std::int64_t Integer(const game::ZhongguoTypedIntegerV1 &field) noexcept {
  return Available(field) ? *field.value
                          : std::numeric_limits<std::int64_t>::min();
}

bool Boolean(const game::ZhongguoTypedBooleanV1 &field) noexcept {
  return Available(field) && *field.value;
}

void WipeCase(game::ZhongguoWorkforceCaseV1 &value,
              std::string_view reason) {
  SetUnavailable(value.owner_character_id, reason);
  SetUnavailable(value.subject_character_id, reason);
  SetUnavailable(value.cycle_serial, reason);
  SetUnavailable(value.case_serial, reason);
  SetUnavailable(value.state, reason);
  SetUnavailable(value.active, reason);
  SetUnavailable(value.revision, reason);
}

void WipeReceipt(game::ZhongguoWorkforceM360ReceiptV1 &value,
                 std::string_view reason) {
  SetUnavailable(value.owner_character_id, reason);
  SetUnavailable(value.subject_character_id, reason);
  SetUnavailable(value.cycle_serial, reason);
  SetUnavailable(value.case_serial, reason);
  SetUnavailable(value.state, reason);
  SetUnavailable(value.choice, reason);
}

void WipeCollective(game::ZhongguoWorkforceCollectiveV1 &value,
                    std::string_view reason) {
  value.phase = game::ZhongguoWorkforceCollectivePhaseV1::unavailable;
  SetUnavailable(value.submission_active, reason);
  SetUnavailable(value.submission_sealed, reason);
  SetUnavailable(value.submission_consumed, reason);
  SetUnavailable(value.owner_character_id, reason);
  SetUnavailable(value.subject_character_id, reason);
  SetUnavailable(value.cycle_serial, reason);
  SetUnavailable(value.case_serial, reason);
  SetUnavailable(value.state, reason);
  SetUnavailable(value.collective_case_serial, reason);
  SetUnavailable(value.submitted_cycle_serial, reason);
  SetUnavailable(value.cohort_count, reason);
  SetUnavailable(value.settlement_id, reason);
  SetUnavailable(value.settlement_hash, reason);
  SetUnavailable(value.settled, reason);
  SetUnavailable(value.route, reason);
  SetUnavailable(value.total_members, reason);
  SetUnavailable(value.total_quota, reason);
  SetUnavailable(value.forced_count, reason);
  SetUnavailable(value.exception_count, reason);
  SetUnavailable(value.manager_cost_total, reason);
}

void WipeCohort(game::ZhongguoWorkforceCohortV1 &value,
                std::string_view reason) {
  SetUnavailable(value.cohort_id, reason);
  SetUnavailable(value.manager_character_id, reason);
  SetUnavailable(value.member_count, reason);
  SetUnavailable(value.member_hash, reason);
  SetUnavailable(value.quota, reason);
  SetUnavailable(value.forced_count, reason);
  SetUnavailable(value.exception_count, reason);
  SetUnavailable(value.manager_cost, reason);
  SetUnavailable(value.partition_verified, reason);
  SetUnavailable(value.approval_verified, reason);
  SetUnavailable(value.b1_cycle_serial, reason);
  SetUnavailable(value.b1_case_serial, reason);
  SetUnavailable(value.b1_source_id, reason);
  SetUnavailable(value.b1_source_hash, reason);
  SetUnavailable(value.mg_cycle_serial, reason);
  SetUnavailable(value.mg_case_serial, reason);
  SetUnavailable(value.mg_snapshot_source_serial, reason);
  SetUnavailable(value.mg_snapshot_revision, reason);
}

void WipeDebt(game::ZhongguoWorkforceDebtV1 &value,
              std::string_view reason) {
  SetUnavailable(value.owner_character_id, reason);
  SetUnavailable(value.subject_character_id, reason);
  SetUnavailable(value.cycle_serial, reason);
  SetUnavailable(value.case_serial, reason);
  SetUnavailable(value.state, reason);
  SetUnavailable(value.open, reason);
  SetUnavailable(value.consumed, reason);
  SetUnavailable(value.due_cycle_serial, reason);
}

void WipeHistorySlot(game::ZhongguoWorkforceHistorySlotV1 &value,
                     std::string_view reason) {
  SetUnavailable(value.owner_character_id, reason);
  SetUnavailable(value.subject_character_id, reason);
  SetUnavailable(value.cycle_serial, reason);
  SetUnavailable(value.case_serial, reason);
  SetUnavailable(value.m357_receipt_id, reason);
  SetUnavailable(value.m357_receipt_hash, reason);
  SetUnavailable(value.m358_receipt_id, reason);
  SetUnavailable(value.m358_receipt_hash, reason);
  SetUnavailable(value.m359_receipt_id, reason);
  SetUnavailable(value.m359_receipt_hash, reason);
}

void WipeHistory(game::ZhongguoWorkforceHistoryV1 &value,
                 std::string_view reason) {
  value.status = game::ZhongguoWorkforceHistoryStatusV1::unavailable;
  SetUnavailable(value.count, reason);
  for (auto &slot : value.slots) WipeHistorySlot(slot, reason);
}

void WipeCharter(game::ZhongguoWorkforceCharterGateV1 &value,
                 std::string_view reason) {
  value.status = game::ZhongguoWorkforceCharterGateStatusV1::unavailable;
  SetUnavailable(value.evidence_count, reason);
  SetUnavailable(value.evidence_ready, reason);
  SetUnavailable(value.evidence_consumed, reason);
  SetUnavailable(value.owner_character_id, reason);
  SetUnavailable(value.subject_character_id, reason);
  SetUnavailable(value.cycle_serial, reason);
  SetUnavailable(value.case_serial, reason);
  SetUnavailable(value.state, reason);
  SetUnavailable(value.prepared_report_id, reason);
  SetUnavailable(value.prepared_charter_id, reason);
  SetUnavailable(value.previous_charter_id, reason);
  SetUnavailable(value.previous_version, reason);
  SetUnavailable(value.adopted_cycle_serial, reason);
  SetUnavailable(value.effective_cycle_serial, reason);
  SetUnavailable(value.portfolio_status, reason);
  SetUnavailable(value.portfolio_closed, reason);
  SetUnavailable(value.terminal_history_accruing, reason);
  SetUnavailable(value.portfolio_history_cycle_count, reason);
  SetUnavailable(value.terminal_success, reason);
}

void WipeSemanticPayload(
    game::ZhongguoWorkforceCollectiveSnapshotV1 &value,
    std::string_view reason) {
  WipeCase(value.al_case, reason);
  WipeReceipt(value.m360_receipt, reason);
  WipeCollective(value.collective, reason);
  for (auto &cohort : value.cohorts) WipeCohort(cohort, reason);
  WipeDebt(value.route_c_debt, reason);
  WipeHistory(value.history, reason);
  WipeCharter(value.charter_gate, reason);
  value.readiness = {};
}

game::ReadZhongguoWorkforceCollectiveSnapshotResultV1 SetTopUnavailable(
    game::ZhongguoWorkforceCollectiveSnapshotV1 &output,
    std::string_view reason) {
  output.status =
      game::ZhongguoWorkforceCollectiveSnapshotStatusV1::unavailable;
  output.unavailable_reason.assign(reason);
  WipeSemanticPayload(output, "case_unavailable");
  return game::ReadZhongguoWorkforceCollectiveSnapshotResultV1::unavailable;
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

bool AllAbsent(const SubjectRows &rows,
               std::initializer_list<std::string_view> keys) {
  return std::all_of(keys.begin(), keys.end(), [&](std::string_view key) {
    return !SubjectRow(rows, key).present;
  });
}

bool AllAbsent(const OwnerRows &rows,
               std::initializer_list<std::string_view> keys) {
  return std::all_of(keys.begin(), keys.end(), [&](std::string_view key) {
    return !OwnerRow(rows, key).present;
  });
}

std::string CohortKey(std::size_t slot, std::string_view suffix) {
  return "zg361_we_al_external_collective_" + std::to_string(slot) + "_" +
         std::string(suffix);
}

std::string HistoryKey(std::size_t slot, std::string_view field) {
  return "zg361_we_completed_cycle_ledger_" + std::string(field) + "_" +
         std::to_string(slot);
}

std::string EvidenceKey(std::size_t slot, std::string_view field) {
  return "zg361_we_m361_evidence_" + std::string(field) + "_" +
         std::to_string(slot);
}

bool SameAvailableInteger(const game::ZhongguoTypedIntegerV1 &left,
                          const game::ZhongguoTypedIntegerV1 &right) noexcept {
  return Available(left) && Available(right) && Integer(left) == Integer(right);
}

bool FrozenEvidenceMatchesHistory(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access, const SubjectRows &rows,
    const game::ZhongguoWorkforceHistoryV1 &history) {
  if (history.status != game::ZhongguoWorkforceHistoryStatusV1::three_cycle) {
    return false;
  }
  for (std::size_t index = 0; index < history.slots.size(); ++index) {
    const auto slot_number = index + 1;
    game::ZhongguoWorkforceHistorySlotV1 frozen{};
    DecodeCharacter(environment, access,
                    SubjectRow(rows, EvidenceKey(slot_number, "owner")),
                    frozen.owner_character_id);
    DecodeCharacter(environment, access,
                    SubjectRow(rows, EvidenceKey(slot_number, "subject")),
                    frozen.subject_character_id);
    DecodeInteger(SubjectRow(rows, EvidenceKey(slot_number, "cycle")),
                  frozen.cycle_serial);
    DecodeInteger(SubjectRow(rows, EvidenceKey(slot_number, "case")),
                  frozen.case_serial);
    DecodeInteger(
        SubjectRow(rows, EvidenceKey(slot_number, "m357_receipt_id")),
        frozen.m357_receipt_id);
    DecodeInteger(
        SubjectRow(rows, EvidenceKey(slot_number, "m357_receipt_hash")),
        frozen.m357_receipt_hash);
    DecodeInteger(
        SubjectRow(rows, EvidenceKey(slot_number, "m358_receipt_id")),
        frozen.m358_receipt_id);
    DecodeInteger(
        SubjectRow(rows, EvidenceKey(slot_number, "m358_receipt_hash")),
        frozen.m358_receipt_hash);
    DecodeInteger(
        SubjectRow(rows, EvidenceKey(slot_number, "m359_receipt_id")),
        frozen.m359_receipt_id);
    DecodeInteger(
        SubjectRow(rows, EvidenceKey(slot_number, "m359_receipt_hash")),
        frozen.m359_receipt_hash);
    const auto &live = history.slots[index];
    if (!SameAvailableInteger(frozen.owner_character_id,
                              live.owner_character_id) ||
        !SameAvailableInteger(frozen.subject_character_id,
                              live.subject_character_id) ||
        !SameAvailableInteger(frozen.cycle_serial, live.cycle_serial) ||
        !SameAvailableInteger(frozen.case_serial, live.case_serial) ||
        !SameAvailableInteger(frozen.m357_receipt_id,
                              live.m357_receipt_id) ||
        !SameAvailableInteger(frozen.m357_receipt_hash,
                              live.m357_receipt_hash) ||
        !SameAvailableInteger(frozen.m358_receipt_id,
                              live.m358_receipt_id) ||
        !SameAvailableInteger(frozen.m358_receipt_hash,
                              live.m358_receipt_hash) ||
        !SameAvailableInteger(frozen.m359_receipt_id,
                              live.m359_receipt_id) ||
        !SameAvailableInteger(frozen.m359_receipt_hash,
                              live.m359_receipt_hash)) {
      return false;
    }
  }
  return true;
}

bool ReceiptFieldsPresent(const SubjectRows &rows) {
  constexpr std::array<std::string_view, 6> keys{
      "zg361_we_m360_receipt_owner",
      "zg361_we_m360_receipt_subject",
      "zg361_we_m360_receipt_cycle",
      "zg361_we_m360_receipt_case",
      "zg361_we_m360_receipt_state",
      "zg361_we_m360_receipt_choice"};
  return std::all_of(keys.begin(), keys.end(), [&](std::string_view key) {
    return SubjectRow(rows, key).present;
  });
}

bool ReceiptFieldsAbsent(const SubjectRows &rows) {
  return AllAbsent(rows, {"zg361_we_m360_receipt_owner",
                          "zg361_we_m360_receipt_subject",
                          "zg361_we_m360_receipt_cycle",
                          "zg361_we_m360_receipt_case",
                          "zg361_we_m360_receipt_state",
                          "zg361_we_m360_receipt_choice"});
}

void DecodeReceipt(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access, const SubjectRows &rows,
    game::ZhongguoWorkforceM360ReceiptV1 &output) {
  DecodeCharacter(environment, access,
                  SubjectRow(rows, "zg361_we_m360_receipt_owner"),
                  output.owner_character_id);
  DecodeCharacter(environment, access,
                  SubjectRow(rows, "zg361_we_m360_receipt_subject"),
                  output.subject_character_id);
  DecodeInteger(SubjectRow(rows, "zg361_we_m360_receipt_cycle"),
                output.cycle_serial);
  DecodeInteger(SubjectRow(rows, "zg361_we_m360_receipt_case"),
                output.case_serial);
  DecodeInteger(SubjectRow(rows, "zg361_we_m360_receipt_state"), output.state);
  DecodeInteger(SubjectRow(rows, "zg361_we_m360_receipt_choice"),
                output.choice);
}

bool ReceiptMatches(const game::ZhongguoWorkforceM360ReceiptV1 &receipt,
                    const game::ZhongguoWorkforceCaseV1 &al_case) noexcept {
  return Available(receipt.owner_character_id) &&
         Available(receipt.subject_character_id) &&
         Available(receipt.cycle_serial) && Available(receipt.case_serial) &&
         Available(receipt.state) && Available(receipt.choice) &&
         Integer(receipt.owner_character_id) ==
             Integer(al_case.owner_character_id) &&
         Integer(receipt.subject_character_id) ==
             Integer(al_case.subject_character_id) &&
         Integer(receipt.cycle_serial) == Integer(al_case.cycle_serial) &&
         Integer(receipt.case_serial) == Integer(al_case.case_serial) &&
         Integer(receipt.state) == 4 && Integer(receipt.choice) >= 1 &&
         Integer(receipt.choice) <= 3;
}

bool DecodeCollective(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access, const SubjectRows &rows,
    const game::ZhongguoWorkforceCaseV1 &al_case,
    const game::ZhongguoWorkforceM360ReceiptV1 &receipt,
    game::ZhongguoWorkforceCollectiveSnapshotV1 &output) {
  auto &value = output.collective;
  const auto choice = Integer(receipt.choice);
  value.phase = choice == 1
                    ? game::ZhongguoWorkforceCollectivePhaseV1::
                          route_a_exception
                    : game::ZhongguoWorkforceCollectivePhaseV1::route_b_forced;
#define XAR_SUBJECT_INT(member, key)                                            \
  DecodeInteger(SubjectRow(rows, key), value.member)
#define XAR_SUBJECT_BOOL(member, key)                                           \
  DecodeBoolean(SubjectRow(rows, key), value.member)
  XAR_SUBJECT_BOOL(submission_active,
                   "zg361_we_al_external_collective_submission_active");
  XAR_SUBJECT_BOOL(submission_sealed,
                   "zg361_we_al_external_collective_submission_sealed");
  XAR_SUBJECT_BOOL(submission_consumed,
                   "zg361_we_al_external_collective_submission_consumed");
  DecodeCharacter(
      environment, access,
      SubjectRow(rows, "zg361_we_al_external_collective_submission_owner"),
      value.owner_character_id);
  DecodeCharacter(
      environment, access,
      SubjectRow(rows, "zg361_we_al_external_collective_submission_subject"),
      value.subject_character_id);
  XAR_SUBJECT_INT(cycle_serial,
                  "zg361_we_al_external_collective_submission_cycle");
  XAR_SUBJECT_INT(case_serial,
                  "zg361_we_al_external_collective_submission_case");
  XAR_SUBJECT_INT(state,
                  "zg361_we_al_external_collective_submission_state");
  XAR_SUBJECT_INT(collective_case_serial,
                  "zg361_we_al_external_collective_case");
  XAR_SUBJECT_INT(submitted_cycle_serial,
                  "zg361_we_al_external_collective_submitted_cycle");
  XAR_SUBJECT_INT(cohort_count,
                  "zg361_we_al_external_collective_cohort_count");
  XAR_SUBJECT_INT(settlement_id,
                  "zg361_we_al_external_collective_settlement_id");
  XAR_SUBJECT_INT(settlement_hash,
                  "zg361_we_al_external_collective_settlement_hash");
  XAR_SUBJECT_BOOL(settled, "zg361_we_al_external_collective_settled");
  XAR_SUBJECT_INT(route, "zg361_we_al_external_collective_route");
  XAR_SUBJECT_INT(total_members,
                  "zg361_we_al_external_collective_total_members");
  XAR_SUBJECT_INT(total_quota,
                  "zg361_we_al_external_collective_total_quota");
  XAR_SUBJECT_INT(forced_count,
                  "zg361_we_al_external_collective_forced_count");
  XAR_SUBJECT_INT(exception_count,
                  "zg361_we_al_external_collective_exception_count");
  XAR_SUBJECT_INT(manager_cost_total,
                  "zg361_we_al_external_collective_manager_cost_total");
#undef XAR_SUBJECT_INT
#undef XAR_SUBJECT_BOOL

  bool cohorts_ready = true;
  std::int64_t members = 0;
  std::int64_t quota = 0;
  std::int64_t forced = 0;
  std::int64_t exceptions = 0;
  std::int64_t manager_cost = 0;
  for (std::size_t index = 0; index < output.cohorts.size(); ++index) {
    const auto slot = index + 1;
    auto &cohort = output.cohorts[index];
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "cohort_id")),
                  cohort.cohort_id);
    DecodeCharacter(environment, access,
                    SubjectRow(rows, CohortKey(slot, "manager")),
                    cohort.manager_character_id);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "member_count")),
                  cohort.member_count);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "member_hash")),
                  cohort.member_hash);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "quota")), cohort.quota);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "forced_count")),
                  cohort.forced_count);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "exception_count")),
                  cohort.exception_count);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "manager_cost")),
                  cohort.manager_cost);
    DecodeBoolean(SubjectRow(rows, CohortKey(slot, "partition_verified")),
                  cohort.partition_verified);
    DecodeBoolean(SubjectRow(rows, CohortKey(slot, "approval_verified")),
                  cohort.approval_verified);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "b1_cycle")),
                  cohort.b1_cycle_serial);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "b1_case")),
                  cohort.b1_case_serial);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "b1_source_id")),
                  cohort.b1_source_id);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "b1_source_hash")),
                  cohort.b1_source_hash);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "mg_cycle")),
                  cohort.mg_cycle_serial);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "mg_case")),
                  cohort.mg_case_serial);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "mg_snapshot_source_serial")),
                  cohort.mg_snapshot_source_serial);
    DecodeInteger(SubjectRow(rows, CohortKey(slot, "mg_snapshot_revision")),
                  cohort.mg_snapshot_revision);
    const bool route_values =
        choice == 1
            ? Integer(cohort.forced_count) == 0 &&
                  Integer(cohort.exception_count) == Integer(cohort.quota) &&
                  Integer(cohort.manager_cost) == Integer(cohort.quota) &&
                  Boolean(cohort.approval_verified)
            : Integer(cohort.forced_count) == Integer(cohort.quota) &&
                  Integer(cohort.exception_count) == 0 &&
                  Integer(cohort.manager_cost) == 0 &&
                  Available(cohort.approval_verified) &&
                  !Boolean(cohort.approval_verified);
    const bool ready = Available(cohort.cohort_id) &&
                       Available(cohort.manager_character_id) &&
                       Available(cohort.member_count) &&
                       Available(cohort.member_hash) &&
                       Available(cohort.quota) && Integer(cohort.quota) >= 0 &&
                       Integer(cohort.quota) <= 6 &&
                       Integer(cohort.member_count) >= Integer(cohort.quota) &&
                       Available(cohort.forced_count) &&
                       Available(cohort.exception_count) &&
                       Available(cohort.manager_cost) &&
                       Boolean(cohort.partition_verified) && route_values &&
                       Available(cohort.b1_cycle_serial) &&
                       Available(cohort.b1_case_serial) &&
                       Available(cohort.b1_source_id) &&
                       Available(cohort.b1_source_hash) &&
                       Available(cohort.mg_cycle_serial) &&
                       Available(cohort.mg_case_serial) &&
                       Available(cohort.mg_snapshot_source_serial) &&
                       Available(cohort.mg_snapshot_revision) &&
                       Integer(cohort.b1_cycle_serial) >= 1 &&
                       Integer(cohort.b1_case_serial) > 0 &&
                       Integer(cohort.b1_source_id) > 0 &&
                       Integer(cohort.b1_source_hash) > 0 &&
                       Integer(cohort.mg_cycle_serial) >= 1 &&
                       Integer(cohort.mg_case_serial) > 0 &&
                       Integer(cohort.mg_snapshot_source_serial) > 0 &&
                       Integer(cohort.mg_snapshot_revision) > 0;
    cohorts_ready = cohorts_ready && ready;
    if (ready) {
      members += Integer(cohort.member_count);
      quota += Integer(cohort.quota);
      forced += Integer(cohort.forced_count);
      exceptions += Integer(cohort.exception_count);
      manager_cost += Integer(cohort.manager_cost);
    }
  }
  const bool distinct = cohorts_ready &&
                        Integer(output.cohorts[0].cohort_id) !=
                            Integer(output.cohorts[1].cohort_id) &&
                        Integer(output.cohorts[0].cohort_id) !=
                            Integer(output.cohorts[2].cohort_id) &&
                        Integer(output.cohorts[1].cohort_id) !=
                            Integer(output.cohorts[2].cohort_id) &&
                        Integer(output.cohorts[0].manager_character_id) !=
                            Integer(output.cohorts[1].manager_character_id) &&
                        Integer(output.cohorts[0].manager_character_id) !=
                            Integer(output.cohorts[2].manager_character_id) &&
                        Integer(output.cohorts[1].manager_character_id) !=
                            Integer(output.cohorts[2].manager_character_id);
  output.readiness.cohort_identity_ready = distinct;
  output.readiness.cohort_conservation_ready =
      cohorts_ready && Available(value.total_members) &&
      Available(value.total_quota) && Integer(value.total_members) == members &&
      Integer(value.total_quota) == quota && quota >= 1 && quota <= 6;
  output.readiness.route_conservation_ready =
      output.readiness.cohort_conservation_ready &&
      Available(value.forced_count) && Available(value.exception_count) &&
      Available(value.manager_cost_total) &&
      Integer(value.forced_count) == forced &&
      Integer(value.exception_count) == exceptions &&
      Integer(value.manager_cost_total) == manager_cost;
  output.readiness.collective_lifecycle_ready =
      Available(value.submission_active) &&
      Available(value.submission_sealed) &&
      Available(value.submission_consumed) &&
      !Boolean(value.submission_active) && Boolean(value.submission_sealed) &&
      Boolean(value.submission_consumed) &&
      Available(value.owner_character_id) &&
      Available(value.subject_character_id) &&
      Available(value.cycle_serial) && Available(value.case_serial) &&
      Available(value.state) && Available(value.collective_case_serial) &&
      Available(value.submitted_cycle_serial) &&
      Available(value.cohort_count) && Available(value.settlement_id) &&
      Available(value.settlement_hash) && Boolean(value.settled) &&
      Available(value.route) && Integer(value.owner_character_id) ==
                                    Integer(al_case.owner_character_id) &&
      Integer(value.subject_character_id) ==
          Integer(al_case.subject_character_id) &&
      Integer(value.cycle_serial) == Integer(al_case.cycle_serial) &&
      Integer(value.case_serial) == Integer(al_case.case_serial) &&
      Integer(value.state) == 4 &&
      Integer(value.collective_case_serial) == Integer(al_case.case_serial) &&
      Integer(value.submitted_cycle_serial) == Integer(al_case.cycle_serial) &&
      Integer(value.cohort_count) == 3 && Integer(value.settlement_id) > 0 &&
      Integer(value.settlement_hash) > 0 && Integer(value.route) == choice &&
      output.readiness.cohort_identity_ready &&
      output.readiness.cohort_conservation_ready &&
      output.readiness.route_conservation_ready;
  return output.readiness.collective_lifecycle_ready;
}

bool DecodeRouteCDebt(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access, const SubjectRows &rows,
    const game::ZhongguoWorkforceCaseV1 &al_case,
    game::ZhongguoWorkforceDebtV1 &value) {
  DecodeCharacter(environment, access,
                  SubjectRow(rows, "zg361_we_m360_debt_owner"),
                  value.owner_character_id);
  DecodeCharacter(environment, access,
                  SubjectRow(rows, "zg361_we_m360_debt_subject"),
                  value.subject_character_id);
  DecodeInteger(SubjectRow(rows, "zg361_we_m360_debt_cycle"),
                value.cycle_serial);
  DecodeInteger(SubjectRow(rows, "zg361_we_m360_debt_case"), value.case_serial);
  DecodeInteger(SubjectRow(rows, "zg361_we_m360_debt_state"), value.state);
  DecodeBoolean(SubjectRow(rows, "zg361_we_m360_debt_open"), value.open);
  DecodeBoolean(SubjectRow(rows, "zg361_we_m360_debt_consumed"),
                value.consumed);
  DecodeInteger(SubjectRow(rows, "zg361_we_m360_debt_due_cycle"),
                value.due_cycle_serial);
  const bool lifecycle =
      (Boolean(value.open) && Available(value.consumed) &&
       !Boolean(value.consumed)) ||
      (Available(value.open) && !Boolean(value.open) &&
       Boolean(value.consumed));
  return Available(value.owner_character_id) &&
         Available(value.subject_character_id) &&
         Available(value.cycle_serial) && Available(value.case_serial) &&
         Available(value.state) && lifecycle &&
         Available(value.due_cycle_serial) &&
         Integer(value.owner_character_id) ==
             Integer(al_case.owner_character_id) &&
         Integer(value.subject_character_id) ==
             Integer(al_case.subject_character_id) &&
         Integer(value.cycle_serial) == Integer(al_case.cycle_serial) &&
         Integer(value.case_serial) == Integer(al_case.case_serial) &&
         Integer(value.state) == 4 &&
         Integer(value.due_cycle_serial) == Integer(al_case.cycle_serial) + 1;
}

bool DecodeHistory(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access, const OwnerRows &rows,
    std::int32_t owner_character_id,
    game::ZhongguoWorkforceCollectiveSnapshotV1 &output) {
  auto &history = output.history;
  const auto &count_raw =
      OwnerRow(rows, "zg361_we_completed_cycle_ledger_count");
  if (!count_raw.present) {
    history.status = game::ZhongguoWorkforceHistoryStatusV1::empty;
    SetUnavailable(history.count, "variable_absent");
    for (auto &slot : history.slots) {
      WipeHistorySlot(slot, "lifecycle_not_reached");
    }
    output.readiness.history_ledger_ready = true;
    output.readiness.history_order_ready = true;
    output.readiness.three_cycle_ready = false;
    return true;
  }
  DecodeInteger(count_raw, history.count);
  const auto count = Integer(history.count);
  if (count < 1 || count > 3) return false;
  history.status = count == 3
                       ? game::ZhongguoWorkforceHistoryStatusV1::three_cycle
                       : game::ZhongguoWorkforceHistoryStatusV1::partial;
  bool slots_ready = true;
  std::int64_t previous_cycle = 0;
  for (std::size_t index = 0; index < history.slots.size(); ++index) {
    const auto slot_number = index + 1;
    auto &slot = history.slots[index];
    if (static_cast<std::int64_t>(slot_number) > count) {
      WipeHistorySlot(slot, "lifecycle_not_reached");
      continue;
    }
    DecodeCharacter(environment, access,
                    OwnerRow(rows, HistoryKey(slot_number, "owner")),
                    slot.owner_character_id);
    DecodeCharacter(environment, access,
                    OwnerRow(rows, HistoryKey(slot_number, "subject")),
                    slot.subject_character_id);
    DecodeInteger(OwnerRow(rows, HistoryKey(slot_number, "cycle")),
                  slot.cycle_serial);
    DecodeInteger(OwnerRow(rows, HistoryKey(slot_number, "case")),
                  slot.case_serial);
    DecodeInteger(OwnerRow(rows, HistoryKey(slot_number, "m357_receipt_id")),
                  slot.m357_receipt_id);
    DecodeInteger(
        OwnerRow(rows, HistoryKey(slot_number, "m357_receipt_hash")),
        slot.m357_receipt_hash);
    DecodeInteger(OwnerRow(rows, HistoryKey(slot_number, "m358_receipt_id")),
                  slot.m358_receipt_id);
    DecodeInteger(
        OwnerRow(rows, HistoryKey(slot_number, "m358_receipt_hash")),
        slot.m358_receipt_hash);
    DecodeInteger(OwnerRow(rows, HistoryKey(slot_number, "m359_receipt_id")),
                  slot.m359_receipt_id);
    DecodeInteger(
        OwnerRow(rows, HistoryKey(slot_number, "m359_receipt_hash")),
        slot.m359_receipt_hash);
    const bool ready =
        Available(slot.owner_character_id) &&
        Available(slot.subject_character_id) &&
        Available(slot.cycle_serial) && Available(slot.case_serial) &&
        Integer(slot.owner_character_id) == owner_character_id &&
        Integer(slot.cycle_serial) > previous_cycle &&
        Integer(slot.case_serial) > 0 && Available(slot.m357_receipt_id) &&
        Available(slot.m357_receipt_hash) &&
        Available(slot.m358_receipt_id) &&
        Available(slot.m358_receipt_hash) &&
        Available(slot.m359_receipt_id) &&
        Available(slot.m359_receipt_hash) &&
        Integer(slot.m357_receipt_id) > 0 &&
        Integer(slot.m357_receipt_hash) > 0 &&
        Integer(slot.m358_receipt_id) > 0 &&
        Integer(slot.m358_receipt_hash) > 0 &&
        Integer(slot.m359_receipt_id) > 0 &&
        Integer(slot.m359_receipt_hash) > 0 &&
        Integer(slot.m357_receipt_id) != Integer(slot.m358_receipt_id) &&
        Integer(slot.m357_receipt_id) != Integer(slot.m359_receipt_id) &&
        Integer(slot.m358_receipt_id) != Integer(slot.m359_receipt_id) &&
        Integer(slot.m357_receipt_hash) != Integer(slot.m358_receipt_hash) &&
        Integer(slot.m357_receipt_hash) != Integer(slot.m359_receipt_hash) &&
        Integer(slot.m358_receipt_hash) != Integer(slot.m359_receipt_hash);
    slots_ready = slots_ready && ready;
    if (ready) previous_cycle = Integer(slot.cycle_serial);
  }
  output.readiness.history_ledger_ready = slots_ready;
  output.readiness.history_order_ready = slots_ready;
  output.readiness.three_cycle_ready = slots_ready && count == 3;
  return slots_ready;
}

bool DecodeCharterGate(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access, const SubjectRows &rows,
    const game::ZhongguoWorkforceCaseV1 &al_case,
    game::ZhongguoWorkforceCollectiveSnapshotV1 &output) {
  auto &gate = output.charter_gate;
  DecodeInteger(SubjectRow(rows, "zg361_we_portfolio_status"),
                gate.portfolio_status);
  DecodeBoolean(SubjectRow(rows, "zg361_we_portfolio_closed"),
                gate.portfolio_closed);
  DecodeBoolean(
      SubjectRow(rows, "zg361_we_portfolio_terminal_history_accruing"),
      gate.terminal_history_accruing);
  DecodeInteger(
      SubjectRow(rows, "zg361_we_portfolio_history_cycle_count"),
      gate.portfolio_history_cycle_count);
  DecodeBoolean(SubjectRow(rows, "zg361_we_portfolio_terminal_success"),
                gate.terminal_success);

  const auto count = Available(output.history.count)
                         ? Integer(output.history.count)
                         : 0;
  if (count == 3) {
    const auto &tail = output.history.slots.back();
    const bool tail_matches_current_case =
        SameAvailableInteger(tail.owner_character_id,
                             al_case.owner_character_id) &&
        SameAvailableInteger(tail.subject_character_id,
                             al_case.subject_character_id) &&
        SameAvailableInteger(tail.cycle_serial, al_case.cycle_serial) &&
        SameAvailableInteger(tail.case_serial, al_case.case_serial);
    if (!tail_matches_current_case) return false;
  }
  const bool evidence_absent =
      AllAbsent(rows, {"zg361_we_m361_evidence_count",
                       "zg361_we_m361_evidence_ready",
                       "zg361_we_m361_evidence_consumed",
                       "zg361_we_m361_evidence_owner",
                       "zg361_we_m361_evidence_subject",
                       "zg361_we_m361_evidence_cycle",
                       "zg361_we_m361_evidence_case",
                       "zg361_we_m361_evidence_state",
                       "zg361_we_m361_prepared_report_id",
                       "zg361_we_m361_prepared_charter_id",
                       "zg361_we_m361_prepared_previous_charter_id",
                       "zg361_we_m361_prepared_previous_version",
                       "zg361_we_m361_prepared_adopted_cycle",
                       "zg361_we_m361_prepared_effective_cycle"});
  if (evidence_absent) {
    const auto status = count < 3
                            ? game::ZhongguoWorkforceCharterGateStatusV1::
                                  not_eligible
                            : game::ZhongguoWorkforceCharterGateStatusV1::
                                  awaiting_gate;
    WipeCharter(gate, "lifecycle_not_reached");
    gate.status = status;
    DecodeInteger(SubjectRow(rows, "zg361_we_portfolio_status"),
                  gate.portfolio_status);
    DecodeBoolean(SubjectRow(rows, "zg361_we_portfolio_closed"),
                  gate.portfolio_closed);
    DecodeBoolean(
        SubjectRow(rows, "zg361_we_portfolio_terminal_history_accruing"),
        gate.terminal_history_accruing);
    DecodeInteger(
        SubjectRow(rows, "zg361_we_portfolio_history_cycle_count"),
        gate.portfolio_history_cycle_count);
    DecodeBoolean(SubjectRow(rows, "zg361_we_portfolio_terminal_success"),
                  gate.terminal_success);
    output.readiness.charter_gate_lifecycle_ready = true;
    return true;
  }

  DecodeInteger(SubjectRow(rows, "zg361_we_m361_evidence_count"),
                gate.evidence_count);
  DecodeBoolean(SubjectRow(rows, "zg361_we_m361_evidence_ready"),
                gate.evidence_ready);
  DecodeBoolean(SubjectRow(rows, "zg361_we_m361_evidence_consumed"),
                gate.evidence_consumed);
  DecodeCharacter(environment, access,
                  SubjectRow(rows, "zg361_we_m361_evidence_owner"),
                  gate.owner_character_id);
  DecodeCharacter(environment, access,
                  SubjectRow(rows, "zg361_we_m361_evidence_subject"),
                  gate.subject_character_id);
  DecodeInteger(SubjectRow(rows, "zg361_we_m361_evidence_cycle"),
                gate.cycle_serial);
  DecodeInteger(SubjectRow(rows, "zg361_we_m361_evidence_case"),
                gate.case_serial);
  DecodeInteger(SubjectRow(rows, "zg361_we_m361_evidence_state"), gate.state);
  DecodeInteger(SubjectRow(rows, "zg361_we_m361_prepared_report_id"),
                gate.prepared_report_id);
  DecodeInteger(SubjectRow(rows, "zg361_we_m361_prepared_charter_id"),
                gate.prepared_charter_id);
  DecodeInteger(
      SubjectRow(rows, "zg361_we_m361_prepared_previous_charter_id"),
      gate.previous_charter_id);
  DecodeInteger(SubjectRow(rows, "zg361_we_m361_prepared_previous_version"),
                gate.previous_version);
  DecodeInteger(SubjectRow(rows, "zg361_we_m361_prepared_adopted_cycle"),
                gate.adopted_cycle_serial);
  DecodeInteger(SubjectRow(rows, "zg361_we_m361_prepared_effective_cycle"),
                gate.effective_cycle_serial);
  const bool evidence_lifecycle =
      Available(gate.evidence_ready) && Available(gate.evidence_consumed) &&
      !(Boolean(gate.evidence_ready) && Boolean(gate.evidence_consumed));
  const bool frozen_evidence_ready =
      FrozenEvidenceMatchesHistory(environment, access, rows, output.history);
  const bool ready = count == 3 && Available(gate.evidence_count) &&
                     Integer(gate.evidence_count) == 3 &&
                     evidence_lifecycle &&
                     Available(gate.owner_character_id) &&
                     Available(gate.subject_character_id) &&
                     Available(gate.cycle_serial) &&
                     Available(gate.case_serial) && Available(gate.state) &&
                     Available(gate.prepared_report_id) &&
                     Available(gate.prepared_charter_id) &&
                     Available(gate.previous_charter_id) &&
                     Available(gate.previous_version) &&
                     Available(gate.adopted_cycle_serial) &&
                     Available(gate.effective_cycle_serial) &&
                     Integer(gate.owner_character_id) ==
                         Integer(al_case.owner_character_id) &&
                     Integer(gate.subject_character_id) ==
                         Integer(al_case.subject_character_id) &&
                     Integer(gate.cycle_serial) == Integer(al_case.cycle_serial) &&
                     Integer(gate.case_serial) == Integer(al_case.case_serial) &&
                     Integer(gate.state) == 5 &&
                     Integer(gate.prepared_report_id) > 0 &&
                     Integer(gate.prepared_charter_id) > 0 &&
                     Integer(gate.previous_version) >= 0 &&
                     Integer(gate.adopted_cycle_serial) ==
                         Integer(al_case.cycle_serial) &&
                     Integer(gate.effective_cycle_serial) ==
                         Integer(al_case.cycle_serial) + 1 &&
                     frozen_evidence_ready;
  gate.status = Boolean(gate.evidence_consumed)
                    ? game::ZhongguoWorkforceCharterGateStatusV1::consumed
                    : (Boolean(gate.evidence_ready)
                           ? game::ZhongguoWorkforceCharterGateStatusV1::ready
                           : game::ZhongguoWorkforceCharterGateStatusV1::
                                 awaiting_gate);
  output.readiness.charter_gate_lifecycle_ready = ready;
  return ready;
}

} // namespace

ZhongguoWorkforceNativeEnvironmentV1
BindZhongguoWorkforceNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base,
                                             exact_build_admitted);
}

game::ReadZhongguoWorkforceCollectiveSnapshotResultV1
ReadZhongguoWorkforceCollectiveSnapshotV1(
    const ZhongguoWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoWorkforceAccessV1 &access,
    const ZhongguoWorkforceCollectiveSnapshotRequestV1 &request,
    game::ZhongguoWorkforceCollectiveSnapshotV1 &output) noexcept {
  output = {};
  output.case_kind.assign(kZhongguoWorkforceCollectiveSnapshotV1CaseKind);
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  output.requested_owner_character_id = request.owner_character_id;
  try {
    if (!EnvironmentIsExact(environment)) {
      return SetTopUnavailable(output, "unsupported_build");
    }
    if (request.expected_snapshot_revision == 0 ||
        request.owner_character_id <= 0 || !ValidNonce(request.request_nonce)) {
      return SetTopUnavailable(output, "internal_error");
    }
    if (access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      return SetTopUnavailable(output, "requires_application_main");
    }
    if (access.capture_frame == nullptr) {
      return SetTopUnavailable(output, "internal_error");
    }
    game::ZhongguoCaseFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      return SetTopUnavailable(output, "state_changed");
    }
    output.snapshot_revision = before.snapshot_revision;
    output.date_raw = before.date_raw;
    output.paused = before.paused;
    output.player_character_id = before.played_character_id;
    output.subject_character_id = before.played_character_id;
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      return SetTopUnavailable(output, "state_changed");
    }
    if (!before.paused) return SetTopUnavailable(output, "requires_paused");
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0) {
      return SetTopUnavailable(output, "map_not_ready");
    }
    output.readiness.player_subject_binding_ready = true;

    SubjectRows subject_first{};
    if (!ReadAllowlistedRows(environment, access, before.played_character_id,
                             kZhongguoWorkforceSubjectVariableAllowlist,
                             subject_first)) {
      return SetTopUnavailable(output, "variable_context_unavailable");
    }

    DecodeCharacter(environment, access,
                    SubjectRow(subject_first, "zg361_case_al_owner"),
                    output.al_case.owner_character_id);
    DecodeCharacter(environment, access,
                    SubjectRow(subject_first, "zg361_case_al_subject"),
                    output.al_case.subject_character_id);
    DecodeInteger(SubjectRow(subject_first, "zg361_case_al_cycle_serial"),
                  output.al_case.cycle_serial);
    DecodeInteger(SubjectRow(subject_first, "zg361_case_al_case_serial"),
                  output.al_case.case_serial);
    DecodeInteger(SubjectRow(subject_first, "zg361_case_al_state"),
                  output.al_case.state);
    DecodeBoolean(SubjectRow(subject_first, "zg361_case_al_active"),
                  output.al_case.active);
    DecodeInteger(SubjectRow(subject_first, "zg361_case_al_revision"),
                  output.al_case.revision);
    const bool case_ready =
        Available(output.al_case.owner_character_id) &&
        Available(output.al_case.subject_character_id) &&
        Available(output.al_case.cycle_serial) &&
        Available(output.al_case.case_serial) &&
        Available(output.al_case.state) && Available(output.al_case.active) &&
        Available(output.al_case.revision) &&
        Integer(output.al_case.subject_character_id) ==
            before.played_character_id &&
        Integer(output.al_case.cycle_serial) >= 1 &&
        Integer(output.al_case.case_serial) > 0 &&
        Integer(output.al_case.state) >= 1 &&
        Integer(output.al_case.state) <= 8 &&
        Integer(output.al_case.revision) >= 1;
    if (!case_ready) {
      const bool all_absent =
          AllAbsent(subject_first, {"zg361_case_al_owner",
                                    "zg361_case_al_subject",
                                    "zg361_case_al_cycle_serial",
                                    "zg361_case_al_case_serial",
                                    "zg361_case_al_state",
                                    "zg361_case_al_active",
                                    "zg361_case_al_revision"});
      return SetTopUnavailable(output,
                               all_absent ? "case_not_found"
                                          : "case_inconsistent");
    }
    output.readiness.case_identity_ready = true;
    if (Integer(output.al_case.owner_character_id) !=
        request.owner_character_id) {
      return SetTopUnavailable(output, "owner_filter_mismatch");
    }
    output.readiness.owner_binding_ready = true;

    // The caller-supplied owner is only a filter.  Do not touch any owner
    // variable context until the received-self AL case has bound it to the
    // player's actual owner.  The complete subject/owner double read below
    // still gives successful queries one atomic paused frame.
    SubjectRows subject_second{};
    OwnerRows owner_first{};
    OwnerRows owner_second{};
    if (!ReadAllowlistedRows(environment, access, request.owner_character_id,
                             kZhongguoWorkforceOwnerVariableAllowlist,
                             owner_first) ||
        !ReadAllowlistedRows(environment, access, before.played_character_id,
                             kZhongguoWorkforceSubjectVariableAllowlist,
                             subject_second) ||
        !ReadAllowlistedRows(environment, access, request.owner_character_id,
                             kZhongguoWorkforceOwnerVariableAllowlist,
                             owner_second)) {
      return SetTopUnavailable(output, "variable_context_unavailable");
    }
    game::ZhongguoCaseFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        subject_first != subject_second || owner_first != owner_second) {
      return SetTopUnavailable(output, "state_changed");
    }
    output.readiness.same_frame_ready = true;

    const bool receipt_present = ReceiptFieldsPresent(subject_first);
    if (!receipt_present && !ReceiptFieldsAbsent(subject_first)) {
      return SetTopUnavailable(output, "case_inconsistent");
    }
    if (!receipt_present) {
      WipeReceipt(output.m360_receipt, "receipt_not_recorded");
      WipeCollective(output.collective, "lifecycle_not_reached");
      output.collective.phase =
          game::ZhongguoWorkforceCollectivePhaseV1::not_reached;
      for (auto &cohort : output.cohorts) {
        WipeCohort(cohort, "lifecycle_not_reached");
      }
      WipeDebt(output.route_c_debt, "lifecycle_not_reached");
      output.readiness.m360_receipt_projection_ready = true;
      output.readiness.collective_lifecycle_ready = true;
      output.readiness.cohort_identity_ready = true;
      output.readiness.cohort_conservation_ready = true;
      output.readiness.route_conservation_ready = true;
    } else {
      DecodeReceipt(environment, access, subject_first, output.m360_receipt);
      if (!ReceiptMatches(output.m360_receipt, output.al_case)) {
        return SetTopUnavailable(output, "case_inconsistent");
      }
      output.readiness.m360_receipt_projection_ready = true;
      const auto choice = Integer(output.m360_receipt.choice);
      if (choice == 1 || choice == 2) {
        WipeDebt(output.route_c_debt, "not_applicable");
        if (!DecodeCollective(environment, access, subject_first,
                              output.al_case, output.m360_receipt, output)) {
          return SetTopUnavailable(output, "collective_inconsistent");
        }
      } else {
        WipeCollective(output.collective, "not_applicable");
        output.collective.phase =
            game::ZhongguoWorkforceCollectivePhaseV1::route_c_debt;
        for (auto &cohort : output.cohorts) WipeCohort(cohort, "not_applicable");
        if (!DecodeRouteCDebt(environment, access, subject_first,
                              output.al_case, output.route_c_debt)) {
          return SetTopUnavailable(output, "collective_inconsistent");
        }
        output.readiness.collective_lifecycle_ready = true;
        output.readiness.cohort_identity_ready = true;
        output.readiness.cohort_conservation_ready = true;
        output.readiness.route_conservation_ready = true;
      }
    }

    if (!DecodeHistory(environment, access, owner_first,
                       request.owner_character_id, output)) {
      return SetTopUnavailable(output, "history_inconsistent");
    }
    if (!DecodeCharterGate(environment, access, subject_first, output.al_case,
                           output)) {
      return SetTopUnavailable(output, "history_inconsistent");
    }

    output.status =
        game::ZhongguoWorkforceCollectiveSnapshotStatusV1::available;
    output.unavailable_reason.clear();
    output.readiness.ready =
        output.readiness.player_subject_binding_ready &&
        output.readiness.owner_binding_ready &&
        output.readiness.case_identity_ready &&
        output.readiness.m360_receipt_projection_ready &&
        output.readiness.collective_lifecycle_ready &&
        output.readiness.cohort_identity_ready &&
        output.readiness.cohort_conservation_ready &&
        output.readiness.route_conservation_ready &&
        output.readiness.history_ledger_ready &&
        output.readiness.history_order_ready &&
        output.readiness.charter_gate_lifecycle_ready &&
        output.readiness.same_frame_ready;
    return game::ReadZhongguoWorkforceCollectiveSnapshotResultV1::available;
  } catch (...) {
    return SetTopUnavailable(output, "internal_error");
  }
}

} // namespace xar::ck3_11906
