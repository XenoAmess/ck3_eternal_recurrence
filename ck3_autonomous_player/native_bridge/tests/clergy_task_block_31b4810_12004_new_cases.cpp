#include "xar_bridge/clergy_task_block_31b4810_12004.hpp"

#include <cstring>
#include <map>
#include <vector>

namespace xar::ck3_12004::religion::clergy::new_cases {
namespace {
constexpr std::uintptr_t kTask = 0x10000;
constexpr std::uintptr_t kType = 0x20000;
constexpr std::uintptr_t kPosition = 0x30000;
constexpr std::uint32_t kOwner = 0x07000002U;

struct CopiedTask {
  std::map<std::uintptr_t, std::vector<unsigned char>> fields;
  std::size_t task40_reads = 0;
  template <typename T> void Put(std::uintptr_t address, T value) {
    auto &field = fields[address];
    field.resize(sizeof(T));
    std::memcpy(field.data(), &value, sizeof(T));
  }
  static bool Read(void *context, const void *address, void *destination,
                   std::size_t bytes) noexcept {
    auto &copy = *static_cast<CopiedTask *>(context);
    const auto key = reinterpret_cast<std::uintptr_t>(address);
    if (key == kTask + 0x40) ++copy.task40_reads;
    const auto field = copy.fields.find(key);
    if (field == copy.fields.end() || field->second.size() != bytes) return false;
    std::memcpy(destination, field->second.data(), bytes);
    return true;
  }
};

CopiedTask Inputs() {
  CopiedTask task;
  task.Put(kTask + 0x18, kType);
  task.Put(kType + 0x40, kPosition);
  task.Put(kTask + 0x44, kOwner);
  return task;
}

ClergyTaskBlock31BDDA0Child12004 Child(std::uint8_t raw_al) {
  ClergyTaskBlock31BDDA0Child12004 child{};
  child.actual_callee_rva = kClergyTaskBlockChildRva12004;
  child.rcx_raw_u32 = kOwner;
  child.rdx_identity = kPosition + 0x2374;
  child.r8_identity = kPosition + 0x1E38;
  child.raw_al = raw_al;
  child.source_ready = true;
  return child;
}

bool ChildZeroSkipsTask40() {
  auto task = Inputs();
  const auto input = ReadClergyTaskBlock31B4810Operands12004(&task, CopiedTask::Read, kTask);
  const auto result = ResolveClergyTaskBlock31B4810NullTooltip12004(
      &task, CopiedTask::Read, input, Child(std::uint8_t{0}));
  return input.source_ready && input.task_identity == kTask &&
      input.child_rdx_identity == kPosition + 0x2374 &&
      input.child_r8_identity == kPosition + 0x1E38 &&
      input.task_44_raw_u32 == kOwner && result.source_ready &&
      result.raw_al == std::uint8_t{0} && task.task40_reads == 0;
}

bool ChildNonzeroReadsActualTask40(std::uint32_t task40, std::uint8_t expected_al) {
  auto task = Inputs();
  task.Put(kTask + 0x40, task40);
  const auto input = ReadClergyTaskBlock31B4810Operands12004(&task, CopiedTask::Read, kTask);
  const auto result = ResolveClergyTaskBlock31B4810NullTooltip12004(
      &task, CopiedTask::Read, input, Child(std::uint8_t{7}));
  return result.source_ready && result.raw_al == expected_al &&
      result.task_40_raw_u32 == task40 && result.task_identity == kTask &&
      task.task40_reads == 1;
}

bool UnreadReachedTask40RemainsUnknown() {
  auto task = Inputs();
  const auto input = ReadClergyTaskBlock31B4810Operands12004(&task, CopiedTask::Read, kTask);
  const auto result = ResolveClergyTaskBlock31B4810NullTooltip12004(
      &task, CopiedTask::Read, input, Child(std::uint8_t{1}));
  return !result.source_ready && !result.raw_al && task.task40_reads == 1;
}

bool DifferentLiteralOperandIsNotTheChild() {
  auto task = Inputs();
  const auto input = ReadClergyTaskBlock31B4810Operands12004(&task, CopiedTask::Read, kTask);
  auto child = Child(std::uint8_t{1});
  ++child.rdx_identity;
  const auto result = ResolveClergyTaskBlock31B4810NullTooltip12004(
      &task, CopiedTask::Read, input, child);
  return !result.source_ready && !result.raw_al && task.task40_reads == 0;
}

bool MissingMandatoryChildIsNotFalse() {
  auto task = Inputs();
  task.Put(kTask + 0x40, std::uint32_t{0x07000003});
  const auto input = ReadClergyTaskBlock31B4810Operands12004(&task, CopiedTask::Read, kTask);
  const auto result = ResolveClergyTaskBlock31B4810NullTooltip12004(
      &task, CopiedTask::Read, input, {});
  return !result.source_ready && !result.raw_al && task.task40_reads == 0;
}

bool UnclosedMandatoryChildIsNotFalse() {
  auto task = Inputs();
  task.Put(kTask + 0x40, std::uint32_t{0x07000003});
  const auto input = ReadClergyTaskBlock31B4810Operands12004(&task, CopiedTask::Read, kTask);
  auto child = Child(std::uint8_t{0});
  child.source_ready = false;
  const auto result = ResolveClergyTaskBlock31B4810NullTooltip12004(
      &task, CopiedTask::Read, input, child);
  return !result.source_ready && !result.raw_al && task.task40_reads == 0;
}
} // namespace

// New no-main cases for the current base packet composition; no old replay.
bool RunClergyTaskBlock31B4810NullTooltip12004NewCases() {
  return ChildZeroSkipsTask40() &&
      ChildNonzeroReadsActualTask40(0xFFFFFFFFU, std::uint8_t{1}) &&
      ChildNonzeroReadsActualTask40(0x07000003U, std::uint8_t{0}) &&
      UnreadReachedTask40RemainsUnknown() && DifferentLiteralOperandIsNotTheChild() &&
      MissingMandatoryChildIsNotFalse() && UnclosedMandatoryChildIsNotFalse();
}
} // namespace xar::ck3_12004::religion::clergy::new_cases
