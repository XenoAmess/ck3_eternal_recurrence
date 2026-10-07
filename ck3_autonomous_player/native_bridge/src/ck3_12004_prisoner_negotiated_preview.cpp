#include "xar_bridge/ck3_12004_prisoner_negotiated_preview.hpp"
#include "xar_bridge/ck3_12004_interaction_context.hpp"

namespace xar::ck3_12004 {

PrisonerNegotiatedBindings12004 BindPrisonerNegotiatedPreview12004(
    std::uintptr_t base, std::string_view actual_sha) noexcept {
  PrisonerNegotiatedBindings12004 bindings{};
  const auto current = BindInteractionContext12004(base, actual_sha);
  if (!current.enabled) return bindings;
  bindings.release = BindPrisonerReleasePreview12004(base, actual_sha);
  if (!bindings.release.enabled) return {};
  bindings.select_local_option = current.select_local_option;
  bindings.evaluate_answer = current.evaluate_answer;
  return bindings;
}

bool ReadPrisonerNegotiatedPreview12004(
    const PrisonerNegotiatedBindings12004 &bindings,
    const PrisonerReleasePreviewAccess12004 &access,
    std::uint32_t jailer, std::uint32_t prisoner, std::uint32_t requested_mask,
    PrisonerNegotiatedPreview12004 &output) noexcept {
  // No historical binder is called: custody/definition/layout and every
  // callback were supplied by the strict actual4 factories above.
  return ck3_12003::ReadPrisonerNegotiatedPreview12003(
      bindings, access, jailer, prisoner, requested_mask, output);
}

bool ReadPrisonerNegotiatedCollectionRow12004(
    const PrisonerNegotiatedBindings12004 &bindings,
    const PrisonerReleasePreviewAccess12004 &access,
    const bridge::PlayerPrisonerCollectionSnapshotV1 &collection,
    std::uint32_t ordinal, std::uint32_t requested_mask,
    std::array<PrisonerNegotiatedPreview12004,
        bridge::kPlayerPrisonerMaximumRowsV1> &previews) noexcept {
  if (requested_mask == 0 ||
      (requested_mask & ~kPrisonerReleaseAllOptionMask12004) != 0 ||
      collection.returned_count > previews.size())
    return false;
  for (std::uint32_t index = 0; index < collection.returned_count; ++index) {
    previews[index] = {};
    previews[index].requested_option_mask_bits = requested_mask;
    previews[index].observation.unavailable_reason = "not_evaluated";
  }
  if (!collection.available || !collection.collection_complete ||
      ordinal >= collection.returned_count || collection.frame.played_character_id <= 0)
    return false;
  return ReadPrisonerNegotiatedPreview12004(bindings, access,
      static_cast<std::uint32_t>(collection.frame.played_character_id),
      collection.rows[ordinal].full_character_id, requested_mask, previews[ordinal]);
}

std::string SerializePrisonerNegotiatedPreview12004(
    const PrisonerNegotiatedPreview12004 &preview) {
  return ck3_12003::SerializePrisonerNegotiatedPreview12003(preview);
}

} // namespace xar::ck3_12004
