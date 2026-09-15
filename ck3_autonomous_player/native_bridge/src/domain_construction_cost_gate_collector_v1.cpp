#include "domain_construction_cost_gate_collector_v1.hpp"

#include <array>
#include <limits>

namespace xar::ck3::shared {
namespace {

bool BindingReady(
    const research::DomainConstructionCandidateSnapshotBindingV1& binding) {
  return binding.generation != 0U && (binding.generation & 1U) == 0U &&
         binding.proof_epoch != 0U && binding.date_raw > 0;
}

bool Readable(const std::uintptr_t address, const std::size_t bytes) {
  return address != 0U &&
         address <= (std::numeric_limits<std::uintptr_t>::max)() -
                        (bytes - 1U);
}

}  // namespace

DomainConstructionCostGateFailureV1 BorrowDomainConstructionCostGateFrameV1(
    const DomainConstructionCostGateAdmissionV1& admission,
    const DomainConstructionCostGateRegistersV1& registers,
    DomainConstructionBorrowedCollectorFrameV1& frame) noexcept {
  frame = {};
  if (!admission.exact_build_admitted) {
    return DomainConstructionCostGateFailureV1::exact_build;
  }
  if (admission.application_main_thread_id == 0U ||
      admission.current_thread_id != admission.application_main_thread_id) {
    return DomainConstructionCostGateFailureV1::application_main;
  }
  if (!admission.session_live) {
    return DomainConstructionCostGateFailureV1::session;
  }
  if (!BindingReady(admission.binding)) {
    return DomainConstructionCostGateFailureV1::binding;
  }
  if (registers.rbp < 0x41U ||
      !Readable(registers.rdi, research::kDomainConstructionCandidateRowBytesV1) ||
      !Readable(registers.rbp - 0x41U,
                research::kDomainConstructionResourceVectorBytesV1) ||
      !Readable(registers.rbx,
                research::kDomainConstructionResourceVectorBytesV1)) {
    return DomainConstructionCostGateFailureV1::source_address;
  }
  frame.observed_binding = admission.binding;
  frame.candidate_row_address = registers.rdi;
  frame.cost_vector_address = registers.rbp - 0x41U;
  frame.resource_balance_vector_address = registers.rbx;
  return DomainConstructionCostGateFailureV1::none;
}

DomainConstructionCostGateOwnedResultV1 ReadDomainConstructionCostGateOwnedV1(
    const DomainConstructionCostGateAdmissionV1& admission,
    const DomainConstructionCostGateRegistersV1& registers,
    const research::DomainConstructionReadMemoryV1 read_memory,
    void* read_context) {
  DomainConstructionCostGateOwnedResultV1 result{};
  DomainConstructionBorrowedCollectorFrameV1 frame{};
  result.failure =
      BorrowDomainConstructionCostGateFrameV1(admission, registers, frame);
  if (result.failure != DomainConstructionCostGateFailureV1::none) {
    return result;
  }
  if (read_memory == nullptr) {
    result.failure = DomainConstructionCostGateFailureV1::source_sample;
    return result;
  }
  std::array<std::uint8_t,
             research::kDomainConstructionCandidateRowBytesV1> row{};
  if (!read_memory(read_context, frame.candidate_row_address, row.data(),
                   row.size())) {
    result.failure = DomainConstructionCostGateFailureV1::source_sample;
    return result;
  }
  const auto identity = research::DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), read_memory, read_context);
  if (!identity.ready) {
    result.failure = DomainConstructionCostGateFailureV1::candidate_identity;
    return result;
  }
  research::DomainConstructionExactCollectorMemorySampleV1 source{};
  source.admission.exact_build_admitted = admission.exact_build_admitted;
  source.admission.application_main_thread_id =
      admission.application_main_thread_id;
  source.admission.current_thread_id = admission.current_thread_id;
  source.admission.session_live = admission.session_live;
  source.admission.expected_binding = admission.binding;
  source.admission.observed_binding = frame.observed_binding;
  source.candidate_row_address = frame.candidate_row_address;
  source.cost_vector_address = frame.cost_vector_address;
  source.resource_balance_vector_address = frame.resource_balance_vector_address;
  source.final_legality.branch =
      identity.kind == research::DomainConstructionCandidateKindV1::
                           building_in_holding
          ? research::DomainConstructionNativeFinalLegalityBranchV1::building
          : research::DomainConstructionNativeFinalLegalityBranchV1::new_holding;
  source.final_legality.observed = false;
  result.sample = research::AdaptDomainConstructionExactCollectorMemoryV1(
      source, read_memory, read_context);
  if (!result.sample.ready &&
      result.sample.failure !=
          research::DomainConstructionCollectorSourceFailureV1::
              final_observation) {
    result.failure = DomainConstructionCostGateFailureV1::source_sample;
  }
  return result;
}

}  // namespace xar::ck3::shared
