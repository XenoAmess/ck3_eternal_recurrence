#include "xar_bridge/ck3_12002_sway_mailbox.hpp"
#include <cstring>

namespace xar::ck3_12002 {
namespace {
using namespace bridge;
bool Simple(std::string_view s) noexcept {
  if (s.empty() || s.size() > 64) return false;
  for (const char c : s) if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
      (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.')) return false;
  return true;
}
std::string Quoted(std::string_view s) {
  std::string out = "\"";
  for (const unsigned char c : s) {
    if (c == '\\' || c == '"') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 32) { constexpr char hex[] = "0123456789abcdef"; out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  out += '"'; return out;
}
} // namespace

std::string SerializeActiveSwayRead12002(const ActiveSwayMailboxContext12002 &q) {
  const auto &p = q.terms.precondition;
  if (!q.completed || !q.failure.empty() || q.active.status != ActiveSchemeStateV1PrivateStatus::available ||
      !p.available || !q.terms.final_legality_sampled || p.capture_epoch != q.active.capture_epoch ||
      p.actor_character_id != q.active.played_character_id || p.target_id != q.target) return {};
  std::string out = "{\"schema\":\"active-scheme-sway-private-read-v1\",\"snapshot_revision\":" +
      std::to_string(q.envelope.expected_snapshot_revision);
  out += ",\"capture_epoch\":" + std::to_string(q.active.capture_epoch);
  out += ",\"container_generation\":" + std::to_string(q.active.container_generation);
  out += ",\"date_raw\":" + std::to_string(q.active.date_raw);
  out += ",\"actor_character_id\":" + std::to_string(q.active.played_character_id);
  out += ",\"target_character_id\":" + std::to_string(q.target);
  out += ",\"target_opinion_of_actor\":" + std::to_string(q.opinion);
  out += ",\"active_scheme_count\":" + std::to_string(q.active.row_count);
  out += ",\"matching_sway_active\":"; out += q.matching ? "true" : "false";
  out += ",\"native_complete_can_send\":"; out += q.terms.complete_can_send ? "true" : "false";
  out += ",\"native_legal_now\":"; out += (!q.matching && p.shown_evaluated && p.shown &&
      p.validity_evaluated && p.valid && q.terms.complete_can_send) ? "true" : "false";
  out += ",\"native_failure_classification\":" + Quoted(p.native_reason_key);
  out += ",\"active_sway_instances\":[";
  bool first = true;
  for (std::size_t i = 0; i < q.active.row_count; ++i) {
    const auto &row = q.active.rows[i];
    if (std::strcmp(row.scheme_type_key.data(), "sway") != 0) continue;
    if (row.progress.status != ActiveSchemeStateV1PrivateValueStatus::available ||
        row.progress_goal.status != ActiveSchemeStateV1PrivateValueStatus::available ||
        row.target_kind != ActiveSchemeStateV1PrivateTargetKind::character) return {};
    if (!first) out += ','; first = false;
    out += "{\"scheme_instance_id\":" + std::to_string(row.scheme_instance_id) +
        ",\"scheme_instance_generation\":" + std::to_string(row.scheme_instance_generation) +
        ",\"target_character_id\":" + std::to_string(row.target_id) +
        ",\"progress\":" + std::to_string(row.progress.value) +
        ",\"progress_goal\":" + std::to_string(row.progress_goal.value) +
        ",\"is_exposed\":" + (row.is_exposed ? std::string("true") : std::string("false")) +
        ",\"is_frozen\":" + (row.is_frozen ? std::string("true") : std::string("false")) + "}";
  }
  out += "]}";
  return out;
}
std::string SerializeActiveSwayFormal12002(const ActiveSwayMailboxContext12002 &q) {
  if (!q.completed || !q.failure.empty() || !Simple(q.action_id)) return {};
  if (!q.receipt_mode) {
    const auto &a = q.ack;
    if (a.status != ActiveSchemeSemanticActionV1PrivateAckStatus::submitted_verification_pending ||
        !a.verification_pending || !a.submit_attempted || a.submit_call_count != 1 ||
        a.request_id != q.action_id || a.target_id != q.target) return {};
    return "{\"schema\":\"active-scheme-sway-formal-private-v1\",\"stage\":\"submitted_verification_pending\",\"action_id\":" +
        Quoted(a.request_id) + ",\"actor_character_id\":" + std::to_string(a.actor_character_id) +
        ",\"target_character_id\":" + std::to_string(a.target_id) +
        ",\"pre_capture_epoch\":" + std::to_string(a.pre_capture_epoch) +
        ",\"pre_container_generation\":" + std::to_string(a.pre_container_generation) +
        ",\"pre_date_raw\":" + std::to_string(a.pre_date_raw) +
        ",\"submit_call_count\":1,\"receipt_pending\":true}";
  }
  const auto &r = q.receipt;
  if (r.status != ActiveSchemeSemanticActionV1PrivateReceiptStatus::applied || !r.postcondition_verified ||
      r.request_id != q.action_id || !r.scheme_instance_id) return {};
  return "{\"schema\":\"active-scheme-sway-formal-private-v1\",\"stage\":\"applied\",\"action_id\":" +
      Quoted(r.request_id) + ",\"post_capture_epoch\":" + std::to_string(r.post_capture_epoch) +
      ",\"post_container_generation\":" + std::to_string(r.post_container_generation) +
      ",\"post_date_raw\":" + std::to_string(r.post_date_raw) +
      ",\"scheme_instance_id\":" + std::to_string(r.scheme_instance_id) +
      ",\"scheme_instance_generation\":" + std::to_string(r.scheme_instance_generation) +
      ",\"postcondition_verified\":true}";
}

std::string SerializeActiveSwayEnvelope12002(const ActiveSwayMailboxContext12002 &q,
    std::string_view step, std::string_view request_id) {
  const auto native = q.formal ? SerializeActiveSwayFormal12002(q) : SerializeActiveSwayRead12002(q);
  if (native.empty()) return {};
  return "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":" + Quoted(request_id) +
      ",\"ok\":true,\"result\":{\"step\":" + Quoted(step) + ",\"accepted\":true,\"status\":" +
      Quoted(!q.formal ? "available" : q.receipt_mode ? "applied" : "submitted_verification_pending") +
      ",\"private_build\":true," + (!q.formal ? std::string("\"read_only\":true,") : std::string{}) +
      "\"advertised\":false,\"" + (q.formal ? std::string("active_scheme_sway_formal") : std::string("active_scheme_sway")) +
      "\":" + native + ",\"backend_id\":\"native-headless\"}}";
}

} // namespace xar::ck3_12002
