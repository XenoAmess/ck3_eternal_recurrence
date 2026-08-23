#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>

#include <array>
#include <atomic>
#include <charconv>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace {

static_assert(sizeof(void *) == 8, "the CK3 bridge is x64-only");

constexpr wchar_t kPipeEnvironment[] = L"XAR_CK3_BRIDGE_PIPE";
constexpr std::size_t kPipeNameCapacity = 256;
constexpr DWORD kHeartbeatIntervalMs = 250;

wchar_t g_pipe_name[kPipeNameCapacity]{};
HANDLE g_stop_event = nullptr;
HANDLE g_worker_thread = nullptr;
std::atomic<long> g_lifecycle{0}; // 0 stopped, 1 starting/running

bool IsPipeName(const wchar_t *value, DWORD length) noexcept {
  constexpr wchar_t prefix[] = L"\\\\.\\pipe\\";
  constexpr DWORD prefix_length =
      static_cast<DWORD>((sizeof(prefix) / sizeof(prefix[0])) - 1U);
  if (length <= prefix_length || length >= kPipeNameCapacity) {
    return false;
  }
  for (DWORD index = 0; index < prefix_length; ++index) {
    if (value[index] != prefix[index]) {
      return false;
    }
  }
  return true;
}

std::string Number(std::uint64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec != std::errc{}) {
    return "0";
  }
  return std::string(buffer.data(), result.ptr);
}

std::string SignedNumber(std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec != std::errc{}) {
    return "0";
  }
  return std::string(buffer.data(), result.ptr);
}

void AppendJsonString(std::string &result, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  result += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      result += '\\';
      result += static_cast<char>(character);
    } else if (character < 0x20U) {
      result += "\\u00";
      result += hex[(character >> 4U) & 0x0FU];
      result += hex[character & 0x0FU];
    } else {
      result += static_cast<char>(character);
    }
  }
  result += '"';
}

std::string IdentityFrame() {
  const auto &descriptor = xar::game::PreferredAdapterDescriptor();
  std::string result =
      "{\"bridge\":\"xar_ck3_bridge\",\"bridge_version\":\"";
  result += XAR_BRIDGE_VERSION;
  result += "\",\"protocol_version\":1,\"architecture\":"
            "\"x86_64-windows-msvc\",\"expected_ck3_version\":";
  AppendJsonString(result, descriptor.game_version);
  result += ",\"expected_ck3_sha256\":";
  AppendJsonString(result, descriptor.executable_sha256);
  result += ",\"game_adapter_id\":";
  AppendJsonString(result, descriptor.adapter_id);
  result += '}';
  return result;
}

struct CheckpointSubmission {
  std::uint64_t sequence = 0;
  std::int32_t date_raw = 0;
  std::string_view save_name;
};

std::string HelloFrame(const xar::game::GameAdapter &game) {
  const auto &descriptor = game.descriptor();
  std::string result =
      "{\"type\":\"hello\",\"protocol_version\":1,\"bridge_version\":\"";
  result += XAR_BRIDGE_VERSION;
  result += "\",\"pid\":";
  result += Number(GetCurrentProcessId());
  result +=
      ",\"session_generation\":0,\"architecture\":\"x86_64-windows-msvc\","
      "\"expected_ck3_version\":";
  AppendJsonString(result, descriptor.game_version);
  result += ",\"expected_ck3_sha256\":";
  AppendJsonString(result, descriptor.executable_sha256);
  result += ",\"game_adapter_id\":";
  AppendJsonString(result, descriptor.adapter_id);
  result += ",\"game_adapter_status\":";
  AppendJsonString(result, game.enabled() ? "ready" : "unsupported_build");
  result += ",\"ck3_build_match\":";
  result += game.enabled() ? "true" : "false";
  result += ",\"capabilities\":[\"bridge.identity\",\"bridge.heartbeat\","
            "\"bridge.ping\"";
  if (game.enabled()) {
    for (const auto capability : descriptor.capabilities) {
      result += ',';
      AppendJsonString(result, capability);
    }
  }
  result += "]}";
  return result;
}

std::string HeartbeatFrame(std::uint64_t sequence) {
  std::string result =
      "{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":";
  result += Number(sequence);
  result += ",\"pid\":";
  result += Number(GetCurrentProcessId());
  result += "\",\"monotonic_ms\":";
  result += Number(GetTickCount64());
  result += "}";
  return result;
}

void AppendArmySnapshot(std::string &result,
                        const xar::game::ArmySnapshot &army) {
  result += "{\"army_id\":";
  result += SignedNumber(army.army_id);
  result += ",\"owner_character_id\":";
  result += SignedNumber(army.owner_character_id);
  result += ",\"current_province_id\":";
  if (army.has_current_province) {
    result += SignedNumber(army.current_province_id);
  } else {
    result += "null";
  }
  result += ",\"controllable\":";
  result += army.controllable ? "true" : "false";
  result += '}';
}

void AppendArmyArray(
    std::string &result,
    const std::vector<xar::game::ArmySnapshot> &armies) {
  result += '[';
  for (std::size_t index = 0; index < armies.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendArmySnapshot(result, armies[index]);
  }
  result += ']';
}

std::string DeclarationId(
    const xar::game::DeclarableWarSnapshot &declaration) {
  std::string result = SignedNumber(declaration.target_character_id);
  result += '-';
  result += SignedNumber(declaration.casus_belli_index);
  result += '-';
  result += SignedNumber(declaration.configuration_index);
  return result;
}

std::string DeclarationStep(
    const xar::game::DeclarableWarSnapshot &declaration) {
  return "declare-war-" + DeclarationId(declaration);
}

void AppendDeclaration(
    std::string &result,
    const xar::game::DeclarableWarSnapshot &declaration) {
  result += "{\"declaration_id\":\"";
  result += DeclarationId(declaration);
  result += "\",\"target_character_id\":";
  result += SignedNumber(declaration.target_character_id);
  result += ",\"casus_belli_index\":";
  result += SignedNumber(declaration.casus_belli_index);
  result += ",\"casus_belli_key\":";
  AppendJsonString(result, declaration.casus_belli_key);
  result += ",\"configuration_index\":";
  result += SignedNumber(declaration.configuration_index);
  result += ",\"claimant_character_id\":";
  result += SignedNumber(declaration.claimant_character_id);
  result += ",\"target_title_ids\":[";
  for (std::size_t index = 0; index < declaration.target_title_ids.size();
       ++index) {
    if (index != 0) {
      result += ',';
    }
    result += SignedNumber(declaration.target_title_ids[index]);
  }
  result += "]}";
}

std::string MarriageChoiceId(
    const xar::game::ArrangeMarriageChoice &choice) {
  std::string result = SignedNumber(choice.played_character_id);
  result += '-';
  result += SignedNumber(choice.candidate_character_id);
  return result;
}

std::string MarriageStep(
    const xar::game::ArrangeMarriageChoice &choice) {
  return "arrange-marriage-" + MarriageChoiceId(choice);
}

void AppendMarriageChoice(
    std::string &result,
    const xar::game::ArrangeMarriageChoice &choice) {
  result += "{\"choice_id\":\"";
  result += MarriageChoiceId(choice);
  result += "\",\"played_character_id\":";
  result += SignedNumber(choice.played_character_id);
  result += ",\"candidate_character_id\":";
  result += SignedNumber(choice.candidate_character_id);
  result += '}';
}

void AppendMarriageQueryDiagnostics(
    std::string &result,
    const xar::game::ArrangeMarriageQueryDiagnostics &diagnostics) {
  result += "{\"storage_capacity\":";
  result += SignedNumber(diagnostics.storage_capacity);
  result += ",\"slots_scanned\":";
  result += SignedNumber(diagnostics.slots_scanned);
  result += ",\"empty_slots\":";
  result += SignedNumber(diagnostics.empty_slots);
  result += ",\"live_candidates\":";
  result += SignedNumber(diagnostics.live_candidates);
  result += ",\"dead_candidates\":";
  result += SignedNumber(diagnostics.dead_candidates);
  result += ",\"self_candidates\":";
  result += SignedNumber(diagnostics.self_candidates);
  result += ",\"generation_mismatch_candidates\":";
  result += SignedNumber(diagnostics.generation_mismatch_candidates);
  result += ",\"contexts_constructed\":";
  result += SignedNumber(diagnostics.contexts_constructed);
  result += ",\"context_construct_failures\":";
  result += SignedNumber(diagnostics.context_construct_failures);
  result += ",\"native_validate_true\":";
  result += SignedNumber(diagnostics.native_validate_true);
  result += ",\"native_validate_false\":";
  result += SignedNumber(diagnostics.native_validate_false);
  result += ",\"validation_false_samples\":[";
  for (std::size_t index = 0;
       index < diagnostics.validation_false_samples.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    const auto &sample = diagnostics.validation_false_samples[index];
    result += "{\"slot_index\":";
    result += SignedNumber(sample.slot_index);
    result += ",\"candidate_character_id\":";
    result += SignedNumber(sample.candidate_character_id);
    result += ",\"actor_character_id\":";
    result += SignedNumber(sample.actor_character_id);
    result += ",\"recipient_character_id\":";
    result += SignedNumber(sample.recipient_character_id);
    result += ",\"secondary_actor_character_id\":";
    result += SignedNumber(sample.secondary_actor_character_id);
    result += ",\"secondary_recipient_character_id\":";
    result += SignedNumber(sample.secondary_recipient_character_id);
    result += ",\"intermediary_character_id\":";
    result += SignedNumber(sample.intermediary_character_id);
    result += '}';
  }
  result += "]}";
}

std::string StateSnapshotFrame(const xar::game::Snapshot &snapshot,
                               std::uint64_t revision,
                               const CheckpointSubmission &checkpoint) {
  std::string result = "{\"type\":\"state_snapshot\",\"protocol_version\":1,"
                       "\"snapshot_id\":\"native:";
  result += Number(revision);
  result += "\",\"revision\":";
  result += Number(revision);
  result += ",\"state\":{\"date_raw\":";
  result += SignedNumber(snapshot.date_raw);
  result += ",\"speed\":";
  result += SignedNumber(snapshot.speed);
  result += ",\"paused\":";
  result += snapshot.paused ? "true" : "false";
  // This is Jomini's 32-bit local/network player id used by
  // CPauseGameCommand, not CK3's played-character CharacterID.
  result += ",\"local_player_id\":";
  result += SignedNumber(snapshot.player_id);
  result += ",\"map_ready\":";
  result += snapshot.map_ready ? "true" : "false";
  result += ",\"played_character\":";
  if (!snapshot.has_played_character) {
    result += "null";
  } else {
    result += "{\"character_id\":";
    result += SignedNumber(snapshot.played_character_id);
    result += ",\"alive\":";
    result += snapshot.played_character_alive ? "true" : "false";
    result += ",\"betrothed_id\":";
    if (snapshot.played_character_betrothed_id == -1) {
      result += "null";
    } else {
      result += SignedNumber(snapshot.played_character_betrothed_id);
    }
    result += ",\"primary_spouse_id\":";
    if (snapshot.played_character_primary_spouse_id == -1) {
      result += "null";
    } else {
      result += SignedNumber(snapshot.played_character_primary_spouse_id);
    }
    result += ",\"spouse_ids\":[";
    for (std::size_t index = 0;
         index < snapshot.played_character_spouse_ids.size(); ++index) {
      if (index != 0) {
        result += ',';
      }
      result += SignedNumber(snapshot.played_character_spouse_ids[index]);
    }
    result += ']';
    result += '}';
  }
  result += ",\"active_event\":";
  if (!snapshot.has_active_event) {
    result += "null";
  } else {
    result += "{\"instance_id\":";
    result += SignedNumber(snapshot.active_event_instance_id);
    result += ",\"option_count\":";
    result += SignedNumber(snapshot.active_event_option_count);
    result += ",\"option_indexes\":[";
    for (std::int32_t public_index = 1;
         public_index <= snapshot.active_event_option_count; ++public_index) {
      if (public_index != 1) {
        result += ',';
      }
      result += SignedNumber(public_index);
    }
    result += "]}";
  }
  result += ",\"pending_character_interaction\":";
  if (!snapshot.has_pending_character_interaction) {
    result += "null";
  } else {
    result += "{\"instance_id\":";
    result += SignedNumber(snapshot.pending_character_interaction_id);
    result += ",\"sender_character_id\":";
    result += SignedNumber(snapshot.pending_sender_character_id);
    result += ",\"auto_accept_notification\":";
    result += snapshot.pending_auto_accept_notification ? "true" : "false";
    result += '}';
  }
  result += ",\"active_wars\":[";
  for (std::size_t index = 0; index < snapshot.active_wars.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    const auto &war = snapshot.active_wars[index];
    result += "{\"war_id\":";
    result += SignedNumber(war.war_id);
    result += ",\"player_side\":\"";
    result += war.player_side == xar::game::PlayerWarSide::attacker
                  ? "attacker"
                  : "defender";
    result += "\",\"player_relative_war_score\":";
    result += SignedNumber(war.player_relative_war_score);
    result += ",\"allied_armies\":";
    AppendArmyArray(result, war.allied_armies);
    result += ",\"enemy_armies\":";
    AppendArmyArray(result, war.enemy_armies);
    result += '}';
  }
  result += "],\"player_armies\":";
  AppendArmyArray(result, snapshot.player_armies);
  result += ",\"last_checkpoint_submission\":";
  if (checkpoint.sequence == 0) {
    result += "null";
  } else {
    result += "{\"sequence\":";
    result += Number(checkpoint.sequence);
    result += ",\"requested_save_name\":\"";
    result += checkpoint.save_name;
    result += "\",\"date_raw\":";
    result += SignedNumber(checkpoint.date_raw);
    result += ",\"status\":\"submitted\"}";
  }
  result += ",\"history\":[]}}";
  return result;
}

std::string CommandResultFrame(std::string_view request_id,
                               std::string_view step, bool ok,
                               std::string_view status) {
  std::string result = "{\"type\":\"command_result\",\"protocol_version\":1,"
                       "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":";
  result += ok ? "true" : "false";
  if (ok) {
    result += ",\"result\":{\"step\":\"";
    result += step;
    result += "\",\"accepted\":true,\"status\":\"";
    result += status;
    result += "\"}}";
  } else {
    result += ",\"error\":\"";
    result += status;
    result += "\"}";
  }
  return result;
}

std::string SaveCheckpointResultFrame(std::string_view request_id,
                                      const CheckpointSubmission &checkpoint) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":true,\"result\":{\"step\":\"save-checkpoint\","
            "\"accepted\":true,\"status\":\"submitted\","
            "\"submission\":{\"sequence\":";
  result += Number(checkpoint.sequence);
  result += ",\"requested_save_name\":\"";
  result += checkpoint.save_name;
  result += "\",\"date_raw\":";
  result += SignedNumber(checkpoint.date_raw);
  result += "}}}";
  return result;
}

std::string DeclarableWarsResultFrame(
    std::string_view request_id, std::uint64_t query_sequence,
    const std::vector<xar::game::DeclarableWarSnapshot> &declarations) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result +=
      "\",\"ok\":true,\"result\":{\"step\":\"query-declarable-wars\","
      "\"accepted\":true,\"status\":\"available\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"declarable_wars\":[";
  for (std::size_t index = 0; index < declarations.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendDeclaration(result, declarations[index]);
  }
  result += "]}}";
  return result;
}

std::string ArrangeMarriageChoicesResultFrame(
    std::string_view request_id, std::uint64_t query_sequence,
    const std::vector<xar::game::ArrangeMarriageChoice> &choices,
    const xar::game::ArrangeMarriageQueryDiagnostics &diagnostics) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":\"";
  result += request_id;
  result +=
      "\",\"ok\":true,\"result\":{\"step\":"
      "\"query-arrange-marriage-choices\",\"accepted\":true,"
      "\"status\":\"available\",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"arrange_marriage_choices\":[";
  for (std::size_t index = 0; index < choices.size(); ++index) {
    if (index != 0) {
      result += ',';
    }
    AppendMarriageChoice(result, choices[index]);
  }
  result += "],\"arrange_marriage_diagnostics\":";
  AppendMarriageQueryDiagnostics(result, diagnostics);
  result += "}}";
  return result;
}

std::int32_t FixedSpeedStep(std::string_view step) noexcept {
  constexpr std::string_view prefix = "set-speed-";
  if (!step.starts_with(prefix) || step.size() != prefix.size() + 1U) {
    return -1;
  }
  const char digit = step.back();
  return digit >= '1' && digit <= '5' ? digit - '0' : -1;
}

std::optional<std::int32_t>
EventOptionStep(std::string_view step) noexcept {
  constexpr std::string_view prefix = "select-event-option-";
  if (!step.starts_with(prefix) || step.size() == prefix.size()) {
    return std::nullopt;
  }
  std::int32_t public_index = -1;
  const auto suffix = step.substr(prefix.size());
  const auto parsed = std::from_chars(suffix.data(),
                                      suffix.data() + suffix.size(),
                                      public_index);
  if (parsed.ec != std::errc{} || parsed.ptr != suffix.data() + suffix.size() ||
      public_index < 1) {
    return std::nullopt;
  }
  // MCP/agent-facing event choices are one based. CK3's native command
  // payload and executor are zero based.
  return public_index - 1;
}

std::optional<std::int32_t> PositiveNativeId(
    std::string_view value) noexcept {
  if (value.empty()) {
    return std::nullopt;
  }
  for (const char character : value) {
    if (character < '0' || character > '9') {
      return std::nullopt;
    }
  }
  std::int32_t parsed_value = -1;
  const auto parsed = std::from_chars(
      value.data(), value.data() + value.size(), parsed_value);
  if (parsed.ec != std::errc{} ||
      parsed.ptr != value.data() + value.size() || parsed_value < 1) {
    return std::nullopt;
  }
  return parsed_value;
}

struct MoveArmyStepIds {
  std::int32_t army_id = -1;
  std::int32_t province_id = -1;
};

std::optional<MoveArmyStepIds> MoveArmyStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix = "move-army-";
  constexpr std::string_view separator = "-to-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  const auto payload = step.substr(prefix.size());
  const std::size_t separator_index = payload.find(separator);
  if (separator_index == std::string_view::npos ||
      payload.find(separator, separator_index + separator.size()) !=
          std::string_view::npos) {
    return std::nullopt;
  }
  const auto army_id = PositiveNativeId(payload.substr(0, separator_index));
  const auto province_id = PositiveNativeId(
      payload.substr(separator_index + separator.size()));
  if (!army_id.has_value() || !province_id.has_value()) {
    return std::nullopt;
  }
  return MoveArmyStepIds{army_id.value(), province_id.value()};
}

std::optional<std::int32_t> DisbandArmyStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix = "disband-army-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  return PositiveNativeId(step.substr(prefix.size()));
}

std::optional<std::int32_t> EnforceDemandsStep(
    std::string_view step) noexcept {
  constexpr std::string_view prefix = "enforce-demands-";
  if (!step.starts_with(prefix)) {
    return std::nullopt;
  }
  return PositiveNativeId(step.substr(prefix.size()));
}

bool PublishSnapshot(HANDLE pipe, const xar::game::GameAdapter &bindings,
                     std::optional<xar::game::Snapshot> &previous,
                     std::uint64_t &revision,
                     const CheckpointSubmission &checkpoint,
                     std::uint64_t &published_checkpoint_sequence) {
  if (!bindings.supports_snapshot()) {
    return true;
  }
  xar::game::Snapshot snapshot{};
  if (!xar::game::ReadSnapshot(bindings, snapshot)) {
    return true;
  }
  if (previous.has_value() && previous.value() == snapshot &&
      published_checkpoint_sequence == checkpoint.sequence) {
    return true;
  }
  ++revision;
  previous = snapshot;
  published_checkpoint_sequence = checkpoint.sequence;
  return xar::bridge::WriteFrame(
      pipe, StateSnapshotFrame(snapshot, revision, checkpoint));
}

bool JsonStringField(std::string_view json, std::string_view key,
                     std::string &output) {
  std::string needle = "\"";
  needle += key;
  needle += "\":\"";
  const std::size_t begin = json.find(needle);
  if (begin == std::string_view::npos) {
    return false;
  }
  const std::size_t value_begin = begin + needle.size();
  const std::size_t end = json.find('"', value_begin);
  if (end == std::string_view::npos || end == value_begin ||
      end - value_begin > 128U) {
    return false;
  }
  const auto value = json.substr(value_begin, end - value_begin);
  if (value.find('\\') != std::string_view::npos) {
    return false;
  }
  output.assign(value);
  return true;
}

bool IsSimpleRequestId(std::string_view value) noexcept {
  if (value.empty() || value.size() > 128U) {
    return false;
  }
  for (const char character : value) {
    const bool accepted = (character >= 'a' && character <= 'z') ||
                          (character >= 'A' && character <= 'Z') ||
                          (character >= '0' && character <= '9') ||
                          character == '-' || character == '_' ||
                          character == '.';
    if (!accepted) {
      return false;
    }
  }
  return true;
}

HANDLE ConnectToHost() noexcept {
  while (WaitForSingleObject(g_stop_event, 0) == WAIT_TIMEOUT) {
    HANDLE pipe = CreateFileW(g_pipe_name, GENERIC_READ | GENERIC_WRITE, 0,
                              nullptr, OPEN_EXISTING, 0, nullptr);
    if (pipe != INVALID_HANDLE_VALUE) {
      return pipe;
    }
    const DWORD error = GetLastError();
    if (error != ERROR_PIPE_BUSY && error != ERROR_FILE_NOT_FOUND) {
      return INVALID_HANDLE_VALUE;
    }
    WaitForSingleObject(g_stop_event, 50);
  }
  return INVALID_HANDLE_VALUE;
}

struct WorkerState {
  std::uint64_t sequence = 0;
  std::uint64_t state_revision = 0;
  CheckpointSubmission checkpoint_submission{};
  std::uint64_t published_checkpoint_sequence = 0;
  std::optional<xar::game::Snapshot> previous_snapshot;
  std::uint64_t declaration_query_sequence = 0;
  std::vector<xar::game::DeclarableWarSnapshot> declarable_wars;
  std::uint64_t marriage_query_sequence = 0;
  std::vector<xar::game::ArrangeMarriageChoice> marriage_choices;
};

void RunConnectedSession(HANDLE pipe, const xar::game::GameAdapter &game,
                         WorkerState &state) noexcept {
  state.checkpoint_submission.save_name =
      game.descriptor().checkpoint_save_name;
  if (!xar::bridge::WriteFrame(pipe, HelloFrame(game))) {
    return;
  }

  auto &sequence = state.sequence;
  auto &state_revision = state.state_revision;
  auto &checkpoint_submission = state.checkpoint_submission;
  auto &published_checkpoint_sequence = state.published_checkpoint_sequence;
  auto &previous_snapshot = state.previous_snapshot;
  auto &declaration_query_sequence = state.declaration_query_sequence;
  auto &declarable_wars = state.declarable_wars;
  auto &marriage_query_sequence = state.marriage_query_sequence;
  auto &marriage_choices = state.marriage_choices;

  // A new MCP server has no copy of the previous semantic snapshot.  Force
  // the first heartbeat on every connection to republish current state and
  // the latest checkpoint submission, even if CK3 itself did not change.
  previous_snapshot.reset();
  published_checkpoint_sequence = 0;
  ULONGLONG next_heartbeat = GetTickCount64();
  bool connected = true;
  while (connected && WaitForSingleObject(g_stop_event, 0) == WAIT_TIMEOUT) {
    const ULONGLONG now = GetTickCount64();
    if (now >= next_heartbeat) {
      ++sequence;
      connected = xar::bridge::WriteFrame(pipe, HeartbeatFrame(sequence));
      if (connected && game.supports_snapshot()) {
        connected = PublishSnapshot(pipe, game, previous_snapshot,
                                    state_revision, checkpoint_submission,
                                    published_checkpoint_sequence);
      }
      next_heartbeat = now + kHeartbeatIntervalMs;
      if (!connected) {
        break;
      }
    }

    const auto incoming = xar::bridge::TryReadFrame(pipe);
    if (incoming.status == xar::bridge::ReadStatus::closed ||
        incoming.status == xar::bridge::ReadStatus::invalid) {
      break;
    }
    if (incoming.status == xar::bridge::ReadStatus::frame) {
      std::string type;
      std::string request_id;
      if (JsonStringField(incoming.payload, "type", type) && type == "ping" &&
          JsonStringField(incoming.payload, "request_id", request_id) &&
          IsSimpleRequestId(request_id)) {
        std::string pong =
            "{\"type\":\"pong\",\"protocol_version\":1,\"request_id\":\"";
        pong += request_id;
        pong += "\",\"pid\":";
        pong += Number(GetCurrentProcessId());
        pong += "}";
        connected = xar::bridge::WriteFrame(pipe, pong);
      } else if (type == "execute_step" &&
                 JsonStringField(incoming.payload, "request_id", request_id) &&
                 IsSimpleRequestId(request_id)) {
        std::string step;
        if (!JsonStringField(incoming.payload, "step", step)) {
          connected = xar::bridge::WriteFrame(
              pipe, CommandResultFrame(request_id, "", false,
                                       "native gameplay step is missing"));
        } else if (!game.supports_step(step)) {
          connected = xar::bridge::WriteFrame(
              pipe, CommandResultFrame(request_id, step, false,
                                       "unsupported native gameplay step"));
        } else if (step == "pause-map") {
          const auto result = xar::game::SubmitPauseMap(game);
          if (result == xar::game::PauseSubmitResult::unavailable) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false,
                                         "CK3 map state is unavailable"));
          } else {
            const std::string_view status =
                result == xar::game::PauseSubmitResult::submitted
                    ? "submitted"
                    : "already_paused";
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, status));
            if (connected) {
              connected = PublishSnapshot(pipe, game, previous_snapshot,
                                          state_revision, checkpoint_submission,
                                          published_checkpoint_sequence);
            }
          }
        } else if (step == "resume-map") {
          const auto result = xar::game::SubmitResumeMap(game);
          if (result == xar::game::ResumeSubmitResult::unavailable) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false,
                                         "CK3 map state is unavailable"));
          } else {
            const std::string_view status =
                result == xar::game::ResumeSubmitResult::submitted
                    ? "submitted"
                    : "already_running";
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, status));
            if (connected) {
              connected = PublishSnapshot(pipe, game, previous_snapshot,
                                          state_revision, checkpoint_submission,
                                          published_checkpoint_sequence);
            }
          }
        } else if (step == "save-checkpoint") {
          const auto result = xar::game::SubmitSaveCheckpoint(game);
          if (result.status ==
              xar::game::SaveCheckpointStatus::submitted) {
            ++checkpoint_submission.sequence;
            checkpoint_submission.date_raw = result.date_raw;
            connected = xar::bridge::WriteFrame(
                pipe,
                SaveCheckpointResultFrame(request_id, checkpoint_submission));
            if (connected) {
              connected = PublishSnapshot(pipe, game, previous_snapshot,
                                          state_revision, checkpoint_submission,
                                          published_checkpoint_sequence);
            }
          } else {
            const std::string_view error =
                result.status ==
                        xar::game::SaveCheckpointStatus::map_not_ready
                    ? "CK3 map is not ready"
                    : "CK3 save state is unavailable";
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
        } else if (step == "accept-pending-character-interaction" ||
                   step == "reject-pending-character-interaction") {
          const auto reply =
              step == "accept-pending-character-interaction"
                  ? xar::game::PendingInteractionReply::accept
                  : xar::game::PendingInteractionReply::reject;
          const auto result =
              xar::game::SubmitReplyToPendingInteraction(game, reply);
          if (result ==
              xar::game::ReplyPendingInteractionResult::submitted) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, "submitted"));
          } else {
            std::string_view error =
                "CK3 pending character interaction state is unavailable";
            if (result == xar::game::ReplyPendingInteractionResult::
                              no_pending_interaction) {
              error = "no pending CK3 character interaction";
            } else if (result == xar::game::ReplyPendingInteractionResult::
                                     acknowledgement_required) {
              error = "pending CK3 interaction requires acknowledgement";
            }
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step == "query-arrange-marriage-choices") {
          marriage_choices.clear();
          xar::game::ArrangeMarriageQueryDiagnostics diagnostics{};
          const auto result = xar::game::ReadArrangeMarriageChoices(
              game, marriage_choices, diagnostics);
          if (result == xar::game::
                            ReadArrangeMarriageChoicesResult::available) {
            ++marriage_query_sequence;
            connected = xar::bridge::WriteFrame(
                pipe, ArrangeMarriageChoicesResultFrame(
                          request_id, marriage_query_sequence,
                          marriage_choices, diagnostics));
          } else {
            const std::string_view error =
                result == xar::game::
                              ReadArrangeMarriageChoicesResult::
                                  no_played_character
                    ? "no living played CK3 character"
                    : "CK3 arrange-marriage query is unavailable";
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
        } else if (step.starts_with("arrange-marriage-")) {
          const xar::game::ArrangeMarriageChoice *selected = nullptr;
          for (const auto &candidate : marriage_choices) {
            if (MarriageStep(candidate) == step) {
              selected = &candidate;
              break;
            }
          }
          if (selected == nullptr) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "arrange-marriage choice is missing or stale; "
                          "query first"));
          } else {
            const auto result =
                xar::game::SubmitArrangeMarriage(game, *selected);
            if (result ==
                xar::game::ArrangeMarriageResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
              marriage_choices.clear();
            } else {
              std::string_view error =
                  "CK3 arrange-marriage state is unavailable";
              if (result == xar::game::ArrangeMarriageResult::
                                no_played_character) {
                error = "no living played CK3 character";
              } else if (result ==
                         xar::game::ArrangeMarriageResult::
                             candidate_not_found) {
                error = "CK3 arrange-marriage candidate was not found";
                marriage_choices.clear();
              } else if (result ==
                         xar::game::ArrangeMarriageResult::
                             choice_unavailable) {
                error = "CK3 arrange-marriage choice changed; query again";
                marriage_choices.clear();
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step == "query-declarable-wars") {
          declarable_wars.clear();
          if (!xar::game::ReadDeclarableWars(game, declarable_wars)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "CK3 declarable-war query is unavailable"));
          } else {
            ++declaration_query_sequence;
            connected = xar::bridge::WriteFrame(
                pipe, DeclarableWarsResultFrame(
                          request_id, declaration_query_sequence,
                          declarable_wars));
          }
        } else if (step.starts_with("declare-war-")) {
          const xar::game::DeclarableWarSnapshot *selected = nullptr;
          for (const auto &candidate : declarable_wars) {
            if (DeclarationStep(candidate) == step) {
              selected = &candidate;
              break;
            }
          }
          if (selected == nullptr) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "declare-war choice is missing or stale; query first"));
          } else {
            const auto result =
                xar::game::SubmitDeclareWar(game, *selected);
            if (result == xar::game::DeclareWarResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
              declarable_wars.clear();
            } else {
              std::string_view error = "CK3 declare-war state is unavailable";
              if (result ==
                  xar::game::DeclareWarResult::no_played_character) {
                error = "no living played CK3 character";
              } else if (result ==
                         xar::game::DeclareWarResult::target_not_found) {
                error = "CK3 declare-war target was not found";
              } else if (
                  result == xar::game::DeclareWarResult::
                                declaration_unavailable) {
                error = "CK3 declare-war choice changed; query again";
              } else if (result ==
                         xar::game::DeclareWarResult::validation_failed) {
                error = "CK3 rejected declare-war validation";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with("enforce-demands-")) {
          const auto war_id = EnforceDemandsStep(step);
          if (!war_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid enforce-demands-<war_id> step"));
          } else {
            const auto result = xar::game::SubmitEnforceDemands(
                game, war_id.value());
            if (result == xar::game::EnforceDemandsResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
            } else {
              std::string_view error =
                  "CK3 enforce-demands state is unavailable";
              if (result ==
                  xar::game::EnforceDemandsResult::
                      no_played_character) {
                error = "no living played CK3 character";
              } else if (result ==
                         xar::game::EnforceDemandsResult::war_not_found) {
                error = "CK3 war was not found";
              } else if (
                  result == xar::game::EnforceDemandsResult::
                                player_not_participant) {
                error = "played CK3 character is not a war participant";
              } else if (
                  result == xar::game::EnforceDemandsResult::
                                player_not_war_leader) {
                error = "played CK3 character is not the war leader";
              } else if (result ==
                         xar::game::EnforceDemandsResult::
                             validation_failed) {
                error = "CK3 rejected enforce-demands validation";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step == "raise-troops-default") {
          const auto result = xar::game::SubmitRaiseTroopsDefault(game);
          if (result == xar::game::RaiseTroopsResult::submitted) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, "submitted"));
          } else {
            std::string_view error = "CK3 raise-troops state is unavailable";
            if (result ==
                xar::game::RaiseTroopsResult::no_played_character) {
              error = "no living played CK3 character";
            } else if (result ==
                       xar::game::RaiseTroopsResult::no_default_province) {
              error = "no default CK3 rally province";
            } else if (result ==
                       xar::game::RaiseTroopsResult::validation_failed) {
              error = "CK3 rejected raise-troops validation";
            }
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with("move-army-")) {
          const auto ids = MoveArmyStep(step);
          if (!ids.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(
                          request_id, step, false,
                          "invalid move-army-<army_id>-to-<province_id> step"));
          } else {
            const auto result = xar::game::SubmitMoveArmy(
                game, ids->army_id, ids->province_id);
            if (result == xar::game::MoveArmyResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
            } else {
              std::string_view error = "CK3 move-army state is unavailable";
              if (result == xar::game::MoveArmyResult::army_not_found) {
                error = "CK3 army was not found";
              } else if (result == xar::game::MoveArmyResult::
                                       army_not_controllable) {
                error = "CK3 army is not player-controllable";
              } else if (result ==
                         xar::game::MoveArmyResult::province_not_found) {
                error = "CK3 destination province was not found";
              } else if (result ==
                         xar::game::MoveArmyResult::move_mode_unavailable) {
                error = "CK3 army has no move mode for the destination";
              } else if (result == xar::game::MoveArmyResult::
                                       character_state_rejected) {
                error = "CK3 played character state rejects army movement";
              } else if (result ==
                         xar::game::MoveArmyResult::army_state_rejected) {
                error = "CK3 army state rejects movement";
              } else if (result ==
                         xar::game::MoveArmyResult::validation_failed) {
                error = "CK3 move-army command validation failed";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (step.starts_with("disband-army-")) {
          const auto army_id = DisbandArmyStep(step);
          if (!army_id.has_value()) {
            connected = xar::bridge::WriteFrame(
                pipe,
                CommandResultFrame(request_id, step, false,
                                   "invalid disband-army-<army_id> step"));
          } else {
            const auto result =
                xar::game::SubmitDisbandArmy(game, army_id.value());
            if (result == xar::game::DisbandArmyResult::submitted) {
              connected = xar::bridge::WriteFrame(
                  pipe,
                  CommandResultFrame(request_id, step, true, "submitted"));
            } else {
              std::string_view error = "CK3 disband-army state is unavailable";
              if (result == xar::game::DisbandArmyResult::army_not_found) {
                error = "CK3 army was not found";
              } else if (result == xar::game::DisbandArmyResult::
                                       army_not_controllable) {
                error = "CK3 army is not player-controllable";
              }
              connected = xar::bridge::WriteFrame(
                  pipe, CommandResultFrame(request_id, step, false, error));
            }
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else if (const auto option_index = EventOptionStep(step);
                   option_index.has_value()) {
          const auto result = xar::game::SubmitSelectEventOption(
              game, option_index.value());
          if (result == xar::game::SelectEventOptionResult::submitted) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, "submitted"));
          } else {
            std::string_view error = "CK3 event state is unavailable";
            if (result ==
                xar::game::SelectEventOptionResult::no_active_event) {
              error = "no active CK3 event";
            } else if (result == xar::game::SelectEventOptionResult::
                                     option_out_of_range) {
              error = "event option index is out of range";
            }
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision, checkpoint_submission,
                                        published_checkpoint_sequence);
          }
        } else {
          const std::int32_t requested_speed = FixedSpeedStep(step);
          if (requested_speed >= 1 &&
              xar::game::SubmitSetSpeed(game, requested_speed)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, "submitted"));
            if (connected) {
              connected = PublishSnapshot(pipe, game, previous_snapshot,
                                          state_revision, checkpoint_submission,
                                          published_checkpoint_sequence);
            }
          } else {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false,
                                         "unsupported native gameplay step"));
          }
        }
      }
    }
    WaitForSingleObject(g_stop_event, 10);
  }
}

DWORD WINAPI WorkerMain(void *) noexcept {
  const auto game = xar::game::SelectCurrentProcessAdapter();
  if (game == nullptr) {
    return 1;
  }
  WorkerState state{};
  while (WaitForSingleObject(g_stop_event, 0) == WAIT_TIMEOUT) {
    HANDLE pipe = ConnectToHost();
    if (pipe == INVALID_HANDLE_VALUE) {
      return WaitForSingleObject(g_stop_event, 0) == WAIT_OBJECT_0 ? 0 : 1;
    }
    RunConnectedSession(pipe, *game, state);
    CloseHandle(pipe);
    if (WaitForSingleObject(g_stop_event, 0) == WAIT_TIMEOUT) {
      WaitForSingleObject(g_stop_event, 50);
    }
  }
  return 0;
}

BOOL StartWithPipeName(const wchar_t *pipe_name, DWORD length) noexcept {
  if (!IsPipeName(pipe_name, length)) {
    return FALSE;
  }
  if (g_lifecycle.exchange(1) != 0) {
    return TRUE;
  }
  for (DWORD index = 0; index <= length; ++index) {
    g_pipe_name[index] = pipe_name[index];
  }

  g_stop_event = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  if (g_stop_event == nullptr) {
    g_lifecycle.store(0);
    return FALSE;
  }
  g_worker_thread = CreateThread(nullptr, 0, WorkerMain, nullptr, 0, nullptr);
  if (g_worker_thread == nullptr) {
    CloseHandle(g_stop_event);
    g_stop_event = nullptr;
    g_lifecycle.store(0);
    return FALSE;
  }
  return TRUE;
}

BOOL StartFromEnvironment() noexcept {
  wchar_t pipe_name[kPipeNameCapacity]{};
  const DWORD length = GetEnvironmentVariableW(
      kPipeEnvironment, pipe_name, static_cast<DWORD>(kPipeNameCapacity));
  return StartWithPipeName(pipe_name, length);
}

void SignalStop() noexcept {
  if (g_stop_event != nullptr) {
    SetEvent(g_stop_event);
  }
}

} // namespace

extern "C" __declspec(dllexport) const char *WINAPI
XarCk3BridgeIdentity() noexcept {
  static const std::string identity = IdentityFrame();
  return identity.c_str();
}

extern "C" __declspec(dllexport) BOOL WINAPI XarCk3BridgeStart() noexcept {
  return StartFromEnvironment();
}

// The signature intentionally matches LPTHREAD_START_ROUTINE on x64 Windows.
// This lets the injector start an already-running process that did not inherit
// XAR_CK3_BRIDGE_PIPE, without modifying that process's environment block.
extern "C" __declspec(dllexport) BOOL WINAPI
XarCk3BridgeStartWithPipe(const wchar_t *pipe_name) noexcept {
  if (pipe_name == nullptr) {
    return FALSE;
  }
  DWORD length = 0;
  while (length < kPipeNameCapacity && pipe_name[length] != L'\0') {
    ++length;
  }
  return StartWithPipeName(pipe_name, length);
}

extern "C" __declspec(dllexport) void WINAPI XarCk3BridgeStop() noexcept {
  SignalStop();
  if (g_worker_thread != nullptr) {
    WaitForSingleObject(g_worker_thread, 5000);
    CloseHandle(g_worker_thread);
    g_worker_thread = nullptr;
  }
  if (g_stop_event != nullptr) {
    CloseHandle(g_stop_event);
    g_stop_event = nullptr;
  }
  g_pipe_name[0] = L'\0';
  g_lifecycle.store(0);
}

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
  if (reason == DLL_PROCESS_ATTACH) {
    DisableThreadLibraryCalls(instance);
    wchar_t pipe_name[kPipeNameCapacity]{};
    const DWORD length = GetEnvironmentVariableW(
        kPipeEnvironment, pipe_name, static_cast<DWORD>(kPipeNameCapacity));
    if (IsPipeName(pipe_name, length)) {
      StartFromEnvironment();
    }
  } else if (reason == DLL_PROCESS_DETACH) {
    // Normal bridge users call XarCk3BridgeStop before FreeLibrary. During
    // process teardown, only signal: waiting from DllMain would block unload.
    SignalStop();
  }
  return TRUE;
}
