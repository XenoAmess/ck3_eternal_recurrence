#include "xar_bridge/ingame_ui_mailbox_v1.hpp"

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/protocol.hpp"

namespace xar::ck3_11906 {

std::string_view PrepareIngameUiMailboxV1(
    const game::GameAdapter &game, const game::Snapshot *previous_snapshot,
    std::string_view payload, std::string_view step,
    std::uint64_t state_revision, std::uint64_t connection_generation,
    std::uintptr_t module_base, MainThreadQueryMailboxV1 &mailbox,
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  query = {};
  std::uint64_t expected_revision = 0;
  game::Snapshot current{};
  if (!bridge::JsonUnsignedField(payload, "expected_revision", expected_revision) ||
      expected_revision != state_revision || !previous_snapshot ||
      !game::ReadSnapshot(game, current) || current != *previous_snapshot)
    return "state_changed";
  if (!current.paused || !current.map_ready || !current.has_played_character)
    return "requires_paused_map_ready_played_actor";
  IngameUiRequestV1 request{};
  if (!ParseIngameUiRequestV1(payload, step == kIngameUiWindowQueryV1Step, request))
    return "invalid_typed_ui_request";
  const auto &descriptor = game.descriptor();
  const bool actual4 = descriptor.game_version == ck3_12004::kGameVersion &&
      descriptor.executable_sha256 == ck3_12004::kExecutableSha256;
  const bool actual3 = descriptor.game_version == ck3_12003::kGameVersion &&
      descriptor.executable_sha256 == ck3_12003::kExecutableSha256;
  const bool legacy = descriptor.game_version == "1.19.0.6" &&
      descriptor.executable_sha256 == kExecutableSha256;
  if (!actual4 && !actual3 && !legacy) return "typed_ui_exact_build_not_available";
  const auto revision = actual4 ? GuiAbiRevisionV1::crozier12004 :
      actual3 ? GuiAbiRevisionV1::crozier12003 : GuiAbiRevisionV1::legacy11906;
  if (!IsIngameUiRequestSupportedV1(revision, request))
    return "typed_ui_operation_not_available_for_exact_build";
  query.mailbox = &mailbox;
  query.operation = FrontendGuiRouteOperationV1::ingame_ui;
  if (actual4 || actual3) query.ingame_game = &game;
  else query.ingame_bindings = BindCurrentProcess(true);
  query.ingame_expected_snapshot = current;
  query.ingame_request = request;
  query.ingame_request.connection_generation = connection_generation;
  query.ingame_request.native_revision = state_revision;
  query.environment = BindZhongguoScoreboardNativeEnvironmentV1(
      module_base, true, revision, descriptor.executable_sha256);
  query.ingame_result.gui_abi_revision = revision;
  return {};
}

std::string IngameUiCommandResultFrameV1(
    std::string_view request_id, const IngameUiRequestV1 &request,
    const IngameUiResultV1 &result, std::uint64_t state_revision) {
  std::string frame = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"";
  frame += request_id;
  frame += "\",\"ok\":true,\"result\":";
  frame += SerializeIngameUiResultV1(request, result, state_revision);
  frame += '}';
  return frame;
}

} // namespace xar::ck3_11906
