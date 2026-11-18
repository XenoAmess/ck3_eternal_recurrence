#include "xar_bridge/ck3_1210_actor_resource_leaf_v2.hpp"
#if defined(_MSC_VER)
#include <windows.h>
#endif
namespace xar::ck3_1210 {
namespace {
std::uintptr_t CurrentImageBase() noexcept {
#if defined(_MSC_VER)
  return reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
#else
  return 0;
#endif
}
bool SameCore(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool ReadCoreSafe(const CoreBindings &b, CoreSnapshotPrefix &out) noexcept {
#if defined(_MSC_VER)
  __try { return ReadCoreSnapshot(b, out); }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return ReadCoreSnapshot(b, out);
#endif
}
bool PausedActor(const CoreSnapshotPrefix &p) noexcept {
  return p.clock.paused && p.map_ready && p.local_player_id >= 0 &&
      p.has_played_character && p.played_character_id != -1 && p.played_character_alive;
}
bool SameBindings(const CoreBindings &a, const CoreBindings &b) noexcept {
  return a.enabled && b.enabled && a.game_state_slot == b.game_state_slot &&
      a.jomini_state_slot == b.jomini_state_slot &&
      a.character_storage_slot == b.character_storage_slot &&
      a.get_local_player == b.get_local_player;
}
bool Fail(ActorResourceLeafObservationV2 &o, std::string_view reason) noexcept {
  const bool image = o.exact_image_verified, owner = o.application_main_observed;
  o = {}; o.exact_image_verified = image; o.application_main_observed = owner;
  o.unavailable_reason = reason; return false;
}
bool ReadImpl(const ActorResourceLeafSourceInputV2 &i,
    ActorResourceLeafObservationV2 &o) noexcept {
  o = {};
  if (i.game_version != kGameVersion || i.executable_sha256 != kExecutableSha256 ||
      i.adapter_id != kAdapterId) return Fail(o, "unsupported_image_identity");
  const auto rebound = BindPersonalGoldImageV1(i.image_base, i.executable_sha256);
  if (!rebound.exact_build_admitted || !i.gold_bindings.exact_build_admitted ||
      !SameBindings(i.gold_bindings.core, rebound.core))
    return Fail(o, "image_core_binding_mismatch");
  o.exact_image_verified = true;
  if (!i.application_main_owner_admitted) return Fail(o, "application_main_owner_unavailable");
  o.application_main_observed = true;
  if (CurrentImageBase() == 0 || CurrentImageBase() != i.image_base)
    return Fail(o, "image_module_before_changed");
  if (!PausedActor(i.expected)) return Fail(o, "requires_paused_alive_actor");
  CoreSnapshotPrefix before{}, after{};
  if (!ReadCoreSafe(i.gold_bindings.core, before)) return Fail(o, "core_before_failed");
  if (!SameCore(before, i.expected)) return Fail(o, "core_before_changed");
  PersonalGoldObservationV1 gold_before{}, gold_after{};
  ActorFoundationObservationV1 actor{};
  if (!ReadPersonalGoldV1(i.gold_bindings, before, gold_before))
    return Fail(o, "personal_gold_before_unavailable");
  const bool actor_read = ReadActorFoundationV1(
      {true, i.gold_bindings.core}, before, actor);
  const bool gold_after_read = ReadPersonalGoldV1(i.gold_bindings, before, gold_after);
  if (!ReadCoreSafe(i.gold_bindings.core, after)) return Fail(o, "core_after_failed");
  if (CurrentImageBase() != i.image_base) return Fail(o, "image_module_after_changed");
  if (!SameCore(before, after) || !SameCore(after, i.expected))
    return Fail(o, "core_interval_changed");
  if (!actor_read || !actor.resources_ready || !actor.same_frame_ready ||
      !actor.gold_raw || !actor.prestige_raw || !actor.piety_raw ||
      actor.resource_scale != kActorFoundationResourceScaleV1 || !SameCore(actor.frame, before))
    return Fail(o, "actor_resources_unavailable");
  if (!gold_before.available || !gold_after_read || !gold_after.available ||
      !gold_before.same_frame_ready || !gold_after.same_frame_ready ||
      !gold_before.personal_gold_raw || !gold_after.personal_gold_raw ||
      gold_before.scale != kPersonalGoldScaleV1 || gold_after.scale != kPersonalGoldScaleV1 ||
      !SameCore(gold_before.frame, before) || !SameCore(gold_after.frame, before))
    return Fail(o, "personal_gold_interval_unavailable");
  if (gold_before.personal_gold_raw != actor.gold_raw || actor.gold_raw != gold_after.personal_gold_raw)
    return Fail(o, "personal_gold_interval_changed");
  o.before = before; o.after = after; o.actor_character_id = before.played_character_id;
  o.personal_gold_before_raw = gold_before.personal_gold_raw;
  o.actor_gold_raw = actor.gold_raw; o.personal_gold_after_raw = gold_after.personal_gold_raw;
  o.prestige_raw = actor.prestige_raw; o.piety_raw = actor.piety_raw;
  o.core_interval_verified = o.gold_interval_verified = true;
  o.unavailable_reason = {}; return true;
}
bool Ready(const ActorResourceLeafObservationV2 &o) noexcept {
  return o.exact_image_verified && o.application_main_observed &&
      o.core_interval_verified && o.gold_interval_verified && PausedActor(o.before) &&
      SameCore(o.before, o.after) && o.actor_character_id == o.before.played_character_id &&
      o.personal_gold_before_raw && o.actor_gold_raw && o.personal_gold_after_raw &&
      o.personal_gold_before_raw == o.actor_gold_raw && o.actor_gold_raw == o.personal_gold_after_raw &&
      o.prestige_raw && o.piety_raw && o.unavailable_reason.empty();
}
void Quote(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef"; out += char(34);
  for (const unsigned char c : value) {
    if (c == 34 || c == 92) { out += char(92); out += char(c); }
    else if (c < 32) { out += char(92); out += "u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += char(c);
  }
  out += char(34);
}
std::string Amount(std::int64_t raw) {
  return "{\"raw\":" + std::to_string(raw) + ",\"scale\":100000}";
}
std::string Prefix(const CoreSnapshotPrefix &p) {
  return "{\"date_raw\":" + std::to_string(p.clock.date_raw) +
      ",\"speed\":" + std::to_string(p.clock.speed) + ",\"paused\":true,\"local_player_id\":" +
      std::to_string(p.local_player_id) + ",\"map_ready\":true,\"has_played_character\":true,\"played_character_id\":" +
      std::to_string(p.played_character_id) + ",\"played_character_alive\":true}";
}
std::string Row(bool ready, const std::optional<std::int64_t> &raw,
    std::string_view reason) {
  if (ready && raw) return "{\"status\":\"available\",\"amount\":" + Amount(*raw) +
      ",\"unavailable_reason\":null}";
  std::string out = "{\"status\":\"unavailable\",\"amount\":null,\"unavailable_reason\":";
  Quote(out, reason); return out + '}';
}
} // namespace

bool ReadActorResourceLeafV2(const ActorResourceLeafSourceInputV2 &input,
    ActorResourceLeafObservationV2 &output) noexcept {
#if defined(_MSC_VER)
  __try { return ReadImpl(input, output); }
  __except(EXCEPTION_EXECUTE_HANDLER) { return Fail(output, "memory_read_failed"); }
#else
  return ReadImpl(input, output);
#endif
}
std::string SerializeActorResourceLeafV2(const ActorResourceLeafObservationV2 &o) {
  const bool ready = Ready(o);
  const auto reason = ready ? std::string_view{} : o.unavailable_reason.empty()
      ? std::string_view{"inconsistent_resource_leaf_dto"} : o.unavailable_reason;
  std::string out = "{\"step\":"; Quote(out, kActorResourceLeafStepV2);
  out += ",\"schema\":"; Quote(out, kActorResourceLeafSchemaV2);
  out += ",\"game_version\":"; Quote(out, kGameVersion);
  out += ",\"executable_sha256\":"; Quote(out, kExecutableSha256);
  out += ",\"adapter_id\":"; Quote(out, kAdapterId);
  out += ",\"steam_build_id\":"; Quote(out, kSteamBuildId);
  out += ",\"executable_file_size\":" + std::to_string(kExecutableFileSize);
  out += ",\"backend\":\"ck3-1.21.0-native-headless-main-thread\",\"status\":";
  Quote(out, ready ? "partial" : "unavailable");
  out += ",\"read_only\":true,\"resources_available\":"; out += ready ? "true" : "false";
  out += ",\"source_identity_verified\":"; out += o.exact_image_verified ? "true" : "false";
  out += ",\"application_main_observed\":"; out += o.application_main_observed ? "true" : "false";
  out += ",\"complete_snapshot\":false,\"root_ready\":false,\"formal_action_ready\":false";
  out += ",\"actor_character_id\":"; out += ready ? std::to_string(*o.actor_character_id) : "null";
  out += ",\"source_kind\":\"exact_1210_actor_foundation_personal_gold_interval\"";
  out += ",\"getter_sources\":{\"prestige\":\"0x2DA2810\",\"piety\":\"0x2DA27E0\",\"personal_gold\":\"0xD9E760\"}";
  out += ",\"core_before\":"; out += ready ? Prefix(o.before) : "null";
  out += ",\"core_after\":"; out += ready ? Prefix(o.after) : "null";
  out += ",\"personal_gold_interval\":";
  if (ready) out += "{\"before\":" + Amount(*o.personal_gold_before_raw) +
      ",\"actor_foundation\":" + Amount(*o.actor_gold_raw) +
      ",\"after\":" + Amount(*o.personal_gold_after_raw) + '}';
  else out += "null";
  out += ",\"resources\":{\"prestige\":" + Row(ready, o.prestige_raw, reason) +
      ",\"piety\":" + Row(ready, o.piety_raw, reason) +
      ",\"renown\":" + Row(false, {}, kActorResourceRenownUnknownV2) +
      ",\"true_treasury\":" + Row(false, {}, kActorResourceTreasuryUnknownV2) + '}';
  out += ",\"unavailable_reason\":";
  if (ready) out += "null"; else Quote(out, reason);
  return out + '}';
}
std::string SerializeActorResourceLeafCommandV2(std::string_view request_id,
    const ActorResourceLeafObservationV2 &o) {
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  Quote(out, request_id); out += ",\"ok\":true,\"result\":";
  return out + SerializeActorResourceLeafV2(o) + '}';
}
} // namespace xar::ck3_1210
