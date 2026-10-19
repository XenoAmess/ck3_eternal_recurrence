#include "xar_bridge/campaign_player_heir_candidate_component12004_v1.hpp"

namespace xar::ck3_12004::campaign_player_heir_candidate_v1 {
namespace {
#if defined(XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1)
void String(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (unsigned char c : value) {
    if (c == '"' || c == '\\') {
      out += '\\'; out += static_cast<char>(c);
    } else if (c < 0x20) {
      out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15];
    } else out += static_cast<char>(c);
  }
  out += '"';
}
void Reason(std::string &out, std::string_view reason) {
  if (reason.empty()) out += "null";
  else String(out, reason);
}
const char *Bool(bool value) noexcept { return value ? "true" : "false"; }
void Core(std::string &out, const CoreSnapshotPrefix &f) {
  out += "{\"date_raw\":" + std::to_string(f.clock.date_raw);
  out += ",\"paused\":"; out += Bool(f.clock.paused);
  out += ",\"speed\":" + std::to_string(f.clock.speed);
  out += ",\"local_player_id\":" + std::to_string(f.local_player_id);
  out += ",\"map_ready\":"; out += Bool(f.map_ready);
  out += ",\"has_played_character\":"; out += Bool(f.has_played_character);
  out += ",\"played_character_id\":" + std::to_string(f.played_character_id);
  out += ",\"played_character_alive\":"; out += Bool(f.played_character_alive);
  out += '}';
}
bool StillBound(const Component &c, const game::CampaignRootContextV1 &p) {
  const auto matches = [&p](const CoreSnapshotPrefix &f) {
    return f.clock.paused && f.map_ready && f.has_played_character &&
           f.played_character_alive && f.clock.date_raw == p.date_raw &&
           p.local_player_id && f.local_player_id == *p.local_player_id &&
           p.player_character_id && f.played_character_id == *p.player_character_id;
  };
  return c.snapshot_revision != 0 && c.snapshot_revision == p.snapshot_revision &&
         p.status == game::CampaignRootContextStatusV1::available &&
         p.readiness.same_frame_ready && p.player_character_alive == true &&
         c.observation.available && c.observation.identity_and_frame_stable &&
         matches(c.observation.before) && matches(c.observation.after) &&
         c.observation.actor_character_id == *p.player_character_id;
}
std::string Serialize(Component c, const game::CampaignRootContextV1 &parent) {
  if (c.parent_frame_bound && !StillBound(c, parent)) {
    c.parent_frame_bound = false;
    c.observation.available = false;
    c.observation.identity_and_frame_stable = false;
    c.observation.unavailable_reason = "serialized_parent_frame_changed";
  }
  auto &o = c.observation;
  if (!c.parent_frame_bound) {
    // No positive candidate facts survive an unbound parent. Diagnostic core
    // copies/source flags are retained; SDK still needs its trusted outer frame.
    o.candidate_present = false;
    o.candidate_character_id = -1;
    o.candidate_alive = false;
    o.lineage_available = false;
    o.candidate_lineage = {};
    o.lineage_unavailable_reason = {};
  }
  std::string out = "{\"schema_version\":1,\"snapshot_revision\":";
  out += std::to_string(c.snapshot_revision);
  out += ",\"query_kind\":\"campaign_root_context_v1\",\"executable_sha256\":";
  String(out, kExecutableSha256);
  out += ",\"getter_rva\":\"0x289DCC0\",\"parent_frame_bound\":";
  out += Bool(c.parent_frame_bound);
  out += ",\"observation\":{\"available\":"; out += Bool(o.available);
  out += ",\"unavailable_reason\":"; Reason(out, o.unavailable_reason);
  out += ",\"source_fixture\":"; out += Bool(o.source_fixture);
  out += ",\"original_getter_source_bound\":";
  out += Bool(o.original_getter_source_bound);
  out += ",\"before\":"; Core(out, o.before);
  out += ",\"after\":"; Core(out, o.after);
  out += ",\"getter_observed\":"; out += Bool(o.getter_observed);
  out += ",\"candidate_present\":"; out += Bool(o.candidate_present);
  out += ",\"actor_character_id\":" + std::to_string(o.actor_character_id);
  out += ",\"candidate_character_id\":" + std::to_string(o.candidate_character_id);
  out += ",\"candidate_alive\":"; out += Bool(o.candidate_alive);
  out += ",\"identity_and_frame_stable\":";
  out += Bool(o.identity_and_frame_stable);
  out += ",\"lineage_available\":"; out += Bool(o.lineage_available);
  out += ",\"candidate_lineage\":{\"house_id\":";
  out += std::to_string(o.candidate_lineage.house_id);
  out += ",\"dynasty_id\":" + std::to_string(o.candidate_lineage.dynasty_id) + '}';
  out += ",\"lineage_unavailable_reason\":";
  Reason(out, o.lineage_unavailable_reason);
  out += "}}";
  return out;
}
#endif
} // namespace

std::string AppendToCanonicalRoot(std::string payload,
                                 const game::CampaignRootContextV1 &parent,
                                 const Component *component) {
#if defined(XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1)
  if (!component || payload.size() < 2 || payload.front() != '{' ||
      payload.back() != '}') return payload;
  payload.pop_back();
  if (payload.size() > 1) payload += ',';
  payload += "\"player_heir_candidate_v1\":";
  payload += Serialize(*component, parent);
  payload += '}';
#else
  (void)parent;
  (void)component;
#endif
  return payload;
}
} // namespace xar::ck3_12004::campaign_player_heir_candidate_v1
