// SOURCE ONLY. No compiler/test/Game invocation by slot41.
// Link with first-package reader/Core and SECOND formatter, C++20.
// --emit-character-manager-candidate-data emits exactly five JSONL records;
// only an owner-run stdout artifact may serve as actual C++ producer evidence.
#include "xar_bridge/ck3_1210_character_manager_candidate_data_v1.hpp"
#include <array>
#include <bit>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <string>

namespace {
using namespace xar::ck3_1210;
constexpr auto kHigh = std::bit_cast<std::int32_t>(0x81000001U);
constexpr auto kNegative = std::bit_cast<std::int32_t>(0xFE000002U);
constexpr auto kMinimum = (std::numeric_limits<std::int32_t>::min)();
void Check(bool value, const char *message) {
  if (!value) { std::cerr << "FAIL " << message << char(0x0A); std::exit(1); }
}
xar::game::AdapterDescriptor Descriptor() {
  return {kAdapterId, kGameVersion, kExecutableSha256, "xar_checkpoint", {}};
}
CharacterManagerObservationV1 Success(std::int32_t actor) {
  CharacterManagerObservationV1 out{};
  out.available = out.same_frame_ready = out.manager_members_complete = true;
  out.frame.clock = {53177016, 5, true}; out.frame.local_player_id = 7;
  out.frame.map_ready = out.frame.has_played_character = out.frame.played_character_alive = true;
  out.frame.played_character_id = actor; out.unavailable_reason = {}; return out;
}
constexpr std::array<std::string_view, 5> kCases{"observed", "empty", "unavailable", "zero", "signed"};
CharacterManagerObservationV1 Case(std::string_view name) {
  if (name == "unavailable") {
    CharacterManagerObservationV1 out{};
    out.unavailable_reason = "character_manager_transcript_changed"; return out;
  }
  auto out = Success(name == "observed" ? kHigh : name == "signed" ? kMinimum : 0);
  if (name == "observed") out.members = {
    {0x02000002, false, true}, {kHigh, true, false}, {0, false, false}, {kMinimum, true, true}};
  else if (name == "zero") out.members = {{0, true, false}};
  else if (name == "signed") out.members = {{kMinimum, false, true}, {kNegative, true, false}, {kHigh, true, true}};
  else Check(name == "empty", "unknown fixture case");
  return out;
}
std::string Formatted(const CharacterManagerObservationV1 &data) {
  std::string out = "stale"; std::string_view reason = "stale";
  Check(FormatCharacterManagerCandidateDataForDescriptorV1(Descriptor(), data, out, reason), "value formatter success");
  Check(!out.empty() && reason.empty(), "successful format clears format reason"); return out;
}
void Reject(const CharacterManagerObservationV1 &data) {
  std::string out = "stale candidate"; std::string_view reason{};
  Check(!SerializeCharacterManagerCandidateDataV1(data, out, reason) && out.empty() && !reason.empty(),
    "malformed input is rejected atomically");
}
void DescriptorCases() {
  auto exact = Descriptor(); const auto bound = DescribeCharacterManagerCandidateDataV1(exact);
  Check(bound.state == CharacterManagerCandidateRegistrationV1::registered_unavailable &&
    bound.reader == &ReadCharacterManagerV1 && bound.formatter == &SerializeCharacterManagerCandidateDataV1 &&
    !bound.public_available && !bound.application_main_observed && !bound.unavailable_reason.empty(),
    "exact tuple binds actual candidate producer without public availability");
  Check(bound.state != CharacterManagerCandidateRegistrationV1::available, "third state cannot be acquired from formatter presence");
  for (int field = 0; field != 3; ++field) {
    auto wrong = exact;
    if (field == 0) wrong.adapter_id = "foreign";
    if (field == 1) wrong.game_version = "1.20.0.4";
    if (field == 2) wrong.executable_sha256 = "foreign";
    const auto rejected = DescribeCharacterManagerCandidateDataV1(wrong);
    Check(rejected.state == CharacterManagerCandidateRegistrationV1::unregistered &&
      rejected.reader == nullptr && rejected.formatter == nullptr && !rejected.public_available &&
      !rejected.application_main_observed, "foreign tuple is unregistered rather than unavailable");
    std::string out = "stale"; std::string_view reason{};
    Check(!FormatCharacterManagerCandidateDataForDescriptorV1(wrong, Case("observed"), out, reason) &&
      out.empty() && !reason.empty(), "foreign descriptor never obtains DATA");
    Check(SerializeCharacterManagerCandidateDescriptorV1(wrong).find("unregistered") != std::string::npos,
      "unregistered descriptor serializes its actual state");
  }
}
void FormatterCases() {
  // Independent expected literal; synthetic software expectation, never an emitted artifact.
  const std::string expected = R"({"schema":"xar.ck3.character-manager-observation1210-candidate/v1","source_role":"internal_candidate_data","game_version":"1.21.0","executable_sha256":"2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC","adapter_id":"ck3-1.21.0-msvc-x64","backend":"ck3-1.21.0-native-headless-main-thread","read_only":true,"available":true,"same_frame_ready":true,"manager_members_complete":true,"candidates_complete":false,"full_snapshot_available":false,"frame":{"date_raw":53177016,"speed":5,"paused":true,"local_player_id":7,"map_ready":true,"has_played_character":true,"played_character_id":-2130706431,"played_character_alive":true},"members":[{"character_id":33554434,"alive":false,"has_living_data":true},{"character_id":-2130706431,"alive":true,"has_living_data":false},{"character_id":0,"alive":false,"has_living_data":false},{"character_id":-2147483648,"alive":true,"has_living_data":true}],"unavailable_reason":""})";
  Check(Formatted(Case("observed")) == expected, "exact formatter literal retains order/dead/full32 and independent bits");
  for (const auto name : kCases) {
    const auto out = Formatted(Case(name));
    Check(out.size() < kCharacterManagerCandidatePacketLimitV1, "fixture packet bounded");
  }
  for (int field = 0; field != 5; ++field) {
    auto bad = Case("observed");
    if (field == 0) bad.available = false;
    if (field == 1) bad.same_frame_ready = false;
    if (field == 2) bad.manager_members_complete = false;
    if (field == 3) bad.candidates_complete = true;
    if (field == 4) bad.full_snapshot_available = true;
    Reject(bad);
  }
  { auto bad = Case("observed"); bad.members[0].character_id = -1; Reject(bad); }
  { auto bad = Case("observed"); bad.members.push_back(bad.members.front()); Reject(bad); }
  { auto bad = Case("observed"); bad.unavailable_reason = "invented"; Reject(bad); }
  { auto bad = Case("unavailable"); bad.unavailable_reason = {}; Reject(bad); }
  { auto bad = Case("unavailable"); bad.members.push_back({0,true,true}); Reject(bad); }
  { auto bad = Case("unavailable"); bad.frame.clock.date_raw = 1; Reject(bad); }
  { auto bad = Case("empty"); bad.frame.played_character_id = -1; Reject(bad); }
  { auto bad = Case("empty"); bad.members.resize(kCharacterManagerMemberLimitV1 + 1); Reject(bad); }
  {
    auto data = Case("unavailable"); std::string reason = "controls ";
    reason += char(0x22); reason += char(0x5C);
    for (int c = 0; c != 32; ++c) reason += char(c);
    reason += std::bit_cast<char>(std::uint8_t{0xE4}); reason += std::bit_cast<char>(std::uint8_t{0xB8}); reason += std::bit_cast<char>(std::uint8_t{0xAD}); // valid UTF-8 U+4E2D
    data.unavailable_reason = reason;
    const auto out = Formatted(data);
    const std::string escaped_prefix(1, char(0x5C));
    Check(out.find(escaped_prefix + "u0000") != std::string::npos &&
      out.find(escaped_prefix + "u0001") != std::string::npos &&
      out.find(escaped_prefix + "n") != std::string::npos,
      "all original controls escaped and valid UTF-8 retained");
    for (unsigned char c : out) Check(c >= 0x20, "no unescaped control byte in JSON");
  }
  for (const auto invalid : {std::string(1, std::bit_cast<char>(std::uint8_t{0x80})),
      std::string{std::bit_cast<char>(std::uint8_t{0xC0}),std::bit_cast<char>(std::uint8_t{0xAF})}, std::string{std::bit_cast<char>(std::uint8_t{0xED}),std::bit_cast<char>(std::uint8_t{0xA0}),std::bit_cast<char>(std::uint8_t{0x80})},
      std::string{std::bit_cast<char>(std::uint8_t{0xF4}),std::bit_cast<char>(std::uint8_t{0x90}),std::bit_cast<char>(std::uint8_t{0x80}),std::bit_cast<char>(std::uint8_t{0x80})}, std::string{std::bit_cast<char>(std::uint8_t{0xE4}),std::bit_cast<char>(std::uint8_t{0xB8})}}) {
    auto bad = Case("unavailable"); bad.unavailable_reason = invalid; Reject(bad);
  }
  {
    auto bad = Case("unavailable"); const std::string oversized(32769, 'x');
    bad.unavailable_reason = oversized; Reject(bad);
  }
}
void Emit() {
  const auto descriptor = SerializeCharacterManagerCandidateDescriptorV1(Descriptor());
  for (const auto name : kCases) {
    std::cout << R"({"case":")" << name << R"(","descriptor":)" << descriptor
      << R"(,"data":)" << Formatted(Case(name)) << '}' << char(0x0A);
  }
}
} // namespace
int main(int argc, char **argv) {
  if (argc == 2 && std::string_view(argv[1]) == "--emit-character-manager-candidate-data") {
    Emit(); return 0;
  }
  if (argc != 1) { std::cerr << "unknown fixture argument" << char(0x0A); return 2; }
  DescriptorCases(); FormatterCases();
  std::cout << "PASS candidate formatter and strict descriptor; software values only" << char(0x0A);
}
