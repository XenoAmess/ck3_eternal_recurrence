#include "xar_bridge/zhongguo_ai_owned_case_snapshot_v1.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
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
constexpr std::size_t kCharacterDeathMarkerOffset = 0x1C8;
constexpr std::size_t kTitleIdentityOffset = 0x10;
constexpr std::size_t kTitleTemplateOffset = 0x160;
constexpr std::size_t kTitleTierOffset = 0x5C;
constexpr std::size_t kGovernmentKeyOffset = 0x18;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 0x0F;
constexpr std::size_t kMaximumStableKeyBytes = 1'024;

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
};

using RawRows =
    std::array<ZhongguoRawVariableV1,
               kZhongguoAiOwnedCaseSnapshotV1VariableAllowlist.size()>;

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

bool ReadBytes(const ZhongguoAiOwnedCaseAccessV1 &access,
               const void *address, void *output, std::size_t size) noexcept {
  if (access.variables.read_memory != nullptr) {
    return access.variables.read_memory(access.variables.context, address,
                                        output, size);
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
bool ReadValue(const ZhongguoAiOwnedCaseAccessV1 &access, const void *base,
               std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

template <typename Value>
bool ReadSlot(const ZhongguoAiOwnedCaseAccessV1 &access, Value *const *slot,
              Value *&output) noexcept {
  return ReadBytes(access, slot, &output, sizeof(output));
}

bool ReadNativeString(const ZhongguoAiOwnedCaseAccessV1 &access,
                      const void *native_string,
                      std::string &output) noexcept {
  std::size_t size = 0;
  std::size_t capacity = 0;
  if (!ReadValue(access, native_string, kMsvcStringSizeOffset, size) ||
      !ReadValue(access, native_string, kMsvcStringCapacityOffset, capacity) ||
      size > capacity || size > kMaximumStableKeyBytes) {
    return false;
  }
  const char *data = static_cast<const char *>(native_string);
  if (capacity > kMsvcStringInlineCapacity &&
      !ReadValue(access, native_string, 0, data)) {
    return false;
  }
  if (size > 0 && data == nullptr) return false;
  try {
    output.assign(size, '\0');
  } catch (...) {
    return false;
  }
  return size == 0 || ReadBytes(access, data, output.data(), size);
}

bool EnvironmentIsExact(
    const ZhongguoAiOwnedCaseNativeEnvironmentV1 &environment) noexcept {
  const auto &variables = environment.variables;
  if (!variables.exact_build_admitted) return false;
  if (variables.offline_fixture_function_overrides) {
    return variables.module_base == 0 &&
           environment.landed_title_storage_slot == nullptr &&
           environment.landed_title_fallback_slot == nullptr &&
           environment.government_fallback_slot == nullptr &&
           environment.primary_title == nullptr &&
           environment.immediate_liege == nullptr &&
           environment.government == nullptr &&
           environment.is_human_player == nullptr;
  }
  if (variables.module_base == 0 ||
      variables.variable_context_for_scope == nullptr ||
      variables.variable_identifier_table == nullptr ||
      variables.variable_identifier_lookup == nullptr ||
      variables.variable_identifier_name == nullptr ||
      variables.character_storage_slot == nullptr ||
      variables.character_fallback_slot == nullptr ||
      environment.landed_title_storage_slot == nullptr ||
      environment.landed_title_fallback_slot == nullptr ||
      environment.government_fallback_slot == nullptr ||
      environment.primary_title == nullptr ||
      environment.immediate_liege == nullptr ||
      environment.government == nullptr ||
      environment.is_human_player == nullptr) {
    return false;
  }
  const auto base = variables.module_base;
  return reinterpret_cast<std::uintptr_t>(
             variables.variable_context_for_scope) ==
             base + kZhongguoVariableContextForScopeRva &&
         reinterpret_cast<std::uintptr_t>(
             variables.variable_identifier_table) ==
             base + kZhongguoVariableIdentifierTableRva &&
         reinterpret_cast<std::uintptr_t>(
             variables.variable_identifier_lookup) ==
             base + kZhongguoVariableIdentifierLookupRva &&
         reinterpret_cast<std::uintptr_t>(
             variables.variable_identifier_name) ==
             base + kZhongguoVariableIdentifierNameRva &&
         reinterpret_cast<std::uintptr_t>(
             variables.character_storage_slot) ==
             base + kZhongguoCharacterStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             variables.character_fallback_slot) ==
             base + kZhongguoCharacterFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.landed_title_storage_slot) ==
             base + kZhongguoAiCaseLandedTitleStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.landed_title_fallback_slot) ==
             base + kZhongguoAiCaseLandedTitleFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.government_fallback_slot) ==
             base + kZhongguoAiCaseGovernmentFallbackSlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.primary_title) ==
             base + kZhongguoAiCasePrimaryTitleRva &&
         reinterpret_cast<std::uintptr_t>(environment.immediate_liege) ==
             base + kZhongguoAiCaseImmediateLiegeRva &&
         reinterpret_cast<std::uintptr_t>(environment.government) ==
             base + kZhongguoAiCaseGovernmentRva &&
         reinterpret_cast<std::uintptr_t>(environment.is_human_player) ==
             base + kZhongguoAiCaseIsHumanPlayerRva;
}

void *ResolveComponent(const ZhongguoAiOwnedCaseAccessV1 &access,
                       void *const *storage_slot,
                       void *const *fallback_slot, std::int32_t full_id,
                       std::size_t identity_offset) noexcept {
  if (full_id <= 0) return nullptr;
  void *storage = nullptr;
  void *fallback = nullptr;
  if (!ReadSlot(access, storage_slot, storage) ||
      !ReadSlot(access, fallback_slot, fallback) || storage == nullptr) {
    return nullptr;
  }
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadValue(access, storage, kStorageSlotsOffset, slots) ||
      !ReadValue(access, storage, kStorageCapacityOffset, capacity) ||
      slots == nullptr || capacity <= 0 || capacity > kMaximumComponents) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *object = nullptr;
  std::int32_t observed = -1;
  if (!ReadValue(access, slots,
                 static_cast<std::size_t>(index) * kStorageSlotStride +
                     kStorageObjectOffset,
                 object) ||
      object == nullptr || object == fallback ||
      !ReadValue(access, object, identity_offset, observed) ||
      observed != full_id) {
    return nullptr;
  }
  return object;
}

bool InvokeCharacterResolver(NativeZhongguoAiCaseCharacterResolverV1 resolver,
                             void *character, void *&output) noexcept {
  output = nullptr;
#if defined(_MSC_VER)
  __try {
    output = resolver(character);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = resolver(character);
  return true;
#endif
}

bool InvokeIsHuman(NativeZhongguoAiCaseIsHumanPlayerV1 resolver,
                   std::int32_t character_id, bool &output) noexcept {
  output = false;
#if defined(_MSC_VER)
  __try {
    output = resolver(character_id);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  output = resolver(character_id);
  return true;
#endif
}

std::string_view TierKey(std::int32_t raw) noexcept {
  switch (raw) {
  case 1: return "barony";
  case 2: return "county";
  case 3: return "duchy";
  case 4: return "kingdom";
  case 5: return "empire";
  case 6: return "hegemony";
  default: return {};
  }
}

bool ObserveOwnerEligibilityNative(
    const ZhongguoAiOwnedCaseNativeEnvironmentV1 &environment,
    const ZhongguoAiOwnedCaseAccessV1 &access, std::int32_t owner_id,
    std::int32_t subject_id,
    ZhongguoAiOwnerEligibilityObservationV1 &output) noexcept {
  output = {};
  void *const owner = ResolveComponent(
      access, environment.variables.character_storage_slot,
      environment.variables.character_fallback_slot, owner_id,
      kCharacterIdentityOffset);
  void *const subject = ResolveComponent(
      access, environment.variables.character_storage_slot,
      environment.variables.character_fallback_slot, subject_id,
      kCharacterIdentityOffset);
  if (owner == nullptr || subject == nullptr) return false;
  output.owner_character_id = owner_id;
  void *death = nullptr;
  bool human = false;
  if (!ReadValue(access, owner, kCharacterDeathMarkerOffset, death) ||
      !InvokeIsHuman(environment.is_human_player, owner_id, human)) {
    return false;
  }
  output.owner_alive = death == nullptr;
  // Match the exact compiled is_ai evaluator: a dead character is classified
  // as AI, while this provider applies living/in-office as a separate gate.
  output.owner_is_ai = output.owner_alive ? !human : true;

  void *title = nullptr;
  void *title_fallback = nullptr;
  if (!ReadSlot(access, environment.landed_title_fallback_slot,
                title_fallback) ||
      !InvokeCharacterResolver(environment.primary_title, owner, title)) {
    return false;
  }
  if (title != nullptr && title != title_fallback) {
    void *title_template = nullptr;
    if (!ReadValue(access, title, kTitleIdentityOffset,
                   output.primary_title_id) ||
        ResolveComponent(access, environment.landed_title_storage_slot,
                         environment.landed_title_fallback_slot,
                         output.primary_title_id, kTitleIdentityOffset) !=
            title ||
        !ReadValue(access, title, kTitleTemplateOffset, title_template) ||
        title_template == nullptr ||
        !ReadValue(access, title_template, kTitleTierOffset,
                   output.primary_title_tier_raw)) {
      return false;
    }
    const auto key = TierKey(output.primary_title_tier_raw);
    if (key.empty()) return false;
    output.primary_title_tier_key.assign(key);
  }

  void *government = nullptr;
  void *government_fallback = nullptr;
  if (!ReadSlot(access, environment.government_fallback_slot,
                government_fallback) ||
      !InvokeCharacterResolver(environment.government, owner, government)) {
    return false;
  }
  if (government != nullptr && government != government_fallback) {
    const void *key_address = nullptr;
    if (!CheckedAddress(government, kGovernmentKeyOffset, key_address) ||
        !ReadNativeString(access, key_address, output.government_key)) {
      return false;
    }
  }

  void *liege = nullptr;
  void *character_fallback = nullptr;
  if (!ReadSlot(access, environment.variables.character_fallback_slot,
                character_fallback) ||
      !InvokeCharacterResolver(environment.immediate_liege, subject, liege)) {
    return false;
  }
  if (liege != nullptr && liege != character_fallback && liege != subject) {
    if (!ReadValue(access, liege, kCharacterIdentityOffset,
                   output.subject_immediate_liege_character_id) ||
        ResolveComponent(access, environment.variables.character_storage_slot,
                         environment.variables.character_fallback_slot,
                         output.subject_immediate_liege_character_id,
                         kCharacterIdentityOffset) != liege) {
      return false;
    }
  }
  return true;
}

bool ObserveOwnerEligibility(
    const ZhongguoAiOwnedCaseNativeEnvironmentV1 &environment,
    const ZhongguoAiOwnedCaseAccessV1 &access, std::int32_t owner_id,
    std::int32_t subject_id,
    ZhongguoAiOwnerEligibilityObservationV1 &output) noexcept {
  if (environment.variables.offline_fixture_function_overrides) {
    return access.observe_owner_eligibility != nullptr &&
           access.observe_owner_eligibility(access.variables.context,
                                             owner_id, subject_id, output);
  }
  return ObserveOwnerEligibilityNative(environment, access, owner_id,
                                       subject_id, output);
}

bool ResolveVariableIdentifier(
    const ZhongguoCaseNativeEnvironmentV1 &environment, std::string_view key,
    std::int32_t &identifier) noexcept {
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

bool FindVariableValue(const ZhongguoAiOwnedCaseAccessV1 &access,
                       void *context, std::int32_t identifier,
                       ZhongguoRawVariableV1 &output) noexcept {
  output = {};
  void *data = nullptr;
  std::int32_t count = 0;
  if (context == nullptr || !ReadValue(access, context, 0x10, data) ||
      !ReadValue(access, context, 0x1C, count) || count < 0 ||
      count > kMaximumVariableRows || (count != 0 && data == nullptr)) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const void *row = nullptr;
    std::int32_t row_identifier = -1;
    if (!CheckedAddress(data, static_cast<std::size_t>(index) * 0x20, row) ||
        !ReadValue(access, row, 0x08, row_identifier)) {
      return false;
    }
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
    const ZhongguoAiOwnedCaseNativeEnvironmentV1 &environment,
    const ZhongguoAiOwnedCaseAccessV1 &access, std::int32_t subject_id,
    std::string_view key, ZhongguoRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment.variables, key, identifier)) {
    return false;
  }
  const ZhongguoEventTarget16V1 target{4, {}, subject_id};
  void *const context =
      environment.variables.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

bool ReadAllowlistedRows(
    const ZhongguoAiOwnedCaseNativeEnvironmentV1 &environment,
    const ZhongguoAiOwnedCaseAccessV1 &access, std::int32_t subject_id,
    RawRows &output) noexcept {
  for (std::size_t index = 0;
       index < kZhongguoAiOwnedCaseSnapshotV1VariableAllowlist.size();
       ++index) {
    const auto key = kZhongguoAiOwnedCaseSnapshotV1VariableAllowlist[index];
    const bool read = environment.variables.offline_fixture_function_overrides
                          ? access.variables.read_allowlisted_variable !=
                                    nullptr &&
                                access.variables.read_allowlisted_variable(
                                    access.variables.context, subject_id, key,
                                    output[index])
                          : ReadAllowlistedVariableNative(
                                environment, access, subject_id, key,
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
    const ZhongguoAiOwnedCaseNativeEnvironmentV1 &environment,
    const ZhongguoAiOwnedCaseAccessV1 &access,
    const ZhongguoRawVariableV1 &raw, game::ZhongguoTypedIntegerV1 &field) {
  if (!raw.present) {
    SetUnavailable(field, "variable_absent");
  } else if (raw.kind != 4) {
    SetUnavailable(field, "value_type_mismatch");
  } else if (raw.payload <= 0 ||
             raw.payload > std::numeric_limits<std::int32_t>::max() ||
             (environment.variables.offline_fixture_function_overrides
                  ? access.variables.validate_character == nullptr ||
                        !access.variables.validate_character(
                            access.variables.context,
                            static_cast<std::int32_t>(raw.payload))
                  : ResolveComponent(
                        access,
                        environment.variables.character_storage_slot,
                        environment.variables.character_fallback_slot,
                        static_cast<std::int32_t>(raw.payload),
                        kCharacterIdentityOffset) == nullptr)) {
    SetUnavailable(field, "value_out_of_range");
  } else {
    SetAvailable(field, raw.payload);
  }
}

bool IntegerEquals(const game::ZhongguoTypedIntegerV1 &field,
                   std::int64_t expected) noexcept {
  return field.available && field.value.has_value() &&
         *field.value == expected;
}

std::string_view StageKey(std::int64_t state) noexcept {
  switch (state) {
  case 1: return "targets_open";
  case 2: return "midcycle_open";
  case 3: return "evidence_open";
  case 4: return "facts_frozen";
  case 5: return "shadow_open";
  case 6: return "quota_ready";
  case 7: return "calibration_open";
  case 8: return "published";
  default: return {};
  }
}

template <typename Value>
void Wipe(game::ZhongguoTypedValueV1<Value> &field,
          std::string_view reason) {
  SetUnavailable(field, reason);
}

void WipeEligibility(game::ZhongguoAiOwnerEligibilityV1 &value,
                     std::string_view reason) {
  Wipe(value.owner_character_id, reason);
  Wipe(value.owner_alive, reason);
  Wipe(value.owner_is_ai, reason);
  Wipe(value.primary_title_id, reason);
  Wipe(value.primary_title_tier_raw, reason);
  Wipe(value.primary_title_tier_key, reason);
  Wipe(value.government_key, reason);
  Wipe(value.subject_immediate_liege_character_id, reason);
  Wipe(value.subject_is_direct_subject, reason);
  Wipe(value.authorized, reason);
}

void WipeIdentity(game::ZhongguoCaseIdentityV1 &value,
                  std::string_view reason) {
  Wipe(value.owner_character_id, reason);
  Wipe(value.subject_character_id, reason);
  Wipe(value.cycle_serial, reason);
  Wipe(value.case_serial, reason);
  Wipe(value.state, reason);
  Wipe(value.active, reason);
  Wipe(value.revision, reason);
  Wipe(value.timeline_serial, reason);
  Wipe(value.feedback_revision, reason);
}

void WipeStage(game::ZhongguoAiOwnedCaseStageV1 &value,
               std::string_view reason) {
  Wipe(value.state, reason);
  Wipe(value.key, reason);
  Wipe(value.active, reason);
}

void WipeRoute(game::ZhongguoAiOwnedCaseRouteV1 &value,
               std::string_view reason) {
  Wipe(value.kind, reason);
  Wipe(value.visible_event_allowed, reason);
  Wipe(value.owner_is_ai, reason);
  Wipe(value.manager_eligible, reason);
  Wipe(value.direct_subject_eligible, reason);
}

void WipePolicy(game::ZhongguoCasePolicyV1 &value,
                std::string_view reason) {
  Wipe(value.policy_id, reason);
  Wipe(value.choice, reason);
}

void WipeOperation(game::ZhongguoCaseOperationV1 &value,
                   std::string_view reason) {
  Wipe(value.operation_id, reason);
  Wipe(value.operation_key, reason);
  Wipe(value.hook, reason);
  Wipe(value.pre_state, reason);
  Wipe(value.post_state, reason);
}

void WipeReceipt(game::ZhongguoCaseReceiptV1 &value,
                 std::string_view reason) {
  value.status = game::ZhongguoReceiptStatusV1::unavailable;
  Wipe(value.key, reason);
  Wipe(value.owner_character_id, reason);
  Wipe(value.subject_character_id, reason);
  Wipe(value.cycle_serial, reason);
  Wipe(value.case_serial, reason);
  Wipe(value.state, reason);
  Wipe(value.choice, reason);
}

void WipeSemantics(game::ZhongguoAiOwnedCaseSnapshotV1 &output,
                   std::string_view reason) {
  WipeEligibility(output.owner_eligibility, reason);
  WipeIdentity(output.case_identity, reason);
  WipeStage(output.stage, reason);
  WipeRoute(output.route, reason);
  WipePolicy(output.policy, reason);
  WipeOperation(output.operation, reason);
  WipeReceipt(output.receipt, reason);
  output.readiness = {};
}

void InitializeEnvelope(const ZhongguoAiOwnedCaseSnapshotRequestV1 &request,
                        const game::ZhongguoCaseFrameV1 *frame,
                        game::ZhongguoAiOwnedCaseSnapshotV1 &output) {
  output = {};
  output.case_kind.assign(kZhongguoAiOwnedCaseSnapshotV1CaseKind);
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  output.requested_owner_character_id = request.owner_character_id;
  output.subject_character_id = request.subject_character_id;
  if (frame != nullptr) {
    output.snapshot_revision = frame->snapshot_revision;
    output.date_raw = frame->date_raw;
    output.paused = frame->paused;
    output.player_character_id = frame->played_character_id;
  }
  WipeSemantics(output, "case_unavailable");
}

game::ReadZhongguoAiOwnedCaseSnapshotResultV1 SetTopUnavailable(
    game::ZhongguoAiOwnedCaseSnapshotV1 &output,
    std::string_view reason) {
  output.status = game::ZhongguoAiOwnedCaseSnapshotStatusV1::unavailable;
  WipeSemantics(output, "case_unavailable");
  output.unavailable_reason.assign(reason);
  return game::ReadZhongguoAiOwnedCaseSnapshotResultV1::unavailable;
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
    const ZhongguoAiOwnedCaseSnapshotRequestV1 &request) noexcept {
  return request.expected_snapshot_revision > 0 &&
         request.owner_character_id > 0 && request.subject_character_id > 0 &&
         request.owner_character_id != request.subject_character_id &&
         ValidNonce(request.request_nonce);
}

std::string_view EligibilityFailure(
    const ZhongguoAiOwnerEligibilityObservationV1 &value,
    std::int32_t subject_id) noexcept {
  if (!value.owner_alive) return "owner_not_alive";
  if (!value.owner_is_ai) return "owner_not_ai";
  if (value.government_key != "celestial_government") {
    return "owner_not_celestial";
  }
  if (value.primary_title_id <= 0 ||
      value.primary_title_tier_raw < 3 ||
      value.primary_title_tier_raw > 6 ||
      TierKey(value.primary_title_tier_raw) !=
          value.primary_title_tier_key) {
    return "owner_not_landed_duke_plus";
  }
  if (subject_id <= 0 ||
      value.subject_immediate_liege_character_id != value.owner_character_id) {
    return "subject_not_direct_subject";
  }
  return {};
}

void PublishEligibility(
    const ZhongguoAiOwnerEligibilityObservationV1 &source,
    game::ZhongguoAiOwnerEligibilityV1 &output) {
  SetAvailable(output.owner_character_id,
               static_cast<std::int64_t>(source.owner_character_id));
  SetAvailable(output.owner_alive, source.owner_alive);
  SetAvailable(output.owner_is_ai, source.owner_is_ai);
  SetAvailable(output.primary_title_id,
               static_cast<std::int64_t>(source.primary_title_id));
  SetAvailable(output.primary_title_tier_raw,
               static_cast<std::int64_t>(source.primary_title_tier_raw));
  SetAvailable(output.primary_title_tier_key,
               source.primary_title_tier_key);
  SetAvailable(output.government_key, source.government_key);
  SetAvailable(output.subject_immediate_liege_character_id,
               static_cast<std::int64_t>(
                   source.subject_immediate_liege_character_id));
  SetAvailable(output.subject_is_direct_subject, true);
  SetAvailable(output.authorized, true);
}

bool CoreAbsent(const RawRows &rows) noexcept {
  return !rows[case_owner].present && !rows[case_subject].present &&
         !rows[cycle_serial].present && !rows[case_serial].present &&
         !rows[case_state].present && !rows[case_active].present;
}

} // namespace

ZhongguoAiOwnedCaseNativeEnvironmentV1
BindZhongguoAiOwnedCaseNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  ZhongguoAiOwnedCaseNativeEnvironmentV1 output{};
  output.variables =
      BindZhongguoCaseNativeEnvironmentV1(module_base, exact_build_admitted);
  if (module_base == 0 || !exact_build_admitted) return output;
  output.landed_title_storage_slot = reinterpret_cast<void **>(
      module_base + kZhongguoAiCaseLandedTitleStorageSlotRva);
  output.landed_title_fallback_slot = reinterpret_cast<void **>(
      module_base + kZhongguoAiCaseLandedTitleFallbackSlotRva);
  output.government_fallback_slot = reinterpret_cast<void **>(
      module_base + kZhongguoAiCaseGovernmentFallbackSlotRva);
  output.primary_title = reinterpret_cast<
      NativeZhongguoAiCaseCharacterResolverV1>(
      module_base + kZhongguoAiCasePrimaryTitleRva);
  output.immediate_liege = reinterpret_cast<
      NativeZhongguoAiCaseCharacterResolverV1>(
      module_base + kZhongguoAiCaseImmediateLiegeRva);
  output.government = reinterpret_cast<
      NativeZhongguoAiCaseCharacterResolverV1>(
      module_base + kZhongguoAiCaseGovernmentRva);
  output.is_human_player = reinterpret_cast<
      NativeZhongguoAiCaseIsHumanPlayerV1>(
      module_base + kZhongguoAiCaseIsHumanPlayerRva);
  return output;
}

game::ReadZhongguoAiOwnedCaseSnapshotResultV1
ReadZhongguoAiOwnedCaseSnapshotV1(
    const ZhongguoAiOwnedCaseNativeEnvironmentV1 &environment,
    const ZhongguoAiOwnedCaseAccessV1 &access,
    const ZhongguoAiOwnedCaseSnapshotRequestV1 &request,
    game::ZhongguoAiOwnedCaseSnapshotV1 &output) noexcept {
  try {
    InitializeEnvelope(request, nullptr, output);
    if (!ValidRequest(request) || !EnvironmentIsExact(environment)) {
      return SetTopUnavailable(output, "unsupported_build");
    }
    if (access.variables.capture_frame == nullptr ||
        access.variables.is_main_thread == nullptr ||
        !access.variables.is_main_thread(access.variables.context)) {
      return SetTopUnavailable(output, "requires_application_main");
    }
    if (environment.variables.offline_fixture_function_overrides &&
        (access.variables.validate_character == nullptr ||
         access.variables.read_allowlisted_variable == nullptr ||
         access.observe_owner_eligibility == nullptr)) {
      return SetTopUnavailable(output, "internal_error");
    }

    game::ZhongguoCaseFrameV1 before{};
    if (!access.variables.capture_frame(access.variables.context, before)) {
      return SetTopUnavailable(output, "state_changed");
    }
    InitializeEnvelope(request, &before, output);
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      return SetTopUnavailable(output, "state_changed");
    }
    if (!before.paused) return SetTopUnavailable(output, "requires_paused");
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0) {
      return SetTopUnavailable(output, "map_not_ready");
    }
    if (request.owner_character_id == before.played_character_id) {
      return SetTopUnavailable(output, "owner_is_played_character");
    }

    ZhongguoAiOwnerEligibilityObservationV1 first_eligibility{};
    if (!ObserveOwnerEligibility(environment, access,
                                 request.owner_character_id,
                                 request.subject_character_id,
                                 first_eligibility) ||
        first_eligibility.owner_character_id !=
            request.owner_character_id) {
      return SetTopUnavailable(output, "owner_eligibility_unavailable");
    }
    const auto eligibility_failure =
        EligibilityFailure(first_eligibility, request.subject_character_id);
    if (!eligibility_failure.empty()) {
      return SetTopUnavailable(output, eligibility_failure);
    }

    RawRows first_rows{};
    RawRows second_rows{};
    ZhongguoAiOwnerEligibilityObservationV1 second_eligibility{};
    if (!ReadAllowlistedRows(environment, access,
                             request.subject_character_id, first_rows)) {
      return SetTopUnavailable(output, "variable_identifier_unavailable");
    }
    if (!ObserveOwnerEligibility(environment, access,
                                 request.owner_character_id,
                                 request.subject_character_id,
                                 second_eligibility) ||
        !ReadAllowlistedRows(environment, access,
                             request.subject_character_id, second_rows)) {
      return SetTopUnavailable(output, "variable_context_unavailable");
    }
    game::ZhongguoCaseFrameV1 after{};
    if (!access.variables.capture_frame(access.variables.context, after) ||
        before != after || first_rows != second_rows ||
        first_eligibility != second_eligibility) {
      return SetTopUnavailable(output, "state_changed");
    }
    output.readiness.same_frame_ready = true;
    if (CoreAbsent(first_rows)) {
      const auto result = SetTopUnavailable(output, "case_not_found");
      output.readiness.same_frame_ready = true;
      return result;
    }

    PublishEligibility(first_eligibility, output.owner_eligibility);
    output.readiness.owner_eligibility_ready = true;
    SetAvailable(output.route.kind,
                 std::string(kZhongguoAiOwnedCaseBackgroundRouteV1));
    SetAvailable(output.route.visible_event_allowed, false);
    SetAvailable(output.route.owner_is_ai, true);
    SetAvailable(output.route.manager_eligible, true);
    SetAvailable(output.route.direct_subject_eligible, true);
    output.readiness.route_ready = true;

    DecodeCharacter(environment, access, first_rows[case_owner],
                    output.case_identity.owner_character_id);
    DecodeCharacter(environment, access, first_rows[case_subject],
                    output.case_identity.subject_character_id);
    DecodeInteger(first_rows[cycle_serial],
                  output.case_identity.cycle_serial);
    DecodeInteger(first_rows[case_serial], output.case_identity.case_serial);
    DecodeInteger(first_rows[case_state], output.case_identity.state);
    DecodeBoolean(first_rows[case_active], output.case_identity.active);
    DecodeInteger(first_rows[case_revision], output.case_identity.revision);
    DecodeInteger(first_rows[case_timeline],
                  output.case_identity.timeline_serial);
    DecodeInteger(first_rows[case_feedback],
                  output.case_identity.feedback_revision);
    DecodeInteger(first_rows[case_last_operation],
                  output.operation.operation_id);
    DecodeInteger(first_rows[case_last_choice], output.policy.choice);

    const bool identity_ready =
        IntegerEquals(output.case_identity.owner_character_id,
                      request.owner_character_id) &&
        IntegerEquals(output.case_identity.subject_character_id,
                      request.subject_character_id) &&
        output.case_identity.cycle_serial.available &&
        *output.case_identity.cycle_serial.value > 0 &&
        output.case_identity.case_serial.available &&
        *output.case_identity.case_serial.value > 0 &&
        output.case_identity.state.available &&
        output.case_identity.active.available &&
        output.case_identity.revision.available &&
        *output.case_identity.revision.value > 0 &&
        output.case_identity.timeline_serial.available &&
        *output.case_identity.timeline_serial.value > 0 &&
        output.case_identity.feedback_revision.available &&
        *output.case_identity.feedback_revision.value > 0;
    output.readiness.case_identity_ready = identity_ready;
    if (!identity_ready) {
      const auto reason =
          output.case_identity.owner_character_id.available &&
                  !IntegerEquals(output.case_identity.owner_character_id,
                                 request.owner_character_id)
              ? "owner_filter_mismatch"
              : "case_not_found";
      const auto result = SetTopUnavailable(output, reason);
      output.readiness.same_frame_ready = true;
      return result;
    }

    SetAvailable(output.stage.state,
                 *output.case_identity.state.value);
    SetAvailable(output.stage.active,
                 *output.case_identity.active.value);
    const auto stage_key = StageKey(*output.case_identity.state.value);
    const bool stage_active_matches =
        !stage_key.empty() &&
        ((*output.case_identity.state.value < 8 &&
          *output.case_identity.active.value) ||
         (*output.case_identity.state.value == 8 &&
          !*output.case_identity.active.value));
    if (stage_active_matches) {
      SetAvailable(output.stage.key, std::string(stage_key));
      output.readiness.stage_ready = true;
    } else {
      SetUnavailable(output.stage.key, "stage_inconsistent");
    }

    const auto operation_id = output.operation.operation_id.available
                                  ? *output.operation.operation_id.value
                                  : -1;
    if (operation_id == 39 && IntegerEquals(output.policy.choice, 1)) {
      SetAvailable(output.policy.policy_id, std::string("mechanism_039"));
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

    DecodeCharacter(environment, access, first_rows[receipt_owner],
                    output.receipt.owner_character_id);
    DecodeCharacter(environment, access, first_rows[receipt_subject],
                    output.receipt.subject_character_id);
    DecodeInteger(first_rows[receipt_cycle], output.receipt.cycle_serial);
    DecodeInteger(first_rows[receipt_case], output.receipt.case_serial);
    DecodeInteger(first_rows[receipt_state], output.receipt.state);
    DecodeInteger(first_rows[receipt_choice], output.receipt.choice);
    const bool receipt_matches =
        IntegerEquals(output.receipt.owner_character_id,
                      request.owner_character_id) &&
        IntegerEquals(output.receipt.subject_character_id,
                      request.subject_character_id) &&
        IntegerEquals(output.receipt.cycle_serial,
                      *output.case_identity.cycle_serial.value) &&
        IntegerEquals(output.receipt.case_serial,
                      *output.case_identity.case_serial.value) &&
        output.receipt.state.available && *output.receipt.state.value > 0 &&
        IntegerEquals(output.receipt.choice, 1);
    if (operation_id == 0) {
      output.receipt.status = game::ZhongguoReceiptStatusV1::not_recorded;
      WipeReceipt(output.receipt, "receipt_not_recorded");
      output.receipt.status = game::ZhongguoReceiptStatusV1::not_recorded;
      SetUnavailable(output.operation.pre_state, "receipt_not_recorded");
      SetUnavailable(output.operation.post_state, "receipt_not_recorded");
      output.readiness.receipt_ready = true;
    } else if (operation_id == 39 &&
               IntegerEquals(output.policy.choice, 1) && receipt_matches) {
      output.receipt.status = game::ZhongguoReceiptStatusV1::recorded;
      SetAvailable(output.receipt.key, std::string("roster_lock"));
      SetAvailable(output.operation.pre_state,
                   *output.receipt.state.value);
      SetAvailable(output.operation.post_state,
                   *output.receipt.state.value);
      output.readiness.receipt_ready = true;
    } else {
      WipeReceipt(output.receipt, "receipt_inconsistent");
      SetUnavailable(output.operation.pre_state, "receipt_inconsistent");
      SetUnavailable(output.operation.post_state, "receipt_inconsistent");
    }

    output.status = game::ZhongguoAiOwnedCaseSnapshotStatusV1::available;
    output.unavailable_reason.clear();
    output.readiness.ready = output.readiness.owner_eligibility_ready &&
                             output.readiness.case_identity_ready &&
                             output.readiness.stage_ready &&
                             output.readiness.route_ready &&
                             output.readiness.receipt_ready &&
                             output.readiness.same_frame_ready;
    return game::ReadZhongguoAiOwnedCaseSnapshotResultV1::available;
  } catch (...) {
    InitializeEnvelope(request, nullptr, output);
    return SetTopUnavailable(output, "internal_error");
  }
}

} // namespace xar::ck3_11906
