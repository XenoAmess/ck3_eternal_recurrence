#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <windows.h>

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

bool ResolveGuiOwner(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
                     const ZhongguoScoreboardAccessV1 &access,
                     void *&owner) noexcept {
  owner = nullptr;
  void *first = nullptr;
  void *second = nullptr;
  void *third = nullptr;
  void *context = nullptr;
  return ReadBytes(access, environment.gui_global_slot, &first,
                   sizeof(first)) &&
         ReadValue(access, first, kZhongguoGuiChainFirstOffset, second) &&
         ReadValue(access, second, kZhongguoGuiChainSecondOffset, third) &&
         ReadValue(access, third, kZhongguoGuiContextOffset, context) &&
         ReadValue(access, context, kZhongguoGuiOwnerOffset, owner) &&
         owner != nullptr;
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
    std::array<void *, kZhongguoScoreboardStateV1WidgetNames.size()>
        &widgets) noexcept {
  widgets = {};
  if (environment.offline_fixture_function_overrides) {
    if (access.find_fixed_widget == nullptr) return false;
    for (std::size_t index = 0; index < widgets.size(); ++index) {
      widgets[index] = access.find_fixed_widget(
          access.context, kZhongguoScoreboardStateV1WidgetNames[index]);
    }
    return true;
  }
  void *owner = nullptr;
  if (!ResolveGuiOwner(environment, access, owner)) return false;
  std::string window_name{kZhongguoScoreboardStateV1WidgetNames[1]};
  void *window = CallFindTopLevelWidget(environment.find_top_level_widget,
                                        owner, &window_name);
  widgets[1] = window;
  if (window == nullptr ||
      !WidgetNameEquals(access, window,
                        kZhongguoScoreboardStateV1WidgetNames[1])) {
    widgets[1] = nullptr;
    return true;
  }
  for (std::size_t index = 0; index < widgets.size(); ++index) {
    if (index != 1) {
      widgets[index] = FindDescendant(
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
  visible = (flags & kZhongguoWidgetHiddenMask) == 0;
  return true;
}

bool ReadEffectiveVisible(const ZhongguoScoreboardAccessV1 &access,
                          void *widget, bool &visible) noexcept {
  visible = true;
  std::array<void *, kMaximumWidgetDepth> seen{};
  std::size_t count = 0;
  void *current = widget;
  while (current != nullptr) {
    if (count >= seen.size()) return false;
    for (std::size_t index = 0; index < count; ++index) {
      if (seen[index] == current) return false;
    }
    seen[count++] = current;
    bool local = false;
    if (!ReadLocalVisible(access, current, local)) return false;
    visible = visible && local;
    void *parent = nullptr;
    if (!ReadValue(access, current, kZhongguoWidgetParentOffset, parent)) {
      return false;
    }
    current = parent;
  }
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
      if (!ReadValue(access, pointers[index], 0, vtable) || vtable == nullptr ||
          !ReadLocalVisible(access, pointers[index], local) ||
          !ReadEffectiveVisible(access, pointers[index], effective)) {
        return false;
      }
      SetAvailable(widget.instance_pointer, FormatPointer(pointers[index]));
      SetAvailable(widget.vtable_pointer, FormatPointer(vtable));
      SetAvailable(widget.local_visible, local);
      SetAvailable(widget.effective_visible, effective);
    }
    SetUnavailable(widget.enabled, "enabled_state_abi_not_frozen");
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
         access.find_fixed_widget == nullptr)) {
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
    output.readiness.player_binding_ready = true;

    std::array<void *, kZhongguoScoreboardStateV1WidgetNames.size()>
        first_widgets{};
    std::array<void *, kZhongguoScoreboardStateV1WidgetNames.size()>
        second_widgets{};
    RawRows first_rows{};
    RawRows second_rows{};
    if (!FindFixedWidgets(environment, access, first_widgets)) {
      SetTopUnavailable(output, "gui_root_unavailable");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    output.readiness.gui_root_ready = true;
    if (!ReadAllowlistedRows(environment, access, before.played_character_id,
                             first_rows) ||
        !FindFixedWidgets(environment, access, second_widgets) ||
        !ReadAllowlistedRows(environment, access, before.played_character_id,
                             second_rows)) {
      SetTopUnavailable(output, "state_projection_unavailable");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    game::ZhongguoCaseFrameV1 after{};
    if (!access.capture_frame(access.context, after) || before != after ||
        first_widgets != second_widgets || first_rows != second_rows) {
      SetTopUnavailable(output, "state_changed");
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    output.readiness.same_frame_ready = true;
    if (!DecodeWidgets(access, first_widgets, output)) {
      SetTopUnavailable(output, "widget_state_unavailable", true);
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    if (!DecodeAcl(environment, access, first_rows,
                   before.played_character_id, output)) {
      SetTopUnavailable(output, "acl_inconsistent", true);
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }
    if (!output.readiness.entry_window_state_ready) {
      SetTopUnavailable(output, "widget_not_instantiated", true);
      return game::ReadZhongguoScoreboardStateResultV1::unavailable;
    }

    output.readiness.state_acl_query_ready =
        output.readiness.player_binding_ready &&
        output.readiness.gui_root_ready &&
        output.readiness.entry_window_state_ready &&
        output.readiness.acl_ready && output.readiness.same_frame_ready;
    output.readiness.full_widget_gate_ready = false;
    output.readiness.production_live_ready = false;
    output.status = game::ZhongguoScoreboardStateStatusV1::available;
    output.unavailable_reason.clear();
    return game::ReadZhongguoScoreboardStateResultV1::available;
  } catch (...) {
    SetTopUnavailable(output, "internal_error");
    return game::ReadZhongguoScoreboardStateResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
