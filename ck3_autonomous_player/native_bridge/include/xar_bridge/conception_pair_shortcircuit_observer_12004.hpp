#pragma once

#include "xar_bridge/conception_pair_shortcircuit_12004.hpp"
#include <cstddef>

namespace xar::ck3_12004 {

using ConceptionPairShortCircuit12004ReadMemory =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct ConceptionPairShortCircuit12004Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  ConceptionPairShortCircuit12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
};

ConceptionPairShortCircuit12004Bindings BindConceptionPairShortCircuit12004(
    std::uintptr_t image_base, std::string_view build_version,
    std::string_view executable_sha256,
    ConceptionPairShortCircuit12004ReadMemory read_memory,
    void *read_context = nullptr) noexcept;

// Root supplies existing core-resolved actual receiver/fullID from its current
// household row. Root also owns the existing before/after frame validation.
// All input reads are guarded copies; no original accessor or initializer.
ConceptionCharacterPredicate12004Read ReadConceptionCharacterPredicate12004(
    const ConceptionPairShortCircuit12004Bindings &bindings,
    std::uintptr_t character, std::uint32_t expected_full_id);

ConceptionPairShortCircuit12004Read ReadConceptionPairShortCircuit12004(
    const ConceptionPairShortCircuit12004Bindings &bindings,
    std::uintptr_t first_character, std::uint32_t first_full_id,
    std::uintptr_t second_character, std::uint32_t second_full_id);

} // namespace xar::ck3_12004
