// Synthetic owned process only. Main never calls SyntheticAdd.
#ifndef XAR_ENABLE_REFILL_V5_COLD_PROBE_12004
#define XAR_ENABLE_REFILL_V5_COLD_PROBE_12004 0
#endif
#if !XAR_ENABLE_REFILL_V5_COLD_PROBE_12004
#include <iostream>
int wmain(int, wchar_t **) { std::cerr << "default OFF: worker cold target\n"; return 3; }
#else
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include "../../include/xar_bridge/refill_core_carrier_12004.hpp"

namespace abi = xar::ck3_12004::refill_carrier;
extern "C" __declspec(dllexport) abi::Directory XarRefillCoreCarrier12004{};
extern "C" void SyntheticAdd(void *, std::uint32_t, std::uint64_t);
extern "C" unsigned char SyntheticBefore, SyntheticAfter;
extern "C" { volatile LONG g_AddExecutedCount = 0; }
namespace {
constexpr std::uint32_t kRegi = 0x11000001, kArRg = 0x12000001, kArmy = 0x13000001;
constexpr std::uint64_t kToken = 0x61000216, kClock = 0x71000216;
constexpr std::uint32_t kBefore = 80, kQ = 10;
alignas(16) std::array<std::uint8_t, 0x180> regi{}, arrg{}, army{};
std::array<std::uint8_t, 0x40> arrg_registry{}, army_registry{};
std::array<std::uintptr_t, 4> arrg_table{}, army_table{};
void *arrg_storage = arrg_registry.data(), *army_storage = army_registry.data();
std::array<std::array<std::uint32_t, 4>, 2> data{};
HANDLE go_event = nullptr, audit_event = nullptr, finish_event = nullptr;
HANDLE initial_done = nullptr, worker_ready = nullptr, post_audit = nullptr, post_done = nullptr;
HANDLE main_thread = nullptr, worker_thread = nullptr, auditor_thread = nullptr;
DWORD main_tid = 0, worker_tid = 0;
std::filesystem::path prefix;
std::string machine_id;
bool exit_before_add = false;
std::string Utc() {
  SYSTEMTIME time{}; GetSystemTime(&time);
  std::ostringstream out; out << std::setfill('0') << std::setw(4) << time.wYear << '-'
    << std::setw(2) << time.wMonth << '-' << std::setw(2) << time.wDay << 'T'
    << std::setw(2) << time.wHour << ':' << std::setw(2) << time.wMinute << ':'
    << std::setw(2) << time.wSecond << '.' << std::setw(3) << time.wMilliseconds << 'Z';
  return out.str();
}
std::uint64_t Filetime(FILETIME value) {
  ULARGE_INTEGER result{};
  result.LowPart = value.dwLowDateTime; result.HighPart = value.dwHighDateTime;
  return result.QuadPart;
}
std::uint64_t Created(HANDLE handle, bool thread) {
  FILETIME c{}, e{}, k{}, u{};
  if (!(thread ? GetThreadTimes(handle, &c, &e, &k, &u) :
                 GetProcessTimes(handle, &c, &e, &k, &u))) return 0;
  return Filetime(c);
}
template<class T> void Put(auto &object, std::size_t offset, T value) {
  std::memcpy(object.data() + offset, &value, sizeof value);
}
std::filesystem::path File(const wchar_t *suffix) { return prefix.wstring() + suffix; }
struct Audit {
  DWORD tid = 0, exit_code = STILL_ACTIVE;
  std::uint64_t created = 0;
  bool alive = false, ok = false;
  std::array<DWORD64, 6> dr{};
};
Audit main_initial, main_after;
Audit Capture(HANDLE thread) {
  Audit result;
  result.tid = GetThreadId(thread); result.created = Created(thread, true);
  if (!result.tid || !result.created || !GetExitCodeThread(thread, &result.exit_code)) return result;
  result.alive = result.exit_code == STILL_ACTIVE;
  if (!result.alive) { result.ok = true; return result; }
  if (SuspendThread(thread) == DWORD(-1)) return result;
  CONTEXT context{}; context.ContextFlags = CONTEXT_DEBUG_REGISTERS;
  result.ok = GetThreadContext(thread, &context) != FALSE;
  result.dr = {context.Dr0, context.Dr1, context.Dr2, context.Dr3, context.Dr6, context.Dr7};
  if (ResumeThread(thread) == DWORD(-1)) result.ok = false;
  return result;
}
void Emit(std::ostream &out, const Audit &audit) {
  out << "{\"thread_id\":" << audit.tid << ",\"thread_created_filetime\":" << audit.created
      << ",\"alive\":" << (audit.alive ? "true" : "false")
      << ",\"ok\":" << (audit.ok ? "true" : "false") << ",\"exit_code\":" << audit.exit_code
      << ",\"Dr0\":" << audit.dr[0] << ",\"Dr1\":" << audit.dr[1]
      << ",\"Dr2\":" << audit.dr[2] << ",\"Dr3\":" << audit.dr[3]
      << ",\"Dr6\":" << audit.dr[4] << ",\"Dr7\":" << audit.dr[5] << '}';
}
bool WriteAudit(const wchar_t *suffix, const Audit &main) {
  const auto worker = Capture(worker_thread), auditor = Capture(auditor_thread);
  std::ofstream out(File(suffix));
  out << "{\"machine_id\":\"" << machine_id << "\",\"observed_at_utc\":\"" << Utc()
      << "\",\"synthetic\":true,\"main\":"; Emit(out, main);
  out << ",\"worker\":"; Emit(out, worker);
  out << ",\"auditor\":"; Emit(out, auditor); out << "}\n";
  return main.ok && worker.ok && auditor.ok && out.good();
}
DWORD WINAPI Auditor(void *) {
  main_initial = Capture(main_thread);
  SetEvent(initial_done);
  if (WaitForSingleObject(post_audit, 60000) != WAIT_OBJECT_0) return 2;
  main_after = Capture(main_thread);
  SetEvent(post_done);
  return WaitForSingleObject(finish_event, 60000) == WAIT_OBJECT_0 ? 0 : 3;
}
DWORD WINAPI Worker(void *) {
  const DWORD tid = GetCurrentThreadId();
  abi::Words payload{};
  payload[abi::active] = 1;
  payload[abi::invocation_token] = kToken;
  payload[abi::nesting_depth] = 1;
  payload[abi::core_clock_identity] = payload[abi::natural_clock_identity] = kClock;
  payload[abi::core_entry_sequence] = 2; payload[abi::natural_entry_sequence] = 1;
  payload[abi::core_thread_id] = payload[abi::natural_thread_id] = tid;
  payload[abi::date_raw] = 53149080;
  payload[abi::manager_identity] = reinterpret_cast<std::uintptr_t>(arrg.data());
  payload[abi::secondary_manager_identity] = payload[abi::manager_identity] + 8;
  payload[abi::game_state_identity] = reinterpret_cast<std::uintptr_t>(army.data());
  payload[abi::caller_return_rva] = 0x2A9A8E2; payload[abi::natural_entry_rva] = 0x2A9A570;
  payload[abi::entry_provenance_complete] = payload[abi::saved_mask02_admitted] = 1;
  payload[abi::invocation_kind] = 3;
  abi::Publication publication(XarRefillCoreCarrier12004, tid, payload);
  if (!publication.published()) return 4;
  SetEvent(worker_ready);
  if (WaitForSingleObject(go_event, 60000) != WAIT_OBJECT_0) return 5;
  // Only this actual worker reaches the unchanged original ADD assembly.
  if (!exit_before_add) SyntheticAdd(regi.data(), kQ, 0);
  std::uint32_t after = 0; std::memcpy(&after, regi.data() + 0x1C, sizeof after);
  std::ofstream out(File(L".add.json"));
  out << "{\"machine_id\":\"" << machine_id << "\",\"observed_at_utc\":\"" << Utc()
      << "\",\"synthetic\":true,\"CK3_actual_ADD_observed\":false,\"main_thread_id\":" << main_tid
      << ",\"worker_thread_id\":" << tid << ",\"worker_created_filetime\":" << Created(GetCurrentThread(), true)
      << ",\"before_u32\":" << kBefore << ",\"q_u32\":" << kQ << ",\"after_u32\":" << after
      << ",\"main_ADD_execution_count\":0,\"worker_ADD_execution_count\":" << g_AddExecutedCount
      << ",\"exited_before_ADD\":" << (exit_before_add ? "true" : "false") << "}\n";
  out.close();
  if (!out.good()) return 6;
  if (exit_before_add) return 0;
  return WaitForSingleObject(finish_event, 60000) == WAIT_OBJECT_0 ? 0 : 7;
}
}
int wmain(int argc, wchar_t **argv) {
  if (argc != 7 || std::wstring(argv[1]) != L"--mode" || std::wstring(argv[3]) != L"--prefix" ||
      std::wstring(argv[5]) != L"--machine-id") return 2;
  const std::wstring mode = argv[2];
  if (mode != L"worker-positive" && mode != L"worker-exit-before-add") return 2;
  for (auto c : std::wstring(argv[6])) {
    if (!((c >= L'a' && c <= L'z') || (c >= L'0' && c <= L'9') || c == L'-')) return 2;
    machine_id += char(c);
  }
  if (machine_id.empty() || machine_id.size() > 128) return 2;
  prefix = argv[4]; exit_before_add = mode == L"worker-exit-before-add"; main_tid = GetCurrentThreadId();
  for (unsigned i = 0; i != 7; ++i) {
    const auto offset = 0x18 + i * 0x24;
    Put(regi, offset, std::uint32_t(100)); Put(regi, offset + 4, kBefore);
    Put(regi, offset + 8, kRegi); Put(regi, offset + 0xC, std::uint32_t(i));
    Put(regi, offset + 0x10, std::int32_t(-1));
  }
  Put(regi, 0x10, kRegi); Put(regi, 0x14, std::uint32_t(0x52656769)); Put(regi, 0x28, kArRg);
  Put(arrg, 0x10, kArRg); Put(arrg, 0x14, std::uint32_t(0x41725267));
  data[0] = {0, 0, kRegi, 0}; data[1] = data[0];
  Put(arrg, 0x20, reinterpret_cast<std::uintptr_t>(data.data())); Put(arrg, 0x2C, std::int32_t(2));
  Put(arrg, 0x140, kArmy); Put(army, 0x10, kArmy); Put(army, 0x14, std::uint32_t(0x41726D79));
  arrg_table[3] = reinterpret_cast<std::uintptr_t>(arrg.data());
  army_table[3] = reinterpret_cast<std::uintptr_t>(army.data());
  Put(arrg_registry, 0x20, reinterpret_cast<std::uintptr_t>(arrg_table.data()));
  Put(arrg_registry, 0x2C, std::uint32_t(2));
  Put(army_registry, 0x20, reinterpret_cast<std::uintptr_t>(army_table.data()));
  Put(army_registry, 0x2C, std::uint32_t(2));
  const auto name = L"Local\\XarRefillV5Cold" + std::to_wstring(GetCurrentProcessId());
  go_event = CreateEventW(nullptr, TRUE, FALSE, (name + L"Go").c_str());
  audit_event = CreateEventW(nullptr, TRUE, FALSE, (name + L"Audit").c_str());
  finish_event = CreateEventW(nullptr, TRUE, FALSE, (name + L"Finish").c_str());
  initial_done = CreateEventW(nullptr, TRUE, FALSE, nullptr); worker_ready = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  post_audit = CreateEventW(nullptr, TRUE, FALSE, nullptr); post_done = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  main_thread = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_LIMITED_INFORMATION,
                           FALSE, main_tid);
  if (!go_event || !audit_event || !finish_event || !initial_done || !worker_ready ||
      !post_audit || !post_done || !main_thread) return 3;
  worker_thread = CreateThread(nullptr, 0, Worker, nullptr, 0, &worker_tid);
  if (!worker_thread || WaitForSingleObject(worker_ready, 5000) != WAIT_OBJECT_0) return 4;
  auditor_thread = CreateThread(nullptr, 0, Auditor, nullptr, 0, nullptr);
  if (!auditor_thread || WaitForSingleObject(initial_done, 5000) != WAIT_OBJECT_0 ||
      !WriteAudit(L".initial-debug.json", main_initial)) return 5;
  std::ofstream meta(File(L".meta.txt"));
  meta << "machine_id=" << machine_id << "\nobserved_at_utc=" << Utc()
       << "\npid=" << GetCurrentProcessId() << "\nmain_tid=" << main_tid << "\nworker_tid=" << worker_tid
       << "\ncreated=" << Created(GetCurrentProcess(), false)
       << "\nworker_created_filetime=" << Created(worker_thread, true)
       << "\nmodule_base=" << reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))
       << "\nsite0=" << reinterpret_cast<std::uintptr_t>(&SyntheticBefore)
       << "\nsite1=" << reinterpret_cast<std::uintptr_t>(&SyntheticAfter)
       << "\nregiment=" << kRegi << "\nslot=0\narrg_registry_slot=" << reinterpret_cast<std::uintptr_t>(&arrg_storage)
       << "\narmy_registry_slot=" << reinterpret_cast<std::uintptr_t>(&army_storage)
       << "\nq=" << kQ << "\nbefore=" << kBefore << "\ncarrier_token=" << kToken
       << "\nmode=" << (exit_before_add ? "worker-exit-before-add" : "worker-positive")
       << "\ngo_event=" << std::string(name.begin(), name.end()) << "Go\naudit_event="
       << std::string(name.begin(), name.end()) << "Audit\nfinish_event="
       << std::string(name.begin(), name.end()) << "Finish\n";
  meta.close(); if (!meta.good()) return 6;
  if (WaitForSingleObject(audit_event, 60000) != WAIT_OBJECT_0) return 7;
  SetEvent(post_audit);
  if (WaitForSingleObject(post_done, 5000) != WAIT_OBJECT_0 ||
      !WriteAudit(L".after-debug.json", main_after)) return 8;
  if (WaitForSingleObject(finish_event, 60000) != WAIT_OBJECT_0) return 9;
  if (WaitForSingleObject(worker_thread, 5000) != WAIT_OBJECT_0 ||
      WaitForSingleObject(auditor_thread, 5000) != WAIT_OBJECT_0) return 10;
  DWORD worker_exit = STILL_ACTIVE, auditor_exit = STILL_ACTIVE;
  if (!GetExitCodeThread(worker_thread, &worker_exit) || !GetExitCodeThread(auditor_thread, &auditor_exit) ||
      worker_exit != 0 || auditor_exit != 0) return 11;
  for (HANDLE handle : {go_event, audit_event, finish_event, initial_done, worker_ready, post_audit,
                        post_done, main_thread, worker_thread, auditor_thread}) CloseHandle(handle);
  return 0;
}
#endif
