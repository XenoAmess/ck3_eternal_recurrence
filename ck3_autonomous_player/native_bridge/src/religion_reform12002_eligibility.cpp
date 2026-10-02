#include "xar_bridge/religion_reform12002_eligibility.hpp"

#include <array>
#include <cstring>
#include <utility>

namespace xar::ck3_12002::religion_reform {
namespace {
// Exact 1.20.0.3 reflection callers 0x14FB0A0 / 0x14FAF10 obtain these
// reasons through 0x14F5780 / 0x14F5110 and release them with 0x856050.
// The game's allocator owns any heap bytes; the DLL only copies them.
struct NativeDraftReasonString {
  std::array<char, 16> storage{};
  std::uint64_t size = 0;
  std::uint64_t capacity = 15;
};
static_assert(sizeof(NativeDraftReasonString) == 32);
static_assert(offsetof(NativeDraftReasonString, size) == 0x10);
static_assert(offsetof(NativeDraftReasonString, capacity) == 0x18);

bool ReadEligibilityWithReason(DraftEligibilityGetter getter,
                               const void *window,
                               DraftReasonStringDestroy destroy,
                               std::optional<std::string> &text) {
  // Legacy injected bindings without a lifecycle reader keep their original
  // final bool; null text describes a reason that was not copied.
  if (!destroy) return getter(window, nullptr);
  NativeDraftReasonString native{};
  const bool allowed = getter(window, &native);
  const char *data = native.storage.data();
  if (native.capacity >= 16)
    std::memcpy(&data, native.storage.data(), sizeof(data));
  if (native.size <= native.capacity && (!native.size || data)) {
    if (native.size)
      text.emplace(data, static_cast<std::size_t>(native.size));
    else
      text.emplace();
  }
  destroy(&native);
  return allowed;
}

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

std::string Text(const std::optional<std::string> &text) {
  if (!text) return "null";
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const auto character : *text) {
    const auto byte = static_cast<unsigned char>(character);
    if (character == '"' || character == '\\') {
      out += '\\';
      out += character;
    } else if (byte < 32) {
      out += "\\u00";
      out += hex[byte >> 4];
      out += hex[byte & 15];
    } else {
      out += character;
    }
  }
  return out + '"';
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
  bindings.destroy_reason_string = reinterpret_cast<DraftReasonStringDestroy>(
      base + kDraftReasonStringDestroyRva);
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
  std::optional<std::string> create_text;
  std::optional<std::string> edit_text;
  const bool create = ReadEligibilityWithReason(
      bindings.can_create_rite, window, bindings.destroy_reason_string, create_text);
  const bool edit = ReadEligibilityWithReason(
      bindings.can_edit_rite, window, bindings.destroy_reason_string, edit_text);
  if (ReadActor(window) != actor) {
    output.failure = EligibilityFailure::draft_actor_changed;
    return false;
  }
  output.can_create_rite = create;
  output.can_edit_rite = edit;
  output.can_create_rite_native_text = std::move(create_text);
  output.can_edit_rite_native_text = std::move(edit_text);
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
      ",\"can_edit_rite\":" + Boolean(output.can_edit_rite) +
      ",\"can_create_rite_native_text\":" + Text(output.can_create_rite_native_text) +
      ",\"can_edit_rite_native_text\":" + Text(output.can_edit_rite_native_text) + "}";
}

} // namespace xar::ck3_12002::religion_reform
