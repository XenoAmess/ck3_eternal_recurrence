#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include "xar_bridge/zhongguo_promotion_source_progress_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <charconv>
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
constexpr std::int32_t kMaximumWidgetChildren = 4'096;
constexpr std::size_t kMaximumWidgetTraversal = 4'096;
constexpr std::size_t kMaximumWidgetDepth = 64;
constexpr std::int32_t kMaximumModalReceivers = 256;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;

enum VariableIndex : std::size_t {
  managed_first = 0,
  managed_owner,
  received_first,
  self_character,
  received_owner,
  received_cycle,
  received_case,
  self_case_owner,
  self_cycle,
  self_case,
  self_b1_owner,
  self_b1_cycle,
  self_b1_case,
  acl_mode,
  policy_available,
  policy_id,
  policy_self_mode,
  policy_team_mode,
  policy_evaluator_mode,
  policy_blackbox_risk,
};

using RawRows = std::array<ZhongguoRawVariableV1, 20>;

struct ResolvedGuiTreeV1 {
  void *context = nullptr;
  void *owner = nullptr;
  void *root = nullptr;
  void *modal_top_receiver = nullptr;
  std::array<void *, kZhongguoScoreboardStateV1WidgetNames.size()> widgets{};
};

enum class ModalTopRelationV1 : std::uint8_t {
  none = 0,
  exact_scoreboard_modal = 1,
  strict_descendant_of_scoreboard_modal = 2,
  other = 3,
};

enum class ScoreboardSurfaceV1 : std::uint8_t {
  none = 0,
  managed = 1,
  received = 2,
  system = 3,
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

bool ReadBytes(const ZhongguoScoreboardAccessV1 &access, const void *address,
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
bool ReadValue(const ZhongguoScoreboardAccessV1 &access, const void *base,
               std::size_t offset, Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

void AppendU8(std::string &output, std::uint8_t value) {
  output.push_back(static_cast<char>(value));
}

void AppendU16Le(std::string &output, std::uint16_t value) {
  for (unsigned shift = 0; shift != 16; shift += 8) {
    AppendU8(output, static_cast<std::uint8_t>(value >> shift));
  }
}

void AppendU32Le(std::string &output, std::uint32_t value) {
  for (unsigned shift = 0; shift != 32; shift += 8) {
    AppendU8(output, static_cast<std::uint8_t>(value >> shift));
  }
}

void AppendU64Le(std::string &output, std::uint64_t value) {
  for (unsigned shift = 0; shift != 64; shift += 8) {
    AppendU8(output, static_cast<std::uint8_t>(value >> shift));
  }
}

void AppendI32Le(std::string &output, std::int32_t value) {
  AppendU32Le(output, static_cast<std::uint32_t>(value));
}

void AppendI64Le(std::string &output, std::int64_t value) {
  AppendU64Le(output, static_cast<std::uint64_t>(value));
}

bool AppendCanonicalString(std::string &output, std::string_view value) {
  if (value.size() > std::numeric_limits<std::uint32_t>::max()) return false;
  AppendU32Le(output, static_cast<std::uint32_t>(value.size()));
  output.append(value);
  return true;
}

void AppendDomain(std::string &output, std::string_view domain) {
  output.append(domain);
  output.push_back('\0');
}

void AppendPointer(std::string &output, const void *pointer) {
  AppendU64Le(output, static_cast<std::uint64_t>(
                          reinterpret_cast<std::uintptr_t>(pointer)));
}

std::uint32_t RotateRight(std::uint32_t value, unsigned count) noexcept {
  return (value >> count) | (value << (32U - count));
}

std::array<std::uint8_t, 32> Sha256(std::string_view input) {
  constexpr std::array<std::uint32_t, 64> constants{
      0x428A2F98U, 0x71374491U, 0xB5C0FBCFU, 0xE9B5DBA5U,
      0x3956C25BU, 0x59F111F1U, 0x923F82A4U, 0xAB1C5ED5U,
      0xD807AA98U, 0x12835B01U, 0x243185BEU, 0x550C7DC3U,
      0x72BE5D74U, 0x80DEB1FEU, 0x9BDC06A7U, 0xC19BF174U,
      0xE49B69C1U, 0xEFBE4786U, 0x0FC19DC6U, 0x240CA1CCU,
      0x2DE92C6FU, 0x4A7484AAU, 0x5CB0A9DCU, 0x76F988DAU,
      0x983E5152U, 0xA831C66DU, 0xB00327C8U, 0xBF597FC7U,
      0xC6E00BF3U, 0xD5A79147U, 0x06CA6351U, 0x14292967U,
      0x27B70A85U, 0x2E1B2138U, 0x4D2C6DFCU, 0x53380D13U,
      0x650A7354U, 0x766A0ABBU, 0x81C2C92EU, 0x92722C85U,
      0xA2BFE8A1U, 0xA81A664BU, 0xC24B8B70U, 0xC76C51A3U,
      0xD192E819U, 0xD6990624U, 0xF40E3585U, 0x106AA070U,
      0x19A4C116U, 0x1E376C08U, 0x2748774CU, 0x34B0BCB5U,
      0x391C0CB3U, 0x4ED8AA4AU, 0x5B9CCA4FU, 0x682E6FF3U,
      0x748F82EEU, 0x78A5636FU, 0x84C87814U, 0x8CC70208U,
      0x90BEFFFAU, 0xA4506CEBU, 0xBEF9A3F7U, 0xC67178F2U};
  std::array<std::uint32_t, 8> hash{
      0x6A09E667U, 0xBB67AE85U, 0x3C6EF372U, 0xA54FF53AU,
      0x510E527FU, 0x9B05688CU, 0x1F83D9ABU, 0x5BE0CD19U};
  std::string padded(input);
  padded.push_back(static_cast<char>(0x80));
  while (padded.size() % 64 != 56) padded.push_back('\0');
  const auto bit_length = static_cast<std::uint64_t>(input.size()) * 8U;
  for (int shift = 56; shift >= 0; shift -= 8) {
    padded.push_back(static_cast<char>(bit_length >> shift));
  }
  for (std::size_t offset = 0; offset < padded.size(); offset += 64) {
    std::array<std::uint32_t, 64> words{};
    for (std::size_t index = 0; index < 16; ++index) {
      const auto *byte = reinterpret_cast<const unsigned char *>(
          padded.data() + offset + index * 4);
      words[index] = (static_cast<std::uint32_t>(byte[0]) << 24U) |
                     (static_cast<std::uint32_t>(byte[1]) << 16U) |
                     (static_cast<std::uint32_t>(byte[2]) << 8U) |
                     static_cast<std::uint32_t>(byte[3]);
    }
    for (std::size_t index = 16; index < words.size(); ++index) {
      const auto s0 = RotateRight(words[index - 15], 7) ^
                      RotateRight(words[index - 15], 18) ^
                      (words[index - 15] >> 3U);
      const auto s1 = RotateRight(words[index - 2], 17) ^
                      RotateRight(words[index - 2], 19) ^
                      (words[index - 2] >> 10U);
      words[index] = words[index - 16] + s0 + words[index - 7] + s1;
    }
    auto a = hash[0];
    auto b = hash[1];
    auto c = hash[2];
    auto d = hash[3];
    auto e = hash[4];
    auto f = hash[5];
    auto g = hash[6];
    auto h = hash[7];
    for (std::size_t index = 0; index < words.size(); ++index) {
      const auto sigma1 = RotateRight(e, 6) ^ RotateRight(e, 11) ^
                          RotateRight(e, 25);
      const auto choose = (e & f) ^ ((~e) & g);
      const auto temporary1 =
          h + sigma1 + choose + constants[index] + words[index];
      const auto sigma0 = RotateRight(a, 2) ^ RotateRight(a, 13) ^
                          RotateRight(a, 22);
      const auto majority = (a & b) ^ (a & c) ^ (b & c);
      const auto temporary2 = sigma0 + majority;
      h = g;
      g = f;
      f = e;
      e = d + temporary1;
      d = c;
      c = b;
      b = a;
      a = temporary1 + temporary2;
    }
    hash[0] += a;
    hash[1] += b;
    hash[2] += c;
    hash[3] += d;
    hash[4] += e;
    hash[5] += f;
    hash[6] += g;
    hash[7] += h;
  }
  std::array<std::uint8_t, 32> digest{};
  for (std::size_t index = 0; index < hash.size(); ++index) {
    for (unsigned byte = 0; byte < 4; ++byte) {
      digest[index * 4 + byte] = static_cast<std::uint8_t>(
          hash[index] >> (24U - byte * 8U));
    }
  }
  return digest;
}

std::string DigestBytes(const std::array<std::uint8_t, 32> &digest) {
  return std::string(reinterpret_cast<const char *>(digest.data()),
                     digest.size());
}

std::string DigestHex(const std::array<std::uint8_t, 32> &digest) {
  constexpr char hex[] = "0123456789ABCDEF";
  std::string output;
  output.reserve(64);
  for (const auto byte : digest) {
    output.push_back(hex[byte >> 4U]);
    output.push_back(hex[byte & 0x0FU]);
  }
  return output;
}

bool AppendExecutableDigest(std::string &output) {
  constexpr auto value = kZhongguoScoreboardStateV1ExecutableSha256;
  if (value.size() != 64) return false;
  const auto digit = [](char character, std::uint8_t &result) {
    if (character >= '0' && character <= '9') {
      result = static_cast<std::uint8_t>(character - '0');
      return true;
    }
    if (character >= 'A' && character <= 'F') {
      result = static_cast<std::uint8_t>(character - 'A' + 10);
      return true;
    }
    return false;
  };
  for (std::size_t index = 0; index < value.size(); index += 2) {
    std::uint8_t high = 0;
    std::uint8_t low = 0;
    if (!digit(value[index], high) || !digit(value[index + 1], low)) {
      return false;
    }
    AppendU8(output, static_cast<std::uint8_t>((high << 4U) | low));
  }
  return true;
}

bool EnvironmentIsExact(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted ||
      !environment.variables.exact_build_admitted) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) {
    return environment.variables.offline_fixture_function_overrides &&
           environment.module_base == 0 && environment.gui_global_slot == nullptr &&
           environment.find_top_level_widget == nullptr;
  }
  const auto base = environment.module_base;
  return base != 0 && !environment.variables.offline_fixture_function_overrides &&
         reinterpret_cast<std::uintptr_t>(environment.gui_global_slot) ==
             base + kZhongguoGuiGlobalSlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.find_top_level_widget) ==
             base + kZhongguoGuiFindTopLevelWidgetRva &&
         environment.variables.module_base == base;
}

bool ValidateCharacterNative(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access,
    std::int32_t character_id) noexcept {
  if (character_id <= 0) return false;
  void *storage = nullptr;
  void *fallback = nullptr;
  if (!ReadBytes(access, environment.variables.character_storage_slot,
                 &storage, sizeof(storage)) ||
      !ReadBytes(access, environment.variables.character_fallback_slot,
                 &fallback, sizeof(fallback)) ||
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
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access,
    std::int32_t character_id) noexcept {
  if (environment.offline_fixture_function_overrides) {
    return access.validate_character != nullptr &&
           access.validate_character(access.context, character_id);
  }
  return ValidateCharacterNative(environment, access, character_id);
}

bool ResolveVariableIdentifier(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    std::string_view key, std::int32_t &identifier) noexcept {
  void *const table = environment.variables.variable_identifier_table();
  if (table == nullptr || key.empty() ||
      key.size() >
          static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max())) {
    return false;
  }
  const ZhongguoNativeStringView32V1 view{
      key.data(), static_cast<std::int32_t>(key.size()), 0};
  identifier = -1;
  if (environment.variables.variable_identifier_lookup(table, &identifier,
                                                         &view) == nullptr ||
      identifier < 0) {
    return false;
  }
  const auto *const name =
      environment.variables.variable_identifier_name(table, identifier);
  return name != nullptr && *name == key;
}

bool FindVariableValue(const ZhongguoScoreboardAccessV1 &access,
                       void *context, std::int32_t identifier,
                       ZhongguoRawVariableV1 &output) noexcept {
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
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, std::int32_t character_id,
    std::string_view key, ZhongguoRawVariableV1 &output) noexcept {
  std::int32_t identifier = -1;
  if (!ResolveVariableIdentifier(environment, key, identifier)) return false;
  const ZhongguoEventTarget16V1 target{4, {}, character_id};
  void *const context =
      environment.variables.variable_context_for_scope(&target);
  return context != nullptr &&
         FindVariableValue(access, context, identifier, output);
}

bool ReadAllowlistedRows(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, std::int32_t character_id,
    RawRows &output) noexcept {
  for (std::size_t index = 0;
       index < kZhongguoScoreboardStateV1VariableAllowlist.size(); ++index) {
    const auto key = kZhongguoScoreboardStateV1VariableAllowlist[index];
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

template <typename... Fields>
void UnavailableMany(std::string_view reason, Fields &...fields) {
  (SetUnavailable(fields, reason), ...);
}

void InitializeWidget(game::ZhongguoScoreboardWidgetStateV1 &widget,
                      std::size_t index, std::string_view reason) {
  widget = {};
  widget.stable_identity.assign(
      kZhongguoScoreboardStateV1WidgetIdentities[index]);
  widget.runtime_name.assign(kZhongguoScoreboardStateV1WidgetNames[index]);
  SetUnavailable(widget.instance_pointer, reason);
  SetUnavailable(widget.vtable_pointer, reason);
  SetUnavailable(widget.exists, reason);
  UnavailableMany(reason, widget.local_visible, widget.effective_visible,
                  widget.enabled, widget.focused, widget.modal_blocking,
                  widget.screen_x, widget.screen_y, widget.screen_width,
                  widget.screen_height, widget.scroll_min, widget.scroll_max,
                  widget.scroll_value);
}

std::string FormatPointer(const void *pointer) {
  std::array<char, 2 + sizeof(std::uintptr_t) * 2> buffer{};
  buffer[0] = '0';
  buffer[1] = 'x';
  const auto value = reinterpret_cast<std::uintptr_t>(pointer);
  const auto converted = std::to_chars(
      buffer.data() + 2, buffer.data() + buffer.size(), value, 16);
  if (converted.ec != std::errc{}) return {};
  for (char *current = buffer.data() + 2; current != converted.ptr; ++current) {
    if (*current >= 'a' && *current <= 'f') {
      *current = static_cast<char>(*current - 'a' + 'A');
    }
  }
  return std::string(buffer.data(), converted.ptr);
}

void InitializeEnvelope(const ZhongguoScoreboardStateRequestV1 &request,
                        const game::ZhongguoCaseFrameV1 *frame,
                        game::ZhongguoScoreboardStateV1 &output) {
  output = {};
  output.case_kind = kZhongguoScoreboardStateV1CaseKind;
  output.request_nonce = request.request_nonce;
  output.provider_session_id = request.provider_session_id;
  output.snapshot_revision = request.expected_snapshot_revision;
  if (frame != nullptr) {
    output.date_raw = frame->date_raw;
    output.paused = frame->paused;
    output.player_character_id = frame->played_character_id;
  }
  for (std::size_t index = 0; index < output.widgets.size(); ++index) {
    InitializeWidget(output.widgets[index], index, "snapshot_unavailable");
  }
  UnavailableMany("snapshot_unavailable",
                  output.managed_acl.owner_character_id,
                  output.managed_acl.first_subject_character_id,
                  output.received_self_acl.first_row_character_id,
                  output.received_self_acl.owner_character_id,
                  output.received_self_acl.subject_character_id,
                  output.received_self_acl.cycle_serial,
                  output.received_self_acl.result_case_serial,
                  output.received_self_acl.b1_case_serial,
                  output.received_self_acl.disclosure_acl_mode,
                  output.received_self_acl.disclosure_policy_available,
                  output.received_self_acl.disclosure_policy_id,
                  output.received_self_acl.disclosure_self_mode,
                  output.received_self_acl.disclosure_team_mode,
                  output.received_self_acl.disclosure_evaluator_identity_mode,
                  output.received_self_acl.disclosure_blackbox_risk);
  SetUnavailable(output.actions.activate,
                 "read_only_provider_action_not_exposed");
  SetUnavailable(output.actions.close,
                 "read_only_provider_action_not_exposed");
  SetUnavailable(output.actions.reopen,
                 "read_only_provider_action_not_exposed");
}

void SetTopUnavailable(game::ZhongguoScoreboardStateV1 &output,
                       std::string_view reason,
                       bool same_frame_ready = false) {
  output.status = game::ZhongguoScoreboardStateStatusV1::unavailable;
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

bool ReadAbiString(const ZhongguoScoreboardAccessV1 &access,
                   const void *object, std::string &output) noexcept {
  struct AbiString {
    std::array<std::uint8_t, 16> storage{};
    std::uint64_t size = 0;
    std::uint64_t capacity = 0;
  } value{};
  if (!ReadBytes(access, object, &value, sizeof(value)) || value.size > 127 ||
      value.capacity < value.size) {
    return false;
  }
  const void *data = object;
  if (value.capacity >= 16) {
    std::memcpy(&data, value.storage.data(), sizeof(data));
  }
  if (data == nullptr) return false;
  std::array<char, 128> buffer{};
  if (value.size != 0 &&
      !ReadBytes(access, data, buffer.data(),
                 static_cast<std::size_t>(value.size))) {
    return false;
  }
  output.assign(buffer.data(), static_cast<std::size_t>(value.size));
  return true;
}

bool WidgetNameEquals(const ZhongguoScoreboardAccessV1 &access, void *widget,
                      std::string_view expected) noexcept {
  const void *name_object = nullptr;
  std::string name;
  return CheckedAddress(widget, kZhongguoWidgetNameOffset, name_object) &&
         ReadAbiString(access, name_object, name) && name == expected;
}

void *FindDescendant(const ZhongguoScoreboardAccessV1 &access, void *root,
                     std::string_view expected) noexcept {
  if (root == nullptr) return nullptr;
  struct Pending {
    void *widget = nullptr;
    std::size_t depth = 0;
  };
  std::array<Pending, kMaximumWidgetTraversal> pending{};
  std::size_t size = 1;
  pending[0] = {root, 0};
  std::size_t visited = 0;
  while (size != 0 && visited++ < kMaximumWidgetTraversal) {
    const auto current = pending[--size];
    if (WidgetNameEquals(access, current.widget, expected)) {
      return current.widget;
    }
    if (current.depth >= kMaximumWidgetDepth) continue;
    void **children = nullptr;
    std::int32_t count = 0;
    if (!ReadValue(access, current.widget, kZhongguoWidgetChildrenOffset,
                   children) ||
        !ReadValue(access, current.widget, kZhongguoWidgetChildCountOffset,
                   count) ||
        count < 0 || count > kMaximumWidgetChildren ||
        (count != 0 && children == nullptr) ||
        size + static_cast<std::size_t>(count) > pending.size()) {
      return nullptr;
    }
    for (std::int32_t index = 0; index < count; ++index) {
      void *child = nullptr;
      if (!ReadValue(access, children,
                     static_cast<std::size_t>(index) * sizeof(void *), child)) {
        return nullptr;
      }
      if (child != nullptr) pending[size++] = {child, current.depth + 1};
    }
  }
  return nullptr;
}

bool ResolveGuiContextAndOwner(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, void *&context,
    void *&owner) noexcept {
  context = nullptr;
  owner = nullptr;
  if (environment.offline_fixture_function_overrides) {
    return access.resolve_fixture_gui != nullptr &&
           access.resolve_fixture_gui(access.context, context, owner) &&
           context != nullptr && owner != nullptr;
  }
  void *first = nullptr;
  void *second = nullptr;
  void *third = nullptr;
  return ReadBytes(access, environment.gui_global_slot, &first,
                   sizeof(first)) &&
         ReadValue(access, first, kZhongguoGuiChainFirstOffset, second) &&
         ReadValue(access, second, kZhongguoGuiChainSecondOffset, third) &&
         ReadValue(access, third, kZhongguoGuiContextOffset, context) &&
         ReadValue(access, context, kZhongguoGuiOwnerOffset, owner) &&
         owner != nullptr;
}

bool ReadModalTopReceiver(const ZhongguoScoreboardAccessV1 &access,
                          void *context, void *&top_receiver) noexcept {
  top_receiver = nullptr;
  void **receivers = nullptr;
  std::int32_t count = 0;
  if (!ReadValue(access, context, kZhongguoGuiModalReceiversOffset,
                 receivers) ||
      !ReadValue(access, context, kZhongguoGuiModalReceiverCountOffset,
                 count) ||
      count < 0 || count > kMaximumModalReceivers ||
      (count != 0 && receivers == nullptr)) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    void *receiver = nullptr;
    void *vtable = nullptr;
    if (!ReadValue(access, receivers,
                   static_cast<std::size_t>(index) * sizeof(void *),
                   receiver) ||
        receiver == nullptr || !ReadValue(access, receiver, 0, vtable) ||
        vtable == nullptr) {
      return false;
    }
    if (index + 1 == count) top_receiver = receiver;
  }
  return true;
}

void *CallFindTopLevelWidget(
    NativeZhongguoFindTopLevelWidgetV1 find_top_level_widget, void *owner,
    const std::string *name) noexcept {
#if defined(_MSC_VER)
  __try {
    return find_top_level_widget(owner, name);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return nullptr;
  }
#else
  return find_top_level_widget(owner, name);
#endif
}

bool FindFixedWidgets(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access,
    ResolvedGuiTreeV1 &resolved) noexcept {
  resolved = {};
  if (!ResolveGuiContextAndOwner(environment, access, resolved.context,
                                 resolved.owner) ||
      !ReadModalTopReceiver(access, resolved.context,
                            resolved.modal_top_receiver)) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) {
    if (access.find_fixed_widget == nullptr) return false;
    for (std::size_t index = 0; index < resolved.widgets.size(); ++index) {
      resolved.widgets[index] = access.find_fixed_widget(
          access.context, kZhongguoScoreboardStateV1WidgetNames[index]);
    }
    resolved.root = resolved.widgets[1];
    return true;
  }
  std::string window_name{kZhongguoScoreboardStateV1WidgetNames[1]};
  void *window = CallFindTopLevelWidget(environment.find_top_level_widget,
                                        resolved.owner, &window_name);
  resolved.widgets[1] = window;
  resolved.root = window;
  if (window == nullptr ||
      !WidgetNameEquals(access, window,
                        kZhongguoScoreboardStateV1WidgetNames[1])) {
    resolved.widgets[1] = nullptr;
    resolved.root = nullptr;
    return true;
  }
  for (std::size_t index = 0; index < resolved.widgets.size(); ++index) {
    if (index != 1) {
      resolved.widgets[index] = FindDescendant(
          access, window, kZhongguoScoreboardStateV1WidgetNames[index]);
    }
  }
  return true;
}

bool ReadLocalVisible(const ZhongguoScoreboardAccessV1 &access, void *widget,
                      bool &visible) noexcept {
  std::uint8_t flags = 0;
  if (!ReadValue(access, widget, kZhongguoWidgetHiddenFlagsOffset, flags)) {
    return false;
  }
  visible = (flags & kZhongguoWidgetLocalHiddenMask) == 0;
  return true;
}

bool ReadEffectiveEnabled(const ZhongguoScoreboardAccessV1 &access,
                          void *widget, bool &enabled) noexcept {
  std::uint8_t flags = 0;
  if (!ReadValue(access, widget, kZhongguoWidgetHiddenFlagsOffset, flags)) {
    return false;
  }
  enabled = (flags & kZhongguoWidgetEffectiveDisabledMask) == 0;
  return true;
}

bool ReadEffectiveVisible(const ZhongguoScoreboardAccessV1 &access,
                          void *widget, bool &visible) noexcept {
  std::uint8_t flags = 0;
  if (!ReadValue(access, widget, kZhongguoWidgetHiddenFlagsOffset, flags)) {
    return false;
  }
  visible = (flags & kZhongguoWidgetEffectiveHiddenMask) == 0;
  return true;
}

bool DecodeWidgets(const ZhongguoScoreboardAccessV1 &access,
                   const std::array<
                       void *, kZhongguoScoreboardStateV1WidgetNames.size()>
                       &pointers,
                   game::ZhongguoScoreboardStateV1 &output) {
  bool all_present = true;
  for (std::size_t index = 0; index < pointers.size(); ++index) {
    auto &widget = output.widgets[index];
    SetAvailable(widget.exists, pointers[index] != nullptr);
    if (pointers[index] == nullptr) {
      all_present = false;
      UnavailableMany("widget_not_instantiated", widget.instance_pointer,
                      widget.vtable_pointer, widget.local_visible,
                      widget.effective_visible);
    } else {
      void *vtable = nullptr;
      bool local = false;
      bool effective = false;
      bool enabled = false;
      if (!ReadValue(access, pointers[index], 0, vtable) || vtable == nullptr ||
          !ReadLocalVisible(access, pointers[index], local) ||
          !ReadEffectiveVisible(access, pointers[index], effective) ||
          !ReadEffectiveEnabled(access, pointers[index], enabled)) {
        return false;
      }
      SetAvailable(widget.instance_pointer, FormatPointer(pointers[index]));
      SetAvailable(widget.vtable_pointer, FormatPointer(vtable));
      SetAvailable(widget.local_visible, local);
      SetAvailable(widget.effective_visible, effective);
      SetAvailable(widget.enabled, enabled);
    }
    SetUnavailable(widget.focused, "focus_owner_abi_not_frozen");
    SetUnavailable(widget.modal_blocking,
                   "modal_blocking_abi_not_frozen");
    UnavailableMany("screen_rect_abi_not_frozen", widget.screen_x,
                    widget.screen_y, widget.screen_width,
                    widget.screen_height);
    UnavailableMany("scroll_area_extent_abi_not_frozen", widget.scroll_min,
                    widget.scroll_max, widget.scroll_value);
  }
  output.readiness.entry_window_state_ready = all_present;
  return true;
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

void DecodeCharacter(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access,
    const ZhongguoRawVariableV1 &raw,
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

bool AvailableEquals(const game::ZhongguoTypedIntegerV1 &field,
                     std::int64_t value) noexcept {
  return field.available && field.value.has_value() && *field.value == value;
}

bool Same(const game::ZhongguoTypedIntegerV1 &left,
          const game::ZhongguoTypedIntegerV1 &right) noexcept {
  return left.available && right.available && left.value == right.value;
}

bool AllAbsent(const RawRows &rows, std::size_t begin,
               std::size_t end) noexcept {
  for (std::size_t index = begin; index <= end; ++index) {
    if (rows[index].present) return false;
  }
  return true;
}

bool DecodeAcl(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
               const ZhongguoScoreboardAccessV1 &access,
               const RawRows &rows, std::int32_t player_character_id,
               game::ZhongguoScoreboardStateV1 &output) {
  auto &managed = output.managed_acl;
  if (!rows[managed_first].present && !rows[managed_owner].present) {
    managed.surface_available = false;
    managed.current_player_can_assess_others = false;
    SetUnavailable(managed.owner_character_id, "surface_not_available");
    SetUnavailable(managed.first_subject_character_id,
                   "surface_not_available");
  } else {
    DecodeCharacter(environment, access, rows[managed_first],
                    managed.first_subject_character_id);
    DecodeCharacter(environment, access, rows[managed_owner],
                    managed.owner_character_id);
    if (!managed.first_subject_character_id.available ||
        !AvailableEquals(managed.owner_character_id, player_character_id)) {
      return false;
    }
    managed.surface_available = true;
    managed.current_player_can_assess_others = true;
  }

  auto &received = output.received_self_acl;
  if (AllAbsent(rows, received_first, policy_blackbox_risk)) {
    received.surface_available = false;
    received.current_player_is_subject = false;
    UnavailableMany("surface_not_available", received.first_row_character_id,
                    received.owner_character_id,
                    received.subject_character_id, received.cycle_serial,
                    received.result_case_serial, received.b1_case_serial,
                    received.disclosure_acl_mode,
                    received.disclosure_policy_available,
                    received.disclosure_policy_id,
                    received.disclosure_self_mode,
                    received.disclosure_team_mode,
                    received.disclosure_evaluator_identity_mode,
                    received.disclosure_blackbox_risk);
    output.readiness.acl_ready = true;
    return true;
  }

  DecodeCharacter(environment, access, rows[received_first],
                  received.first_row_character_id);
  DecodeCharacter(environment, access, rows[received_owner],
                  received.owner_character_id);
  DecodeCharacter(environment, access, rows[self_character],
                  received.subject_character_id);
  DecodeInteger(rows[received_cycle], received.cycle_serial);
  DecodeInteger(rows[received_case], received.result_case_serial);
  game::ZhongguoTypedIntegerV1 case_owner;
  game::ZhongguoTypedIntegerV1 self_cycle_value;
  game::ZhongguoTypedIntegerV1 self_case_value;
  game::ZhongguoTypedIntegerV1 b1_owner;
  game::ZhongguoTypedIntegerV1 b1_cycle;
  DecodeCharacter(environment, access, rows[self_case_owner], case_owner);
  DecodeInteger(rows[self_cycle], self_cycle_value);
  DecodeInteger(rows[self_case], self_case_value);
  DecodeCharacter(environment, access, rows[self_b1_owner], b1_owner);
  DecodeInteger(rows[self_b1_cycle], b1_cycle);
  DecodeInteger(rows[self_b1_case], received.b1_case_serial);
  DecodeInteger(rows[acl_mode], received.disclosure_acl_mode);
  DecodeInteger(rows[policy_available],
                received.disclosure_policy_available);
  DecodeInteger(rows[policy_id], received.disclosure_policy_id);
  DecodeInteger(rows[policy_self_mode], received.disclosure_self_mode);
  DecodeInteger(rows[policy_team_mode], received.disclosure_team_mode);
  DecodeInteger(rows[policy_evaluator_mode],
                received.disclosure_evaluator_identity_mode);
  DecodeInteger(rows[policy_blackbox_risk],
                received.disclosure_blackbox_risk);

  const bool identity_valid =
      received.first_row_character_id.available &&
      AvailableEquals(received.subject_character_id, player_character_id) &&
      received.owner_character_id.available &&
      received.cycle_serial.available &&
      received.result_case_serial.available &&
      received.b1_case_serial.available &&
      Same(case_owner, received.owner_character_id) &&
      Same(self_cycle_value, received.cycle_serial) &&
      Same(self_case_value, received.result_case_serial) &&
      Same(b1_owner, received.owner_character_id) &&
      Same(b1_cycle, received.cycle_serial);
  const bool mode_c =
      AvailableEquals(received.disclosure_acl_mode, 0) &&
      AvailableEquals(received.disclosure_policy_available, 0);
  const bool mode_ab =
      (AvailableEquals(received.disclosure_acl_mode, 3) ||
       AvailableEquals(received.disclosure_acl_mode, 1)) &&
      AvailableEquals(received.disclosure_policy_available, 1) &&
      Same(received.disclosure_policy_id, received.b1_case_serial) &&
      Same(received.disclosure_self_mode,
           received.disclosure_acl_mode) &&
      received.disclosure_team_mode.available &&
      received.disclosure_evaluator_identity_mode.available &&
      received.disclosure_blackbox_risk.available;
  if (!identity_valid || (!mode_c && !mode_ab)) return false;
  received.surface_available = true;
  received.current_player_is_subject = true;
  output.readiness.acl_ready = true;
  return true;
}

bool ReadChildOrdinal(const ZhongguoScoreboardAccessV1 &access, void *parent,
                      void *child, std::uint32_t &ordinal) noexcept {
  void **children = nullptr;
  std::int32_t count = 0;
  if (!ReadValue(access, parent, kZhongguoWidgetChildrenOffset, children) ||
      !ReadValue(access, parent, kZhongguoWidgetChildCountOffset, count) ||
      count < 0 || count > kMaximumWidgetChildren ||
      (count != 0 && children == nullptr)) {
    return false;
  }
  bool found = false;
  for (std::int32_t index = 0; index < count; ++index) {
    void *candidate = nullptr;
    if (!ReadValue(access, children,
                   static_cast<std::size_t>(index) * sizeof(void *),
                   candidate)) {
      return false;
    }
    if (candidate == child) {
      if (found) return false;
      found = true;
      ordinal = static_cast<std::uint32_t>(index);
    }
  }
  return found;
}

bool AppendParentPath(const ZhongguoScoreboardAccessV1 &access, void *widget,
                      void *root, std::string &output) {
  struct Hop {
    void *ancestor = nullptr;
    std::uint32_t child_ordinal = 0;
  };
  std::array<Hop, kMaximumWidgetDepth> hops{};
  std::size_t depth = 0;
  void *current = widget;
  while (current != root) {
    if (current == nullptr || depth == hops.size()) return false;
    void *parent = nullptr;
    std::uint32_t ordinal = 0;
    if (!ReadValue(access, current, kZhongguoWidgetParentOffset, parent) ||
        parent == nullptr ||
        !ReadChildOrdinal(access, parent, current, ordinal)) {
      return false;
    }
    for (std::size_t index = 0; index < depth; ++index) {
      if (hops[index].ancestor == parent) return false;
    }
    hops[depth++] = {parent, ordinal};
    current = parent;
  }
  AppendU8(output, static_cast<std::uint8_t>(depth));
  // The frozen TREE encoding walks each edge from the scoreboard window root
  // down to the target.  Discovery naturally produced the opposite order, so
  // serialize the bounded hop stack in reverse rather than making the public
  // fingerprint depend on an implementation traversal detail.
  for (std::size_t index = depth; index != 0; --index) {
    AppendPointer(output, hops[index - 1].ancestor);
    AppendU32Le(output, hops[index - 1].child_ordinal);
  }
  return true;
}

bool BuildTreeCanonicalBytes(const ZhongguoScoreboardAccessV1 &access,
                             const ResolvedGuiTreeV1 &resolved,
                             std::string &output) {
  output.clear();
  AppendDomain(output, kZhongguoScoreboardTreeDomainV1);
  AppendU16Le(output, 1);
  if (!AppendExecutableDigest(output) ||
      !AppendCanonicalString(output, kZhongguoScoreboardStateV1AllowlistId) ||
      resolved.owner == nullptr || resolved.root == nullptr) {
    return false;
  }
  AppendPointer(output, resolved.owner);
  AppendPointer(output, resolved.root);
  for (std::size_t index = 0; index < resolved.widgets.size(); ++index) {
    void *const widget = resolved.widgets[index];
    AppendU8(output, static_cast<std::uint8_t>(index));
    AppendU8(output, widget != nullptr ? 1 : 0);
    AppendPointer(output, widget);
    void *vtable = nullptr;
    if (widget != nullptr &&
        (!ReadValue(access, widget, 0, vtable) || vtable == nullptr)) {
      return false;
    }
    AppendPointer(output, vtable);
    if (widget == nullptr) {
      AppendU8(output, 0);
    } else if (!AppendParentPath(access, widget, resolved.root, output)) {
      return false;
    }
  }
  return true;
}

bool ClassifyModalTop(const ZhongguoScoreboardAccessV1 &access,
                      void *top_receiver, void *scoreboard_modal,
                      ModalTopRelationV1 &relation) noexcept {
  if (top_receiver == nullptr) {
    relation = ModalTopRelationV1::none;
    return true;
  }
  if (top_receiver == scoreboard_modal) {
    relation = ModalTopRelationV1::exact_scoreboard_modal;
    return true;
  }
  void *current = top_receiver;
  std::array<void *, kMaximumWidgetDepth> visited{};
  std::size_t depth = 0;
  while (current != nullptr) {
    if (depth == visited.size()) return false;
    for (std::size_t index = 0; index < depth; ++index) {
      if (visited[index] == current) return false;
    }
    visited[depth++] = current;
    void *parent = nullptr;
    if (!ReadValue(access, current, kZhongguoWidgetParentOffset, parent)) {
      return false;
    }
    if (parent == scoreboard_modal) {
      relation = ModalTopRelationV1::strict_descendant_of_scoreboard_modal;
      return true;
    }
    current = parent;
  }
  relation = ModalTopRelationV1::other;
  return true;
}

bool ReadObservedBoolean(const game::ZhongguoTypedBooleanV1 &field,
                         bool &value) noexcept {
  if (!field.available || !field.value.has_value()) return false;
  value = *field.value;
  return true;
}

bool UniqueVisibleSurface(const game::ZhongguoScoreboardStateV1 &state,
                          std::size_t begin, ScoreboardSurfaceV1 &surface,
                          std::uint8_t &count) noexcept {
  surface = ScoreboardSurfaceV1::none;
  count = 0;
  for (std::size_t offset = 0; offset < 3; ++offset) {
    bool exists = false;
    bool visible = false;
    if (!ReadObservedBoolean(state.widgets[begin + offset].exists, exists) ||
        !ReadObservedBoolean(state.widgets[begin + offset].effective_visible,
                             visible)) {
      return false;
    }
    if (exists && visible) {
      ++count;
      surface = static_cast<ScoreboardSurfaceV1>(offset + 1);
    }
  }
  return count <= 1;
}

void AppendTypedIntegerCanonical(
    std::string &output, const game::ZhongguoTypedIntegerV1 &field) {
  AppendU8(output, field.available && field.value.has_value() ? 1 : 0);
  if (field.available && field.value.has_value()) {
    AppendI64Le(output, *field.value);
  }
}

void AppendDerivedAclCanonical(
    std::string &output, const game::ZhongguoScoreboardStateV1 &state) {
  const auto &managed = state.managed_acl;
  AppendU8(output, managed.surface_available ? 1 : 0);
  AppendU8(output, managed.current_player_can_assess_others ? 1 : 0);
  AppendTypedIntegerCanonical(output, managed.owner_character_id);
  AppendTypedIntegerCanonical(output, managed.first_subject_character_id);

  const auto &received = state.received_self_acl;
  AppendU8(output, received.surface_available ? 1 : 0);
  AppendU8(output, received.current_player_is_subject ? 1 : 0);
  AppendTypedIntegerCanonical(output, received.first_row_character_id);
  AppendTypedIntegerCanonical(output, received.owner_character_id);
  AppendTypedIntegerCanonical(output, received.subject_character_id);
  AppendTypedIntegerCanonical(output, received.cycle_serial);
  AppendTypedIntegerCanonical(output, received.result_case_serial);
  AppendTypedIntegerCanonical(output, received.b1_case_serial);
  AppendTypedIntegerCanonical(output, received.disclosure_acl_mode);
  AppendTypedIntegerCanonical(output, received.disclosure_policy_available);
  AppendTypedIntegerCanonical(output, received.disclosure_policy_id);
  AppendTypedIntegerCanonical(output, received.disclosure_self_mode);
  AppendTypedIntegerCanonical(output, received.disclosure_team_mode);
  AppendTypedIntegerCanonical(output,
                              received.disclosure_evaluator_identity_mode);
  AppendTypedIntegerCanonical(output, received.disclosure_blackbox_risk);
}

bool BuildSemanticCanonicalBytes(
    const ZhongguoScoreboardAccessV1 &access,
    const ResolvedGuiTreeV1 &resolved, const RawRows &rows,
    const game::ZhongguoScoreboardStateV1 &state, std::string &output) {
  output.clear();
  AppendDomain(output, kZhongguoScoreboardSemanticDomainV1);
  AppendU16Le(output, 1);
  if (!AppendExecutableDigest(output) ||
      !AppendCanonicalString(output, kZhongguoScoreboardStateV1AllowlistId)) {
    return false;
  }
  AppendI32Le(output, state.player_character_id);
  for (std::size_t index = 0; index < state.widgets.size(); ++index) {
    bool exists = false;
    bool visible = false;
    bool enabled = false;
    if (!ReadObservedBoolean(state.widgets[index].exists, exists) ||
        !ReadObservedBoolean(state.widgets[index].effective_visible, visible) ||
        !ReadObservedBoolean(state.widgets[index].enabled, enabled)) {
      return false;
    }
    AppendU8(output, static_cast<std::uint8_t>(index));
    AppendU8(output, exists ? 1 : 0);
    AppendU8(output, visible ? 1 : 0);
    AppendU8(output, enabled ? 1 : 0);
  }

  bool modal_open = false;
  if (!ReadObservedBoolean(state.widgets[2].effective_visible, modal_open)) {
    return false;
  }
  ModalTopRelationV1 modal_relation = ModalTopRelationV1::none;
  if (!ClassifyModalTop(access, resolved.modal_top_receiver,
                        resolved.widgets[2], modal_relation)) {
    return false;
  }
  if ((modal_open && modal_relation != ModalTopRelationV1::exact_scoreboard_modal &&
       modal_relation !=
           ModalTopRelationV1::strict_descendant_of_scoreboard_modal) ||
      (!modal_open &&
       (modal_relation == ModalTopRelationV1::exact_scoreboard_modal ||
        modal_relation ==
            ModalTopRelationV1::strict_descendant_of_scoreboard_modal))) {
    return false;
  }

  ScoreboardSurfaceV1 active_page = ScoreboardSurfaceV1::none;
  ScoreboardSurfaceV1 visible_closed_entry = ScoreboardSurfaceV1::none;
  std::uint8_t active_page_count = 0;
  std::uint8_t visible_closed_entry_count = 0;
  if (!UniqueVisibleSurface(state, 10, active_page, active_page_count) ||
      !UniqueVisibleSurface(state, 4, visible_closed_entry,
                            visible_closed_entry_count) ||
      (modal_open &&
       (active_page_count != 1 || visible_closed_entry_count != 0)) ||
      (!modal_open &&
       (active_page_count != 0 || visible_closed_entry_count != 1))) {
    return false;
  }
  AppendU8(output, modal_open ? 1 : 0);
  AppendU8(output, static_cast<std::uint8_t>(modal_relation));
  AppendPointer(output, resolved.modal_top_receiver);
  AppendU8(output, static_cast<std::uint8_t>(active_page));
  AppendU8(output, static_cast<std::uint8_t>(visible_closed_entry));

  for (std::size_t index = 0; index < rows.size(); ++index) {
    AppendU8(output, rows[index].present ? 1 : 0);
    if (rows[index].present) {
      AppendI32Le(output, static_cast<std::int32_t>(rows[index].kind));
      AppendI64Le(output, rows[index].payload);
    }
  }
  AppendDerivedAclCanonical(output, state);
  return true;
}

bool ValidProviderSession(std::string_view value) noexcept {
  if (value.size() != 32) return false;
  for (const char character : value) {
    if (!((character >= '0' && character <= '9') ||
          (character >= 'A' && character <= 'F'))) {
      return false;
    }
  }
  return true;
}

bool SameProviderBinding(
    const ZhongguoScoreboardProviderRevisionTrackerV1 &tracker,
    const ZhongguoScoreboardStateRequestV1 &request,
    const game::ZhongguoCaseFrameV1 &frame) noexcept {
  return tracker.initialized &&
         tracker.provider_session_id == request.provider_session_id &&
         tracker.connection_generation == request.connection_generation &&
         tracker.player_character_id == frame.played_character_id &&
         tracker.date_raw == frame.date_raw &&
         tracker.game_version == kZhongguoScoreboardStateV1GameVersion &&
         tracker.executable_sha256 ==
             kZhongguoScoreboardStateV1ExecutableSha256 &&
         tracker.allowlist_id == kZhongguoScoreboardStateV1AllowlistId;
}

bool ApplyProviderRevision(
    const ZhongguoScoreboardStateRequestV1 &request,
    const game::ZhongguoCaseFrameV1 &frame,
    const std::string &tree_canonical_bytes,
    const std::string &semantic_canonical_bytes,
    game::ZhongguoScoreboardStateV1 &output) {
  auto *const tracker = request.provider_revision_tracker;
  if (tracker == nullptr || !ValidProviderSession(request.provider_session_id) ||
      request.connection_generation == 0 ||
      request.provider_read_mode ==
          ZhongguoScoreboardProviderReadModeV1::unavailable) {
    return false;
  }
  const auto tree_digest = Sha256(tree_canonical_bytes);
  const auto semantic_digest = Sha256(semantic_canonical_bytes);
  std::string state_digest_material;
  AppendDomain(state_digest_material, kZhongguoScoreboardStateDomainV1);
  state_digest_material.append(
      reinterpret_cast<const char *>(tree_digest.data()), tree_digest.size());
  state_digest_material.append(
      reinterpret_cast<const char *>(semantic_digest.data()),
      semantic_digest.size());
  const auto state_digest = Sha256(state_digest_material);

  const bool same_binding = SameProviderBinding(*tracker, request, frame);
  if (request.provider_read_mode ==
      ZhongguoScoreboardProviderReadModeV1::validate_without_advancing) {
    if (!same_binding ||
        tracker->last_tree_canonical_bytes != tree_canonical_bytes ||
        tracker->last_semantic_canonical_bytes != semantic_canonical_bytes) {
      return false;
    }
    output.provider_session_id = tracker->provider_session_id;
    output.observation_sequence = tracker->observation_sequence;
    output.observed_state_revision = tracker->observed_state_revision;
    output.tree_fingerprint_v1 = DigestHex(tree_digest);
    output.semantic_fingerprint_v1 = DigestHex(semantic_digest);
    return true;
  }
  if (request.provider_read_mode !=
      ZhongguoScoreboardProviderReadModeV1::publish_observation) {
    return false;
  }

  ZhongguoScoreboardProviderRevisionTrackerV1 next = *tracker;
  if (!same_binding) {
    next = {};
    next.initialized = true;
    next.provider_session_id = request.provider_session_id;
    next.connection_generation = request.connection_generation;
    next.player_character_id = frame.played_character_id;
    next.date_raw = frame.date_raw;
    next.game_version.assign(kZhongguoScoreboardStateV1GameVersion);
    next.executable_sha256.assign(
        kZhongguoScoreboardStateV1ExecutableSha256);
    next.allowlist_id.assign(kZhongguoScoreboardStateV1AllowlistId);
    next.observation_sequence = 1;
    next.observed_state_revision = 1;
  } else {
    if (next.observation_sequence ==
            std::numeric_limits<std::uint64_t>::max() ||
        next.observed_state_revision ==
            std::numeric_limits<std::uint64_t>::max()) {
      return false;
    }
    ++next.observation_sequence;
    if (next.last_tree_canonical_bytes != tree_canonical_bytes ||
        next.last_semantic_canonical_bytes != semantic_canonical_bytes) {
      ++next.observed_state_revision;
    }
  }
  next.last_tree_canonical_bytes = tree_canonical_bytes;
  next.last_semantic_canonical_bytes = semantic_canonical_bytes;
  next.last_state_digest_bytes = DigestBytes(state_digest);
  *tracker = std::move(next);

  output.provider_session_id = tracker->provider_session_id;
  output.observation_sequence = tracker->observation_sequence;
  output.observed_state_revision = tracker->observed_state_revision;
  output.tree_fingerprint_v1 = DigestHex(tree_digest);
  output.semantic_fingerprint_v1 = DigestHex(semantic_digest);
  return true;
}

} // namespace

ZhongguoScoreboardNativeEnvironmentV1 BindZhongguoScoreboardNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  environment.variables =
      BindZhongguoCaseNativeEnvironmentV1(module_base, exact_build_admitted);
  environment.module_base = module_base;
  environment.exact_build_admitted = exact_build_admitted;
  if (module_base != 0 && exact_build_admitted) {
    environment.gui_global_slot = reinterpret_cast<void **>(
        module_base + kZhongguoGuiGlobalSlotRva);
    environment.find_top_level_widget =
        reinterpret_cast<NativeZhongguoFindTopLevelWidgetV1>(
            module_base + kZhongguoGuiFindTopLevelWidgetRva);
  }
  return environment;
}

game::ReadZhongguoScoreboardStateResultV1 ReadZhongguoScoreboardStateV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access,
    const ZhongguoScoreboardStateRequestV1 &request,
    game::ZhongguoScoreboardStateV1 &output) noexcept {
  try {
    InitializeEnvelope(request, nullptr, output);
    if (request.expected_snapshot_revision == 0 ||
        !ValidNonce(request.request_nonce) || !EnvironmentIsExact(environment)) {
      SetTopUnavailable(output, "unsupported_build");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetTopUnavailable(output, "requires_application_main");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    if (environment.offline_fixture_function_overrides &&
        (access.validate_character == nullptr ||
         access.read_allowlisted_variable == nullptr ||
         access.find_fixed_widget == nullptr ||
         access.resolve_fixture_gui == nullptr)) {
      SetTopUnavailable(output, "internal_error");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }

    game::ZhongguoCaseFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    InitializeEnvelope(request, &before, output);
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    if (!before.paused) {
      SetTopUnavailable(output, "requires_paused");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0 ||
        !ValidateCharacter(environment, access, before.played_character_id)) {
      SetTopUnavailable(output, "map_not_ready");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    ResolvedGuiTreeV1 first_gui{};
    ResolvedGuiTreeV1 second_gui{};
    RawRows first_rows{};
    RawRows second_rows{};
    if (!FindFixedWidgets(environment, access, first_gui)) {
      SetTopUnavailable(output, "gui_root_unavailable");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    if (!ReadAllowlistedRows(environment, access, before.played_character_id,
                             first_rows)) {
      SetTopUnavailable(output, "state_projection_unavailable");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }

    game::ZhongguoScoreboardStateV1 first_state{};
    InitializeEnvelope(request, &before, first_state);
    first_state.readiness.player_binding_ready = true;
    first_state.readiness.gui_root_ready = true;
    if (!DecodeWidgets(access, first_gui.widgets, first_state)) {
      SetTopUnavailable(output, "widget_state_unavailable");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    if (!DecodeAcl(environment, access, first_rows,
                   before.played_character_id, first_state)) {
      SetTopUnavailable(output, "acl_inconsistent");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    if (!first_state.readiness.entry_window_state_ready) {
      SetTopUnavailable(output, "widget_not_instantiated");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }

    std::string first_tree_bytes;
    std::string first_semantic_bytes;
    if (!BuildTreeCanonicalBytes(access, first_gui, first_tree_bytes) ||
        !BuildSemanticCanonicalBytes(access, first_gui, first_rows,
                                     first_state, first_semantic_bytes) ||
        !FindFixedWidgets(environment, access, second_gui) ||
        !ReadAllowlistedRows(environment, access, before.played_character_id,
                             second_rows)) {
      SetTopUnavailable(output, "state_projection_unavailable");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }

    game::ZhongguoScoreboardStateV1 second_state{};
    InitializeEnvelope(request, &before, second_state);
    second_state.readiness.player_binding_ready = true;
    second_state.readiness.gui_root_ready = true;
    std::string second_tree_bytes;
    std::string second_semantic_bytes;
    if (!DecodeWidgets(access, second_gui.widgets, second_state) ||
        !DecodeAcl(environment, access, second_rows,
                   before.played_character_id, second_state) ||
        !second_state.readiness.entry_window_state_ready ||
        !BuildTreeCanonicalBytes(access, second_gui, second_tree_bytes) ||
        !BuildSemanticCanonicalBytes(access, second_gui, second_rows,
                                     second_state, second_semantic_bytes)) {
      SetTopUnavailable(output, "state_projection_unavailable");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    game::ZhongguoCaseFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first_gui.context != second_gui.context ||
        first_gui.owner != second_gui.owner ||
        first_gui.root != second_gui.root ||
        first_gui.modal_top_receiver != second_gui.modal_top_receiver ||
        first_gui.widgets != second_gui.widgets || first_rows != second_rows ||
        first_tree_bytes != second_tree_bytes ||
        first_semantic_bytes != second_semantic_bytes) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }

    output = std::move(first_state);
    output.readiness.same_frame_ready = true;
    output.readiness.state_acl_query_ready =
        output.readiness.player_binding_ready &&
        output.readiness.gui_root_ready &&
        output.readiness.entry_window_state_ready &&
        output.readiness.acl_ready && output.readiness.same_frame_ready;
    output.readiness.full_widget_gate_ready = false;
    output.readiness.production_live_ready = false;
    output.status = game::ZhongguoScoreboardStateStatusV1::available;
    output.unavailable_reason.clear();
    if (!ApplyProviderRevision(request, before, first_tree_bytes,
                               first_semantic_bytes, output)) {
      SetTopUnavailable(output, "provider_revision_unavailable", true);
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    return game::ReadZhongguoScoreboardStateResultV1::available;
  } catch (...) {
    SetTopUnavailable(output, "internal_error");
    return game::ReadZhongguoScoreboardStateResultV1::unavailable;
  }
}

namespace {

void InitializePromotionProgressWidget(
    game::ZhongguoScoreboardWidgetStateV1 &widget, std::size_t index,
    std::string_view reason) {
  widget = {};
  widget.stable_identity.assign(
      kZhongguoPromotionSourceProgressV1WidgetIdentities[index]);
  widget.runtime_name.assign(
      kZhongguoPromotionSourceProgressV1WidgetNames[index]);
  SetUnavailable(widget.instance_pointer, reason);
  SetUnavailable(widget.vtable_pointer, reason);
  SetUnavailable(widget.exists, reason);
  UnavailableMany(reason, widget.local_visible, widget.effective_visible,
                  widget.enabled, widget.focused, widget.modal_blocking,
                  widget.screen_x, widget.screen_y, widget.screen_width,
                  widget.screen_height, widget.scroll_min, widget.scroll_max,
                  widget.scroll_value);
}

void InitializePromotionProgressEnvelope(
    const ZhongguoPromotionSourceProgressRequestV1 &request,
    const game::ZhongguoCaseFrameV1 *frame,
    game::ZhongguoPromotionSourceProgressV1 &output) {
  output = {};
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  if (frame != nullptr) {
    output.date_raw = frame->date_raw;
    output.paused = frame->paused;
    output.player_character_id = frame->played_character_id;
  }
  for (std::size_t index = 0; index < output.widgets.size(); ++index) {
    InitializePromotionProgressWidget(output.widgets[index], index,
                                      "snapshot_unavailable");
  }
}

void SetPromotionProgressUnavailable(
    game::ZhongguoPromotionSourceProgressV1 &output,
    std::string_view reason, bool same_frame_ready = false) {
  output.status = game::ZhongguoPromotionSourceProgressStatusV1::unavailable;
  output.readiness = {};
  output.readiness.same_frame_ready = same_frame_ready;
  output.unavailable_reason.assign(reason);
}

std::string PromotionTopLevelProbeReason(
    const ZhongguoPromotionSourceProgressNativeEnvironmentV1 &environment,
    const ZhongguoPromotionSourceProgressAccessV1 &access) {
  std::string reason{"widget_not_instantiated:custom_top_level_probe="};
  if (environment.offline_fixture_function_overrides) {
    reason += "offline_fixture";
    return reason;
  }
  void *context = nullptr;
  void *owner = nullptr;
  if (!ResolveGuiContextAndOwner(environment, access, context, owner)) {
    reason += "gui_owner_unavailable";
    return reason;
  }
  constexpr std::array<std::string_view, 3> comparison_names{
      "zg361_scoreboard_window", "zg361_decision_bridge_window",
      "zg361_mechanism_bridge_window"};
  bool found_any = false;
  for (const auto comparison : comparison_names) {
    std::string name{comparison};
    void *const widget = CallFindTopLevelWidget(
        environment.find_top_level_widget, owner, &name);
    if (widget != nullptr && WidgetNameEquals(access, widget, comparison)) {
      if (found_any) reason.push_back(',');
      reason.append(comparison);
      found_any = true;
    }
  }
  if (!found_any) reason += "none";
  reason += ":native_top_level_probe=";
  constexpr std::array<std::string_view, 4> native_names{
      "hud_bottom", "ingame_topbar", "war_overview_window",
      "console_window"};
  found_any = false;
  for (const auto comparison : native_names) {
    std::string name{comparison};
    void *const widget = CallFindTopLevelWidget(
        environment.find_top_level_widget, owner, &name);
    if (widget != nullptr && WidgetNameEquals(access, widget, comparison)) {
      if (found_any) reason.push_back(',');
      reason.append(comparison);
      found_any = true;
    }
  }
  if (!found_any) reason += "none";
  reason += ":global_tree_probe=";
  void *global_root = nullptr;
  if (!ReadValue(access, owner, kZhongguoGuiOwnerRootWidgetOffset,
                 global_root) ||
      global_root == nullptr) {
    reason += "root_unavailable";
    return reason;
  }
  constexpr std::array<std::string_view, 3> global_tree_names{
      "zg361_promotion_source_bridge_window", "hud_bottom",
      "ingame_topbar"};
  found_any = false;
  for (const auto comparison : global_tree_names) {
    void *const widget = FindDescendant(access, global_root, comparison);
    if (widget != nullptr) {
      if (found_any) reason.push_back(',');
      reason.append(comparison);
      found_any = true;
    }
  }
  if (!found_any) reason += "none";
  return reason;
}

bool FindPromotionProgressWidgets(
    const ZhongguoPromotionSourceProgressNativeEnvironmentV1 &environment,
    const ZhongguoPromotionSourceProgressAccessV1 &access,
    std::array<void *, kZhongguoPromotionSourceProgressV1WidgetNames.size()>
        &widgets) noexcept {
  widgets = {};
  void *context = nullptr;
  void *owner = nullptr;
  if (!ResolveGuiContextAndOwner(environment, access, context, owner)) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) {
    if (access.find_fixed_widget == nullptr) return false;
    for (std::size_t index = 0; index < widgets.size(); ++index) {
      widgets[index] = access.find_fixed_widget(
          access.context, kZhongguoPromotionSourceProgressV1WidgetNames[index]);
    }
    return true;
  }
  std::string window_name{
      kZhongguoPromotionSourceProgressV1WidgetNames.front()};
  void *window = CallFindTopLevelWidget(environment.find_top_level_widget,
                                        owner, &window_name);
  if (window == nullptr ||
      !WidgetNameEquals(access, window,
                        kZhongguoPromotionSourceProgressV1WidgetNames[0])) {
    window = nullptr;
    void *global_root = nullptr;
    if (ReadValue(access, owner, kZhongguoGuiOwnerRootWidgetOffset,
                  global_root) &&
        global_root != nullptr) {
      window = FindDescendant(
          access, global_root,
          kZhongguoPromotionSourceProgressV1WidgetNames[0]);
    }
    if (window == nullptr) {
      widgets[0] = nullptr;
      return true;
    }
  }
  widgets[0] = window;
  for (std::size_t index = 1; index < widgets.size(); ++index) {
    widgets[index] = FindDescendant(
        access, window, kZhongguoPromotionSourceProgressV1WidgetNames[index]);
  }
  return true;
}

bool DecodePromotionProgressWidgets(
    const ZhongguoPromotionSourceProgressAccessV1 &access,
    const std::array<void *,
                     kZhongguoPromotionSourceProgressV1WidgetNames.size()>
        &pointers,
    game::ZhongguoPromotionSourceProgressV1 &output) {
  bool complete = true;
  for (std::size_t index = 0; index < pointers.size(); ++index) {
    auto &widget = output.widgets[index];
    SetAvailable(widget.exists, pointers[index] != nullptr);
    if (pointers[index] == nullptr) {
      complete = false;
      UnavailableMany("widget_not_instantiated", widget.instance_pointer,
                      widget.vtable_pointer, widget.local_visible,
                      widget.effective_visible, widget.enabled);
    } else {
      void *vtable = nullptr;
      bool local = false;
      bool effective = false;
      bool enabled = false;
      if (!ReadValue(access, pointers[index], 0, vtable) || vtable == nullptr ||
          !ReadLocalVisible(access, pointers[index], local) ||
          !ReadEffectiveVisible(access, pointers[index], effective) ||
          !ReadEffectiveEnabled(access, pointers[index], enabled)) {
        return false;
      }
      SetAvailable(widget.instance_pointer, FormatPointer(pointers[index]));
      SetAvailable(widget.vtable_pointer, FormatPointer(vtable));
      SetAvailable(widget.local_visible, local);
      SetAvailable(widget.effective_visible, effective);
      SetAvailable(widget.enabled, enabled);
    }
    SetUnavailable(widget.focused, "focus_owner_abi_not_frozen");
    SetUnavailable(widget.modal_blocking, "modal_blocking_abi_not_frozen");
    UnavailableMany("screen_rect_abi_not_frozen", widget.screen_x,
                    widget.screen_y, widget.screen_width,
                    widget.screen_height);
    UnavailableMany("scroll_abi_not_frozen", widget.scroll_min,
                    widget.scroll_max, widget.scroll_value);
  }
  output.readiness.exact_widget_set_ready = complete;
  return true;
}

void AppendProgressJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char current : value) {
    if (current == '"' || current == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(current));
    } else if (current < 0x20) {
      output += "\\u00";
      output.push_back(hex[(current >> 4U) & 0x0FU]);
      output.push_back(hex[current & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(current));
    }
  }
  output.push_back('"');
}

template <typename Value, typename Append>
void AppendProgressTyped(std::string &output,
                         const game::ZhongguoTypedValueV1<Value> &field,
                         Append append) {
  output += "{\"status\":";
  AppendProgressJsonString(output, field.available ? "available" : "unavailable");
  output += ",\"value\":";
  if (field.available && field.value.has_value()) {
    append(output, *field.value);
  } else {
    output += "null";
  }
  output += ",\"unavailable_reason\":";
  if (field.available) {
    output += "null";
  } else {
    AppendProgressJsonString(output, field.unavailable_reason);
  }
  output.push_back('}');
}

void AppendProgressWidget(
    std::string &output,
    const game::ZhongguoScoreboardWidgetStateV1 &widget) {
  output += "{\"stable_identity\":";
  AppendProgressJsonString(output, widget.stable_identity);
  output += ",\"runtime_name\":";
  AppendProgressJsonString(output, widget.runtime_name);
  output += ",\"instance_pointer\":";
  AppendProgressTyped(output, widget.instance_pointer,
                      [](std::string &target, const std::string &value) {
                        AppendProgressJsonString(target, value);
                      });
  output += ",\"vtable_pointer\":";
  AppendProgressTyped(output, widget.vtable_pointer,
                      [](std::string &target, const std::string &value) {
                        AppendProgressJsonString(target, value);
                      });
  output += ",\"exists\":";
  AppendProgressTyped(output, widget.exists,
                      [](std::string &target, bool value) {
                        target += value ? "true" : "false";
                      });
  output += ",\"effective_visible\":";
  AppendProgressTyped(output, widget.effective_visible,
                      [](std::string &target, bool value) {
                        target += value ? "true" : "false";
                      });
  output += ",\"enabled\":";
  AppendProgressTyped(output, widget.enabled,
                      [](std::string &target, bool value) {
                        target += value ? "true" : "false";
                      });
  output.push_back('}');
}

} // namespace

game::ReadZhongguoPromotionSourceProgressResultV1
ReadZhongguoPromotionSourceProgressV1(
    const ZhongguoPromotionSourceProgressNativeEnvironmentV1 &environment,
    const ZhongguoPromotionSourceProgressAccessV1 &access,
    const ZhongguoPromotionSourceProgressRequestV1 &request,
    game::ZhongguoPromotionSourceProgressV1 &output) noexcept {
  try {
    InitializePromotionProgressEnvelope(request, nullptr, output);
    if (request.expected_snapshot_revision == 0 ||
        !ValidNonce(request.request_nonce) || !EnvironmentIsExact(environment)) {
      SetPromotionProgressUnavailable(output, "unsupported_build");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetPromotionProgressUnavailable(output, "requires_application_main");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    if (environment.offline_fixture_function_overrides &&
        (access.validate_character == nullptr ||
         access.find_fixed_widget == nullptr ||
         access.resolve_fixture_gui == nullptr)) {
      SetPromotionProgressUnavailable(output, "fixture_access_incomplete");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    game::ZhongguoCaseFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetPromotionProgressUnavailable(output, "state_changed");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    InitializePromotionProgressEnvelope(request, &before, output);
    if (before.snapshot_revision != request.expected_snapshot_revision ||
        !before.paused) {
      SetPromotionProgressUnavailable(output, "requires_stable_paused_frame");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    if (!before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0 ||
        !ValidateCharacter(environment, access, before.played_character_id)) {
      SetPromotionProgressUnavailable(output, "played_owner_unavailable");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    output.readiness.player_binding_ready = true;
    std::array<void *, kZhongguoPromotionSourceProgressV1WidgetNames.size()>
        first{};
    std::array<void *, kZhongguoPromotionSourceProgressV1WidgetNames.size()>
        second{};
    if (!FindPromotionProgressWidgets(environment, access, first)) {
      SetPromotionProgressUnavailable(output, "gui_root_unavailable");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    output.readiness.gui_root_ready = true;
    if (!DecodePromotionProgressWidgets(access, first, output)) {
      SetPromotionProgressUnavailable(output, "widget_state_unavailable");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    if (!output.readiness.exact_widget_set_ready) {
      SetPromotionProgressUnavailable(
          output, first[0] == nullptr
                      ? PromotionTopLevelProbeReason(environment, access)
                      : "widget_not_instantiated:promotion_root_present");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    game::ZhongguoPromotionSourceProgressV1 second_state{};
    InitializePromotionProgressEnvelope(request, &before, second_state);
    if (!FindPromotionProgressWidgets(environment, access, second) ||
        !DecodePromotionProgressWidgets(access, second, second_state)) {
      SetPromotionProgressUnavailable(output, "widget_state_unavailable");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    game::ZhongguoCaseFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first != second || output.widgets != second_state.widgets) {
      SetPromotionProgressUnavailable(output, "state_changed");
      return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
    }
    output.readiness.same_frame_ready = true;
    output.readiness.query_ready = true;
    output.readiness.production_live_ready = false;
    output.status = game::ZhongguoPromotionSourceProgressStatusV1::available;
    output.unavailable_reason.clear();
    return game::ReadZhongguoPromotionSourceProgressResultV1::available;
  } catch (...) {
    SetPromotionProgressUnavailable(output, "internal_error");
    return game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
  }
}

std::string SerializeZhongguoPromotionSourceProgressV1(
    const game::ZhongguoPromotionSourceProgressV1 &progress) {
  std::string output = "{\"schema_version\":1,\"status\":";
  AppendProgressJsonString(
      output,
      progress.status == game::ZhongguoPromotionSourceProgressStatusV1::available
          ? "available"
          : "unavailable");
  output += ",\"capability\":";
  AppendProgressJsonString(output, kZhongguoPromotionSourceProgressV1Capability);
  output += ",\"source_backend_id\":";
  AppendProgressJsonString(output, kZhongguoPromotionSourceProgressV1BackendId);
  output += ",\"request_nonce\":";
  AppendProgressJsonString(output, progress.request_nonce);
  output += ",\"snapshot_revision\":" +
            std::to_string(progress.snapshot_revision);
  output += ",\"date_raw\":" + std::to_string(progress.date_raw);
  output += ",\"paused\":";
  output += progress.paused ? "true" : "false";
  output += ",\"player_character_id\":" +
            std::to_string(progress.player_character_id);
  output += ",\"widgets\":[";
  for (std::size_t index = 0; index < progress.widgets.size(); ++index) {
    if (index != 0) output.push_back(',');
    AppendProgressWidget(output, progress.widgets[index]);
  }
  output += "]";
  output += ",\"readiness\":{\"player_binding_ready\":";
  output += progress.readiness.player_binding_ready ? "true" : "false";
  output += ",\"gui_root_ready\":";
  output += progress.readiness.gui_root_ready ? "true" : "false";
  output += ",\"exact_widget_set_ready\":";
  output += progress.readiness.exact_widget_set_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += progress.readiness.same_frame_ready ? "true" : "false";
  output += ",\"query_ready\":";
  output += progress.readiness.query_ready ? "true" : "false";
  output += ",\"production_live_ready\":";
  output += progress.readiness.production_live_ready ? "true" : "false";
  output += "},\"unavailable_reason\":";
  if (progress.unavailable_reason.empty()) {
    output += "null";
  } else {
    AppendProgressJsonString(output, progress.unavailable_reason);
  }
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_11906
