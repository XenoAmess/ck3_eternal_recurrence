#include "xar_bridge/player_prisoner_ransom_private_v1.hpp"

// Value-only serialization is shared by the two independently bound builds.
// This source never calls a native reader or submits an interaction.
namespace xar::ck3_11906 {
namespace {
std::string_view FailureName(PlayerPrisonerRansomQuoteFailureV1 value) {
  switch (value) {
  case PlayerPrisonerRansomQuoteFailureV1::none: return "none";
  case PlayerPrisonerRansomQuoteFailureV1::not_evaluated:
    return "not_evaluated";
  case PlayerPrisonerRansomQuoteFailureV1::binding_unavailable:
    return "binding_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::frame_changed:
    return "frame_changed";
  case PlayerPrisonerRansomQuoteFailureV1::definition_unavailable:
    return "definition_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::role_unavailable:
    return "role_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::option_unavailable:
    return "option_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::option_context_roles_unverified:
    return "option_context_roles_unverified";
  case PlayerPrisonerRansomQuoteFailureV1::option_flag_identity_unverified:
    return "option_flag_identity_unverified";
  case PlayerPrisonerRansomQuoteFailureV1::option_mask_unreadable:
    return "option_mask_unreadable";
  case PlayerPrisonerRansomQuoteFailureV1::option_definition_pointer_unreadable:
    return "option_definition_pointer_unreadable";
  case PlayerPrisonerRansomQuoteFailureV1::option_definition_count_unreadable:
    return "option_definition_count_unreadable";
  case PlayerPrisonerRansomQuoteFailureV1::option_definition_count_unexpected:
    return "option_definition_count_unexpected";
  case PlayerPrisonerRansomQuoteFailureV1::option_data_pointer_unreadable:
    return "option_data_pointer_unreadable";
  case PlayerPrisonerRansomQuoteFailureV1::option_data_pointer_null:
    return "option_data_pointer_null";
  case PlayerPrisonerRansomQuoteFailureV1::option_context_count_unreadable:
    return "option_context_count_unreadable";
  case PlayerPrisonerRansomQuoteFailureV1::option_context_count_mismatch:
    return "option_context_count_mismatch";
  case PlayerPrisonerRansomQuoteFailureV1::option_byte_unreadable:
    return "option_byte_unreadable";
  case PlayerPrisonerRansomQuoteFailureV1::option_byte_out_of_range:
    return "option_byte_out_of_range";
  case PlayerPrisonerRansomQuoteFailureV1::option_mask_unexpected:
    return "option_mask_unexpected";
  case PlayerPrisonerRansomQuoteFailureV1::payer_below_one_gold:
    return "payer_below_one_gold";
  case PlayerPrisonerRansomQuoteFailureV1::payer_gold_read_unavailable:
    return "payer_gold_read_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::gold_options_not_selected_with_funded_payer:
    return "gold_options_not_selected_with_funded_payer";
  case PlayerPrisonerRansomQuoteFailureV1::extortionate_gold_option_requires_valuation:
    return "extortionate_gold_option_requires_valuation";
  case PlayerPrisonerRansomQuoteFailureV1::extortionate_final_can_send_false:
    return "extortionate_final_can_send_false";
  case PlayerPrisonerRansomQuoteFailureV1::final_can_send_false:
    return "final_can_send_false";
  case PlayerPrisonerRansomQuoteFailureV1::final_legality_unavailable:
    return "final_legality_unavailable";
  case PlayerPrisonerRansomQuoteFailureV1::quote_unavailable:
    return "quote_unavailable";
  }
  return "binding_unavailable";
}

} // namespace

std::string SerializePlayerPrisonerRansomQuotePrivateV1(
    const PlayerPrisonerRansomQuoteV1 &quote, std::uint64_t revision,
    std::int64_t date_raw, std::uint64_t proof_epoch) {
  std::string value =
      "{\"private_build\":true,\"read_only\":true,\"advertised\":false,"
      "\"action_surface_present\":false,\"status\":\"";
  value += quote.available ? "available" : "unavailable";
  value += "\",\"unavailable_reason\":";
  if (!quote.available) {
    value += '"';
    value += FailureName(quote.failure);
    value += '"';
    if (quote.failure == PlayerPrisonerRansomQuoteFailureV1::
                             option_definition_count_unexpected) {
      value += ",\"observed_definition_option_count\":";
      value += quote.observed_definition_option_count
                   ? std::to_string(*quote.observed_definition_option_count)
                   : "null";
      value += ",\"observed_context_option_count\":";
      value += quote.observed_context_option_count
                   ? std::to_string(*quote.observed_context_option_count)
                   : "null";
    }
    if (quote.failure == PlayerPrisonerRansomQuoteFailureV1::
                             option_mask_unexpected) {
      value += ",\"requested_option_index\":";
      value += quote.requested_option_index
                   ? std::to_string(*quote.requested_option_index)
                   : "null";
      value += ",\"observed_option_mask_bits\":";
      value += quote.observed_option_mask_bits
                   ? std::to_string(*quote.observed_option_mask_bits)
                   : "null";
    }
    value += '}';
    return value;
  }
  if (revision == 0 || date_raw <= 0 || proof_epoch == 0 || quote.failure !=
                                             PlayerPrisonerRansomQuoteFailureV1::none ||
      quote.jailer_character_id <= 0 || quote.payer_character_id <= 0 ||
      quote.prisoner_character_id <= 0 || quote.quoted_gold_raw <= 0 ||
      (quote.selected_option != "gold" &&
       quote.selected_option != "current_gold") ||
      quote.recipient_answer_status_raw > 2)
    return {};
  value += "null,\"snapshot_id\":\"native:" +
           std::to_string(revision) + "\",\"public_revision\":" +
           std::to_string(revision) + ",\"native_revision\":" +
           std::to_string(revision) + ",\"proof_epoch\":" +
           std::to_string(proof_epoch) + ",\"date_raw\":" +
           std::to_string(date_raw) + ",\"definition_key\":\"ransom_interaction\","
           "\"jailer_character_id\":" + std::to_string(quote.jailer_character_id) +
           ",\"payer_character_id\":" + std::to_string(quote.payer_character_id) +
           ",\"prisoner_character_id\":" +
           std::to_string(quote.prisoner_character_id) +
           ",\"selected_option\":\"" + std::string(quote.selected_option) +
           "\",\"can_send\":true,\"quoted_gold_raw\":" +
           std::to_string(quote.quoted_gold_raw) +
           ",\"raw_scale\":100000,\"recipient_acceptance_raw\":" +
           std::to_string(quote.recipient_acceptance_raw) +
           ",\"recipient_answer_status_raw\":" +
           std::to_string(quote.recipient_answer_status_raw) +
           ",\"would_accept_now\":" +
           std::string(quote.would_accept_now ? "true" : "false") +
           ",\"amount_is_acceptance_time_quote\":" +
           std::string(quote.amount_is_acceptance_time_quote ? "true" : "false") +
           '}';
  return value;
}

} // namespace xar::ck3_11906
