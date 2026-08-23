#include "xar_bridge/injector.hpp"

#include <windows.h>
#include <tlhelp32.h>

#include <cstddef>
#include <cstdint>
#include <cwchar>
#include <filesystem>
#include <string>

namespace xar::bridge {
namespace {

static_assert(sizeof(void*) == 8, "the CK3 bridge injector is x64-only");

InjectionResult Failure(DWORD error) noexcept {
  return {false, error == ERROR_SUCCESS ? ERROR_GEN_FAILURE : error, 0};
}

AttachResult AttachFailure(DWORD error, DWORD load_exit = 0,
                           DWORD start_exit = 0) noexcept {
  return {false, error == ERROR_SUCCESS ? ERROR_GEN_FAILURE : error, load_exit,
          start_exit};
}

bool EqualOrdinalIgnoreCase(const wchar_t* left,
                            const wchar_t* right) noexcept {
  return CompareStringOrdinal(left, -1, right, -1, TRUE) == CSTR_EQUAL;
}

std::uintptr_t FindRemoteModule(DWORD pid, const std::wstring& filename,
                               DWORD& error) noexcept {
  for (int attempt = 0; attempt < 8; ++attempt) {
    HANDLE snapshot = CreateToolhelp32Snapshot(
        TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid);
    if (snapshot == INVALID_HANDLE_VALUE) {
      error = GetLastError();
      if (error == ERROR_BAD_LENGTH) {
        continue;
      }
      return 0;
    }

    MODULEENTRY32W entry{};
    entry.dwSize = sizeof(entry);
    if (!Module32FirstW(snapshot, &entry)) {
      error = GetLastError();
      CloseHandle(snapshot);
      if (error == ERROR_BAD_LENGTH) {
        continue;
      }
      return 0;
    }
    do {
      if (EqualOrdinalIgnoreCase(entry.szModule, filename.c_str())) {
        const auto base = reinterpret_cast<std::uintptr_t>(entry.modBaseAddr);
        CloseHandle(snapshot);
        error = ERROR_SUCCESS;
        return base;
      }
    } while (Module32NextW(snapshot, &entry));

    error = GetLastError();
    CloseHandle(snapshot);
    if (error != ERROR_NO_MORE_FILES && error != ERROR_SUCCESS) {
      return 0;
    }
    error = ERROR_MOD_NOT_FOUND;
    return 0;
  }
  error = ERROR_BAD_LENGTH;
  return 0;
}

std::uintptr_t ExportRva(const std::filesystem::path& dll_path,
                         const char* export_name, DWORD& error) noexcept {
  HMODULE local_module = LoadLibraryExW(
      dll_path.c_str(), nullptr, DONT_RESOLVE_DLL_REFERENCES);
  if (local_module == nullptr) {
    error = GetLastError();
    return 0;
  }
  const FARPROC local_export = GetProcAddress(local_module, export_name);
  if (local_export == nullptr) {
    error = GetLastError();
    FreeLibrary(local_module);
    return 0;
  }
  const auto module_address = reinterpret_cast<std::uintptr_t>(local_module);
  const auto export_address = reinterpret_cast<std::uintptr_t>(local_export);
  const std::uintptr_t rva = export_address - module_address;
  FreeLibrary(local_module);
  if (rva == 0) {
    error = ERROR_PROC_NOT_FOUND;
    return 0;
  }
  error = ERROR_SUCCESS;
  return rva;
}

InjectionResult RunRemoteThread(HANDLE process,
                                LPTHREAD_START_ROUTINE routine,
                                void* parameter, DWORD timeout_ms) noexcept {
  HANDLE remote_thread = CreateRemoteThread(process, nullptr, 0, routine,
                                            parameter, 0, nullptr);
  if (remote_thread == nullptr) {
    return Failure(GetLastError());
  }

  const DWORD wait_result = WaitForSingleObject(remote_thread, timeout_ms);
  if (wait_result != WAIT_OBJECT_0) {
    const DWORD error =
        wait_result == WAIT_TIMEOUT ? WAIT_TIMEOUT : GetLastError();
    CloseHandle(remote_thread);
    return Failure(error);
  }

  DWORD remote_exit_code = 0;
  if (!GetExitCodeThread(remote_thread, &remote_exit_code)) {
    const DWORD error = GetLastError();
    CloseHandle(remote_thread);
    return Failure(error);
  }
  CloseHandle(remote_thread);
  return {true, ERROR_SUCCESS, remote_exit_code};
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
  const InjectionResult thread_result =
      RunRemoteThread(process, start_routine, remote_path, timeout_ms);
  if (!thread_result.succeeded &&
      thread_result.windows_error == WAIT_TIMEOUT) {
    // The remote thread may still be reading its argument after a timeout, so
    // leave this tiny allocation owned by the target instead of invalidating it.
    return thread_result;
  }
  VirtualFreeEx(process, remote_path, 0, MEM_RELEASE);
  if (!thread_result.succeeded) {
    return thread_result;
  }
  if (thread_result.remote_exit_code == 0) {
    return Failure(ERROR_DLL_INIT_FAILED);
  }
  return thread_result;
}

AttachResult InjectLibraryAndStart(HANDLE process,
                                   const std::filesystem::path& dll_path,
                                   const wchar_t* pipe_name,
                                   DWORD timeout_ms) noexcept {
  if (process == nullptr || process == INVALID_HANDLE_VALUE) {
    return AttachFailure(ERROR_INVALID_HANDLE);
  }
  if (pipe_name == nullptr) {
    return AttachFailure(ERROR_INVALID_PARAMETER);
  }
  constexpr wchar_t prefix[] = L"\\\\.\\pipe\\";
  constexpr std::size_t prefix_length =
      (sizeof(prefix) / sizeof(prefix[0])) - 1U;
  std::size_t pipe_length = 0;
  while (pipe_length < 256U && pipe_name[pipe_length] != L'\0') {
    ++pipe_length;
  }
  if (pipe_length <= prefix_length || pipe_length >= 256U ||
      std::wcsncmp(pipe_name, prefix, prefix_length) != 0) {
    return AttachFailure(ERROR_INVALID_NAME);
  }

  std::error_code path_error;
  const auto absolute_path = std::filesystem::absolute(dll_path, path_error);
  if (path_error ||
      !std::filesystem::is_regular_file(absolute_path, path_error) ||
      path_error) {
    return AttachFailure(ERROR_FILE_NOT_FOUND);
  }

  const InjectionResult load_result =
      InjectLibrary(process, absolute_path, timeout_ms);
  if (!load_result.succeeded) {
    return AttachFailure(load_result.windows_error,
                         load_result.remote_exit_code);
  }

  const DWORD pid = GetProcessId(process);
  if (pid == 0) {
    return AttachFailure(GetLastError(), load_result.remote_exit_code);
  }
  DWORD resolve_error = ERROR_SUCCESS;
  const std::uintptr_t remote_module =
      FindRemoteModule(pid, absolute_path.filename().native(), resolve_error);
  if (remote_module == 0) {
    return AttachFailure(resolve_error, load_result.remote_exit_code);
  }
  const std::uintptr_t start_rva =
      ExportRva(absolute_path, "XarCk3BridgeStartWithPipe", resolve_error);
  if (start_rva == 0) {
    return AttachFailure(resolve_error, load_result.remote_exit_code);
  }

  const SIZE_T pipe_bytes = (pipe_length + 1U) * sizeof(wchar_t);
  void* remote_pipe = VirtualAllocEx(process, nullptr, pipe_bytes,
                                     MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
  if (remote_pipe == nullptr) {
    return AttachFailure(GetLastError(), load_result.remote_exit_code);
  }
  SIZE_T bytes_written = 0;
  if (!WriteProcessMemory(process, remote_pipe, pipe_name, pipe_bytes,
                          &bytes_written) ||
      bytes_written != pipe_bytes) {
    const DWORD error = GetLastError();
    VirtualFreeEx(process, remote_pipe, 0, MEM_RELEASE);
    return AttachFailure(error, load_result.remote_exit_code);
  }

#pragma warning(push)
#pragma warning(disable : 4191)
  const auto start_routine = reinterpret_cast<LPTHREAD_START_ROUTINE>(
      remote_module + start_rva);
#pragma warning(pop)
  const InjectionResult start_result =
      RunRemoteThread(process, start_routine, remote_pipe, timeout_ms);
  if (!start_result.succeeded &&
      start_result.windows_error == WAIT_TIMEOUT) {
    return AttachFailure(start_result.windows_error,
                         load_result.remote_exit_code,
                         start_result.remote_exit_code);
  }
  VirtualFreeEx(process, remote_pipe, 0, MEM_RELEASE);
  if (!start_result.succeeded) {
    return AttachFailure(start_result.windows_error,
                         load_result.remote_exit_code,
                         start_result.remote_exit_code);
  }
  if (start_result.remote_exit_code == 0) {
    return AttachFailure(ERROR_DLL_INIT_FAILED,
                         load_result.remote_exit_code,
                         start_result.remote_exit_code);
  }
  return {true, ERROR_SUCCESS, load_result.remote_exit_code,
          start_result.remote_exit_code};
}

}  // namespace xar::bridge
