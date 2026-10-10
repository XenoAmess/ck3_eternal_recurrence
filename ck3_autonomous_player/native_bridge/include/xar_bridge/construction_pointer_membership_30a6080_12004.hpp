#pragma once
#include "xar_bridge/construction_context_predicate_2c25010_12004.hpp"
#include <array>
#include <cstdint>
#include <optional>

namespace xar::ck3_12004::construction_owner_mode3 {
inline constexpr std::uintptr_t kConstructionPointerMembershipRva12004=0x30A6080;
inline constexpr std::size_t kConstructionPointerMembershipMaximumProbes12004=32;
enum class PointerMembershipFailure12004 : std::uint8_t {
  none, exact_build, read_callback, copied_operands, collection_header,
  probe_address, probe_copy,
};
enum class PointerMembershipPath12004 : std::uint8_t {
  unavailable, iterator_at_end_false, candidate_greater_false,
  candidate_index_true, candidate_minus_one_false,
};
struct PointerMembershipProbe12004 {
  std::uintptr_t address=0;
  std::optional<std::uintptr_t> copied_value;
};
struct ConstructionPointerMembership30A6080Result12004 {
  ContextPredicateInputsV1 inputs;
  std::uintptr_t actual_rcx=0, actual_rdx=0;
  std::optional<std::uintptr_t> collection_pointer;
  std::optional<std::int32_t> count_raw_i32;
  std::uintptr_t end_pointer_bits=0, selected_pointer_bits=0;
  std::optional<std::int32_t> selected_index_raw_i32;
  std::uint32_t probe_count=0;
  std::array<PointerMembershipProbe12004,kConstructionPointerMembershipMaximumProbes12004> probes{};
  PointerMembershipFailure12004 failure=PointerMembershipFailure12004::none;
  PointerMembershipPath12004 path=PointerMembershipPath12004::unavailable;
  std::optional<bool> value;
};
// Pure source model over the parent's admitted paused-frame raw reader. The
// collection remains in native order; only the naturally demanded qwords are
// copied. No native getter, object tag, registry resolution or sort is used.
ConstructionPointerMembership30A6080Result12004
ReadConstructionPointerMembership30A6080V1(const RawReceiverAccessV1 &,
    const ContextPredicateInputsV1 &,std::uintptr_t actual_rcx,
    std::uintptr_t actual_rdx) noexcept;
// Exact typed21c callback. false is unavailable and leaves output unchanged;
// true can return native ALfalse. Context is unused; it is not a native ABI.
bool ReadConstructionPointerMembership30A6080ChildV1(void *,
    const RawReceiverAccessV1 &,const ContextPredicateInputsV1 &,
    std::uintptr_t actual_rcx,std::uintptr_t actual_rdx,bool &output) noexcept;
} // namespace xar::ck3_12004::construction_owner_mode3
