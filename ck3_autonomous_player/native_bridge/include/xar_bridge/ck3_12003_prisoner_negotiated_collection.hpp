#pragma once

#include "xar_bridge/ck3_12003_prisoner_negotiated_preview.hpp"
#include "xar_bridge/protocol.hpp"

namespace xar::ck3_12003 {

// The existing compact protocol carries this optional unsigned request input.
// Zero is the internal absent-field sentinel; a present zero is rejected.
inline bool ParsePrisonerNegotiatedRequestMask12003(
    std::string_view payload, std::uint32_t &requested_mask) noexcept {
  requested_mask = 0;
  if (payload.find("\"release_option_mask_bits\"") == std::string_view::npos)
    return true;
  std::uint64_t raw = 0;
  if (!bridge::JsonUnsignedField(payload, "release_option_mask_bits", raw) ||
      raw == 0 || raw > kPrisonerReleaseAllOptionMask12003)
    return false;
  requested_mask = static_cast<std::uint32_t>(raw);
  return true;
}

// The actual mailbox collector and new whole-wire fixture use this same
// selected-row routing. Request identity is metadata; observed masks, roles,
// CanSend, costs and answers are supplied only by the actual native leaf.
inline bool ReadPrisonerNegotiatedCollectionRow12003(
    const PrisonerNegotiatedBindings12003 &bindings,
    const PrisonerReleasePreviewAccess12003 &access,
    const bridge::PlayerPrisonerCollectionSnapshotV1 &collection,
    std::uint32_t ordinal, std::uint32_t requested_mask,
    std::array<PrisonerNegotiatedPreview12003,
        bridge::kPlayerPrisonerMaximumRowsV1> &previews) noexcept {
  if (requested_mask == 0 ||
      (requested_mask & ~kPrisonerReleaseAllOptionMask12003) != 0 ||
      collection.returned_count > previews.size())
    return false;
  for (std::uint32_t index = 0; index < collection.returned_count; ++index) {
    previews[index] = {};
    previews[index].requested_option_mask_bits = requested_mask;
  }
  if (!collection.available || !collection.collection_complete ||
      ordinal >= collection.returned_count || collection.frame.played_character_id <= 0)
    return false;
  return ReadPrisonerNegotiatedPreview12003(bindings, access,
      static_cast<std::uint32_t>(collection.frame.played_character_id),
      collection.rows[ordinal].full_character_id, requested_mask, previews[ordinal]);
}

} // namespace xar::ck3_12003
