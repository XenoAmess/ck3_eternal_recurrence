// Private exact-build debugger probe for the phase-two loader callback.
//
// This executable is deliberately not linked into xar_ck3_bridge.dll and does
// not change the public bridge ABI.  It launches one isolated CK3 process as a
// Windows debugger, places a one-shot breakpoint on the already-frozen
// callback call instruction, captures the paused register/vtable identity,
// restores the original byte, and terminates the isolated process.

#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>

#include <array>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

namespace {

constexpr std::uint64_t kCallbackCallRva = 0x3B9AB90;
constexpr std::uint64_t kCallbackSlotTargetRva = 0x3B9BA70;
constexpr std::array<std::uint64_t, 2> kCandidateVtableRvas = {
    0x4558700,
    0x4558770,
};
constexpr std::array<std::uint8_t, 3> kCallbackBytes = {0xFF, 0x50, 0x10};
constexpr std::uint64_t kExpectedExeSize = 95206008;
constexpr wchar_t kExpectedExeSha256[] =
    L"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

struct Options {
  std::filesystem::path exe;
  std::filesystem::path userdir;
  std::filesystem::path output;
  DWORD timeout_ms = 45000;
};

struct Capture {
  bool breakpoint_installed = false;
  bool callback_observed = false;
  bool original_byte_restored = false;
  bool process_terminated = false;
  DWORD pid = 0;
  DWORD thread_id = 0;
  std::uint64_t image_base = 0;
  std::uint64_t callback_address = 0;
  std::uint64_t node = 0;
  std::uint64_t receiver = 0;
  std::uint64_t receiver_from_node = 0;
  std::uint64_t vptr = 0;
  std::uint64_t slot_target = 0;
  std::uint64_t vptr_rva = 0;
  std::uint64_t slot_target_rva = 0;
  bool receiver_matches_node = false;
  bool vptr_matches_candidate = false;
  bool slot_target_matches = false;
  std::string result = "RED";
  std::string reason = "not-started";
  std::string exe_sha256;
  double elapsed_seconds = 0.0;
};

std::string Narrow(const std::wstring& value) {
  if (value.empty()) return {};
  const int size = WideCharToMultiByte(CP_UTF8, 0, value.data(),
                                       static_cast<int>(value.size()), nullptr,
                                       0, nullptr, nullptr);
  if (size <= 0) throw std::runtime_error("WideCharToMultiByte failed");
  std::string result(static_cast<std::size_t>(size), '\0');
  if (WideCharToMultiByte(CP_UTF8, 0, value.data(),
                          static_cast<int>(value.size()), result.data(), size,
                          nullptr, nullptr) != size) {
    throw std::runtime_error("WideCharToMultiByte failed");
  }
  return result;
}

std::string JsonEscape(const std::string& value) {
  std::ostringstream out;
  for (const unsigned char ch : value) {
    switch (ch) {
      case '\\': out << "\\\\"; break;
      case '"': out << "\\\""; break;
      case '\b': out << "\\b"; break;
      case '\f': out << "\\f"; break;
      case '\n': out << "\\n"; break;
      case '\r': out << "\\r"; break;
      case '\t': out << "\\t"; break;
      default:
        if (ch < 0x20) {
          out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
              << static_cast<int>(ch) << std::dec;
        } else {
          out << ch;
        }
    }
  }
  return out.str();
}

std::string Hex(std::uint64_t value) {
  std::ostringstream out;
  out << "0x" << std::uppercase << std::hex << value;
  return out.str();
}

std::wstring Quote(const std::wstring& value) {
  std::wstring quoted = L"\"";
  std::size_t slashes = 0;
  for (const wchar_t ch : value) {
    if (ch == L'\\') {
      ++slashes;
      continue;
    }
    if (ch == L'"') {
      quoted.append(slashes * 2 + 1, L'\\');
      quoted.push_back(L'"');
      slashes = 0;
      continue;
    }
    quoted.append(slashes, L'\\');
    slashes = 0;
    quoted.push_back(ch);
  }
  quoted.append(slashes * 2, L'\\');
  quoted.push_back(L'"');
  return quoted;
}

std::string Sha256(const std::filesystem::path& path) {
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  DWORD object_size = 0;
  DWORD hash_size = 0;
  DWORD result_size = 0;
  std::vector<std::uint8_t> object;
  std::vector<std::uint8_t> digest;
  auto check = [](NTSTATUS status, const char* operation) {
    if (status < 0) throw std::runtime_error(operation);
  };
  try {
    check(BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                      nullptr, 0),
          "BCryptOpenAlgorithmProvider failed");
    check(BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                            reinterpret_cast<PUCHAR>(&object_size),
                            sizeof(object_size), &result_size, 0),
          "BCryptGetProperty(object length) failed");
    check(BCryptGetProperty(algorithm, BCRYPT_HASH_LENGTH,
                            reinterpret_cast<PUCHAR>(&hash_size),
                            sizeof(hash_size), &result_size, 0),
          "BCryptGetProperty(hash length) failed");
    object.resize(object_size);
    digest.resize(hash_size);
    check(BCryptCreateHash(algorithm, &hash, object.data(), object_size,
                           nullptr, 0, 0),
          "BCryptCreateHash failed");
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("could not open executable for hash");
    // Keep the 1 MiB streaming buffer off the default 1 MiB Windows stack.
    std::vector<char> buffer(1024 * 1024);
    while (input) {
      input.read(buffer.data(), static_cast<std::streamsize>(buffer.size()));
      const auto count = input.gcount();
      if (count > 0) {
        check(BCryptHashData(
                  hash, reinterpret_cast<PUCHAR>(buffer.data()),
                  static_cast<ULONG>(count), 0),
              "BCryptHashData failed");
      }
    }
    check(BCryptFinishHash(hash, digest.data(), hash_size, 0),
          "BCryptFinishHash failed");
  } catch (...) {
    if (hash) BCryptDestroyHash(hash);
    if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0);
    throw;
  }
  BCryptDestroyHash(hash);
  BCryptCloseAlgorithmProvider(algorithm, 0);
  std::ostringstream out;
  out << std::uppercase << std::hex << std::setfill('0');
  for (const auto value : digest) out << std::setw(2) << int(value);
  return out.str();
}

template <typename T>
bool ReadRemote(HANDLE process, std::uint64_t address, T* value) {
  SIZE_T read = 0;
  return ReadProcessMemory(process, reinterpret_cast<const void*>(address),
                           value, sizeof(T), &read) && read == sizeof(T);
}

bool WriteBreakpointByte(HANDLE process, std::uint64_t address,
                         std::uint8_t value) {
  DWORD old_protection = 0;
  if (!VirtualProtectEx(process, reinterpret_cast<void*>(address), 1,
                        PAGE_EXECUTE_READWRITE, &old_protection)) {
    return false;
  }
  SIZE_T written = 0;
  const bool wrote =
      WriteProcessMemory(process, reinterpret_cast<void*>(address), &value, 1,
                         &written) &&
      written == 1 &&
      FlushInstructionCache(process, reinterpret_cast<void*>(address), 1);
  DWORD ignored = 0;
  const bool restored =
      VirtualProtectEx(process, reinterpret_cast<void*>(address), 1,
                       old_protection, &ignored) != FALSE;
  return wrote && restored;
}

HANDLE CreateKillOnCloseJob() {
  HANDLE job = CreateJobObjectW(nullptr, nullptr);
  if (!job) throw std::runtime_error("CreateJobObjectW failed");
  JOBOBJECT_EXTENDED_LIMIT_INFORMATION info{};
  info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
  if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, &info,
                               sizeof(info))) {
    CloseHandle(job);
    throw std::runtime_error("SetInformationJobObject failed");
  }
  return job;
}

Options ParseOptions(int argc, wchar_t** argv) {
  Options options;
  for (int index = 1; index < argc; ++index) {
    const std::wstring name = argv[index];
    auto next = [&]() -> std::wstring {
      if (++index >= argc) throw std::runtime_error("missing option value");
      return argv[index];
    };
    if (name == L"--exe") options.exe = next();
    else if (name == L"--userdir") options.userdir = next();
    else if (name == L"--output") options.output = next();
    else if (name == L"--timeout-ms") options.timeout_ms = std::stoul(next());
    else throw std::runtime_error("unknown option: " + Narrow(name));
  }
  if (options.exe.empty() || options.userdir.empty() || options.output.empty()) {
    throw std::runtime_error("--exe, --userdir, and --output are required");
  }
  if (options.timeout_ms < 1000 || options.timeout_ms > 60000) {
    throw std::runtime_error("--timeout-ms must be within [1000,60000]");
  }
  return options;
}

void WriteReport(const Options& options, const Capture& capture) {
  std::ofstream output(options.output, std::ios::binary | std::ios::trunc);
  if (!output) throw std::runtime_error("could not create output artifact");
  output << "{\n"
         << "  \"schema\": \"xar.phase2.loader_callback_private_debug_capture.v1\",\n"
         << "  \"result\": \"" << capture.result << "\",\n"
         << "  \"reason\": \"" << JsonEscape(capture.reason) << "\",\n"
         << "  \"exact_build\": {\n"
         << "    \"product_version\": \"1.19.0.6\",\n"
         << "    \"exe_sha256\": \"" << capture.exe_sha256 << "\",\n"
         << "    \"expected_exe_sha256\": \""
         << Narrow(kExpectedExeSha256) << "\",\n"
         << "    \"file_size\": " << kExpectedExeSize << "\n"
         << "  },\n"
         << "  \"launch\": {\n"
         << "    \"exe\": \""
         << JsonEscape(Narrow(options.exe.wstring())) << "\",\n"
         << "    \"isolated_userdir\": \""
         << JsonEscape(Narrow(options.userdir.wstring())) << "\",\n"
         << "    \"pid\": " << capture.pid << ",\n"
         << "    \"debug_only_this_process\": true,\n"
         << "    \"timeout_ms\": " << options.timeout_ms << "\n"
         << "  },\n"
         << "  \"paused_observation\": {\n"
         << "    \"callback_observed\": "
         << (capture.callback_observed ? "true" : "false") << ",\n"
         << "    \"breakpoint_installed\": "
         << (capture.breakpoint_installed ? "true" : "false") << ",\n"
         << "    \"thread_id\": " << capture.thread_id << ",\n"
         << "    \"image_base\": \"" << Hex(capture.image_base) << "\",\n"
         << "    \"callback_call_rva\": \"" << Hex(kCallbackCallRva)
         << "\",\n"
         << "    \"callback_address\": \""
         << Hex(capture.callback_address) << "\",\n"
         << "    \"node\": \"" << Hex(capture.node) << "\",\n"
         << "    \"receiver_rcx\": \"" << Hex(capture.receiver)
         << "\",\n"
         << "    \"receiver_from_node_plus_0x88\": \""
         << Hex(capture.receiver_from_node) << "\",\n"
         << "    \"receiver_matches_node\": "
         << (capture.receiver_matches_node ? "true" : "false") << ",\n"
         << "    \"vptr\": \"" << Hex(capture.vptr) << "\",\n"
         << "    \"vptr_rva\": \"" << Hex(capture.vptr_rva) << "\",\n"
         << "    \"vptr_matches_static_candidate\": "
         << (capture.vptr_matches_candidate ? "true" : "false") << ",\n"
         << "    \"slot_2_target\": \"" << Hex(capture.slot_target)
         << "\",\n"
         << "    \"slot_2_target_rva\": \""
         << Hex(capture.slot_target_rva) << "\",\n"
         << "    \"slot_2_target_matches_static_contract\": "
         << (capture.slot_target_matches ? "true" : "false") << "\n"
         << "  },\n"
         << "  \"cleanup\": {\n"
         << "    \"original_breakpoint_byte_restored\": "
         << (capture.original_byte_restored ? "true" : "false") << ",\n"
         << "    \"process_terminated\": "
         << (capture.process_terminated ? "true" : "false") << ",\n"
         << "    \"real_user_profile_targeted\": false\n"
         << "  },\n"
         << "  \"scope\": {\n"
         << "    \"private_test_only\": true,\n"
         << "    \"public_bridge_abi_changed\": false,\n"
         << "    \"production_detour_installed\": false,\n"
         << "    \"callback_return_observed\": false,\n"
         << "    \"readiness_promotion\": false\n"
         << "  },\n"
         << "  \"elapsed_seconds\": " << std::fixed << std::setprecision(3)
         << capture.elapsed_seconds << "\n"
         << "}\n";
}

Capture Run(const Options& options) {
  Capture capture;
  const auto started = std::chrono::steady_clock::now();
  PROCESS_INFORMATION process_info{};
  HANDLE job = nullptr;
  bool current_event_active = false;
  DEBUG_EVENT current_event{};
  auto finish_elapsed = [&]() {
    capture.elapsed_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
  };

  try {
    if (!std::filesystem::is_regular_file(options.exe)) {
      throw std::runtime_error("exact executable does not exist");
    }
    if (std::filesystem::file_size(options.exe) != kExpectedExeSize) {
      throw std::runtime_error("exact executable size mismatch");
    }
    capture.exe_sha256 = Sha256(options.exe);
    if (_wcsicmp(std::wstring(capture.exe_sha256.begin(),
                             capture.exe_sha256.end()).c_str(),
                 kExpectedExeSha256) != 0) {
      throw std::runtime_error("exact executable SHA-256 mismatch");
    }
    std::filesystem::create_directories(options.userdir);
    std::filesystem::create_directories(options.output.parent_path());

    job = CreateKillOnCloseJob();
    const std::wstring command =
        Quote(options.exe.wstring()) + L" -gdpr-compliant -userdir=" +
        Quote(options.userdir.wstring());
    std::vector<wchar_t> mutable_command(command.begin(), command.end());
    mutable_command.push_back(L'\0');
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    if (!CreateProcessW(options.exe.c_str(), mutable_command.data(), nullptr,
                        nullptr, FALSE,
                        DEBUG_ONLY_THIS_PROCESS | CREATE_NEW_PROCESS_GROUP,
                        nullptr, options.exe.parent_path().c_str(), &startup,
                        &process_info)) {
      throw std::runtime_error("CreateProcessW debug launch failed");
    }
    capture.pid = process_info.dwProcessId;
    if (!AssignProcessToJobObject(job, process_info.hProcess)) {
      throw std::runtime_error("AssignProcessToJobObject failed");
    }

    const auto deadline = started + std::chrono::milliseconds(options.timeout_ms);
    bool initial_breakpoint_seen = false;
    while (std::chrono::steady_clock::now() < deadline &&
           !capture.callback_observed) {
      const auto remaining = std::chrono::duration_cast<std::chrono::milliseconds>(
          deadline - std::chrono::steady_clock::now());
      const DWORD wait_ms = static_cast<DWORD>(
          std::max<std::int64_t>(1, std::min<std::int64_t>(500, remaining.count())));
      DEBUG_EVENT event{};
      if (!WaitForDebugEvent(&event, wait_ms)) {
        if (GetLastError() == ERROR_SEM_TIMEOUT) continue;
        throw std::runtime_error("WaitForDebugEvent failed");
      }
      current_event = event;
      current_event_active = true;
      DWORD continue_status = DBG_CONTINUE;

      if (event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT) {
        capture.image_base = reinterpret_cast<std::uint64_t>(
            event.u.CreateProcessInfo.lpBaseOfImage);
        capture.callback_address = capture.image_base + kCallbackCallRva;
        std::array<std::uint8_t, 3> actual{};
        SIZE_T read = 0;
        if (!ReadProcessMemory(process_info.hProcess,
                               reinterpret_cast<const void*>(
                                   capture.callback_address),
                               actual.data(), actual.size(), &read) ||
            read != actual.size() || actual != kCallbackBytes) {
          throw std::runtime_error("callback instruction bytes mismatch");
        }
        if (!WriteBreakpointByte(process_info.hProcess,
                                 capture.callback_address, 0xCC)) {
          throw std::runtime_error("could not install callback breakpoint");
        }
        capture.breakpoint_installed = true;
        if (event.u.CreateProcessInfo.hFile) {
          CloseHandle(event.u.CreateProcessInfo.hFile);
        }
      } else if (event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT) {
        if (event.u.LoadDll.hFile) CloseHandle(event.u.LoadDll.hFile);
      } else if (event.dwDebugEventCode == CREATE_THREAD_DEBUG_EVENT) {
        if (event.u.CreateThread.hThread) CloseHandle(event.u.CreateThread.hThread);
      } else if (event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT) {
        const auto& exception = event.u.Exception.ExceptionRecord;
        const auto address = reinterpret_cast<std::uint64_t>(
            exception.ExceptionAddress);
        if (exception.ExceptionCode == EXCEPTION_BREAKPOINT &&
            address == capture.callback_address) {
          HANDLE thread = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT |
                                         THREAD_QUERY_INFORMATION,
                                     FALSE, event.dwThreadId);
          if (!thread) throw std::runtime_error("OpenThread failed at callback");
          CONTEXT context{};
          context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
          const bool context_ok = GetThreadContext(thread, &context) != FALSE;
          CloseHandle(thread);
          if (!context_ok) {
            throw std::runtime_error("GetThreadContext failed at callback");
          }
          capture.thread_id = event.dwThreadId;
          capture.node = context.Rsi;
          capture.receiver = context.Rcx;
          capture.vptr = context.Rax;
          if (!ReadRemote(process_info.hProcess, capture.node + 0x88,
                          &capture.receiver_from_node)) {
            throw std::runtime_error("could not read node+0x88 receiver");
          }
          if (!ReadRemote(process_info.hProcess, capture.vptr + 0x10,
                          &capture.slot_target)) {
            throw std::runtime_error("could not read callback vtable slot 2");
          }
          capture.receiver_matches_node =
              capture.receiver != 0 &&
              capture.receiver == capture.receiver_from_node;
          capture.vptr_rva = capture.vptr - capture.image_base;
          capture.slot_target_rva = capture.slot_target - capture.image_base;
          for (const auto candidate : kCandidateVtableRvas) {
            capture.vptr_matches_candidate |= capture.vptr_rva == candidate;
          }
          capture.slot_target_matches =
              capture.slot_target_rva == kCallbackSlotTargetRva;
          if (!WriteBreakpointByte(process_info.hProcess,
                                   capture.callback_address,
                                   kCallbackBytes[0])) {
            throw std::runtime_error("could not restore callback byte");
          }
          std::uint8_t restored = 0;
          capture.original_byte_restored =
              ReadRemote(process_info.hProcess, capture.callback_address,
                         &restored) &&
              restored == kCallbackBytes[0];
          capture.callback_observed = true;
          capture.result =
              capture.receiver_matches_node && capture.vptr_matches_candidate &&
                      capture.slot_target_matches &&
                      capture.original_byte_restored
                  ? "GREEN"
                  : "RED";
          capture.reason = capture.result == "GREEN"
                               ? "runtime-vtable-identity-observed"
                               : "runtime-vtable-identity-mismatch";
        } else if (exception.ExceptionCode == EXCEPTION_BREAKPOINT &&
                   !initial_breakpoint_seen) {
          initial_breakpoint_seen = true;
        } else {
          continue_status = DBG_EXCEPTION_NOT_HANDLED;
        }
      }

      ContinueDebugEvent(event.dwProcessId, event.dwThreadId, continue_status);
      current_event_active = false;
    }

    if (!capture.callback_observed) {
      capture.result = "RED";
      capture.reason = "callback-breakpoint-timeout";
    }
  } catch (const std::exception& error) {
    capture.result = "RED";
    capture.reason = error.what();
  }

  if (process_info.hProcess) {
    if (capture.breakpoint_installed && !capture.original_byte_restored &&
        capture.callback_address != 0) {
      capture.original_byte_restored = WriteBreakpointByte(
          process_info.hProcess, capture.callback_address, kCallbackBytes[0]);
    }
    TerminateProcess(process_info.hProcess, 0);
    if (current_event_active) {
      ContinueDebugEvent(current_event.dwProcessId, current_event.dwThreadId,
                         DBG_CONTINUE);
      current_event_active = false;
    }
    // A debuggee cannot finish termination until its EXIT_PROCESS event is
    // drained.  Waiting on the process handle first would deadlock against
    // the debugger protocol and incorrectly report cleanup as unproven.
    const auto cleanup_deadline =
        std::chrono::steady_clock::now() + std::chrono::seconds(5);
    while (std::chrono::steady_clock::now() < cleanup_deadline) {
      DEBUG_EVENT event{};
      if (!WaitForDebugEvent(&event, 100)) {
        if (GetLastError() == ERROR_SEM_TIMEOUT) continue;
        break;
      }
      if (event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT &&
          event.u.LoadDll.hFile) {
        CloseHandle(event.u.LoadDll.hFile);
      } else if (event.dwDebugEventCode == CREATE_THREAD_DEBUG_EVENT &&
                 event.u.CreateThread.hThread) {
        CloseHandle(event.u.CreateThread.hThread);
      }
      const bool exited =
          event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT &&
          event.dwProcessId == process_info.dwProcessId;
      ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
      if (exited) break;
    }
    capture.process_terminated =
        WaitForSingleObject(process_info.hProcess, 0) == WAIT_OBJECT_0;
  }
  if (job) {
    CloseHandle(job);
    job = nullptr;
  }
  if (process_info.hThread) CloseHandle(process_info.hThread);
  if (process_info.hProcess) CloseHandle(process_info.hProcess);
  finish_elapsed();
  if (!capture.process_terminated && capture.pid != 0) {
    capture.result = "RED";
    capture.reason += "; cleanup-unproven";
  }
  return capture;
}

}  // namespace

int wmain(int argc, wchar_t** argv) {
  if (argc == 2 && std::wstring(argv[1]) == L"--self-test") {
    const bool ok = kCallbackCallRva == 0x3B9AB90 &&
                    kCallbackSlotTargetRva == 0x3B9BA70 &&
                    kCallbackBytes == std::array<std::uint8_t, 3>{0xFF, 0x50, 0x10};
    std::cout << (ok ? "phase2-private-debug-capture-self-test=GREEN\n"
                     : "phase2-private-debug-capture-self-test=RED\n");
    return ok ? 0 : 2;
  }
  try {
    const Options options = ParseOptions(argc, argv);
    const Capture capture = Run(options);
    WriteReport(options, capture);
    std::cout << "result=" << capture.result << " reason=" << capture.reason
              << " artifact=" << Narrow(options.output.wstring()) << "\n";
    return capture.result == "GREEN" ? 0 : 2;
  } catch (const std::exception& error) {
    std::cerr << "phase2 private debug capture failed: " << error.what() << "\n";
    return 3;
  }
}
