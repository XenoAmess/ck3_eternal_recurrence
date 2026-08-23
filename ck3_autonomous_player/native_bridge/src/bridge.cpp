#include "xar_bridge/protocol.hpp"

#include <windows.h>

#include <array>
#include <atomic>
#include <charconv>
#include <cstdint>
#include <string>
#include <string_view>

namespace {

static_assert(sizeof(void*) == 8, "the CK3 bridge is x64-only");

constexpr wchar_t kPipeEnvironment[] = L"XAR_CK3_BRIDGE_PIPE";
constexpr std::size_t kPipeNameCapacity = 256;
constexpr DWORD kHeartbeatIntervalMs = 250;
constexpr char kExpectedCk3Version[] = "1.19.0.6";
constexpr char kExpectedCk3Sha256[] =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

constexpr char kIdentityJson[] =
    "{\"bridge\":\"xar_ck3_bridge\",\"bridge_version\":\""
    XAR_BRIDGE_VERSION
    "\",\"protocol_version\":1,\"architecture\":\"x86_64-windows-msvc\","
    "\"expected_ck3_version\":\"1.19.0.6\","
    "\"expected_ck3_sha256\":\""
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\"}";

wchar_t g_pipe_name[kPipeNameCapacity]{};
HANDLE g_stop_event = nullptr;
HANDLE g_worker_thread = nullptr;
std::atomic<long> g_lifecycle{0};  // 0 stopped, 1 starting/running

bool IsPipeName(const wchar_t* value, DWORD length) noexcept {
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
  const auto result = std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec != std::errc{}) {
    return "0";
  }
  return std::string(buffer.data(), result.ptr);
}

std::string HelloFrame() {
  std::string result =
      "{\"type\":\"hello\",\"protocol_version\":1,\"bridge_version\":\"";
  result += XAR_BRIDGE_VERSION;
  result += "\",\"pid\":";
  result += Number(GetCurrentProcessId());
  result += ",\"session_generation\":0,\"architecture\":\"x86_64-windows-msvc\","
            "\"expected_ck3_version\":\"";
  result += kExpectedCk3Version;
  result += "\",\"expected_ck3_sha256\":\"";
  result += kExpectedCk3Sha256;
  result += "\",\"capabilities\":[\"bridge.identity\",\"bridge.heartbeat\","
            "\"bridge.ping\"]}";
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

bool JsonStringField(std::string_view json, std::string_view key,
                     std::string& output) {
  std::string needle = "\"";
  needle += key;
  needle += "\":\"";
  const std::size_t begin = json.find(needle);
  if (begin == std::string_view::npos) {
    return false;
  }
  const std::size_t value_begin = begin + needle.size();
  const std::size_t end = json.find('"', value_begin);
  if (end == std::string_view::npos || end == value_begin || end - value_begin > 128U) {
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
    const bool accepted =
        (character >= 'a' && character <= 'z') ||
        (character >= 'A' && character <= 'Z') ||
        (character >= '0' && character <= '9') || character == '-' ||
        character == '_' || character == '.';
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

DWORD WINAPI WorkerMain(void*) noexcept {
  HANDLE pipe = ConnectToHost();
  if (pipe == INVALID_HANDLE_VALUE) {
    return 1;
  }

  if (!xar::bridge::WriteFrame(pipe, HelloFrame())) {
    CloseHandle(pipe);
    return 2;
  }

  std::uint64_t sequence = 0;
  ULONGLONG next_heartbeat = GetTickCount64();
  bool connected = true;
  while (connected && WaitForSingleObject(g_stop_event, 0) == WAIT_TIMEOUT) {
    const ULONGLONG now = GetTickCount64();
    if (now >= next_heartbeat) {
      ++sequence;
      connected = xar::bridge::WriteFrame(pipe, HeartbeatFrame(sequence));
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
      }
    }
    WaitForSingleObject(g_stop_event, 10);
  }

  CloseHandle(pipe);
  return 0;
}

BOOL StartFromEnvironment() noexcept {
  if (g_lifecycle.exchange(1) != 0) {
    return TRUE;
  }

  wchar_t pipe_name[kPipeNameCapacity]{};
  const DWORD length = GetEnvironmentVariableW(
      kPipeEnvironment, pipe_name, static_cast<DWORD>(kPipeNameCapacity));
  if (!IsPipeName(pipe_name, length)) {
    g_lifecycle.store(0);
    return FALSE;
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

void SignalStop() noexcept {
  if (g_stop_event != nullptr) {
    SetEvent(g_stop_event);
  }
}

}  // namespace

extern "C" __declspec(dllexport) const char* WINAPI
XarCk3BridgeIdentity() noexcept {
  return kIdentityJson;
}

extern "C" __declspec(dllexport) BOOL WINAPI XarCk3BridgeStart() noexcept {
  return StartFromEnvironment();
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
