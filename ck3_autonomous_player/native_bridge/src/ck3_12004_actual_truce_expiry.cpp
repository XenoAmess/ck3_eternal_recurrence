#include "xar_bridge/ck3_12004_actual_truce_expiry.hpp"

namespace xar::ck3_12004 {
namespace {
struct ReadContext {
  const ActualTruceExpiryBindings12004 *bindings = nullptr;
  std::int32_t owner_id = 0;
  std::int32_t toward_id = 0;
  void *owner = nullptr;
  void *toward = nullptr;
};

bool ReadSnapshot(void *opaque, game::Snapshot &out) noexcept {
  auto &context = *static_cast<ReadContext *>(opaque);
  CoreSnapshotPrefix frame{};
  if (!xar::ck3_12004::ReadCoreSnapshot(context.bindings->core, frame)) return false;
  out = {};
  out.date_raw = frame.clock.date_raw;
  out.speed = frame.clock.speed;
  out.paused = frame.clock.paused;
  out.player_id = frame.local_player_id;
  out.map_ready = frame.map_ready;
  out.has_played_character = frame.has_played_character;
  out.played_character_id = frame.played_character_id;
  out.played_character_alive = frame.played_character_alive;
  context.owner_id = frame.played_character_id;
  return true;
}

void *ResolveCharacter(void *opaque, std::int32_t full_id) noexcept {
  auto &context = *static_cast<ReadContext *>(opaque);
  void *value = xar::ck3_12004::ResolveCoreCharacter(context.bindings->core, full_id);
  if (full_id == context.owner_id) context.owner = value;
  if (full_id == context.toward_id) context.toward = value;
  return value;
}

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') { out += '\\'; out += static_cast<char>(byte); }
    else if (byte < 0x20) { out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15]; }
    else out += static_cast<char>(byte);
  }
  return out + '"';
}
const char *Bool(bool value) noexcept { return value ? "true" : "false"; }
const char *Status(game::RaiktorActualTruceExpiryStatusV1 value) noexcept {
  switch (value) {
  case game::RaiktorActualTruceExpiryStatusV1::available: return "available";
  case game::RaiktorActualTruceExpiryStatusV1::no_truce: return "no_truce";
  case game::RaiktorActualTruceExpiryStatusV1::unavailable: return "unavailable";
  }
  return "unavailable";
}
} // namespace

ActualTruceExpiryBindings12004 BindActualTruceExpiryImage12004(
    void *module, std::string_view executable_sha256) noexcept {
  ActualTruceExpiryBindings12004 out{};
  const auto base = reinterpret_cast<std::uintptr_t>(module);
  if (base == 0 || executable_sha256 != kExecutableSha256) return out;
  out.core = BindCoreImage(base, executable_sha256);
  if (!out.core.enabled) return {};
  out.has_truce = reinterpret_cast<ck3_11906::RaiktorHasTruceV1>(
      base + kActualHasTruceRva12004);
  out.get_truce_end_date = reinterpret_cast<ck3_11906::RaiktorGetTruceEndDateV1>(
      base + kActualTruceEndDateRva12004);
  out.exact_build_admitted = true;
  return out;
}

game::ReadRaiktorActualTruceExpiryResultV1 ReadActualTruceExpiry12004(
    const ActualTruceExpiryBindings12004 &bindings,
    std::int32_t toward_character_id,
    game::RaiktorActualTruceExpirySnapshotV1 &output) noexcept {
  ReadContext context{&bindings, 0, toward_character_id, nullptr, nullptr};
  ck3_11906::RaiktorActualTruceExpiryAccessV1 access{};
  access.exact_build_admitted = bindings.exact_build_admitted && bindings.core.enabled;
  access.context = &context;
  access.read_snapshot = ReadSnapshot;
  access.resolve_character = ResolveCharacter;
  access.has_truce = bindings.has_truce;
  access.get_truce_end_date = bindings.get_truce_end_date;
  const auto result = ck3_11906::ReadRaiktorActualTruceExpiryV1(
      access, toward_character_id, output);
  using Result = game::ReadRaiktorActualTruceExpiryResultV1;
  if ((result == Result::available || result == Result::no_truce) &&
      (xar::ck3_12004::ResolveCoreCharacter(bindings.core, output.owner_character_id) != context.owner ||
       xar::ck3_12004::ResolveCoreCharacter(bindings.core, toward_character_id) != context.toward)) {
    output.status = game::RaiktorActualTruceExpiryStatusV1::unavailable;
    output.native_has_truce = false;
    output.actual_expiry_observable = false;
    output.expiry_date_raw = 0;
    output.same_frame_stable = false;
    output.readiness = false;
    output.unavailable_reason = "character_generation_changed_during_query";
    return Result::unstable_snapshot;
  }
  return result;
}

std::string SerializeActualTruceExpiry12004(
    const game::RaiktorActualTruceExpirySnapshotV1 &s) {
  return "{\"schema_version\":1,\"backend_id\":" + Quote(kActualTruceExpiryBackend12004) +
      ",\"ck3_build\":" + Quote(kGameVersion) +
      ",\"executable_sha256\":" + Quote(kExecutableSha256) +
      ",\"status\":" + Quote(Status(s.status)) +
      ",\"snapshot_revision\":" + std::to_string(s.snapshot_revision) +
      ",\"current_date_raw\":" + std::to_string(s.current_date_raw) +
      ",\"owner_character_id\":" + std::to_string(s.owner_character_id) +
      ",\"toward_character_id\":" + std::to_string(s.toward_character_id) +
      ",\"native_has_truce\":" + Bool(s.native_has_truce) +
      ",\"actual_expiry_observable\":" + Bool(s.actual_expiry_observable) +
      ",\"expiry_date_raw\":" + (s.actual_expiry_observable ? std::to_string(s.expiry_date_raw) : "null") +
      ",\"same_frame_stable\":" + Bool(s.same_frame_stable) +
      ",\"readiness\":" + Bool(s.readiness) +
      ",\"temporal_semantics\":" + Quote(s.temporal_semantics) +
      ",\"unavailable_reason\":" + (s.unavailable_reason.empty() ? std::string("null") : Quote(s.unavailable_reason)) + '}';
}
} // namespace xar::ck3_12004
