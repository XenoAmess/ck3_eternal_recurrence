#include "xar_bridge/religion_reform12002_eligibility.hpp"

#include <cstring>

namespace xar::ck3_12002::religion_reform {
namespace {
std::uint32_t ReadActor(const void *window) noexcept {
  std::uint32_t actor{};
  std::memcpy(&actor, static_cast<const std::byte *>(window) +
                         kCreationWindowActorIdOffset,
              sizeof(actor));
  return actor;
}

std::string Boolean(const std::optional<bool> &value) {
  if (!value) return "null";
  return *value ? "true" : "false";
}
} // namespace

EligibilityBindings BindEligibilityImage12002(std::uintptr_t base,
                                               std::string_view sha) noexcept {
  EligibilityBindings bindings{};
  if (!base || sha != kExecutableSha256) return bindings;
  bindings.enabled = true;
  bindings.can_create_rite = reinterpret_cast<DraftEligibilityGetter>(
      base + kCanCreateRiteCoreRva);
  bindings.can_edit_rite = reinterpret_cast<DraftEligibilityGetter>(
      base + kCanEditRiteCoreRva);
  return bindings;
}

bool ReadCurrentDraftEligibility12002(const EligibilityBindings &bindings,
                                     const void *window,
                                     std::uint32_t played_character_id,
                                     DraftEligibility &output) noexcept {
  output = {};
  if (!bindings.enabled || !bindings.can_create_rite || !bindings.can_edit_rite)
    return false;
  if (!window) {
    output.failure = EligibilityFailure::current_window_unavailable;
    return false;
  }
  if (played_character_id == 0xFFFFFFFFU) {
    output.failure = EligibilityFailure::played_character_unavailable;
    return false;
  }
  const auto actor = ReadActor(window);
  output.draft_actor_id = actor;
  if (actor != played_character_id) {
    output.failure = EligibilityFailure::draft_actor_mismatch;
    return false;
  }
  const bool create = bindings.can_create_rite(window, nullptr);
  const bool edit = bindings.can_edit_rite(window, nullptr);
  if (ReadActor(window) != actor) {
    output.failure = EligibilityFailure::draft_actor_changed;
    return false;
  }
  output.can_create_rite = create;
  output.can_edit_rite = edit;
  output.available = true;
  output.failure = EligibilityFailure::none;
  return true;
}

const char *EligibilityFailureKey(EligibilityFailure failure) noexcept {
  switch (failure) {
  case EligibilityFailure::none: return "none";
  case EligibilityFailure::bindings_unavailable: return "bindings_unavailable";
  case EligibilityFailure::current_window_unavailable:
    return "current_window_unavailable";
  case EligibilityFailure::played_character_unavailable:
    return "played_character_unavailable";
  case EligibilityFailure::draft_actor_mismatch: return "draft_actor_mismatch";
  case EligibilityFailure::draft_actor_changed: return "draft_actor_changed";
  }
  return "bindings_unavailable";
}

std::string SerializeDraftEligibility12002(const DraftEligibility &output) {
  return "{\"schema\":\"ck3_12002_rite_draft_eligibility_v1\","
      "\"scope\":\"actual_current_rite_creation_window_draft\","
      "\"available\":" + std::string(output.available ? "true" : "false") +
      ",\"unavailable_reason\":" +
      (output.available ? std::string("null")
                        : std::string("\"") + EligibilityFailureKey(output.failure) + "\"") +
      ",\"draft_actor_id\":" +
      (output.draft_actor_id ? std::to_string(*output.draft_actor_id) : "null") +
      ",\"can_create_rite\":" + Boolean(output.can_create_rite) +
      ",\"can_edit_rite\":" + Boolean(output.can_edit_rite) + "}";
}

} // namespace xar::ck3_12002::religion_reform
