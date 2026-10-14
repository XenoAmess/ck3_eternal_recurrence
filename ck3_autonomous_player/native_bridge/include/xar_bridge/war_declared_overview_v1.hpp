#pragma once
#include "xar_bridge/war_results_dismiss_adapter_v1.hpp"

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include <charconv>

namespace xar::ck3_11906 {

inline constexpr std::string_view kWarDeclaredOverviewQueryV1Step =
    "query-war-declared-overview-v1";
inline constexpr std::string_view kWarDeclaredOverviewCloseV1Step =
    "close-war-declared-overview-v1";
inline constexpr std::string_view kWarDeclaredOverviewQueryV1Capability =
    "game.command.query-war-declared-overview-v1";
inline constexpr std::string_view kWarDeclaredOverviewCloseV1Capability =
    "game.command.close-war-declared-overview-v1";
inline constexpr std::string_view kWarDeclaredOverviewWindowNameV1 =
    "war_declared_overview";
inline constexpr std::string_view kWarResultsQueryV1Step =
    "query-war-results-window-v1";
inline constexpr std::string_view kWarResultsCloseV1Step =
    "close-war-results-window-v1";
inline constexpr std::string_view kWarResultsQueryV1Capability =
    "game.command.query-war-results-window-v1";
inline constexpr std::string_view kWarResultsCloseV1Capability =
    "game.command.close-war-results-window-v1";
inline constexpr std::string_view kWarResultsWindowNameV1 = "war_results";

enum class WarDeclaredOverviewOperationV1 : std::uint8_t { query, close };

// Internal revision-object syntax. The production entry consumes the complete
// transport frame through ParseWarDeclaredRequestV1 below, never a projection.
inline bool ParseWarDeclaredExpectedRevisionV1(
    std::string_view text, std::uint64_t &revision) noexcept {
  revision = 0;
  std::size_t at = 0;
  const auto whitespace = [&]() noexcept {
    while (at < text.size() && (text[at]==' ' || text[at]=='\t' ||
           text[at]=='\r' || text[at]=='\n')) ++at;
  };
  whitespace();
  if (at == text.size() || text[at++] != '{') return false;
  whitespace();
  constexpr std::string_view key = "\"expected_revision\"";
  if (text.substr(at,key.size()) != key) return false;
  at += key.size();
  whitespace();
  if (at == text.size() || text[at++] != ':') return false;
  whitespace();
  const auto begin = at;
  while (at < text.size() && text[at] >= '0' && text[at] <= '9') ++at;
  if (at == begin || (at-begin > 1 && text[begin]=='0')) return false;
  std::uint64_t parsed_revision = 0;
  const auto parsed = std::from_chars(text.data()+begin,text.data()+at,parsed_revision);
  if (parsed.ec != std::errc{} || parsed.ptr != text.data()+at) return false;
  whitespace();
  if (at == text.size() || text[at++] != '}') return false;
  whitespace();
  if (at != text.size()) return false;
  revision = parsed_revision;
  return true;
}

// Actual incoming wire is the complete execute_step frame, not a nested
// payload. All five keys are mandatory, unique and closed; order is arbitrary.
// The qualified .4 sender uses protocol 1 and compact unescaped control strings.
inline bool ParseWarDeclaredRequestV1(std::string_view text,
    std::string_view expected_request_id, std::string_view expected_step,
    std::uint64_t &revision) noexcept {
  revision = 0;
  if (text.size() > 4096 || expected_request_id.empty() ||
      expected_request_id.size() > 128 ||
       (expected_step != kWarDeclaredOverviewQueryV1Step &&
        expected_step != kWarDeclaredOverviewCloseV1Step &&
        expected_step != kWarResultsQueryV1Step &&
        expected_step != kWarResultsCloseV1Step)) return false;
  std::size_t at = 0;
  const auto whitespace = [&]() noexcept {
    while (at < text.size() && (text[at]==' ' || text[at]=='\t' ||
           text[at]=='\r' || text[at]=='\n')) ++at;
  };
  const auto control_string = [&](std::string_view &value) noexcept {
    whitespace();
    if (at == text.size() || text[at++] != '"') return false;
    const auto begin = at;
    while (at < text.size() && text[at] != '"') {
      const auto byte = static_cast<unsigned char>(text[at]);
      if (byte < 0x20 || byte > 0x7e || byte == '\\' || at-begin >= 128)
        return false;
      ++at;
    }
    if (at == text.size()) return false;
    value = text.substr(begin,at-begin);
    ++at;
    return true;
  };
  const auto unsigned_number = [&](std::uint64_t &value) noexcept {
    whitespace();
    const auto begin = at;
    while (at < text.size() && text[at] >= '0' && text[at] <= '9') ++at;
    if (at == begin || (at-begin > 1 && text[begin]=='0')) return false;
    const auto parsed = std::from_chars(text.data()+begin,text.data()+at,value);
    return parsed.ec == std::errc{} && parsed.ptr == text.data()+at;
  };
  whitespace();
  if (at == text.size() || text[at++] != '{') return false;
  std::uint32_t seen = 0;
  std::uint64_t parsed_revision = 0;
  for (;;) {
    std::string_view key, value;
    if (!control_string(key)) return false;
    whitespace();
    if (at == text.size() || text[at++] != ':') return false;
    const std::uint32_t bit = key=="type" ? 1U : key=="protocol_version" ? 2U :
        key=="request_id" ? 4U : key=="step" ? 8U : key=="expected_revision" ? 16U : 0U;
    if (!bit || (seen & bit)) return false;
    seen |= bit;
    if (bit == 2U) {
      std::uint64_t protocol = 0;
      if (!unsigned_number(protocol) || protocol != 1) return false;
    } else if (bit == 16U) {
      if (!unsigned_number(parsed_revision)) return false;
    } else {
      if (!control_string(value) ||
          (bit == 1U && value != "execute_step") ||
          (bit == 4U && value != expected_request_id) ||
          (bit == 8U && value != expected_step)) return false;
    }
    whitespace();
    if (at == text.size()) return false;
    if (text[at] == '}') { ++at; break; }
    if (text[at++] != ',') return false;
  }
  whitespace();
  if (seen != 31U || at != text.size()) return false;
  revision = parsed_revision;
  return true;
}

// Independent DTO: existing navigation requests, results and enums stay intact.
struct WarDeclaredOverviewResultV1 {
  WarDeclaredOverviewOperationV1 operation = WarDeclaredOverviewOperationV1::query;
  bool war_results = false;
  bool available = false;
  bool accepted = false;
  bool root_observed = false;
  bool window_present = false;
  bool effective_visible = false;
  bool dispatch_attempted = false;
  bool dispatch_invoked = false;
  bool native_handled = false;
  bool post_observed = false;
  bool post_window_present = false;
  bool post_effective_visible = false;
  bool scope_unchanged = false;
  bool closure_verified = false;
  bool application_owner_thread_verified = false;
  WarResultsDismissTraceV1 dismiss_trace{};
  std::string button_name;
  std::string request_id;
  std::string root_observation_source;
  std::string post_observation_source;
  std::string status = "unavailable";
  std::string unavailable_reason;
  decltype(game::Snapshot{}.played_character_id) played_character_id = -1;
  decltype(game::Snapshot{}.date_raw) date_raw = 0;
  bool paused = false;
  std::uint64_t native_revision = 0;
  std::uint64_t connection_generation = 0;
  std::uint64_t pump_epoch = 0;
  std::uint32_t thread_id = 0;
  std::uint64_t ticket_sequence = 0;
};

// Native-owned only. No pointer, window name or child path comes from payload.
// The bridge keeps this context alive until its ticket is terminal/reclaimed.
struct WarDeclaredOverviewMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  const game::GameAdapter *game = nullptr;
  game::Snapshot expected_snapshot{};
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  ZhongguoScoreboardActionDispatchEnvironmentV1 dispatch_environment{};
  WarDeclaredOverviewOperationV1 operation = WarDeclaredOverviewOperationV1::query;
  bool war_results = false;
  std::string request_id;
  std::uint64_t native_revision = 0;
  std::uint64_t connection_generation = 0;
  WarDeclaredOverviewResultV1 result{};
};

std::string_view PrepareWarDeclaredOverviewMailboxV1(
    const game::GameAdapter &game, const game::Snapshot *previous_snapshot,
    std::string_view request_id, std::string_view payload, std::string_view step,
    std::uint64_t state_revision, std::uint64_t connection_generation,
    std::uintptr_t module_base, MainThreadQueryMailboxV1 &mailbox,
    WarDeclaredOverviewMailboxContextV1 &query) noexcept;

bool ExecuteWarDeclaredOverviewMailboxV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept;

std::string SerializeWarDeclaredOverviewResultV1(
    const WarDeclaredOverviewResultV1 &result);

std::string WarDeclaredOverviewCommandResultFrameV1(
    std::string_view request_id, const WarDeclaredOverviewResultV1 &result);

} // namespace xar::ck3_11906
