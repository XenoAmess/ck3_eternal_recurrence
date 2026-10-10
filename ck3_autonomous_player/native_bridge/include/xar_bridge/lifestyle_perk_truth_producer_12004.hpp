#pragma once
#include "xar_bridge/lifestyle_character_scope_12004.hpp"
#include "xar_bridge/source_read_leaf_frame_12004.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12004::lifestyle {

inline constexpr std::uintptr_t kLifestylePerkTruthProducerRva12004 = 0x37998D0;
inline constexpr std::uintptr_t kLifestylePerkTruthNullTailRva12004 = 0x372DF10;
inline constexpr std::uintptr_t kLifestylePerkTruthChildRva12004 = 0x372E000;
inline constexpr std::uintptr_t kLifestylePerkTruthEvaluationFlagRva12004 = 0x5D1DADC;

// Copied inputs and source-projected child output, never active native truth.
// The selected caller applies TEST AL and returns canonical BL, while the two
// intervening native wrappers preserve the original raw byte.
struct LifestylePerkTruthProducer37998D0Result12004 {
  std::uintptr_t selected_perk_identity = 0;
  std::optional<std::uintptr_t> compiled_trigger_receiver_identity;
  std::optional<std::uint16_t> context_root_word;
  std::optional<std::uint64_t> context_full_id_payload;
  std::optional<std::uint8_t> evaluation_flag_raw_u8;
  std::optional<SourceLeafFrame12004> child_frame;
  // Existing same-query raw addresses, retained for source-first target closure.
  // They never represent virtual getter or evaluator outputs.
  std::optional<std::uintptr_t> trigger_vtable_raw;
  std::optional<std::uintptr_t> root_kind_getter_slot58_raw;
  std::optional<std::uintptr_t> root_mask_getter_slot60_raw;
  std::optional<std::uintptr_t> final_evaluator_slotc8_raw;
  std::optional<std::uint8_t> source_projected_returned_raw_u8;
  std::optional<bool> value;
  bool context_projection_available = false;
  bool copied_frame_ready = false;
  bool input_leaf_ready = false;
  bool child_source_value_ready = false;
  bool native_callback_executed = false;
  bool actual_trigger_evaluation_observed = false;
  std::string unavailable_reason;
};

// The stable scope is 18's noncopyable source-equivalent storage. Its known
// bytes are read through the definition mask, and unknown holes never become0.
// Caller frame metadata is copied from an existing accepted query separately;
// neither a context projection nor a fixture creates current frame facts.
// Missing final virtual producer/witness remains an unknown optional value.
LifestylePerkTruthProducer37998D0Result12004
ReadLifestylePerkTruthProducer37998D012004(
    const LifestylePerkReadonlyAccess12004 &,
    std::uintptr_t selected_perk,
    const LifestyleCharacterScope12004 &stable_context,
    const SourceReadFrame12004 *caller_frame = nullptr) noexcept;

} // namespace xar::ck3_12004::lifestyle
