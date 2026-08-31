#include "xar_bridge/zhongguo_incident_snapshot_v1.hpp"

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
  probe_owner = 0,
  probe_subject,
  probe_cycle,
  probe_serial,
  probe_result,
  probe_source,
  probe_consequence,
  probe_subject_gold,
  probe_manager_treasury,
  probe_capital_control,
  final_applicable,
  final_kpi_staged,
  na_owner,
  na_subject,
  na_cycle,
  na_reason,
  na_probe_serial,
  na_receipt,
  final_owner,
  final_subject,
  final_cycle,
  final_case,
  final_state,
  final_revision,
  final_incident_serial,
  final_source,
  final_consequence,
  final_score,
  kpi_pending,
  kpi_consumed,
  kpi_owner,
  kpi_subject,
  kpi_origin_cycle,
  kpi_case,
  kpi_state,
  kpi_score,
  kpi_due_cycle,
  kpi_due_offset,
  kpi_incident_serial,
  kpi_source,
  kpi_consequence,
  kpi_receipt_serial,
  kpi_consumed_owner,
  kpi_consumed_subject,
  kpi_consumed_origin_cycle,
  kpi_consumed_due_cycle,
  kpi_consumed_cycle,
  kpi_consumed_case,
  kpi_consumed_score,
  kpi_consumed_incident_serial,
};

using RawRows = std::array<ZhongguoIncidentRawVariableV1, 50>;

const std::array<std::string_view, 50> &Allowlist(
    game::ZhongguoIncidentProfileV1 profile) noexcept {
  switch (profile) {
  case game::ZhongguoIncidentProfileV1::x:
    return kZhongguoIncidentSnapshotV1XAllowlist;
  case game::ZhongguoIncidentProfileV1::y:
    return kZhongguoIncidentSnapshotV1YAllowlist;
  case game::ZhongguoIncidentProfileV1::z:
    return kZhongguoIncidentSnapshotV1ZAllowlist;
  }
  return kZhongguoIncidentSnapshotV1XAllowlist;
}

std::string_view ProfileName(game::ZhongguoIncidentProfileV1 profile) {
  switch (profile) {
  case game::ZhongguoIncidentProfileV1::x: return "x";
  case game::ZhongguoIncidentProfileV1::y: return "y";
  case game::ZhongguoIncidentProfileV1::z: return "z";
  }
  return {};
}

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

bool ReadBytes(const ZhongguoIncidentAccessV1 &access, const void *address,
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
bool ReadValue(const ZhongguoIncidentAccessV1 &access, const void *base,
               std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const ZhongguoIncidentNativeEnvironmentV1 &environment) noexcept {
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
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
    const ZhongguoIncidentAccessV1 &access,
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
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
    const ZhongguoIncidentAccessV1 &access,
    std::int32_t character_id) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.validate_character != nullptr &&
           access.validate_character(access.context, character_id);
  }
  return ResolveCharacterNative(environment, access, character_id);
}

bool ResolveVariableIdentifier(
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
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

bool FindVariableValue(const ZhongguoIncidentAccessV1 &access, void *context,
                       std::int32_t identifier,
                       ZhongguoIncidentRawVariableV1 &output) noexcept {
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
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
    const ZhongguoIncidentAccessV1 &access, std::int32_t character_id,
    std::string_view key, ZhongguoIncidentRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) return false;
  // The paused played character is the only engine scope.  Owner is an
  // expected-value filter over character targets frozen on that subject.
  const ZhongguoEventTarget16V1 target{4, {}, character_id};
  void *const context = environment.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

bool ReadAllowlistedRows(
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
    const ZhongguoIncidentAccessV1 &access,
    const ZhongguoIncidentSnapshotRequestV1 &request,
    std::int32_t character_id, RawRows &output) noexcept {
  const auto &allowlist = Allowlist(request.profile);
  for (std::size_t index = 0; index < allowlist.size(); ++index) {
    const bool read = environment.offline_fixture_function_overrides
                          ? access.read_allowlisted_variable != nullptr &&
                                access.read_allowlisted_variable(
                                    access.context, character_id,
                                    allowlist[index], output[index])
                          : ReadAllowlistedVariableNative(
                                environment, access, character_id,
                                allowlist[index], output[index]);
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

void DecodeInteger(const ZhongguoIncidentRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1 || raw.payload % kFixedScale != 0) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload / kFixedScale);
  }
}

void DecodeQ100000(const ZhongguoIncidentRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload);
  }
}

void DecodeCharacter(
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
    const ZhongguoIncidentAccessV1 &access,
    const ZhongguoIncidentRawVariableV1 &raw,
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

void MakeNaUnavailable(game::ZhongguoIncidentNaTerminalV1 &value,
                       std::string_view reason) {
  UnavailableMany(reason, value.owner_character_id, value.subject_character_id,
                  value.cycle_serial, value.reason, value.probe_serial,
                  value.receipt_serial, value.applicable, value.kpi_staged);
}

void MakeIncidentUnavailable(
    game::ZhongguoIncidentPositiveTerminalV1 &value,
    std::string_view reason) {
  UnavailableMany(reason, value.owner_character_id, value.subject_character_id,
                  value.cycle_serial, value.case_serial, value.state,
                  value.revision, value.incident_serial, value.source_kind,
                  value.consequence_kind, value.final_score, value.applicable,
                  value.kpi_staged);
}

void MakeKpiUnavailable(game::ZhongguoIncidentKpiStateV1 &value,
                        std::string_view reason) {
  value.disposition = game::ZhongguoIncidentKpiDispositionV1::unavailable;
  UnavailableMany(
      reason, value.pending, value.consumed, value.owner_character_id,
      value.subject_character_id, value.origin_cycle, value.due_cycle,
      value.due_offset, value.case_serial, value.state, value.score,
      value.incident_serial, value.source_kind, value.consequence_kind,
      value.receipt_serial, value.consumed_owner_character_id,
      value.consumed_subject_character_id, value.consumed_origin_cycle,
      value.consumed_due_cycle, value.consumed_cycle,
      value.consumed_case_serial, value.consumed_score,
      value.consumed_incident_serial);
}

void MakeAllFieldsUnavailable(game::ZhongguoIncidentSnapshotV1 &output,
                              std::string_view reason) {
  UnavailableMany(reason, output.probe.owner_character_id,
                  output.probe.subject_character_id,
                  output.probe.cycle_serial, output.probe.probe_serial,
                  output.probe.result, output.probe.source_kind,
                  output.probe.consequence_kind,
                  output.resources.subject_personal_gold_q100000,
                  output.resources.manager_treasury_q100000,
                  output.resources.capital_control_q100000);
  MakeNaUnavailable(output.na_terminal, reason);
  MakeIncidentUnavailable(output.incident_terminal, reason);
  MakeKpiUnavailable(output.kpi, reason);
}

void InitializeEnvelope(const ZhongguoIncidentSnapshotRequestV1 &request,
                        const ZhongguoIncidentFrameV1 *frame,
                        game::ZhongguoIncidentSnapshotV1 &output) {
  output = {};
  output.case_kind = kZhongguoIncidentSnapshotV1CaseKind;
  output.profile.assign(ProfileName(request.profile));
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  output.requested_owner_character_id = request.owner_character_id;
  if (frame != nullptr) {
    output.date_raw = frame->date_raw;
    output.paused = frame->paused;
    output.player_character_id = frame->played_character_id;
    output.subject_character_id = frame->played_character_id;
  }
  MakeAllFieldsUnavailable(output, "snapshot_unavailable");
}

void SetTopUnavailable(game::ZhongguoIncidentSnapshotV1 &output,
                       std::string_view reason,
                       bool same_frame_ready = false) {
  output.status = game::ZhongguoIncidentSnapshotStatusV1::unavailable;
  output.terminal_kind = game::ZhongguoIncidentTerminalKindV1::unavailable;
  MakeAllFieldsUnavailable(output, "snapshot_unavailable");
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

bool ValidRequest(const ZhongguoIncidentSnapshotRequestV1 &request) noexcept {
  return request.expected_snapshot_revision > 0 &&
         request.owner_character_id > 0 &&
         !ProfileName(request.profile).empty() && ValidNonce(request.request_nonce);
}

bool AllProbeAbsent(const RawRows &rows) noexcept {
  for (std::size_t index = probe_owner; index <= probe_consequence; ++index) {
    if (rows[index].present) return false;
  }
  return true;
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

bool SameInteger(const game::ZhongguoTypedIntegerV1 &left,
                 const game::ZhongguoTypedIntegerV1 &right) noexcept {
  return left.available && right.available && left.value == right.value;
}

bool ValidSourceConsequence(std::int64_t source,
                            std::int64_t consequence) noexcept {
  return (source == 1 && consequence == 1) ||
         ((source == 3 || source == 4) && consequence == 2) ||
         (source == 5 && consequence == 3);
}

bool ComponentGate(const game::ZhongguoIncidentReadinessV1 &value) noexcept {
  return value.player_subject_binding_ready && value.owner_binding_ready &&
         value.profile_binding_ready && value.probe_ready &&
         value.terminal_ready && value.resource_snapshot_ready &&
         value.kpi_state_ready && value.same_frame_ready;
}

void DecodeProbe(const ZhongguoIncidentNativeEnvironmentV1 &environment,
                 const ZhongguoIncidentAccessV1 &access,
                 const RawRows &rows,
                 game::ZhongguoIncidentSnapshotV1 &output) {
  DecodeCharacter(environment, access, rows[probe_owner],
                  output.probe.owner_character_id);
  DecodeCharacter(environment, access, rows[probe_subject],
                  output.probe.subject_character_id);
  DecodeInteger(rows[probe_cycle], output.probe.cycle_serial);
  DecodeInteger(rows[probe_serial], output.probe.probe_serial);
  DecodeInteger(rows[probe_result], output.probe.result);
  DecodeInteger(rows[probe_source], output.probe.source_kind);
  DecodeInteger(rows[probe_consequence], output.probe.consequence_kind);
  DecodeQ100000(rows[probe_subject_gold],
                output.resources.subject_personal_gold_q100000);
  DecodeQ100000(rows[probe_manager_treasury],
                output.resources.manager_treasury_q100000);
  DecodeQ100000(rows[probe_capital_control],
                output.resources.capital_control_q100000);
}

bool DecodeAndValidateNa(
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
    const ZhongguoIncidentAccessV1 &access, const RawRows &rows,
    game::ZhongguoIncidentSnapshotV1 &output) {
  auto &na = output.na_terminal;
  DecodeCharacter(environment, access, rows[na_owner], na.owner_character_id);
  DecodeCharacter(environment, access, rows[na_subject],
                  na.subject_character_id);
  DecodeInteger(rows[na_cycle], na.cycle_serial);
  DecodeInteger(rows[na_reason], na.reason);
  DecodeInteger(rows[na_probe_serial], na.probe_serial);
  DecodeInteger(rows[na_receipt], na.receipt_serial);
  DecodeInteger(rows[final_applicable], na.applicable);
  DecodeInteger(rows[final_kpi_staged], na.kpi_staged);
  return IntegerEquals(output.probe.result, 0) &&
         IntegerEquals(output.probe.source_kind, 0) &&
         IntegerEquals(output.probe.consequence_kind, 0) &&
         SameInteger(na.owner_character_id, output.probe.owner_character_id) &&
         SameInteger(na.subject_character_id,
                     output.probe.subject_character_id) &&
         SameInteger(na.cycle_serial, output.probe.cycle_serial) &&
         SameInteger(na.probe_serial, output.probe.probe_serial) &&
         IntegerEquals(na.reason, 1) &&
         IntegerInRange(na.receipt_serial, 1,
                        std::numeric_limits<std::int64_t>::max()) &&
         IntegerEquals(na.applicable, 0) &&
         IntegerEquals(na.kpi_staged, 0);
}

bool DecodeAndValidatePositive(
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
    const ZhongguoIncidentAccessV1 &access, const RawRows &rows,
    game::ZhongguoIncidentProfileV1 profile,
    game::ZhongguoIncidentSnapshotV1 &output) {
  auto &incident = output.incident_terminal;
  DecodeCharacter(environment, access, rows[final_owner],
                  incident.owner_character_id);
  DecodeCharacter(environment, access, rows[final_subject],
                  incident.subject_character_id);
  DecodeInteger(rows[final_cycle], incident.cycle_serial);
  DecodeInteger(rows[final_case], incident.case_serial);
  DecodeInteger(rows[final_state], incident.state);
  DecodeInteger(rows[final_revision], incident.revision);
  DecodeInteger(rows[final_incident_serial], incident.incident_serial);
  DecodeInteger(rows[final_source], incident.source_kind);
  DecodeInteger(rows[final_consequence], incident.consequence_kind);
  DecodeInteger(rows[final_score], incident.final_score);
  DecodeInteger(rows[final_applicable], incident.applicable);
  DecodeInteger(rows[final_kpi_staged], incident.kpi_staged);
  const auto expected_state =
      profile == game::ZhongguoIncidentProfileV1::x ? 8 : 6;
  return IntegerEquals(output.probe.result, 1) &&
         output.probe.source_kind.available &&
         output.probe.consequence_kind.available &&
         ValidSourceConsequence(*output.probe.source_kind.value,
                                *output.probe.consequence_kind.value) &&
         SameInteger(incident.owner_character_id,
                     output.probe.owner_character_id) &&
         SameInteger(incident.subject_character_id,
                     output.probe.subject_character_id) &&
         SameInteger(incident.cycle_serial, output.probe.cycle_serial) &&
         IntegerInRange(incident.case_serial, 1, 999'999) &&
         IntegerEquals(incident.state, expected_state) &&
         IntegerInRange(incident.revision, 1,
                        std::numeric_limits<std::int64_t>::max()) &&
         IntegerInRange(incident.incident_serial, 1,
                        std::numeric_limits<std::int64_t>::max()) &&
         SameInteger(incident.source_kind, output.probe.source_kind) &&
         SameInteger(incident.consequence_kind,
                     output.probe.consequence_kind) &&
         IntegerInRange(incident.final_score, -4, 4) &&
         IntegerEquals(incident.applicable, 1) &&
         IntegerInRange(incident.kpi_staged, 0, 1);
}

void DecodeKpiBase(const ZhongguoIncidentNativeEnvironmentV1 &environment,
                   const ZhongguoIncidentAccessV1 &access,
                   const RawRows &rows,
                   game::ZhongguoIncidentKpiStateV1 &kpi) {
  DecodeInteger(rows[kpi_pending], kpi.pending);
  DecodeInteger(rows[kpi_consumed], kpi.consumed);
  DecodeCharacter(environment, access, rows[kpi_owner],
                  kpi.owner_character_id);
  DecodeCharacter(environment, access, rows[kpi_subject],
                  kpi.subject_character_id);
  DecodeInteger(rows[kpi_origin_cycle], kpi.origin_cycle);
  DecodeInteger(rows[kpi_due_cycle], kpi.due_cycle);
  DecodeInteger(rows[kpi_due_offset], kpi.due_offset);
  DecodeInteger(rows[kpi_case], kpi.case_serial);
  DecodeInteger(rows[kpi_state], kpi.state);
  DecodeInteger(rows[kpi_score], kpi.score);
  DecodeInteger(rows[kpi_incident_serial], kpi.incident_serial);
  DecodeInteger(rows[kpi_source], kpi.source_kind);
  DecodeInteger(rows[kpi_consequence], kpi.consequence_kind);
}

bool ValidateKpiBase(const game::ZhongguoIncidentSnapshotV1 &output) {
  const auto &kpi = output.kpi;
  const auto &terminal = output.incident_terminal;
  return SameInteger(kpi.owner_character_id, terminal.owner_character_id) &&
         SameInteger(kpi.subject_character_id,
                     terminal.subject_character_id) &&
         SameInteger(kpi.origin_cycle, terminal.cycle_serial) &&
         kpi.due_cycle.available && kpi.origin_cycle.available &&
         *kpi.due_cycle.value == *kpi.origin_cycle.value + 1 &&
         IntegerEquals(kpi.due_offset, 1) &&
         SameInteger(kpi.case_serial, terminal.case_serial) &&
         SameInteger(kpi.state, terminal.state) &&
         SameInteger(kpi.score, terminal.final_score) &&
         SameInteger(kpi.incident_serial, terminal.incident_serial) &&
         SameInteger(kpi.source_kind, terminal.source_kind) &&
         SameInteger(kpi.consequence_kind, terminal.consequence_kind);
}

bool DecodeAndValidateKpi(
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
    const ZhongguoIncidentAccessV1 &access, const RawRows &rows,
    game::ZhongguoIncidentSnapshotV1 &output) {
  if (!IntegerEquals(output.incident_terminal.kpi_staged, 1)) {
    MakeKpiUnavailable(output.kpi, "kpi_not_staged");
    return false;
  }
  DecodeKpiBase(environment, access, rows, output.kpi);
  if (!ValidateKpiBase(output)) return false;
  if (IntegerEquals(output.kpi.pending, 1) &&
      IntegerEquals(output.kpi.consumed, 0)) {
    output.kpi.disposition = game::ZhongguoIncidentKpiDispositionV1::pending;
    UnavailableMany(
        "not_yet_consumed", output.kpi.receipt_serial,
        output.kpi.consumed_owner_character_id,
        output.kpi.consumed_subject_character_id,
        output.kpi.consumed_origin_cycle, output.kpi.consumed_due_cycle,
        output.kpi.consumed_cycle, output.kpi.consumed_case_serial,
        output.kpi.consumed_score, output.kpi.consumed_incident_serial);
    return true;
  }
  if (!IntegerEquals(output.kpi.pending, 0) ||
      !IntegerEquals(output.kpi.consumed, 1)) {
    return false;
  }
  DecodeInteger(rows[kpi_receipt_serial], output.kpi.receipt_serial);
  DecodeCharacter(environment, access, rows[kpi_consumed_owner],
                  output.kpi.consumed_owner_character_id);
  DecodeCharacter(environment, access, rows[kpi_consumed_subject],
                  output.kpi.consumed_subject_character_id);
  DecodeInteger(rows[kpi_consumed_origin_cycle],
                output.kpi.consumed_origin_cycle);
  DecodeInteger(rows[kpi_consumed_due_cycle],
                output.kpi.consumed_due_cycle);
  DecodeInteger(rows[kpi_consumed_cycle], output.kpi.consumed_cycle);
  DecodeInteger(rows[kpi_consumed_case], output.kpi.consumed_case_serial);
  DecodeInteger(rows[kpi_consumed_score], output.kpi.consumed_score);
  DecodeInteger(rows[kpi_consumed_incident_serial],
                output.kpi.consumed_incident_serial);
  const bool valid =
      IntegerInRange(output.kpi.receipt_serial, 1,
                     std::numeric_limits<std::int64_t>::max()) &&
      SameInteger(output.kpi.consumed_owner_character_id,
                  output.kpi.owner_character_id) &&
      SameInteger(output.kpi.consumed_subject_character_id,
                  output.kpi.subject_character_id) &&
      SameInteger(output.kpi.consumed_origin_cycle,
                  output.kpi.origin_cycle) &&
      SameInteger(output.kpi.consumed_due_cycle, output.kpi.due_cycle) &&
      output.kpi.consumed_cycle.available && output.kpi.due_cycle.available &&
      *output.kpi.consumed_cycle.value >= *output.kpi.due_cycle.value &&
      SameInteger(output.kpi.consumed_case_serial, output.kpi.case_serial) &&
      SameInteger(output.kpi.consumed_score, output.kpi.score) &&
      SameInteger(output.kpi.consumed_incident_serial,
                  output.kpi.incident_serial);
  if (valid) {
    output.kpi.disposition =
        game::ZhongguoIncidentKpiDispositionV1::consumed;
  }
  return valid;
}

} // namespace

ZhongguoIncidentNativeEnvironmentV1 BindZhongguoIncidentNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base,
                                             exact_build_admitted);
}

game::ReadZhongguoIncidentSnapshotResultV1 ReadZhongguoIncidentSnapshotV1(
    const ZhongguoIncidentNativeEnvironmentV1 &environment,
    const ZhongguoIncidentAccessV1 &access,
    const ZhongguoIncidentSnapshotRequestV1 &request,
    game::ZhongguoIncidentSnapshotV1 &output) noexcept {
  try {
    InitializeEnvelope(request, nullptr, output);
    if (!ValidRequest(request) || !EnvironmentIsExact(environment)) {
      SetTopUnavailable(output, "unsupported_build");
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetTopUnavailable(output, "requires_application_main");
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    if (environment.offline_fixture_function_overrides &&
        (access.validate_character == nullptr ||
         access.read_allowlisted_variable == nullptr)) {
      SetTopUnavailable(output, "internal_error");
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }

    ZhongguoIncidentFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    InitializeEnvelope(request, &before, output);
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    if (!before.paused) {
      SetTopUnavailable(output, "requires_paused");
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0 ||
        !ValidateCharacter(environment, access,
                           before.played_character_id)) {
      SetTopUnavailable(output, "map_not_ready");
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }

    RawRows first{};
    RawRows second{};
    if (!ReadAllowlistedRows(environment, access, request,
                             before.played_character_id, first)) {
      SetTopUnavailable(output, "variable_identifier_unavailable");
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    if (!ReadAllowlistedRows(environment, access, request,
                             before.played_character_id, second)) {
      SetTopUnavailable(output, "variable_context_unavailable");
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    ZhongguoIncidentFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first != second) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    output.readiness.same_frame_ready = true;
    output.readiness.profile_binding_ready = true;
    if (AllProbeAbsent(first)) {
      SetTopUnavailable(output, "incident_not_found", true);
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }

    DecodeProbe(environment, access, first, output);
    const bool probe_shape =
        output.probe.owner_character_id.available &&
        IntegerInRange(output.probe.cycle_serial, 1,
                       std::numeric_limits<std::int64_t>::max()) &&
        IntegerInRange(output.probe.probe_serial, 1,
                       std::numeric_limits<std::int64_t>::max()) &&
        IntegerInRange(output.probe.result, 0, 1) &&
        IntegerInRange(output.probe.source_kind, 0, 5) &&
        IntegerInRange(output.probe.consequence_kind, 0, 3);
    if (!probe_shape ||
        !IntegerEquals(output.probe.subject_character_id,
                       before.played_character_id)) {
      SetTopUnavailable(output, "incident_inconsistent", true);
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    output.readiness.player_subject_binding_ready = true;
    const auto actual_owner =
        static_cast<std::int32_t>(*output.probe.owner_character_id.value);
    if (actual_owner == before.played_character_id) {
      SetTopUnavailable(output, "not_received_self", true);
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    if (actual_owner != request.owner_character_id) {
      SetTopUnavailable(output, "owner_filter_mismatch", true);
      return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
    }
    output.readiness.owner_binding_ready = true;
    output.readiness.probe_ready = true;
    output.readiness.resource_snapshot_ready =
        output.resources.subject_personal_gold_q100000.available &&
        output.resources.manager_treasury_q100000.available &&
        output.resources.capital_control_q100000.available;

    DecodeInteger(first[final_applicable],
                  output.na_terminal.applicable);
    if (IntegerEquals(output.na_terminal.applicable, 0)) {
      if (!DecodeAndValidateNa(environment, access, first, output)) {
        SetTopUnavailable(output, "incident_inconsistent", true);
        return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
      }
      output.terminal_kind = game::ZhongguoIncidentTerminalKindV1::na;
      MakeIncidentUnavailable(output.incident_terminal,
                              "terminal_not_selected");
      MakeKpiUnavailable(output.kpi, "not_applicable");
      output.kpi.disposition =
          game::ZhongguoIncidentKpiDispositionV1::not_staged;
      output.readiness.terminal_ready = true;
      output.readiness.kpi_state_ready = true;
    } else {
      MakeNaUnavailable(output.na_terminal, "terminal_not_selected");
      if (!DecodeAndValidatePositive(environment, access, first,
                                     request.profile, output)) {
        SetTopUnavailable(output, "incident_inconsistent", true);
        return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
      }
      output.terminal_kind = game::ZhongguoIncidentTerminalKindV1::incident;
      output.readiness.terminal_ready = true;
      output.readiness.kpi_state_ready =
          DecodeAndValidateKpi(environment, access, first, output);
    }

    output.status = game::ZhongguoIncidentSnapshotStatusV1::available;
    output.unavailable_reason.clear();
    output.readiness.ready = ComponentGate(output.readiness);
    return game::ReadZhongguoIncidentSnapshotResultV1::available;
  } catch (...) {
    InitializeEnvelope(request, nullptr, output);
    SetTopUnavailable(output, "internal_error");
    return game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
