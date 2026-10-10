#include "xar_bridge/lifestyle_perk_predicate_288b1b0_12004.hpp"
#include <array>
#include <cstring>
#include <stdexcept>

namespace {
struct Word {
  std::uintptr_t address;
  std::uint64_t value;
  std::size_t width;
};
struct SourceRows {
  std::array<Word, 16> words;
  std::size_t reads = 0;
  std::size_t copied_bytes = 0;
  bool budget_exhausted = false;
};
bool ReadSourceRow(void *context, std::uintptr_t address, void *out,
                   std::size_t width) {
  auto &source = *static_cast<SourceRows *>(context);
  if (source.reads >= 64 || width > 512 - source.copied_bytes) {
    source.budget_exhausted = true;
    return false;
  }
  ++source.reads;
  source.copied_bytes += width;
  for (const auto &word : source.words) {
    if (word.address == address && word.width == width) {
      std::memcpy(out, &word.value, width);
      return true;
    }
  }
  return false;
}
}

// Synthetic raw operands exercise the newly connected source path. They are
// neither an observed native validator return nor a copied application frame.
// The owned-membership short circuit needs no TLS, prerequisites or trigger.
bool RunLifestyleSelectedPerkConnectedNewCase12004() {
  using namespace xar::ck3_12004::lifestyle;
  SourceRows source{{{
      {0x100000 + 0x5C67568, 0x1000, 8},
      {0x5000 + 0x20, 0x01000003, 4},
      {0x1000 + 0x2C, 4, 4},
      {0x1000 + 0x20, 0x2000, 8},
      {0x2000 + 3 * 16 + 8, 0x3000, 8},
      {0x3000 + 0x18, 0x02000003, 4},
      {0x100000 + 0x5C67570, 0x4000, 8},
      {0x4000 + 0x18, 0x0A000099, 4},
      {0x4000 + 0x1C, 0x43686172, 4},
      {0x4000 + 0x1D0, 0, 8},
      {0x5000 + 0x28, 0x6000, 8},
      {0x6000 + 0x38, 0x4744624F, 4},
      {0x4000 + 0x1B0, 0x7000, 8},
      {0x7220 + 0xC, 1, 4},
      {0x7220, 0x8000, 8},
      {0x8000, 0x6000, 8},
  }}};
  const LifestylePerkReadonlyAccess12004 access{0x100000, &source, &ReadSourceRow};
  const auto result = ReadLifestylePerkPredicate288B1B012004(access, 0x5000);
  const auto &inputs = result.inputs;
  if (inputs.prefix_admitted != true || inputs.used_fallback != true ||
      inputs.selected_character_identity != std::uintptr_t{0x4000} ||
      inputs.selected_perk_identity != std::uintptr_t{0x6000} ||
      inputs.requested_full_character_id_u32 != 0x01000003U ||
      inputs.indexed_character_full_id_u32 != 0x02000003U ||
      inputs.selected_character_full_id_u32 != 0x0A000099U ||
      !inputs.unavailable_reason.empty()) {
    throw std::runtime_error("new connected Lifestyle prefix differs");
  }
  if (result.value != false || !result.tail || result.tail->value != false || result.truth_trace ||
      !result.tail->unavailable_reason.empty() || !result.unavailable_reason.empty() ||
      source.reads != 18 || source.copied_bytes != 112 || source.budget_exhausted) {
    throw std::runtime_error("new connected Lifestyle owned-membership short circuit differs");
  }
  return true;
}
