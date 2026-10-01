#include "xar_bridge/ck3_12002_prewar_muster.hpp"

#include <cstring>

namespace xar::ck3_12002 {
namespace {
template <typename T> T LoadAt(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  output += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') {
      output += '\\';
      output += static_cast<char>(c);
    } else if (c < 0x20) {
      output += "\\u00";
      output += hex[c >> 4];
      output += hex[c & 15];
    } else {
      output += static_cast<char>(c);
    }
  }
  output += '"';
}

std::string_view StatusKey(PrewarDefaultMusterStatusV1 status) noexcept {
  switch (status) {
  case PrewarDefaultMusterStatusV1::available: return "available";
  case PrewarDefaultMusterStatusV1::partial: return "partial";
  case PrewarDefaultMusterStatusV1::invalid_request: return "invalid_request";
  case PrewarDefaultMusterStatusV1::requires_paused: return "requires_paused";
  case PrewarDefaultMusterStatusV1::unavailable: return "unavailable";
  }
  return "unavailable";
}

struct CommandCleanup {
  const MilitaryBindings &bindings;
  void *command = nullptr;
  ~CommandCleanup() {
    if (command != nullptr) bindings.destroy_raise(command, 0);
  }
};

void ReadRow(const MilitaryBindings &bindings, const MilitaryWorldAccess &world,
             PrewarDefaultMusterRowV1 &row) noexcept {
  void *const character =
      world.resolve_character(world.context, row.character_id);
  if (character == nullptr ||
      LoadAt<std::int32_t>(character, 0x18) != row.character_id) {
    row.failure = "character_unavailable";
    return;
  }
  void *const province = ResolveMilitaryDefaultRaiseProvince(bindings, character);
  if (province == nullptr) {
    row.failure = "default_province_unavailable";
    return;
  }
  const auto province_id = LoadAt<std::int32_t>(province, 0x10);
  if (province_id < 1 ||
      world.resolve_province(world.context, province_id) != province) {
    row.failure = "default_province_unavailable";
    return;
  }
  row.default_raise_province_id = province_id;
  alignas(16) std::array<std::byte, 0x50> storage{};
  const std::array<std::int32_t, 2> entry{province_id, -1};
  void *const command = storage.data();
  if (bindings.construct_raise(command, row.character_id, entry.data()) !=
      command) {
    row.failure = "temporary_command_unavailable";
    return;
  }
  CommandCleanup cleanup{bindings, command};
  if (LoadAt<std::uintptr_t>(command, 0) != bindings.raise_primary ||
      LoadAt<std::uintptr_t>(command, 0x18) != bindings.raise_secondary) {
    row.failure = "temporary_command_unavailable";
    return;
  }
  row.native_default_raise_legal = bindings.validate_raise(command, nullptr);
  row.failure = "none";
}
} // namespace

PrewarDefaultMusterStatusV1 ReadPrewarDefaultMusterV1(
    const MilitaryBindings &bindings, const MilitaryWorldAccess &world,
    const PrewarDefaultMusterRequestV1 &request,
    PrewarDefaultMusterObservationV1 &output) noexcept {
  output = {};
  output.request = request;
  output.rows[0].character_id = request.actor_character_id;
  output.rows[0].attacker = true;
  output.rows[1].character_id = request.effective_defender_character_id;
  if (request.actor_character_id <= 0 ||
      request.effective_defender_character_id <= 0 ||
      request.actor_character_id == request.effective_defender_character_id) {
    output.status = PrewarDefaultMusterStatusV1::invalid_request;
    return output.status;
  }
  if (!bindings.enabled || world.read_snapshot == nullptr ||
      world.resolve_character == nullptr || world.resolve_province == nullptr ||
      bindings.get_character_capital == nullptr ||
      bindings.resolve_raise_province == nullptr ||
      bindings.construct_raise == nullptr || bindings.validate_raise == nullptr ||
      bindings.destroy_raise == nullptr || bindings.raise_primary == 0 ||
      bindings.raise_secondary == 0) {
    return output.status;
  }
  game::Snapshot snapshot{};
  if (!world.read_snapshot(world.context, snapshot)) return output.status;
  output.date_raw = snapshot.date_raw;
  if (!snapshot.paused) {
    output.status = PrewarDefaultMusterStatusV1::requires_paused;
    return output.status;
  }
  if (!snapshot.map_ready || !snapshot.has_played_character ||
      !snapshot.played_character_alive ||
      snapshot.played_character_id != request.actor_character_id) {
    output.status = PrewarDefaultMusterStatusV1::invalid_request;
    return output.status;
  }
  ReadRow(bindings, world, output.rows[0]);
  ReadRow(bindings, world, output.rows[1]);
  output.default_raise_legality_ready =
      output.rows[0].native_default_raise_legal.has_value() &&
      output.rows[1].native_default_raise_legal.has_value();
  output.status = output.default_raise_legality_ready
                      ? PrewarDefaultMusterStatusV1::available
                      : PrewarDefaultMusterStatusV1::partial;
  return output.status;
}

std::string SerializePrewarDefaultMusterV1(
    std::string_view request_id, std::uint64_t snapshot_revision,
    const PrewarDefaultMusterObservationV1 &observation) {
  std::string output =
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(output, request_id);
  output += ",\"ok\":true,\"result\":{\"step\":";
  AppendString(output, kPrewarDefaultMusterStepV1);
  output += ",\"accepted\":true,\"private_build\":true,\"read_only\":true,"
            "\"advertised\":false,\"domain_key\":\"prewar_default_muster\","
            "\"game_version\":\"1.20.0.2\","
            "\"executable_sha256\":\"AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D\","
            "\"snapshot_revision\":";
  output += std::to_string(snapshot_revision);
  output += ",\"date_raw\":" + std::to_string(observation.date_raw);
  output += ",\"actor_character_id\":" +
            std::to_string(observation.request.actor_character_id);
  output += ",\"effective_defender_character_id\":" +
            std::to_string(observation.request.effective_defender_character_id);
  output += ",\"status\":";
  AppendString(output, StatusKey(observation.status));
  output += ",\"rows\":[";
  for (std::size_t i = 0; i < observation.rows.size(); ++i) {
    if (i != 0) output += ',';
    const auto &row = observation.rows[i];
    output += "{\"character_id\":" + std::to_string(row.character_id);
    output += ",\"side\":\"";
    output += row.attacker ? "attacker" : "defender";
    output += "\",\"default_raise_province_id\":";
    output += row.default_raise_province_id
                  ? std::to_string(*row.default_raise_province_id) : "null";
    output += ",\"native_default_raise_legal\":";
    output += row.native_default_raise_legal
                  ? (*row.native_default_raise_legal ? "true" : "false") : "null";
    output += ",\"failure\":";
    AppendString(output, row.failure);
    output += '}';
  }
  output += "],\"default_raise_legality_ready\":";
  output += observation.default_raise_legality_ready ? "true" : "false";
  output += ",\"hypothetical_raised_roster_ready\":false,"
            "\"muster_time_ready\":false,\"future_supply_ready\":false}}";
  return output;
}
} // namespace xar::ck3_12002
