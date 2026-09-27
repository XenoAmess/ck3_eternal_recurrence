#pragma once

#include "xar_bridge/ck3_11906.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

enum class PlayerPrisonerRansomQuoteFailureV1 : std::uint8_t {
  none,
  not_evaluated,
  binding_unavailable,
  frame_changed,
  definition_unavailable,
  role_unavailable,
  option_unavailable,
  final_legality_unavailable,
  quote_unavailable,
};

struct PlayerPrisonerRansomQuoteV1 {
  bool available = false;
  PlayerPrisonerRansomQuoteFailureV1 failure =
      PlayerPrisonerRansomQuoteFailureV1::binding_unavailable;
  std::int32_t jailer_character_id = -1;
  std::int32_t payer_character_id = -1;
  std::int32_t prisoner_character_id = -1;
  std::string_view selected_option{};
  std::int64_t quoted_gold_raw = 0;
  std::int64_t recipient_acceptance_raw = 0;
  std::uint8_t recipient_answer_status_raw = 3;
  bool would_accept_now = false;
  // Current-gold is sampled before send; stock on_accept saves payer gold
  // again. Even the script-value quote is not an observed transfer.
  bool amount_is_acceptance_time_quote = false;
};

PlayerPrisonerRansomQuoteV1 ReadPlayerPrisonerRansomQuotePrivateV1(
    const Bindings &bindings, std::uintptr_t module_base,
    std::int32_t jailer_character_id,
    std::int32_t prisoner_character_id) noexcept;

std::string SerializePlayerPrisonerRansomQuotePrivateV1(
    const PlayerPrisonerRansomQuoteV1 &quote, std::uint64_t revision,
    std::int64_t date_raw, std::uint64_t proof_epoch);

} // namespace xar::ck3_11906
