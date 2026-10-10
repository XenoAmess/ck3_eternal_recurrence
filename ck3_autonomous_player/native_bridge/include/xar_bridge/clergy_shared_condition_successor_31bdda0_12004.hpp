#pragma once

#include "xar_bridge/clergy_shared_condition_31bdda0_12004.hpp"
#include "xar_bridge/generic_trigger_receiver_372df10_12004.hpp"

namespace xar::ck3_12004::religion::clergy {

// Separate successor: the qualified20f reader and its result ABI stay intact.
// Run its literal byte/DWORD gates once. Only condition_child_required calls
// the typed09 software producer with originalR8, WORD4 and zext rawowner.
// The caller supplies an existing borrowed query carrier in child; a missing
// original frame identity remains unavailable. No frame or native Eval is
// manufactured here. Optional child diagnostics use09's same copied result.
ClergyShared31BDDA0RawAL12004 ReadClergyShared31BDDA0WithGenericChild12004(
    void *read_context, ReadMemory, std::uint32_t owner_raw_u32,
    std::uintptr_t literal_rdx, std::uintptr_t literal_r8,
    xar::ck3_12004::GenericTriggerOwnerScopeChildContext12004 &child);

} // namespace xar::ck3_12004::religion::clergy
