#include "xar_bridge/zhongguo_career_hc_workforce_postcondition_v1.hpp"

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
  receipt_owner = 0,
  receipt_subject,
  receipt_cycle,
  receipt_case,
  receipt_state,
  receipt_choice,
  hc_authorized,
  hc_available,
  hc_reserved,
  hc_occupied,
  hc_frozen,
  hc_reclaimed,
  hc_conserved,
  manager_cost_total,
};

using RawRows = std::array<
    ZhongguoCareerHcWorkforceRawVariableV1,
    kZhongguoCareerHcWorkforcePostconditionV1VariableAllowlist.size()>;

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

bool ReadBytes(const ZhongguoCareerHcWorkforceAccessV1 &access,
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
bool ReadValue(const ZhongguoCareerHcWorkforceAccessV1 &access,
               const void *base, std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const ZhongguoCareerHcWorkforceNativeEnvironmentV1 &environment) noexcept {
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
    const ZhongguoCareerHcWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoCareerHcWorkforceAccessV1 &access,
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
    const ZhongguoCareerHcWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoCareerHcWorkforceAccessV1 &access,
    std::int32_t character_id) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.validate_character != nullptr &&
           access.validate_character(access.context, character_id);
  }
  return ResolveCharacterNative(environment, access, character_id);
}

bool ResolveVariableIdentifier(
    const ZhongguoCareerHcWorkforceNativeEnvironmentV1 &environment,
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

bool FindVariableValue(const ZhongguoCareerHcWorkforceAccessV1 &access,
                       void *context, std::int32_t identifier,
                       ZhongguoCareerHcWorkforceRawVariableV1 &output) noexcept {
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
    const ZhongguoCareerHcWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoCareerHcWorkforceAccessV1 &access,
    std::int32_t character_id, std::string_view key,
    ZhongguoCareerHcWorkforceRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) return false;
  const ZhongguoEventTarget16V1 target{4, {}, character_id};
  void *const context = environment.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

bool ReadAllowlistedRows(
    const ZhongguoCareerHcWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoCareerHcWorkforceAccessV1 &access,
    std::int32_t character_id, RawRows &output) noexcept {
  for (std::size_t index = 0;
       index <
       kZhongguoCareerHcWorkforcePostconditionV1VariableAllowlist.size();
       ++index) {
    const auto key =
        kZhongguoCareerHcWorkforcePostconditionV1VariableAllowlist[index];
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

void DecodeInteger(const ZhongguoCareerHcWorkforceRawVariableV1 &raw,
                   game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 1 || raw.payload % kFixedScale != 0) {
    SetUnavailable(field, "value_type_mismatch");
  } else {
    SetAvailable(field, raw.payload / kFixedScale);
  }
}

void DecodeBoolean(const ZhongguoCareerHcWorkforceRawVariableV1 &raw,
                   game::ZhongguoTypedBooleanV1 &field) {
  game::ZhongguoTypedIntegerV1 decoded;
  DecodeInteger(raw, decoded);
  if (!decoded.available || !decoded.value.has_value()) {
    SetUnavailable(field, decoded.unavailable_reason);
  } else if (*decoded.value != 0 && *decoded.value != 1) {
    SetUnavailable(field, "value_out_of_range");
  } else {
    SetAvailable(field, *decoded.value == 1);
  }
}

void DecodeCharacter(
    const ZhongguoCareerHcWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoCareerHcWorkforceAccessV1 &access,
    const ZhongguoCareerHcWorkforceRawVariableV1 &raw,
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

void MarkIdentityUnavailable(game::ZhongguoCareerHcWorkforceIdentityV1 &value,
                             std::string_view reason) {
  SetUnavailable(value.owner_character_id, reason);
  SetUnavailable(value.subject_character_id, reason);
  SetUnavailable(value.cycle_serial, reason);
  SetUnavailable(value.case_serial, reason);
}

void MarkAllUnavailable(
    game::ZhongguoCareerHcWorkforcePostconditionV1 &output,
    std::string_view reason) {
  MarkIdentityUnavailable(output.m360_identity, reason);
  MarkIdentityUnavailable(output.m360_receipt.identity, reason);
  SetUnavailable(output.m360_receipt.state, reason);
  SetUnavailable(output.m360_receipt.choice, reason);
  SetUnavailable(output.career_hc_partition.authorized, reason);
  SetUnavailable(output.career_hc_partition.available, reason);
  SetUnavailable(output.career_hc_partition.reserved, reason);
  SetUnavailable(output.career_hc_partition.occupied, reason);
  SetUnavailable(output.career_hc_partition.frozen, reason);
  SetUnavailable(output.career_hc_partition.reclaimed, reason);
  SetUnavailable(output.career_hc_partition.conserved, reason);
  SetUnavailable(output.route_b_cost.manager_cost_total, reason);
}

void InitializeEnvelope(
    const ZhongguoCareerHcWorkforcePostconditionRequestV1 &request,
    const ZhongguoCareerHcWorkforceFrameV1 *frame,
    game::ZhongguoCareerHcWorkforcePostconditionV1 &output) {
  output = {};
  output.case_kind = kZhongguoCareerHcWorkforcePostconditionV1CaseKind;
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  output.requested_owner_character_id = request.owner_character_id;
  if (frame != nullptr) {
    output.date_raw = frame->date_raw;
    output.paused = frame->paused;
    output.player_character_id = frame->played_character_id;
    output.subject_character_id = frame->played_character_id;
  }
  MarkAllUnavailable(output, "postcondition_unavailable");
}

void SetTopUnavailable(
    game::ZhongguoCareerHcWorkforcePostconditionV1 &output,
    std::string_view reason, bool same_frame_ready = false,
    bool preserve_fields = false) {
  output.status =
      game::ZhongguoCareerHcWorkforcePostconditionStatusV1::unavailable;
  if (!preserve_fields) MarkAllUnavailable(output, "postcondition_unavailable");
  output.readiness.ready = false;
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
    const ZhongguoCareerHcWorkforcePostconditionRequestV1 &request) noexcept {
  return request.expected_snapshot_revision > 0 &&
         request.owner_character_id > 0 && ValidNonce(request.request_nonce);
}

bool IntegerEquals(const game::ZhongguoTypedIntegerV1 &field,
                   std::int64_t expected) noexcept {
  return field.available && field.value.has_value() &&
         *field.value == expected;
}

bool Positive(const game::ZhongguoTypedIntegerV1 &field) noexcept {
  return field.available && field.value.has_value() && *field.value > 0;
}

bool NonNegative(const game::ZhongguoTypedIntegerV1 &field) noexcept {
  return field.available && field.value.has_value() && *field.value >= 0;
}

bool Conserved(const game::ZhongguoCareerHcPartitionV1 &partition) noexcept {
  if (!NonNegative(partition.authorized) ||
      !NonNegative(partition.available) ||
      !NonNegative(partition.reserved) ||
      !NonNegative(partition.occupied) ||
      !NonNegative(partition.frozen) ||
      !NonNegative(partition.reclaimed) || !partition.conserved.available ||
      !partition.conserved.value.has_value() ||
      !*partition.conserved.value) {
    return false;
  }
  const auto authorized = *partition.authorized.value;
  std::int64_t total = 0;
  const std::array<const game::ZhongguoTypedIntegerV1 *, 5> buckets{
      &partition.available, &partition.reserved, &partition.occupied,
      &partition.frozen, &partition.reclaimed};
  for (const auto *bucket : buckets) {
    const auto value = *bucket->value;
    if (value > authorized ||
        total > std::numeric_limits<std::int64_t>::max() - value) {
      return false;
    }
    total += value;
  }
  return total == authorized;
}

bool AnyReceiptField(const RawRows &rows) noexcept {
  for (std::size_t index = receipt_owner; index <= receipt_choice; ++index) {
    if (rows[index].present) return true;
  }
  return false;
}

bool ComponentGate(
    const game::ZhongguoCareerHcWorkforcePostconditionReadinessV1 &value) {
  return value.player_subject_binding_ready && value.owner_binding_ready &&
         value.m360_identity_ready && value.m360_route_b_receipt_ready &&
         value.career_hc_partition_ready &&
         value.career_hc_conservation_ready &&
         value.route_b_manager_cost_zero_ready && value.same_frame_ready;
}

} // namespace

ZhongguoCareerHcWorkforceNativeEnvironmentV1
BindZhongguoCareerHcWorkforceNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return BindZhongguoCaseNativeEnvironmentV1(module_base,
                                             exact_build_admitted);
}

game::ReadZhongguoCareerHcWorkforcePostconditionResultV1
ReadZhongguoCareerHcWorkforcePostconditionV1(
    const ZhongguoCareerHcWorkforceNativeEnvironmentV1 &environment,
    const ZhongguoCareerHcWorkforceAccessV1 &access,
    const ZhongguoCareerHcWorkforcePostconditionRequestV1 &request,
    game::ZhongguoCareerHcWorkforcePostconditionV1 &output) noexcept {
  try {
    InitializeEnvelope(request, nullptr, output);
    if (!ValidRequest(request) || !EnvironmentIsExact(environment)) {
      SetTopUnavailable(output, "unsupported_build");
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetTopUnavailable(output, "requires_application_main");
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }
    if (environment.offline_fixture_function_overrides &&
        (access.validate_character == nullptr ||
         access.read_allowlisted_variable == nullptr)) {
      SetTopUnavailable(output, "internal_error");
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }

    ZhongguoCareerHcWorkforceFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }
    InitializeEnvelope(request, &before, output);
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }
    if (!before.paused) {
      SetTopUnavailable(output, "requires_paused");
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0 ||
        !ValidateCharacter(environment, access, before.played_character_id)) {
      SetTopUnavailable(output, "map_not_ready");
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }
    if (request.owner_character_id == before.played_character_id ||
        !ValidateCharacter(environment, access, request.owner_character_id)) {
      SetTopUnavailable(output, "owner_filter_mismatch");
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }

    RawRows first{};
    RawRows second{};
    if (!ReadAllowlistedRows(environment, access, before.played_character_id,
                             first) ||
        !ReadAllowlistedRows(environment, access, before.played_character_id,
                             second)) {
      SetTopUnavailable(output, "variable_context_unavailable");
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }
    ZhongguoCareerHcWorkforceFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first != second) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }

    DecodeCharacter(environment, access, first[receipt_owner],
                    output.m360_receipt.identity.owner_character_id);
    DecodeCharacter(environment, access, first[receipt_subject],
                    output.m360_receipt.identity.subject_character_id);
    DecodeInteger(first[receipt_cycle],
                  output.m360_receipt.identity.cycle_serial);
    DecodeInteger(first[receipt_case], output.m360_receipt.identity.case_serial);
    DecodeInteger(first[receipt_state], output.m360_receipt.state);
    DecodeInteger(first[receipt_choice], output.m360_receipt.choice);
    output.m360_identity = output.m360_receipt.identity;

    DecodeInteger(first[hc_authorized], output.career_hc_partition.authorized);
    DecodeInteger(first[hc_available], output.career_hc_partition.available);
    DecodeInteger(first[hc_reserved], output.career_hc_partition.reserved);
    DecodeInteger(first[hc_occupied], output.career_hc_partition.occupied);
    DecodeInteger(first[hc_frozen], output.career_hc_partition.frozen);
    DecodeInteger(first[hc_reclaimed], output.career_hc_partition.reclaimed);
    DecodeBoolean(first[hc_conserved], output.career_hc_partition.conserved);
    DecodeInteger(first[manager_cost_total],
                  output.route_b_cost.manager_cost_total);

    auto &ready = output.readiness;
    ready.same_frame_ready = true;
    const auto owner = request.owner_character_id;
    const auto subject = before.played_character_id;
    ready.player_subject_binding_ready =
        IntegerEquals(output.m360_identity.subject_character_id, subject);
    ready.owner_binding_ready = owner != subject &&
                                IntegerEquals(
                                    output.m360_identity.owner_character_id,
                                    owner);
    ready.m360_identity_ready =
        ready.player_subject_binding_ready && ready.owner_binding_ready &&
        Positive(output.m360_identity.cycle_serial) &&
        Positive(output.m360_identity.case_serial);
    ready.m360_route_b_receipt_ready =
        ready.m360_identity_ready && IntegerEquals(output.m360_receipt.state, 4) &&
        IntegerEquals(output.m360_receipt.choice, 2);
    ready.career_hc_partition_ready =
        NonNegative(output.career_hc_partition.authorized) &&
        NonNegative(output.career_hc_partition.available) &&
        NonNegative(output.career_hc_partition.reserved) &&
        NonNegative(output.career_hc_partition.occupied) &&
        NonNegative(output.career_hc_partition.frozen) &&
        NonNegative(output.career_hc_partition.reclaimed) &&
        output.career_hc_partition.conserved.available;
    ready.career_hc_conservation_ready =
        ready.career_hc_partition_ready && Conserved(output.career_hc_partition);
    ready.route_b_manager_cost_zero_ready =
        IntegerEquals(output.route_b_cost.manager_cost_total, 0);
    ready.ready = ComponentGate(ready);

    if (!AnyReceiptField(first)) {
      SetTopUnavailable(output, "receipt_not_recorded", true, true);
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }
    if (!ready.ready) {
      SetTopUnavailable(output, "postcondition_incomplete", true, true);
      return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
          unavailable;
    }
    output.status =
        game::ZhongguoCareerHcWorkforcePostconditionStatusV1::available;
    output.unavailable_reason.clear();
    return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::available;
  } catch (...) {
    InitializeEnvelope(request, nullptr, output);
    SetTopUnavailable(output, "internal_error");
    return game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::
        unavailable;
  }
}

} // namespace xar::ck3_11906
