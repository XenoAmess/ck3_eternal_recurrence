#include "xar_bridge/character_interaction_proposal_payload_source_extension_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <sstream>

namespace xar::ck3_11906 {
namespace {

using Failure = game::CharacterInteractionProposalPayloadSourceFailureV1;
using Result = game::ReadCharacterInteractionProposalPayloadSourceResultV1;

constexpr std::int32_t kInvalidId = -1;
constexpr std::uint32_t kSlotMask = 0x00FFFFFFU;
constexpr std::int32_t kMaximumSelectedTitles = 128;
constexpr std::int32_t kMaximumSendOptions = 32;

constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageSlotObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kLandedTitleIdentityOffset = 0x10;

constexpr std::size_t kContextDefinitionOffset = 0x00;
constexpr std::size_t kContextActorOffset = 0x2D8;
constexpr std::size_t kContextRecipientOffset = 0x2DC;
constexpr std::size_t kContextSecondaryActorOffset = 0x2E0;
constexpr std::size_t kContextSecondaryRecipientOffset = 0x2E4;
constexpr std::size_t kContextIntermediaryOffset = 0x2E8;
constexpr std::size_t kContextSelectedOptionsDataOffset = 0x300;
constexpr std::size_t kContextSelectedOptionsCapacityOffset = 0x308;
constexpr std::size_t kContextSelectedOptionsCountOffset = 0x30C;
constexpr std::size_t kContextSpecialDataOffset = 0x330;
constexpr std::size_t kDefinitionSelectedOptionsCountOffset = 0x2554;

constexpr std::size_t kGrantTitlesOfferVtableOffset = 0x00;
constexpr std::size_t kGrantTitlesOfferIdsDataOffset = 0x08;
constexpr std::size_t kGrantTitlesOfferIdsCapacityOffset = 0x10;
constexpr std::size_t kGrantTitlesOfferIdsCountOffset = 0x14;

constexpr std::array<std::string_view, 6> kSupportedKeys{
    "educate_child_interaction",
    "offer_ward_interaction",
    "offer_guardianship_interaction",
    "grant_titles_interaction",
    "grant_vassal_interaction",
    "ransom_interaction",
};

constexpr bool IsEducation(std::string_view key) noexcept {
  return key == kSupportedKeys[0] || key == kSupportedKeys[1] ||
         key == kSupportedKeys[2];
}

template <typename T>
bool Read(const CharacterInteractionProposalPayloadSourceAccessV1 &access,
          const void *base, std::size_t offset, T &output) noexcept {
  if (base == nullptr || access.read_memory == nullptr ||
      offset > std::numeric_limits<std::uintptr_t>::max() -
                   reinterpret_cast<std::uintptr_t>(base)) {
    return false;
  }
  const auto address = reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(base) + offset);
  return access.read_memory(access.context, address, &output, sizeof(output));
}

bool AddRva(std::uintptr_t module, std::uintptr_t rva,
            std::uintptr_t &output) noexcept {
  if (module == 0 || module > std::numeric_limits<std::uintptr_t>::max() - rva)
    return false;
  output = module + rva;
  return true;
}

bool ExactBindings(
    const CharacterInteractionProposalPayloadSourceEnvironmentV1 &environment)
    noexcept {
  if (environment.offline_fixture) return true;
  std::uintptr_t character_slot = 0;
  std::uintptr_t title_slot = 0;
  return AddRva(environment.module_base,
                kCharacterInteractionProposalPayloadCharacterStorageSlotRvaV1,
                character_slot) &&
         AddRva(environment.module_base,
                kCharacterInteractionProposalPayloadTitleStorageSlotRvaV1,
                title_slot) &&
         reinterpret_cast<std::uintptr_t>(environment.character_storage_slot) ==
             character_slot &&
         reinterpret_cast<std::uintptr_t>(
             environment.landed_title_storage_slot) == title_slot;
}

bool SameSnapshot(
    const CharacterInteractionPreviewFrameV1 &frame,
    const game::CharacterInteractionPreviewV1 &preview) noexcept {
  return frame.paused &&
         frame.snapshot_id == preview.snapshot_id &&
         frame.public_revision == preview.public_revision &&
         frame.native_revision == preview.native_revision &&
         frame.proof_epoch == preview.proof_epoch &&
         frame.date_raw == preview.date_raw;
}

void Fail(game::CharacterInteractionProposalPayloadSourceV1 &output,
          Failure failure, std::string_view reason) {
  output.available = false;
  output.failure = failure;
  output.reason.assign(reason);
}

void *ResolveFullId(
    const CharacterInteractionProposalPayloadSourceEnvironmentV1 &environment,
    const CharacterInteractionProposalPayloadSourceAccessV1 &access,
    void **storage_slot, std::int32_t full_id,
    std::size_t identity_offset) noexcept {
  if (storage_slot == nullptr || full_id == kInvalidId) return nullptr;
  void *storage = nullptr;
  if (!access.read_memory(access.context, storage_slot, &storage,
                          sizeof(storage)) ||
      storage == nullptr) {
    return nullptr;
  }
  std::int32_t capacity = 0;
  void *slots = nullptr;
  if (!Read(access, storage, kStorageCapacityOffset, capacity) ||
      !Read(access, storage, kStorageSlotsOffset, slots) || slots == nullptr) {
    return nullptr;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & kSlotMask;
  if (capacity <= 0 || index >= static_cast<std::uint32_t>(capacity) ||
      index > (std::numeric_limits<std::uintptr_t>::max() -
               reinterpret_cast<std::uintptr_t>(slots) -
               kStorageSlotObjectOffset) /
                  kStorageSlotStride) {
    return nullptr;
  }
  const auto slot = reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(slots) +
      static_cast<std::uintptr_t>(index) * kStorageSlotStride);
  void *object = nullptr;
  std::int32_t stored_id = kInvalidId;
  if (!Read(access, slot, kStorageSlotObjectOffset, object) ||
      object == nullptr || !Read(access, object, identity_offset, stored_id) ||
      stored_id != full_id) {
    return nullptr;
  }
  (void)environment;
  return object;
}

bool ReadOptions(
    const CharacterInteractionProposalPayloadSourceAccessV1 &access,
    const void *context, const void *definition, std::string_view key,
    std::uint32_t &mask, bool &religious) noexcept {
  void *data = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  std::int32_t definition_count = 0;
  if (!Read(access, context, kContextSelectedOptionsDataOffset, data) ||
      !Read(access, context, kContextSelectedOptionsCapacityOffset, capacity) ||
      !Read(access, context, kContextSelectedOptionsCountOffset, count) ||
      !Read(access, definition, kDefinitionSelectedOptionsCountOffset,
            definition_count) ||
      count < 0 || count > kMaximumSendOptions || count != definition_count ||
      capacity < count || (count != 0 && data == nullptr)) {
    return false;
  }
  mask = 0;
  religious = false;
  for (std::int32_t index = 0; index < count; ++index) {
    std::uint8_t selected = 0;
    if (!Read(access, data, static_cast<std::size_t>(index), selected) ||
        selected > 1) {
      return false;
    }
    if (selected != 0) mask |= (std::uint32_t{1} << index);
  }
  // In all three frozen education definitions the authored option order is
  // convert_culture, convert_faith, university, hook.
  religious = IsEducation(key) && (mask & (std::uint32_t{1} << 1)) != 0;
  return true;
}

std::string Fingerprint(
    const game::CharacterInteractionProposalPayloadSourceV1 &source) {
  std::ostringstream stream;
  stream << "cipps:v1:" << source.interaction_key << ":a="
         << source.actor_character_id << ":r=" << source.recipient_character_id
         << ":sa=" << source.secondary_actor_character_id << ":sr="
         << source.secondary_recipient_character_id << ":i="
         << source.intermediary_character_id << ":o="
         << source.selected_option_mask << ":t=";
  for (std::size_t index = 0; index < source.selected_title_ids.size(); ++index) {
    if (index != 0) stream << ',';
    stream << source.selected_title_ids[index];
  }
  return stream.str();
}

bool ResolveCharacter(
    const CharacterInteractionProposalPayloadSourceEnvironmentV1 &environment,
    const CharacterInteractionProposalPayloadSourceAccessV1 &access,
    std::int32_t id) noexcept {
  return ResolveFullId(environment, access, environment.character_storage_slot,
                       id, kCharacterIdentityOffset) != nullptr;
}

bool ResolveOptionalCharacter(
    const CharacterInteractionProposalPayloadSourceEnvironmentV1 &environment,
    const CharacterInteractionProposalPayloadSourceAccessV1 &access,
    std::int32_t id) noexcept {
  return id == kInvalidId || ResolveCharacter(environment, access, id);
}

} // namespace

game::ReadCharacterInteractionProposalPayloadSourceResultV1
ReadCharacterInteractionProposalPayloadSourceV1(
    const CharacterInteractionProposalPayloadSourceEnvironmentV1 &environment,
    const CharacterInteractionProposalPayloadSourceAccessV1 &access,
    const game::CharacterInteractionPreviewV1 &bound_preview,
    game::CharacterInteractionProposalPayloadSourceV1 &output) noexcept {
  output = {};
  try {
    const auto key = std::string_view(bound_preview.definition.canonical_key);
    if (!environment.enabled || key.empty() ||
        bound_preview.status != game::CharacterInteractionPreviewStatusV1::available ||
        !bound_preview.readiness.same_frame_ready ||
        bound_preview.roles.actor_character_id == kInvalidId ||
        bound_preview.roles.recipient_character_id == kInvalidId ||
        access.capture_collector == nullptr || access.read_memory == nullptr ||
        access.lookup_definition == nullptr) {
      Fail(output, Failure::invalid_request, "invalid_request");
      return Result::unavailable;
    }
    if (std::find(kSupportedKeys.begin(), kSupportedKeys.end(), key) ==
        kSupportedKeys.end()) {
      Fail(output, Failure::interaction_not_supported,
           "interaction_not_supported");
      return Result::unavailable;
    }
    if (!environment.exact_build_admitted ||
        environment.admitted_executable_sha256 !=
            kCharacterInteractionProposalPayloadSourceExecutableSha256V1) {
      Fail(output, Failure::exact_build_not_admitted,
           "exact_build_not_admitted");
      return Result::unavailable;
    }
    if (!ExactBindings(environment) || environment.character_storage_slot == nullptr ||
        environment.landed_title_storage_slot == nullptr) {
      Fail(output, Failure::native_bindings_unavailable,
           "native_bindings_unavailable");
      return Result::unavailable;
    }

    CharacterInteractionProposalPayloadCollectorMemoryV1 collector{};
    if (!access.capture_collector(access.context, key,
                                  bound_preview.roles.actor_character_id,
                                  bound_preview.roles.recipient_character_id,
                                  collector) ||
        collector.interaction_context == nullptr) {
      Fail(output, Failure::collector_capture_failed,
           "collector_capture_failed");
      return Result::unavailable;
    }
    if (!SameSnapshot(collector.frame, bound_preview)) {
      Fail(output, Failure::collector_frame_mismatch,
           "collector_frame_mismatch");
      return Result::unavailable;
    }

    void *canonical_definition = nullptr;
    void *observed_definition = nullptr;
    if (!access.lookup_definition(access.context, key, canonical_definition) ||
        canonical_definition == nullptr ||
        !Read(access, collector.interaction_context, kContextDefinitionOffset,
              observed_definition)) {
      Fail(output, Failure::collector_context_malformed,
           "collector_context_malformed");
      return Result::unavailable;
    }
    if (observed_definition != canonical_definition) {
      Fail(output, Failure::definition_identity_mismatch,
           "definition_identity_mismatch");
      return Result::unavailable;
    }

    output.snapshot_id = collector.frame.snapshot_id;
    output.public_revision = collector.frame.public_revision;
    output.native_revision = collector.frame.native_revision;
    output.proof_epoch = collector.frame.proof_epoch;
    output.date_raw = collector.frame.date_raw;
    output.interaction_key.assign(key);
    if (!Read(access, collector.interaction_context, kContextActorOffset,
              output.actor_character_id) ||
        !Read(access, collector.interaction_context, kContextRecipientOffset,
              output.recipient_character_id) ||
        !Read(access, collector.interaction_context,
              kContextSecondaryActorOffset,
              output.secondary_actor_character_id) ||
        !Read(access, collector.interaction_context,
              kContextSecondaryRecipientOffset,
              output.secondary_recipient_character_id) ||
        !Read(access, collector.interaction_context, kContextIntermediaryOffset,
              output.intermediary_character_id) ||
        output.actor_character_id != bound_preview.roles.actor_character_id ||
        output.recipient_character_id !=
            bound_preview.roles.recipient_character_id ||
        !ResolveCharacter(environment, access, output.actor_character_id) ||
        !ResolveCharacter(environment, access, output.recipient_character_id) ||
        !ResolveOptionalCharacter(environment, access,
                                  output.secondary_actor_character_id) ||
        !ResolveOptionalCharacter(environment, access,
                                  output.secondary_recipient_character_id) ||
        !ResolveOptionalCharacter(environment, access,
                                  output.intermediary_character_id)) {
      Fail(output, Failure::role_identity_unavailable,
           "role_identity_unavailable");
      return Result::unavailable;
    }

    bool religious_option_selected = false;
    if (!ReadOptions(access, collector.interaction_context, canonical_definition,
                     key, output.selected_option_mask,
                     religious_option_selected)) {
      Fail(output, Failure::selected_options_malformed,
           "selected_options_malformed");
      return Result::unavailable;
    }
    if (religious_option_selected) {
      Fail(output, Failure::religious_option_deferred,
           "religious_option_deferred");
      return Result::unavailable;
    }

    auto &payload = output.payload;
    if (key == "educate_child_interaction") {
      payload.semantic_subject_character_id =
          output.secondary_recipient_character_id;
      payload.semantic_object_character_id = output.secondary_actor_character_id;
    } else if (key == "offer_ward_interaction") {
      payload.semantic_subject_character_id = output.secondary_actor_character_id;
      payload.semantic_object_character_id =
          output.secondary_recipient_character_id;
    } else if (key == "offer_guardianship_interaction") {
      payload.semantic_subject_character_id =
          output.secondary_recipient_character_id;
      payload.semantic_object_character_id = output.secondary_actor_character_id;
    } else if (key == "grant_vassal_interaction") {
      payload.semantic_subject_character_id = output.secondary_actor_character_id;
      payload.semantic_object_character_id = output.recipient_character_id;
    } else if (key == "ransom_interaction") {
      payload.semantic_subject_character_id =
          output.secondary_recipient_character_id;
      payload.semantic_object_character_id = output.actor_character_id;
      if (output.selected_option_mask == 0) {
        Fail(output, Failure::selected_options_malformed,
             "ransom_option_missing");
        return Result::unavailable;
      }
    } else {
      payload.semantic_subject_character_id = output.recipient_character_id;
      payload.semantic_object_character_id = output.actor_character_id;
      void *offer = nullptr;
      void *vtable = nullptr;
      void *ids = nullptr;
      std::int32_t capacity = 0;
      std::int32_t count = 0;
      std::uintptr_t expected_vtable = 0;
      if (!Read(access, collector.interaction_context, kContextSpecialDataOffset,
                offer) ||
          offer == nullptr ||
          !Read(access, offer, kGrantTitlesOfferVtableOffset, vtable) ||
          !AddRva(environment.module_base,
                  kCharacterInteractionProposalPayloadGrantTitlesOfferVtableRvaV1,
                  expected_vtable) ||
          reinterpret_cast<std::uintptr_t>(vtable) != expected_vtable) {
        Fail(output, Failure::title_offer_identity_mismatch,
             "title_offer_identity_mismatch");
        return Result::unavailable;
      }
      if (!Read(access, offer, kGrantTitlesOfferIdsDataOffset, ids) ||
          !Read(access, offer, kGrantTitlesOfferIdsCapacityOffset, capacity) ||
          !Read(access, offer, kGrantTitlesOfferIdsCountOffset, count) ||
          count <= 0 || count > kMaximumSelectedTitles || capacity < count ||
          ids == nullptr) {
        Fail(output, Failure::selected_titles_malformed,
             "selected_titles_malformed");
        return Result::unavailable;
      }
      output.selected_title_ids.reserve(static_cast<std::size_t>(count));
      for (std::int32_t index = 0; index < count; ++index) {
        std::int32_t title_id = kInvalidId;
        if (!Read(access, ids, static_cast<std::size_t>(index) * sizeof(title_id),
                  title_id) ||
            ResolveFullId(environment, access,
                          environment.landed_title_storage_slot, title_id,
                          kLandedTitleIdentityOffset) == nullptr ||
            std::find(output.selected_title_ids.begin(),
                      output.selected_title_ids.end(),
                      title_id) != output.selected_title_ids.end()) {
          Fail(output, Failure::selected_title_identity_unavailable,
               "selected_title_identity_unavailable");
          return Result::unavailable;
        }
        output.selected_title_ids.push_back(title_id);
      }
      payload.selected_title_count =
          static_cast<std::uint32_t>(output.selected_title_ids.size());
    }

    if (payload.semantic_subject_character_id == kInvalidId ||
        payload.semantic_object_character_id == kInvalidId ||
        !ResolveCharacter(environment, access,
                          payload.semantic_subject_character_id) ||
        !ResolveCharacter(environment, access,
                          payload.semantic_object_character_id)) {
      Fail(output, Failure::role_identity_unavailable,
           "role_identity_unavailable");
      return Result::unavailable;
    }
    payload.complete = true;
    payload.religious_option_selected = false;
    payload.ordinary_feudal_or_clan_vassalization = false;
    payload.fingerprint = Fingerprint(output);
    output.available = true;
    output.failure = Failure::none;
    output.reason = "available";
    return Result::available;
  } catch (...) {
    output = {};
    Fail(output, Failure::collector_context_malformed,
         "collector_context_malformed");
    return Result::unavailable;
  }
}

std::string_view CharacterInteractionProposalPayloadSourceFailureKeyV1(
    Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::invalid_request: return "invalid_request";
  case Failure::interaction_not_supported: return "interaction_not_supported";
  case Failure::exact_build_not_admitted: return "exact_build_not_admitted";
  case Failure::native_bindings_unavailable:
    return "native_bindings_unavailable";
  case Failure::collector_capture_failed: return "collector_capture_failed";
  case Failure::collector_frame_mismatch: return "collector_frame_mismatch";
  case Failure::collector_context_malformed:
    return "collector_context_malformed";
  case Failure::definition_identity_mismatch:
    return "definition_identity_mismatch";
  case Failure::role_identity_unavailable: return "role_identity_unavailable";
  case Failure::selected_options_malformed: return "selected_options_malformed";
  case Failure::religious_option_deferred: return "religious_option_deferred";
  case Failure::title_offer_identity_mismatch:
    return "title_offer_identity_mismatch";
  case Failure::selected_titles_malformed: return "selected_titles_malformed";
  case Failure::selected_title_identity_unavailable:
    return "selected_title_identity_unavailable";
  }
  return "unknown";
}

} // namespace xar::ck3_11906
