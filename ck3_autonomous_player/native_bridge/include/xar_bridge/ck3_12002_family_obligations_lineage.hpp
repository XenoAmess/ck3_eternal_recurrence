#pragma once

#include "xar_bridge/ck3_12002_family.hpp"

namespace xar::ck3_12002::family_obligations_lineage {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

inline constexpr std::uintptr_t kNativeChildHousePreviewParentRva = 0x13753A0;
inline constexpr std::uintptr_t kNativeMarriageMatchOfferVtableRva = 0x454E460;
using ReadChildHousePreviewParent = void *(*)(const void *offer);

struct Bindings {
  bool enabled = false;
  FamilyBindings family{};
  FamilyProjectionBindings projection{};
  ReadChildHousePreviewParent native_preview_parent = nullptr;
  std::uintptr_t native_offer_vtable = 0;
};

struct Snapshot {
  bool available = false;
  std::int32_t played_character_id = -1;
  std::int64_t date_raw = 0;
  std::int32_t subject_character_id = -1;
  std::int32_t candidate_character_id = -1;
  bool requested_matrilineal_option = false;
  bool selected_matrilineal_option = false;
  bool effective_matrilineal_if_accepted = false;
  bool complete_can_send = false;
  std::int32_t native_selected_parent_character_id = -1;
  family_value::Lineage native_preview_lineage{};
};

Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept;

// Reuses the finalized exact marriage context and the native MatchOffer house
// preview getter. It observes a prospective UI result, never an unborn child,
// a birth probability, or a realized dynasty continuation reward.
bool Read(const Bindings &, std::int32_t subject_character_id,
          std::int32_t candidate_character_id, bool request_matrilineal_option,
          Snapshot &, std::string_view *reason = nullptr) noexcept;

#endif
} // namespace xar::ck3_12002::family_obligations_lineage
