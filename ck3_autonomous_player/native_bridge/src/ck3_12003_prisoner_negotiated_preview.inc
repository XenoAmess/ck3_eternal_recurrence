// Include once inside xar::ck3_12003, after ReadPrisonerReleasePreview12003.
// Reuses the existing leaf's identity/custody/definition/context helpers.
namespace {
struct NegotiatedNativeSample12003 {
  NativeSample common{};
  bool answer_available = false;
  std::int64_t answer_score = 0;
  std::uint8_t answer_status = 3;
  friend bool operator==(const NegotiatedNativeSample12003 &,
      const NegotiatedNativeSample12003 &) = default;
};

bool ReadNegotiatedSample12003(const PrisonerNegotiatedBindings12003 &b,
    const PrisonerReleasePreviewAccess12003 &access,
    std::uint32_t jailer, std::uint32_t prisoner, std::uint32_t requested_mask,
    NegotiatedNativeSample12003 &sample, std::string &reason) {
  auto &common = sample.common;
  if (!ReadCustody(b.release, access, jailer, prisoner, common)) {
    reason = "custody_relation_unverified"; return false;
  }
  if (!ReadDefinition(b.release, access, common, reason)) return false;
  const auto &c = b.release.gift.interaction;
  OwnedContext owned(c.destroy);
  void *const context = owned.data();
  if (b.release.gift.construct_two_role(context,
          reinterpret_cast<void *>(common.definition),
          static_cast<std::int32_t>(jailer), static_cast<std::int32_t>(prisoner),
          nullptr, true) != context) {
    reason = "context_construction_unavailable"; return false;
  }
  owned.MarkConstructed();
  b.release.clear_local_options(context);
  for (std::size_t i = 0; i < kPrisonerReleaseOptionKeys12003.size(); ++i)
    if ((requested_mask & (std::uint32_t{1} << i)) != 0)
      b.select_local_option(context, static_cast<std::int32_t>(i));
  c.refresh(context, true);
  c.finalize(context);
  const bool ordinary_selection = ReadFinalSelection(access,
      reinterpret_cast<std::uintptr_t>(context), jailer, prisoner, common, reason);
  // ReadFinalSelection has verified identity, roles, all13 and every selected
  // byte before reporting its ordinary-path-only nonzero-mask distinction.
  if (!ordinary_selection && reason != "option_mask_unexpected") return false;
  if (common.selected_option_mask_bits != requested_mask) {
    reason = "requested_release_options_not_retained"; return false;
  }
  reason.clear();
  common.can_send = c.validate(context, nullptr);
  c.evaluate_cost(reinterpret_cast<const std::byte *>(common.definition) +
      ck3_12002::kFactionGiftDefinitionCostOffsetV1, owned.scope(), common.costs.data());
  std::uintptr_t trigger = 0;
  if (!Read(access, common.definition,
          ck3_12002::kFactionGiftAutoAcceptTriggerOffsetV1, trigger)) {
    reason = "auto_accept_unavailable"; return false;
  }
  if (trigger != 0) {
    common.auto_accept = c.evaluate_trigger(reinterpret_cast<void *>(trigger), owned.scope());
  } else {
    std::uint8_t scalar = 0;
    if (!Read(access, common.definition,
            ck3_12002::kFactionGiftAutoAcceptScalarOffsetV1, scalar)) {
      reason = "auto_accept_unavailable"; return false;
    }
    common.auto_accept = scalar != 0;
  }
  // A false final CanSend is a complete observed gate. There is no sendable
  // native answer in that branch, so leave the answer explicitly unavailable.
  if (!common.can_send || common.auto_accept) return true;
  sample.answer_available = c.recipient_answer_score(context, &sample.answer_score) ==
      &sample.answer_score;
  if (!sample.answer_available) {
    reason = "recipient_answer_score_unavailable"; return false;
  }
  sample.answer_status = b.evaluate_answer(context, 1, 1, nullptr, nullptr);
  if (sample.answer_status > 2) {
    reason = "recipient_native_answer_unavailable"; return false;
  }
  return true;
}
} // namespace

PrisonerNegotiatedBindings12003 BindPrisonerNegotiatedPreview12003(
    std::uintptr_t base, std::string_view actual_sha) noexcept {
  PrisonerNegotiatedBindings12003 b{};
  b.release = BindPrisonerReleasePreview12003(base, actual_sha);
  if (!b.release.enabled) return b;
  b.select_local_option = reinterpret_cast<void (*)(void *, std::int32_t)>(
      base + ck3_12002::kPrisonerSelectOptionRva);
  b.evaluate_answer = reinterpret_cast<ck3_11906::EvaluateCharacterInteractionAnswer>(
      base + ck3_12002::kPrisonerEvaluateAnswerRva);
  return b;
}

bool ReadPrisonerNegotiatedPreview12003(const PrisonerNegotiatedBindings12003 &b,
    const PrisonerReleasePreviewAccess12003 &access,
    std::uint32_t jailer, std::uint32_t prisoner, std::uint32_t requested_mask,
    PrisonerNegotiatedPreview12003 &output) noexcept {
  output = {};
  output.requested_option_mask_bits = requested_mask;
  try {
    const auto fail = [&output](std::string_view reason) {
      output.observation.available = false;
      output.observation.unavailable_reason.assign(reason);
      return false;
    };
    if (!HasBindings(b.release) || b.select_local_option == nullptr ||
        b.evaluate_answer == nullptr ||
        b.release.gift.interaction.recipient_answer_score == nullptr ||
        access.capture_frame == nullptr || access.read_memory == nullptr)
      return fail("native_bindings_unavailable");
    if (access.current_thread_id == 0 ||
        access.current_thread_id != access.application_main_thread_id)
      return fail("application_main_thread_required");
    if (jailer == 0 || prisoner == 0 || jailer == prisoner)
      return fail("invalid_roles");
    if (requested_mask == 0 || (requested_mask & ~kPrisonerReleaseAllOptionMask12003) != 0)
      return fail("invalid_release_option_mask");
    bridge::PlayerPrisonerFrameV1 before{};
    if (!access.capture_frame(access.context, before)) return fail("frame_unavailable");
    if (!before.paused) return fail("not_paused");
    if (!before.map_ready || !before.played_character_alive ||
        !before.played_character_identity_round_trip || before.public_revision == 0 ||
        before.native_revision == 0 || before.proof_epoch == 0 ||
        static_cast<std::uint32_t>(before.played_character_id) != jailer)
      return fail("player_unavailable");
    NegotiatedNativeSample12003 first{};
    NegotiatedNativeSample12003 second{};
    std::string reason;
    if (!ReadNegotiatedSample12003(b, access, jailer, prisoner, requested_mask,
            first, reason)) {
      output.observation.selected_option_mask_bits = first.common.selected_option_mask_bits;
      return fail(reason);
    }
    if (!ReadNegotiatedSample12003(b, access, jailer, prisoner, requested_mask,
            second, reason)) {
      output.observation.selected_option_mask_bits = second.common.selected_option_mask_bits;
      return fail(reason);
    }
    if (first != second) return fail("native_sample_drift");
    bridge::PlayerPrisonerFrameV1 after{};
    if (!access.capture_frame(access.context, after)) return fail("frame_unavailable");
    if (before != after) return fail("frame_drift");
    const auto &common = first.common;
    auto &o = output.observation;
    o.frame = before;
    o.definition_key.assign(kPrisonerReleaseDefinitionKey12003);
    o.definition_stable_hash = static_cast<std::uint32_t>(common.definition_hash);
    o.definition_ordinal = common.definition_ordinal;
    o.actor_character_id = common.actor;
    o.recipient_character_id = common.recipient;
    o.jailer_character_id = jailer;
    o.prisoner_character_id = prisoner;
    o.puppet_or_actor_character_id = common.puppet_or_actor;
    o.can_send = common.can_send;
    o.auto_accept = common.auto_accept;
    o.send_costs_raw = common.costs;
    o.observed_definition_option_count = common.definition_option_count;
    o.observed_context_option_count = common.context_option_count;
    o.selected_option_mask_bits = common.selected_option_mask_bits;
    output.recipient_answer_available = first.answer_available;
    output.recipient_acceptance_score_raw = first.answer_score;
    output.recipient_answer_status_raw = first.answer_status;
    o.unavailable_reason.clear();
    o.available = true;
    return true;
  } catch (...) {
    output.observation.available = false;
    output.observation.unavailable_reason = "native_evaluation_unavailable";
    return false;
  }
}
