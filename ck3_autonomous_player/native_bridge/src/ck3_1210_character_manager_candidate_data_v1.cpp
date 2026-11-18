#include "xar_bridge/ck3_1210_character_manager_candidate_data_v1.hpp"
#include <algorithm>
#include <vector>
#include <utility>

namespace xar::ck3_1210 {
namespace {
const char *Boolean(bool value) noexcept { return value ? "true" : "false"; }
bool SamePrefix(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
    a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
    a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
    a.played_character_id == b.played_character_id && a.played_character_alive == b.played_character_alive;
}
// Strict UTF-8: no overlong, surrogate, truncated or above-Unicode sequences.
bool Utf8(std::string_view value) noexcept {
  std::size_t i = 0;
  while (i < value.size()) {
    const auto first = static_cast<unsigned char>(value[i++]);
    if (first < 0x80) continue;
    unsigned remaining = 0; std::uint32_t code = 0, minimum = 0;
    if (first >= 0xC2 && first <= 0xDF) { remaining = 1; code = first & 31; minimum = 0x80; }
    else if (first >= 0xE0 && first <= 0xEF) { remaining = 2; code = first & 15; minimum = 0x800; }
    else if (first >= 0xF0 && first <= 0xF4) { remaining = 3; code = first & 7; minimum = 0x10000; }
    else return false;
    if (remaining > value.size() - i) return false;
    while (remaining-- != 0) {
      const auto next = static_cast<unsigned char>(value[i++]);
      if (next < 0x80 || next > 0xBF) return false;
      code = (code << 6) | (next & 63);
    }
    if (code < minimum || code > 0x10FFFF || (code >= 0xD800 && code <= 0xDFFF)) return false;
  }
  return true;
}
void Quote(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  constexpr char escape = 0x5C, quotation = 0x22;
  out += quotation;
  for (const unsigned char c : value) {
    if (c == 0x22 || c == 0x5C) { out += escape; out += static_cast<char>(c); }
    else if (c < 0x20) {
      out += escape;
      switch (c) {
      case 0x08: out += 'b'; break;
      case 0x0C: out += 'f'; break;
      case 0x0A: out += 'n'; break;
      case 0x0D: out += 'r'; break;
      case 0x09: out += 't'; break;
      default: out += "u00"; out += hex[c >> 4]; out += hex[c & 15]; break;
      }
    } else out += static_cast<char>(c);
  }
  out += quotation;
}
bool Validate(const CharacterManagerObservationV1 &data, std::string_view &reason) {
  reason = "character_manager_candidate_shape_invalid";
  if (data.candidates_complete || data.full_snapshot_available ||
      data.same_frame_ready != data.available || data.manager_members_complete != data.available ||
      data.members.size() > static_cast<std::size_t>(kCharacterManagerMemberLimitV1)) return false;
  if (!data.available) {
    return data.members.empty() && SamePrefix(data.frame, CoreSnapshotPrefix{}) &&
      !data.unavailable_reason.empty() && data.unavailable_reason.size() <= 32768 && Utf8(data.unavailable_reason);
  }
  const auto &frame = data.frame;
  if (!data.unavailable_reason.empty() || !frame.clock.paused || !frame.map_ready ||
      frame.local_player_id < 0 || !frame.has_played_character || frame.played_character_id == -1 ||
      !frame.played_character_alive) return false;
  std::vector<std::uint32_t> ids; ids.reserve(data.members.size());
  for (const auto &member : data.members) {
    if (member.character_id == -1) return false;
    ids.push_back(static_cast<std::uint32_t>(member.character_id));
  }
  std::sort(ids.begin(), ids.end());
  return std::adjacent_find(ids.begin(), ids.end()) == ids.end();
}
void Prefix(std::string &out, const CoreSnapshotPrefix &frame) {
  out += "{\"date_raw\":" + std::to_string(frame.clock.date_raw);
  out += ",\"speed\":" + std::to_string(frame.clock.speed);
  out += ",\"paused\":"; out += Boolean(frame.clock.paused);
  out += ",\"local_player_id\":" + std::to_string(frame.local_player_id);
  out += ",\"map_ready\":"; out += Boolean(frame.map_ready);
  out += ",\"has_played_character\":"; out += Boolean(frame.has_played_character);
  out += ",\"played_character_id\":" + std::to_string(frame.played_character_id);
  out += ",\"played_character_alive\":"; out += Boolean(frame.played_character_alive); out += '}';
}
} // namespace
bool SerializeCharacterManagerCandidateDataV1(const CharacterManagerObservationV1 &data,
    std::string &output, std::string_view &format_reason) noexcept {
  output.clear(); format_reason = {};
  try {
    if (!Validate(data, format_reason)) return false;
    std::string out; out.reserve(1024 + data.members.size() * 96);
    out += R"({"schema":)"; Quote(out, kCharacterManagerCandidateSchemaV1);
    out += R"(,"source_role":)"; Quote(out, kCharacterManagerCandidateRoleV1);
    out += R"(,"game_version":)"; Quote(out, kGameVersion);
    out += R"(,"executable_sha256":)"; Quote(out, kExecutableSha256);
    out += R"(,"adapter_id":)"; Quote(out, kAdapterId);
    out += R"(,"backend":)"; Quote(out, kCharacterManagerCandidateBackendV1);
    out += R"(,"read_only":true,"available":)"; out += Boolean(data.available);
    out += R"(,"same_frame_ready":)"; out += Boolean(data.same_frame_ready);
    out += R"(,"manager_members_complete":)"; out += Boolean(data.manager_members_complete);
    out += R"(,"candidates_complete":false,"full_snapshot_available":false,"frame":)";
    Prefix(out, data.frame); out += R"(,"members":[)";
    bool first = true;
    for (const auto &member : data.members) {
      if (!first) out += ','; first = false;
      out += R"({"character_id":)" + std::to_string(member.character_id);
      out += R"(,"alive":)"; out += Boolean(member.alive);
      out += R"(,"has_living_data":)"; out += Boolean(member.has_living_data); out += '}';
    }
    out += R"(],"unavailable_reason":)"; Quote(out, data.unavailable_reason); out += '}';
    if (out.size() > kCharacterManagerCandidatePacketLimitV1) {
      format_reason = "character_manager_candidate_packet_bound_exceeded"; return false;
    }
    output = std::move(out); format_reason = {}; return true;
  } catch (...) {
    output.clear(); format_reason = "character_manager_candidate_format_exception"; return false;
  }
}
CharacterManagerCandidateDescriptorV1 DescribeCharacterManagerCandidateDataV1(
    const game::AdapterDescriptor &descriptor) noexcept {
  CharacterManagerCandidateDescriptorV1 out{};
  // Strict tuple, consistent with IsCk3_1210Descriptor. Capability strings and
  // version-only matches never select a producer; metadata is not live proof.
  if (descriptor.adapter_id != kAdapterId || descriptor.game_version != kGameVersion ||
      descriptor.executable_sha256 != kExecutableSha256) return out;
  out.state = CharacterManagerCandidateRegistrationV1::registered_unavailable;
  out.reader = &ReadCharacterManagerV1;
  out.formatter = &SerializeCharacterManagerCandidateDataV1;
  out.unavailable_reason = "candidate_data_has_no_owned_main_custody";
  return out;
}
bool FormatCharacterManagerCandidateDataForDescriptorV1(const game::AdapterDescriptor &descriptor,
    const CharacterManagerObservationV1 &data, std::string &output,
    std::string_view &format_reason) noexcept {
  output.clear(); format_reason = {};
  const auto source = DescribeCharacterManagerCandidateDataV1(descriptor);
  if (source.state == CharacterManagerCandidateRegistrationV1::unregistered ||
      source.reader != &ReadCharacterManagerV1 || source.formatter != &SerializeCharacterManagerCandidateDataV1) {
    format_reason = source.unavailable_reason; return false;
  }
  // Only copied values pass to the real formatter. Never invoke source.reader
  // here: this value seam possesses no application-main custody or native lease.
  return source.formatter(data, output, format_reason);
}
std::string SerializeCharacterManagerCandidateDescriptorV1(const game::AdapterDescriptor &descriptor) {
  const auto source = DescribeCharacterManagerCandidateDataV1(descriptor);
  const bool registered = source.state != CharacterManagerCandidateRegistrationV1::unregistered;
  std::string out = R"({"schema":"xar.ck3.character-manager-candidate-descriptor/v1","source_role":)";
  Quote(out, kCharacterManagerCandidateRoleV1);
  out += R"(,"adapter_id":)"; if (registered) Quote(out, kAdapterId); else out += "null";
  out += R"(,"game_version":)"; if (registered) Quote(out, kGameVersion); else out += "null";
  out += R"(,"executable_sha256":)"; if (registered) Quote(out, kExecutableSha256); else out += "null";
  out += R"(,"registration_state":)"; Quote(out, registered ? "registered_unavailable" : "unregistered");
  out += R"(,"reader_bound":)"; out += Boolean(source.reader == &ReadCharacterManagerV1);
  out += R"(,"producer_bound":)"; out += Boolean(source.formatter == &SerializeCharacterManagerCandidateDataV1);
  out += R"(,"public_available":false,"application_main_observed":false,"unavailable_reason":)";
  Quote(out, source.unavailable_reason); out += '}'; return out;
}
} // namespace xar::ck3_1210
