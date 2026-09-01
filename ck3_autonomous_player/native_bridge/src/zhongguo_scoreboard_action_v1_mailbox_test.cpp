#include "xar_bridge/zhongguo_scoreboard_action_v1_mailbox.hpp"

#include <windows.h>

#include <array>
#include <cstdint>
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

xar::game::Snapshot g_snapshot{};
xar::game::ZhongguoScoreboardStateV1 g_source{};
bool g_fixture_gui_resolver_forwarded = false;

template <typename Value>
void Available(xar::game::ZhongguoTypedValueV1<Value> &field, Value value) {
  field.available = true;
  field.value = std::move(value);
  field.unavailable_reason.clear();
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

xar::game::ZhongguoScoreboardStateV1 Source(std::string_view nonce) {
  xar::game::ZhongguoScoreboardStateV1 source{};
  source.status = xar::game::ZhongguoScoreboardStateStatusV1::available;
  source.case_kind = xar::ck3_11906::kZhongguoScoreboardStateV1CaseKind;
  source.request_nonce.assign(nonce);
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
  Available(source.widgets[0].effective_visible, true);
  Available(source.widgets[1].effective_visible, true);
  Available(source.widgets[5].effective_visible, true);
  return source;
}

xar::game::Snapshot Snapshot() {
  xar::game::Snapshot snapshot{};
  snapshot.date_raw = 4242;
  snapshot.paused = true;
  snapshot.map_ready = true;
  snapshot.has_played_character = true;
  snapshot.played_character_alive = true;
  snapshot.played_character_id = 101;
  return snapshot;
}

bool Dispatch(void *, xar::game::ZhongguoScoreboardActionV1,
              std::string_view stable_identity, std::string_view runtime_name,
              std::string_view, std::string_view,
              bool &native_handled) noexcept {
  native_handled = false;
  return stable_identity == "zg361_scoreboard_entry_received" &&
         stable_identity == runtime_name;
}

bool ResolveFixtureGui(void *, void *&gui_context, void *&gui_owner) noexcept {
  gui_context = reinterpret_cast<void *>(0x14001000);
  gui_owner = reinterpret_cast<void *>(0x14002000);
  return true;
}

bool Expect(bool condition, std::string_view message) {
  if (!condition) std::cerr << message << '\n';
  return condition;
}

void PrepareMailbox(
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    xar::ck3_11906::ZhongguoScoreboardActionMailboxContextV1 &context,
    std::uint64_t sequence) {
  context.mailbox = &mailbox;
  context.ticket.sequence = sequence;
  context.expected_snapshot = g_snapshot;
  context.request.request_nonce = "scoreboard.action";
  context.request.action = xar::game::ZhongguoScoreboardActionV1::open;
  context.request.expected_revision = 19;
  context.request.expected_native_revision = 77;
  context.request.expected_connection_generation = 3;
  context.request.expected_player_character_id = 101;
  context.request.expected_provider_session_id.assign(kProviderSession);
  context.request.expected_observation_sequence = 7;
  context.request.expected_observed_state_revision = 3;
  context.request.expected_tree_fingerprint_v1.assign(kTreeFingerprint);
  context.request.expected_semantic_fingerprint_v1.assign(
      kSemanticFingerprint);
  context.request.expected_window_instance_pointer = Pointer(2);
  context.request.expected_target_instance_pointer = Pointer(6);
  context.request.expected_target_vtable_pointer = "0x14506020";
  context.state_access.resolve_fixture_gui = &ResolveFixtureGui;
  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  mailbox.stop_requested.store(false);
  mailbox.failure_flags.store(0);
  mailbox.published_sequence.store(sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor =
      &xar::ck3_11906::ExecuteZhongguoScoreboardActionMailboxV1;
  mailbox.executor_context = &context;
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}

game::ReadZhongguoScoreboardStateResultV1 ReadZhongguoScoreboardStateV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &,
    const ZhongguoScoreboardAccessV1 &access,
    const ZhongguoScoreboardStateRequestV1 &request,
    game::ZhongguoScoreboardStateV1 &output) noexcept {
  void *gui_context = nullptr;
  void *gui_owner = nullptr;
  if (access.resolve_fixture_gui == nullptr ||
      !access.resolve_fixture_gui(access.context, gui_context, gui_owner) ||
      gui_context != reinterpret_cast<void *>(0x14001000) ||
      gui_owner != reinterpret_cast<void *>(0x14002000)) {
    return game::ReadZhongguoScoreboardStateResultV1::unavailable;
  }
  g_fixture_gui_resolver_forwarded = true;
  output = g_source;
  output.request_nonce = request.request_nonce;
  output.snapshot_revision = request.expected_snapshot_revision;
  return game::ReadZhongguoScoreboardStateResultV1::available;
}

} // namespace xar::ck3_11906

int main() {
  bool ok = true;
  xar::game::ZhongguoScoreboardActionRequestV1 parsed{};
  const std::string request =
      "{\"type\":\"execute_step\",\"protocol_version\":1,"
      "\"request_id\":\"fixture\","
      "\"step\":\"activate-zhongguo-scoreboard-v1\","
      "\"expected_revision\":77,"
      "\"request_nonce\":\"scoreboard.action\",\"action\":\"open\","
      "\"expected_public_revision\":19,"
      "\"expected_native_revision\":77,"
      "\"expected_connection_generation\":3,"
      "\"expected_player_character_id\":101,"
      "\"expected_provider_session_id\":"
      "\"0123456789ABCDEF0123456789ABCDEF\","
      "\"expected_observation_sequence\":7,"
      "\"expected_observed_state_revision\":3,"
      "\"expected_tree_fingerprint_v1\":"
      "\"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\","
      "\"expected_semantic_fingerprint_v1\":"
      "\"BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB\","
      "\"expected_window_instance_pointer\":\"0x14000200\","
      "\"expected_target_instance_pointer\":\"0x14000600\","
      "\"expected_target_vtable_pointer\":\"0x14506020\"}";
  ok &= Expect(xar::ck3_11906::ParseZhongguoScoreboardActionRequestV1(
                   request, parsed),
               "exact request did not parse");
  ok &= Expect(parsed.expected_revision == 19 &&
                   parsed.expected_native_revision == 77 &&
                   parsed.expected_connection_generation == 3 &&
                   parsed.expected_provider_session_id == kProviderSession &&
                   parsed.expected_observation_sequence == 7 &&
                   parsed.expected_observed_state_revision == 3,
               "public/native/generation revisions were conflated");
  const std::string unknown = request.substr(0, request.size() - 1) +
                              ",\"unknown_field\":1}";
  ok &= Expect(!xar::ck3_11906::ParseZhongguoScoreboardActionRequestV1(
                    unknown, parsed),
               "unknown request field was accepted");
  std::string mismatched = request;
  const auto native = mismatched.find("\"expected_native_revision\":77");
  mismatched.replace(native, std::string("\"expected_native_revision\":77").size(),
                     "\"expected_native_revision\":78");
  ok &= Expect(!xar::ck3_11906::ParseZhongguoScoreboardActionRequestV1(
                    mismatched, parsed),
               "wire/native revision mismatch was accepted");

  g_snapshot = Snapshot();
  g_source = Source("scoreboard.action");
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 1;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address = 1;
  stamp.tls_initialized = 1;
  stamp.tls_context = 1;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 1;
  stamp.game_state = 1;
  stamp.date_raw = 4242;
  stamp.paused = true;

  xar::ck3_11906::MainThreadQueryMailboxV1 unavailable_mailbox{};
  xar::ck3_11906::ZhongguoScoreboardActionMailboxContextV1 unavailable{};
  PrepareMailbox(unavailable_mailbox, unavailable, 1);
  ok &= Expect(
      xar::ck3_11906::ExecuteZhongguoScoreboardActionMailboxV1(&unavailable,
                                                               stamp),
      "fail-closed action executor did not complete structurally");
  ok &= Expect(
      unavailable.completion ==
              xar::ck3_11906::ZhongguoScoreboardActionMailboxCompletionV1::
                  completed_unavailable &&
          !unavailable.result.accepted &&
          unavailable.result.rejection_reason == "action_dispatch_unavailable",
      "missing dispatch did not return typed unavailable");

  xar::ck3_11906::MainThreadQueryMailboxV1 acknowledged_mailbox{};
  xar::ck3_11906::ZhongguoScoreboardActionMailboxContextV1 acknowledged{};
  PrepareMailbox(acknowledged_mailbox, acknowledged, 2);
  acknowledged.action_access.dispatch = &Dispatch;
  ok &= Expect(
      xar::ck3_11906::ExecuteZhongguoScoreboardActionMailboxV1(&acknowledged,
                                                               stamp),
      "injected fixture dispatch did not complete");
  ok &= Expect(
      acknowledged.completion ==
              xar::ck3_11906::ZhongguoScoreboardActionMailboxCompletionV1::
                  completed_acknowledged &&
          acknowledged.result.accepted &&
          !acknowledged.result.postcondition_verified,
      "fixture ACK was missing or incorrectly verified");
  ok &= Expect(g_fixture_gui_resolver_forwarded,
               "mailbox did not forward fixture GUI resolver");

  return ok ? 0 : 1;
}
