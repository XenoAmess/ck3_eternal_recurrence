#include "xar_bridge/clergy_mode0_task_raw_al_31b4a10_12004.hpp"

#include <limits>

namespace xar::ck3_12004::religion::clergy {
namespace {

bool Address(std::uintptr_t base, std::uintptr_t offset,
             std::uintptr_t &output) noexcept {
  if (base == 0 || base > (std::numeric_limits<std::uintptr_t>::max)() - offset)
    return false;
  output = base + offset;
  return true;
}

template <class T>
bool Read(void *context, ReadMemory reader, std::uintptr_t base,
          std::uintptr_t offset, T &output) noexcept {
  std::uintptr_t address{};
  return reader && Address(base, offset, address) &&
      reader(context, reinterpret_cast<const void *>(address), &output,
             sizeof(output));
}

} // namespace

ClergyMode0TaskRawAlResult12004 ReadClergyMode0TaskRawAl12004(
    void *read_context, ReadMemory read_memory, std::uintptr_t actual_task,
    std::uintptr_t actual_module_base,
    const ClergyMode0TaskRawAlReaders12004 &readers) noexcept {
  ClergyMode0TaskRawAlResult12004 result{};
  result.actual_task = actual_task;

  // 31B4A20 -> 31B4810; 31B4A25/27 test AL and branch.
  std::uint8_t initial{};
  if (!readers.initial ||
      !readers.initial(readers.initial_context, actual_task, initial))
    return result;
  result.initial_raw_al = initial;
  if (initial != 0) {
    result.raw_al = std::uint8_t{0}; // 31B4A29 xor AL,AL; no later input is read.
    result.branch = ClergyMode0TaskRawAlBranch12004::initial_nonzero_returns_zero;
    result.failure = ClergyMode0TaskRawAlFailure12004::none;
    return result;
  }
  if (!read_memory) {
    result.failure = ClergyMode0TaskRawAlFailure12004::read_access_unavailable;
    return result;
  }

  // Preserve the native field demand order before 31B4A70.
  std::uintptr_t type{};
  if (!Read(read_context, read_memory, actual_task, 0x18, type) || type == 0) {
    result.failure = ClergyMode0TaskRawAlFailure12004::task_type_unavailable;
    return result;
  }
  result.task_type = type;
  std::uint32_t owner{};
  if (!Read(read_context, read_memory, actual_task, 0x44, owner)) {
    result.failure = ClergyMode0TaskRawAlFailure12004::owner_raw32_unavailable;
    return result;
  }
  result.owner_id_raw32 = owner;
  std::uintptr_t position{};
  if (!Read(read_context, read_memory, type, 0x40, position) || position == 0) {
    result.failure = ClergyMode0TaskRawAlFailure12004::position_unavailable;
    return result;
  }
  result.position = position;
  std::uint32_t incumbent{}, compared{};
  if (!Read(read_context, read_memory, actual_task, 0x40, incumbent)) {
    result.failure = ClergyMode0TaskRawAlFailure12004::incumbent_raw32_unavailable;
    return result;
  }
  result.incumbent_id_raw32 = incumbent;
  if (!Read(read_context, read_memory, actual_task, 0x30, compared)) {
    result.failure = ClergyMode0TaskRawAlFailure12004::compared_raw32_unavailable;
    return result;
  }
  result.compared_id_raw32 = compared;
  std::uintptr_t byte_input{}, predicate_input{};
  if (!Address(position, 0x2377, byte_input) ||
      !Address(position, 0x20A8, predicate_input)) {
    result.failure = ClergyMode0TaskRawAlFailure12004::operand_address_unavailable;
    return result;
  }

  // 31B4A70 -> 31BDE90. Values 2..255 remain nonzero raw bytes.
  std::uint8_t position_al{};
  if (!readers.position || !readers.position(readers.position_context, owner,
          byte_input, predicate_input, position_al)) {
    result.failure = ClergyMode0TaskRawAlFailure12004::position_source_unavailable;
    return result;
  }
  result.position_raw_al = position_al;
  if (position_al == 0) {
    result.raw_al = std::uint8_t{0}; // 31B4A77 -> 31B4A9B, AL is preserved as zero.
    result.branch = ClergyMode0TaskRawAlBranch12004::position_zero_returns_zero;
    result.failure = ClergyMode0TaskRawAlFailure12004::none;
    return result;
  }

  std::uintptr_t task_28{}, argument5{};
  if (!Address(actual_task, 0x28, task_28) ||
      !Address(actual_module_base, kClergyMode0StaticArgumentRva12004,
               argument5)) {
    result.failure = ClergyMode0TaskRawAlFailure12004::operand_address_unavailable;
    return result;
  }
  // 31B4A96 -> 31BD1A0, null tooltip argument6. The software adapter
  // receives the actual literal inputs; it may report a required branch unknown.
  std::uint8_t final_al{};
  if (!readers.final || !readers.final(readers.final_context, position, owner,
          task_28, compared != incumbent ? 1U : 0U, argument5, final_al)) {
    result.failure = ClergyMode0TaskRawAlFailure12004::final_source_unavailable;
    return result;
  }
  result.final_raw_al = final_al;
  result.raw_al = final_al; // Native epilogue preserves AL unchanged.
  result.branch = ClergyMode0TaskRawAlBranch12004::final_raw_al;
  result.failure = ClergyMode0TaskRawAlFailure12004::none;
  return result;
}

} // namespace xar::ck3_12004::religion::clergy
