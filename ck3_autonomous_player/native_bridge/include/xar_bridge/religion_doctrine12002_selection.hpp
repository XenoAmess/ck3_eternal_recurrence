#pragma once

#include "xar_bridge/religion_reform12002_choices.hpp"

namespace xar::ck3_12002::religion::doctrine12002 {

inline constexpr std::uintptr_t kDoctrineItemShouldDisplayCallbackRva = 0xEE4CC0;
inline constexpr std::uintptr_t kDoctrineItemCanPickCallbackRva = 0xEE4E60;
inline constexpr std::size_t kDoctrineShownTriggerOffset = 0x1B8;
inline constexpr std::size_t kDoctrinePickTriggerOffset = 0xE8;

struct DoctrineSelectionRow {
  religion_reform::DraftDoctrineChoice choice{};
  bool native_should_display = false;
  bool selectable = false;
  std::string selection_blocker = "none";
};
struct CurrentDoctrineSelection {
  bool available = false;
  bool popup_observed = false;
  bool selection_ready = false;
  std::string failure = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> source_rite_id;
  std::vector<DoctrineSelectionRow> rows;
  std::vector<std::string> selectable_doctrine_keys;
};

// Same owning-thread, current-epoch actual popup producer output only. The
// current native model supplies identities; this observer adds ShouldDisplay
// and the visible/enabled conjunction. No pointer or arbitrary actor wire input.
bool ObserveCurrentDraftDoctrineSelection12002(
    const religion_reform::DraftChoiceBindings &bindings,
    const religion_reform::DraftChoices &current_popup,
    std::uint64_t capture_epoch, CurrentDoctrineSelection &output) noexcept;
// Standalone convenience entry: invokes the existing actual popup producer.
bool ReadCurrentDraftDoctrineSelection12002(
    const religion_reform::DraftChoiceBindings &bindings,
    std::uint64_t capture_epoch, CurrentDoctrineSelection &output) noexcept;
std::string SerializeCurrentDraftDoctrineSelection12002(const CurrentDoctrineSelection &value);

} // namespace xar::ck3_12002::religion::doctrine12002
