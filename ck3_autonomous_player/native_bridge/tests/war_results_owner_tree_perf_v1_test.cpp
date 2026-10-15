// Offline DLL fixture: only this Python host's allocated memory is read.
#define NOMINMAX
#include <windows.h>
#include "xar_bridge/war_declared_owner_memory_v1.hpp"
#define main WarOwnerTreeContractTestMain
#define Unknown WarOwnerFixtureUnknown
#include "war_declared_owner_tree_v1_test.cpp"
#undef Unknown
#undef main
#include <algorithm>
#include <array>
#include <chrono>
#include <sstream>
#include <string>

namespace {
using namespace xar::ck3_11906::detail;
struct RuntimeNode {
  std::uintptr_t vtable = 1;
  bool target = false, visible = false;
  std::uintptr_t children = 0;
  std::int32_t count = 0;
};
struct MemoryGraph {
  std::vector<RuntimeNode> nodes;
  std::vector<std::uintptr_t> children;
  bool kernel_reads = false;
  explicit MemoryGraph(std::size_t count) : nodes(count), children(count-1) {
    nodes.front().target = true;
    for (std::size_t i = 1; i < count; ++i)
      children[i-1] = reinterpret_cast<std::uintptr_t>(&nodes[i]);
    nodes.front().children = reinterpret_cast<std::uintptr_t>(children.data());
    nodes.front().count = static_cast<std::int32_t>(children.size());
  }
  bool read(std::uintptr_t address, void *out, std::size_t count) const noexcept {
    if (!kernel_reads) return ReadWarDeclaredOwnerBytesV1(reinterpret_cast<void *>(address), out, count);
    SIZE_T got = 0;
    return ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<void *>(address), out, count, &got) && got == count;
  }
  static Failure Runtime(const void *, std::uintptr_t node, bool &target, bool &visible) noexcept {
    std::uintptr_t vtable = 0;
    // B15 runtime already uses guarded direct reads, so both modes do as well.
    return ReadWarDeclaredOwnerValueV1(node, offsetof(RuntimeNode, vtable), vtable) && vtable &&
        ReadWarDeclaredOwnerValueV1(node, offsetof(RuntimeNode, target), target) &&
        ReadWarDeclaredOwnerValueV1(node, offsetof(RuntimeNode, visible), visible)
        ? Failure::none : Failure::widget_runtime_unreadable;
  }
  static Failure Children(const void *opaque, std::uintptr_t node,
                          std::uintptr_t &address, std::int32_t &count) noexcept {
    const auto &graph = *static_cast<const MemoryGraph *>(opaque);
    if (!graph.read(node + offsetof(RuntimeNode, children), &address, sizeof(address)))
      return Failure::child_vector_unreadable;
    return graph.read(node + offsetof(RuntimeNode, count), &count, sizeof(count))
        ? Failure::none : Failure::child_count_unreadable;
  }
  static Failure Child(const void *opaque, std::uintptr_t address,
                       std::uint32_t index, std::uintptr_t &value) noexcept {
    const auto &graph = *static_cast<const MemoryGraph *>(opaque);
    const auto offset = std::size_t(index) * sizeof(value);
    if (offset > (std::numeric_limits<std::uintptr_t>::max)() - address)
      return Failure::child_address_overflow;
    return graph.read(address + offset, &value, sizeof(value)) ? Failure::none : Failure::child_slot_unreadable;
  }
  WarDeclaredOwnerReadCallbacksV1 callbacks() const { return {this, &Runtime, &Children, &Child}; }
};

template<class Run>
double MedianMilliseconds(Run run) {
  std::array<double,3> times{};
  for (auto &time : times) {
    const auto start = std::chrono::steady_clock::now();
    if (!run()) return -1;
    time = std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
  }
  std::sort(times.begin(), times.end());
  return times[1];
}
}

extern "C" __declspec(dllexport) int RunWarOwnerFocusedTests() {
  if (WarOwnerTreeContractTestMain()) return 1;
  std::uintptr_t value = 123, copy = 0;
  bool ok = ReadWarDeclaredOwnerValueV1(reinterpret_cast<std::uintptr_t>(&value), 0, copy) && copy == value;
  ok &= !ReadWarDeclaredOwnerBytesV1(nullptr, &copy, sizeof(copy));
  ok &= !ReadWarDeclaredOwnerBytesV1(&value, nullptr, sizeof(copy));
  ok &= !ReadWarDeclaredOwnerBytesV1(&value, &copy, 0);
  ok &= !ReadWarDeclaredOwnerValueV1((std::numeric_limits<std::uintptr_t>::max)()-3, 8, copy);
  SYSTEM_INFO info{};
  GetSystemInfo(&info);
  const auto size = static_cast<std::size_t>(info.dwPageSize);
  auto *pages = static_cast<unsigned char *>(VirtualAlloc(nullptr, size*2, MEM_COMMIT|MEM_RESERVE, PAGE_READWRITE));
  if (!pages) return 2;
  DWORD previous = 0;
  if (!VirtualProtect(pages+size, size, PAGE_NOACCESS, &previous)) {
    VirtualFree(pages, 0, MEM_RELEASE);
    return 3;
  }
  ok &= !ReadWarDeclaredOwnerBytesV1(pages+size, &copy, sizeof(copy));
  ok &= !ReadWarDeclaredOwnerBytesV1(pages+size-4, &copy, sizeof(copy));
  ok &= ReadWarDeclaredOwnerBytesV1(pages, &copy, sizeof(copy));
  VirtualFree(pages, 0, MEM_RELEASE);
  std::cout << "{\"guarded_memory_scenes\":8,\"status\":\"" << (ok?"GREEN":"RED") << "\"}\n";
  return ok ? 0 : 4;
}

extern "C" __declspec(dllexport) const char *RunWarOwnerMicrobenchmark() {
  static std::string response;
  std::ostringstream json;
  json << "{\"fixture\":\"owned-synthetic-memory-no-Game\",\"repetitions\":3,\"rows\":[";
  bool first = true;
  for (const auto count : {4097u, 32768u, 131072u}) {
    MemoryGraph graph(count);
    WarDeclaredOwnerReadResultV1 result;
    const auto root = reinterpret_cast<std::uintptr_t>(graph.nodes.data());
    graph.kernel_reads = true;
    const auto baseline = MedianMilliseconds([&] { return ReadWarDeclaredOwnerTreeV1(root,graph.callbacks(),result); });
    graph.kernel_reads = false;
    const auto direct = MedianMilliseconds([&] { return ReadWarDeclaredOwnerTreeV1(root,graph.callbacks(),result); });
    WarDeclaredOwnerTreeCacheV1 cache;
    if (!ReadWarDeclaredOwnerTreeCachedV1(root,graph.callbacks(),cache,result)) return nullptr;
    const auto warm = MedianMilliseconds([&] { return ReadWarDeclaredOwnerTreeCachedV1(root,graph.callbacks(),cache,result); });
    if (baseline < 0 || direct < 0 || warm < 0 || !result.complete || result.visited != count || result.edges != count-1)
      return nullptr;
    if (!first) json << ',';
    first = false;
    json << "{\"nodes\":" << count << ",\"edges\":" << result.edges
         << ",\"baseline_rpm_full_ms\":" << baseline << ",\"direct_full_ms\":" << direct
         << ",\"direct_cached_warm_ms\":" << warm << ",\"speedup\":" << baseline/warm << '}';
  }
  json << "],\"scope\":\"tree plus header/edge reads only; excludes actual GUI name strings, Native snapshots, mailbox scheduling and MCP\"}";
  response = json.str();
  return response.c_str();
}
