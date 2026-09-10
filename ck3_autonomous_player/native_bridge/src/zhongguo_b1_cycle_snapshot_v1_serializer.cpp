#include "xar_bridge/zhongguo_b1_cycle_snapshot_v1.hpp"

#include <array>
#include <charconv>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

void String(std::string &out, std::string_view value) {
  out.push_back('"');
  for (unsigned char c : value) {
    if (c == '"' || c == '\\') {
      out.push_back('\\');
      out.push_back(static_cast<char>(c));
    } else if (c < 0x20) {
      constexpr char hex[] = "0123456789ABCDEF";
      out += "\\u00";
      out.push_back(hex[(c >> 4) & 15]);
      out.push_back(hex[c & 15]);
    } else {
      out.push_back(static_cast<char>(c));
    }
  }
  out.push_back('"');
}

template <typename Value> bool Number(std::string &out, Value value) {
  std::array<char, 32> buffer{};
  const auto converted =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (converted.ec != std::errc{}) return false;
  out.append(buffer.data(), converted.ptr);
  return true;
}

bool FieldReason(std::string_view reason) {
  return reason == "cycle_unavailable" || reason == "variable_absent" ||
         reason == "value_type_mismatch" ||
         reason == "value_out_of_range" ||
         reason == "lifecycle_not_reached";
}

template <typename Value, typename Writer>
bool Typed(std::string &out, const game::ZhongguoTypedValueV1<Value> &field,
           Writer writer) {
  if (field.available != field.value.has_value() ||
      (field.available && !field.unavailable_reason.empty()) ||
      (!field.available && !FieldReason(field.unavailable_reason)))
    return false;
  out += field.available
             ? "{\"status\":\"available\",\"value\":"
             : "{\"status\":\"unavailable\",\"value\":null";
  if (field.available && !writer(out, *field.value)) return false;
  out += ",\"unavailable_reason\":";
  if (field.available)
    out += "null";
  else
    String(out, field.unavailable_reason);
  out.push_back('}');
  return true;
}

bool Integer(std::string &out, const game::ZhongguoTypedIntegerV1 &field) {
  return Typed(out, field,
               [](std::string &target, std::int64_t value) {
                 return Number(target, value);
               });
}

bool Boolean(std::string &out, const game::ZhongguoTypedBooleanV1 &field) {
  return Typed(out, field, [](std::string &target, bool value) {
    target += value ? "true" : "false";
    return true;
  });
}

template <typename Append>
bool Named(std::string &out, std::string_view name, Append append) {
  String(out, name);
  out.push_back(':');
  return append();
}

bool TopReason(std::string_view reason) {
  return reason == "unsupported_build" ||
         reason == "requires_application_main" ||
         reason == "requires_paused" || reason == "map_not_ready" ||
         reason == "cycle_not_found" || reason == "cycle_inconsistent" ||
         reason == "variable_identifier_unavailable" ||
         reason == "variable_context_unavailable" ||
         reason == "state_changed" || reason == "internal_error";
}

bool Nonce(std::string_view value) {
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t i = 0; i < value.size(); ++i) {
    const char c = value[i];
    const bool a = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
                   (c >= '0' && c <= '9');
    if ((!a && c != '.' && c != '_' && c != ':' && c != '-') ||
        (i == 0 && !a))
      return false;
  }
  return true;
}

} // namespace

std::string SerializeZhongguoB1CycleSnapshotV1(
    const game::ZhongguoB1CycleSnapshotV1 &s) {
  const bool available =
      s.status == game::ZhongguoB1CycleSnapshotStatusV1::available;
  if (s.case_kind != kZhongguoB1CycleSnapshotV1CaseKind ||
      !Nonce(s.request_nonce) || s.snapshot_revision == 0 || !s.paused ||
      s.player_character_id <= 0 ||
      s.manager_character_id != s.player_character_id ||
      (available ? !s.unavailable_reason.empty()
                 : !TopReason(s.unavailable_reason)))
    return {};
  std::string out = "{\"schema_version\":1,\"status\":\"";
  out += available ? "available" : "unavailable";
  out += "\",\"case_kind\":";
  String(out, s.case_kind);
  out += ",\"request_nonce\":";
  String(out, s.request_nonce);
  out += ",\"snapshot_revision\":";
  if (!Number(out, s.snapshot_revision)) return {};
  out += ",\"date_raw\":";
  if (!Number(out, s.date_raw)) return {};
  out += ",\"paused\":true,\"player_character_id\":";
  if (!Number(out, s.player_character_id)) return {};
  out += ",\"manager_character_id\":";
  if (!Number(out, s.manager_character_id)) return {};

#define XAR_GROUP_BEGIN(name) out += ",\"" name "\":{"
#define XAR_INT(name, field)                                                   \
  if (!Named(out, name, [&] { return Integer(out, field); })) return {};       \
  out.push_back(',')
#define XAR_BOOL(name, field)                                                  \
  if (!Named(out, name, [&] { return Boolean(out, field); })) return {};       \
  out.push_back(',')
#define XAR_GROUP_END()                                                        \
  out.back() = '}'
  XAR_GROUP_BEGIN("cycle");
  XAR_INT("cycle_serial", s.cycle.cycle_serial);
  XAR_INT("case_serial", s.cycle.case_serial);
  XAR_INT("state", s.cycle.state);
  XAR_INT("open_year", s.cycle.open_year);
  XAR_INT("runtime_schema", s.cycle.runtime_schema);
  XAR_BOOL("active", s.cycle.active);
  XAR_GROUP_END();
  XAR_GROUP_BEGIN("roster");
  XAR_INT("subject_count", s.roster.subject_count);
  XAR_INT("before_prune_count", s.roster.before_prune_count);
  XAR_INT("pruned_count", s.roster.pruned_count);
  XAR_INT("amendment_count", s.roster.amendment_count);
  XAR_INT("audit_version", s.roster.audit_version);
  XAR_BOOL("reopen_required", s.roster.reopen_required);
  XAR_GROUP_END();
  XAR_GROUP_BEGIN("processing");
  XAR_INT("count", s.processing.count);
  XAR_INT("agenda_count", s.processing.agenda_count);
  XAR_INT("local_candidate_count", s.processing.local_candidate_count);
  XAR_INT("pre_calibration_valid_count",
          s.processing.pre_calibration_valid_count);
  XAR_GROUP_END();
  XAR_GROUP_BEGIN("quota");
  XAR_INT("rebuild_generation", s.quota.rebuild_generation);
  XAR_INT("built_case_serial", s.quota.built_case_serial);
  XAR_INT("book_version", s.quota.book_version);
  XAR_INT("target_top", s.quota.target_top);
  XAR_INT("target_middle", s.quota.target_middle);
  XAR_INT("target_bottom", s.quota.target_bottom);
  XAR_INT("recount_top", s.quota.recount_top);
  XAR_INT("recount_middle", s.quota.recount_middle);
  XAR_INT("recount_bottom", s.quota.recount_bottom);
  XAR_INT("pre_calibration_expected_count",
          s.quota.pre_calibration_expected_count);
  XAR_BOOL("pre_calibration_mismatch", s.quota.pre_calibration_mismatch);
  XAR_BOOL("pool_membership", s.quota.pool_membership);
  XAR_GROUP_END();
  XAR_GROUP_BEGIN("closure");
  XAR_BOOL("calibration_finalized", s.closure.calibration_finalized);
  XAR_INT("state", s.closure.state);
  XAR_BOOL("rewards_issued", s.closure.rewards_issued);
  XAR_BOOL("publication_blocked", s.closure.publication_blocked);
  XAR_GROUP_END();
  XAR_GROUP_BEGIN("pending");
  XAR_INT("open_count", s.pending.open_count);
  XAR_INT("slot_used", s.pending.slot_used);
  XAR_INT("reward_expected_count", s.pending.reward_expected_count);
  XAR_INT("rewards_paid_count", s.pending.rewards_paid_count);
  XAR_BOOL("rewards_committed", s.pending.rewards_committed);
  XAR_INT("watchdog_cancelled_count", s.pending.watchdog_cancelled_count);
  XAR_INT("watchdog_orphan_count", s.pending.watchdog_orphan_count);
  XAR_GROUP_END();
#undef XAR_GROUP_BEGIN
#undef XAR_INT
#undef XAR_BOOL
#undef XAR_GROUP_END

  out += ",\"readiness\":{";
#define XAR_READY(name, field) out += "\"" name "\":"; out += field ? "true," : "false,"
  XAR_READY("manager_binding_ready", s.readiness.manager_binding_ready);
  XAR_READY("cycle_identity_ready", s.readiness.cycle_identity_ready);
  XAR_READY("roster_ready", s.readiness.roster_ready);
  XAR_READY("processing_ready", s.readiness.processing_ready);
  XAR_READY("quota_ready", s.readiness.quota_ready);
  XAR_READY("closure_ready", s.readiness.closure_ready);
  XAR_READY("pending_ready", s.readiness.pending_ready);
  XAR_READY("same_frame_ready", s.readiness.same_frame_ready);
  XAR_READY("ready", s.readiness.ready);
#undef XAR_READY
  out.back() = '}';
  out += ",\"unavailable_reason\":";
  if (available) out += "null"; else String(out, s.unavailable_reason);
  out += ",\"provenance\":{"
         "\"game_version\":\"1.19.0.6\"," 
         "\"executable_sha256\":\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\"," 
         "\"backend_id\":\"ck3-1.19.0.6-native-zhongguo-b1-cycle-snapshot-v1\"," 
         "\"consumer_id\":\"xar-autoplayer-zhongguo-b1-cycle-snapshot-v1\"," 
         "\"allowlist_id\":\"zg361-b1-cycle-manager-v1\"," 
         "\"variable_context_for_scope_rva\":\"0x3329A40\"," 
         "\"variable_identifier_table_rva\":\"0x3B971A0\"," 
         "\"variable_identifier_lookup_rva\":\"0x3B97020\"," 
         "\"variable_identifier_name_rva\":\"0x3B97090\"," 
         "\"character_storage_slot_rva\":\"0x570C130\"}}";
  return out;
}

} // namespace xar::ck3_11906
