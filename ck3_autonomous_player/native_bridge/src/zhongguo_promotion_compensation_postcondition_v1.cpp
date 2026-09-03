#include "xar_bridge/zhongguo_promotion_compensation_postcondition_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <limits>
#include <sstream>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using Raw = ZhongguoPromotionCompensationRawVariableV1;
using OwnerRows = std::array<
    Raw, kZhongguoPromotionCompensationOwnerVariableAllowlist.size()>;
using SubjectRows = std::array<
    Raw, kZhongguoPromotionCompensationSubjectBaseVariableAllowlist.size()>;
using ReceiptRows = std::array<Raw, 8>;

constexpr std::int64_t kFixedScale = 100'000;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::int32_t kMaximumComponents = 4'194'304;
constexpr std::int32_t kMaximumVariableRows = 65'536;

enum OwnerIndex : std::size_t {
  portfolio_domain = 0,
  portfolio_subject,
  result_owner,
  result_subject,
  result_cycle,
  result_case,
  result_snapshot_applied,
};

enum SubjectIndex : std::size_t {
  choice_active = 0,
  choice_consumed,
  choice_owner,
  choice_subject,
  choice_cycle,
  choice_case,
  choice_route,
  choice_consumer_revision,
  choice_serial,
  choice_receipt_revision,
  posted_active,
  posted_flag,
  posted_owner,
  posted_subject,
  posted_cycle,
  posted_case,
  posted_choice_serial,
  posted_serial,
  posted_choice_revision,
  posted_revision,
  posted_operation,
  posted_route,
  l_owner,
  l_subject,
  l_cycle,
  l_case,
  l_revision,
  l_last_operation,
  l_last_route,
  l_active,
  ae_owner,
  ae_subject,
  ae_cycle,
  ae_case,
  ae_revision,
  ae_last_operation,
  ae_last_route,
  ae_active,
  af_owner,
  af_subject,
  af_cycle,
  af_case,
  af_revision,
  af_last_operation,
  af_last_route,
  af_active,
};

enum ReceiptIndex : std::size_t {
  receipt_active = 0,
  receipt_consumed,
  receipt_owner,
  receipt_subject,
  receipt_cycle,
  receipt_case,
  receipt_route,
  numbered_receipt_revision,
};

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

bool ReadBytes(const ZhongguoPromotionCompensationAccessV1 &access,
               const void *address, void *output, std::size_t size) noexcept {
  return access.read_memory != nullptr
             ? access.read_memory(access.context, address, output, size)
             : GuardedDirectRead(address, output, size);
}

template <typename Value>
bool ReadValue(const ZhongguoPromotionCompensationAccessV1 &access,
               const void *base, std::size_t offset, Value &output) noexcept {
  if (base == nullptr ||
      offset > std::numeric_limits<std::uintptr_t>::max() -
                   reinterpret_cast<std::uintptr_t>(base)) {
    return false;
  }
  const auto *address = reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(base) + offset);
  return ReadBytes(access, address, &output, sizeof(output));
}

bool EnvironmentIsExact(
    const ZhongguoPromotionCompensationNativeEnvironmentV1 &environment) {
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

bool ResolveVariableIdentifier(
    const ZhongguoPromotionCompensationNativeEnvironmentV1 &environment,
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

bool FindVariableValue(const ZhongguoPromotionCompensationAccessV1 &access,
                       void *context, std::int32_t identifier,
                       Raw &output) noexcept {
  output = {};
  if (context == nullptr) return false;
  void *data = nullptr;
  std::int32_t count = 0;
  if (!ReadValue(access, context, 0x10, data) ||
      !ReadValue(access, context, 0x18, count) || data == nullptr || count < 0 ||
      count > kMaximumVariableRows) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    std::int32_t row_identifier = -1;
    ZhongguoEventTarget16V1 target{};
    const auto offset = static_cast<std::size_t>(index) * 0x18;
    if (!ReadValue(access, data, offset, row_identifier) ||
        !ReadValue(access, data, offset + 0x08, target)) {
      return false;
    }
    if (row_identifier != identifier) continue;
    output.present = true;
    output.kind = target.kind;
    output.payload = target.payload;
    return true;
  }
  return true;
}

bool ReadAllowlistedVariableNative(
    const ZhongguoPromotionCompensationNativeEnvironmentV1 &environment,
    const ZhongguoPromotionCompensationAccessV1 &access,
    std::int32_t character_id, std::string_view key, Raw &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) return false;
  const ZhongguoEventTarget16V1 character_scope{
      4, {}, static_cast<std::int64_t>(character_id)};
  void *const context = environment.variable_context_for_scope(&character_scope);
  return FindVariableValue(access, context, identifier, output);
}

bool ReadAllowlistedVariable(
    const ZhongguoPromotionCompensationNativeEnvironmentV1 &environment,
    const ZhongguoPromotionCompensationAccessV1 &access,
    std::int32_t character_id, std::string_view key, Raw &output) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.read_allowlisted_variable != nullptr &&
           access.read_allowlisted_variable(access.context, character_id, key,
                                            output);
  }
  return ReadAllowlistedVariableNative(environment, access, character_id, key,
                                       output);
}

bool ResolveCharacterNative(
    const ZhongguoPromotionCompensationNativeEnvironmentV1 &environment,
    const ZhongguoPromotionCompensationAccessV1 &access,
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
    const ZhongguoPromotionCompensationNativeEnvironmentV1 &environment,
    const ZhongguoPromotionCompensationAccessV1 &access,
    std::int32_t character_id) noexcept {
  return environment.offline_fixture_function_overrides
             ? access.validate_character != nullptr &&
                   access.validate_character(access.context, character_id)
             : ResolveCharacterNative(environment, access, character_id);
}

template <std::size_t Count>
bool ReadRows(
    const ZhongguoPromotionCompensationNativeEnvironmentV1 &environment,
    const ZhongguoPromotionCompensationAccessV1 &access,
    std::int32_t character_id,
    const std::array<std::string_view, Count> &keys,
    std::array<Raw, Count> &rows) noexcept {
  for (std::size_t index = 0; index < Count; ++index) {
    if (!ReadAllowlistedVariable(environment, access, character_id, keys[index],
                                 rows[index])) {
      return false;
    }
  }
  return true;
}

bool IsMechanismAllowlisted(std::int64_t value) {
  return std::find(kZhongguoPromotionCompensationMechanismAllowlist.begin(),
                   kZhongguoPromotionCompensationMechanismAllowlist.end(),
                   value) !=
         kZhongguoPromotionCompensationMechanismAllowlist.end();
}

std::array<std::string, 8> ReceiptKeys(std::int64_t operation) {
  std::ostringstream prefix;
  prefix << "zg361_comp_m" << std::setfill('0') << std::setw(3) << operation;
  const auto base = prefix.str();
  return {
      base + "_receipt_active",  base + "_consumed",
      base + "_receipt_owner",   base + "_receipt_subject",
      base + "_receipt_cycle",   base + "_receipt_case",
      base + "_receipt_route",   base + "_visible_revision",
  };
}

bool ReadReceiptRows(
    const ZhongguoPromotionCompensationNativeEnvironmentV1 &environment,
    const ZhongguoPromotionCompensationAccessV1 &access,
    std::int32_t character_id, const std::array<std::string, 8> &keys,
    ReceiptRows &rows) noexcept {
  for (std::size_t index = 0; index < keys.size(); ++index) {
    if (!ReadAllowlistedVariable(environment, access, character_id, keys[index],
                                 rows[index])) {
      return false;
    }
  }
  return true;
}

void Unavailable(game::ZhongguoTypedIntegerV1 &value,
                 std::string_view reason) {
  value = {};
  value.unavailable_reason = std::string(reason);
}

void Unavailable(game::ZhongguoTypedBooleanV1 &value,
                 std::string_view reason) {
  value = {};
  value.unavailable_reason = std::string(reason);
}

bool DecodeNumber(const Raw &raw, game::ZhongguoTypedIntegerV1 &output,
                  bool positive = false) {
  if (!raw.present) {
    Unavailable(output, "variable_absent");
    return false;
  }
  if (raw.kind != 1 || raw.payload % kFixedScale != 0) {
    Unavailable(output, "variable_kind_mismatch");
    return false;
  }
  const auto decoded = raw.payload / kFixedScale;
  if (positive && decoded <= 0) {
    Unavailable(output, "value_not_positive");
    return false;
  }
  output.available = true;
  output.value = decoded;
  output.unavailable_reason.clear();
  return true;
}

bool DecodeCharacter(const Raw &raw, game::ZhongguoTypedIntegerV1 &output) {
  if (!raw.present) {
    Unavailable(output, "variable_absent");
    return false;
  }
  if (raw.kind != 4 || raw.payload <= 0 ||
      raw.payload > std::numeric_limits<std::int32_t>::max()) {
    Unavailable(output, "character_identity_invalid");
    return false;
  }
  output.available = true;
  output.value = raw.payload;
  output.unavailable_reason.clear();
  return true;
}

bool DecodeBool(const Raw &raw, game::ZhongguoTypedBooleanV1 &output) {
  game::ZhongguoTypedIntegerV1 number;
  if (!DecodeNumber(raw, number) || !number.value ||
      (*number.value != 0 && *number.value != 1)) {
    Unavailable(output, number.unavailable_reason.empty()
                            ? "boolean_value_invalid"
                            : number.unavailable_reason);
    return false;
  }
  output.available = true;
  output.value = *number.value == 1;
  output.unavailable_reason.clear();
  return true;
}

bool IdentityReady(
    const game::ZhongguoPromotionCompensationIdentityV1 &identity) {
  const auto positive = [](const game::ZhongguoTypedIntegerV1 &value) {
    return value.available && value.value && *value.value > 0;
  };
  return positive(identity.owner_character_id) &&
         positive(identity.subject_character_id) &&
         positive(identity.cycle_serial) && positive(identity.case_serial) &&
         positive(identity.revision);
}

bool SameIdentity(
    const game::ZhongguoPromotionCompensationIdentityV1 &left,
    const game::ZhongguoPromotionCompensationIdentityV1 &right) {
  return IdentityReady(left) && IdentityReady(right) &&
         left.owner_character_id.value == right.owner_character_id.value &&
         left.subject_character_id.value == right.subject_character_id.value &&
         left.cycle_serial.value == right.cycle_serial.value &&
         left.case_serial.value == right.case_serial.value;
}

void DecodeIdentity(const Raw &owner, const Raw &subject, const Raw &cycle,
                    const Raw &case_serial, const Raw &revision,
                    game::ZhongguoPromotionCompensationIdentityV1 &output) {
  DecodeCharacter(owner, output.owner_character_id);
  DecodeCharacter(subject, output.subject_character_id);
  DecodeNumber(cycle, output.cycle_serial, true);
  DecodeNumber(case_serial, output.case_serial, true);
  DecodeNumber(revision, output.revision, true);
}

std::string JsonEscape(std::string_view value) {
  std::ostringstream out;
  for (const unsigned char ch : value) {
    switch (ch) {
    case '\\': out << "\\\\"; break;
    case '"': out << "\\\""; break;
    case '\n': out << "\\n"; break;
    case '\r': out << "\\r"; break;
    case '\t': out << "\\t"; break;
    default:
      if (ch < 0x20) {
        out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
            << static_cast<int>(ch) << std::dec;
      } else {
        out << static_cast<char>(ch);
      }
    }
  }
  return out.str();
}

std::string TypedIntegerJson(const game::ZhongguoTypedIntegerV1 &value) {
  std::ostringstream out;
  out << "{\"status\":\"" << (value.available ? "available" : "unavailable")
      << "\",\"value\":";
  if (value.available && value.value) out << *value.value;
  else out << "null";
  out << ",\"unavailable_reason\":";
  if (value.unavailable_reason.empty()) out << "null";
  else out << "\"" << JsonEscape(value.unavailable_reason) << "\"";
  out << "}";
  return out.str();
}

std::string TypedBooleanJson(const game::ZhongguoTypedBooleanV1 &value) {
  std::ostringstream out;
  out << "{\"status\":\"" << (value.available ? "available" : "unavailable")
      << "\",\"value\":";
  if (value.available && value.value) out << (*value.value ? "true" : "false");
  else out << "null";
  out << ",\"unavailable_reason\":";
  if (value.unavailable_reason.empty()) out << "null";
  else out << "\"" << JsonEscape(value.unavailable_reason) << "\"";
  out << "}";
  return out.str();
}

std::string IdentityJson(
    const game::ZhongguoPromotionCompensationIdentityV1 &identity) {
  return "{\"owner_character_id\":" +
         TypedIntegerJson(identity.owner_character_id) +
         ",\"subject_character_id\":" +
         TypedIntegerJson(identity.subject_character_id) +
         ",\"cycle_serial\":" + TypedIntegerJson(identity.cycle_serial) +
         ",\"case_serial\":" + TypedIntegerJson(identity.case_serial) +
         ",\"revision\":" + TypedIntegerJson(identity.revision) + "}";
}

} // namespace

ZhongguoPromotionCompensationNativeEnvironmentV1
BindZhongguoPromotionCompensationNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  ZhongguoPromotionCompensationNativeEnvironmentV1 environment{};
  environment.module_base = module_base;
  environment.exact_build_admitted = exact_build_admitted;
  if (module_base == 0 || !exact_build_admitted) return environment;
  environment.variable_context_for_scope =
      reinterpret_cast<NativeZhongguoVariableContextForScopeV1>(
          module_base + kZhongguoVariableContextForScopeRva);
  environment.variable_identifier_table =
      reinterpret_cast<NativeZhongguoGetVariableIdentifierTableV1>(
          module_base + kZhongguoVariableIdentifierTableRva);
  environment.variable_identifier_lookup =
      reinterpret_cast<NativeZhongguoLookupVariableIdentifierV1>(
          module_base + kZhongguoVariableIdentifierLookupRva);
  environment.variable_identifier_name =
      reinterpret_cast<NativeZhongguoVariableIdentifierNameV1>(
          module_base + kZhongguoVariableIdentifierNameRva);
  environment.character_storage_slot = reinterpret_cast<void **>(
      module_base + kZhongguoCharacterStorageSlotRva);
  environment.character_fallback_slot = reinterpret_cast<void **>(
      module_base + kZhongguoCharacterFallbackSlotRva);
  return environment;
}

game::ReadZhongguoPromotionCompensationResultV1
ReadZhongguoPromotionCompensationPostconditionV1(
    const ZhongguoPromotionCompensationNativeEnvironmentV1 &environment,
    const ZhongguoPromotionCompensationAccessV1 &access,
    const ZhongguoPromotionCompensationRequestV1 &request,
    game::ZhongguoPromotionCompensationPostconditionV1 &output) noexcept {
  output = {};
  output.request_nonce = request.request_nonce;
  const auto fail = [&](std::string_view reason) {
    output.status =
        game::ZhongguoPromotionCompensationStatusV1::unavailable;
    output.unavailable_reason = std::string(reason);
    return game::ReadZhongguoPromotionCompensationResultV1::unavailable;
  };
  if (request.request_nonce.empty()) return fail("request_nonce_missing");
  if (!EnvironmentIsExact(environment)) return fail("exact_build_not_admitted");
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      !access.is_main_thread(access.context)) {
    return fail("application_main_thread_required");
  }

  ZhongguoPromotionCompensationFrameV1 before{};
  if (!access.capture_frame(access.context, before))
    return fail("frame_capture_failed");
  if (before.snapshot_revision != request.expected_snapshot_revision)
    return fail("revision_mismatch");
  if (!before.paused) return fail("game_not_paused");
  if (!before.map_ready || !before.has_played_character ||
      !before.played_character_alive || before.played_character_id <= 0)
    return fail("played_character_unavailable");
  if (!ValidateCharacter(environment, access, before.played_character_id))
    return fail("played_character_invalid");

  OwnerRows owner_first{};
  OwnerRows owner_second{};
  if (!ReadRows(environment, access, before.played_character_id,
                kZhongguoPromotionCompensationOwnerVariableAllowlist,
                owner_first)) {
    return fail("owner_projection_read_failed");
  }
  game::ZhongguoTypedIntegerV1 subject_value;
  if (!DecodeCharacter(owner_first[portfolio_subject], subject_value) ||
      !subject_value.value ||
      *subject_value.value > std::numeric_limits<std::int32_t>::max()) {
    return fail("portfolio_subject_unavailable");
  }
  const auto subject_id = static_cast<std::int32_t>(*subject_value.value);
  if (subject_id == before.played_character_id)
    return fail("portfolio_subject_is_player");
  if (!ValidateCharacter(environment, access, subject_id))
    return fail("portfolio_subject_invalid");

  SubjectRows subject_first{};
  SubjectRows subject_second{};
  if (!ReadRows(environment, access, subject_id,
                kZhongguoPromotionCompensationSubjectBaseVariableAllowlist,
                subject_first)) {
    return fail("subject_projection_read_failed");
  }
  game::ZhongguoTypedIntegerV1 domain_value;
  if (!DecodeNumber(owner_first[portfolio_domain], domain_value, true) ||
      !domain_value.value || *domain_value.value > 3) {
    return fail("portfolio_domain_unavailable");
  }
  const auto domain = static_cast<std::size_t>(*domain_value.value - 1);
  const auto base = static_cast<std::size_t>(l_owner) + domain * 8;
  game::ZhongguoTypedIntegerV1 operation_value;
  if (!DecodeNumber(subject_first[base + 5], operation_value, true) ||
      !operation_value.value || !IsMechanismAllowlisted(*operation_value.value)) {
    return fail("compensation_operation_unavailable");
  }
  const auto receipt_keys = ReceiptKeys(*operation_value.value);
  ReceiptRows receipt_first{};
  ReceiptRows receipt_second{};
  if (!ReadReceiptRows(environment, access, subject_id, receipt_keys,
                       receipt_first)) {
    return fail("compensation_receipt_read_failed");
  }
  if (!ReadRows(environment, access, before.played_character_id,
                kZhongguoPromotionCompensationOwnerVariableAllowlist,
                owner_second) ||
      !ReadRows(environment, access, subject_id,
                kZhongguoPromotionCompensationSubjectBaseVariableAllowlist,
                subject_second) ||
      !ReadReceiptRows(environment, access, subject_id, receipt_keys,
                       receipt_second)) {
    return fail("second_projection_read_failed");
  }
  ZhongguoPromotionCompensationFrameV1 after{};
  if (!access.capture_frame(access.context, after))
    return fail("frame_capture_failed");
  if (!(before == after) || owner_first != owner_second ||
      subject_first != subject_second || receipt_first != receipt_second) {
    return fail("state_changed");
  }

  output.status = game::ZhongguoPromotionCompensationStatusV1::available;
  output.snapshot_revision = before.snapshot_revision;
  output.date_raw = before.date_raw;
  output.paused = before.paused;
  output.player_character_id = before.played_character_id;
  output.subject_character_id = subject_id;
  output.portfolio_domain = domain_value;

  // #147's generic receipt_case remains the internal T kernel ticket.  The
  // new positive serial is the immutable delivered-result case shared with
  // the visible compensation portfolio and is therefore the business case.
  DecodeIdentity(subject_first[choice_owner], subject_first[choice_subject],
                 subject_first[choice_cycle], subject_first[choice_serial],
                 subject_first[choice_receipt_revision],
                 output.source_identity);
  output.promotion_choice.identity = output.source_identity;
  DecodeNumber(subject_first[choice_route],
               output.promotion_choice.option_number, true);
  DecodeBool(subject_first[choice_active], output.promotion_choice.active);
  DecodeBool(subject_first[choice_consumed], output.promotion_choice.consumed);
  DecodeNumber(subject_first[choice_serial],
               output.promotion_choice.receipt_serial, true);
  game::ZhongguoTypedIntegerV1 choice_consumer_revision_value;
  DecodeNumber(subject_first[choice_consumer_revision],
               choice_consumer_revision_value, true);

  DecodeIdentity(subject_first[posted_owner], subject_first[posted_subject],
                 subject_first[posted_cycle], subject_first[posted_case],
                 subject_first[posted_revision], output.result_identity);
  output.frozen_case = output.result_identity;
  DecodeIdentity(subject_first[posted_owner], subject_first[posted_subject],
                 subject_first[posted_cycle], subject_first[posted_case],
                 subject_first[posted_revision],
                 output.compensation_receipt.identity);
  DecodeNumber(subject_first[posted_operation],
               output.compensation_receipt.operation_id, true);
  DecodeNumber(subject_first[posted_route],
               output.compensation_receipt.option_number, true);
  DecodeNumber(subject_first[posted_serial],
               output.compensation_receipt.receipt_serial, true);
  DecodeBool(subject_first[posted_active],
             output.compensation_receipt.active);
  DecodeBool(receipt_first[receipt_consumed],
             output.compensation_receipt.consumed);
  DecodeBool(subject_first[posted_flag], output.compensation_receipt.posted);

  game::ZhongguoPromotionCompensationIdentityV1 numbered_case;
  DecodeIdentity(subject_first[base], subject_first[base + 1],
                 subject_first[base + 2], subject_first[base + 3],
                 subject_first[base + 4], numbered_case);
  game::ZhongguoPromotionCompensationIdentityV1 numbered_receipt_identity;
  DecodeIdentity(receipt_first[receipt_owner], receipt_first[receipt_subject],
                 receipt_first[receipt_cycle], receipt_first[receipt_case],
                 receipt_first[numbered_receipt_revision],
                 numbered_receipt_identity);
  game::ZhongguoTypedIntegerV1 numbered_option;
  DecodeNumber(receipt_first[receipt_route], numbered_option, true);
  const bool numbered_receipt_matches_case =
      SameIdentity(numbered_case, numbered_receipt_identity) &&
      numbered_case.revision.value == numbered_receipt_identity.revision.value;
  game::ZhongguoPromotionCompensationIdentityV1 portfolio_identity;
  DecodeIdentity(owner_first[result_owner], owner_first[result_subject],
                 owner_first[result_cycle], owner_first[result_case],
                 subject_first[posted_revision], portfolio_identity);
  game::ZhongguoTypedIntegerV1 posted_choice_revision_value;
  DecodeNumber(subject_first[posted_choice_revision],
               posted_choice_revision_value, true);
  const bool posted = output.compensation_receipt.active.available &&
                      output.compensation_receipt.active.value &&
                      *output.compensation_receipt.active.value &&
                      output.compensation_receipt.consumed.available &&
                      output.compensation_receipt.consumed.value &&
                      *output.compensation_receipt.consumed.value &&
                      output.compensation_receipt.posted.available &&
                      output.compensation_receipt.posted.value &&
                      *output.compensation_receipt.posted.value &&
                      numbered_receipt_matches_case &&
                      operation_value.value ==
                          output.compensation_receipt.operation_id.value &&
                      numbered_option.value ==
                          output.compensation_receipt.option_number.value &&
                      output.compensation_receipt.option_number.available &&
                      output.compensation_receipt.option_number.value &&
                      *output.compensation_receipt.option_number.value > 0;
  auto &ready = output.readiness;
  ready.player_owner_binding_ready =
      output.frozen_case.owner_character_id.available &&
      output.frozen_case.owner_character_id.value &&
      *output.frozen_case.owner_character_id.value == before.played_character_id;
  game::ZhongguoTypedBooleanV1 result_applied;
  DecodeBool(owner_first[result_snapshot_applied], result_applied);
  ready.portfolio_subject_binding_ready =
      output.frozen_case.subject_character_id.available &&
      output.frozen_case.subject_character_id.value &&
      *output.frozen_case.subject_character_id.value == subject_id &&
      output.result_identity.owner_character_id.available &&
      output.result_identity.owner_character_id.value &&
      *output.result_identity.owner_character_id.value ==
          before.played_character_id &&
      output.result_identity.subject_character_id.available &&
      output.result_identity.subject_character_id.value &&
      *output.result_identity.subject_character_id.value == subject_id &&
      output.result_identity.owner_character_id.value ==
          output.source_identity.owner_character_id.value &&
      output.result_identity.subject_character_id.value ==
          output.source_identity.subject_character_id.value &&
      output.result_identity.cycle_serial.value ==
          output.source_identity.cycle_serial.value &&
      output.result_identity.case_serial.value ==
          output.source_identity.case_serial.value &&
      SameIdentity(output.result_identity, portfolio_identity) &&
      result_applied.available && result_applied.value &&
      *result_applied.value;
  ready.source_identity_ready = IdentityReady(output.source_identity);
  ready.result_identity_ready = IdentityReady(output.result_identity);
  ready.frozen_case_identity_ready = IdentityReady(output.frozen_case);
  ready.promotion_choice_receipt_ready =
      ready.source_identity_ready && output.promotion_choice.active.available &&
      output.promotion_choice.active.value &&
      *output.promotion_choice.active.value &&
      output.promotion_choice.consumed.available &&
      output.promotion_choice.consumed.value &&
      *output.promotion_choice.consumed.value &&
      output.promotion_choice.option_number.available &&
      output.promotion_choice.receipt_serial.available &&
      choice_consumer_revision_value.available &&
      output.source_identity.revision.value ==
          choice_consumer_revision_value.value;
  ready.compensation_receipt_posted = posted;
  ready.same_case_identity_ready =
      SameIdentity(output.source_identity, output.result_identity) &&
      SameIdentity(output.source_identity, output.frozen_case) &&
      SameIdentity(output.source_identity,
                   output.compensation_receipt.identity);
  ready.revision_binding_ready =
      ready.source_identity_ready && ready.result_identity_ready &&
      ready.frozen_case_identity_ready &&
      IdentityReady(output.compensation_receipt.identity) &&
      output.result_identity.revision.value == output.frozen_case.revision.value &&
      output.result_identity.revision.value ==
          output.compensation_receipt.identity.revision.value &&
      output.source_identity.revision.value ==
          posted_choice_revision_value.value &&
      *output.result_identity.revision.value >
          *output.source_identity.revision.value;
  game::ZhongguoTypedIntegerV1 posted_choice_serial_value;
  DecodeNumber(subject_first[posted_choice_serial], posted_choice_serial_value,
               true);
  ready.receipt_serials_ready =
      output.promotion_choice.receipt_serial.available &&
      output.compensation_receipt.receipt_serial.available &&
      posted_choice_serial_value.available &&
      output.promotion_choice.receipt_serial.value ==
          output.compensation_receipt.receipt_serial.value &&
      output.promotion_choice.receipt_serial.value ==
          posted_choice_serial_value.value;
  ready.same_frame_ready = true;
  ready.ready = ready.player_owner_binding_ready &&
                ready.portfolio_subject_binding_ready &&
                ready.source_identity_ready && ready.result_identity_ready &&
                ready.frozen_case_identity_ready &&
                ready.promotion_choice_receipt_ready &&
                ready.compensation_receipt_posted &&
                ready.same_case_identity_ready &&
                ready.revision_binding_ready && ready.receipt_serials_ready &&
                ready.same_frame_ready;
  output.unavailable_reason =
      ready.ready ? "" : "business_postcondition_not_fully_observable";
  return game::ReadZhongguoPromotionCompensationResultV1::available;
}

std::string SerializeZhongguoPromotionCompensationPostconditionV1(
    const game::ZhongguoPromotionCompensationPostconditionV1 &snapshot) {
  const auto bool_text = [](bool value) { return value ? "true" : "false"; };
  std::ostringstream out;
  out << "{\"schema_version\":1,\"status\":\""
      << (snapshot.status ==
                  game::ZhongguoPromotionCompensationStatusV1::available
              ? "available"
              : "unavailable")
      << "\",\"capability\":\""
      << kZhongguoPromotionCompensationPostconditionV1Capability
      << "\",\"source_backend_id\":\""
      << kZhongguoPromotionCompensationPostconditionV1BackendId
      << "\",\"request_nonce\":\"" << JsonEscape(snapshot.request_nonce)
      << "\",\"snapshot_revision\":" << snapshot.snapshot_revision
      << ",\"date_raw\":" << snapshot.date_raw
      << ",\"paused\":" << bool_text(snapshot.paused)
      << ",\"player_character_id\":" << snapshot.player_character_id
      << ",\"subject_character_id\":" << snapshot.subject_character_id
      << ",\"promotion_compensation\":{\"source_identity\":"
      << IdentityJson(snapshot.source_identity)
      << ",\"result_identity\":" << IdentityJson(snapshot.result_identity)
      << ",\"frozen_case\":{\"identity\":"
      << IdentityJson(snapshot.frozen_case) << ",\"frozen\":true}"
      << ",\"promotion_choice\":{\"identity\":"
      << IdentityJson(snapshot.promotion_choice.identity)
      << ",\"option_number\":"
      << TypedIntegerJson(snapshot.promotion_choice.option_number)
      << ",\"receipt_serial\":"
      << TypedIntegerJson(snapshot.promotion_choice.receipt_serial)
      << ",\"active\":" << TypedBooleanJson(snapshot.promotion_choice.active)
      << ",\"consumed\":"
      << TypedBooleanJson(snapshot.promotion_choice.consumed) << "}"
      << ",\"compensation_receipt\":{\"identity\":"
      << IdentityJson(snapshot.compensation_receipt.identity)
      << ",\"operation_id\":"
      << TypedIntegerJson(snapshot.compensation_receipt.operation_id)
      << ",\"option_number\":"
      << TypedIntegerJson(snapshot.compensation_receipt.option_number)
      << ",\"receipt_serial\":"
      << TypedIntegerJson(snapshot.compensation_receipt.receipt_serial)
      << ",\"active\":"
      << TypedBooleanJson(snapshot.compensation_receipt.active)
      << ",\"consumed\":"
      << TypedBooleanJson(snapshot.compensation_receipt.consumed)
      << ",\"posted\":"
      << TypedBooleanJson(snapshot.compensation_receipt.posted) << "}}"
      << ",\"readiness\":{\"player_owner_binding_ready\":"
      << bool_text(snapshot.readiness.player_owner_binding_ready)
      << ",\"portfolio_subject_binding_ready\":"
      << bool_text(snapshot.readiness.portfolio_subject_binding_ready)
      << ",\"source_identity_ready\":"
      << bool_text(snapshot.readiness.source_identity_ready)
      << ",\"result_identity_ready\":"
      << bool_text(snapshot.readiness.result_identity_ready)
      << ",\"frozen_case_identity_ready\":"
      << bool_text(snapshot.readiness.frozen_case_identity_ready)
      << ",\"promotion_choice_receipt_ready\":"
      << bool_text(snapshot.readiness.promotion_choice_receipt_ready)
      << ",\"compensation_receipt_posted\":"
      << bool_text(snapshot.readiness.compensation_receipt_posted)
      << ",\"same_case_identity_ready\":"
      << bool_text(snapshot.readiness.same_case_identity_ready)
      << ",\"revision_binding_ready\":"
      << bool_text(snapshot.readiness.revision_binding_ready)
      << ",\"receipt_serials_ready\":"
      << bool_text(snapshot.readiness.receipt_serials_ready)
      << ",\"same_frame_ready\":"
      << bool_text(snapshot.readiness.same_frame_ready)
      << ",\"ready\":" << bool_text(snapshot.readiness.ready) << "}"
      << ",\"unavailable_reason\":";
  if (snapshot.unavailable_reason.empty()) out << "null";
  else out << "\"" << JsonEscape(snapshot.unavailable_reason) << "\"";
  out << "}";
  return out.str();
}

} // namespace xar::ck3_11906
