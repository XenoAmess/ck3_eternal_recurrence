#include "xar_bridge/ck3_12003_religion_conversion_action_v1.hpp"

namespace xar::ck3_12002::religion_conversion::action12003 {
namespace {
bool SameActorFrame(const outcome::actor::Context &value,
                    const game::Snapshot &frame,
                    std::uint64_t epoch) noexcept {
  return value.available && value.capture_epoch == epoch &&
      value.played_character_id == frame.played_character_id &&
      value.date_raw == frame.date_raw;
}

std::optional<std::int64_t> Net(std::optional<std::int64_t> before,
                               std::optional<std::int64_t> after) noexcept {
  return before && after ? std::optional<std::int64_t>{*after - *before}
                         : std::nullopt;
}
} // namespace

Submission SubmitPaidPlayerConversion12003(
    const Access &access, const game::Snapshot &published,
    std::uint64_t public_revision, std::uint64_t native_revision,
    std::uint64_t pump_epoch, std::string_view request_id,
    const Request &request) {
  Submission out;
  out.request_id = request_id;
  out.request = request;
  out.native_revision = native_revision;
  out.capture_epoch = pump_epoch;
  out.date_raw = static_cast<std::int32_t>(published.date_raw);
  out.played_character_id = published.played_character_id;
  out.command_target_rite_id = request.target_rite_id;
  if (!public_revision || request.expected_revision != public_revision ||
      !published.paused || !published.map_ready ||
      !published.has_played_character || !published.played_character_alive ||
      request.target_rite_id == religion::kAbsentReference) {
    out.failure = "conversion_current_frame_or_target_unavailable";
    return out;
  }

  // The existing actor part is enough for identities and three balances.
  // Ancillary flag/state unavailability is retained rather than made a new gate.
  (void)outcome::ReadPlayedConversionOutcome12002(
      access.outcome, request.target_rite_id, pump_epoch, out.before);
  if (!SameActorFrame(out.before.actor, published, pump_epoch)) {
    out.failure = "conversion_before_actor_unavailable";
    return out;
  }
  if (out.before.actor.current_religion.rite_id == request.target_rite_id) {
    out.status = SubmitStatus::already_target_noop;
    return out;
  }
  if (!terms::ReadPlayedReligionConversionTerms12002(
          access.terms, request.target_rite_id, pump_epoch, out.paid_terms) ||
      out.paid_terms.played_character_id != published.played_character_id ||
      out.paid_terms.date_raw != published.date_raw ||
      out.paid_terms.capture_epoch != pump_epoch) {
    out.failure = "conversion_paid_terms_unavailable";
    return out;
  }
  (void)reasons::ReadPlayedReligionConversionReasons12002(
      access.reasons, request.target_rite_id, pump_epoch, out.native_reasons);
  if (!out.paid_terms.can_convert.value_or(false)) {
    out.failure = "conversion_paid_final_legality_denied";
    return out;
  }
  if (!out.paid_terms.cost.piety_cost_raw ||
      *out.paid_terms.cost.piety_cost_raw > request.max_piety_cost_raw) {
    out.failure = "conversion_piety_cost_exceeds_maximum";
    return out;
  }
  if (!access.commands.enabled || !access.terms.rite.module_base) {
    out.failure = "conversion_command_binding_unavailable";
    return out;
  }

  // .3 actual caller1516880 proves this same flags0/metadata0/payload, pay1.
  // No direct Execute, manual resource mutation, or setRite call is used here.
  auto command = religion_conversion_rite::MakeReadOnlyConvertRiteValue12002(
      access.terms.rite.module_base, published.played_character_id,
      request.target_rite_id, true);
  out.native_submit_copy_called = true;
  const auto queued = SubmitCommandCopy(access.commands, &command,
                                        kPaidConversionChannel);
  if (queued != CommandSubmitResult::submitted) {
    out.failure = queued == CommandSubmitResult::rejected
        ? "conversion_native_queue_rejected"
        : "conversion_command_copy_unavailable";
    return out;
  }
  out.status = SubmitStatus::queued_verification_pending;
  return out;
}

IndependentResult ReadPlayerConversionResult12003(
    const Access &access, const Submission &submitted,
    std::uint64_t pump_epoch) {
  IndependentResult out;
  out.request_id = submitted.request_id;
  out.action_id = submitted.request.action_id;
  out.submit_status = submitted.status;
  out.verification_pending =
      submitted.status == SubmitStatus::queued_verification_pending;
  out.quoted_base_piety_cost_raw = submitted.paid_terms.cost.piety_cost_raw;
  (void)outcome::ReadPlayedConversionOutcome12002(
      access.outcome, submitted.command_target_rite_id, pump_epoch, out.after);
  out.after_actor_available = out.after.actor.available &&
      out.after.actor.played_character_id == submitted.played_character_id &&
      out.after.actor.capture_epoch == pump_epoch;
  if (!out.after_actor_available || !submitted.before.actor.available)
    return out;
  const auto before_rite = submitted.before.actor.current_religion.rite_id;
  const auto after_rite = out.after.actor.current_religion.rite_id;
  if (before_rite && after_rite) {
    out.target_already_reached_before =
        *before_rite == submitted.command_target_rite_id;
    out.actual_target_reached_after =
        *after_rite == submitted.command_target_rite_id;
    out.actual_rite_changed = *before_rite != *after_rite;
  }
  const auto after_faith = out.after.actor.current_religion.faith_id;
  if (after_faith && submitted.paid_terms.available)
    out.actual_target_faith_reached_after =
        *after_faith == submitted.paid_terms.final_gate.target_faith_id;
  out.piety_net_delta_raw = Net(submitted.before.actor.piety_raw,
                                out.after.actor.piety_raw);
  out.gold_net_delta_raw = Net(submitted.before.actor.gold_raw,
                               out.after.actor.gold_raw);
  out.prestige_net_delta_raw = Net(submitted.before.actor.prestige_raw,
                                   out.after.actor.prestige_raw);
  out.request_associated_conversion_material_observed =
      submitted.status == SubmitStatus::queued_verification_pending &&
      pump_epoch > submitted.capture_epoch &&
      !out.target_already_reached_before.value_or(true) &&
      out.actual_rite_changed.value_or(false) &&
      out.actual_target_reached_after.value_or(false) &&
      out.actual_target_faith_reached_after.value_or(false) &&
      out.piety_net_delta_raw.has_value() &&
      out.gold_net_delta_raw.has_value() &&
      out.prestige_net_delta_raw.has_value();
  if (out.request_associated_conversion_material_observed)
    out.verification_pending = false;
  // This action result associates the owning request with fresh material.
  // It neither modifies the old readonly causality flag nor calls the net delta
  // an isolated native base payment; no Execute hook is a submit prerequisite.
  return out;
}
} // namespace xar::ck3_12002::religion_conversion::action12003
