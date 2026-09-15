#pragma once

#include "domain_construction_application_main_runtime_v1.hpp"

#include <cstdint>

namespace xar::ck3::shared {

// Exact CK3 1.19.0.6, immediately before 0x18D18F3. The native helper owns
// these addresses only for this synchronous call; no caller may retain them.
struct DomainConstructionCostGateRegistersV1 final {
  std::uintptr_t rbp = 0U;
  std::uintptr_t rbx = 0U;
  std::uintptr_t rdi = 0U;
};

struct DomainConstructionCostGateAdmissionV1 final {
  bool exact_build_admitted = false;
  bool session_live = false;
  std::uint32_t application_main_thread_id = 0U;
  std::uint32_t current_thread_id = 0U;
  research::DomainConstructionCandidateSnapshotBindingV1 binding;
};

enum class DomainConstructionCostGateFailureV1 : std::uint8_t {
  none = 0,
  exact_build,
  application_main,
  session,
  binding,
  source_address,
  candidate_identity,
  source_sample,
};

struct DomainConstructionCostGateOwnedResultV1 final {
  DomainConstructionCostGateFailureV1 failure =
      DomainConstructionCostGateFailureV1::none;
  research::DomainConstructionOwnedCollectorSampleV1 sample;
};

// Address derivation is version-bound: rdi is the selected 0x28 row,
// [rbp-0x41] is its projected eight-qword cost, and rbx is the corresponding
// eight-qword resource balance. The returned frame is borrowed, not owned.
[[nodiscard]] DomainConstructionCostGateFailureV1
BorrowDomainConstructionCostGateFrameV1(
    const DomainConstructionCostGateAdmissionV1& admission,
    const DomainConstructionCostGateRegistersV1& registers,
    DomainConstructionBorrowedCollectorFrameV1& frame) noexcept;

// Copies all source values before the cost helper returns. A resource-known
// rejection is observable; an affordable candidate stays unready until the
// independent native final-legality callback has been observed.
[[nodiscard]] DomainConstructionCostGateOwnedResultV1
ReadDomainConstructionCostGateOwnedV1(
    const DomainConstructionCostGateAdmissionV1& admission,
    const DomainConstructionCostGateRegistersV1& registers,
    research::DomainConstructionReadMemoryV1 read_memory,
    void* read_context);

}  // namespace xar::ck3::shared
