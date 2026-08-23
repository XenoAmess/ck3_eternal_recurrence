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

std::wstring UniqueName(std::wstring_view prefix) {
  std::wstring result(prefix);
  result += std::to_wstring(GetCurrentProcessId());
  result += L"_";
  result += std::to_wstring(GetTickCount64());
  return result;
}

bool Has(std::string_view payload, std::string_view fragment) {
  return payload.find(fragment) != std::string_view::npos;
}

int Fail(std::string_view message) {
  std::cerr << "FAIL: " << message << '\n';
  return 1;
}

std::wstring Quoted(std::wstring_view value) {
  return L"\"" + std::wstring(value) + L"\"";
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
  const DWORD copied = GetEnvironmentVariableW(
      kPipeEnvironment, saved.value.data(),
      static_cast<DWORD>(saved.value.size()));
  if (copied != 0 && copied < saved.value.size()) {
    saved.value.resize(copied);
    saved.existed = true;
  } else {
    saved.value.clear();
  }
  return saved;
}

void RestorePipeEnvironment(const SavedEnvironment& saved) {
  SetEnvironmentVariableW(kPipeEnvironment,
                          saved.existed ? saved.value.c_str() : nullptr);
}

bool StartRunningTargetWithoutPipe(const std::filesystem::path& target_path,
                                   std::wstring_view event_name,
                                   PROCESS_INFORMATION& target) {
  const SavedEnvironment saved = SavePipeEnvironment();
  SetEnvironmentVariableW(kPipeEnvironment, nullptr);

  STARTUPINFOW startup{};
  startup.cb = sizeof(startup);
  std::wstring command_line = Quoted(target_path.native());
  command_line += L" --wait-event ";
  command_line += Quoted(event_name);
  const BOOL created =
      CreateProcessW(target_path.c_str(), command_line.data(), nullptr, nullptr,
                     FALSE, CREATE_UNICODE_ENVIRONMENT, nullptr, nullptr,
                     &startup, &target);
  RestorePipeEnvironment(saved);
  return created == TRUE;
}

bool RunExplicitPipeInjector(const std::filesystem::path& injector_path,
                             std::wstring_view pipe_name, DWORD target_pid,
                             const std::filesystem::path& dll_path,
                             DWORD& exit_code) {
  std::wstring command_line = Quoted(injector_path.native());
  command_line += L" --pipe ";
  command_line += Quoted(pipe_name);
  command_line += L" ";
  command_line += std::to_wstring(target_pid);
  command_line += L" ";
  command_line += Quoted(dll_path.native());

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

void TerminateTarget(PROCESS_INFORMATION& target) {
  if (target.hProcess == nullptr) {
    return;
  }
  DWORD exit_code = 0;
  if (GetExitCodeProcess(target.hProcess, &exit_code) &&
      exit_code == STILL_ACTIVE) {
    TerminateProcess(target.hProcess, 121);
    WaitForSingleObject(target.hProcess, 5'000);
  }
}

void CloseTarget(PROCESS_INFORMATION& target) {
  if (target.hThread != nullptr) {
    CloseHandle(target.hThread);
    target.hThread = nullptr;
  }
  if (target.hProcess != nullptr) {
    CloseHandle(target.hProcess);
    target.hProcess = nullptr;
  }
}

}  // namespace

int wmain(int argc, wchar_t** argv) {
  if (argc != 4) {
    return Fail("usage: xar_ck3_bridge_attach_host <dll-path> "
                "<injector-path> <target-path>");
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

  const std::wstring pipe_name =
      UniqueName(L"\\\\.\\pipe\\xar_ck3_bridge_attach_");
  const std::wstring event_name =
      UniqueName(L"Local\\xar_ck3_bridge_attach_target_");
  HANDLE pipe = CreateNamedPipeW(
      pipe_name.c_str(), PIPE_ACCESS_DUPLEX,
      PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT, 1,
      xar::bridge::kMaximumFrameBytes + 4U,
      xar::bridge::kMaximumFrameBytes + 4U, 0, nullptr);
  if (pipe == INVALID_HANDLE_VALUE) {
    return Fail("CreateNamedPipeW failed");
  }
  HANDLE target_event =
      CreateEventW(nullptr, TRUE, FALSE, event_name.c_str());
  if (target_event == nullptr) {
    CloseHandle(pipe);
    return Fail("CreateEventW failed");
  }

  PROCESS_INFORMATION target{};
  if (!StartRunningTargetWithoutPipe(target_path, event_name, target)) {
    CloseHandle(target_event);
    CloseHandle(pipe);
    return Fail("could not start the offline target without pipe environment");
  }
  if (WaitForSingleObject(target.hProcess, 100) != WAIT_TIMEOUT) {
    CloseTarget(target);
    CloseHandle(target_event);
    CloseHandle(pipe);
    return Fail("offline target was not running before attach");
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
  if (!RunExplicitPipeInjector(injector_path, pipe_name, target.dwProcessId,
                               dll_path, injector_exit) ||
      injector_exit != 0) {
    CancelSynchronousIo(connector.native_handle());
    connector.join();
    TerminateTarget(target);
    CloseTarget(target);
    CloseHandle(target_event);
    CloseHandle(pipe);
    return Fail("explicit-pipe injector process failed");
  }
  if (connected_future.wait_for(std::chrono::seconds(5)) !=
      std::future_status::ready) {
    CancelSynchronousIo(connector.native_handle());
    connector.join();
    TerminateTarget(target);
    CloseTarget(target);
    CloseHandle(target_event);
    CloseHandle(pipe);
    return Fail("attached bridge did not connect within five seconds");
  }
  const DWORD connect_error = connected_future.get();
  connector.join();
  if (connect_error != ERROR_SUCCESS) {
    TerminateTarget(target);
    CloseTarget(target);
    CloseHandle(target_event);
    CloseHandle(pipe);
    return Fail("ConnectNamedPipe failed");
  }

  bool hello = false;
  bool heartbeat = false;
  bool pong = false;
  bool ping_sent = false;
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
        Has(frame.payload, "\"ck3_build_match\":false")) {
      const std::string expected_pid =
          "\"pid\":" + std::to_string(target.dwProcessId);
      hello = Has(frame.payload, expected_pid);
    } else if (Has(frame.payload, "\"type\":\"heartbeat\"") &&
               Has(frame.payload, "\"sequence\":")) {
      heartbeat = true;
    } else if (Has(frame.payload, "\"type\":\"pong\"") &&
               Has(frame.payload,
                   "\"request_id\":\"running-explicit-pipe-1\"")) {
      pong = true;
    }
    if (hello && !ping_sent) {
      ping_sent = xar::bridge::WriteFrame(
          pipe, "{\"type\":\"ping\",\"protocol_version\":1,"
                "\"request_id\":\"running-explicit-pipe-1\"}");
    }
  }

  if (!hello || !heartbeat || !pong || !ping_sent) {
    TerminateTarget(target);
    CloseTarget(target);
    DisconnectNamedPipe(pipe);
    CloseHandle(target_event);
    CloseHandle(pipe);
    return Fail("attached hello/heartbeat/ping/pong exchange was incomplete");
  }

  SetEvent(target_event);
  if (WaitForSingleObject(target.hProcess, 5'000) != WAIT_OBJECT_0) {
    TerminateTarget(target);
    CloseTarget(target);
    DisconnectNamedPipe(pipe);
    CloseHandle(target_event);
    CloseHandle(pipe);
    return Fail("offline target did not exit after the test event");
  }
  DWORD target_exit = 1;
  GetExitCodeProcess(target.hProcess, &target_exit);
  CloseTarget(target);
  DisconnectNamedPipe(pipe);
  CloseHandle(target_event);
  CloseHandle(pipe);
  if (target_exit != 0) {
    return Fail("offline target returned a non-zero exit code");
  }

  std::cout << "PASS: already_running=1 inherited_pipe=0 explicit_pipe=1 "
               "injected=1 hello=1 heartbeat=1 pong=1 target_exit=0\n";
  return 0;
}
