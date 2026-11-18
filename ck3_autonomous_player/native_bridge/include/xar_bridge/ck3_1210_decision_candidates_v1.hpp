#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_1210 {
inline constexpr char kDecisionCandidatesSchemaV1[] = "ck3_1210_decision_candidates_data_v1";
enum class DecisionCandidateSourceV1 { gui_cache, database_pool };
enum class DecisionCandidateReasonV1 {
  native_producer_not_installed, owner_not_held, frame_not_current,
  source_pins_unavailable, gui_actor_differs_from_snapshot,
  native_read_unavailable, not_queried, parameter_scope_unverified
};
struct DecisionCandidateExactRefV1 {
  std::string path, sha256;
  std::uint64_t bytes = 0;
  friend bool operator==(const DecisionCandidateExactRefV1 &, const DecisionCandidateExactRefV1 &) = default;
};
struct DecisionCandidateFrameV1 {
  std::string machine_id, session_id;
  std::uint32_t game_pid = 0;
  std::uint64_t game_creation_filetime = 0, connection_generation = 0, native_revision = 0;
  std::int32_t date_raw = 0, snapshot_actor_character_id = -1;
  friend bool operator==(const DecisionCandidateFrameV1 &, const DecisionCandidateFrameV1 &) = default;
};
// Metadata about the outer owner's capture, not a token minted by this leaf.
// owner_address identifies the source object: GUI list or database singleton.
struct DecisionCandidateCaptureV1 {
  DecisionCandidateFrameV1 frame{};
  DecisionCandidateExactRefV1 producer_source{};
  DecisionCandidateSourceV1 source = DecisionCandidateSourceV1::gui_cache;
  bool owner_held = false, paused_application_main_owner_held = false;
  std::uint32_t owner_thread_id = 0;
  std::uint64_t capture_epoch = 0, owner_address = 0;
  friend bool operator==(const DecisionCandidateCaptureV1 &, const DecisionCandidateCaptureV1 &) = default;
};
struct DecisionCandidateBindingsV1 {
  bool exact_build_admitted = false;
  std::uint64_t image_base = 0;
};
using DecisionCandidateCopyV1 = bool (*)(void *context, std::uint64_t source,
    void *destination, std::size_t size) noexcept;
struct DecisionCandidateAccessV1 {
  void *context = nullptr;
  // Required: no direct memcpy, OS/process API or native-call fallback.
  DecisionCandidateCopyV1 copy = nullptr;
};
using DecisionCandidateCurrentCaptureV1 = bool (*)(void *context,
    DecisionCandidateCaptureV1 &capture) noexcept;
struct DecisionCandidateReadContextV1 {
  DecisionCandidateCaptureV1 expected{};
  // External exact source/caller pins admission; binding an image does not set it.
  bool source_pins_admitted = false;
  // Must read the CURRENT capture under retained paused application-main
  // custody. Returning expected by value is not a production implementation.
  DecisionCandidateCurrentCaptureV1 read_current_capture = nullptr;
  void *current_capture_context = nullptr;
};
struct DecisionCandidateDefinitionV1 {
  std::uint64_t address = 0;
  // This package does not infer string layout from legacy versions. Definition
  // keys remain null until their exact1210 copy contract is independently bound.
  std::optional<std::string> key;
  friend bool operator==(const DecisionCandidateDefinitionV1 &, const DecisionCandidateDefinitionV1 &) = default;
};
struct DecisionCandidateRowV1 {
  DecisionCandidateDefinitionV1 definition{};
  std::uint32_t database_index = 0, group_index = 0, row_index = 0;
  std::uint64_t parameter_address = 0, gui_owner_address = 0;
  // Full signed32 identity read from the row; scope remap may change actor.
  std::int32_t row_actor_character_id = -1;
  std::uint8_t cached_enabled_byte = 0;
  // No observed/CanExecute variant exists in this DATA version.
  DecisionCandidateReasonV1 command_unobserved_reason = DecisionCandidateReasonV1::not_queried;
  friend bool operator==(const DecisionCandidateRowV1 &, const DecisionCandidateRowV1 &) = default;
};
struct DecisionCandidatesObservationV1 {
  DecisionCandidateCaptureV1 capture{};
  std::optional<std::int32_t> gui_global_actor_character_id;
  bool completed = false;
  std::vector<DecisionCandidateRowV1> candidates;
  DecisionCandidateReasonV1 unavailable_reason = DecisionCandidateReasonV1::native_producer_not_installed;
};
DecisionCandidateBindingsV1 BindDecisionCandidateImageV1(std::uint64_t image_base,
    std::string_view executable_sha256) noexcept;
// Two complete value/address transcripts, bracketed by three fresh capture
// callbacks. Reads the actual +260 GUI groups or +50/+5C DB pool. It does not
// evaluate script predicates, rebuild a GUI list, call CanExecute, or submit.
// A failed/partial scan clears all rows; a real empty scan retains [].
bool ReadDecisionCandidatesV1(const DecisionCandidateBindingsV1 &bindings,
    const DecisionCandidateReadContextV1 &context, DecisionCandidateAccessV1 access,
    DecisionCandidatesObservationV1 &output) noexcept;
// Strictly the slot14 proposed DATA contract, not a transport envelope or wire
// capability. Pointers/u64 identities use decimal strings. Invalid outer
// metadata returns false and no bytes; invalid rows yield unavailable/null.
bool SerializeDecisionCandidatesV1(const DecisionCandidatesObservationV1 &observation,
    std::string &output) noexcept;
} // namespace xar::ck3_1210
