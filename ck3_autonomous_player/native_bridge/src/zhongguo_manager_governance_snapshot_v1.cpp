#include "xar_bridge/zhongguo_manager_governance_snapshot_v1.hpp"

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
  case_owner = 0,
  case_subject,
  case_cycle,
  case_serial,
  case_state,
  case_active,
  case_revision,
  team_status,
  team_owner,
  team_subject,
  team_cycle,
  team_case,
  team_revision,
  team_source_cycle,
  team_n,
  team_targets,
  team_jingcha,
  team_calibration,
  team_pip_success,
  team_appeal_overturn,
  team_retention,
  team_hc_efficiency,
  f035_receipt_owner,
  f035_receipt_subject,
  f035_receipt_cycle,
  f035_receipt_case,
  f035_receipt_state,
  f035_receipt_choice,
  distribution_available,
  distribution_mode,
  distribution_rule_source,
  distribution_top,
  distribution_middle,
  distribution_bottom,
  distribution_conserved,
  policy_status,
  policy_owner,
  policy_subject,
  policy_source_reviewer,
  policy_source_cycle,
  policy_source_case,
  policy_source_revision,
  policy_input_revision,
  policy_mode,
  policy_rule_source,
  policy_due_cycle,
  effective_mode,
  effective_cycle,
  effective_source_cycle,
  effective_source_case,
  effective_input_revision,
  policy_settled_cycle,
  policy_settlement_receipt,
  actual_cohort_n,
  actual_bottom_slots,
  f032_receipt_owner,
  f032_receipt_subject,
  f032_receipt_cycle,
  f032_receipt_case,
  f032_receipt_state,
  f032_receipt_choice,
  manager_score,
  manager_score_mode,
  component_status,
  component_owner,
  component_subject,
  component_source_cycle,
  component_source_case,
  component_source_revision,
  component_input_revision,
  component_number,
  component_value,
  component_due_cycle,
  component_settled_by,
  component_settled_cycle,
  component_settled_value,
  component_settlement_receipt,
};

using RawRows =
    std::array<ZhongguoManagerGovernanceRawVariableV1,
               kZhongguoManagerGovernanceSnapshotV1VariableAllowlist.size()>;

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

bool ReadBytes(const ZhongguoManagerGovernanceAccessV1 &access,
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
bool ReadValue(const ZhongguoManagerGovernanceAccessV1 &access,
               const void *base, std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const ZhongguoManagerGovernanceNativeEnvironmentV1 &environment) noexcept {
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
    const ZhongguoManagerGovernanceNativeEnvironmentV1 &environment,
    const ZhongguoManagerGovernanceAccessV1 &access,
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
    const ZhongguoManagerGovernanceNativeEnvironmentV1 &environment,
    const ZhongguoManagerGovernanceAccessV1 &access,
    std::int32_t character_id) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.validate_character != nullptr &&
           access.validate_character(access.context, character_id);
  }
  return ResolveCharacterNative(environment, access, character_id);
}

bool ResolveVariableIdentifier(
    const ZhongguoManagerGovernanceNativeEnvironmentV1 &environment,
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

bool FindVariableValue(const ZhongguoManagerGovernanceAccessV1 &access,
                       void *context, std::int32_t identifier,
                       ZhongguoManagerGovernanceRawVariableV1 &output) noexcept {
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
    const ZhongguoManagerGovernanceNativeEnvironmentV1 &environment,
    const ZhongguoManagerGovernanceAccessV1 &access,
    std::int32_t character_id, std::string_view key,
    ZhongguoManagerGovernanceRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) return false;
  const ZhongguoEventTarget16V1 target{4, {}, character_id};
  void *const context = environment.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

bool ReadAllowlistedRows(
    const ZhongguoManagerGovernanceNativeEnvironmentV1 &environment,
    const ZhongguoManagerGovernanceAccessV1 &access,
    std::int32_t character_id, RawRows &output) noexcept {
  for (std::size_t index = 0;
       index < kZhongguoManagerGovernanceSnapshotV1VariableAllowlist.size();
       ++index) {
    const auto key =
        kZhongguoManagerGovernanceSnapshotV1VariableAllowlist[index];
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

void DecodeInteger(const ZhongguoManagerGovernanceRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1 || raw.payload % kFixedScale != 0) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload / kFixedScale);
  }
}

void DecodeBoolean(const ZhongguoManagerGovernanceRawVariableV1 &raw,
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
    const ZhongguoManagerGovernanceNativeEnvironmentV1 &environment,
    const ZhongguoManagerGovernanceAccessV1 &access,
    const ZhongguoManagerGovernanceRawVariableV1 &raw,
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
  return Available(field) ? *field.value : std::numeric_limits<std::int64_t>::min();
}

void SetReceiptUnavailable(game::ZhongguoManagerReceiptV1 &value,
                           std::string_view reason) {
  SetUnavailable(value.owner_character_id, reason);
  SetUnavailable(value.subject_character_id, reason);
  SetUnavailable(value.cycle_serial, reason);
  SetUnavailable(value.case_serial, reason);
  SetUnavailable(value.state, reason);
  SetUnavailable(value.choice, reason);
}

void SetDistributionSnapshotUnavailable(
    game::ZhongguoManagerDistributionSnapshotV1 &value,
    std::string_view reason) {
  SetUnavailable(value.available, reason);
  SetUnavailable(value.mode, reason);
  SetUnavailable(value.rule_source, reason);
  SetUnavailable(value.top_slots, reason);
  SetUnavailable(value.middle_slots, reason);
  SetUnavailable(value.bottom_slots, reason);
  SetUnavailable(value.conserved_slots, reason);
}

void SetNextPolicyUnavailable(game::ZhongguoManagerNextCyclePolicyV1 &value,
                              std::string_view reason) {
  SetUnavailable(value.status, reason);
  SetUnavailable(value.owner_character_id, reason);
  SetUnavailable(value.subject_character_id, reason);
  SetUnavailable(value.source_reviewer_character_id, reason);
  SetUnavailable(value.source_cycle, reason);
  SetUnavailable(value.source_case, reason);
  SetUnavailable(value.source_revision, reason);
  SetUnavailable(value.input_revision, reason);
  SetUnavailable(value.mode, reason);
  SetUnavailable(value.rule_source, reason);
  SetUnavailable(value.due_cycle, reason);
}

void SetEffectiveUnavailable(
    game::ZhongguoManagerEffectiveDistributionV1 &value,
    std::string_view reason) {
  SetUnavailable(value.mode, reason);
  SetUnavailable(value.cycle, reason);
  SetUnavailable(value.source_cycle, reason);
  SetUnavailable(value.source_case, reason);
  SetUnavailable(value.input_revision, reason);
  SetUnavailable(value.settled_cycle, reason);
  SetUnavailable(value.settlement_receipt, reason);
  SetUnavailable(value.actual_cohort_n, reason);
  SetUnavailable(value.actual_bottom_slots, reason);
}

void SetComponentUnavailable(game::ZhongguoManagerComponent8V1 &value,
                             std::string_view reason) {
  SetUnavailable(value.status, reason);
  SetUnavailable(value.owner_character_id, reason);
  SetUnavailable(value.subject_character_id, reason);
  SetUnavailable(value.source_cycle, reason);
  SetUnavailable(value.source_case, reason);
  SetUnavailable(value.source_revision, reason);
  SetUnavailable(value.input_revision, reason);
  SetUnavailable(value.component, reason);
  SetUnavailable(value.value, reason);
  SetUnavailable(value.due_cycle, reason);
  SetUnavailable(value.settled_by_owner_character_id, reason);
  SetUnavailable(value.settled_cycle, reason);
  SetUnavailable(value.settled_value, reason);
  SetUnavailable(value.settlement_receipt, reason);
}

void WipeSemanticPayload(game::ZhongguoManagerGovernanceSnapshotV1 &value,
                         std::string_view reason) {
  value.subject_binding.kind =
      game::ZhongguoManagerSubjectBindingKindV1::unavailable;
  SetUnavailable(value.subject_binding.manager_character_id, reason);
  SetUnavailable(value.subject_binding.owner_character_id, reason);
  SetUnavailable(value.subject_binding.bounded_ai_manager_dependency, reason);
  SetUnavailable(value.f_case.owner_character_id, reason);
  SetUnavailable(value.f_case.subject_character_id, reason);
  SetUnavailable(value.f_case.cycle_serial, reason);
  SetUnavailable(value.f_case.case_serial, reason);
  SetUnavailable(value.f_case.state, reason);
  SetUnavailable(value.f_case.active, reason);
  SetUnavailable(value.f_case.revision, reason);
  SetUnavailable(value.team_snapshot.status, reason);
  SetUnavailable(value.team_snapshot.owner_character_id, reason);
  SetUnavailable(value.team_snapshot.subject_character_id, reason);
  SetUnavailable(value.team_snapshot.cycle_serial, reason);
  SetUnavailable(value.team_snapshot.case_serial, reason);
  SetUnavailable(value.team_snapshot.revision, reason);
  SetUnavailable(value.team_snapshot.source_cycle, reason);
  SetUnavailable(value.team_snapshot.cohort_n, reason);
  SetUnavailable(value.team_snapshot.targets, reason);
  SetUnavailable(value.team_snapshot.jingcha, reason);
  SetUnavailable(value.team_snapshot.calibration, reason);
  SetUnavailable(value.team_snapshot.pip_success, reason);
  SetUnavailable(value.team_snapshot.appeal_overturn, reason);
  SetUnavailable(value.team_snapshot.retention, reason);
  SetUnavailable(value.team_snapshot.hc_efficiency, reason);
  SetReceiptUnavailable(value.f035_receipt, reason);
  SetDistributionSnapshotUnavailable(value.distribution_snapshot, reason);
  SetNextPolicyUnavailable(value.next_cycle_policy, reason);
  SetEffectiveUnavailable(value.effective_distribution, reason);
  SetReceiptUnavailable(value.f032_receipt, reason);
  SetUnavailable(value.manager_score.sum, reason);
  SetUnavailable(value.manager_score.mode, reason);
  SetComponentUnavailable(value.component8, reason);
  value.readiness = {};
}

game::ReadZhongguoManagerGovernanceSnapshotResultV1 SetTopUnavailable(
    game::ZhongguoManagerGovernanceSnapshotV1 &output,
    std::string_view reason) {
  output.status =
      game::ZhongguoManagerGovernanceSnapshotStatusV1::unavailable;
  output.unavailable_reason.assign(reason);
  WipeSemanticPayload(output, "case_unavailable");
  return game::ReadZhongguoManagerGovernanceSnapshotResultV1::unavailable;
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

bool ReceiptMatches(const game::ZhongguoManagerReceiptV1 &receipt,
                    const game::ZhongguoManagerFCaseV1 &f_case) noexcept {
  return Available(receipt.owner_character_id) &&
         Available(receipt.subject_character_id) &&
         Available(receipt.cycle_serial) && Available(receipt.case_serial) &&
         Available(receipt.state) && Available(receipt.choice) &&
         Integer(receipt.owner_character_id) ==
             Integer(f_case.owner_character_id) &&
         Integer(receipt.subject_character_id) ==
             Integer(f_case.subject_character_id) &&
         Integer(receipt.cycle_serial) == Integer(f_case.cycle_serial) &&
         Integer(receipt.case_serial) == Integer(f_case.case_serial) &&
         Integer(receipt.state) == 1 && Integer(receipt.choice) >= 1 &&
         Integer(receipt.choice) <= 3;
}

std::int64_t ExpectedBottomSlots(std::int64_t cohort,
                                 std::int64_t mode) noexcept {
  if (cohort < 0) return -1;
  if (mode == 1) {
    const auto slots = cohort / 10;
    return cohort >= 5 && slots < 1 ? 1 : slots;
  }
  if (mode == 2) return cohort / 20;
  if (mode == 3) return 0;
  return -1;
}

void DecodeReceipt(
    const ZhongguoManagerGovernanceNativeEnvironmentV1 &environment,
    const ZhongguoManagerGovernanceAccessV1 &access, const RawRows &rows,
    VariableIndex begin, game::ZhongguoManagerReceiptV1 &output) {
  DecodeCharacter(environment, access, rows[begin],
                  output.owner_character_id);
  DecodeCharacter(environment, access, rows[begin + 1],
                  output.subject_character_id);
  DecodeInteger(rows[begin + 2], output.cycle_serial);
  DecodeInteger(rows[begin + 3], output.case_serial);
  DecodeInteger(rows[begin + 4], output.state);
  DecodeInteger(rows[begin + 5], output.choice);
}

} // namespace

ZhongguoManagerGovernanceNativeEnvironmentV1
BindZhongguoManagerGovernanceNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base,
                                             exact_build_admitted);
}

game::ReadZhongguoManagerGovernanceSnapshotResultV1
ReadZhongguoManagerGovernanceSnapshotV1(
    const ZhongguoManagerGovernanceNativeEnvironmentV1 &environment,
    const ZhongguoManagerGovernanceAccessV1 &access,
    const ZhongguoManagerGovernanceSnapshotRequestV1 &request,
    game::ZhongguoManagerGovernanceSnapshotV1 &output) noexcept {
  output = {};
  output.case_kind.assign(kZhongguoManagerGovernanceSnapshotV1CaseKind);
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  output.subject_character_id = request.subject_character_id;
  output.requested_owner_character_id = request.owner_character_id;
  try {
    if (!EnvironmentIsExact(environment)) {
      return SetTopUnavailable(output, "unsupported_build");
    }
    if (request.expected_snapshot_revision == 0 ||
        request.subject_character_id <= 0 || request.owner_character_id <= 0 ||
        !ValidNonce(request.request_nonce)) {
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
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      return SetTopUnavailable(output, "state_changed");
    }
    if (!before.paused) return SetTopUnavailable(output, "requires_paused");
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0) {
      return SetTopUnavailable(output, "map_not_ready");
    }

    if (request.subject_character_id == before.played_character_id) {
      output.subject_binding.kind =
          game::ZhongguoManagerSubjectBindingKindV1::played_character;
      SetAvailable(output.subject_binding.manager_character_id,
                   static_cast<std::int64_t>(request.subject_character_id));
      SetAvailable(output.subject_binding.owner_character_id,
                   static_cast<std::int64_t>(request.owner_character_id));
      SetUnavailable(output.subject_binding.bounded_ai_manager_dependency,
                     "not_applicable");
      output.readiness.subject_binding_ready = true;
    } else {
      if (request.owner_character_id != before.played_character_id) {
        return SetTopUnavailable(output, "ai_manager_owner_not_player");
      }
      if (access.authorize_bounded_ai_manager == nullptr) {
        return SetTopUnavailable(
            output, "bounded_ai_manager_dependency_unavailable");
      }
      const auto authorization = access.authorize_bounded_ai_manager(
          access.context, before.played_character_id,
          request.subject_character_id, request.owner_character_id);
      if (authorization ==
          ZhongguoBoundedAiManagerAuthorizationV1::dependency_unavailable) {
        return SetTopUnavailable(
            output, "bounded_ai_manager_dependency_unavailable");
      }
      if (authorization != ZhongguoBoundedAiManagerAuthorizationV1::
                               authorized_direct_manager) {
        return SetTopUnavailable(output, "subject_not_bounded_ai_manager");
      }
      output.subject_binding.kind = game::ZhongguoManagerSubjectBindingKindV1::
          bounded_ai_direct_manager;
      SetAvailable(output.subject_binding.manager_character_id,
                   static_cast<std::int64_t>(request.subject_character_id));
      SetAvailable(output.subject_binding.owner_character_id,
                   static_cast<std::int64_t>(request.owner_character_id));
      SetAvailable(output.subject_binding.bounded_ai_manager_dependency,
                   std::string(kZhongguoBoundedAiManagerDependencyV1));
      output.readiness.subject_binding_ready = true;
      output.readiness.bounded_ai_dependency_ready = true;
    }

    RawRows first{};
    RawRows second{};
    if (!ReadAllowlistedRows(environment, access,
                             request.subject_character_id, first) ||
        !ReadAllowlistedRows(environment, access,
                             request.subject_character_id, second)) {
      return SetTopUnavailable(output, "variable_context_unavailable");
    }
    game::ZhongguoCaseFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first != second) {
      return SetTopUnavailable(output, "state_changed");
    }
    output.readiness.same_frame_ready = true;

    DecodeCharacter(environment, access, first[case_owner],
                    output.f_case.owner_character_id);
    DecodeCharacter(environment, access, first[case_subject],
                    output.f_case.subject_character_id);
    DecodeInteger(first[case_cycle], output.f_case.cycle_serial);
    DecodeInteger(first[case_serial], output.f_case.case_serial);
    DecodeInteger(first[case_state], output.f_case.state);
    DecodeBoolean(first[case_active], output.f_case.active);
    DecodeInteger(first[case_revision], output.f_case.revision);
    const bool case_ready =
        Available(output.f_case.owner_character_id) &&
        Available(output.f_case.subject_character_id) &&
        Available(output.f_case.cycle_serial) &&
        Available(output.f_case.case_serial) && Available(output.f_case.state) &&
        Available(output.f_case.active) && Available(output.f_case.revision) &&
        Integer(output.f_case.owner_character_id) == request.owner_character_id &&
        Integer(output.f_case.subject_character_id) ==
            request.subject_character_id &&
        Integer(output.f_case.cycle_serial) >= 1 &&
        Integer(output.f_case.case_serial) >= 1 &&
        Integer(output.f_case.state) >= 1 &&
        Integer(output.f_case.state) <= 5 &&
        Integer(output.f_case.revision) >= 1;
    if (!case_ready) {
      const bool all_absent =
          !first[case_owner].present && !first[case_subject].present &&
          !first[case_cycle].present && !first[case_serial].present &&
          !first[case_state].present && !first[case_active].present &&
          !first[case_revision].present;
      return SetTopUnavailable(output,
                               all_absent ? "case_not_found"
                                          : "case_inconsistent");
    }
    output.readiness.case_identity_ready = true;

    DecodeInteger(first[team_status], output.team_snapshot.status);
    DecodeCharacter(environment, access, first[team_owner],
                    output.team_snapshot.owner_character_id);
    DecodeCharacter(environment, access, first[team_subject],
                    output.team_snapshot.subject_character_id);
    DecodeInteger(first[team_cycle], output.team_snapshot.cycle_serial);
    DecodeInteger(first[team_case], output.team_snapshot.case_serial);
    DecodeInteger(first[team_revision], output.team_snapshot.revision);
    DecodeInteger(first[team_source_cycle], output.team_snapshot.source_cycle);
    DecodeInteger(first[team_n], output.team_snapshot.cohort_n);
    DecodeInteger(first[team_targets], output.team_snapshot.targets);
    DecodeInteger(first[team_jingcha], output.team_snapshot.jingcha);
    DecodeInteger(first[team_calibration], output.team_snapshot.calibration);
    DecodeInteger(first[team_pip_success], output.team_snapshot.pip_success);
    DecodeInteger(first[team_appeal_overturn],
                  output.team_snapshot.appeal_overturn);
    DecodeInteger(first[team_retention], output.team_snapshot.retention);
    DecodeInteger(first[team_hc_efficiency],
                  output.team_snapshot.hc_efficiency);
    output.readiness.team_snapshot_ready =
        Available(output.team_snapshot.status) &&
        Available(output.team_snapshot.owner_character_id) &&
        Available(output.team_snapshot.subject_character_id) &&
        Available(output.team_snapshot.cycle_serial) &&
        Available(output.team_snapshot.case_serial) &&
        Available(output.team_snapshot.revision) &&
        Available(output.team_snapshot.source_cycle) &&
        Available(output.team_snapshot.cohort_n) &&
        Available(output.team_snapshot.targets) &&
        Available(output.team_snapshot.jingcha) &&
        Available(output.team_snapshot.calibration) &&
        Available(output.team_snapshot.pip_success) &&
        Available(output.team_snapshot.appeal_overturn) &&
        Available(output.team_snapshot.retention) &&
        Available(output.team_snapshot.hc_efficiency) &&
        Integer(output.team_snapshot.status) == 1 &&
        Integer(output.team_snapshot.owner_character_id) ==
            Integer(output.f_case.owner_character_id) &&
        Integer(output.team_snapshot.subject_character_id) ==
            Integer(output.f_case.subject_character_id) &&
        Integer(output.team_snapshot.cycle_serial) ==
            Integer(output.f_case.cycle_serial) &&
        Integer(output.team_snapshot.case_serial) ==
            Integer(output.f_case.case_serial) &&
        Integer(output.team_snapshot.revision) >= 1 &&
        Integer(output.team_snapshot.source_cycle) <
            Integer(output.f_case.cycle_serial) &&
        Integer(output.team_snapshot.cohort_n) >= 0;

    DecodeReceipt(environment, access, first, f035_receipt_owner,
                  output.f035_receipt);
    output.readiness.f035_receipt_ready =
        ReceiptMatches(output.f035_receipt, output.f_case);
    if (!output.readiness.f035_receipt_ready) {
      SetReceiptUnavailable(output.f035_receipt, "receipt_not_recorded");
      SetDistributionSnapshotUnavailable(output.distribution_snapshot,
                                         "lifecycle_not_reached");
      SetNextPolicyUnavailable(output.next_cycle_policy,
                               "lifecycle_not_reached");
      SetEffectiveUnavailable(output.effective_distribution,
                              "lifecycle_not_reached");
    } else if (Integer(output.f035_receipt.choice) == 3) {
      SetDistributionSnapshotUnavailable(output.distribution_snapshot,
                                         "not_applicable");
      SetNextPolicyUnavailable(output.next_cycle_policy, "not_applicable");
      SetEffectiveUnavailable(output.effective_distribution,
                              "not_applicable");
      output.readiness.distribution_lifecycle_ready = true;
    } else {
      DecodeBoolean(first[distribution_available],
                    output.distribution_snapshot.available);
      DecodeInteger(first[distribution_mode],
                    output.distribution_snapshot.mode);
      DecodeInteger(first[distribution_rule_source],
                    output.distribution_snapshot.rule_source);
      DecodeInteger(first[distribution_top],
                    output.distribution_snapshot.top_slots);
      DecodeInteger(first[distribution_middle],
                    output.distribution_snapshot.middle_slots);
      DecodeInteger(first[distribution_bottom],
                    output.distribution_snapshot.bottom_slots);
      DecodeInteger(first[distribution_conserved],
                    output.distribution_snapshot.conserved_slots);
      const auto n = Integer(output.team_snapshot.cohort_n);
      const auto mode = Integer(output.distribution_snapshot.mode);
      const auto top = Integer(output.distribution_snapshot.top_slots);
      const auto middle = Integer(output.distribution_snapshot.middle_slots);
      const auto bottom = Integer(output.distribution_snapshot.bottom_slots);
      const auto conserved =
          Integer(output.distribution_snapshot.conserved_slots);
      output.readiness.distribution_snapshot_ready =
          output.readiness.team_snapshot_ready &&
          Available(output.distribution_snapshot.available) &&
          *output.distribution_snapshot.available.value &&
          Available(output.distribution_snapshot.mode) && mode >= 1 &&
          mode <= 3 && Available(output.distribution_snapshot.rule_source) &&
          Integer(output.distribution_snapshot.rule_source) >= 1 &&
          Integer(output.distribution_snapshot.rule_source) <= 3 &&
          Available(output.distribution_snapshot.top_slots) && top >= 0 &&
          Available(output.distribution_snapshot.middle_slots) && middle >= 0 &&
          Available(output.distribution_snapshot.bottom_slots) && bottom >= 0 &&
          Available(output.distribution_snapshot.conserved_slots) &&
          conserved >= 0 && top == n * 30 / 100 &&
          bottom == ExpectedBottomSlots(n, mode);
      output.readiness.distribution_conservation_ready =
          output.readiness.distribution_snapshot_ready &&
          top + middle + bottom == conserved && conserved == n;

      DecodeInteger(first[policy_status], output.next_cycle_policy.status);
      DecodeCharacter(environment, access, first[policy_owner],
                      output.next_cycle_policy.owner_character_id);
      DecodeCharacter(environment, access, first[policy_subject],
                      output.next_cycle_policy.subject_character_id);
      DecodeCharacter(environment, access, first[policy_source_reviewer],
                      output.next_cycle_policy.source_reviewer_character_id);
      DecodeInteger(first[policy_source_cycle],
                    output.next_cycle_policy.source_cycle);
      DecodeInteger(first[policy_source_case],
                    output.next_cycle_policy.source_case);
      DecodeInteger(first[policy_source_revision],
                    output.next_cycle_policy.source_revision);
      DecodeInteger(first[policy_input_revision],
                    output.next_cycle_policy.input_revision);
      DecodeInteger(first[policy_mode], output.next_cycle_policy.mode);
      DecodeInteger(first[policy_rule_source],
                    output.next_cycle_policy.rule_source);
      DecodeInteger(first[policy_due_cycle],
                    output.next_cycle_policy.due_cycle);
      output.readiness.next_cycle_policy_ready =
          Available(output.next_cycle_policy.status) &&
          (Integer(output.next_cycle_policy.status) == 1 ||
           Integer(output.next_cycle_policy.status) == 2) &&
          Available(output.next_cycle_policy.owner_character_id) &&
          Available(output.next_cycle_policy.subject_character_id) &&
          Available(output.next_cycle_policy.source_reviewer_character_id) &&
          Available(output.next_cycle_policy.source_cycle) &&
          Available(output.next_cycle_policy.source_case) &&
          Available(output.next_cycle_policy.source_revision) &&
          Available(output.next_cycle_policy.input_revision) &&
          Available(output.next_cycle_policy.mode) &&
          Available(output.next_cycle_policy.rule_source) &&
          Available(output.next_cycle_policy.due_cycle) &&
          Integer(output.next_cycle_policy.owner_character_id) ==
              request.subject_character_id &&
          Integer(output.next_cycle_policy.subject_character_id) ==
              request.subject_character_id &&
          Integer(output.next_cycle_policy.source_reviewer_character_id) ==
              request.owner_character_id &&
          Integer(output.next_cycle_policy.source_cycle) ==
              Integer(output.f_case.cycle_serial) &&
          Integer(output.next_cycle_policy.source_case) ==
              Integer(output.f_case.case_serial) &&
          Integer(output.next_cycle_policy.source_revision) >= 1 &&
          Integer(output.next_cycle_policy.input_revision) ==
              Integer(output.team_snapshot.revision) &&
          Integer(output.next_cycle_policy.mode) == mode &&
          Integer(output.next_cycle_policy.rule_source) ==
              Integer(output.distribution_snapshot.rule_source) &&
          Integer(output.next_cycle_policy.due_cycle) ==
              Integer(output.f_case.cycle_serial) + 1;

      if (output.readiness.next_cycle_policy_ready &&
          Integer(output.next_cycle_policy.status) == 2) {
        DecodeInteger(first[effective_mode],
                      output.effective_distribution.mode);
        DecodeInteger(first[effective_cycle],
                      output.effective_distribution.cycle);
        DecodeInteger(first[effective_source_cycle],
                      output.effective_distribution.source_cycle);
        DecodeInteger(first[effective_source_case],
                      output.effective_distribution.source_case);
        DecodeInteger(first[effective_input_revision],
                      output.effective_distribution.input_revision);
        DecodeInteger(first[policy_settled_cycle],
                      output.effective_distribution.settled_cycle);
        DecodeInteger(first[policy_settlement_receipt],
                      output.effective_distribution.settlement_receipt);
        DecodeInteger(first[actual_cohort_n],
                      output.effective_distribution.actual_cohort_n);
        DecodeInteger(first[actual_bottom_slots],
                      output.effective_distribution.actual_bottom_slots);
        output.readiness.effective_distribution_ready =
            Available(output.effective_distribution.mode) &&
            Available(output.effective_distribution.cycle) &&
            Available(output.effective_distribution.source_cycle) &&
            Available(output.effective_distribution.source_case) &&
            Available(output.effective_distribution.input_revision) &&
            Integer(output.effective_distribution.mode) == mode &&
            Integer(output.effective_distribution.cycle) >=
                Integer(output.next_cycle_policy.due_cycle) &&
            Integer(output.effective_distribution.source_cycle) ==
                Integer(output.next_cycle_policy.source_cycle) &&
            Integer(output.effective_distribution.source_case) ==
                Integer(output.next_cycle_policy.source_case) &&
            Integer(output.effective_distribution.input_revision) ==
                Integer(output.next_cycle_policy.input_revision);
        output.readiness.distribution_settlement_ready =
            output.readiness.effective_distribution_ready &&
            Available(output.effective_distribution.settled_cycle) &&
            Available(output.effective_distribution.settlement_receipt) &&
            Integer(output.effective_distribution.settled_cycle) ==
                Integer(output.effective_distribution.cycle) &&
            Integer(output.effective_distribution.settlement_receipt) ==
                Integer(output.next_cycle_policy.source_case);
        output.readiness.actual_bottom_slots_ready =
            output.readiness.effective_distribution_ready &&
            Available(output.effective_distribution.actual_cohort_n) &&
            Available(output.effective_distribution.actual_bottom_slots) &&
            Integer(output.effective_distribution.actual_cohort_n) >= 0 &&
            Integer(output.effective_distribution.actual_bottom_slots) ==
                ExpectedBottomSlots(
                    Integer(output.effective_distribution.actual_cohort_n),
                    mode);
      } else {
        SetEffectiveUnavailable(output.effective_distribution,
                                "lifecycle_not_reached");
      }
      output.readiness.distribution_lifecycle_ready =
          output.readiness.distribution_snapshot_ready &&
          output.readiness.distribution_conservation_ready &&
          output.readiness.next_cycle_policy_ready &&
          (Integer(output.next_cycle_policy.status) == 1 ||
           (Integer(output.next_cycle_policy.status) == 2 &&
            output.readiness.effective_distribution_ready &&
            output.readiness.distribution_settlement_ready &&
            output.readiness.actual_bottom_slots_ready));
    }

    DecodeReceipt(environment, access, first, f032_receipt_owner,
                  output.f032_receipt);
    output.readiness.f032_receipt_ready =
        ReceiptMatches(output.f032_receipt, output.f_case);
    if (!output.readiness.f032_receipt_ready) {
      SetReceiptUnavailable(output.f032_receipt, "receipt_not_recorded");
      SetUnavailable(output.manager_score.sum, "lifecycle_not_reached");
      SetUnavailable(output.manager_score.mode, "lifecycle_not_reached");
      SetComponentUnavailable(output.component8, "lifecycle_not_reached");
    } else if (Integer(output.f032_receipt.choice) == 3) {
      SetUnavailable(output.manager_score.sum, "not_applicable");
      SetUnavailable(output.manager_score.mode, "not_applicable");
      SetComponentUnavailable(output.component8, "not_applicable");
      output.readiness.component8_lifecycle_ready = true;
    } else {
      DecodeInteger(first[manager_score], output.manager_score.sum);
      DecodeInteger(first[manager_score_mode], output.manager_score.mode);
      output.readiness.manager_score_ready =
          Available(output.manager_score.sum) &&
          Available(output.manager_score.mode) &&
          Integer(output.manager_score.mode) ==
              Integer(output.f032_receipt.choice);

      DecodeInteger(first[component_status], output.component8.status);
      DecodeCharacter(environment, access, first[component_owner],
                      output.component8.owner_character_id);
      DecodeCharacter(environment, access, first[component_subject],
                      output.component8.subject_character_id);
      DecodeInteger(first[component_source_cycle],
                    output.component8.source_cycle);
      DecodeInteger(first[component_source_case],
                    output.component8.source_case);
      DecodeInteger(first[component_source_revision],
                    output.component8.source_revision);
      DecodeInteger(first[component_input_revision],
                    output.component8.input_revision);
      DecodeInteger(first[component_number], output.component8.component);
      DecodeInteger(first[component_value], output.component8.value);
      DecodeInteger(first[component_due_cycle], output.component8.due_cycle);
      output.readiness.component8_token_ready =
          output.readiness.manager_score_ready &&
          Available(output.component8.status) &&
          (Integer(output.component8.status) == 1 ||
           Integer(output.component8.status) == 2) &&
          Available(output.component8.owner_character_id) &&
          Available(output.component8.subject_character_id) &&
          Available(output.component8.source_cycle) &&
          Available(output.component8.source_case) &&
          Available(output.component8.source_revision) &&
          Available(output.component8.input_revision) &&
          Available(output.component8.component) &&
          Available(output.component8.value) &&
          Available(output.component8.due_cycle) &&
          Integer(output.component8.owner_character_id) ==
              request.owner_character_id &&
          Integer(output.component8.subject_character_id) ==
              request.subject_character_id &&
          Integer(output.component8.source_cycle) ==
              Integer(output.f_case.cycle_serial) &&
          Integer(output.component8.source_case) ==
              Integer(output.f_case.case_serial) &&
          Integer(output.component8.source_revision) >= 1 &&
          Integer(output.component8.input_revision) ==
              Integer(output.team_snapshot.revision) &&
          Integer(output.component8.component) == 8 &&
          Integer(output.component8.value) ==
              Integer(output.manager_score.sum) &&
          Integer(output.component8.due_cycle) ==
              Integer(output.component8.source_cycle) + 1;
      if (output.readiness.component8_token_ready &&
          Integer(output.component8.status) == 2) {
        DecodeCharacter(environment, access, first[component_settled_by],
                        output.component8.settled_by_owner_character_id);
        DecodeInteger(first[component_settled_cycle],
                      output.component8.settled_cycle);
        DecodeInteger(first[component_settled_value],
                      output.component8.settled_value);
        DecodeInteger(first[component_settlement_receipt],
                      output.component8.settlement_receipt);
        output.readiness.component8_settlement_ready =
            Available(output.component8.settled_by_owner_character_id) &&
            Available(output.component8.settled_cycle) &&
            Available(output.component8.settled_value) &&
            Available(output.component8.settlement_receipt) &&
            Integer(output.component8.settled_cycle) >=
                Integer(output.component8.due_cycle) &&
            Integer(output.component8.settled_value) ==
                Integer(output.component8.value) &&
            Integer(output.component8.settlement_receipt) ==
                Integer(output.component8.source_case);
      } else {
        SetUnavailable(output.component8.settled_by_owner_character_id,
                       "lifecycle_not_reached");
        SetUnavailable(output.component8.settled_cycle,
                       "lifecycle_not_reached");
        SetUnavailable(output.component8.settled_value,
                       "lifecycle_not_reached");
        SetUnavailable(output.component8.settlement_receipt,
                       "lifecycle_not_reached");
      }
      output.readiness.component8_lifecycle_ready =
          output.readiness.component8_token_ready &&
          (Integer(output.component8.status) == 1 ||
           (Integer(output.component8.status) == 2 &&
            output.readiness.component8_settlement_ready));
    }

    output.status = game::ZhongguoManagerGovernanceSnapshotStatusV1::available;
    output.unavailable_reason.clear();
    output.readiness.ready =
        output.readiness.subject_binding_ready &&
        output.readiness.case_identity_ready &&
        output.readiness.team_snapshot_ready &&
        output.readiness.f035_receipt_ready &&
        output.readiness.distribution_lifecycle_ready &&
        output.readiness.f032_receipt_ready &&
        output.readiness.component8_lifecycle_ready &&
        output.readiness.same_frame_ready;
    return game::ReadZhongguoManagerGovernanceSnapshotResultV1::available;
  } catch (...) {
    return SetTopUnavailable(output, "internal_error");
  }
}

} // namespace xar::ck3_11906
