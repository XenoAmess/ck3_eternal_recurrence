// Owned-sibling synthetic qualification of the actual carrier worker Probe.
// This entry never enables the production CK3 CLI or accepts carrier addresses.
#ifndef XAR_ENABLE_REFILL_V5_COLD_PROBE_12004
#define XAR_ENABLE_REFILL_V5_COLD_PROBE_12004 0
#endif
#ifndef XAR_ENABLE_REFILL_CARRIER_THREAD_DISCOVERY_12004
#define XAR_ENABLE_REFILL_CARRIER_THREAD_DISCOVERY_12004 0
#endif
#if !XAR_ENABLE_REFILL_V5_COLD_PROBE_12004 || !XAR_ENABLE_REFILL_CARRIER_THREAD_DISCOVERY_12004
#include <iostream>
int wmain(int, wchar_t **) {
  std::cerr << "default OFF: carrier worker cold Probe not entered\n";
  return 3;
}
#else
#define XAR_REFILL_V5_COLD_BUILD 1
#define wmain XarDisabledProductionEntryForV5Cold12004
#include "../refill_add_hwprobe_12004.cpp"
#undef wmain

int wmain(int argc, wchar_t **argv) {
  if (argc != 17 || std::wstring(argv[1]) != L"--fixture-meta" ||
      std::wstring(argv[3]) != L"--timeout-ms" || std::wstring(argv[5]) != L"--raw" ||
      std::wstring(argv[7]) != L"--ready" || std::wstring(argv[9]) != L"--max-hits" ||
      std::wstring(argv[11]) != L"--max-threads" ||
      std::wstring(argv[13]) != L"--thread-policy" ||
      std::wstring(argv[14]) != L"carrier-owned-target" ||
      std::wstring(argv[15]) != L"--machine-id") return 2;
  try {
    const std::filesystem::path metadata(argv[2]);
    if (std::filesystem::file_size(metadata) > 8192) return 2;
    std::ifstream input(metadata);
    if (!input) return 2;
    std::map<std::string, std::string> meta;
    std::string line;
    while (std::getline(input, line)) {
      if (!line.empty() && line.back() == '\r') line.pop_back();
      const auto at = line.find('=');
      if (at == std::string::npos || line.size() > 1024 ||
          !meta.emplace(line.substr(0, at), line.substr(at + 1)).second) return 2;
    }
    const std::array<const char *, 21> keys{
      "pid", "main_tid", "worker_tid", "created", "worker_created_filetime",
      "module_base", "site0", "site1", "regiment", "slot", "arrg_registry_slot",
      "army_registry_slot", "q", "before", "carrier_token", "mode", "go_event",
      "audit_event", "finish_event", "machine_id", "observed_at_utc"};
    if (meta.size() != keys.size()) return 2;
    for (auto key : keys) if (!meta.contains(key)) return 2;
    auto number = [](const std::string &s) {
      std::size_t n = 0;
      auto value = std::stoull(s, &n, 0);
      if (n != s.size() || s.empty() || s[0] == '-')
        throw std::out_of_range("unsigned cold metadata");
      return value;
    };
    auto u32 = [&](const char *key) {
      auto value = number(meta.at(key));
      if (value > 0xFFFFFFFFULL) throw std::out_of_range("u32");
      return DWORD(value);
    };
    auto ascii = [](const std::wstring &s) {
      std::string out;
      for (auto c : s) {
        if (c > 127) throw std::out_of_range("ASCII");
        out += char(c);
      }
      return out;
    };
    const DWORD pid = u32("pid");
    const DWORD main_tid = u32("main_tid"), worker_tid = u32("worker_tid");
    if (!pid || !main_tid || !worker_tid || main_tid == worker_tid ||
        !number(meta.at("worker_created_filetime")) ||
        (meta.at("mode") != "worker-positive" && meta.at("mode") != "worker-exit-before-add")) return 2;
    g_expected_created = number(meta.at("created"));
    g_expected_regiment = u32("regiment");
    g_expected_slot = u32("slot");
    g_fixture_base = number(meta.at("module_base"));
    g_fixture_sites = {number(meta.at("site0")), number(meta.at("site1"))};
    g_fixture_arrg_slot = number(meta.at("arrg_registry_slot"));
    g_fixture_army_slot = number(meta.at("army_registry_slot"));
    g_fixture_hit_limit = number(ascii(argv[10]));
    const auto maximum_threads = number(ascii(argv[12]));
    const auto timeout = number(ascii(argv[4]));
    if (timeout < 1000 || timeout > 300000 || !g_fixture_hit_limit ||
        g_fixture_hit_limit > 100000 || maximum_threads < 3 || maximum_threads > 16 ||
        !g_expected_created || g_expected_slot >= 7 || g_expected_regiment == 0xFFFFFFFFU) return 2;
    for (auto c : std::wstring(argv[16])) {
      if (!((c >= L'a' && c <= L'z') || (c >= L'0' && c <= L'9') || c == L'-')) return 2;
      g_machine += char(c);
    }
    if (g_machine.empty() || g_machine.size() > 128) return 2;
    if (meta.at("machine_id") != g_machine || meta.at("observed_at_utc").empty()) return 2;
    // The metadata TIDs are assertions for the runner, never thread selection.
    g_expected_tid = 0;
    g_carrier_owned_target = true;
    g_maximum_owned_threads = static_cast<unsigned>(maximum_threads);
    HANDLE process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    if (!process) return 2;
    const bool owned = ProcessCreationTime(process) == g_expected_created &&
      ColdSiblingImage12004(process, pid);
    CloseHandle(process);
    if (!owned) return 2;
    return Probe(pid, DWORD(timeout), argv[6], argv[8], g_fixture_sites);
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
}
#endif
