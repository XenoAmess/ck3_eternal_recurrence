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

// Registration IsHost 0x33590 -> callback 0xA9C020:
// (byte[base+0x5CC14D0] & 0xFD) == 0.
// Registration HasGameStartedForTheFirstTime 0x2A240 -> 0xA98B20:
// game-state slot 0x5C68C50 non-null && state[0xC3] == 0.
// These are the actual stock Next/Prev/Apply visible predicates, not a preset.
struct ControlPass {
  NativePass model;
  const void *game_state = nullptr;
  std::uint8_t host_flags = 0, started_flag = 0, root_flags = 0;
  bool operator==(const ControlPass &) const = default;
};

bool ExactEnvironment(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
                      const void *root) noexcept {
  return environment.exact_build_admitted && environment.module_base != 0 &&
         environment.gui_abi_revision == GuiAbiRevisionV1::crozier12003 &&
         reinterpret_cast<std::uintptr_t>(environment.gui_global_slot) ==
             environment.module_base + kCrozierGuiGlobalSlotRva && root;
}

bool ReadControlPass(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
                     const ZhongguoScoreboardAccessV1 &access, const void *root,
                     ControlPass &pass, std::string &reason) {
  const auto module = environment.module_base;
  if (!ReadPass(environment, access, root, pass.model, reason)) return false;
  if (!ReadAt(access, root, kZhongguoWidgetHiddenFlagsOffset, pass.root_flags) ||
      !ReadBytes(access, reinterpret_cast<const void *>(module + 0x5CC14D0),
                 &pass.host_flags, sizeof(pass.host_flags)) ||
      !ReadBytes(access, reinterpret_cast<const void *>(module + 0x5C68C50),
                 &pass.game_state, sizeof(pass.game_state)) ||
      (pass.game_state && !ReadAt(access, pass.game_state, 0xC3,
                                 pass.started_flag))) {
    reason = "game_rules_native_control_predicates_unverified";
    return false;
  }
  return true;
}

bool ReadStableControl(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
                       const ZhongguoScoreboardAccessV1 &access, const void *root,
                       ControlPass &pass, std::string &reason) {
  if (!ExactEnvironment(environment, root)) {
    reason = "exact_12003_game_rules_environment_unverified"; return false;
  }
  ControlPass before{};
  if (!ReadControlPass(environment, access, root, before, reason) ||
      !ReadControlPass(environment, access, root, pass, reason)) return false;
  if (!(before == pass)) {
    reason = "game_rules_control_changed_during_observation"; return false;
  }
  return true;
}

FrontendGameRulesControlV1 ProjectControl(const ControlPass &pass) {
  FrontendGameRulesControlV1 result;
  result.ready = true;
  result.window_visible =
      (pass.root_flags & kZhongguoWidgetEffectiveHiddenMask) == 0;
  result.window_enabled =
      (pass.root_flags & kZhongguoWidgetEffectiveDisabledMask) == 0;
  result.is_host = (pass.host_flags & 0xFD) == 0;
  result.game_has_started = pass.game_state && pass.started_flag == 0;
  result.may_edit = result.window_visible && result.window_enabled &&
                    result.is_host && !result.game_has_started;
  return result;
}

struct ChoicePass {
  const void *data = nullptr;
  std::uint32_t capacity = 0, count = 0;
  std::vector<const void *> pointers;
  std::vector<std::string> keys;
  bool operator==(const ChoicePass &) const = default;
};

bool ReadChoices(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
                 const ZhongguoScoreboardAccessV1 &access, const void *rule,
                 ChoicePass &choices, std::string &reason) {
  if (!ReadAt(access, rule, 0x40, choices.data) ||
      !ReadAt(access, rule, 0x48, choices.capacity) ||
      !ReadAt(access, rule, 0x4C, choices.count) ||
      choices.count == 0 || choices.count > choices.capacity ||
      choices.count > 512 || !choices.data) {
    reason = "game_rule_option_collection_unverified"; return false;
  }
  for (std::uint32_t index = 0; index < choices.count; ++index) {
    const void *setting = nullptr, *parent = nullptr;
    std::uint32_t marker = 0;
    std::string key;
    if (!ReadAt(access, choices.data, static_cast<std::size_t>(index) * 8, setting) ||
        !IsTypedObject(access, environment.module_base, setting,
                       kSettingVtable, kSettingType) ||
        !ReadAt(access, setting, 0x38, marker) || marker != kDatabaseObjectMarker ||
        !ReadAt(access, setting, 0x40, parent) || parent != rule ||
        !ReadKey(access, setting, key)) {
      reason = "game_rule_option_setting_unverified"; return false;
    }
    if (std::find(choices.pointers.begin(), choices.pointers.end(), setting) !=
            choices.pointers.end() ||
        std::find(choices.keys.begin(), choices.keys.end(), key) !=
            choices.keys.end()) {
      reason = "game_rule_duplicate_option"; return false;
    }
    choices.pointers.push_back(setting); choices.keys.push_back(std::move(key));
  }
  return true;
}

bool ScriptKey(std::string_view key) noexcept {
  if (key.empty() || key.size() > kMaximumKeyBytes) return false;
  for (const auto c : key) if (!((c >= 'a' && c <= 'z') ||
      (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_')) return false;
  return true;
}

bool BuildChoice(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
                 const ZhongguoScoreboardAccessV1 &access, const void *root,
                 std::string_view rule_key, std::string_view expected,
                 std::string_view desired, ControlPass &control,
                 ChoicePass &options, std::size_t &record_index,
                 FrontendGameRuleChoiceV1 &result) {
  if (!ScriptKey(rule_key) || !ScriptKey(expected) || !ScriptKey(desired)) {
    result.unavailable_reason = "invalid_game_rule_script_key"; return false;
  }
  if (!ReadStableControl(environment, access, root, control,
                         result.unavailable_reason)) return false;
  if (!ProjectControl(control).may_edit) {
    result.unavailable_reason = "game_rules_edit_predicates_not_satisfied";
    return false;
  }
  const auto &model = control.model;
  auto found = std::find_if(model.values.begin(), model.values.end(),
      [&](const auto &value) { return value.rule_key == rule_key; });
  if (found == model.values.end()) {
    result.unavailable_reason = "game_rule_key_absent_from_actual_model"; return false;
  }
  record_index = static_cast<std::size_t>(found - model.values.begin());
  if (found->selected_setting_key != expected) {
    result.unavailable_reason = "game_rule_expected_current_setting_changed";
    return false;
  }
  ChoicePass before{};
  const auto &pair = model.pointers[record_index];
  if (!ReadChoices(environment, access, pair[0], before, result.unavailable_reason) ||
      !ReadChoices(environment, access, pair[0], options, result.unavailable_reason))
    return false;
  if (!(before == options)) {
    result.unavailable_reason = "game_rule_options_changed_during_observation";
    return false;
  }
  ControlPass after_options{};
  if (!ReadControlPass(environment, access, root, after_options,
                       result.unavailable_reason) || !(control == after_options)) {
    result.unavailable_reason = "game_rule_model_changed_while_reading_options";
    return false;
  }
  const auto current = std::find(options.pointers.begin(), options.pointers.end(), pair[1]);
  const auto target = std::find(options.keys.begin(), options.keys.end(), desired);
  if (current == options.pointers.end()) {
    result.unavailable_reason = "game_rule_current_setting_absent_from_options";
    return false;
  }
  if (target == options.keys.end()) {
    result.unavailable_reason = "game_rule_desired_setting_absent_from_options";
    return false;
  }
  const auto current_index = static_cast<std::size_t>(current - options.pointers.begin());
  const auto target_index = static_cast<std::size_t>(target - options.keys.begin());
  result.rule_key.assign(rule_key);
  result.current_setting_key.assign(expected);
  result.desired_setting_key.assign(desired);
  result.option_keys = options.keys;
  result.next_count = static_cast<std::uint32_t>(
      (target_index + options.count - current_index) % options.count);
  result.ready = true;
  return true;
}

enum class StockRuleCall { next, apply, hide };

bool CallsAdmitted(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
                   const ZhongguoScoreboardAccessV1 &access,
                   const FrontendGameRulesCallsV1 &calls) noexcept {
  if (environment.offline_fixture_function_overrides)
    return access.read_memory != nullptr;
  return access.read_memory == nullptr && calls.context == nullptr &&
         calls.next == nullptr && calls.apply == nullptr && calls.hide == nullptr;
}

// Leaf SEH wrappers contain no C++ objects requiring unwinding. Stock bound
// callbacks invoke exactly these methods with their real record/controller.
bool CallStockRuleMethod(std::uintptr_t module, StockRuleCall kind,
                         void *target) noexcept {
#if defined(_MSC_VER)
  __try {
    const auto rva = kind == StockRuleCall::next ? 0x21DD6F0u :
                     kind == StockRuleCall::apply ? 0x21DBD20u : 0xBE9CF0u;
    const auto method = reinterpret_cast<void (__fastcall *)(void *)>(module+rva);
    method(target); return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  (void)module; (void)kind; (void)target; return false;
#endif
}

bool InvokeRuleMethod(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
                      const FrontendGameRulesCallsV1 &calls,
                      StockRuleCall kind, const void *target) noexcept {
  if (environment.offline_fixture_function_overrides) {
    const auto fn = kind == StockRuleCall::next ? calls.next :
                    kind == StockRuleCall::apply ? calls.apply : calls.hide;
    return fn && fn(calls.context, const_cast<void *>(target));
  }
  return CallStockRuleMethod(environment.module_base, kind,
                             const_cast<void *>(target));
}

// The exact stock installed getter chain: initialization 0x228DE36 creates
// std::_Func_impl_no_alloc< const CGameRuleInstance*(*)() > (VT 0x46BF988)
// with function 0x27F82F0 at +8, registered in std::function slot 0x5CB3D78.
// Virtual +0x10 is 0x9B4F50 -> jmp [holder+8]. The installed getter itself
// reads state-slot 0x5C68C50: non-null -> state+0xF0; else app+0x268.
// Read this exact pure getter chain without invoking an arbitrary virtual call.
struct AppliedPass {
  const void *holder = nullptr, *getter = nullptr, *application = nullptr;
  const void *game_state = nullptr, *instance = nullptr, *data = nullptr;
  std::uint32_t capacity = 0, count = 0;
  std::vector<std::array<const void *, 2>> pointers;
  std::vector<FrontendGameRuleSelectionV1> values;
  bool operator==(const AppliedPass &) const = default;
};

bool ReadAppliedPass(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
                     const ZhongguoScoreboardAccessV1 &access,
                     AppliedPass &pass, std::string &reason) {
  const auto module = environment.module_base;
  const void *application_vtable = nullptr;
  if (!ReadAt(access, environment.gui_global_slot, 0, pass.application) ||
      !ReadAt(access, pass.application, 0, application_vtable) ||
      reinterpret_cast<std::uintptr_t>(application_vtable) != module+kApplicationVtable ||
      !ReadBytes(access, reinterpret_cast<const void *>(module+0x5CB3D78),
                 &pass.holder, sizeof(pass.holder)) ||
      !IsTypedObject(access, module, pass.holder, 0x46BF988, 0x59A4770) ||
      !ReadAt(access, pass.holder, 8, pass.getter) ||
      reinterpret_cast<std::uintptr_t>(pass.getter) != module+0x27F82F0 ||
      !ReadBytes(access, reinterpret_cast<const void *>(module+0x5C68C50),
                 &pass.game_state, sizeof(pass.game_state))) {
    reason = "applied_game_rules_selection_service_unverified"; return false;
  }
  if (!(pass.game_state ? ReadAt(access, pass.game_state, 0xF0, pass.instance)
                        : ReadAt(access, pass.application, 0x268, pass.instance)) ||
      !IsTypedObject(access, module, pass.instance, 0x491BFF8, 0x5B964B0)) {
    reason = "applied_game_rule_instance_unverified"; return false;
  }
  if (!ReadAt(access, pass.instance, 8, pass.data) ||
      !ReadAt(access, pass.instance, 0x10, pass.capacity) ||
      !ReadAt(access, pass.instance, 0x14, pass.count) ||
      pass.count == 0 || pass.count > pass.capacity || pass.count > kMaximumRules ||
      !pass.data) {
    reason = "applied_game_rule_setting_collection_unverified"; return false;
  }
  for (std::uint32_t i = 0; i < pass.count; ++i) {
    const void *setting = nullptr, *rule = nullptr;
    std::uint32_t setting_marker = 0, rule_marker = 0;
    FrontendGameRuleSelectionV1 value;
    if (!ReadAt(access, pass.data, static_cast<std::size_t>(i)*8, setting) ||
        !IsTypedObject(access, module, setting, kSettingVtable, kSettingType) ||
        !ReadAt(access, setting, 0x38, setting_marker) || setting_marker != kDatabaseObjectMarker ||
        !ReadAt(access, setting, 0x40, rule) ||
        !IsTypedObject(access, module, rule, kRuleVtable, kRuleType) ||
        !ReadAt(access, rule, 0x38, rule_marker) || rule_marker != kDatabaseObjectMarker ||
        !ReadKey(access, rule, value.rule_key) ||
        !ReadKey(access, setting, value.selected_setting_key)) {
      reason = "applied_game_rule_selected_setting_unverified"; return false;
    }
    pass.pointers.push_back({rule, setting}); pass.values.push_back(std::move(value));
  }
  auto values = pass.values;
  std::sort(values.begin(), values.end(), [](const auto &a, const auto &b) {
    return a.rule_key < b.rule_key;
  });
  if (std::adjacent_find(values.begin(), values.end(), [](const auto &a, const auto &b) {
        return a.rule_key == b.rule_key;
      }) != values.end()) {
    reason = "applied_game_rule_duplicate_rule_key"; return false;
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

bool ProbeFrontendGameRulesControlV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, const void *root,
    FrontendGameRulesControlV1 &output) noexcept {
  output = {};
  try {
    ControlPass pass;
    if (!ReadStableControl(environment, access, root, pass,
                           output.unavailable_reason)) return true;
    output = ProjectControl(pass); return true;
  } catch (...) {
    output = {}; output.unavailable_reason = "game_rules_control_allocation_failed";
    return false;
  }
}

bool ProbeFrontendGameRuleChoiceV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, const void *root,
    std::string_view rule_key, std::string_view expected,
    std::string_view desired, FrontendGameRuleChoiceV1 &output) noexcept {
  output = {};
  try {
    ControlPass control; ChoicePass options; std::size_t index = 0;
    BuildChoice(environment, access, root, rule_key, expected, desired,
                control, options, index, output);
    return true;
  } catch (...) {
    output = {}; output.unavailable_reason = "game_rule_choice_allocation_failed";
    return false;
  }
}

bool SelectFrontendGameRuleV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, const void *root,
    std::string_view rule_key, std::string_view expected,
    std::string_view desired, const FrontendGameRulesCallsV1 &calls,
    FrontendGameRulesMutationV1 &output) noexcept {
  output = {};
  try {
    if (!CallsAdmitted(environment, access, calls)) {
      output.unavailable_reason = "game_rules_native_call_access_unverified";
      return true;
    }
    ControlPass control{}; ChoicePass options{}; std::size_t index = 0;
    FrontendGameRuleChoiceV1 plan;
    if (!BuildChoice(environment, access, root, rule_key, expected, desired,
                      control, options, index, plan)) {
      output.unavailable_reason = plan.unavailable_reason; return true;
    }
    auto current = std::find(options.pointers.begin(), options.pointers.end(),
                              control.model.pointers[index][1]);
    auto option_index = static_cast<std::size_t>(current-options.pointers.begin());
    for (std::uint32_t step = 0; step < plan.next_count; ++step) {
      ControlPass before{}; ChoicePass choices_before{};
      if (!ReadStableControl(environment, access, root, before,
                             output.unavailable_reason) || !(before == control) ||
          !ProjectControl(before).may_edit ||
          !ReadChoices(environment, access, before.model.pointers[index][0],
                        choices_before, output.unavailable_reason) ||
          !(choices_before == options)) {
        output.unavailable_reason = "game_rule_owner_model_changed_before_next";
        return true;
      }
      const auto record = reinterpret_cast<const void *>(
          reinterpret_cast<std::uintptr_t>(control.model.records) + index*16);
      output.native_invoked = true;
      ++output.native_next_calls;
      if (!InvokeRuleMethod(environment, calls, StockRuleCall::next, record)) {
        output.unavailable_reason = "game_rule_native_next_failed"; return true;
      }
      option_index = (option_index + 1) % options.count;
      control.model.pointers[index][1] = options.pointers[option_index];
      control.model.values[index].selected_setting_key = options.keys[option_index];
      ControlPass after{};
      if (!ReadStableControl(environment, access, root, after,
                             output.unavailable_reason) || !(after == control)) {
        output.unavailable_reason = "game_rule_native_next_postcondition_failed";
        return true;
      }
    }
    output.selection_verified = control.model.values[index].selected_setting_key == desired;
    output.ready = output.selection_verified;
    if (!output.ready) output.unavailable_reason = "game_rule_target_not_observed";
    return true;
  } catch (...) {
    output.ready = false;
    output.unavailable_reason = "game_rule_selection_allocation_failed";
    return false;
  }
}

bool ApplyAndHideFrontendGameRulesV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, const void *root,
    bool apply, const FrontendGameRulesCallsV1 &calls,
    FrontendGameRulesMutationV1 &output) noexcept {
  output = {};
  try {
    if (!CallsAdmitted(environment, access, calls)) {
      output.unavailable_reason = "game_rules_native_call_access_unverified";
      return true;
    }
    ControlPass control{};
    if (!ReadStableControl(environment, access, root, control,
                           output.unavailable_reason)) return true;
    const auto eligibility = ProjectControl(control);
    if (!eligibility.window_visible || !eligibility.window_enabled ||
        (apply && !eligibility.may_edit)) {
      output.unavailable_reason = "game_rules_action_predicates_not_satisfied";
      return true;
    }
    if (apply) {
      output.native_invoked = true; output.apply_invoked = true;
      if (!InvokeRuleMethod(environment, calls, StockRuleCall::apply, control.model.owner)) {
        output.unavailable_reason = "game_rules_native_apply_failed"; return true;
      }
      ControlPass after_apply{};
      if (!ReadStableControl(environment, access, root, after_apply,
                             output.unavailable_reason) || !(after_apply == control)) {
        output.unavailable_reason = "game_rules_owner_model_changed_after_apply";
        return true;
      }
    }
    output.native_invoked = true; output.hide_invoked = true;
    if (!InvokeRuleMethod(environment, calls, StockRuleCall::hide, control.model.owner)) {
      output.unavailable_reason = "game_rules_native_hide_failed"; return true;
    }
    output.ready = true;
    // Neither return nor this same-ticket action establishes applied rules or
    // an independently observed closed window. Later queries must prove both.
    return true;
  } catch (...) {
    output.ready = false;
    output.unavailable_reason = "game_rules_action_allocation_failed";
    return false;
  }
}

std::string SerializeFrontendGameRulesControlV1(const FrontendGameRulesControlV1 &o) {
  std::string s = "{\"schema\":\"frontend_game_rules_window_v1\",\"schema_version\":1,"
      "\"read_only\":true,\"uses_ocr\":false,\"uses_mouse\":false,\"uses_keyboard\":false,"
      "\"applied_settings_proven\":false,\"game_version\":\"1.20.0.3\","
      "\"executable_sha256\":\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\","
      "\"source\":\"CJominiGameRulesGui.owner_root_and_stock_predicates\",\"ready\":";
  s += o.ready ? "true" : "false";
  s += ",\"unavailable_reason\":\"" + o.unavailable_reason + "\"";
  for (const auto &field : std::array<std::pair<const char *, bool>,6>{{
       {"window_visible",o.window_visible},{"window_enabled",o.window_enabled},
       {"is_host",o.is_host},{"game_has_started",o.game_has_started},
       {"may_edit",o.may_edit},{"window_closed_proven",o.ready && !o.window_visible}}}) {
    s += ",\""; s += field.first; s += "\":"; s += field.second ? "true" : "false";
  }
  return s + "}";
}

std::string SerializeFrontendGameRulesMutationV1(
    FrontendGameRulesMutationKindV1 kind, const FrontendGameRulesMutationV1 &r) {
  std::string s = "{\"schema\":\"frontend_game_rules_mutation_v1\",\"schema_version\":1,"
      "\"read_only\":false,\"uses_ocr\":false,\"uses_mouse\":false,\"uses_keyboard\":false,"
      "\"applied_settings_proven\":false,\"window_closed_proven\":false,"
      "\"game_version\":\"1.20.0.3\","
      "\"executable_sha256\":\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\","
      "\"source\":\"CJominiGameRulesGui.stock_methods\",\"action\":\"";
  s += kind == FrontendGameRulesMutationKindV1::select ? "select" :
       kind == FrontendGameRulesMutationKindV1::apply_and_hide ? "apply_and_hide" : "hide";
  s += "\",\"ready\":"; s += r.ready ? "true" : "false";
  s += ",\"unavailable_reason\":\"" + r.unavailable_reason + "\"";
  for (const auto &field : std::array<std::pair<const char *, bool>,4>{{
       {"native_invoked",r.native_invoked},{"selection_verified",r.selection_verified},
       {"apply_invoked",r.apply_invoked},{"hide_invoked",r.hide_invoked}}}) {
    s += ",\""; s += field.first; s += "\":"; s += field.second ? "true" : "false";
  }
  return s + ",\"native_next_calls\":" + std::to_string(r.native_next_calls) + "}";
}

bool ProbeFrontendAppliedGameRulesV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access,
    FrontendAppliedGameRulesV1 &output) noexcept {
  output = {};
  try {
    if (!environment.exact_build_admitted || !environment.module_base ||
        environment.gui_abi_revision != GuiAbiRevisionV1::crozier12003 ||
        reinterpret_cast<std::uintptr_t>(environment.gui_global_slot) !=
            environment.module_base + kCrozierGuiGlobalSlotRva) {
      output.unavailable_reason = "exact_12003_game_rules_environment_unverified";
      return true;
    }
    AppliedPass before{}, after{};
    if (!ReadAppliedPass(environment, access, before, output.unavailable_reason) ||
        !ReadAppliedPass(environment, access, after, output.unavailable_reason)) return true;
    if (!(before == after)) {
      output.unavailable_reason = "applied_game_rules_changed_during_observation";
      return true;
    }
    output.selections = std::move(after.values);
    std::sort(output.selections.begin(), output.selections.end(), [](const auto &a, const auto &b) {
      return a.rule_key < b.rule_key;
    });
    output.ready = true; return true;
  } catch (...) {
    output = {}; output.unavailable_reason = "applied_game_rules_allocation_failed";
    return false;
  }
}

std::string SerializeFrontendAppliedGameRulesV1(const FrontendAppliedGameRulesV1 &o) {
  std::string s = "{\"schema\":\"frontend_applied_game_rules_v1\",\"schema_version\":1,"
      "\"read_only\":true,\"uses_ocr\":false,\"uses_mouse\":false,\"uses_keyboard\":false,"
      "\"game_version\":\"1.20.0.3\","
      "\"executable_sha256\":\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\","
      "\"source\":\"CGameRuleInstance.selected_settings\",\"ready\":";
  s += o.ready ? "true" : "false";
  s += ",\"applied_settings_proven\":"; s += o.ready ? "true" : "false";
  s += ",\"unavailable_reason\":\"" + o.unavailable_reason + "\",\"selection_count\":";
  s += std::to_string(o.ready ? o.selections.size() : 0) + ",\"selections\":[";
  bool first = true;
  if (o.ready) for (const auto &p : o.selections) {
    if (!first) s += ',';
    first = false;
    s += "{\"rule_key\":\"" + p.rule_key + "\",\"selected_setting_key\":\"" + p.selected_setting_key + "\"}";
  }
  return s+"]}";
}

} // namespace xar::ck3_11906
