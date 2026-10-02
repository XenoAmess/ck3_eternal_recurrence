#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12002::religion_reform {

inline constexpr std::uintptr_t kCanCreateRiteCoreRva = 0x14F56D0;
inline constexpr std::uintptr_t kCanEditRiteCoreRva = 0x14F5050;
inline constexpr std::size_t kCreationWindowActorIdOffset = 0xCC;
inline constexpr std::uintptr_t kDraftReasonStringDestroyRva = 0x856050;

// Both native methods accept an optional CString reason sink. A null sink
// takes the same boolean path used by the native data-model callbacks.
using DraftEligibilityGetter = bool (*)(const void *window, void *reason);
using DraftReasonStringDestroy = void (*)(void *reason);

struct EligibilityBindings {
  bool enabled = false;
  DraftEligibilityGetter can_create_rite = nullptr;
  DraftEligibilityGetter can_edit_rite = nullptr;
  DraftReasonStringDestroy destroy_reason_string = nullptr;
};

enum class EligibilityFailure {
  none,
  bindings_unavailable,
  current_window_unavailable,
  played_character_unavailable,
  draft_actor_mismatch,
  draft_actor_changed,
};

struct DraftEligibility {
  bool available = false;
  EligibilityFailure failure = EligibilityFailure::bindings_unavailable;
  std::optional<std::uint32_t> draft_actor_id;
  std::optional<bool> can_create_rite;
  std::optional<bool> can_edit_rite;
  std::optional<std::string> can_create_rite_native_text;
  std::optional<std::string> can_edit_rite_native_text;
};

EligibilityBindings BindEligibilityImage12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Called only by the existing paused application-main owner. The window is
// the real current CRiteCreationWindow obtained by the companion window
// observer; it is not a synthesized draft or a pointer from a query request.
// The player ID comes from the same actual played-character snapshot.
// This copies native booleans and their final native text; it neither
// creates/edits a Rite nor queues a
// command. A missing window cannot evaluate a headless proposed draft.
bool ReadCurrentDraftEligibility12002(const EligibilityBindings &bindings,
                                     const void *current_window,
                                     std::uint32_t played_character_id,
                                     DraftEligibility &output) noexcept;

const char *EligibilityFailureKey(EligibilityFailure failure) noexcept;
std::string SerializeDraftEligibility12002(const DraftEligibility &output);

} // namespace xar::ck3_12002::religion_reform
