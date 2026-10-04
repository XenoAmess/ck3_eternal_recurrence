#include "xar_bridge/ck3_12003_player_mercenary_context.hpp"

#include <optional>
#include <sstream>

namespace xar::ck3_12003::mercenary {
namespace {
void Quote(std::ostream &out, std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char value : text) {
    if (value == '"' || value == '\\') out << '\\' << static_cast<char>(value);
    else if (value < 0x20)
      out << "\\u00" << hex[value >> 4] << hex[value & 15];
    else out << static_cast<char>(value);
  }
  out << '"';
}

template <typename T>
void Optional(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}

void Location(std::ostream &out,
    const xar::ck3_12003::MercenaryPositionObservationV1 &location) {
  out << "{\"company_home_title_id\":";
  Optional(out, location.company_home_title_id);
  out << ",\"company_home_province_id\":";
  Optional(out, location.company_home_province_id);
  out << ",\"company_home_ready\":" << location.company_home_ready
      << ",\"company_home_failure\":";
  Quote(out, location.company_home_failure);
  out << ",\"company_home_source\":";
  Quote(out, location.company_home_source);
  out << ",\"hire_auto_raise_province_id\":";
  Optional(out, location.hire_auto_raise_province_id);
  out << ",\"actor_active_war_count\":";
  Optional(out, location.actor_active_war_count);
  out << ",\"hire_auto_raise_attempted_in_active_war\":";
  Optional(out, location.hire_auto_raise_attempted_in_active_war);
  out << ",\"hire_auto_raise_position_ready\":"
      << location.hire_auto_raise_position_ready
      << ",\"hire_auto_raise_position_failure\":";
  Quote(out, location.hire_auto_raise_position_failure);
  out << ",\"hire_auto_raise_position_source\":";
  Quote(out, location.hire_auto_raise_position_source);
  out << '}';
}

void WriteRow(std::ostream &out, const Row &row) {
  const auto &candidate = row.candidate;
  out << "{\"company_id\":" << candidate.company_id
      << ",\"manager_slot_index\":" << candidate.manager_slot_index
      << ",\"employer_id\":";
  Optional(out, candidate.employer_id);
  out << ",\"troop_strength\":{\"available\":"
      << candidate.troop_strength_available << ",\"current_soldiers\":";
  Optional(out, candidate.current_soldiers);
  out << ",\"unavailable_reason\":";
  if (candidate.troop_strength_available) out << "null";
  else Quote(out, candidate.troop_strength_unavailable_reason);
  out << "},\"final_terms\":"
      << SerializeMercenaryFinalTerms12003(row.final_terms)
      << ",\"composition_v1\":"
      << SerializeMercenaryComposition12003(row.composition)
      << ",\"location\":";
  Location(out, row.location);
  out << '}';
}
} // namespace

std::string SerializePlayerMercenaryContext12003(const Context &context) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":";
  Quote(out, kPlayerMercenaryContextSchema12003);
  out << ",\"read_only\":true,\"game_version\":\"1.20.0.3\","
      << "\"executable_sha256\":";
  Quote(out, kPlayerMercenaryContextExecutableSha256);
  out << ",\"actor_character_id\":" << context.actor_character_id
      << ",\"date_raw\":" << context.date_raw
      << ",\"capture_epoch\":" << context.capture_epoch
      << ",\"native_hire_mode\":" << kNormalHireMode
      << ",\"available\":" << context.available
      << ",\"unavailable_reason\":";
  if (context.available) out << "null";
  else Quote(out, context.unavailable_reason);
  out << ",\"rows\":[";
  for (std::size_t index = 0; index < context.rows.size(); ++index) {
    if (index != 0) out << ',';
    WriteRow(out, context.rows[index]);
  }
  out << "]}";
  return out.str();
}

std::string SerializePlayerMercenaryContextResultV1(const Context &context,
    std::string_view request_id, std::uint64_t query_sequence,
    std::uint64_t snapshot_revision) {
  std::ostringstream out;
  out << "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  Quote(out, request_id);
  out << ",\"ok\":true,\"result\":{\"step\":";
  Quote(out, kPlayerMercenaryContextStep12003);
  out << ",\"accepted\":true,\"status\":\"completed\",\"read_only\":true,"
      << "\"game_version\":\"1.20.0.3\",\"executable_sha256\":";
  Quote(out, kPlayerMercenaryContextExecutableSha256);
  out << ",\"query_sequence\":" << query_sequence
      << ",\"snapshot_revision\":" << snapshot_revision
      << ",\"date_raw\":" << context.date_raw
      << ",\"player_mercenary_context\":"
      << SerializePlayerMercenaryContext12003(context) << "}}";
  return out.str();
}

} // namespace xar::ck3_12003::mercenary
