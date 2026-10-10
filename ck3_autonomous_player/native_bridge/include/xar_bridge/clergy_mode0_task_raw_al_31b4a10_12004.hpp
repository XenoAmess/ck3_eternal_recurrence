#pragma once

#include "xar_bridge/ck3_12004_clergy_appointment.hpp"

#include <cstdint>
#include <optional>

namespace xar::ck3_12004::religion::clergy {

inline constexpr std::uintptr_t kClergyMode0TaskPredicateRva12004 = 0x31B4A10;
inline constexpr std::uintptr_t kClergyMode0StaticArgumentRva12004 = 0x48C8710;

// Software source readers only. These signatures are not native function ABIs
// and must never be populated by rebasing native addresses. False means the
// required source input is unavailable; raw AL zero is an independent value.
using ClergyMode0InitialRawAlReader12004 = bool (*)(
    void *, std::uintptr_t actual_task, std::uint8_t &raw_al) noexcept;
using ClergyMode0PositionRawAlReader12004 = bool (*)(
    void *, std::uint32_t owner_id_raw32, std::uintptr_t byte_input,
    std::uintptr_t predicate_input, std::uint8_t &raw_al) noexcept;
using ClergyMode0FinalRawAlReader12004 = bool (*)(
    void *, std::uintptr_t position, std::uint32_t owner_id_raw32,
    std::uintptr_t task_28_address, std::uint32_t comparison_raw32,
    std::uintptr_t static_argument5, std::uint8_t &raw_al) noexcept;

struct ClergyMode0TaskRawAlReaders12004 {
  void *initial_context{};
  ClergyMode0InitialRawAlReader12004 initial{}; // source 0x31B4810
  void *position_context{};
  ClergyMode0PositionRawAlReader12004 position{}; // source 0x31BDE90
  void *final_context{};
  ClergyMode0FinalRawAlReader12004 final{}; // source 0x31BD1A0
};

enum class ClergyMode0TaskRawAlBranch12004 : std::uint8_t {
  unavailable,
  initial_nonzero_returns_zero,
  position_zero_returns_zero,
  final_raw_al,
};

enum class ClergyMode0TaskRawAlFailure12004 : std::uint8_t {
  none,
  initial_source_unavailable,
  read_access_unavailable,
  task_type_unavailable,
  owner_raw32_unavailable,
  position_unavailable,
  incumbent_raw32_unavailable,
  compared_raw32_unavailable,
  operand_address_unavailable,
  position_source_unavailable,
  final_source_unavailable,
};

struct ClergyMode0TaskRawAlResult12004 {
  std::uintptr_t actual_task{};
  std::optional<std::uint8_t> raw_al;
  std::optional<std::uint8_t> initial_raw_al;
  std::optional<std::uint8_t> position_raw_al;
  std::optional<std::uint8_t> final_raw_al;
  std::optional<std::uintptr_t> task_type;
  std::optional<std::uintptr_t> position;
  std::optional<std::uint32_t> owner_id_raw32;
  std::optional<std::uint32_t> incumbent_id_raw32;
  std::optional<std::uint32_t> compared_id_raw32;
  ClergyMode0TaskRawAlBranch12004 branch{
      ClergyMode0TaskRawAlBranch12004::unavailable};
  ClergyMode0TaskRawAlFailure12004 failure{
      ClergyMode0TaskRawAlFailure12004::initial_source_unavailable};
};

// Source-exact null-tooltip projection of the 165-byte actual4 body. The caller
// supplies the existing base query's actual Task, exact module base and guarded
// ReadMemory adapter. Existing query admission owns build, frame and full-ID
// checks. This leaf does not construct a frame, resolve IDs, call native code,
// submit a query or derive appointment eligibility. A missing required software
// child reader stays unavailable, including a reader with an unclosed branch.
ClergyMode0TaskRawAlResult12004 ReadClergyMode0TaskRawAl12004(
    void *read_context, ReadMemory read_memory, std::uintptr_t actual_task,
    std::uintptr_t actual_module_base,
    const ClergyMode0TaskRawAlReaders12004 &readers) noexcept;

} // namespace xar::ck3_12004::religion::clergy
