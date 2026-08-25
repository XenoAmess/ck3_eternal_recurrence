#pragma once

#include <windows.h>

#include <filesystem>

namespace xar::bridge {

struct InjectionResult {
  bool succeeded = false;
  DWORD windows_error = ERROR_SUCCESS;
  DWORD remote_exit_code = 0;
};

struct AttachResult {
  bool succeeded = false;
  DWORD windows_error = ERROR_SUCCESS;
  DWORD remote_loadlibrary_exit_code = 0;
  DWORD remote_start_exit_code = 0;
};

struct StartupInjectionResult {
  bool succeeded = false;
  DWORD windows_error = ERROR_SUCCESS;
  DWORD remote_loadlibrary_exit_code = 0;
  DWORD remote_prepare_exit_code = 0;
};

// Loads one x64 DLL into an already-created x64 process. The caller owns the
// process handle; it must grant PROCESS_CREATE_THREAD, PROCESS_QUERY_INFORMATION,
// PROCESS_VM_OPERATION, PROCESS_VM_WRITE, and PROCESS_VM_READ.
InjectionResult InjectLibrary(
    HANDLE process, const std::filesystem::path& dll_path,
    DWORD timeout_ms = 15'000) noexcept;

// Loads the bridge into a newly-created process whose primary thread is still
// suspended, then invokes its exact-build startup preparation export before
// the caller resumes that primary thread. Running-process attach must use
// InjectLibraryAndStart instead and never installs startup-only containment.
// timeout_ms is one shared budget for both remote calls.
StartupInjectionResult InjectLibraryAndPrepareStartup(
    HANDLE process, const std::filesystem::path& dll_path,
    DWORD timeout_ms = 15'000) noexcept;

// Loads the bridge and explicitly starts it with a named pipe. Unlike the
// environment-driven entry point, this works for a process that was already
// running before the daemon selected its pipe name.
AttachResult InjectLibraryAndStart(
    HANDLE process, const std::filesystem::path& dll_path,
    const wchar_t* pipe_name, DWORD timeout_ms = 15'000) noexcept;

}  // namespace xar::bridge
