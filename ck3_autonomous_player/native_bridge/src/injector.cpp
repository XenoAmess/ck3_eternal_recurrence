#include "xar_bridge/injector.hpp"

#include <windows.h>

#include <cstddef>
#include <filesystem>
#include <string>

namespace xar::bridge {
namespace {

static_assert(sizeof(void*) == 8, "the CK3 bridge injector is x64-only");

InjectionResult Failure(DWORD error) noexcept {
  return {false, error == ERROR_SUCCESS ? ERROR_GEN_FAILURE : error, 0};
}

}  // namespace

InjectionResult InjectLibrary(HANDLE process,
                              const std::filesystem::path& dll_path,
                              DWORD timeout_ms) noexcept {
  if (process == nullptr || process == INVALID_HANDLE_VALUE) {
    return Failure(ERROR_INVALID_HANDLE);
  }

  std::error_code path_error;
  const auto absolute_path = std::filesystem::absolute(dll_path, path_error);
  if (path_error || !std::filesystem::is_regular_file(absolute_path, path_error) ||
      path_error) {
    return Failure(ERROR_FILE_NOT_FOUND);
  }

  const std::wstring path = absolute_path.native();
  if (path.empty()) {
    return Failure(ERROR_INVALID_PARAMETER);
  }
  const SIZE_T path_bytes = (path.size() + 1U) * sizeof(wchar_t);

  void* remote_path =
      VirtualAllocEx(process, nullptr, path_bytes, MEM_COMMIT | MEM_RESERVE,
                     PAGE_READWRITE);
  if (remote_path == nullptr) {
    return Failure(GetLastError());
  }

  SIZE_T bytes_written = 0;
  if (!WriteProcessMemory(process, remote_path, path.c_str(), path_bytes,
                          &bytes_written) ||
      bytes_written != path_bytes) {
    const DWORD error = GetLastError();
    VirtualFreeEx(process, remote_path, 0, MEM_RELEASE);
    return Failure(error);
  }

  HMODULE kernel32 = GetModuleHandleW(L"kernel32.dll");
  if (kernel32 == nullptr) {
    const DWORD error = GetLastError();
    VirtualFreeEx(process, remote_path, 0, MEM_RELEASE);
    return Failure(error);
  }
  const auto load_library = GetProcAddress(kernel32, "LoadLibraryW");
  if (load_library == nullptr) {
    const DWORD error = GetLastError();
    VirtualFreeEx(process, remote_path, 0, MEM_RELEASE);
    return Failure(error);
  }

#pragma warning(push)
#pragma warning(disable : 4191)
  const auto start_routine =
      reinterpret_cast<LPTHREAD_START_ROUTINE>(load_library);
#pragma warning(pop)
  HANDLE remote_thread = CreateRemoteThread(process, nullptr, 0, start_routine,
                                            remote_path, 0, nullptr);
  if (remote_thread == nullptr) {
    const DWORD error = GetLastError();
    VirtualFreeEx(process, remote_path, 0, MEM_RELEASE);
    return Failure(error);
  }

  const DWORD wait_result = WaitForSingleObject(remote_thread, timeout_ms);
  if (wait_result != WAIT_OBJECT_0) {
    const DWORD error =
        wait_result == WAIT_TIMEOUT ? WAIT_TIMEOUT : GetLastError();
    CloseHandle(remote_thread);
    // The remote thread may still be reading its argument after a timeout, so
    // leave this tiny allocation owned by the target instead of invalidating it.
    return Failure(error);
  }

  DWORD remote_exit_code = 0;
  if (!GetExitCodeThread(remote_thread, &remote_exit_code)) {
    const DWORD error = GetLastError();
    CloseHandle(remote_thread);
    VirtualFreeEx(process, remote_path, 0, MEM_RELEASE);
    return Failure(error);
  }
  CloseHandle(remote_thread);
  VirtualFreeEx(process, remote_path, 0, MEM_RELEASE);

  if (remote_exit_code == 0) {
    return Failure(ERROR_DLL_INIT_FAILED);
  }
  return {true, ERROR_SUCCESS, remote_exit_code};
}

}  // namespace xar::bridge
