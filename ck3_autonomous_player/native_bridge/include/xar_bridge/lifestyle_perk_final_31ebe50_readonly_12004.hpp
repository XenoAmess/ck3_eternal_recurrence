#pragma once

#include "xar_bridge/lifestyle_perk_predicate_inputs_12004.hpp"

namespace xar::ck3_12004::lifestyle {
struct LifestylePerkTruthProducer37998D0Result12004;
// Exact 288B219 tail ABI: selected Perk, resolved Character, null diagnostic
// writer. R9 command identity is unused by the actual truth-producing path.
// Returns a current optional condition only; never invokes native validators.
// The optional software output is reset at entry and copied from the same
// reached truth call only. It is separate from the native diagnostic pointer.
LifestylePerkReadonlyPredicate12004 ReadLifestylePerkFinal31EBE5012004(
    const LifestylePerkReadonlyAccess12004 &access,
    std::uintptr_t selected_perk, std::uintptr_t resolved_character,
    std::uintptr_t diagnostic_writer_identity = 0,
    LifestylePerkTruthProducer37998D0Result12004 *reached_truth_observation =
        nullptr) noexcept;
} // namespace xar::ck3_12004::lifestyle
