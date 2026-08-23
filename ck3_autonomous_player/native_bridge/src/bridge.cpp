#include "xar_bridge/ck3_11906.hpp"
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
constexpr char kExpectedCk3Version[] = "1.19.0.6";
constexpr char kExpectedCk3Sha256[] =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

constexpr char kIdentityJson[] =
    "{\"bridge\":\"xar_ck3_bridge\",\"bridge_version\":\"" XAR_BRIDGE_VERSION
    "\",\"protocol_version\":1,\"architecture\":\"x86_64-windows-msvc\","
    "\"expected_ck3_version\":\"1.19.0.6\","
    "\"expected_ck3_sha256\":\""
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\"}";

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

std::string HelloFrame(bool ck3_gameplay_enabled) {
  std::string result =
      "{\"type\":\"hello\",\"protocol_version\":1,\"bridge_version\":\"";
  result += XAR_BRIDGE_VERSION;
  result += "\",\"pid\":";
  result += Number(GetCurrentProcessId());
  result +=
      ",\"session_generation\":0,\"architecture\":\"x86_64-windows-msvc\","
      "\"expected_ck3_version\":\"";
  result += kExpectedCk3Version;
  result += "\",\"expected_ck3_sha256\":\"";
  result += kExpectedCk3Sha256;
  result += "\",\"ck3_build_match\":";
  result += ck3_gameplay_enabled ? "true" : "false";
  result += ",\"capabilities\":[\"bridge.identity\",\"bridge.heartbeat\","
            "\"bridge.ping\"";
  if (ck3_gameplay_enabled) {
    result += ",\"game.state.snapshot\",\"game.state.active-event\","
              "\"game.command.pause-map\","
              "\"game.command.resume-map\","
              "\"game.command.set-speed-1\",\"game.command.set-speed-2\","
              "\"game.command.set-speed-3\",\"game.command.set-speed-4\","
              "\"game.command.set-speed-5\","
              "\"game.command.select-event-option-N\"";
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

std::string StateSnapshotFrame(const xar::ck3_11906::Snapshot &snapshot,
                               std::uint64_t revision) {
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
  // CPauseGameCommand, not CK3's 64-bit played-character id.
  result += ",\"local_player_id\":";
  result += SignedNumber(snapshot.player_id);
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

bool PublishSnapshot(HANDLE pipe, const xar::ck3_11906::Bindings &bindings,
                     std::optional<xar::ck3_11906::Snapshot> &previous,
                     std::uint64_t &revision) {
  xar::ck3_11906::Snapshot snapshot{};
  if (!xar::ck3_11906::ReadSnapshot(bindings, snapshot)) {
    return true;
  }
  if (previous.has_value() && previous.value() == snapshot) {
    return true;
  }
  ++revision;
  previous = snapshot;
  return xar::bridge::WriteFrame(pipe, StateSnapshotFrame(snapshot, revision));
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

DWORD WINAPI WorkerMain(void *) noexcept {
  const xar::ck3_11906::Bindings game = xar::ck3_11906::BindCurrentProcess();
  HANDLE pipe = ConnectToHost();
  if (pipe == INVALID_HANDLE_VALUE) {
    return 1;
  }

  if (!xar::bridge::WriteFrame(pipe, HelloFrame(game.enabled))) {
    CloseHandle(pipe);
    return 2;
  }

  std::uint64_t sequence = 0;
  std::uint64_t state_revision = 0;
  std::optional<xar::ck3_11906::Snapshot> previous_snapshot;
  ULONGLONG next_heartbeat = GetTickCount64();
  bool connected = true;
  while (connected && WaitForSingleObject(g_stop_event, 0) == WAIT_TIMEOUT) {
    const ULONGLONG now = GetTickCount64();
    if (now >= next_heartbeat) {
      ++sequence;
      connected = xar::bridge::WriteFrame(pipe, HeartbeatFrame(sequence));
      if (connected && game.enabled) {
        connected =
            PublishSnapshot(pipe, game, previous_snapshot, state_revision);
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
      } else if (game.enabled && type == "execute_step" &&
                 JsonStringField(incoming.payload, "request_id", request_id) &&
                 IsSimpleRequestId(request_id)) {
        std::string step;
        if (!JsonStringField(incoming.payload, "step", step)) {
          connected = xar::bridge::WriteFrame(
              pipe, CommandResultFrame(request_id, "", false,
                                       "native gameplay step is missing"));
        } else if (step == "pause-map") {
          const auto result = xar::ck3_11906::SubmitPauseMap(game);
          if (result == xar::ck3_11906::PauseSubmitResult::unavailable) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false,
                                         "CK3 map state is unavailable"));
          } else {
            const std::string_view status =
                result == xar::ck3_11906::PauseSubmitResult::submitted
                    ? "submitted"
                    : "already_paused";
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, status));
            if (connected) {
              connected = PublishSnapshot(pipe, game, previous_snapshot,
                                          state_revision);
            }
          }
        } else if (step == "resume-map") {
          const auto result = xar::ck3_11906::SubmitResumeMap(game);
          if (result == xar::ck3_11906::ResumeSubmitResult::unavailable) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false,
                                         "CK3 map state is unavailable"));
          } else {
            const std::string_view status =
                result == xar::ck3_11906::ResumeSubmitResult::submitted
                    ? "submitted"
                    : "already_running";
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, status));
            if (connected) {
              connected = PublishSnapshot(pipe, game, previous_snapshot,
                                          state_revision);
            }
          }
        } else if (const auto option_index = EventOptionStep(step);
                   option_index.has_value()) {
          const auto result = xar::ck3_11906::SubmitSelectEventOption(
              game, option_index.value());
          if (result ==
              xar::ck3_11906::SelectEventOptionResult::submitted) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, "submitted"));
          } else {
            std::string_view error = "CK3 event state is unavailable";
            if (result ==
                xar::ck3_11906::SelectEventOptionResult::no_active_event) {
              error = "no active CK3 event";
            } else if (
                result == xar::ck3_11906::SelectEventOptionResult::option_out_of_range) {
              error = "event option index is out of range";
            }
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, false, error));
          }
          if (connected) {
            connected = PublishSnapshot(pipe, game, previous_snapshot,
                                        state_revision);
          }
        } else {
          const std::int32_t requested_speed = FixedSpeedStep(step);
          if (requested_speed >= 1 &&
              xar::ck3_11906::SubmitSetSpeed(game, requested_speed)) {
            connected = xar::bridge::WriteFrame(
                pipe, CommandResultFrame(request_id, step, true, "submitted"));
            if (connected) {
              connected = PublishSnapshot(pipe, game, previous_snapshot,
                                          state_revision);
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

  CloseHandle(pipe);
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
  return kIdentityJson;
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
