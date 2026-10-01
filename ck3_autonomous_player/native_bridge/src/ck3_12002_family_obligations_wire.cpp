#include "xar_bridge/ck3_12002_family_obligations_wire.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1) && \
    defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
namespace xar::ck3_12002 {
namespace {
void String(std::string &wire, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  wire += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { wire += '\\'; wire += static_cast<char>(c); }
    else if (c < 0x20) {
      wire += "\\u00"; wire += hex[c >> 4]; wire += hex[c & 15];
    } else wire += static_cast<char>(c);
  }
  wire += '"';
}
void Boolean(std::string &wire, bool value) { wire += value ? "true" : "false"; }
void Id(std::string &wire, std::int32_t id) {
  wire += id >= 0 ? std::to_string(id) : "null";
}
template <typename T> void Numbers(std::string &wire, const T &values) {
  wire += '[';
  bool first = true;
  for (const auto value : values) {
    if (!first) wire += ',';
    first = false; wire += std::to_string(value);
  }
  wire += ']';
}
bool BreakAvailable(const FamilyObligationsObservation12002 &o) {
  return o.break_terms.status == FamilyObligationsBreakStatusV1::available ||
      o.break_terms.status == FamilyObligationsBreakStatusV1::no_betrothal;
}
} // namespace

std::string_view FamilyObligationsQueryStatus12002(
    const FamilyObligationsObservation12002 &o) noexcept {
  unsigned requested = 1, available = o.lineage_available ? 1U : 0U;
  if (o.request.break_recipient_character_id > 0) {
    ++requested; if (BreakAvailable(o)) ++available;
  }
  return available == requested ? "available" : available ? "partial" : "unavailable";
}

std::string SerializeFamilyObligationsObservation12002(
    const FamilyObligationsObservation12002 &o) {
  std::string wire = "{\"schema_version\":1,\"kind\":\"ck3_12002_family_obligations_private_v1\","
      "\"game_version\":\"1.20.0.2\",\"executable_sha256\":";
  String(wire, kExecutableSha256);
  wire += ",\"query_status\":"; String(wire, FamilyObligationsQueryStatus12002(o));
  wire += ",\"frame\":{\"snapshot_revision\":" + std::to_string(o.snapshot_revision);
  wire += ",\"date_raw\":" + std::to_string(o.frame.date_raw);
  wire += ",\"played_character_id\":"; Id(wire, o.frame.played_character_id);
  wire += ",\"paused\":"; Boolean(wire, o.frame.paused);
  wire += ",\"map_ready\":"; Boolean(wire, o.frame.map_ready);
  wire += ",\"played_character_alive\":"; Boolean(wire, o.frame.played_character_alive);
  wire += "},\"native_child_house_preview\":{\"status\":";
  String(wire, o.lineage_available ? "available" : "unavailable");
  wire += ",\"reason\":"; String(wire, o.lineage_reason);
  wire += ",\"subject_character_id\":"; Id(wire, o.request.subject_character_id);
  wire += ",\"candidate_character_id\":"; Id(wire, o.request.candidate_character_id);
  wire += ",\"requested_matrilineal_option\":"; Boolean(wire, o.request.request_matrilineal_option);
  if (o.lineage_available) {
    const auto &r = o.lineage;
    wire += ",\"selected_matrilineal_option\":"; Boolean(wire, r.selected_matrilineal_option);
    wire += ",\"effective_matrilineal_if_accepted\":"; Boolean(wire, r.effective_matrilineal_if_accepted);
    wire += ",\"complete_can_send\":"; Boolean(wire, r.complete_can_send);
    wire += ",\"native_selected_parent_character_id\":"; Id(wire, r.native_selected_parent_character_id);
    wire += ",\"house_id\":"; Id(wire, r.native_preview_lineage.house_id);
    wire += ",\"dynasty_id\":"; Id(wire, r.native_preview_lineage.dynasty_id);
  }
  wire += "},\"alliance_obligations\":{\"status\":";
  String(wire, o.request.ally_character_id <= 0 ? "not_requested" : "deferred_by_owner");
  wire += ",\"reason\":";
  String(wire, o.request.ally_character_id <= 0 ? std::string_view{} :
      "war_research_deferred_by_owner");
  wire += ",\"first_character_id\":"; Id(wire, o.frame.played_character_id);
  wire += ",\"second_character_id\":"; Id(wire, o.request.ally_character_id);
  const auto &b = o.break_terms;
  wire += "},\"betrothal_break_terms\":{\"status\":";
  String(wire, o.request.break_recipient_character_id <= 0 ? "not_requested" :
      b.status == FamilyObligationsBreakStatusV1::available ? "available" :
      b.status == FamilyObligationsBreakStatusV1::no_betrothal ? "no_betrothal" : "unavailable");
  wire += ",\"reason\":";
  String(wire, o.request.break_recipient_character_id <= 0 ? std::string_view{} : b.unavailable_reason);
  wire += ",\"actor_character_id\":"; Id(wire, b.actor_character_id);
  wire += ",\"subject_character_id\":"; Id(wire, o.request.subject_character_id);
  wire += ",\"requested_recipient_character_id\":"; Id(wire, o.request.break_recipient_character_id);
  if (o.request.break_recipient_character_id > 0 && BreakAvailable(o)) {
    wire += ",\"betrothed_character_id\":"; Id(wire, b.betrothed_character_id);
    wire += ",\"recipient_character_id\":"; Id(wire, b.recipient_character_id);
    wire += ",\"secondary_actor_character_id\":"; Id(wire, b.secondary_actor_character_id);
    wire += ",\"secondary_recipient_character_id\":"; Id(wire, b.secondary_recipient_character_id);
    wire += ",\"intermediary_character_id\":"; Id(wire, b.intermediary_character_id);
    wire += ",\"definition_ordinal\":"; Id(wire, b.definition_ordinal);
    wire += ",\"definition_stable_hash\":" + std::to_string(b.definition_stable_hash);
    wire += ",\"final_legality_sampled\":"; Boolean(wire, b.final_legality_sampled);
    wire += ",\"complete_can_send\":";
    if (b.final_legality_sampled) Boolean(wire, b.complete_can_send); else wire += "null";
    wire += ",\"native_send_costs_available\":"; Boolean(wire, b.native_send_costs_available);
    wire += ",\"native_send_costs_raw\":";
    if (b.native_send_costs_available) Numbers(wire, b.native_send_costs_raw); else wire += "null";
    const auto &p = b.outcome_resource_penalty;
    wire += ",\"outcome_penalty_available\":"; Boolean(wire, p.resource_penalty_available);
    wire += ",\"outcome_penalty_unavailable_reason\":"; String(wire, p.unavailable_reason);
    wire += ",\"outcome_resource_penalty\":{\"resource_penalty_available\":";
    Boolean(wire, p.resource_penalty_available);
    wire += ",\"effects_complete\":"; Boolean(wire, p.effects_complete);
    wire += ",\"source\":"; String(wire, p.source);
    wire += ",\"reason\":"; String(wire, p.unavailable_reason);
    if (p.resource_penalty_available) {
      wire += ",\"proper_reason\":"; Boolean(wire, p.proper_reason);
      wire += ",\"grand_wedding_promised\":"; Boolean(wire, p.grand_wedding_promised);
      wire += ",\"ordinary_prestige_relevant\":"; Boolean(wire, p.ordinary_prestige_relevant);
      wire += ",\"native_yields_alliance_evaluated\":"; Boolean(wire, p.native_yields_alliance_evaluated);
      wire += ",\"yields_alliance\":"; Boolean(wire, p.yields_alliance);
      wire += ",\"rejected_owner_character_id\":"; Id(wire, p.rejected_owner_character_id);
      wire += ",\"highest_rejected_tier\":" + std::to_string(p.highest_rejected_tier);
      wire += ",\"stock_prestige_effect_raw\":" + std::to_string(p.stock_prestige_effect_raw);
      wire += ",\"stock_prestige_level_effect\":" + std::to_string(p.stock_prestige_level_effect);
    }
    wire += '}';
  }
  wire += "}}";
  return wire;
}

std::string SerializeFamilyObligationsResult12002(
    std::string_view request_id, const FamilyObligationsObservation12002 &o) {
  std::string wire = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  String(wire, request_id);
  wire += ",\"ok\":true,\"result\":";
  auto observation = SerializeFamilyObligationsObservation12002(o);
  observation.pop_back();
  wire += observation;
  wire += ",\"step\":"; String(wire, kFamilyObligationsPrivateStep12002);
  wire += ",\"accepted\":true,\"private_build\":true,\"read_only\":true,\"advertised\":false,";
  wire += "\"snapshot_revision\":" + std::to_string(o.snapshot_revision) + "}}";
  return wire;
}
} // namespace xar::ck3_12002
#endif
