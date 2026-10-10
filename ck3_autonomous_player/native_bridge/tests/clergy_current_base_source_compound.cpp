#include "xar_bridge/clergy_mode0_task_raw_al_31b4a10_12004.hpp"
#include "xar_bridge/clergy_task_block_31b4810_12004.hpp"
#include "xar_bridge/clergy_position_raw_al_31bde90_12004.hpp"
#include "xar_bridge/clergy_position_check_31bd1a0_12004.hpp"
#include "xar_bridge/clergy_shared_condition_31bdda0_12004.hpp"

#include <cstdint>
#include <cstring>
#include <exception>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>

int RunClergyMode0TaskRawAl12004NewCases();
void RunRootScopeInitializer889F6012004NewCases();
namespace xar::ck3_12004::religion::clergy {
int RunClergyPositionRawAl31BDE9012004NewCases();
int RunClergyPosition31BD1A0NewCases12004();
void VerifyClergyShared31BDDA0ConnectedCases12004();
namespace new_cases {
bool RunClergyTaskBlock31B4810NullTooltip12004NewCases();
}
}

namespace {
namespace c = xar::ck3_12004::religion::clergy;
constexpr std::uintptr_t task = 0x10000;
constexpr std::uintptr_t type = 0x20000;
constexpr std::uintptr_t position = 0x30000;
constexpr std::uintptr_t clock_address = 0x40000;
constexpr std::uintptr_t module = 0x140000000;
constexpr std::string_view sha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::uint32_t owner_raw = 0xFF001234U;
constexpr std::uint32_t incumbent_raw = 0xAB005678U;

void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}

// Declared software bytes only. These fixtures do not read Game memory or
// establish any live frame/ID, constructor, predicate or native ABI fact.
struct Memory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::uintptr_t deny = 0;
  std::uintptr_t last_read = 0;
  std::size_t read_count = 0;
  int initial_calls = 0;
  int position_calls = 0;
  c::ClergyPosition31BD1A0ReadContext12004 final_context{};

  template <typename T> void Put(std::uintptr_t address, T value) {
    const auto *input = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(T); ++i) bytes[address + i] = input[i];
  }
  static bool Read(void *opaque, const void *address, void *out,
                   std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(opaque);
    const auto start = reinterpret_cast<std::uintptr_t>(address);
    m.last_read = start;
    ++m.read_count;
    if (start == m.deny) return false;
    auto *destination = static_cast<std::uint8_t *>(out);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = m.bytes.find(start + i);
      if (found == m.bytes.end()) return false;
      destination[i] = found->second;
    }
    return true;
  }
  void Seed() {
    Put(task + 0x18, type);
    Put(type + 0x40, position);
    Put(task + 0x44, owner_raw);
    Put(task + 0x40, incumbent_raw);
    Put(task + 0x30, incumbent_raw);
    Put(task + 0x28, std::uint32_t{48});
    Put(position + 0x2374, std::uint8_t{2});
    Put(position + 0x2377, std::uint8_t{2});
    Put(position + 0x2378, std::uint8_t{0});
    Put(position + 0x1E38 + 0x4C, std::uint32_t{0});
    Put(position + 0x20A8 + 0x4C, std::uint32_t{0});
    Put(position + 0x2178 + 0x4C, std::uint32_t{0});
    Put(position + 0x2338, std::uint32_t{0});
    Put(module + 0x5C68C50, clock_address);
    Put(clock_address + 8, std::uint32_t{120});
    final_context = {this, Read, module, sha};
  }
  static bool Initial(void *opaque, std::uintptr_t actual_task,
                      std::uint8_t &raw) noexcept {
    auto &m = *static_cast<Memory *>(opaque);
    ++m.initial_calls;
    const auto operands = c::ReadClergyTaskBlock31B4810Operands12004(
        &m, Read, actual_task);
    if (!operands.source_ready || !operands.task_44_raw_u32) return false;
    const auto child = c::ReadClergyShared31BDDA0RawAL12004(
        &m, Read, *operands.task_44_raw_u32, operands.child_rdx_identity,
        operands.child_r8_identity);
    // Copy computed child identities/readiness. No asserted native closure.
    const c::ClergyTaskBlock31BDDA0Child12004 packet{
        c::kClergyTaskBlockChildRva12004, child.rcx_raw_u32,
        child.rdx_identity, child.r8_identity, child.raw_al, child.source_ready};
    const auto result = c::ResolveClergyTaskBlock31B4810NullTooltip12004(
        &m, Read, operands, packet);
    if (!result.source_ready || !result.raw_al) return false;
    raw = *result.raw_al;
    return true;
  }
  static bool Position(void *opaque, std::uint32_t actual_owner,
                       std::uintptr_t actual_byte, std::uintptr_t actual_predicate,
                       std::uint8_t &raw) noexcept {
    auto &m = *static_cast<Memory *>(opaque);
    ++m.position_calls;
    const auto result = c::ReadClergyPositionRawAl12004(
        Read, &m, {actual_owner, actual_byte, actual_predicate, 0});
    if (!result.raw_al) return false;
    raw = *result.raw_al;
    return true;
  }
  c::ClergyMode0TaskRawAlResult12004 Run() {
    const c::ClergyMode0TaskRawAlReaders12004 readers{
        this, Initial, this, Position, &final_context,
        c::ReadClergyPosition31BD1A0Callback12004};
    return c::ReadClergyMode0TaskRawAl12004(this, Read, task, module, readers);
  }
};

void ConnectedTrue() {
  Memory m; m.Seed(); const auto r = m.Run();
  Require(r.raw_al == std::uint8_t{1} && r.initial_raw_al == std::uint8_t{0} &&
          r.position_raw_al == std::uint8_t{2} && r.final_raw_al == std::uint8_t{1},
          "source callbacks did not produce exact raw AL chain");
  Require(r.owner_id_raw32 == owner_raw && r.incumbent_id_raw32 == incumbent_raw,
          "raw full DWORD identities changed");
}
void ConnectedFalse() {
  Memory m; m.Seed(); m.Put(position + 0x2378, std::uint8_t{2});
  m.deny = position + 0x2338;
  const auto r = m.Run();
  Require(r.raw_al == std::uint8_t{0} && r.final_raw_al == std::uint8_t{0},
          "source final false must be available zero");
  Require(m.last_read == position + 0x2378, "final short circuit read +2338");
}
void InitialNonzeroShortCircuit() {
  Memory m; m.Seed(); m.Put(task + 0x40, std::uint32_t{0xFFFFFFFFU});
  m.deny = task + 0x30; const auto r = m.Run();
  Require(r.raw_al == std::uint8_t{0} && r.initial_raw_al == std::uint8_t{1} &&
          m.position_calls == 0 && m.last_read == task + 0x40,
          "actual initial nonzero did not stop the source chain");
}
void PositionZeroShortCircuit() {
  Memory m; m.Seed(); m.Put(position + 0x2377, std::uint8_t{0});
  m.deny = position + 0x2378; const auto r = m.Run();
  Require(r.raw_al == std::uint8_t{0} && r.position_raw_al == std::uint8_t{0} &&
          !r.final_raw_al && m.last_read == position + 0x2377,
          "actual position zero did not stop the source chain");
}
void GenerationBits() {
  Memory m; m.Seed(); m.Put(task + 0x30, incumbent_raw ^ 0x01000000U);
  m.Put(position + 0x2378, std::uint8_t{2}); const auto r = m.Run();
  Require(r.raw_al == std::uint8_t{1} &&
          r.compared_id_raw32 == (incumbent_raw ^ 0x01000000U),
          "raw DWORD comparison masked generation bits");
}
void InitialUnknown() {
  Memory m; m.Seed(); m.Put(position + 0x2374, std::uint8_t{0});
  m.Put(position + 0x1E38 + 0x4C, std::uint32_t{1}); const auto r = m.Run();
  Require(!r.raw_al && !r.initial_raw_al && m.position_calls == 0 &&
          r.failure == c::ClergyMode0TaskRawAlFailure12004::initial_source_unavailable,
          "initial dynamic child became a truth value");
}
void PositionUnknown() {
  Memory m; m.Seed(); m.Put(position + 0x2377, std::uint8_t{1});
  m.Put(position + 0x20A8 + 0x4C, std::uint32_t{1}); const auto r = m.Run();
  Require(!r.raw_al && !r.position_raw_al && !r.final_raw_al &&
          r.failure == c::ClergyMode0TaskRawAlFailure12004::position_source_unavailable,
          "position predicate missing source became a truth value");
}
void FinalSharedUnknown() {
  Memory m; m.Seed(); m.Put(position + 0x2178 + 0x4C, std::uint32_t{1});
  const auto r = m.Run();
  Require(!r.raw_al && !r.final_raw_al &&
          r.failure == c::ClergyMode0TaskRawAlFailure12004::final_source_unavailable,
          "final shared predicate missing source became a truth value");
}
void FinalDynamicUnknown() {
  Memory m; m.Seed(); m.Put(position + 0x2338, std::uint32_t{1});
  const auto r = m.Run();
  Require(!r.raw_al && !r.final_raw_al && m.last_read == task + 0x28,
          "dynamic numerical source replaced by a static value");
}
void GuardedReadFailure() {
  Memory m; m.Seed(); m.deny = task + 0x44; const auto r = m.Run();
  Require(!r.raw_al && m.position_calls == 0,
          "failed guarded read became a resolved initial child");
}
void CallbackUnknownPreservesOutput() {
  Memory m; m.Seed(); m.Put(position + 0x2338, std::uint32_t{1});
  std::uint8_t out = 219;
  const bool available = c::ReadClergyPosition31BD1A0Callback12004(
      &m.final_context, position, owner_raw, task + 0x28, 0,
      module + 0x48C8710, out);
  Require(!available && out == 219, "unavailable callback overwrote output byte");
}

struct Scenario { const char *name; void (*run)(); int logical_cases; };
void Cases26() { Require(RunClergyMode0TaskRawAl12004NewCases() == 0, "26c cases failed"); }
void Cases04() { Require(c::new_cases::RunClergyTaskBlock31B4810NullTooltip12004NewCases(), "04f cases failed"); }
void Cases06() { Require(c::RunClergyPositionRawAl31BDE9012004NewCases() == 0, "06e cases failed"); }
void Cases08() { Require(c::RunClergyPosition31BD1A0NewCases12004() == 13, "08e return contract changed"); }
constexpr Scenario scenarios[] = {
    {"26c-source-cases", Cases26, 7}, {"04f-source-cases", Cases04, 7},
    {"06e-source-cases", Cases06, 11}, {"08e-source-cases", Cases08, 13},
    {"20f-source-cases", c::VerifyClergyShared31BDDA0ConnectedCases12004, 9},
    {"15f-owned-mask-cases", RunRootScopeInitializer889F6012004NewCases, 4},
    {"connected-true", ConnectedTrue, 1}, {"connected-false", ConnectedFalse, 1},
    {"initial-nonzero-short-circuit", InitialNonzeroShortCircuit, 1},
    {"position-zero-short-circuit", PositionZeroShortCircuit, 1},
    {"generation-bits", GenerationBits, 1}, {"initial-unknown", InitialUnknown, 1},
    {"position-unknown", PositionUnknown, 1}, {"final-shared-unknown", FinalSharedUnknown, 1},
    {"final-dynamic-unknown", FinalDynamicUnknown, 1}, {"guarded-read-failure", GuardedReadFailure, 1},
    {"callback-unknown-output", CallbackUnknownPreservesOutput, 1}};
}

int main(int argc, char **argv) {
  const std::string_view selected = argc == 2 ? argv[1] : "";
  if (argc > 2) return 2;
  int failures = 0, count = 0;
  for (const auto &scenario : scenarios) {
    if (!selected.empty() && selected != scenario.name) continue;
    ++count;
    try {
      scenario.run();
      std::cout << scenario.name << "\tGREEN\t" << scenario.logical_cases << '\n';
    } catch (const std::exception &error) {
      ++failures;
      std::cout << scenario.name << "\tRED\t" << error.what() << '\n';
    } catch (...) {
      ++failures;
      std::cout << scenario.name << "\tRED\tunknown exception\n";
    }
  }
  return count == 0 ? 2 : (failures ? 1 : 0);
}
