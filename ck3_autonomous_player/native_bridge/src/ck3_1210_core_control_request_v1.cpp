#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include <charconv>
#include <limits>

namespace xar::ck3_1210 {
namespace {
struct Cursor {
  std::string_view text;
  std::size_t at = 0;
  void space() noexcept {
    while (at < text.size() && (text[at] == ' ' || text[at] == char{10} ||
        text[at] == char{13} || text[at] == char{9})) ++at;
  }
  bool take(char value) noexcept {
    space();
    if (at == text.size() || text[at] != value) return false;
    ++at; return true;
  }
  bool string(std::string_view &value) noexcept {
    if (!take('"')) return false;
    const auto start = at;
    while (at < text.size() && text[at] != '"') {
      const unsigned char ch = static_cast<unsigned char>(text[at]);
      if (ch < 0x20 || ch >= 0x7F || ch == 92 || at - start >= 192) return false;
      ++at;
    }
    if (at == text.size()) return false;
    value = text.substr(start, at++ - start); return true;
  }
  template<class T> bool number(T &value) noexcept {
    space(); const auto start = at;
    if (at < text.size() && text[at] == '-') ++at;
    const auto digits = at;
    while (at < text.size() && text[at] >= '0' && text[at] <= '9') ++at;
    if (at == digits || (at - digits > 1 && text[digits] == '0')) return false;
    T parsed{};
    const auto result = std::from_chars(text.data() + start, text.data() + at, parsed);
    if (result.ec != std::errc{} || result.ptr != text.data() + at) return false;
    value = parsed; return true;
  }
  bool boolean(bool &value) noexcept {
    space();
    if (text.substr(at, 4) == "true") { at += 4; value = true; return true; }
    if (text.substr(at, 5) == "false") { at += 5; value = false; return true; }
    return false;
  }
};
bool hash_matches(std::string_view value, std::string_view expected) noexcept {
  if (value.size() != 64) return false;
  for (std::size_t i = 0; i < value.size(); ++i) {
    char ch = value[i]; if (ch >= 'a' && ch <= 'f') ch = static_cast<char>(ch - 'a' + 'A');
    if (ch != expected[i]) return false;
  }
  return true;
}
bool identity(Cursor &c, std::string_view expected, bool hash = false) noexcept {
  std::string_view value;
  return c.string(value) && (hash ? hash_matches(value,expected) : value == expected);
}
bool claim(Cursor &c, CoreSnapshotPrefix &expected,bool exit_claim,ImageBuildV1 build) noexcept {
  if (!c.take('{')) return false;
  std::uint32_t seen = 0; bool first = true;
  while (!c.take('}')) {
    if (!first && !c.take(',')) return false;
    first = false;
    std::string_view key;
    if (!c.string(key) || !c.take(':')) return false;
    std::uint32_t bit = 0; bool valid = false;
    if (key == "schema") { bit=1U<<0; valid=identity(c,exit_claim?kApplicationExitSchemaV1:kCoreControlSchemaV1); }
    else if (key == "game_version") { bit=1U<<1; valid=identity(c,GameVersionForBuild(build)); }
    else if (key == "executable_sha256") { bit=1U<<2; valid=identity(c,ExecutableShaForBuild(build),true); }
    else if (key == "adapter_id") { bit=1U<<3; valid=identity(c,AdapterIdForBuild(build)); }
    else if (key == "backend") { bit=1U<<4; valid=identity(c,BackendForBuild(build)); }
    else if (key == "date_raw") { bit=1U<<5; valid=c.number(expected.clock.date_raw); }
    else if (key == "speed") { bit=1U<<6; valid=c.number(expected.clock.speed); }
    else if (key == "paused") { bit=1U<<7; valid=c.boolean(expected.clock.paused); }
    else if (key == "local_player_id") { bit=1U<<8; valid=c.number(expected.local_player_id); }
    else if (key == "map_ready") { bit=1U<<9; valid=c.boolean(expected.map_ready); }
    else if (key == "has_played_character") { bit=1U<<10; valid=c.boolean(expected.has_played_character); }
    else if (key == "played_character_id") { bit=1U<<11; valid=c.number(expected.played_character_id); }
    else if (key == "played_character_alive") { bit=1U<<12; valid=c.boolean(expected.played_character_alive); }
    if (!valid || !bit || (seen & bit)) return false;
    seen |= bit;
  }
  return seen == ((1U<<13)-1) && expected.clock.speed >= 1 &&
      expected.clock.speed <= 5 && (expected.has_played_character
          ? expected.played_character_id != -1
          : expected.played_character_id == -1 && !expected.played_character_alive);
}
bool request_id(std::string_view value) noexcept {
  if (value.empty() || value.size() > 96) return false;
  for (const char ch : value) if (!((ch >= '0' && ch <= '9') ||
      (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
      ch == '-' || ch == '_' || ch == '.')) return false;
  return true;
}
} // namespace

bool ParseCoreControlRequestV1(std::string_view payload,
    CoreControlRequestV1 &output,ImageBuildV1 build) noexcept {
  output = {};
  if (build==ImageBuildV1::unknown || payload.size() > 16384) return false;
  Cursor c{payload}; CoreControlRequestV1 parsed{};
  std::uint32_t seen = 0; bool first = true; bool exit_claim=false;
  if (!c.take('{')) return false;
  while (!c.take('}')) {
    if (!first && !c.take(',')) return false;
    first = false; std::string_view key, value;
    if (!c.string(key) || !c.take(':')) return false;
    std::uint32_t bit = 0; bool valid = false; std::uint64_t number = 0;
    if (key == "type") { bit=1U<<0; valid=identity(c,"execute_step"); }
    else if (key == "protocol_version") { bit=1U<<1; valid=c.number(number) && number==1; }
    else if (key == "request_id") { bit=1U<<2; valid=c.string(value) && request_id(value); }
    else if (key == "step") { bit=1U<<3; valid=c.string(parsed.step); }
    else if (key == "expected_revision") { bit=1U<<4; valid=c.number(number) && number==0; }
    else if (key == "core_clock_control") { bit=1U<<5; valid=claim(c,parsed.expected,false,build); }
    else if (key == "core_application_exit") { bit=1U<<5; exit_claim=true; valid=claim(c,parsed.expected,true,build); }
    else if (key == "core_control_deadline_unix_ms") {
      bit=1U<<6; valid=c.number(parsed.deadline_unix_ms) && parsed.deadline_unix_ms>0;
    } else if (key == "arguments") { bit=1U<<7; valid=c.take('{') && c.take('}'); }
    if (!valid || !bit || (seen & bit)) return false;
    seen |= bit;
  }
  c.space();
  if (c.at != payload.size() || (seen & 127U) != 127U) return false;
  if (exit_claim != (parsed.step==kApplicationExitStepV1)) return false;
  if (parsed.step == kApplicationExitStepV1) { parsed.operation=CoreControlOperationV1::application_exit; parsed.step=kApplicationExitStepV1; }
  else if (parsed.step == "pause-map") { parsed.operation=CoreControlOperationV1::pause; parsed.step="pause-map"; }
  else if (parsed.step == "resume-map") { parsed.operation=CoreControlOperationV1::resume; parsed.step="resume-map"; }
  else if (parsed.step == "save-checkpoint") { parsed.operation=CoreControlOperationV1::save; parsed.step="save-checkpoint"; }
  else if (parsed.step.size()==11 && parsed.step.starts_with("set-speed-") &&
      parsed.step[10]>='1' && parsed.step[10]<='5') {
    parsed.operation=CoreControlOperationV1::speed;
    parsed.public_speed=parsed.step[10]-'0';
    static constexpr std::string_view steps[]{"set-speed-1","set-speed-2","set-speed-3","set-speed-4","set-speed-5"};
    parsed.step=steps[parsed.public_speed-1];
  } else return false;
  output=parsed; return true;
}
} // namespace xar::ck3_1210
