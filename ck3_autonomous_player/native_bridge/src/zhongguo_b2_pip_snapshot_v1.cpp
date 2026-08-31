#include "xar_bridge/zhongguo_b2_pip_snapshot_v1.hpp"

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

enum SubjectVariableIndex : std::size_t {
  gate_owner = 0,
  gate_subject,
  gate_cycle,
  gate_case,
  gate_threshold,
  gate_component_count,
  gate_evidence_complete,
  gate_status,
  result_case_serial,
  result_grade,
  result_absolute_grade,
  result_kpi_frozen,
  evidence_governance,
  evidence_capability,
  evidence_growth,
  evidence_superior,
  evidence_values,
  evidence_collaboration,
  evidence_jingcha,
  evidence_organization,
  pip_owner,
  pip_subject,
  pip_cycle,
  pip_case,
  pip_state,
  pip_task_kind,
  pip_task_controllable,
  pip_policy_route,
  m015_receipt_serial,
  pip_subject_response,
  pip_subject_response_case,
  pip_subject_response_author,
  pip_goal_revision_used,
  pip_refusal_receipt,
  support_reserved,
  support_absent,
  support_hours,
  support_attention,
  support_mentor,
  support_budget_owner,
  support_budget_allocated,
  support_budget_spent,
  m016_receipt_serial,
  support_released,
  support_withheld,
  support_atomic_shortfall,
  result_treasury_paid,
  result_gold_paid,
  midpoint_receipt,
  midpoint_resource_delivery_valid,
  midpoint_progress_status,
  midpoint_progress_red_code,
  midpoint_state,
  outcome_code,
  settlement_receipt,
  outcome_result_cycle,
  outcome_result_case,
  outcome_result_grade,
  stability_days_observed,
  independent_review_status,
  independent_review_red_code,
  graduation_receipt,
  failure_receipt,
  no_support_liability,
  performance_evidence_status,
  performance_evidence_owner,
  performance_evidence_subject,
  performance_evidence_source_cycle,
  performance_evidence_source_case,
  performance_evidence_due_cycle,
  performance_evidence_delta,
  performance_evidence_consumed_cycle,
  performance_evidence_consumed_case,
};

static_assert(performance_evidence_consumed_case + 1 ==
              kZhongguoB2PipSubjectVariableAllowlist.size());

using SubjectRows =
    std::array<ZhongguoB2PipRawVariableV1,
               kZhongguoB2PipSubjectVariableAllowlist.size()>;
using OwnerRows =
    std::array<ZhongguoB2PipRawVariableV1,
               kZhongguoB2PipOwnerVariableAllowlist.size()>;

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

bool ReadBytes(const ZhongguoB2PipAccessV1 &access, const void *address,
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
bool ReadValue(const ZhongguoB2PipAccessV1 &access, const void *base,
               std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const ZhongguoB2PipNativeEnvironmentV1 &environment) noexcept {
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
    const ZhongguoB2PipNativeEnvironmentV1 &environment,
    const ZhongguoB2PipAccessV1 &access,
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
    const ZhongguoB2PipNativeEnvironmentV1 &environment,
    const ZhongguoB2PipAccessV1 &access,
    std::int32_t character_id) noexcept {
  return environment.offline_fixture_function_overrides
             ? access.validate_character != nullptr &&
                   access.validate_character(access.context, character_id)
             : ResolveCharacterNative(environment, access, character_id);
}

bool ResolveVariableIdentifier(
    const ZhongguoB2PipNativeEnvironmentV1 &environment,
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

bool FindVariableValue(const ZhongguoB2PipAccessV1 &access, void *context,
                       std::int32_t identifier,
                       ZhongguoB2PipRawVariableV1 &output) noexcept {
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

bool ReadFixedVariableNative(
    const ZhongguoB2PipNativeEnvironmentV1 &environment,
    const ZhongguoB2PipAccessV1 &access, std::int32_t character_id,
    std::string_view key, ZhongguoB2PipRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) return false;
  const ZhongguoEventTarget16V1 target{4, {}, character_id};
  void *const context = environment.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

template <std::size_t Size>
bool ReadFixedRows(
    const ZhongguoB2PipNativeEnvironmentV1 &environment,
    const ZhongguoB2PipAccessV1 &access, std::int32_t character_id,
    const std::array<std::string_view, Size> &allowlist,
    std::array<ZhongguoB2PipRawVariableV1, Size> &output) noexcept {
  for (std::size_t index = 0; index < Size; ++index) {
    const bool read = environment.offline_fixture_function_overrides
                          ? access.read_allowlisted_variable != nullptr &&
                                access.read_allowlisted_variable(
                                    access.context, character_id,
                                    allowlist[index], output[index])
                          : ReadFixedVariableNative(environment, access,
                                                    character_id,
                                                    allowlist[index],
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

void DecodeInteger(const ZhongguoB2PipRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1 || raw.payload % kFixedScale != 0) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload / kFixedScale);
  }
}

void DecodeQ100000(const ZhongguoB2PipRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload);
  }
}

void DecodeBoolean(const ZhongguoB2PipRawVariableV1 &raw,
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
    const ZhongguoB2PipNativeEnvironmentV1 &environment,
    const ZhongguoB2PipAccessV1 &access,
    const ZhongguoB2PipRawVariableV1 &raw,
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

template <typename... Fields>
void UnavailableMany(std::string_view reason, Fields &...fields) {
  (SetUnavailable(fields, reason), ...);
}

void MakeAllFieldsUnavailable(game::ZhongguoB2PipSnapshotV1 &output,
                              std::string_view reason) {
  auto &g = output.gate;
  UnavailableMany(reason, g.owner_character_id, g.subject_character_id,
                  g.cycle_serial, g.case_serial, g.threshold,
                  g.negative_component_count, g.evidence_complete, g.status,
                  g.result_case_serial, g.result_grade, g.absolute_grade,
                  g.kpi_frozen_q100000, g.governance_q100000,
                  g.capability_q100000, g.growth_q100000,
                  g.superior_q100000, g.values_q100000,
                  g.collaboration_q100000, g.jingcha_q100000,
                  g.organization_q100000);
  auto &p = output.pip;
  UnavailableMany(reason, p.owner_character_id, p.subject_character_id,
                  p.cycle_serial, p.case_serial, p.state, p.task_kind,
                  p.task_controllable, p.policy_route);
  auto &r = output.response;
  UnavailableMany(reason, r.subject_response, r.response_case_serial,
                  r.response_author_character_id,
                  r.acknowledgement_receipt_serial, r.goal_revision_used,
                  r.refusal_receipt_serial);
  auto &s = output.support;
  UnavailableMany(reason, s.capacity_reserved, s.owner_capacity_used,
                  s.support_absent, s.hours, s.attention_units,
                  s.mentor_character_id, s.budget_owner_character_id,
                  s.treasury_budget_allocated, s.treasury_budget_spent,
                  s.support_receipt_serial, s.released, s.withheld,
                  s.atomic_shortfall);
  auto &b = output.budget_ledger;
  UnavailableMany(reason, b.result_case_serial, b.treasury_penalty_paid,
                  b.personal_gold_penalty_paid,
                  b.support_treasury_allocated,
                  b.support_treasury_spent);
  auto unset_ticket = [reason](game::ZhongguoB2PipTicketV1 &ticket) {
    UnavailableMany(reason, ticket.owner_character_id,
                    ticket.subject_character_id, ticket.cycle_serial,
                    ticket.case_serial, ticket.expected_state,
                    ticket.due_date_raw);
  };
  unset_ticket(output.d180_ticket);
  unset_ticket(output.d365_ticket);
  auto &m = output.midpoint;
  UnavailableMany(reason, m.receipt_serial, m.resource_delivery_valid,
                  m.progress_status, m.progress_red_code, m.state);
  auto &o = output.outcome;
  UnavailableMany(reason, o.code, o.settlement_receipt_serial,
                  o.result_cycle_serial, o.result_case_serial, o.result_grade,
                  o.stability_days_observed, o.independent_review_status,
                  o.independent_review_red_code,
                  o.graduation_receipt_serial, o.failure_receipt_serial,
                  o.no_support_liability);
  auto &e = output.next_cycle_evidence;
  UnavailableMany(reason, e.status, e.owner_character_id,
                  e.subject_character_id, e.source_cycle_serial,
                  e.source_case_serial, e.due_cycle_serial, e.delta,
                  e.consumed_cycle_serial, e.consumed_case_serial);
  SetUnavailable(output.pip_modifier_present, reason);
}

void InitializeEnvelope(const ZhongguoB2PipSnapshotRequestV1 &request,
                        const ZhongguoB2PipFrameV1 *frame,
                        game::ZhongguoB2PipSnapshotV1 &output) {
  output = {};
  output.case_kind = kZhongguoB2PipSnapshotV1CaseKind;
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

void SetTopUnavailable(game::ZhongguoB2PipSnapshotV1 &output,
                       std::string_view reason,
                       bool same_frame_ready = false) {
  output.status = game::ZhongguoB2PipSnapshotStatusV1::unavailable;
  MakeAllFieldsUnavailable(output, "case_unavailable");
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
        (index == 0 && !alpha && !digit)) return false;
  }
  return true;
}

bool ValidRequest(const ZhongguoB2PipSnapshotRequestV1 &request) noexcept {
  return request.expected_snapshot_revision > 0 &&
         request.owner_character_id > 0 && ValidNonce(request.request_nonce);
}

bool AnyProviderIdentity(const SubjectRows &rows) noexcept {
  return rows[gate_owner].present || rows[gate_status].present ||
         rows[pip_owner].present || rows[pip_state].present;
}

bool RawCharacterId(const ZhongguoB2PipRawVariableV1 &raw,
                    std::int32_t &output) noexcept {
  if (!raw.present || raw.kind != 4 || raw.payload <= 0 ||
      raw.payload > std::numeric_limits<std::int32_t>::max()) {
    return false;
  }
  output = static_cast<std::int32_t>(raw.payload);
  return true;
}

bool BoundOwnerFromRows(
    const ZhongguoB2PipNativeEnvironmentV1 &environment,
    const ZhongguoB2PipAccessV1 &access, const SubjectRows &rows,
    std::int32_t requested_owner, std::int32_t &actual_owner) noexcept {
  std::int32_t gate_id = -1;
  std::int32_t pip_id = -1;
  const bool has_gate = RawCharacterId(rows[gate_owner], gate_id);
  const bool has_pip = RawCharacterId(rows[pip_owner], pip_id);
  if ((!has_gate && !has_pip) || (has_gate && has_pip && gate_id != pip_id)) {
    return false;
  }
  actual_owner = has_pip ? pip_id : gate_id;
  return actual_owner == requested_owner &&
         ValidateCharacter(environment, access, actual_owner);
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

bool BooleanValue(const game::ZhongguoTypedBooleanV1 &field,
                  bool &output) noexcept {
  if (!field.available || !field.value.has_value()) return false;
  output = *field.value;
  return true;
}

bool OptionalAbsent(const game::ZhongguoTypedIntegerV1 &field) noexcept {
  return !field.available && field.unavailable_reason == "variable_absent";
}

bool BooleanFalseOrAbsent(
    const game::ZhongguoTypedBooleanV1 &field) noexcept {
  return (!field.available && field.unavailable_reason == "variable_absent") ||
         (field.available && field.value.has_value() && !*field.value);
}

bool BooleanEquals(const game::ZhongguoTypedBooleanV1 &field,
                   bool expected) noexcept {
  return field.available && field.value.has_value() &&
         *field.value == expected;
}

void MarkGateEvidenceBindingMismatch(game::ZhongguoB2PipGateV1 &gate) {
  UnavailableMany("case_binding_mismatch", gate.result_grade,
                  gate.absolute_grade, gate.kpi_frozen_q100000,
                  gate.governance_q100000, gate.capability_q100000,
                  gate.growth_q100000, gate.superior_q100000,
                  gate.values_q100000, gate.collaboration_q100000,
                  gate.jingcha_q100000, gate.organization_q100000);
}

void MarkBudgetBindingMismatch(game::ZhongguoB2PipBudgetLedgerV1 &ledger) {
  UnavailableMany("case_binding_mismatch", ledger.treasury_penalty_paid,
                  ledger.personal_gold_penalty_paid);
}

void MarkUnobservableTickets(game::ZhongguoB2PipSnapshotV1 &output) {
  auto mark = [](game::ZhongguoB2PipTicketV1 &ticket) {
    UnavailableMany("native_observation_unavailable",
                    ticket.owner_character_id, ticket.subject_character_id,
                    ticket.cycle_serial, ticket.case_serial,
                    ticket.expected_state);
    SetUnavailable(ticket.due_date_raw, "product_not_persisted");
  };
  mark(output.d180_ticket);
  mark(output.d365_ticket);
  SetUnavailable(output.pip_modifier_present,
                 "native_observation_unavailable");
}

bool ComponentGate(const game::ZhongguoB2PipReadinessV1 &readiness) {
  return readiness.player_subject_binding_ready &&
         readiness.owner_binding_ready && readiness.gate_ready &&
         readiness.same_frame_ready;
}

} // namespace

ZhongguoB2PipNativeEnvironmentV1 BindZhongguoB2PipNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base,
                                             exact_build_admitted);
}

game::ReadZhongguoB2PipSnapshotResultV1 ReadZhongguoB2PipSnapshotV1(
    const ZhongguoB2PipNativeEnvironmentV1 &environment,
    const ZhongguoB2PipAccessV1 &access,
    const ZhongguoB2PipSnapshotRequestV1 &request,
    game::ZhongguoB2PipSnapshotV1 &output) noexcept {
  try {
    InitializeEnvelope(request, nullptr, output);
    if (!ValidRequest(request) || !EnvironmentIsExact(environment)) {
      SetTopUnavailable(output, "unsupported_build");
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetTopUnavailable(output, "requires_application_main");
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    if (environment.offline_fixture_function_overrides &&
        (access.validate_character == nullptr ||
         access.read_allowlisted_variable == nullptr)) {
      SetTopUnavailable(output, "internal_error");
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }

    ZhongguoB2PipFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    InitializeEnvelope(request, &before, output);
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    if (!before.paused) {
      SetTopUnavailable(output, "requires_paused");
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0 ||
        !ValidateCharacter(environment, access,
                           before.played_character_id)) {
      SetTopUnavailable(output, "map_not_ready");
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }

    SubjectRows first{};
    SubjectRows second{};
    if (!ReadFixedRows(environment, access, before.played_character_id,
                       kZhongguoB2PipSubjectVariableAllowlist, first)) {
      SetTopUnavailable(output, "variable_identifier_unavailable");
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    if (!AnyProviderIdentity(first)) {
      SetTopUnavailable(output, "case_not_found", true);
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    std::int32_t actual_owner = -1;
    if (!BoundOwnerFromRows(environment, access, first,
                            request.owner_character_id, actual_owner)) {
      SetTopUnavailable(output, "owner_filter_mismatch", true);
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    if (actual_owner == before.played_character_id) {
      SetTopUnavailable(output, "not_received_self", true);
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    OwnerRows owner_first{};
    OwnerRows owner_second{};
    if (!ReadFixedRows(environment, access, actual_owner,
                       kZhongguoB2PipOwnerVariableAllowlist, owner_first) ||
        !ReadFixedRows(environment, access, before.played_character_id,
                       kZhongguoB2PipSubjectVariableAllowlist, second) ||
        !ReadFixedRows(environment, access, actual_owner,
                       kZhongguoB2PipOwnerVariableAllowlist, owner_second)) {
      SetTopUnavailable(output, "variable_context_unavailable");
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    ZhongguoB2PipFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first != second || owner_first != owner_second) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }
    output.readiness.same_frame_ready = true;

    auto &g = output.gate;
    DecodeCharacter(environment, access, first[gate_owner],
                    g.owner_character_id);
    DecodeCharacter(environment, access, first[gate_subject],
                    g.subject_character_id);
    DecodeInteger(first[gate_cycle], g.cycle_serial);
    DecodeInteger(first[gate_case], g.case_serial);
    DecodeInteger(first[gate_threshold], g.threshold);
    DecodeInteger(first[gate_component_count], g.negative_component_count);
    DecodeBoolean(first[gate_evidence_complete], g.evidence_complete);
    DecodeInteger(first[gate_status], g.status);
    DecodeInteger(first[result_case_serial], g.result_case_serial);
    DecodeInteger(first[result_grade], g.result_grade);
    DecodeInteger(first[result_absolute_grade], g.absolute_grade);
    DecodeQ100000(first[result_kpi_frozen], g.kpi_frozen_q100000);
    DecodeQ100000(first[evidence_governance], g.governance_q100000);
    DecodeQ100000(first[evidence_capability], g.capability_q100000);
    DecodeQ100000(first[evidence_growth], g.growth_q100000);
    DecodeQ100000(first[evidence_superior], g.superior_q100000);
    DecodeQ100000(first[evidence_values], g.values_q100000);
    DecodeQ100000(first[evidence_collaboration],
                  g.collaboration_q100000);
    DecodeQ100000(first[evidence_jingcha], g.jingcha_q100000);
    DecodeQ100000(first[evidence_organization], g.organization_q100000);

    bool gate_complete = false;
    output.readiness.gate_ready =
        IntegerEquals(g.owner_character_id, actual_owner) &&
        IntegerEquals(g.subject_character_id, before.played_character_id) &&
        IntegerInRange(g.cycle_serial, 1,
                       std::numeric_limits<std::int64_t>::max()) &&
        IntegerInRange(g.case_serial, 1, 999'999) &&
        IntegerEquals(g.threshold, 3) &&
        IntegerInRange(g.negative_component_count, 0, 10) &&
        BooleanValue(g.evidence_complete, gate_complete) &&
        IntegerInRange(g.status, 0, 3) &&
        ((gate_complete && *g.status.value != 0) ||
         (!gate_complete && *g.status.value == 0));

    if (g.result_case_serial.available && g.case_serial.available &&
        *g.result_case_serial.value != *g.case_serial.value) {
      MarkGateEvidenceBindingMismatch(g);
    }
    const std::array<const game::ZhongguoTypedIntegerV1 *, 8> evidence{
        &g.governance_q100000, &g.capability_q100000,
        &g.growth_q100000, &g.superior_q100000, &g.values_q100000,
        &g.collaboration_q100000, &g.jingcha_q100000,
        &g.organization_q100000};
    bool all_evidence = g.result_case_serial.available &&
                        g.result_grade.available && g.absolute_grade.available &&
                        g.kpi_frozen_q100000.available;
    std::int64_t computed_negative = 0;
    if (all_evidence) {
      computed_negative += *g.absolute_grade.value == 1 ? 1 : 0;
      computed_negative += *g.kpi_frozen_q100000.value < 0 ? 1 : 0;
      for (const auto *field : evidence) {
        if (!field->available) {
          all_evidence = false;
          break;
        }
        computed_negative += *field->value < 0 ? 1 : 0;
      }
    }
    output.readiness.gate_evidence_ready =
        output.readiness.gate_ready && gate_complete && all_evidence &&
        IntegerEquals(g.result_case_serial, *g.case_serial.value) &&
        IntegerInRange(g.result_grade, 1, 3) &&
        IntegerInRange(g.absolute_grade, 1, 3) &&
        computed_negative == *g.negative_component_count.value;

    auto &p = output.pip;
    DecodeCharacter(environment, access, first[pip_owner],
                    p.owner_character_id);
    DecodeCharacter(environment, access, first[pip_subject],
                    p.subject_character_id);
    DecodeInteger(first[pip_cycle], p.cycle_serial);
    DecodeInteger(first[pip_case], p.case_serial);
    DecodeInteger(first[pip_state], p.state);
    DecodeInteger(first[pip_task_kind], p.task_kind);
    DecodeBoolean(first[pip_task_controllable], p.task_controllable);
    DecodeInteger(first[pip_policy_route], p.policy_route);
    const bool any_pip =
        first[pip_owner].present || first[pip_subject].present ||
        first[pip_cycle].present || first[pip_case].present ||
        first[pip_state].present || first[pip_task_kind].present ||
        first[pip_task_controllable].present ||
        first[pip_policy_route].present;
    output.readiness.pip_identity_ready =
        any_pip && output.readiness.gate_ready &&
        IntegerEquals(p.owner_character_id, actual_owner) &&
        IntegerEquals(p.subject_character_id, before.played_character_id) &&
        IntegerInRange(p.cycle_serial, 1,
                       std::numeric_limits<std::int64_t>::max() - 1) &&
        IntegerInRange(p.case_serial, 1, 999'999) &&
        IntegerEquals(p.cycle_serial, *g.cycle_serial.value) &&
        IntegerEquals(p.case_serial, *g.case_serial.value) &&
        IntegerInRange(p.state, 1, 5) && IntegerInRange(p.task_kind, 1, 3) &&
        p.task_controllable.available &&
        IntegerInRange(p.policy_route, 1, 2);
    if (any_pip && !output.readiness.pip_identity_ready) {
      SetTopUnavailable(output, "case_inconsistent", true);
      return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
    }

    output.readiness.player_subject_binding_ready =
        IntegerEquals(g.subject_character_id, before.played_character_id) &&
        (!any_pip || IntegerEquals(p.subject_character_id,
                                   before.played_character_id));
    output.readiness.owner_binding_ready =
        IntegerEquals(g.owner_character_id, actual_owner) &&
        (!any_pip || IntegerEquals(p.owner_character_id, actual_owner));

    auto &r = output.response;
    DecodeInteger(first[pip_subject_response], r.subject_response);
    DecodeInteger(first[pip_subject_response_case], r.response_case_serial);
    DecodeCharacter(environment, access, first[pip_subject_response_author],
                    r.response_author_character_id);
    DecodeInteger(first[m015_receipt_serial],
                  r.acknowledgement_receipt_serial);
    DecodeBoolean(first[pip_goal_revision_used], r.goal_revision_used);
    DecodeInteger(first[pip_refusal_receipt], r.refusal_receipt_serial);
    if (output.readiness.pip_identity_ready) {
      const auto state = *p.state.value;
      const auto response = r.subject_response.available
                                ? *r.subject_response.value
                                : -1;
      const auto case_id = *p.case_serial.value;
      const bool pending =
          state == 1 && response == 0 &&
          IntegerEquals(r.response_case_serial, 0) &&
          OptionalAbsent(r.response_author_character_id) &&
          IntegerEquals(r.refusal_receipt_serial, 0);
      const bool accepted =
          (state == 2 || state == 3 || state == 4) &&
          (response == 1 || response == 2) &&
          IntegerEquals(r.response_case_serial, case_id) &&
          IntegerEquals(r.response_author_character_id,
                        before.played_character_id) &&
          IntegerEquals(r.refusal_receipt_serial, 0);
      const bool refused =
          state == 5 && response == 3 &&
          IntegerEquals(r.response_case_serial, case_id) &&
          IntegerEquals(r.response_author_character_id,
                        before.played_character_id) &&
          IntegerEquals(r.refusal_receipt_serial, case_id);
      output.readiness.response_ready =
          IntegerEquals(r.acknowledgement_receipt_serial, case_id) &&
          r.goal_revision_used.available && (pending || accepted || refused);
    }

    auto &s = output.support;
    DecodeBoolean(first[support_reserved], s.capacity_reserved);
    DecodeInteger(owner_first[0], s.owner_capacity_used);
    DecodeBoolean(first[support_absent], s.support_absent);
    DecodeInteger(first[support_hours], s.hours);
    DecodeInteger(first[support_attention], s.attention_units);
    DecodeCharacter(environment, access, first[support_mentor],
                    s.mentor_character_id);
    DecodeCharacter(environment, access, first[support_budget_owner],
                    s.budget_owner_character_id);
    DecodeInteger(first[support_budget_allocated],
                  s.treasury_budget_allocated);
    DecodeInteger(first[support_budget_spent], s.treasury_budget_spent);
    DecodeInteger(first[m016_receipt_serial], s.support_receipt_serial);
    DecodeBoolean(first[support_released], s.released);
    DecodeBoolean(first[support_withheld], s.withheld);
    DecodeBoolean(first[support_atomic_shortfall], s.atomic_shortfall);
    if (output.readiness.pip_identity_ready) {
      bool reserved = false;
      bool absent = false;
      const bool core_support =
          BooleanValue(s.capacity_reserved, reserved) &&
          BooleanValue(s.support_absent, absent) &&
          IntegerInRange(s.hours, 0, 12) &&
          IntegerInRange(s.attention_units, 0, 1) &&
          IntegerInRange(s.treasury_budget_allocated, 0, 25) &&
          IntegerInRange(s.treasury_budget_spent, 0, 25) &&
          IntegerEquals(s.support_receipt_serial, *p.case_serial.value);
      const bool reserved_package =
          *p.state.value == 2 && reserved && !absent &&
          IntegerEquals(s.hours, 12) &&
          IntegerEquals(s.attention_units, 1) &&
          s.mentor_character_id.available &&
          IntegerEquals(s.budget_owner_character_id, actual_owner) &&
          IntegerEquals(s.treasury_budget_allocated, 25) &&
          IntegerEquals(s.treasury_budget_spent, 25) &&
          IntegerInRange(s.owner_capacity_used, 1, 2) &&
          BooleanFalseOrAbsent(s.released) &&
          BooleanFalseOrAbsent(s.withheld) &&
          BooleanFalseOrAbsent(s.atomic_shortfall);
      const bool absent_package =
          *p.state.value == 2 && !reserved && absent &&
          IntegerEquals(s.hours, 0) &&
          IntegerEquals(s.attention_units, 0) &&
          IntegerEquals(s.treasury_budget_allocated, 0) &&
          IntegerEquals(s.treasury_budget_spent, 0) &&
          BooleanFalseOrAbsent(s.released) &&
          ((IntegerEquals(p.policy_route, 1) &&
            BooleanFalseOrAbsent(s.withheld) &&
            BooleanEquals(s.atomic_shortfall, true)) ||
           (IntegerEquals(p.policy_route, 2) &&
            BooleanEquals(s.withheld, true) &&
            BooleanFalseOrAbsent(s.atomic_shortfall)));
      output.readiness.support_ready =
          core_support && (reserved_package || absent_package);
    }

    auto &b = output.budget_ledger;
    DecodeInteger(first[result_case_serial], b.result_case_serial);
    DecodeInteger(first[result_treasury_paid], b.treasury_penalty_paid);
    DecodeInteger(first[result_gold_paid], b.personal_gold_penalty_paid);
    DecodeInteger(first[support_budget_allocated],
                  b.support_treasury_allocated);
    DecodeInteger(first[support_budget_spent], b.support_treasury_spent);
    if (output.readiness.pip_identity_ready && b.result_case_serial.available &&
        *b.result_case_serial.value != *p.case_serial.value) {
      MarkBudgetBindingMismatch(b);
    }
    output.readiness.budget_ledger_ready =
        output.readiness.pip_identity_ready &&
        IntegerEquals(b.result_case_serial, *p.case_serial.value) &&
        IntegerInRange(b.treasury_penalty_paid, 0,
                       std::numeric_limits<std::int64_t>::max()) &&
        IntegerInRange(b.personal_gold_penalty_paid, 0,
                       std::numeric_limits<std::int64_t>::max()) &&
        IntegerInRange(b.support_treasury_allocated, 0, 25) &&
        IntegerInRange(b.support_treasury_spent, 0, 25);

    MarkUnobservableTickets(output);

    auto &m = output.midpoint;
    DecodeInteger(first[midpoint_receipt], m.receipt_serial);
    DecodeBoolean(first[midpoint_resource_delivery_valid],
                  m.resource_delivery_valid);
    DecodeInteger(first[midpoint_progress_status], m.progress_status);
    DecodeInteger(first[midpoint_progress_red_code], m.progress_red_code);
    DecodeInteger(first[midpoint_state], m.state);
    output.readiness.midpoint_ready =
        output.readiness.pip_identity_ready &&
        IntegerEquals(m.receipt_serial, *p.case_serial.value) &&
        m.resource_delivery_valid.available &&
        IntegerEquals(m.progress_status, 0) &&
        IntegerEquals(m.progress_red_code, 1) && IntegerEquals(m.state, 2);

    auto &o = output.outcome;
    DecodeInteger(first[outcome_code], o.code);
    DecodeInteger(first[settlement_receipt], o.settlement_receipt_serial);
    DecodeInteger(first[outcome_result_cycle], o.result_cycle_serial);
    DecodeInteger(first[outcome_result_case], o.result_case_serial);
    DecodeInteger(first[outcome_result_grade], o.result_grade);
    DecodeInteger(first[stability_days_observed],
                  o.stability_days_observed);
    DecodeInteger(first[independent_review_status],
                  o.independent_review_status);
    DecodeInteger(first[independent_review_red_code],
                  o.independent_review_red_code);
    DecodeInteger(first[graduation_receipt], o.graduation_receipt_serial);
    DecodeInteger(first[failure_receipt], o.failure_receipt_serial);
    DecodeBoolean(first[no_support_liability], o.no_support_liability);
    if (output.readiness.pip_identity_ready &&
        (*p.state.value == 3 || *p.state.value == 4)) {
      const auto case_id = *p.case_serial.value;
      const bool graduated =
          *p.state.value == 3 && IntegerEquals(o.code, 1) &&
          IntegerEquals(o.graduation_receipt_serial, case_id) &&
          (IntegerEquals(o.failure_receipt_serial, 0) ||
           OptionalAbsent(o.failure_receipt_serial));
      const bool failed =
          *p.state.value == 4 && IntegerEquals(o.code, 2) &&
          IntegerEquals(o.failure_receipt_serial, case_id) &&
          (IntegerEquals(o.graduation_receipt_serial, 0) ||
           OptionalAbsent(o.graduation_receipt_serial));
      output.readiness.outcome_ready =
          IntegerEquals(o.settlement_receipt_serial, case_id) &&
          IntegerInRange(o.result_cycle_serial, 1,
                         std::numeric_limits<std::int64_t>::max()) &&
          IntegerInRange(o.result_case_serial, 1, 999'999) &&
          IntegerInRange(o.result_grade, 1, 3) &&
          IntegerEquals(o.stability_days_observed, 365) &&
          IntegerEquals(o.independent_review_status, 0) &&
          IntegerEquals(o.independent_review_red_code, 2) &&
          (graduated || failed);
    }

    auto &e = output.next_cycle_evidence;
    DecodeInteger(first[performance_evidence_status], e.status);
    DecodeCharacter(environment, access, first[performance_evidence_owner],
                    e.owner_character_id);
    DecodeCharacter(environment, access, first[performance_evidence_subject],
                    e.subject_character_id);
    DecodeInteger(first[performance_evidence_source_cycle],
                  e.source_cycle_serial);
    DecodeInteger(first[performance_evidence_source_case],
                  e.source_case_serial);
    DecodeInteger(first[performance_evidence_due_cycle], e.due_cycle_serial);
    DecodeInteger(first[performance_evidence_delta], e.delta);
    DecodeInteger(first[performance_evidence_consumed_cycle],
                  e.consumed_cycle_serial);
    DecodeInteger(first[performance_evidence_consumed_case],
                  e.consumed_case_serial);
    if (output.readiness.pip_identity_ready &&
        IntegerInRange(e.status, 1, 2)) {
      const bool base =
          IntegerEquals(e.owner_character_id, actual_owner) &&
          IntegerEquals(e.subject_character_id, before.played_character_id) &&
          IntegerEquals(e.source_cycle_serial, *p.cycle_serial.value) &&
          IntegerEquals(e.source_case_serial, *p.case_serial.value) &&
          IntegerEquals(e.due_cycle_serial, *p.cycle_serial.value + 1) &&
          (IntegerEquals(e.delta, 10) || IntegerEquals(e.delta, -10) ||
           IntegerEquals(e.delta, -15));
      const bool pending =
          IntegerEquals(e.status, 1) && OptionalAbsent(e.consumed_cycle_serial) &&
          OptionalAbsent(e.consumed_case_serial);
      const bool consumed =
          IntegerEquals(e.status, 2) &&
          e.due_cycle_serial.available &&
          IntegerInRange(e.consumed_cycle_serial, *e.due_cycle_serial.value,
                         std::numeric_limits<std::int64_t>::max()) &&
          IntegerEquals(e.consumed_case_serial, *p.case_serial.value);
      output.readiness.next_cycle_evidence_ready =
          base && (pending || consumed);
    }

    output.status = game::ZhongguoB2PipSnapshotStatusV1::available;
    output.unavailable_reason.clear();
    output.readiness.ready = ComponentGate(output.readiness);
    return game::ReadZhongguoB2PipSnapshotResultV1::available;
  } catch (...) {
    InitializeEnvelope(request, nullptr, output);
    SetTopUnavailable(output, "internal_error");
    return game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
