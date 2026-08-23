#include "xar_bridge/protocol.hpp"

#include <windows.h>

#include <chrono>
#include <filesystem>
#include <future>
#include <iostream>
#include <string>
#include <string_view>
#include <thread>

namespace {

constexpr wchar_t kPipeEnvironment[] = L"XAR_CK3_BRIDGE_PIPE";

std::wstring PipeName() {
  return L"\\\\.\\pipe\\xar_ck3_bridge_injection_" +
         std::to_wstring(GetCurrentProcessId()) + L"_" +
         std::to_wstring(GetTickCount64());
}

bool Has(std::string_view payload, std::string_view fragment) {
  return payload.find(fragment) != std::string_view::npos;
}

int Fail(std::string_view message) {
  std::cerr << "FAIL: " << message << '\n';
  return 1;
}

std::wstring Quoted(const std::filesystem::path &path) {
  return L"\"" + path.native() + L"\"";
}

struct SavedEnvironment {
  bool existed = false;
  std::wstring value;
};

SavedEnvironment SavePipeEnvironment() {
  SavedEnvironment saved;
  const DWORD required = GetEnvironmentVariableW(kPipeEnvironment, nullptr, 0);
  if (required == 0) {
    return saved;
  }
  saved.value.resize(required);
  const DWORD copied =
      GetEnvironmentVariableW(kPipeEnvironment, saved.value.data(),
                              static_cast<DWORD>(saved.value.size()));
  if (copied != 0 && copied < saved.value.size()) {
    saved.value.resize(copied);
    saved.existed = true;
  } else {
    saved.value.clear();
  }
  return saved;
}

void RestorePipeEnvironment(const SavedEnvironment &saved) {
  SetEnvironmentVariableW(kPipeEnvironment,
                          saved.existed ? saved.value.c_str() : nullptr);
}

bool StartSuspendedTarget(const std::filesystem::path &target_path,
                          const std::wstring &pipe_name,
                          PROCESS_INFORMATION &target) {
  const SavedEnvironment saved = SavePipeEnvironment();
  if (!SetEnvironmentVariableW(kPipeEnvironment, pipe_name.c_str())) {
    return false;
  }

  STARTUPINFOW startup{};
  startup.cb = sizeof(startup);
  std::wstring command_line = Quoted(target_path);
  const BOOL created =
      CreateProcessW(target_path.c_str(), command_line.data(), nullptr, nullptr,
                     FALSE, CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT,
                     nullptr, nullptr, &startup, &target);
  RestorePipeEnvironment(saved);
  return created == TRUE;
}

bool RunInjector(const std::filesystem::path &injector_path, DWORD target_pid,
                 const std::filesystem::path &dll_path, DWORD &exit_code) {
  std::wstring command_line = Quoted(injector_path);
  command_line += L" ";
  command_line += std::to_wstring(target_pid);
  command_line += L" ";
  command_line += Quoted(dll_path);

  STARTUPINFOW startup{};
  startup.cb = sizeof(startup);
  PROCESS_INFORMATION injector{};
  if (!CreateProcessW(injector_path.c_str(), command_line.data(), nullptr,
                      nullptr, FALSE, 0, nullptr, nullptr, &startup,
                      &injector)) {
    return false;
  }
  CloseHandle(injector.hThread);

  const DWORD wait_result = WaitForSingleObject(injector.hProcess, 20'000);
  if (wait_result != WAIT_OBJECT_0) {
    TerminateProcess(injector.hProcess, 120);
    WaitForSingleObject(injector.hProcess, 5'000);
    CloseHandle(injector.hProcess);
    SetLastError(wait_result == WAIT_TIMEOUT ? WAIT_TIMEOUT : GetLastError());
    return false;
  }
  const BOOL read_exit = GetExitCodeProcess(injector.hProcess, &exit_code);
  CloseHandle(injector.hProcess);
  return read_exit == TRUE;
}

void TerminateTarget(PROCESS_INFORMATION &target) {
  if (target.hProcess != nullptr) {
    DWORD exit_code = 0;
    if (GetExitCodeProcess(target.hProcess, &exit_code) &&
        exit_code == STILL_ACTIVE) {
      TerminateProcess(target.hProcess, 121);
      WaitForSingleObject(target.hProcess, 5'000);
    }
  }
}

void CloseTarget(PROCESS_INFORMATION &target) {
  if (target.hThread != nullptr) {
    CloseHandle(target.hThread);
    target.hThread = nullptr;
  }
  if (target.hProcess != nullptr) {
    CloseHandle(target.hProcess);
    target.hProcess = nullptr;
  }
}

bool ConnectWithinFiveSeconds(HANDLE pipe) {
  std::promise<DWORD> connected_promise;
  auto connected_future = connected_promise.get_future();
  std::thread connector([pipe,
                         promise = std::move(connected_promise)]() mutable {
    if (ConnectNamedPipe(pipe, nullptr)) {
      promise.set_value(ERROR_SUCCESS);
      return;
    }
    const DWORD error = GetLastError();
    promise.set_value(error == ERROR_PIPE_CONNECTED ? ERROR_SUCCESS : error);
  });
  if (connected_future.wait_for(std::chrono::seconds(5)) !=
      std::future_status::ready) {
    CancelSynchronousIo(connector.native_handle());
    connector.join();
    return false;
  }
  const DWORD error = connected_future.get();
  connector.join();
  return error == ERROR_SUCCESS;
}

} // namespace

int wmain(int argc, wchar_t **argv) {
  if (argc != 4) {
    return Fail(
        "usage: xar_ck3_bridge_host <dll-path> <injector-path> <target-path>");
  }

  const std::filesystem::path dll_path = std::filesystem::absolute(argv[1]);
  const std::filesystem::path injector_path =
      std::filesystem::absolute(argv[2]);
  const std::filesystem::path target_path = std::filesystem::absolute(argv[3]);
  if (!std::filesystem::is_regular_file(dll_path) ||
      !std::filesystem::is_regular_file(injector_path) ||
      !std::filesystem::is_regular_file(target_path)) {
    return Fail("DLL, injector, or target executable does not exist");
  }

  const std::wstring pipe_name = PipeName();
  HANDLE pipe =
      CreateNamedPipeW(pipe_name.c_str(), PIPE_ACCESS_DUPLEX,
                       PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT, 1,
                       xar::bridge::kMaximumFrameBytes + 4U,
                       xar::bridge::kMaximumFrameBytes + 4U, 0, nullptr);
  if (pipe == INVALID_HANDLE_VALUE) {
    return Fail("CreateNamedPipeW failed");
  }

  PROCESS_INFORMATION target{};
  if (!StartSuspendedTarget(target_path, pipe_name, target)) {
    CloseHandle(pipe);
    return Fail("could not create the offline target suspended");
  }

  std::promise<DWORD> connected_promise;
  auto connected_future = connected_promise.get_future();
  std::thread connector([pipe,
                         promise = std::move(connected_promise)]() mutable {
    if (ConnectNamedPipe(pipe, nullptr)) {
      promise.set_value(ERROR_SUCCESS);
      return;
    }
    const DWORD error = GetLastError();
    promise.set_value(error == ERROR_PIPE_CONNECTED ? ERROR_SUCCESS : error);
  });

  DWORD injector_exit = 0;
  if (!RunInjector(injector_path, target.dwProcessId, dll_path,
                   injector_exit) ||
      injector_exit != 0) {
    CancelSynchronousIo(connector.native_handle());
    connector.join();
    TerminateTarget(target);
    CloseTarget(target);
    CloseHandle(pipe);
    return Fail("injector process failed");
  }

  if (connected_future.wait_for(std::chrono::seconds(5)) !=
      std::future_status::ready) {
    CancelSynchronousIo(connector.native_handle());
    connector.join();
    TerminateTarget(target);
    CloseTarget(target);
    CloseHandle(pipe);
    return Fail("injected bridge did not connect within five seconds");
  }
  const DWORD connect_error = connected_future.get();
  connector.join();
  if (connect_error != ERROR_SUCCESS) {
    TerminateTarget(target);
    CloseTarget(target);
    CloseHandle(pipe);
    return Fail("ConnectNamedPipe failed");
  }

  bool hello = false;
  bool heartbeat = false;
  bool pong = false;
  bool ping_sent = false;
  DWORD bridge_pid = 0;
  const auto deadline =
      std::chrono::steady_clock::now() + std::chrono::seconds(5);
  while (std::chrono::steady_clock::now() < deadline &&
         !(hello && heartbeat && pong)) {
    const auto frame = xar::bridge::TryReadFrame(pipe);
    if (frame.status == xar::bridge::ReadStatus::closed ||
        frame.status == xar::bridge::ReadStatus::invalid) {
      break;
    }
    if (frame.status == xar::bridge::ReadStatus::none) {
      std::this_thread::sleep_for(std::chrono::milliseconds(5));
      continue;
    }
    if (Has(frame.payload, "\"type\":\"hello\"") &&
        Has(frame.payload, "\"protocol_version\":1") &&
        Has(frame.payload, "\"bridge.heartbeat\"") &&
        Has(frame.payload, "\"expected_ck3_version\":\"1.19.0.6\"") &&
        Has(frame.payload, "\"ck3_build_match\":false") &&
        !Has(frame.payload, "\"game.state.snapshot\"") &&
        !Has(frame.payload, "\"game.command.pause-map\"") &&
        !Has(frame.payload, "\"game.command.set-speed-")) {
      hello = true;
      bridge_pid = target.dwProcessId;
      const std::string expected_pid =
          "\"pid\":" + std::to_string(target.dwProcessId);
      if (!Has(frame.payload, expected_pid)) {
        hello = false;
      }
    } else if (Has(frame.payload, "\"type\":\"heartbeat\"") &&
               Has(frame.payload, "\"sequence\":")) {
      heartbeat = true;
    } else if (Has(frame.payload, "\"type\":\"pong\"") &&
               Has(frame.payload, "\"request_id\":\"suspended-injection-1\"")) {
      pong = true;
    }
    if (hello && !ping_sent) {
      ping_sent = xar::bridge::WriteFrame(
          pipe, "{\"type\":\"ping\",\"protocol_version\":1,"
                "\"request_id\":\"suspended-injection-1\"}");
    }
  }

  if (!hello || !heartbeat || !pong || !ping_sent) {
    TerminateTarget(target);
    CloseTarget(target);
    DisconnectNamedPipe(pipe);
    CloseHandle(pipe);
    return Fail("injected hello/heartbeat/ping/pong exchange was incomplete");
  }

  // Dropping an MCP daemon must not require reinjecting or restarting CK3.
  // Recreate the server under the same name and require the already-loaded
  // DLL to establish a fresh hello/heartbeat/ping/pong exchange.
  DisconnectNamedPipe(pipe);
  CloseHandle(pipe);
  pipe = CreateNamedPipeW(pipe_name.c_str(), PIPE_ACCESS_DUPLEX,
                          PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT, 1,
                          xar::bridge::kMaximumFrameBytes + 4U,
                          xar::bridge::kMaximumFrameBytes + 4U, 0, nullptr);
  if (pipe == INVALID_HANDLE_VALUE || !ConnectWithinFiveSeconds(pipe)) {
    TerminateTarget(target);
    CloseTarget(target);
    if (pipe != INVALID_HANDLE_VALUE) {
      CloseHandle(pipe);
    }
    return Fail("injected bridge did not reconnect to a replacement server");
  }

  bool reconnect_hello = false;
  bool reconnect_heartbeat = false;
  bool reconnect_pong = false;
  bool reconnect_ping_sent = false;
  const auto reconnect_deadline =
      std::chrono::steady_clock::now() + std::chrono::seconds(5);
  while (std::chrono::steady_clock::now() < reconnect_deadline &&
         !(reconnect_hello && reconnect_heartbeat && reconnect_pong)) {
    const auto frame = xar::bridge::TryReadFrame(pipe);
    if (frame.status == xar::bridge::ReadStatus::closed ||
        frame.status == xar::bridge::ReadStatus::invalid) {
      break;
    }
    if (frame.status == xar::bridge::ReadStatus::none) {
      std::this_thread::sleep_for(std::chrono::milliseconds(5));
      continue;
    }
    if (Has(frame.payload, "\"type\":\"hello\"") &&
        Has(frame.payload, "\"protocol_version\":1")) {
      reconnect_hello = true;
    } else if (Has(frame.payload, "\"type\":\"heartbeat\"") &&
               Has(frame.payload, "\"sequence\":")) {
      reconnect_heartbeat = true;
    } else if (Has(frame.payload, "\"type\":\"pong\"") &&
               Has(frame.payload,
                   "\"request_id\":\"suspended-injection-reconnect\"")) {
      reconnect_pong = true;
    }
    if (reconnect_hello && !reconnect_ping_sent) {
      reconnect_ping_sent = xar::bridge::WriteFrame(
          pipe, "{\"type\":\"ping\",\"protocol_version\":1,"
                "\"request_id\":\"suspended-injection-reconnect\"}");
    }
  }
  if (!reconnect_hello || !reconnect_heartbeat || !reconnect_pong ||
      !reconnect_ping_sent) {
    TerminateTarget(target);
    CloseTarget(target);
    DisconnectNamedPipe(pipe);
    CloseHandle(pipe);
    return Fail("reconnected bridge exchange was incomplete");
  }

  if (ResumeThread(target.hThread) == static_cast<DWORD>(-1)) {
    TerminateTarget(target);
    CloseTarget(target);
    DisconnectNamedPipe(pipe);
    CloseHandle(pipe);
    return Fail("could not resume the offline target primary thread");
  }
  if (WaitForSingleObject(target.hProcess, 5'000) != WAIT_OBJECT_0) {
    TerminateTarget(target);
    CloseTarget(target);
    DisconnectNamedPipe(pipe);
    CloseHandle(pipe);
    return Fail("offline target did not exit after resume");
  }
  DWORD target_exit = 1;
  GetExitCodeProcess(target.hProcess, &target_exit);
  CloseTarget(target);
  DisconnectNamedPipe(pipe);
  CloseHandle(pipe);
  if (target_exit != 0) {
    return Fail("offline target returned a non-zero exit code");
  }

  std::cout << "PASS: suspended=1 injected=1 protocol=1 hello=1 heartbeat=1 "
               "pong=1 reconnected=1 resumed=1 target_exit=0 bridge_pid="
            << bridge_pid << '\n';
  return 0;
}
