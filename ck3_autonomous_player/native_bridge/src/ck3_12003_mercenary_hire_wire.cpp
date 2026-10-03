#include "xar_bridge/ck3_12003_mercenary_hire_wire.hpp"

#include "xar_bridge/ck3_12003_mercenary_hire_action.hpp"

#include <charconv>
#include <sstream>

namespace xar::ck3_12003 {
namespace {
bool IsSpace(char value) noexcept {
  return value == ' ' || value == '\t' || value == '\r' || value == '\n';
}

// Match the compact unsigned-field grammar of the native revision protocol.
bool UnsignedField(std::string_view payload, std::string_view key,
    std::uint64_t &output) noexcept {
  const auto at = payload.find(key);
  if (at == std::string_view::npos ||
      payload.find(key, at + key.size()) != std::string_view::npos) return false;
  auto begin = at + key.size();
  while (begin < payload.size() && IsSpace(payload[begin])) ++begin;
  auto end = begin;
  while (end < payload.size() && payload[end] >= '0' && payload[end] <= '9')
    ++end;
  auto delimiter = end;
  while (delimiter < payload.size() && IsSpace(payload[delimiter])) ++delimiter;
  if (begin == end || (payload[begin] == '0' && end - begin != 1U) ||
      (delimiter < payload.size() && payload[delimiter] != ',' &&
       payload[delimiter] != '}')) return false;
  std::uint64_t parsed = 0;
  const auto result = std::from_chars(
      payload.data() + begin, payload.data() + end, parsed);
  if (result.ec != std::errc{} || result.ptr != payload.data() + end)
    return false;
  output = parsed;
  return true;
}

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

std::string_view NativeStatus(mercenary::HireActionStatus status) noexcept {
  switch (status) {
  case mercenary::HireActionStatus::unavailable: return "unavailable";
  case mercenary::HireActionStatus::rejected: return "rejected";
  case mercenary::HireActionStatus::submitted: return "submitted";
  case mercenary::HireActionStatus::already_hired: return "already_hired";
  }
  return "unavailable";
}

std::string_view EnvelopeStatus(mercenary::HireActionStatus status) noexcept {
  return status == mercenary::HireActionStatus::submitted
      ? std::string_view("submitted_verification_pending") : NativeStatus(status);
}

void WriteNullableActor(std::ostream &out, std::int32_t actor_id) {
  if (actor_id < 0) out << "null";
  else out << actor_id;
}

void WriteNullableCompany(std::ostream &out, std::uint32_t company_id) {
  if (company_id == UINT32_MAX) out << "null";
  else out << company_id;
}

void WriteAction(std::ostream &out,
    const mercenary::HireActionResult &action, std::uint64_t snapshot_revision,
    std::int32_t date_raw) {
  out << "{\"schema\":";
  Quote(out, kMercenaryHireResultSchemaV1);
  out << ",\"status\":";
  Quote(out, NativeStatus(action.status));
  out << ",\"snapshot_revision\":" << snapshot_revision
      << ",\"date_raw\":" << date_raw
      << ",\"actor_character_id\":";
  WriteNullableActor(out, action.actor_character_id);
  out << ",\"company_id\":";
  WriteNullableCompany(out, action.company_id);
  out << ",\"company_resolved\":" << action.company_resolved
      << ",\"prior_employer_character_id\":";
  if (action.prior_employer_character_id)
    out << *action.prior_employer_character_id;
  else out << "null";
  out << ",\"native_hire_mode\":" << mercenary::kNormalHireMode
      << ",\"final_terms\":"
      << mercenary::SerializeMercenaryFinalTerms12003(action.final_terms)
      << ",\"native_command_validation_observable\":"
      << action.native_command_validation_observable
      << ",\"native_command_valid\":";
  if (action.native_command_validation_observable)
    out << action.native_command_valid;
  else out << "null";
  out << ",\"command_submitted\":" << action.command_submitted
      << ",\"verification_pending\":" << action.verification_pending
      << ",\"after_state_observed\":false,\"unavailable_reason\":";
  if (action.unavailable_reason.empty()) out << "null";
  else Quote(out, action.unavailable_reason);
  out << '}';
}
} // namespace

bool ParseMercenaryHireRequestV1(std::string_view step,
    std::string_view payload, MercenaryHireRequestV1 &request) noexcept {
  request = {};
  std::uint64_t company_id = 0;
  std::uint64_t expected_revision = 0;
  if (step != kMercenaryHireStepV1 ||
      !UnsignedField(payload, "\"company_id\":", company_id) ||
      company_id >= static_cast<std::uint64_t>(UINT32_MAX) ||
      !UnsignedField(payload, "\"expected_revision\":", expected_revision) ||
      expected_revision == 0) return false;
  request.company_id = static_cast<std::uint32_t>(company_id);
  request.expected_revision = expected_revision;
  return true;
}

std::string SerializeMercenaryHireResultV1(
    const mercenary::HireActionResult &action, std::string_view request_id,
    std::uint64_t command_sequence, std::uint64_t snapshot_revision,
    std::int32_t date_raw) {
  const bool accepted = action.status == mercenary::HireActionStatus::submitted ||
      action.status == mercenary::HireActionStatus::already_hired;
  std::ostringstream out;
  out << std::boolalpha
      << "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  Quote(out, request_id);
  out << ",\"ok\":true,\"result\":{\"step\":";
  Quote(out, kMercenaryHireStepV1);
  out << ",\"accepted\":" << accepted << ",\"status\":";
  Quote(out, EnvelopeStatus(action.status));
  out << ",\"read_only\":false,\"game_version\":\"1.20.0.3\","
      << "\"executable_sha256\":";
  Quote(out, mercenary::kHireActionExecutableSha256);
  out << ",\"command_sequence\":" << command_sequence
      << ",\"snapshot_revision\":" << snapshot_revision
      << ",\"date_raw\":" << date_raw << ",\"mercenary_hire\":";
  WriteAction(out, action, snapshot_revision, date_raw);
  out << "}}";
  return out.str();
}

} // namespace xar::ck3_12003
