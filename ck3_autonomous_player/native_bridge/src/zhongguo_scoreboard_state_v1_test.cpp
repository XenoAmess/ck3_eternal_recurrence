#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>

namespace {

using xar::ck3_11906::ZhongguoRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{77, 4242, true, true, true, true,
                                       101};
  bool main_thread = true;
  std::unordered_map<std::string, ZhongguoRawVariableV1> rows;
  std::array<std::array<std::uint8_t, 0x200>, 9> widgets{};
};

ZhongguoRawVariableV1 Integer(std::int64_t value) {
  return {true, 1, value * 100'000};
}

ZhongguoRawVariableV1 Character(std::int64_t value) {
  return {true, 4, value};
}

void SetParent(std::array<std::uint8_t, 0x200> &widget, void *parent) {
  std::memcpy(widget.data() + xar::ck3_11906::kZhongguoWidgetParentOffset,
              &parent, sizeof(parent));
}

void SetVtable(std::array<std::uint8_t, 0x200> &widget, void *vtable) {
  std::memcpy(widget.data(), &vtable, sizeof(vtable));
}

bool Capture(void *opaque,
             xar::game::ZhongguoCaseFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(opaque)->frame;
  return true;
}

bool IsMain(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->main_thread;
}

bool ValidateCharacter(void *, std::int32_t id) noexcept {
  return id == 101 || id == 202 || id == 303;
}

bool ReadVariable(void *opaque, std::int32_t subject, std::string_view key,
                  ZhongguoRawVariableV1 &output) noexcept {
  if (subject != 101) return false;
  auto &rows = static_cast<Fixture *>(opaque)->rows;
  const auto found = rows.find(std::string(key));
  output = found == rows.end() ? ZhongguoRawVariableV1{} : found->second;
  return true;
}

void *FindWidget(void *opaque, std::string_view name) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  for (std::size_t index = 0;
       index < xar::ck3_11906::kZhongguoScoreboardStateV1WidgetNames.size();
       ++index) {
    if (name ==
        xar::ck3_11906::kZhongguoScoreboardStateV1WidgetNames[index]) {
      return fixture.widgets[index].data();
    }
  }
  return nullptr;
}

xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 Environment() {
  xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  environment.variables.exact_build_admitted = true;
  environment.variables.offline_fixture_function_overrides = true;
  return environment;
}

xar::ck3_11906::ZhongguoScoreboardAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::ZhongguoScoreboardAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMain;
  access.validate_character = &ValidateCharacter;
  access.read_allowlisted_variable = &ReadVariable;
  access.find_fixed_widget = &FindWidget;
  return access;
}

void PopulateReceivedA(Fixture &fixture) {
  auto &rows = fixture.rows;
  rows["zg361_sb_r_01_char"] = Character(101);
  rows["zg361_sb_self_char"] = Character(101);
  rows["zg361_scoreboard_received_owner"] = Character(202);
  rows["zg361_scoreboard_received_cycle_serial"] = Integer(8);
  rows["zg361_scoreboard_received_case_serial"] = Integer(903);
  rows["zg361_sb_self_case_owner"] = Character(202);
  rows["zg361_sb_self_cycle_serial"] = Integer(8);
  rows["zg361_sb_self_case_serial"] = Integer(903);
  rows["zg361_sb_self_b1_case_owner"] = Character(202);
  rows["zg361_sb_self_b1_cycle_serial"] = Integer(8);
  rows["zg361_sb_self_b1_case_serial"] = Integer(41);
  rows["zg361_sb_self_disclosure_acl_mode"] = Integer(3);
  rows["zg361_sb_self_disclosure_policy_available"] = Integer(1);
  rows["zg361_sb_self_disclosure_policy_id"] = Integer(41);
  rows["zg361_sb_self_disclosure_self_mode"] = Integer(3);
  rows["zg361_sb_self_disclosure_team_mode"] = Integer(2);
  rows["zg361_sb_self_disclosure_evaluator_identity_mode"] = Integer(0);
  rows["zg361_sb_self_disclosure_blackbox_risk"] = Integer(1);
}

bool Expect(bool condition, std::string_view message) {
  if (!condition) std::cerr << message << '\n';
  return condition;
}

} // namespace

int main() {
  bool ok = true;
  Fixture fixture{};
  std::uintptr_t push_button_vtable = 0x14506020;
  for (auto &widget : fixture.widgets) {
    SetVtable(widget, reinterpret_cast<void *>(push_button_vtable));
  }
  SetParent(fixture.widgets[0], fixture.widgets[1].data());
  SetParent(fixture.widgets[1], nullptr);
  SetParent(fixture.widgets[2], fixture.widgets[1].data());
  SetParent(fixture.widgets[3], fixture.widgets[2].data());
  SetParent(fixture.widgets[4], fixture.widgets[0].data());
  SetParent(fixture.widgets[5], fixture.widgets[0].data());
  SetParent(fixture.widgets[6], fixture.widgets[0].data());
  SetParent(fixture.widgets[7], fixture.widgets[2].data());
  SetParent(fixture.widgets[8], fixture.widgets[3].data());
  // The modal and panel are locally hidden in the initial closed state.
  fixture.widgets[2][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetHiddenMask;
  fixture.widgets[3][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] = 0;
  fixture.widgets[4][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetHiddenMask;
  fixture.widgets[6][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetHiddenMask;
  PopulateReceivedA(fixture);

  const xar::ck3_11906::ZhongguoScoreboardStateRequestV1 request{
      77, "scoreboard-fixture-a"};
  xar::game::ZhongguoScoreboardStateV1 result{};
  const auto read = xar::ck3_11906::ReadZhongguoScoreboardStateV1(
      Environment(), Access(fixture), request, result);
  ok &= Expect(
      read == xar::game::ReadZhongguoScoreboardStateResultV1::available,
      "received-only fixture must be readable");
  ok &= Expect(result.status ==
                   xar::game::ZhongguoScoreboardStateStatusV1::available,
               "fixture status must be available");
  ok &= Expect(!result.managed_acl.surface_available &&
                   !result.managed_acl.current_player_can_assess_others,
               "received-only player must not acquire manager ACL");
  ok &= Expect(result.received_self_acl.surface_available &&
                   result.received_self_acl.current_player_is_subject,
               "received-self ACL must bind the played character");
  ok &= Expect(result.received_self_acl.result_case_serial.value == 903 &&
                   result.received_self_acl.b1_case_serial.value == 41,
               "result and B1 case serials must remain independent");
  ok &= Expect(result.widgets[0].stable_identity ==
                   "zg361_open_scoreboard" &&
                   result.widgets[0].exists.value == true &&
                   result.widgets[0].effective_visible.value == true,
               "real entry container must be observed by fixed identity");
  ok &= Expect(result.widgets[2].local_visible.value == false &&
                   result.widgets[3].effective_visible.value == false,
               "effective visibility must include the hidden modal parent");
  ok &= Expect(result.widgets[4].runtime_name ==
                       "zg361_scoreboard_entry_managed" &&
                   result.widgets[5].runtime_name ==
                       "zg361_scoreboard_entry_received" &&
                   result.widgets[6].runtime_name ==
                       "zg361_scoreboard_entry_system" &&
                   result.widgets[7].runtime_name ==
                       "zg361_scoreboard_modal_backdrop_close" &&
                   result.widgets[8].runtime_name ==
                       "zg361_scoreboard_header_close" &&
                   result.widgets[5].instance_pointer.available &&
                   result.widgets[5].vtable_pointer.value == "0x14506020" &&
                   result.widgets[5].local_visible.value == true &&
                   result.widgets[4].local_visible.value == false,
               "five action-probe targets must expose identity, pointers and "
               "visibility");
  ok &= Expect(!result.widgets[0].enabled.available &&
                   result.widgets[0].enabled.unavailable_reason ==
                       "enabled_state_abi_not_frozen" &&
                   !result.widgets[0].focused.available &&
                   !result.widgets[0].scroll_max.available,
               "unfrozen widget ABI must remain typed unavailable");
  ok &= Expect(!result.actions.activate.available &&
                   !result.actions.close.available &&
                   !result.actions.reopen.available &&
                   !result.readiness.full_widget_gate_ready &&
                   !result.readiness.production_live_ready,
               "read-only static provider must not claim actions or live");
  const auto json =
      xar::ck3_11906::SerializeZhongguoScoreboardStateV1(result);
  ok &= Expect(!json.empty() &&
                   json.find("\"zg361_open_scoreboard\"") !=
                       std::string::npos &&
                   json.find("\"production_live_ready\":false") !=
                       std::string::npos &&
                   json.find("read_only_provider_action_not_exposed") !=
                       std::string::npos,
               "serializer must preserve fixed identity and honest boundary");

  fixture.rows["zg361_sb_self_disclosure_policy_id"] = Integer(903);
  xar::game::ZhongguoScoreboardStateV1 inconsistent{};
  const auto rejected = xar::ck3_11906::ReadZhongguoScoreboardStateV1(
      Environment(), Access(fixture), request, inconsistent);
  ok &= Expect(
      rejected == xar::game::ReadZhongguoScoreboardStateResultV1::unavailable &&
          inconsistent.unavailable_reason == "acl_inconsistent",
      "policy ID must bind B1 case 41, never result case 903");

  const auto bound =
      xar::ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(
          0x10000000, true);
  ok &= Expect(reinterpret_cast<std::uintptr_t>(bound.gui_global_slot) ==
                   0x10000000 +
                       xar::ck3_11906::kZhongguoGuiGlobalSlotRva &&
                   reinterpret_cast<std::uintptr_t>(
                       bound.find_top_level_widget) ==
                       0x10000000 +
                           xar::ck3_11906::
                               kZhongguoGuiFindTopLevelWidgetRva,
               "production binder must use exact-build GUI RVAs");
  return ok ? 0 : 1;
}
