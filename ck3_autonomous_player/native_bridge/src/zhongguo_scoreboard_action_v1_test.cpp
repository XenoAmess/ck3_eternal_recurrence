#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>

namespace {

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

std::string Pointer(std::size_t index) {
  constexpr char hex[] = "0123456789ABCDEF";
  std::uintptr_t value = 0x14000000 + index * 0x100;
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

xar::game::ZhongguoScoreboardStateV1 State() {
  xar::game::ZhongguoScoreboardStateV1 source{};
  source.status = xar::game::ZhongguoScoreboardStateStatusV1::available;
  source.case_kind = xar::ck3_11906::kZhongguoScoreboardStateV1CaseKind;
  source.request_nonce = "scoreboard.source";
  source.snapshot_revision = 77;
  source.date_raw = 4242;
  source.paused = true;
  source.player_character_id = 101;
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
  return {19, 77, 3, 4242, 101};
}

xar::game::ZhongguoScoreboardActionRequestV1 Request(
    const xar::game::ZhongguoScoreboardStateV1 &source,
    xar::game::ZhongguoScoreboardActionV1 action,
    std::size_t target_index) {
  return {"scoreboard.action", action, 19, 77, 3, 101,
          *source.widgets[1].instance_pointer.value,
          *source.widgets[target_index].instance_pointer.value,
          *source.widgets[target_index].vtable_pointer.value};
}

bool Dispatch(void *opaque, xar::game::ZhongguoScoreboardActionV1,
              std::string_view stable_identity, std::string_view runtime_name,
              std::string_view, std::string_view) noexcept {
  auto &fixture = *static_cast<DispatchFixture *>(opaque);
  ++fixture.calls;
  fixture.target.assign(stable_identity);
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
      {xar::game::ZhongguoScoreboardActionV1::reopen, 6, 99, 6, "system"},
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
            ack.accepted && !ack.postcondition_verified &&
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
                std::string::npos,
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

  xar::game::ZhongguoScoreboardActionAckV1 no_dispatch_ack{};
  ok &= Expect(
      xar::ck3_11906::ExecuteZhongguoScoreboardActionV1(
          request, Binding(), source, {}, no_dispatch_ack) ==
              xar::game::ZhongguoScoreboardActionResultV1::rejected &&
          no_dispatch_ack.rejection_reason == "action_dispatch_unavailable",
      "unwired production dispatch must remain fail closed");
  return ok ? 0 : 1;
}
