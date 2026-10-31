#include "xar_bridge/family_marriage_send_outgoing_v2.hpp"
#include "xar_bridge/protocol.hpp"

#include <array>
#include <charconv>
#include <system_error>

namespace xar::bridge {
namespace {

constexpr bool ValidCharacter(std::uint64_t value) noexcept {
  return value > 0 && value < 0xFFFFFFFFULL;
}

constexpr bool Whitespace(char value) noexcept {
  return value == ' ' || value == '\t' || value == '\r' || value == '\n';
}

bool OptionalCharacter(std::string_view payload, std::string_view key,
                       std::string_view canonical_key,
                       std::optional<std::uint32_t> &output) noexcept {
  std::uint64_t value = 0;
  if (JsonUnsignedField(payload, key, value)) {
    if (!ValidCharacter(value)) return false;
    output = static_cast<std::uint32_t>(value);
    return true;
  }
  const auto begin = payload.find(canonical_key);
  if (begin == std::string_view::npos) return false;
  auto cursor = begin + canonical_key.size();
  while (cursor < payload.size() && Whitespace(payload[cursor])) ++cursor;
  if (payload.substr(cursor, 4) != "null") return false;
  cursor += 4;
  while (cursor < payload.size() && Whitespace(payload[cursor])) ++cursor;
  if (cursor == payload.size() ||
      (payload[cursor] != ',' && payload[cursor] != '}')) return false;
  output.reset();
  return true;
}

bool CanonicalRulerStep(std::string_view step, std::uint32_t actor,
                        std::uint32_t candidate) noexcept {
  constexpr std::string_view prefix = "arrange-marriage-";
  if (!step.starts_with(prefix)) return false;
  std::array<char, 21> pair{};
  auto first = std::to_chars(pair.data(), pair.data() + pair.size(), actor);
  if (first.ec != std::errc{}) return false;
  *first.ptr++ = '-';
  const auto second = std::to_chars(first.ptr, pair.data() + pair.size(), candidate);
  if (second.ec != std::errc{}) return false;
  return step.substr(prefix.size()) ==
      std::string_view(pair.data(), static_cast<std::size_t>(second.ptr - pair.data()));
}

}  // namespace

bool ParseFamilyMarriageOutgoingNativeFieldsV2(
    std::string_view payload, FamilyMarriageOutgoingRequestV2 &output) noexcept {
  output = {};
  FamilyMarriageOutgoingRequestV2 parsed{};
  std::string scope;
  std::string source_step;
  std::uint64_t actor = 0, subject = 0, candidate = 0;
  if (!JsonStringField(payload, "read_scope", scope, kMaximumControlStringBytes) ||
      !JsonStringField(payload, "source_action_step", source_step,
                       kMaximumControlStringBytes) ||
      !JsonUnsignedField(payload, "actor_character_id", actor) ||
      !JsonUnsignedField(payload, "subject_character_id", subject) ||
      !JsonUnsignedField(payload, "candidate_character_id", candidate) ||
      !ValidCharacter(actor) || !ValidCharacter(subject) || !ValidCharacter(candidate) ||
      !OptionalCharacter(payload, "expected_recipient_character_id",
                         "\"expected_recipient_character_id\":", parsed.expected_recipient) ||
      !OptionalCharacter(payload, "sender_character_id", "\"sender_character_id\":",
                         parsed.sender) ||
      !JsonBooleanField(payload, "request_matrilineal_option",
                        parsed.request_matrilineal_option) ||
      !JsonBooleanField(payload, "require_matrilineal_option_off",
                        parsed.require_matrilineal_option_off)) return false;
  parsed.actor = static_cast<std::uint32_t>(actor);
  parsed.subject = static_cast<std::uint32_t>(subject);
  parsed.candidate = static_cast<std::uint32_t>(candidate);
  if (scope == "ACTION_PREPARATION") {
    parsed.scope = FamilyMarriageOutgoingScopeV2::action_preparation;
  } else if (scope == "POST_SUBMISSION") {
    parsed.scope = FamilyMarriageOutgoingScopeV2::post_submission;
  } else {
    return false;
  }
  if ((parsed.scope == FamilyMarriageOutgoingScopeV2::post_submission) !=
      parsed.sender.has_value() || subject == candidate) return false;
  if (source_step == "submit-observed-first-heir-marriage-v1-private") {
    parsed.route = FamilyMarriageOutgoingRouteV2::first_heir;
  } else if (source_step == "submit-current-first-heir-betrothal-fulfillment-v1-private") {
    parsed.route = FamilyMarriageOutgoingRouteV2::fulfill_betrothal;
  } else if (source_step == "submit-player-child-matrilineal-marriage-v1-private") {
    parsed.route = FamilyMarriageOutgoingRouteV2::child_matrilineal;
  } else if (source_step == "submit-player-child-default-marriage-v1-private") {
    parsed.route = FamilyMarriageOutgoingRouteV2::child_default;
  } else if (CanonicalRulerStep(source_step, parsed.actor, parsed.candidate)) {
    parsed.route = FamilyMarriageOutgoingRouteV2::ruler;
  } else {
    return false;
  }
  if (parsed.route == FamilyMarriageOutgoingRouteV2::ruler) {
    if (actor != subject || parsed.expected_recipient.has_value() ||
        parsed.request_matrilineal_option || parsed.require_matrilineal_option_off)
      return false;
  } else {
    if (actor == subject || !parsed.expected_recipient.has_value() ||
        subject > 0x7FFFFFFFULL || candidate > 0x7FFFFFFFULL ||
        *parsed.expected_recipient > 0x7FFFFFFFU) return false;
    if (parsed.request_matrilineal_option !=
            (parsed.route == FamilyMarriageOutgoingRouteV2::child_matrilineal) ||
        parsed.require_matrilineal_option_off !=
            (parsed.route == FamilyMarriageOutgoingRouteV2::child_default)) return false;
  }
  output = parsed;
  return true;
}

}  // namespace xar::bridge
