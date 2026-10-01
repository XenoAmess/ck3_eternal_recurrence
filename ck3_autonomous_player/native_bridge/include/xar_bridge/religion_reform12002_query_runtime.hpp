#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/religion_doctrine12002_selection.hpp"
#include "xar_bridge/religion_reform12002_choices.hpp"
#include "xar_bridge/religion_reform12002_costs.hpp"
#include "xar_bridge/religion_reform12002_eligibility.hpp"
#include "xar_bridge/religion_reform12002_rite.hpp"
#include "xar_bridge/religion_reform12002_willingness.hpp"

#include <string>

namespace xar::ck3_12002::religion_reform::query {

// The existing application-main mailbox owner supplies the image and epoch.
// Every component uses this core binding; no request accepts a native pointer.
struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  religion::Bindings context{};
  rite::Bindings rite_model{};
  MainRiteBindings main_rite{};
  DraftWindowBindings window{};
  CostBindings costs{};
  EligibilityBindings eligibility{};
  DraftChoiceBindings choices{};
};

struct Observation {
  bool available = false;
  std::string failure = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  religion::Context context{};
  rite::Model rite_model{};
  MainRiteUnreformed main_rite{};
  DraftWindowView current_window{};
  CostQuote draft_costs{};
  DraftEligibility draft_eligibility{};
  DraftChoices popup_choices{};
  religion::doctrine12002::CurrentDoctrineSelection current_doctrine_selection{};
};

Bindings BindReformQueryImage12002(std::uintptr_t module_base,
                                 std::string_view executable_sha256) noexcept;

// Read-only current state. An absent/hidden creation window is a legitimate
// observation and leaves draft-only values unavailable. This never opens a
// window, initializes a draft, picks a doctrine/tenet or queues a command.
bool ReadPlayedReformQuery12002(const Bindings &bindings,
                              std::uint64_t capture_epoch,
                              Observation &output) noexcept;

// Raw popup rows remain separate from the actual final Doctrine selection
// observer. The unclosed full Tenet CanPick path remains unknown; aggregate
// final_choice_legality_readiness stays false.
std::string SerializePlayedReformQuery12002(const Observation &observation);

} // namespace xar::ck3_12002::religion_reform::query
