#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <initializer_list>
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
  std::array<std::array<std::uint8_t, 0x200>,
             xar::ck3_11906::kZhongguoScoreboardStateV1WidgetNames.size()>
      widgets{};
  std::array<std::array<void *, 15>, 15> children{};
  std::array<std::int32_t, 15> child_counts{};
  std::array<std::uint8_t, 0x400> gui_context{};
  std::array<std::uint8_t, 8> gui_owner{};
  std::array<void *, 4> modal_receivers{};
};

ZhongguoRawVariableV1 Integer(std::int64_t value) {
  return {true, 1, value * 100'000};
}

ZhongguoRawVariableV1 Character(std::int64_t value) {
  return {true, 4, value};
}

void SetParent(Fixture &fixture, std::size_t child_index,
               std::size_t parent_index) {
  auto *parent = fixture.widgets[parent_index].data();
  std::memcpy(fixture.widgets[child_index].data() +
                  xar::ck3_11906::kZhongguoWidgetParentOffset,
              &parent, sizeof(parent));
  const auto count = fixture.child_counts[parent_index]++;
  fixture.children[parent_index][static_cast<std::size_t>(count)] =
      fixture.widgets[child_index].data();
}

void FinalizeHierarchy(Fixture &fixture) {
  for (std::size_t index = 0; index < fixture.widgets.size(); ++index) {
    auto *children = fixture.children[index].data();
    std::memcpy(fixture.widgets[index].data() +
                    xar::ck3_11906::kZhongguoWidgetChildrenOffset,
                &children, sizeof(children));
    std::memcpy(fixture.widgets[index].data() +
                    xar::ck3_11906::kZhongguoWidgetChildCountOffset,
                &fixture.child_counts[index],
                sizeof(fixture.child_counts[index]));
  }
}

void SetModalReceivers(Fixture &fixture,
                       std::initializer_list<void *> receivers) {
  fixture.modal_receivers.fill(nullptr);
  std::copy(receivers.begin(), receivers.end(),
            fixture.modal_receivers.begin());
  auto *data = fixture.modal_receivers.data();
  const auto count = static_cast<std::int32_t>(receivers.size());
  std::memcpy(fixture.gui_context.data() +
                  xar::ck3_11906::kZhongguoGuiModalReceiversOffset,
              &data, sizeof(data));
  std::memcpy(fixture.gui_context.data() +
                  xar::ck3_11906::kZhongguoGuiModalReceiverCountOffset,
              &count, sizeof(count));
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

bool ResolveGui(void *opaque, void *&context, void *&owner) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  context = fixture.gui_context.data();
  owner = fixture.gui_owner.data();
  return true;
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
  access.resolve_fixture_gui = &ResolveGui;
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

bool ReadU8(std::string_view bytes, std::size_t &cursor,
            std::uint8_t &value) {
  if (cursor >= bytes.size()) return false;
  value = static_cast<std::uint8_t>(bytes[cursor++]);
  return true;
}

bool ReadU16Le(std::string_view bytes, std::size_t &cursor,
               std::uint16_t &value) {
  std::uint8_t low = 0;
  std::uint8_t high = 0;
  if (!ReadU8(bytes, cursor, low) || !ReadU8(bytes, cursor, high)) {
    return false;
  }
  value = static_cast<std::uint16_t>(low) |
          (static_cast<std::uint16_t>(high) << 8U);
  return true;
}

bool ReadU32Le(std::string_view bytes, std::size_t &cursor,
               std::uint32_t &value) {
  value = 0;
  for (unsigned shift = 0; shift != 32; shift += 8) {
    std::uint8_t byte = 0;
    if (!ReadU8(bytes, cursor, byte)) return false;
    value |= static_cast<std::uint32_t>(byte) << shift;
  }
  return true;
}

bool ReadU64Le(std::string_view bytes, std::size_t &cursor,
               std::uint64_t &value) {
  value = 0;
  for (unsigned shift = 0; shift != 64; shift += 8) {
    std::uint8_t byte = 0;
    if (!ReadU8(bytes, cursor, byte)) return false;
    value |= static_cast<std::uint64_t>(byte) << shift;
  }
  return true;
}

bool ReadCanonicalString(std::string_view bytes, std::size_t &cursor,
                         std::string_view &value) {
  std::uint32_t size = 0;
  if (!ReadU32Le(bytes, cursor, size) ||
      size > bytes.size() - cursor) {
    return false;
  }
  value = bytes.substr(cursor, size);
  cursor += size;
  return true;
}

bool ConsumeDomain(std::string_view bytes, std::size_t &cursor,
                   std::string_view domain) {
  if (domain.size() + 1 > bytes.size() - cursor ||
      bytes.substr(cursor, domain.size()) != domain ||
      bytes[cursor + domain.size()] != '\0') {
    return false;
  }
  cursor += domain.size() + 1;
  return true;
}

bool CanonicalEncodingMatches(
    const xar::ck3_11906::ZhongguoScoreboardProviderRevisionTrackerV1 &tracker,
    const Fixture &fixture) {
  std::size_t cursor = 0;
  std::uint16_t format = 0;
  std::string_view allowlist;
  std::uint64_t owner = 0;
  std::uint64_t root = 0;
  std::string_view tree = tracker.last_tree_canonical_bytes;
  if (!ConsumeDomain(tree, cursor,
                     xar::ck3_11906::kZhongguoScoreboardTreeDomainV1) ||
      !ReadU16Le(tree, cursor, format) || format != 1 ||
      tree.size() - cursor < 32) {
    return false;
  }
  cursor += 32;
  if (!ReadCanonicalString(tree, cursor, allowlist) ||
      allowlist != xar::ck3_11906::kZhongguoScoreboardStateV1AllowlistId ||
      !ReadU64Le(tree, cursor, owner) ||
      owner != reinterpret_cast<std::uintptr_t>(fixture.gui_owner.data()) ||
      !ReadU64Le(tree, cursor, root) ||
      root != reinterpret_cast<std::uintptr_t>(fixture.widgets[1].data())) {
    return false;
  }
  for (std::size_t index = 0; index < fixture.widgets.size(); ++index) {
    std::uint8_t observed_index = 0;
    std::uint8_t exists = 0;
    std::uint64_t instance = 0;
    std::uint64_t vtable = 0;
    std::uint8_t depth = 0;
    if (!ReadU8(tree, cursor, observed_index) || observed_index != index ||
        !ReadU8(tree, cursor, exists) || exists != 1 ||
        !ReadU64Le(tree, cursor, instance) ||
        instance !=
            reinterpret_cast<std::uintptr_t>(fixture.widgets[index].data()) ||
        !ReadU64Le(tree, cursor, vtable) || vtable != 0x14506020 ||
        !ReadU8(tree, cursor, depth)) {
      return false;
    }
    for (std::size_t hop = 0; hop < depth; ++hop) {
      std::uint64_t ancestor = 0;
      std::uint32_t ordinal = 0;
      if (!ReadU64Le(tree, cursor, ancestor) ||
          !ReadU32Le(tree, cursor, ordinal)) {
        return false;
      }
      if (index == 7) {
        constexpr std::array<std::size_t, 3> ancestors{1, 2, 3};
        constexpr std::array<std::uint32_t, 3> ordinals{1, 0, 0};
        if (depth != ancestors.size() ||
            ancestor != reinterpret_cast<std::uintptr_t>(
                            fixture.widgets[ancestors[hop]].data()) ||
            ordinal != ordinals[hop]) {
          return false;
        }
      }
    }
  }
  if (cursor != tree.size()) return false;

  cursor = 0;
  format = 0;
  std::string_view semantic = tracker.last_semantic_canonical_bytes;
  if (!ConsumeDomain(semantic, cursor,
                     xar::ck3_11906::kZhongguoScoreboardSemanticDomainV1) ||
      !ReadU16Le(semantic, cursor, format) || format != 1 ||
      semantic.size() - cursor < 32) {
    return false;
  }
  cursor += 32;
  std::uint32_t player = 0;
  if (!ReadCanonicalString(semantic, cursor, allowlist) ||
      allowlist != xar::ck3_11906::kZhongguoScoreboardStateV1AllowlistId ||
      !ReadU32Le(semantic, cursor, player) || player != 101) {
    return false;
  }
  for (std::size_t index = 0; index < fixture.widgets.size(); ++index) {
    std::uint8_t observed_index = 0;
    std::uint8_t exists = 0;
    std::uint8_t visible = 0;
    std::uint8_t enabled = 0;
    if (!ReadU8(semantic, cursor, observed_index) || observed_index != index ||
        !ReadU8(semantic, cursor, exists) || exists != 1 ||
        !ReadU8(semantic, cursor, visible) || visible > 1 ||
        !ReadU8(semantic, cursor, enabled) || enabled > 1) {
      return false;
    }
  }
  std::uint8_t modal_open = 0;
  std::uint8_t modal_relation = 0;
  std::uint64_t modal_receiver = 0;
  std::uint8_t active_page = 0;
  std::uint8_t closed_entry = 0;
  if (!ReadU8(semantic, cursor, modal_open) || modal_open != 0 ||
      !ReadU8(semantic, cursor, modal_relation) || modal_relation != 0 ||
      !ReadU64Le(semantic, cursor, modal_receiver) || modal_receiver != 0 ||
      !ReadU8(semantic, cursor, active_page) || active_page != 0 ||
      !ReadU8(semantic, cursor, closed_entry) || closed_entry != 2) {
    return false;
  }
  for (const auto key :
       xar::ck3_11906::kZhongguoScoreboardStateV1VariableAllowlist) {
    const auto found = fixture.rows.find(std::string(key));
    const bool expected_present = found != fixture.rows.end();
    std::uint8_t present = 0;
    if (!ReadU8(semantic, cursor, present) ||
        (present != 0) != expected_present) {
      return false;
    }
    if (expected_present) {
      std::uint32_t kind = 0;
      std::uint64_t payload = 0;
      if (!ReadU32Le(semantic, cursor, kind) ||
          !ReadU64Le(semantic, cursor, payload) ||
          static_cast<std::int32_t>(kind) != found->second.kind ||
          static_cast<std::int64_t>(payload) != found->second.payload) {
        return false;
      }
    }
  }
  std::uint8_t managed_surface = 0;
  std::uint8_t can_assess = 0;
  if (!ReadU8(semantic, cursor, managed_surface) || managed_surface != 0 ||
      !ReadU8(semantic, cursor, can_assess) || can_assess != 0) {
    return false;
  }
  for (std::size_t index = 0; index < 2; ++index) {
    std::uint8_t available = 0;
    if (!ReadU8(semantic, cursor, available) || available != 0) return false;
  }
  std::uint8_t received_surface = 0;
  std::uint8_t is_subject = 0;
  if (!ReadU8(semantic, cursor, received_surface) || received_surface != 1 ||
      !ReadU8(semantic, cursor, is_subject) || is_subject != 1) {
    return false;
  }
  constexpr std::size_t kReceivedTypedFieldCount = 13;
  for (std::size_t index = 0; index < kReceivedTypedFieldCount; ++index) {
    std::uint8_t available = 0;
    std::uint64_t value = 0;
    if (!ReadU8(semantic, cursor, available) || available != 1 ||
        !ReadU64Le(semantic, cursor, value)) {
      return false;
    }
  }
  return cursor == semantic.size();
}

} // namespace

int main() {
  bool ok = true;
  Fixture fixture{};
  std::uintptr_t push_button_vtable = 0x14506020;
  for (auto &widget : fixture.widgets) {
    SetVtable(widget, reinterpret_cast<void *>(push_button_vtable));
  }
  SetParent(fixture, 0, 1);
  SetParent(fixture, 2, 1);
  SetParent(fixture, 3, 2);
  SetParent(fixture, 4, 0);
  SetParent(fixture, 5, 0);
  SetParent(fixture, 6, 0);
  SetParent(fixture, 7, 3);
  SetParent(fixture, 8, 3);
  SetParent(fixture, 9, 3);
  SetParent(fixture, 10, 3);
  SetParent(fixture, 11, 3);
  SetParent(fixture, 12, 3);
  SetParent(fixture, 13, 2);
  SetParent(fixture, 14, 3);
  FinalizeHierarchy(fixture);
  SetModalReceivers(fixture, {});
  // The modal is locally hidden in the initial closed state.  CK3 caches
  // effective-hidden separately; the child panel proves the provider reads
  // that cache instead of reconstructing visibility from the parent chain.
  fixture.widgets[2][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[3][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[4][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[6][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[7][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[9][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[10][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[11][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[12][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  // The received tab is locally disabled and has its recursively propagated
  // effective-disabled cache set.  Other widgets remain enabled.
  fixture.widgets[8][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalDisabledMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveDisabledMask;
  PopulateReceivedA(fixture);

  xar::ck3_11906::ZhongguoScoreboardProviderRevisionTrackerV1 tracker{};
  xar::ck3_11906::ZhongguoScoreboardStateRequestV1 request{};
  request.expected_snapshot_revision = 77;
  request.request_nonce = "scoreboard-fixture-a";
  request.provider_session_id = "0123456789ABCDEF0123456789ABCDEF";
  request.connection_generation = 3;
  request.provider_read_mode = xar::ck3_11906::
      ZhongguoScoreboardProviderReadModeV1::publish_observation;
  request.provider_revision_tracker = &tracker;
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
                   result.widgets[3].local_visible.value == true &&
                   result.widgets[3].effective_visible.value == false,
               "effective visibility must use +D0 bit 0x08 cache");
  ok &= Expect(result.widgets[4].runtime_name ==
                       "zg361_scoreboard_entry_managed" &&
                   result.widgets[5].runtime_name ==
                       "zg361_scoreboard_entry_received" &&
                   result.widgets[6].runtime_name ==
                       "zg361_scoreboard_entry_system" &&
                   result.widgets[7].runtime_name ==
                       "zg361_scoreboard_tab_managed" &&
                   result.widgets[8].runtime_name ==
                       "zg361_scoreboard_tab_received" &&
                   result.widgets[9].runtime_name ==
                       "zg361_scoreboard_tab_system" &&
                   result.widgets[10].runtime_name ==
                       "zg361_scoreboard_page_managed" &&
                   result.widgets[11].runtime_name ==
                       "zg361_scoreboard_page_received" &&
                   result.widgets[12].runtime_name ==
                       "zg361_scoreboard_page_system" &&
                   result.widgets[13].runtime_name ==
                       "zg361_scoreboard_modal_backdrop_close" &&
                   result.widgets[14].runtime_name ==
                       "zg361_scoreboard_header_close" &&
                   result.widgets[5].instance_pointer.available &&
                   result.widgets[5].vtable_pointer.value == "0x14506020" &&
                   result.widgets[5].local_visible.value == true &&
                   result.widgets[4].local_visible.value == false,
               "eleven action/postcondition probes must expose identity, pointers and "
               "visibility");
  ok &= Expect(result.widgets[0].enabled.available &&
                   result.widgets[0].enabled.value == true &&
                   result.widgets[8].enabled.available &&
                   result.widgets[8].enabled.value == false &&
                   !result.widgets[0].focused.available &&
                   !result.widgets[0].scroll_max.available,
               "effective enabled must use +D0 bit 0x02 while other "
               "unfrozen widget ABI stays typed unavailable");
  ok &= Expect(!result.actions.activate.available &&
                   !result.actions.close.available &&
                   !result.actions.reopen.available &&
                   !result.readiness.full_widget_gate_ready &&
                   !result.readiness.production_live_ready,
               "read-only static provider must not claim actions or live");
  ok &= Expect(result.provider_session_id ==
                       "0123456789ABCDEF0123456789ABCDEF" &&
                   result.observation_sequence == 1 &&
                   result.observed_state_revision == 1 &&
                   result.tree_fingerprint_v1.size() == 64 &&
                   result.semantic_fingerprint_v1.size() == 64,
               "first provider observation must publish two diagnostics and "
               "revision 1");
  ok &= Expect(CanonicalEncodingMatches(tracker, fixture),
               "provider canonical TREE/SEMANTIC v1 layout drifted");
  const auto tree_a = result.tree_fingerprint_v1;
  const auto semantic_a = result.semantic_fingerprint_v1;
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

  request.request_nonce = "scoreboard-fixture-same";
  xar::game::ZhongguoScoreboardStateV1 same{};
  const auto same_read = xar::ck3_11906::ReadZhongguoScoreboardStateV1(
      Environment(), Access(fixture), request, same);
  ok &= Expect(
      same_read == xar::game::ReadZhongguoScoreboardStateResultV1::available &&
          same.observation_sequence == 2 &&
          same.observed_state_revision == 1 &&
          same.tree_fingerprint_v1 == tree_a &&
          same.semantic_fingerprint_v1 == semantic_a,
      "identical successful observation advances sequence but not revision");

  // Open B: modal/panel and received page are visible, closed entries are
  // hidden, and the top modal receiver is a strict descendant of the modal.
  fixture.widgets[2][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] = 0;
  fixture.widgets[3][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] = 0;
  fixture.widgets[5][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[11][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] = 0;
  SetModalReceivers(fixture, {fixture.widgets[3].data()});
  request.request_nonce = "scoreboard-fixture-b";
  xar::game::ZhongguoScoreboardStateV1 state_b{};
  const auto read_b = xar::ck3_11906::ReadZhongguoScoreboardStateV1(
      Environment(), Access(fixture), request, state_b);
  ok &= Expect(
      read_b == xar::game::ReadZhongguoScoreboardStateResultV1::available &&
          state_b.observation_sequence == 3 &&
          state_b.observed_state_revision == 2 &&
          state_b.tree_fingerprint_v1 == tree_a &&
          state_b.semantic_fingerprint_v1 != semantic_a,
      "sampled open state must change semantic revision without changing tree");

  // Return to A. Because B was actually sampled, A-B-A advances revision a
  // second time even though the public semantic diagnostic returns to A.
  fixture.widgets[2][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[3][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[5][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] = 0;
  fixture.widgets[11][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  SetModalReceivers(fixture, {});
  request.request_nonce = "scoreboard-fixture-a-return";
  xar::game::ZhongguoScoreboardStateV1 returned_a{};
  const auto returned_read = xar::ck3_11906::ReadZhongguoScoreboardStateV1(
      Environment(), Access(fixture), request, returned_a);
  ok &= Expect(
      returned_read ==
              xar::game::ReadZhongguoScoreboardStateResultV1::available &&
          returned_a.observation_sequence == 4 &&
          returned_a.observed_state_revision == 3 &&
          returned_a.semantic_fingerprint_v1 == semantic_a,
      "sampled A-B-A must retain proof through the monotonic revision");

  request.provider_read_mode = xar::ck3_11906::
      ZhongguoScoreboardProviderReadModeV1::validate_without_advancing;
  request.request_nonce = "scoreboard-fixture-ack-validation";
  xar::game::ZhongguoScoreboardStateV1 validation{};
  const auto validation_read = xar::ck3_11906::ReadZhongguoScoreboardStateV1(
      Environment(), Access(fixture), request, validation);
  ok &= Expect(
      validation_read ==
              xar::game::ReadZhongguoScoreboardStateResultV1::available &&
          validation.observation_sequence == 4 &&
          validation.observed_state_revision == 3 &&
          tracker.observation_sequence == 4 &&
          tracker.observed_state_revision == 3,
      "ACK validation read must never advance provider observation state");

  // An unsampled B cannot be accepted or silently recorded by ACK validation.
  fixture.widgets[2][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] = 0;
  fixture.widgets[3][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] = 0;
  fixture.widgets[5][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[11][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] = 0;
  SetModalReceivers(fixture, {fixture.widgets[3].data()});
  xar::game::ZhongguoScoreboardStateV1 unsampled_b{};
  const auto unsampled_read = xar::ck3_11906::ReadZhongguoScoreboardStateV1(
      Environment(), Access(fixture), request, unsampled_b);
  ok &= Expect(
      unsampled_read ==
              xar::game::ReadZhongguoScoreboardStateResultV1::unavailable &&
          unsampled_b.unavailable_reason == "provider_revision_unavailable" &&
          tracker.observation_sequence == 4 &&
          tracker.observed_state_revision == 3,
      "ACK may neither publish nor advance an unsampled semantic change");

  fixture.widgets[2][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetLocalHiddenMask |
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[3][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  fixture.widgets[5][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] = 0;
  fixture.widgets[11][xar::ck3_11906::kZhongguoWidgetHiddenFlagsOffset] =
      xar::ck3_11906::kZhongguoWidgetEffectiveHiddenMask;
  SetModalReceivers(fixture, {});
  request.provider_read_mode = xar::ck3_11906::
      ZhongguoScoreboardProviderReadModeV1::publish_observation;

  fixture.rows["zg361_sb_self_disclosure_policy_id"] = Integer(903);
  xar::game::ZhongguoScoreboardStateV1 inconsistent{};
  const auto rejected = xar::ck3_11906::ReadZhongguoScoreboardStateV1(
      Environment(), Access(fixture), request, inconsistent);
  ok &= Expect(
      rejected == xar::game::ReadZhongguoScoreboardStateResultV1::unavailable &&
          inconsistent.unavailable_reason == "acl_inconsistent" &&
          tracker.observation_sequence == 4 &&
          tracker.observed_state_revision == 3,
      "unavailable query must not update provider state; policy ID binds B1 "
      "case 41, never result case 903");

  fixture.rows["zg361_sb_self_disclosure_policy_id"] = Integer(41);
  request.connection_generation = 4;
  request.request_nonce = "scoreboard-new-connection";
  xar::game::ZhongguoScoreboardStateV1 rebound{};
  const auto rebound_read = xar::ck3_11906::ReadZhongguoScoreboardStateV1(
      Environment(), Access(fixture), request, rebound);
  ok &= Expect(
      rebound_read ==
              xar::game::ReadZhongguoScoreboardStateResultV1::available &&
          rebound.observation_sequence == 1 &&
          rebound.observed_state_revision == 1 &&
          tracker.connection_generation == 4,
      "connection binding change must begin a new provider observation line");

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
