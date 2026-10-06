#include "xar_bridge/ck3_12004_core_frame_v1.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"

#include <array>

namespace xar::ck3_12004 {
namespace {
void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  output += '"';
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\b': output += "\\b"; break;
    case '\f': output += "\\f"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character < 0x20) {
        output += "\\u00";
        output += hex[character >> 4];
        output += hex[character & 15];
      } else {
        output += static_cast<char>(character);
      }
    }
  }
  output += '"';
}
const char *Boolean(bool value) noexcept { return value ? "true" : "false"; }
} // namespace

bool ExecuteCoreFrameMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *context = static_cast<CoreFrameMailboxContextV1 *>(opaque);
  if (context == nullptr) return false;
  auto &output = context->observation;
  output = {};
  output.application_main_observed = stamp.thread_id != 0 && stamp.pump_epoch != 0;
  if (!output.application_main_observed) {
    output.unavailable_reason = "application_main_not_observed";
    return true;
  }
  if (context->game == nullptr || !context->game->enabled() ||
      !game::IsCk3_12004Descriptor(context->game->descriptor()) ||
      !context->game->supports(kCoreFrameCapabilityV1) || context->read_core == nullptr) {
    output.unavailable_reason = "exact_core_reader_unavailable";
    return true;
  }
  // This entry point dispatches the selected core reader. It never calls the
  // complete Snapshot reader or fills any unreviewed resource family.
  game::Snapshot prefix{};
  if (!context->read_core(*context->game, prefix)) {
    output.unavailable_reason = "core_prefix_unavailable";
    return true;
  }
  if (prefix.date_raw != stamp.date_raw || prefix.paused != stamp.paused) {
    output.unavailable_reason = "core_frame_changed";
    return true;
  }
  output.core.clock = {prefix.date_raw, prefix.speed, prefix.paused};
  output.core.local_player_id = prefix.player_id;
  output.core.map_ready = prefix.map_ready;
  output.core.has_played_character = prefix.has_played_character;
  output.core.played_character_id = prefix.played_character_id;
  output.core.played_character_alive = prefix.played_character_alive;
  output.core_available = true;
  output.unavailable_reason = {};
  return true;
}

ck3_11906::MainThreadQueryInstallEnvironmentV1 BindCoreFrameMailboxEnvironmentV1(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  const std::array<ck3_11906::MainThreadQueryExecutorV1, 1> executors{
      &ExecuteCoreFrameMailboxV1};
  return BindThreadRuntimeImage(module_base, executable_sha256, executors);
}

std::string SerializeCoreFrameV1(const CoreFrameObservationV1 &observation) {
  std::string result = "{\"schema\":";
  AppendString(result, kCoreFrameSchemaV1);
  result += ",\"game_version\":";
  AppendString(result, kGameVersion);
  result += ",\"executable_sha256\":";
  AppendString(result, kExecutableSha256);
  result += ",\"adapter_id\":";
  AppendString(result, kAdapterId);
  result += ",\"backend\":\"ck3-1.20.0.4-native-headless-main-thread\",\"status\":";
  AppendString(result, observation.core_available ? "partial" : "unavailable");
  result += ",\"complete_snapshot\":false,\"core_available\":";
  result += Boolean(observation.core_available);
  result += ",\"application_main_observed\":";
  result += Boolean(observation.application_main_observed);
  result += ",\"unavailable_reason\":";
  if (observation.core_available) result += "null";
  else AppendString(result, observation.unavailable_reason);
  const auto number = [&observation](std::int32_t value) {
    return observation.core_available ? std::to_string(value) : std::string("null");
  };
  const auto boolean = [&observation](bool value) {
    return observation.core_available ? Boolean(value) : "null";
  };
  result += ",\"date_raw\":" + number(observation.core.clock.date_raw);
  result += ",\"speed\":" + number(observation.core.clock.speed);
  result += ",\"paused\":";
  result += boolean(observation.core.clock.paused);
  result += ",\"local_player_id\":" + number(observation.core.local_player_id);
  result += ",\"map_ready\":";
  result += boolean(observation.core.map_ready);
  result += ",\"has_played_character\":";
  result += boolean(observation.core.has_played_character);
  result += ",\"played_character_id\":" + number(observation.core.played_character_id);
  result += ",\"played_character_alive\":";
  result += boolean(observation.core.played_character_alive);
  result += ",\"excluded_snapshot_families\":[\"treasury\",\"domain\",\"military\",\"campaign\"]}";
  return result;
}

std::string SerializeCoreFrameCommandResultV1(std::string_view request_id,
    const CoreFrameObservationV1 &observation) {
  std::string result = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(result, request_id);
  result += ",\"ok\":true,\"result\":";
  result += SerializeCoreFrameV1(observation);
  result += '}';
  return result;
}
} // namespace xar::ck3_12004
