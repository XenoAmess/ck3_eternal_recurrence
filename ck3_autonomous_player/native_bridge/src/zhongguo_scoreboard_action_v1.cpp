#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include "xar_bridge/zhongguo_promotion_source_progress_v1.hpp"

#include <array>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <string_view>

#if defined(_MSC_VER)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#endif

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kWindowIndex = 1;
constexpr std::size_t kModalIndex = 2;
constexpr std::array<std::size_t, 3> kEntryIndices{4, 5, 6};
constexpr std::array<std::size_t, 3> kTabIndices{7, 8, 9};
constexpr std::size_t kHeaderCloseIndex = 14;
constexpr std::array<std::string_view, 3> kTabs{"managed", "received",
                                                        "system"};

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t index = 0; index < value.size(); ++index) {
    const char current = value[index];
    const bool alpha = (current >= 'A' && current <= 'Z') ||
                       (current >= 'a' && current <= 'z');
    const bool digit = current >= '0' && current <= '9';
    const bool punctuation = current == '.' || current == '_' ||
                             current == ':' || current == '-';
    if ((!alpha && !digit && !punctuation) ||
        (index == 0 && !alpha && !digit)) {
      return false;
    }
  }
  return true;
}

bool ValidPointer(std::string_view value) noexcept {
  if (value.size() < 3 || value[0] != '0' || value[1] != 'x') return false;
  for (std::size_t index = 2; index < value.size(); ++index) {
    const char current = value[index];
    if (!((current >= '0' && current <= '9') ||
          (current >= 'A' && current <= 'F'))) {
      return false;
    }
  }
  return true;
}

bool ValidProviderSessionId(std::string_view value) noexcept {
  if (value.size() != 32) return false;
  for (const char current : value) {
    if (!((current >= '0' && current <= '9') ||
          (current >= 'A' && current <= 'F'))) {
      return false;
    }
  }
  return true;
}

bool ValidFingerprint(std::string_view value) noexcept {
  if (value.size() != 64) return false;
  for (const char current : value) {
    if (!((current >= '0' && current <= '9') ||
          (current >= 'A' && current <= 'F'))) {
      return false;
    }
  }
  return true;
}

bool ParsePointer(std::string_view value, void *&output) noexcept {
  output = nullptr;
  if (!ValidPointer(value)) return false;
  std::uint64_t parsed = 0;
  const auto converted = std::from_chars(value.data() + 2,
                                         value.data() + value.size(), parsed,
                                         16);
  if (converted.ec != std::errc{} || converted.ptr != value.data() + value.size() ||
      parsed == 0 || parsed > std::numeric_limits<std::uintptr_t>::max()) {
    return false;
  }
  output = reinterpret_cast<void *>(static_cast<std::uintptr_t>(parsed));
  return true;
}

bool ReadBytes(const void *address, void *output, std::size_t size) noexcept {
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

template <typename T>
bool ReadValue(const void *base, std::size_t offset, T &output) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  if (address == 0 ||
      address > std::numeric_limits<std::uintptr_t>::max() - offset) {
    return false;
  }
  return ReadBytes(reinterpret_cast<const void *>(address + offset), &output,
                   sizeof(output));
}

bool CallableAddress(
    const ZhongguoScoreboardActionDispatchEnvironmentV1 &environment,
    void *address) noexcept {
  if (address == nullptr) return false;
  if (environment.offline_fixture_function_overrides) return true;
  const auto value = reinterpret_cast<std::uintptr_t>(address);
  return environment.module_base != 0 && value >= environment.module_base &&
         value - environment.module_base < kZhongguoExactImageSize;
}

bool DispatchEnvironmentIsExact(
    const ZhongguoScoreboardActionDispatchEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted ||
      environment.gui_global_slot == nullptr ||
      environment.activate_shortcut == nullptr ||
      environment.is_strict_descendant == nullptr ||
      environment.button_base_slot13 == nullptr) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) return true;
  return environment.module_base != 0 &&
         reinterpret_cast<std::uintptr_t>(environment.gui_global_slot) ==
             environment.module_base + kZhongguoGuiGlobalSlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.activate_shortcut) ==
             environment.module_base + kZhongguoShortcutManagerActivateRva &&
         reinterpret_cast<std::uintptr_t>(environment.is_strict_descendant) ==
             environment.module_base + kZhongguoStrictDescendantRva &&
         reinterpret_cast<std::uintptr_t>(environment.button_base_slot13) ==
             environment.module_base + kZhongguoButtonBaseSlot13Rva;
}

bool ResolveGuiContext(
    const ZhongguoScoreboardActionDispatchEnvironmentV1 &environment,
    void *&context) noexcept {
  context = nullptr;
  void *first = nullptr;
  void *second = nullptr;
  void *third = nullptr;
  return ReadBytes(environment.gui_global_slot, &first, sizeof(first)) &&
         ReadValue(first, kZhongguoGuiChainFirstOffset, second) &&
         ReadValue(second, kZhongguoGuiChainSecondOffset, third) &&
         ReadValue(third, kZhongguoGuiContextOffset, context) &&
         context != nullptr;
}

bool CallStrictDescendant(
    NativeZhongguoStrictDescendantV1 function, void *root,
    void *target) noexcept {
#if defined(_MSC_VER)
  __try {
    return function(root, target);
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  return function(root, target);
#endif
}

bool ValidateModalAdmission(
    const ZhongguoScoreboardActionDispatchEnvironmentV1 &environment,
    void *context, void *target) noexcept {
  void **receivers = nullptr;
  std::int32_t count = 0;
  if (!ReadValue(context, kZhongguoGuiModalVectorOffset, receivers) ||
      !ReadValue(context, kZhongguoGuiModalCountOffset, count) || count < 0 ||
      count > kZhongguoMaximumModalReceivers ||
      (count != 0 && receivers == nullptr)) {
    return false;
  }
  bool any_effectively_visible = false;
  for (std::int32_t index = count - 1; index >= 0; --index) {
    void *receiver = nullptr;
    std::uint8_t flags = 0;
    if (!ReadValue(receivers, static_cast<std::size_t>(index) * sizeof(void *),
                   receiver) ||
        receiver == nullptr ||
        !ReadValue(receiver, kZhongguoWidgetHiddenFlagsOffset, flags)) {
      return false;
    }
    if ((flags & kZhongguoWidgetEffectiveHiddenMask) == 0) {
      any_effectively_visible = true;
      break;
    }
  }
  if (!any_effectively_visible) return true;
  void *root = nullptr;
  if (!ReadValue(receivers,
                 static_cast<std::size_t>(count - 1) * sizeof(void *), root) ||
      root == nullptr) {
    return false;
  }
  return CallStrictDescendant(environment.is_strict_descendant, root, target);
}

bool ValidateCallbackGroup(
    const ZhongguoScoreboardActionDispatchEnvironmentV1 &environment,
    void *target) noexcept {
  std::int32_t primary_count = 0;
  if (!ReadValue(target, kZhongguoPrimaryCallbackGroupOffset +
                             kZhongguoCallbackGroupCountOffset,
                 primary_count) ||
      primary_count < 0 || primary_count > kZhongguoMaximumCallbacks) {
    return false;
  }
  const auto group_offset = primary_count > 0
                                ? kZhongguoPrimaryCallbackGroupOffset
                                : kZhongguoFallbackCallbackGroupOffset;
  std::int32_t count = primary_count;
  if (primary_count == 0 &&
      (!ReadValue(target, group_offset + kZhongguoCallbackGroupCountOffset,
                  count) ||
       count < 0 || count > kZhongguoMaximumCallbacks)) {
    return false;
  }
  if (count == 0) return false;
  void *data = nullptr;
  if (!ReadValue(target, group_offset + kZhongguoCallbackGroupDataOffset,
                 data) ||
      data == nullptr) {
    return false;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    const auto row_offset = static_cast<std::size_t>(index) *
                            kZhongguoCallbackStride;
    void *callback = nullptr;
    void *vtable = nullptr;
    void *slot2 = nullptr;
    if (!ReadValue(data, row_offset + kZhongguoCallbackObjectOffset,
                   callback) ||
        callback == nullptr || !ReadValue(callback, 0, vtable) ||
        vtable == nullptr ||
        !ReadValue(vtable, kZhongguoCallbackVtableSlot2Offset, slot2) ||
        !CallableAddress(environment, slot2)) {
      return false;
    }
  }
  return true;
}

bool CallShortcutActivate(
    NativeZhongguoShortcutManagerActivateV1 function, void *manager,
    void *target, bool &native_handled) noexcept {
  native_handled = false;
  alignas(void *) std::array<std::byte, kZhongguoShortcutCStringSize> text{};
  const std::uint64_t capacity = kZhongguoShortcutCStringEmptyCapacity;
  std::memcpy(text.data() + kZhongguoShortcutCStringCapacityOffset, &capacity,
              sizeof(capacity));
  alignas(void *) std::array<std::byte, kZhongguoShortcutPimplSize> pimpl{};
  std::memcpy(pimpl.data() + kZhongguoShortcutPimplTargetOffset, &target,
              sizeof(target));
#if defined(_MSC_VER)
  __try {
    native_handled = function(manager, 0, text.data(), pimpl.data());
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  native_handled = function(manager, 0, text.data(), pimpl.data());
  return true;
#endif
}

std::string_view ActionName(game::ZhongguoScoreboardActionV1 value) noexcept {
  switch (value) {
  case game::ZhongguoScoreboardActionV1::open:
    return "open";
  case game::ZhongguoScoreboardActionV1::switch_managed:
    return "switch-managed";
  case game::ZhongguoScoreboardActionV1::switch_received:
    return "switch-received";
  case game::ZhongguoScoreboardActionV1::switch_system:
    return "switch-system";
  case game::ZhongguoScoreboardActionV1::close:
    return "close";
  case game::ZhongguoScoreboardActionV1::reopen:
    return "reopen";
  }
  return {};
}

game::ZhongguoScoreboardActionResultV1 Reject(
    const game::ZhongguoScoreboardActionRequestV1 &request,
    const game::ZhongguoScoreboardActionBindingV1 &binding,
    std::string_view reason,
    game::ZhongguoScoreboardActionAckV1 &ack) noexcept {
  ack = {};
  ack.request_nonce = request.request_nonce;
  ack.action = request.action;
  ack.source = binding;
  ack.rejection_reason.assign(reason);
  return game::ZhongguoScoreboardActionResultV1::rejected;
}

bool AvailableBool(const game::ZhongguoTypedBooleanV1 &field,
                   bool &value) noexcept {
  if (!field.available || !field.value.has_value()) return false;
  value = *field.value;
  return true;
}

bool AvailableString(const game::ZhongguoTypedStringV1 &field,
                     std::string_view &value) noexcept {
  if (!field.available || !field.value.has_value() ||
      !ValidPointer(*field.value)) {
    return false;
  }
  value = *field.value;
  return true;
}

bool FixedProjection(const game::ZhongguoScoreboardStateV1 &source) noexcept {
  for (std::size_t index = 0; index < source.widgets.size(); ++index) {
    if (source.widgets[index].stable_identity !=
            kZhongguoScoreboardStateV1WidgetIdentities[index] ||
        source.widgets[index].runtime_name !=
            kZhongguoScoreboardStateV1WidgetNames[index]) {
      return false;
    }
  }
  return true;
}

bool AppendNumber(std::string &output, std::uint64_t value) {
  std::array<char, 32> buffer{};
  const auto converted =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (converted.ec != std::errc{}) return false;
  output.append(buffer.data(), converted.ptr);
  return true;
}

bool AppendSigned(std::string &output, std::int32_t value) {
  std::array<char, 16> buffer{};
  const auto converted =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (converted.ec != std::errc{}) return false;
  output.append(buffer.data(), converted.ptr);
  return true;
}

void AppendJsonString(std::string &output, std::string_view value) {
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

} // namespace

ZhongguoScoreboardActionDispatchEnvironmentV1
BindZhongguoScoreboardActionDispatchEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  ZhongguoScoreboardActionDispatchEnvironmentV1 environment{};
  environment.module_base = module_base;
  environment.exact_build_admitted = exact_build_admitted;
  if (module_base != 0 && exact_build_admitted) {
    environment.gui_global_slot = reinterpret_cast<void **>(
        module_base + kZhongguoGuiGlobalSlotRva);
    environment.activate_shortcut =
        reinterpret_cast<NativeZhongguoShortcutManagerActivateV1>(
            module_base + kZhongguoShortcutManagerActivateRva);
    environment.is_strict_descendant =
        reinterpret_cast<NativeZhongguoStrictDescendantV1>(
            module_base + kZhongguoStrictDescendantRva);
    environment.button_base_slot13 = reinterpret_cast<void *>(
        module_base + kZhongguoButtonBaseSlot13Rva);
  }
  return environment;
}

bool DispatchZhongguoScoreboardActionNativeV1(
    void *opaque_environment, game::ZhongguoScoreboardActionV1 action,
    std::string_view stable_identity, std::string_view runtime_name,
    std::string_view instance_pointer, std::string_view vtable_pointer,
    bool &native_handled) noexcept {
  native_handled = false;
  try {
    auto *environment = static_cast<
        ZhongguoScoreboardActionDispatchEnvironmentV1 *>(opaque_environment);
    if (environment == nullptr || !DispatchEnvironmentIsExact(*environment) ||
        action == game::ZhongguoScoreboardActionV1::reopen ||
        stable_identity.empty() || stable_identity != runtime_name) {
      return false;
    }
    void *target = nullptr;
    void *expected_vtable = nullptr;
    if (!ParsePointer(instance_pointer, target) ||
        !ParsePointer(vtable_pointer, expected_vtable)) {
      return false;
    }
    void *context = nullptr;
    void *manager = nullptr;
    void *manager_context = nullptr;
    void *target_context = nullptr;
    void *actual_vtable = nullptr;
    void *slot13 = nullptr;
    void *slot10 = nullptr;
    std::uint8_t flags = 0;
    if (!ResolveGuiContext(*environment, context) ||
        !ReadValue(context, kZhongguoGuiShortcutManagerOffset, manager) ||
        manager == nullptr || !ReadValue(manager, 0, manager_context) ||
        manager_context != context ||
        !ReadValue(target, kZhongguoWidgetGuiContextOffset, target_context) ||
        target_context != context ||
        !ReadValue(target, kZhongguoWidgetHiddenFlagsOffset, flags) ||
        (flags & kZhongguoWidgetShortcutRejectedMask) != 0 ||
        !ReadValue(target, 0, actual_vtable) ||
        actual_vtable != expected_vtable ||
        !ReadValue(actual_vtable, 13 * sizeof(void *), slot13) ||
        slot13 != environment->button_base_slot13 ||
        !ReadValue(actual_vtable, 10 * sizeof(void *), slot10) ||
        !CallableAddress(*environment, slot10) ||
        !ValidateCallbackGroup(*environment, target) ||
        !ValidateModalAdmission(*environment, context, target)) {
      return false;
    }
    // The native boolean is only a diagnostic: a prehandler may mutate the
    // event's +0x14 gate or return a value that does not identify whether the
    // product callback ran.  Successful invocation therefore yields an ACK
    // with verification pending regardless of native_handled; only a later
    // independent provider observation may prove the postcondition.
    return CallShortcutActivate(environment->activate_shortcut, manager, target,
                                native_handled);
  } catch (...) {
    native_handled = false;
    return false;
  }
}

game::ZhongguoScoreboardActionResultV1 ExecuteZhongguoScoreboardActionV1(
    const game::ZhongguoScoreboardActionRequestV1 &request,
    const game::ZhongguoScoreboardActionBindingV1 &binding,
    const game::ZhongguoScoreboardStateV1 &source,
    const ZhongguoScoreboardActionAccessV1 &access,
    game::ZhongguoScoreboardActionAckV1 &ack) noexcept {
  const auto action_name = ActionName(request.action);
  if (action_name.empty() || !ValidNonce(request.request_nonce) ||
      request.expected_native_revision == 0 ||
      request.expected_connection_generation == 0 ||
      request.expected_player_character_id <= 0 ||
      !ValidProviderSessionId(request.expected_provider_session_id) ||
      request.expected_observation_sequence == 0 ||
      request.expected_observed_state_revision == 0 ||
      !ValidFingerprint(request.expected_tree_fingerprint_v1) ||
      !ValidFingerprint(request.expected_semantic_fingerprint_v1) ||
      !ValidPointer(request.expected_window_instance_pointer) ||
      !ValidPointer(request.expected_target_instance_pointer) ||
      !ValidPointer(request.expected_target_vtable_pointer)) {
    return Reject(request, binding, "invalid_request", ack);
  }
  if (request.expected_observation_sequence ==
          std::numeric_limits<std::uint64_t>::max() ||
      request.expected_observed_state_revision ==
          std::numeric_limits<std::uint64_t>::max()) {
    return Reject(request, binding, "revision_overflow", ack);
  }
  if (binding.revision != request.expected_revision) {
    return Reject(request, binding, "revision_mismatch", ack);
  }
  if (binding.native_revision != request.expected_native_revision ||
      source.snapshot_revision != request.expected_native_revision) {
    return Reject(request, binding, "native_revision_mismatch", ack);
  }
  if (binding.connection_generation !=
      request.expected_connection_generation) {
    return Reject(request, binding, "connection_generation_mismatch", ack);
  }
  if (binding.player_character_id != request.expected_player_character_id ||
      source.player_character_id != request.expected_player_character_id) {
    return Reject(request, binding, "player_binding_mismatch", ack);
  }
  if (binding.provider_session_id != request.expected_provider_session_id ||
      source.provider_session_id != request.expected_provider_session_id) {
    return Reject(request, binding, "provider_session_mismatch", ack);
  }
  if (binding.observation_sequence != request.expected_observation_sequence ||
      source.observation_sequence != request.expected_observation_sequence) {
    return Reject(request, binding, "observation_sequence_mismatch", ack);
  }
  if (binding.observed_state_revision !=
          request.expected_observed_state_revision ||
      source.observed_state_revision !=
          request.expected_observed_state_revision) {
    return Reject(request, binding, "observed_state_revision_mismatch", ack);
  }
  if (binding.tree_fingerprint_v1 !=
          request.expected_tree_fingerprint_v1 ||
      source.tree_fingerprint_v1 != request.expected_tree_fingerprint_v1) {
    return Reject(request, binding, "tree_fingerprint_mismatch", ack);
  }
  if (binding.semantic_fingerprint_v1 !=
          request.expected_semantic_fingerprint_v1 ||
      source.semantic_fingerprint_v1 !=
          request.expected_semantic_fingerprint_v1) {
    return Reject(request, binding, "semantic_fingerprint_mismatch", ack);
  }
  if (source.status != game::ZhongguoScoreboardStateStatusV1::available ||
      !source.paused || source.date_raw != binding.date_raw ||
      !source.readiness.player_binding_ready ||
      !source.readiness.gui_root_ready ||
      !source.readiness.entry_window_state_ready ||
      !source.readiness.acl_ready || !source.readiness.same_frame_ready ||
      !source.readiness.state_acl_query_ready || !FixedProjection(source)) {
    return Reject(request, binding, "source_state_unavailable", ack);
  }

  const auto &window = source.widgets[kWindowIndex];
  bool window_exists = false;
  std::string_view window_instance;
  if (!AvailableBool(window.exists, window_exists) || !window_exists ||
      !AvailableString(window.instance_pointer, window_instance)) {
    return Reject(request, binding, "window_not_instantiated", ack);
  }
  if (window_instance != request.expected_window_instance_pointer) {
    return Reject(request, binding, "window_instance_mismatch", ack);
  }
  bool modal_visible = false;
  if (!AvailableBool(source.widgets[kModalIndex].effective_visible,
                     modal_visible)) {
    return Reject(request, binding, "modal_visibility_unavailable", ack);
  }

  std::size_t target_index = source.widgets.size();
  std::size_t active_tab_index = 0;
  bool active_tab_available = false;
  if (request.action == game::ZhongguoScoreboardActionV1::open) {
    if (modal_visible) {
      return Reject(request, binding, "scoreboard_already_open", ack);
    }
    std::size_t visible_count = 0;
    for (std::size_t index = 0; index < kEntryIndices.size(); ++index) {
      bool visible = false;
      if (!AvailableBool(source.widgets[kEntryIndices[index]].effective_visible,
                         visible)) {
        return Reject(request, binding, "entry_visibility_unavailable", ack);
      }
      if (visible) {
        ++visible_count;
        target_index = kEntryIndices[index];
        active_tab_index = index;
      }
    }
    if (visible_count != 1) {
      return Reject(request, binding, "entry_target_not_unique", ack);
    }
    active_tab_available = true;
  } else if (request.action ==
                 game::ZhongguoScoreboardActionV1::switch_managed ||
             request.action ==
                 game::ZhongguoScoreboardActionV1::switch_received ||
             request.action ==
                 game::ZhongguoScoreboardActionV1::switch_system) {
    if (!modal_visible) {
      return Reject(request, binding, "scoreboard_not_open", ack);
    }
    active_tab_index =
        request.action == game::ZhongguoScoreboardActionV1::switch_managed
            ? 0
            : request.action ==
                      game::ZhongguoScoreboardActionV1::switch_received
                  ? 1
                  : 2;
    if (active_tab_index == 0 &&
        !source.managed_acl.current_player_can_assess_others) {
      return Reject(request, binding, "managed_acl_denied", ack);
    }
    if (active_tab_index == 1 &&
        !source.received_self_acl.surface_available) {
      return Reject(request, binding, "received_acl_denied", ack);
    }
    bool page_visible = false;
    if (!AvailableBool(source.widgets[10 + active_tab_index].effective_visible,
                       page_visible)) {
      return Reject(request, binding, "active_page_visibility_unavailable", ack);
    }
    if (page_visible) {
      return Reject(request, binding, "action_noop", ack);
    }
    target_index = kTabIndices[active_tab_index];
    active_tab_available = true;
  } else if (request.action == game::ZhongguoScoreboardActionV1::close) {
    if (!modal_visible) {
      return Reject(request, binding, "scoreboard_not_open", ack);
    }
    target_index = kHeaderCloseIndex;
  } else if (request.action == game::ZhongguoScoreboardActionV1::reopen) {
    return Reject(request, binding, "reopen_requires_two_phase_sequence", ack);
  } else {
    return Reject(request, binding, "invalid_request", ack);
  }

  const auto &target = source.widgets[target_index];
  bool exists = false;
  bool visible = false;
  bool enabled = false;
  std::string_view instance;
  std::string_view vtable;
  if (!AvailableBool(target.exists, exists)) {
    return Reject(request, binding, "target_exists_unavailable", ack);
  }
  if (!exists) {
    return Reject(request, binding, "target_not_instantiated", ack);
  }
  if (!AvailableBool(target.effective_visible, visible)) {
    return Reject(request, binding, "target_visibility_unavailable", ack);
  }
  if (!visible) {
    return Reject(request, binding, "target_not_visible", ack);
  }
  if (!AvailableBool(target.enabled, enabled)) {
    return Reject(request, binding, "target_enabled_unavailable", ack);
  }
  if (!enabled) {
    return Reject(request, binding, "target_disabled", ack);
  }
  if (!AvailableString(target.instance_pointer, instance)) {
    return Reject(request, binding, "target_instance_unavailable", ack);
  }
  if (!AvailableString(target.vtable_pointer, vtable)) {
    return Reject(request, binding, "target_vtable_unavailable", ack);
  }
  if (instance != request.expected_target_instance_pointer) {
    return Reject(request, binding, "target_instance_mismatch", ack);
  }
  if (vtable != request.expected_target_vtable_pointer) {
    return Reject(request, binding, "target_vtable_mismatch", ack);
  }
  if (access.dispatch == nullptr) {
    return Reject(request, binding, "action_dispatch_unavailable", ack);
  }
  bool native_handled = false;
  if (!access.dispatch(access.context, request.action, target.stable_identity,
                       target.runtime_name, instance, vtable,
                       native_handled)) {
    return Reject(request, binding, "action_dispatch_rejected", ack);
  }

  ack = {};
  ack.result =
      game::ZhongguoScoreboardActionResultV1::acknowledged_verification_pending;
  ack.accepted = true;
  ack.request_nonce = request.request_nonce;
  ack.action = request.action;
  ack.source = binding;
  ack.window_instance_pointer.assign(window_instance);
  ack.target.stable_identity = target.stable_identity;
  ack.target.runtime_name = target.runtime_name;
  ack.target.instance_pointer.assign(instance);
  ack.target.vtable_pointer.assign(vtable);
  ack.expected_postcondition.minimum_observation_sequence =
      binding.observation_sequence + 1;
  ack.expected_postcondition.minimum_observed_state_revision =
      binding.observed_state_revision + 1;
  ack.expected_postcondition.expected_provider_session_id =
      binding.provider_session_id;
  ack.expected_postcondition.expected_tree_fingerprint_v1 =
      binding.tree_fingerprint_v1;
  ack.expected_postcondition.modal_effective_visible =
      request.action != game::ZhongguoScoreboardActionV1::close;
  ack.expected_postcondition.active_tab_available = active_tab_available;
  if (active_tab_available) {
    ack.expected_postcondition.active_tab.assign(kTabs[active_tab_index]);
  }
  ack.expected_postcondition.list_view_required = active_tab_available;
  ack.expected_postcondition.expected_window_instance_pointer.assign(
      window_instance);
  ack.native_handled = native_handled;
  ack.postcondition_verified = false;
  return ack.result;
}

std::string SerializeZhongguoScoreboardActionAckV1(
    const game::ZhongguoScoreboardActionAckV1 &ack) {
  const auto action = ActionName(ack.action);
  if (ack.result != game::ZhongguoScoreboardActionResultV1::
                        acknowledged_verification_pending ||
      !ack.accepted || !ack.rejection_reason.empty() || action.empty() ||
      !ValidNonce(ack.request_nonce) || ack.source.native_revision == 0 ||
      ack.source.connection_generation == 0 ||
      ack.source.player_character_id <= 0 ||
      !ValidProviderSessionId(ack.source.provider_session_id) ||
      ack.source.observation_sequence == 0 ||
      ack.source.observed_state_revision == 0 ||
      !ValidFingerprint(ack.source.tree_fingerprint_v1) ||
      !ValidFingerprint(ack.source.semantic_fingerprint_v1) ||
      !ValidPointer(ack.window_instance_pointer) ||
      !ValidPointer(ack.target.instance_pointer) ||
      !ValidPointer(ack.target.vtable_pointer) ||
      ack.target.stable_identity != ack.target.runtime_name ||
      !ack.expected_postcondition.requires_independent_query ||
      ack.source.observation_sequence ==
          std::numeric_limits<std::uint64_t>::max() ||
      ack.source.observed_state_revision ==
          std::numeric_limits<std::uint64_t>::max() ||
      ack.expected_postcondition.minimum_observation_sequence !=
          ack.source.observation_sequence + 1 ||
      ack.expected_postcondition.minimum_observed_state_revision !=
          ack.source.observed_state_revision + 1 ||
      ack.expected_postcondition.expected_provider_session_id !=
          ack.source.provider_session_id ||
      ack.expected_postcondition.expected_tree_fingerprint_v1 !=
          ack.source.tree_fingerprint_v1 ||
      ack.expected_postcondition.expected_window_instance_pointer !=
          ack.window_instance_pointer ||
      ack.postcondition_verified) {
    return {};
  }
  std::string output =
      "{\"schema_version\":1,\"status\":"
      "\"acknowledged_verification_pending\",\"accepted\":true,"
      "\"capability\":\"game.command.activate-zhongguo-scoreboard-v1\","
      "\"step\":\"activate-zhongguo-scoreboard-v1\",\"request_nonce\":";
  AppendJsonString(output, ack.request_nonce);
  output += ",\"action\":";
  AppendJsonString(output, action);
  output += ",\"source\":{\"revision\":";
  if (!AppendNumber(output, ack.source.revision)) return {};
  output += ",\"native_revision\":";
  if (!AppendNumber(output, ack.source.native_revision)) return {};
  output += ",\"connection_generation\":";
  if (!AppendNumber(output, ack.source.connection_generation)) return {};
  output += ",\"date_raw\":";
  if (!AppendSigned(output, ack.source.date_raw)) return {};
  output += ",\"player_character_id\":";
  if (!AppendSigned(output, ack.source.player_character_id)) return {};
  output += ",\"provider_session_id\":";
  AppendJsonString(output, ack.source.provider_session_id);
  output += ",\"observation_sequence\":";
  if (!AppendNumber(output, ack.source.observation_sequence)) return {};
  output += ",\"observed_state_revision\":";
  if (!AppendNumber(output, ack.source.observed_state_revision)) return {};
  output += ",\"tree_fingerprint_v1\":";
  AppendJsonString(output, ack.source.tree_fingerprint_v1);
  output += ",\"semantic_fingerprint_v1\":";
  AppendJsonString(output, ack.source.semantic_fingerprint_v1);
  output += ",\"window_instance_pointer\":";
  AppendJsonString(output, ack.window_instance_pointer);
  output += "},\"target\":{\"stable_identity\":";
  AppendJsonString(output, ack.target.stable_identity);
  output += ",\"runtime_name\":";
  AppendJsonString(output, ack.target.runtime_name);
  output += ",\"instance_pointer\":";
  AppendJsonString(output, ack.target.instance_pointer);
  output += ",\"vtable_pointer\":";
  AppendJsonString(output, ack.target.vtable_pointer);
  output +=
      "},\"expected_postcondition\":{\"requires_independent_query\":true,"
      "\"minimum_observation_sequence\":";
  if (!AppendNumber(
          output,
          ack.expected_postcondition.minimum_observation_sequence)) {
    return {};
  }
  output += ",\"minimum_observed_state_revision\":";
  if (!AppendNumber(
          output,
          ack.expected_postcondition.minimum_observed_state_revision)) {
    return {};
  }
  output += ",\"expected_provider_session_id\":";
  AppendJsonString(
      output, ack.expected_postcondition.expected_provider_session_id);
  output += ",\"expected_tree_fingerprint_v1\":";
  AppendJsonString(
      output, ack.expected_postcondition.expected_tree_fingerprint_v1);
  output += ",\"modal_effective_visible\":";
  output += ack.expected_postcondition.modal_effective_visible ? "true" : "false";
  output += ",\"active_tab\":";
  if (ack.expected_postcondition.active_tab_available) {
    AppendJsonString(output, ack.expected_postcondition.active_tab);
  } else {
    output += "null";
  }
  output += ",\"list_view_required\":";
  output += ack.expected_postcondition.list_view_required ? "true" : "false";
  output += ",\"expected_window_instance_pointer\":";
  AppendJsonString(
      output, ack.expected_postcondition.expected_window_instance_pointer);
  output += "},\"native_handled\":";
  output += ack.native_handled ? "true" : "false";
  output +=
      ",\"postcondition_verified\":false,\"provenance\":{"
      "\"game_version\":\"1.19.0.6\","
      "\"executable_sha256\":"
      "\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\","
      "\"backend_id\":\"ck3-1.19.0.6-native-zhongguo-scoreboard-action-v1\","
      "\"consumer_id\":\"xar-autoplayer-zhongguo-scoreboard-action-v1\","
      "\"allowlist_id\":\"zg361-scoreboard-named-widget-action-v1\","
      "\"contract_stage\":\"exact_dispatch_ack_provider_revision_live_unverified\"}}";
  return output;
}

bool DispatchZhongguoReviewNowActionNativeV1(
    void *opaque_environment, std::string_view stable_identity,
    std::string_view runtime_name, std::string_view instance_pointer,
    std::string_view vtable_pointer, bool &native_handled) noexcept {
  // The shared dispatcher does not derive semantic success from this enum; it
  // only rejects the scoreboard-only two-phase `reopen` marker before running
  // the exact widget/vtable/callback/modal admission checks.
  return DispatchZhongguoScoreboardActionNativeV1(
      opaque_environment, game::ZhongguoScoreboardActionV1::open,
      stable_identity, runtime_name, instance_pointer, vtable_pointer,
      native_handled);
}

bool ExecuteZhongguoReviewNowActionV1(
    const game::ZhongguoReviewNowActionRequestV1 &request,
    const game::ZhongguoPromotionSourceProgressV1 &source,
    const ZhongguoReviewNowActionAccessV1 &access,
    game::ZhongguoReviewNowActionAckV1 &ack) noexcept {
  ack = {};
  ack.request_nonce = request.request_nonce;
  ack.source_revision = request.expected_revision;
  ack.source_native_revision = request.expected_native_revision;
  ack.source_connection_generation = request.expected_connection_generation;
  ack.date_raw = source.date_raw;
  ack.player_character_id = source.player_character_id;
  const auto reject = [&](std::string_view reason) {
    ack.rejection_reason.assign(reason);
    return false;
  };
  if (!ValidNonce(request.request_nonce) || request.expected_revision == 0 ||
      request.expected_native_revision == 0 ||
      request.expected_connection_generation == 0 ||
      request.expected_player_character_id <= 0 ||
      source.status !=
          game::ZhongguoPromotionSourceProgressStatusV1::available ||
      !source.paused ||
      source.snapshot_revision != request.expected_native_revision ||
      source.player_character_id != request.expected_player_character_id ||
      !source.readiness.query_ready ||
      !source.readiness.exact_widget_set_ready) {
    return reject("source_progress_unavailable");
  }
  for (std::size_t index = 0; index < source.widgets.size(); ++index) {
    if (source.widgets[index].stable_identity !=
            kZhongguoPromotionSourceProgressV1WidgetIdentities[index] ||
        source.widgets[index].runtime_name !=
            kZhongguoPromotionSourceProgressV1WidgetNames[index]) {
      return reject("fixed_widget_allowlist_drifted");
    }
  }
  bool action_exists = false;
  bool action_visible = false;
  bool action_enabled = false;
  bool b1_visible = false;
  bool central_visible = false;
  bool pp_visible = false;
  std::string_view instance;
  std::string_view vtable;
  const auto &target = source.widgets[1];
  if (!AvailableBool(target.exists, action_exists) || !action_exists ||
      !AvailableBool(target.effective_visible, action_visible) ||
      !action_visible || !AvailableBool(target.enabled, action_enabled) ||
      !action_enabled || !AvailableString(target.instance_pointer, instance) ||
      !AvailableString(target.vtable_pointer, vtable)) {
    return reject("review_now_action_not_available");
  }
  if (!AvailableBool(source.widgets[2].effective_visible, b1_visible) ||
      !AvailableBool(source.widgets[3].effective_visible, central_visible) ||
      !AvailableBool(source.widgets[4].effective_visible, pp_visible)) {
    return reject("progress_witness_unavailable");
  }
  if (b1_visible || central_visible || pp_visible) {
    return reject("promotion_pipeline_already_active");
  }
  if (access.dispatch == nullptr) {
    return reject("action_dispatch_unavailable");
  }
  bool native_handled = false;
  if (!access.dispatch(access.context, target.stable_identity,
                       target.runtime_name, instance, vtable,
                       native_handled)) {
    return reject("action_dispatch_rejected");
  }
  ack.accepted = true;
  ack.target.stable_identity = target.stable_identity;
  ack.target.runtime_name = target.runtime_name;
  ack.target.instance_pointer.assign(instance);
  ack.target.vtable_pointer.assign(vtable);
  ack.expected_postcondition =
      "played_owner_b1_active_on_independent_paused_progress_query";
  ack.native_handled = native_handled;
  ack.postcondition_verified = false;
  ack.rejection_reason.clear();
  return true;
}

std::string SerializeZhongguoReviewNowActionAckV1(
    const game::ZhongguoReviewNowActionAckV1 &ack) {
  if (!ack.accepted || !ValidNonce(ack.request_nonce) ||
      ack.source_revision == 0 || ack.source_native_revision == 0 ||
      ack.source_connection_generation == 0 || ack.player_character_id <= 0 ||
      ack.target.stable_identity !=
          kZhongguoPromotionSourceProgressV1WidgetIdentities[1] ||
      ack.target.runtime_name !=
          kZhongguoPromotionSourceProgressV1WidgetNames[1] ||
      !ValidPointer(ack.target.instance_pointer) ||
      !ValidPointer(ack.target.vtable_pointer) ||
      !ack.requires_independent_progress_query || ack.postcondition_verified ||
      ack.expected_postcondition !=
          "played_owner_b1_active_on_independent_paused_progress_query" ||
      !ack.rejection_reason.empty()) {
    return {};
  }
  std::string output =
      "{\"schema_version\":1,\"status\":\"acknowledged_verification_pending\",";
  output += "\"accepted\":true,\"capability\":";
  AppendJsonString(output, kZhongguoReviewNowActionV1Capability);
  output += ",\"step\":";
  AppendJsonString(output, kZhongguoReviewNowActionV1Step);
  output += ",\"request_nonce\":";
  AppendJsonString(output, ack.request_nonce);
  output += ",\"source\":{\"revision\":";
  AppendNumber(output, ack.source_revision);
  output += ",\"native_revision\":";
  AppendNumber(output, ack.source_native_revision);
  output += ",\"connection_generation\":";
  AppendNumber(output, ack.source_connection_generation);
  output += ",\"date_raw\":";
  AppendSigned(output, ack.date_raw);
  output += ",\"player_character_id\":";
  AppendSigned(output, ack.player_character_id);
  output += "},\"target\":{\"stable_identity\":";
  AppendJsonString(output, ack.target.stable_identity);
  output += ",\"runtime_name\":";
  AppendJsonString(output, ack.target.runtime_name);
  output += ",\"instance_pointer\":";
  AppendJsonString(output, ack.target.instance_pointer);
  output += ",\"vtable_pointer\":";
  AppendJsonString(output, ack.target.vtable_pointer);
  output += "},\"expected_postcondition\":{\"requires_independent_progress_query\":true,\"predicate\":";
  AppendJsonString(output, ack.expected_postcondition);
  output += "},\"native_handled\":";
  output += ack.native_handled ? "true" : "false";
  output += ",\"postcondition_verified\":false}";
  return output;
}

} // namespace xar::ck3_11906
