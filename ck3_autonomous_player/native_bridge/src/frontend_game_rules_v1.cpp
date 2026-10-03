#include "xar_bridge/frontend_game_rules_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

// Exact 1.20.0.3 94B55397... evidence: AccessGameRules 0xA98990,
// AccessNamedGameRule 0x21DB470, GuiGameRule.GetSetting 0x21DE790,
// model population 0x21DBF60, setting ctor 0x36658D0, rule ctor 0x3666120.
constexpr std::uintptr_t kImageSize = 0x61C5000;
constexpr std::uintptr_t kApplicationVtable = 0x449BDA8;
constexpr std::uintptr_t kRulesVtable = 0x46B79B0;
constexpr std::uintptr_t kRulesType = 0x59929F8;
constexpr std::uintptr_t kRuleVtable = 0x491BE58;
constexpr std::uintptr_t kRuleType = 0x560C140;
constexpr std::uintptr_t kSettingVtable = 0x491C3D8;
constexpr std::uintptr_t kSettingType = 0x55C96F8;
constexpr std::uint32_t kDatabaseObjectMarker = 0x4744624F;
constexpr std::uint32_t kMaximumRules = 4096;
constexpr std::size_t kMaximumKeyBytes = 96;

bool ReadBytes(const ZhongguoScoreboardAccessV1 &access,
               const void *address, void *output, std::size_t size) noexcept {
  if (!address || !output || size == 0) return false;
  if (access.read_memory) {
    return access.read_memory(access.context, address, output, size);
  }
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return false;
#endif
}

template <typename T>
bool ReadAt(const ZhongguoScoreboardAccessV1 &access, const void *base,
            std::size_t offset, T &output) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  if (value == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - value)
    return false;
  return ReadBytes(access, reinterpret_cast<const void *>(value + offset),
                   &output, sizeof(output));
}

bool IsTypedObject(const ZhongguoScoreboardAccessV1 &access,
                   std::uintptr_t module, const void *object,
                   std::uintptr_t expected_vtable,
                   std::uintptr_t expected_type) noexcept {
  const void *vtable = nullptr;
  if (!ReadAt(access, object, 0, vtable) ||
      reinterpret_cast<std::uintptr_t>(vtable) != module + expected_vtable)
    return false;
  const void *locator = nullptr;
  if (!ReadBytes(access, reinterpret_cast<const void *>(
          module + expected_vtable - sizeof(void *)), &locator, sizeof(locator)))
    return false;
  const auto col = reinterpret_cast<std::uintptr_t>(locator);
  if (col < module || col - module > kImageSize - 24) return false;
  std::array<std::uint32_t, 6> fields{};
  return ReadBytes(access, locator, fields.data(), sizeof(fields)) &&
         fields[0] == 1 && fields[1] == 0 && fields[3] == expected_type &&
         fields[5] == col - module;
}

bool ReadKey(const ZhongguoScoreboardAccessV1 &access, const void *object,
             std::string &output) {
  std::uint64_t length = 0, capacity = 0;
  if (!ReadAt(access, object, 0x28, length) ||
      !ReadAt(access, object, 0x30, capacity) || length == 0 ||
      length > kMaximumKeyBytes || length > capacity ||
      (capacity < 16 && capacity != 15)) return false;
  const void *characters = nullptr;
  if (capacity < 16) {
    characters = reinterpret_cast<const void *>(
        reinterpret_cast<std::uintptr_t>(object) + 0x18);
  } else if (!ReadAt(access, object, 0x18, characters) || !characters) {
    return false;
  }
  std::array<char, kMaximumKeyBytes + 1> bytes{};
  if (!ReadBytes(access, characters, bytes.data(),
                 static_cast<std::size_t>(length) + 1) || bytes[length] != 0)
    return false;
  for (std::size_t i = 0; i < length; ++i) {
    const auto c = bytes[i];
    if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
          (c >= '0' && c <= '9') || c == '_')) return false;
  }
  output.assign(bytes.data(), static_cast<std::size_t>(length));
  return true;
}

struct NativePass {
  const void *application = nullptr;
  const void *owner = nullptr;
  const void *root = nullptr;
  const void *records = nullptr;
  std::uint32_t capacity = 0, count = 0;
  std::vector<std::array<const void *, 2>> pointers;
  std::vector<FrontendGameRuleSelectionV1> values;
  bool operator==(const NativePass &) const = default;
};

bool ReadPass(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
              const ZhongguoScoreboardAccessV1 &access, const void *root,
              NativePass &pass, std::string &reason) {
  const auto module = environment.module_base;
  const void *application_vtable = nullptr;
  if (!ReadAt(access, environment.gui_global_slot, 0, pass.application) ||
      !ReadAt(access, pass.application, 0, application_vtable) ||
      reinterpret_cast<std::uintptr_t>(application_vtable) !=
          module + kApplicationVtable ||
      !ReadAt(access, pass.application, 0xA38, pass.owner) ||
      !IsTypedObject(access, module, pass.owner, kRulesVtable, kRulesType)) {
    reason = "current_game_rules_owner_unverified";
    return false;
  }
  if (!ReadAt(access, pass.owner, 0x60, pass.root) || pass.root != root) {
    reason = "game_rules_owner_root_mismatch";
    return false;
  }
  if (!ReadAt(access, pass.owner, 0x98, pass.records) ||
      !ReadAt(access, pass.owner, 0xA0, pass.capacity) ||
      !ReadAt(access, pass.owner, 0xA4, pass.count) || pass.count == 0 ||
      pass.count > pass.capacity || pass.count > kMaximumRules || !pass.records) {
    reason = "game_rules_selection_collection_unverified";
    return false;
  }
  pass.pointers.reserve(pass.count);
  pass.values.reserve(pass.count);
  for (std::uint32_t index = 0; index < pass.count; ++index) {
    std::array<const void *, 2> pair{};
    const void *setting_rule = nullptr;
    std::uint32_t rule_marker = 0, setting_marker = 0;
    FrontendGameRuleSelectionV1 value;
    if (!ReadAt(access, pass.records, static_cast<std::size_t>(index) * 16,
                pair) ||
        !IsTypedObject(access, module, pair[0], kRuleVtable, kRuleType) ||
        !IsTypedObject(access, module, pair[1], kSettingVtable, kSettingType) ||
        !ReadAt(access, pair[0], 0x38, rule_marker) ||
        !ReadAt(access, pair[1], 0x38, setting_marker) ||
        rule_marker != kDatabaseObjectMarker ||
        setting_marker != kDatabaseObjectMarker ||
        !ReadAt(access, pair[1], 0x40, setting_rule) || setting_rule != pair[0] ||
        !ReadKey(access, pair[0], value.rule_key) ||
        !ReadKey(access, pair[1], value.selected_setting_key)) {
      reason = "game_rules_selected_pair_unverified";
      return false;
    }
    pass.pointers.push_back(pair);
    pass.values.push_back(std::move(value));
  }
  auto sorted = pass.values;
  std::sort(sorted.begin(), sorted.end(), [](const auto &left, const auto &right) {
    return left.rule_key < right.rule_key;
  });
  if (std::adjacent_find(sorted.begin(), sorted.end(),
          [](const auto &left, const auto &right) {
            return left.rule_key == right.rule_key;
          }) != sorted.end()) {
    reason = "game_rules_duplicate_rule_key";
    return false;
  }
  return true;
}

} // namespace

bool ProbeFrontendGameRulesV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, const void *game_rules_root,
    FrontendGameRulesObservationV1 &output) noexcept {
  output = {};
  try {
    if (!environment.exact_build_admitted || environment.module_base == 0 ||
        environment.gui_abi_revision != GuiAbiRevisionV1::crozier12003 ||
        reinterpret_cast<std::uintptr_t>(environment.gui_global_slot) !=
            environment.module_base + kCrozierGuiGlobalSlotRva ||
        !game_rules_root) {
      output.unavailable_reason = "exact_12003_game_rules_environment_unverified";
      return true;
    }
    NativePass before{}, after{};
    if (!ReadPass(environment, access, game_rules_root, before,
                  output.unavailable_reason) ||
        !ReadPass(environment, access, game_rules_root, after,
                  output.unavailable_reason)) return true;
    if (!(before == after)) {
      output.unavailable_reason = "game_rules_selection_changed_during_observation";
      return true;
    }
    output.selections = std::move(after.values);
    std::sort(output.selections.begin(), output.selections.end(),
              [](const auto &left, const auto &right) {
                return left.rule_key < right.rule_key;
              });
    output.ready = true;
    return true;
  } catch (...) {
    output = {};
    output.unavailable_reason = "game_rules_observation_allocation_failed";
    return false;
  }
}

std::string SerializeFrontendGameRulesV1(
    const FrontendGameRulesObservationV1 &observation) {
  // All strings originate from checked script-key bytes or fixed provider
  // reasons; no addresses or caller strings cross the public result boundary.
  std::string result = "{\"schema\":\"frontend_game_rule_selections_v1\","
      "\"schema_version\":1,\"read_only\":true,\"uses_ocr\":false,"
      "\"uses_mouse\":false,\"uses_keyboard\":false,"
      "\"applied_settings_proven\":false,"
      "\"game_version\":\"1.20.0.3\",\"executable_sha256\":"
      "\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\","
      "\"source\":\"CJominiGameRulesGui.current_selections\",\"ready\":";
  result += observation.ready ? "true" : "false";
  result += ",\"unavailable_reason\":\"";
  result += observation.unavailable_reason;
  result += "\",\"selection_count\":";
  result += std::to_string(observation.ready ? observation.selections.size() : 0);
  result += ",\"selections\":[";
  bool first = true;
  if (observation.ready) for (const auto &pair : observation.selections) {
    if (!first) result += ',';
    first = false;
    result += "{\"rule_key\":\"" + pair.rule_key +
              "\",\"selected_setting_key\":\"" + pair.selected_setting_key + "\"}";
  }
  result += "]}";
  return result;
}

} // namespace xar::ck3_11906
