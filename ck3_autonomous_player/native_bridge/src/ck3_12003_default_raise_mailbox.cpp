#include "xar_bridge/ck3_12003_default_raise_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"

namespace xar::ck3_12003 {
namespace {
std::string Quote(std::string_view value) {
  std::string out = "\"";
  for (const char c : value) {
    if (c == '"' || c == '\\') out += '\\';
    out += c;
  }
  return out + '"';
}
std::string_view Status(ck3_12002::PrewarDefaultMusterStatusV1 status) noexcept {
  using S = ck3_12002::PrewarDefaultMusterStatusV1;
  switch (status) {
  case S::available: return "available";
  case S::partial: return "partial";
  case S::requires_paused: return "requires_paused";
  case S::invalid_request: return "invalid_request";
  case S::unavailable: return "unavailable";
  }
  return "unavailable";
}
} // namespace
bool ExecutePlayerDefaultRaiseMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<ck3_12002::QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !ck3_12002::EnterQueryMailbox(*envelope, stamp,
          &ExecutePlayerDefaultRaiseMailboxV1)) return false;
  auto &query = *static_cast<PlayerDefaultRaiseMailboxContextV1 *>(envelope->typed_context);
  if (envelope != &query.envelope || query.completed ||
      !game::IsCk3_12003Descriptor(envelope->game->descriptor())) return false;
  game::ReadCk3_12003PlayerDefaultRaiseV1(*envelope->game, query.observation);
  query.completed = true;
  return ck3_12002::FinishQueryMailbox(*envelope);
}
std::string SerializePlayerDefaultRaiseV1(
    const ck3_12002::PlayerDefaultRaiseObservationV1 &observation,
    std::uint64_t query_sequence, std::uint64_t snapshot_revision,
    std::int32_t date_raw) {
  const auto &row = observation.actor;
  std::string out = "{\"step\":" + Quote(kPlayerDefaultRaiseStepV1) +
      ",\"accepted\":true,\"status\":\"completed\",\"read_only\":true,"
      "\"query_sequence\":" + std::to_string(query_sequence) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(date_raw) +
      ",\"player_default_raise\":{\"schema\":\"ck3_12003_player_default_raise_v1\","
      "\"game_version\":\"1.20.0.3\",\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"status\":" + Quote(Status(observation.status)) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(observation.date_raw) +
      ",\"actor_character_id\":" + std::to_string(row.character_id) +
      ",\"default_raise_province_id\":" +
      (row.default_raise_province_id ? std::to_string(*row.default_raise_province_id) : "null") +
      ",\"native_default_raise_legal\":" +
      (row.native_default_raise_legal ? std::string(*row.native_default_raise_legal ? "true" : "false") : "null") +
      ",\"default_raise_legality_ready\":" +
      (observation.default_raise_legality_ready ? "true" : "false") +
      ",\"failure\":" + Quote(row.failure) + "}}";
  return out;
}
} // namespace xar::ck3_12003
