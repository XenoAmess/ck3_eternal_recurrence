#include "xar_bridge/injector.hpp"

#include <windows.h>

#include <cstdint>
#include <filesystem>
#include <iostream>
#include <limits>
#include <string_view>

namespace {

int Fail(std::wstring_view message) {
  std::wcerr << L"FAIL: " << message << L'\n';
  return 1;
}

bool ParsePid(std::wstring_view text, DWORD& pid) noexcept {
  if (text.empty()) {
    return false;
  }
  std::uint64_t value = 0;
  for (const wchar_t character : text) {
    if (character < L'0' || character > L'9') {
      return false;
    }
    value = value * 10U + static_cast<unsigned>(character - L'0');
    if (value > static_cast<std::uint64_t>((std::numeric_limits<DWORD>::max)())) {
      return false;
    }
  }
  if (value == 0) {
    return false;
  }
  pid = static_cast<DWORD>(value);
  return true;
}

}  // namespace

int wmain(int argc, wchar_t** argv) {
  if (argc != 3) {
    return Fail(L"usage: xar_ck3_bridge_injector <pid> <dll-path>");
  }

  DWORD pid = 0;
  if (!ParsePid(argv[1], pid)) {
    return Fail(L"pid must be a positive decimal process id");
  }

  constexpr DWORD access = PROCESS_CREATE_THREAD | PROCESS_QUERY_INFORMATION |
                           PROCESS_VM_OPERATION | PROCESS_VM_WRITE |
                           PROCESS_VM_READ;
  HANDLE process = OpenProcess(access, FALSE, pid);
  if (process == nullptr) {
    std::wcerr << L"FAIL: OpenProcess error=" << GetLastError() << L'\n';
    return 2;
  }

  const auto result =
      xar::bridge::InjectLibrary(process, std::filesystem::path(argv[2]));
  CloseHandle(process);
  if (!result.succeeded) {
    std::wcerr << L"FAIL: InjectLibrary error=" << result.windows_error
               << L'\n';
    return 3;
  }

  std::wcout << L"PASS: injected pid=" << pid
             << L" remote_loadlibrary_exit=" << result.remote_exit_code
             << L'\n';
  return 0;
}
