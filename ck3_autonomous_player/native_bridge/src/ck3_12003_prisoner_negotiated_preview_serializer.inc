// Include once inside xar::ck3_12003, after the existing release serializer.
std::string SerializePrisonerNegotiatedPreview12003(
    const PrisonerNegotiatedPreview12003 &preview) {
  const auto &o = preview.observation;
  std::string out = "{\"private_build\":true,\"read_only\":true,"
      "\"advertised\":false,\"action_surface_present\":false";
  out += ",\"requested_option_mask_bits\":" +
      std::to_string(preview.requested_option_mask_bits);
  if (!o.available) {
    out += ",\"status\":\"unavailable\",\"unavailable_reason\":";
    AppendEscaped(out, o.unavailable_reason.empty() ?
        std::string_view{"native_evaluation_unavailable"} :
        std::string_view{o.unavailable_reason});
    if (o.unavailable_reason == "requested_release_options_not_retained")
      out += ",\"observed_option_mask_bits\":" +
          std::to_string(o.selected_option_mask_bits);
    out += '}';
    return out;
  }
  out += ",\"status\":\"available\",\"snapshot_id\":";
  AppendEscaped(out, "native:" + std::to_string(o.frame.native_revision));
  out += ",\"public_revision\":" + std::to_string(o.frame.native_revision);
  out += ",\"native_revision\":" + std::to_string(o.frame.native_revision);
  out += ",\"proof_epoch\":" + std::to_string(o.frame.proof_epoch);
  out += ",\"date_raw\":" + std::to_string(o.frame.date_raw);
  out += ",\"definition\":{\"canonical_key\":";
  AppendEscaped(out, o.definition_key);
  out += ",\"deterministic_key_hash\":" + std::to_string(o.definition_stable_hash);
  out += ",\"runtime_ordinal\":" + std::to_string(o.definition_ordinal) + '}';
  out += ",\"payload_shape\":\"two_role_selected_release_options\"";
  out += ",\"roles\":{\"actor_character_id\":" + std::to_string(o.actor_character_id);
  out += ",\"recipient_character_id\":" + std::to_string(o.recipient_character_id) + '}';
  out += ",\"puppet_or_actor_character_id\":" +
      std::to_string(o.puppet_or_actor_character_id);
  out += ",\"option_keys\":[";
  for (std::size_t i = 0; i < kPrisonerReleaseOptionKeys12003.size(); ++i) {
    if (i != 0) out.push_back(',');
    AppendEscaped(out, kPrisonerReleaseOptionKeys12003[i]);
  }
  out += "],\"selected_option_mask_bits\":" +
      std::to_string(o.selected_option_mask_bits);
  out += ",\"can_send\":";
  out += o.can_send ? "true" : "false";
  out += ",\"costs\":{\"raw_scale\":100000,\"payer_role\":\"actor\","
      "\"application_timing\":\"on_send\",\"entries\":[";
  for (std::size_t i = 0; i < kPrisonerReleaseCostKeys12003.size(); ++i) {
    if (i != 0) out.push_back(',');
    out += "{\"resource_key\":";
    AppendEscaped(out, kPrisonerReleaseCostKeys12003[i]);
    out += ",\"raw\":" + std::to_string(o.send_costs_raw[i]) + '}';
  }
  out += "]},\"acceptance\":{\"auto_accept\":";
  out += o.auto_accept ? "true" : "false";
  if (!o.can_send) {
    out += ",\"kind\":\"not_evaluated_unsendable\"";
  } else if (o.auto_accept) {
    out += ",\"kind\":\"auto_accept\",\"would_accept_now\":true";
  } else {
    out += ",\"kind\":\"native_answer\",\"raw_scale\":100000,"
        "\"recipient_acceptance_score_raw\":" +
        std::to_string(preview.recipient_acceptance_score_raw);
    out += ",\"recipient_answer_status_raw\":" +
        std::to_string(preview.recipient_answer_status_raw);
    out += ",\"would_accept_now\":";
    out += preview.recipient_answer_status_raw != 2 ? "true" : "false";
  }
  out += "},\"readiness\":{\"definition_ready\":true,\"actor_ready\":true,"
      "\"recipient_ready\":true,\"finalized_context_ready\":true,"
      "\"can_send_ready\":true,\"costs_ready\":true,\"acceptance_ready\":";
  out += o.can_send ? "true" : "false";
  out += ",\"same_frame_ready\":true}}";
  return out;
}
