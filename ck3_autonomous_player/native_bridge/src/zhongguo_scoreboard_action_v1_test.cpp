#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <string_view>

namespace {

constexpr std::string_view kProviderSession =
    "0123456789ABCDEF0123456789ABCDEF";
constexpr std::string_view kTreeFingerprint =
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
constexpr std::string_view kSemanticFingerprint =
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB";

struct DispatchFixture {
  std::size_t calls = 0;
  std::string target;
  bool accept = true;
};

template <typename Value>
void Available(xar::game::ZhongguoTypedValueV1<Value> &field, Value value) {
  field.available = true;
  field.value = std::move(value);
  field.unavailable_reason.clear();
}

template <typename Value>
void Unavailable(xar::game::ZhongguoTypedValueV1<Value> &field,
                 std::string_view reason) {
  field.available = false;
  field.value.reset();
  field.unavailable_reason.assign(reason);
}

std::string PointerValue(std::uintptr_t value) {
  constexpr char hex[] = "0123456789ABCDEF";
  std::array<char, 2 + sizeof(value) * 2> buffer{};
  buffer[0] = '0';
  buffer[1] = 'x';
  std::size_t cursor = buffer.size();
  do {
    buffer[--cursor] = hex[value & 0xF];
    value >>= 4;
  } while (value != 0);
  return std::string(buffer.data(), buffer.data() + 2) +
         std::string(buffer.data() + cursor, buffer.data() + buffer.size());
}

std::string Pointer(std::size_t index) {
  return PointerValue(0x14000000 + index * 0x100);
}

template <typename T, std::size_t Size>
void Store(std::array<std::byte, Size> &bytes, std::size_t offset,
           const T &value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct NativeDispatchFixture;

struct NativeManagerFixture {
  void *context = nullptr;
  NativeDispatchFixture *fixture = nullptr;
};

struct NativeDispatchFixture {
  std::array<std::byte, 0x200> first{};
  std::array<std::byte, 0x100> second{};
  std::array<std::byte, 0x500> third{};
  std::array<std::byte, 0x500> context{};
  NativeManagerFixture manager{};
  std::array<std::byte, 0x500> target{};
  std::array<void *, 14> target_vtable{};
  std::array<std::byte, 0x48> callback_row{};
  std::array<void *, 3> callback_vtable{};
  std::array<void *, 1> callback_object{};
  void *global = nullptr;
  std::size_t calls = 0;
  bool returned_native_handled = false;
  bool saw_empty_cstring = false;
  bool saw_target = false;
};

void __fastcall Slot13Marker() {}
void __fastcall Slot10Marker() {}
void __fastcall CallbackSlot2Marker() {}

bool __fastcall FixtureStrictDescendant(void *root, void *target) {
  return root != nullptr && target != nullptr && root != target;
}

bool __fastcall FixtureActivate(void *manager, std::uint32_t input,
                                const void *cstring, void *pimpl) {
  auto *typed = static_cast<NativeManagerFixture *>(manager);
  auto &fixture = *typed->fixture;
  ++fixture.calls;
  std::uint64_t length = 1;
  std::uint64_t capacity = 0;
  void *target = nullptr;
  std::memcpy(&length,
              static_cast<const std::byte *>(cstring) +
                  xar::ck3_11906::kZhongguoShortcutCStringLengthOffset,
              sizeof(length));
  std::memcpy(&capacity,
              static_cast<const std::byte *>(cstring) +
                  xar::ck3_11906::kZhongguoShortcutCStringCapacityOffset,
              sizeof(capacity));
  std::memcpy(&target,
              static_cast<const std::byte *>(pimpl) +
                  xar::ck3_11906::kZhongguoShortcutPimplTargetOffset,
              sizeof(target));
  fixture.saw_empty_cstring =
      input == 0 && length == 0 &&
      capacity == xar::ck3_11906::kZhongguoShortcutCStringEmptyCapacity;
  fixture.saw_target = target == fixture.target.data();
  return fixture.returned_native_handled;
}

void PrepareNativeDispatchFixture(NativeDispatchFixture &fixture) {
  void *first = fixture.first.data();
  void *second = fixture.second.data();
  void *third = fixture.third.data();
  void *context = fixture.context.data();
  fixture.global = first;
  Store(fixture.first, xar::ck3_11906::kZhongguoGuiChainFirstOffset,
        second);
  Store(fixture.second, xar::ck3_11906::kZhongguoGuiChainSecondOffset,
        third);
  Store(fixture.third, xar::ck3_11906::kZhongguoGuiContextOffset, context);
  fixture.manager.context = context;
  fixture.manager.fixture = &fixture;
  void *manager = &fixture.manager;
  Store(fixture.context, xar::ck3_11906::kZhongguoGuiShortcutManagerOffset,
        manager);
  void *target_context = context;
  Store(fixture.target, xar::ck3_11906::kZhongguoWidgetGuiContextOffset,
        target_context);
  fixture.target_vtable[13] = reinterpret_cast<void *>(&Slot13Marker);
  fixture.target_vtable[10] = reinterpret_cast<void *>(&Slot10Marker);
  void *target_vtable = fixture.target_vtable.data();
  Store(fixture.target, 0, target_vtable);
  fixture.callback_vtable[2] =
      reinterpret_cast<void *>(&CallbackSlot2Marker);
  fixture.callback_object[0] = fixture.callback_vtable.data();
  void *callback = fixture.callback_object.data();
  Store(fixture.callback_row,
        xar::ck3_11906::kZhongguoCallbackObjectOffset, callback);
  void *row = fixture.callback_row.data();
  const std::int32_t one = 1;
  Store(fixture.target,
        xar::ck3_11906::kZhongguoPrimaryCallbackGroupOffset +
            xar::ck3_11906::kZhongguoCallbackGroupDataOffset,
        row);
  Store(fixture.target,
        xar::ck3_11906::kZhongguoPrimaryCallbackGroupOffset +
            xar::ck3_11906::kZhongguoCallbackGroupCountOffset,
        one);
}

xar::game::ZhongguoScoreboardStateV1 State() {
  xar::game::ZhongguoScoreboardStateV1 source{};
  source.status = xar::game::ZhongguoScoreboardStateStatusV1::available;
  source.case_kind = xar::ck3_11906::kZhongguoScoreboardStateV1CaseKind;
  source.request_nonce = "scoreboard.source";
  source.snapshot_revision = 77;
  source.date_raw = 4242;
  source.paused = true;
  source.player_character_id = 101;
  source.provider_session_id.assign(kProviderSession);
  source.observation_sequence = 7;
  source.observed_state_revision = 3;
  source.tree_fingerprint_v1.assign(kTreeFingerprint);
  source.semantic_fingerprint_v1.assign(kSemanticFingerprint);
  source.readiness.player_binding_ready = true;
  source.readiness.gui_root_ready = true;
  source.readiness.entry_window_state_ready = true;
  source.readiness.acl_ready = true;
  source.readiness.same_frame_ready = true;
  source.readiness.state_acl_query_ready = true;
  source.received_self_acl.surface_available = true;
  source.received_self_acl.current_player_is_subject = true;
  for (std::size_t index = 0; index < source.widgets.size(); ++index) {
    auto &widget = source.widgets[index];
    widget.stable_identity.assign(
        xar::ck3_11906::kZhongguoScoreboardStateV1WidgetIdentities[index]);
    widget.runtime_name.assign(
        xar::ck3_11906::kZhongguoScoreboardStateV1WidgetNames[index]);
    Available(widget.instance_pointer, Pointer(index + 1));
    Available(widget.vtable_pointer, std::string("0x14506020"));
    Available(widget.exists, true);
    Available(widget.local_visible, false);
    Available(widget.effective_visible, false);
    Available(widget.enabled, true);
  }
  Available(source.widgets[0].local_visible, true);
  Available(source.widgets[0].effective_visible, true);
  Available(source.widgets[1].local_visible, true);
  Available(source.widgets[1].effective_visible, true);
  return source;
}

void SetVisible(xar::game::ZhongguoScoreboardStateV1 &source,
                std::size_t index, bool value) {
  Available(source.widgets[index].local_visible, value);
  Available(source.widgets[index].effective_visible, value);
}

xar::game::ZhongguoScoreboardActionBindingV1 Binding() {
  xar::game::ZhongguoScoreboardActionBindingV1 binding{};
  binding.revision = 19;
  binding.native_revision = 77;
  binding.connection_generation = 3;
  binding.date_raw = 4242;
  binding.player_character_id = 101;
  binding.provider_session_id.assign(kProviderSession);
  binding.observation_sequence = 7;
  binding.observed_state_revision = 3;
  binding.tree_fingerprint_v1.assign(kTreeFingerprint);
  binding.semantic_fingerprint_v1.assign(kSemanticFingerprint);
  return binding;
}

xar::game::ZhongguoScoreboardActionRequestV1 Request(
    const xar::game::ZhongguoScoreboardStateV1 &source,
    xar::game::ZhongguoScoreboardActionV1 action,
    std::size_t target_index) {
  xar::game::ZhongguoScoreboardActionRequestV1 request{};
  request.request_nonce = "scoreboard.action";
  request.action = action;
  request.expected_revision = 19;
  request.expected_native_revision = 77;
  request.expected_connection_generation = 3;
  request.expected_player_character_id = 101;
  request.expected_provider_session_id.assign(kProviderSession);
  request.expected_observation_sequence = source.observation_sequence;
  request.expected_observed_state_revision = source.observed_state_revision;
  request.expected_tree_fingerprint_v1 = source.tree_fingerprint_v1;
  request.expected_semantic_fingerprint_v1 = source.semantic_fingerprint_v1;
  request.expected_window_instance_pointer =
      *source.widgets[1].instance_pointer.value;
  request.expected_target_instance_pointer =
      *source.widgets[target_index].instance_pointer.value;
  request.expected_target_vtable_pointer =
      *source.widgets[target_index].vtable_pointer.value;
  return request;
}

bool Dispatch(void *opaque, xar::game::ZhongguoScoreboardActionV1,
              std::string_view stable_identity, std::string_view runtime_name,
              std::string_view, std::string_view,
              bool &native_handled) noexcept {
  auto &fixture = *static_cast<DispatchFixture *>(opaque);
  ++fixture.calls;
  fixture.target.assign(stable_identity);
  native_handled = fixture.accept;
  return fixture.accept && stable_identity == runtime_name;
}

bool Expect(bool condition, std::string_view message) {
  if (!condition) std::cerr << message << '\n';
  return condition;
}

} // namespace

int main() {
  bool ok = true;
  const struct Case {
    xar::game::ZhongguoScoreboardActionV1 action;
    std::size_t target;
    std::size_t source_tab;
    std::size_t entry;
    std::string_view active_tab;
  } cases[] = {
      {xar::game::ZhongguoScoreboardActionV1::open, 5, 99, 5, "received"},
      {xar::game::ZhongguoScoreboardActionV1::switch_managed, 7, 1, 99,
       "managed"},
      {xar::game::ZhongguoScoreboardActionV1::switch_received, 8, 0, 99,
       "received"},
      {xar::game::ZhongguoScoreboardActionV1::switch_system, 9, 0, 99,
       "system"},
      {xar::game::ZhongguoScoreboardActionV1::close, 14, 1, 99, ""},
  };
  for (const auto &test : cases) {
    auto source = State();
    if (test.entry != 99) {
      SetVisible(source, test.entry, true);
    } else {
      SetVisible(source, 2, true);
      SetVisible(source, 3, true);
      SetVisible(source, 7, true);
      SetVisible(source, 8, true);
      SetVisible(source, 9, true);
      SetVisible(source, 14, true);
      source.managed_acl.surface_available = true;
      source.managed_acl.current_player_can_assess_others = true;
      SetVisible(source, 10 + test.source_tab, true);
    }
    auto request = Request(source, test.action, test.target);
    DispatchFixture dispatch{};
    const xar::ck3_11906::ZhongguoScoreboardActionAccessV1 access{
        &dispatch, &Dispatch};
    xar::game::ZhongguoScoreboardActionAckV1 ack{};
    const auto result = xar::ck3_11906::ExecuteZhongguoScoreboardActionV1(
        request, Binding(), source, access, ack);
    ok &= Expect(
        result == xar::game::ZhongguoScoreboardActionResultV1::
                      acknowledged_verification_pending &&
            ack.accepted && ack.native_handled &&
            !ack.postcondition_verified &&
            dispatch.calls == 1 &&
            dispatch.target == source.widgets[test.target].stable_identity &&
            ack.expected_postcondition.active_tab == test.active_tab,
        "allowlisted action must produce only a verification-pending ACK");
    const auto json =
        xar::ck3_11906::SerializeZhongguoScoreboardActionAckV1(ack);
    ok &= Expect(
        !json.empty() &&
            json.find("\"postcondition_verified\":false") !=
                std::string::npos &&
            json.find("\"requires_independent_query\":true") !=
                std::string::npos &&
            json.find("\"native_handled\":true") != std::string::npos,
        "serialized ACK must not claim the postcondition");
  }

  auto source = State();
  SetVisible(source, 5, true);
  auto request = Request(
      source, xar::game::ZhongguoScoreboardActionV1::open, 5);
  DispatchFixture dispatch{};
  const xar::ck3_11906::ZhongguoScoreboardActionAccessV1 access{&dispatch,
                                                                &Dispatch};
  const auto rejected = [&](std::string_view expected_reason) {
    xar::game::ZhongguoScoreboardActionAckV1 ack{};
    const auto result = xar::ck3_11906::ExecuteZhongguoScoreboardActionV1(
        request, Binding(), source, access, ack);
    return result == xar::game::ZhongguoScoreboardActionResultV1::rejected &&
           !ack.accepted && ack.rejection_reason == expected_reason;
  };

  Unavailable(source.widgets[5].enabled, "enabled_state_abi_not_frozen");
  ok &= Expect(rejected("target_enabled_unavailable") && dispatch.calls == 0,
               "unfrozen enabled ABI must fail before dispatch");
  Available(source.widgets[5].enabled, false);
  ok &= Expect(rejected("target_disabled") && dispatch.calls == 0,
               "disabled target must fail before dispatch");
  Available(source.widgets[5].enabled, true);
  request.expected_target_instance_pointer = "0xDEADBEEF";
  ok &= Expect(rejected("target_instance_mismatch") && dispatch.calls == 0,
               "rebound target identity must fail before dispatch");
  request = Request(source, xar::game::ZhongguoScoreboardActionV1::open, 5);
  auto non_player = source;
  non_player.readiness.player_binding_ready = false;
  xar::game::ZhongguoScoreboardActionAckV1 non_player_ack{};
  ok &= Expect(
      xar::ck3_11906::ExecuteZhongguoScoreboardActionV1(
          request, Binding(), non_player, access, non_player_ack) ==
              xar::game::ZhongguoScoreboardActionResultV1::rejected &&
          non_player_ack.rejection_reason == "source_state_unavailable" &&
          dispatch.calls == 0,
      "non-player binding must fail before dispatch");
  auto stale_binding = Binding();
  ++stale_binding.revision;
  xar::game::ZhongguoScoreboardActionAckV1 stale_ack{};
  ok &= Expect(
      xar::ck3_11906::ExecuteZhongguoScoreboardActionV1(
          request, stale_binding, source, access, stale_ack) ==
              xar::game::ZhongguoScoreboardActionResultV1::rejected &&
          stale_ack.rejection_reason == "revision_mismatch" &&
          dispatch.calls == 0,
      "stale revision must fail before dispatch");

  auto managed = State();
  SetVisible(managed, 2, true);
  SetVisible(managed, 7, true);
  auto managed_request = Request(
      managed, xar::game::ZhongguoScoreboardActionV1::switch_managed, 7);
  xar::game::ZhongguoScoreboardActionAckV1 managed_ack{};
  ok &= Expect(
      xar::ck3_11906::ExecuteZhongguoScoreboardActionV1(
          managed_request, Binding(), managed, access, managed_ack) ==
              xar::game::ZhongguoScoreboardActionResultV1::rejected &&
          managed_ack.rejection_reason == "managed_acl_denied" &&
          dispatch.calls == 0,
      "managed tab must obey the materialized managed ACL");

  managed.managed_acl.surface_available = true;
  managed.managed_acl.current_player_can_assess_others = true;
  SetVisible(managed, 10, true);
  managed_request = Request(
      managed, xar::game::ZhongguoScoreboardActionV1::switch_managed, 7);
  xar::game::ZhongguoScoreboardActionAckV1 noop_ack{};
  ok &= Expect(
      xar::ck3_11906::ExecuteZhongguoScoreboardActionV1(
          managed_request, Binding(), managed, access, noop_ack) ==
              xar::game::ZhongguoScoreboardActionResultV1::rejected &&
          noop_ack.rejection_reason == "action_noop" && dispatch.calls == 0,
      "switching to the already-active page must be rejected as a no-op");

  auto reopen_source = State();
  SetVisible(reopen_source, 6, true);
  auto reopen_request = Request(
      reopen_source, xar::game::ZhongguoScoreboardActionV1::reopen, 6);
  xar::game::ZhongguoScoreboardActionAckV1 reopen_ack{};
  ok &= Expect(
      xar::ck3_11906::ExecuteZhongguoScoreboardActionV1(
          reopen_request, Binding(), reopen_source, access, reopen_ack) ==
              xar::game::ZhongguoScoreboardActionResultV1::rejected &&
          reopen_ack.rejection_reason ==
              "reopen_requires_two_phase_sequence" &&
          dispatch.calls == 0,
      "reopen must remain a close/query/open/query composition");

  xar::game::ZhongguoScoreboardActionAckV1 no_dispatch_ack{};
  ok &= Expect(
      xar::ck3_11906::ExecuteZhongguoScoreboardActionV1(
          request, Binding(), source, {}, no_dispatch_ack) ==
              xar::game::ZhongguoScoreboardActionResultV1::rejected &&
          no_dispatch_ack.rejection_reason == "action_dispatch_unavailable",
      "unwired production dispatch must remain fail closed");

  NativeDispatchFixture native{};
  PrepareNativeDispatchFixture(native);
  xar::ck3_11906::ZhongguoScoreboardActionDispatchEnvironmentV1
      native_environment{};
  native_environment.exact_build_admitted = true;
  native_environment.offline_fixture_function_overrides = true;
  native_environment.gui_global_slot = &native.global;
  native_environment.activate_shortcut = &FixtureActivate;
  native_environment.is_strict_descendant = &FixtureStrictDescendant;
  native_environment.button_base_slot13 =
      reinterpret_cast<void *>(&Slot13Marker);
  bool native_handled = true;
  const auto native_invoked =
      xar::ck3_11906::DispatchZhongguoScoreboardActionNativeV1(
          &native_environment,
          xar::game::ZhongguoScoreboardActionV1::open,
          "zg361_scoreboard_entry_received",
          "zg361_scoreboard_entry_received",
          PointerValue(reinterpret_cast<std::uintptr_t>(native.target.data())),
          PointerValue(reinterpret_cast<std::uintptr_t>(
              native.target_vtable.data())),
          native_handled);
  ok &= Expect(native_invoked && !native_handled && native.calls == 1 &&
                   native.saw_empty_cstring && native.saw_target,
               "exact dispatcher must ACK invocation even when the borrowed "
               "native handled boolean is false");
  const std::uint8_t hidden =
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  Store(native.target, xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset,
        hidden);
  native_handled = true;
  ok &= Expect(
      !xar::ck3_11906::DispatchZhongguoScoreboardActionNativeV1(
          &native_environment,
          xar::game::ZhongguoScoreboardActionV1::open,
          "zg361_scoreboard_entry_received",
          "zg361_scoreboard_entry_received",
          PointerValue(reinterpret_cast<std::uintptr_t>(native.target.data())),
          PointerValue(reinterpret_cast<std::uintptr_t>(
              native.target_vtable.data())),
          native_handled) &&
          !native_handled && native.calls == 1,
      "exact dispatcher must reject the cached effective-hidden gate before "
      "calling CPdxGuiShortcutManager");
  return ok ? 0 : 1;
}
