// Experimental CK3 1.19.0.6 War31 two-point observer. Explicit PID only.
// Hardware execute breakpoints change debugger/thread context, but never patch
// CK3 code or submit a gameplay action. Do not run without a coordinated,
// independently authorized action and an isolated attempt directory.
#include <windows.h>
#include <tlhelp32.h>

#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr std::array<DWORD64, 2> kSiteRvas{0x2E9F746, 0x2EC4410};
constexpr std::array<std::uint8_t, 3> kSetupBytes{0x48, 0x8B, 0xF0};
constexpr std::array<std::uint8_t, 7> kResolveBytes{
    0x83, 0xB8, 0x68, 0x02, 0x00, 0x00, 0x17};
constexpr DWORD kResumeFlag = 0x10000;
constexpr DWORD kWaitSliceMs = 100;
constexpr DWORD kBreakCleanupWaitMs = 5000;
std::atomic<bool> g_stop_requested{false};

BOOL WINAPI OnConsoleControl(DWORD control) {
  if (control == CTRL_C_EVENT || control == CTRL_BREAK_EVENT ||
      control == CTRL_CLOSE_EVENT) {
    g_stop_requested.store(true, std::memory_order_release);
    return TRUE;
  }
  return FALSE;
}

std::string Hex(std::uint64_t value) {
  std::ostringstream stream;
  stream << "0x" << std::uppercase << std::hex << value;
  return stream.str();
}

bool ReadExact(HANDLE process, DWORD64 address, void *dest, std::size_t size) {
  SIZE_T read = 0;
  return address != 0 && ReadProcessMemory(
      process, reinterpret_cast<const void *>(address), dest, size, &read) &&
      read == size;
}

bool ExactAnchorsAt(HANDLE process, const std::array<DWORD64, 2> &sites) {
  std::array<std::uint8_t, kSetupBytes.size()> setup{};
  std::array<std::uint8_t, kResolveBytes.size()> resolve{};
  return ReadExact(process, sites[0], setup.data(), setup.size()) &&
         ReadExact(process, sites[1], resolve.data(), resolve.size()) &&
         setup == kSetupBytes && resolve == kResolveBytes;
}

DWORD64 ModuleBase(DWORD pid) {
  HANDLE snapshot = CreateToolhelp32Snapshot(
      TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid);
  if (snapshot == INVALID_HANDLE_VALUE) return 0;
  MODULEENTRY32W entry{};
  entry.dwSize = sizeof(entry);
  DWORD64 base = 0;
  if (Module32FirstW(snapshot, &entry)) {
    do {
      if (_wcsicmp(entry.szModule, L"ck3.exe") == 0) {
        base = reinterpret_cast<DWORD64>(entry.modBaseAddr);
        break;
      }
    } while (Module32NextW(snapshot, &entry));
  }
  CloseHandle(snapshot);
  return base;
}

bool IsCk3Image(HANDLE process) {
  std::array<wchar_t, 32768> path{};
  DWORD size = static_cast<DWORD>(path.size());
  if (!QueryFullProcessImageNameW(process, 0, path.data(), &size)) return false;
  const std::wstring name(path.data(), size);
  const auto slash = name.find_last_of(L"\\/");
  const auto basename = name.substr(slash == std::wstring::npos ? 0 : slash + 1);
  return _wcsicmp(basename.c_str(), L"ck3.exe") == 0;
}

std::uint64_t ProcessCreationTime(HANDLE process) {
  FILETIME created{}, exited{}, kernel{}, user{};
  if (!GetProcessTimes(process, &created, &exited, &kernel, &user)) return 0;
  ULARGE_INTEGER value{};
  value.LowPart = created.dwLowDateTime;
  value.HighPart = created.dwHighDateTime;
  return value.QuadPart;
}

bool GetContext(HANDLE thread, CONTEXT &context) {
  context = CONTEXT{};
  context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER |
                         CONTEXT_DEBUG_REGISTERS;
  return GetThreadContext(thread, &context) != FALSE;
}

bool ArmThread(HANDLE thread, const std::array<DWORD64, 2> &sites) {
  alignas(16) CONTEXT context{};
  if (!GetContext(thread, context)) return false;
  // Do not overwrite another component's processor breakpoints.
  if (context.Dr0 || context.Dr1 || context.Dr2 || context.Dr3 ||
      (context.Dr7 & (0xFFULL | 0xFFFF0000ULL))) return false;
  context.Dr0 = sites[0];
  context.Dr1 = sites[1];
  context.Dr6 = 0;
  context.Dr7 |= 0x5;  // local execute breakpoints 0 and 1, length 1.
  return SetThreadContext(thread, &context) != FALSE;
}

bool ClearThread(HANDLE thread) {
  alignas(16) CONTEXT context{};
  if (!GetContext(thread, context)) return false;
  context.Dr0 = 0;
  context.Dr1 = 0;
  context.Dr6 = 0;
  context.Dr7 &= ~0x5ULL;
  return SetThreadContext(thread, &context) != FALSE;
}

bool ClearAll(const std::map<DWORD, HANDLE> &threads,
              const std::set<DWORD> &armed_tids) {
  bool clean = true;
  for (const DWORD tid : armed_tids) {
    const auto item = threads.find(tid);
    if (item != threads.end()) clean = ClearThread(item->second) && clean;
  }
  return clean;
}

bool SuspendAndClearAll(const std::map<DWORD, HANDLE> &threads,
                        const std::set<DWORD> &armed_tids) {
  bool clean = true;
  for (const DWORD tid : armed_tids) {
    const auto item = threads.find(tid);
    if (item == threads.end()) continue;
    const DWORD previous = SuspendThread(item->second);
    if (previous == static_cast<DWORD>(-1)) {
      clean = false;
      continue;
    }
    clean = ClearThread(item->second) && clean;
    if (ResumeThread(item->second) == static_cast<DWORD>(-1)) clean = false;
  }
  return clean;
}

struct Hit {
  int site = -1;
  DWORD tid = 0;
  DWORD64 pointer = 0;
  std::uint32_t type = 0;
  std::uint64_t qpc = 0;
};

bool PairIsUnique(const std::vector<Hit> &hits) {
  return hits.size() == 2 && hits[0].site == 0 && hits[1].site == 1 &&
         hits[0].tid == hits[1].tid && hits[0].pointer != 0 &&
         hits[0].pointer == hits[1].pointer && hits[0].qpc < hits[1].qpc;
}

void LogHit(std::ofstream &output, const Hit &hit, DWORD pid,
            std::uint64_t ordinal) {
  output << "{\"kind\":\"sample\",\"site_rva\":\""
         << Hex(kSiteRvas[hit.site]) << "\",\"pid\":" << pid
         << ",\"thread_id\":" << hit.tid << ",\"event_ordinal\":"
         << ordinal << ",\"qpc\":" << hit.qpc
         << ",\"rax_change_pointer\":\"" << Hex(hit.pointer)
         << "\",\"change_type_dword\":" << hit.type
         << ",\"memory_read_status\":\"ok\"}\n";
  output.flush();
}

bool WriteReady(const std::filesystem::path &path, DWORD pid, DWORD64 base) {
  if (std::filesystem::exists(path)) return false;
  std::ofstream ready(path, std::ios::binary | std::ios::out);
  if (!ready) return false;
  ready << "{\"schema\":\"xar.ck3.war31.hwprobe_ready.v1\","
        << "\"pid\":" << pid << ",\"module_base\":\"" << Hex(base)
        << "\",\"site_0\":\"" << Hex(kSiteRvas[0])
        << "\",\"site_1\":\"" << Hex(kSiteRvas[1]) << "\"}\n";
  ready.flush();
  return ready.good();
}

void LogTerminal(std::ofstream &output, const std::string &status,
                 const std::string &reason, bool cleared, bool detached,
                 std::size_t hit_count) {
  output << "{\"kind\":\"terminal\",\"status\":\"" << status
         << "\",\"reason\":\"" << reason
         << "\",\"debug_registers_cleared\":"
         << (cleared ? "true" : "false") << ",\"detached\":"
         << (detached ? "true" : "false") << ",\"hit_count\":"
         << hit_count << "}\n";
  output.flush();
}

bool HasExpectedImageAndAnchors(HANDLE process, DWORD pid, DWORD64 &base) {
  if (!IsCk3Image(process)) return false;
  base = ModuleBase(pid);
  return base && ExactAnchorsAt(process,
                                {base + kSiteRvas[0], base + kSiteRvas[1]});
}

int Probe(DWORD pid, DWORD timeout_ms, const std::filesystem::path &raw_path,
          const std::filesystem::path &ready_path,
          const std::array<DWORD64, 2> &fixture_sites = {}) {
  g_stop_requested.store(false, std::memory_order_release);
  if (pid == 0 || timeout_ms < 1000 || timeout_ms > 300000 ||
      std::filesystem::exists(raw_path) || std::filesystem::exists(ready_path)) {
    std::cerr << "invalid PID/timeout or attempt output already exists\n";
    return 2;
  }
  HANDLE process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ |
                               PROCESS_CREATE_THREAD, FALSE, pid);
  if (!process) {
    std::cerr << "cannot open explicit process\n";
    return 2;
  }
  DWORD64 base = 0;
  const std::uint64_t process_created = ProcessCreationTime(process);
  const bool fixture = fixture_sites[0] != 0 || fixture_sites[1] != 0;
#if !defined(XAR_WAR31_HWPROBE_FIXTURE)
  if (fixture) {
    CloseHandle(process);
    std::cerr << "fixture sites are unavailable in the production sampler\n";
    return 2;
  }
#endif
  const bool image_ok = fixture ?
      (fixture_sites[0] != 0 && fixture_sites[1] != 0 &&
       ExactAnchorsAt(process, fixture_sites)) :
      HasExpectedImageAndAnchors(process, pid, base);
  if (!process_created || !image_ok) {
    CloseHandle(process);
    std::cerr << "process image or exact in-memory sites differ\n";
    return 2;
  }
  std::ofstream output(raw_path, std::ios::binary | std::ios::out);
  if (!output) {
    CloseHandle(process);
    std::cerr << "cannot create unique raw capture\n";
    return 2;
  }
  output << "{\"kind\":\"start\",\"schema\":"
         << "\"xar.ck3.war31.hwprobe_raw.v1\",\"pid\":" << pid
         << ",\"process_created_filetime\":" << process_created
         << ",\"module_base\":\"" << Hex(base)
         << "\",\"fixture\":" << (fixture ? "true" : "false") << "}\n";
  output.flush();

  (void)SetConsoleCtrlHandler(OnConsoleControl, TRUE);
  bool attached = DebugActiveProcess(pid) != FALSE;
  bool kill_on_exit_disabled = false;
  bool cleared = false;
  bool detached = false;
  bool process_exited = false;
  bool pending_event = false;
  DEBUG_EVENT event{};
  std::string reason = attached ? "none" : "debug_attach_failed";
  std::map<DWORD, HANDLE> threads;
  std::set<DWORD> armed_tids;
  std::vector<Hit> hits;
  bool ready = false;
  if (attached) {
    kill_on_exit_disabled = DebugSetProcessKillOnExit(FALSE) != FALSE;
    if (!kill_on_exit_disabled) reason = "kill_on_exit_disable_failed";
  }
  const std::array<DWORD64, 2> sites = fixture ? fixture_sites :
      std::array<DWORD64, 2>{base + kSiteRvas[0], base + kSiteRvas[1]};
  const auto deadline = std::chrono::steady_clock::now() +
                        std::chrono::milliseconds(timeout_ms);
  while (attached && kill_on_exit_disabled && reason == "none") {
    if (g_stop_requested.load(std::memory_order_acquire)) {
      reason = "control_cancel_requested";
      break;
    }
    if (std::chrono::steady_clock::now() >= deadline) {
      reason = "timeout_before_unique_pair";
      break;
    }
    event = DEBUG_EVENT{};
    if (!WaitForDebugEvent(&event, kWaitSliceMs)) {
      if (GetLastError() == ERROR_SEM_TIMEOUT) continue;
      reason = "debug_event_wait_failed";
      break;
    }
    pending_event = true;
    DWORD disposition = DBG_CONTINUE;
    switch (event.dwDebugEventCode) {
      case CREATE_PROCESS_DEBUG_EVENT:
        threads[event.dwThreadId] = event.u.CreateProcessInfo.hThread;
        if (event.u.CreateProcessInfo.hFile)
          CloseHandle(event.u.CreateProcessInfo.hFile);
        if (event.u.CreateProcessInfo.hProcess)
          CloseHandle(event.u.CreateProcessInfo.hProcess);
        if (!ArmThread(event.u.CreateProcessInfo.hThread, sites))
          reason = "cannot_arm_process_thread";
        else armed_tids.insert(event.dwThreadId);
        break;
      case CREATE_THREAD_DEBUG_EVENT:
        threads[event.dwThreadId] = event.u.CreateThread.hThread;
        if (!ArmThread(event.u.CreateThread.hThread, sites))
          reason = "cannot_arm_new_thread";
        else armed_tids.insert(event.dwThreadId);
        break;
      case EXIT_THREAD_DEBUG_EVENT:
        if (const auto exiting = threads.find(event.dwThreadId);
            exiting != threads.end() && exiting->second)
          CloseHandle(exiting->second);
        threads.erase(event.dwThreadId);
        armed_tids.erase(event.dwThreadId);
        break;
      case LOAD_DLL_DEBUG_EVENT:
        if (event.u.LoadDll.hFile) CloseHandle(event.u.LoadDll.hFile);
        break;
      case EXIT_PROCESS_DEBUG_EVENT:
        process_exited = true;
        reason = "process_exited_during_probe";
        break;
      case EXCEPTION_DEBUG_EVENT: {
        const DWORD code = event.u.Exception.ExceptionRecord.ExceptionCode;
        if (code == EXCEPTION_BREAKPOINT && !ready) {
          ready = WriteReady(ready_path, pid, base);
          if (!ready) reason = "ready_receipt_failed";
          break;
        }
        if (code != EXCEPTION_SINGLE_STEP) {
          disposition = DBG_EXCEPTION_NOT_HANDLED;
          reason = "unexpected_target_exception";
          break;
        }
        auto iterator = threads.find(event.dwThreadId);
        alignas(16) CONTEXT context{};
        if (iterator == threads.end() || !GetContext(iterator->second, context)) {
          reason = "single_step_context_unavailable";
          break;
        }
        int site = -1;
        for (int index = 0; index < 2; ++index) {
          if (context.Rip == sites[index] &&
              (context.Dr6 & (1ULL << index))) site = index;
        }
        if (site < 0) {
          disposition = DBG_EXCEPTION_NOT_HANDLED;
          reason = "unrelated_single_step_exception";
          break;
        }
        std::uint32_t type = 0;
        const DWORD64 pointer = context.Rax;
        if (pointer == 0 || pointer > UINT64_MAX - 0x268 ||
            !ReadExact(process, pointer + 0x268, &type, sizeof(type))) {
          reason = "change_type_memory_read_failed";
        } else {
          LARGE_INTEGER counter{};
          if (!QueryPerformanceCounter(&counter)) {
            reason = "qpc_failed";
          } else {
            hits.push_back(Hit{site, event.dwThreadId, pointer, type,
                               static_cast<std::uint64_t>(counter.QuadPart)});
            LogHit(output, hits.back(), pid, hits.size());
          }
        }
        // Intel RF suppresses immediate re-trigger at the same preinstruction
        // execute breakpoint. This changes debugger state, not game data.
        context.Dr6 = 0;
        context.EFlags |= kResumeFlag;
        if (!SetThreadContext(iterator->second, &context))
          reason = "cannot_restore_breakpoint_context";
        if (hits.size() >= 2) {
          if (PairIsUnique(hits)) reason = "paired";
          else reason = "ambiguous_or_cross_thread_pair";
        }
        break;
      }
      default:
        break;
    }
    if (reason != "none") {
      cleared = ClearAll(threads, armed_tids);
      if (!cleared && reason == "paired") reason = "debug_register_cleanup_failed";
    }
    bool continued = ContinueDebugEvent(event.dwProcessId,
                                        event.dwThreadId, disposition) != FALSE;
    if (!continued) {
      reason = "continue_debug_event_failed";
      cleared = ClearAll(threads, armed_tids);
      continued = ContinueDebugEvent(event.dwProcessId,
                                     event.dwThreadId, disposition) != FALSE;
    }
    pending_event = !continued;
  }

  if (attached && !process_exited && !pending_event && !cleared &&
      !armed_tids.empty()) {
    // On timeout/wait failure obtain a debugger event so all target threads
    // are suspended before clearing DR0/DR1/DR7. Do not detach with armed DRs.
    if (DebugBreakProcess(process)) {
      const auto cleanup_deadline = std::chrono::steady_clock::now() +
                                    std::chrono::milliseconds(kBreakCleanupWaitMs);
      while (std::chrono::steady_clock::now() < cleanup_deadline) {
        event = DEBUG_EVENT{};
        if (!WaitForDebugEvent(&event, kWaitSliceMs)) continue;
        pending_event = true;
        if (event.dwDebugEventCode == CREATE_THREAD_DEBUG_EVENT)
          threads[event.dwThreadId] = event.u.CreateThread.hThread;
        if (event.dwDebugEventCode == EXIT_THREAD_DEBUG_EVENT) {
          if (const auto exiting = threads.find(event.dwThreadId);
              exiting != threads.end() && exiting->second)
            CloseHandle(exiting->second);
          threads.erase(event.dwThreadId);
          armed_tids.erase(event.dwThreadId);
        }
        if (event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT && event.u.LoadDll.hFile)
          CloseHandle(event.u.LoadDll.hFile);
        if (event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT) process_exited = true;
        const bool cleanup_break = event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT &&
            event.u.Exception.ExceptionRecord.ExceptionCode == EXCEPTION_BREAKPOINT;
        if (cleanup_break || process_exited)
          cleared = process_exited || ClearAll(threads, armed_tids);
        const DWORD disposition =
            event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT &&
                    event.u.Exception.ExceptionRecord.ExceptionCode != EXCEPTION_BREAKPOINT
                ? DBG_EXCEPTION_NOT_HANDLED : DBG_CONTINUE;
        (void)ContinueDebugEvent(event.dwProcessId, event.dwThreadId, disposition);
        pending_event = false;
        if (cleared) break;
      }
    }
    if (!cleared && !process_exited)
      cleared = SuspendAndClearAll(threads, armed_tids);
  }
  if (pending_event && !process_exited) {
    cleared = ClearAll(threads, armed_tids);
    if (ContinueDebugEvent(event.dwProcessId, event.dwThreadId,
                           DBG_EXCEPTION_NOT_HANDLED)) pending_event = false;
  }
  if (armed_tids.empty()) cleared = true;
  if (attached && !process_exited) {
    // DebugSetProcessKillOnExit(FALSE) ensures unexpected sampler exit detaches
    // rather than killing CK3. A RED cleanup remains explicit in the receipt.
    detached = DebugActiveProcessStop(pid) != FALSE;
  } else if (process_exited) {
    detached = true;
  }
  if (!process_exited) {
    for (const auto &[tid, handle] : threads) {
      (void)tid;
      if (handle) CloseHandle(handle);
    }
  }
  if (pending_event) reason = "pending_debug_event_cleanup_failed";
  if (reason == "paired" && (!cleared || !detached))
    reason = "cleanup_not_proven";
  LogTerminal(output, reason == "paired" ? "paired" : "red", reason,
              cleared || process_exited, detached, hits.size());
  CloseHandle(process);
  (void)SetConsoleCtrlHandler(OnConsoleControl, FALSE);
  return reason == "paired" ? 0 : 1;
}

int SelfTest() {
  const std::vector<Hit> good{{0, 7, 0x1008, 0, 10},
                              {1, 7, 0x1008, 23, 11}};
  auto bad = good;
  bad[1].pointer += 8;
  if (!PairIsUnique(good) || PairIsUnique(bad)) return 1;
  bad = good;
  bad[1].tid = 8;
  if (PairIsUnique(bad)) return 1;
  bad = good;
  bad.pop_back();
  if (PairIsUnique(bad)) return 1;
  std::cout << "war31-hwprobe-self-test: passed\n";
  return 0;
}

int Inspect(DWORD pid) {
  HANDLE process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ,
                               FALSE, pid);
  if (!process) return 2;
  DWORD64 base = 0;
  const std::uint64_t created = ProcessCreationTime(process);
  const bool verified = created && HasExpectedImageAndAnchors(process, pid, base);
  CloseHandle(process);
  if (!verified) return 2;
  std::cout << "{\"schema\":\"xar.ck3.war31.hwprobe_inspect.v1\","
            << "\"pid\":" << pid << ",\"process_created_filetime\":"
            << created << ",\"module_base\":\"" << Hex(base)
            << "\",\"exact_in_memory_sites\":true,"
            << "\"attached\":false}\n";
  return 0;
}

}  // namespace

int wmain(int argc, wchar_t **argv) {
  if (argc == 2 && std::wstring(argv[1]) == L"--self-test") return SelfTest();
  if (argc == 3 && std::wstring(argv[1]) == L"--inspect-pid") {
    try { return Inspect(static_cast<DWORD>(std::stoul(argv[2]))); }
    catch (const std::exception &) { return 2; }
  }
#if defined(XAR_WAR31_HWPROBE_FIXTURE)
  if (argc == 13 && std::wstring(argv[1]) == L"--fixture-pid" &&
      std::wstring(argv[3]) == L"--site0" &&
      std::wstring(argv[5]) == L"--site1" &&
      std::wstring(argv[7]) == L"--timeout-ms" &&
      std::wstring(argv[9]) == L"--raw" &&
      std::wstring(argv[11]) == L"--ready") {
    try {
      return Probe(static_cast<DWORD>(std::stoul(argv[2])),
                   static_cast<DWORD>(std::stoul(argv[8])), argv[10], argv[12],
                   {std::stoull(argv[4], nullptr, 0),
                    std::stoull(argv[6], nullptr, 0)});
    } catch (const std::exception &error) {
      std::cerr << "fixture argument error: " << error.what() << "\n";
      return 2;
    }
  }
#endif
  if (argc != 9 || std::wstring(argv[1]) != L"--pid" ||
      std::wstring(argv[3]) != L"--timeout-ms" ||
      std::wstring(argv[5]) != L"--raw" ||
      std::wstring(argv[7]) != L"--ready") {
    std::cerr << "usage: war31_two_point_hwprobe --pid N --timeout-ms N "
                 "--raw NEW.ndjson --ready NEW.json\n";
    return 2;
  }
  try {
    const auto pid = static_cast<DWORD>(std::stoul(argv[2]));
    const auto timeout = static_cast<DWORD>(std::stoul(argv[4]));
    return Probe(pid, timeout, argv[6], argv[8]);
  } catch (const std::exception &error) {
    std::cerr << "argument or probe failure: " << error.what() << "\n";
    return 2;
  }
}
