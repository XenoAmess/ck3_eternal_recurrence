#pragma once

#include <windows.h>

#include <filesystem>

namespace xar::bridge {

struct InjectionResult {
  bool succeeded = false;
  DWORD windows_error = ERROR_SUCCESS;
  DWORD remote_exit_code = 0;
};

// Loads one x64 DLL into an already-created x64 process. The caller owns the
// process handle; it must grant PROCESS_CREATE_THREAD, PROCESS_QUERY_INFORMATION,
// PROCESS_VM_OPERATION, PROCESS_VM_WRITE, and PROCESS_VM_READ.
InjectionResult InjectLibrary(
    HANDLE process, const std::filesystem::path& dll_path,
    DWORD timeout_ms = 15'000) noexcept;

}  // namespace xar::bridge
